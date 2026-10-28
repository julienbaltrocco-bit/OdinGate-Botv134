import { notFound, redirect } from "next/navigation";
import { getBrand } from "@/server/brand";
import { env } from "@/server/env";
import { CONSENT_TEXT, createLead } from "@/server/leads/leads";
import { errorMessage } from "@/server/actions";
import { unstable_rethrow } from "next/navigation";

export const dynamic = "force-dynamic";

async function submitApplication(fd: FormData) {
  "use server";
  const type = String(fd.get("type"));
  const src = String(fd.get("src") ?? "");
  const get = (k: string) => String(fd.get(k) ?? "");
  let target = `/apply/${type}?done=1`;
  try {
    const utm: Record<string, string> = {};
    for (const k of ["utm_source", "utm_medium", "utm_campaign", "utm_content"]) if (get(k)) utm[k] = get(k).slice(0, 100);
    const base = { name: get("name"), email: get("email"), instagramHandle: get("instagramHandle"), message: get("message"), consent: fd.get("consent") === "on", src: src || undefined, utm, website: get("website") };
    await createLead(
      type === "coaching"
        ? { ...base, type, salesExperience: get("salesExperience"), cryptoExperience: get("cryptoExperience"), hoursPerWeek: get("hoursPerWeek"), budgetOk: fd.get("budgetOk") === "on", goal: get("goal") }
        : { ...base, type, company: get("company"), communitySize: get("communitySize"), platforms: get("platforms"), monthlyVolume: get("monthlyVolume"), currentExchangePartner: get("currentExchangePartner") },
    );
  } catch (err) {
    unstable_rethrow(err);
    target = `/apply/${type}?err=${encodeURIComponent(errorMessage(err).slice(0, 200))}${src ? `&src=${encodeURIComponent(src)}` : ""}`;
  }
  redirect(target);
}

const input = "w-full rounded-lg border border-slate-300 px-3 py-2 text-sm";

function Select({ name, label, options }: { name: string; label: string; options: [string, string][] }) {
  return (
    <label className="block text-sm">
      <span className="mb-1 block font-medium">{label}</span>
      <select name={name} required defaultValue="" className={input}>
        <option value="" disabled>Bitte wählen</option>
        {options.map(([v, l]) => <option key={v} value={v}>{l}</option>)}
      </select>
    </label>
  );
}

export default async function ApplyPage({ params, searchParams }: { params: Promise<{ type: string }>; searchParams: Promise<Record<string, string | undefined>> }) {
  const { type } = await params;
  if (type !== "coaching" && type !== "partner") notFound();
  const sp = await searchParams;
  const brand = await getBrand();
  const e = env();
  const offer = brand.settings.offers[type === "coaching" ? 0 : 1];

  if (sp.done) {
    return (
      <main className="mx-auto max-w-xl p-6">
        <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
          <h1 className="text-xl font-semibold">Danke für deine Anfrage.</h1>
          <p className="mt-2 text-sm text-slate-600">Wir melden uns persönlich per E-Mail. Es gibt keine automatisierten Nachrichten.</p>
        </div>
      </main>
    );
  }

  return (
    <main className="mx-auto max-w-xl p-6">
      <form action={submitApplication} className="space-y-4 rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
        <div>
          <h1 className="text-xl font-semibold">{type === "coaching" ? "Bewerbung Coaching" : "Partnerschaftsanfrage"}</h1>
          {offer ? <p className="mt-1 text-sm text-slate-600">{offer.description}{offer.price ? ` (${offer.price})` : ""}</p> : null}
        </div>
        {sp.err ? <p className="rounded-lg bg-red-50 px-3 py-2 text-sm text-red-700">{sp.err}</p> : null}
        <input type="hidden" name="type" value={type} />
        <input type="hidden" name="src" value={sp.src ?? ""} />
        {["utm_source", "utm_medium", "utm_campaign", "utm_content"].map((k) => <input key={k} type="hidden" name={k} value={sp[k] ?? ""} />)}
        {/* Honeypot: hidden from humans */}
        <input type="text" name="website" tabIndex={-1} autoComplete="off" className="hidden" aria-hidden="true" />
        <label className="block text-sm"><span className="mb-1 block font-medium">Name</span><input name="name" required className={input} /></label>
        <label className="block text-sm"><span className="mb-1 block font-medium">E-Mail</span><input name="email" type="email" required className={input} /></label>
        <label className="block text-sm"><span className="mb-1 block font-medium">Instagram (optional)</span><input name="instagramHandle" className={input} placeholder="@handle" /></label>
        {type === "coaching" ? (
          <>
            <Select name="salesExperience" label="Vertriebserfahrung" options={[["none", "Keine"], ["lt1", "Unter 1 Jahr"], ["1to3", "1–3 Jahre"], ["gt3", "Über 3 Jahre"]]} />
            <Select name="cryptoExperience" label="Erfahrung im Krypto-Bereich" options={[["none", "Keine"], ["basic", "Grundlagen"], ["active", "Aktiv im Markt"], ["industry", "Beruflich in der Branche"]]} />
            <Select name="hoursPerWeek" label="Zeit pro Woche" options={[["lt5", "Unter 5 Stunden"], ["5to15", "5–15 Stunden"], ["gt15", "Über 15 Stunden"]]} />
            <label className="flex items-start gap-2 text-sm"><input type="checkbox" name="budgetOk" className="mt-1" /> Die Investition von {offer?.price ?? "500 € / Monat"} ist für mich grundsätzlich möglich.</label>
            <label className="block text-sm"><span className="mb-1 block font-medium">Dein Ziel</span><textarea name="goal" rows={3} className={input} /></label>
            <p className="text-xs text-slate-500">Hinweis: Das Coaching vermittelt Vertriebsmethodik. Es gibt keine Einkommensgarantie; Beteiligungen an Deals nur nach vertraglich festgelegten Bedingungen.</p>
          </>
        ) : (
          <>
            <label className="block text-sm"><span className="mb-1 block font-medium">Community / Firma</span><input name="company" className={input} /></label>
            <Select name="communitySize" label="Größe der Community" options={[["lt1k", "Unter 1.000"], ["1kto10k", "1.000–10.000"], ["10kto50k", "10.000–50.000"], ["gt50k", "Über 50.000"]]} />
            <label className="block text-sm"><span className="mb-1 block font-medium">Plattformen</span><input name="platforms" className={input} placeholder="Telegram, YouTube, Discord …" /></label>
            <Select name="monthlyVolume" label="Monatliches Handelsvolumen der Community (geschätzt)" options={[["unknown", "Unbekannt"], ["lt1m", "Unter 1 Mio. USD"], ["1mto10m", "1–10 Mio. USD"], ["gt10m", "Über 10 Mio. USD"]]} />
            <Select name="currentExchangePartner" label="Bestehende Börsen-Partnerschaft" options={[["none", "Keine"], ["yes_unhappy", "Ja, aber unzufrieden"], ["yes_ok", "Ja, zufrieden"]]} />
          </>
        )}
        <label className="block text-sm"><span className="mb-1 block font-medium">Nachricht (optional)</span><textarea name="message" rows={3} className={input} /></label>
        <label className="flex items-start gap-2 text-xs text-slate-600">
          <input type="checkbox" name="consent" required className="mt-0.5" />
          <span>
            {CONSENT_TEXT}{" "}
            {e.PRIVACY_URL ? <a href={e.PRIVACY_URL} className="underline" target="_blank" rel="noreferrer">Datenschutzerklärung</a> : null}
          </span>
        </label>
        <button className="w-full rounded-lg bg-slate-900 py-2 text-sm font-medium text-white">Absenden</button>
        <div className="flex gap-3 text-xs text-slate-500">
          {e.IMPRINT_URL ? <a href={e.IMPRINT_URL} className="underline">Impressum</a> : null}
          {e.PRIVACY_URL ? <a href={e.PRIVACY_URL} className="underline">Datenschutz</a> : null}
        </div>
      </form>
    </main>
  );
}
