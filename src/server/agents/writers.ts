import { z } from "zod";
import { brandContext, CONTENT_GUARDRAILS } from "@/server/brand";
import { generateStructured } from "@/server/ai/llm";
import { CarouselDraft, ProductionBrief, ReelScript, StorySet } from "@/lib/content-types";
import type { BrandSettings } from "@/server/db/schema";

/**
 * Writing agents. Each is a separate, single-purpose call with its own system
 * prompt so they can be tuned and evaluated independently:
 * - Scriptwriting Agent  → ReelScript
 * - Creative Director    → ProductionBrief (shotlist, raw material, editing)
 * - Carousel Agent       → CarouselDraft
 * - Story Agent          → StorySet
 */

export type WritingContext = {
  brand: BrandSettings;
  styleGuide: string | null;
  item: { title: string; brief: string; pillar: string; audience: string; ctaGoal: string };
  topic?: { title: string; angle: string; sources: { title: string; url?: string }[] } | null;
  trackingUrl?: string | null;
  previous?: { body: unknown; caption: string } | null;
  feedback?: string | null;
};

function contextBlock(ctx: WritingContext): string {
  return [
    brandContext(ctx.brand, ctx.styleGuide),
    CONTENT_GUARDRAILS,
    `\n# Auftrag\nTitel: ${ctx.item.title}\nBriefing: ${ctx.item.brief}\nSäule: ${ctx.item.pillar}\nZielgruppe: ${ctx.item.audience}\nCTA-Ziel: ${ctx.item.ctaGoal}`,
    ctx.topic
      ? `\n# Thema\n${ctx.topic.title} – ${ctx.topic.angle}\nQuellen: ${ctx.topic.sources.map((s) => s.title + (s.url ? ` <${s.url}>` : "")).join("; ")}`
      : "",
    ctx.trackingUrl
      ? `\n# Tracking-Link\nFür Bewerbungen/Anfragen: ${ctx.trackingUrl} (als "Link in Bio" bzw. Story-Link-Sticker referenzieren, nicht als klickbarer Caption-Link versprechen).`
      : "",
    ctx.previous ? `\n# Vorherige Version\n${JSON.stringify(ctx.previous.body).slice(0, 6000)}\nCaption: ${ctx.previous.caption}` : "",
    ctx.feedback ? `\n# Feedback für die Überarbeitung (verbindlich umsetzen)\n${ctx.feedback}` : "",
  ]
    .filter(Boolean)
    .join("\n");
}

const SCRIPT_SYSTEM = `Du bist der Scriptwriting Agent. Du schreibst Instagram-Reel-Skripte (25-60 Sekunden) in der Stimme der Marke.
Aufbau: starker Hook in den ersten 1-3 Sekunden (konkret, keine Clickbait-Lüge), klare Argumentation, mindestens ein konkretes (anonymisiertes) Praxisbeispiel, ein einziger klarer CTA passend zum CTA-Ziel.
Gesprochene Sprache: kurze Sätze, natürlich, wie der Kunde selbst reden würde. Keine KI-Floskeln, keine Emojis.
Die Summe der Segment-Dauern soll targetDurationSec ergeben (ca. 2,5 Wörter pro Sekunde).`;

export async function writeReelScript(ctx: WritingContext) {
  return generateStructured({
    agent: "scriptwriter",
    system: SCRIPT_SYSTEM,
    prompt: contextBlock(ctx),
    schema: ReelScript,
    meta: { title: ctx.item.title, regenerate: !!ctx.feedback },
  });
}

const CREATIVE_SYSTEM = `Du bist der Creative Director Agent. Aus einem fertigen Reel-Skript erstellst du ein umsetzbares Produktionsbriefing für eine Einzelperson mit kleinem Marketing-Team:
Konzept, Shotlist (Einstellung, Bildausschnitt, Hinweise), konkret benötigtes Rohmaterial, B-Roll, Schnittanweisungen, Musikstimmung, Designvorgaben (Untertitel-Stil, Overlays).
Realistisch und authentisch: Büro, Laptop, Calls, Whiteboard, Gehen und Sprechen. Kein inszenierter Luxus, keine fremden Logos/Marken ohne Rechte, keine vertraulichen Bildschirminhalte.
Benenne unter manualSteps, was bewusst manuell bleibt (z.B. Dreh, Freigabe von Bildschirmaufnahmen).`;

export async function writeProductionBrief(ctx: WritingContext, script: ReelScript) {
  return generateStructured({
    agent: "creative_director",
    system: CREATIVE_SYSTEM,
    prompt: `${contextBlock({ ...ctx, previous: null, feedback: null })}\n\n# Skript\n${JSON.stringify(script)}`,
    schema: ProductionBrief,
    meta: { title: ctx.item.title },
  });
}

const CAROUSEL_SYSTEM = `Du bist der Carousel Agent. Du erstellst Instagram-Carousels (6-9 Slides, Format 4:5) mit hohem Speicher-Wert.
Slide 1 (cover): klare Headline mit Nutzenversprechen ohne Übertreibung, max. 10 Wörter.
Content-Slides: eine Idee pro Slide, Headline max. 8 Wörter, Body max. 35 Wörter, gut lesbar.
Letzte Slide (cta): ein klarer CTA passend zum CTA-Ziel.
Caption: ergänzt die Slides, endet mit CTA; Kennzeichnung/Risikohinweis wenn nötig. Keine Emojis.`;

export async function writeCarousel(ctx: WritingContext) {
  return generateStructured({
    agent: "carousel",
    system: CAROUSEL_SYSTEM,
    prompt: contextBlock(ctx),
    schema: CarouselDraft,
    meta: { title: ctx.item.title, regenerate: !!ctx.feedback },
  });
}

const STORY_SYSTEM = `Du bist der Story Agent. Du planst ein Story-Set für einen Tag (3-5 Frames) mit echten Einblicken in den Geschäftsalltag.
Mische: Behind-the-Scenes, eine Interaktion (Umfrage, Frage-Sticker oder Quiz), ggf. einen Link-Sticker zum Tracking-Link wenn ein Link-Fokus gesetzt ist.
Story-Texte sind kurz (max. 20 Wörter pro Frame). Keine automatisierten DMs; Anfragen laufen über Link-Sticker oder Profil.`;

export async function writeStorySet(ctx: WritingContext) {
  return generateStructured({
    agent: "story",
    system: STORY_SYSTEM,
    prompt: contextBlock(ctx),
    schema: StorySet,
    meta: { title: ctx.item.title, regenerate: !!ctx.feedback },
  });
}

/** Brand Voice Agent: derives a concise style guide from approved texts. */
const StyleGuide = z.object({
  summary: z.string(),
  toneTraits: z.array(z.string()),
  sentenceStyle: z.string(),
  vocabularyToUse: z.array(z.string()),
  vocabularyToAvoid: z.array(z.string()),
  hookPatterns: z.array(z.string()),
  ctaPatterns: z.array(z.string()),
});

export async function deriveStyleGuide(brand: BrandSettings, samples: string[]) {
  const res = await generateStructured({
    agent: "brand_voice",
    system:
      "Du bist der Brand Voice Agent. Analysiere die freigegebenen Texte und Beispiele und leite einen präzisen, umsetzbaren Stilleitfaden ab. Beschreibe nur Muster, die tatsächlich in den Texten vorkommen.",
    prompt: `${brandContext(brand, null)}\n\n# Freigegebene Texte und Beispiele\n${samples.map((s, i) => `[${i + 1}]\n${s}`).join("\n\n")}`,
    schema: StyleGuide,
    meta: { samples: samples.length },
  });
  const g = res.output;
  const text = [
    g.summary,
    `Ton: ${g.toneTraits.join(", ")}`,
    `Satzbau: ${g.sentenceStyle}`,
    `Bevorzugte Begriffe: ${g.vocabularyToUse.join(", ")}`,
    `Vermeiden: ${g.vocabularyToAvoid.join(", ")}`,
    `Hook-Muster: ${g.hookPatterns.join(" | ")}`,
    `CTA-Muster: ${g.ctaPatterns.join(" | ")}`,
  ].join("\n");
  return { text, runId: res.runId };
}
