export const DEFAULT_TZ = "Europe/Berlin";

/** Offset (minutes) of `timeZone` from UTC at the given instant. */
function tzOffsetMinutes(date: Date, timeZone: string): number {
  const parts = new Intl.DateTimeFormat("en-US", {
    timeZone,
    hourCycle: "h23",
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  }).formatToParts(date);
  const get = (t: string) => Number(parts.find((p) => p.type === t)?.value);
  const asUtc = Date.UTC(get("year"), get("month") - 1, get("day"), get("hour"), get("minute"), get("second"));
  return Math.round((asUtc - date.getTime()) / 60000);
}

/** Converts a wall-clock time in `timeZone` (e.g. 2026-11-02 18:30 Berlin) to a UTC Date. */
export function zonedToUtc(isoDate: string, hhmm: string, timeZone = DEFAULT_TZ): Date {
  const [y, m, d] = isoDate.split("-").map(Number);
  const [hh, mm] = hhmm.split(":").map(Number);
  const guess = new Date(Date.UTC(y, m - 1, d, hh, mm));
  const offset = tzOffsetMinutes(guess, timeZone);
  const result = new Date(guess.getTime() - offset * 60000);
  // Re-check across DST boundaries.
  const offset2 = tzOffsetMinutes(result, timeZone);
  return offset2 === offset ? result : new Date(guess.getTime() - offset2 * 60000);
}

export function addDays(isoDate: string, days: number): string {
  const [y, m, d] = isoDate.split("-").map(Number);
  return new Date(Date.UTC(y, m - 1, d + days)).toISOString().slice(0, 10);
}

/** Monday (ISO week start) of the week containing `date`, as YYYY-MM-DD in the given zone. */
export function weekStartOf(date: Date, timeZone = DEFAULT_TZ): string {
  const local = new Intl.DateTimeFormat("en-CA", { timeZone, year: "numeric", month: "2-digit", day: "2-digit" }).format(date);
  const [y, m, d] = local.split("-").map(Number);
  const dow = new Date(Date.UTC(y, m - 1, d)).getUTCDay(); // 0 = Sunday
  return addDays(local, -((dow + 6) % 7));
}

export function formatDateTime(date: Date | string | null | undefined, timeZone = DEFAULT_TZ): string {
  if (!date) return "–";
  return new Intl.DateTimeFormat("de-DE", { timeZone, dateStyle: "medium", timeStyle: "short" }).format(new Date(date));
}

export function formatDate(date: Date | string, timeZone = DEFAULT_TZ): string {
  return new Intl.DateTimeFormat("de-DE", { timeZone, weekday: "short", day: "2-digit", month: "2-digit" }).format(new Date(date));
}

export const WEEKDAYS_DE = ["Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag", "Samstag", "Sonntag"];

/** YYYY-MM-DD of an instant in the given zone. */
export function localIsoDate(date: Date, timeZone = DEFAULT_TZ): string {
  return new Intl.DateTimeFormat("en-CA", { timeZone, year: "numeric", month: "2-digit", day: "2-digit" }).format(date);
}

/** HH:MM of an instant in the given zone. */
export function localTime(date: Date | null | undefined, timeZone = DEFAULT_TZ): string {
  if (!date) return "";
  return new Intl.DateTimeFormat("de-DE", { timeZone, hour: "2-digit", minute: "2-digit", hourCycle: "h23" }).format(date);
}
