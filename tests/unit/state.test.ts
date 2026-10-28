import { describe, expect, it } from "vitest";
import { assertTransition, canTransition, statusAfterEdit } from "@/server/workflow/state";

describe("content state machine", () => {
  it("allows the happy path", () => {
    const path = ["planned", "draft", "in_review", "approved", "scheduled", "publishing", "published"] as const;
    for (let i = 0; i < path.length - 1; i++) expect(canTransition(path[i], path[i + 1])).toBe(true);
  });
  it("forbids skipping review", () => {
    expect(canTransition("draft", "approved")).toBe(false);
    expect(canTransition("draft", "scheduled")).toBe(false);
    expect(() => assertTransition("draft", "published")).toThrow();
  });
  it("published is terminal and cannot be edited", () => {
    expect(canTransition("published", "draft")).toBe(false);
    expect(() => statusAfterEdit("published")).toThrow();
  });
  it("editing approved content falls back to draft", () => {
    expect(statusAfterEdit("approved")).toBe("draft");
    expect(statusAfterEdit("scheduled")).toBe("draft");
  });
});
