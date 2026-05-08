#!/usr/bin/env bash
# perm_audit.sh - jednostavan pregled permisija fajlova (LOTL pristup)
#
# Provere:
#  1) SUID/SGID binarni fajlovi      -> privilege escalation (GTFOBins)
#  2) World-writable fajlovi         -> svako moze da menja sadrzaj
#  3) World-writable dirovi (no +t)  -> TOCTOU / symlink napadi
#  4) Fajlovi bez vlasnika           -> ostavljen artefakt / loš cleanup
#  5) Osetljivi sistemski fajlovi    -> /etc/shadow, sudoers, ssh keys...
#  6) Writable direktorijumi u PATH  -> PATH hijacking
#
# Pokretanje: sudo ./perm_audit.sh

RED='\033[0;31m'; YEL='\033[1;33m'; GRN='\033[0;32m'; NC='\033[0m'
HITS=0
warn() { echo -e "${YEL}[!]${NC} $1"; HITS=$((HITS+1)); }
crit() { echo -e "${RED}[!!]${NC} $1"; HITS=$((HITS+1)); }
ok()   { echo -e "${GRN}[+]${NC} $1"; }
hdr()  { echo; echo "=== $1 ==="; }

[[ $EUID -ne 0 ]] && warn "Nije pokrenuto kao root – neki nalazi mogu nedostajati."

# 1) SUID/SGID
hdr "1. SUID/SGID fajlovi"
KNOWN='/(passwd|chsh|chfn|gpasswd|newgrp|sudo|su|mount|umount|ping|pkexec|crontab|at)$'
SUID=$(find / -xdev -type f \( -perm -4000 -o -perm -2000 \) 2>/dev/null | grep -Ev "$KNOWN")
if [[ -n "$SUID" ]]; then
    warn "Neuobicajeni SUID/SGID fajlovi (proveri svaki):"
    echo "$SUID" | head -20 | sed 's/^/   /'
else
    ok "Nema SUID/SGID fajlova van standardne liste."
fi

# 2) World-writable fajlovi
hdr "2. World-writable fajlovi"
WW=$(find / -xdev -type f -perm -0002 ! -path '/proc/*' ! -path '/sys/*' ! -path '/dev/*' 2>/dev/null)
if [[ -n "$WW" ]]; then
    crit "World-writable fajlovi ($(echo "$WW" | wc -l)):"
    echo "$WW" | head -20 | sed 's/^/   /'
else
    ok "Nema world-writable fajlova."
fi

# 3) World-writable direktorijumi bez sticky bita
hdr "3. World-writable dirovi bez sticky bita"
WD=$(find / -xdev -type d -perm -0002 ! -perm -1000 ! -path '/proc/*' ! -path '/sys/*' 2>/dev/null)
if [[ -n "$WD" ]]; then
    crit "Dirovi bez sticky bita ($(echo "$WD" | wc -l)):"
    echo "$WD" | head -20 | sed 's/^/   /'
else
    ok "Svi world-writable dirovi imaju sticky bit."
fi

# 4) Fajlovi bez vlasnika
hdr "4. Fajlovi bez vlasnika/grupe"
NO=$(find / -xdev \( -nouser -o -nogroup \) ! -path '/proc/*' 2>/dev/null)
if [[ -n "$NO" ]]; then
    warn "Orphaned fajlovi ($(echo "$NO" | wc -l)):"
    echo "$NO" | head -10 | sed 's/^/   /'
else
    ok "Nema orphaned fajlova."
fi

# 5) Osetljivi sistemski fajlovi
hdr "5. Osetljivi fajlovi"
declare -A FILES=(
    [/etc/passwd]=644 [/etc/shadow]=640 [/etc/group]=644
    [/etc/gshadow]=640 [/etc/sudoers]=440 [/etc/ssh/sshd_config]=644
)
for f in "${!FILES[@]}"; do
    [[ -e "$f" ]] || continue
    M=$(stat -c '%a' "$f")
    if (( 10#$M > 10#${FILES[$f]} )); then
        crit "$f ima mode $M (preporuceno: ${FILES[$f]})"
    else
        ok "$f mode=$M"
    fi
done

# SSH private kljucevi moraju biti 600
for d in /root /home/*; do
    [[ -d "$d/.ssh" ]] || continue
    for k in "$d"/.ssh/id_*; do
        [[ -f "$k" && "$k" != *.pub ]] || continue
        M=$(stat -c '%a' "$k")
        (( 10#$M > 600 )) && crit "Private key $k ima mode $M (treba 600)"
    done
done

# 6) Writable direktorijumi u PATH
hdr "6. Writable dirovi u \$PATH"
IFS=':' read -ra DIRS <<< "$PATH"
for d in "${DIRS[@]}"; do
    [[ -d "$d" ]] || continue
    M=$(stat -c '%a' "$d")
    LAST="${M: -1}"
    if [[ "$LAST" =~ [2367] ]]; then
        crit "$d je world-writable (mode=$M) – PATH hijacking rizik!"
    fi
done

# Sazetak
hdr "SAZETAK"
echo "Ukupno nalaza: $HITS"
[[ $HITS -eq 0 ]] && echo -e "${GRN}Status: OK${NC}" || echo -e "${RED}Status: proveri nalaze${NC}"
