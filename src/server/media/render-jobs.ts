import { mkdtemp, rm, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import path from "node:path";
import { eq } from "drizzle-orm";
import { db, schema } from "@/server/db";
import { getBrand } from "@/server/brand";
import { audit, type Actor } from "@/server/audit";
import { enqueue } from "@/server/jobs/queue";
import { renderCarouselSlides, renderStoryFrames } from "@/server/carousel/render";
import type { CarouselBody, StorySet } from "@/lib/content-types";
import { registerGeneratedFile } from "./assets";
import { ReelRenderInput, renderReel } from "./reel-render";

export async function requestRender(actor: Actor, itemId: string, input: Record<string, unknown> = {}) {
  const [item] = await db().select().from(schema.contentItems).where(eq(schema.contentItems.id, itemId));
  if (!item) throw new Error("Inhalt nicht gefunden");
  if (!item.currentVersionId) throw new Error("Erst einen Entwurf erstellen.");
  const kind = item.format;
  const parsedInput = kind === "reel" ? ReelRenderInput.parse(input) : {};
  const [render] = await db()
    .insert(schema.renders)
    .values({ itemId, versionId: item.currentVersionId, kind, input: parsedInput, status: "queued" })
    .returning();
  await enqueue(kind === "reel" ? "render.reel" : "render.carousel", { renderId: render.id }, { createdBy: actor.id, maxAttempts: 1 });
  await audit(actor, "render.requested", "content_item", itemId, { renderId: render.id, kind });
  return render;
}

async function appendLog(renderId: string, line: string) {
  const [r] = await db().select({ log: schema.renders.log }).from(schema.renders).where(eq(schema.renders.id, renderId));
  await db().update(schema.renders).set({ log: `${r?.log ?? ""}${new Date().toISOString()} ${line}\n` }).where(eq(schema.renders.id, renderId));
}

/** Executes a render (called by the worker). Status + log are written to the render row. */
export async function executeRender(renderId: string) {
  await db().update(schema.renders).set({ status: "running" }).where(eq(schema.renders.id, renderId));
  const [render] = await db().select().from(schema.renders).where(eq(schema.renders.id, renderId));
  try {
    let outputs: string[];
    if (render.kind === "reel") {
      const lines: string[] = [];
      outputs = await renderReel(renderId, (l) => lines.push(l));
      for (const l of lines) await appendLog(renderId, l);
    } else {
      outputs = await renderImages(render);
    }
    await db().update(schema.renders).set({ status: "succeeded", outputAssetIds: outputs, finishedAt: new Date() }).where(eq(schema.renders.id, renderId));
    await appendLog(renderId, `Fertig: ${outputs.length} Dateien`);
    return outputs;
  } catch (err) {
    await db()
      .update(schema.renders)
      .set({ status: "failed", error: (err as Error).message, finishedAt: new Date() })
      .where(eq(schema.renders.id, renderId));
    throw err;
  }
}

async function renderImages(render: typeof schema.renders.$inferSelect) {
  if (!render.versionId) throw new Error("Keine Version");
  const [version] = await db().select().from(schema.contentVersions).where(eq(schema.contentVersions.id, render.versionId));
  const brand = await getBrand();
  const pngs =
    render.kind === "carousel"
      ? await renderCarouselSlides(version.body as unknown as CarouselBody, brand.settings)
      : await renderStoryFrames(version.body as unknown as StorySet, brand.settings);
  const dir = await mkdtemp(path.join(tmpdir(), "ce-slides-"));
  try {
    const ids: string[] = [];
    for (let i = 0; i < pngs.length; i++) {
      const file = path.join(dir, `${i + 1}.png`);
      await writeFile(file, pngs[i]);
      const asset = await registerGeneratedFile(file, {
        kind: "slide",
        filename: `${render.kind}-v${version.version}-${String(i + 1).padStart(2, "0")}.png`,
        mimeType: "image/png",
        itemId: render.itemId,
        renderId: render.id,
        ext: ".png",
      });
      ids.push(asset.id);
    }
    return ids;
  } finally {
    await rm(dir, { recursive: true, force: true });
  }
}
