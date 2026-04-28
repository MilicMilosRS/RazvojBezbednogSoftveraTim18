## 1. Analiza klase napada: Authentication

### Objašnjenje klase napada
Ranjivosti autentifikacije nastaju kada veb aplikacija neadekvatno potvrđuje identitet korisnika koji pokušava da pristupi zaštićenom delu sistema. Ovi propusti omogućavaju napadačima da zaobiđu sigurnosne provere, preuzmu tuđe naloge (Account Takeover) ili vrše automatizovane napade radi pogađanja kredencijala.

### Uticaj (Impact)
Uspešno iskorišćavanje ove klase ranjivosti može imati katastrofalne posledice:
* **Krađa podataka:** Pristup osetljivim informacijama korisnika (podaci o karticama, privatne poruke).
* **Krađa identiteta:** Napadač može vršiti akcije u ime legitimnog korisnika.
* **Administratorski pristup:** Ukoliko je kompromitovan privilegovani nalog, napadač može preuzeti kontrolu nad celim serverom ili bazom podataka.

### Uzrok ranjivosti (Root Cause)
Glavni razlozi za uspeh ovih napada su:
1. **Nedostatak Rate Limiting-a:** Server dozvoljava neograničen broj pokušaja prijave u kratkom vremenskom roku.
2. **Username Enumeration:** Aplikacija otkriva da li korisničko ime postoji kroz različite poruke o grešci ili suptilne razlike u HTTP odgovorima (npr. različita dužina odgovora).
3. **Slaba polisa lozinki:** Dozvoljavanje korišćenja lozinki koje se nalaze na listama najčešće korišćenih.

### Kontramere (Defenses)
Kako bi se sprečili ovi napadi, potrebno je implementirati sledeće mehanizme:
* **Generički odgovori:** Bez obzira na to da li je pogrešan username ili password, aplikacija uvek treba da ispiše istu poruku: "Invalid username or password".
* **Account Lockout:** Privremeno zaključavanje naloga nakon određenog broja neuspelih pokušaja (npr. 5 pokušaja).
* **Multi-Factor Authentication (MFA):** Uvođenje drugog faktora provere (SMS kod, aplikacija) koji onemogućava pristup čak i ako je lozinka pogodjena.
* **CAPTCHA:** Zahtevanje od korisnika da reši vizuelni test kako bi se sprečili automatizovani alati (poput Burp Intruder-a).

---

## Zadatak 1: Username enumeration via different responses
**Nivo:** Apprentice (Zeleni)

### Opis zadatka
Cilj zadatka je bio otkriti validno korisničko ime iz ponuđene liste na osnovu razlika u odgovorima servera, a zatim identifikovati lozinku za tog korisnika.

### Writeup (Koraci rešavanja)

#### Korak 1: Presretanje zahteva
Prvi korak je bio pokretanje Burp Suite Proxy-ja i hvatanje `POST /login` zahteva koji šalje podatke formi za prijavu. Ovaj zahtev nam služi kao osnova za dalji napad.

![Screenshot 1![alt text](login-1-1.jpg) - HTTP History](./login-1.jpg)
*(Ovde ubaci sliku gde se vidi POST /login u HTTP History tabu)*

#### Korak 2: Konfiguracija meta napada (Positions)
Zahtev je prosleđen u alat **Intruder**. Korišćen je tip napada **Sniper**. Prvo smo odredili polje `username` kao metu za "enumeration" (pogađanje korisničkog imena).

![Screenshot 2 - Intruder Positions](./login2.jpg)
*(Ovde ubaci sliku gde se vidi username=§test§)*

#### Korak 3: Identifikacija korisničkog imena
Učitana je lista *Candidate usernames* u Payloads tab. Nakon pokretanja napada, analizom rezultata primećeno je da korisnik `ajax` vraća odgovor čija je dužina (**Length**) drugačija od svih ostalih.

![Screenshot 3 - Username Results](./login3-final.jpg)
*(OVDE UBACI SLIKU na kojoj si sortirala Length i gde se vidi da ajax odskače)*

#### Korak 4: Brute-force lozinke
Kada smo potvrdili da korisnik `ajax` postoji, vratili smo se na podešavanja i fiksirali username, dok smo polje `password` postavili kao novu metu. Korišćena je lista *Candidate passwords*. Za lozinku `ranger`, server je vratio statusni kod **302**.

![Screenshot 4 - Password Results](./login4-pass-final.jpg)
*(Ovde ubaci sliku gde se vidi status 302 za lozinku ranger)*

#### Korak 5: Potvrda rešenja
Unosom kredencijala `ajax:ranger` u formu za prijavu, dobijen je pristup nalogu i laboratorija je označena kao uspešno rešena.

![Screenshot 5 - Lab Solved](./solved1-lab.jpg)
*(Ovde ubaci sliku Congratulations, you solved the lab)*

## Zadatak 2: 2FA simple bypass
**Nivo:** Apprentice (Zeleni)

### Opis zadatka
U ovom zadatku cilj je bio zaobići dvofaktorsku autentifikaciju (2FA) korisnika `carlos`. Ranjivost se ogleda u lošoj logici aplikacije koja dozvoljava pristup korisničkom panelu odmah nakon unosa ispravne lozinke, bez obzira na to da li je unet validan 2FA kod.

### Writeup (Koraci rešavanja)

#### Korak 1: Analiza legitimnog procesa prijave
Prvo sam koristila sopstvene kredencijale (`wiener:peter`) kako bih mapirala korake. Primetila sam da nakon unosa lozinke, URL browsera postaje `/login2`, gde se od korisnika očekuje unos četvorocifrenog koda.

#### Korak 2: Pokretanje napada na nalog žrtve
Ulogovala sam se kao korisnik `carlos` koristeći lozinku `montoya`. Aplikacija je prihvatila lozinku i preusmerila me na stranicu za unos drugog faktora (2FA).

![Screenshot 1 - Carlos 2FA zahtev](./lab2-carlos.jpg)
*Slika prikazuje polje za unos koda za korisnika Carlos.*

#### Korak 3: Manipulacija URL-om (Bypass tehnika)
Pretpostavka je bila da je sesija za korisnika već kreirana u bazi nakon prvog koraka prijave. Umesto unosa koda, u adresnoj traci browsera sam ručno promenila URL sa `/login2` na `/my-account`.

![Screenshot 2 - URL Manipulacija](./changing-url.jpg)
*(Napomena: Ovde ubaci skrinšot gde se vidi kako u address bar-u pišeš /my-account)*

#### Korak 4: Uspešan pristup profilu
Nakon pritiska na taster Enter, aplikacija me je direktno pustila na Carlosov profil, ignorišući potrebu za 2FA kodom. Laboratorija je time uspešno rešena.

![Screenshot 3 - Lab Solved](./lab2-solved.jpg)
*Potvrda o uspešnom pristupu nalogu korisnika Carlos i rešenom izazovu.*

---

## Analiza ranjivosti za Zadatak 2

### Koje ranjivosti su dozvolile da napad uspe?
Glavna ranjivost je **Broken Authentication (Logic Flaw)**. Aplikacija prati dvostepeni proces, ali ne održava "privremeno" stanje sesije. Čim je lozinka ispravna, korisniku se dodeljuje punopravni sesioni token, a stranica `/login2` služi samo kao vizuelna prepreka koja se lako zaobilazi direktnim pristupom krajnjem URL-u.

### Kontramere (Defenses)
Kako bi se sprečio ovaj tip zaobilaženja, potrebno je:
1. **Partial Session State:** Korisnik ne sme dobiti puni pristup (session cookie) dok se ne potvrde svi faktori autentifikacije. Sesija treba da bude u stanju "pending" dok se 2FA ne potvrdi.
2. **Access Control Check:** Svaka stranica (poput `/my-account`) mora da proveri da li je korisnik prošao kompletan proces prijave pre nego što mu se servira sadržaj.
3. **Redirekcija:** Ako korisnik pokuša da pristupi `/my-account` a nije uneo 2FA, server ga mora automatski vratiti na `/login2`.

## Zadatak 3: Username enumeration via subtly different responses
**Nivo:** Practitioner (Plavi)

### Opis zadatka
Cilj ovog zadatka bio je otkriti validno korisničko ime identifikacijom ekstremno suptilnih razlika u odgovorima servera koje je ljudskom oku skoro nemoguće primetiti bez pomoći alata. Fokus je bio na preciznoj analizi poruka o grešci, a nakon otkrivanja korisnika, cilj je bio identifikovati lozinku putem brute-force napada.

### Writeup (Koraci rešavanja)

#### Korak 1: Mapiranje suptilnih razlika (Grep - Extract)
Pošto su poruke o grešci naizgled bile identične ("Invalid username or password."), koristili smo **Grep - Extract** funkciju u **Intruder** podešavanjima. Ova funkcija omogućava Burp-u da iz svakog HTTP odgovora "izvuče" tačan tekst poruke kako bismo lakše uočili razlike.

![Screenshot 1 - Grep Extract Podešavanje](./jel%20ovo%20ok.jpg)
*Slika prikazuje proces definisanja ekstrakcije teksta unutar HTML-a kako bi se pratila svaka varijacija u poruci.*

#### Korak 2: Identifikacija korisničkog imena (Enumeration)
Učitali smo kompletnu listu *Candidate usernames* i pokrenuli **Sniper** napad. Analizom nove kolone koju je kreirao Grep - Extract, otkrili smo da korisnik `antivirus` (zahtev broj 66) vraća poruku koja se razlikuje za samo jedan karakter – **nedostaje tačka na kraju rečenice**.

![Screenshot 2 - Username Results](./3-final-antivirus.jpg)
*Rezultati napada: Red 66 za payload 'antivirus' jasno pokazuje odstupanje u tekstu poruke o grešci.*

#### Korak 3: Brute-force lozinke
Nakon što smo potvrdili da korisnik `antivirus` postoji, vratili smo se na **Positions** tab, fiksirali username na `antivirus`, a kao metu postavili polje `password`. Učitali smo listu *Candidate passwords*. Za lozinku `mustang`, server je vratio statusni kod **302 Found**.

![Screenshot 3 - Password Results](./lab3-found-pass.jpg)
*Rezultati napada na lozinku: Status 302 potvrđuje da je 'mustang' ispravna lozinka.*

#### Korak 4: Potvrda rešenja
Korišćenjem pronađenih kredencijala (`antivirus:mustang`) na stranici za prijavu, uspešno smo pristupili korisničkom panelu i rešili laboratoriju.

![Screenshot 4 - Lab Solved](./3-solved-antivirus.jpg)
*Potvrda o uspešno rešenom zadatku i pristupu nalogu korisnika antivirus.*

---

## Analiza ranjivosti za Zadatak 3

### Koje ranjivosti su dozvolile da napad uspe?
Glavna ranjivost u ovom zadatku je **Information Exposure through Subtle Response Differences** (Otkrivanje informacija kroz suptilne razlike u odgovoru). 
* **Logička greška:** Iako je aplikacija dizajnirana da daje generičku poruku, programerska greška (nedostatak tačke u jednom od uslovnih odgovora u kodu) omogućila je automatizovano razlikovanje postojećeg korisnika od nepostojećeg.
* **Nedostatak zaštite od nabrajanja:** Aplikacija ne koristi rate-limiting ili privremenu blokadu, što dozvoljava napadaču da testira stotine imena bez ometanja.

### Kontramere (Defenses)
* **Strogo uniformni odgovori:** Sve poruke o grešci u procesu autentifikacije moraju biti identične do poslednjeg bajta. Najbolja praksa je korišćenje jedne globalne konstante za poruku o grešci.
* **Sanitizacija odgovora:** Pre slanja odgovora klijentu, aplikacija treba da osigura da nema varijacija u whitespace-u ili interpunkciji koje bi mogle odati stanje na backendu.
* **Rate Limiting:** Implementacija mehanizma koji ograničava broj pokušaja prijave po IP adresi ili nalogu značajno otežava automatizovanu enumeraciju.
* **Monitoring:** Praćenje anomalija u saobraćaju (veliki broj 200 OK odgovora sa različitim payloadima u kratkom roku) može pomoći u detekciji napada u realnom vremenu.

## Zadatak 4: Broken brute-force protection, IP block
**Nivo:** Practitioner (Plavi)

### Opis zadatka
Cilj ovog zadatka bio je zaobići zaštitu od brute-force napada koja se zasniva na blokiranju IP adrese nakon tri neuspešna pokušaja. Specifičnost ove laboratorije je logički propust gde se brojač neuspelih pokušaja za ciljanog korisnika (`carlos`) resetuje čim se bilo koji drugi korisnik (u ovom slučaju naš nalog `wiener`) uspešno uloguje.

### Writeup (Koraci rešavanja)

#### Korak 1: Postavljanje "cik-cak" strategije
Kako bismo sprečili blokadu, morali smo da kreiramo specifičan redosled zahteva: jedan pokušaj za korisnika `carlos`, a zatim odmah jedan ispravan login za `wiener` kako bi se brojač na serveru vratio na nulu. Za ovo smo koristili **Pitchfork** tip napada u Intruderu.

![Screenshot 1 - Podešavanje korisničkih imena](./4-username.jpg)
*Payload 1: Lista u kojoj se naizmenično smenjuju wiener (za reset brojača) i carlos (meta).*

#### Korak 2: Mapiranje lozinki
Na isti način, druga lista payloada pratila je prvu: ispravna lozinka za naš nalog (`peter`), pa potencijalna lozinka za Carlosa iz ponuđene liste.

![Screenshot 2 - Podešavanje lozinki](./4-password.jpg)
*Payload 2: Sinhronizovana lista lozinki gde svaka druga stavka odgovara našem ispravnom kredencijalu.*

#### Korak 3: Konfiguracija Resource Pool-a
Ovo je bio kritičan korak. Pošto server prati redosled pokušaja, morali smo osigurati da Burp Suite šalje samo **jedan po jedan** zahtev. Da su zahtevi išli paralelno, redosled bi se pomešao i IP bi bio blokiran.

![Screenshot 3 - Limitiranje istovremenih zahteva](./4-pool.jpg)
*Podešavanje Resource Pool-a na maksimalno 1 istovremeni zahtev (Maximum concurrent requests: 1).*

#### Korak 4: Identifikacija lozinke
Pokretanjem napada, pratili smo HTTP statuse. Svi zahtevi za korisnika `wiener` su vraćali **302**, dok su neuspešni pokušaji za Carlosa vraćali **200**. U 28. redu, korisnik `carlos` je vratio status **302**, što je označilo pronalazak lozinke.

![Screenshot 4 - Uspešan pronalazak lozinke](./4-final-pass.jpg)
*Rezultat napada: Lozinka 'football' je uspešno ulogovala korisnika carlos.*

#### Korak 5: Potvrda rešenja
Unosom kredencijala `carlos:football` direktno u browseru, dobili smo pristup administratorskom panelu i laboratorija je uspešno rešena.

![Screenshot 5 - Lab Solved](./4-solved-ip.jpg)
*Prikaz uspešno rešenog zadatka nakon prijave na Carlosov nalog.*

---

## Analiza ranjivosti za Zadatak 4

### Koje ranjivosti su dozvolile da napad uspe?
Glavna ranjivost je **Logic Flaw in Brute-force Protection** (Logički propust u zaštiti od grubih napada). 
* **Globalni ili slabo izolovan brojač:** Server prati neuspešne pokušaje po IP adresi, ali dozvoljava da jedan uspešan login bilo kog korisnika sa te adrese "obriše grehe" prethodnih neuspelih pokušaja.
* **Nepravilna implementacija Rate Limiting-a:** Umesto da se blokira pristup nakon određenog broja grešaka bez obzira na usputne uspehe, sistem je previše "popustljiv" čim se uoči legitimna aktivnost.

### Kontramere (Defenses)
* **Per-user Lockout:** Brojač neuspešnih pokušaja treba da bude vezan za specifičan nalog, a ne samo za IP adresu ili globalnu sesiju.
* **Progresivna blokada:** Uvođenje eksponencijalnog čekanja (npr. 1 minut nakon 3 greške, 5 minuta nakon 5 grešaka) značajno usporava brute-force napade bez potrebe za potpunim blokiranjem IP-a.
* **Neresetujući brojači:** Uspešan login drugog korisnika nikada ne bi smeo da resetuje brojač neuspelih pokušaja za drugog, sumnjivog korisnika.


## Zadatak 5: Password brute-force via password change
**Nivo:** Practitioner (Plavi)

### Opis zadatka
Cilj ovog zadatka bio je preuzimanje naloga korisnika `carlos` korišćenjem logičkog propusta u funkciji za promenu lozinke. Umesto pogađanja lozinke na standardnoj login stranici (gde obično postoje strogi mehanizmi zaštite poput blokiranja IP adrese), iskoristili smo asimetriju u porukama o grešci pri promeni lozinke kako bismo potvrdili ispravnost trenutne lozinke žrtve.

### Writeup (Koraci rešavanja)

#### Korak 1: Detekcija logičke greške (Oracle)
Prvi korak je bio mapiranje ponašanja servera na sopstvenom nalogu (`wiener:peter`). Utvrđeno je da server validira podatke specifičnim redosledom. Ukoliko se unese ispravna trenutna lozinka, ali se nove lozinke ne poklapaju, server vraća poruku **"New passwords do not match"**. Ukoliko je trenutna lozinka pogrešna, poruka je **"Current password is incorrect"**. Ova razlika nam služi kao "Oracle" za potvrdu tačnosti lozinke.

![Screenshot Fraza](./auth5-1-0.jpg)

![Screenshot 1 - Interceptovani zahtev](./auth5-1.jpg)
*Slika 1: Presretanje POST zahteva za promenu lozinke koji služi kao baza za napad.*

#### Korak 2: Konfiguracija Intruder napada
Zahtev sam prosledila u Intruder alat. Korisničko ime sam fiksirala na `carlos`, a polje `current-password` sam postavila kao metu napada. Polja za novu lozinku (`new-password-1` i `new-password-2`) sam popunila različitim vrednostima kako bih namerno izazvala ciljanu poruku o nepoklapanju ukoliko pogodim lozinku.

![Screenshot 2 - Intruder Positions](./auth5-pre4.jpg)
![Screenshot Fraza](./auth5-posle4.jpg)
*Slika 2: Postavka meta u Intruderu sa fokusom na polje trenutne lozinke žrtve.*

#### Korak 3: Automatizacija pretrage (Grep - Match)
Da bih identifikovala ispravnu lozinku iz liste kandidata, koristila sam opciju **Grep - Match**. Definisala sam da Burp Suite prati pojavljivanje fraze "New passwords do not match" u odgovorima servera.

![Screenshot Fraza](./auth5-3.jpg)

![Screenshot 3 - Grep Match podešavanje](./auth5-grepmatch.jpg)
*Slika 3: Konfiguracija automatskog filtriranja rezultata na osnovu poruke o grešci.*

#### Korak 4: Identifikacija lozinke i provala u nalog
Nakon pokretanja napada, kolona Grep filtera je pokazala pogodak za lozinku **`aaaaaa`**. Ovo je bio jedini zahtev koji je prošao prvu barijeru validacije. Upotrebom ovih kredencijala, uspešno sam se prijavila na Carlosov nalog.

![Screenshot 4 - Rezultati napada](./auth5-passfound.jpg)
*Slika 4: Rezultat napada gde se jasno vidi da je lozinka 'aaaaaa' jedina aktivirala traženu poruku.*

#### Korak 5: Potvrda rešenja
Pristupom stranici "My account" kao korisnik `carlos`, laboratorija je označena kao uspešno rešena.

![Screenshot 5 - Lab Solved](./auth5-finished.jpg)
*Slika 5: Potvrda o uspešno završenom izazovu.*

---

## Analiza ranjivosti za Zadatak 5

### Koje ranjivosti su dozvolile da napad uspe?
1. **Insecure Validation Sequence:** Server vrši validaciju korak-po-korak i šalje različite odgovore za svaki neuspešan korak. Ovo odaje informaciju o stanju baze (ispravnost lozinke) pre nego što se cela operacija završi.
2. **Missing Rate Limiting on Secondary Endpoints:** Dok login stranice često imaju brute-force zaštitu, stranice za promenu lozinke ili profila su često zapostavljene, što omogućava hiljade pokušaja bez blokade.
3. **Logic Flaw:** Programerska logika pretpostavlja da će promenu lozinke vršiti samo ulogovan korisnik za svoj nalog, zanemarujući mogućnost da napadač može manipulisati `username` parametrom u samom zahtevu.

### Kontramere (Defenses)
* **Atomic Validation:** Sve provere (stara lozinka, poklapanje novih lozinki, kompleksnost) treba vršiti istovremeno, a klijentu vratiti jednu generičku poruku o grešci u slučaju bilo kog neuspeha.
* **Unified Error Messages:** Aplikacija uvek treba da koristi istu poruku, npr. "Unable to change password. Please check your inputs.", bez preciziranja šta je tačno pogrešno.
* **Session Binding:** Aplikacija ne bi smela da dozvoli promenu lozinke za korisnika čiji ID u zahtevu ne odgovara ID-u iz trenutne sesije (session cookie).
* **Anti-automation:** Implementacija CAPTCHA testa ili zahtev za ponovnom MFA verifikacijom pre nego što se uopšte dozvoli provera trenutne lozinke.