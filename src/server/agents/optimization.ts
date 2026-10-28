import { z } from "zod";
import { db, schema } from "@/server/db";
import { brandContext, getBrand } from "@/server/brand";
import { generateStructured } from "@/server/ai/llm";
import { funnelStats, performanceSummary } from "@/server/analytics/metrics";
import { audit, type Actor } from "@/server/audit";

/**
 * Optimization Agent: turns measured performance and funnel data into concrete,
 * evidence-backed recommendations. Refuses to speculate without data.
 */
const Recs = z.object({
  recommendations: z.array(
    z.object({
      category: z.enum(["topic", "hook", "format", "cta", "timing", "conversion"]),
      title: z.string(),
      body: z.string().describe("Konkrete Änderung für die nächste Woche"),
      evidence: z.string().describe("Welche Messwerte das stützen"),
      confidence: z.enum(["low", "medium", "high"]),
    }),
  ),
});

export class NotEnoughDataError extends Error {
  constructor() {
    super("Noch keine veröffentlichten Inhalte mit Messwerten – Optimierung erst nach den ersten Daten sinnvoll.");
    this.name = "NotEnoughDataError";
  }
}

export async function runOptimization(actor: Actor) {
  const perf = await performanceSummary();
  if (!perf.rows.length) throw new NotEnoughDataError();
  const funnel = await funnelStats();
  const brand = await getBrand();
  const { output, runId } = await generateStructured({
    agent: "optimization",
    system:
      "Du bist der Optimization Agent. Ziel: mehr qualifizierte B2B-Partner- und Coaching-Anfragen. Leite 3-7 Empfehlungen ausschließlich aus den Daten ab, nenne die Evidenz und bewerte die Sicherheit ehrlich (wenige Datenpunkte = low).",
    prompt: `${brandContext(brand.settings, brand.derivedStyleGuide)}\n\n# Performance\n${perf.text}\n\n# Funnel (Leads nach Typ/Stage, Klicks 30 Tage)\n${JSON.stringify(funnel)}`,
    schema: Recs,
    meta: { items: perf.rows.length },
  });
  const rows = output.recommendations.map((r) => ({ ...r, agentRunId: runId }));
  if (rows.length) await db().insert(schema.recommendations).values(rows);
  await audit(actor, "optimization.completed", "agent_run", runId, { recommendations: rows.length });
  return { runId, count: rows.length };
}
