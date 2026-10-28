import { and, desc, eq, inArray } from "drizzle-orm";
import { requireUser } from "@/server/auth/current";
import { can } from "@/server/auth/rbac";
import { action, str } from "@/server/actions";
import { db, schema } from "@/server/db";
import { getBrand } from "@/server/brand";
import { audit } from "@/server/audit";
import { enqueue } from "@/server/jobs/queue";
import type { BrandSettings } from "@/server/db/schema";
import { formatDateTime } from "@/lib/time";
import { AutoRefresh } from "@/components/auto-refresh";
import { Button, Card, Field, Flash, inputCls, PageHeader } from "@/components/ui";

const lines = (s: string) => s.split("\n").map((l) => l.trim()).filter(Boolean);
const hex = (s: string, fallback: string) => (/^#[0-9a-fA-F]{6}$/.test(s) ? s : fallback);

async function saveBrand(fd: FormData) {
  "use server";
  await action("/settings", "brand.edit", async ({ actor }) => {
    const brand = await getBrand();
    const prev = brand.settings;
    const next: BrandSettings = {
      ...prev,
      personName: str(fd, "personName"),
      handle: str(fd, "handle").replace(/^@/, ""),
      language: str(fd, "language") === "en" ? "en" : "de",
      positioning: str(fd, "positioning"),
      voiceRules: lines(str(fd, "voiceRules")),
      bannedPhrases: lines(str(fd, "bannedPhrases")),
      examples: str(fd, "examples").split(/\n-{3,}\n/).map((e) => e.trim()).filter(Boolean),
      offers: prev.offers.map((o, i) => ({ ...o, description: str(fd, `offer_${i}_description`) || o.description, price: str(fd, `offer_${i}_price`) || o.price, cta: str(fd, `offer_${i}_cta`) || o.cta })),
      disclosures: { affiliate: str(fd, "discAffiliate"), advertising: str(fd, "discAdvertising"), risk: str(fd, "discRisk") },
      colors: {
        background: hex(str(fd, "cBackground"), prev.colors.background),
        foreground: hex(str(fd, "cForeground"), prev.colors.foreground),
        accent: hex(str(fd, "cAccent"), prev.colors.accent),
        muted: hex(str(fd, "cMuted"), prev.colors.muted),
      },
    };
    await db().update(schema.brandProfile).set({ settings: next, updatedAt: new Date() }).where(eq(schema.brandProfile.id, 1));
    await audit(actor, "brand.updated", "brand_profile", "1");
    return "Brand-Profil gespeichert.";
  });
}

async function derive() {
  "use server";
  await action("/settings", "brand.edit", async ({ user }) => {
    await enqueue("brand.derive", {}, { createdBy: user.id, maxAttempts: 1 });
    return "Brand Voice Agent analysiert freigegebene Texte …";
  });
}

export default async function BrandSettingsPage({ searchParams }: { searchParams: Promise<{ ok?: string; err?: string }> }) {
  const user = await requireUser("content.read");
  const sp = await searchParams;
  const brand = await getBrand();
  const b = brand.settings;
  const editable = can(user.role, "brand.edit");
  const [running, lastDerive] = await Promise.all([
    db().select({ id: schema.jobs.id }).from(schema.jobs).where(and(eq(schema.jobs.type, "brand.derive"), inArray(schema.jobs.status, ["queued", "running"]))),
    db().select().from(schema.jobs).where(eq(schema.jobs.type, "brand.derive")).orderBy(desc(schema.jobs.createdAt)).limit(1),
  ]);

  return (
    <>
      <PageHeader title="Brand Voice & Positionierung" subtitle="Grundlage für alle Schreib-Agenten" />
      <Flash ok={sp.ok} err={sp.err} />
      <AutoRefresh active={running.length > 0} />
      <div className="grid gap-6 xl:grid-cols-3">
        <form action={saveBrand} className="space-y-6 xl:col-span-2">
          <fieldset disabled={!editable} className="space-y-6">
            <Card title="Person & Positionierung">
              <div className="grid gap-3 md:grid-cols-3">
                <Field label="Name"><input name="personName" defaultValue={b.personName} className={inputCls} /></Field>
                <Field label="Instagram-Handle"><input name="handle" defaultValue={b.handle} className={inputCls} /></Field>
                <Field label="Sprache">
                  <select name="language" defaultValue={b.language} className={inputCls}><option value="de">Deutsch</option><option value="en">Englisch</option></select>
                </Field>
                <div className="md:col-span-3"><Field label="Positionierung"><textarea name="positioning" rows={3} defaultValue={b.positioning} className={inputCls} /></Field></div>
              </div>
            </Card>
            <Card title="Angebote">
              <div className="space-y-4">
                {b.offers.map((o, i) => (
                  <div key={i} className="grid gap-2 md:grid-cols-3">
                    <div className="text-sm font-medium md:col-span-3">{o.name}</div>
                    <div className="md:col-span-3"><textarea name={`offer_${i}_description`} rows={2} defaultValue={o.description} className={inputCls} /></div>
                    <input name={`offer_${i}_price`} defaultValue={o.price ?? ""} placeholder="Preis" className={inputCls} />
                    <input name={`offer_${i}_cta`} defaultValue={o.cta} placeholder="CTA" className={`${inputCls} md:col-span-2`} />
                  </div>
                ))}
              </div>
            </Card>
            <Card title="Stilregeln">
              <div className="grid gap-3 md:grid-cols-2">
                <Field label="Regeln (eine pro Zeile)"><textarea name="voiceRules" rows={7} defaultValue={b.voiceRules.join("\n")} className={inputCls} /></Field>
                <Field label="Verbotene Formulierungen (eine pro Zeile)"><textarea name="bannedPhrases" rows={7} defaultValue={b.bannedPhrases.join("\n")} className={inputCls} /></Field>
                <div className="md:col-span-2">
                  <Field label="Eigene Beispieltexte (getrennt durch eine Zeile mit ---)" hint="Captions, Skripte, Sprachnachrichten-Transkripte. Je mehr echte Texte, desto natürlicher der Stil.">
                    <textarea name="examples" rows={8} defaultValue={b.examples.join("\n---\n")} className={inputCls} />
                  </Field>
                </div>
              </div>
            </Card>
            <Card title="Pflichtangaben & Design">
              <div className="grid gap-3 md:grid-cols-2">
                <Field label="Affiliate-/Börsen-Kennzeichnung"><input name="discAffiliate" defaultValue={b.disclosures.affiliate} className={inputCls} /></Field>
                <Field label="Werbekennzeichnung"><input name="discAdvertising" defaultValue={b.disclosures.advertising} className={inputCls} /></Field>
                <div className="md:col-span-2"><Field label="Risikohinweis"><input name="discRisk" defaultValue={b.disclosures.risk} className={inputCls} /></Field></div>
                {(["background", "foreground", "accent", "muted"] as const).map((k) => (
                  <Field key={k} label={`Farbe ${k}`}>
                    <input name={`c${k[0].toUpperCase()}${k.slice(1)}`} type="color" defaultValue={b.colors[k]} className="h-9 w-20 rounded border border-slate-300" />
                  </Field>
                ))}
              </div>
            </Card>
            {editable ? <Button>Speichern</Button> : null}
          </fieldset>
        </form>
        <Card title="Abgeleiteter Stil (Brand Voice Agent)">
          {brand.derivedStyleGuide ? (
            <>
              <pre className="whitespace-pre-wrap text-xs text-slate-700">{brand.derivedStyleGuide}</pre>
              <p className="mt-2 text-xs text-slate-400">Stand: {formatDateTime(brand.derivedAt)}</p>
            </>
          ) : (
            <p className="text-sm text-slate-500">Noch nicht abgeleitet. Benötigt mindestens 3 freigegebene Texte oder eigene Beispiele.</p>
          )}
          {lastDerive[0]?.status === "failed" ? <p className="mt-2 text-xs text-amber-700">{lastDerive[0].lastError}</p> : null}
          {editable ? (
            <form action={derive} className="mt-3">
              <Button variant="secondary">Stil aus freigegebenen Texten ableiten</Button>
            </form>
          ) : null}
        </Card>
      </div>
    </>
  );
}
