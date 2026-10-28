import { eq } from "drizzle-orm";
import { db, schema } from "@/server/db";
import { deviceClass, resolveDestination } from "@/server/leads/links";
import { env } from "@/server/env";

/**
 * Tracking redirect. Logs an anonymous click (no IP, no full user agent,
 * no cookies) and forwards to the destination with the link code attached.
 */
export async function GET(request: Request, { params }: { params: Promise<{ code: string }> }) {
  const { code } = await params;
  // Public base URL (request.url may be an internal address behind a reverse proxy).
  const base = new URL(env().APP_URL);
  if (!/^[a-z0-9]{4,20}$/.test(code)) return Response.redirect(new URL("/apply/coaching", base), 302);
  const [link] = await db().select().from(schema.trackingLinks).where(eq(schema.trackingLinks.code, code));
  if (!link) return Response.redirect(new URL("/apply/coaching", base), 302);
  let referrerHost: string | null = null;
  try {
    referrerHost = request.headers.get("referer") ? new URL(request.headers.get("referer")!).host : null;
  } catch {
    referrerHost = null;
  }
  await db().insert(schema.linkClicks).values({ linkId: link.id, device: deviceClass(request.headers.get("user-agent")), referrerHost });
  return Response.redirect(new URL(resolveDestination(link), base), 302);
}
