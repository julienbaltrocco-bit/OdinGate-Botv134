import { mkdtemp, readFile, rm } from "node:fs/promises";
import { tmpdir } from "node:os";
import path from "node:path";
import { env } from "@/server/env";
import { ffmpeg, run } from "./ffmpeg";
import { parseSrt, type Cue } from "./subtitles";

/**
 * Automatic transcription via a self-hosted whisper.cpp binary (no SaaS).
 * Requires WHISPER_CPP_BIN and WHISPER_CPP_MODEL. Not available in the default
 * setup – see docs/BLOCKERS.md. Script-timed subtitles or SRT upload work without it.
 */
export function transcriptionAvailable(): boolean {
  const e = env();
  return !!(e.WHISPER_CPP_BIN && e.WHISPER_CPP_MODEL);
}

export async function transcribe(videoPath: string, language = "de"): Promise<Cue[]> {
  const e = env();
  if (!e.WHISPER_CPP_BIN || !e.WHISPER_CPP_MODEL) {
    throw new Error("Automatische Transkription nicht konfiguriert (WHISPER_CPP_BIN / WHISPER_CPP_MODEL).");
  }
  const dir = await mkdtemp(path.join(tmpdir(), "ce-whisper-"));
  try {
    const wav = path.join(dir, "audio.wav");
    await ffmpeg(["-i", videoPath, "-vn", "-ac", "1", "-ar", "16000", "-c:a", "pcm_s16le", wav]);
    const outPrefix = path.join(dir, "out");
    await run(e.WHISPER_CPP_BIN, ["-m", e.WHISPER_CPP_MODEL, "-f", wav, "-l", language, "-osrt", "-of", outPrefix], { timeoutMs: 30 * 60_000 });
    return parseSrt(await readFile(`${outPrefix}.srt`, "utf8"));
  } finally {
    await rm(dir, { recursive: true, force: true });
  }
}
