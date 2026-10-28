import Link from "next/link";
import { and, desc, gte, inArray, lt, sql } from "drizzle-orm";
import { requireUser } from "@/server/auth/current";
import { db, schema } from "@/server/db";
import { systemBlockers } from "@/server/status";
import { addDays, formatDateTime, weekStartOf, zonedToUtc } from "@/lib/time";
import { Badge, Card, Empty, PageHeader, Stat, StatusBadge } from "@/components/ui";
import { FORMAT_LABELS, type Format } from "@/lib/content-types";

export default async function Dashboard() {
  await requireUser("content.read");
  const week = weekStartOf(new Date());
  const from = zonedToUtc(week, "00:00");
  const to = zonedToUtc(addDays(week, 7), "00:00");

  const [weekItems, blockers, review, jobs, leads30, recs] = await Promise.all([
    db().select().from(schema.contentItems).where(and(gte(schema.contentItems.scheduledAt, from), lt(schema.contentItems.scheduledAt, to))),
    systemBlockers(),
    db().select().from(schema.contentItems).where(inArray(schema.contentItems.status, ["in_review"])).orderBy(schema.contentItems.scheduledAt).limit(8),
    db().select().from(schema.jobs).orderBy(desc(schema.jobs.createdAt)).limit(6),
    db().execute(sql`SELECT type, count(*)::int AS n, count(*) FILTER (WHERE stage IN ('qualified','call_scheduled','won'))::int AS q FROM leads WHERE created_at > now() - interval '30 days' GROUP BY type`),
    db().select().from(schema.recommendations).where(inArray(schema.recommendations.status, ["open"])).orderBy(desc(schema.recommendations.createdAt)).limit(3),
  ]);

  const byFormat = (f: Format) => weekItems.filter((i) => i.format === f).length;
  const approved = weekItems.filter((i) => ["approved", "scheduled", "published"].includes(i.status)).length;
  const leadRows = leads30.rows as { type: string; n: number; q: number }[];
  const leadsTotal = leadRows.reduce((a, r) => a + r.n, 0);
  const leadsQualified = leadRows.reduce((a, r) => a + r.q, 0);

  return (
    <>
      <PageHeader title="Übersicht" subtitle={`Woche ab ${new Date(week).toLocaleDateString("de-DE")}`} />
      <div className="mb-6 grid grid-cols-2 gap-4 lg:grid-cols-4">
        <Stat label="Reels / Ziel 5" value={`${byFormat("reel")} / 5`} />
        <Stat label="Carousels / Ziel 2" value={`${byFormat("carousel")} / 2`} />
        <Stat label="Freigegeben diese Woche" value={`${approved} / ${weekItems.length}`} />
        <Stat label="Leads (30 Tage)" value={leadsTotal} hint={`${leadsQualified} qualifiziert`} />
      </div>

      <div className="grid gap-6 lg:grid-cols-3">
        <div className="space-y-6 lg:col-span-2">
          <Card title="Wartet auf Freigabe" actions={<Link className="text-xs text-blue-700 hover:underline" href="/review">Alle</Link>}>
            {review.length ? (
              <ul className="divide-y divide-slate-100">
                {review.map((i) => (
                  <li key={i.id} className="flex items-center justify-between gap-2 py-2">
                    <Link href={`/content/${i.id}`} className="min-w-0 truncate text-sm font-medium hover:underline">
                      {i.title}
                    </Link>
                    <div className="flex shrink-0 items-center gap-2">
                      {i.requiresComplianceReview ? <Badge color="violet">Compliance</Badge> : null}
                      <Badge>{FORMAT_LABELS[i.format as Format]}</Badge>
                      <span className="text-xs text-slate-500">{formatDateTime(i.scheduledAt)}</span>
                    </div>
                  </li>
                ))}
              </ul>
            ) : (
              <Empty>Nichts offen.</Empty>
            )}
          </Card>
          <Card title="Diese Woche" actions={<Link className="text-xs text-blue-700 hover:underline" href="/calendar">Kalender</Link>}>
            {weekItems.length ? (
              <ul className="divide-y divide-slate-100">
                {weekItems
                  .filter((i) => i.format !== "story")
                  .sort((a, b) => (a.scheduledAt?.getTime() ?? 0) - (b.scheduledAt?.getTime() ?? 0))
                  .map((i) => (
                    <li key={i.id} className="flex items-center justify-between gap-2 py-2">
                      <Link href={`/content/${i.id}`} className="min-w-0 truncate text-sm hover:underline">
                        <span className="mr-2 text-xs text-slate-500">{formatDateTime(i.scheduledAt)}</span>
                        {i.title}
                      </Link>
                      <StatusBadge status={i.status} />
                    </li>
                  ))}
              </ul>
            ) : (
              <Empty>
                Noch kein Plan für diese Woche. <Link className="text-blue-700 underline" href="/calendar">Wochenplan generieren</Link>
              </Empty>
            )}
          </Card>
        </div>
        <div className="space-y-6">
          <Card title="Blocker & offene Entscheidungen">
            <ul className="space-y-3">
              {blockers.map((b) => (
                <li key={b.key} className="text-sm">
                  <div className="flex items-center gap-2">
                    <Badge color={b.severity === "blocker" ? "red" : "amber"}>{b.severity === "blocker" ? "Blocker" : "Hinweis"}</Badge>
                    <span className="font-medium">{b.title}</span>
                  </div>
                  <p className="mt-1 text-xs text-slate-600">{b.detail}</p>
                </li>
              ))}
            </ul>
          </Card>
          <Card title="KI-Empfehlungen">
            {recs.length ? (
              <ul className="space-y-2 text-sm">
                {recs.map((r) => (
                  <li key={r.id}>
                    <span className="font-medium">{r.title}</span>
                    <p className="text-xs text-slate-600">{r.body}</p>
                  </li>
                ))}
              </ul>
            ) : (
              <p className="text-sm text-slate-500">Keine offenen Empfehlungen. Entstehen nach den ersten Messwerten.</p>
            )}
          </Card>
          <Card title="Letzte Jobs" actions={<Link className="text-xs text-blue-700 hover:underline" href="/jobs">Alle</Link>}>
            <ul className="space-y-1 text-xs">
              {jobs.map((j) => (
                <li key={j.id} className="flex justify-between gap-2">
                  <span className="truncate">{j.type}</span>
                  <Badge color={j.status === "succeeded" ? "green" : j.status === "failed" ? "red" : "blue"}>{j.status}</Badge>
                </li>
              ))}
            </ul>
          </Card>
        </div>
      </div>
    </>
  );
}
