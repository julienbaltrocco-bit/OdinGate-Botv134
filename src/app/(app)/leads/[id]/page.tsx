import { Fragment } from "react";
import Link from "next/link";
import { notFound } from "next/navigation";
import { eq } from "drizzle-orm";
import { requireUser } from "@/server/auth/current";
import { action, optNum, str } from "@/server/actions";
import { db, schema } from "@/server/db";
import { anonymizeLead, updateLead } from "@/server/leads/leads";
import { formatDateTime } from "@/lib/time";
import { Badge, Button, Card, Field, Flash, inputCls, PageHeader } from "@/components/ui";

async function save(fd: FormData) {
  "use server";
  const id = str(fd, "id");
  await action(`/leads/${id}`, "leads.write", async ({ actor }) => {
    await updateLead(actor, id, {
      stage: str(fd, "stage") as "new",
      notes: str(fd, "notes"),
      dealValueUsd: optNum(fd, "dealValueUsd") ?? null,
      crmExternalId: str(fd, "crmExternalId") || null,
    });
    return "Lead aktualisiert.";
  });
}

async function anonymize(fd: FormData) {
  "use server";
  const id = str(fd, "id");
  await action(`/leads/${id}`, "leads.write", async ({ actor }) => {
    await anonymizeLead(actor, id);
    return "Personenbezogene Daten gelöscht (Datensatz anonymisiert).";
  });
}

export default async function LeadPage({ params, searchParams }: { params: Promise<{ id: string }>; searchParams: Promise<{ ok?: string; err?: string }> }) {
  await requireUser("leads.read");
  const { id } = await params;
  const sp = await searchParams;
  if (!/^[0-9a-f-]{36}$/.test(id)) notFound();
  const [lead] = await db().select().from(schema.leads).where(eq(schema.leads.id, id));
  if (!lead) notFound();
  const [item] = lead.sourceItemId ? await db().select().from(schema.contentItems).where(eq(schema.contentItems.id, lead.sourceItemId)) : [];

  return (
    <>
      <PageHeader title={lead.name} subtitle={<span className="flex gap-2"><Badge>{lead.type}</Badge><span>{formatDateTime(lead.createdAt)}</span></span>} actions={<Link className="text-sm text-blue-700" href="/leads">← Leads</Link>} />
      <Flash ok={sp.ok} err={sp.err} />
      <div className="grid gap-6 lg:grid-cols-2">
        <Card title="Anfrage">
          <dl className="grid grid-cols-3 gap-2 text-sm">
            <dt className="text-slate-500">E-Mail</dt><dd className="col-span-2"><a className="underline" href={`mailto:${lead.email}`}>{lead.email}</a></dd>
            <dt className="text-slate-500">Instagram</dt><dd className="col-span-2">{lead.instagramHandle ?? "–"}</dd>
            <dt className="text-slate-500">Firma</dt><dd className="col-span-2">{lead.company ?? "–"}</dd>
            {Object.entries(lead.answers).map(([k, v]) => (
              <Fragment key={k}>
                <dt className="text-slate-500">{k}</dt>
                <dd className="col-span-2">{String(v)}</dd>
              </Fragment>
            ))}
            <dt className="text-slate-500">Nachricht</dt><dd className="col-span-2 whitespace-pre-line">{lead.message || "–"}</dd>
            <dt className="text-slate-500">Quelle</dt><dd className="col-span-2">{item ? <Link className="underline" href={`/content/${item.id}`}>{item.title}</Link> : "direkt / unbekannt"}</dd>
            <dt className="text-slate-500">Einwilligung</dt><dd className="col-span-2 text-xs">{formatDateTime(lead.consentAt)} – {lead.consentText}</dd>
          </dl>
        </Card>
        <div className="space-y-6">
          <Card title={`Qualifizierung · Score ${lead.score}`}>
            <ul className="text-sm">{lead.scoreReasons.map((r, i) => <li key={i}>{r}</li>)}</ul>
          </Card>
          <Card title="Bearbeitung">
            <form action={save} className="space-y-3">
              <input type="hidden" name="id" value={lead.id} />
              <Field label="Stage">
                <select name="stage" defaultValue={lead.stage} className={inputCls}>
                  {["new", "qualified", "call_scheduled", "won", "lost", "disqualified"].map((s) => <option key={s} value={s}>{s}</option>)}
                </select>
              </Field>
              <Field label="Deal-Wert (USD, optional)"><input name="dealValueUsd" defaultValue={lead.dealValueUsd ?? ""} className={inputCls} /></Field>
              <Field label="CRM-ID"><input name="crmExternalId" defaultValue={lead.crmExternalId ?? ""} className={inputCls} /></Field>
              <Field label="Notizen"><textarea name="notes" rows={4} defaultValue={lead.notes} className={inputCls} /></Field>
              <Button>Speichern</Button>
            </form>
          </Card>
          <Card title="DSGVO">
            <form action={anonymize}>
              <input type="hidden" name="id" value={lead.id} />
              <p className="mb-2 text-xs text-slate-600">Bei Widerruf/Löschanfrage: personenbezogene Daten löschen. Statistik bleibt anonym erhalten.</p>
              <Button variant="danger">Daten löschen</Button>
            </form>
          </Card>
        </div>
      </div>
    </>
  );
}
