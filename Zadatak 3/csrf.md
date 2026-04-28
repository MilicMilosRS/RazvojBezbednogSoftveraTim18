## 2. Analiza klase napada: Cross-Site Request Forgery (CSRF)

### Objašnjenje klase napada
CSRF (Cross-Site Request Forgery) je ranjivost na strani klijenta koja omogućava napadaču da natera browser žrtve da izvrši neželjenu akciju na drugom sajtu gde je žrtva trenutno autentifikovana. Napad koristi činjenicu da browseri automatski uključuju sesione kolačiće (session cookies) u svaki zahtev ka određenom domenu, bez obzira na to odakle je zahtev potekao.

### Uticaj (Impact)
Uspešno iskorišćavanje ove klase ranjivosti može imati različite posledice u zavisnosti od funkcije:
* **Krađa podataka / Preuzimanje naloga:** Promena email adrese ili lozinke korisnika (što vodi do Account Takeover-a).
* **Finansijska šteta:** Neovlašćeni prenos novca ili kupovina robe bez znanja korisnika.
* **Administratorski nivo:** Ako je žrtva administrator, napadač može kreirati nove privilegovane naloge ili manipulisati celim sistemom.

### Uzrok ranjivosti (Root Cause)
Glavni razlozi za uspeh ovih napada su:
1. **Relevantna akcija:** Postoji akcija unutar aplikacije koja menja stanje podataka (npr. promenu parametara naloga).
2. **Sesija zasnovana na kolačićima:** Aplikacija koristi isključivo kolačiće za prepoznavanje ulogovanog korisnika.
3. **Odsustvo nepredvidivih parametara:** Zahtev ne sadrži nikakve tajne vrednosti (tokene) koje napadač ne može da pogodi.

### Kontramere (Defenses)
Kako bi se sprečili ovi napadi, potrebno je implementirati sledeće mehanizme:
* **Anti-CSRF Tokeni:** Server treba da generiše jedinstvenu, nepredvidivu vrednost koja se validira pri svakom zahtevu koji menja podatke.
* **SameSite Cookie Attribute:** Postavljanje atributa na kolačiće (`SameSite=Strict` ili `Lax`) koji sprečava browser da šalje kolačiće uz eksterne zahteve.
* **Referer i Origin Checks:** Provera zaglavlja zahteva kako bi se potvrdilo da on zaista potiče sa originalnog domena aplikacije.

---

## Zadatak 1: CSRF vulnerability with no defenses
**Nivo:** Apprentice (Zeleni)

### Opis zadatka
Cilj zadatka je bio iskoristiti potpuno odsustvo CSRF zaštite u formi za promenu email adrese. Aplikacija nije koristila nikakve tokene, što omogućava slanje falsifikovanog zahteva u ime ulogovanog korisnika.

### Writeup (Koraci rešavanja)

#### Korak 1: Analiza zahteva u Burp-u
Prvi korak je bio prijava na nalog `wiener:peter` i promena email adrese. U **Burp Proxy > HTTP History** identifikovan je `POST /my-account/change-email` zahtev. Analizom je utvrđeno da zahtev ne sadrži nikakve anti-CSRF tokene.

<img width="1528" height="501" alt="csrf1" src="https://github.com/user-attachments/assets/9140324c-fa9f-4d40-8c2c-48f3088ce3b3" />

#### Korak 2: Izrada exploit koda
S obzirom na to da koristim **Burp Community Edition**, ručno sam kreirala HTML formu koja automatski vrši "submit" zahteva koristeći JavaScript.

```html
<form method="POST" action="https://[TVOJ-LAB-ID].web-security-academy.net/my-account/change-email">
    <input type="hidden" name="email" value="napad@test.rs">
</form>
<script>
    document.forms[0].submit();
</script>
```
<img width="1743" height="740" alt="csrf2" src="https://github.com/user-attachments/assets/a15a2d4f-5400-4678-b491-809f52a8f9c1" />

#### Korak 3: Isporuka napada (Exploit Server)
Kod je nalepen u Body sekciju na Exploit Serveru. Prvo je korišćena opcija Store, a zatim View exploit kako bi se proverilo da li skripta radi na mom nalogu.

(Slika prikazuje konfiguraciju exploit-a na serveru)

#### Korak 4: Rešavanje laboratorije
Nakon potvrde da exploit radi, kliknula sam na Deliver exploit to victim. Bot je posetio link, što je okinulo promenu njegovog email-a na serveru.

<img width="1551" height="822" alt="csrf-solved" src="https://github.com/user-attachments/assets/e4ebdf50-f8bb-4836-a274-88d2e19611e6" />

---

## Zadatak 2: CSRF where token validation depends on request method
**Nivo:** Practitioner (Plavi)

### Opis zadatka
Cilj ovog izazova je bio zaobići CSRF zaštitu koja je polovično implementirana. Server proverava validnost tokena isključivo za `POST` zahteve, dok za `GET` metodu potpuno ignoriše postojanje tokena.

### Writeup (Koraci rešavanja)

#### Korak 1: Analiza ranjivosti u Repeater-u
Nakon presretanja legitimnog `POST` zahteva, utvrđeno je da server blokira promenu email-a ako je token neispravan. Međutim, promenom HTTP metode u `GET` pomoću opcije "Change request method" u Burp Suite-u, primetila sam da server prihvata zahtev čak i kada se CSRF token potpuno ukloni.

<img width="1746" height="983" alt="lab2-csrf" src="https://github.com/user-attachments/assets/20638b42-b716-4bc1-a725-dba37accde8a" />

#### Korak 2: Konstrukcija napada
Iskoristila sam HTML formu bez definisane metode (default je `GET`). Na taj način browser žrtve šalje parametre kroz URL, što server ne proverava.

```html
<form action="https://[ID-LABA].web-security-academy.net/my-account/change-email">
    <input type="hidden" name="email" value="haker@metoda.rs">
</form>
<script>
    document.forms[0].submit();
</script>
```

#### Korak 3: Isporuka

Nakon postavljanja koda na Exploit Server i klika na "Deliver exploit to victim", lab je uspešno rešen.

<img width="1476" height="246" alt="lab2-csrf-solved" src="https://github.com/user-attachments/assets/3bd14507-e919-4e9f-a994-11eb25bd0f91" />

## Zadatak 3: CSRF where token validation depends on token being present
**Nivo:** Practitioner (Plavi)

### Opis zadatka
Ovaj laboratorijski zadatak demonstrira propust u logici validacije CSRF tokena. Aplikacija je konfigurisana tako da proverava ispravnost tokena **isključivo** ukoliko je taj parametar prisutan u HTTP zahtevu. Ukoliko se parametar koji nosi token u potpunosti izostavi, backend server preskače validaciju i izvršava akciju, verujući da je zahtev legitiman.

### Writeup (Koraci rešavanja)

#### Korak 1: Analiza mehanizma validacije (Repeater)
Nakon presretanja legitimnog `POST` zahteva za promenu email-a u Burp Suite-u, prosledila sam ga u **Repeater**. 
* Prvobitno sam modifikovala vrednost `csrf` tokena, što je rezultovalo greškom `"Invalid CSRF token"`. 
* Zatim sam u potpunosti obrisala red koji sadrži `csrf=[vrednost]` parametar (zajedno sa pratećim `&` znakom). Nakon slanja takvog zahteva, server je vratio status **302 Found**, što potvrđuje da je promena email-a prihvaćena bez provere tokena.

<img width="1263" height="786" alt="lab3-izbrisan-csrf" src="https://github.com/user-attachments/assets/ab2b357a-d716-4d87-8489-1d6dbdbe563f" />
*Slika 1: Prikaz Repeater prozora gde se vidi POST zahtev bez CSRF parametra i uspešan odgovor servera.*

#### Korak 2: Konstrukcija malicioznog koda
Na osnovu analize, kreirala sam HTML formu na exploit serveru. Ključno je bilo izostaviti bilo kakvo polje (input) koje se odnosi na CSRF token, ostavljajući samo polje za email. Skripta automatski šalje formu čim žrtva učita stranicu.

```html
<form method="POST" action="https://[VAŠ-LAB-ID].web-security-academy.net/my-account/change-email">
    <input type="hidden" name="email" value="haker@bez-tokena.rs">
</form>
<script>
    document.forms[0].submit();
</script>
```
<img width="1570" height="582" alt="lab3-body" src="https://github.com/user-attachments/assets/e2b885d0-1068-4f83-b9aa-04b8a8fbbab6" />
Slika 2: Konfiguracija malicioznog koda u Body sekciji exploit servera.

#### Korak 3: Isporuka i finalizacija napada
Proces isporuke napada žrtvi izvršen je kroz sledeće podkorake:

Store: Klikom na dugme "Store", sačuvala sam pripremljeni HTML kod na putanji koju kontroliše napadački server.

View exploit: Pre isporuke žrtvi, iskoristila sam opciju "View exploit" kako bih pokrenula napad na sopstvenom nalogu i potvrdila da kod ispravno vrši automatski "submit" forme.

Modifikacija za žrtvu: Pošto aplikacija ne dozvoljava registraciju već postojećeg email-a, nakon uspešnog testa sam se vratila u Body i promenila vrednost email-a u jedinstvenu adresu (npr. final-attack@test.rs).

Deliver exploit to victim: Klikom na ovo dugme, server simulira slanje linka žrtvi. Kada žrtva (bot) poseti link, njen browser automatski šalje falsifikovani zahtev bez tokena, čime se menja njen email.

<img width="1460" height="246" alt="lab3-final" src="https://github.com/user-attachments/assets/4f1b3622-453f-4444-a982-5b361bc3ba4c" />
Slika 3: Potvrda o uspešno rešenom Practitioner izazovu.

## Zadatak 4: CSRF where token is not tied to user session
**Nivo:** Practitioner (Plavi)

### Opis zadatka
Ova laboratorija demonstrira ozbiljan bezbednosni propust u implementaciji CSRF zaštite. Iako aplikacija koristi tokene, oni nisu povezani sa sesijom specifičnog korisnika. Napadač može iskoristiti bilo koji validan CSRF token (izvučen iz sopstvene sesije) kako bi autorizovao maliciozni zahtev koji će izvršiti žrtva.

### Writeup (Koraci rešavanja)

#### Korak 1: Presretanje validnog tokena (Token Stealing)
Prvi korak je bio dobijanje validnog CSRF tokena koji server prepoznaje. Prijavila sam se kao korisnik `wiener` i pokrenula promenu email adrese uz uključen **Burp Intercept**. Iskopirala sam vrednost tokena iz zahteva.

<img width="1541" height="847" alt="drop" src="https://github.com/user-attachments/assets/f406d435-13b0-4d54-b74f-5da350b3a922" />
*Slika 1: Presretanje POST zahteva i kopiranje CSRF tokena pre slanja serveru.*

Da bih osigurala da token ostane "svež" i neiskorišćen za finalni napad, iskoristila sam opciju **Drop**. Time je zahtev poništen, a token je ostao validan u bazi servera.

<img width="1562" height="932" alt="posle-dropa" src="https://github.com/user-attachments/assets/213b52f8-93b3-4446-985e-011be243b4f1" />
*Slika 2: Potvrda da je zahtev odbačen (Dropped) kako bi se sačuvao integritet tokena.*

#### Korak 2: Dokazivanje ranjivosti (Cross-User Validation)
Kako bih potvrdila da tokeni nisu vezani za sesiju, prijavila sam se kao drugi korisnik (`carlos`) u odvojenoj sesiji. U **Repeateru** sam kreirala zahtev za promenu Carlosovog email-a, ali sam originalni token zamenila onim koji pripada korisniku `wiener`.

<img width="1455" height="756" alt="podmetnuli-csrf" src="https://github.com/user-attachments/assets/8fbd3fa6-ad36-411f-a740-f308ad74c0a7" />
*Slika 3: Uspešno podmetanje Wienerovog tokena u Carlosov zahtev. Server vraća "302 Found", što je direktan dokaz ranjivosti.*

#### Korak 3: Konstrukcija i isporuka eksploita
Na exploit serveru sam kreirala malicioznu HTML formu. U `csrf` polje sam unela novi, neiskorišćeni token dobijen metodom iz Koraka 1. Skripta je konfigurisana da automatski izvrši "submit" čim žrtva poseti stranicu.

<img width="1503" height="453" alt="lab4-body-final" src="https://github.com/user-attachments/assets/bb14dbe2-df5c-4ee2-8ee8-4e361b586278" />
*Slika 4: Finalni payload na exploit serveru spreman za isporuku botu (žrtvi).*

#### Korak 4: Finalna potvrda
Nakon klika na **Deliver exploit to victim**, laboratorija je uspešno rešena. Bot je posetio maliciozni link, njegov browser je poslao zahtev sa mojim tokenom, a server je promenu email-a prihvatio kao legitimnu.

<img width="1457" height="247" alt="lab4-finished" src="https://github.com/user-attachments/assets/9bd292c4-7e21-4b05-9fd6-1a6798638712" />
*Slika 5: Potvrda o uspešno rešenom Practitioner izazovu.*

## Zadatak 5: CSRF where token is tied to non-session cookie
**Nivo:** Practitioner (Plavi)

### Opis zadatka
Ovaj laboratorijski zadatak demonstrira kompleksan bezbednosni propust gde aplikacija koristi "double-submit" mehanizam zaštite, ali on nije integrisan u glavni sistem sesija. Aplikacija proverava da li se `csrf` token iz tela zahteva poklapa sa `csrfKey` kolačićem, ali ne proverava kome taj par pripada. Dodatno, ranjivost u pretrazi omogućava ubrizgavanje HTTP zaglavlja (Header Injection) radi manipulacije kolačićima.

### Writeup (Koraci rešavanja)

#### Korak 1: Analiza i prikupljanje uparenih identifikatora
Prijavila sam se na nalog `wiener` i presrela zahtev za promenu email-a. Iz HTTP zahteva sam izvukla par identifikatora koji server smatra validnim:
* **Kolačić:** `csrfKey=R77DnIhcBRaZNlntQ44gUNlf4PjuozVn`
* **Parametar:** `csrf=jmefDXbwRr9vBkEXU1GQAtCCRbelaqjN`

<img width="1491" height="832" alt="lab5-skrin1" src="https://github.com/user-attachments/assets/61130c72-80d2-4185-8cc3-f4a0c91f5dce" />
*Slika 1: Presretanje uparenog csrfKey kolačića i csrf tokena iz validne sesije.*

#### Korak 2: Iskorišćavanje Header Injection ranjivosti
Identifikovala sam da funkcija pretrage dozvoljava ubrizgavanje novih redova u HTTP odgovor. Ovo sam iskoristila da konstruišem URL koji će u browser žrtve "nasilno" postaviti moj `csrfKey` kolačić pre slanja glavne forme. Koristila sam `%0d%0a` (CRLF) sekvencu za injekciju `Set-Cookie` zaglavlja.

#### Korak 3: Konstrukcija naprednog CSRF exploita
Na exploit serveru sam kreirala payload koji kombinuje promenu email-a i injekciju kolačića. Koristila sam `<img>` tag čiji `src` atribut cilja ranjivu pretragu, dok `onerror` događaj okida automatsko slanje forme.

```html
<form method="POST" action="https://[LAB-ID].web-security-academy.net/my-account/change-email">
    <input type="hidden" name="email" value="haker-final-boss@test.rs">
    <input type="hidden" name="csrf" value="jmefDXbwRr9vBkEXU1GQAtCCRbelaqjN">
</form>

<img src="https://[LAB-ID].web-security-academy.net/?search=test%0d%0aSet-Cookie:%20csrfKey=R77DnIhcBRaZNlntQ44gUNlf4PjuozVn%3b%20SameSite=None" onerror="document.forms[0].submit()">
```
<img width="1398" height="467" alt="lab5-body" src="https://github.com/user-attachments/assets/f589bfc8-483c-436f-8be6-2b886c924869" />
Slika 2: Sklopljen napad na exploit serveru koji vrši injekciju kolačića i automatski submit forme.

#### Korak 4: Rezultat napada
Nakon isporuke napada (Deliver exploit to victim), browser žrtve je primio moj csrfKey putem pretrage, a potom poslao zahtev za promenu email-a sa mojim csrf tokenom. Pošto se parovi poklapaju, server je dozvolio akciju iako sesija (session cookie) pripada žrtvi.

<img width="1472" height="247" alt="lab5-finished" src="https://github.com/user-attachments/assets/087b50f3-508f-4347-930a-2115d10c18ec" />
Slika 3: Potvrda o uspešno rešenom finalnom Practitioner izazovu iz CSRF oblasti.
