import Link from "next/link";
import { and, desc, eq, gte, inArray, lt } from "drizzle-orm";
import { requireUser } from "@/server/auth/current";
import { action, str } from "@/server/actions";
import { can } from "@/server/auth/rbac";
import { db, schema } from "@/server/db";
import { enqueue } from "@/server/jobs/queue";
import { activatePlan } from "@/server/agents/strategy";
import { addDays, DEFAULT_TZ, localIsoDate, localTime, WEEKDAYS_DE, weekStartOf, zonedToUtc } from "@/lib/time";
import { AutoRefresh } from "@/components/auto-refresh";
import { Badge, Button, Card, Flash, inputCls, LinkButton, PageHeader, StatusBadge } from "@/components/ui";
import { FORMAT_LABELS, PILLAR_LABELS, type Format, type Pillar } from "@/lib/content-types";

async function generatePlan(fd: FormData) {
  "use server";
  const week = str(fd, "week");
  await action(`/calendar?week=${week}`, "content.generate", async ({ user }) => {
    if (!/^\d{4}-\d{2}-\d{2}$/.test(week)) throw new Error("Ungültige Woche");
    await enqueue("plan.generate", { weekStart: weekStartOf(new Date(`${week}T12:00:00Z`)), research: fd.get("research") === "on", draftAll: fd.get("draftAll") === "on" }, { createdBy: user.id, maxAttempts: 2 });
    return "Wochenplan wird generiert (Research → Strategie → Entwürfe).";
  });
}

async function draftAll(fd: FormData) {
  "use server";
  const planId = str(fd, "planId");
  await action(`/calendar?week=${str(fd, "week")}`, "content.generate", async ({ user }) => {
    await enqueue("plan.draft_all", { planId }, { createdBy: user.id });
    return "Entwürfe werden erstellt.";
  });
}

async function activate(fd: FormData) {
  "use server";
  await action(`/calendar?week=${str(fd, "week")}`, "content.edit", async ({ actor }) => {
    await activatePlan(actor, str(fd, "planId"));
    return "Plan aktiviert.";
  });
}

export default async function CalendarPage({ searchParams }: { searchParams: Promise<{ week?: string; ok?: string; err?: string }> }) {
  const user = await requireUser("content.read");
  const sp = await searchParams;
  const week = sp.week && /^\d{4}-\d{2}-\d{2}$/.test(sp.week) ? weekStartOf(new Date(`${sp.week}T12:00:00Z`)) : weekStartOf(new Date());
  const from = zonedToUtc(week, "00:00");
  const to = zonedToUtc(addDays(week, 7), "00:00");

  const [items, plans, running] = await Promise.all([
    db().select().from(schema.contentItems).where(and(gte(schema.contentItems.scheduledAt, from), lt(schema.contentItems.scheduledAt, to))).orderBy(schema.contentItems.scheduledAt),
    db().select().from(schema.contentPlans).where(eq(schema.contentPlans.weekStart, week)).orderBy(desc(schema.contentPlans.createdAt)),
    db().select().from(schema.jobs).where(and(inArray(schema.jobs.status, ["queued", "running"]), inArray(schema.jobs.type, ["plan.generate", "plan.draft_all", "item.draft", "research.run"]))),
  ]);
  const canGen = can(user.role, "content.generate");

  return (
    <>
      <PageHeader
        title="Redaktionskalender"
        subtitle={`KW ab ${new Date(week).toLocaleDateString("de-DE")} · Zeiten in ${DEFAULT_TZ}`}
        actions={
          <>
            <LinkButton href={`/calendar?week=${addDays(week, -7)}`}>← Vorwoche</LinkButton>
            <LinkButton href="/calendar">Heute</LinkButton>
            <LinkButton href={`/calendar?week=${addDays(week, 7)}`}>Nächste Woche →</LinkButton>
          </>
        }
      />
      <Flash ok={sp.ok} err={sp.err} />
      <AutoRefresh active={running.length > 0} />

      <div className="mb-6 grid gap-4 lg:grid-cols-3">
        <Card title="Wochenplan generieren" className="lg:col-span-1">
          {canGen ? (
            <form action={generatePlan} className="space-y-3 text-sm">
              <input type="hidden" name="week" value={week} />
              <p className="text-slate-600">5 Reels, 2 Carousels, täglich 3–5 Stories. Alle Inhalte landen als Entwurf in der Freigabe.</p>
              <label className="flex items-center gap-2">
                <input type="checkbox" name="research" /> Vorher neue Themen recherchieren
              </label>
              <label className="flex items-center gap-2">
                <input type="checkbox" name="draftAll" defaultChecked /> Direkt alle Entwürfe schreiben
              </label>
              <Button>Plan für diese Woche erzeugen</Button>
            </form>
          ) : (
            <p className="text-sm text-slate-500">Keine Berechtigung zur Generierung.</p>
          )}
        </Card>
        <Card title="Pläne dieser Woche" className="lg:col-span-2">
          {plans.length ? (
            <ul className="space-y-3">
              {plans.map((p) => (
                <li key={p.id} className="rounded-lg border border-slate-200 p-3 text-sm">
                  <div className="mb-1 flex items-center justify-between gap-2">
                    <Badge color={p.status === "active" ? "green" : "slate"}>{p.status}</Badge>
                    <div className="flex gap-2">
                      <form action={draftAll}>
                        <input type="hidden" name="planId" value={p.id} />
                        <input type="hidden" name="week" value={week} />
                        <Button variant="secondary">Fehlende Entwürfe erzeugen</Button>
                      </form>
                      {p.status !== "active" ? (
                        <form action={activate}>
                          <input type="hidden" name="planId" value={p.id} />
                          <input type="hidden" name="week" value={week} />
                          <Button variant="secondary">Als aktiv markieren</Button>
                        </form>
                      ) : null}
                    </div>
                  </div>
                  <p className="whitespace-pre-line text-slate-700">{p.strategySummary}</p>
                </li>
              ))}
            </ul>
          ) : (
            <p className="text-sm text-slate-500">Noch kein Plan.</p>
          )}
        </Card>
      </div>

      <div className="grid gap-3 md:grid-cols-7">
        {WEEKDAYS_DE.map((d, idx) => {
          const dayItems = items.filter((i) => i.scheduledAt && localIsoDate(i.scheduledAt) === addDays(week, idx));
          return (
            <div key={d} className="min-h-40 rounded-xl border border-slate-200 bg-white p-2">
              <div className="mb-2 px-1 text-xs font-semibold text-slate-600">
                {d} <span className="font-normal text-slate-400">{new Date(addDays(week, idx)).toLocaleDateString("de-DE", { day: "2-digit", month: "2-digit" })}</span>
              </div>
              <div className="space-y-2">
                {dayItems.map((i) => (
                  <Link
                    key={i.id}
                    href={`/content/${i.id}`}
                    className={`block rounded-lg border p-2 text-xs hover:shadow ${i.format === "story" ? "border-dashed border-slate-300 bg-slate-50" : "border-slate-200 bg-white"}`}
                  >
                    <div className="mb-1 flex items-center justify-between gap-1">
                      <span className="font-semibold">{FORMAT_LABELS[i.format as Format]}</span>
                      <span className="text-slate-500">{localTime(i.scheduledAt)}</span>
                    </div>
                    <div className="mb-1 line-clamp-3 text-slate-800">{i.title}</div>
                    <div className="flex flex-wrap gap-1">
                      <StatusBadge status={i.status} />
                      {i.format !== "story" ? <span className="text-[10px] text-slate-500">{PILLAR_LABELS[i.pillar as Pillar]}</span> : null}
                    </div>
                  </Link>
                ))}
              </div>
            </div>
          );
        })}
      </div>
      <form className="mt-4 flex items-center gap-2 text-sm" action="/calendar">
        <span className="text-slate-500">Zu Woche springen:</span>
        <input type="date" name="week" defaultValue={week} className={`${inputCls} w-auto`} />
        <Button variant="secondary">Anzeigen</Button>
      </form>
    </>
  );
}
