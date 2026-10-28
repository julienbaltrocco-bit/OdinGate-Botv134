/**
 * Minimal client for the official Instagram Platform API (Instagram API with
 * Instagram Login, host graph.instagram.com). Publishing uses the documented
 * two-step container flow: create container → poll status → media_publish.
 *
 * No scraping, no login automation, no DMs. Media must be reachable via a
 * public URL at publish time (Meta fetches it server-side).
 */

export type IgConfig = { host: string; version: string; accessToken: string; userId: string };

export class InstagramApiError extends Error {
  constructor(
    message: string,
    public status: number,
    public code?: number,
    public subcode?: number,
  ) {
    super(message);
    this.name = "InstagramApiError";
  }
  /** Rate-limit / transient errors that are worth retrying later. */
  get retryable(): boolean {
    return this.status >= 500 || this.code === 4 || this.code === 17 || this.code === 32 || this.code === 613 || this.code === 2;
  }
}

export type ContainerStatus = "EXPIRED" | "ERROR" | "FINISHED" | "IN_PROGRESS" | "PUBLISHED";

export class InstagramClient {
  constructor(
    private cfg: IgConfig,
    private fetchImpl: typeof fetch = fetch,
  ) {}

  private url(pathname: string, params: Record<string, string | undefined> = {}) {
    const u = new URL(`${this.cfg.host.replace(/\/$/, "")}/${this.cfg.version}/${pathname.replace(/^\//, "")}`);
    for (const [k, v] of Object.entries(params)) if (v !== undefined) u.searchParams.set(k, v);
    return u;
  }

  private async request<T>(method: "GET" | "POST", pathname: string, rawParams: Record<string, string | undefined> = {}): Promise<T> {
    // Token is sent both as Bearer header and as documented access_token parameter; never logged.
    const params = { ...rawParams, access_token: this.cfg.accessToken };
    const u = this.url(pathname, method === "GET" ? params : {});
    const init: RequestInit = { method, headers: { authorization: `Bearer ${this.cfg.accessToken}` }, signal: AbortSignal.timeout(30_000) };
    if (method === "POST") {
      const form = new URLSearchParams();
      for (const [k, v] of Object.entries(params)) if (v !== undefined) form.set(k, v);
      init.body = form;
      init.headers = { ...init.headers, "content-type": "application/x-www-form-urlencoded" };
    }
    const res = await this.fetchImpl(u, init);
    const json = (await res.json().catch(() => ({}))) as { error?: { message: string; code?: number; error_subcode?: number } } & T;
    if (!res.ok || json.error) {
      throw new InstagramApiError(json.error?.message ?? `HTTP ${res.status}`, res.status, json.error?.code, json.error?.error_subcode);
    }
    return json;
  }

  me() {
    return this.request<{ user_id?: string; id?: string; username: string; account_type?: string }>("GET", "me", {
      fields: "user_id,username,account_type",
    });
  }

  publishingLimit() {
    return this.request<{ data: { quota_usage: number; config?: { quota_total: number; quota_duration: number } }[] }>(
      "GET",
      `${this.cfg.userId}/content_publishing_limit`,
      { fields: "quota_usage,config" },
    );
  }

  createReelContainer(videoUrl: string, caption: string, opts: { coverUrl?: string; shareToFeed?: boolean } = {}) {
    return this.request<{ id: string }>("POST", `${this.cfg.userId}/media`, {
      media_type: "REELS",
      video_url: videoUrl,
      caption,
      cover_url: opts.coverUrl,
      share_to_feed: String(opts.shareToFeed ?? true),
    });
  }

  createCarouselItem(imageUrl: string) {
    return this.request<{ id: string }>("POST", `${this.cfg.userId}/media`, { image_url: imageUrl, is_carousel_item: "true" });
  }

  createCarouselContainer(childIds: string[], caption: string) {
    return this.request<{ id: string }>("POST", `${this.cfg.userId}/media`, {
      media_type: "CAROUSEL",
      children: childIds.join(","),
      caption,
    });
  }

  containerStatus(containerId: string) {
    return this.request<{ status_code: ContainerStatus; status?: string }>("GET", containerId, { fields: "status_code,status" });
  }

  publish(containerId: string) {
    return this.request<{ id: string }>("POST", `${this.cfg.userId}/media_publish`, { creation_id: containerId });
  }

  media(mediaId: string) {
    return this.request<{ id: string; permalink?: string; timestamp?: string; media_type?: string }>("GET", mediaId, {
      fields: "id,permalink,timestamp,media_type",
    });
  }

  /**
   * Media insights. Metric availability changes between API versions
   * (e.g. `impressions`/`plays` were replaced by `views`), so unsupported
   * metrics are dropped individually instead of failing the whole sync.
   */
  async insights(mediaId: string, metrics: string[]): Promise<Record<string, number>> {
    const parse = (r: { data: { name: string; values?: { value: number }[]; total_value?: { value: number } }[] }) =>
      Object.fromEntries(r.data.map((d) => [d.name, Number(d.total_value?.value ?? d.values?.[0]?.value ?? 0)]));
    try {
      return parse(await this.request("GET", `${mediaId}/insights`, { metric: metrics.join(",") }));
    } catch (err) {
      if (!(err instanceof InstagramApiError) || err.retryable) throw err;
      const out: Record<string, number> = {};
      for (const m of metrics) {
        try {
          Object.assign(out, parse(await this.request("GET", `${mediaId}/insights`, { metric: m })));
        } catch (inner) {
          if (inner instanceof InstagramApiError && inner.retryable) throw inner;
        }
      }
      return out;
    }
  }

  refreshToken() {
    const u = new URL(`${this.cfg.host.replace(/\/$/, "")}/refresh_access_token`);
    u.searchParams.set("grant_type", "ig_refresh_token");
    u.searchParams.set("access_token", this.cfg.accessToken);
    return this.fetchImpl(u, { signal: AbortSignal.timeout(30_000) }).then(async (r) => {
      const j = (await r.json()) as { access_token?: string; expires_in?: number; error?: { message: string } };
      if (!r.ok || !j.access_token) throw new InstagramApiError(j.error?.message ?? `HTTP ${r.status}`, r.status);
      return { accessToken: j.access_token, expiresIn: j.expires_in ?? 0 };
    });
  }
}

export const REEL_METRICS = ["views", "reach", "likes", "comments", "saved", "shares", "total_interactions", "ig_reels_avg_watch_time"];
export const FEED_METRICS = ["views", "reach", "likes", "comments", "saved", "shares", "total_interactions", "profile_visits", "follows"];

/** Polls a container until FINISHED (video processing can take minutes). */
export async function waitForContainer(
  client: InstagramClient,
  containerId: string,
  opts: { intervalMs?: number; timeoutMs?: number; sleep?: (ms: number) => Promise<void> } = {},
) {
  const interval = opts.intervalMs ?? 10_000;
  const deadline = Date.now() + (opts.timeoutMs ?? 10 * 60_000);
  const sleep = opts.sleep ?? ((ms: number) => new Promise((r) => setTimeout(r, ms)));
  for (;;) {
    const s = await client.containerStatus(containerId);
    if (s.status_code === "FINISHED") return;
    if (s.status_code === "ERROR" || s.status_code === "EXPIRED") {
      throw new InstagramApiError(`Container ${s.status_code}: ${s.status ?? ""}`, 400);
    }
    if (Date.now() > deadline) throw new InstagramApiError("Zeitüberschreitung bei der Videoverarbeitung", 504);
    await sleep(interval);
  }
}
