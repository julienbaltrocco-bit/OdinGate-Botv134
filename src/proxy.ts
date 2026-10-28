import { NextResponse, type NextRequest } from "next/server";

/**
 * Optimistic auth gate: redirects to /login when no session cookie exists.
 * The real check (session in DB, role permissions) happens in every page and
 * server action via requireUser().
 */
export function proxy(request: NextRequest) {
  if (!request.cookies.get("ce_session")) {
    const url = request.nextUrl.clone();
    url.pathname = "/login";
    url.search = "";
    return NextResponse.redirect(url);
  }
  return NextResponse.next();
}

export const config = {
  // Public: login, application forms, tracking redirects, public API (own auth), health, assets.
  matcher: ["/((?!login|apply|r/|api/v1|api/health|_next|favicon.ico).*)"],
};
