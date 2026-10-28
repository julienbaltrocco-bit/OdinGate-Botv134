/** Weekly mix targets from the briefing; enforced in code, not left to the model. */
export const WEEKLY_MIX = { reels: 5, carousels: 2, storyDays: 7, storyFramesMin: 3, storyFramesMax: 5 } as const;

export type PlannedPost = { day: number; time: string; title: string };
export type PlannedStoryDay = { day: number };

export type PlanShape = { reels: PlannedPost[]; carousels: PlannedPost[]; storyDays: PlannedStoryDay[] };

export function validatePlanShape(plan: PlanShape): string[] {
  const errors: string[] = [];
  if (plan.reels.length !== WEEKLY_MIX.reels) errors.push(`Es müssen genau ${WEEKLY_MIX.reels} Reels sein (erhalten: ${plan.reels.length}).`);
  if (plan.carousels.length !== WEEKLY_MIX.carousels)
    errors.push(`Es müssen genau ${WEEKLY_MIX.carousels} Carousels sein (erhalten: ${plan.carousels.length}).`);
  const storyDays = new Set(plan.storyDays.map((s) => s.day));
  if (storyDays.size !== WEEKLY_MIX.storyDays || [...storyDays].some((d) => d < 0 || d > 6))
    errors.push("Für jeden Wochentag (0-6) muss genau ein Story-Set geplant sein.");
  for (const p of [...plan.reels, ...plan.carousels]) {
    if (!Number.isInteger(p.day) || p.day < 0 || p.day > 6) errors.push(`Ungültiger Tag ${p.day} bei "${p.title}".`);
    if (!/^([01]\d|2[0-3]):[0-5]\d$/.test(p.time)) errors.push(`Ungültige Uhrzeit "${p.time}" bei "${p.title}".`);
  }
  const feedPerDay = new Map<number, number>();
  for (const p of [...plan.reels, ...plan.carousels]) feedPerDay.set(p.day, (feedPerDay.get(p.day) ?? 0) + 1);
  if ([...feedPerDay.values()].some((n) => n > 2)) errors.push("Maximal 2 Feed-Beiträge pro Tag.");
  return errors;
}

/** Clamps story frame counts into the 3-5 range expected per day. */
export function storyFramesWithinRange(n: number): boolean {
  return n >= WEEKLY_MIX.storyFramesMin && n <= WEEKLY_MIX.storyFramesMax;
}
