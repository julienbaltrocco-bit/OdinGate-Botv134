# CRM-Schnittstelle

Zwei Richtungen:
1. **Pull/Write-back:** Das CRM liest Leads und Inhalte und schreibt Vertriebsergebnisse zurück (REST v1).
2. **Push:** Die Content Engine meldet Ereignisse sofort per signiertem Webhook.

## Authentifizierung

API-Keys werden unter *Einstellungen → CRM-API & Webhooks* erzeugt. Der Klartext wird nur einmal angezeigt, gespeichert wird nur der SHA-256-Hash.

```
Authorization: Bearer ce_…
```

| Scope | Erlaubt |
|---|---|
| `leads:read` | `GET /api/v1/leads`, `GET /api/v1/leads/:id` |
| `leads:write` | `PATCH /api/v1/leads/:id` |
| `content:read` | `GET /api/v1/content` |
| `metrics:read` | `GET /api/v1/metrics` |

Fehler: `401 missing_token|invalid_token`, `403 insufficient_scope`, `404 not_found`, `422 validation_error`, `400 invalid_json`.

## Endpunkte

### `GET /api/v1/leads`

Query: `since` (ISO, filtert auf `updatedAt ≥`; für inkrementelle Synchronisation), `before`, `stage`, `type` (`coaching|partner`), `limit` (≤ 500).

```json
{ "data": [{
  "id": "uuid", "type": "partner", "name": "…", "email": "…", "instagramHandle": "@…", "company": "…",
  "message": "…", "answers": { "communitySize": "10kto50k", "monthlyVolume": "1mto10m" },
  "score": 75, "scoreReasons": ["+35 Community-Größe", "…"], "stage": "new",
  "sourceItemId": "uuid|null", "sourceLinkId": "uuid|null", "utm": {},
  "consentAt": "…", "dealValueUsd": null, "crmExternalId": null, "createdAt": "…", "updatedAt": "…"
}]}
```

### `PATCH /api/v1/leads/:id`

```json
{ "stage": "won", "crmExternalId": "HS-42", "dealValueUsd": 6000, "notes": "…" }
```

`stage ∈ new | qualified | call_scheduled | won | lost | disqualified`. Die Antwort enthält den aktualisierten Lead. Ein `lead.updated`-Webhook wird ausgelöst.
So landen Abschlüsse aus dem CRM in der Content-Attribution (Analytics → qualifizierte Leads je Beitrag/Säule).

### `GET /api/v1/content?status=published`

Inhalte mit Format, Säule, Zielgruppe, Termin, Permalink. Damit kann `sourceItemId` im CRM aufgelöst werden.

### `GET /api/v1/metrics`

Performance je Beitrag (letzte 90 Tage) inkl. Leads/Klicks sowie den Funnel nach Typ und Stage.

## Webhooks

Konfiguration unter *Einstellungen → CRM-API & Webhooks*. Events: `lead.created`, `lead.updated`, `content.approved`, `content.published`.

```
POST <deine URL>
content-type: application/json
x-ce-event: lead.created
x-ce-delivery: <uuid>            # Idempotenz-Schlüssel
x-ce-timestamp: <unix sekunden>
x-ce-signature: sha256=<hex>     # HMAC-SHA256(secret, "<timestamp>.<body>")

{ "id": "<uuid>", "event": "lead.created", "createdAt": "…", "data": { …Lead wie oben… } }
```

Prüfung im Empfänger (Node):

```js
const expected = "sha256=" + crypto.createHmac("sha256", SECRET).update(`${ts}.${rawBody}`).digest("hex");
const ok = crypto.timingSafeEqual(Buffer.from(expected), Buffer.from(sigHeader)) && Math.abs(Date.now()/1000 - ts) < 300;
```

Zustellung: über die Job-Queue mit bis zu 6 Versuchen und exponentiellem Backoff. Jede Antwort außer 2xx gilt als Fehler. Status unter *Jobs & Agenten*.

