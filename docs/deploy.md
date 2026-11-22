# Objava aplikacije

## Lokalna provjera Docker slike

U korijenu repozitorija pokrenite Docker i provjerite sliku koja sadrži Python 3.11, OR-Tools i izgrađeno sučelje iz `web/dist`.

```powershell
docker info --format '{{.ServerVersion}}'
docker build -t uprent-planner .
docker run --rm -p 127.0.0.1:8000:8000 uprent-planner
```

U drugom terminalu pokrenite `curl.exe http://127.0.0.1:8000/api/health`. Očekivani odgovor je `{"status":"ok"}`. Na adresi `http://127.0.0.1:8000` provjerite da se zadani plan sam prikaže s 10/10 izvršenih naloga i 182,2 km. Zaustavite lokalni kontejner kombinacijom Ctrl+C u prvom terminalu.

## Cloudflare Containers

Za ovaj demo koristi se Workers Paid račun s poddomenom `lovre-petrina2.workers.dev`. Njegov ID čuva se lokalno u `cloudflare/.env`. Objavu pokrenite nakon uspješne lokalne provjere, testova, usporedbe s referentnim solverom i provjere CI-ja.

Iz korijena repozitorija prijeđite u mapu Workera. U PowerShellu odaberite račun iz lokalne datoteke i provjerite postojeću Wrangler prijavu.

```powershell
Set-Location cloudflare
npm ci
if ($LASTEXITCODE -ne 0) { throw 'Instalacija Wrangler ovisnosti nije uspjela.' }

$accountLine = Select-String -LiteralPath .env -Pattern '^\s*CLOUDFLARE_ACCOUNT_ID\s*=\s*["'']?([0-9a-fA-F]{32})["'']?\s*(?:#.*)?$'
if (@($accountLine).Count -ne 1) { throw 'Provjerite CLOUDFLARE_ACCOUNT_ID u cloudflare/.env.' }
$env:CLOUDFLARE_ACCOUNT_ID = $accountLine.Matches[0].Groups[1].Value
npx wrangler whoami
if ($LASTEXITCODE -ne 0) { throw 'Provjera postojeće prijave nije uspjela.' }
docker info --format '{{.ServerVersion}}'
if ($LASTEXITCODE -ne 0) { throw 'Docker nije dostupan.' }
npx wrangler deploy
if ($LASTEXITCODE -ne 0) { throw 'Objava nije uspjela. Provjerite poruku Wranglera.' }
```

Worker prosljeđuje zahtjeve jednoj imenovanoj instanci na portu 8000. `max_instances: 1` ograničava broj istodobnih instanci, a `sleepAfter: "15m"` uspavljuje kontejner nakon 15 minuta neaktivnosti. Profil `basic` daje 1 GiB memorije solveru. Konfiguracija koristi politiku raspoređivanja `default` jer ona podržava ograničenje broja instanci na razini platforme. Cloudflare tu politiku označava zastarjelom. [Konfiguracija](https://developers.cloudflare.com/containers/configuration/wrangler/) · [Politike raspoređivanja](https://developers.cloudflare.com/containers/configuration/scheduling-policy/) · [Veličine instanci](https://developers.cloudflare.com/containers/platform/limits/)

Otvorite URL koji je ispisao Wrangler. Prvo pokretanje nakon objave može trajati nekoliko minuta. Stanje možete provjeriti naredbom `npx wrangler containers list`. U pregledniku potvrdite `/api/health` i provjerite 182,2 km na naslovnici. Provjereni URL upišite u README. [Objava i prva provjera](https://developers.cloudflare.com/containers/get-started/)

## Rezervna objava na Pages i Render

1. Na Renderu izradite **Web Service** iz ovog repozitorija. Odaberite Docker, besplatnu instancu, Dockerfile u korijenu, port 8000 (`PORT=8000`) i zdravstvenu provjeru `/api/health`. U varijablu `UPRENT_CORS_ORIGIN` postavite točnu HTTPS adresu Pages projekta, primjerice `https://uprent-smart-logistics-planner.pages.dev`. Render pokreće naredbu iz Dockerfilea. Zabilježite dodijeljeni URL servisa i provjerite mu `/api/health`. [Docker na Renderu](https://render.com/docs/docker)
2. U mapi `web` izgradite sučelje s adresom tog API-ja. Zamijenite primjer stvarnom adresom servisa.

   ```powershell
   $env:VITE_API_BASE_URL = 'https://vas-servis.onrender.com'
   npm ci
   npm run build
   Remove-Item Env:VITE_API_BASE_URL
   ```

3. U mapi `cloudflare`, s već odabranim računom, jednokratno izradite Pages projekt i učitajte gotov sadržaj. Ako odaberete drugo dostupno ime, prilagodite i `UPRENT_CORS_ORIGIN` na Renderu.

   ```powershell
   npx wrangler pages project create uprent-smart-logistics-planner --production-branch main
   npx wrangler pages deploy ../web/dist --project-name uprent-smart-logistics-planner --branch main
   ```

4. Otvorite dodijeljenu produkcijsku Pages adresu i provjerite zadani plan te promjenu tumačenja na 200,1 km. Besplatni Render servis uspavljuje se nakon neaktivnosti pa prvo računanje može potrajati. [Pages Direct Upload](https://developers.cloudflare.com/pages/get-started/direct-upload/) · [Besplatni servisi na Renderu](https://render.com/docs/free)
