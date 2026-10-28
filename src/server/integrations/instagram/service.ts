import { and, desc, eq, isNotNull } from "drizzle-orm";
import { db, schema } from "@/server/db";
import { env } from "@/server/env";
import { decryptSecret, encryptSecret } from "@/server/crypto";
import { audit, SYSTEM_ACTOR, type Actor } from "@/server/audit";
import { storage } from "@/server/media/storage";
import { assertCurrentVersionApproved } from "@/server/workflow/content";
import { assertTransition } from "@/server/workflow/state";
import { emitEvent } from "@/server/integrations/crm/webhooks";
import { FEED_METRICS, InstagramApiError, InstagramClient, REEL_METRICS, waitForContainer } from "./client";

/** Thrown when publishing cannot run for a configuration reason (not retryable). */
export class PublishBlockedError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "PublishBlockedError";
  }
}

export async function instagramIntegration() {
  const [row] = await db().select().from(schema.integrations).where(eq(schema.integrations.provider, "instagram"));
  return row ?? null;
}

export async function instagramClient(fetchImpl?: typeof fetch): Promise<InstagramClient | null> {
  const row = await instagramIntegration();
  if (!row || row.status !== "connected" || !row.secretEnc) return null;
  const e = env();
  return new InstagramClient(
    { host: e.INSTAGRAM_GRAPH_HOST, version: e.INSTAGRAM_API_VERSION, accessToken: decryptSecret(row.secretEnc), userId: String(row.config.userId) },
    fetchImpl,
  );
}

/**
 * Stores a long-lived Instagram User access token (generated in the Meta App
 * dashboard for a Business/Creator account). The token is verified against the
 * API before saving and stored AES-GCM encrypted.
 */
export async function connectInstagram(actor: Actor, accessToken: string, fetchImpl?: typeof fetch) {
  const e = env();
  const probe = new InstagramClient({ host: e.INSTAGRAM_GRAPH_HOST, version: e.INSTAGRAM_API_VERSION, accessToken, userId: "me" }, fetchImpl);
  const me = await probe.me();
  const userId = me.user_id ?? me.id;
  if (!userId) throw new Error("Instagram-Konto-ID konnte nicht ermittelt werden.");
  const values = {
    provider: "instagram" as const,
    status: "connected" as const,
    config: { userId, username: me.username, accountType: me.account_type ?? null, connectedAt: new Date().toISOString() },
    secretEnc: encryptSecret(accessToken),
    lastError: null,
    updatedAt: new Date(),
  };
  await db().insert(schema.integrations).values(values).onConflictDoUpdate({ target: schema.integrations.provider, set: values });
  await audit(actor, "integration.connected", "integration", "instagram", { username: me.username });
  return me;
}

export async function disconnectInstagram(actor: Actor) {
  await db()
    .update(schema.integrations)
    .set({ status: "not_connected", secretEnc: null, updatedAt: new Date() })
    .where(eq(schema.integrations.provider, "instagram"));
  await audit(actor, "integration.disconnected", "integration", "instagram");
}

async function latestRenderAssets(itemId: string, versionId: string) {
  const renders = await db()
    .select()
    .from(schema.renders)
    .where(and(eq(schema.renders.itemId, itemId), eq(schema.renders.versionId, versionId), eq(schema.renders.status, "succeeded")))
    .orderBy(desc(schema.renders.createdAt));
  return renders[0] ?? null;
}

/**
 * Publishes an approved, scheduled item. Preconditions are re-checked at run
 * time (approval bound to current version, schedule time reached, quota).
 */
export async function publishItem(itemId: string, opts: { fetchImpl?: typeof fetch; sleep?: (ms: number) => Promise<void> } = {}) {
  const [item] = await db().select().from(schema.contentItems).where(eq(schema.contentItems.id, itemId));
  if (!item) throw new PublishBlockedError("Inhalt nicht gefunden");
  if (item.status === "published") return { skipped: "already_published" };
  if (item.status !== "scheduled") throw new PublishBlockedError(`Status ist "${item.status}", nicht "scheduled".`);
  if (item.scheduledAt && item.scheduledAt.getTime() > Date.now() + 60_000) {
    return { skipped: "not_due", runAt: item.scheduledAt };
  }
  if (!env().INSTAGRAM_PUBLISHING_ENABLED) throw new PublishBlockedError("API-Publishing ist deaktiviert (INSTAGRAM_PUBLISHING_ENABLED=false).");
  await assertCurrentVersionApproved(itemId);
  if (item.format === "story") {
    throw new PublishBlockedError("Stories mit interaktiven Stickern werden manuell veröffentlicht (API unterstützt keine Sticker).");
  }
  if (storage().driver !== "s3") {
    throw new PublishBlockedError("Instagram lädt Medien per öffentlicher URL. Dafür ist STORAGE_DRIVER=s3 mit öffentlich erreichbarem Endpoint nötig.");
  }
  const client = await instagramClient(opts.fetchImpl);
  if (!client) throw new PublishBlockedError("Instagram ist nicht verbunden.");

  const limit = await client.publishingLimit().catch(() => null);
  const quota = limit?.data?.[0];
  if (quota?.config && quota.quota_usage >= quota.config.quota_total) {
    throw new InstagramApiError("Tageslimit für API-Veröffentlichungen erreicht", 429, 4);
  }

  const [version] = await db().select().from(schema.contentVersions).where(eq(schema.contentVersions.id, item.currentVersionId!));
  const render = await latestRenderAssets(itemId, version.id);
  if (!render) throw new PublishBlockedError("Kein fertiges Rendering für die freigegebene Version vorhanden.");
  const assets = await Promise.all(
    render.outputAssetIds.map(async (id) => (await db().select().from(schema.mediaAssets).where(eq(schema.mediaAssets.id, id)))[0]),
  );

  assertTransition("scheduled", "publishing");
  await db().update(schema.contentItems).set({ status: "publishing", updatedAt: new Date() }).where(eq(schema.contentItems.id, itemId));
  try {
    let containerId: string;
    if (item.format === "reel") {
      const video = assets.find((a) => a?.mimeType === "video/mp4");
      const cover = assets.find((a) => a?.mimeType === "image/jpeg");
      if (!video) throw new PublishBlockedError("Rendering enthält kein Video.");
      const videoUrl = await storage().signedUrl(video.storageKey, 3600);
      const coverUrl = cover ? await storage().signedUrl(cover.storageKey, 3600) : undefined;
      containerId = (await client.createReelContainer(videoUrl!, version.caption, { coverUrl: coverUrl ?? undefined })).id;
    } else {
      const slides = assets.filter((a) => a?.kind === "slide").slice(0, 10);
      if (slides.length < 2) throw new PublishBlockedError("Carousel benötigt mindestens 2 gerenderte Slides.");
      const children: string[] = [];
      for (const s of slides) children.push((await client.createCarouselItem((await storage().signedUrl(s.storageKey, 3600))!)).id);
      containerId = (await client.createCarouselContainer(children, version.caption)).id;
    }
    await db().update(schema.contentItems).set({ igContainerId: containerId }).where(eq(schema.contentItems.id, itemId));
    await waitForContainer(client, containerId, { sleep: opts.sleep });
    const published = await client.publish(containerId);
    const media = await client.media(published.id).catch(() => null);
    await db()
      .update(schema.contentItems)
      .set({ status: "published", igMediaId: published.id, igPermalink: media?.permalink ?? null, publishedAt: new Date(), lastError: null, updatedAt: new Date() })
      .where(eq(schema.contentItems.id, itemId));
    await audit(SYSTEM_ACTOR, "content.published_api", "content_item", itemId, { mediaId: published.id });
    await emitEvent("content.published", { itemId, permalink: media?.permalink ?? null, method: "api" });
    return { mediaId: published.id };
  } catch (err) {
    await db()
      .update(schema.contentItems)
      .set({ status: "failed", lastError: (err as Error).message, updatedAt: new Date() })
      .where(eq(schema.contentItems.id, itemId));
    await audit(SYSTEM_ACTOR, "content.publish_failed", "content_item", itemId, { error: (err as Error).message });
    throw err;
  }
}

/** Pulls insights for API-published items into post_metrics. */
export async function syncInsights(fetchImpl?: typeof fetch) {
  const client = await instagramClient(fetchImpl);
  if (!client) return { synced: 0, reason: "not_connected" };
  const items = await db()
    .select()
    .from(schema.contentItems)
    .where(and(eq(schema.contentItems.status, "published"), isNotNull(schema.contentItems.igMediaId)));
  let synced = 0;
  for (const item of items) {
    const values = await client.insights(item.igMediaId!, item.format === "reel" ? REEL_METRICS : FEED_METRICS);
    await db().insert(schema.postMetrics).values({
      itemId: item.id,
      source: "instagram_api",
      views: values.views ?? null,
      reach: values.reach ?? null,
      likes: values.likes ?? null,
      comments: values.comments ?? null,
      saves: values.saved ?? null,
      shares: values.shares ?? null,
      profileVisits: values.profile_visits ?? null,
      follows: values.follows ?? null,
      // ig_reels_avg_watch_time is reported in milliseconds.
      avgWatchTimeSec: values.ig_reels_avg_watch_time !== undefined ? values.ig_reels_avg_watch_time / 1000 : null,
      raw: values,
    });
    synced++;
  }
  return { synced };
}
