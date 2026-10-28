/**
 * Single-series horizontal bar list (magnitude by category). One hue, thin
 * rounded bars anchored at the baseline, values in text ink, native hover
 * tooltip per row. Used where a full chart library would be overkill.
 */
export function BarList({ rows, unit = "", emptyText = "Keine Daten" }: { rows: { label: string; value: number | null; hint?: string }[]; unit?: string; emptyText?: string }) {
  const values = rows.map((r) => r.value ?? 0);
  const max = Math.max(...values, 0);
  if (!rows.length || max === 0) return <p className="text-sm text-slate-500">{emptyText}</p>;
  return (
    <ul className="space-y-2" role="list">
      {rows.map((r) => {
        const pct = r.value ? Math.max(2, (r.value / max) * 100) : 0;
        const text = `${r.label}: ${r.value ?? "–"}${unit}${r.hint ? ` (${r.hint})` : ""}`;
        return (
          <li key={r.label} title={text} className="group grid grid-cols-[8rem_1fr_4rem] items-center gap-2 text-sm">
            <span className="truncate text-slate-700">{r.label}</span>
            <span className="h-3 rounded-r-[4px] bg-slate-100">
              <span className="block h-3 rounded-r-[4px] bg-[#2a78d6] transition-opacity group-hover:opacity-80" style={{ width: `${pct}%` }} />
            </span>
            <span className="text-right tabular-nums text-slate-900">{r.value ?? "–"}{unit}</span>
          </li>
        );
      })}
    </ul>
  );
}
