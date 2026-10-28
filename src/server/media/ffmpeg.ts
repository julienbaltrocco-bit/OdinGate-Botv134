import { spawn } from "node:child_process";
import { env } from "@/server/env";

export type ProbeResult = {
  durationSec: number | null;
  width: number | null;
  height: number | null;
  hasVideo: boolean;
  hasAudio: boolean;
  videoCodec: string | null;
  audioCodec: string | null;
};

export function run(bin: string, args: string[], opts: { timeoutMs?: number } = {}): Promise<{ stdout: string; stderr: string }> {
  return new Promise((resolve, reject) => {
    const child = spawn(bin, args, { stdio: ["ignore", "pipe", "pipe"] });
    let stdout = "";
    let stderr = "";
    child.stdout.on("data", (d) => (stdout += d));
    child.stderr.on("data", (d) => {
      stderr += d;
      if (stderr.length > 200_000) stderr = stderr.slice(-100_000);
    });
    const timer = opts.timeoutMs ? setTimeout(() => child.kill("SIGKILL"), opts.timeoutMs) : null;
    child.on("error", (err) => {
      if (timer) clearTimeout(timer);
      reject(new Error(`${bin} konnte nicht gestartet werden: ${err.message}`));
    });
    child.on("close", (code) => {
      if (timer) clearTimeout(timer);
      if (code === 0) resolve({ stdout, stderr });
      else reject(new Error(`${bin} exit ${code}: ${stderr.split("\n").slice(-15).join("\n")}`));
    });
  });
}

export async function probe(filePath: string): Promise<ProbeResult> {
  const { stdout } = await run(env().FFPROBE_PATH, ["-v", "error", "-print_format", "json", "-show_format", "-show_streams", filePath], {
    timeoutMs: 60_000,
  });
  const data = JSON.parse(stdout) as {
    format?: { duration?: string };
    streams?: { codec_type: string; codec_name?: string; width?: number; height?: number; duration?: string; tags?: { rotate?: string }; side_data_list?: { rotation?: number }[] }[];
  };
  const v = data.streams?.find((s) => s.codec_type === "video");
  const a = data.streams?.find((s) => s.codec_type === "audio");
  const rotation = Math.abs(Number(v?.tags?.rotate ?? v?.side_data_list?.find((s) => s.rotation !== undefined)?.rotation ?? 0));
  const swap = rotation === 90 || rotation === 270;
  const duration = Number(data.format?.duration ?? v?.duration ?? NaN);
  return {
    durationSec: Number.isFinite(duration) ? duration : null,
    width: (swap ? v?.height : v?.width) ?? null,
    height: (swap ? v?.width : v?.height) ?? null,
    hasVideo: !!v,
    hasAudio: !!a,
    videoCodec: v?.codec_name ?? null,
    audioCodec: a?.codec_name ?? null,
  };
}

export function ffmpeg(args: string[], timeoutMs = 20 * 60_000) {
  return run(env().FFMPEG_PATH, ["-hide_banner", "-y", ...args], { timeoutMs });
}
