import typer
import requests
import os
import zipfile
import shutil

app = typer.Typer(help="Oblak CDK CLI - Alat za deploy Python koda")

SERVER_URL = "http://localhost:8000"
TOKEN_FILE = ".oblak_token"

def _require_token():
    if not os.path.exists(TOKEN_FILE):
        typer.secho("❌ Niste ulogovani.", fg=typer.colors.RED)
        raise typer.Exit()
    with open(TOKEN_FILE, "r") as f:
        return f.read().strip()

@app.command()
def login(username: str):
    """
    Logovanje na Oblak server. Traži lozinku i čuva JWT token lokalno.
    """
    password = typer.prompt("Unesite lozinku", hide_input=True)
    
    response = requests.post(
        f"{SERVER_URL}/login", 
        data={"username": username, "password": password},
        timeout=10
    )
    
    if response.status_code == 200:
        token = response.json().get("access_token")
        with open(TOKEN_FILE, "w") as f:
            f.write(token)
        typer.secho("✅ Uspešno ste se ulogovali!", fg=typer.colors.GREEN)
    else:
        typer.secho(f"❌ Greška pri logovanju: {response.json().get('detail')}", fg=typer.colors.RED)

@app.command()
def deploy(
    script: str = typer.Argument(..., help="Putanja do Python fajla koji se pokreće"),
    requirements: str = typer.Option(None, "--requirements", "-r",
                                      help="Putanja do requirements.txt (opciono)")
):
    """
    Šalje Python fajl (i opciono requirements.txt) na server.
    """
    if not os.path.exists(TOKEN_FILE):
        typer.secho("❌ Niste ulogovani. Pokrenite 'python cli.py login <username>'", fg=typer.colors.RED)
        raise typer.Exit()

    with open(TOKEN_FILE, "r") as f:
        token = f.read().strip()

    # Validacija ulaza
    if not os.path.isfile(script) or not script.endswith(".py"):
        typer.secho("❌ Prvi argument mora biti postojeći .py fajl.", fg=typer.colors.RED)
        raise typer.Exit()

    if requirements and not os.path.isfile(requirements):
        typer.secho(f"❌ Requirements fajl '{requirements}' ne postoji.", fg=typer.colors.RED)
        raise typer.Exit()

    headers = {"Authorization": f"Bearer {token}"}

    # Sastavljanje multipart payload-a; requirements se dodaje samo ako postoji
    open_files = []
    try:
        script_f = open(script, "rb")
        open_files.append(script_f)
        files = {"script": (os.path.basename(script), script_f, "text/x-python")}

        if requirements:
            req_f = open(requirements, "rb")
            open_files.append(req_f)
            files["requirements"] = ("requirements.txt", req_f, "text/plain")

        typer.echo(f"📤 Šaljem {os.path.basename(script)}" +
                   (f" + requirements.txt" if requirements else "") + "...")

        response = requests.post(
            f"{SERVER_URL}/upload", headers=headers, files=files, timeout=30
        )
    finally:
        for f in open_files:
            f.close()

    if response.status_code == 200:
        data = response.json()
        typer.secho(f"✅ Uspešan deploy: {data.get('message')}", fg=typer.colors.GREEN)
        typer.secho(f"📌 Vaš task ID je: {data.get('task_id')}", fg=typer.colors.CYAN)
    else:
        typer.secho(f"❌ Greška pri upload-u: {response.text}", fg=typer.colors.RED)

@app.command()
def status(task_id: str):
    """
    Proverava status poslatog koda.
    """
    if not os.path.exists(TOKEN_FILE):
        typer.secho("❌ Niste ulogovani.", fg=typer.colors.RED)
        raise typer.Exit()

    with open(TOKEN_FILE, "r") as f:
        token = f.read().strip()

    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(
        f"{SERVER_URL}/status/{task_id}", 
        headers=headers,
        timeout=10
    )

    if response.status_code == 200:
        typer.secho(f"ℹ️  Status za task {task_id}: {response.json().get('status')}", fg=typer.colors.CYAN)
    else:
        typer.secho(f"❌ Greška: {response.json().get('detail')}", fg=typer.colors.RED)

@app.command()
def generate_url(task_id: str):
    """
    Generiše URL za pokretanje izvršavanja koda.
    """
    if not os.path.exists(TOKEN_FILE):
        typer.secho("❌ Niste ulogovani.", fg=typer.colors.RED)
        raise typer.Exit()

    with open(TOKEN_FILE, "r") as f:
        token = f.read().strip()

    headers = {"Authorization": f"Bearer {token}"}
    response = requests.post(
        f"{SERVER_URL}/generate-url", 
        headers=headers, 
        params={"task_id": task_id},
        timeout=10
    )

    if response.status_code == 200:
        typer.secho(f"🔗 URL generisan: {response.json().get('url')}", fg=typer.colors.GREEN)
    else:
        typer.secho(f"❌ Greška: {response.json().get('detail')}", fg=typer.colors.RED)

@app.command()
def run(task_id: str):
    """Pokreće izvršavanje koda u MicroVM-u."""
    if not os.path.exists(TOKEN_FILE):
        typer.secho("❌ Niste ulogovani.", fg=typer.colors.RED)
        raise typer.Exit()

    with open(TOKEN_FILE, "r") as f:
        token = f.read().strip()

    headers = {"Authorization": f"Bearer {token}"}
    typer.echo("⏳ Pokrećem VM, sačekaj...")
    response = requests.post(
        f"{SERVER_URL}/run/{task_id}",
        headers=headers,
        timeout=120   # VM boot + izvršavanje ume da potraje
    )

    if response.status_code == 200:
        data = response.json()
        typer.secho(f"✅ Izvršeno (vm_id: {data.get('vm_id')})", fg=typer.colors.GREEN)
        typer.secho("--- Izlaz ---", fg=typer.colors.CYAN)
        typer.echo(data.get("output", "(prazno)"))
    else:
        typer.secho(f"❌ Greška: {response.text}", fg=typer.colors.RED)

@app.command()
def runs(task_id: str):
    """Prikazuje istoriju izvršavanja za task."""
    token = _require_token()
    headers = {"Authorization": f"Bearer {token}"}
    r = requests.get(f"{SERVER_URL}/runs/{task_id}", headers=headers, timeout=10)
    if r.status_code != 200:
        typer.secho(f"❌ Greška: {r.text}", fg=typer.colors.RED)
        return
    data = r.json()
    if not data["runs"]:
        typer.secho("Nema izvršavanja za ovaj task.", fg=typer.colors.YELLOW)
        return
    typer.secho(f"📜 Istorija za task {task_id}:", fg=typer.colors.CYAN)
    for run in data["runs"]:
        boja = typer.colors.GREEN if run["status"] == "SUCCESS" else typer.colors.RED
        typer.secho(
            f"  {run['timestamp']} | {run['status']:8} | "
            f"{run['duration_ms']}ms | {run['run_id']}", fg=boja)


@app.command()
def run_log(task_id: str, run_id: str):
    """Prikazuje pun izlaz jednog izvršavanja."""
    token = _require_token()
    headers = {"Authorization": f"Bearer {token}"}
    r = requests.get(f"{SERVER_URL}/runs/{task_id}/{run_id}",
                     headers=headers, timeout=10)
    if r.status_code != 200:
        typer.secho(f"❌ Greška: {r.text}", fg=typer.colors.RED)
        return
    data = r.json()
    typer.secho(f"📊 Status: {data['status']} ({data['duration_ms']}ms)",
                fg=typer.colors.CYAN)
    typer.secho("--- Izlaz ---", fg=typer.colors.CYAN)
    typer.echo(data.get("output") or "(prazno)")

if __name__ == "__main__":
    app()