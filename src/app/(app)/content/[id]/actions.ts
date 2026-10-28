"use server";

import { eq } from "drizzle-orm";
import { action, optNum, str } from "@/server/actions";
import { db, schema } from "@/server/db";
import { enqueue } from "@/server/jobs/queue";
import {
  createVersion,
  decide,
  getItem,
  markPublished,
  schedule,
  submitForReview,
  unschedule,
  updateItemMeta,
  withdrawFromReview,
  type Decision,
} from "@/server/workflow/content";
import { carouselFromForm, reelFromForm, storyFromForm } from "@/server/workflow/forms";
import { requestRender } from "@/server/media/render-jobs";
import { recordManualMetrics } from "@/server/analytics/metrics";
import { zonedToUtc } from "@/lib/time";
import { AUDIENCES, PILLARS, type Audience, type Pillar } from "@/lib/content-types";

const back = (fd: FormData) => `/content/${str(fd, "itemId")}`;

export async function saveContent(fd: FormData) {
  await action(back(fd), "content.edit", async ({ principal }) => {
    const item = await getItem(str(fd, "itemId"));
    const prev = item.currentVersionId
      ? ((await db().select().from(schema.contentVersions).where(eq(schema.contentVersions.id, item.currentVersionId)))[0]?.body ?? {})
      : {};
    let body: Record<string, unknown>;
    if (str(fd, "mode") === "json") {
      try {
        body = JSON.parse(str(fd, "json"));
      } catch {
        throw new Error("JSON ist ungültig.");
      }
      if (!body || typeof body !== "object" || Array.isArray(body)) throw new Error("JSON muss ein Objekt sein.");
    } else if (item.format === "reel") body = reelFromForm(fd, prev);
    else if (item.format === "carousel") body = carouselFromForm(fd, prev);
    else body = storyFromForm(fd, prev);
    const v = await createVersion(principal, item.id, { body, caption: str(fd, "caption"), source: "human" });
    return `Version ${v.version} gespeichert${v.compliance?.blocking ? " – blockierende Compliance-Befunde prüfen" : ""}.`;
  });
}

export async function saveMeta(fd: FormData) {
  await action(back(fd), "content.edit", async ({ principal }) => {
    const pillar = str(fd, "pillar");
    const audience = str(fd, "audience");
    await updateItemMeta(principal, str(fd, "itemId"), {
      title: str(fd, "title"),
      brief: str(fd, "brief"),
      pillar: (PILLARS as readonly string[]).includes(pillar) ? (pillar as Pillar) : undefined,
      audience: (AUDIENCES as readonly string[]).includes(audience) ? (audience as Audience) : undefined,
      scheduledAt: str(fd, "date") ? zonedToUtc(str(fd, "date"), str(fd, "time") || "18:00") : null,
    });
    return "Metadaten gespeichert.";
  });
}

export async function regenerate(fd: FormData) {
  await action(back(fd), "content.generate", async ({ user }) => {
    await enqueue("item.draft", { itemId: str(fd, "itemId"), feedback: str(fd, "feedback") || undefined }, { createdBy: user.id, maxAttempts: 2 });
    return "Neuer KI-Entwurf wird erstellt.";
  });
}

export async function submit(fd: FormData) {
  await action(back(fd), "content.edit", async ({ principal }) => {
    await submitForReview(principal, str(fd, "itemId"));
    return "Zur Freigabe eingereicht.";
  });
}

export async function withdraw(fd: FormData) {
  await action(back(fd), "content.edit", async ({ principal }) => {
    await withdrawFromReview(principal, str(fd, "itemId"));
    return "Aus der Prüfung zurückgezogen.";
  });
}

export async function review(fd: FormData) {
  await action(back(fd), "content.approve", async ({ principal }) => {
    const decision = str(fd, "decision") as Decision;
    if (!["approved", "changes_requested", "rejected"].includes(decision)) throw new Error("Ungültige Entscheidung");
    await decide(principal, str(fd, "itemId"), decision, str(fd, "comment"), fd.get("complianceAck") === "on");
    return { approved: "Freigegeben und dokumentiert.", changes_requested: "Änderungen angefragt.", rejected: "Abgelehnt." }[decision];
  });
}

export async function scheduleItem(fd: FormData) {
  await action(back(fd), "content.schedule", async ({ principal }) => {
    const date = str(fd, "date");
    if (!date) throw new Error("Datum fehlt.");
    const res = await schedule(principal, str(fd, "itemId"), zonedToUtc(date, str(fd, "time") || "18:00"));
    return res.autoPublish ? "Eingeplant – wird automatisch über die Instagram-API veröffentlicht." : "Eingeplant – Veröffentlichung als manueller Schritt.";
  });
}

export async function unscheduleItem(fd: FormData) {
  await action(back(fd), "content.schedule", async ({ principal }) => {
    await unschedule(principal, str(fd, "itemId"));
    return "Einplanung entfernt.";
  });
}

export async function publishedManually(fd: FormData) {
  await action(back(fd), "content.schedule", async ({ principal }) => {
    const permalink = str(fd, "permalink");
    if (permalink && !/^https:\/\/(www\.)?instagram\.com\//.test(permalink)) throw new Error("Bitte einen Instagram-Link angeben.");
    await markPublished(principal, str(fd, "itemId"), permalink);
    return "Als veröffentlicht dokumentiert.";
  });
}

export async function renderItem(fd: FormData) {
  await action(back(fd), "media.write", async ({ actor }) => {
    const itemId = str(fd, "itemId");
    const item = await getItem(itemId);
    if (item.format !== "reel") {
      await requestRender(actor, itemId);
      return "Rendering gestartet.";
    }
    const clips = fd
      .getAll("clip")
      .map(String)
      .map((assetId) => ({
        assetId,
        order: optNum(fd, `order_${assetId}`) ?? 99,
        start: optNum(fd, `start_${assetId}`),
        end: optNum(fd, `end_${assetId}`),
      }))
      .sort((a, b) => a.order - b.order)
      .map(({ order: _o, ...c }) => c);
    if (!clips.length) throw new Error("Mindestens einen Clip auswählen.");
    const variants = [{ name: "main" }];
    const shortLen = optNum(fd, "shortLen");
    if (shortLen) variants.push({ name: `kurz-${shortLen}s`, maxDurationSec: shortLen } as { name: string; maxDurationSec?: number });
    await requestRender(actor, itemId, {
      clips,
      subtitles: { mode: str(fd, "subMode") || "script", assetId: str(fd, "subAsset") || undefined },
      hookText: str(fd, "hookText") || undefined,
      ctaText: str(fd, "ctaText") || undefined,
      logoAssetId: str(fd, "logo") || null,
      musicAssetId: str(fd, "music") || null,
      variants,
    });
    return "Reel-Rendering gestartet.";
  });
}

export async function addMetrics(fd: FormData) {
  await action(back(fd), "analytics.write", async ({ actor }) => {
    await recordManualMetrics(actor, str(fd, "itemId"), {
      views: optNum(fd, "views"),
      reach: optNum(fd, "reach"),
      likes: optNum(fd, "likes"),
      comments: optNum(fd, "comments"),
      saves: optNum(fd, "saves"),
      shares: optNum(fd, "shares"),
      profileVisits: optNum(fd, "profileVisits"),
      follows: optNum(fd, "follows"),
      avgWatchTimeSec: optNum(fd, "avgWatchTimeSec"),
      dmInquiries: optNum(fd, "dmInquiries"),
    });
    return "Messwerte gespeichert.";
  });
}
