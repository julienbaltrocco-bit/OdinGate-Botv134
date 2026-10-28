import { eq } from "drizzle-orm";
import { z } from "zod";
import { db, schema } from "@/server/db";
import { hashPassword } from "@/server/crypto";
import { audit, type Actor } from "@/server/audit";
import type { Role } from "./rbac";

export const NewUser = z.object({
  email: z.string().trim().toLowerCase().email(),
  name: z.string().trim().min(1).max(120),
  role: z.enum(["admin", "editor", "reviewer", "compliance", "viewer"]),
  password: z.string().min(12, "Passwort: mindestens 12 Zeichen"),
});

export async function createUser(actor: Actor, input: z.infer<typeof NewUser>) {
  const data = NewUser.parse(input);
  const [user] = await db()
    .insert(schema.users)
    .values({ email: data.email, name: data.name, role: data.role, passwordHash: await hashPassword(data.password) })
    .returning({ id: schema.users.id, email: schema.users.email, role: schema.users.role });
  await audit(actor, "user.created", "user", user.id, { email: user.email, role: user.role });
  return user;
}

export async function setUserRole(actor: Actor, userId: string, role: Role) {
  await db().update(schema.users).set({ role }).where(eq(schema.users.id, userId));
  await audit(actor, "user.role_changed", "user", userId, { role });
}

export async function setUserActive(actor: Actor, userId: string, active: boolean) {
  if (actor.id === userId && !active) throw new Error("Eigenes Konto kann nicht deaktiviert werden.");
  await db().update(schema.users).set({ active }).where(eq(schema.users.id, userId));
  if (!active) await db().delete(schema.sessions).where(eq(schema.sessions.userId, userId));
  await audit(actor, active ? "user.activated" : "user.deactivated", "user", userId);
}

export async function resetPassword(actor: Actor, userId: string, password: string) {
  if (password.length < 12) throw new Error("Passwort: mindestens 12 Zeichen");
  await db().update(schema.users).set({ passwordHash: await hashPassword(password) }).where(eq(schema.users.id, userId));
  await db().delete(schema.sessions).where(eq(schema.sessions.userId, userId));
  await audit(actor, "user.password_reset", "user", userId);
}
