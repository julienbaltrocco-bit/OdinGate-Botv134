import { createReadStream, createWriteStream } from "node:fs";
import { mkdir, mkdtemp, rm, stat, unlink } from "node:fs/promises";
import { tmpdir } from "node:os";
import path from "node:path";
import { Readable } from "node:stream";
import { pipeline } from "node:stream/promises";
import { DeleteObjectCommand, GetObjectCommand, S3Client } from "@aws-sdk/client-s3";
import { Upload } from "@aws-sdk/lib-storage";
import { getSignedUrl } from "@aws-sdk/s3-request-presigner";
import { env } from "@/server/env";

/**
 * Storage abstraction: local filesystem (default, dev) or any S3-compatible
 * bucket (MinIO, R2, AWS). Keys are opaque, e.g. "uploads/2026/11/<uuid>.mp4".
 */
export interface Storage {
  driver: "local" | "s3";
  putStream(key: string, body: Readable, contentType: string): Promise<number>;
  putFile(key: string, filePath: string, contentType: string): Promise<number>;
  getStream(key: string, range?: { start: number; end: number }): Promise<Readable>;
  size(key: string): Promise<number>;
  delete(key: string): Promise<void>;
  /** Runs `fn` with a local file path (downloads to a temp file for S3). */
  withLocalFile<T>(key: string, fn: (filePath: string) => Promise<T>): Promise<T>;
  /** Time-limited public URL (S3 only). Needed for Instagram publishing, which fetches media by URL. */
  signedUrl(key: string, expiresSec: number): Promise<string | null>;
}

function safeJoin(root: string, key: string): string {
  const resolved = path.resolve(root, key);
  if (!resolved.startsWith(path.resolve(root) + path.sep)) throw new Error("Invalid storage key");
  return resolved;
}

class LocalStorage implements Storage {
  driver = "local" as const;
  constructor(private root: string) {}

  async putStream(key: string, body: Readable, _contentType: string) {
    const target = safeJoin(this.root, key);
    await mkdir(path.dirname(target), { recursive: true });
    await pipeline(body, createWriteStream(target));
    return (await stat(target)).size;
  }
  async putFile(key: string, filePath: string, contentType: string) {
    return this.putStream(key, createReadStream(filePath), contentType);
  }
  async getStream(key: string, range?: { start: number; end: number }) {
    return createReadStream(safeJoin(this.root, key), range);
  }
  async size(key: string) {
    return (await stat(safeJoin(this.root, key))).size;
  }
  async delete(key: string) {
    await unlink(safeJoin(this.root, key)).catch(() => undefined);
  }
  async withLocalFile<T>(key: string, fn: (p: string) => Promise<T>) {
    return fn(safeJoin(this.root, key));
  }
  async signedUrl() {
    return null;
  }
}

class S3Storage implements Storage {
  driver = "s3" as const;
  private client: S3Client;
  constructor(private bucket: string) {
    const e = env();
    this.client = new S3Client({
      region: e.S3_REGION,
      endpoint: e.S3_ENDPOINT || undefined,
      forcePathStyle: e.S3_FORCE_PATH_STYLE,
      credentials:
        e.S3_ACCESS_KEY_ID && e.S3_SECRET_ACCESS_KEY
          ? { accessKeyId: e.S3_ACCESS_KEY_ID, secretAccessKey: e.S3_SECRET_ACCESS_KEY }
          : undefined,
    });
  }
  async putStream(key: string, body: Readable, contentType: string) {
    let bytes = 0;
    body.on("data", (c: Buffer) => (bytes += c.length));
    await new Upload({ client: this.client, params: { Bucket: this.bucket, Key: key, Body: body, ContentType: contentType } }).done();
    return bytes;
  }
  async putFile(key: string, filePath: string, contentType: string) {
    return this.putStream(key, createReadStream(filePath), contentType);
  }
  async getStream(key: string, range?: { start: number; end: number }) {
    const res = await this.client.send(
      new GetObjectCommand({ Bucket: this.bucket, Key: key, Range: range ? `bytes=${range.start}-${range.end}` : undefined }),
    );
    return res.Body as Readable;
  }
  async size(key: string) {
    const res = await this.client.send(new GetObjectCommand({ Bucket: this.bucket, Key: key, Range: "bytes=0-0" }));
    const total = res.ContentRange?.split("/")[1];
    return total ? Number(total) : Number(res.ContentLength ?? 0);
  }
  async delete(key: string) {
    await this.client.send(new DeleteObjectCommand({ Bucket: this.bucket, Key: key }));
  }
  async withLocalFile<T>(key: string, fn: (p: string) => Promise<T>) {
    const dir = await mkdtemp(path.join(tmpdir(), "ce-s3-"));
    const file = path.join(dir, path.basename(key));
    try {
      await pipeline(await this.getStream(key), createWriteStream(file));
      return await fn(file);
    } finally {
      await rm(dir, { recursive: true, force: true });
    }
  }
  async signedUrl(key: string, expiresSec: number) {
    return getSignedUrl(this.client, new GetObjectCommand({ Bucket: this.bucket, Key: key }), { expiresIn: expiresSec });
  }
}

let instance: Storage | undefined;
export function storage(): Storage {
  if (!instance) {
    const e = env();
    if (e.STORAGE_DRIVER === "s3") {
      if (!e.S3_BUCKET) throw new Error("STORAGE_DRIVER=s3 erfordert S3_BUCKET");
      instance = new S3Storage(e.S3_BUCKET);
    } else {
      instance = new LocalStorage(path.resolve(e.STORAGE_LOCAL_DIR));
    }
  }
  return instance;
}

export function resetStorage() {
  instance = undefined;
}

export function storageKey(prefix: string, id: string, ext: string): string {
  const d = new Date();
  return `${prefix}/${d.getUTCFullYear()}/${String(d.getUTCMonth() + 1).padStart(2, "0")}/${id}${ext}`;
}

export { Readable };
