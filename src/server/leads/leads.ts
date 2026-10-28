import { eq } from "drizzle-orm";
import { z } from "zod";
import { db, schema } from "@/server/db";
import { audit, SYSTEM_ACTOR, type Actor } from "@/server/audit";
import { emitEvent } from "@/server/integrations/crm/webhooks";

/**
 * Inbound leads from the application forms (/apply/coaching, /apply/partner).
 * Qualification is rule-based and transparent (score + reasons), so the sales
 * team can see why a lead is ranked high. No automated outreach.
 */

export const CONSENT_TEXT_VERSION = "2026-10-v1";
export const CONSENT_TEXT =
  "Ich willige ein, dass meine Angaben zur Bearbeitung meiner Anfrage gespeichert und verarbeitet werden. Die Einwilligung kann ich jederzeit per E-Mail widerrufen. Details in der Datenschutzerklärung.";

const base = {
  name: z.string().trim().min(2).max(120),
  email: z.string().trim().toLowerCase().email().max(200),
  instagramHandle: z.string().trim().max(60).optional().default(""),
  message: z.string().trim().max(3000).optional().default(""),
  consent: z.literal(true, { message: "Einwilligung erforderlich" }),
  src: z.string().max(40).optional(),
  utm: z.record(z.string(), z.string()).optional().default({}),
  // Honeypot against bots: must stay empty.
  website: z.string().max(0).optional().default(""),
};

export const CoachingApplication = z.object({
  ...base,
  type: z.literal("coaching"),
  salesExperience: z.enum(["none", "lt1", "1to3", "gt3"]),
  cryptoExperience: z.enum(["none", "basic", "active", "industry"]),
  hoursPerWeek: z.enum(["lt5", "5to15", "gt15"]),
  budgetOk: z.boolean(),
  goal: z.string().trim().max(1000).optional().default(""),
});

export const PartnerInquiry = z.object({
  ...base,
  type: z.literal("partner"),
  company: z.string().trim().max(160).optional().default(""),
  communitySize: z.enum(["lt1k", "1kto10k", "10kto50k", "gt50k"]),
  platforms: z.string().trim().max(300).optional().default(""),
  monthlyVolume: z.enum(["unknown", "lt1m", "1mto10m", "gt10m"]),
  currentExchangePartner: z.enum(["none", "yes_unhappy", "yes_ok"]),
});

export const LeadSubmission = z.discriminatedUnion("type", [CoachingApplication, PartnerInquiry]);
export type LeadSubmission = z.infer<typeof LeadSubmission>;

export function scoreLead(l: LeadSubmission): { score: number; reasons: string[] } {
  const reasons: string[] = [];
  let score = 0;
  const add = (pts: number, why: string) => {
    score += pts;
    reasons.push(`${pts > 0 ? "+" : ""}${pts} ${why}`);
  };
  if (l.type === "coaching") {
    add({ none: 0, lt1: 10, "1to3": 25, gt3: 30 }[l.salesExperience], "Vertriebserfahrung");
    add({ none: 0, basic: 5, active: 15, industry: 25 }[l.cryptoExperience], "Krypto-Erfahrung");
    add({ lt5: 0, "5to15": 15, gt15: 20 }[l.hoursPerWeek], "Zeitbudget");
    add(l.budgetOk ? 25 : -20, l.budgetOk ? "Budget bestätigt" : "Budget nicht bestätigt");
  } else {
    add({ lt1k: 5, "1kto10k": 20, "10kto50k": 35, gt50k: 45 }[l.communitySize], "Community-Größe");
    add({ unknown: 0, lt1m: 10, "1mto10m": 25, gt10m: 35 }[l.monthlyVolume], "Handelsvolumen");
    add({ none: 15, yes_unhappy: 20, yes_ok: 5 }[l.currentExchangePartner], "Partner-Situation");
  }
  if (l.instagramHandle) add(5, "Instagram-Handle angegeben");
  return { score: Math.max(0, Math.min(100, score)), reasons };
}

export async function createLead(input: unknown) {
  const data = LeadSubmission.parse(input);
  const link = data.src
    ? (await db().select().from(schema.trackingLinks).where(eq(schema.trackingLinks.code, data.src)))[0]
    : undefined;
  const { score, reasons } = scoreLead(data);
  const { name, email, instagramHandle, message, consent: _c, src: _s, utm, website: _w, type, ...answers } = data;
  const [lead] = await db()
    .insert(schema.leads)
    .values({
      type,
      name,
      email,
      instagramHandle: instagramHandle || null,
      company: "company" in answers ? (answers.company as string) || null : null,
      message,
      answers: answers as Record<string, string | boolean>,
      score,
      scoreReasons: reasons,
      sourceLinkId: link?.id ?? null,
      sourceItemId: link?.itemId ?? null,
      utm,
      consentAt: new Date(),
      consentText: `${CONSENT_TEXT_VERSION}: ${CONSENT_TEXT}`,
    })
    .returning();
  await audit(SYSTEM_ACTOR, "lead.created", "lead", lead.id, { type, score, attributed: !!link });
  await emitEvent("lead.created", leadPayload(lead));
  return lead;
}

export function leadPayload(l: typeof schema.leads.$inferSelect) {
  return {
    id: l.id,
    type: l.type,
    name: l.name,
    email: l.email,
    instagramHandle: l.instagramHandle,
    company: l.company,
    message: l.message,
    answers: l.answers,
    score: l.score,
    scoreReasons: l.scoreReasons,
    stage: l.stage,
    sourceItemId: l.sourceItemId,
    sourceLinkId: l.sourceLinkId,
    utm: l.utm,
    consentAt: l.consentAt,
    dealValueUsd: l.dealValueUsd,
    crmExternalId: l.crmExternalId,
    createdAt: l.createdAt,
    updatedAt: l.updatedAt,
  };
}

export const LeadUpdate = z.object({
  stage: z.enum(["new", "qualified", "call_scheduled", "won", "lost", "disqualified"]).optional(),
  notes: z.string().max(5000).optional(),
  dealValueUsd: z.number().min(0).nullable().optional(),
  crmExternalId: z.string().max(200).nullable().optional(),
});

export async function updateLead(actor: Actor, id: string, patch: z.infer<typeof LeadUpdate>) {
  const data = LeadUpdate.parse(patch);
  const [lead] = await db()
    .update(schema.leads)
    .set({ ...data, ...(data.crmExternalId !== undefined ? { crmSyncedAt: new Date() } : {}), updatedAt: new Date() })
    .where(eq(schema.leads.id, id))
    .returning();
  if (!lead) throw new Error("Lead nicht gefunden");
  await audit(actor, "lead.updated", "lead", id, { fields: Object.keys(data) });
  await emitEvent("lead.updated", leadPayload(lead));
  return lead;
}

/** DSGVO: erasure on request. Keeps an anonymised row so attribution stats stay correct. */
export async function anonymizeLead(actor: Actor, id: string) {
  await db()
    .update(schema.leads)
    .set({ name: "[gelöscht]", email: `deleted-${id}@invalid`, instagramHandle: null, company: null, message: "", answers: {}, notes: "", updatedAt: new Date() })
    .where(eq(schema.leads.id, id));
  await audit(actor, "lead.anonymized", "lead", id);
}
