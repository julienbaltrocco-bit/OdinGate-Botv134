import { mkdtemp, readFile, rm, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import path from "node:path";
import { eq, inArray } from "drizzle-orm";
import { z } from "zod";
import { db, schema } from "@/server/db";
import { getBrand } from "@/server/brand";
import { reelSpokenSegments, type ReelBody } from "@/lib/content-types";
import { ffmpeg, probe } from "./ffmpeg";
import { buildAss, cuesFromScript, parseSrt, type Cue } from "./subtitles";
import { storage } from "./storage";
import { registerGeneratedFile } from "./assets";
import { transcribe } from "./transcribe";

/**
 * Production Agent (deterministic): renders 9:16 Reel drafts from uploaded
 * footage with FFmpeg — trimming/concatenation, 1080x1920 crop, burned-in
 * subtitles, hook + CTA overlays, logo, optional music bed, loudness
 * normalisation — and produces one MP4 + thumbnail per variant.
 */

export const FONT_DIR = path.resolve(process.cwd(), "assets/fonts");
export const OUT_W = 1080;
export const OUT_H = 1920;
export const FPS = 30;

export const ReelRenderInput = z.object({
  clips: z.array(z.object({ assetId: z.string().uuid(), start: z.number().min(0).optional(), end: z.number().positive().optional() })).min(1),
  subtitles: z.object({ mode: z.enum(["script", "asset", "transcribe", "none"]), assetId: z.string().uuid().optional() }),
  hookText: z.string().max(120).optional(),
  hookDurationSec: z.number().min(0).max(10).default(3),
  ctaText: z.string().max(120).optional(),
  ctaDurationSec: z.number().min(0).max(10).default(3),
  logoAssetId: z.string().uuid().nullable().optional(),
  musicAssetId: z.string().uuid().nullable().optional(),
  musicVolume: z.number().min(0).max(1).default(0.12),
  variants: z.array(z.object({ name: z.string().min(1).max(40), maxDurationSec: z.number().positive().optional() })).min(1).max(4),
});
export type ReelRenderInput = z.infer<typeof ReelRenderInput>;

export type ClipSource = { path: string; start: number; end: number; hasAudio: boolean };

/** Pure: builds the ffmpeg argument list. Unit-tested. */
export function buildReelArgs(o: {
  clips: ClipSource[];
  assPath: string | null;
  fontDir: string;
  logoPath: string | null;
  musicPath: string | null;
  musicVolume: number;
  durationSec: number;
  outPath: string;
}): string[] {
  const args: string[] = [];
  const filters: string[] = [];
  o.clips.forEach((c) => args.push("-ss", c.start.toFixed(3), "-to", c.end.toFixed(3), "-i", c.path));
  let idx = o.clips.length;
  const logoIdx = o.logoPath ? idx++ : -1;
  if (o.logoPath) args.push("-i", o.logoPath);
  const musicIdx = o.musicPath ? idx++ : -1;
  if (o.musicPath) args.push("-stream_loop", "-1", "-i", o.musicPath);

  const concatInputs: string[] = [];
  o.clips.forEach((c, i) => {
    filters.push(
      `[${i}:v]scale=${OUT_W}:${OUT_H}:force_original_aspect_ratio=increase,crop=${OUT_W}:${OUT_H},setsar=1,fps=${FPS},format=yuv420p[v${i}]`,
    );
    const d = (c.end - c.start).toFixed(3);
    filters.push(
      c.hasAudio
        ? `[${i}:a]aresample=48000,aformat=sample_fmts=fltp:channel_layouts=stereo,apad=whole_dur=${d}[a${i}]`
        : `anullsrc=r=48000:cl=stereo,atrim=duration=${d},aformat=sample_fmts=fltp[a${i}]`,
    );
    concatInputs.push(`[v${i}][a${i}]`);
  });
  filters.push(`${concatInputs.join("")}concat=n=${o.clips.length}:v=1:a=1[vc][ac]`);

  let vLabel = "vc";
  if (o.assPath) {
    filters.push(`[${vLabel}]subtitles=filename=${escapeFilterPath(o.assPath)}:fontsdir=${escapeFilterPath(o.fontDir)}[vs]`);
    vLabel = "vs";
  }
  if (logoIdx >= 0) {
    filters.push(`[${logoIdx}:v]scale=180:-1[lg]`, `[${vLabel}][lg]overlay=W-w-48:72[vl]`);
    vLabel = "vl";
  }
  let aLabel = "ac";
  if (musicIdx >= 0) {
    filters.push(
      `[${musicIdx}:a]aresample=48000,aformat=sample_fmts=fltp:channel_layouts=stereo,volume=${o.musicVolume}[mu]`,
      `[${aLabel}][mu]amix=inputs=2:duration=first:dropout_transition=0:normalize=0[am]`,
    );
    aLabel = "am";
  }
  filters.push(`[${aLabel}]loudnorm=I=-14:TP=-1.5:LRA=11[ao]`);

  args.push(
    "-filter_complex",
    filters.join(";"),
    "-map",
    `[${vLabel}]`,
    "-map",
    "[ao]",
    "-t",
    o.durationSec.toFixed(3),
    "-c:v",
    "libx264",
    "-preset",
    "medium",
    "-crf",
    "20",
    "-profile:v",
    "high",
    "-pix_fmt",
    "yuv420p",
    "-r",
    String(FPS),
    "-c:a",
    "aac",
    "-b:a",
    "160k",
    "-ar",
    "48000",
    "-movflags",
    "+faststart",
    o.outPath,
  );
  return args;
}

/** Escapes a path for use inside an ffmpeg filtergraph option value. */
export function escapeFilterPath(p: string): string {
  return p.replace(/\\/g, "/").replace(/([:'\[\],;])/g, "\\$1");
}

export class RightsError extends Error {
  constructor(files: string[]) {
    super(`Nutzungsrechte ungeklärt für: ${files.join(", ")}. Bitte in der Medienbibliothek bestätigen.`);
    this.name = "RightsError";
  }
}

/** Downloads (S3) or resolves (local) all keys, then runs fn with local paths. */
async function withLocalFiles<T>(keys: string[], fn: (paths: Map<string, string>) => Promise<T>, acc = new Map<string, string>()): Promise<T> {
  const [head, ...rest] = keys;
  if (head === undefined) return fn(acc);
  if (acc.has(head)) return withLocalFiles(rest, fn, acc);
  return storage().withLocalFile(head, (p) => withLocalFiles(rest, fn, new Map(acc).set(head, p)));
}

export async function renderReel(renderId: string, log: (line: string) => void = () => undefined) {
  const [render] = await db().select().from(schema.renders).where(eq(schema.renders.id, renderId));
  if (!render) throw new Error("Render nicht gefunden");
  const input = ReelRenderInput.parse(render.input);
  const version = render.versionId
    ? (await db().select().from(schema.contentVersions).where(eq(schema.contentVersions.id, render.versionId)))[0]
    : null;
  const body = (version?.body ?? {}) as Partial<ReelBody>;
  const brand = await getBrand();

  const assetIds = [
    ...input.clips.map((c) => c.assetId),
    ...(input.logoAssetId ? [input.logoAssetId] : []),
    ...(input.musicAssetId ? [input.musicAssetId] : []),
    ...(input.subtitles.mode === "asset" && input.subtitles.assetId ? [input.subtitles.assetId] : []),
  ];
  const assets = await db().select().from(schema.mediaAssets).where(inArray(schema.mediaAssets.id, assetIds));
  const byId = new Map(assets.map((a) => [a.id, a]));
  const missing = assetIds.filter((id) => !byId.has(id));
  if (missing.length) throw new Error(`Assets fehlen: ${missing.join(", ")}`);
  const unknownRights = assets.filter((a) => a.rightsStatus === "unknown" && a.kind !== "subtitle");
  if (unknownRights.length) throw new RightsError(unknownRights.map((a) => a.filename));

  return withLocalFiles([...new Set(assets.map((a) => a.storageKey))], async (paths) => {
    const work = await mkdtemp(path.join(tmpdir(), "ce-reel-"));
    try {
      const clips: ClipSource[] = [];
      for (const c of input.clips) {
        const asset = byId.get(c.assetId)!;
        if (asset.kind !== "video") throw new Error(`${asset.filename} ist kein Video.`);
        const p = paths.get(asset.storageKey)!;
        const info = await probe(p);
        const dur = info.durationSec ?? 0;
        const start = Math.min(c.start ?? 0, Math.max(0, dur - 0.5));
        const end = Math.min(c.end ?? dur, dur);
        if (end - start < 0.5) throw new Error(`Clip ${asset.filename}: Ausschnitt zu kurz.`);
        clips.push({ path: p, start, end, hasAudio: info.hasAudio });
      }
      const fullDuration = clips.reduce((a, c) => a + (c.end - c.start), 0);

      let baseCues: Cue[] = [];
      if (input.subtitles.mode === "script") {
        baseCues = cuesFromScript(reelSpokenSegments(body), fullDuration);
        log(`Untertitel aus Skript: ${baseCues.length} Cues (Timing geschätzt)`);
      } else if (input.subtitles.mode === "asset" && input.subtitles.assetId) {
        const sub = byId.get(input.subtitles.assetId)!;
        baseCues = parseSrt(await readFile(paths.get(sub.storageKey)!, "utf8"));
        log(`Untertitel aus Datei ${sub.filename}: ${baseCues.length} Cues`);
      } else if (input.subtitles.mode === "transcribe") {
        if (clips.length !== 1) throw new Error("Automatische Transkription unterstützt aktuell genau einen Clip.");
        baseCues = (await transcribe(clips[0].path, brand.settings.language)).map((c) => ({
          start: c.start - clips[0].start,
          end: c.end - clips[0].start,
          text: c.text,
        }));
        log(`Transkription: ${baseCues.length} Cues`);
      }

      const outputs: string[] = [];
      for (const variant of input.variants) {
        const duration = Math.min(fullDuration, variant.maxDurationSec ?? fullDuration);
        const cues = baseCues.filter((c) => c.start < duration).map((c) => ({ ...c, end: Math.min(c.end, duration) }));
        const hookText = input.hookText ?? body.onScreenHook ?? "";
        const ctaText = input.ctaText ?? "";
        const ass = buildAss({
          width: OUT_W,
          height: OUT_H,
          cues,
          hook: hookText ? { text: hookText, durationSec: Math.min(input.hookDurationSec, duration) } : null,
          cta: ctaText ? { text: ctaText, start: Math.max(0, duration - input.ctaDurationSec), end: duration } : null,
          colors: brand.settings.colors,
        });
        const hasOverlay = cues.length > 0 || !!hookText || !!ctaText;
        const assPath = path.join(work, `${variant.name}.ass`);
        if (hasOverlay) await writeFile(assPath, ass, "utf8");
        const outPath = path.join(work, `${variant.name}.mp4`);
        const args = buildReelArgs({
          clips,
          assPath: hasOverlay ? assPath : null,
          fontDir: FONT_DIR,
          logoPath: input.logoAssetId ? paths.get(byId.get(input.logoAssetId)!.storageKey)! : null,
          musicPath: input.musicAssetId ? paths.get(byId.get(input.musicAssetId)!.storageKey)! : null,
          musicVolume: input.musicVolume,
          durationSec: duration,
          outPath,
        });
        log(`Rendere Variante "${variant.name}" (${duration.toFixed(1)}s)`);
        await ffmpeg(args);
        const thumbPath = path.join(work, `${variant.name}.jpg`);
        await ffmpeg(["-ss", Math.min(1, duration / 2).toFixed(2), "-i", outPath, "-frames:v", "1", "-q:v", "3", thumbPath]);

        const video = await registerGeneratedFile(outPath, {
          kind: "render",
          filename: `reel-${variant.name}.mp4`,
          mimeType: "video/mp4",
          itemId: render.itemId,
          renderId,
          ext: ".mp4",
        });
        const thumb = await registerGeneratedFile(thumbPath, {
          kind: "render",
          filename: `reel-${variant.name}-thumb.jpg`,
          mimeType: "image/jpeg",
          itemId: render.itemId,
          renderId,
          ext: ".jpg",
        });
        outputs.push(video.id, thumb.id);
      }
      return outputs;
    } finally {
      await rm(work, { recursive: true, force: true });
    }
  });
}
