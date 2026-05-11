#!/usr/bin/env bash
# network_audit.sh - pregled mrezne konfiguracije i bezbednosti (LOTL pristup)
#
# Provere:
#  1) Firewall pravila (IPv4)        -> zastita ulaznog/izlaznog saobracaja
#  2) IPv6 status                    -> sprecavanje IPv6 bypass napada
#  3) Otvoreni portovi               -> nepotrebni servisi izlozeni na mrezi
#  4) IP Forwarding                  -> zloupotreba rutiranja (Pivot/Man-in-the-Middle)
#  5) TCP/IP Hardening               -> zastita od DoS i MITM napada (SYN cookies, ICMP redir)
#  6) Promiskuitetni mod             -> detekcija mreznog snifovanja
#  7) Lokalni DNS (/etc/hosts)       -> preusmjeravanje saobracaja na maliciozne adrese
#  8) Logovanje sumnjivih paketa     -> detekcija IP spoofinga (martian paketi)
#  9) ICMP Broadcast i Source Route  -> zastita od Smurf DDoS napada i manipulacije rutingom
# 10) TCP Wrappers (hosts.deny)      -> dodatni sloj blokiranja nezeljenog saobracaja
#
# Pokretanje: sudo ./network_audit.sh

RED='\033[0;31m'; YEL='\033[1;33m'; GRN='\033[0;32m'; NC='\033[0m'
HITS=0
warn() { echo -e "${YEL}[!]${NC} $1"; HITS=$((HITS+1)); }
crit() { echo -e "${RED}[!!]${NC} $1"; HITS=$((HITS+1)); }
ok()   { echo -e "${GRN}[+]${NC} $1"; }
hdr()  { echo; echo "=== $1 ==="; }

[[ $EUID -ne 0 ]] && warn "Nije pokrenuto kao root, neki nalazi mogu nedostajati ili status firewall-a nece biti vidljiv."

# 1) Firewall pravila
hdr "1. Firewall pravila (IPv4 iptables)"
if command -v iptables >/dev/null; then
    RULES=$(iptables -L INPUT -v -n 2>/dev/null | wc -l)
    if [ "$RULES" -le 2 ]; then
        warn "Nema restriktivnih iptables pravila za INPUT lanac (otvoren saobracaj)."
    else
        ok "iptables pravila postoje (Broj linija za INPUT: $RULES)."
    fi
else
    warn "Komanda iptables nije pronadjena na sistemu."
fi

# 2) IPv6 status
hdr "2. IPv6 Status"
IPV6_STATUS=$(cat /proc/sys/net/ipv6/conf/all/disable_ipv6 2>/dev/null)
if [ "$IPV6_STATUS" == "1" ]; then
    ok "IPv6 je sistemski onemogucen."
else
    warn "IPv6 je omogucen. Potrebno je provjeriti ip6tables pravila da se sprijeci neovlascen pristup."
fi

# 3) Otvoreni portovi
hdr "3. Otvoreni portovi i aktivni servisi"
echo "Servisi koji osluskuju mrezu (LISTEN):"
if command -v ss >/dev/null; then
    ss -tulwn | grep LISTEN | sed 's/^/   /' || warn "Nema otvorenih portova ili nedostaju privilegije."
else
    netstat -tulpn | grep LISTEN | sed 's/^/   /' || warn "Nema otvorenih portova ili nedostaju privilegije."
fi

# 4) IP Forwarding
hdr "4. IP Forwarding (Rutiranje)"
FORWARD=$(sysctl -n net.ipv4.ip_forward 2>/dev/null || cat /proc/sys/net/ipv4/ip_forward 2>/dev/null)
if [ "$FORWARD" == "1" ]; then
    crit "IP Forwarding je omogucen! Server moze da rutira tudji saobracaj."
else
    ok "IP Forwarding je onemogucen."
fi

# 5) TCP/IP Hardening
hdr "5. TCP/IP Hardening (Anti-Spoofing i DoS zastita)"
SYNC=$(sysctl -n net.ipv4.tcp_syncookies 2>/dev/null || cat /proc/sys/net/ipv4/tcp_syncookies 2>/dev/null)
if [ "$SYNC" == "1" ]; then
    ok "TCP SYN cookies su omoguceni (zastita od SYN Flood DoS napada)."
else
    warn "TCP SYN cookies nisu omoguceni."
fi

REDIR=$(sysctl -n net.ipv4.conf.all.accept_redirects 2>/dev/null || cat /proc/sys/net/ipv4/conf/all/accept_redirects 2>/dev/null)
if [ "$REDIR" == "0" ]; then
    ok "ICMP redirects su onemoguceni (zastita od MITM napada)."
else
    warn "Sistem prihvata ICMP redirects (rizik od neovlascene izmjene ruting tabele)."
fi

# 6) Promiskuitetni mod
hdr "6. Promiskuitetni mod (Mrezno snifovanje)"
if ip link | grep -q PROMISC; then
    crit "Pronadjen je mrezni interfejs u PROMISC modu! Moguce neovlasceno snifovanje saobracaja."
    ip link | grep PROMISC | sed 's/^/   /'
else
    ok "Nijedan mrezni interfejs ne snifuje tudji saobracaj (nije u PROMISC modu)."
fi

# 7) Sumnjivi unosi u /etc/hosts
hdr "7. Sumnjivi unosi u /etc/hosts (Lokalni DNS)"
HOSTS_MOD=$(grep -vE '^127\.|^::1|^#|^$' /etc/hosts 2>/dev/null)
if [ -n "$HOSTS_MOD" ]; then
    warn "Pronadjeni su nestandardni unosi u /etc/hosts. Provjeriti da li su legitimni:"
    echo "$HOSTS_MOD" | sed 's/^/   /'
else
    ok "/etc/hosts fajl deluje cisto (sadrzi samo standardne lokalne adrese)."
fi

# 8) Logovanje sumnjivih paketa (Martians)
hdr "8. Logovanje sumnjivih paketa (Martian logging)"
MARTIANS=$(sysctl -n net.ipv4.conf.all.log_martians 2>/dev/null || cat /proc/sys/net/ipv4/conf/all/log_martians 2>/dev/null)
if [ "$MARTIANS" == "1" ]; then
    ok "Logovanje 'martian' paketa je omoguceno."
else
    warn "Logovanje 'martian' paketa nije omoguceno (preporucuje se za detekciju IP spoofinga)."
fi

# 9) ICMP Broadcast (Smurf napadi) i Source Routing
hdr "9. ICMP Broadcast i Source Routing"
BCAST=$(sysctl -n net.ipv4.icmp_echo_ignore_broadcasts 2>/dev/null || cat /proc/sys/net/ipv4/icmp_echo_ignore_broadcasts 2>/dev/null)
if [ "$BCAST" == "1" ]; then
    ok "ICMP echo na broadcast je ignorisan (zastita od Smurf napada)."
else
    warn "Sistem odgovara na ICMP broadcast pingove."
fi

SROUTE=$(sysctl -n net.ipv4.conf.all.accept_source_route 2>/dev/null || cat /proc/sys/net/ipv4/conf/all/accept_source_route 2>/dev/null)
if [ "$SROUTE" == "0" ]; then
    ok "Source routing je onemogucen."
else
    warn "Source routing je omogucen (potencijalni rizik od manipulacije rutingom od strane napadaca)."
fi

# 10) TCP Wrappers (hosts.allow / hosts.deny)
hdr "10. TCP Wrappers (Legacy mrezna zastita)"
if [ -s /etc/hosts.deny ]; then
    ok "/etc/hosts.deny nije prazan (postoje definisane restrikcije)."
else
    warn "/etc/hosts.deny je prazan ili ne postoji (nema globalne TCP wrapper zabrane)."
fi

echo
echo -e "=== Ukupno upozorenja/kriticnih nalaza: ${YEL}${HITS}${NC} ==="