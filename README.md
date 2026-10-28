# Content Engine – KI-native Content- & Growth-Infrastruktur

Selbst gehostete Plattform für die Personal Brand im Crypto Business Development:
Themenrecherche → 7-Tage-Redaktionsplan → Reel-Skripte, Carousels, Story-Sets →
Rendering aus eigenem Rohmaterial → dokumentierte Freigabe → Planung/Veröffentlichung →
Messwerte → Lead-Attribution → Optimierung der nächsten Woche.

Ziel sind qualifizierte B2B-Partner- und Coaching-Anfragen, nicht Vanity Metrics.
Die Plattform ist über eine dokumentierte REST-API mit Webhooks an das eigene Sales-CRM anbindbar.

| Dokument | Inhalt |
|---|---|
| [docs/SETUP.md](docs/SETUP.md) | Lokale Inbetriebnahme, Docker, Konfiguration |
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | Bestandsaufnahme, Architektur, Datenmodell, Agenten, Entscheidungen |
| [docs/API.md](docs/API.md) | CRM-Schnittstelle (REST v1 + signierte Webhooks) |
| [docs/COMPLIANCE.md](docs/COMPLIANCE.md) | Freigabeprozess, Compliance-Regeln, DSGVO, Instagram-Richtlinien |
| [docs/BLOCKERS.md](docs/BLOCKERS.md) | Fehlende Zugänge und offene Entscheidungen |
| [docs/ROADMAP.md](docs/ROADMAP.md) | Umsetzungsstand je Phase und nächste Schritte |

## Schnellstart (lokal)

```bash
pnpm install
cp .env.example .env            # APP_ENCRYPTION_KEY + ANTHROPIC_API_KEY setzen
pnpm db:migrate
pnpm seed --email du@example.com --name "Dein Name" --password 'mindestens-12-zeichen'
pnpm dev                         # Web (http://localhost:3000) + Worker
```

Voraussetzungen: Node.js 22, pnpm 10, PostgreSQL 16, FFmpeg (mit libass/libx264). Details in [docs/SETUP.md](docs/SETUP.md).

## Tests

```bash
pnpm test           # 57 Unit- und Integrationstests (benötigt Postgres-Testdatenbank, FFmpeg)
pnpm test:e2e       # Browser-Smoke-Test gegen laufende App im Mock-Modus
pnpm lint && pnpm typecheck
```

## Stack

Next.js 16 (App Router, Server Actions) · TypeScript · PostgreSQL + Drizzle ORM ·
Claude (Anthropic SDK, strukturierte Ausgaben) · FFmpeg · satori/resvg (Carousels) ·
S3-kompatibler Speicher (optional) · Postgres-basierte Job-Queue · Docker Compose.
