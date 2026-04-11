### 1. Access Control (Kontrola pristupa)

**Objašnjenje klase napada:** 
Kontrola pristupa (ili autorizacija) je primena ograničenja o tome ko (ili šta) može izvesti određenu akciju ili pristupiti resursu. Napadi na kontrolu pristupa se dešavaju kada korisnik uspe da zaobiđe ta ograničenja. Ovo uključuje *vertikalnu eskalaciju privilegija* (običan korisnik dobija admin prava), *horizontalnu eskalaciju privilegija* (korisnik pristupa podacima drugog korisnika istog ranga - npr. Insecure Direct Object Reference ili IDOR), i *kontekstno-zavisnu eskalaciju* (zaobilaženje redosleda koraka, npr. preskakanje plaćanja u e-commerce aplikaciji).

**Uticaj iskorišćenja (exploit-a):** 
Uticaj je često kritičan. Napadač može pristupiti osetljivim podacima drugih korisnika (PII podaci, finansijski izveštaji), modifikovati tuđe podatke, obrisati resurse sa servera ili u potpunosti preuzeti kontrolu nad aplikacijom ukoliko dobije administratorske privilegije.

**Ranjivosti u softveru koje su dozvolile napad:** 
Ove ranjivosti najčešće nastaju usled lošeg dizajna sistema. Glavni uzroci su:
* Verovanje podacima koji dolaze od klijenta (npr. manipulacija `id` parametrom u URL-u tipa `?userId=123`).
* Oslanjanje na skrivanje elemenata u UI-u umesto sprovođenja validacije na backendu.
* Nedostatak centralizovanog mehanizma za autorizaciju, pa se provere zaborave na pojedinačnim API endpointima.
* Oslanjanje na nesigurne identifikatore (poput predvidivih auto-inkrementing celih brojeva).

**Primerene kontramere:** 
* **Deny by default:** Sistem u startu treba da odbije pristup svakom resursu, osim ako nije eksplicitno dozvoljen.
* **Centralizovana autorizacija:** Korišćenje globalnih filtera ili middleware-a koji se primenjuju na nivou rutinga, a ne samo unutar pojedinačnih kontrolera.
* **Indirektne reference:** Korišćenje nepredvidivih identifikatora poput GUID-ova/UUID-ova umesto sekvencijalnih brojeva u bazi.
* **Vlasnička provera (Ownership check):** Pre svake akcije nad bazom (bilo da je u pitanju čitanje, izmena ili brisanje), backend logikom na nivou servisa mora proveriti da li resurs kojem se pristupa zaista pripada trenutno ulogovanom korisniku, čiji se identitet vadi iz sigurnog izvora (npr. JWT tokena), a ne iz korisničkog unosa.