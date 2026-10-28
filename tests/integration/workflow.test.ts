import { beforeAll, describe, expect, it } from "vitest";
import { and, eq } from "drizzle-orm";
import { db, schema } from "@/server/db";
import { enqueue } from "@/server/jobs/queue";
import {
  assertCurrentVersionApproved,
  createVersion,
  decide,
  getItem,
  markPublished,
  schedule,
  submitForReview,
  type Principal,
} from "@/server/workflow/content";
import { ForbiddenError } from "@/server/auth/rbac";
import { drainJobs, makeUser, resetDb } from "../helpers";

const WEEK = "2026-11-02";

describe("weekly workflow (mock LLM)", () => {
  let editor: Principal;
  let reviewer: Principal;
  let compliance: Principal;

  beforeAll(async () => {
    await resetDb();
    editor = await makeUser("editor");
    reviewer = await makeUser("reviewer");
    compliance = await makeUser("compliance");
    await db().insert(schema.researchSources).values({
      kind: "faq",
      title: "Häufige Frage aus Calls",
      content: "Wie werden Overrides auf Handelsvolumen abgerechnet?",
    });
  });

  it("research creates traceable topics", async () => {
    await enqueue("research.run", { count: 6 }, { createdBy: editor.id });
    await drainJobs();
    const topics = await db().select().from(schema.topics);
    expect(topics.length).toBe(6);
    expect(topics[0].sources[0].title).toBe("Häufige Frage aus Calls");
    const runs = await db().select().from(schema.agentRuns).where(eq(schema.agentRuns.agent, "research"));
    expect(runs[0].status).toBe("succeeded");
    expect(runs[0].provider).toBe("mock");
  });

  it("generates a 7-day plan with the required mix and drafts every item", async () => {
    await enqueue("plan.generate", { weekStart: WEEK, draftAll: true }, { createdBy: editor.id });
    const log = await drainJobs();
    expect(log.filter((l) => l.includes("FAILED"))).toEqual([]);

    const [plan] = await db().select().from(schema.contentPlans);
    expect(plan.weekStart).toBe(WEEK);
    const items = await db().select().from(schema.contentItems).where(eq(schema.contentItems.planId, plan.id));
    expect(items.filter((i) => i.format === "reel")).toHaveLength(5);
    expect(items.filter((i) => i.format === "carousel")).toHaveLength(2);
    expect(items.filter((i) => i.format === "story")).toHaveLength(7);
    expect(items.every((i) => i.status === "draft" && i.currentVersionId)).toBe(true);

    // Reel slots were planned at 18:00 Berlin time (CET in November = 17:00 UTC).
    const monday = items.find((i) => i.format === "reel" && i.scheduledAt?.toISOString().startsWith(WEEK));
    expect(monday?.scheduledAt?.toISOString()).toBe(`${WEEK}T17:00:00.000Z`);

    // Conversion items get an attribution link.
    const withLink = items.filter((i) => i.trackingLinkId);
    expect(withLink.length).toBeGreaterThan(0);

    const reel = items.find((i) => i.format === "reel")!;
    const [v] = await db().select().from(schema.contentVersions).where(eq(schema.contentVersions.id, reel.currentVersionId!));
    expect((v.body as { production?: unknown }).production).toBeTruthy();
    expect(v.compliance).toBeTruthy();
  });

  it("documents approvals bound to a version and enforces roles", async () => {
    const [item] = await db().select().from(schema.contentItems).where(eq(schema.contentItems.format, "carousel")).limit(1);
    await submitForReview(editor, item.id);
    await expect(decide(editor, item.id, "approved", "")).rejects.toBeInstanceOf(ForbiddenError);
    await expect(decide(reviewer, item.id, "changes_requested", "")).rejects.toThrow(/Begründung/);

    const approval = await decide(reviewer, item.id, "approved", "Passt.");
    expect(approval.versionId).toBe((await getItem(item.id)).currentVersionId);
    expect((await getItem(item.id)).status).toBe("approved");
    await assertCurrentVersionApproved(item.id);

    // Editing after approval invalidates it.
    await createVersion(editor, item.id, { body: { slides: [{ kind: "cover", headline: "Neu", body: "" }] }, caption: "Neue Caption", source: "human" });
    expect((await getItem(item.id)).status).toBe("draft");
    await expect(assertCurrentVersionApproved(item.id)).rejects.toThrow(/nicht freigegeben/);

    const audits = await db().select().from(schema.auditLogs).where(and(eq(schema.auditLogs.entityId, item.id), eq(schema.auditLogs.action, "content.approved")));
    expect(audits).toHaveLength(1);
  });

  it("routes trading content to compliance and blocks unlawful claims", async () => {
    const [item] = await db().select().from(schema.contentItems).where(eq(schema.contentItems.format, "reel")).limit(1);
    await createVersion(editor, item.id, {
      body: { hook: "Warum Signalgruppen mit Hebel gefährlich sind", segments: [] },
      caption: "Keine Anlageberatung.",
      source: "human",
    });
    expect((await getItem(item.id)).requiresComplianceReview).toBe(true);
    await submitForReview(editor, item.id);
    await expect(decide(reviewer, item.id, "approved", "ok")).rejects.toThrow(/Compliance/);
    await expect(decide(compliance, item.id, "approved", "ok", false)).rejects.toThrow(/bestätigen/);
    await decide(compliance, item.id, "approved", "Geprüft", true);
    expect((await getItem(item.id)).status).toBe("approved");

    await createVersion(editor, item.id, { body: { hook: "Garantiert 10% Rendite pro Monat", segments: [] }, caption: "", source: "human" });
    await submitForReview(editor, item.id);
    await expect(decide(compliance, item.id, "approved", "ok", true)).rejects.toThrow(/blockierende/);
    await decide(compliance, item.id, "rejected", "Renditeversprechen");
    expect((await getItem(item.id)).status).toBe("rejected");
  });

  it("regeneration passes reviewer feedback and creates a new AI version", async () => {
    const [item] = await db().select().from(schema.contentItems).where(eq(schema.contentItems.format, "story")).limit(1);
    await submitForReview(editor, item.id);
    await decide(reviewer, item.id, "changes_requested", "Mehr Praxisbezug");
    await enqueue("item.draft", { itemId: item.id, feedback: "Bitte kürzer" }, { createdBy: editor.id });
    await drainJobs();
    const versions = await db().select().from(schema.contentVersions).where(eq(schema.contentVersions.itemId, item.id));
    expect(versions).toHaveLength(2);
    expect((await getItem(item.id)).status).toBe("draft");
    const [run] = await db()
      .select()
      .from(schema.agentRuns)
      .where(eq(schema.agentRuns.id, versions.find((v) => v.version === 2)!.agentRunId!));
    expect(String((run.input as { prompt: string }).prompt)).toContain("Mehr Praxisbezug");
  });

  it("schedules approved content; without API publishing a manual publish is recorded", async () => {
    const [item] = await db().select().from(schema.contentItems).where(and(eq(schema.contentItems.format, "reel"), eq(schema.contentItems.status, "draft"))).limit(1);
    await submitForReview(editor, item.id);
    const it2 = await getItem(item.id);
    if (it2.requiresComplianceReview) await decide(compliance, item.id, "approved", "ok", true);
    else await decide(reviewer, item.id, "approved", "ok");
    const res = await schedule(editor, item.id, new Date(Date.now() + 3600_000));
    expect(res.autoPublish).toBe(false);
    expect((await getItem(item.id)).status).toBe("scheduled");
    await markPublished(editor, item.id, "https://www.instagram.com/reel/abc/");
    const done = await getItem(item.id);
    expect(done.status).toBe("published");
    expect(done.igPermalink).toContain("instagram.com");
  });
});
