# Umsetzungsstand & Roadmap

Legende: ✅ implementiert und automatisiert getestet · 🟡 implementiert, aber nicht gegen den echten Dienst verifiziert · ⬜ offen

## Definition of Done (MVP)

| Kriterium | Stand | Nachweis |
|---|---|---|
| Anwendung lokal startbar | ✅ | `pnpm dev`; Build und Start geprüft |
| Wochenplan generierbar | ✅ (Mock-LLM) / 🟡 (echtes Claude) | `tests/integration/workflow.test.ts`, E2E-Smoke-Test |
| Skripte und Carousel-Entwürfe erstellbar | ✅ | Integrationstest + E2E (inkl. gerenderter Slides) |
| Medien verwaltbar | ✅ | Upload (Streaming), Rechte-Status, Vorschau, Löschen |
| Mindestens ein Reel aus Rohmaterial gerendert | ✅ | `tests/integration/media.test.ts`: 2 Clips (16:9 + 9:16, einer ohne Ton) → 1080×1920 H.264/AAC mit Untertiteln, Hook/CTA, Kurzvariante, Thumbnail |
| Alle Inhalte im Dashboard prüfbar | ✅ | Kalender, Editor, Vorschau, Freigabe-Queue |
| Freigabe dokumentiert | ✅ | `approvals` + Audit-Log, versionsgebunden. E2E-Test |
| Tests und Setup-Anleitung | ✅ | 37 Unit-, 20 Integrations-, 2 E2E-Tests · docs/SETUP.md |

## Phasen

### Phase 1 – Architektur & MVP
- ✅ Datenmodell, Migrationen, Audit-Log (nur anfügbar)
- ✅ Benutzer, Rollen (5), Berechtigungsmatrix, Sessions
- ✅ Redaktionskalender, Ideen-Backlog mit Quellen
- ✅ Research, Strategy, Scriptwriting, Creative Director, Carousel, Story, Brand Voice (🟡 Prompt-Qualität mit echtem Claude prüfen)
- ✅ Compliance-Prüfung, Freigabe-Workflow, Vier-Augen-Prinzip

### Phase 2 – Content-Produktion
- ✅ Medienbibliothek (lokal), 🟡 S3-Treiber (implementiert, nicht gegen echten Bucket getestet)
- ✅ Reel-Pipeline FFmpeg, Untertitel aus Skript/SRT, Varianten
- 🟡 Automatische Transkription (whisper.cpp-Adapter)
- ✅ Carousel-Generator, Story-Vorlagen
- ⬜ Animierte Reel-Templates (z.B. Remotion, Lizenzentscheidung), B-Roll-Zuordnung per KI, Schnitt auf Satzgrenzen

### Phase 3 – Publishing & Analytics
- ✅ Freigabe → Einplanung → manueller Veröffentlichungsschritt mit Live-Link
- 🟡 Instagram-Publishing (Reels, Carousels), Quota-Check, Retry/Fehlerstatus, tägliche Insights-Synchronisation
- ✅ Analytics-Dashboard (manuelle und API-Metriken, Leads/Klicks je Beitrag, Funnel)
- ⬜ OAuth-Flow statt Token-Einfügen, automatische Token-Verlängerung (Client-Methode vorhanden)

### Phase 4 – Optimierung & Integration
- ✅ Optimization Agent (nur mit Daten), Übernahme in die Planung
- ✅ Attribution über Tracking-Links und Formulare, Lead-Scoring
- ✅ CRM-REST-API v1 + signierte Webhooks
- ⬜ CRM-spezifisches Mapping (nach Klärung des CRMs), Kohortenanalyse (Content → Abschluss → Provisionen)
- ⬜ Evals für Prompt-Qualität (Hook-Stärke, Brand-Voice-Treue) auf Basis freigegebener und abgelehnter Versionen

## Empfohlene nächste Schritte

1. API-Key hinterlegen, eine echte Woche generieren und 5–10 echte Beispieltexte in Brand Voice eintragen.
2. Rechtstexte setzen, Tracking-Link als Link in Bio verwenden.
3. Meta-App und S3 einrichten, danach API-Publishing erst für Carousels aktivieren, dann für Reels.
4. CRM festlegen, Webhook verbinden und Stages zurückschreiben, damit der Optimization Agent auf Abschlüsse statt nur auf Leads optimiert.
