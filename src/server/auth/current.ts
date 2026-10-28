import "server-only";
import { cookies } from "next/headers";
import { redirect } from "next/navigation";
import { userForSessionToken, type SessionUser } from "./sessions";
import { can, ForbiddenError, type Permission } from "./rbac";
import type { Actor } from "@/server/audit";

export const SESSION_COOKIE = "ce_session";

export async function currentUser(): Promise<SessionUser | null> {
  const token = (await cookies()).get(SESSION_COOKIE)?.value;
  if (!token) return null;
  return userForSessionToken(token);
}

/** For pages: redirects to /login when signed out. */
export async function requireUser(permission?: Permission): Promise<SessionUser> {
  const user = await currentUser();
  if (!user) redirect("/login");
  if (permission && !can(user.role, permission)) throw new ForbiddenError(permission);
  return user;
}

export function actorOf(user: SessionUser): Actor {
  return { id: user.id, label: user.email };
}
