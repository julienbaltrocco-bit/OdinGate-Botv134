import { and, eq, isNull } from "drizzle-orm";
import { db, schema } from "@/server/db";
import { randomToken, sha256 } from "@/server/crypto";
import { audit, type Actor } from "@/server/audit";

export const API_SCOPES = ["leads:read", "leads:write", "content:read", "metrics:read"] as const;
export type ApiScope = (typeof API_SCOPES)[number];

/** Creates a key; the plaintext is shown once and only its hash is stored. */
export async function createApiKey(actor: Actor, name: string, scopes: ApiScope[]) {
  const token = `ce_${randomToken(24)}`;
  const [key] = await db()
    .insert(schema.apiKeys)
    .values({ name, prefix: token.slice(0, 10), keyHash: sha256(token), scopes, createdBy: actor.id })
    .returning();
  await audit(actor, "apikey.created", "api_key", key.id, { name, scopes });
  return { key, token };
}

export async function revokeApiKey(actor: Actor, id: string) {
  await db().update(schema.apiKeys).set({ revokedAt: new Date() }).where(eq(schema.apiKeys.id, id));
  await audit(actor, "apikey.revoked", "api_key", id);
}

export async function authenticateApiKey(header: string | null, scope: ApiScope) {
  const token = header?.match(/^Bearer\s+(\S+)$/i)?.[1];
  if (!token) return { ok: false as const, status: 401, error: "missing_token" };
  const [key] = await db()
    .select()
    .from(schema.apiKeys)
    .where(and(eq(schema.apiKeys.keyHash, sha256(token)), isNull(schema.apiKeys.revokedAt)));
  if (!key) return { ok: false as const, status: 401, error: "invalid_token" };
  if (!key.scopes.includes(scope)) return { ok: false as const, status: 403, error: "insufficient_scope" };
  await db().update(schema.apiKeys).set({ lastUsedAt: new Date() }).where(eq(schema.apiKeys.id, key.id));
  return { ok: true as const, key };
}
