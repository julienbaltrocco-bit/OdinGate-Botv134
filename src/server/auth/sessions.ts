import { and, eq, gt } from "drizzle-orm";
import { db, schema } from "@/server/db";
import { env } from "@/server/env";
import { randomToken, sha256, verifyPassword } from "@/server/crypto";
import type { Role } from "./rbac";

export type SessionUser = { id: string; email: string; name: string; role: Role };

export async function authenticate(email: string, password: string): Promise<SessionUser | null> {
  const [user] = await db()
    .select()
    .from(schema.users)
    .where(eq(schema.users.email, email.trim().toLowerCase()))
    .limit(1);
  if (!user || !user.active) return null;
  if (!(await verifyPassword(password, user.passwordHash))) return null;
  return { id: user.id, email: user.email, name: user.name, role: user.role };
}

export async function createSession(userId: string): Promise<{ token: string; expiresAt: Date }> {
  const token = randomToken();
  const expiresAt = new Date(Date.now() + env().SESSION_TTL_HOURS * 3600_000);
  await db().insert(schema.sessions).values({ id: sha256(token), userId, expiresAt });
  return { token, expiresAt };
}

export async function userForSessionToken(token: string): Promise<SessionUser | null> {
  const [row] = await db()
    .select({ id: schema.users.id, email: schema.users.email, name: schema.users.name, role: schema.users.role, active: schema.users.active })
    .from(schema.sessions)
    .innerJoin(schema.users, eq(schema.users.id, schema.sessions.userId))
    .where(and(eq(schema.sessions.id, sha256(token)), gt(schema.sessions.expiresAt, new Date())))
    .limit(1);
  if (!row || !row.active) return null;
  return { id: row.id, email: row.email, name: row.name, role: row.role };
}

export async function deleteSession(token: string) {
  await db().delete(schema.sessions).where(eq(schema.sessions.id, sha256(token)));
}
