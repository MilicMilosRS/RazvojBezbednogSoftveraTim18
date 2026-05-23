from fastapi import FastAPI, Depends, UploadFile, File, Form, HTTPException
from auth import create_access_token, verify_token
import os
import shutil
import sqlite3
import uuid
from werkzeug.utils import secure_filename # Dodato za bezbednost

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
            url TEXT
        )
    ''')
    # Tabela za reviziju (Audit log)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS audit_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            username TEXT,
            action TEXT
        )
    ''')
    conn.commit()
    conn.close()

init_db()

def log_audit(username: str, action: str):
    """Beleži događaje za potrebe revizije."""
    conn = sqlite3.connect("oblak.db")
    conn.cursor().execute("INSERT INTO audit_log (username, action) VALUES (?, ?)", (username, action))
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
    file: UploadFile = File(...), 
    username: str = Depends(verify_token)
):
    # STRIDE: Ublažavanje Tampering pretnje i Path Traversal napada
    # secure_filename uklanja opasne karaktere poput "../"
    safe_filename = secure_filename(file.filename)
    if not safe_filename:
        raise HTTPException(status_code=400, detail="Nevažeće ime fajla")

    user_dir = os.path.join(STORAGE_DIR, username)
    os.makedirs(user_dir, exist_ok=True)
    
    task_id = str(uuid.uuid4())
    # Dodajemo task_id u ime fajla kako bismo izbegli prepisivanje
    final_filename = f"{task_id}_{safe_filename}"
    file_path = os.path.join(user_dir, final_filename)
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    # Upis u bazu
    conn = sqlite3.connect("oblak.db")
    conn.cursor().execute(
        "INSERT INTO tasks (task_id, username, filename, status, url) VALUES (?, ?, ?, ?, ?)",
        (task_id, username, final_filename, "UPLOADED", "")
    )
    conn.commit()
    conn.close()
    
    log_audit(username, f"Uploadovao fajl {safe_filename} pod ID-jem {task_id}")
    
    return {"message": "Fajl uspešno sačuvan.", "task_id": task_id}

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