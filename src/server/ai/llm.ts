import Anthropic from "@anthropic-ai/sdk";
import { betaZodOutputFormat } from "@anthropic-ai/sdk/helpers/beta/zod";
import { eq } from "drizzle-orm";
import type { z } from "zod";
import { db, schema } from "@/server/db";
import { env } from "@/server/env";
import { mockOutput } from "./mock";

/**
 * Single entry point for all agent calls. Every call is recorded in `agent_runs`
 * (input, output, model, usage, duration) so generated content is traceable.
 */

export type Citation = { title: string; url: string };

export type StructuredRequest<T> = {
  agent: string;
  system: string;
  prompt: string;
  schema: z.ZodType<T>;
  /** Stored with the run for traceability (keep it small: ids, not full payloads). */
  meta?: Record<string, unknown>;
};

export type AgentResult<T> = { output: T; runId: string; provider: string; model: string };

export class LlmNotConfiguredError extends Error {
  constructor() {
    super(
      "KI nicht konfiguriert: ANTHROPIC_API_KEY fehlt. Bitte in .env setzen (oder LLM_PROVIDER=mock für einen gekennzeichneten Demo-Modus).",
    );
    this.name = "LlmNotConfiguredError";
  }
}

export class LlmOutputError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "LlmOutputError";
  }
}

export function llmStatus(): { provider: "anthropic" | "mock"; configured: boolean; model: string } {
  const e = env();
  if (e.LLM_PROVIDER === "mock") return { provider: "mock", configured: true, model: "mock" };
  return { provider: "anthropic", configured: !!e.ANTHROPIC_API_KEY, model: e.ANTHROPIC_MODEL };
}

let client: Anthropic | undefined;
function anthropic(): Anthropic {
  const e = env();
  if (!e.ANTHROPIC_API_KEY) throw new LlmNotConfiguredError();
  client ??= new Anthropic({ apiKey: e.ANTHROPIC_API_KEY, maxRetries: 3 });
  return client;
}

async function startRun(agent: string, provider: string, model: string, input: Record<string, unknown>) {
  const [run] = await db()
    .insert(schema.agentRuns)
    .values({ agent, provider, model, input, status: "running" })
    .returning({ id: schema.agentRuns.id });
  return run.id;
}

async function finishRun(
  id: string,
  started: number,
  patch: Partial<typeof schema.agentRuns.$inferInsert>,
) {
  await db()
    .update(schema.agentRuns)
    .set({ ...patch, durationMs: Date.now() - started })
    .where(eq(schema.agentRuns.id, id));
}

export async function generateStructured<T>(req: StructuredRequest<T>): Promise<AgentResult<T>> {
  const status = llmStatus();
  const e = env();
  if (status.provider === "anthropic" && !status.configured) throw new LlmNotConfiguredError();

  const started = Date.now();
  const runId = await startRun(req.agent, status.provider, status.model, {
    ...req.meta,
    promptChars: req.prompt.length,
    prompt: req.prompt.slice(0, 20_000),
  });

  try {
    let output: T;
    let usage: Record<string, unknown> | undefined;
    let servedModel = status.model;

    if (status.provider === "mock") {
      output = req.schema.parse(mockOutput(req.agent, req.prompt));
    } else {
      const stream = anthropic().beta.messages.stream({
        model: e.ANTHROPIC_MODEL,
        max_tokens: 64000,
        betas: ["server-side-fallback-2026-07-01"],
        fallbacks: "default",
        thinking: { type: "adaptive" },
        output_config: { effort: e.ANTHROPIC_EFFORT, format: betaZodOutputFormat(req.schema) },
        system: req.system,
        messages: [{ role: "user", content: req.prompt }],
      });
      const message = await stream.finalMessage();
      usage = message.usage as unknown as Record<string, unknown>;
      servedModel = message.model;
      if (message.stop_reason === "refusal") {
        throw new LlmOutputError(
          `Claude hat die Anfrage abgelehnt (${message.stop_details?.category ?? "ohne Kategorie"}).`,
        );
      }
      if (message.stop_reason === "max_tokens") throw new LlmOutputError("Antwort wurde abgeschnitten (max_tokens).");
      if (message.parsed_output == null) throw new LlmOutputError("Strukturierte Ausgabe konnte nicht gelesen werden.");
      output = message.parsed_output as T;
    }

    await finishRun(runId, started, { status: "succeeded", output, usage, model: servedModel });
    return { output, runId, provider: status.provider, model: servedModel };
  } catch (err) {
    await finishRun(runId, started, { status: "failed", error: describeError(err) });
    throw err;
  }
}

/**
 * Free-text research with Anthropic's server-side web search. Returns the memo
 * and the URLs of all search results Claude cited or retrieved, so topics can
 * reference verifiable sources. Only used when RESEARCH_WEB_SEARCH=true.
 */
export async function webResearch(agent: string, system: string, prompt: string): Promise<{ memo: string; citations: Citation[]; runId: string }> {
  const status = llmStatus();
  if (status.provider === "mock") {
    throw new LlmOutputError("Websuche ist im Mock-Modus nicht verfügbar.");
  }
  const started = Date.now();
  const runId = await startRun(agent, status.provider, status.model, { prompt: prompt.slice(0, 20_000), webSearch: true });
  try {
    const messages: Anthropic.Beta.BetaMessageParam[] = [{ role: "user", content: prompt }];
    const citations = new Map<string, Citation>();
    let memo = "";
    // Server tools may pause long turns; resume a bounded number of times.
    for (let i = 0; i < 4; i++) {
      const message = await anthropic()
        .beta.messages.stream({
          model: env().ANTHROPIC_MODEL,
          max_tokens: 32000,
          betas: ["server-side-fallback-2026-07-01"],
          fallbacks: "default",
          thinking: { type: "adaptive" },
          output_config: { effort: "medium" },
          system,
          tools: [{ type: "web_search_20260209", name: "web_search", max_uses: 6 }],
          messages,
        })
        .finalMessage();
      if (message.stop_reason === "refusal") throw new LlmOutputError("Claude hat die Recherche abgelehnt.");
      for (const block of message.content) {
        if (block.type === "text") {
          memo += block.text;
          for (const c of block.citations ?? []) {
            if (c.type === "web_search_result_location") citations.set(c.url, { title: c.title ?? c.url, url: c.url });
          }
        } else if (block.type === "web_search_tool_result" && Array.isArray(block.content)) {
          for (const r of block.content) {
            if (r.type === "web_search_result" && !citations.has(r.url)) citations.set(r.url, { title: r.title, url: r.url });
          }
        }
      }
      if (message.stop_reason !== "pause_turn") break;
      messages.push({ role: "assistant", content: message.content });
    }
    const list = [...citations.values()];
    await finishRun(runId, started, { status: "succeeded", output: { memo }, citations: list });
    return { memo, citations: list, runId };
  } catch (err) {
    await finishRun(runId, started, { status: "failed", error: describeError(err) });
    throw err;
  }
}

export function describeError(err: unknown): string {
  if (err instanceof Anthropic.AuthenticationError) return "Anthropic: API-Key ungültig.";
  if (err instanceof Anthropic.RateLimitError) return "Anthropic: Rate-Limit erreicht, später erneut versuchen.";
  if (err instanceof Anthropic.BadRequestError) return `Anthropic: ungültige Anfrage – ${err.message}`;
  if (err instanceof Anthropic.APIError) return `Anthropic API-Fehler ${err.status ?? ""}: ${err.message}`;
  if (err instanceof Error) return err.message;
  return String(err);
}
