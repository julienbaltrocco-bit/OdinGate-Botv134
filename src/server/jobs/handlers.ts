import { eq } from "drizzle-orm";
import { db, schema } from "@/server/db";
import { SYSTEM_ACTOR } from "@/server/audit";
import { runResearch } from "@/server/agents/research";
import { generateWeeklyPlan } from "@/server/agents/strategy";
import { runOptimization, NotEnoughDataError } from "@/server/agents/optimization";
import { refreshStyleGuide } from "@/server/agents/brand-voice";
import { draftItem } from "@/server/workflow/drafting";
import { SYSTEM, type Principal } from "@/server/workflow/content";
import { executeRender } from "@/server/media/render-jobs";
import { RightsError } from "@/server/media/reel-render";
import { PublishBlockedError, publishItem, syncInsights } from "@/server/integrations/instagram/service";
import { InstagramApiError } from "@/server/integrations/instagram/client";
import { deliverWebhook } from "@/server/integrations/crm/webhooks";
import { LlmNotConfiguredError } from "@/server/ai/llm";
import { enqueue, type Job, type JobType } from "./queue";

/** Errors that will not succeed on retry (configuration/business rules). */
export class PermanentJobError extends Error {}
export function isPermanent(err: unknown): boolean {
  return (
    err instanceof PermanentJobError ||
    err instanceof LlmNotConfiguredError ||
    err instanceof RightsError ||
    err instanceof PublishBlockedError ||
    err instanceof NotEnoughDataError ||
    (err instanceof InstagramApiError && !err.retryable)
  );
}

/** Jobs run on behalf of the user who queued them (recorded in audit logs). */
async function principalFor(job: Job): Promise<Principal> {
  if (!job.createdBy) return SYSTEM;
  const [u] = await db().select().from(schema.users).where(eq(schema.users.id, job.createdBy));
  return u ? { id: u.id, label: `${u.email} (via worker)`, role: u.role } : SYSTEM;
}

type Handler = (job: Job) => Promise<Record<string, unknown>>;

export const handlers: Record<JobType, Handler> = {
  "research.run": async (job) => {
    const p = await principalFor(job);
    return runResearch(p, job.payload as { focus?: string; count?: number });
  },
  "plan.generate": async (job) => {
    const p = await principalFor(job);
    const { weekStart, research, draftAll } = job.payload as { weekStart: string; research?: boolean; draftAll?: boolean };
    if (research) await runResearch(p, { count: 12 });
    const plan = await generateWeeklyPlan(p, weekStart);
    if (draftAll) {
      for (const itemId of plan.itemIds) await enqueue("item.draft", { itemId }, { createdBy: job.createdBy });
    }
    return plan;
  },
  "plan.draft_all": async (job) => {
    const { planId } = job.payload as { planId: string };
    const items = await db().select({ id: schema.contentItems.id, status: schema.contentItems.status }).from(schema.contentItems).where(eq(schema.contentItems.planId, planId));
    const todo = items.filter((i) => i.status === "planned");
    for (const i of todo) await enqueue("item.draft", { itemId: i.id }, { createdBy: job.createdBy });
    return { queued: todo.length };
  },
  "item.draft": async (job) => {
    const p = await principalFor(job);
    const { itemId, feedback } = job.payload as { itemId: string; feedback?: string };
    const v = await draftItem(p, itemId, feedback);
    return { versionId: v.id, version: v.version };
  },
  "render.reel": async (job) => ({ outputs: await executeRender((job.payload as { renderId: string }).renderId) }),
  "render.carousel": async (job) => ({ outputs: await executeRender((job.payload as { renderId: string }).renderId) }),
  "brand.derive": async (job) => refreshStyleGuide(await principalFor(job)),
  "optimize.run": async (job) => runOptimization(await principalFor(job)),
  "instagram.publish": async (job) => {
    const result = await publishItem((job.payload as { itemId: string }).itemId);
    if ("skipped" in result && result.skipped === "not_due" && result.runAt) {
      // Schedule moved later: re-enqueue for the new time.
      await enqueue("instagram.publish", job.payload, { runAt: result.runAt, createdBy: job.createdBy });
    }
    return result;
  },
  "instagram.sync_insights": async () => syncInsights(),
  "webhook.deliver": async (job) => {
    const { endpointId, envelope } = job.payload as { endpointId: string; envelope: Record<string, unknown> };
    return deliverWebhook(endpointId, envelope);
  },
};

export { SYSTEM_ACTOR };
