import { and, desc, eq, gte, isNotNull, sql } from "drizzle-orm";
import { db, schema } from "@/server/db";
import { audit, type Actor } from "@/server/audit";

/**
 * Analytics: deterministic aggregation of post metrics (Instagram API or manual
 * entry) joined with attributed leads. Feeds the dashboard and the planning agents.
 */

export type ItemPerformance = {
  itemId: string;
  title: string;
  format: string;
  pillar: string;
  audience: string;
  publishedAt: Date | null;
  hook: string | null;
  views: number | null;
  reach: number | null;
  saves: number | null;
  shares: number | null;
  comments: number | null;
  likes: number | null;
  profileVisits: number | null;
  follows: number | null;
  avgWatchTimeSec: number | null;
  leads: number;
  qualifiedLeads: number;
  wonLeads: number;
  linkClicks: number;
};

export async function itemPerformance(sinceDays = 90): Promise<ItemPerformance[]> {
  const since = new Date(Date.now() - sinceDays * 86400_000);
  const items = await db()
    .select({
      id: schema.contentItems.id,
      title: schema.contentItems.title,
      format: schema.contentItems.format,
      pillar: schema.contentItems.pillar,
      audience: schema.contentItems.audience,
      publishedAt: schema.contentItems.publishedAt,
      body: schema.contentVersions.body,
    })
    .from(schema.contentItems)
    .leftJoin(schema.contentVersions, eq(schema.contentVersions.id, schema.contentItems.currentVersionId))
    .where(and(eq(schema.contentItems.status, "published"), isNotNull(schema.contentItems.publishedAt), gte(schema.contentItems.publishedAt, since)));
  if (!items.length) return [];

  // Latest metric snapshot per item.
  const latest = await db().execute(sql`
    SELECT DISTINCT ON (item_id) item_id, views, reach, saves, shares, comments, likes, profile_visits, follows, avg_watch_time_sec
    FROM post_metrics ORDER BY item_id, captured_at DESC`);
  const metricByItem = new Map((latest.rows as Record<string, unknown>[]).map((r) => [r.item_id as string, r]));

  const leadRows = await db().execute(sql`
    SELECT source_item_id AS item_id,
      count(*)::int AS leads,
      count(*) FILTER (WHERE stage IN ('qualified','call_scheduled','won'))::int AS qualified,
      count(*) FILTER (WHERE stage = 'won')::int AS won
    FROM leads WHERE source_item_id IS NOT NULL GROUP BY source_item_id`);
  const leadsByItem = new Map((leadRows.rows as Record<string, unknown>[]).map((r) => [r.item_id as string, r]));

  const clickRows = await db().execute(sql`
    SELECT tl.item_id, count(lc.id)::int AS clicks FROM tracking_links tl
    JOIN link_clicks lc ON lc.link_id = tl.id WHERE tl.item_id IS NOT NULL GROUP BY tl.item_id`);
  const clicksByItem = new Map((clickRows.rows as Record<string, unknown>[]).map((r) => [r.item_id as string, Number(r.clicks)]));

  const num = (v: unknown) => (v === null || v === undefined ? null : Number(v));
  return items.map((i) => {
    const m = metricByItem.get(i.id) ?? {};
    const l = leadsByItem.get(i.id) ?? {};
    const body = (i.body ?? {}) as { hook?: string; slides?: { headline: string }[] };
    return {
      itemId: i.id,
      title: i.title,
      format: i.format,
      pillar: i.pillar,
      audience: i.audience,
      publishedAt: i.publishedAt,
      hook: body.hook ?? body.slides?.[0]?.headline ?? null,
      views: num(m.views),
      reach: num(m.reach),
      saves: num(m.saves),
      shares: num(m.shares),
      comments: num(m.comments),
      likes: num(m.likes),
      profileVisits: num(m.profile_visits),
      follows: num(m.follows),
      avgWatchTimeSec: num(m.avg_watch_time_sec),
      leads: Number(l.leads ?? 0),
      qualifiedLeads: Number(l.qualified ?? 0),
      wonLeads: Number(l.won ?? 0),
      linkClicks: clicksByItem.get(i.id) ?? 0,
    };
  });
}

export type GroupStat = { key: string; posts: number; avgViews: number | null; avgSaves: number | null; leads: number; qualifiedLeads: number };

export function groupBy(rows: ItemPerformance[], key: "format" | "pillar" | "audience"): GroupStat[] {
  const groups = new Map<string, ItemPerformance[]>();
  for (const r of rows) groups.set(r[key], [...(groups.get(r[key]) ?? []), r]);
  const avg = (vals: (number | null)[]) => {
    const v = vals.filter((x): x is number => x !== null);
    return v.length ? Math.round(v.reduce((a, b) => a + b, 0) / v.length) : null;
  };
  return [...groups.entries()]
    .map(([k, rs]) => ({
      key: k,
      posts: rs.length,
      avgViews: avg(rs.map((r) => r.views)),
      avgSaves: avg(rs.map((r) => r.saves)),
      leads: rs.reduce((a, r) => a + r.leads, 0),
      qualifiedLeads: rs.reduce((a, r) => a + r.qualifiedLeads, 0),
    }))
    .sort((a, b) => b.qualifiedLeads - a.qualifiedLeads || (b.avgViews ?? 0) - (a.avgViews ?? 0));
}

/** Compact text for agent prompts. Explicitly states when there is no data yet. */
export async function performanceSummary(): Promise<{ text: string; rows: ItemPerformance[] }> {
  const rows = await itemPerformance(90);
  if (!rows.length) return { text: "Noch keine veröffentlichten Inhalte mit Messwerten. Keine Performance-Schlüsse ziehen.", rows };
  const fmt = (g: GroupStat[]) =>
    g.map((s) => `  - ${s.key}: ${s.posts} Posts, Ø Views ${s.avgViews ?? "n/a"}, Ø Saves ${s.avgSaves ?? "n/a"}, Leads ${s.leads} (qualifiziert ${s.qualifiedLeads})`).join("\n");
  const top = [...rows]
    .sort((a, b) => b.qualifiedLeads - a.qualifiedLeads || (b.views ?? 0) - (a.views ?? 0))
    .slice(0, 8)
    .map((r) => `  - [${r.format}/${r.pillar}] "${r.title}" Hook: "${r.hook ?? "-"}" | Views ${r.views ?? "n/a"}, Saves ${r.saves ?? "n/a"}, Ø Watch ${r.avgWatchTimeSec ?? "n/a"}s, Leads ${r.leads}/${r.qualifiedLeads} qual.`)
    .join("\n");
  return {
    rows,
    text: `Letzte 90 Tage, ${rows.length} veröffentlichte Inhalte.\nNach Format:\n${fmt(groupBy(rows, "format"))}\nNach Säule:\n${fmt(groupBy(rows, "pillar"))}\nNach Zielgruppe:\n${fmt(groupBy(rows, "audience"))}\nTop-Inhalte:\n${top}`,
  };
}

export type ManualMetrics = Partial<{
  views: number;
  reach: number;
  likes: number;
  comments: number;
  saves: number;
  shares: number;
  profileVisits: number;
  follows: number;
  avgWatchTimeSec: number;
  dmInquiries: number;
}>;

export async function recordManualMetrics(actor: Actor, itemId: string, m: ManualMetrics) {
  const [row] = await db()
    .insert(schema.postMetrics)
    .values({ itemId, source: "manual", ...m, enteredBy: actor.id })
    .returning();
  await audit(actor, "metrics.recorded", "content_item", itemId, { source: "manual" });
  return row;
}

export async function funnelStats() {
  const result = await db().execute(sql`
    SELECT type, stage, count(*)::int AS n FROM leads GROUP BY type, stage`);
  const clicks = await db().execute(sql`SELECT count(*)::int AS n FROM link_clicks WHERE created_at > now() - interval '30 days'`);
  const out: Record<string, Record<string, number>> = { coaching: {}, partner: {} };
  for (const r of result.rows as { type: string; stage: string; n: number }[]) out[r.type][r.stage] = r.n;
  return { byType: out, clicks30d: Number((clicks.rows[0] as { n: number }).n) };
}

export async function latestMetrics(itemId: string) {
  return db().select().from(schema.postMetrics).where(eq(schema.postMetrics.itemId, itemId)).orderBy(desc(schema.postMetrics.capturedAt)).limit(10);
}
