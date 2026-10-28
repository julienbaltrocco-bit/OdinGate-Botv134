import { and, desc, eq, inArray } from "drizzle-orm";
import { requireUser } from "@/server/auth/current";
import { action, str } from "@/server/actions";
import { db, schema } from "@/server/db";
import { enqueue } from "@/server/jobs/queue";
import { audit } from "@/server/audit";
import { formatDateTime } from "@/lib/time";
import { AutoRefresh } from "@/components/auto-refresh";
import { Badge, Button, Card, Empty, Flash, PageHeader } from "@/components/ui";

async function run() {
  "use server";
  await action("/insights", "content.generate", async ({ user }) => {
    await enqueue("optimize.run", {}, { createdBy: user.id, maxAttempts: 1 });
    return "Optimization Agent gestartet.";
  });
}

async function setStatus(fd: FormData) {
  "use server";
  await action("/insights", "content.edit", async ({ actor }) => {
    const status = str(fd, "status") as "accepted" | "dismissed";
    await db().update(schema.recommendations).set({ status }).where(eq(schema.recommendations.id, str(fd, "id")));
    await audit(actor, `recommendation.${status}`, "recommendation", str(fd, "id"));
    return status === "accepted" ? "Übernommen – fließt in die nächste Wochenplanung ein." : "Verworfen.";
  });
}

export default async function InsightsPage({ searchParams }: { searchParams: Promise<{ ok?: string; err?: string }> }) {
  await requireUser("analytics.read");
  const sp = await searchParams;
  const [recs, running, lastFailed] = await Promise.all([
    db().select().from(schema.recommendations).orderBy(desc(schema.recommendations.createdAt)).limit(60),
    db().select({ id: schema.jobs.id }).from(schema.jobs).where(and(eq(schema.jobs.type, "optimize.run"), inArray(schema.jobs.status, ["queued", "running"]))),
    db().select().from(schema.jobs).where(eq(schema.jobs.type, "optimize.run")).orderBy(desc(schema.jobs.createdAt)).limit(1),
  ]);
  return (
    <>
      <PageHeader
        title="KI-Empfehlungen"
        subtitle="Optimization Agent: Vorschläge zu Themen, Hooks, Formaten, CTAs und Timing – nur aus gemessenen Daten"
        actions={
          <form action={run}>
            <Button>Analyse starten</Button>
          </form>
        }
      />
      <Flash ok={sp.ok} err={sp.err} />
      <AutoRefresh active={running.length > 0} />
      {lastFailed[0]?.status === "failed" ? <p className="mb-4 text-sm text-amber-700">Letzter Lauf: {lastFailed[0].lastError}</p> : null}
      {recs.length ? (
        <div className="grid gap-4 md:grid-cols-2">
          {recs.map((r) => (
            <Card key={r.id} title={r.title} actions={<Badge color={r.status === "accepted" ? "green" : r.status === "dismissed" ? "slate" : "blue"}>{r.status}</Badge>}>
              <div className="space-y-2 text-sm">
                <div className="flex gap-2"><Badge>{r.category}</Badge><Badge color={r.confidence === "high" ? "green" : r.confidence === "medium" ? "amber" : "slate"}>Sicherheit: {r.confidence}</Badge></div>
                <p>{r.body}</p>
                <p className="text-xs text-slate-600">Evidenz: {r.evidence}</p>
                <div className="text-xs text-slate-400">{formatDateTime(r.createdAt)}</div>
                {r.status === "open" ? (
                  <form action={setStatus} className="flex gap-2">
                    <input type="hidden" name="id" value={r.id} />
                    <Button name="status" value="accepted">Übernehmen</Button>
                    <Button name="status" value="dismissed" variant="secondary">Verwerfen</Button>
                  </form>
                ) : null}
              </div>
            </Card>
          ))}
        </div>
      ) : (
        <Empty>Noch keine Empfehlungen. Der Optimization Agent braucht veröffentlichte Beiträge mit Messwerten.</Empty>
      )}
    </>
  );
}
