import { and, desc, eq, gte, lt, type SQL } from "drizzle-orm";
import { db, schema } from "@/server/db";
import { apiHandler } from "@/server/integrations/crm/http";
import { leadPayload } from "@/server/leads/leads";

/** GET /api/v1/leads?since=ISO&before=ISO&stage=new&type=coaching&limit=100 */
export const GET = apiHandler("leads:read", async (req) => {
  const p = new URL(req.url).searchParams;
  const conds: SQL[] = [];
  if (p.get("since")) conds.push(gte(schema.leads.updatedAt, new Date(p.get("since")!)));
  if (p.get("before")) conds.push(lt(schema.leads.createdAt, new Date(p.get("before")!)));
  const stage = p.get("stage");
  if (stage) conds.push(eq(schema.leads.stage, stage as "new"));
  const type = p.get("type");
  if (type === "coaching" || type === "partner") conds.push(eq(schema.leads.type, type));
  const limit = Math.min(500, Math.max(1, Number(p.get("limit") ?? 100) || 100));
  const rows = await db().select().from(schema.leads).where(conds.length ? and(...conds) : undefined).orderBy(desc(schema.leads.createdAt)).limit(limit);
  return Response.json({ data: rows.map(leadPayload) });
});
