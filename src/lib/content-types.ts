import { z } from "zod";

/**
 * Shared content shapes. Used as structured-output schemas for the agents,
 * for validating human edits, and by the UI/renderers.
 *
 * Note: the Claude structured-output JSON schema subset does not enforce numeric
 * ranges or array lengths; those rules are enforced in code (see workflow/plan-rules.ts).
 */

export const FORMATS = ["reel", "carousel", "story"] as const;
export const PILLARS = ["authority", "behind_the_scenes", "education", "personal", "conversion"] as const;
export const AUDIENCES = ["b2b_partner", "coaching", "both"] as const;
export const CTA_TYPES = [
  "coaching_application",
  "partner_inquiry",
  "profile_visit",
  "follow",
  "save",
  "comment_keyword",
  "share",
  "none",
] as const;

export type Format = (typeof FORMATS)[number];
export type Pillar = (typeof PILLARS)[number];
export type Audience = (typeof AUDIENCES)[number];
export type CtaType = (typeof CTA_TYPES)[number];

export const PILLAR_LABELS: Record<Pillar, string> = {
  authority: "Authority & Expertise",
  behind_the_scenes: "Behind the Scenes",
  education: "Education",
  personal: "Personal Brand",
  conversion: "Conversion",
};
export const AUDIENCE_LABELS: Record<Audience, string> = {
  b2b_partner: "B2B-Partner",
  coaching: "Coaching-Kunden",
  both: "Beide",
};
export const FORMAT_LABELS: Record<Format, string> = { reel: "Reel", carousel: "Carousel", story: "Story" };

// --- Reel -------------------------------------------------------------------

export const ReelSegment = z.object({
  label: z.string().describe("Abschnitt, z.B. Hook, Kontext, Beispiel, Takeaway, CTA"),
  spoken: z.string().describe("Gesprochener Text, natürlich formuliert"),
  onScreenText: z.string().describe("Kurzer Text-Overlay, leer wenn keiner"),
  visual: z.string().describe("Was im Bild zu sehen ist"),
  durationSec: z.number().describe("Geschätzte Dauer in Sekunden"),
});

export const ReelScript = z.object({
  hook: z.string().describe("Erster gesprochener Satz (0-3 Sekunden)"),
  onScreenHook: z.string().describe("Text-Overlay zum Einstieg, max. 8 Wörter"),
  segments: z.array(ReelSegment),
  cta: z.string(),
  ctaType: z.enum(CTA_TYPES),
  targetDurationSec: z.number(),
  caption: z.string().describe("Instagram-Caption inkl. CTA und ggf. Kennzeichnung"),
  hashtags: z.array(z.string()),
  claimsToVerify: z.array(z.string()).describe("Aussagen, die vor Veröffentlichung belegt werden müssen"),
});
export type ReelScript = z.infer<typeof ReelScript>;

export const ProductionBrief = z.object({
  concept: z.string(),
  shotlist: z.array(
    z.object({
      shot: z.string(),
      description: z.string(),
      framing: z.string(),
      notes: z.string(),
    }),
  ),
  rawMaterialNeeded: z.array(z.string()).describe("Konkretes Rohmaterial, das gefilmt/beschafft werden muss"),
  editingNotes: z.array(z.string()),
  broll: z.array(z.string()),
  musicMood: z.string(),
  designNotes: z.string(),
  manualSteps: z.array(z.string()).describe("Schritte, die bewusst manuell bleiben"),
});
export type ProductionBrief = z.infer<typeof ProductionBrief>;

export type ReelBody = ReelScript & { production?: ProductionBrief };

// --- Carousel ---------------------------------------------------------------

export const CarouselSlide = z.object({
  kind: z.enum(["cover", "content", "cta"]),
  headline: z.string(),
  body: z.string(),
});

export const CarouselDraft = z.object({
  slides: z.array(CarouselSlide),
  caption: z.string(),
  hashtags: z.array(z.string()),
  designNotes: z.string(),
  ctaType: z.enum(CTA_TYPES),
  claimsToVerify: z.array(z.string()),
});
export type CarouselDraft = z.infer<typeof CarouselDraft>;
export type CarouselBody = Omit<CarouselDraft, "caption">;

// --- Story ------------------------------------------------------------------

export const StoryFrame = z.object({
  type: z.enum(["text", "poll", "question", "quiz", "link", "selfie_video", "behind_scenes", "repost"]),
  text: z.string(),
  interactive: z.string().describe("Sticker-Konfiguration (z.B. Umfrage-Optionen), leer wenn keiner"),
  visualNote: z.string(),
  usesTrackingLink: z.boolean(),
});

export const StorySet = z.object({
  dayTheme: z.string(),
  frames: z.array(StoryFrame),
  claimsToVerify: z.array(z.string()),
});
export type StorySet = z.infer<typeof StorySet>;

export type ContentBody = ReelBody | CarouselBody | StorySet;

/** Concatenated human-readable text of a body + caption (for compliance checks and brand-voice analysis). */
export function bodyText(format: Format, body: Record<string, unknown>, caption = ""): string {
  const parts: string[] = [];
  if (format === "reel") {
    const b = body as Partial<ReelBody>;
    parts.push(b.hook ?? "", b.onScreenHook ?? "");
    for (const s of b.segments ?? []) parts.push(s.spoken, s.onScreenText);
    parts.push(b.cta ?? "");
  } else if (format === "carousel") {
    for (const s of (body as Partial<CarouselBody>).slides ?? []) parts.push(s.headline, s.body);
  } else {
    for (const f of (body as Partial<StorySet>).frames ?? []) parts.push(f.text, f.interactive);
  }
  parts.push(caption);
  return parts.filter(Boolean).join("\n");
}

/** Spoken script of a reel, used for script-timed subtitles. */
export function reelSpokenSegments(body: Partial<ReelBody>): { text: string; durationSec: number }[] {
  return (body.segments ?? [])
    .filter((s) => s.spoken?.trim())
    .map((s) => ({ text: s.spoken.trim(), durationSec: Math.max(1, Number(s.durationSec) || 3) }));
}
