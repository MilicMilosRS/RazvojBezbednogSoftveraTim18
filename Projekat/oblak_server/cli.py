import typer
import requests
import os
import zipfile
import shutil

app = typer.Typer(help="Oblak CDK CLI - Alat za deploy Python koda")

SERVER_URL = "http://localhost:8000"
TOKEN_FILE = ".oblak_token"

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
def deploy(path: str):
    """
    Pakuje kod iz zadatog foldera i šalje ga na server.
    """
    if not os.path.exists(TOKEN_FILE):
        typer.secho("❌ Niste ulogovani. Pokrenite 'python cli.py login <username>'", fg=typer.colors.RED)
        raise typer.Exit()

    with open(TOKEN_FILE, "r") as f:
        token = f.read().strip()

    if not os.path.isdir(path):
        typer.secho("❌ Zadati put mora biti folder sa vašim kodom.", fg=typer.colors.RED)
        raise typer.Exit()

    # Pakovanje foldera u ZIP arhivu
    zip_filename = f"{os.path.basename(os.path.normpath(path))}.zip"
    shutil.make_archive(zip_filename.replace('.zip', ''), 'zip', path)
    
    typer.echo(f"📦 Arhiva {zip_filename} kreirana. Šaljem na server...")

    # Slanje na server sa JWT tokenom
    headers = {"Authorization": f"Bearer {token}"}
    with open(zip_filename, "rb") as f:
        files = {"file": (zip_filename, f, "application/zip")}
        response = requests.post(
            f"{SERVER_URL}/upload", 
            headers=headers, 
            files=files,
            timeout=10
        )

    if response.status_code == 200:
        data = response.json()
        typer.secho(f"✅ Uspešan deploy: {data.get('message')}", fg=typer.colors.GREEN)
        typer.secho(f"📌 Vaš task ID je: {data.get('task_id')}", fg=typer.colors.CYAN)
    else:
        typer.secho(f"❌ Greška pri upload-u: {response.text}", fg=typer.colors.RED)

    # Čišćenje lokalne arhive nakon slanja
    if os.path.exists(zip_filename):
        os.remove(zip_filename)

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

if __name__ == "__main__":
    app()