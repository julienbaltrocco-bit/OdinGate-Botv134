/** Content lifecycle. Pure functions, unit-tested in tests/unit/state.test.ts. */

export type ContentStatus =
  | "planned"
  | "draft"
  | "in_review"
  | "changes_requested"
  | "approved"
  | "rejected"
  | "scheduled"
  | "publishing"
  | "published"
  | "failed";

const TRANSITIONS: Record<ContentStatus, ContentStatus[]> = {
  planned: ["draft"],
  draft: ["draft", "in_review"],
  in_review: ["approved", "changes_requested", "rejected", "draft"],
  changes_requested: ["draft", "in_review"],
  rejected: ["draft"],
  approved: ["scheduled", "draft", "published"],
  scheduled: ["publishing", "approved", "draft", "published"],
  publishing: ["published", "failed"],
  failed: ["scheduled", "approved", "draft", "published"],
  published: [],
};

export function canTransition(from: ContentStatus, to: ContentStatus): boolean {
  return TRANSITIONS[from].includes(to);
}

export class TransitionError extends Error {
  constructor(from: ContentStatus, to: ContentStatus) {
    super(`Statuswechsel von "${STATUS_LABELS[from]}" nach "${STATUS_LABELS[to]}" ist nicht erlaubt.`);
    this.name = "TransitionError";
  }
}

export function assertTransition(from: ContentStatus, to: ContentStatus) {
  if (!canTransition(from, to)) throw new TransitionError(from, to);
}

/** Editing content after approval invalidates the approval (it is bound to a version). */
export function statusAfterEdit(current: ContentStatus): ContentStatus {
  if (current === "published" || current === "publishing") {
    throw new Error("Veröffentlichte Inhalte können nicht mehr bearbeitet werden.");
  }
  return "draft";
}

export const STATUS_LABELS: Record<ContentStatus, string> = {
  planned: "Geplant (ohne Entwurf)",
  draft: "Entwurf",
  in_review: "In Prüfung",
  changes_requested: "Änderungen angefragt",
  approved: "Freigegeben",
  rejected: "Abgelehnt",
  scheduled: "Eingeplant",
  publishing: "Wird veröffentlicht",
  published: "Veröffentlicht",
  failed: "Fehlgeschlagen",
};

export const STATUS_COLORS: Record<ContentStatus, string> = {
  planned: "bg-slate-100 text-slate-700",
  draft: "bg-amber-100 text-amber-800",
  in_review: "bg-blue-100 text-blue-800",
  changes_requested: "bg-orange-100 text-orange-800",
  approved: "bg-emerald-100 text-emerald-800",
  rejected: "bg-red-100 text-red-800",
  scheduled: "bg-indigo-100 text-indigo-800",
  publishing: "bg-indigo-100 text-indigo-800",
  published: "bg-emerald-600 text-white",
  failed: "bg-red-600 text-white",
};
