import { z } from "zod";

/**
 * Central, validated runtime configuration. Secrets are only read from the
 * environment (never from source). Optional integrations stay `undefined`
 * when not configured; the UI surfaces them as blockers instead of faking them.
 */
const schema = z.object({
  NODE_ENV: z.enum(["development", "test", "production"]).default("development"),
  DATABASE_URL: z.string().min(1),
  APP_URL: z.string().url().default("http://localhost:3000"),

  /** 32-byte key (base64 or hex) for AES-256-GCM encryption of stored credentials. */
  APP_ENCRYPTION_KEY: z.string().min(32),

  /** "anthropic" (default) or "mock". Mock is for tests / UI demos and is labelled everywhere. */
  LLM_PROVIDER: z.enum(["anthropic", "mock"]).default("anthropic"),
  ANTHROPIC_API_KEY: z.string().optional(),
  ANTHROPIC_MODEL: z.string().default("claude-opus-5-5"),
  ANTHROPIC_EFFORT: z.enum(["low", "medium", "high", "xhigh", "max"]).default("high"),
  /** Allow the Research Agent to use Anthropic's server-side web search (with citations). */
  RESEARCH_WEB_SEARCH: z
    .enum(["true", "false"])
    .default("false")
    .transform((v) => v === "true"),

  STORAGE_DRIVER: z.enum(["local", "s3"]).default("local"),
  STORAGE_LOCAL_DIR: z.string().default("./data/media"),
  S3_ENDPOINT: z.string().optional(),
  S3_REGION: z.string().default("us-east-1"),
  S3_BUCKET: z.string().optional(),
  S3_ACCESS_KEY_ID: z.string().optional(),
  S3_SECRET_ACCESS_KEY: z.string().optional(),
  S3_FORCE_PATH_STYLE: z
    .enum(["true", "false"])
    .default("true")
    .transform((v) => v === "true"),

  FFMPEG_PATH: z.string().default("ffmpeg"),
  FFPROBE_PATH: z.string().default("ffprobe"),
  /** Optional whisper.cpp CLI for automatic transcription (see docs/BLOCKERS.md). */
  WHISPER_CPP_BIN: z.string().optional(),
  WHISPER_CPP_MODEL: z.string().optional(),

  INSTAGRAM_GRAPH_HOST: z.string().default("https://graph.instagram.com"),
  INSTAGRAM_API_VERSION: z.string().default("v23.0"),
  /** Publishing stays disabled until explicitly enabled AND an account is connected. */
  INSTAGRAM_PUBLISHING_ENABLED: z
    .enum(["true", "false"])
    .default("false")
    .transform((v) => v === "true"),

  /** Public legal pages linked from the application forms (DSGVO / Impressumspflicht). */
  PRIVACY_URL: z.string().url().optional(),
  IMPRINT_URL: z.string().url().optional(),

  MAX_UPLOAD_MB: z.coerce.number().default(1024),
  SESSION_TTL_HOURS: z.coerce.number().default(24 * 7),
});

export type Env = z.infer<typeof schema>;

let cached: Env | undefined;

export function env(): Env {
  if (!cached) {
    // Treat empty values from .env templates as "not set".
    const raw = Object.fromEntries(Object.entries(process.env).filter(([, v]) => v !== ""));
    const parsed = schema.safeParse(raw);
    if (!parsed.success) {
      const issues = parsed.error.issues.map((i) => `${i.path.join(".")}: ${i.message}`).join("; ");
      throw new Error(`Invalid environment configuration: ${issues}`);
    }
    cached = parsed.data;
  }
  return cached;
}

/** For tests that mutate process.env. */
export function resetEnvCache() {
  cached = undefined;
}
