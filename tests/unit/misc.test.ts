import { beforeAll, describe, expect, it } from "vitest";
import { decryptSecret, encryptSecret, hashPassword, verifyPassword } from "@/server/crypto";
import { can } from "@/server/auth/rbac";
import { addDays, weekStartOf, zonedToUtc } from "@/lib/time";
import { scoreLead, LeadSubmission } from "@/server/leads/leads";
import { deviceClass, resolveDestination } from "@/server/leads/links";
import { signPayload } from "@/server/integrations/crm/webhooks";
import { resolveSources } from "@/server/agents/research";
import { withHashtags } from "@/server/workflow/drafting";
import { carouselFromForm, reelFromForm, storyFromForm } from "@/server/workflow/forms";
import { fitFontSize } from "@/server/carousel/render";
import { createHmac } from "node:crypto";
import { resetEnvCache } from "@/server/env";

beforeAll(() => resetEnvCache());

describe("crypto", () => {
  it("hashes and verifies passwords", async () => {
    const h = await hashPassword("correct horse battery");
    expect(await verifyPassword("correct horse battery", h)).toBe(true);
    expect(await verifyPassword("wrong", h)).toBe(false);
  });
  it("encrypts secrets with authenticated encryption", () => {
    const enc = encryptSecret("token-123");
    expect(enc).not.toContain("token-123");
    expect(decryptSecret(enc)).toBe("token-123");
    const tampered = enc.slice(0, -2) + (enc.endsWith("A") ? "BB" : "AA");
    expect(() => decryptSecret(tampered)).toThrow();
  });
});

describe("rbac", () => {
  it("separates editing from approval", () => {
    expect(can("editor", "content.edit")).toBe(true);
    expect(can("editor", "content.approve")).toBe(false);
    expect(can("reviewer", "content.compliance_signoff")).toBe(false);
    expect(can("compliance", "content.compliance_signoff")).toBe(true);
    expect(can("viewer", "leads.read")).toBe(false);
  });
});

describe("time", () => {
  it("converts Berlin wall-clock time across DST", () => {
    expect(zonedToUtc("2026-07-01", "18:00").toISOString()).toBe("2026-07-01T16:00:00.000Z");
    expect(zonedToUtc("2026-12-01", "18:00").toISOString()).toBe("2026-12-01T17:00:00.000Z");
    expect(zonedToUtc("2026-03-29", "12:00").toISOString()).toBe("2026-03-29T10:00:00.000Z");
  });
  it("finds the Monday of a week", () => {
    expect(weekStartOf(new Date("2026-10-28T12:00:00Z"))).toBe("2026-10-26");
    expect(weekStartOf(new Date("2026-11-01T22:30:00Z"))).toBe("2026-10-26"); // Sunday 23:30 in Berlin
    expect(weekStartOf(new Date("2026-11-01T23:30:00Z"))).toBe("2026-11-02"); // already Monday 00:30 in Berlin
    expect(addDays("2026-12-31", 1)).toBe("2027-01-01");
  });
});

describe("lead qualification", () => {
  const base = { name: "Max", email: "max@example.com", consent: true as const };
  it("scores partner inquiries transparently", () => {
    const l = LeadSubmission.parse({ ...base, type: "partner", communitySize: "gt50k", monthlyVolume: "gt10m", currentExchangePartner: "yes_unhappy" });
    const s = scoreLead(l);
    expect(s.score).toBe(100);
    expect(s.reasons.length).toBe(3);
  });
  it("penalises missing budget for coaching", () => {
    const l = LeadSubmission.parse({ ...base, type: "coaching", salesExperience: "none", cryptoExperience: "none", hoursPerWeek: "lt5", budgetOk: false });
    expect(scoreLead(l).score).toBe(0);
  });
  it("requires consent and rejects bots (honeypot)", () => {
    expect(() => LeadSubmission.parse({ ...base, consent: false, type: "partner", communitySize: "lt1k", monthlyVolume: "unknown", currentExchangePartner: "none" })).toThrow();
    expect(() => LeadSubmission.parse({ ...base, website: "spam", type: "partner", communitySize: "lt1k", monthlyVolume: "unknown", currentExchangePartner: "none" })).toThrow();
  });
});

describe("links & webhooks", () => {
  it("resolves internal and external destinations", () => {
    expect(resolveDestination({ destination: "coaching", code: "abc" })).toBe("/apply/coaching?src=abc");
    expect(resolveDestination({ destination: "https://cal.example.com/x", code: "abc" })).toContain("utm_content=abc");
  });
  it("classifies devices coarsely", () => {
    expect(deviceClass("Mozilla/5.0 (iPhone) Instagram 300")).toBe("instagram_inapp");
    expect(deviceClass(null)).toBe("unknown");
  });
  it("signs webhook payloads with HMAC-SHA256 over timestamp.body", () => {
    const expected = createHmac("sha256", "s3cret").update("123.{}").digest("hex");
    expect(signPayload("s3cret", "123", "{}")).toBe(`sha256=${expected}`);
  });
});

describe("agents helpers", () => {
  it("keeps only real source references", () => {
    const map = new Map([["S1", { kind: "faq", title: "FAQ", sourceId: "x" }]]);
    expect(resolveSources(["S1", "S9"], map)).toEqual([{ kind: "faq", title: "FAQ", sourceId: "x" }]);
    expect(resolveSources(["erfunden"], map)[0].kind).toBe("expertise");
  });
  it("appends normalised hashtags once", () => {
    expect(withHashtags("Text #kol", ["#kol", "crypto business", ""])).toBe("Text #kol\n\n#cryptobusiness");
  });
  it("shrinks font size for long text but not below the minimum", () => {
    expect(fitFontSize("kurz", 72, 48, 45)).toBe(72);
    expect(fitFontSize("x".repeat(500), 72, 48, 45)).toBe(48);
  });
});

describe("editor forms", () => {
  it("parses reel segments and drops empty rows", () => {
    const fd = new FormData();
    fd.set("hook", "Hook");
    fd.set("seg_0_spoken", "Satz eins");
    fd.set("seg_0_durationSec", "4");
    fd.set("seg_1_spoken", "");
    fd.set("ctaType", "coaching_application");
    const body = reelFromForm(fd, { production: { concept: "c" } as never });
    expect(body.segments).toHaveLength(1);
    expect(body.targetDurationSec).toBe(4);
    expect(body.ctaType).toBe("coaching_application");
    expect(body.production).toBeTruthy();
  });
  it("parses carousel slides and story frames", () => {
    const fd = new FormData();
    fd.set("slide_0_kind", "cover");
    fd.set("slide_0_headline", "Titel");
    fd.set("slide_1_headline", "");
    expect(carouselFromForm(fd, {}).slides).toEqual([{ kind: "cover", headline: "Titel", body: "" }]);
    const sf = new FormData();
    sf.set("frame_0_type", "poll");
    sf.set("frame_0_text", "Frage?");
    sf.set("frame_0_usesTrackingLink", "on");
    expect(storyFromForm(sf, {}).frames[0]).toMatchObject({ type: "poll", usesTrackingLink: true });
  });
});
