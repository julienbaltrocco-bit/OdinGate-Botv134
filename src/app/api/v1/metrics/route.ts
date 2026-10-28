import { apiHandler } from "@/server/integrations/crm/http";
import { funnelStats, itemPerformance } from "@/server/analytics/metrics";

/** GET /api/v1/metrics – per-item performance + lead funnel (last 90 days). */
export const GET = apiHandler("metrics:read", async () => {
  const [items, funnel] = await Promise.all([itemPerformance(90), funnelStats()]);
  return Response.json({ data: { items, funnel } });
});
