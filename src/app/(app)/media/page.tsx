import Link from "next/link";
import { and, desc, eq, isNotNull, isNull, type SQL } from "drizzle-orm";
import { requireUser } from "@/server/auth/current";
import { can } from "@/server/auth/rbac";
import { action, str } from "@/server/actions";
import { db, schema } from "@/server/db";
import { deleteAsset, updateRights, type RightsStatus } from "@/server/media/assets";
import { formatDateTime } from "@/lib/time";
import { UploadForm } from "@/components/upload-form";
import { Badge, Button, Card, Empty, Flash, inputCls, PageHeader } from "@/components/ui";

async function setRights(fd: FormData) {
  "use server";
  await action("/media", "media.write", async ({ actor }) => {
    await updateRights(actor, str(fd, "id"), str(fd, "rights") as RightsStatus, str(fd, "note"));
    return "Rechte aktualisiert.";
  });
}

async function remove(fd: FormData) {
  "use server";
  await action("/media", "media.write", async ({ actor }) => {
    await deleteAsset(actor, str(fd, "id"));
    return "Gelöscht.";
  });
}

const KINDS = ["video", "image", "audio", "subtitle", "logo", "render", "slide"] as const;

export default async function MediaPage({ searchParams }: { searchParams: Promise<{ kind?: string; generated?: string; ok?: string; err?: string }> }) {
  const user = await requireUser("media.read");
  const sp = await searchParams;
  const conds: SQL[] = [sp.generated ? isNotNull(schema.mediaAssets.itemId) : isNull(schema.mediaAssets.renderId)];
  if (sp.kind && (KINDS as readonly string[]).includes(sp.kind)) conds.push(eq(schema.mediaAssets.kind, sp.kind as (typeof KINDS)[number]));
  const assets = await db().select().from(schema.mediaAssets).where(and(...conds)).orderBy(desc(schema.mediaAssets.createdAt)).limit(120);
  const writable = can(user.role, "media.write");

  return (
    <>
      <PageHeader title="Medienbibliothek" subtitle="Rohmaterial, Logos, Musik, Untertitel und generierte Renderings" />
      <Flash ok={sp.ok} err={sp.err} />
      {writable ? (
        <Card title="Hochladen" className="mb-6">
          <UploadForm />
          <p className="mt-3 text-xs text-slate-500">
            Nur Material mit Nutzungsrechten verwenden. Bei erkennbaren Personen ist deren Einwilligung erforderlich; vertrauliche Bildschirminhalte (Deal-Konditionen, Namen) vorher schwärzen.
          </p>
        </Card>
      ) : null}
      <div className="mb-4 flex flex-wrap gap-2 text-sm">
        <Link href="/media" className={`rounded-full px-3 py-1 ${!sp.kind && !sp.generated ? "bg-slate-900 text-white" : "bg-white"}`}>Uploads</Link>
        {KINDS.slice(0, 5).map((k) => (
          <Link key={k} href={`/media?kind=${k}`} className={`rounded-full px-3 py-1 ${sp.kind === k ? "bg-slate-900 text-white" : "bg-white"}`}>{k}</Link>
        ))}
        <Link href="/media?generated=1" className={`rounded-full px-3 py-1 ${sp.generated ? "bg-slate-900 text-white" : "bg-white"}`}>Generiert</Link>
      </div>
      {assets.length ? (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
          {assets.map((a) => (
            <div key={a.id} className="overflow-hidden rounded-xl border border-slate-200 bg-white shadow-sm">
              <div className="flex aspect-video items-center justify-center bg-slate-100">
                {a.mimeType.startsWith("video/") ? (
                  <video src={`/api/media/${a.id}`} controls preload="metadata" className="h-full w-full object-contain" />
                ) : a.mimeType.startsWith("image/") ? (
                  // eslint-disable-next-line @next/next/no-img-element
                  <img src={`/api/media/${a.id}`} alt={a.filename} className="h-full w-full object-contain" />
                ) : a.mimeType.startsWith("audio/") ? (
                  <audio src={`/api/media/${a.id}`} controls className="w-11/12" />
                ) : (
                  <span className="text-xs text-slate-500">{a.kind}</span>
                )}
              </div>
              <div className="space-y-2 p-3 text-xs">
                <div className="truncate font-medium text-slate-800" title={a.filename}>{a.filename}</div>
                <div className="flex flex-wrap gap-1">
                  <Badge>{a.kind}</Badge>
                  <Badge color={a.rightsStatus === "unknown" ? "red" : "green"}>Rechte: {a.rightsStatus}</Badge>
                  {a.durationSec ? <Badge>{a.durationSec.toFixed(1)}s</Badge> : null}
                  {a.width ? <Badge>{a.width}×{a.height}</Badge> : null}
                </div>
                {a.rightsNote ? <div className="text-slate-500">{a.rightsNote}</div> : null}
                {a.itemId ? <Link href={`/content/${a.itemId}`} className="text-blue-700 underline">Zum Inhalt</Link> : null}
                <div className="text-slate-400">{formatDateTime(a.createdAt)} · {(a.sizeBytes / 1e6).toFixed(1)} MB</div>
                {writable && !a.renderId ? (
                  <form action={setRights} className="flex gap-1">
                    <input type="hidden" name="id" value={a.id} />
                    <select name="rights" defaultValue={a.rightsStatus} className={`${inputCls} py-1 text-xs`}>
                      <option value="own">own</option>
                      <option value="licensed">licensed</option>
                      <option value="unknown">unknown</option>
                    </select>
                    <input name="note" defaultValue={a.rightsNote} placeholder="Notiz" className={`${inputCls} py-1 text-xs`} />
                    <Button variant="secondary">OK</Button>
                  </form>
                ) : null}
                {writable ? (
                  <form action={remove}>
                    <input type="hidden" name="id" value={a.id} />
                    <Button variant="ghost">Löschen</Button>
                  </form>
                ) : null}
              </div>
            </div>
          ))}
        </div>
      ) : (
        <Empty>Keine Medien.</Empty>
      )}
    </>
  );
}
