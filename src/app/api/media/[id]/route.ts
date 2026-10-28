import { Readable } from "node:stream";
import { currentUser } from "@/server/auth/current";
import { can } from "@/server/auth/rbac";
import { getAsset } from "@/server/media/assets";
import { storage } from "@/server/media/storage";

/** Authenticated media delivery with HTTP Range support (video scrubbing). */
export async function GET(request: Request, { params }: { params: Promise<{ id: string }> }) {
  const user = await currentUser();
  if (!user || !can(user.role, "media.read")) return new Response("Unauthorized", { status: 401 });
  const { id } = await params;
  if (!/^[0-9a-f-]{36}$/.test(id)) return new Response("Not found", { status: 404 });
  const asset = await getAsset(id);
  if (!asset) return new Response("Not found", { status: 404 });

  const size = asset.sizeBytes;
  const headers = new Headers({
    "content-type": asset.mimeType,
    "accept-ranges": "bytes",
    "cache-control": "private, max-age=3600",
    "x-content-type-options": "nosniff",
  });
  if (new URL(request.url).searchParams.get("download")) {
    headers.set("content-disposition", `attachment; filename="${asset.filename.replace(/[^\w.\-]/g, "_")}"`);
  }
  const range = request.headers.get("range")?.match(/^bytes=(\d*)-(\d*)$/);
  if (range && (range[1] || range[2])) {
    const start = range[1] ? Number(range[1]) : Math.max(0, size - Number(range[2]));
    const end = range[1] && range[2] ? Math.min(Number(range[2]), size - 1) : size - 1;
    if (start >= size || start > end) return new Response(null, { status: 416, headers: { "content-range": `bytes */${size}` } });
    headers.set("content-range", `bytes ${start}-${end}/${size}`);
    headers.set("content-length", String(end - start + 1));
    const stream = await storage().getStream(asset.storageKey, { start, end });
    return new Response(Readable.toWeb(stream) as ReadableStream, { status: 206, headers });
  }
  headers.set("content-length", String(size));
  const stream = await storage().getStream(asset.storageKey);
  return new Response(Readable.toWeb(stream) as ReadableStream, { status: 200, headers });
}
