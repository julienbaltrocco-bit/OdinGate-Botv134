import { describe, expect, it } from "vitest";
import { assColor, assEscape, assTime, buildAss, cuesFromScript, parseSrt } from "@/server/media/subtitles";

describe("subtitles", () => {
  it("splits script into short cues timed by word count", () => {
    const cues = cuesFromScript([{ text: "eins zwei drei vier fünf sechs sieben acht", durationSec: 4 }], 10);
    expect(cues).toHaveLength(2);
    expect(cues[0]).toMatchObject({ start: 0, text: "eins zwei drei vier fünf" });
    expect(cues[1].end).toBeCloseTo(4, 1);
  });
  it("compresses timing when footage is shorter than the script", () => {
    const cues = cuesFromScript([{ text: "a b c d e f g h i j", durationSec: 10 }], 5);
    expect(cues.at(-1)!.end).toBeLessThanOrEqual(5);
  });
  it("parses SRT and VTT", () => {
    const srt = "1\n00:00:01,000 --> 00:00:02,500\nHallo <i>Welt</i>\n\n2\n00:00:03,000 --> 00:00:04,000\nZwei\n";
    expect(parseSrt(srt)).toEqual([
      { start: 1, end: 2.5, text: "Hallo Welt" },
      { start: 3, end: 4, text: "Zwei" },
    ]);
    expect(parseSrt("WEBVTT\n\n00:01.000 --> 00:02.000\nVTT")).toEqual([{ start: 1, end: 2, text: "VTT" }]);
  });
  it("formats ASS values safely", () => {
    expect(assTime(61.234)).toBe("0:01:01.23");
    expect(assColor("#3B82F6")).toBe("&H00F6823B");
    expect(assEscape("{\\b1}Hack\nZeile")).toBe("(\\\\b1)Hack\\NZeile");
    const ass = buildAss({ width: 1080, height: 1920, cues: [{ start: 0, end: 1, text: "Hi" }], hook: { text: "Hook", durationSec: 2 }, cta: null, colors: { accent: "#000000", foreground: "#ffffff", background: "#000000" } });
    expect(ass).toContain("Style: Caption");
    expect(ass).toContain(",Hook,,0,0,0,,Hook");
  });
});
