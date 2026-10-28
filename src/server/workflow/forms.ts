import { CTA_TYPES, type CarouselBody, type ReelBody, type StorySet } from "@/lib/content-types";

/**
 * Converts editor form submissions into content bodies. Rows whose main text
 * is empty are dropped, so the editor can offer blank rows for additions.
 */

type Get = (key: string) => string;
const getter = (fd: FormData): Get => (key) => {
  const v = fd.get(key);
  return typeof v === "string" ? v.trim() : "";
};

function indices(fd: FormData, prefix: string): number[] {
  const set = new Set<number>();
  for (const key of fd.keys()) {
    const m = key.match(new RegExp(`^${prefix}_(\\d+)_`));
    if (m) set.add(Number(m[1]));
  }
  return [...set].sort((a, b) => a - b);
}

export function reelFromForm(fd: FormData, previous: Partial<ReelBody>): ReelBody {
  const g = getter(fd);
  const segments = indices(fd, "seg")
    .map((i) => ({
      label: g(`seg_${i}_label`) || "Abschnitt",
      spoken: g(`seg_${i}_spoken`),
      onScreenText: g(`seg_${i}_onScreenText`),
      visual: g(`seg_${i}_visual`),
      durationSec: Number(g(`seg_${i}_durationSec`)) || 3,
    }))
    .filter((s) => s.spoken || s.onScreenText);
  const ctaType = g("ctaType");
  return {
    ...previous,
    hook: g("hook"),
    onScreenHook: g("onScreenHook"),
    segments,
    cta: g("cta"),
    ctaType: (CTA_TYPES as readonly string[]).includes(ctaType) ? (ctaType as ReelBody["ctaType"]) : "none",
    targetDurationSec: segments.reduce((a, s) => a + s.durationSec, 0),
    caption: "",
    hashtags: previous.hashtags ?? [],
    claimsToVerify: g("claimsToVerify").split("\n").map((s) => s.trim()).filter(Boolean),
  };
}

export function carouselFromForm(fd: FormData, previous: Partial<CarouselBody>): CarouselBody {
  const g = getter(fd);
  const slides = indices(fd, "slide")
    .map((i) => ({
      kind: (["cover", "content", "cta"].includes(g(`slide_${i}_kind`)) ? g(`slide_${i}_kind`) : "content") as "cover" | "content" | "cta",
      headline: g(`slide_${i}_headline`),
      body: g(`slide_${i}_body`),
    }))
    .filter((s) => s.headline);
  return {
    slides,
    hashtags: previous.hashtags ?? [],
    designNotes: g("designNotes"),
    ctaType: previous.ctaType ?? "none",
    claimsToVerify: g("claimsToVerify").split("\n").map((s) => s.trim()).filter(Boolean),
  };
}

const FRAME_TYPES = ["text", "poll", "question", "quiz", "link", "selfie_video", "behind_scenes", "repost"] as const;

export function storyFromForm(fd: FormData, previous: Partial<StorySet>): StorySet {
  const g = getter(fd);
  const frames = indices(fd, "frame")
    .map((i) => ({
      type: ((FRAME_TYPES as readonly string[]).includes(g(`frame_${i}_type`)) ? g(`frame_${i}_type`) : "text") as StorySet["frames"][number]["type"],
      text: g(`frame_${i}_text`),
      interactive: g(`frame_${i}_interactive`),
      visualNote: g(`frame_${i}_visualNote`),
      usesTrackingLink: fd.get(`frame_${i}_usesTrackingLink`) === "on",
    }))
    .filter((f) => f.text);
  return { dayTheme: g("dayTheme") || previous.dayTheme || "", frames, claimsToVerify: previous.claimsToVerify ?? [] };
}

export { FRAME_TYPES };
