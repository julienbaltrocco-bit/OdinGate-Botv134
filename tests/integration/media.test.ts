import { createReadStream } from "node:fs";
import { mkdtemp, rm } from "node:fs/promises";
import { tmpdir } from "node:os";
import path from "node:path";
import { afterAll, beforeAll, describe, expect, it } from "vitest";
import { eq } from "drizzle-orm";
import { db, schema } from "@/server/db";
import { ingestUpload } from "@/server/media/assets";
import { ffmpeg, probe } from "@/server/media/ffmpeg";
import { requestRender } from "@/server/media/render-jobs";
import { storage } from "@/server/media/storage";
import { createVersion, type Principal } from "@/server/workflow/content";
import { drainJobs, makeUser, resetDb } from "../helpers";

let dir: string;
let editor: Principal;

async function makeClip(name: string, opts: { w: number; h: number; sec: number; audio: boolean }) {
  const out = path.join(dir, name);
  const args = ["-f", "lavfi", "-i", `testsrc2=size=${opts.w}x${opts.h}:rate=30:duration=${opts.sec}`];
  if (opts.audio) args.push("-f", "lavfi", "-i", `sine=frequency=440:duration=${opts.sec}`);
  args.push("-c:v", "libx264", "-pix_fmt", "yuv420p", ...(opts.audio ? ["-c:a", "aac"] : []), "-shortest", out);
  await ffmpeg(args);
  return out;
}

async function upload(file: string, rights: "own" | "unknown", mime = "video/mp4") {
  return ingestUpload(
    { id: editor.id, label: editor.label },
    { filename: path.basename(file), mimeType: mime, body: createReadStream(file), rightsStatus: rights, rightsNote: "Test", tags: [] },
  );
}

async function makeItem(format: "reel" | "carousel" | "story", body: Record<string, unknown>) {
  const [item] = await db().insert(schema.contentItems).values({ format, pillar: "education", audience: "both", title: `Test ${format}` }).returning();
  await createVersion(editor, item.id, { body, caption: "Caption", source: "human" });
  return item;
}

beforeAll(async () => {
  await resetDb();
  editor = await makeUser("editor");
  dir = await mkdtemp(path.join(tmpdir(), "ce-media-test-"));
});
afterAll(async () => {
  await rm(dir, { recursive: true, force: true });
});

describe("media pipeline", () => {
  it("ingests uploads with probed metadata", async () => {
    const clip = await makeClip("landscape.mp4", { w: 1280, h: 720, sec: 4, audio: true });
    const asset = await upload(clip, "own");
    expect(asset.kind).toBe("video");
    expect(asset.width).toBe(1280);
    expect(asset.durationSec).toBeCloseTo(4, 0);
    expect(await storage().size(asset.storageKey)).toBe(asset.sizeBytes);
  });

  it("renders a 9:16 reel with subtitles, overlays and two variants from raw footage", async () => {
    const a = await upload(await makeClip("a.mp4", { w: 1920, h: 1080, sec: 8, audio: true }), "own");
    const b = await upload(await makeClip("b.mp4", { w: 720, h: 1280, sec: 4, audio: false }), "own");
    const item = await makeItem("reel", {
      hook: "Die meisten Deals scheitern nicht am Preis",
      onScreenHook: "Daran scheitern Deals",
      segments: [
        { label: "Hook", spoken: "Die meisten Deals scheitern nicht am Preis.", onScreenText: "", visual: "", durationSec: 3 },
        { label: "Kontext", spoken: "Sie scheitern an unklaren Abrechnungen und fehlender Struktur im Partnermanagement.", onScreenText: "", visual: "", durationSec: 6 },
        { label: "CTA", spoken: "Mehr dazu im Profil.", onScreenText: "", visual: "", durationSec: 2 },
      ],
    });
    const render = await requestRender({ id: editor.id, label: editor.label }, item.id, {
      clips: [{ assetId: a.id, start: 1, end: 8 }, { assetId: b.id }],
      subtitles: { mode: "script" },
      ctaText: "Link in Bio",
      variants: [{ name: "main" }, { name: "short", maxDurationSec: 5 }],
    });
    const log = await drainJobs();
    const [done] = await db().select().from(schema.renders).where(eq(schema.renders.id, render.id));
    expect(done.error, log.join("\n")).toBeNull();
    expect(done.status).toBe("succeeded");
    expect(done.outputAssetIds).toHaveLength(4);

    const outputs = await db().select().from(schema.mediaAssets).where(eq(schema.mediaAssets.renderId, render.id));
    const main = outputs.find((o) => o.filename === "reel-main.mp4")!;
    const short = outputs.find((o) => o.filename === "reel-short.mp4")!;
    const info = await storage().withLocalFile(main.storageKey, probe);
    expect(info).toMatchObject({ width: 1080, height: 1920, videoCodec: "h264", audioCodec: "aac", hasAudio: true });
    expect(info.durationSec!).toBeGreaterThan(10.5);
    expect(info.durationSec!).toBeLessThan(11.6);
    const shortInfo = await storage().withLocalFile(short.storageKey, probe);
    expect(shortInfo.durationSec!).toBeLessThan(5.3);
    expect(outputs.some((o) => o.mimeType === "image/jpeg")).toBe(true);
  });

  it("refuses to render footage with unclear usage rights", async () => {
    const c = await upload(await makeClip("c.mp4", { w: 640, h: 360, sec: 2, audio: false }), "unknown");
    const item = await makeItem("reel", { hook: "x", segments: [] });
    const render = await requestRender({ id: editor.id, label: editor.label }, item.id, {
      clips: [{ assetId: c.id }],
      subtitles: { mode: "none" },
      variants: [{ name: "main" }],
    });
    await drainJobs();
    const [done] = await db().select().from(schema.renders).where(eq(schema.renders.id, render.id));
    expect(done.status).toBe("failed");
    expect(done.error).toMatch(/Nutzungsrechte/);
  });

  it("renders carousel slides as 1080x1350 PNGs and story frames as 1080x1920", async () => {
    const carousel = await makeItem("carousel", {
      slides: [
        { kind: "cover", headline: "5 Fehler bei Börsen-Partnerschaften", body: "" },
        { kind: "content", headline: "Keine Abrechnungsprüfung", body: "Wer die Abrechnung nicht versteht, verhandelt blind. Fordere eine nachvollziehbare Aufschlüsselung." },
        { kind: "cta", headline: "Speichern für den nächsten Deal", body: "Mehr im Profil." },
      ],
    });
    const story = await makeItem("story", {
      dayTheme: "Alltag",
      frames: [
        { type: "behind_scenes", text: "Drei Partner-Calls heute", interactive: "", visualNote: "Desk", usesTrackingLink: false },
        { type: "poll", text: "Wie verhandelt ihr?", interactive: "Selbst / Agentur", visualNote: "Text", usesTrackingLink: false },
        { type: "text", text: "Learning des Tages", interactive: "", visualNote: "Notiz", usesTrackingLink: false },
      ],
    });
    await requestRender({ id: editor.id, label: editor.label }, carousel.id);
    await requestRender({ id: editor.id, label: editor.label }, story.id);
    await drainJobs();
    const slides = await db().select().from(schema.mediaAssets).where(eq(schema.mediaAssets.itemId, carousel.id));
    expect(slides).toHaveLength(3);
    expect(slides.every((s) => s.width === 1080 && s.height === 1350 && s.mimeType === "image/png")).toBe(true);
    const frames = await db().select().from(schema.mediaAssets).where(eq(schema.mediaAssets.itemId, story.id));
    expect(frames).toHaveLength(3);
    expect(frames[0].height).toBe(1920);
  });
});
