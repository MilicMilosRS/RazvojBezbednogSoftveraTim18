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
