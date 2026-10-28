import Link from "next/link";

const TABS = [
  ["/settings", "Brand Voice"],
  ["/settings/users", "Team & Rollen"],
  ["/settings/integrations", "Integrationen"],
  ["/settings/api", "CRM-API & Webhooks"],
  ["/settings/audit", "Audit-Log"],
];

export default function SettingsLayout({ children }: { children: React.ReactNode }) {
  return (
    <>
      <nav className="mb-6 flex flex-wrap gap-2 border-b border-slate-200 pb-3 text-sm">
        {TABS.map(([href, label]) => (
          <Link key={href} href={href} className="rounded-lg px-3 py-1.5 text-slate-700 hover:bg-white">
            {label}
          </Link>
        ))}
      </nav>
      {children}
    </>
  );
}
