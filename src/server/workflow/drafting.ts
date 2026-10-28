import { and, desc, eq, inArray } from "drizzle-orm";
import { db, schema } from "@/server/db";
import { getBrand } from "@/server/brand";
import { writeCarousel, writeProductionBrief, writeReelScript, writeStorySet, type WritingContext } from "@/server/agents/writers";
import { destinationForCta, ensureItemLink } from "@/server/leads/links";
import { createVersion, getItem, type Principal, WorkflowError } from "./content";
import { storyFramesWithinRange } from "./plan-rules";

/**
 * Drafts (or regenerates) one content item with the matching agents and stores
 * the result as a new AI version. Reviewer feedback from the last
 * "changes requested" decision is passed to the agents automatically.
 */
export async function draftItem(p: Principal, itemId: string, extraFeedback?: string | null) {
  const item = await getItem(itemId);
  if (item.status === "published" || item.status === "publishing") throw new WorkflowError("Veröffentlichte Inhalte werden nicht neu generiert.");
  const brand = await getBrand();

  const [topic] = item.topicId ? await db().select().from(schema.topics).where(eq(schema.topics.id, item.topicId)) : [];
  const previous = item.currentVersionId
    ? (await db().select().from(schema.contentVersions).where(eq(schema.contentVersions.id, item.currentVersionId)))[0]
    : null;
  const [lastReview] = await db()
    .select()
    .from(schema.approvals)
    .where(and(eq(schema.approvals.itemId, itemId), inArray(schema.approvals.decision, ["changes_requested", "rejected"])))
    .orderBy(desc(schema.approvals.createdAt))
    .limit(1);
  const feedback = [lastReview && previous && lastReview.versionId === previous.id ? `Reviewer: ${lastReview.comment}` : "", extraFeedback ?? ""]
    .filter(Boolean)
    .join("\n");

  const destination = destinationForCta(item.ctaGoal);
  const link = destination
    ? await ensureItemLink(itemId, destination, item.format === "story" ? "story_link" : "bio", item.title)
    : null;

  const ctx: WritingContext = {
    brand: brand.settings,
    styleGuide: brand.derivedStyleGuide,
    item: { title: item.title, brief: item.brief, pillar: item.pillar, audience: item.audience, ctaGoal: item.ctaGoal },
    topic: topic ? { title: topic.title, angle: topic.angle, sources: topic.sources } : null,
    trackingUrl: link?.url ?? null,
    previous: previous ? { body: previous.body, caption: previous.caption } : null,
    feedback: feedback || null,
  };

  if (item.format === "reel") {
    const script = await writeReelScript(ctx);
    const brief = await writeProductionBrief(ctx, script.output);
    const { caption, ...rest } = script.output;
    return createVersion(p, itemId, {
      body: { ...rest, production: brief.output },
      caption: withHashtags(caption, script.output.hashtags),
      source: "ai",
      agentRunId: script.runId,
    });
  }
  if (item.format === "carousel") {
    const res = await writeCarousel(ctx);
    const { caption, ...rest } = res.output;
    return createVersion(p, itemId, { body: rest, caption: withHashtags(caption, res.output.hashtags), source: "ai", agentRunId: res.runId });
  }
  const res = await writeStorySet(ctx);
  const frames = res.output.frames.slice(0, 5);
  if (!storyFramesWithinRange(frames.length)) {
    throw new WorkflowError(`Story-Set hat ${frames.length} Frames; erwartet werden 3-5.`);
  }
  return createVersion(p, itemId, { body: { ...res.output, frames }, caption: "", source: "ai", agentRunId: res.runId });
}

export function withHashtags(caption: string, hashtags: string[]): string {
  const tags = hashtags
    .map((h) => h.trim().replace(/^#?/, "#").replace(/\s+/g, ""))
    .filter((h) => h.length > 1 && !caption.includes(h))
    .slice(0, 8);
  return tags.length ? `${caption.trim()}\n\n${tags.join(" ")}` : caption.trim();
}
