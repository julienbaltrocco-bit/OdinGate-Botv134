import { eq } from "drizzle-orm";
import { db, schema } from "@/server/db";
import { apiHandler } from "@/server/integrations/crm/http";
import { leadPayload, LeadUpdate, updateLead } from "@/server/leads/leads";

type Ctx = { params: Promise<{ id: string }> };

export const GET = apiHandler<Ctx>("leads:read", async (_req, { params }) => {
  const { id } = await params;
  if (!/^[0-9a-f-]{36}$/.test(id)) return Response.json({ error: "not_found" }, { status: 404 });
  const [lead] = await db().select().from(schema.leads).where(eq(schema.leads.id, id));
  return lead ? Response.json({ data: leadPayload(lead) }) : Response.json({ error: "not_found" }, { status: 404 });
});

/** PATCH /api/v1/leads/:id  { stage?, notes?, dealValueUsd?, crmExternalId? } – CRM writes back sales outcomes. */
export const PATCH = apiHandler<Ctx>("leads:write", async (req, { params }, key) => {
  const { id } = await params;
  if (!/^[0-9a-f-]{36}$/.test(id)) return Response.json({ error: "not_found" }, { status: 404 });
  const patch = LeadUpdate.parse(await req.json());
  const [exists] = await db().select({ id: schema.leads.id }).from(schema.leads).where(eq(schema.leads.id, id));
  if (!exists) return Response.json({ error: "not_found" }, { status: 404 });
  const lead = await updateLead({ id: null, label: `api:${key.name}` }, id, patch);
  return Response.json({ data: leadPayload(lead) });
});
