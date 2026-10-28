import { sql } from "drizzle-orm";
import { db } from "@/server/db";
import { createUser } from "@/server/auth/users";
import { SYSTEM_ACTOR } from "@/server/audit";
import type { Principal } from "@/server/workflow/content";
import type { Role } from "@/server/auth/rbac";
import { tick } from "@/server/jobs/worker";

export async function resetDb() {
  await db().execute(sql`
    TRUNCATE users, sessions, audit_logs, brand_profile, research_sources, topics, content_plans, content_items,
      content_versions, approvals, media_assets, renders, jobs, agent_runs, tracking_links, link_clicks, leads,
      api_keys, webhook_endpoints, integrations, post_metrics, recommendations RESTART IDENTITY CASCADE`);
}

let n = 0;
export async function makeUser(role: Role): Promise<Principal> {
  n++;
  const u = await createUser(SYSTEM_ACTOR, { email: `${role}${n}@test.local`, name: `${role} ${n}`, role, password: "test-password-123" });
  return { id: u.id, label: u.email, role };
}

/** Runs queued jobs until the queue is empty (or a limit is hit). */
export async function drainJobs(limit = 100) {
  const log: string[] = [];
  for (let i = 0; i < limit; i++) {
    const handled = await tick({ log: (m) => log.push(m) });
    if (!handled) break;
  }
  return log;
}
