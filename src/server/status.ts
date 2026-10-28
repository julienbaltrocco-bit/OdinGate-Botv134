import { env } from "@/server/env";
import { llmStatus } from "@/server/ai/llm";
import { instagramIntegration } from "@/server/integrations/instagram/service";
import { transcriptionAvailable } from "@/server/media/transcribe";

export type Blocker = { key: string; severity: "blocker" | "info"; title: string; detail: string; href?: string };

/** Lists missing access / infrastructure decisions. Shown on the dashboard and in docs/BLOCKERS.md. */
export async function systemBlockers(): Promise<Blocker[]> {
  const e = env();
  const out: Blocker[] = [];
  const llm = llmStatus();
  if (llm.provider === "mock") {
    out.push({ key: "llm_mock", severity: "blocker", title: "KI im Mock-Modus", detail: "LLM_PROVIDER=mock: Alle Texte sind [MOCK]-Platzhalter. Für echte Inhalte ANTHROPIC_API_KEY setzen und LLM_PROVIDER=anthropic." });
  } else if (!llm.configured) {
    out.push({ key: "llm_key", severity: "blocker", title: "Anthropic API-Key fehlt", detail: "Ohne ANTHROPIC_API_KEY können keine Themen, Pläne oder Skripte generiert werden." });
  }
  const ig = await instagramIntegration();
  if (!ig || ig.status !== "connected") {
    out.push({ key: "ig", severity: "info", title: "Instagram nicht verbunden", detail: "Veröffentlichung erfolgt als manueller Schritt. Für API-Publishing: Instagram-Business/Creator-Konto + Meta-App + Token.", href: "/settings/integrations" });
  }
  if (!e.INSTAGRAM_PUBLISHING_ENABLED) {
    out.push({ key: "ig_pub", severity: "info", title: "API-Publishing deaktiviert", detail: "INSTAGRAM_PUBLISHING_ENABLED=false – bewusst, bis Freigabe-Prozess und Meta-Zugang bestätigt sind." });
  }
  if (e.STORAGE_DRIVER !== "s3") {
    out.push({ key: "storage", severity: "info", title: "Lokaler Medienspeicher", detail: "Für Instagram-Publishing (Medien per öffentlicher URL) wird S3-kompatibler Speicher benötigt." });
  }
  if (!transcriptionAvailable()) {
    out.push({ key: "whisper", severity: "info", title: "Automatische Transkription nicht eingerichtet", detail: "Untertitel aus Skript oder SRT-Upload funktionieren. Für Transkription whisper.cpp installieren." });
  }
  if (!e.PRIVACY_URL) {
    out.push({ key: "privacy", severity: "blocker", title: "Datenschutzerklärung fehlt", detail: "PRIVACY_URL setzen, bevor Bewerbungsformulare öffentlich verlinkt werden (DSGVO)." });
  }
  return out;
}
