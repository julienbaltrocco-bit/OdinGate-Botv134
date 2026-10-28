"use client";

import { useRouter } from "next/navigation";
import { useEffect } from "react";

/** Refreshes server data while background jobs are running. */
export function AutoRefresh({ active, intervalMs = 3000 }: { active: boolean; intervalMs?: number }) {
  const router = useRouter();
  useEffect(() => {
    if (!active) return;
    const id = setInterval(() => router.refresh(), intervalMs);
    return () => clearInterval(id);
  }, [active, intervalMs, router]);
  if (!active) return null;
  return (
    <div className="mb-4 flex items-center gap-2 rounded-lg border border-blue-200 bg-blue-50 px-4 py-2 text-sm text-blue-800">
      <span className="h-2 w-2 animate-pulse rounded-full bg-blue-500" />
      Hintergrund-Jobs laufen – die Ansicht aktualisiert sich automatisch.
    </div>
  );
}
