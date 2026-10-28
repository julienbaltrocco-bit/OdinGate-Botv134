import { desc, eq } from "drizzle-orm";
import { db, schema } from "@/server/db";
import { getBrand } from "@/server/brand";
import { deriveStyleGuide } from "./writers";
import { bodyText, type Format } from "@/lib/content-types";
import { audit, type Actor } from "@/server/audit";

/** Collects approved texts (+ the customer's own examples) and updates the derived style guide. */
export async function refreshStyleGuide(actor: Actor) {
  const brand = await getBrand();
  const approved = await db()
    .select({ format: schema.contentItems.format, body: schema.contentVersions.body, caption: schema.contentVersions.caption })
    .from(schema.approvals)
    .innerJoin(schema.contentVersions, eq(schema.contentVersions.id, schema.approvals.versionId))
    .innerJoin(schema.contentItems, eq(schema.contentItems.id, schema.approvals.itemId))
    .where(eq(schema.approvals.decision, "approved"))
    .orderBy(desc(schema.approvals.createdAt))
    .limit(25);
  const samples = [
    ...brand.settings.examples,
    ...approved.map((a) => bodyText(a.format as Format, a.body, a.caption)),
  ].filter((s) => s.trim().length > 40);
  if (samples.length < 3) {
    throw new Error("Mindestens 3 freigegebene Texte oder eigene Beispieltexte nötig, um den Stil abzuleiten.");
  }
  const { text, runId } = await deriveStyleGuide(brand.settings, samples.slice(0, 30));
  await db().update(schema.brandProfile).set({ derivedStyleGuide: text, derivedAt: new Date(), updatedAt: new Date() }).where(eq(schema.brandProfile.id, 1));
  await audit(actor, "brand.style_derived", "brand_profile", "1", { samples: samples.length, agentRunId: runId });
  return { runId, samples: samples.length };
}
