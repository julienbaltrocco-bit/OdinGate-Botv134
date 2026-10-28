import { and, desc, eq, max } from "drizzle-orm";
import { db, schema } from "@/server/db";
import { audit } from "@/server/audit";
import { can, ForbiddenError, type Permission, type Role } from "@/server/auth/rbac";
import { checkCompliance } from "@/server/compliance/checker";
import { getBrand } from "@/server/brand";
import { bodyText, type Format } from "@/lib/content-types";
import { assertTransition, statusAfterEdit, type ContentStatus } from "./state";
import { enqueue } from "@/server/jobs/queue";
import { env } from "@/server/env";
import { emitEvent } from "@/server/integrations/crm/webhooks";

/** Who performs an action. Workers act as `system` with admin-equivalent rights for automated steps. */
export type Principal = { id: string | null; label: string; role: Role };
export const SYSTEM: Principal = { id: null, label: "system", role: "admin" };

export class WorkflowError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "WorkflowError";
  }
}

function require(p: Principal, permission: Permission) {
  if (!can(p.role, permission)) throw new ForbiddenError(permission);
}

export async function getItem(itemId: string) {
  const [item] = await db().select().from(schema.contentItems).where(eq(schema.contentItems.id, itemId));
  if (!item) throw new WorkflowError("Inhalt nicht gefunden.");
  return item;
}

export async function getVersion(versionId: string) {
  const [v] = await db().select().from(schema.contentVersions).where(eq(schema.contentVersions.id, versionId));
  return v ?? null;
}

async function setStatus(itemId: string, from: ContentStatus, to: ContentStatus, patch: Partial<typeof schema.contentItems.$inferInsert> = {}) {
  assertTransition(from, to);
  // Optimistic concurrency: only update when the status is still what we validated against.
  const updated = await db()
    .update(schema.contentItems)
    .set({ ...patch, status: to, updatedAt: new Date() })
    .where(and(eq(schema.contentItems.id, itemId), eq(schema.contentItems.status, from)))
    .returning({ id: schema.contentItems.id });
  if (!updated.length) throw new WorkflowError("Der Inhalt wurde zwischenzeitlich geändert. Bitte neu laden.");
}

/**
 * Creates a new version (AI or human), runs compliance checks and resets the
 * item to "draft". Any previous approval no longer applies to the new version.
 */
export async function createVersion(
  p: Principal,
  itemId: string,
  input: { body: Record<string, unknown>; caption: string; source: "ai" | "human"; agentRunId?: string | null },
) {
  require(p, input.source === "ai" ? "content.generate" : "content.edit");
  const item = await getItem(itemId);
  const nextStatus = statusAfterEdit(item.status);
  const brand = await getBrand();
  const compliance = checkCompliance({
    text: bodyText(item.format as Format, input.body, ""),
    caption: input.caption,
    disclosureText: brand.settings.disclosures.affiliate,
  });

  const [{ value: last }] = await db()
    .select({ value: max(schema.contentVersions.version) })
    .from(schema.contentVersions)
    .where(eq(schema.contentVersions.itemId, itemId));

  const [version] = await db()
    .insert(schema.contentVersions)
    .values({
      itemId,
      version: (last ?? 0) + 1,
      body: input.body,
      caption: input.caption,
      source: input.source,
      agentRunId: input.agentRunId ?? null,
      compliance,
      createdBy: p.id,
    })
    .returning();

  const wasApproved = ["approved", "scheduled", "failed"].includes(item.status);
  await db()
    .update(schema.contentItems)
    .set({
      currentVersionId: version.id,
      status: nextStatus,
      requiresComplianceReview: compliance.requiresComplianceReview,
      updatedAt: new Date(),
    })
    .where(eq(schema.contentItems.id, itemId));

  await audit(p, "content.version_created", "content_item", itemId, {
    version: version.version,
    source: input.source,
    agentRunId: input.agentRunId ?? null,
    complianceBlocking: compliance.blocking,
    approvalInvalidated: wasApproved,
  });
  return version;
}

export async function submitForReview(p: Principal, itemId: string) {
  require(p, "content.edit");
  const item = await getItem(itemId);
  if (!item.currentVersionId) throw new WorkflowError("Kein Entwurf vorhanden.");
  await setStatus(itemId, item.status, "in_review");
  await audit(p, "content.submitted", "content_item", itemId, { versionId: item.currentVersionId });
}

export async function withdrawFromReview(p: Principal, itemId: string) {
  require(p, "content.edit");
  const item = await getItem(itemId);
  await setStatus(itemId, item.status, "draft");
  await audit(p, "content.withdrawn", "content_item", itemId);
}

export type Decision = "approved" | "changes_requested" | "rejected";

/**
 * Records a documented review decision bound to the current version.
 * Rules: blocking compliance findings cannot be approved; trading/financial
 * content needs a compliance sign-off; reviewers cannot approve their own edits.
 */
export async function decide(p: Principal, itemId: string, decision: Decision, comment: string, complianceAck = false) {
  require(p, "content.approve");
  if (!p.id) throw new WorkflowError("Freigaben erfordern einen angemeldeten Menschen.");
  const item = await getItem(itemId);
  if (item.status !== "in_review") throw new WorkflowError("Nur Inhalte im Status 'In Prüfung' können entschieden werden.");
  const version = item.currentVersionId ? await getVersion(item.currentVersionId) : null;
  if (!version) throw new WorkflowError("Kein Entwurf vorhanden.");

  if (decision !== "approved" && !comment.trim()) {
    throw new WorkflowError("Bitte eine Begründung angeben.");
  }
  if (decision === "approved") {
    if (version.compliance?.blocking) {
      throw new WorkflowError("Freigabe nicht möglich: Es gibt blockierende Compliance-Befunde.");
    }
    if (item.requiresComplianceReview) {
      if (!can(p.role, "content.compliance_signoff")) {
        throw new WorkflowError("Dieser Inhalt hat Trading-/Finanzbezug und benötigt eine Freigabe durch Compliance.");
      }
      if (!complianceAck) throw new WorkflowError("Bitte die Compliance-Prüfung ausdrücklich bestätigen.");
    }
    if (version.source === "human" && version.createdBy === p.id && p.role !== "admin") {
      throw new WorkflowError("Vier-Augen-Prinzip: Eigene Änderungen können nicht selbst freigegeben werden.");
    }
  }

  await setStatus(itemId, "in_review", decision);
  const [approval] = await db()
    .insert(schema.approvals)
    .values({
      itemId,
      versionId: version.id,
      decision,
      comment: comment.trim(),
      complianceAck: decision === "approved" && item.requiresComplianceReview ? complianceAck : false,
      reviewerId: p.id,
      reviewerRole: p.role,
    })
    .returning();
  await audit(p, `content.${decision}`, "content_item", itemId, {
    approvalId: approval.id,
    versionId: version.id,
    version: version.version,
    comment: comment.trim(),
  });
  if (decision === "approved") {
    await emitEvent("content.approved", { itemId, versionId: version.id, version: version.version, title: item.title, format: item.format });
  }
  return approval;
}

/** Plans an approved item. Publishing via API only happens when explicitly enabled and connected. */
export async function schedule(p: Principal, itemId: string, at: Date) {
  require(p, "content.schedule");
  const item = await getItem(itemId);
  if (!["approved", "failed", "scheduled"].includes(item.status)) {
    throw new WorkflowError("Nur freigegebene Inhalte können eingeplant werden.");
  }
  await assertCurrentVersionApproved(itemId);
  if (item.status === "scheduled") {
    await db().update(schema.contentItems).set({ scheduledAt: at, updatedAt: new Date() }).where(eq(schema.contentItems.id, itemId));
  } else {
    await setStatus(itemId, item.status, "scheduled", { scheduledAt: at, lastError: null });
  }
  const autoPublish = await canAutoPublish();
  if (autoPublish) await enqueue("instagram.publish", { itemId }, { runAt: at, createdBy: p.id, maxAttempts: 3 });
  await audit(p, "content.scheduled", "content_item", itemId, { at: at.toISOString(), autoPublish });
  return { autoPublish };
}

export async function unschedule(p: Principal, itemId: string) {
  require(p, "content.schedule");
  const item = await getItem(itemId);
  await setStatus(itemId, item.status, "approved");
  await audit(p, "content.unscheduled", "content_item", itemId);
}

/** Manual publishing step (when API publishing is not available): records the live post. */
export async function markPublished(p: Principal, itemId: string, permalink: string) {
  require(p, "content.schedule");
  const item = await getItem(itemId);
  await assertCurrentVersionApproved(itemId);
  await setStatus(itemId, item.status, "published", { publishedAt: new Date(), igPermalink: permalink || null });
  await audit(p, "content.published_manual", "content_item", itemId, { permalink });
  await emitEvent("content.published", { itemId, permalink, method: "manual" });
}

export async function assertCurrentVersionApproved(itemId: string) {
  const item = await getItem(itemId);
  const [latest] = await db()
    .select()
    .from(schema.approvals)
    .where(eq(schema.approvals.itemId, itemId))
    .orderBy(desc(schema.approvals.createdAt))
    .limit(1);
  if (!latest || latest.decision !== "approved" || latest.versionId !== item.currentVersionId) {
    throw new WorkflowError("Die aktuelle Version ist nicht freigegeben.");
  }
  return latest;
}

export async function canAutoPublish(): Promise<boolean> {
  if (!env().INSTAGRAM_PUBLISHING_ENABLED) return false;
  const [ig] = await db().select().from(schema.integrations).where(eq(schema.integrations.provider, "instagram"));
  return ig?.status === "connected";
}

export async function updateItemMeta(
  p: Principal,
  itemId: string,
  patch: { title?: string; brief?: string; scheduledAt?: Date | null; pillar?: typeof schema.contentItems.$inferInsert.pillar; audience?: typeof schema.contentItems.$inferInsert.audience },
) {
  require(p, "content.edit");
  await db().update(schema.contentItems).set({ ...patch, updatedAt: new Date() }).where(eq(schema.contentItems.id, itemId));
  await audit(p, "content.meta_updated", "content_item", itemId, { fields: Object.keys(patch) });
}
