# Pretpostavke i njihov utjecaj na plan

Podatak „9 sati” po zadanom određuje dopuštenu vožnju. Za planiranje cijele smjene korisnik može uključiti i rad na stajalištima. Uz limit vožnje na zadanim podacima dovoljan je B, a uz limit cijelog radnog dana A preuzima N03.

## Pravila i zadane postavke

| Postavka | Zadano | Razlog i učinak promjene |
|---|---|---|
| Dnevni limit (`day_limit_min`) | 540 min | Svaki vozač ima svojih devet sati. Na limitu vožnje od 180 min potrebna su oba kamiona i ukupno 200,1 km. |
| Što ulazi u limit (`limit_includes_handling`) | Samo vožnja | To je doslovno čitanje zadanog vremena vožnje. Uključi li se i utovar i istovar, minimum raste sa 182,2 na 200,1 km. |
| Trajanje utovara i istovara (`load_min`, `unload_min`) | 20 min za svaku radnju | Jedan nalog ima dvije radnje. Drugo tumačenje, ukupno 20 min po nalogu, postavlja 10 + 10 min. Trajanje upisano uz nalog ima prednost, uključujući nulu. |
| Brzina (`speed_kmh`) | 60 km/h po kamionu | Zadana su jednako brza vozila. Pri toj brzini 0,1 km traje 6 s. Brzina se za izmijenjenu flotu zadaje pojedinačno. |
| Korištenje svih kamiona (`require_all_trucks`) | Isključeno | Kamion može ostati u bazi. Uključena postavka daje prednost rasporedu s više kamiona među onima s jednakim brojem izvršenih naloga. Ovdje to dodaje 17,9 km. |
| Djelomičan plan (`allow_partial`) | Uključeno | Kada neki prijevoz nije izvediv, korisnik dobiva raspored za ostale i razlog izostavljanja. Uz strogi limit od 5 h stane 8 od 10 naloga. Uz isključenu opciju egzaktni solver javlja da potpuni plan nije moguć. |
| Cilj (`objective`) | Najmanje ukupno km | Zadatak traži smanjenje kilometraže. Najraniji završetak (`makespan`) na istom ulazu traži 284,2 km. Uračunava radnje i kad dnevni limit obuhvaća samo vožnju. |
| Izbor solvera (`solver`) | Automatski | Za tipičan mali scenarij može se dokazati optimum. Zadani pragovi su 12 naloga i tri kamiona (`exact_max_orders`, `exact_max_trucks`). Iznad praga koristi se OR-Tools. |
| Vrijeme pretrage (`ortools_time_limit_s`) | 3 s | Vremenski budžet za heurističko traženje plana, podesiv od 1 do 30 s. |
| Usporedba solvera (`compare_with_ortools`) | Uključeno | Nakon egzaktnog plana može se usporediti koliko je naloga OR-Tools izvršio i s koliko kilometara. |
| Početak smjene (`day_start`) | 07:00 | Početni sat služi prikazu dolazaka i odlazaka. Pomak početka smjene pomiče i prikazanu satnicu. |
| Prikvačeni nalozi (`pinned_orders`) | Prazno | Prikvačeni nalog smije voziti samo odabrani kamion. Ako se N04 prikvači na A, najkraći plan ima 217,0 km i A preuzima i N01. Ako se ostalih devet prikvači na B, rezultat je 218,8 km. |

Prikvačivanje na kamion premale nosivosti javlja se kao greška unosa. Ako nalog ne stane u raspoloživo vrijeme tog kamiona, može se izostaviti iz djelomičnog plana uz razlog.

## Referentne vrijednosti na zadanim podacima

„Strogi limit” u tablici znači da se zbrajaju vožnja, utovari i istovari. Svaki redak mijenja samo navedene postavke. Najveći teret odnosi se na fiksne referentne rute. Redoslijedi jednake ukupne kilometraže mogu imati različit najveći teret.

| Promjena u odnosu na zadano | Ishod |
|---|---|
| Bez promjene | **182,2 km, 10/10.** B vozi 3 h 02 min i obavi 400 min radnji. Radni dan traje 582,2 min (9 h 42 min). A ostaje u bazi. Na referentnoj ruti B doseže 9.400 kg i tri stroja. |
| Strogi limit od 9 h | **200,1 km, 10/10.** A vozi N03, 37,2 km i ukupno radi 77,2 min. B vozi 162,9 km, ukupno radi 522,9 min i na referentnoj ruti doseže 9.900 kg. |
| Svaki kamion mora voziti | 200,1 km. A vozi N03, B ostalih devet. |
| Samo vožnja u limitu, svaka radnja 0–30 min | 182,2 km. Mijenja se trajanje radnog dana. |
| Limit vožnje 3 h | 200,1 km. |
| Limit vožnje 2 h 30 min | 239,2 km. A vozi N03 i N05. |
| Limit vožnje 2 h 20 min | 9/10 naloga. |
| Limit vožnje 1 h 40 min | 7/10 naloga. |
| Strogi limit od 9 h, svaka radnja najviše 17 min | 182,2 km. |
| Strogi limit od 9 h, svaka radnja 18–20 min | 200,1 km. Pri 20,95 min po radnji B u tom planu radi točno 9 h. |
| Strogi limit od 9 h, svaka radnja 21 min | 217,0 km. A vozi N01 i N04. |
| Strogi limit od 9 h, svaka radnja 25 ili 30 min | 235,1 km pri 25 min, odnosno 254,9 km pri 30 min. |
| Strogi limit od 8 h | 235,1 km. |
| Strogi limit od 5 h 45 min | 284,2 km, 10/10 naloga. |
| Strogi limit od 5 h 30 min | 9/10 naloga. |
| Strogi limit od 5 h | 203,8 km, 8/10 naloga. Izostavljeni su N08 i N09. |
| Strogi limit od 9 h, 10 min utovar i 10 min istovar | 182,2 km. |
| Cilj najraniji završetak | 284,2 km. A vozi N01–N05, B vozi N06–N10. Posljednji kamion završava nakon 344,8 min (5 h 45 min). |
| Jedno mjesto za stroj po kamionu | 209,0 km uz limit vožnje, 226,0 km uz strogi limit. |
| A smije voziti samo N04 i njega mora preuzeti, B preuzima ostale | B radi 540,4 min. Uz limit vožnje raspored je valjan. Uz strogi limit prekoračenje je 24 sekunde. |

Pravilo zaokruživanja vrijedi za svaku dionicu, uključujući povratak u bazu. Zato i predprovjera neizvedivih naloga mora uzeti u obzir učinak međustajališta. [Obrazloženje i primjer iz specifikacije v4.2](LOGIKA.md#kada-se-nalog-smije-unaprijed-izostaviti).
