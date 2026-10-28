import { createHmac, randomUUID } from "node:crypto";
import { eq } from "drizzle-orm";
import { db, schema } from "@/server/db";
import { decryptSecret } from "@/server/crypto";
import { enqueue } from "@/server/jobs/queue";

/**
 * Outbound webhooks for the sales CRM. Each event is delivered as a signed JSON
 * POST via the job queue (retries with backoff). See docs/API.md#webhooks.
 */
export const WEBHOOK_EVENTS = [
  "lead.created",
  "lead.updated",
  "content.approved",
  "content.published",
] as const;
export type WebhookEvent = (typeof WEBHOOK_EVENTS)[number];

export async function emitEvent(event: WebhookEvent, data: Record<string, unknown>) {
  const endpoints = await db().select().from(schema.webhookEndpoints).where(eq(schema.webhookEndpoints.active, true));
  const envelope = { id: randomUUID(), event, createdAt: new Date().toISOString(), data };
  for (const ep of endpoints) {
    if (ep.events.includes(event) || ep.events.includes("*")) {
      await enqueue("webhook.deliver", { endpointId: ep.id, envelope }, { maxAttempts: 6 });
    }
  }
}

export function signPayload(secret: string, timestamp: string, body: string): string {
  return "sha256=" + createHmac("sha256", secret).update(`${timestamp}.${body}`).digest("hex");
}

export async function deliverWebhook(endpointId: string, envelope: Record<string, unknown>, fetchImpl: typeof fetch = fetch) {
  const [ep] = await db().select().from(schema.webhookEndpoints).where(eq(schema.webhookEndpoints.id, endpointId));
  if (!ep || !ep.active) return { skipped: true };
  const body = JSON.stringify(envelope);
  const timestamp = Math.floor(Date.now() / 1000).toString();
  const res = await fetchImpl(ep.url, {
    method: "POST",
    headers: {
      "content-type": "application/json",
      "x-ce-event": String(envelope.event),
      "x-ce-delivery": String(envelope.id),
      "x-ce-timestamp": timestamp,
      "x-ce-signature": signPayload(decryptSecret(ep.secretEnc), timestamp, body),
    },
    body,
    signal: AbortSignal.timeout(10_000),
  });
  if (!res.ok) throw new Error(`Webhook ${ep.url} antwortete mit HTTP ${res.status}`);
  return { status: res.status };
}
