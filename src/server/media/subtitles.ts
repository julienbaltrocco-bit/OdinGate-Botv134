/**
 * Subtitle cues and ASS generation for burned-in captions, hook and CTA overlays.
 * Pure functions (unit-tested): no I/O.
 */

export type Cue = { start: number; end: number; text: string };

/** Splits spoken script segments into short caption cues (max ~5 words) timed by word count. */
export function cuesFromScript(segments: { text: string; durationSec: number }[], totalDurationSec: number, maxWords = 5): Cue[] {
  const chunks: { text: string; weight: number }[] = [];
  for (const seg of segments) {
    const words = seg.text.replace(/\s+/g, " ").trim().split(" ").filter(Boolean);
    if (!words.length) continue;
    const perWord = seg.durationSec / words.length;
    for (let i = 0; i < words.length; i += maxWords) {
      const part = words.slice(i, i + maxWords);
      chunks.push({ text: part.join(" "), weight: perWord * part.length });
    }
  }
  const scriptTotal = chunks.reduce((a, c) => a + c.weight, 0);
  if (!chunks.length || scriptTotal <= 0 || totalDurationSec <= 0) return [];
  // Compress the script timing when the footage is shorter; never stretch it.
  const factor = Math.min(1, totalDurationSec / scriptTotal);
  const cues: Cue[] = [];
  let t = 0;
  for (const c of chunks) {
    const d = c.weight * factor;
    cues.push({ start: round(t), end: round(Math.min(totalDurationSec, t + d)), text: c.text });
    t += d;
  }
  return cues.filter((c) => c.end - c.start > 0.05);
}

/** Parses SRT or WebVTT. */
export function parseSrt(input: string): Cue[] {
  const text = input.replace(/\r/g, "").replace(/^WEBVTT[^\n]*\n/, "");
  const blocks = text.split(/\n{2,}/);
  const cues: Cue[] = [];
  const time = /(\d{1,2}:)?(\d{1,2}):(\d{2})[,.](\d{3})/;
  for (const block of blocks) {
    const lines = block.trim().split("\n");
    const idx = lines.findIndex((l) => l.includes("-->"));
    if (idx < 0) continue;
    const [a, b] = lines[idx].split("-->").map((s) => s.trim());
    const start = toSec(a.match(time));
    const end = toSec(b.match(time));
    const body = lines.slice(idx + 1).join(" ").replace(/<[^>]+>/g, "").trim();
    if (start !== null && end !== null && body) cues.push({ start, end, text: body });
  }
  return cues;
}

function toSec(m: RegExpMatchArray | null): number | null {
  if (!m) return null;
  const h = m[1] ? Number(m[1].replace(":", "")) : 0;
  return h * 3600 + Number(m[2]) * 60 + Number(m[3]) + Number(m[4]) / 1000;
}

function round(n: number) {
  return Math.round(n * 100) / 100;
}

export function assTime(sec: number): string {
  const cs = Math.max(0, Math.round(sec * 100));
  const h = Math.floor(cs / 360000);
  const m = Math.floor((cs % 360000) / 6000);
  const s = Math.floor((cs % 6000) / 100);
  return `${h}:${String(m).padStart(2, "0")}:${String(s).padStart(2, "0")}.${String(cs % 100).padStart(2, "0")}`;
}

/** Escapes text for ASS dialogue lines (no override tags from user input). */
export function assEscape(text: string): string {
  return text.replace(/\\/g, "\\\\").replace(/\{/g, "(").replace(/\}/g, ")").replace(/\r?\n/g, "\\N");
}

/** "#RRGGBB" → ASS "&H00BBGGRR". */
export function assColor(hex: string, alpha = 0): string {
  const h = hex.replace("#", "").padEnd(6, "0");
  const a = alpha.toString(16).padStart(2, "0").toUpperCase();
  return `&H${a}${h.slice(4, 6)}${h.slice(2, 4)}${h.slice(0, 2)}`.toUpperCase();
}

export type AssOptions = {
  width: number;
  height: number;
  cues: Cue[];
  hook?: { text: string; durationSec: number } | null;
  cta?: { text: string; start: number; end: number } | null;
  colors: { accent: string; foreground: string; background: string };
  fontName?: string;
};

export function buildAss(o: AssOptions): string {
  const font = o.fontName ?? "Inter";
  const fg = assColor(o.colors.foreground);
  const accent = assColor(o.colors.accent);
  const boxBg = assColor(o.colors.background, 0x30);
  const header = `[Script Info]
ScriptType: v4.00+
PlayResX: ${o.width}
PlayResY: ${o.height}
WrapStyle: 0
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Caption,${font},68,${fg},${fg},&H00000000,&H64000000,-1,0,0,0,100,100,0,0,1,5,0,2,90,90,430,1
Style: Hook,${font},84,${fg},${fg},${boxBg},${boxBg},-1,0,0,0,100,100,0,0,3,24,0,8,80,80,260,1
Style: Cta,${font},72,${fg},${fg},${accent},${accent},-1,0,0,0,100,100,0,0,3,26,0,5,90,90,0,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
`;
  const lines: string[] = [];
  if (o.hook?.text) lines.push(`Dialogue: 2,${assTime(0)},${assTime(o.hook.durationSec)},Hook,,0,0,0,,${assEscape(o.hook.text)}`);
  for (const c of o.cues) lines.push(`Dialogue: 0,${assTime(c.start)},${assTime(c.end)},Caption,,0,0,0,,${assEscape(c.text)}`);
  if (o.cta?.text) lines.push(`Dialogue: 3,${assTime(o.cta.start)},${assTime(o.cta.end)},Cta,,0,0,0,,${assEscape(o.cta.text)}`);
  return header + lines.join("\n") + "\n";
}
