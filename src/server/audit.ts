import { db, schema } from "@/server/db";

export type Actor = { id: string | null; label: string };

export const SYSTEM_ACTOR: Actor = { id: null, label: "system" };

export async function audit(
  actor: Actor,
  action: string,
  entityType: string,
  entityId: string | null,
  data: Record<string, unknown> = {},
) {
  await db().insert(schema.auditLogs).values({
    actorId: actor.id,
    actorLabel: actor.label,
    action,
    entityType,
    entityId,
    data,
  });
}
