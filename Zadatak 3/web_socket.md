### 3. WebSockets ranjivosti

**Objašnjenje klase napada:**
WebSockets tehnologija se široko koristi u modernim veb-aplikacijama. Za razliku od standardnog HTTP-a (gdje klijent pita, a server odgovara), WebSockets omogućavaju dugotrajnu, asinhronu dvosmjernu komunikaciju. Konekcija se inicira preko standardnog HTTP-a (kroz tzv. *WebSocket Handshake*), a zatim prelazi u stalno otvoreni kanal. S obzirom na to da se koriste za prenos osjetljivih podataka i izvršavanje akcija, gotovo svaka ranjivost koja važi za HTTP (SQL injekcije, XSS, itd.) može se primijeniti i na WebSocket komunikaciju.

**Manipulacija WebSocket saobraćajem:**
Pronalaženje ranjivosti uglavnom se svodi na manipulaciju podacima na način koji aplikacija ne očekuje. Alat Burp Suite se koristi za:
* **Presretanje i modifikaciju poruka:** Korišćenjem *Intercept* taba mogu se hvatati i mijenjati pojedinačne WebSocket poruke u letu (bilo od klijenta ka serveru, ili obrnuto).
* **Ponavljanje poruka:** Korišćenjem *Repeater* taba, jednom uhvaćena poruka se može izolovati, modifikovati i slati neograničen broj puta.
* **Manipulaciju "rukovanja" (Handshake):** Ponekad napad zahtijva promjenu inicijalnog HTTP zahtjeva kojim se uspostavlja WebSocket konekcija (kako bi se npr. zaobišli filteri ili promijenili sesijski tokeni).

**Vrste ranjivosti i uticaj:**
* **Injekcije kroz WebSocket poruke:** Ako aplikacija uzima tekst iz WebSocket poruke i direktno ga prikazuje drugim korisnicima (npr. u *chat* aplikacijama) bez sanitizacije, napadač može poslati zlonamjerni JavaScript kod i izazvati **XSS (Cross-Site Scripting)** napad.
* **Ranjivosti pri uspostavljanju konekcije (Handshake flaws):** Ove greške u dizajnu nastaju kada server donosi bezbjednosne odluke oslanjajući se na manipulativna HTTP zaglavlja (poput `X-Forwarded-For`) tokom inicijalnog spajanja.
* **Cross-site WebSockets hijacking (CSWSH):** Ovo je specifična vrsta napada, slična CSRF-u, gdje napadač sa svog zlonamjernog domena uspijeva da otvori WebSocket konekciju ka ranjivom serveru u ime ulogovane žrtve. Ovo napadaču omogućava dvosmjernu krađu podataka i izvršavanje privilegovanih akcija.

**Primjerene kontramjere:**
* **Korišćenje sigurnih protokola:** Uvijek koristiti `wss://` (WebSockets over TLS) umjesto neenkriptovanog `ws://` protokola.
* **Zaštita od CSRF-a:** Inicijalni *Handshake* zahtjev mora biti zaštićen od *Cross-Site Request Forgery* napada korišćenjem CSRF tokena ili strogih `SameSite` polisa za kolačiće.
* **Tretiranje podataka kao nepouzdanih:** Svi podaci primljeni kroz WebSocket kanal (u oba smjera) moraju se smatrati nebezbjednim. Neophodno je primijeniti strogu validaciju na serveru i bezbjedno enkodiranje prilikom prikaza na klijentu (prevencija SQLi, XSS i drugih injekcija).
* **Hardkodovanje endpoint-a:** Adresa WebSockets servera bi trebalo da bude fiksna i ne bi smjela da zavisi od korisničkog unosa.

### Lab 1: Manipulating WebSocket messages to exploit vulnerabilities (Težina: Zeleni)

**Cilj zadatka:** Aplikacija posjeduje "Live chat" funkcionalnost koja koristi WebSockets za komunikaciju u realnom vremenu između korisnika i agenta podrške. Cilj je iskoristiti ranjivost nedostatka sanitizacije unosa i kroz WebSocket poruku proslijediti XSS (Cross-Site Scripting) payload koji će okinuti `alert()` prozorčić u pregledaču agenta podrške.

**Metodologija i koraci rješavanja:**

1. **Mapiranje funkcionalnosti i presretanje saobraćaja:**
   Proces je započet korišćenjem "Live chat" opcije na aplikaciji. Poslata je benigna testna poruka ("Zdravo!").
   
<img width="1920" height="1080" alt="Screenshot 2026-04-12 173848" src="https://github.com/user-attachments/assets/47f7a24d-1fce-408e-9433-151f99553f2b" />

   Umjesto klasičnog HTTP taba, u Burp Suite alatu otvoren je **WebSockets history** tab kako bi se pratila dvosmjerna komunikacija. Zabilježena je poruka koja ide ka serveru (`Direction: To server`) i njen sadržaj u JSON formatu: `{"message":"cao"}`.
   
<img width="1920" height="1080" alt="Screenshot 2026-04-12 175458" src="https://github.com/user-attachments/assets/d385f05c-b42f-4813-8969-d292221a8783" />

3. **Modifikacija poruke (XSS Injekcija):**
   Uhvaćena poruka je proslijeđena u alat **Repeater** radi manipulacije.

<img width="1920" height="1080" alt="Screenshot 2026-04-12 175523" src="https://github.com/user-attachments/assets/0af98a32-c085-41d7-82b7-7630d237eca3" />

   Umjesto benigne poruke, u JSON objekat je ubačen klasičan XSS payload: `<img src=1 onerror='alert(1)'>`. Puna poruka je sada izgledala ovako:
   `{"message":"<img src=1 onerror='alert(1)'>"}`
   
<img width="1920" height="1080" alt="Screenshot 2026-04-12 175545" src="https://github.com/user-attachments/assets/bfc38135-fc9e-4f95-bc7a-d2ed61ba8a37" />

5. **Slanje i okidanje napada:**
   Napad je lansiran klikom na dugme "Send". Modifikovana poruka je kroz otvorenu WebSocket konekciju stigla do backend servera, koji ju je proslijedio agentu podrške bez prethodnog filtriranja. Pregledač agenta (a povratno i naš pregledač u chatu) pokušao je da učita sliku sa nepostojećeg izvora (`src=1`), što je izazvalo grešku i automatski pokrenulo JavaScript funkciju `alert(1)`.
   
<img width="1920" height="1080" alt="Screenshot 2026-04-12 175553" src="https://github.com/user-attachments/assets/c3d0829f-6cfb-4158-9be1-c1bc5388808e" />

6. **Potvrda rješenja:**
   Uspješnim okidanjem `alert()` prozorčića na klijentskoj strani, potvrđeno je prisustvo ranjivosti i uspješno je izvršen zadatak. Aplikacija je izbacila poruku o uspješno riješenoj laboratoriji.
   
<img width="1920" height="1080" alt="Screenshot 2026-04-12 175603" src="https://github.com/user-attachments/assets/e70521c1-0e9c-45da-8bbd-0d6825f128a3" />

### Lab 2: Cross-site WebSocket hijacking (Težina: Plavi)

**Cilj zadatka:** Aplikacija koristi WebSockets za "Live chat" funkcionalnost, ali inicijalni HTTP zahtjev za uspostavljanje konekcije (Handshake) nije zaštićen od CSRF napada (oslanja se isključivo na sesijske kolačiće). Cilj je konstruisati Cross-Site WebSocket Hijacking (CSWSH) napad, ukrasti istoriju ćaskanja korisnika, pronaći njegovu lozinku u porukama i kompromitovati nalog.

**Metodologija i koraci rješavanja:**

1. **Analiza WebSocket konekcije:**
   Proces je započet otvaranjem zadatka i analizom funkcionalnosti "Live chat-a".
   
<img width="1920" height="1080" alt="Screenshot 2026-04-12 180907" src="https://github.com/user-attachments/assets/e83082a1-e569-46ed-92d1-84e0d3795499" />

   Korišćenjem alata Burp Suite, analiziran je proces uspostavljanja WebSocket konekcije. U HTTP istoriji zabilježen je `GET /chat` zahtjev (Handshake) sa statusom "101 Switching Protocols". Utvrđeno je da aplikacija autorizuje korisnika isključivo na osnovu proslijeđenog `session` kolačića, te da ne koristi nikakve nasumične CSRF tokene za zaštitu konekcije.
   
<img width="1920" height="1080" alt="Screenshot 2026-04-12 181320" src="https://github.com/user-attachments/assets/374868b0-fb3f-4365-880f-ddc9b9d2752c" />
 
   U WebSockets istoriji je primijećeno da klijent nakon otvaranja konekcije šalje komandu `READY` ka serveru, na šta server automatski odgovara slanjem cjelokupne istorije ćaskanja.
   
<img width="1920" height="1080" alt="Screenshot 2026-04-12 182204" src="https://github.com/user-attachments/assets/0af10789-c740-4f45-8025-da0c06f22f8f" />

2. **Priprema CSWSH napada:**
   Kako bi se ranjivost eksploatisala, korišćen je ugrađeni Exploit server. Napisana je zlonamjerna JavaScript skripta koja otvara WebSocket konekciju ka ranjivom serveru sa domena napadača. S obzirom na nedostatak CSRF zaštite, pregledač žrtve prilikom otvaranja konekcije automatski priključuje njene sesijske kolačiće. 

<img width="1920" height="1080" alt="Screenshot 2026-04-12 182645" src="https://github.com/user-attachments/assets/8ba0f5dc-edf6-4275-8834-85b09e839660" />

   Skripta nakon otvaranja konekcije šalje komandu `READY`. Sve pristigle poruke (koje sadrže žrtvinu istoriju chata) prikupljaju se, enkodiraju u **Base64 format** (kako bi se obezbjedio siguran prenos i izbjeglo pucanje HTTP zahtjeva) i šalju napadaču nazad kroz HTTP `GET` zahtjev kao URL parametar.
   
<img width="1920" height="1080" alt="Screenshot 2026-04-12 183235" src="https://github.com/user-attachments/assets/8cf4166f-4a03-401e-87b8-3b0f86a4d7d5" />

2. **Isporuka napada i krađa podataka:**
   Napad je sačuvan i isporučen žrtvi (Deliver exploit to victim). Pregledom pristupnih logova (Access log) na Exploit serveru, zabilježeni su dolazni `GET` zahtjevi žrtve koji su u URL parametru `?key=` sadržali ukradene, Base64 enkodirane podatke iz chata.
   
<img width="1920" height="1080" alt="Screenshot 2026-04-12 183604" src="https://github.com/user-attachments/assets/4f03763c-240e-40de-a2d1-8718d756ee6f" />

   Odgovarajući Base64 string je izolovan i iskopiran radi dalje analize.
   
<img width="1920" height="1080" alt="Screenshot 2026-04-12 183404" src="https://github.com/user-attachments/assets/53344ab3-316c-40c5-b9e3-657b2f496c00" />

3. **Dekodiranje i kompromitovanje naloga:**
   Ukradeni Base64 string je uspješno dekodiran, čime je dobijen pristup originalnoj JSON poruci iz chata, u kojoj agent podrške šalje lozinku korisniku.
   
<img width="1920" height="1080" alt="Screenshot 2026-04-12 183436" src="https://github.com/user-attachments/assets/92caee82-fc01-4d4a-926d-629f7638fdb6" />
 
   Iz poruke je ekstrahovana korisnička lozinka žrtve (`cn37bvzegankvblpd4fg`). Ovi kredencijali su iskorišćeni za uspješnu prijavu na sistem sa korisničkim imenom `carlos`.
   
<img width="1920" height="1080" alt="Screenshot 2026-04-12 183835" src="https://github.com/user-attachments/assets/ba0d38c0-56fa-4265-a21c-1651e9fa5b29" />

   Uspješnom prijavom, korisnički nalog je kompromitovan, a laboratorija je zvanično riješena.

### Lab 3: Manipulating the WebSocket handshake to exploit vulnerabilities (Težina: Practitioner)

**Cilj zadatka:** Aplikacija koristi WebSockets za "Live chat" funkcionalnost i posjeduje agresivan XSS filter. Cilj je iskoristiti manipulaciju WebSocket handshake-a (zaglavlja) kako bi se zaobišle restrikcije zasnovane na IP adresi i poslati modifikovan XSS payload kroz **Repeater** koji će pokrenuti `alert()` funkciju kod agenta.

**Metodologija i koraci rješavanja:**

1.  **Analiza i detekcija blokade:**
    Nakon inicijalnog pokušaja slanja XSS koda, aplikacija je detektovala napad, prekinula konekciju i blokirala IP adresu korisnika.

<img width="1920" height="1080" alt="Screenshot 2026-04-12 192836" src="https://github.com/user-attachments/assets/8f4503cf-0574-4abc-a5cf-c3925d932df3" />

   Svaki sljedeći pokušaj povezivanja rezultovao je porukom "This address is blacklisted".

2.  **Bypass IP restrikcije (Match and Replace):**
    U Burp Suite postavkama (Proxy -\> Proxy settings) dodato je **Match and Replace** pravilo kako bi se u handshake zahtjev ubacilo zaglavlje `X-Forwarded-For`. Ovo je omogućilo serveru da zahtjev vidi kao da dolazi sa nove, neblokirane IP adrese (`1.1.1.99`), čime je ponovo uspostavljena WebSocket konekcija.

<img width="1920" height="1080" alt="Screenshot 2026-04-12 202005" src="https://github.com/user-attachments/assets/32bc1068-1d9d-4729-a505-4367a72db00a" />
<img width="1920" height="1080" alt="Screenshot 2026-04-12 204910" src="https://github.com/user-attachments/assets/60de8398-b7bd-4e3e-b9d5-32db0f8e3ec1" />

3.  **Eksploatacija putem Repeater-a:**
    Za finalni napad korišćen je **Burp Repeater**. WebSocket poruka je presretnuta i poslata u Repeater tab. Ovakav pristup je omogućio slanje sirovog (raw) JSON paketa bez rizika da browser enkodira specijalne karaktere.

    Konstruisan je payload koji zaobilazi filter koristeći miješana slova i backtick karaktere:
    `{"message":"<img src=1 oNeRrOr=alert`1`>"}`

<img width="1920" height="1080" alt="Screenshot 2026-04-12 204956" src="https://github.com/user-attachments/assets/bbb32a02-fece-41fc-b2e0-f28af2bba72d" />

4.  **Potvrda izvršavanja i rješavanje laba:**
    Slanjem poruke iz Repeater-a, maliciozni kod je uspješno proslijeđen agentu (Hal Pline). U chat interfejsu se vidi ikonica polomljene slike, što potvrđuje da je HTML uspješno injektovan u stranicu.

<img width="1920" height="1080" alt="Screenshot 2026-04-12 205026" src="https://github.com/user-attachments/assets/8c462c53-d0e3-4f7d-bfdc-d4c48c84ea5c" />
<img width="1920" height="1080" alt="Screenshot 2026-04-12 205034" src="https://github.com/user-attachments/assets/ba568fe9-129b-4c64-a0f2-1a3b14d686af" />

Ubrzo nakon toga, na vrhu stranice se pojavio zeleni baner koji potvrđuje da je laboratorija uspješno riješena.

<img width="1920" height="1080" alt="Screenshot 2026-04-12 205045" src="https://github.com/user-attachments/assets/e3c57c51-10fb-4957-95b5-3f69bd1fee2d" />














