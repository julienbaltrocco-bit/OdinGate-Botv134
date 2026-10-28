# Blocker & offene Entscheidungen

Stand der MVP-Lieferung. Nichts davon wird in der Software simuliert. Das Dashboard (Übersicht und Einstellungen → Integrationen) zeigt den jeweiligen Status live an.

## Zugänge (von dir bereitzustellen)

| # | Blocker | Auswirkung bis zur Lösung | Was nötig ist |
|---|---|---|---|
| 1 | **Anthropic API-Key** | Echte Generierung nicht möglich. In der Entwicklung lief alles mit `LLM_PROVIDER=mock`: gekennzeichnete `[MOCK]`-Platzhalter mit Banner im UI. Die Qualität echter Claude-Ausgaben ist daher noch **nicht** verifiziert. | `ANTHROPIC_API_KEY` setzen, `LLM_PROVIDER=anthropic`. Danach einen Wochenplan erzeugen und Prompts anhand echter Ergebnisse nachschärfen. |
| 2 | **Instagram / Meta** | Veröffentlichung und Insights laufen manuell (Live-Link und Messwerte im Beitrag erfassen). Der API-Client ist implementiert und gegen dokumentierte Antwortformate getestet, aber **nicht gegen die Live-API**. | Instagram Business- oder Creator-Konto, Meta-App mit „Instagram API with Instagram Login“, Berechtigungen `instagram_business_basic`, `instagram_business_content_publish`, `instagram_business_manage_insights`, ggf. App-Review. Token unter Einstellungen → Integrationen hinterlegen. |
| 3 | **Öffentlich erreichbarer Medienspeicher** | Instagram lädt Medien per URL, deshalb ist API-Publishing mit lokalem Speicher unmöglich. | S3-kompatibler Bucket (MinIO hinter HTTPS, Cloudflare R2, AWS S3), `STORAGE_DRIVER=s3`. Signierte URLs mit 1 h Gültigkeit sind implementiert. |
| 4 | **Rechtstexte** | Bewerbungsformulare sollten nicht öffentlich verlinkt werden. | `PRIVACY_URL`, `IMPRINT_URL`. Einwilligungstext (`src/server/leads/leads.ts`) und Werbekennzeichnung anwaltlich prüfen lassen. AV-Vertrag mit Anthropic. |
| 5 | **Sales-CRM-Details** | Generische REST-API und Webhooks sind fertig, eine CRM-spezifische Zuordnung von Feldern und Pipelines fehlt noch. | Welches CRM (HubSpot, Pipedrive, eigenes)? Pipeline-Stages und Pflichtfelder. |

## Infrastruktur-Entscheidungen

| # | Thema | Stand / Empfehlung |
|---|---|---|
| 6 | **Hosting** | Docker Compose ist vorbereitet, das Image wurde aber nicht gebaut, weil Docker Hub in der Entwicklungsumgebung gesperrt war. Empfehlung: kleiner VPS in der EU (z.B. Hetzner) mit Compose und Caddy/Traefik für TLS. Vor dem Livegang einmal `docker compose up --build` verifizieren. |
| 7 | **Automatische Transkription** | Adapter für selbst gehostetes whisper.cpp ist vorhanden (`WHISPER_CPP_BIN`, `WHISPER_CPP_MODEL`), aber **nicht verifiziert**, weil der Modell-Download hier gesperrt war. Bis dahin funktionieren Untertitel aus dem Skript (Timing geschätzt) und SRT/VTT-Upload. |
| 8 | **Remotion** | Bewusst nicht eingesetzt. Für Firmen ab 4 Mitarbeitern ist eine kostenpflichtige Lizenz nötig. FFmpeg deckt das MVP ab. Entscheidung offen, falls animierte Templates gewünscht sind. |
| 9 | **Backups** | Postgres-Dump und Medien-Bucket sind nicht automatisiert. Vor dem Produktivbetrieb einrichten. |
| 10 | **API-Version Instagram** | `INSTAGRAM_API_VERSION` ist auf `v23.0` voreingestellt. Die aktuelle Version auf developers.facebook.com prüfen (Seite war in der Entwicklungsumgebung nicht erreichbar) und ggf. anpassen. Metrik-Namen ändern sich zwischen Versionen (z.B. `impressions`/`plays` → `views`). Der Client verwirft nicht unterstützte Metriken einzeln. |
