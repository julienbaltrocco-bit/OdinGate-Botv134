import { desc, eq } from "drizzle-orm";
import { requireUser } from "@/server/auth/current";
import { db, schema } from "@/server/db";
import { formatDateTime } from "@/lib/time";
import { Card, PageHeader, Table } from "@/components/ui";

export default async function AuditPage({ searchParams }: { searchParams: Promise<{ entity?: string }> }) {
  await requireUser("audit.read");
  const sp = await searchParams;
  const rows = await db()
    .select()
    .from(schema.auditLogs)
    .where(sp.entity ? eq(schema.auditLogs.entityId, sp.entity) : undefined)
    .orderBy(desc(schema.auditLogs.createdAt))
    .limit(300);
  return (
    <>
      <PageHeader title="Audit-Log" subtitle="Unveränderliches Protokoll aller relevanten Aktionen (letzte 300)" />
      <Card>
        <Table head={["Zeit", "Akteur", "Aktion", "Objekt", "Details"]}>
          {rows.map((r) => (
            <tr key={r.id}>
              <td className="whitespace-nowrap px-2 py-1.5 text-xs">{formatDateTime(r.createdAt)}</td>
              <td className="px-2 py-1.5 text-xs">{r.actorLabel}</td>
              <td className="px-2 py-1.5 font-mono text-xs">{r.action}</td>
              <td className="px-2 py-1.5 text-xs">{r.entityType}{r.entityId ? <a className="ml-1 text-blue-700 underline" href={`?entity=${r.entityId}`}>{r.entityId.slice(0, 8)}</a> : null}</td>
              <td className="max-w-md truncate px-2 py-1.5 text-xs text-slate-600" title={JSON.stringify(r.data)}>{JSON.stringify(r.data)}</td>
            </tr>
          ))}
        </Table>
      </Card>
    </>
  );
}
