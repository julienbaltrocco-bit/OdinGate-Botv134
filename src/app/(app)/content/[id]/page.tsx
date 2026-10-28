import Link from "next/link";
import { notFound } from "next/navigation";
import { and, desc, eq, inArray, isNull, ne, or } from "drizzle-orm";
import { requireUser } from "@/server/auth/current";
import { can } from "@/server/auth/rbac";
import { db, schema } from "@/server/db";
import { linkUrl } from "@/server/leads/links";
import { transcriptionAvailable } from "@/server/media/transcribe";
import { canAutoPublish } from "@/server/workflow/content";
import { localIsoDate, localTime, formatDateTime } from "@/lib/time";
import {
  AUDIENCE_LABELS,
  AUDIENCES,
  CTA_TYPES,
  FORMAT_LABELS,
  PILLAR_LABELS,
  PILLARS,
  type CarouselBody,
  type Format,
  type ReelBody,
  type StorySet,
} from "@/lib/content-types";
import { FRAME_TYPES } from "@/server/workflow/forms";
import { AutoRefresh } from "@/components/auto-refresh";
import { Badge, Button, Card, Field, Flash, inputCls, PageHeader, StatusBadge } from "@/components/ui";
import {
  addMetrics,
  publishedManually,
  regenerate,
  renderItem,
  review,
  saveContent,
  saveMeta,
  scheduleItem,
  submit,
  unscheduleItem,
  withdraw,
} from "./actions";

export default async function ContentPage({
  params,
  searchParams,
}: {
  params: Promise<{ id: string }>;
  searchParams: Promise<{ ok?: string; err?: string; v?: string }>;
}) {
  const user = await requireUser("content.read");
  const { id } = await params;
  const sp = await searchParams;
  if (!/^[0-9a-f-]{36}$/.test(id)) notFound();
  const [item] = await db().select().from(schema.contentItems).where(eq(schema.contentItems.id, id));
  if (!item) notFound();

  const [versions, approvals, renders, jobs, link, metrics] = await Promise.all([
    db().select().from(schema.contentVersions).where(eq(schema.contentVersions.itemId, id)).orderBy(desc(schema.contentVersions.version)),
    db()
      .select({ a: schema.approvals, name: schema.users.name })
      .from(schema.approvals)
      .innerJoin(schema.users, eq(schema.users.id, schema.approvals.reviewerId))
      .where(eq(schema.approvals.itemId, id))
      .orderBy(desc(schema.approvals.createdAt)),
    db().select().from(schema.renders).where(eq(schema.renders.itemId, id)).orderBy(desc(schema.renders.createdAt)).limit(6),
    db()
      .select()
      .from(schema.jobs)
      .where(and(inArray(schema.jobs.status, ["queued", "running"]), or(eq(schema.jobs.type, "item.draft"), eq(schema.jobs.type, "render.reel"), eq(schema.jobs.type, "render.carousel")))),
    item.trackingLinkId ? db().select().from(schema.trackingLinks).where(eq(schema.trackingLinks.id, item.trackingLinkId)) : Promise.resolve([]),
    db().select().from(schema.postMetrics).where(eq(schema.postMetrics.itemId, id)).orderBy(desc(schema.postMetrics.capturedAt)).limit(5),
  ]);
  const myJobs = jobs.filter((j) => (j.payload as { itemId?: string }).itemId === id || renders.some((r) => r.id === (j.payload as { renderId?: string }).renderId));
  const current = versions.find((v) => v.id === item.currentVersionId) ?? null;
  const shown = (sp.v ? versions.find((v) => String(v.version) === sp.v) : null) ?? current;
  const body = (shown?.body ?? {}) as Record<string, unknown>;
  const format = item.format as Format;
  const editable = can(user.role, "content.edit") && !["published", "publishing"].includes(item.status);
  const renderOutputs = renders.flatMap((r) => r.outputAssetIds);
  const outputAssets = renderOutputs.length
    ? await db().select().from(schema.mediaAssets).where(inArray(schema.mediaAssets.id, renderOutputs))
    : [];
  const assetById = new Map(outputAssets.map((a) => [a.id, a]));
  const library =
    format === "reel" && can(user.role, "media.write")
      ? await db()
          .select()
          .from(schema.mediaAssets)
          .where(and(isNull(schema.mediaAssets.renderId), ne(schema.mediaAssets.kind, "slide")))
          .orderBy(desc(schema.mediaAssets.createdAt))
          .limit(100)
      : [];
  const autoPublish = await canAutoPublish();
  const latestApproval = approvals[0]?.a;
  const approvedCurrent = latestApproval?.decision === "approved" && latestApproval.versionId === item.currentVersionId;

  return (
    <>
      <PageHeader
        title={item.title}
        subtitle={
          <span className="flex flex-wrap items-center gap-2">
            <Badge>{FORMAT_LABELS[format]}</Badge>
            <StatusBadge status={item.status} />
            {item.requiresComplianceReview ? <Badge color="violet">Compliance-Prüfung nötig</Badge> : null}
            <span>{PILLAR_LABELS[item.pillar as keyof typeof PILLAR_LABELS]}</span>·<span>{AUDIENCE_LABELS[item.audience as keyof typeof AUDIENCE_LABELS]}</span>·
            <span>{formatDateTime(item.scheduledAt)}</span>
          </span>
        }
        actions={<Link href="/calendar" className="text-sm text-blue-700 hover:underline">← Kalender</Link>}
      />
      <Flash ok={sp.ok} err={sp.err} />
      <AutoRefresh active={myJobs.length > 0} />

      <div className="grid gap-6 xl:grid-cols-5">
        {/* ------------------------------------------------ Editor */}
        <div className="space-y-6 xl:col-span-3">
          {!current ? (
            <Card title="Noch kein Entwurf">
              <p className="mb-3 text-sm text-slate-600">{item.brief || "Kein Briefing."}</p>
              {can(user.role, "content.generate") ? (
                <form action={regenerate}>
                  <input type="hidden" name="itemId" value={item.id} />
                  <Button>KI-Entwurf erstellen</Button>
                </form>
              ) : null}
            </Card>
          ) : (
            <Card
              title={`Inhalt · Version ${shown!.version}${shown!.source === "ai" ? " (KI)" : " (manuell)"}${shown!.id !== current.id ? " – ältere Version" : ""}`}
              actions={shown!.id !== current.id ? <Link className="text-xs text-blue-700 underline" href={`/content/${item.id}`}>Zur aktuellen Version</Link> : null}
            >
              <form action={saveContent} className="space-y-4">
                <input type="hidden" name="itemId" value={item.id} />
                <fieldset disabled={!editable} className="space-y-4">
                  {format === "reel" ? <ReelEditor body={body as Partial<ReelBody>} /> : null}
                  {format === "carousel" ? <CarouselEditor body={body as Partial<CarouselBody>} /> : null}
                  {format === "story" ? <StoryEditor body={body as Partial<StorySet>} /> : null}
                  {format !== "story" ? (
                    <Field label="Caption" hint="Inkl. CTA, Kennzeichnung (Werbung/Provision) und Risikohinweis, falls relevant.">
                      <textarea name="caption" rows={6} defaultValue={shown!.caption} className={inputCls} />
                    </Field>
                  ) : (
                    <input type="hidden" name="caption" value="" />
                  )}
                  {editable ? (
                    <div className="flex flex-wrap gap-2">
                      <Button name="mode" value="form">Als neue Version speichern</Button>
                    </div>
                  ) : null}
                </fieldset>
              </form>
              {editable ? (
                <details className="mt-4">
                  <summary className="cursor-pointer text-xs text-slate-500">Erweitert: Rohdaten (JSON) bearbeiten</summary>
                  <form action={saveContent} className="mt-2 space-y-2">
                    <input type="hidden" name="itemId" value={item.id} />
                    <input type="hidden" name="caption" value={shown!.caption} />
                    <textarea name="json" rows={14} defaultValue={JSON.stringify(body, null, 2)} className={`${inputCls} font-mono text-xs`} />
                    <Button variant="secondary" name="mode" value="json">JSON speichern</Button>
                  </form>
                </details>
              ) : null}
            </Card>
          )}

          {current && format === "reel" && (body as Partial<ReelBody>).production ? <ProductionBriefView body={body as ReelBody} /> : null}

          <Card title="Vorschau & Rendering">
            <RenderSection
              item={item}
              renders={renders}
              assetById={assetById}
              library={library}
              hookDefault={(body as Partial<ReelBody>).onScreenHook ?? ""}
              canRender={can(user.role, "media.write") && !!current}
              whisper={transcriptionAvailable()}
            />
          </Card>
        </div>

        {/* ------------------------------------------------ Side panel */}
        <div className="space-y-6 xl:col-span-2">
          <Card title="Compliance-Prüfung">
            {shown?.compliance ? (
              shown.compliance.findings.length ? (
                <ul className="space-y-2 text-sm">
                  {shown.compliance.findings.map((f, i) => (
                    <li key={i}>
                      <Badge color={f.severity === "block" ? "red" : f.severity === "warn" ? "amber" : "blue"}>
                        {f.severity === "block" ? "blockiert" : f.severity === "warn" ? "prüfen" : "Hinweis"}
                      </Badge>{" "}
                      {f.message}
                      {f.excerpt ? <div className="mt-0.5 text-xs italic text-slate-500">„…{f.excerpt}…“</div> : null}
                    </li>
                  ))}
                </ul>
              ) : (
                <p className="text-sm text-emerald-700">Keine automatischen Befunde. Menschliche Prüfung bleibt erforderlich.</p>
              )
            ) : (
              <p className="text-sm text-slate-500">Noch kein Entwurf.</p>
            )}
            {((body as { claimsToVerify?: string[] }).claimsToVerify ?? []).length ? (
              <div className="mt-3 rounded-lg bg-amber-50 p-2 text-xs text-amber-900">
                <div className="font-semibold">Vor Veröffentlichung belegen:</div>
                <ul className="list-disc pl-4">
                  {((body as { claimsToVerify?: string[] }).claimsToVerify ?? []).map((c, i) => <li key={i}>{c}</li>)}
                </ul>
              </div>
            ) : null}
          </Card>

          <Card title="Freigabe">
            <WorkflowPanel
              item={item}
              userRole={user.role}
              hasDraft={!!current}
              blocking={!!current?.compliance?.blocking}
              approvedCurrent={approvedCurrent}
              autoPublish={autoPublish}
            />
          </Card>

          {can(user.role, "content.generate") && current && editable ? (
            <Card title="Neu generieren">
              <form action={regenerate} className="space-y-2">
                <input type="hidden" name="itemId" value={item.id} />
                <textarea name="feedback" rows={3} placeholder="Feedback an die KI, z.B. 'Hook konkreter, Beispiel aus Partner-Call ergänzen'" className={inputCls} />
                <Button variant="secondary">Neue KI-Version erzeugen</Button>
              </form>
              <p className="mt-2 text-xs text-slate-500">Das letzte Reviewer-Feedback wird automatisch übernommen.</p>
            </Card>
          ) : null}

          {editable ? (
            <Card title="Planung & Metadaten">
              <form action={saveMeta} className="space-y-3">
                <input type="hidden" name="itemId" value={item.id} />
                <Field label="Titel"><input name="title" defaultValue={item.title} className={inputCls} /></Field>
                <Field label="Briefing"><textarea name="brief" rows={3} defaultValue={item.brief} className={inputCls} /></Field>
                <div className="grid grid-cols-2 gap-2">
                  <Field label="Säule">
                    <select name="pillar" defaultValue={item.pillar} className={inputCls}>{PILLARS.map((p) => <option key={p} value={p}>{PILLAR_LABELS[p]}</option>)}</select>
                  </Field>
                  <Field label="Zielgruppe">
                    <select name="audience" defaultValue={item.audience} className={inputCls}>{AUDIENCES.map((a) => <option key={a} value={a}>{AUDIENCE_LABELS[a]}</option>)}</select>
                  </Field>
                  <Field label="Datum"><input type="date" name="date" defaultValue={item.scheduledAt ? localIsoDate(item.scheduledAt) : ""} className={inputCls} /></Field>
                  <Field label="Uhrzeit"><input type="time" name="time" defaultValue={localTime(item.scheduledAt) || "18:00"} className={inputCls} /></Field>
                </div>
                <Button variant="secondary">Speichern</Button>
              </form>
            </Card>
          ) : null}

          <Card title="Attribution">
            {link[0] ? (
              <div className="space-y-1 text-sm">
                <div>Tracking-Link ({link[0].placement}):</div>
                <code className="block break-all rounded bg-slate-100 px-2 py-1 text-xs">{linkUrl(link[0].code)}</code>
                <p className="text-xs text-slate-500">Im Link-in-Bio bzw. Story-Link-Sticker verwenden. Anfragen über diesen Link werden diesem Inhalt zugeordnet.</p>
              </div>
            ) : (
              <p className="text-sm text-slate-500">Kein Conversion-CTA → kein Tracking-Link. Unter „Leads & Links“ manuell anlegbar.</p>
            )}
          </Card>

          {item.status === "published" ? (
            <Card title="Messwerte">
              {metrics.length ? (
                <ul className="mb-3 space-y-1 text-xs">
                  {metrics.map((m) => (
                    <li key={m.id}>
                      {formatDateTime(m.capturedAt)} ({m.source}): Views {m.views ?? "–"}, Reach {m.reach ?? "–"}, Saves {m.saves ?? "–"}, Shares {m.shares ?? "–"}, Profilbesuche {m.profileVisits ?? "–"}
                    </li>
                  ))}
                </ul>
              ) : null}
              {can(user.role, "analytics.write") ? (
                <form action={addMetrics} className="grid grid-cols-2 gap-2">
                  <input type="hidden" name="itemId" value={item.id} />
                  {[
                    ["views", "Views"],
                    ["reach", "Reichweite"],
                    ["likes", "Likes"],
                    ["comments", "Kommentare"],
                    ["saves", "Saves"],
                    ["shares", "Shares"],
                    ["profileVisits", "Profilbesuche"],
                    ["follows", "Follows"],
                    ["avgWatchTimeSec", "Ø Watchtime (s)"],
                    ["dmInquiries", "DM-Anfragen"],
                  ].map(([k, l]) => (
                    <Field key={k} label={l}><input name={k} inputMode="decimal" className={inputCls} /></Field>
                  ))}
                  <div className="col-span-2"><Button variant="secondary">Manuell erfassen</Button></div>
                </form>
              ) : null}
            </Card>
          ) : null}

          <Card title="Versionen & Entscheidungen">
            <ul className="space-y-1 text-xs">
              {versions.map((v) => (
                <li key={v.id} className="flex items-center justify-between gap-2">
                  <Link href={`/content/${item.id}?v=${v.version}`} className="text-blue-700 hover:underline">
                    v{v.version} · {v.source === "ai" ? "KI" : "manuell"}
                  </Link>
                  <span className="text-slate-500">{formatDateTime(v.createdAt)}</span>
                </li>
              ))}
            </ul>
            {approvals.length ? (
              <ul className="mt-3 space-y-2 border-t border-slate-100 pt-3 text-xs">
                {approvals.map(({ a, name }) => (
                  <li key={a.id}>
                    <Badge color={a.decision === "approved" ? "green" : a.decision === "rejected" ? "red" : "amber"}>{a.decision}</Badge>{" "}
                    v{versions.find((v) => v.id === a.versionId)?.version} · {name} ({a.reviewerRole}) · {formatDateTime(a.createdAt)}
                    {a.complianceAck ? " · Compliance bestätigt" : ""}
                    {a.comment ? <div className="text-slate-600">„{a.comment}“</div> : null}
                  </li>
                ))}
              </ul>
            ) : null}
          </Card>
        </div>
      </div>
    </>
  );
}

// ---------------------------------------------------------------------------

function ReelEditor({ body }: { body: Partial<ReelBody> }) {
  const segments = [...(body.segments ?? []), { label: "", spoken: "", onScreenText: "", visual: "", durationSec: 3 }];
  return (
    <>
      <div className="grid gap-3 md:grid-cols-2">
        <Field label="Hook (gesprochen, 0–3 s)"><textarea name="hook" rows={2} defaultValue={body.hook ?? ""} className={inputCls} /></Field>
        <Field label="Hook-Overlay (max. 8 Wörter)"><input name="onScreenHook" defaultValue={body.onScreenHook ?? ""} className={inputCls} /></Field>
      </div>
      <div className="space-y-2">
        <div className="text-sm font-medium text-slate-700">Skript-Abschnitte</div>
        {segments.map((s, i) => (
          <div key={i} className="grid gap-2 rounded-lg border border-slate-200 p-2 md:grid-cols-12">
            <input name={`seg_${i}_label`} defaultValue={s.label} placeholder="Abschnitt" className={`${inputCls} md:col-span-2`} />
            <textarea name={`seg_${i}_spoken`} defaultValue={s.spoken} placeholder={i === segments.length - 1 ? "Neuer Abschnitt …" : "Gesprochener Text"} rows={2} className={`${inputCls} md:col-span-5`} />
            <input name={`seg_${i}_onScreenText`} defaultValue={s.onScreenText} placeholder="Overlay" className={`${inputCls} md:col-span-2`} />
            <input name={`seg_${i}_visual`} defaultValue={s.visual} placeholder="Bild" className={`${inputCls} md:col-span-2`} />
            <input name={`seg_${i}_durationSec`} defaultValue={s.durationSec} type="number" step="0.5" min={0.5} className={`${inputCls} md:col-span-1`} title="Sekunden" />
          </div>
        ))}
      </div>
      <div className="grid gap-3 md:grid-cols-3">
        <div className="md:col-span-2"><Field label="CTA"><input name="cta" defaultValue={body.cta ?? ""} className={inputCls} /></Field></div>
        <Field label="CTA-Typ">
          <select name="ctaType" defaultValue={body.ctaType ?? "none"} className={inputCls}>{CTA_TYPES.map((c) => <option key={c} value={c}>{c}</option>)}</select>
        </Field>
      </div>
      <Field label="Zu belegende Aussagen (eine pro Zeile)">
        <textarea name="claimsToVerify" rows={2} defaultValue={(body.claimsToVerify ?? []).join("\n")} className={inputCls} />
      </Field>
    </>
  );
}

function CarouselEditor({ body }: { body: Partial<CarouselBody> }) {
  const slides = [...(body.slides ?? []), { kind: "content" as const, headline: "", body: "" }];
  return (
    <>
      <div className="space-y-2">
        {slides.map((s, i) => (
          <div key={i} className="grid gap-2 rounded-lg border border-slate-200 p-2 md:grid-cols-12">
            <div className="text-xs font-semibold text-slate-500 md:col-span-1">{i + 1}</div>
            <select name={`slide_${i}_kind`} defaultValue={s.kind} className={`${inputCls} md:col-span-3`}>
              <option value="cover">Cover</option>
              <option value="content">Inhalt</option>
              <option value="cta">CTA</option>
            </select>
            <input name={`slide_${i}_headline`} defaultValue={s.headline} placeholder={i === slides.length - 1 ? "Neue Slide …" : "Headline"} className={`${inputCls} md:col-span-8`} />
            <textarea name={`slide_${i}_body`} defaultValue={s.body} rows={2} placeholder="Text" className={`${inputCls} md:col-span-12`} />
          </div>
        ))}
      </div>
      <Field label="Design-Hinweise"><input name="designNotes" defaultValue={body.designNotes ?? ""} className={inputCls} /></Field>
      <Field label="Zu belegende Aussagen (eine pro Zeile)">
        <textarea name="claimsToVerify" rows={2} defaultValue={(body.claimsToVerify ?? []).join("\n")} className={inputCls} />
      </Field>
    </>
  );
}

function StoryEditor({ body }: { body: Partial<StorySet> }) {
  const frames = [...(body.frames ?? []), { type: "text" as const, text: "", interactive: "", visualNote: "", usesTrackingLink: false }];
  return (
    <>
      <Field label="Tagesthema"><input name="dayTheme" defaultValue={body.dayTheme ?? ""} className={inputCls} /></Field>
      <div className="space-y-2">
        {frames.map((f, i) => (
          <div key={i} className="grid gap-2 rounded-lg border border-slate-200 p-2 md:grid-cols-12">
            <select name={`frame_${i}_type`} defaultValue={f.type} className={`${inputCls} md:col-span-3`}>
              {FRAME_TYPES.map((t) => <option key={t} value={t}>{t}</option>)}
            </select>
            <input name={`frame_${i}_text`} defaultValue={f.text} placeholder={i === frames.length - 1 ? "Neuer Frame …" : "Text"} className={`${inputCls} md:col-span-9`} />
            <input name={`frame_${i}_interactive`} defaultValue={f.interactive} placeholder="Sticker (z.B. Umfrage-Optionen)" className={`${inputCls} md:col-span-5`} />
            <input name={`frame_${i}_visualNote`} defaultValue={f.visualNote} placeholder="Visual" className={`${inputCls} md:col-span-5`} />
            <label className="flex items-center gap-1 text-xs md:col-span-2"><input type="checkbox" name={`frame_${i}_usesTrackingLink`} defaultChecked={f.usesTrackingLink} /> Link</label>
          </div>
        ))}
      </div>
      <p className="text-xs text-slate-500">Stories werden manuell aufgenommen und gepostet (interaktive Sticker sind über die API nicht verfügbar). Die gerenderten Frames dienen als Vorlage.</p>
    </>
  );
}

function ProductionBriefView({ body }: { body: ReelBody }) {
  const p = body.production!;
  return (
    <Card title="Produktionsbriefing (Creative Director)">
      <div className="space-y-3 text-sm">
        <p>{p.concept}</p>
        <div>
          <div className="font-medium">Benötigtes Rohmaterial</div>
          <ul className="list-disc pl-5 text-slate-700">{p.rawMaterialNeeded.map((r, i) => <li key={i}>{r}</li>)}</ul>
        </div>
        <div>
          <div className="font-medium">Shotlist</div>
          <ul className="list-disc pl-5 text-slate-700">
            {p.shotlist.map((s, i) => (
              <li key={i}>
                <b>{s.shot}</b> ({s.framing}): {s.description} {s.notes ? <span className="text-slate-500">– {s.notes}</span> : null}
              </li>
            ))}
          </ul>
        </div>
        <div className="grid gap-3 md:grid-cols-2">
          <div>
            <div className="font-medium">Schnitt</div>
            <ul className="list-disc pl-5 text-slate-700">{p.editingNotes.map((r, i) => <li key={i}>{r}</li>)}</ul>
          </div>
          <div>
            <div className="font-medium">B-Roll · Musik · Design</div>
            <ul className="list-disc pl-5 text-slate-700">
              {p.broll.map((r, i) => <li key={i}>{r}</li>)}
              <li>Musik: {p.musicMood}</li>
              <li>{p.designNotes}</li>
            </ul>
          </div>
        </div>
        {p.manualSteps.length ? (
          <div className="rounded-lg bg-slate-50 p-2 text-xs">
            <b>Manuelle Schritte:</b> {p.manualSteps.join(" · ")}
          </div>
        ) : null}
      </div>
    </Card>
  );
}

type Asset = typeof schema.mediaAssets.$inferSelect;
type Render = typeof schema.renders.$inferSelect;

function RenderSection({
  item,
  renders,
  assetById,
  library,
  hookDefault,
  canRender,
  whisper,
}: {
  item: typeof schema.contentItems.$inferSelect;
  renders: Render[];
  assetById: Map<string, Asset>;
  library: Asset[];
  hookDefault: string;
  canRender: boolean;
  whisper: boolean;
}) {
  const videos = library.filter((a) => a.kind === "video");
  return (
    <div className="space-y-4">
      {renders.length ? (
        <div className="space-y-4">
          {renders.map((r) => {
            const outs = r.outputAssetIds.map((x) => assetById.get(x)).filter((a): a is Asset => !!a);
            return (
              <div key={r.id} className="rounded-lg border border-slate-200 p-3">
                <div className="mb-2 flex items-center justify-between text-xs">
                  <span>
                    {formatDateTime(r.createdAt)} · {r.versionId === item.currentVersionId ? "aktuelle Version" : "ältere Version"}
                  </span>
                  <Badge color={r.status === "succeeded" ? "green" : r.status === "failed" ? "red" : "blue"}>{r.status}</Badge>
                </div>
                {r.error ? <p className="mb-2 text-xs text-red-700">{r.error}</p> : null}
                <div className="flex flex-wrap gap-3">
                  {outs
                    .filter((a) => a.mimeType === "video/mp4")
                    .map((a) => (
                      <figure key={a.id} className="w-48">
                        <video src={`/api/media/${a.id}`} controls preload="metadata" className="aspect-[9/16] w-full rounded-lg bg-black" />
                        <figcaption className="mt-1 text-xs text-slate-500">
                          {a.filename} · {a.durationSec?.toFixed(1)}s · <a className="underline" href={`/api/media/${a.id}?download=1`}>Download</a>
                        </figcaption>
                      </figure>
                    ))}
                  {outs
                    .filter((a) => a.kind === "slide")
                    .map((a) => (
                      <a key={a.id} href={`/api/media/${a.id}`} target="_blank" rel="noreferrer" className="block w-32">
                        {/* eslint-disable-next-line @next/next/no-img-element */}
                        <img src={`/api/media/${a.id}`} alt={a.filename} className="w-full rounded border border-slate-200" />
                      </a>
                    ))}
                </div>
                {r.log ? (
                  <details className="mt-2">
                    <summary className="cursor-pointer text-xs text-slate-500">Protokoll</summary>
                    <pre className="mt-1 max-h-40 overflow-auto whitespace-pre-wrap rounded bg-slate-50 p-2 text-[11px]">{r.log}</pre>
                  </details>
                ) : null}
              </div>
            );
          })}
        </div>
      ) : (
        <p className="text-sm text-slate-500">Noch kein Rendering.</p>
      )}

      {canRender && item.format !== "reel" ? (
        <form action={renderItem}>
          <input type="hidden" name="itemId" value={item.id} />
          <Button variant="secondary">{item.format === "carousel" ? "Slides rendern (1080×1350)" : "Story-Vorlagen rendern (1080×1920)"}</Button>
        </form>
      ) : null}

      {canRender && item.format === "reel" ? (
        <details className="rounded-lg border border-slate-200 p-3" open={!renders.length}>
          <summary className="cursor-pointer text-sm font-medium">Reel aus Rohmaterial rendern</summary>
          {videos.length ? (
            <form action={renderItem} className="mt-3 space-y-3 text-sm">
              <input type="hidden" name="itemId" value={item.id} />
              <div className="space-y-1">
                <div className="text-xs text-slate-500">Clips auswählen (Reihenfolge, optional Start/Ende in Sekunden). Nur Material mit geklärten Rechten wird gerendert.</div>
                {videos.map((v) => (
                  <div key={v.id} className="flex flex-wrap items-center gap-2 rounded border border-slate-100 p-1.5">
                    <label className="flex min-w-0 flex-1 items-center gap-2">
                      <input type="checkbox" name="clip" value={v.id} />
                      <span className="truncate">{v.filename}</span>
                      <span className="text-xs text-slate-500">{v.durationSec?.toFixed(1)}s</span>
                      {v.rightsStatus === "unknown" ? <Badge color="red">Rechte ungeklärt</Badge> : null}
                    </label>
                    <input name={`order_${v.id}`} placeholder="#" className={`${inputCls} w-12 py-1`} />
                    <input name={`start_${v.id}`} placeholder="Start" className={`${inputCls} w-16 py-1`} />
                    <input name={`end_${v.id}`} placeholder="Ende" className={`${inputCls} w-16 py-1`} />
                  </div>
                ))}
              </div>
              <div className="grid gap-2 md:grid-cols-2">
                <Field label="Untertitel">
                  <select name="subMode" defaultValue="script" className={inputCls}>
                    <option value="script">Aus Skript (Timing geschätzt)</option>
                    <option value="asset">Aus SRT/VTT-Datei</option>
                    <option value="transcribe" disabled={!whisper}>Automatisch transkribieren{whisper ? "" : " (nicht eingerichtet)"}</option>
                    <option value="none">Keine</option>
                  </select>
                </Field>
                <Field label="Untertitel-Datei">
                  <select name="subAsset" className={inputCls}>
                    <option value="">–</option>
                    {library.filter((a) => a.kind === "subtitle").map((a) => <option key={a.id} value={a.id}>{a.filename}</option>)}
                  </select>
                </Field>
                <Field label="Hook-Overlay"><input name="hookText" defaultValue={hookDefault} className={inputCls} /></Field>
                <Field label="CTA-Endkarte"><input name="ctaText" placeholder="z.B. Link in Bio" className={inputCls} /></Field>
                <Field label="Logo">
                  <select name="logo" className={inputCls}>
                    <option value="">–</option>
                    {library.filter((a) => a.kind === "image" || a.kind === "logo").map((a) => <option key={a.id} value={a.id}>{a.filename}</option>)}
                  </select>
                </Field>
                <Field label="Musik (nur lizenziert)">
                  <select name="music" className={inputCls}>
                    <option value="">–</option>
                    {library.filter((a) => a.kind === "audio").map((a) => <option key={a.id} value={a.id}>{a.filename} ({a.rightsStatus})</option>)}
                  </select>
                </Field>
                <Field label="Zusätzliche Kurzvariante (Sekunden)" hint="Leer = nur Hauptvariante">
                  <input name="shortLen" inputMode="numeric" placeholder="z.B. 20" className={inputCls} />
                </Field>
              </div>
              <Button>Rendern</Button>
            </form>
          ) : (
            <p className="mt-2 text-sm text-slate-500">
              Keine Videos in der <Link className="underline" href="/media">Medienbibliothek</Link>. Rohmaterial laut Produktionsbriefing hochladen.
            </p>
          )}
        </details>
      ) : null}
    </div>
  );
}

function WorkflowPanel({
  item,
  userRole,
  hasDraft,
  blocking,
  approvedCurrent,
  autoPublish,
}: {
  item: typeof schema.contentItems.$inferSelect;
  userRole: Parameters<typeof can>[0];
  hasDraft: boolean;
  blocking: boolean;
  approvedCurrent: boolean;
  autoPublish: boolean;
}) {
  const s = item.status;
  return (
    <div className="space-y-4 text-sm">
      {["draft", "changes_requested"].includes(s) && hasDraft && can(userRole, "content.edit") ? (
        <form action={submit}>
          <input type="hidden" name="itemId" value={item.id} />
          <Button>Zur Freigabe einreichen</Button>
        </form>
      ) : null}

      {s === "in_review" ? (
        <>
          {can(userRole, "content.approve") ? (
            <form action={review} className="space-y-2">
              <input type="hidden" name="itemId" value={item.id} />
              <textarea name="comment" rows={3} placeholder="Kommentar (bei Änderungen/Ablehnung Pflicht)" className={inputCls} />
              {item.requiresComplianceReview ? (
                <label className="flex items-start gap-2 rounded-lg bg-violet-50 p-2 text-xs text-violet-900">
                  <input type="checkbox" name="complianceAck" className="mt-0.5" />
                  Ich habe den Inhalt fachlich/regulatorisch geprüft (keine Anlageberatung, keine Rendite-/Einkommensversprechen, Kennzeichnung vorhanden).
                  {!can(userRole, "content.compliance_signoff") ? " – Freigabe nur durch Rolle Compliance/Admin." : ""}
                </label>
              ) : null}
              <div className="flex flex-wrap gap-2">
                <Button name="decision" value="approved" disabled={blocking}>Freigeben</Button>
                <Button name="decision" value="changes_requested" variant="secondary">Änderungen anfragen</Button>
                <Button name="decision" value="rejected" variant="danger">Ablehnen</Button>
              </div>
              {blocking ? <p className="text-xs text-red-700">Freigabe gesperrt: blockierende Compliance-Befunde.</p> : null}
            </form>
          ) : (
            <p className="text-slate-600">Wartet auf Prüfung durch Reviewer.</p>
          )}
          {can(userRole, "content.edit") ? (
            <form action={withdraw}>
              <input type="hidden" name="itemId" value={item.id} />
              <Button variant="ghost">Zurückziehen</Button>
            </form>
          ) : null}
        </>
      ) : null}

      {["approved", "failed", "scheduled"].includes(s) && approvedCurrent && can(userRole, "content.schedule") ? (
        <div className="space-y-3">
          <form action={scheduleItem} className="flex flex-wrap items-end gap-2">
            <input type="hidden" name="itemId" value={item.id} />
            <Field label="Datum"><input type="date" name="date" required defaultValue={item.scheduledAt ? localIsoDate(item.scheduledAt) : ""} className={inputCls} /></Field>
            <Field label="Uhrzeit"><input type="time" name="time" defaultValue={localTime(item.scheduledAt) || "18:00"} className={inputCls} /></Field>
            <Button>{s === "scheduled" ? "Zeit ändern" : "Einplanen"}</Button>
          </form>
          <p className="text-xs text-slate-500">
            {autoPublish && item.format !== "story"
              ? "API-Publishing aktiv: wird zum Zeitpunkt automatisch veröffentlicht."
              : "Manueller Schritt: zum geplanten Zeitpunkt in Instagram posten und hier dokumentieren."}
          </p>
          {s === "scheduled" ? (
            <form action={unscheduleItem}>
              <input type="hidden" name="itemId" value={item.id} />
              <Button variant="ghost">Einplanung entfernen</Button>
            </form>
          ) : null}
          <form action={publishedManually} className="space-y-2 border-t border-slate-100 pt-3">
            <input type="hidden" name="itemId" value={item.id} />
            <Field label="Live-Link des Posts"><input name="permalink" placeholder="https://www.instagram.com/reel/…" className={inputCls} /></Field>
            <Button variant="secondary">Als veröffentlicht markieren</Button>
          </form>
        </div>
      ) : null}

      {s === "failed" && item.lastError ? <p className="text-xs text-red-700">Fehler: {item.lastError}</p> : null}
      {s === "published" ? (
        <p>
          Veröffentlicht {formatDateTime(item.publishedAt)}
          {item.igPermalink ? (
            <>
              {" "}· <a className="text-blue-700 underline" href={item.igPermalink} target="_blank" rel="noreferrer">Post öffnen</a>
            </>
          ) : null}
        </p>
      ) : null}
      {s === "rejected" ? <p className="text-slate-600">Abgelehnt. Neue Version speichern oder neu generieren, um erneut einzureichen.</p> : null}
      {s === "planned" ? <p className="text-slate-600">Noch kein Entwurf.</p> : null}
    </div>
  );
}
