import { desc, inArray } from "drizzle-orm";
import { requireUser } from "@/server/auth/current";
import { db, schema } from "@/server/db";
import { formatDateTime } from "@/lib/time";
import { AutoRefresh } from "@/components/auto-refresh";
import { Badge, Card, PageHeader, Table } from "@/components/ui";

export default async function JobsPage() {
  await requireUser("content.read");
  const [jobs, runs] = await Promise.all([
    db().select().from(schema.jobs).orderBy(desc(schema.jobs.createdAt)).limit(60),
    db()
      .select({
        id: schema.agentRuns.id,
        agent: schema.agentRuns.agent,
        provider: schema.agentRuns.provider,
        model: schema.agentRuns.model,
        status: schema.agentRuns.status,
        error: schema.agentRuns.error,
        usage: schema.agentRuns.usage,
        durationMs: schema.agentRuns.durationMs,
        citations: schema.agentRuns.citations,
        createdAt: schema.agentRuns.createdAt,
      })
      .from(schema.agentRuns)
      .orderBy(desc(schema.agentRuns.createdAt))
      .limit(60),
  ]);
  const active = jobs.some((j) => j.status === "queued" || j.status === "running");
  const color = (s: string) => (s === "succeeded" ? "green" : s === "failed" ? "red" : "blue") as "green" | "red" | "blue";
  const running = await db().select({ id: schema.jobs.id }).from(schema.jobs).where(inArray(schema.jobs.status, ["running"]));

  return (
    <>
      <PageHeader title="Jobs & Agenten" subtitle={`Workflow-Protokoll: jede KI-Ausgabe ist mit Modell, Laufzeit und Token-Verbrauch nachvollziehbar · ${running.length} laufend`} />
      <AutoRefresh active={active} />
      <Card title="Jobs" className="mb-6">
        <Table head={["Erstellt", "Typ", "Status", "Versuche", "Fehler / Ergebnis"]}>
          {jobs.map((j) => (
            <tr key={j.id}>
              <td className="px-2 py-2 text-xs">{formatDateTime(j.createdAt)}</td>
              <td className="px-2 py-2 font-mono text-xs">{j.type}</td>
              <td className="px-2 py-2"><Badge color={color(j.status)}>{j.status}</Badge></td>
              <td className="px-2 py-2 text-xs">{j.attempts}/{j.maxAttempts}</td>
              <td className="max-w-md px-2 py-2 text-xs text-slate-600">{j.lastError ?? (j.result ? JSON.stringify(j.result).slice(0, 160) : "")}</td>
            </tr>
          ))}
        </Table>
      </Card>
      <Card title="Agent-Läufe">
        <Table head={["Zeit", "Agent", "Modell", "Status", "Dauer", "Tokens (in/out)", "Quellen"]}>
          {runs.map((r) => {
            const u = (r.usage ?? {}) as { input_tokens?: number; output_tokens?: number };
            return (
              <tr key={r.id}>
                <td className="px-2 py-2 text-xs">{formatDateTime(r.createdAt)}</td>
                <td className="px-2 py-2 font-mono text-xs">{r.agent}</td>
                <td className="px-2 py-2 text-xs">{r.provider === "mock" ? <Badge color="amber">MOCK</Badge> : r.model}</td>
                <td className="px-2 py-2"><Badge color={color(r.status)}>{r.status}</Badge>{r.error ? <div className="text-xs text-red-700">{r.error}</div> : null}</td>
                <td className="px-2 py-2 text-xs">{r.durationMs ? `${(r.durationMs / 1000).toFixed(1)}s` : "–"}</td>
                <td className="px-2 py-2 text-xs tabular-nums">{u.input_tokens ?? "–"} / {u.output_tokens ?? "–"}</td>
                <td className="px-2 py-2 text-xs">{r.citations?.length ?? 0}</td>
              </tr>
            );
          })}
        </Table>
      </Card>
    </>
  );
}
