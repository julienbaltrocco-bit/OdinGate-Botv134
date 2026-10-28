# Architektur

## 1. Bestandsaufnahme (Ausgangslage)

- Repository `OdinGate-Botv134`: lokal und remote leer, keine Commits und kein bestehender Code. Daher Neuaufbau ohne Altlasten.
- Verfügbare Infrastruktur in der Entwicklungsumgebung: Node 22, pnpm 10, PostgreSQL 16, FFmpeg 6.1 (libass, libx264, AAC), Chromium für Tests.
- Nicht verfügbar: Anthropic-API-Key, Meta/Instagram-Zugang, öffentlicher Medienspeicher. Außerdem sind Docker Hub, HuggingFace und developers.facebook.com in dieser Umgebung per Netzwerk gesperrt.
- Für das eigene Sales-CRM gibt es noch keine Spezifikation. Deshalb gibt es eine generische, dokumentierte Schnittstelle (REST + Webhooks).

## 2. Überblick

```
                    ┌─────────────────────── Next.js 16 (web) ────────────────────────┐
 Team (Browser) ──▶ │ Dashboard (Server Components + Server Actions, RBAC je Aktion) │
 Öffentlichkeit ──▶ │ /apply/* Formulare · /r/<code> Tracking-Redirect                │
 Sales-CRM ───────▶ │ /api/v1/* (API-Keys, Scopes)                                   │
                    └──────────────┬──────────────────────────────────┬──────────────┘
                                   │ enqueue                          │ read/write
                                   ▼                                  ▼
                    ┌──────────────────────┐            ┌──────────────────────────┐
                    │ jobs (Postgres-Queue)│◀──claim────│ worker (Node, tsx)        │
                    └──────────────────────┘            │  Agenten · FFmpeg · satori│
                                                        │  Instagram · Webhooks      │
                    ┌──────────────────────┐            └───────┬──────────┬───────┘
                    │ PostgreSQL (alles)   │◀───────────────────┘          │
                    └──────────────────────┘                    Claude API · Instagram API
                    ┌──────────────────────┐                    CRM-Webhooks
                    │ Medien: lokal | S3   │◀── Uploads, Renderings
                    └──────────────────────┘
```

Eine Codebasis und ein Datenmodell. Web-App und Worker sind zwei Prozesse desselben Images.

## 3. Technische Entscheidungen

| Entscheidung | Begründung |
|---|---|
| **Ein Next.js-Projekt statt Monorepo** | Kleines Team, eine Domäne. Agenten, Rendering und API teilen Datenmodell und Typen. Weniger Build-Komplexität. |
| **Agenten in TypeScript** statt Python | Ein Stack, geteilte Zod-Schemas zwischen KI-Ausgabe, Editor und Renderer. |
| **Job-Queue in Postgres** (`FOR UPDATE SKIP LOCKED`) statt Redis/SaaS | Keine zusätzliche Infrastruktur. Jobs sind auditierbar, haben Retries mit Backoff, und hängengebliebene Jobs werden wieder aufgenommen. |
| **Claude mit strukturierten Ausgaben** (`messages.parse`-Äquivalent über Streaming + Zod) | Validierte JSON-Ausgaben statt Freitext-Parsing. Adaptive Thinking und konfigurierbarer Effort. Server-seitige Fallbacks bei Ablehnungen (`fallbacks: "default"`) sind aktiv. |
| **Jeder KI-Aufruf in `agent_runs`** | Nachvollziehbarkeit: Input, Output, Modell, Tokens, Dauer, Quellen. |
| **FFmpeg direkt** für Reels, **Remotion vorerst nicht** | FFmpeg deckt Schnitt, 9:16-Crop, Untertitel (ASS), Overlays, Logo, Musik und Loudness ab. Remotion braucht Chromium-Rendering und für Firmen ab 4 Mitarbeitern eine kostenpflichtige Lizenz. Es ist sinnvoll für animierte Templates in Phase 2+, aber erst nach einer Lizenzentscheidung (siehe BLOCKERS). |
| **satori + resvg** für Carousels/Story-Vorlagen | Deterministisch, ohne Browser. Brand-Farben und Schrift (Inter, OFL) kommen aus dem Brand-Profil. |
| **Eigene Session-Auth** (scrypt, DB-Sessions, httpOnly-Cookie) | Keine externe Identity-Abhängigkeit. Rollen und Audit sind integriert. |
| **Tracking-Links + eigene Formulare** für Attribution | Rechtlich sauber (keine DMs automatisieren, keine Cookies/IP-Speicherung). Funktioniert ohne Instagram-API. |
| **Manuelle Schritte, wo Automatisierung nicht erlaubt oder sinnvoll ist** | Story-Sticker (nicht per API), Dreh, Veröffentlichung solange kein Meta-Zugang besteht, Freigaben. |

## 4. Datenmodell (PostgreSQL, `src/server/db/schema.ts`)

| Bereich | Tabellen |
|---|---|
| Identität & Governance | `users` (Rolle), `sessions`, `audit_logs` (per Trigger nur anfügbar), `api_keys` (nur Hashes) |
| Marke & Recherche | `brand_profile` (Settings JSON + abgeleiteter Stil), `research_sources`, `topics` (mit Quellenreferenzen) |
| Planung & Inhalt | `content_plans`, `content_items` (Format, Säule, Zielgruppe, CTA-Ziel, Status, Termin), `content_versions` (versionierter Body + Caption + Compliance-Report), `approvals` (Entscheidung, gebunden an Version) |
| Produktion | `media_assets` (Rechte-Status, Metadaten), `renders` (Eingaben, Log, Ausgaben) |
| Ausführung | `jobs`, `agent_runs` |
| Growth | `tracking_links`, `link_clicks` (anonym), `leads` (Einwilligung, Score, Stage, CRM-ID), `post_metrics`, `recommendations` |
| Integrationen | `integrations` (Instagram, Token verschlüsselt), `webhook_endpoints` (Secret verschlüsselt) |

## 5. Agenten (`src/server/agents/*`)

| Agent | Umsetzung | Ein-/Ausgabe |
|---|---|---|
| Research | Claude, strukturierte Ausgabe; optional Websuche mit Zitaten | Eingabe: interne Quellen, anonymisierte Lead-Fragen, Performance. Ausgabe: priorisierte `topics` mit geprüften Quellen-Referenzen |
| Strategy | Claude + harte Regeln in Code (`plan-rules.ts`), max. 2 Versuche mit Fehler-Feedback | 7-Tage-Plan: genau 5 Reels, 2 Carousels, 7 Story-Sets |
| Scriptwriting | Claude | Reel-Skript (Hook, Segmente mit Dauer, Overlay, CTA, Caption, zu belegende Aussagen) |
| Creative Director | Claude | Produktionsbriefing: Shotlist, Rohmaterial, Schnitt, B-Roll, Musik, manuelle Schritte |
| Carousel | Claude (Text) + satori (Rendering) | Slides 1080×1350 PNG |
| Story | Claude (Text) + satori (Vorlagen) | 3–5 Frames je Tag, Vorlagen 1080×1920 |
| Production | deterministisch: FFmpeg | Reel 1080×1920 H.264/AAC mit Untertiteln, Hook/CTA, Logo, Musik, Varianten, Thumbnail |
| Publishing | deterministisch: Scheduler + Instagram-Container-Flow | nur freigegebene aktuelle Version, Quota-Check |
| Analytics | deterministisch: Aggregation | Instagram-Insights (falls verbunden) oder manuelle Erfassung + Leads/Klicks |
| Optimization | Claude, nur mit Messdaten | Empfehlungen mit Evidenz und Sicherheit. Übernommene Empfehlungen fließen in den nächsten Plan ein |
| Brand Voice | Claude | Stilleitfaden aus freigegebenen Texten und eigenen Beispielen |

Alle Schreib-Agenten erhalten denselben Brand-Kontext und dieselben Guardrails (`src/server/brand.ts`):
keine erfundenen Zahlen und Testimonials, Platzhalter `[ZAHL BELEGEN]`, Kennzeichnung bei Börsenbezug, keine Anlageberatung.

## 6. Workflow (Statusmaschine `src/server/workflow/state.ts`)

```
planned → draft → in_review → approved → scheduled → publishing → published
                      │  ↘ changes_requested → draft          ↘ failed → scheduled
                      └→ rejected → draft
Jede Bearbeitung nach der Freigabe → draft (Freigabe gilt nur für die freigegebene Version)
```

Regeln in `src/server/workflow/content.ts`:
- Freigabe nur durch `reviewer`, `compliance` oder `admin`. Editoren können nicht freigeben.
- Blockierende Compliance-Befunde verhindern die Freigabe.
- Inhalte mit Trading-/Börsenbezug erfordern die Rolle `compliance` und eine ausdrückliche Bestätigung.
- Vier-Augen-Prinzip: Eigene manuelle Änderungen kann man nicht selbst freigeben (außer als Admin).
- Veröffentlichung prüft zur Laufzeit erneut, dass die aktuelle Version freigegeben ist.

## 7. Rollen

| Rolle | Darf |
|---|---|
| admin | alles inkl. Benutzer, Integrationen, API-Keys |
| editor | Inhalte erstellen/bearbeiten/generieren, Medien, Leads, Planung (nicht freigeben) |
| reviewer | Inhalte freigeben/ablehnen |
| compliance | wie reviewer + Pflicht-Sign-off für Trading-/Finanzinhalte + Audit-Log |
| viewer | lesen (ohne Leads) |

Die vollständige Matrix steht in `src/server/auth/rbac.ts` und wird unter Einstellungen → Team & Rollen angezeigt.

## 8. Verzeichnisstruktur

```
src/app/(app)/…        Dashboard-Seiten (Server Components + Server Actions)
src/app/(public)/…     Login, Bewerbungsformulare
src/app/api/…          Medien-Streaming/Upload, Health, CRM-API v1
src/app/r/[code]       Tracking-Redirect
src/server/agents      KI-Agenten
src/server/ai          Claude-Client, Mock-Provider
src/server/workflow    Statusmaschine, Versionen, Freigaben, Drafting, Formulare
src/server/media       Storage, FFmpeg, Untertitel, Reel-Renderer, Transkriptions-Adapter
src/server/carousel    Slide- und Story-Rendering
src/server/jobs        Queue, Handler, Worker
src/server/leads       Links, Leads, Qualifizierung
src/server/integrations Instagram, CRM (API-Keys, Webhooks)
drizzle/               SQL-Migrationen
tests/                 unit, integration, e2e
```
