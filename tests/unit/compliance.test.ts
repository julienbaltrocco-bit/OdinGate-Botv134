import { describe, expect, it } from "vitest";
import { checkCompliance } from "@/server/compliance/checker";

const rules = (text: string, caption = "") => checkCompliance({ text, caption, disclosureText: "Werbung" }).findings.map((f) => f.rule);

describe("compliance checker", () => {
  it("blocks guaranteed and periodic return promises", () => {
    const r = checkCompliance({ text: "Garantiert 10% Rendite pro Monat", caption: "" });
    expect(r.blocking).toBe(true);
    expect(r.findings.map((f) => f.rule)).toEqual(expect.arrayContaining(["guaranteed_returns", "return_promise"]));
  });

  it("blocks income promises to the audience", () => {
    expect(rules("Mit meinem System kannst du 10k im Monat verdienen")).toContain("income_promise");
    expect(rules("Passives Einkommen mit Krypto")).toContain("income_promise");
  });

  it("does not flag B2B talk about trading communities as trading advice", () => {
    const r = checkCompliance({ text: "So gewinnst du Trading-Communities als Partner. Verkaufen heißt zuhören.", caption: "" });
    expect(r.requiresComplianceReview).toBe(false);
    expect(r.blocking).toBe(false);
  });

  it("routes real trading content to compliance and asks for a risk note", () => {
    const r = checkCompliance({ text: "Warum ich Signalgruppen mit Hebel meide", caption: "" });
    expect(r.requiresComplianceReview).toBe(true);
    expect(r.findings.map((f) => f.rule)).toContain("missing_risk_note");
    const ok = checkCompliance({ text: "Warum ich Signalgruppen mit Hebel meide", caption: "Keine Anlageberatung." });
    expect(ok.findings.map((f) => f.rule)).not.toContain("missing_risk_note");
  });

  it("requires a disclosure when a specific exchange is named", () => {
    expect(checkCompliance({ text: "Meine Erfahrung mit Bybit", caption: "Mehr im Profil" }).blocking).toBe(true);
    expect(checkCompliance({ text: "Meine Erfahrung mit Bybit", caption: "Werbung: Ich arbeite auf Provisionsbasis." }).blocking).toBe(false);
  });

  it("warns on emojis, money figures and hype", () => {
    expect(rules("Deal abgeschlossen 🚀")).toContain("emoji");
    expect(rules("Ein Deal über 25.000 USD")).toContain("money_figure");
    expect(rules("Dieser Coin geht to the moon")).toContain("hype");
  });

  it("passes clean educational content", () => {
    const r = checkCompliance({ text: "Drei Fragen, die ich in jedem Erstgespräch mit einem KOL stelle.", caption: "Speichern für dein nächstes Gespräch." });
    expect(r.findings).toEqual([]);
  });
});
