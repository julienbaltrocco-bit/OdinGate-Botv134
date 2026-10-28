import { readFile } from "node:fs/promises";
import path from "node:path";
import satori from "satori";
import { Resvg } from "@resvg/resvg-js";
import type { BrandSettings } from "@/server/db/schema";
import type { CarouselBody, StorySet } from "@/lib/content-types";

/**
 * Carousel Agent (rendering half): turns slide text into brand-consistent PNGs
 * (1080x1350, 4:5) via satori → SVG → resvg. Also renders story text frames
 * (1080x1920) as templates for the team.
 */

type Node = { type: string; props: Record<string, unknown> & { children?: unknown } };
function h(type: string, style: Record<string, unknown>, ...children: unknown[]): Node {
  return { type, props: { style, children: children.length === 1 ? children[0] : children } };
}

let fontsCache: { name: string; data: Buffer; weight: 400 | 600 | 700; style: "normal" }[] | null = null;
async function fonts() {
  if (!fontsCache) {
    const dir = path.resolve(process.cwd(), "assets/fonts");
    fontsCache = [
      { name: "Inter", data: await readFile(path.join(dir, "Inter-Regular.otf")), weight: 400, style: "normal" },
      { name: "Inter", data: await readFile(path.join(dir, "Inter-SemiBold.otf")), weight: 600, style: "normal" },
      { name: "Inter", data: await readFile(path.join(dir, "Inter-Bold.otf")), weight: 700, style: "normal" },
    ];
  }
  return fontsCache;
}

/** Picks a font size so long text still fits; carousel text must stay readable on a phone. */
export function fitFontSize(text: string, base: number, min: number, charsAtBase: number): number {
  const len = text.length;
  if (len <= charsAtBase) return base;
  return Math.max(min, Math.round(base * Math.sqrt(charsAtBase / len)));
}

async function toPng(node: Node, width: number, height: number): Promise<Buffer> {
  // satori accepts plain element objects; cast keeps React out of the worker bundle.
  const svg = await satori(node as unknown as Parameters<typeof satori>[0], { width, height, fonts: await fonts() });
  return new Resvg(svg, { fitTo: { mode: "width", value: width } }).render().asPng();
}

// satori resolves percentage widths against the padded box, so text columns use explicit pixel widths.
const SLIDE_CONTENT_W = 1080 - 2 * 88;
const STORY_CONTENT_W = 1080 - 2 * 96;

export type SlideRenderOptions = { brand: BrandSettings; index: number; total: number };

export function slideNode(slide: CarouselBody["slides"][number], o: SlideRenderOptions): Node {
  const { colors } = o.brand;
  const isCover = slide.kind === "cover";
  const isCta = slide.kind === "cta";
  const headlineSize = fitFontSize(slide.headline, isCover ? 96 : 72, isCover ? 64 : 48, isCover ? 40 : 45);
  const bodySize = fitFontSize(slide.body, 42, 30, 160);
  const footer = o.brand.handle ? `@${o.brand.handle.replace(/^@/, "")}` : o.brand.personName;

  return h(
    "div",
    {
      width: 1080,
      height: 1350,
      display: "flex",
      flexDirection: "column",
      justifyContent: "center",
      position: "relative",
      backgroundColor: isCta ? colors.accent : colors.background,
      color: colors.foreground,
      paddingLeft: 88,
      paddingRight: 88,
      fontFamily: "Inter",
    },
    // Header and footer are absolutely positioned: satori mis-sizes padded flex columns.
    h(
      "div",
      { position: "absolute", top: 72, left: 88, display: "flex", width: SLIDE_CONTENT_W, justifyContent: "space-between", fontSize: 28, color: isCta ? colors.foreground : colors.muted, fontWeight: 600 },
      h("div", { display: "flex" }, footer || " "),
      h("div", { display: "flex" }, `${o.index + 1} / ${o.total}`),
    ),
    h(
      "div",
      { display: "flex", flexDirection: "column", width: SLIDE_CONTENT_W, gap: 40 },
      isCover ? h("div", { display: "flex", width: 120, height: 10, backgroundColor: colors.accent }) : null,
      h("div", { display: "flex", width: SLIDE_CONTENT_W, fontSize: headlineSize, fontWeight: 700, lineHeight: 1.12, letterSpacing: -1 }, slide.headline),
      slide.body
        ? h("div", { display: "flex", width: SLIDE_CONTENT_W, fontSize: bodySize, fontWeight: 400, lineHeight: 1.4, color: colors.foreground, opacity: 0.92 }, slide.body)
        : null,
    ),
    h(
      "div",
      { position: "absolute", bottom: 72, left: 88, display: "flex", width: SLIDE_CONTENT_W, justifyContent: "flex-end", fontSize: 28, fontWeight: 600, color: isCta ? colors.foreground : colors.accent },
      o.index + 1 < o.total ? "Weiter →" : " ",
    ),
  );
}

export async function renderCarouselSlides(body: CarouselBody, brand: BrandSettings): Promise<Buffer[]> {
  const total = body.slides.length;
  const out: Buffer[] = [];
  for (let i = 0; i < total; i++) out.push(await toPng(slideNode(body.slides[i], { brand, index: i, total }), 1080, 1350));
  return out;
}

export function storyFrameNode(frame: StorySet["frames"][number], brand: BrandSettings, index: number, total: number): Node {
  const { colors } = brand;
  const label: Record<string, string> = {
    poll: "Umfrage",
    question: "Frage-Sticker",
    quiz: "Quiz",
    link: "Link-Sticker",
    selfie_video: "Selfie-Video",
    behind_scenes: "Behind the Scenes",
    repost: "Repost",
    text: "Text",
  };
  return h(
    "div",
    {
      width: 1080,
      height: 1920,
      display: "flex",
      flexDirection: "column",
      justifyContent: "center",
      backgroundColor: colors.background,
      color: colors.foreground,
      padding: "160px 96px",
      fontFamily: "Inter",
      gap: 48,
    },
    h("div", { display: "flex", fontSize: 30, fontWeight: 600, color: colors.accent }, `${label[frame.type] ?? frame.type} · ${index + 1}/${total}`),
    h("div", { display: "flex", width: STORY_CONTENT_W, fontSize: fitFontSize(frame.text, 80, 52, 60), fontWeight: 700, lineHeight: 1.15 }, frame.text),
    frame.interactive
      ? h(
          "div",
          { display: "flex", fontSize: 38, padding: "28px 36px", borderRadius: 24, backgroundColor: colors.foreground, color: colors.background, fontWeight: 600 },
          frame.interactive,
        )
      : null,
    h("div", { display: "flex", width: STORY_CONTENT_W, fontSize: 28, color: colors.muted }, `Visual: ${frame.visualNote}`),
  );
}

export async function renderStoryFrames(body: StorySet, brand: BrandSettings): Promise<Buffer[]> {
  const out: Buffer[] = [];
  for (let i = 0; i < body.frames.length; i++) out.push(await toPng(storyFrameNode(body.frames[i], brand, i, body.frames.length), 1080, 1920));
  return out;
}
