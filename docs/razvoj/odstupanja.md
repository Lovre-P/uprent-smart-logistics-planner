# Odstupanja od specifikacije i plana

## 22. 11. 2026. — Predprovjera može izostaviti izvediv nalog

**Nalaz u specifikaciji v4.1.** Specifikacija §5 propisuje zaokruživanje svake dionice na desetinku kilometra. Prema §11 i zadacima 4 i 8, predprovjera izostavlja nalog ako njegova samostalna vožnja premašuje limit na svakom dopuštenom kamionu. Nakon zaokruživanja vožnja preko mjesta utovara drugog naloga može biti kraća od izravne dionice. U tom slučaju izostavljanje krši zahtjev iz §6 da se izvrši najveći mogući broj naloga i može dovesti do pogrešnog statusa `NO_FULL_PLAN` iz §8.

### Primjer koji se može ponoviti

Lokacije su L0 (0, 0), L1 (2, 2) i L2 (4, 4). L0 je baza. Kamion A ima nosivost 3.500 kg, dva mjesta i brzinu 60 km/h. N01 prevozi M01 iz L0 u L2, a N02 prevozi M02 iz L1 u L0. Svaki stroj ima 800 kg. Limit vožnje je 11,3 min, utovar i istovar traju po 20 min i ne ulaze u limit. Djelomičan plan je isključen.

| Vožnja | Zaokružene dionice | Udaljenost | Vrijeme vožnje |
|---|---|---:|---:|
| N01 sam | L0 → L2 → L0 | 5,7 + 5,7 = 11,4 km | 684 s |
| N01 i N02 zajedno | L0 → L1 → L2 → L0 | 2,8 + 2,8 + 5,7 = 11,3 km | 678 s |

Limit je točno 678 s. Kamion u bazi utovari M01, u L1 utovari M02, u L2 istovari M01 i po povratku u bazu istovari M02. Najveći teret iznosi 1.600 kg uz dva zauzeta mjesta. Oba naloga stanu u limit. Lokalni referentni solver `qa/oracle/oracle_exact.py` za ovaj je scenarij vratio 2/2 naloga, 11,3 km i prazan popis neizvršenih naloga. Neovisni pregled potvrdio je isti problem i uz cjelobrojni limit od 10 min pri brzini od 68 km/h.

### Predložena izmjena pravila

Predprovjera može izostaviti nalog zbog vremena samo kad dokaže da i **donja granica** vremena prelazi limit na svakom dopuštenom kamionu. Za svaku od tri dionice samostalne rute donja granica može se dobiti najkraćim putem kroz mrežu već zaokruženih udaljenosti između lokacija. Ako se radnje računaju u limit, dodaje se i trajanje utovara i istovara tog naloga. Kad granica stane u limit, odluku donosi solver. Stvarne rute i validator i dalje računaju svaku prijeđenu dionicu prema §5.

Na izvornim koordinatama provjerene su donje granice od 60,2 km za N06, 34,5 km za N09 i 38,4 km za N04. Time ostaju očuvani referentni primjeri predprovjere iz zadatka 4. Predložena izmjena odnosi se samo na dokaz za izostavljanje naloga. Vlasnik je odobrio izmjenu i regresijski test s gornjim primjerom.

### Odluka (22. 11. 2026.)

Odobreno; specifikacija je ažurirana na v4.2.

- §11: donja granica, s grafom od baze i svih lokacija utovara i istovara.
- §15: test 27.
- §19: zapis izmjene.
- Plan, zadatak 4: `min_route_tenths`, `test_min_route_task_data` i `test_rounding_shortcut_not_excluded`. Za gornji primjer donja granica za N01 iznosi 11,2 km (5,6 + 5,6).
- Plan, zadatak 8: `test_rounding_shortcut_full_plan`.

Implementacija nastavlja od zadatka 1.

## 22. 11. 2026. — Prikvačeni nalozi u Python sučelju OR-Toolsa

U verziji 9.15.6755 poziv `SetAllowedVehiclesForIndex([0], index)` s Pythonovom listom javlja `TypeError` pri pretvorbi u `absl::Span< int const >`. Za utovar i istovar prikvačenog naloga koristi se `VehicleVar(index).SetValues([-1, v])`. Vrijednost `v` označava dopušteni kamion, a −1 izostavljeni nalog. U modelu s dva kamiona provjereno je da postavka za kamion 0 dopušta vrijednosti −1 i 0, a odbija 1.

## Analiza većih flota i usporedba tumačenja

Za izračun krivulje i gornje granice limita vrijede zaštite od milijun razmotrenih mogućnosti i osam sekundi. Broj potpunih raspodjela može biti velik i kada je solver brzo dokazao osnovni plan. Nakon prekida aplikacija prikazuje taj plan te navodi koje dijelove analize nije uspjela dovršiti.

Ugrađenih šest usporedbi koristi iste ulazne podatke i dnevni limit. Kao osnovu uzimaju doslovno tumačenje vremena, korištenja kamiona i cilja iz zadatka. Vlastite varijante zadane u API pozivu mijenjaju odabrana polja trenutačnog scenarija.

## Upute za lokalno pokretanje

README je prvotno navodio Node 20+, što obuhvaća i izdanja koja zaključane verzije Vitea i Vitesta ne podržavaju. Testovi sučelja koriste Node 24. Dodana je naredba za instalaciju Chromiuma koji treba Playwrightu na novom računalu. Za samo pokretanje aplikacije dovoljan je uv.

Upute sada opisuju kada su dostupna druga tumačenja i usporedba solvera, te razlikuju obvezna pravila od informativne provjere korištenja svih kamiona. Za vremensku predprovjeru vrijedi donja granica iz odobrene specifikacije v4.2.

