import docker
import uuid
import os

class DockerManager:
    def __init__(self):
        self.client = docker.from_env()
        self.containers = {}

    def start_vm(self, task_dir: str) -> str:
        run_id = str(uuid.uuid4())

        # Inline komanda — bez run.sh fajla, bez CRLF problema
        cmd = (
            "if [ -f requirements.txt ]; then "
            "  pip install --quiet -r requirements.txt 2>&1; "
            "fi; "
            "python main.py 2>&1"
        )

        container = self.client.containers.run(
            "python:3.11-slim",
            command=["sh", "-c", cmd],
            working_dir="/workspace",
            volumes={os.path.abspath(task_dir): {
                "bind": "/workspace", "mode": "ro"
            }},
            mem_limit="256m",
            cpu_quota=50000,
            network_mode="bridge",
            cap_drop=["ALL"],
            security_opt=["no-new-privileges"],
            detach=True,
            remove=False,
        )
        self.containers[run_id] = container
        return run_id

    def get_output(self, run_id: str, timeout: int = 30) -> str:
        container = self.containers[run_id]
        try:
            container.wait(timeout=timeout)
        except Exception:
            container.kill()
        return container.logs().decode("utf-8", errors="replace")[-4096:]

    def stop_vm(self, run_id: str):
        container = self.containers.pop(run_id, None)
        if not container:
            return
        try:
            container.remove(force=True)
        except Exception:
            pass