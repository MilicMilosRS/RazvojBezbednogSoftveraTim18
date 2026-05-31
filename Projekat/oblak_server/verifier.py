import subprocess
import os
import sqlite3
import zipfile
import json
from google import genai
from google.genai import types
from dotenv import load_dotenv
load_dotenv()

STORAGE_DIR = "storage"
SANDBOX_DIR = "sandbox"

def update_status(task_id: str, status: str):
    conn = sqlite3.connect("oblak.db")
    conn.cursor().execute(
        "UPDATE tasks SET status = ? WHERE task_id = ?", 
        (status, task_id)
    )
    conn.commit()
    conn.close()

def run_bandit(code_path: str) -> dict:
    result = subprocess.run(
        ["bandit", "-r", code_path, "-f", "json", "-q"],
        capture_output=True, text=True
    )
    try:
        if not result.stdout.strip():
            return {"passed": True, "issues": [], "high_severity_count": 0}
        
        report = json.loads(result.stdout)
        issues = report.get("results", [])
        # Blokiraj i MEDIUM i HIGH, ne samo HIGH
        risky = [i for i in issues if i["issue_severity"] in ("HIGH", "MEDIUM")]
        return {
            "passed": len(risky) == 0,
            "issues": issues,
            "high_severity_count": len(risky)
        }
    except Exception:
        return {"passed": False, "issues": [], "high_severity_count": 0}
    
def run_clamav(file_path: str) -> dict:
    """Skenira fajl pomoću ClamAV-a."""
    result = subprocess.run(
        ["clamscan", "--no-summary", file_path],
        capture_output=True, text=True
    )
    # Exit code 0 = čisto, 1 = virus pronađen
    return {
        "passed": result.returncode == 0,
        "output": result.stdout
    }

def run_llm_analysis(code_snippet: str) -> dict:
    """Šalje kod Gemini API-ju na analizu i vraća JSON odgovor."""
    # Klijent automatski povlači ključ iz os.environ.get("GEMINI_API_KEY")
    # Ako želiš ručno, možeš staviti: client = genai.Client(api_key="TVOJ_KLJUČ")
    client = genai.Client()

    prompt = f"""Analiziraj sledeći Python kod sa bezbednosnog aspekta.
Odgovori SAMO u JSON formatu ovako:
{{"safe": true/false, "reason": "kratak opis", "risk_level": "LOW/MEDIUM/HIGH"}}

Kod:
{code_snippet}"""

    # Koristimo response_mime_type da nateramo Gemini da garantovano vrati čist JSON
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            temperature=0.1,  # Niža temperatura za precizniji i stabilniji JSON
        ),
    )

    # Gemini vraća čist JSON string u response.text, bez ```json ... ``` blokova
    return json.loads(response.text)

def install_dependencies(extract_path: str) -> bool:
    """Instalira zavisnosti iz requirements.txt ako postoji."""
    req_file = os.path.join(extract_path, "requirements.txt")
    if not os.path.exists(req_file):
        return True  # Nema zavisnosti, OK
    
    sandbox_path = os.path.join(SANDBOX_DIR, os.path.basename(extract_path))
    os.makedirs(sandbox_path, exist_ok=True)
    
    result = subprocess.run(
        ["pip", "install", "-r", req_file, 
         "--target", sandbox_path,      # Instaliraj u sandbox, ne globalno
         "--quiet"],
        capture_output=True, text=True,
        timeout=60                       # Max 60 sekundi
    )
    return result.returncode == 0

def verify(task_id: str, file_path: str):
    """
    Glavni verifikacioni pipeline.
    Poziva se nakon upload-a.
    """
    try:
        update_status(task_id, "VERIFYING")
        
        # 1. ClamAV anti-virus sken
        av_result = run_clamav(file_path)
        if not av_result["passed"]:
            update_status(task_id, "REJECTED_AV")
            return {"passed": False, "stage": "antivirus", "detail": av_result["output"]}
        
        # 2. Raspakivanje ZIP-a
        extract_path = os.path.join(STORAGE_DIR, task_id + "_extracted")
        os.makedirs(extract_path, exist_ok=True)
        with zipfile.ZipFile(file_path, 'r') as z:
            z.extractall(extract_path)
        
        # 3. Bandit statička analiza
        bandit_result = run_bandit(extract_path)
        if not bandit_result["passed"]:
            update_status(task_id, "REJECTED_BANDIT")
            return {"passed": False, "stage": "bandit", 
                    "detail": f"{bandit_result['high_severity_count']} HIGH nalaza"}
        
        # 4. LLM analiza — čita main.py ili prvi .py fajl
        py_files = [f for f in os.listdir(extract_path) if f.endswith(".py")]
        if py_files:
            with open(os.path.join(extract_path, py_files[0]), "r") as f:
                code = f.read()
            llm_result = run_llm_analysis(code)
            if not llm_result.get("safe"):
                update_status(task_id, "REJECTED_LLM")
                return {"passed": False, "stage": "llm", 
                        "detail": llm_result.get("reason")}
        
        # 5. Instalacija zavisnosti
        deps_ok = install_dependencies(extract_path)
        if not deps_ok:
            update_status(task_id, "REJECTED_DEPS")
            return {"passed": False, "stage": "dependencies"}
        
        update_status(task_id, "VERIFIED")
        return {"passed": True}
    
    except zipfile.BadZipFile:
        # Fajl nije validan ZIP
        update_status(task_id, "REJECTED_INVALID")
        return {"passed": False, "stage": "zip", "detail": "Nevažeći ZIP fajl"}
    
    except Exception as e:
        # Neočekivana greška — odbij, ne propuštaj
        update_status(task_id, "REJECTED_ERROR")
        return {"passed": False, "stage": "unknown", "detail": str(e)}