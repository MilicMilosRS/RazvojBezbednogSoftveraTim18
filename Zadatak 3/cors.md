### 2. Cross-Origin Resource Sharing (CORS) ranjivosti

**Objašnjenje klase napada:**
CORS (Cross-Origin Resource Sharing) je mehanizam veb-pregledača koji omogućava kontrolisan pristup resursima koji se nalaze van izvornog domena. On predstavlja kontrolisano "opuštanje" izuzetno restriktivne SOP (*Same-Origin Policy*) polise, koja inače spriječava jedan domen da čita podatke sa drugog. CORS koristi HTTP zaglavlja (poput `Access-Control-Allow-Origin`) da definiše kojim eksternim domenima je dozvoljeno čitanje odgovora i da li se pritom smiju slati sesijski kolačići. Napadi bazirani na CORS-u nastaju kada je ova polisa na serveru loše konfigurisana, omogućavajući zlonamjernim domenima da zaobiđu SOP zaštitu.

**Uticaj iskorišćenja:**
Ukoliko je korisnik prijavljen na ranjivu aplikaciju, a zatim posjeti zlonamjerni sajt, napadač može natjerati pregledač žrtve da u pozadini pošalje CORS zahtjev ka ranjivoj aplikaciji (zajedno sa kolačićima žrtve). Zbog loše konfiguracije, pregledač će dozvoliti zlonamjernom sajtu da pročita odgovor. Na ovaj način napadač može ukrasti osjetljive privatne podatke žrtve, API ključeve, CSRF tokene ili čak dobiti pristup internim resursima organizacije.

**Ranjivosti u softveru koje su dozvolile napad:**
Veb-serveri često griješe u implementaciji CORS-a kako bi olakšali integraciju različitih servisa, a najčešći uzroci su:
* **Slijepo reflektovanje `Origin` zaglavlja:** Kako bi izbjegli održavanje liste dozvoljenih domena, programeri podese server da jednostavno pročita `Origin` zaglavlje iz zahtjeva klijenta i iskopira ga u `Access-Control-Allow-Origin` zaglavlje odgovora, dajući tako pristup bilo kom sajtu na internetu.
* **Greške u parsiranju domena (loše bijele liste):** Korišćenje nesigurnih regularnih izraza ili pravila za provjeru URL-ova (npr. dozvoljavanje svih domena koji se *završavaju* sa `normal-website.com`, što napadač zaobilazi registracijom domena `hackersnormal-website.com`).
* **Dozvoljavanje `null` origin-a:** Serveri se ponekad konfigurišu da dozvole vrijednost `null` u `Origin` zaglavlju (često zbog lokalnog razvoja). Napadači ovo eksploatišu generišući zahtjeve iz *sandboxed* ifrejmova (gdje pregledač šalje `Origin: null`).
* **Povjerenje u nesigurne protokole:** Ukoliko siguran (HTTPS) sajt u svojoj CORS polisi dozvoli pristup svom nesigurnom (HTTP) poddomenu, napadač koji presreće saobraćaj može kompromitovati TLS enkripciju.

**Primjerene kontramere:**
* **Striktna definicija dozvoljenih domena (Whitelist):** `Access-Control-Allow-Origin` zaglavlje smije da sadrži isključivo tačne nazive pouzdanih sajtova. Nikada ne treba dinamički i bez provjere reflektovati origin koji pošalje klijent.
* **Zabrana `null` vrijednosti:** Izbjegavati konfigurisanje zaglavlja `Access-Control-Allow-Origin: null`, s obzirom na to da se ono lako lažira iz zlonamjernih dokumenata.
* **Izbjegavanje "wildcard" (`*`) konfiguracija u intranetu:** Samo postojanje aplikacije u privatnoj mrežnoj zoni nije dovoljna zaštita ako unutrašnji korisnici pristupaju javnom internetu.
* **Slojevita zaštita:** CORS definiše ponašanje pregledača i nije zamjena za serversku bezbednost. Server uvijek mora da provjerava autentifikaciju, autorizaciju i vlasništvo nad podacima, nezavisno od CORS zaglavlja.
