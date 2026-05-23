#!/usr/bin/env bash
# system_audit.sh - pregled sistemske konfiguracije i bezbednosti (LOTL pristup)
#
# Provere:
#  1) Korisnici sa uid=0 (root privilegije)  -> neovlasceni root nalozi
#  2) Korisnici sa praznom lozinkom          -> otvoreni nalozi bez autentikacije
#  3) Sudo konfiguracija                     -> opasna sudo pravila (NOPASSWD, ALL)
#  4) Cron jobovi                            -> maliciozni zakazani taskovi
#  5) Pokrenuti servisi                      -> nepotrebni/sumnjivi servisi
#  6) Kernel verzija                         -> zastareo kernel sa poznatim exploitima
#  7) Neuspeli login pokusaji               -> brute force detekcija
#  8) Environment varijable                  -> sumnjive promenljive u okruzenju
#  9) Instalirani paketi sa poznatim CVE    -> zastareli softver
# 10) Bash istorija root korisnika           -> tragovi malicioznih komandi
#
# Pokretanje: sudo ./system_audit.sh

RED='\033[0;31m'; YEL='\033[1;33m'; GRN='\033[0;32m'; NC='\033[0m'
HITS=0
warn() { echo -e "${YEL}[!]${NC} $1"; HITS=$((HITS+1)); }
crit() { echo -e "${RED}[!!]${NC} $1"; HITS=$((HITS+1)); }
ok()   { echo -e "${GRN}[+]${NC} $1"; }
hdr()  { echo; echo "=== $1 ==="; }

[[ $EUID -ne 0 ]] && warn "Nije pokrenuto kao root – neki nalazi mogu nedostajati."

# 1) Korisnici sa uid=0
hdr "1. Korisnici sa root privilegijama (uid=0)"
ROOT_USERS=$(awk -F: '($3 == 0) { print $1 }' /etc/passwd 2>/dev/null)
COUNT=$(echo "$ROOT_USERS" | grep -c .)
if [ "$COUNT" -gt 1 ]; then
    crit "Pronadjeni korisnici sa uid=0 pored root-a:"
    echo "$ROOT_USERS" | grep -v '^root$' | sed 's/^/   /'
elif [ "$COUNT" -eq 1 ]; then
    ok "Samo root ima uid=0."
else
    ok "Nema neocekivanih korisnika sa uid=0."
fi

# 2) Korisnici sa praznom lozinkom
hdr "2. Korisnici sa praznom lozinkom"
EMPTY=$(awk -F: '($2 == "" || $2 == "!!" || $2 == "!") { print $1 }' /etc/shadow 2>/dev/null)
if [ -n "$EMPTY" ]; then
    crit "Korisnici bez lozinke (moguc direktan pristup):"
    echo "$EMPTY" | sed 's/^/   /'
else
    ok "Svi aktivni korisnici imaju postavljenu lozinku."
fi

# 3) Sudo konfiguracija
hdr "3. Sudo konfiguracija (privilegovana pravila)"
if [ -f /etc/sudoers ]; then
    NOPASSWD=$(grep -E 'NOPASSWD' /etc/sudoers /etc/sudoers.d/* 2>/dev/null | grep -v '^#')
    if [ -n "$NOPASSWD" ]; then
        crit "Pronadjena NOPASSWD sudo pravila (komande bez lozinke):"
        echo "$NOPASSWD" | sed 's/^/   /'
    else
        ok "Nema NOPASSWD sudo pravila."
    fi

    ALL_ALL=$(grep -E 'ALL=\(ALL\)' /etc/sudoers /etc/sudoers.d/* 2>/dev/null | grep -v '^#')
    if [ -n "$ALL_ALL" ]; then
        warn "Korisnici sa neogranicenim sudo pristupom (ALL=(ALL)):"
        echo "$ALL_ALL" | sed 's/^/   /'
    else
        ok "Nema korisnika sa neogranicenim sudo pristupom."
    fi
else
    warn "/etc/sudoers ne postoji ili nije citljiv."
fi

# 4) Cron jobovi
hdr "4. Cron jobovi (zakazani taskovi)"
CRON_DIRS="/etc/cron.d /etc/cron.daily /etc/cron.hourly /etc/cron.weekly /etc/cron.monthly"
CRON_FOUND=0
for dir in $CRON_DIRS; do
    if [ -d "$dir" ]; then
        FILES=$(ls "$dir" 2>/dev/null)
        if [ -n "$FILES" ]; then
            warn "Cron jobovi u $dir:"
            ls -la "$dir" | sed 's/^/   /'
            CRON_FOUND=1
        fi
    fi
done

# Root crontab
ROOT_CRON=$(crontab -l -u root 2>/dev/null)
if [ -n "$ROOT_CRON" ]; then
    crit "Root crontab nije prazan:"
    echo "$ROOT_CRON" | grep -v '^#' | sed 's/^/   /'
    CRON_FOUND=1
fi

[ "$CRON_FOUND" -eq 0 ] && ok "Nisu pronadjeni sumnjivi cron jobovi."

# 5) Pokrenuti servisi
hdr "5. Pokrenuti sistemski servisi"
if command -v systemctl >/dev/null; then
    SERVICES=$(systemctl list-units --type=service --state=running 2>/dev/null | grep '\.service' | awk '{print $1}')
    COUNT=$(echo "$SERVICES" | grep -c .)
    echo "   Aktivnih servisa: $COUNT"
    SUSPICIOUS=$(echo "$SERVICES" | grep -Ei 'nc|ncat|netcat|backdoor|shell|miner|crypto' 2>/dev/null)
    if [ -n "$SUSPICIOUS" ]; then
        crit "Sumnjivi servisi:"
        echo "$SUSPICIOUS" | sed 's/^/   /'
    else
        ok "Nisu pronadjeni ocigledni sumnjivi servisi."
    fi
else
    warn "systemctl nije dostupan."
fi

# 6) Kernel verzija
hdr "6. Kernel verzija"
KERNEL=$(uname -r)
echo "   Trenutna verzija kernela: $KERNEL"
MAJOR=$(echo "$KERNEL" | cut -d. -f1)
MINOR=$(echo "$KERNEL" | cut -d. -f2)
if [ "$MAJOR" -lt 5 ]; then
    warn "Kernel $KERNEL je potencijalno zastareo. Preporucuje se azuriranje na noviju verziju."
else
    ok "Kernel $KERNEL je relativno azuran."
fi

# 7) Neuspeli login pokusaji
hdr "7. Neuspeli login pokusaji (brute force detekcija)"
if [ -f /var/log/auth.log ]; then
    FAILED=$(grep "Failed password" /var/log/auth.log 2>/dev/null | tail -20)
    COUNT=$(grep -c "Failed password" /var/log/auth.log 2>/dev/null)
    if [ "$COUNT" -gt 10 ]; then
        crit "Pronadjeno $COUNT neuspelih pokusaja prijave (moguc brute force napad):"
        echo "$FAILED" | tail -5 | sed 's/^/   /'
    elif [ "$COUNT" -gt 0 ]; then
        warn "Pronadjeno $COUNT neuspelih pokusaja prijave."
    else
        ok "Nema zabelezenih neuspelih pokusaja prijave."
    fi
elif [ -f /var/log/secure ]; then
    COUNT=$(grep -c "Failed password" /var/log/secure 2>/dev/null)
    [ "$COUNT" -gt 10 ] && crit "Pronadjeno $COUNT neuspelih pokusaja (moguc brute force)." \
                         || ok "Manji broj neuspelih pokusaja prijave: $COUNT"
else
    warn "Log fajl za autentikaciju nije pronadjen (/var/log/auth.log ili /var/log/secure)."
fi

# 8) Environment varijable
hdr "8. Sumnjive environment varijable"
SUSPICIOUS_ENV=$(env 2>/dev/null | grep -Ei '(LD_PRELOAD|LD_LIBRARY_PATH|PYTHONPATH|PERL5LIB|RUBYLIB)' | grep -v '^#')
if [ -n "$SUSPICIOUS_ENV" ]; then
    crit "Pronadjene potencijalno maliciozne environment varijable:"
    echo "$SUSPICIOUS_ENV" | sed 's/^/   /'
else
    ok "Nisu pronadjene sumnjive environment varijable."
fi

# LD_PRELOAD posebna provera
if [ -n "$LD_PRELOAD" ]; then
    crit "LD_PRELOAD je postavljen: $LD_PRELOAD (moguce library injection!)"
fi

# 9) Zastareli paketi
hdr "9. Zastareli paketi (bezbednosna azuriranja)"
if command -v apt >/dev/null; then
    apt-get update -qq 2>/dev/null
    UPGRADABLE=$(apt list --upgradable 2>/dev/null | grep -v "^Listing" | wc -l)
    SECURITY=$(apt list --upgradable 2>/dev/null | grep -i security | wc -l)
    if [ "$SECURITY" -gt 0 ]; then
        crit "Dostupno je $SECURITY bezbednosnih azuriranja!"
        apt list --upgradable 2>/dev/null | grep -i security | head -10 | sed 's/^/   /'
    elif [ "$UPGRADABLE" -gt 0 ]; then
        warn "Dostupno je $UPGRADABLE azuriranja paketa (pokrenuti: apt upgrade)."
    else
        ok "Svi paketi su azurni."
    fi
elif command -v yum >/dev/null; then
    UPDATES=$(yum check-update --security 2>/dev/null | grep -c "^[A-Za-z]")
    [ "$UPDATES" -gt 0 ] && crit "$UPDATES bezbednosnih azuriranja dostupno." || ok "Svi paketi su azurni."
else
    warn "Menadzer paketa nije prepoznat (nije apt/yum)."
fi

# 10) Bash istorija root korisnika
hdr "10. Bash istorija root korisnika"
HIST_FILE="/root/.bash_history"
if [ -f "$HIST_FILE" ]; then
    COUNT=$(wc -l < "$HIST_FILE")
    echo "   Broj komandi u istoriji: $COUNT"
    SUSPICIOUS_CMDS=$(grep -Ei '(wget|curl|chmod \+x|nc -|ncat|base64|/dev/tcp|python.*http|perl -e|ruby -e|bash -i)' "$HIST_FILE" 2>/dev/null)
    if [ -n "$SUSPICIOUS_CMDS" ]; then
        crit "Sumnjive komande u root bash istoriji:"
        echo "$SUSPICIOUS_CMDS" | head -10 | sed 's/^/   /'
    else
        ok "Nisu pronadjene ocigledne sumnjive komande u istoriji."
    fi
else
    warn "/root/.bash_history ne postoji ili nije citljiv."
fi

# Sazetak
hdr "SAZETAK"
echo "Ukupno nalaza: $HITS"
[[ $HITS -eq 0 ]] && echo -e "${GRN}Status: OK${NC}" || echo -e "${RED}Status: proveri nalaze${NC}"
