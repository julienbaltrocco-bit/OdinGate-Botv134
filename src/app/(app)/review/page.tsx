import Link from "next/link";
import { desc, eq, inArray } from "drizzle-orm";
import { requireUser } from "@/server/auth/current";
import { can } from "@/server/auth/rbac";
import { db, schema } from "@/server/db";
import { formatDateTime } from "@/lib/time";
import { FORMAT_LABELS, type Format } from "@/lib/content-types";
import { Badge, Card, Empty, PageHeader, StatusBadge, Table } from "@/components/ui";

export default async function ReviewPage() {
  const user = await requireUser("content.read");
  const queue = await db()
    .select({ item: schema.contentItems, version: schema.contentVersions })
    .from(schema.contentItems)
    .leftJoin(schema.contentVersions, eq(schema.contentVersions.id, schema.contentItems.currentVersionId))
    .where(inArray(schema.contentItems.status, ["in_review", "changes_requested"]))
    .orderBy(schema.contentItems.scheduledAt);
  const recent = await db()
    .select({ a: schema.approvals, title: schema.contentItems.title, name: schema.users.name })
    .from(schema.approvals)
    .innerJoin(schema.contentItems, eq(schema.contentItems.id, schema.approvals.itemId))
    .innerJoin(schema.users, eq(schema.users.id, schema.approvals.reviewerId))
    .orderBy(desc(schema.approvals.createdAt))
    .limit(30);

  return (
    <>
      <PageHeader
        title="Freigaben"
        subtitle={can(user.role, "content.approve") ? "Inhalte prüfen, freigeben, ablehnen oder Änderungen anfragen" : "Status der eingereichten Inhalte"}
      />
      <Card title={`Offen (${queue.length})`} className="mb-6">
        {queue.length ? (
          <Table head={["Inhalt", "Format", "Geplant", "Status", "Prüfung"]}>
            {queue.map(({ item, version }) => (
              <tr key={item.id}>
                <td className="px-2 py-2"><Link href={`/content/${item.id}`} className="font-medium hover:underline">{item.title}</Link></td>
                <td className="px-2 py-2">{FORMAT_LABELS[item.format as Format]}</td>
                <td className="px-2 py-2 text-xs">{formatDateTime(item.scheduledAt)}</td>
                <td className="px-2 py-2"><StatusBadge status={item.status} /></td>
                <td className="space-x-1 px-2 py-2">
                  {item.requiresComplianceReview ? <Badge color="violet">Compliance</Badge> : null}
                  {version?.compliance?.blocking ? <Badge color="red">blockiert</Badge> : null}
                  {version?.compliance?.findings.some((f) => f.severity === "warn") ? <Badge color="amber">Hinweise</Badge> : null}
                </td>
              </tr>
            ))}
          </Table>
        ) : (
          <Empty>Keine offenen Freigaben.</Empty>
        )}
      </Card>
      <Card title="Dokumentierte Entscheidungen">
        {recent.length ? (
          <Table head={["Zeit", "Inhalt", "Entscheidung", "Prüfer", "Kommentar"]}>
            {recent.map(({ a, title, name }) => (
              <tr key={a.id}>
                <td className="px-2 py-2 text-xs">{formatDateTime(a.createdAt)}</td>
                <td className="px-2 py-2"><Link href={`/content/${a.itemId}`} className="hover:underline">{title}</Link></td>
                <td className="px-2 py-2"><Badge color={a.decision === "approved" ? "green" : a.decision === "rejected" ? "red" : "amber"}>{a.decision}</Badge>{a.complianceAck ? " ✓ Compliance" : ""}</td>
                <td className="px-2 py-2 text-xs">{name} ({a.reviewerRole})</td>
                <td className="px-2 py-2 text-xs text-slate-600">{a.comment}</td>
              </tr>
            ))}
          </Table>
        ) : (
          <Empty>Noch keine Entscheidungen.</Empty>
        )}
      </Card>
    </>
  );
}
