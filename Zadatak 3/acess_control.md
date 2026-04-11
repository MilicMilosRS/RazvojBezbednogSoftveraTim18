### 1. Access Control (Kontrola pristupa)

**Objašnjenje klase napada:** 
Kontrola pristupa (ili autorizacija) je primjena ograničenja o tome ko (ili šta) može izvesti određenu akciju ili pristupiti resursu. Napadi na kontrolu pristupa se dešavaju kada korisnik uspije da zaobiđe ta ograničenja. Ovo uključuje *vertikalnu eskalaciju privilegija* (običan korisnik dobija admin prava), *horizontalnu eskalaciju privilegija* (korisnik pristupa podacima drugog korisnika istog ranga - npr. Insecure Direct Object Reference ili IDOR), i *kontekstno-zavisnu eskalaciju* (zaobilaženje redoslijeda koraka, npr. preskakanje plaćanja u e-commerce aplikaciji).

**Uticaj iskorišćenja:** 
Uticaj je često kritičan. Napadač može pristupiti osjetljivim podacima drugih korisnika (PII podaci, finansijski izvještaji), modifikovati tuđe podatke, obrisati resurse sa servera ili u potpunosti preuzeti kontrolu nad aplikacijom ukoliko dobije administratorske privilegije.

**Ranjivosti u softveru koje su dozvolile napad:** 
Ove ranjivosti najčešće nastaju uslijed lošeg dizajna sistema. Glavni uzroci su:
* Vjerovanje podacima koji dolaze od klijenta (npr. manipulacija `id` parametrom u URL-u tipa `?userId=123`).
* Oslanjanje na skrivanje elemenata u UI-u umjesto sprovođenja validacije na backendu.
* Nedostatak centralizovanog mehanizma za autorizaciju, pa se provjere zaborave na pojedinačnim API endpointima.
* Oslanjanje na nesigurne identifikatore (poput predvidivih auto-inkrementing cijelih brojeva).

**Primjerene kontramjere:** 
* **Deny by default:** Sistem u startu treba da odbije pristup svakom resursu, osim ako nije eksplicitno dozvoljen.
* **Centralizovana autorizacija:** Korišćenje globalnih filtera ili middleware-a koji se primijenjuju na nivou rutinga, a ne samo unutar pojedinačnih kontrolera.
* **Indirektne reference:** Korišćenje nepredvidivih identifikatora poput GUID-ova/UUID-ova umjesto sekvencijalnih brojeva u bazi.
* **Vlasnička provjera (Ownership check):** Prije svake akcije nad bazom (bilo da je u pitanju čitanje, izmjena ili brisanje), backend logikom na nivou servisa mora provjeriti da li resurs kom se pristupa zaista pripada trenutno ulogovanom korisniku, čiji se identitet vadi iz sigurnog izvora (npr. JWT tokena), a ne iz korisničkog unosa.

### Lab 1: Unprotected admin functionality (Težina: Zeleni)

**Cilj zadatka:** Pristupiti nezaštićenom administratorskom panelu i obrisati korisnika `carlos`.

**Metodologija i koraci rješavanja:**

1. **Istraživanje i pronalaženje skrivenih putanja:**
   Kada se pristupi početnoj stranici aplikacije, u korisničkom interfejsu ne postoji vidljiv link ka administratorskom panelu. Pošto se programeri često oslanjaju na *Security by obscurity* (bezbjednost kroz opskurnost), prvi korak je bila provjera fajla `robots.txt` koji služi za skrivanje putanja od web pretraživača.
   Dodavanjem `/robots.txt` na osnovni URL aplikacije, otkrivena je sakrivena putanja:
   
<img width="1912" height="960" alt="image" src="https://github.com/user-attachments/assets/1d6921da-0432-462f-98bb-b5550954c539" />

2.  **Pristup administratorskom panelu:**
    Koristeći putanju otkrivenu u prethodnom koraku, u URL traku browsera je unijeto `/administrator-panel`. Zbog potpunog nedostatka kontrole pristupa na serverskoj strani (nema provjere sesije, JWT tokena niti korisničkih rola), aplikacija je dozvolila neautentifikovan pristup i direktno prikazala administratorski interfejs.

<img width="1919" height="953" alt="image" src="https://github.com/user-attachments/assets/87f3a6f4-1ab2-40c3-a5b2-f846fb1ad6dc" />

3.  **Eksploatacija i rješavanje laboratorije:**
    Na administratorskoj tabli, u redu gdje se nalazi ciljani korisnik `carlos`, iskorišćena je ponuđena funkcionalnost brisanja klikom na opciju **Delete**. Ovim je akcija uspješno izvršena, što dokazuje ranjivost sistema, a laboratorija je riješena.

<img width="1919" height="960" alt="image" src="https://github.com/user-attachments/assets/1f5facbb-47db-4edf-8541-b67c503bdf97" />

### Lab 2: User role controlled by request parameter (Težina: Zeleni)

**Cilj zadatka:** Pristupiti administratorskom panelu na putanji `/admin` i obrisati korisnika `carlos` modifikovanjem nesigurnog kolačića za autorizaciju.

**Metodologija i koraci rješavanja:**

1. **Autentifikacija korisnika:**
   Prvi korak je bio prijavljivanje na aplikaciju korišćenjem obezbjeđenih kredencijala (`wiener:peter`). Nakon uspješne prijave, server uspostavlja sesiju.

<img width="1920" height="1080" alt="Screenshot 2026-04-11 230632" src="https://github.com/user-attachments/assets/0d551a91-ca09-4e28-9465-391d346317a8" />
   
2. **Presretanje zahtjeva i eskalacija privilegija:**
   Pokušaj pristupa putanji `/admin` je presretnut pomoću alata Burp Suite (Proxy Intercept). U zaglavlju HTTP GET zahtjeva primijećeno je prisustvo kolačića `Admin` čija je vrijednost inicijalno postavljena na `false`, što ukazuje na to da se kontrola pristupa vrši na klijentskoj strani.
   
<img width="1920" height="1080" alt="Screenshot 2026-04-11 230649" src="https://github.com/user-attachments/assets/b50591c0-c24b-4a2b-a9da-95e103ce7444" />

   Da bi se zaobišla ova loše implementirana kontrola pristupa, vrijednost parametra `Admin` u kolačiću je ručno modifikovana iz `false` u `true` prije nego što je zahtjev proslijeđen (Forward) ka serveru.
   
<img width="1920" height="1080" alt="Screenshot 2026-04-11 230703" src="https://github.com/user-attachments/assets/03b12c7c-44df-4df1-937b-51a45805074c" />

3. **Pristup administratorskom panelu:**
   Server je obradio modifikovani zahtjev i, slijepo vjerujući vrijednosti kolačića, dodijelio administratorske privilegije, čime je omogućen pristup zaštićenom interfejsu.
   
<img width="1920" height="1080" alt="Screenshot 2026-04-11 230716" src="https://github.com/user-attachments/assets/9ded5c51-11cb-4bcb-a9e4-604f376edc9a" />

4. **Izvršenje akcije brisanja:**
   Klinom na opciju "Delete" pored korisnika `carlos`, generisan je novi HTTP zahtjev ka putanji `/admin/delete?username=carlos`. Pošto browser u originalnom stanju ponovo šalje originalni kolačić, i ovaj zahtjev je presretnut u Burp Suite-u gdje se ponovo vidi `Admin=false`.
   
<img width="1920" height="1080" alt="Screenshot 2026-04-11 230802" src="https://github.com/user-attachments/assets/e03db074-a028-4f36-85af-11b4b5bed334" />

   Vrijednost je izmijenjena ponovo u `Admin=true` kako bi server autorizovao i samu komandu za brisanje.
   
<img width="1920" height="1080" alt="Screenshot 2026-04-11 230813" src="https://github.com/user-attachments/assets/4b80c401-8617-462a-9312-095ddfe5c2a1" />

5. **Potvrda akcije:**
   Nakon brisanja, server vrši redirekciju nazad na panel. Ovaj zahtjev za redirekciju je takođe presretnut i modifikovan (iz `false` u `true`) kako bi se stranica uspješno i do kraja učitala.
   
<img width="1920" height="1080" alt="Screenshot 2026-04-11 230830" src="https://github.com/user-attachments/assets/143603b5-ca4f-44d2-8b6b-3b1fa4d258f8" />

<img width="1920" height="1080" alt="Screenshot 2026-04-11 230840" src="https://github.com/user-attachments/assets/274d224a-eff0-4dc2-b8ae-9a87c5e6e34a" />

   Akcija je uspješno izvršena, korisnik je obrisan, a laboratorija je riješena. Ovo jasno demonstrira kritičnu grešku oslanjanja na korisnički kontrolisane parametre za sprovođenje serverske autorizacije.
   
<img width="1920" height="1080" alt="Screenshot 2026-04-11 230851" src="https://github.com/user-attachments/assets/09f79bad-9b42-49f5-907e-6d780cd26092" />










### Lab 3: URL-based access control can be circumvented (Težina: Plavi)

**Cilj zadatka:** Zaobići *front-end* kontrolu pristupa, pristupiti administratorskom panelu i obrisati korisnika `carlos`.

**Metodologija i koraci rješavanja:**

1. **Analiza mehanizma zaštite i prvobitni pokušaj:**
   Prvi korak je bio pokušaj direktnog pristupa administratorskom interfejsu slanjem HTTP GET zahtjeva na putanju `/admin`.
   Aplikacija je vratila poruku "Access denied" (Pristup odbijen), a u Burp Suite istoriji je zabilježen HTTP status `403 Forbidden`. Ovo ukazuje da je ispred *back-end* servera postavljen *front-end* proxy ili ruter koji je eksplicitno konfigurisan da blokira svaki spoljni zahtjev ka putanji `/admin`.
   
<img width="1920" height="1080" alt="Screenshot 2026-04-11 232901" src="https://github.com/user-attachments/assets/5ab2c614-bdbe-4ba7-8b2a-f066c4aeb973" />

<img width="1920" height="1080" alt="Screenshot 2026-04-11 232923" src="https://github.com/user-attachments/assets/ccb38a99-2a9c-473e-bba1-18669ec6fbce" />

2. **Zaobilaženje front-end zaštite manipulisanjem HTTP zaglavlja:**
   Pošto je poznato da *back-end* framework podržava nestandardno HTTP zaglavlje `X-Original-URL`, moguće je prevariti *front-end* proxy. Presretnut je legitimni zahtjev ka početnoj stranici (`GET /`), koji *front-end* dozvoljava. Zatim je u zaglavlje ručno dodata linija `X-Original-URL: /admin`. 
   
<img width="1920" height="1080" alt="Screenshot 2026-04-11 233049" src="https://github.com/user-attachments/assets/ce223792-def6-426c-ba2e-1e0a02961e57" />

<img width="1920" height="1080" alt="Screenshot 2026-04-11 233100" src="https://github.com/user-attachments/assets/9c9d1a62-d4c7-4380-a941-2addb5e93e79" />

   *Front-end* proxy je propustio ovaj zahtjev jer je ciljana putanja u samom zahtjevu bila bezopasna (`/`), ali je *back-end* server obradio `X-Original-URL` zaglavlje, premostio rutu i uspješno vratio sadržaj zaštićenog administratorskog panela.
   
3. **Priprema za eksploataciju i pronalazak putanje za brisanje:**
   Pregledom učitanog administratorskog panela, identifikovana je tačna putanja potrebna za brisanje korisnika: `/admin/delete?username=carlos`.

<img width="1920" height="1080" alt="Screenshot 2026-04-11 233139" src="https://github.com/user-attachments/assets/317f09ea-8a6e-4b1d-95a0-3b827c280fe0" />

   Kada se pokušalo sa ubacivanjem cijele ove putanje (zajedno sa query parametrom) u `X-Original-URL` zaglavlje, aplikacija je vratila grešku "Missing parameter 'username'". Ovo je otkrilo specifično ponašanje *back-end* rutera: on mapira putanju iz zaglavlja, ali očekuje da se query parametri nalaze u glavnom URL-u zahtjeva.

3. **Korišćenje Burp Repeater-a za finalno izvršenje napada:**
   Da bi se ostvarila precizna kontrola nad zahtjevom bez ometanja od strane pozadinskog saobraćaja browsera, validan HTTP zahtjev je prebačen u alat **Burp Repeater**.

<img width="1920" height="1080" alt="Screenshot 2026-04-11 234111" src="https://github.com/user-attachments/assets/2b3023a5-0efa-4094-8632-27748326b1e1" />

   Napad je razdvojen na dva dijela unutar istog zahteva:
   * Ciljani parametar je dodat u glavni URL zahtjeva: `GET /?username=carlos` (kako bi ga backend pročitao).
   * Putanja za brisanje je dodata u zaglavlje: `X-Original-URL: /admin/delete` (kako bi se zaobišao frontend).   

<img width="1920" height="1080" alt="Screenshot 2026-04-11 234707" src="https://github.com/user-attachments/assets/d932c01a-2f30-4db6-97ea-5ed9afa26804" />

4. **Potvrda uspješnog brisanja:**
   Nakon slanja ovog modifikovanog zahtjeva kroz Repeater, server je odgovorio sa HTTP statusom `302 Found`, što je indikator da je akcija uspješno procesuirana i da server pokušava redirekciju nazad na admin panel.
   
<img width="1920" height="1080" alt="Screenshot 2026-04-11 234733" src="https://github.com/user-attachments/assets/1d65d42d-14fa-4bbc-b67a-72c991755634" />
   
   Osvježavanjem početne stranice u browseru, potvrđeno je da je korisnik `carlos` uspješno obrisan, čime je ranjivost uspješno eksploatisana, a zadatak riješen.
   
<img width="1920" height="1080" alt="Screenshot 2026-04-11 234747" src="https://github.com/user-attachments/assets/57f6dc3c-e675-4b4a-99b9-f1b481209d4b" />



















