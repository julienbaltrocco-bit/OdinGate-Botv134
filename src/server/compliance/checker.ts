import type { ComplianceFinding, ComplianceReport } from "@/server/db/schema";

/**
 * Deterministic pre-publication checks. This is a safety net, not legal advice:
 * findings are shown in the review screen, `block` findings prevent approval,
 * and trading/financial content is routed to a compliance sign-off.
 */

type Rule = {
  id: string;
  severity: ComplianceFinding["severity"];
  pattern: RegExp;
  message: string;
  /** Matching this rule routes the item to compliance review. */
  compliance?: boolean;
};

const RULES: Rule[] = [
  {
    id: "guaranteed_returns",
    severity: "block",
    pattern: /\b(garantiert\w*|garantie\w*|risikofrei\w*|ohne (jedes )?risiko|sichere[rnm]? (gewinn|rendite|profit)\w*|guaranteed|risk[- ]free)\b/i,
    message: "Garantie- oder Risikofrei-Versprechen sind unzulässig.",
    compliance: true,
  },
  {
    id: "return_promise",
    severity: "block",
    pattern: /\b\d+([.,]\d+)?\s?%\s*(rendite|gewinn|profit|return|roi)?\s*(pro|im|am|per|\/)\s*(tag|woche|monat|jahr|day|week|month)\b/i,
    message: "Konkrete Rendite-Aussagen pro Zeitraum sind nicht zulässig.",
    compliance: true,
  },
  {
    id: "income_promise",
    severity: "block",
    pattern: /\b(passive[sn]? einkommen|schnell reich|get rich|finanzielle freiheit in \d+)/i,
    message: "Einkommensversprechen an die Zielgruppe sind unzulässig. Eigene Ergebnisse nur belegt und ohne Übertragbarkeitsversprechen nennen.",
    compliance: true,
  },
  {
    id: "money_figure",
    severity: "warn",
    pattern: /(\d[\d.,]*\s?(k|tsd\.?|mio\.?)?\s?(€|eur\b|euro|\$|usd|usdt))|((€|\$)\s?\d)/i,
    message: "Geldbetrag erwähnt: Nur mit Beleg verwenden (keine erfundenen oder geschönten Zahlen).",
  },
  {
    id: "trading_content",
    severity: "info",
    pattern:
      /\b(trading(?![- ]?(communit\w*|gruppe\w*|discord|telegram|kan(al|äle)|influencer\w*|creator\w*|volum\w*))|trade[ns]?|signal(e|gruppe\w*|s)?|hebel|leverage|long-?position|short-?position|altcoin\w*|memecoin\w*|futures|kursziel|price target|take[- ]profit|stop[- ]loss)\b/i,
    message: "Trading-Bezug erkannt: fachliche/regulatorische Prüfung erforderlich (keine Anlageberatung).",
    compliance: true,
  },
  {
    id: "exchange_mention",
    severity: "info",
    pattern: /\b(binance|bybit|bitget|okx|mexc|kucoin|bingx|blofin|htx|gate\.io|weex|phemex|ref[- ]?link|referral[- ]?link|partnerlink)\b/i,
    message: "Konkrete Börse / Ref-Link erwähnt: Werbe-/Affiliate-Interesse kennzeichnen.",
    compliance: true,
  },
  {
    id: "business_interest",
    severity: "info",
    pattern: /\b(affiliate|rev(enue)?[- ]?share|provision\w*|override\w*)\b/i,
    message: "Eigenes wirtschaftliches Interesse im Thema: bei Empfehlungen Interessenkonflikt offenlegen.",
  },
  {
    id: "testimonial",
    severity: "warn",
    pattern: /\b(kunde|kundin|teilnehmer\w*|schüler\w*|coachee|client)\b[^.!?\n]{0,50}\b(hat|haben|verdient|macht|made|earned)\b[^.!?\n]{0,40}\d/i,
    message: "Testimonial mit Zahl: nur echte, belegte Fälle mit Einwilligung verwenden.",
  },
  {
    id: "hype",
    severity: "warn",
    pattern: /\b(to the moon|100x|1000x|lambo\w*|nur noch heute|letzte chance|einmalige chance|explodier\w*)\b/i,
    message: "Hype-/Druck-Formulierung widerspricht der Brand Voice.",
  },
  {
    id: "luxury_props",
    severity: "warn",
    pattern: /\b(rolex|privatjet|private jet|ferrari|lamborghini|penthouse)\b/i,
    message: "Luxus-Inszenierung vermeiden (Brand-Vorgabe: kein künstlicher Luxus).",
  },
];

// Extended_Pictographic covers emoji; exclude plain digits/symbols like # and *.
const EMOJI = /\p{Extended_Pictographic}/u;
const AUDIENCE = /\b(du|dir|dich|ihr|euch|you)\b/i;
const EARN = /\b(verdien\w*|earn\w*|kassier\w*|einnahmen|einkommen|umsatz machen)\b/i;
const AMOUNT = /\d|€|\$/;
const DISCLOSURE = /\b(werbung|anzeige|affiliate|partnerlink|provisionslink|\*?werbelink|kooperation|eigeninteresse|interessenkonflikt|ad\b)/i;
const RISK_NOTE = /\b(keine (anlage|finanz)beratung|not financial advice|risiko(hinweis)?|totalverlust|verlustrisiko)\b/i;

export type ComplianceInput = { text: string; caption: string; disclosureText?: string };

export function checkCompliance({ text, caption, disclosureText }: ComplianceInput): ComplianceReport {
  const all = `${text}\n${caption}`;
  const findings: ComplianceFinding[] = [];
  let requiresComplianceReview = false;
  const hit = new Set<string>();

  for (const rule of RULES) {
    const m = all.match(rule.pattern);
    if (!m) continue;
    hit.add(rule.id);
    if (rule.compliance) requiresComplianceReview = true;
    findings.push({ rule: rule.id, severity: rule.severity, message: rule.message, excerpt: excerpt(all, m.index ?? 0) });
  }

  // Sentence-level: addressing the audience + earning verb + an amount = income promise.
  if (!hit.has("income_promise")) {
    for (const sentence of all.split(/(?<=[.!?\n])\s*/)) {
      if (AUDIENCE.test(sentence) && EARN.test(sentence) && AMOUNT.test(sentence)) {
        hit.add("income_promise");
        requiresComplianceReview = true;
        findings.push({
          rule: "income_promise",
          severity: "block",
          message: "Einkommensversprechen an die Zielgruppe sind unzulässig. Eigene Ergebnisse nur belegt und ohne Übertragbarkeitsversprechen nennen.",
          excerpt: sentence.trim().slice(0, 100),
        });
        break;
      }
    }
  }

  if (EMOJI.test(all)) {
    findings.push({ rule: "emoji", severity: "warn", message: "Emojis gefunden: Brand Voice sieht möglichst keine Emojis vor." });
  }

  if (hit.has("exchange_mention")) {
    const disclosed = DISCLOSURE.test(caption) || (!!disclosureText && caption.includes(disclosureText.trim()));
    if (!disclosed) {
      findings.push({
        rule: "missing_disclosure",
        severity: "block",
        message: "Börsen-/Affiliate-Bezug ohne Kennzeichnung in der Caption (z.B. 'Werbung' / Hinweis auf Provision).",
      });
    }
  }

  if (hit.has("trading_content") && !RISK_NOTE.test(all)) {
    findings.push({
      rule: "missing_risk_note",
      severity: "warn",
      message: "Trading-Bezug ohne Risikohinweis ('Keine Anlageberatung', Verlustrisiko).",
    });
  }

  return {
    findings,
    requiresComplianceReview,
    blocking: findings.some((f) => f.severity === "block"),
    checkedAt: new Date().toISOString(),
  };
}

function excerpt(text: string, index: number): string {
  const start = Math.max(0, index - 30);
  return text.slice(start, index + 70).replace(/\s+/g, " ").trim();
}
