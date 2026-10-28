import { requireUser } from "@/server/auth/current";
import { action, str } from "@/server/actions";
import { env } from "@/server/env";
import { llmStatus } from "@/server/ai/llm";
import { connectInstagram, disconnectInstagram, instagramIntegration } from "@/server/integrations/instagram/service";
import { transcriptionAvailable } from "@/server/media/transcribe";
import { enqueue } from "@/server/jobs/queue";
import { formatDateTime } from "@/lib/time";
import { Badge, Button, Card, Field, Flash, inputCls, PageHeader } from "@/components/ui";

async function connect(fd: FormData) {
  "use server";
  await action("/settings/integrations", "integrations.manage", async ({ actor }) => {
    const me = await connectInstagram(actor, str(fd, "token"));
    return `Verbunden mit @${me.username}.`;
  });
}

async function disconnect() {
  "use server";
  await action("/settings/integrations", "integrations.manage", async ({ actor }) => {
    await disconnectInstagram(actor);
    return "Verbindung getrennt, Token gelöscht.";
  });
}

async function syncNow() {
  "use server";
  await action("/settings/integrations", "integrations.manage", async ({ user }) => {
    await enqueue("instagram.sync_insights", {}, { createdBy: user.id, maxAttempts: 1 });
    return "Insights-Synchronisation gestartet.";
  });
}

function Row({ label, ok, children }: { label: string; ok: boolean; children: React.ReactNode }) {
  return (
    <div className="flex items-start justify-between gap-4 border-b border-slate-100 py-3 last:border-0">
      <div>
        <div className="text-sm font-medium">{label}</div>
        <div className="text-xs text-slate-600">{children}</div>
      </div>
      <Badge color={ok ? "green" : "amber"}>{ok ? "bereit" : "offen"}</Badge>
    </div>
  );
}

export default async function IntegrationsPage({ searchParams }: { searchParams: Promise<{ ok?: string; err?: string }> }) {
  await requireUser("integrations.manage");
  const sp = await searchParams;
  const e = env();
  const llm = llmStatus();
  const ig = await instagramIntegration();
  const connected = ig?.status === "connected";

  return (
    <>
      <PageHeader title="Integrationen" subtitle="Status aller externen Verbindungen. Nichts wird simuliert: nicht verbundene Dienste sind als offen markiert." />
      <Flash ok={sp.ok} err={sp.err} />
      <div className="grid gap-6 lg:grid-cols-2">
        <Card title="Systemstatus">
          <Row label={`Claude (${llm.model})`} ok={llm.provider === "anthropic" && llm.configured}>
            {llm.provider === "mock" ? "Mock-Modus aktiv (LLM_PROVIDER=mock)." : llm.configured ? `Effort: ${e.ANTHROPIC_EFFORT}. Server-seitiger Fallback bei Ablehnungen aktiv.` : "ANTHROPIC_API_KEY fehlt."}
          </Row>
          <Row label="Research-Websuche" ok={e.RESEARCH_WEB_SEARCH}>{e.RESEARCH_WEB_SEARCH ? "Aktiv – Quellen werden mit URL gespeichert." : "Aus (RESEARCH_WEB_SEARCH=false). Recherche nutzt interne Quellen."}</Row>
          <Row label={`Medienspeicher (${e.STORAGE_DRIVER})`} ok={e.STORAGE_DRIVER === "s3"}>
            {e.STORAGE_DRIVER === "s3" ? `Bucket ${e.S3_BUCKET}` : `Lokal: ${e.STORAGE_LOCAL_DIR}. Für API-Publishing S3-kompatiblen Speicher konfigurieren.`}
          </Row>
          <Row label="FFmpeg" ok>Rendering lokal über {e.FFMPEG_PATH}.</Row>
          <Row label="Automatische Transkription (whisper.cpp)" ok={transcriptionAvailable()}>
            {transcriptionAvailable() ? "Eingerichtet." : "Nicht eingerichtet – Untertitel aus Skript oder SRT-Upload."}
          </Row>
          <Row label="API-Publishing" ok={e.INSTAGRAM_PUBLISHING_ENABLED && connected}>
            {e.INSTAGRAM_PUBLISHING_ENABLED ? "Aktiviert (nur freigegebene Inhalte)." : "Deaktiviert (INSTAGRAM_PUBLISHING_ENABLED=false) – Veröffentlichung als dokumentierter manueller Schritt."}
          </Row>
          <Row label="Rechtstexte" ok={!!e.PRIVACY_URL && !!e.IMPRINT_URL}>PRIVACY_URL / IMPRINT_URL für die Bewerbungsformulare.</Row>
        </Card>
        <Card title="Instagram (offizielle Instagram Platform API)">
          {connected ? (
            <div className="space-y-3 text-sm">
              <p>
                Verbunden: <b>@{String(ig!.config.username)}</b> ({String(ig!.config.accountType ?? "")}) seit {formatDateTime(String(ig!.config.connectedAt))}
              </p>
              <div className="flex gap-2">
                <form action={syncNow}><Button variant="secondary">Insights jetzt synchronisieren</Button></form>
                <form action={disconnect}><Button variant="danger">Trennen</Button></form>
              </div>
            </div>
          ) : (
            <form action={connect} className="space-y-3 text-sm">
              <p className="text-slate-600">
                Voraussetzungen: Instagram Business- oder Creator-Konto, Meta-App mit „Instagram API with Instagram Login“, Berechtigungen{" "}
                <code>instagram_business_basic</code>, <code>instagram_business_content_publish</code>, <code>instagram_business_manage_insights</code>.
                Langlebigen Token im Meta-App-Dashboard erzeugen und hier einfügen. Er wird geprüft und verschlüsselt gespeichert.
              </p>
              <Field label="Access Token"><input name="token" type="password" required autoComplete="off" className={inputCls} /></Field>
              <Button>Prüfen & verbinden</Button>
            </form>
          )}
          {ig?.lastError ? <p className="mt-2 text-xs text-red-700">{ig.lastError}</p> : null}
        </Card>
      </div>
    </>
  );
}
