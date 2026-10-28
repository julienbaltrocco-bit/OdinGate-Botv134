import Link from "next/link";
import { requireUser } from "@/server/auth/current";
import { funnelStats, groupBy, itemPerformance } from "@/server/analytics/metrics";
import { instagramIntegration } from "@/server/integrations/instagram/service";
import { formatDateTime } from "@/lib/time";
import { AUDIENCE_LABELS, FORMAT_LABELS, PILLAR_LABELS, type Audience, type Format, type Pillar } from "@/lib/content-types";
import { BarList } from "@/components/bar-list";
import { Card, Empty, PageHeader, Stat, Table } from "@/components/ui";

const sum = (xs: (number | null)[]) => xs.reduce<number>((a, x) => a + (x ?? 0), 0);

export default async function AnalyticsPage() {
  await requireUser("analytics.read");
  const [rows, funnel, ig] = await Promise.all([itemPerformance(90), funnelStats(), instagramIntegration()]);
  const leads = sum(rows.map((r) => r.leads));
  const qualified = sum(rows.map((r) => r.qualifiedLeads));
  const stages = ["new", "qualified", "call_scheduled", "won"] as const;
  const stageLabel: Record<string, string> = { new: "Neu", qualified: "Qualifiziert", call_scheduled: "Erstgespräch", won: "Abschluss" };
  // Funnel counts are cumulative: a won lead also passed every earlier stage.
  const funnelRows = (type: "coaching" | "partner") =>
    stages.map((s, i) => ({ label: stageLabel[s], value: stages.slice(i).reduce((a, st) => a + (funnel.byType[type][st] ?? 0), 0) }));

  return (
    <>
      <PageHeader
        title="Analytics"
        subtitle={
          ig?.status === "connected"
            ? "Messwerte aus der Instagram-API (tägliche Synchronisation) und manuellen Eingaben · letzte 90 Tage"
            : "Instagram nicht verbunden: Messwerte werden manuell pro Beitrag erfasst · letzte 90 Tage"
        }
      />
      <div className="mb-6 grid grid-cols-2 gap-4 md:grid-cols-3 xl:grid-cols-6">
        <Stat label="Veröffentlicht" value={rows.length} />
        <Stat label="Views" value={sum(rows.map((r) => r.views)).toLocaleString("de-DE")} />
        <Stat label="Saves" value={sum(rows.map((r) => r.saves)).toLocaleString("de-DE")} />
        <Stat label="Profilbesuche" value={sum(rows.map((r) => r.profileVisits)).toLocaleString("de-DE")} hint="nur wo verfügbar/erfasst" />
        <Stat label="Link-Klicks (30 T.)" value={funnel.clicks30d} />
        <Stat label="Leads aus Content" value={leads} hint={`${qualified} qualifiziert`} />
      </div>

      <div className="mb-6 grid gap-6 lg:grid-cols-2">
        <Card title="Coaching-Funnel (alle Leads)">
          <BarList rows={funnelRows("coaching")} emptyText="Noch keine Coaching-Anfragen." />
        </Card>
        <Card title="Partner-Funnel (alle Leads)">
          <BarList rows={funnelRows("partner")} emptyText="Noch keine Partneranfragen." />
        </Card>
        <Card title="Qualifizierte Leads nach Content-Säule">
          <BarList rows={groupBy(rows, "pillar").map((g) => ({ label: PILLAR_LABELS[g.key as Pillar], value: g.qualifiedLeads, hint: `${g.posts} Posts` }))} />
        </Card>
        <Card title="Ø Views nach Format">
          <BarList rows={groupBy(rows, "format").map((g) => ({ label: FORMAT_LABELS[g.key as Format], value: g.avgViews, hint: `${g.posts} Posts` }))} />
        </Card>
      </div>

      <Card title="Beiträge">
        {rows.length ? (
          <Table head={["Beitrag", "Format", "Zielgruppe", "Views", "Reach", "Saves", "Shares", "Ø Watch", "Klicks", "Leads (qual.)"]}>
            {rows
              .sort((a, b) => (b.publishedAt?.getTime() ?? 0) - (a.publishedAt?.getTime() ?? 0))
              .map((r) => (
                <tr key={r.itemId}>
                  <td className="max-w-xs px-2 py-2">
                    <Link className="font-medium hover:underline" href={`/content/${r.itemId}`}>{r.title}</Link>
                    <div className="text-xs text-slate-500">{formatDateTime(r.publishedAt)}</div>
                  </td>
                  <td className="px-2 py-2 text-xs">{FORMAT_LABELS[r.format as Format]}</td>
                  <td className="px-2 py-2 text-xs">{AUDIENCE_LABELS[r.audience as Audience]}</td>
                  <td className="px-2 py-2 tabular-nums">{r.views ?? "–"}</td>
                  <td className="px-2 py-2 tabular-nums">{r.reach ?? "–"}</td>
                  <td className="px-2 py-2 tabular-nums">{r.saves ?? "–"}</td>
                  <td className="px-2 py-2 tabular-nums">{r.shares ?? "–"}</td>
                  <td className="px-2 py-2 tabular-nums">{r.avgWatchTimeSec ? `${r.avgWatchTimeSec.toFixed(1)}s` : "–"}</td>
                  <td className="px-2 py-2 tabular-nums">{r.linkClicks}</td>
                  <td className="px-2 py-2 tabular-nums">{r.leads} ({r.qualifiedLeads})</td>
                </tr>
              ))}
          </Table>
        ) : (
          <Empty>Noch keine veröffentlichten Beiträge. Nach Veröffentlichung Messwerte im Beitrag erfassen oder Instagram verbinden.</Empty>
        )}
      </Card>
    </>
  );
}
