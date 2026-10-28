import { randomUUID } from "node:crypto";
import path from "node:path";
import type { Readable } from "node:stream";
import { eq } from "drizzle-orm";
import { db, schema } from "@/server/db";
import { audit, type Actor } from "@/server/audit";
import { probe } from "./ffmpeg";
import { storage, storageKey } from "./storage";

export type AssetKind = (typeof schema.assetKindEnum.enumValues)[number];
export type RightsStatus = "own" | "licensed" | "unknown";

const ALLOWED: Record<string, { kind: AssetKind; ext: string }> = {
  "video/mp4": { kind: "video", ext: ".mp4" },
  "video/quicktime": { kind: "video", ext: ".mov" },
  "video/webm": { kind: "video", ext: ".webm" },
  "image/jpeg": { kind: "image", ext: ".jpg" },
  "image/png": { kind: "image", ext: ".png" },
  "image/webp": { kind: "image", ext: ".webp" },
  "audio/mpeg": { kind: "audio", ext: ".mp3" },
  "audio/wav": { kind: "audio", ext: ".wav" },
  "audio/x-wav": { kind: "audio", ext: ".wav" },
  "audio/mp4": { kind: "audio", ext: ".m4a" },
  "application/x-subrip": { kind: "subtitle", ext: ".srt" },
  "text/vtt": { kind: "subtitle", ext: ".vtt" },
};

export function classifyUpload(mimeType: string, filename: string): { kind: AssetKind; ext: string } | null {
  const byMime = ALLOWED[mimeType.split(";")[0].trim().toLowerCase()];
  if (byMime) return byMime;
  const ext = path.extname(filename).toLowerCase();
  if (ext === ".srt") return { kind: "subtitle", ext };
  if (ext === ".vtt") return { kind: "subtitle", ext };
  return null;
}

export const MIME_BY_EXT: Record<string, string> = Object.fromEntries(
  Object.entries(ALLOWED).map(([mime, { ext }]) => [ext, mime]),
);

export async function ingestUpload(
  actor: Actor,
  input: {
    filename: string;
    mimeType: string;
    body: Readable;
    rightsStatus: RightsStatus;
    rightsNote: string;
    tags: string[];
    kindOverride?: AssetKind;
  },
) {
  const cls = classifyUpload(input.mimeType, input.filename);
  if (!cls) throw new Error(`Dateityp nicht unterstützt: ${input.mimeType || path.extname(input.filename)}`);
  const id = randomUUID();
  const key = storageKey("uploads", id, cls.ext);
  const mimeType = MIME_BY_EXT[cls.ext] ?? input.mimeType;
  const size = await storage().putStream(key, input.body, mimeType);

  let meta: { durationSec: number | null; width: number | null; height: number | null } = { durationSec: null, width: null, height: null };
  if (cls.kind === "video" || cls.kind === "audio" || cls.kind === "image") {
    try {
      meta = await storage().withLocalFile(key, probe);
    } catch (err) {
      await storage().delete(key);
      throw new Error(`Datei konnte nicht gelesen werden (beschädigt?): ${(err as Error).message}`);
    }
  }

  const [asset] = await db()
    .insert(schema.mediaAssets)
    .values({
      id,
      kind: input.kindOverride ?? cls.kind,
      filename: input.filename.slice(0, 200),
      mimeType,
      sizeBytes: size,
      storageKey: key,
      durationSec: meta.durationSec,
      width: meta.width,
      height: meta.height,
      rightsStatus: input.rightsStatus,
      rightsNote: input.rightsNote,
      tags: input.tags,
      uploadedBy: actor.id,
    })
    .returning();
  await audit(actor, "media.uploaded", "media_asset", asset.id, { filename: asset.filename, rights: input.rightsStatus, size });
  return asset;
}

/** Registers a file produced by the system (render output, slides). */
export async function registerGeneratedFile(
  filePath: string,
  input: { kind: AssetKind; filename: string; mimeType: string; itemId: string; renderId?: string; ext: string },
) {
  const id = randomUUID();
  const key = storageKey("generated", id, input.ext);
  const size = await storage().putFile(key, filePath, input.mimeType);
  const meta = input.mimeType.startsWith("video/") || input.mimeType.startsWith("image/") ? await probe(filePath) : null;
  const [asset] = await db()
    .insert(schema.mediaAssets)
    .values({
      id,
      kind: input.kind,
      filename: input.filename,
      mimeType: input.mimeType,
      sizeBytes: size,
      storageKey: key,
      durationSec: meta?.durationSec ?? null,
      width: meta?.width ?? null,
      height: meta?.height ?? null,
      rightsStatus: "own",
      rightsNote: "Generiert aus Assets mit geprüften Rechten",
      itemId: input.itemId,
      renderId: input.renderId ?? null,
    })
    .returning();
  return asset;
}

export async function getAsset(id: string) {
  const [a] = await db().select().from(schema.mediaAssets).where(eq(schema.mediaAssets.id, id));
  return a ?? null;
}

export async function updateRights(actor: Actor, id: string, rightsStatus: RightsStatus, rightsNote: string) {
  await db().update(schema.mediaAssets).set({ rightsStatus, rightsNote }).where(eq(schema.mediaAssets.id, id));
  await audit(actor, "media.rights_updated", "media_asset", id, { rightsStatus, rightsNote });
}

export async function deleteAsset(actor: Actor, id: string) {
  const asset = await getAsset(id);
  if (!asset) return;
  await db().delete(schema.mediaAssets).where(eq(schema.mediaAssets.id, id));
  await storage().delete(asset.storageKey);
  await audit(actor, "media.deleted", "media_asset", id, { filename: asset.filename });
}
