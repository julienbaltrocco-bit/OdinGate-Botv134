# Sicherheit, Compliance & Freigabeprozess

> Die automatischen Prüfungen sind ein Sicherheitsnetz, keine Rechtsberatung. Insbesondere Trading-Inhalte,
> Werbekennzeichnung und Einwilligungstexte sollten einmalig anwaltlich geprüft werden.

## Freigabe (menschlich, dokumentiert)

- **Nichts wird ohne ausdrückliche menschliche Freigabe veröffentlicht.** API-Publishing ist standardmäßig aus (`INSTAGRAM_PUBLISHING_ENABLED=false`).
- Jede Freigabe wird in `approvals` gespeichert: Version, Entscheidung, Kommentar, Prüfer und dessen Rolle, Compliance-Bestätigung. Zusätzlich wird sie ins Audit-Log geschrieben.
- Eine Freigabe gilt nur für genau die geprüfte Version. Jede spätere Änderung setzt den Inhalt auf „Entwurf“ zurück.
- Vier-Augen-Prinzip: Eigene manuelle Änderungen kann niemand selbst freigeben (Ausnahme: Admin).
- Vor jeder Veröffentlichung, auch der automatischen, wird erneut geprüft, ob die aktuelle Version freigegeben ist.

## Automatische Inhaltsprüfung (`src/server/compliance/checker.ts`)

| Regel | Wirkung |
|---|---|
| Garantie-/„risikofrei“-Aussagen, Rendite pro Zeitraum (z.B. „10 % pro Monat“) | **blockiert** die Freigabe |
| Einkommensversprechen an die Zielgruppe („du kannst 10k im Monat verdienen“, „passives Einkommen“) | **blockiert** |
| Konkrete Börse oder Ref-Link ohne Kennzeichnung in der Caption | **blockiert** |
| Trading-Bezug (Signale, Hebel, Futures, Kursziele …) | Compliance-Sign-off Pflicht, Warnung bei fehlendem Risikohinweis |
| Geldbeträge, Testimonials mit Zahlen | Warnung: nur belegt bzw. mit Einwilligung |
| Hype-/Druckformulierungen, Luxus-Inszenierung, Emojis | Warnung (Brand Voice) |

Die Schreib-Agenten werden zusätzlich angewiesen, keine Zahlen oder Testimonials zu erfinden. Zu belegende Aussagen landen sichtbar unter „Vor Veröffentlichung belegen“.

## Instagram

- Es werden ausschließlich offizielle Schnittstellen genutzt: Instagram Platform API (Container → Status → `media_publish`, Insights, `content_publishing_limit`).
- Kein Scraping, keine Login-Bots, keine automatisierten DMs oder Kommentare.
- Stories mit interaktiven Stickern werden manuell gepostet, weil die API keine Sticker unterstützt.
- Access-Tokens werden vor dem Speichern gegen die API geprüft und AES-256-GCM-verschlüsselt abgelegt.

## Medienrechte

- Jeder Upload braucht einen Rechte-Status (`own`, `licensed`, `unknown`). Material mit `unknown` wird **nicht gerendert**.
- Musik nur mit Lizenz (Lizenznummer in der Notiz). Bei erkennbaren Personen ist eine Einwilligung nötig. Vertrauliche Bildschirminhalte (Deal-Konditionen, Partnernamen) vor dem Upload schwärzen.

## DSGVO

- **Formulare:** Pflicht-Einwilligung mit versioniertem Text, Zeitstempel und Text werden am Lead gespeichert. Honeypot statt Tracking-Captcha. Links zu Datenschutz und Impressum (`PRIVACY_URL`, `IMPRINT_URL`) sind Pflicht vor dem Livegang.
- **Tracking:** `/r/<code>` speichert weder IP noch vollständigen User-Agent und setzt keine Cookies. Erfasst werden nur Geräteklasse und Referrer-Host.
- **Datenminimierung:** Der Research Agent erhält nur den Nachrichtentext von Leads, keine Namen oder E-Mails.
- **Löschung:** Unter Lead → „Daten löschen“ wird der Lead anonymisiert, die Statistik bleibt erhalten. Der Vorgang wird im Audit-Log protokolliert.
- **Auftragsverarbeitung:** Inhalte gehen zur Generierung an Anthropic. Personenbezogene Daten Dritter gehören nicht in Briefings oder Quellen. Für den Produktivbetrieb ist ein AV-Vertrag mit Anthropic abzuschließen bzw. zu prüfen.

## Werbung & Interessenkonflikte

Bei Nennung konkreter Börsen und Ref-Links wird eine Kennzeichnung erzwungen. Die Standardtexte (Brand-Einstellungen) sind:
„Hinweis: Ich arbeite mit Kryptobörsen auf Provisionsbasis zusammen (Werbung).“ und „Keine Anlageberatung. Krypto-Handel ist mit hohem Verlustrisiko verbunden.“
Das Coaching-Formular weist darauf hin, dass es keine Einkommensgarantie gibt und Deal-Beteiligungen nur vertraglich geregelt erfolgen.

## Technische Sicherheit

- Passwörter mit scrypt gehasht. Sessions serverseitig, Cookie `httpOnly` und `sameSite=lax` (`secure` unter HTTPS).
- Jede Server Action und jede API-Route prüft Rolle bzw. Scope serverseitig. Der Proxy (Middleware) ist nur eine Vorab-Weiterleitung.
- Secrets nur über Umgebungsvariablen. Gespeicherte Tokens und Webhook-Secrets sind AES-256-GCM-verschlüsselt, API-Keys nur als Hash gespeichert.
- Das Audit-Log ist per Datenbank-Trigger nur anfügbar (kein UPDATE/DELETE).
- Medien werden nur an angemeldete Benutzer ausgeliefert. Storage-Keys sind gegen Path-Traversal geschützt. Uploads haben ein Größenlimit (`MAX_UPLOAD_MB`).
