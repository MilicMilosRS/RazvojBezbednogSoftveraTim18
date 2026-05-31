from fastapi import FastAPI, Depends, UploadFile, File, Form, HTTPException, BackgroundTasks, Request
from verifier import verify
from auth import create_access_token, verify_token
import os
from dotenv import load_dotenv
import shutil
import sqlite3
import uuid
from werkzeug.utils import secure_filename # Dodato za bezbednost

load_dotenv()

app = FastAPI(title="Oblak API Server")

STORAGE_DIR = "storage"
os.makedirs(STORAGE_DIR, exist_ok=True)

# --- Inicijalizacija baze podataka ---
def init_db():
    conn = sqlite3.connect("oblak.db")
    cursor = conn.cursor()
    # Tabela za zadatke (kodove)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tasks (
            task_id TEXT PRIMARY KEY,
            username TEXT,
            filename TEXT,
            status TEXT,
            url TEXT,
            output TEXT
        )
    ''')
    # Tabela za reviziju (Audit log)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS audit_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            username TEXT,
            action TEXT,
            task_id TEXT,
            source_ip TEXT,
            result TEXT,
            duration_ms INTEGER
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS runs (
            run_id TEXT PRIMARY KEY,
            task_id TEXT,
            username TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            status TEXT,
            output TEXT,
            duration_ms INTEGER,
            vm_id TEXT
        )
    ''')

    conn.commit()
    conn.close()

init_db()

# prošireni log_audit
def log_audit(username, action, task_id=None, source_ip=None,
              result=None, duration_ms=None):
    conn = sqlite3.connect("oblak.db")
    conn.cursor().execute(
        """INSERT INTO audit_log
           (username, action, task_id, source_ip, result, duration_ms)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (username, action, task_id, source_ip, result, duration_ms)
    )
    conn.commit()
    conn.close()

# --- Rute ---

@app.post("/login")
def login(username: str = Form(...), password: str = Form(...)):
    if username == "admin" and password == "tajna123":
        token = create_access_token(username)
        log_audit(username, "Ulogovao se na sistem")
        return {"access_token": token, "token_type": "bearer"}
    raise HTTPException(status_code=401, detail="Pogrešni kredencijali")

@app.post("/upload")
def upload_code(
    script: UploadFile = File(...),
    requirements: UploadFile = File(None),   # opciono
    background_tasks: BackgroundTasks, 
    username: str = Depends(verify_token)
):
    # Path Traversal zaštita za oba fajla
    safe_script = secure_filename(script.filename)
    if not safe_script or not safe_script.endswith(".py"):
        raise HTTPException(status_code=400, detail="Nevažeće ime Python fajla")

    user_dir = os.path.join(STORAGE_DIR, username)
    os.makedirs(user_dir, exist_ok=True)

    task_id = str(uuid.uuid4())
    #Svaki task dobija svoj poddirektorijum, drži skriptu i requirements zajedno
    task_dir = os.path.join(user_dir, task_id)
    os.makedirs(task_dir, exist_ok=True)

    #Skripta se uvek čuva kao main.py radi predvidljivog pokretanja u VM-u
    script_path = os.path.join(task_dir, "main.py")
    with open(script_path, "wb") as buffer:
        shutil.copyfileobj(script.file, buffer)

    has_requirements = False
    if requirements is not None:
        req_path = os.path.join(task_dir, "requirements.txt")
        with open(req_path, "wb") as buffer:
            shutil.copyfileobj(requirements.file, buffer)
        has_requirements = True

    #Upis u bazu — čuvamo putanju do task direktorijuma i da li ima requirements
    conn = sqlite3.connect("oblak.db")
    conn.cursor().execute(
        "INSERT INTO tasks (task_id, username, filename, status, url) VALUES (?, ?, ?, ?, ?)",
        (task_id, username, task_dir, "UPLOADED", "")
    )
    conn.commit()
    conn.close()

    log_audit(username, f"Uploadovao {safe_script}" +
              (" sa requirements.txt" if has_requirements else "") +
              f" pod ID-jem {task_id}")
    
    background_tasks.add_task(verify, task_id, script_path)
     
    return {
        "message": "Fajl(ovi) uspešno sačuvani.",
        "task_id": task_id,
        "requirements": has_requirements
    }

@app.get("/status/{task_id}")
def get_status(task_id: str, username: str = Depends(verify_token)):
    conn = sqlite3.connect("oblak.db")
    cursor = conn.cursor()
    cursor.execute("SELECT status FROM tasks WHERE task_id = ? AND username = ?", (task_id, username))
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return {"task_id": task_id, "status": row[0]}
    raise HTTPException(status_code=404, detail="Task nije pronađen")

@app.post("/generate-url")
def generate_url(task_id: str, username: str = Depends(verify_token)):
    conn = sqlite3.connect("oblak.db")
    cursor = conn.cursor()
    cursor.execute("SELECT status FROM tasks WHERE task_id = ? AND username = ?", (task_id, username))
    row = cursor.fetchone()
    
    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="Task nije pronađen")
        
    generated_url = f"http://localhost:8000/run/{task_id}"
    cursor.execute("UPDATE tasks SET url = ? WHERE task_id = ?", (generated_url, task_id))
    conn.commit()
    conn.close()
    
    log_audit(username, f"Generisao URL za task {task_id}")
    
    return {"url": generated_url}

from docker_manager import DockerManager
import time

fc_manager = DockerManager()

def save_run(run_id, task_id, username, status, output=None,
             duration_ms=None, vm_id=None):
    conn = sqlite3.connect("oblak.db")
    conn.cursor().execute(
        """INSERT INTO runs
           (run_id, task_id, username, status, output, duration_ms, vm_id)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (run_id, task_id, username, status, output, duration_ms, vm_id)
    )
    conn.commit()
    conn.close()

@app.post("/run/{task_id}")
def run_code(task_id: str, request: Request,
             username: str = Depends(verify_token)):
    source_ip = request.client.host
    conn = sqlite3.connect("oblak.db")
    cursor = conn.cursor()
    cursor.execute(
        "SELECT username, filename FROM tasks WHERE task_id = ? AND username = ?",
        (task_id, username)
    )
    row = cursor.fetchone()
    if not row:
        conn.close()
        log_audit(username, "Pokušaj izvršavanja nepostojećeg/tuđeg taska",
                  task_id=task_id, source_ip=source_ip, result="DENIED")
        raise HTTPException(status_code=404, detail="Task nije pronađen")

    owner, task_dir = row
    conn.close()

    run_id = str(uuid.uuid4())   # svako izvršavanje ima svoj ID
    log_audit(username, "Započeo izvršavanje", task_id=task_id,
              source_ip=source_ip, result="STARTED")

    start = time.time()
    vm_id = None
    try:
        vm_id = fc_manager.start_vm(task_dir)
        output = fc_manager.get_output(vm_id, timeout=30)
        duration = int((time.time() - start) * 1000)

        _update_status(task_id, "COMPLETED")
        save_run(run_id, task_id, username, "SUCCESS",
                 output=output, duration_ms=duration, vm_id=vm_id)
        log_audit(username, "Završio izvršavanje", task_id=task_id,
                  source_ip=source_ip, result="SUCCESS", duration_ms=duration)
        return {"task_id": task_id, "run_id": run_id,
                "vm_id": vm_id, "output": output}

    except Exception as e:
        duration = int((time.time() - start) * 1000)
        _update_status(task_id, "FAILED")
        save_run(run_id, task_id, username, "ERROR",
                 output=str(e), duration_ms=duration, vm_id=vm_id)
        log_audit(username, "Greška pri izvršavanju", task_id=task_id,
                  source_ip=source_ip, result=f"ERROR: {e}", duration_ms=duration)
        raise HTTPException(status_code=500, detail="Izvršavanje neuspešno")
    finally:
        if vm_id:
            fc_manager.stop_vm(vm_id)


def _update_status(task_id, status, output=None):
    conn = sqlite3.connect("oblak.db")
    if output is not None:
        conn.cursor().execute(
            "UPDATE tasks SET status = ?, output = ? WHERE task_id = ?",
            (status, output, task_id))
    else:
        conn.cursor().execute(
            "UPDATE tasks SET status = ? WHERE task_id = ?",
            (status, task_id))
    conn.commit()
    conn.close()


@app.get("/audit-log")
def get_audit_log(username: str = Depends(verify_token), limit: int = 100):
    conn = sqlite3.connect("oblak.db")
    cursor = conn.cursor()
    cursor.execute(
        """SELECT timestamp, username, action, task_id, source_ip, result, duration_ms
           FROM audit_log ORDER BY id DESC LIMIT ?""", (limit,)
    )
    rows = cursor.fetchall()
    conn.close()
    keys = ["timestamp", "username", "action", "task_id",
            "source_ip", "result", "duration_ms"]
    return {"entries": [dict(zip(keys, r)) for r in rows]}

@app.get("/runs/{task_id}")
def list_runs(task_id: str, username: str = Depends(verify_token)):
    """Lista svih izvršavanja za dati task (bez punog izlaza, samo pregled)."""
    conn = sqlite3.connect("oblak.db")
    cursor = conn.cursor()
    cursor.execute(
        """SELECT run_id, timestamp, status, duration_ms
           FROM runs WHERE task_id = ? AND username = ?
           ORDER BY timestamp DESC""",
        (task_id, username)
    )
    rows = cursor.fetchall()
    conn.close()
    keys = ["run_id", "timestamp", "status", "duration_ms"]
    return {"task_id": task_id, "runs": [dict(zip(keys, r)) for r in rows]}


@app.get("/runs/{task_id}/{run_id}")
def get_run(task_id: str, run_id: str, username: str = Depends(verify_token)):
    """Pun izlaz jednog konkretnog izvršavanja."""
    conn = sqlite3.connect("oblak.db")
    cursor = conn.cursor()
    cursor.execute(
        """SELECT timestamp, status, output, duration_ms, vm_id
           FROM runs WHERE run_id = ? AND task_id = ? AND username = ?""",
        (run_id, task_id, username)
    )
    row = cursor.fetchone()
    conn.close()
    if not row:
        raise HTTPException(status_code=404, detail="Izvršavanje nije pronađeno")
    keys = ["timestamp", "status", "output", "duration_ms", "vm_id"]
    return {"run_id": run_id, **dict(zip(keys, row))}