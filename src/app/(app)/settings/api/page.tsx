import { desc, eq } from "drizzle-orm";
import { requireUser } from "@/server/auth/current";
import { action, str } from "@/server/actions";
import { db, schema } from "@/server/db";
import { API_SCOPES, createApiKey, revokeApiKey, type ApiScope } from "@/server/integrations/crm/api-keys";
import { WEBHOOK_EVENTS } from "@/server/integrations/crm/webhooks";
import { encryptSecret, randomToken } from "@/server/crypto";
import { audit } from "@/server/audit";
import { formatDateTime } from "@/lib/time";
import { Badge, Button, Card, Field, Flash, inputCls, PageHeader, Table } from "@/components/ui";

async function newKey(fd: FormData) {
  "use server";
  await action("/settings/api", "apikeys.manage", async ({ actor }) => {
    const scopes = fd.getAll("scopes").map(String).filter((s): s is ApiScope => (API_SCOPES as readonly string[]).includes(s));
    if (!scopes.length) throw new Error("Mindestens einen Scope wählen.");
    const { token } = await createApiKey(actor, str(fd, "name") || "CRM", scopes);
    return `API-Key (nur jetzt sichtbar, sicher speichern): ${token}`;
  });
}

async function revoke(fd: FormData) {
  "use server";
  await action("/settings/api", "apikeys.manage", async ({ actor }) => {
    await revokeApiKey(actor, str(fd, "id"));
    return "Key widerrufen.";
  });
}

async function newWebhook(fd: FormData) {
  "use server";
  await action("/settings/api", "apikeys.manage", async ({ actor }) => {
    const url = str(fd, "url");
    if (!/^https:\/\//.test(url)) throw new Error("Webhook-URL muss mit https:// beginnen.");
    const events = fd.getAll("events").map(String);
    if (!events.length) throw new Error("Mindestens ein Event wählen.");
    const secret = `whsec_${randomToken(24)}`;
    const [ep] = await db().insert(schema.webhookEndpoints).values({ url, events, secretEnc: encryptSecret(secret) }).returning();
    await audit(actor, "webhook.created", "webhook", ep.id, { url, events });
    return `Webhook angelegt. Signing-Secret (nur jetzt sichtbar): ${secret}`;
  });
}

async function deleteWebhook(fd: FormData) {
  "use server";
  await action("/settings/api", "apikeys.manage", async ({ actor }) => {
    await db().delete(schema.webhookEndpoints).where(eq(schema.webhookEndpoints.id, str(fd, "id")));
    await audit(actor, "webhook.deleted", "webhook", str(fd, "id"));
    return "Webhook gelöscht.";
  });
}

export default async function ApiSettingsPage({ searchParams }: { searchParams: Promise<{ ok?: string; err?: string }> }) {
  await requireUser("apikeys.manage");
  const sp = await searchParams;
  const [keys, hooks] = await Promise.all([
    db().select().from(schema.apiKeys).orderBy(desc(schema.apiKeys.createdAt)),
    db().select().from(schema.webhookEndpoints).orderBy(desc(schema.webhookEndpoints.createdAt)),
  ]);
  return (
    <>
      <PageHeader title="CRM-API & Webhooks" subtitle="Schnittstelle zum eigenen Sales-CRM – Dokumentation: docs/API.md" />
      <Flash ok={sp.ok} err={sp.err} />
      <div className="grid gap-6 lg:grid-cols-2">
        <Card title="API-Keys">
          <Table head={["Name", "Prefix", "Scopes", "Zuletzt", ""]}>
            {keys.map((k) => (
              <tr key={k.id}>
                <td className="px-2 py-2">{k.name}</td>
                <td className="px-2 py-2 font-mono text-xs">{k.prefix}…</td>
                <td className="px-2 py-2 text-xs">{k.scopes.join(", ")}</td>
                <td className="px-2 py-2 text-xs">{k.revokedAt ? <Badge color="red">widerrufen</Badge> : formatDateTime(k.lastUsedAt)}</td>
                <td className="px-2 py-2">
                  {!k.revokedAt ? (
                    <form action={revoke}><input type="hidden" name="id" value={k.id} /><Button variant="ghost">Widerrufen</Button></form>
                  ) : null}
                </td>
              </tr>
            ))}
          </Table>
          <form action={newKey} className="mt-4 space-y-3 border-t border-slate-100 pt-4">
            <Field label="Name"><input name="name" placeholder="z.B. Sales-CRM" className={inputCls} /></Field>
            <div className="flex flex-wrap gap-3 text-sm">
              {API_SCOPES.map((s) => <label key={s} className="flex items-center gap-1"><input type="checkbox" name="scopes" value={s} /> {s}</label>)}
            </div>
            <Button>Key erzeugen</Button>
          </form>
        </Card>
        <Card title="Webhooks (ausgehend, HMAC-signiert)">
          <Table head={["URL", "Events", ""]}>
            {hooks.map((h) => (
              <tr key={h.id}>
                <td className="px-2 py-2 text-xs break-all">{h.url}</td>
                <td className="px-2 py-2 text-xs">{h.events.join(", ")}</td>
                <td className="px-2 py-2"><form action={deleteWebhook}><input type="hidden" name="id" value={h.id} /><Button variant="ghost">Löschen</Button></form></td>
              </tr>
            ))}
          </Table>
          <form action={newWebhook} className="mt-4 space-y-3 border-t border-slate-100 pt-4">
            <Field label="Endpoint-URL"><input name="url" placeholder="https://crm.example.com/hooks/content-engine" className={inputCls} /></Field>
            <div className="flex flex-wrap gap-3 text-sm">
              {WEBHOOK_EVENTS.map((e) => <label key={e} className="flex items-center gap-1"><input type="checkbox" name="events" value={e} defaultChecked={e.startsWith("lead")} /> {e}</label>)}
            </div>
            <Button>Webhook anlegen</Button>
          </form>
        </Card>
      </div>
    </>
  );
}
