import { describe, expect, it } from "vitest";
import { buildReelArgs, escapeFilterPath } from "@/server/media/reel-render";

describe("reel ffmpeg arguments", () => {
  const base = { assPath: "/tmp/x.ass", fontDir: "/fonts", logoPath: null, musicPath: null, musicVolume: 0.1, durationSec: 12, outPath: "/tmp/out.mp4" };

  it("trims, normalises and concatenates clips (silent clips get generated audio)", () => {
    const args = buildReelArgs({ ...base, clips: [{ path: "/a.mp4", start: 1, end: 8, hasAudio: true }, { path: "/b.mp4", start: 0, end: 5, hasAudio: false }] });
    const fc = args[args.indexOf("-filter_complex") + 1];
    expect(args.slice(0, 6)).toEqual(["-ss", "1.000", "-to", "8.000", "-i", "/a.mp4"]);
    expect(fc).toContain("crop=1080:1920");
    expect(fc).toContain("anullsrc");
    expect(fc).toContain("concat=n=2:v=1:a=1");
    expect(fc).toContain("subtitles=filename=/tmp/x.ass");
    expect(fc).toContain("loudnorm");
    expect(args).toContain("libx264");
    expect(args.at(-1)).toBe("/tmp/out.mp4");
  });

  it("adds logo overlay and music bed when provided", () => {
    const args = buildReelArgs({ ...base, assPath: null, logoPath: "/logo.png", musicPath: "/m.mp3", clips: [{ path: "/a.mp4", start: 0, end: 5, hasAudio: true }] });
    const fc = args[args.indexOf("-filter_complex") + 1];
    expect(fc).toContain("overlay=W-w-48:72");
    expect(fc).toContain("amix=inputs=2");
    expect(fc).not.toContain("subtitles=");
    expect(args).toContain("-stream_loop");
  });

  it("escapes filtergraph special characters in paths", () => {
    expect(escapeFilterPath("/tmp/a:b,c'd.ass")).toBe("/tmp/a\\:b\\,c\\'d.ass");
  });
});
