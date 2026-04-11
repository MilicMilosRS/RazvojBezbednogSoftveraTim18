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
