import {
  boolean,
  date,
  index,
  integer,
  jsonb,
  pgEnum,
  pgTable,
  real,
  text,
  timestamp,
  uniqueIndex,
  uuid,
} from "drizzle-orm/pg-core";

// ---------------------------------------------------------------------------
// Enums
// ---------------------------------------------------------------------------

export const roleEnum = pgEnum("role", ["admin", "editor", "reviewer", "compliance", "viewer"]);
export const formatEnum = pgEnum("content_format", ["reel", "carousel", "story"]);
export const pillarEnum = pgEnum("content_pillar", [
  "authority",
  "behind_the_scenes",
  "education",
  "personal",
  "conversion",
]);
export const audienceEnum = pgEnum("audience", ["b2b_partner", "coaching", "both"]);
export const contentStatusEnum = pgEnum("content_status", [
  "planned",
  "draft",
  "in_review",
  "changes_requested",
  "approved",
  "rejected",
  "scheduled",
  "publishing",
  "published",
  "failed",
]);
export const decisionEnum = pgEnum("approval_decision", ["approved", "changes_requested", "rejected"]);
export const topicStatusEnum = pgEnum("topic_status", ["backlog", "planned", "used", "discarded"]);
export const jobStatusEnum = pgEnum("job_status", ["queued", "running", "succeeded", "failed", "cancelled"]);
export const assetKindEnum = pgEnum("asset_kind", ["video", "image", "audio", "subtitle", "logo", "render", "slide"]);
export const rightsEnum = pgEnum("rights_status", ["own", "licensed", "unknown"]);
export const leadTypeEnum = pgEnum("lead_type", ["coaching", "partner"]);
export const leadStageEnum = pgEnum("lead_stage", [
  "new",
  "qualified",
  "call_scheduled",
  "won",
  "lost",
  "disqualified",
]);
export const metricSourceEnum = pgEnum("metric_source", ["instagram_api", "manual"]);
export const recStatusEnum = pgEnum("recommendation_status", ["open", "accepted", "dismissed"]);

const ts = (name: string) => timestamp(name, { withTimezone: true });
const createdAt = () => ts("created_at").defaultNow().notNull();

// ---------------------------------------------------------------------------
// Users, sessions, audit
// ---------------------------------------------------------------------------

export const users = pgTable("users", {
  id: uuid("id").primaryKey().defaultRandom(),
  email: text("email").notNull().unique(),
  name: text("name").notNull(),
  role: roleEnum("role").notNull().default("viewer"),
  passwordHash: text("password_hash").notNull(),
  active: boolean("active").notNull().default(true),
  createdAt: createdAt(),
});

export const sessions = pgTable("sessions", {
  /** sha256 of the session token; the raw token only lives in the cookie. */
  id: text("id").primaryKey(),
  userId: uuid("user_id")
    .notNull()
    .references(() => users.id, { onDelete: "cascade" }),
  expiresAt: ts("expires_at").notNull(),
  createdAt: createdAt(),
});

export const auditLogs = pgTable(
  "audit_logs",
  {
    id: uuid("id").primaryKey().defaultRandom(),
    actorId: uuid("actor_id").references(() => users.id, { onDelete: "set null" }),
    actorLabel: text("actor_label").notNull(),
    action: text("action").notNull(),
    entityType: text("entity_type").notNull(),
    entityId: text("entity_id"),
    data: jsonb("data").$type<Record<string, unknown>>().notNull().default({}),
    createdAt: createdAt(),
  },
  (t) => [index("audit_entity_idx").on(t.entityType, t.entityId), index("audit_created_idx").on(t.createdAt)],
);

// ---------------------------------------------------------------------------
// Brand & research
// ---------------------------------------------------------------------------

export type BrandSettings = {
  personName: string;
  positioning: string;
  offers: { name: string; description: string; price?: string; cta: string }[];
  audiences: { key: "b2b_partner" | "coaching"; description: string; painPoints: string[] }[];
  voiceRules: string[];
  bannedPhrases: string[];
  examples: string[];
  disclosures: { affiliate: string; advertising: string; risk: string };
  colors: { background: string; foreground: string; accent: string; muted: string };
  handle: string;
  language: "de" | "en";
};

export const brandProfile = pgTable("brand_profile", {
  id: integer("id").primaryKey().default(1),
  settings: jsonb("settings").$type<BrandSettings>().notNull(),
  /** Style guide derived by the Brand Voice agent from approved texts. */
  derivedStyleGuide: text("derived_style_guide"),
  derivedAt: ts("derived_at"),
  logoAssetId: uuid("logo_asset_id"),
  updatedAt: ts("updated_at").defaultNow().notNull(),
});

export const researchSources = pgTable("research_sources", {
  id: uuid("id").primaryKey().defaultRandom(),
  kind: text("kind").$type<"note" | "faq" | "comment" | "lead_question" | "url" | "web_search">().notNull(),
  title: text("title").notNull(),
  content: text("content").notNull(),
  url: text("url"),
  createdBy: uuid("created_by").references(() => users.id, { onDelete: "set null" }),
  createdAt: createdAt(),
});

export type TopicSource = { kind: string; title: string; url?: string; sourceId?: string };

export const topics = pgTable("topics", {
  id: uuid("id").primaryKey().defaultRandom(),
  title: text("title").notNull(),
  angle: text("angle").notNull(),
  pillar: pillarEnum("pillar").notNull(),
  audience: audienceEnum("audience").notNull(),
  priority: integer("priority").notNull().default(50),
  rationale: text("rationale").notNull().default(""),
  sources: jsonb("sources").$type<TopicSource[]>().notNull().default([]),
  status: topicStatusEnum("status").notNull().default("backlog"),
  agentRunId: uuid("agent_run_id"),
  createdAt: createdAt(),
});

// ---------------------------------------------------------------------------
// Planning & content
// ---------------------------------------------------------------------------

export const contentPlans = pgTable(
  "content_plans",
  {
    id: uuid("id").primaryKey().defaultRandom(),
    weekStart: date("week_start").notNull(),
    status: text("status").$type<"generating" | "draft" | "active" | "archived" | "failed">().notNull(),
    strategySummary: text("strategy_summary").notNull().default(""),
    agentRunId: uuid("agent_run_id"),
    createdBy: uuid("created_by").references(() => users.id, { onDelete: "set null" }),
    createdAt: createdAt(),
  },
  (t) => [index("plan_week_idx").on(t.weekStart)],
);

export const contentItems = pgTable(
  "content_items",
  {
    id: uuid("id").primaryKey().defaultRandom(),
    planId: uuid("plan_id").references(() => contentPlans.id, { onDelete: "set null" }),
    topicId: uuid("topic_id").references(() => topics.id, { onDelete: "set null" }),
    format: formatEnum("format").notNull(),
    pillar: pillarEnum("pillar").notNull(),
    audience: audienceEnum("audience").notNull(),
    title: text("title").notNull(),
    brief: text("brief").notNull().default(""),
    /** CTA goal from planning (see CTA_TYPES); drives tracking links and conversion attribution. */
    ctaGoal: text("cta_goal").notNull().default("none"),
    scheduledAt: ts("scheduled_at"),
    status: contentStatusEnum("status").notNull().default("planned"),
    currentVersionId: uuid("current_version_id"),
    requiresComplianceReview: boolean("requires_compliance_review").notNull().default(false),
    trackingLinkId: uuid("tracking_link_id"),
    igContainerId: text("ig_container_id"),
    igMediaId: text("ig_media_id"),
    igPermalink: text("ig_permalink"),
    publishedAt: ts("published_at"),
    lastError: text("last_error"),
    createdAt: createdAt(),
    updatedAt: ts("updated_at").defaultNow().notNull(),
  },
  (t) => [index("item_sched_idx").on(t.scheduledAt), index("item_status_idx").on(t.status)],
);

/** Format-specific body, versioned. See src/lib/content-types.ts for shapes. */
export const contentVersions = pgTable(
  "content_versions",
  {
    id: uuid("id").primaryKey().defaultRandom(),
    itemId: uuid("item_id")
      .notNull()
      .references(() => contentItems.id, { onDelete: "cascade" }),
    version: integer("version").notNull(),
    body: jsonb("body").$type<Record<string, unknown>>().notNull(),
    caption: text("caption").notNull().default(""),
    source: text("source").$type<"ai" | "human">().notNull(),
    agentRunId: uuid("agent_run_id"),
    compliance: jsonb("compliance").$type<ComplianceReport>(),
    createdBy: uuid("created_by").references(() => users.id, { onDelete: "set null" }),
    createdAt: createdAt(),
  },
  (t) => [uniqueIndex("version_item_num_idx").on(t.itemId, t.version)],
);

export type ComplianceFinding = {
  rule: string;
  severity: "block" | "warn" | "info";
  message: string;
  excerpt?: string;
};
export type ComplianceReport = {
  findings: ComplianceFinding[];
  requiresComplianceReview: boolean;
  blocking: boolean;
  checkedAt: string;
};

export const approvals = pgTable("approvals", {
  id: uuid("id").primaryKey().defaultRandom(),
  itemId: uuid("item_id")
    .notNull()
    .references(() => contentItems.id, { onDelete: "cascade" }),
  versionId: uuid("version_id")
    .notNull()
    .references(() => contentVersions.id, { onDelete: "cascade" }),
  decision: decisionEnum("decision").notNull(),
  comment: text("comment").notNull().default(""),
  complianceAck: boolean("compliance_ack").notNull().default(false),
  reviewerId: uuid("reviewer_id")
    .notNull()
    .references(() => users.id),
  reviewerRole: roleEnum("reviewer_role").notNull(),
  createdAt: createdAt(),
});

// ---------------------------------------------------------------------------
// Media & rendering
// ---------------------------------------------------------------------------

export const mediaAssets = pgTable("media_assets", {
  id: uuid("id").primaryKey().defaultRandom(),
  kind: assetKindEnum("kind").notNull(),
  filename: text("filename").notNull(),
  mimeType: text("mime_type").notNull(),
  sizeBytes: integer("size_bytes").notNull(),
  storageKey: text("storage_key").notNull().unique(),
  durationSec: real("duration_sec"),
  width: integer("width"),
  height: integer("height"),
  rightsStatus: rightsEnum("rights_status").notNull().default("unknown"),
  rightsNote: text("rights_note").notNull().default(""),
  tags: jsonb("tags").$type<string[]>().notNull().default([]),
  /** For generated assets (renders, slides): which content item produced them. */
  itemId: uuid("item_id").references(() => contentItems.id, { onDelete: "set null" }),
  renderId: uuid("render_id"),
  uploadedBy: uuid("uploaded_by").references(() => users.id, { onDelete: "set null" }),
  createdAt: createdAt(),
});

export const renders = pgTable("renders", {
  id: uuid("id").primaryKey().defaultRandom(),
  itemId: uuid("item_id")
    .notNull()
    .references(() => contentItems.id, { onDelete: "cascade" }),
  versionId: uuid("version_id").references(() => contentVersions.id, { onDelete: "set null" }),
  kind: text("kind").$type<"reel" | "carousel" | "story">().notNull(),
  variant: text("variant").notNull().default("main"),
  status: jobStatusEnum("status").notNull().default("queued"),
  input: jsonb("input").$type<Record<string, unknown>>().notNull().default({}),
  outputAssetIds: jsonb("output_asset_ids").$type<string[]>().notNull().default([]),
  log: text("log").notNull().default(""),
  error: text("error"),
  createdAt: createdAt(),
  finishedAt: ts("finished_at"),
});

// ---------------------------------------------------------------------------
// Jobs & agent runs
// ---------------------------------------------------------------------------

export const jobs = pgTable(
  "jobs",
  {
    id: uuid("id").primaryKey().defaultRandom(),
    type: text("type").notNull(),
    payload: jsonb("payload").$type<Record<string, unknown>>().notNull().default({}),
    status: jobStatusEnum("status").notNull().default("queued"),
    attempts: integer("attempts").notNull().default(0),
    maxAttempts: integer("max_attempts").notNull().default(3),
    runAt: ts("run_at").defaultNow().notNull(),
    lockedAt: ts("locked_at"),
    lastError: text("last_error"),
    result: jsonb("result").$type<Record<string, unknown>>(),
    createdBy: uuid("created_by").references(() => users.id, { onDelete: "set null" }),
    createdAt: createdAt(),
    finishedAt: ts("finished_at"),
  },
  (t) => [index("jobs_pick_idx").on(t.status, t.runAt)],
);

export const agentRuns = pgTable("agent_runs", {
  id: uuid("id").primaryKey().defaultRandom(),
  agent: text("agent").notNull(),
  provider: text("provider").notNull(),
  model: text("model").notNull(),
  input: jsonb("input").$type<Record<string, unknown>>().notNull(),
  output: jsonb("output").$type<unknown>(),
  status: text("status").$type<"running" | "succeeded" | "failed">().notNull(),
  error: text("error"),
  usage: jsonb("usage").$type<Record<string, unknown>>(),
  citations: jsonb("citations").$type<{ title: string; url: string }[]>(),
  durationMs: integer("duration_ms"),
  createdAt: createdAt(),
});

// ---------------------------------------------------------------------------
// Attribution, leads, CRM
// ---------------------------------------------------------------------------

export const trackingLinks = pgTable("tracking_links", {
  id: uuid("id").primaryKey().defaultRandom(),
  code: text("code").notNull().unique(),
  label: text("label").notNull(),
  itemId: uuid("item_id").references(() => contentItems.id, { onDelete: "set null" }),
  /** "coaching" | "partner" → internal application form; otherwise an absolute URL. */
  destination: text("destination").notNull(),
  placement: text("placement").$type<"bio" | "story_link" | "caption" | "dm_manual" | "other">().notNull(),
  createdAt: createdAt(),
});

export const linkClicks = pgTable(
  "link_clicks",
  {
    id: uuid("id").primaryKey().defaultRandom(),
    linkId: uuid("link_id")
      .notNull()
      .references(() => trackingLinks.id, { onDelete: "cascade" }),
    /** No IPs or full UAs stored (data minimisation); only coarse device class + referrer host. */
    device: text("device").notNull(),
    referrerHost: text("referrer_host"),
    createdAt: createdAt(),
  },
  (t) => [index("clicks_link_idx").on(t.linkId)],
);

export const leads = pgTable(
  "leads",
  {
    id: uuid("id").primaryKey().defaultRandom(),
    type: leadTypeEnum("type").notNull(),
    name: text("name").notNull(),
    email: text("email").notNull(),
    instagramHandle: text("instagram_handle"),
    company: text("company"),
    message: text("message").notNull().default(""),
    answers: jsonb("answers").$type<Record<string, string | number | boolean>>().notNull().default({}),
    score: integer("score").notNull().default(0),
    scoreReasons: jsonb("score_reasons").$type<string[]>().notNull().default([]),
    stage: leadStageEnum("stage").notNull().default("new"),
    sourceLinkId: uuid("source_link_id").references(() => trackingLinks.id, { onDelete: "set null" }),
    sourceItemId: uuid("source_item_id").references(() => contentItems.id, { onDelete: "set null" }),
    utm: jsonb("utm").$type<Record<string, string>>().notNull().default({}),
    consentAt: ts("consent_at").notNull(),
    consentText: text("consent_text").notNull(),
    crmExternalId: text("crm_external_id"),
    crmSyncedAt: ts("crm_synced_at"),
    dealValueUsd: real("deal_value_usd"),
    notes: text("notes").notNull().default(""),
    createdAt: createdAt(),
    updatedAt: ts("updated_at").defaultNow().notNull(),
  },
  (t) => [index("leads_stage_idx").on(t.stage), index("leads_item_idx").on(t.sourceItemId)],
);

export const apiKeys = pgTable("api_keys", {
  id: uuid("id").primaryKey().defaultRandom(),
  name: text("name").notNull(),
  prefix: text("prefix").notNull(),
  keyHash: text("key_hash").notNull().unique(),
  scopes: jsonb("scopes").$type<string[]>().notNull(),
  createdBy: uuid("created_by").references(() => users.id, { onDelete: "set null" }),
  lastUsedAt: ts("last_used_at"),
  revokedAt: ts("revoked_at"),
  createdAt: createdAt(),
});

export const webhookEndpoints = pgTable("webhook_endpoints", {
  id: uuid("id").primaryKey().defaultRandom(),
  url: text("url").notNull(),
  /** AES-GCM encrypted signing secret. */
  secretEnc: text("secret_enc").notNull(),
  events: jsonb("events").$type<string[]>().notNull(),
  active: boolean("active").notNull().default(true),
  createdAt: createdAt(),
});

// ---------------------------------------------------------------------------
// Integrations, analytics, optimisation
// ---------------------------------------------------------------------------

export const integrations = pgTable("integrations", {
  provider: text("provider").$type<"instagram">().primaryKey(),
  status: text("status").$type<"not_connected" | "connected" | "error">().notNull(),
  /** Non-secret config (account id, username, token expiry). */
  config: jsonb("config").$type<Record<string, unknown>>().notNull().default({}),
  /** AES-GCM encrypted access token. */
  secretEnc: text("secret_enc"),
  lastError: text("last_error"),
  updatedAt: ts("updated_at").defaultNow().notNull(),
});

export const postMetrics = pgTable(
  "post_metrics",
  {
    id: uuid("id").primaryKey().defaultRandom(),
    itemId: uuid("item_id")
      .notNull()
      .references(() => contentItems.id, { onDelete: "cascade" }),
    source: metricSourceEnum("source").notNull(),
    capturedAt: ts("captured_at").defaultNow().notNull(),
    views: integer("views"),
    reach: integer("reach"),
    likes: integer("likes"),
    comments: integer("comments"),
    saves: integer("saves"),
    shares: integer("shares"),
    profileVisits: integer("profile_visits"),
    follows: integer("follows"),
    avgWatchTimeSec: real("avg_watch_time_sec"),
    dmInquiries: integer("dm_inquiries"),
    raw: jsonb("raw").$type<Record<string, unknown>>().notNull().default({}),
    enteredBy: uuid("entered_by").references(() => users.id, { onDelete: "set null" }),
  },
  (t) => [index("metrics_item_idx").on(t.itemId, t.capturedAt)],
);

export const recommendations = pgTable("recommendations", {
  id: uuid("id").primaryKey().defaultRandom(),
  category: text("category").$type<"topic" | "hook" | "format" | "cta" | "timing" | "conversion">().notNull(),
  title: text("title").notNull(),
  body: text("body").notNull(),
  evidence: text("evidence").notNull().default(""),
  confidence: text("confidence").$type<"low" | "medium" | "high">().notNull(),
  status: recStatusEnum("status").notNull().default("open"),
  agentRunId: uuid("agent_run_id"),
  createdAt: createdAt(),
});
