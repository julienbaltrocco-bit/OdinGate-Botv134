import { beforeAll, describe, expect, it } from "vitest";
import { eq } from "drizzle-orm";
import { db, schema } from "@/server/db";
import { createLead } from "@/server/leads/leads";
import { createLink } from "@/server/leads/links";
import { createApiKey, revokeApiKey } from "@/server/integrations/crm/api-keys";
import { deliverWebhook, emitEvent, signPayload } from "@/server/integrations/crm/webhooks";
import { encryptSecret } from "@/server/crypto";
import { GET as listLeads } from "@/app/api/v1/leads/route";
import { PATCH as patchLead } from "@/app/api/v1/leads/[id]/route";
import { GET as trackingRedirect } from "@/app/r/[code]/route";
import { itemPerformance } from "@/server/analytics/metrics";
import { makeUser, resetDb } from "../helpers";

let itemId: string;
let code: string;

beforeAll(async () => {
  await resetDb();
  const [item] = await db()
    .insert(schema.contentItems)
    .values({ format: "reel", pillar: "conversion", audience: "coaching", title: "Conversion Reel", status: "published", publishedAt: new Date() })
    .returning();
  itemId = item.id;
  code = (await createLink({ label: "Bio", destination: "coaching", placement: "bio", itemId })).code;
});

describe("attribution", () => {
  it("tracking redirect logs an anonymous click and forwards with the code", async () => {
    const res = await trackingRedirect(new Request(`http://localhost/r/${code}`, { headers: { "user-agent": "Instagram 300 iPhone" } }), {
      params: Promise.resolve({ code }),
    });
    expect(res.status).toBe(302);
    expect(res.headers.get("location")).toBe(`http://localhost:3000/apply/coaching?src=${code}`);
    const clicks = await db().select().from(schema.linkClicks);
    expect(clicks).toHaveLength(1);
    expect(clicks[0].device).toBe("instagram_inapp");
  });

  it("form submissions via the link are attributed to the content item", async () => {
    const lead = await createLead({
      type: "coaching",
      name: "Anna",
      email: "anna@example.com",
      consent: true,
      src: code,
      salesExperience: "1to3",
      cryptoExperience: "active",
      hoursPerWeek: "5to15",
      budgetOk: true,
    });
    expect(lead.sourceItemId).toBe(itemId);
    expect(lead.score).toBe(80);
    expect(lead.consentText).toContain("willige ein");
    const perf = await itemPerformance(30);
    expect(perf.find((p) => p.itemId === itemId)).toMatchObject({ leads: 1, linkClicks: 1 });
  });
});

describe("CRM API v1", () => {
  it("requires a valid key with the right scope", async () => {
    const actor = await makeUser("admin");
    const { token, key } = await createApiKey(actor, "CRM", ["leads:read"]);
    expect((await listLeads(new Request("http://x/api/v1/leads"), {})).status).toBe(401);
    const ok = await listLeads(new Request("http://x/api/v1/leads", { headers: { authorization: `Bearer ${token}` } }), {});
    expect(ok.status).toBe(200);
    const body = (await ok.json()) as { data: { email: string }[] };
    expect(body.data[0].email).toBe("anna@example.com");

    const [lead] = await db().select().from(schema.leads);
    const forbidden = await patchLead(
      new Request("http://x", { method: "PATCH", headers: { authorization: `Bearer ${token}` }, body: JSON.stringify({ stage: "won" }) }),
      { params: Promise.resolve({ id: lead.id }) },
    );
    expect(forbidden.status).toBe(403);

    await revokeApiKey(actor, key.id);
    expect((await listLeads(new Request("http://x/api/v1/leads", { headers: { authorization: `Bearer ${token}` } }), {})).status).toBe(401);
  });

  it("lets the CRM write back sales outcomes", async () => {
    const actor = await makeUser("admin");
    const { token } = await createApiKey(actor, "CRM-write", ["leads:write"]);
    const [lead] = await db().select().from(schema.leads);
    const res = await patchLead(
      new Request("http://x", { method: "PATCH", headers: { authorization: `Bearer ${token}` }, body: JSON.stringify({ stage: "won", crmExternalId: "HS-42", dealValueUsd: 6000 }) }),
      { params: Promise.resolve({ id: lead.id }) },
    );
    expect(res.status).toBe(200);
    const [updated] = await db().select().from(schema.leads).where(eq(schema.leads.id, lead.id));
    expect(updated).toMatchObject({ stage: "won", crmExternalId: "HS-42", dealValueUsd: 6000 });
    const bad = await patchLead(
      new Request("http://x", { method: "PATCH", headers: { authorization: `Bearer ${token}` }, body: JSON.stringify({ stage: "bogus" }) }),
      { params: Promise.resolve({ id: lead.id }) },
    );
    expect(bad.status).toBe(422);
  });
});

describe("webhooks", () => {
  it("queues lead events and delivers them signed", async () => {
    const [ep] = await db().insert(schema.webhookEndpoints).values({ url: "https://crm.example.com/hook", events: ["lead.created"], secretEnc: encryptSecret("whsec_test") }).returning();
    await emitEvent("lead.created", { id: "x" });
    const jobs = await db().select().from(schema.jobs).where(eq(schema.jobs.type, "webhook.deliver"));
    expect(jobs.length).toBeGreaterThan(0);

    let captured: { headers: Headers; body: string } | null = null;
    const fakeFetch = (async (_url: string, init: RequestInit) => {
      captured = { headers: new Headers(init.headers), body: String(init.body) };
      return new Response("ok", { status: 200 });
    }) as unknown as typeof fetch;
    await deliverWebhook(ep.id, { id: "evt1", event: "lead.created", data: {} }, fakeFetch);
    const ts = captured!.headers.get("x-ce-timestamp")!;
    expect(captured!.headers.get("x-ce-signature")).toBe(signPayload("whsec_test", ts, captured!.body));

    const failing = (async () => new Response("no", { status: 500 })) as unknown as typeof fetch;
    await expect(deliverWebhook(ep.id, { id: "evt2", event: "lead.created" }, failing)).rejects.toThrow(/500/);
  });
});

describe("audit log", () => {
  it("is append-only at the database level", async () => {
    const [row] = await db().select().from(schema.auditLogs).limit(1);
    await expect(db().update(schema.auditLogs).set({ action: "x" }).where(eq(schema.auditLogs.id, row.id))).rejects.toThrow();
    await expect(db().delete(schema.auditLogs).where(eq(schema.auditLogs.id, row.id))).rejects.toThrow();
  });
});
