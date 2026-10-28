import { and, eq, inArray, sql } from "drizzle-orm";
import { db, schema } from "@/server/db";

export type JobType =
  | "research.run"
  | "plan.generate"
  | "plan.draft_all"
  | "item.draft"
  | "render.reel"
  | "render.carousel"
  | "brand.derive"
  | "optimize.run"
  | "instagram.publish"
  | "instagram.sync_insights"
  | "webhook.deliver";

export type Job = typeof schema.jobs.$inferSelect;

export async function enqueue(
  type: JobType,
  payload: Record<string, unknown>,
  opts: { runAt?: Date; createdBy?: string | null; maxAttempts?: number } = {},
): Promise<string> {
  const [job] = await db()
    .insert(schema.jobs)
    .values({
      type,
      payload,
      runAt: opts.runAt ?? new Date(),
      createdBy: opts.createdBy ?? null,
      maxAttempts: opts.maxAttempts ?? 3,
    })
    .returning({ id: schema.jobs.id });
  return job.id;
}

/** Atomically claims the next due job (safe with multiple workers). */
export async function claimNext(types?: string[]): Promise<Job | null> {
  const typeFilter = types?.length ? sql`AND type IN (${sql.join(types.map((t) => sql`${t}`), sql`, `)})` : sql``;
  const result = await db().execute(sql`
    UPDATE jobs SET status = 'running', locked_at = now(), attempts = attempts + 1
    WHERE id = (
      SELECT id FROM jobs
      WHERE status = 'queued' AND run_at <= now() ${typeFilter}
      ORDER BY run_at ASC
      FOR UPDATE SKIP LOCKED
      LIMIT 1
    )
    RETURNING id`);
  const id = (result.rows[0] as { id: string } | undefined)?.id;
  if (!id) return null;
  const [job] = await db().select().from(schema.jobs).where(eq(schema.jobs.id, id));
  return job ?? null;
}

export async function completeJob(id: string, result: Record<string, unknown> = {}) {
  await db()
    .update(schema.jobs)
    .set({ status: "succeeded", result, finishedAt: new Date(), lockedAt: null })
    .where(eq(schema.jobs.id, id));
}

/** Retries with exponential backoff until maxAttempts, then marks failed. */
export async function failJob(job: Job, error: string, opts: { retryable?: boolean } = {}) {
  const retry = opts.retryable !== false && job.attempts < job.maxAttempts;
  await db()
    .update(schema.jobs)
    .set(
      retry
        ? { status: "queued", lastError: error, lockedAt: null, runAt: new Date(Date.now() + 2 ** job.attempts * 15_000) }
        : { status: "failed", lastError: error, lockedAt: null, finishedAt: new Date() },
    )
    .where(eq(schema.jobs.id, job.id));
  return retry;
}

/** Requeues jobs whose worker died mid-run. */
export async function recoverStaleJobs(staleMinutes = 30) {
  await db().execute(sql`
    UPDATE jobs SET status = 'queued', locked_at = NULL, last_error = 'recovered after worker timeout'
    WHERE status = 'running' AND locked_at < now() - (${staleMinutes} || ' minutes')::interval`);
}

export async function activeJobsFor(key: string, value: string) {
  return db()
    .select()
    .from(schema.jobs)
    .where(and(inArray(schema.jobs.status, ["queued", "running"]), sql`${schema.jobs.payload} ->> ${key} = ${value}`));
}
