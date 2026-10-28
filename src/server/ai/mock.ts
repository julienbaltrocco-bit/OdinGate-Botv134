/**
 * Deterministic placeholder output for LLM_PROVIDER=mock (tests, UI demos
 * without API key). Every text is prefixed with [MOCK] and every agent run is
 * stored with provider "mock", so mock content can never be mistaken for real
 * generated content. The dashboard shows a permanent banner in this mode.
 */

const M = "[MOCK]";

export function mockOutput(agent: string, prompt: string): unknown {
  switch (agent) {
    case "research":
      return {
        topics: Array.from({ length: 6 }, (_, i) => ({
          title: `${M} Thema ${i + 1}: Warum KOL-Partnerschaften an Abrechnungstransparenz scheitern`,
          angle: `${M} Blickwinkel ${i + 1}`,
          pillar: (["authority", "education", "behind_the_scenes", "personal", "conversion", "education"] as const)[i],
          audience: (["b2b_partner", "coaching", "both", "coaching", "b2b_partner", "both"] as const)[i],
          priority: 80 - i * 5,
          rationale: `${M} Abgeleitet aus Quellen`,
          sourceRefs: prompt.includes("[S1]") ? ["S1"] : ["fachwissen"],
        })),
      };
    case "strategy": {
      const topicIds = [...prompt.matchAll(/id=([0-9a-f-]{36})/g)].map((m) => m[1]);
      const pillars = ["authority", "education", "behind_the_scenes", "personal", "conversion"] as const;
      const post = (day: number, time: string, i: number) => ({
        day,
        time,
        title: `${M} Beitrag ${i + 1}`,
        brief: `${M} Briefing ${i + 1}`,
        pillar: pillars[i % pillars.length],
        audience: i % 2 ? "coaching" : "b2b_partner",
        topicId: topicIds[i] ?? "",
        ctaGoal: i === 4 ? "coaching_application" : i === 3 ? "partner_inquiry" : "save",
      });
      return {
        strategySummary: `${M} Wochenstrategie: Vertrauen aufbauen, am Donnerstag Conversion.`,
        reels: [0, 1, 2, 3, 4].map((d, i) => post(d, "18:00", i)),
        carousels: [1, 3].map((d, i) => post(d, "12:00", i + 5)),
        storyDays: [0, 1, 2, 3, 4, 5, 6].map((d) => ({
          day: d,
          theme: `${M} Story-Tag ${d + 1}`,
          brief: `${M} Einblick in den Arbeitstag`,
          linkFocus: d === 3 ? "coaching" : "none",
        })),
      };
    }
    case "scriptwriter":
      return {
        hook: `${M} Die meisten KOL-Deals scheitern nicht am Preis.`,
        onScreenHook: `${M} Daran scheitern KOL-Deals`,
        segments: [
          { label: "Hook", spoken: `${M} Die meisten KOL-Deals scheitern nicht am Preis.`, onScreenText: "", visual: "Talking Head", durationSec: 3 },
          { label: "Kontext", spoken: `${M} Sie scheitern daran, dass niemand die Abrechnung versteht.`, onScreenText: "Abrechnung", visual: "Laptop", durationSec: 5 },
          { label: "Beispiel", spoken: `${M} Letzte Woche hatte ich genau so einen Fall im Call.`, onScreenText: "", visual: "B-Roll Call", durationSec: 5 },
          { label: "CTA", spoken: `${M} Wenn du das sauber aufsetzen willst, Link in Bio.`, onScreenText: "Link in Bio", visual: "Talking Head", durationSec: 4 },
        ],
        cta: `${M} Bewerbung über den Link in Bio`,
        ctaType: "coaching_application",
        targetDurationSec: 17,
        caption: `${M} Caption mit Mehrwert und CTA.`,
        hashtags: ["cryptobusiness", "kolmarketing"],
        claimsToVerify: [],
      };
    case "creative_director":
      return {
        concept: `${M} Ruhiger Talking Head im Büro`,
        shotlist: [{ shot: "A", description: `${M} Talking Head`, framing: "Halbnah", notes: "" }],
        rawMaterialNeeded: [`${M} 1x Talking Head 20s`],
        editingNotes: [`${M} Schnitte auf Satzenden`],
        broll: [`${M} Laptop-Detail`],
        musicMood: "ruhig",
        designNotes: `${M} Brand-Farben`,
        manualSteps: [`${M} Dreh durch Kunden`],
      };
    case "carousel":
      return {
        slides: [
          { kind: "cover", headline: `${M} 5 Fehler bei Börsen-Partnerschaften`, body: "" },
          ...[1, 2, 3, 4, 5].map((i) => ({ kind: "content", headline: `${M} Fehler ${i}`, body: `${M} Erklärung zu Fehler ${i}.` })),
          { kind: "cta", headline: `${M} Speichern und teilen`, body: `${M} Mehr dazu im Profil.` },
        ],
        caption: `${M} Carousel-Caption.`,
        hashtags: ["cryptobusiness"],
        designNotes: `${M} Klar und ruhig`,
        ctaType: "save",
        claimsToVerify: [],
      };
    case "story":
      return {
        dayTheme: `${M} Arbeitstag`,
        frames: [
          { type: "behind_scenes", text: `${M} Heute: drei Partner-Calls`, interactive: "", visualNote: "Schreibtisch", usesTrackingLink: false },
          { type: "poll", text: `${M} Wie verhandelt ihr Konditionen?`, interactive: "Selbst / Agentur", visualNote: "Text", usesTrackingLink: false },
          { type: "text", text: `${M} Learning des Tages`, interactive: "", visualNote: "Notizbuch", usesTrackingLink: false },
        ],
        claimsToVerify: [],
      };
    case "brand_voice":
      return {
        summary: `${M} Direkt, sachlich, praxisnah.`,
        toneTraits: ["direkt"],
        sentenceStyle: "kurz",
        vocabularyToUse: ["Struktur"],
        vocabularyToAvoid: ["Hype"],
        hookPatterns: ["Die meisten ... scheitern an ..."],
        ctaPatterns: ["Link in Bio"],
      };
    case "optimization":
      return {
        recommendations: [
          { category: "hook", title: `${M} Hooks mit konkretem Fehler`, body: `${M} Mehr Fehler-Hooks testen`, evidence: `${M} Höhere Saves`, confidence: "low" },
        ],
      };
    default:
      throw new Error(`Kein Mock für Agent "${agent}"`);
  }
}
