import { Readable } from "node:stream";
import { currentUser } from "@/server/auth/current";
import { can } from "@/server/auth/rbac";
import { ingestUpload, type RightsStatus } from "@/server/media/assets";
import { env } from "@/server/env";

/**
 * Streaming upload: the browser PUTs the raw file body (no multipart buffering),
 * metadata travels in query parameters. Size is limited by MAX_UPLOAD_MB.
 */
export async function PUT(request: Request) {
  const user = await currentUser();
  if (!user || !can(user.role, "media.write")) return Response.json({ error: "Keine Berechtigung" }, { status: 403 });
  const url = new URL(request.url);
  const filename = url.searchParams.get("filename") ?? "upload";
  const rights = (url.searchParams.get("rights") ?? "unknown") as RightsStatus;
  if (!["own", "licensed", "unknown"].includes(rights)) return Response.json({ error: "Ungültiger Rechte-Status" }, { status: 400 });
  const kind = url.searchParams.get("kind");
  const length = Number(request.headers.get("content-length") ?? 0);
  const max = env().MAX_UPLOAD_MB * 1024 * 1024;
  if (length > max) return Response.json({ error: `Datei zu groß (max. ${env().MAX_UPLOAD_MB} MB)` }, { status: 413 });
  if (!request.body) return Response.json({ error: "Leerer Upload" }, { status: 400 });

  let received = 0;
  const limited = Readable.fromWeb(request.body as import("node:stream/web").ReadableStream).on("data", (chunk: Buffer) => {
    received += chunk.length;
    if (received > max) limited.destroy(new Error("Datei zu groß"));
  });
  try {
    const asset = await ingestUpload(
      { id: user.id, label: user.email },
      {
        filename,
        mimeType: request.headers.get("content-type") ?? "application/octet-stream",
        body: limited,
        rightsStatus: rights,
        rightsNote: url.searchParams.get("note") ?? "",
        tags: (url.searchParams.get("tags") ?? "").split(",").map((t) => t.trim()).filter(Boolean).slice(0, 10),
        kindOverride: kind === "logo" ? "logo" : undefined,
      },
    );
    return Response.json({ id: asset.id });
  } catch (err) {
    return Response.json({ error: (err as Error).message }, { status: 400 });
  }
}
