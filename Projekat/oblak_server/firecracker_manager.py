# firecracker_manager.py
import os
import json
import time
import uuid
import shutil
import subprocess

FIRECRACKER_BIN = "/usr/bin/firecracker"
KERNEL_IMAGE = "/opt/firecracker/vmlinux.bin"
BASE_ROOTFS = "/opt/firecracker/rootfs.ext4"
VM_DIR = "/tmp/firecracker_vms"

os.makedirs(VM_DIR, exist_ok=True)


class FirecrackerManager:
    """Pokreće, izoluje i gasi MicroVM-ove. Bez mreže — kod se izvršava offline."""

    def __init__(self):
        self.vms = {}  # vm_id -> dict sa procesom i putanjama

    def start_vm(self, code_path: str) -> str:
        vm_id = str(uuid.uuid4())
        rootfs = os.path.join(VM_DIR, f"{vm_id}.ext4")
        config = os.path.join(VM_DIR, f"{vm_id}.json")
        log_path = os.path.join(VM_DIR, f"{vm_id}.log")

        # Izolacija: svaki VM dobija svežu kopiju rootfs-a
        shutil.copy(BASE_ROOTFS, rootfs)
        self._inject_code(rootfs, code_path)

        # Cela konfiguracija u jednom fajlu — nema potrebe za API pozivima
        json.dump({
            "boot-source": {
                "kernel_image_path": KERNEL_IMAGE,
                "boot_args": "console=ttyS0 reboot=k panic=1 pci=off"
            },
            "drives": [{
                "drive_id": "rootfs",
                "path_on_host": rootfs,
                "is_root_device": True,
                "is_read_only": False
            }],
            # Ograničenje resursa: 1 vCPU + 128MB sprečava DoS na hostu
            "machine-config": {"vcpu_count": 1, "mem_size_mib": 128}
        }, open(config, "w"))

        # Pokretanje sa config fajlom; log ide u fajl radi skupljanja izlaza
        proc = subprocess.Popen(
            [FIRECRACKER_BIN, "--no-api", "--config-file", config],
            stdout=open(log_path, "w"), stderr=subprocess.STDOUT
        )

        self.vms[vm_id] = {
            "process": proc, "rootfs": rootfs,
            "config": config, "log": log_path, "started": time.time()
        }
        return vm_id

    def _inject_code(self, rootfs: str, task_dir: str):
        """Kopira task fajlove u /workspace, pravi run.sh i systemd servis
        koji ga pokreće po boot-u, pa gasi VM kad kod završi."""
        mnt = f"/tmp/mnt_{uuid.uuid4().hex[:8]}"
        os.makedirs(mnt, exist_ok=True)
        try:
            subprocess.run(["mount", "-o", "loop", rootfs, mnt], check=True)

            # 1. Kod u /workspace
            ws = os.path.join(mnt, "workspace")
            os.makedirs(ws, exist_ok=True)
            for name in os.listdir(task_dir):
                shutil.copy(os.path.join(task_dir, name), os.path.join(ws, name))

            # 2. run.sh — instalira requirements (ako ima) pa pokreće main.py.
            #    Sve ide na konzolu (ttyS0) da bi se videlo u logu.
            #    Na kraju gasi VM da get_output ne čeka ceo timeout.
            run_script = (
                "#!/bin/sh\n"
                "sleep 2\n"                         # sačekaj da systemd boot utihne
                "echo '===== OBLAK RUN START ====='\n"
                "cd /workspace\n"
                "if [ -f requirements.txt ]; then\n"
                "  pip install -r requirements.txt 2>&1\n"
                "fi\n"
                "python3 main.py 2>&1\n"
                "echo '===== OBLAK RUN END ====='\n"
                "sync\n"
                "poweroff -f\n"
            )
            run_path = os.path.join(ws, "run.sh")
            with open(run_path, "w") as f:
                f.write(run_script)
            os.chmod(run_path, 0o755)

            # 3. systemd servis koji pokreće run.sh po boot-u, na konzoli
            service = (
                "[Unit]\n"
                "Description=Oblak user code runner\n"
                "After=multi-user.target\n"
                "[Service]\n"
                "Type=oneshot\n"
                "ExecStart=/workspace/run.sh\n"
                "StandardOutput=tty\n"
                "StandardError=tty\n"
                "TTYPath=/dev/ttyS0\n"
                "[Install]\n"
                "WantedBy=multi-user.target\n"
            )
            svc_dir = os.path.join(mnt, "etc/systemd/system")
            os.makedirs(svc_dir, exist_ok=True)
            svc_path = os.path.join(svc_dir, "oblak-run.service")
            with open(svc_path, "w") as f:
                f.write(service)

            # 4. Aktiviraj servis (symlink u multi-user.target.wants)
            wants_dir = os.path.join(mnt, "etc/systemd/system/multi-user.target.wants")
            os.makedirs(wants_dir, exist_ok=True)
            link = os.path.join(wants_dir, "oblak-run.service")
            if not os.path.exists(link):
                os.symlink("/etc/systemd/system/oblak-run.service", link)
        finally:
            subprocess.run(["umount", mnt], check=False)
            shutil.rmtree(mnt, ignore_errors=True)

    def get_output(self, vm_id: str, timeout: int = 30) -> str:
        """Čeka da VM završi (ili timeout) i vraća SAMO korisnički izlaz
        (deo između OBLAK RUN START/END markera)."""
        vm = self.vms[vm_id]
        deadline = time.time() + timeout
        while time.time() < deadline and vm["process"].poll() is None:
            time.sleep(0.5)

        with open(vm["log"]) as f:
            full_log = f.read()

        return self._extract_user_output(full_log)

    @staticmethod
    def _extract_user_output(log: str) -> str:
        start_marker = "===== OBLAK RUN START ====="
        end_marker = "===== OBLAK RUN END ====="
        start = log.find(start_marker)
        end = log.find(end_marker)
        if start != -1 and end != -1 and end > start:
            return log[start + len(start_marker):end].strip()
        return log[-4096:]  # fallback ako markeri fale

    def stop_vm(self, vm_id: str):
        """Gasi VM i briše sve njegove fajlove."""
        vm = self.vms.pop(vm_id, None)
        if not vm:
            return
        if vm["process"].poll() is None:
            vm["process"].kill()
            vm["process"].wait(timeout=5)
        for path in (vm["rootfs"], vm["config"], vm["log"]):
            if os.path.exists(path):
                os.remove(path)

    def cleanup_stale(self, max_age: int = 30):
        """Gasi VM-ove starije od max_age sekundi."""
        now = time.time()
        for vm_id in [k for k, v in self.vms.items()
                      if now - v["started"] > max_age]:
            self.stop_vm(vm_id)