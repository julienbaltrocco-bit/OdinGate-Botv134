import { desc, eq, ne } from "drizzle-orm";
import { z } from "zod";
import { db, schema } from "@/server/db";
import { brandContext, getBrand } from "@/server/brand";
import { generateStructured, webResearch, type Citation } from "@/server/ai/llm";
import { env } from "@/server/env";
import { AUDIENCES, PILLARS } from "@/lib/content-types";
import { audit, type Actor } from "@/server/audit";
import { performanceSummary } from "@/server/analytics/metrics";

/**
 * Research Agent: turns traceable inputs (own notes/FAQs, anonymised lead
 * questions, performance data and, optionally, cited web search results)
 * into prioritised topics. Every topic carries the sources it was derived from.
 */

const TopicIdeas = z.object({
  topics: z.array(
    z.object({
      title: z.string(),
      angle: z.string().describe("Konkreter Blickwinkel / These des Beitrags"),
      pillar: z.enum(PILLARS),
      audience: z.enum(AUDIENCES),
      priority: z.number().describe("0-100, Beitrag zu qualifizierten Leads"),
      rationale: z.string(),
      sourceRefs: z.array(z.string()).describe("IDs der genutzten Quellen (S1, S2, ...) oder URLs"),
    }),
  ),
});

const SYSTEM = `Du bist der Research Agent einer Content-Engine für eine Personal Brand im Crypto Business Development.
Du findest Themen mit hohem Potenzial für qualifizierte B2B-Partner- und Coaching-Anfragen (nicht für reine Reichweite).
Arbeite ausschließlich mit den bereitgestellten Quellen und deinem allgemeinen Fachwissen. Erfinde keine Quellen, Zahlen oder Ereignisse.
Referenziere für jedes Thema die Quellen-IDs (z.B. "S3") oder URLs, aus denen es abgeleitet ist. Wenn ein Thema nur auf Fachwissen beruht, gib "fachwissen" an.`;

export async function runResearch(actor: Actor, opts: { focus?: string; count?: number } = {}) {
  const brand = await getBrand();
  const count = Math.min(Math.max(opts.count ?? 12, 3), 25);

  const [sources, leadQuestions, backlog] = await Promise.all([
    db().select().from(schema.researchSources).orderBy(desc(schema.researchSources.createdAt)).limit(40),
    // Only the free-text message, never names/emails (data minimisation).
    db()
      .select({ type: schema.leads.type, message: schema.leads.message })
      .from(schema.leads)
      .orderBy(desc(schema.leads.createdAt))
      .limit(30),
    db()
      .select({ title: schema.topics.title })
      .from(schema.topics)
      .where(ne(schema.topics.status, "discarded"))
      .orderBy(desc(schema.topics.createdAt))
      .limit(60),
  ]);
  const perf = await performanceSummary();

  const refMap = new Map<string, { kind: string; title: string; url?: string; sourceId?: string }>();
  const lines: string[] = [];
  sources.forEach((s, i) => {
    const ref = `S${i + 1}`;
    refMap.set(ref, { kind: s.kind, title: s.title, url: s.url ?? undefined, sourceId: s.id });
    lines.push(`[${ref}] (${s.kind}) ${s.title}${s.url ? ` <${s.url}>` : ""}\n${s.content.slice(0, 1200)}`);
  });
  leadQuestions
    .filter((l) => l.message.trim())
    .forEach((l, i) => {
      const ref = `L${i + 1}`;
      refMap.set(ref, { kind: "lead_question", title: `Anfrage (${l.type})` });
      lines.push(`[${ref}] (anonymisierte Lead-Anfrage, ${l.type}) ${l.message.slice(0, 600)}`);
    });

  let citations: Citation[] = [];
  if (env().RESEARCH_WEB_SEARCH) {
    const web = await webResearch(
      "research.web",
      "Du recherchierst aktuelle, belegbare Entwicklungen für Crypto Business Development (Börsen-Partnerprogramme, KOL-Marketing, Regulierung wie MiCA, Affiliate-Strukturen). Nenne nur, was die Quellen hergeben.",
      `Recherchiere aktuelle Themen und häufige Fragen für: ${brand.settings.positioning}${opts.focus ? `\nFokus: ${opts.focus}` : ""}`,
    );
    citations = web.citations;
    citations.forEach((c, i) => {
      const ref = `W${i + 1}`;
      refMap.set(ref, { kind: "web_search", title: c.title, url: c.url });
    });
    lines.push(`# Web-Recherche (zitiert)\n${web.memo}\n\nQuellen:\n${citations.map((c, i) => `[W${i + 1}] ${c.title} <${c.url}>`).join("\n")}`);
    for (const c of citations.slice(0, 10)) {
      await db()
        .insert(schema.researchSources)
        .values({ kind: "web_search", title: c.title, content: `Gefunden durch Research Agent (Websuche).`, url: c.url })
        .onConflictDoNothing();
    }
  }

  const prompt = [
    brandContext(brand.settings, brand.derivedStyleGuide),
    `\n# Quellen\n${lines.length ? lines.join("\n\n") : "(Keine internen Quellen hinterlegt – stütze dich auf Fachwissen und markiere das.)"}`,
    `\n# Performance bisher\n${perf.text}`,
    `\n# Bereits vorhandene Themen (nicht wiederholen)\n${backlog.map((b) => `- ${b.title}`).join("\n") || "(keine)"}`,
    opts.focus ? `\n# Fokus dieser Recherche\n${opts.focus}` : "",
    `\nErzeuge ${count} priorisierte Themen, verteilt über alle Content-Säulen und beide Zielgruppen.`,
  ].join("\n");

  const { output, runId } = await generateStructured({
    agent: "research",
    system: SYSTEM,
    prompt,
    schema: TopicIdeas,
    meta: { focus: opts.focus ?? null, sources: refMap.size },
  });

  const rows = output.topics.slice(0, count).map((t) => ({
    title: t.title,
    angle: t.angle,
    pillar: t.pillar,
    audience: t.audience,
    priority: Math.round(Math.min(100, Math.max(0, t.priority))),
    rationale: t.rationale,
    sources: resolveSources(t.sourceRefs, refMap),
    agentRunId: runId,
  }));
  const inserted = rows.length ? await db().insert(schema.topics).values(rows).returning({ id: schema.topics.id }) : [];
  await audit(actor, "research.completed", "agent_run", runId, { topics: inserted.length, webSources: citations.length });
  return { runId, topicIds: inserted.map((r) => r.id) };
}

/** Keeps only references that point to real inputs, so every topic stays traceable. */
export function resolveSources(
  refs: string[],
  refMap: Map<string, { kind: string; title: string; url?: string; sourceId?: string }>,
) {
  const out: { kind: string; title: string; url?: string; sourceId?: string }[] = [];
  for (const raw of refs) {
    const ref = raw.trim().replace(/^\[|\]$/g, "");
    const known = refMap.get(ref.toUpperCase());
    if (known) out.push(known);
    else {
      const byUrl = [...refMap.values()].find((v) => v.url && v.url === ref);
      if (byUrl) out.push(byUrl);
    }
  }
  if (!out.length) out.push({ kind: "expertise", title: "Fachwissen (keine externe Quelle)" });
  return out;
}

export async function discardTopic(actor: Actor, topicId: string) {
  await db().update(schema.topics).set({ status: "discarded" }).where(eq(schema.topics.id, topicId));
  await audit(actor, "topic.discarded", "topic", topicId);
}
