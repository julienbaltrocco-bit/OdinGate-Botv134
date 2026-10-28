import Link from "next/link";
import { desc, eq, sql } from "drizzle-orm";
import { requireUser } from "@/server/auth/current";
import { action, str } from "@/server/actions";
import { db, schema } from "@/server/db";
import { createLink, linkUrl, type Placement } from "@/server/leads/links";
import { audit } from "@/server/audit";
import { formatDateTime } from "@/lib/time";
import { Badge, Button, Card, Empty, Field, Flash, inputCls, PageHeader, Table } from "@/components/ui";

async function newLink(fd: FormData) {
  "use server";
  await action("/leads", "leads.write", async ({ actor }) => {
    const destination = str(fd, "destination") === "url" ? str(fd, "url") : str(fd, "destination");
    if (!["coaching", "partner"].includes(destination)) {
      try {
        const u = new URL(destination);
        if (u.protocol !== "https:") throw new Error();
      } catch {
        throw new Error("Ziel-URL muss mit https:// beginnen.");
      }
    }
    const link = await createLink({ label: str(fd, "label") || "Link", destination, placement: str(fd, "placement") as Placement, itemId: str(fd, "itemId") || null });
    await audit(actor, "link.created", "tracking_link", link.id, { destination });
    return `Link erstellt: ${linkUrl(link.code)}`;
  });
}

const STAGE_COLORS: Record<string, "slate" | "blue" | "green" | "amber" | "red" | "violet"> = {
  new: "blue",
  qualified: "violet",
  call_scheduled: "amber",
  won: "green",
  lost: "slate",
  disqualified: "red",
};

export default async function LeadsPage({ searchParams }: { searchParams: Promise<{ ok?: string; err?: string; type?: string }> }) {
  await requireUser("leads.read");
  const sp = await searchParams;
  const leads = await db()
    .select({ lead: schema.leads, itemTitle: schema.contentItems.title, linkLabel: schema.trackingLinks.label })
    .from(schema.leads)
    .leftJoin(schema.contentItems, eq(schema.contentItems.id, schema.leads.sourceItemId))
    .leftJoin(schema.trackingLinks, eq(schema.trackingLinks.id, schema.leads.sourceLinkId))
    .where(sp.type === "coaching" || sp.type === "partner" ? eq(schema.leads.type, sp.type) : undefined)
    .orderBy(desc(schema.leads.createdAt))
    .limit(200);
  const links = await db().execute(sql`
    SELECT tl.*, ci.title AS item_title,
      (SELECT count(*)::int FROM link_clicks lc WHERE lc.link_id = tl.id) AS clicks,
      (SELECT count(*)::int FROM leads l WHERE l.source_link_id = tl.id) AS leads
    FROM tracking_links tl LEFT JOIN content_items ci ON ci.id = tl.item_id ORDER BY tl.created_at DESC LIMIT 100`);
  type LinkRow = { id: string; code: string; label: string; destination: string; placement: string; item_id: string | null; item_title: string | null; clicks: number; leads: number };

  return (
    <>
      <PageHeader title="Leads & Links" subtitle="Anfragen aus den Bewerbungsformularen, zugeordnet zu Inhalten über Tracking-Links" />
      <Flash ok={sp.ok} err={sp.err} />
      <Card title="Formulare" className="mb-6">
        <div className="grid gap-2 text-sm md:grid-cols-2">
          <div>Coaching-Bewerbung: <code className="rounded bg-slate-100 px-1">{linkUrl("").replace(/\/r\/$/, "")}/apply/coaching</code></div>
          <div>Partnerschaftsanfrage: <code className="rounded bg-slate-100 px-1">{linkUrl("").replace(/\/r\/$/, "")}/apply/partner</code></div>
        </div>
        <p className="mt-2 text-xs text-slate-500">Für Attribution immer einen Tracking-Link (/r/…) statt der direkten Formular-URL verwenden.</p>
      </Card>
      <Card title={`Leads (${leads.length})`} className="mb-6" actions={
        <div className="flex gap-2 text-xs">
          <Link href="/leads" className="underline">Alle</Link>
          <Link href="/leads?type=coaching" className="underline">Coaching</Link>
          <Link href="/leads?type=partner" className="underline">Partner</Link>
        </div>
      }>
        {leads.length ? (
          <Table head={["Eingang", "Typ", "Name", "Score", "Stage", "Quelle", "CRM"]}>
            {leads.map(({ lead, itemTitle, linkLabel }) => (
              <tr key={lead.id}>
                <td className="px-2 py-2 text-xs">{formatDateTime(lead.createdAt)}</td>
                <td className="px-2 py-2"><Badge>{lead.type === "coaching" ? "Coaching" : "Partner"}</Badge></td>
                <td className="px-2 py-2"><Link href={`/leads/${lead.id}`} className="font-medium hover:underline">{lead.name}</Link><div className="text-xs text-slate-500">{lead.company ?? lead.instagramHandle ?? ""}</div></td>
                <td className="px-2 py-2 font-semibold">{lead.score}</td>
                <td className="px-2 py-2"><Badge color={STAGE_COLORS[lead.stage]}>{lead.stage}</Badge></td>
                <td className="px-2 py-2 text-xs">{itemTitle ? <Link className="underline" href={`/content/${lead.sourceItemId}`}>{itemTitle}</Link> : linkLabel ?? "direkt"}</td>
                <td className="px-2 py-2 text-xs">{lead.crmExternalId ?? "–"}</td>
              </tr>
            ))}
          </Table>
        ) : (
          <Empty>Noch keine Leads.</Empty>
        )}
      </Card>
      <div className="grid gap-6 lg:grid-cols-3">
        <Card title="Tracking-Link erstellen">
          <form action={newLink} className="space-y-3">
            <Field label="Bezeichnung"><input name="label" required placeholder="z.B. Link in Bio November" className={inputCls} /></Field>
            <Field label="Ziel">
              <select name="destination" className={inputCls}>
                <option value="coaching">Coaching-Bewerbung</option>
                <option value="partner">Partnerschaftsanfrage</option>
                <option value="url">Externe URL (z.B. Terminbuchung)</option>
              </select>
            </Field>
            <Field label="Externe URL (nur bei 'Externe URL')"><input name="url" placeholder="https://…" className={inputCls} /></Field>
            <Field label="Platzierung">
              <select name="placement" className={inputCls}>
                <option value="bio">Link in Bio</option>
                <option value="story_link">Story-Link-Sticker</option>
                <option value="caption">Caption (Text)</option>
                <option value="dm_manual">Manuelle DM-Antwort</option>
                <option value="other">Sonstiges</option>
              </select>
            </Field>
            <Field label="Inhalts-ID (optional)"><input name="itemId" className={inputCls} /></Field>
            <Button>Erstellen</Button>
          </form>
        </Card>
        <Card title="Tracking-Links" className="lg:col-span-2">
          {links.rows.length ? (
            <Table head={["Link", "Ziel", "Inhalt", "Klicks", "Leads"]}>
              {(links.rows as LinkRow[]).map((l) => (
                <tr key={l.id}>
                  <td className="px-2 py-2"><div className="font-medium">{l.label}</div><code className="text-xs">{linkUrl(l.code)}</code></td>
                  <td className="px-2 py-2 text-xs">{l.destination} · {l.placement}</td>
                  <td className="px-2 py-2 text-xs">{l.item_id ? <Link className="underline" href={`/content/${l.item_id}`}>{l.item_title}</Link> : "–"}</td>
                  <td className="px-2 py-2">{l.clicks}</td>
                  <td className="px-2 py-2">{l.leads}</td>
                </tr>
              ))}
            </Table>
          ) : (
            <Empty>Noch keine Links.</Empty>
          )}
        </Card>
      </div>
    </>
  );
}
