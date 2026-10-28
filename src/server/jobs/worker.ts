import { claimNext, completeJob, enqueue, failJob, recoverStaleJobs } from "./queue";
import { handlers, isPermanent } from "./handlers";
import { describeError } from "@/server/ai/llm";
import { db, schema } from "@/server/db";
import { and, eq, gte } from "drizzle-orm";

export type WorkerOptions = { pollMs?: number; types?: string[]; once?: boolean; log?: (msg: string) => void };

/** Processes one job if available. Returns true when a job was handled. */
export async function tick(opts: WorkerOptions = {}): Promise<boolean> {
  const log = opts.log ?? console.log;
  const job = await claimNext(opts.types);
  if (!job) return false;
  const handler = handlers[job.type as keyof typeof handlers];
  const started = Date.now();
  try {
    if (!handler) throw new Error(`Unbekannter Job-Typ: ${job.type}`);
    const result = await handler(job);
    await completeJob(job.id, result);
    log(`[worker] ${job.type} ${job.id} ok (${Date.now() - started}ms)`);
  } catch (err) {
    const message = describeError(err);
    const retried = await failJob(job, message, { retryable: !isPermanent(err) });
    log(`[worker] ${job.type} ${job.id} ${retried ? "retry" : "FAILED"}: ${message}`);
  }
  return true;
}

/** Daily insights sync, enqueued at most once per 24h. */
async function ensureRecurring() {
  const since = new Date(Date.now() - 23 * 3600_000);
  const existing = await db()
    .select({ id: schema.jobs.id })
    .from(schema.jobs)
    .where(and(eq(schema.jobs.type, "instagram.sync_insights"), gte(schema.jobs.createdAt, since)))
    .limit(1);
  if (!existing.length) await enqueue("instagram.sync_insights", {}, { maxAttempts: 2 });
}

export async function runWorker(opts: WorkerOptions = {}) {
  const pollMs = opts.pollMs ?? 2000;
  let stopping = false;
  const stop = () => (stopping = true);
  process.on("SIGINT", stop);
  process.on("SIGTERM", stop);
  let lastMaintenance = 0;
  while (!stopping) {
    if (Date.now() - lastMaintenance > 5 * 60_000) {
      await recoverStaleJobs().catch(() => undefined);
      await ensureRecurring().catch(() => undefined);
      lastMaintenance = Date.now();
    }
    const handled = await tick(opts).catch((err) => {
      console.error("[worker] tick error", err);
      return false;
    });
    if (opts.once && !handled) break;
    if (!handled) await new Promise((r) => setTimeout(r, pollMs));
  }
}
