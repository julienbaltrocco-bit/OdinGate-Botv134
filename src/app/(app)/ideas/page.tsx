import { and, desc, eq, inArray, ne } from "drizzle-orm";
import { requireUser } from "@/server/auth/current";
import { action, optNum, str } from "@/server/actions";
import { db, schema } from "@/server/db";
import { enqueue } from "@/server/jobs/queue";
import { audit } from "@/server/audit";
import { discardTopic } from "@/server/agents/research";
import { zonedToUtc } from "@/lib/time";
import { AUDIENCE_LABELS, AUDIENCES, FORMATS, FORMAT_LABELS, PILLAR_LABELS, PILLARS, type Audience, type Format, type Pillar } from "@/lib/content-types";
import { AutoRefresh } from "@/components/auto-refresh";
import { Badge, Button, Card, Empty, Field, Flash, inputCls, PageHeader, Table } from "@/components/ui";

async function runResearchAction(fd: FormData) {
  "use server";
  await action("/ideas", "content.generate", async ({ user }) => {
    await enqueue("research.run", { focus: str(fd, "focus") || undefined, count: optNum(fd, "count") ?? 12 }, { createdBy: user.id, maxAttempts: 2 });
    return "Recherche gestartet.";
  });
}

async function addSource(fd: FormData) {
  "use server";
  await action("/ideas", "research.write", async ({ actor }) => {
    const kind = str(fd, "kind") as "note" | "faq" | "comment" | "url";
    const title = str(fd, "title");
    const content = str(fd, "content");
    if (!title || !content) throw new Error("Titel und Inhalt erforderlich.");
    const url = str(fd, "url") || null;
    if (url && !/^https?:\/\//.test(url)) throw new Error("URL muss mit http(s) beginnen.");
    const [row] = await db().insert(schema.researchSources).values({ kind, title, content, url, createdBy: actor.id }).returning();
    await audit(actor, "research.source_added", "research_source", row.id, { kind });
    return "Quelle gespeichert.";
  });
}

async function addTopic(fd: FormData) {
  "use server";
  await action("/ideas", "content.edit", async ({ actor }) => {
    const [row] = await db()
      .insert(schema.topics)
      .values({
        title: str(fd, "title"),
        angle: str(fd, "angle"),
        pillar: str(fd, "pillar") as Pillar,
        audience: str(fd, "audience") as Audience,
        priority: optNum(fd, "priority") ?? 50,
        rationale: "Manuell erfasst",
        sources: [{ kind: "manual", title: `Manuell von ${actor.label}` }],
      })
      .returning();
    await audit(actor, "topic.created", "topic", row.id);
    return "Thema angelegt.";
  });
}

async function planTopic(fd: FormData) {
  "use server";
  await action("/ideas", "content.edit", async ({ actor, user }) => {
    const [topic] = await db().select().from(schema.topics).where(eq(schema.topics.id, str(fd, "topicId")));
    if (!topic) throw new Error("Thema nicht gefunden");
    const date = str(fd, "date");
    const [item] = await db()
      .insert(schema.contentItems)
      .values({
        topicId: topic.id,
        format: str(fd, "format") as Format,
        pillar: topic.pillar,
        audience: topic.audience,
        title: topic.title,
        brief: topic.angle,
        ctaGoal: str(fd, "cta") || "none",
        scheduledAt: date ? zonedToUtc(date, str(fd, "time") || "18:00") : null,
      })
      .returning();
    await db().update(schema.topics).set({ status: "planned" }).where(eq(schema.topics.id, topic.id));
    await audit(actor, "content.created", "content_item", item.id, { fromTopic: topic.id });
    if (fd.get("draft") === "on") await enqueue("item.draft", { itemId: item.id }, { createdBy: user.id });
    return { message: "Inhalt angelegt.", redirectTo: `/content/${item.id}` };
  });
}

async function discard(fd: FormData) {
  "use server";
  await action("/ideas", "content.edit", async ({ actor }) => {
    await discardTopic(actor, str(fd, "topicId"));
    return "Thema verworfen.";
  });
}

export default async function IdeasPage({ searchParams }: { searchParams: Promise<{ ok?: string; err?: string }> }) {
  await requireUser("content.read");
  const sp = await searchParams;
  const [topics, sources, running] = await Promise.all([
    db().select().from(schema.topics).where(ne(schema.topics.status, "discarded")).orderBy(desc(schema.topics.priority), desc(schema.topics.createdAt)).limit(100),
    db().select().from(schema.researchSources).orderBy(desc(schema.researchSources.createdAt)).limit(30),
    db().select({ id: schema.jobs.id }).from(schema.jobs).where(and(eq(schema.jobs.type, "research.run"), inArray(schema.jobs.status, ["queued", "running"]))),
  ]);

  return (
    <>
      <PageHeader title="Ideen & Recherche" subtitle="Themen-Backlog mit nachvollziehbaren Quellen" />
      <Flash ok={sp.ok} err={sp.err} />
      <AutoRefresh active={running.length > 0} />
      <div className="mb-6 grid gap-4 lg:grid-cols-3">
        <Card title="Research Agent starten">
          <form action={runResearchAction} className="space-y-3">
            <Field label="Fokus (optional)" hint="z.B. 'Einwände von KOLs gegen Exklusivverträge'">
              <input name="focus" className={inputCls} />
            </Field>
            <Field label="Anzahl Themen">
              <input name="count" type="number" min={3} max={25} defaultValue={12} className={inputCls} />
            </Field>
            <Button>Recherche starten</Button>
          </form>
        </Card>
        <Card title="Quelle hinzufügen" className="lg:col-span-2">
          <form action={addSource} className="grid gap-3 md:grid-cols-2">
            <Field label="Art">
              <select name="kind" className={inputCls}>
                <option value="faq">Häufige Frage (aus Calls/DMs)</option>
                <option value="comment">Kommentar / Feedback</option>
                <option value="note">Notiz / Erfahrung</option>
                <option value="url">Artikel / URL</option>
              </select>
            </Field>
            <Field label="Titel">
              <input name="title" required className={inputCls} />
            </Field>
            <div className="md:col-span-2">
              <Field label="Inhalt" hint="Keine personenbezogenen Daten Dritter eintragen.">
                <textarea name="content" required rows={3} className={inputCls} />
              </Field>
            </div>
            <Field label="URL (optional)">
              <input name="url" className={inputCls} />
            </Field>
            <div className="flex items-end">
              <Button>Speichern</Button>
            </div>
          </form>
        </Card>
      </div>

      <Card title={`Backlog (${topics.length})`} className="mb-6">
        {topics.length ? (
          <Table head={["Prio", "Thema", "Säule / Zielgruppe", "Quellen", "Einplanen", ""]}>
            {topics.map((t) => (
              <tr key={t.id} className="align-top">
                <td className="px-2 py-2 font-semibold">{t.priority}</td>
                <td className="max-w-md px-2 py-2">
                  <div className="font-medium">{t.title}</div>
                  <div className="text-xs text-slate-600">{t.angle}</div>
                  {t.status !== "backlog" ? <Badge color="blue">{t.status}</Badge> : null}
                </td>
                <td className="px-2 py-2 text-xs">
                  {PILLAR_LABELS[t.pillar as Pillar]}
                  <br />
                  {AUDIENCE_LABELS[t.audience as Audience]}
                </td>
                <td className="max-w-xs px-2 py-2 text-xs text-slate-600">
                  {t.sources.map((s, i) => (
                    <div key={i}>{s.url ? <a className="text-blue-700 underline" href={s.url} target="_blank" rel="noreferrer">{s.title}</a> : s.title}</div>
                  ))}
                </td>
                <td className="px-2 py-2">
                  <form action={planTopic} className="flex flex-wrap items-center gap-1 text-xs">
                    <input type="hidden" name="topicId" value={t.id} />
                    <select name="format" className={`${inputCls} w-auto py-1 text-xs`}>
                      {FORMATS.map((f) => (
                        <option key={f} value={f}>{FORMAT_LABELS[f]}</option>
                      ))}
                    </select>
                    <input type="date" name="date" className={`${inputCls} w-auto py-1 text-xs`} />
                    <input type="time" name="time" defaultValue="18:00" className={`${inputCls} w-auto py-1 text-xs`} />
                    <select name="cta" className={`${inputCls} w-auto py-1 text-xs`}>
                      <option value="none">CTA: Engagement</option>
                      <option value="coaching_application">CTA: Coaching</option>
                      <option value="partner_inquiry">CTA: Partner</option>
                    </select>
                    <label className="flex items-center gap-1"><input type="checkbox" name="draft" defaultChecked /> Entwurf</label>
                    <Button variant="secondary">Anlegen</Button>
                  </form>
                </td>
                <td className="px-2 py-2">
                  <form action={discard}>
                    <input type="hidden" name="topicId" value={t.id} />
                    <Button variant="ghost">Verwerfen</Button>
                  </form>
                </td>
              </tr>
            ))}
          </Table>
        ) : (
          <Empty>Noch keine Themen. Quellen hinzufügen und Research Agent starten.</Empty>
        )}
      </Card>

      <div className="grid gap-4 lg:grid-cols-2">
        <Card title="Thema manuell anlegen">
          <form action={addTopic} className="grid gap-3 md:grid-cols-2">
            <div className="md:col-span-2"><Field label="Titel"><input name="title" required className={inputCls} /></Field></div>
            <div className="md:col-span-2"><Field label="Blickwinkel / These"><input name="angle" required className={inputCls} /></Field></div>
            <Field label="Säule">
              <select name="pillar" className={inputCls}>{PILLARS.map((p) => <option key={p} value={p}>{PILLAR_LABELS[p]}</option>)}</select>
            </Field>
            <Field label="Zielgruppe">
              <select name="audience" className={inputCls}>{AUDIENCES.map((a) => <option key={a} value={a}>{AUDIENCE_LABELS[a]}</option>)}</select>
            </Field>
            <Field label="Priorität (0–100)"><input name="priority" type="number" min={0} max={100} defaultValue={50} className={inputCls} /></Field>
            <div className="flex items-end"><Button>Anlegen</Button></div>
          </form>
        </Card>
        <Card title="Quellen">
          {sources.length ? (
            <ul className="max-h-96 space-y-2 overflow-y-auto text-sm">
              {sources.map((s) => (
                <li key={s.id} className="border-b border-slate-100 pb-2">
                  <div className="flex items-center gap-2"><Badge>{s.kind}</Badge><span className="font-medium">{s.title}</span></div>
                  <p className="line-clamp-2 text-xs text-slate-600">{s.content}</p>
                  {s.url ? <a href={s.url} target="_blank" rel="noreferrer" className="text-xs text-blue-700 underline">{s.url}</a> : null}
                </li>
              ))}
            </ul>
          ) : (
            <Empty>Keine Quellen.</Empty>
          )}
        </Card>
      </div>
    </>
  );
}
