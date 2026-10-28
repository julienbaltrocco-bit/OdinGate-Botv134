import { and, desc, eq, gte, inArray } from "drizzle-orm";
import { z } from "zod";
import { db, schema } from "@/server/db";
import { brandContext, CONTENT_GUARDRAILS, getBrand } from "@/server/brand";
import { generateStructured } from "@/server/ai/llm";
import { AUDIENCES, CTA_TYPES, PILLARS } from "@/lib/content-types";
import { audit, type Actor } from "@/server/audit";
import { performanceSummary } from "@/server/analytics/metrics";
import { validatePlanShape, WEEKLY_MIX } from "@/server/workflow/plan-rules";
import { addDays, WEEKDAYS_DE, zonedToUtc } from "@/lib/time";

/**
 * Strategy Agent: builds the 7-day editorial plan (5 reels, 2 carousels,
 * one 3-5 frame story set per day) from the topic backlog, performance data
 * and accepted optimisation recommendations.
 */

const PlanPost = z.object({
  day: z.number().describe("0 = Montag ... 6 = Sonntag"),
  time: z.string().describe("HH:MM, Europe/Berlin"),
  title: z.string(),
  brief: z.string().describe("Kernaussage, Beispiel, gewünschte Wirkung"),
  pillar: z.enum(PILLARS),
  audience: z.enum(AUDIENCES),
  topicId: z.string().describe("ID des Backlog-Themas oder leer"),
  ctaGoal: z.enum(CTA_TYPES),
});

const PlanOutput = z.object({
  strategySummary: z.string().describe("Wochenstrategie in 3-6 Sätzen: Ziel, Schwerpunkte, Begründung"),
  reels: z.array(PlanPost),
  carousels: z.array(PlanPost),
  storyDays: z.array(
    z.object({
      day: z.number(),
      theme: z.string(),
      brief: z.string(),
      linkFocus: z.enum(["coaching", "partner", "none"]),
    }),
  ),
});
type PlanOutput = z.infer<typeof PlanOutput>;

const SYSTEM = `Du bist der Strategy Agent und Content Director einer Personal Brand im Crypto Business Development.
Ziel: qualifizierte B2B-Partner- und Coaching-Anfragen, nicht Vanity Metrics. Die Marke steht am Anfang (ca. 700 Follower, gemischte Zielgruppe), daher: klare Positionierung, wiedererkennbare Formate, Vertrauen durch echte Prozesse.
Plane genau ${WEEKLY_MIX.reels} Reels, ${WEEKLY_MIX.carousels} Carousels und für jeden der 7 Tage ein Story-Set.
Verteile die Content-Säulen sinnvoll (Authority, Behind the Scenes, Education, Personal Brand, Conversion). Conversion-Inhalte sparsam und erst nach Vertrauensaufbau in der Woche.
Nutze vorrangig Themen aus dem Backlog (topicId angeben). Leite Entscheidungen aus Performance-Daten nur ab, wenn Daten vorhanden sind.
${CONTENT_GUARDRAILS}`;

export async function generateWeeklyPlan(actor: Actor, weekStart: string) {
  const brand = await getBrand();
  const backlog = await db()
    .select()
    .from(schema.topics)
    .where(eq(schema.topics.status, "backlog"))
    .orderBy(desc(schema.topics.priority))
    .limit(30);
  const recs = await db()
    .select()
    .from(schema.recommendations)
    .where(eq(schema.recommendations.status, "accepted"))
    .orderBy(desc(schema.recommendations.createdAt))
    .limit(10);
  const recent = await db()
    .select({ title: schema.contentItems.title, format: schema.contentItems.format })
    .from(schema.contentItems)
    .where(gte(schema.contentItems.createdAt, new Date(Date.now() - 21 * 86400_000)))
    .limit(60);
  const perf = await performanceSummary();

  const basePrompt = [
    brandContext(brand.settings, brand.derivedStyleGuide),
    `\n# Woche\nStart (Montag): ${weekStart}. Tage: ${WEEKDAYS_DE.map((d, i) => `${i}=${d}`).join(", ")}`,
    `\n# Themen-Backlog\n${backlog.map((t) => `- id=${t.id} | ${t.title} | ${t.pillar} | ${t.audience} | Prio ${t.priority} | ${t.angle}`).join("\n") || "(leer – eigene Themen wählen, topicId leer lassen)"}`,
    `\n# Performance\n${perf.text}`,
    `\n# Akzeptierte Optimierungsempfehlungen\n${recs.map((r) => `- [${r.category}] ${r.title}: ${r.body}`).join("\n") || "(keine)"}`,
    `\n# Kürzlich geplante Inhalte (Wiederholungen vermeiden)\n${recent.map((r) => `- ${r.format}: ${r.title}`).join("\n") || "(keine)"}`,
  ].join("\n");

  let output: PlanOutput | null = null;
  let runId = "";
  let errors: string[] = [];
  for (let attempt = 0; attempt < 2; attempt++) {
    const prompt = errors.length
      ? `${basePrompt}\n\n# Korrektur\nDer vorige Plan war ungültig:\n${errors.map((e) => `- ${e}`).join("\n")}\nErzeuge einen vollständigen, korrigierten Plan.`
      : basePrompt;
    const res = await generateStructured({ agent: "strategy", system: SYSTEM, prompt, schema: PlanOutput, meta: { weekStart, attempt } });
    runId = res.runId;
    errors = validatePlanShape(res.output);
    if (!errors.length) {
      output = res.output;
      break;
    }
  }
  if (!output) throw new Error(`Wochenplan ungültig nach 2 Versuchen: ${errors.join(" ")}`);

  const validTopicIds = new Set(backlog.map((t) => t.id));
  return db().transaction(async (tx) => {
    const [plan] = await tx
      .insert(schema.contentPlans)
      .values({ weekStart, status: "draft", strategySummary: output.strategySummary, agentRunId: runId, createdBy: actor.id })
      .returning();

    const feed = [
      ...output.reels.map((p) => ({ ...p, format: "reel" as const })),
      ...output.carousels.map((p) => ({ ...p, format: "carousel" as const })),
    ];
    const itemRows: (typeof schema.contentItems.$inferInsert)[] = feed.map((p) => ({
      planId: plan.id,
      topicId: validTopicIds.has(p.topicId) ? p.topicId : null,
      format: p.format,
      pillar: p.pillar,
      audience: p.audience,
      title: p.title,
      brief: p.brief,
      ctaGoal: p.ctaGoal,
      scheduledAt: zonedToUtc(addDays(weekStart, p.day), p.time),
    }));
    for (const s of output.storyDays) {
      itemRows.push({
        planId: plan.id,
        format: "story",
        pillar: "behind_the_scenes",
        audience: s.linkFocus === "partner" ? "b2b_partner" : s.linkFocus === "coaching" ? "coaching" : "both",
        title: `Stories ${WEEKDAYS_DE[s.day]}: ${s.theme}`,
        brief: s.brief,
        ctaGoal: s.linkFocus === "partner" ? "partner_inquiry" : s.linkFocus === "coaching" ? "coaching_application" : "none",
        scheduledAt: zonedToUtc(addDays(weekStart, s.day), "09:00"),
      });
    }
    const items = await tx.insert(schema.contentItems).values(itemRows).returning({ id: schema.contentItems.id });
    const usedTopics = itemRows.map((r) => r.topicId).filter((x): x is string => !!x);
    if (usedTopics.length) {
      await tx.update(schema.topics).set({ status: "planned" }).where(and(inArray(schema.topics.id, usedTopics), eq(schema.topics.status, "backlog")));
    }
    await tx.insert(schema.auditLogs).values({
      actorId: actor.id,
      actorLabel: actor.label,
      action: "plan.generated",
      entityType: "content_plan",
      entityId: plan.id,
      data: { weekStart, items: items.length, agentRunId: runId },
    });
    return { planId: plan.id, itemIds: items.map((i) => i.id) };
  });
}

export async function activatePlan(actor: Actor, planId: string) {
  await db().update(schema.contentPlans).set({ status: "active" }).where(eq(schema.contentPlans.id, planId));
  await audit(actor, "plan.activated", "content_plan", planId);
}
