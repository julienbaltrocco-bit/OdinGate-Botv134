import { ZodError } from "zod";
import { authenticateApiKey, type ApiScope } from "./api-keys";

/** Wraps a /api/v1 handler with API-key auth, scope check and JSON errors. */
export function apiHandler<Ctx>(scope: ApiScope, fn: (req: Request, ctx: Ctx, key: { id: string; name: string }) => Promise<Response>) {
  return async (req: Request, ctx: Ctx) => {
    const auth = await authenticateApiKey(req.headers.get("authorization"), scope);
    if (!auth.ok) return Response.json({ error: auth.error }, { status: auth.status });
    try {
      return await fn(req, ctx, { id: auth.key.id, name: auth.key.name });
    } catch (err) {
      if (err instanceof ZodError) return Response.json({ error: "validation_error", issues: err.issues }, { status: 422 });
      if (err instanceof SyntaxError) return Response.json({ error: "invalid_json" }, { status: 400 });
      console.error("[api/v1]", err);
      return Response.json({ error: "internal_error" }, { status: 500 });
    }
  };
}
