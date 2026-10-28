import { desc, eq } from "drizzle-orm";
import { db, schema } from "@/server/db";
import { apiHandler } from "@/server/integrations/crm/http";

/** GET /api/v1/content?status=published – content items for attribution in the CRM. */
export const GET = apiHandler("content:read", async (req) => {
  const status = new URL(req.url).searchParams.get("status");
  const rows = await db()
    .select({
      id: schema.contentItems.id,
      title: schema.contentItems.title,
      format: schema.contentItems.format,
      pillar: schema.contentItems.pillar,
      audience: schema.contentItems.audience,
      status: schema.contentItems.status,
      scheduledAt: schema.contentItems.scheduledAt,
      publishedAt: schema.contentItems.publishedAt,
      permalink: schema.contentItems.igPermalink,
    })
    .from(schema.contentItems)
    .where(status ? eq(schema.contentItems.status, status as "published") : undefined)
    .orderBy(desc(schema.contentItems.scheduledAt))
    .limit(500);
  return Response.json({ data: rows });
});
