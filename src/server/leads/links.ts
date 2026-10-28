import { randomBytes } from "node:crypto";
import { and, eq } from "drizzle-orm";
import { db, schema } from "@/server/db";
import { env } from "@/server/env";

/**
 * Tracking links are the attribution backbone: every link in bio, story link
 * sticker or caption points to /r/<code>, which logs an anonymous click and
 * forwards to the application form with the code attached. Leads submitted via
 * that form are attributed to the link (and thus the content item).
 */

export type Destination = "coaching" | "partner" | string;
export type Placement = "bio" | "story_link" | "caption" | "dm_manual" | "other";

export function newCode(): string {
  // 7 chars, unambiguous alphabet.
  const alphabet = "abcdefghjkmnpqrstuvwxyz23456789";
  const bytes = randomBytes(7);
  return [...bytes].map((b) => alphabet[b % alphabet.length]).join("");
}

export function linkUrl(code: string): string {
  return `${env().APP_URL.replace(/\/$/, "")}/r/${code}`;
}

export async function createLink(input: { label: string; destination: Destination; placement: Placement; itemId?: string | null }) {
  const [link] = await db()
    .insert(schema.trackingLinks)
    .values({ code: newCode(), label: input.label, destination: input.destination, placement: input.placement, itemId: input.itemId ?? null })
    .returning();
  return link;
}

export async function ensureItemLink(itemId: string, destination: "coaching" | "partner", placement: Placement, label: string) {
  const [existing] = await db()
    .select()
    .from(schema.trackingLinks)
    .where(and(eq(schema.trackingLinks.itemId, itemId), eq(schema.trackingLinks.destination, destination)))
    .limit(1);
  const link = existing ?? (await createLink({ label, destination, placement, itemId }));
  await db().update(schema.contentItems).set({ trackingLinkId: link.id }).where(eq(schema.contentItems.id, itemId));
  return { ...link, url: linkUrl(link.code) };
}

export function destinationForCta(cta: string): "coaching" | "partner" | null {
  if (cta === "coaching_application") return "coaching";
  if (cta === "partner_inquiry") return "partner";
  return null;
}

/** Where /r/<code> forwards to. Internal forms receive the code as `src`. */
export function resolveDestination(link: { destination: string; code: string }): string {
  if (link.destination === "coaching" || link.destination === "partner") {
    return `/apply/${link.destination}?src=${encodeURIComponent(link.code)}`;
  }
  const url = new URL(link.destination);
  url.searchParams.set("utm_source", "instagram");
  url.searchParams.set("utm_medium", "social");
  url.searchParams.set("utm_content", link.code);
  return url.toString();
}

export function deviceClass(userAgent: string | null): string {
  if (!userAgent) return "unknown";
  if (/Instagram/i.test(userAgent)) return "instagram_inapp";
  if (/Mobi|Android|iPhone/i.test(userAgent)) return "mobile";
  return "desktop";
}
