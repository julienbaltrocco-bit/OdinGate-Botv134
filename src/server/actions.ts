import "server-only";
import { redirect, unstable_rethrow } from "next/navigation";
import { ZodError } from "zod";
import { requireUser, actorOf } from "@/server/auth/current";
import type { Permission } from "@/server/auth/rbac";
import type { SessionUser } from "@/server/auth/sessions";
import type { Principal } from "@/server/workflow/content";
import { describeError } from "@/server/ai/llm";

/**
 * Wraps a server action: authenticates + authorises, runs `fn`, then redirects
 * back to `back` with a flash message (?ok=… or ?err=…). Errors never leak
 * stack traces to the browser.
 */
export async function action(
  back: string,
  permission: Permission,
  fn: (ctx: { user: SessionUser; principal: Principal; actor: { id: string; label: string } }) => Promise<string | { message: string; redirectTo: string } | void>,
): Promise<never> {
  const user = await requireUser();
  let target: string;
  try {
    const { can } = await import("@/server/auth/rbac");
    if (!can(user.role, permission)) throw new Error(`Keine Berechtigung (${permission}).`);
    const actor = actorOf(user) as { id: string; label: string };
    const result = await fn({ user, principal: { id: user.id, label: user.email, role: user.role }, actor });
    if (result && typeof result === "object") target = flash(result.redirectTo, "ok", result.message);
    else target = flash(back, "ok", result || "Gespeichert.");
  } catch (err) {
    unstable_rethrow(err);
    target = flash(back, "err", errorMessage(err));
  }
  redirect(target);
}

export function errorMessage(err: unknown): string {
  if (err instanceof ZodError) return err.issues.map((i) => `${i.path.join(".") || "Eingabe"}: ${i.message}`).join("; ");
  return describeError(err);
}

function flash(path: string, key: "ok" | "err", message: string) {
  const url = new URL(path, "http://x");
  url.searchParams.delete("ok");
  url.searchParams.delete("err");
  url.searchParams.set(key, message.slice(0, 300));
  return url.pathname + url.search + url.hash;
}

export function str(fd: FormData, key: string): string {
  const v = fd.get(key);
  return typeof v === "string" ? v.trim() : "";
}

export function optNum(fd: FormData, key: string): number | undefined {
  const s = str(fd, key);
  if (!s) return undefined;
  const n = Number(s.replace(",", "."));
  if (!Number.isFinite(n)) throw new Error(`${key}: keine Zahl`);
  return n;
}
