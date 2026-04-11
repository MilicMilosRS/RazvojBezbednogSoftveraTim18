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




