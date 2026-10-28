import { beforeAll, describe, expect, it } from "vitest";
import { eq } from "drizzle-orm";
import { db, schema } from "@/server/db";
import { InstagramClient, waitForContainer } from "@/server/integrations/instagram/client";
import { connectInstagram, instagramIntegration, publishItem, PublishBlockedError } from "@/server/integrations/instagram/service";
import { decryptSecret } from "@/server/crypto";
import { makeUser, resetDb } from "../helpers";

/**
 * Contract tests against recorded response shapes of the Instagram Platform API.
 * They verify request construction and error handling; they do NOT prove a live
 * connection (see docs/BLOCKERS.md).
 */
type Call = { method: string; url: URL; body: URLSearchParams | null };

function fakeGraph(routes: (c: Call) => { status?: number; json: unknown }) {
  const calls: Call[] = [];
  const f = (async (input: URL | string, init?: RequestInit) => {
    const c: Call = { method: init?.method ?? "GET", url: new URL(String(input)), body: init?.body instanceof URLSearchParams ? init.body : null };
    calls.push(c);
    const r = routes(c);
    return new Response(JSON.stringify(r.json), { status: r.status ?? 200 });
  }) as unknown as typeof fetch;
  return { f, calls };
}

beforeAll(async () => {
  await resetDb();
});

describe("Instagram client", () => {
  it("runs the documented reel container → status → publish flow", async () => {
    let polls = 0;
    const { f, calls } = fakeGraph((c) => {
      if (c.method === "POST" && c.url.pathname.endsWith("/123/media")) return { json: { id: "c1" } };
      if (c.url.pathname.endsWith("/c1")) return { json: { status_code: ++polls < 2 ? "IN_PROGRESS" : "FINISHED" } };
      if (c.url.pathname.endsWith("/123/media_publish")) return { json: { id: "m1" } };
      return { status: 404, json: { error: { message: "unknown", code: 100 } } };
    });
    const client = new InstagramClient({ host: "https://graph.instagram.com", version: "v23.0", accessToken: "tok", userId: "123" }, f);
    const { id } = await client.createReelContainer("https://cdn/x.mp4", "Caption");
    await waitForContainer(client, id, { sleep: async () => undefined });
    const pub = await client.publish(id);
    expect(pub.id).toBe("m1");
    const create = calls[0];
    expect(create.url.pathname).toBe("/v23.0/123/media");
    expect(create.body?.get("media_type")).toBe("REELS");
    expect(create.body?.get("video_url")).toBe("https://cdn/x.mp4");
    expect(calls.at(-1)!.body?.get("creation_id")).toBe("c1");
  });

  it("surfaces container errors and drops unsupported insight metrics individually", async () => {
    const { f } = fakeGraph((c) => {
      if (c.url.pathname.endsWith("/bad")) return { json: { status_code: "ERROR", status: "Video too long" } };
      const metric = c.url.searchParams.get("metric") ?? "";
      if (metric.includes(",")) return { status: 400, json: { error: { message: "metric invalid", code: 100 } } };
      if (metric === "impressions") return { status: 400, json: { error: { message: "deprecated", code: 100 } } };
      return { json: { data: [{ name: metric, values: [{ value: 7 }] }] } };
    });
    const client = new InstagramClient({ host: "https://graph.instagram.com", version: "v23.0", accessToken: "t", userId: "1" }, f);
    await expect(waitForContainer(client, "bad", { sleep: async () => undefined })).rejects.toThrow(/Video too long/);
    expect(await client.insights("m1", ["views", "impressions", "saved"])).toEqual({ views: 7, saved: 7 });
  });
});

describe("Instagram service", () => {
  it("verifies the token and stores it encrypted", async () => {
    const admin = await makeUser("admin");
    const { f } = fakeGraph(() => ({ json: { user_id: "17841", username: "brand", account_type: "BUSINESS" } }));
    await connectInstagram({ id: admin.id, label: admin.label }, "secret-token", f);
    const row = await instagramIntegration();
    expect(row?.status).toBe("connected");
    expect(row?.secretEnc).not.toContain("secret-token");
    expect(decryptSecret(row!.secretEnc!)).toBe("secret-token");
  });

  it("refuses to publish when API publishing is disabled or content is not scheduled", async () => {
    const [item] = await db().insert(schema.contentItems).values({ format: "reel", pillar: "education", audience: "both", title: "x", status: "approved" }).returning();
    await expect(publishItem(item.id)).rejects.toBeInstanceOf(PublishBlockedError);
    await db().update(schema.contentItems).set({ status: "scheduled", scheduledAt: new Date(Date.now() - 1000) }).where(eq(schema.contentItems.id, item.id));
    await expect(publishItem(item.id)).rejects.toThrow(/deaktiviert/);
  });
});
