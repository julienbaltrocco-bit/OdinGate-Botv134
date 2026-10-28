# Inbetriebnahme

## 1. Voraussetzungen

| Komponente | Version | Hinweis |
|---|---|---|
| Node.js | 22 | |
| pnpm | 10 | `corepack enable` |
| PostgreSQL | 16 | lokal oder per Docker |
| FFmpeg | ≥ 6 | mit `libass`, `libx264`, `aac` (Ubuntu/Debian: `apt install ffmpeg`) |

## 2. Konfiguration

```bash
cp .env.example .env
node -e "console.log(require('crypto').randomBytes(32).toString('base64'))"   # → APP_ENCRYPTION_KEY
```

Wichtige Variablen (vollständige Liste: `.env.example`, Validierung: `src/server/env.ts`):

| Variable | Zweck |
|---|---|
| `DATABASE_URL` | Postgres-Verbindung |
| `APP_URL` | Öffentliche Basis-URL (Tracking-Links, Redirects) |
| `APP_ENCRYPTION_KEY` | 32 Byte, AES-256-GCM für gespeicherte Tokens/Secrets. **Nicht verlieren** – sonst sind gespeicherte Tokens unlesbar. |
| `LLM_PROVIDER` | `anthropic` (echt) oder `mock` (gekennzeichnete Platzhalter für Demo/Tests) |
| `ANTHROPIC_API_KEY` | Claude API-Key |
| `ANTHROPIC_MODEL` / `ANTHROPIC_EFFORT` | Standard `claude-opus-5-5` / `high` |
| `RESEARCH_WEB_SEARCH` | `true` erlaubt dem Research Agent die Websuche von Anthropic (mit gespeicherten Quellen-URLs) |
| `STORAGE_DRIVER` | `local` (Standard) oder `s3` |
| `PRIVACY_URL`, `IMPRINT_URL` | Pflicht, bevor Bewerbungsformulare öffentlich verlinkt werden |
| `INSTAGRAM_PUBLISHING_ENABLED` | `false` (Standard). Erst aktivieren, wenn Meta-Zugang + S3 bereitstehen |

Secrets gehören ausschließlich in `.env` bzw. den Secret-Store des Servers, nie ins Repository (`.env*` ist in `.gitignore`).

## 3. Lokal starten

```bash
pnpm install
createdb contentengine            # bzw. per psql
pnpm db:migrate
pnpm seed --email du@example.com --name "Dein Name" --password 'mindestens-12-zeichen'
pnpm dev
```

`pnpm dev` startet Web-App und Worker parallel. Getrennt: `pnpm dev:web` und `pnpm worker`.
Ohne laufenden Worker werden Generierung, Rendering und Webhooks nur eingereiht, nicht ausgeführt.

Produktion ohne Docker: `pnpm build && pnpm start` plus `pnpm worker` als eigener Prozess (z.B. systemd).

## 4. Docker (selbst gehostet)

```bash
cp .env.example .env    # zusätzlich POSTGRES_PASSWORD, S3_* setzen
docker compose up -d --build
docker compose run --rm web pnpm seed --email du@example.com --password '…'
```

Dienste: `db` (Postgres 16), `minio` (S3-kompatibel), `migrate` (einmalig), `web` (Port 3000), `worker`.
Für MinIO als Speicher: `STORAGE_DRIVER=s3`, `S3_ENDPOINT=http://minio:9000`, Bucket einmalig anlegen
(MinIO-Konsole Port 9001 oder `mc mb`). Für Instagram-Publishing muss der Bucket-Endpoint öffentlich per HTTPS
erreichbar sein (Meta lädt Medien per URL), z.B. über einen Reverse Proxy.

> Hinweis: Das Docker-Image wurde in der Entwicklungsumgebung nicht gebaut (Docker Hub dort gesperrt).
> Die Compose-Datei ist vor dem ersten produktiven Einsatz einmal zu verifizieren – siehe docs/BLOCKERS.md.

## 5. Erster Durchlauf (Definition of Done)

1. **Einstellungen → Brand Voice**: Name, Handle, eigene Beispieltexte eintragen.
2. **Ideen & Recherche**: Quellen (häufige Fragen aus Calls, Einwände, Notizen) erfassen, Research Agent starten.
3. **Redaktionskalender → Plan für diese Woche erzeugen** (5 Reels, 2 Carousels, 7 Story-Sets, alle Entwürfe).
4. **Medienbibliothek**: Rohmaterial hochladen (Rechte-Status angeben).
5. **Inhalt öffnen**: Skript bearbeiten, Reel aus Rohmaterial rendern bzw. Slides rendern, zur Freigabe einreichen.
6. **Freigaben**: Reviewer/Compliance prüft, gibt frei oder fordert Änderungen an (dokumentiert, versionsgebunden).
7. **Einplanen** und nach dem Posten den Live-Link hinterlegen (manueller Schritt, solange API-Publishing aus ist).

## 6. Tests

```bash
createdb contentengine_test       # einmalig; wird bei jedem Lauf zurückgesetzt
pnpm test                         # Unit + Integration (TEST_DATABASE_URL überschreibbar)
```

E2E (Browser) gegen eine laufende Instanz im Mock-Modus:

```bash
LLM_PROVIDER=mock pnpm build && pnpm start &   # plus: pnpm worker &
E2E_EMAIL=… E2E_PASSWORD=… pnpm test:e2e
```
