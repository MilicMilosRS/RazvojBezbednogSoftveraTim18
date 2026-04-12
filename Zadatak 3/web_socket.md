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

