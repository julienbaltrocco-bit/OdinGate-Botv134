import { cookies } from "next/headers";
import { redirect } from "next/navigation";
import { count, eq } from "drizzle-orm";
import { requireUser, SESSION_COOKIE } from "@/server/auth/current";
import { deleteSession } from "@/server/auth/sessions";
import { can, ROLE_LABELS } from "@/server/auth/rbac";
import { llmStatus } from "@/server/ai/llm";
import { db, schema } from "@/server/db";
import { Nav, type NavItem } from "@/components/nav";

export const dynamic = "force-dynamic";

async function logout() {
  "use server";
  const jar = await cookies();
  const token = jar.get(SESSION_COOKIE)?.value;
  if (token) await deleteSession(token);
  jar.delete(SESSION_COOKIE);
  redirect("/login");
}

export default async function AppLayout({ children }: { children: React.ReactNode }) {
  const user = await requireUser();
  const [{ value: inReview }] = await db().select({ value: count() }).from(schema.contentItems).where(eq(schema.contentItems.status, "in_review"));
  const [{ value: newLeads }] = can(user.role, "leads.read")
    ? await db().select({ value: count() }).from(schema.leads).where(eq(schema.leads.stage, "new"))
    : [{ value: 0 }];
  const llm = llmStatus();

  const items: NavItem[] = [
    { href: "/", label: "Übersicht" },
    { href: "/calendar", label: "Redaktionskalender" },
    { href: "/ideas", label: "Ideen & Recherche" },
    { href: "/review", label: "Freigaben", badge: inReview },
    { href: "/media", label: "Medienbibliothek" },
    ...(can(user.role, "leads.read") ? [{ href: "/leads", label: "Leads & Links", badge: newLeads }] : []),
    { href: "/analytics", label: "Analytics" },
    { href: "/insights", label: "KI-Empfehlungen" },
    { href: "/jobs", label: "Jobs & Agenten" },
    { href: "/settings", label: "Einstellungen" },
  ];

  return (
    <div className="flex min-h-screen">
      <aside className="sticky top-0 hidden h-screen w-60 shrink-0 flex-col bg-slate-900 p-4 md:flex">
        <div className="mb-6 px-3">
          <div className="text-sm font-semibold text-white">Content Engine</div>
          <div className="text-xs text-slate-400">Personal Brand · Growth</div>
        </div>
        <Nav items={items} />
        <div className="mt-auto space-y-2 border-t border-slate-800 px-3 pt-4 text-xs text-slate-400">
          <div className="truncate text-slate-200">{user.name}</div>
          <div>{ROLE_LABELS[user.role]}</div>
          <form action={logout}>
            <button className="text-slate-300 underline-offset-2 hover:underline">Abmelden</button>
          </form>
        </div>
      </aside>
      <div className="min-w-0 flex-1">
        {llm.provider === "mock" ? (
          <div className="bg-amber-500 px-4 py-1.5 text-center text-xs font-semibold text-amber-950">
            KI-Mock-Modus aktiv – generierte Inhalte sind gekennzeichnete Platzhalter, keine echten Claude-Ausgaben.
          </div>
        ) : null}
        <div className="border-b border-slate-200 bg-white px-4 py-2 md:hidden">
          <details>
            <summary className="cursor-pointer text-sm font-medium">Menü</summary>
            <div className="mt-2 rounded-lg bg-slate-900 p-2">
              <Nav items={items} />
            </div>
          </details>
        </div>
        <main className="mx-auto max-w-7xl p-4 md:p-8">{children}</main>
      </div>
    </div>
  );
}
