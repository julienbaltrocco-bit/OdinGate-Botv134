import { describe, expect, it } from "vitest";
import { validatePlanShape } from "@/server/workflow/plan-rules";

const post = (day: number, time = "18:00") => ({ day, time, title: `t${day}` });
const valid = {
  reels: [0, 1, 2, 3, 4].map((d) => post(d)),
  carousels: [post(1, "12:00"), post(3, "12:00")],
  storyDays: [0, 1, 2, 3, 4, 5, 6].map((day) => ({ day })),
};

describe("weekly plan rules", () => {
  it("accepts 5 reels, 2 carousels, 7 story days", () => expect(validatePlanShape(valid)).toEqual([]));
  it("rejects wrong counts", () => {
    expect(validatePlanShape({ ...valid, reels: valid.reels.slice(0, 4) })).toHaveLength(1);
    expect(validatePlanShape({ ...valid, storyDays: valid.storyDays.slice(1) }).join()).toMatch(/Story/);
  });
  it("rejects invalid times and overloaded days", () => {
    expect(validatePlanShape({ ...valid, reels: [...valid.reels.slice(0, 4), post(4, "25:00")] }).join()).toMatch(/Uhrzeit/);
    expect(validatePlanShape({ ...valid, carousels: [post(1, "12:00"), post(1, "13:00")] }).join()).toMatch(/Maximal 2/);
  });
});
