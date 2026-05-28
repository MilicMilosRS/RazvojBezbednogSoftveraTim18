#!/bin/bash
#
# Morate pokrenuti WSL (i to bas WSL2) i pokrenuti ovu skriptu
#
# setup_firecracker.sh
# Priprema Firecracker okruženje: binary, kernel i rootfs.
# Idempotentno — preskače ono što već postoji.
#
# Upotreba:
#   bash setup_firecracker.sh
#
set -euo pipefail

# --- Konfiguracija (zakucane verzije radi reproducibilnosti) ---
FC_DIR="/opt/firecracker"
ARCH="$(uname -m)"

# Firecracker binary verzija
FC_VERSION="v1.13.1"

# Zakucani URL-ovi za kernel i rootfs (datum-hash se rotira na S3, zato fiksiramo)
KERNEL_URL="https://s3.amazonaws.com/spec.ccfc.min/firecracker-ci/20260527-14108ca14ef1-0/${ARCH}/vmlinux-5.10.253"
ROOTFS_URL="https://s3.amazonaws.com/spec.ccfc.min/firecracker-ci/acpi/${ARCH}/ubuntu-22.04.ext4"

# --- Pomoćne funkcije za ispis ---
info()  { echo -e "\033[0;36mℹ️  $*\033[0m"; }
ok()    { echo -e "\033[0;32m✅ $*\033[0m"; }
warn()  { echo -e "\033[0;33m⚠️  $*\033[0m"; }
err()   { echo -e "\033[0;31m❌ $*\033[0m" >&2; }

# --- Provera arhitekture ---
if [ "$ARCH" != "x86_64" ] && [ "$ARCH" != "aarch64" ]; then
    err "Nepodržana arhitektura: $ARCH (podržano: x86_64, aarch64)"
    exit 1
fi

# --- Provera KVM-a ---
info "Proveravam KVM..."
if [ ! -e /dev/kvm ]; then
    err "/dev/kvm ne postoji. Firecracker zahteva KVM."
    err "Na WSL2 uključi nestedVirtualization=true u .wslconfig pa 'wsl --shutdown'."
    exit 1
fi
ok "KVM dostupan."

# --- Kreiranje direktorijuma ---
info "Pripremam $FC_DIR ..."
sudo mkdir -p "$FC_DIR"

# --- Instalacija Firecracker binary-ja ---
if command -v firecracker >/dev/null 2>&1; then
    ok "Firecracker već instaliran: $(firecracker --version | head -n1)"
else
    info "Preuzimam Firecracker $FC_VERSION ..."
    release_url="https://github.com/firecracker-microvm/firecracker/releases"
    tmp_dir="$(mktemp -d)"
    curl -fsSL "${release_url}/download/${FC_VERSION}/firecracker-${FC_VERSION}-${ARCH}.tgz" \
        | tar -xz -C "$tmp_dir"
    sudo mv "${tmp_dir}/release-${FC_VERSION}-${ARCH}/firecracker-${FC_VERSION}-${ARCH}" \
        /usr/bin/firecracker
    sudo chmod +x /usr/bin/firecracker
    rm -rf "$tmp_dir"
    ok "Firecracker instaliran: $(firecracker --version | head -n1)"
fi

# --- Preuzimanje kernela ---
if [ -f "${FC_DIR}/vmlinux.bin" ]; then
    ok "Kernel već postoji (preskačem)."
else
    info "Preuzimam kernel..."
    sudo curl -fsSL -o "${FC_DIR}/vmlinux.bin" "$KERNEL_URL"
    ok "Kernel preuzet."
fi

# --- Preuzimanje rootfs-a ---
if [ -f "${FC_DIR}/rootfs.ext4" ]; then
    ok "Rootfs već postoji (preskačem)."
else
    info "Preuzimam rootfs (može potrajati, par stotina MB)..."
    sudo curl -fsSL -o "${FC_DIR}/rootfs.ext4" "$ROOTFS_URL"
    ok "Rootfs preuzet."
fi

# --- Završni prikaz ---
echo
ok "Sve spremno. Sadržaj $FC_DIR:"
ls -lh "$FC_DIR"
echo
info "Test boot:"
info "  cd $FC_DIR && sudo firecracker --no-api --config-file test_config.json"