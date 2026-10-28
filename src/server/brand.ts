import { eq } from "drizzle-orm";
import { db, schema } from "@/server/db";
import type { BrandSettings } from "@/server/db/schema";

/** Starting profile derived from the briefing. Editable in Settings → Brand. */
export const DEFAULT_BRAND: BrandSettings = {
  personName: "",
  handle: "",
  language: "de",
  positioning:
    "Crypto Business Development: KOL-Akquise, Affiliate-Partnerschaften mit Kryptobörsen, Revenue-Share-Strukturen und Vertriebsaufbau. Teilt echte Prozesse aus dem Geschäftsalltag statt Hype.",
  offers: [
    {
      name: "KOL-Akquise-Coaching",
      description:
        "Monatliches Coaching für angehende KOL-Akquisiteure und Closer: Vertriebsmethodik, Outreach, Verhandlung. Beteiligung an vermittelten Deals nur nach vertraglich festgelegten Bedingungen.",
      price: "500 € / Monat",
      cta: "Bewerbung für ein Erstgespräch",
    },
    {
      name: "Partnerschaften für KOLs & Trading-Communities",
      description: "Vermittlung und Strukturierung von Partnerschaften mit Kryptobörsen (Revenue Share / Overrides).",
      cta: "Partnerschaftsanfrage",
    },
  ],
  audiences: [
    {
      key: "b2b_partner",
      description: "Krypto-Influencer, Trading-Communities, Community-Owner, die Partnerschaften mit Börsen suchen oder optimieren wollen.",
      painPoints: [
        "Intransparente Konditionen und Abrechnungen",
        "Keine Verhandlungsposition gegenüber Börsen",
        "Zu wenig Zeit für Partner-Management",
      ],
    },
    {
      key: "coaching",
      description: "Vertriebsorientierte Menschen, die in Crypto-BD / KOL-Akquise einsteigen oder als Closer arbeiten wollen.",
      painPoints: ["Kein Zugang zu Entscheidern", "Unklare Outreach-Strategie", "Fehlende Abschlusssicherheit"],
    },
  ],
  voiceRules: [
    "Professionell, selbstbewusst, direkt auf den Punkt.",
    "Fachlich fundiert, mit konkreten Beispielen aus der Praxis (anonymisiert).",
    "Natürlich gesprochen, keine generischen KI-Floskeln.",
    "Möglichst keine Emojis.",
    "Keine übertriebenen oder unbelegten Aussagen, keine Einkommens- oder Renditeversprechen.",
    "Kein künstlicher Luxus, keine erfundenen Zahlen oder Testimonials.",
  ],
  bannedPhrases: [
    "In der heutigen schnelllebigen Welt",
    "Lass uns eintauchen",
    "Game-Changer",
    "passives Einkommen",
    "garantiert",
  ],
  examples: [],
  disclosures: {
    affiliate: "Hinweis: Ich arbeite mit Kryptobörsen auf Provisionsbasis zusammen (Werbung).",
    advertising: "Werbung",
    risk: "Keine Anlageberatung. Krypto-Handel ist mit hohem Verlustrisiko verbunden.",
  },
  colors: { background: "#0B0F14", foreground: "#F5F7FA", accent: "#3B82F6", muted: "#94A3B8" },
};

export async function getBrand() {
  const [row] = await db().select().from(schema.brandProfile).where(eq(schema.brandProfile.id, 1)).limit(1);
  if (row) return row;
  const [created] = await db()
    .insert(schema.brandProfile)
    .values({ id: 1, settings: DEFAULT_BRAND })
    .onConflictDoNothing()
    .returning();
  return created ?? (await db().select().from(schema.brandProfile).where(eq(schema.brandProfile.id, 1)))[0];
}

/** Brand context block shared by all writing agents (stable → prompt-cache friendly). */
export function brandContext(settings: BrandSettings, derivedStyleGuide: string | null): string {
  const offers = settings.offers.map((o) => `- ${o.name}${o.price ? ` (${o.price})` : ""}: ${o.description} CTA: ${o.cta}`).join("\n");
  const audiences = settings.audiences
    .map((a) => `- ${a.key}: ${a.description}\n  Pain Points: ${a.painPoints.join("; ")}`)
    .join("\n");
  return [
    `# Marke`,
    settings.personName ? `Person: ${settings.personName}${settings.handle ? ` (@${settings.handle})` : ""}` : "",
    `Positionierung: ${settings.positioning}`,
    `Sprache der Inhalte: ${settings.language === "de" ? "Deutsch" : "Englisch"}`,
    `\n# Angebote\n${offers}`,
    `\n# Zielgruppen\n${audiences}`,
    `\n# Brand Voice (verbindlich)\n${settings.voiceRules.map((r) => `- ${r}`).join("\n")}`,
    settings.bannedPhrases.length ? `Verbotene Formulierungen: ${settings.bannedPhrases.map((p) => `"${p}"`).join(", ")}` : "",
    derivedStyleGuide ? `\n# Abgeleiteter Stil aus freigegebenen Texten\n${derivedStyleGuide}` : "",
    settings.examples.length
      ? `\n# Beispieltexte des Kunden (Stilreferenz, nicht kopieren)\n${settings.examples.map((e, i) => `[${i + 1}] ${e}`).join("\n\n")}`
      : "",
    `\n# Pflichtangaben\n- Affiliate/Börsenbezug: "${settings.disclosures.affiliate}"\n- Werbung: "${settings.disclosures.advertising}"\n- Risiko bei Trading-Bezug: "${settings.disclosures.risk}"`,
  ]
    .filter(Boolean)
    .join("\n");
}

export const CONTENT_GUARDRAILS = `# Harte Regeln
- Keine erfundenen Umsätze, Zahlen, Kunden, Deals oder Testimonials. Wenn eine Zahl hilfreich wäre, nutze einen Platzhalter wie [ZAHL BELEGEN] und liste die Aussage unter claimsToVerify.
- Keine Rendite-, Gewinn- oder Einkommensversprechen; keine Trading-Signale oder Anlageempfehlungen.
- Deal-Strukturen nur anonymisiert und ohne vertrauliche Konditionen.
- Bei Nennung konkreter Börsen oder Ref-Links: Kennzeichnung (Werbung/Provision) in die Caption.
- Bei Trading-Bezug: Risikohinweis in die Caption.
- Keine automatisierten DMs vorschlagen; CTAs führen zu Profil, Link in Bio/Story-Link oder Bewerbungsformular.
- Qualifizierte Leads vor Reichweite: lieber präzise Zielgruppenansprache als Viralität.`;
