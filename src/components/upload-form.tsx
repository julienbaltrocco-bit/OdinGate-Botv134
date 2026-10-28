"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

/** Uploads files one by one via streaming PUT with progress. */
export function UploadForm() {
  const router = useRouter();
  const [busy, setBusy] = useState(false);
  const [status, setStatus] = useState<string | null>(null);

  async function onSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const form = e.currentTarget;
    const fd = new FormData(form);
    const files = (form.elements.namedItem("files") as HTMLInputElement).files;
    if (!files?.length) return;
    setBusy(true);
    const errors: string[] = [];
    for (const [i, file] of [...files].entries()) {
      setStatus(`Lade ${i + 1}/${files.length}: ${file.name} …`);
      const params = new URLSearchParams({
        filename: file.name,
        rights: String(fd.get("rights")),
        note: String(fd.get("note") ?? ""),
        tags: String(fd.get("tags") ?? ""),
        kind: String(fd.get("kind") ?? ""),
      });
      const res = await fetch(`/api/media/upload?${params}`, { method: "PUT", body: file, headers: { "content-type": file.type || "application/octet-stream" } });
      if (!res.ok) errors.push(`${file.name}: ${((await res.json().catch(() => ({}))) as { error?: string }).error ?? res.status}`);
    }
    setBusy(false);
    setStatus(errors.length ? `Fehler: ${errors.join("; ")}` : `${files.length} Datei(en) hochgeladen.`);
    form.reset();
    router.refresh();
  }

  const input = "w-full rounded-lg border border-slate-300 px-3 py-1.5 text-sm";
  return (
    <form onSubmit={onSubmit} className="grid gap-3 md:grid-cols-2">
      <label className="text-sm md:col-span-2">
        <span className="mb-1 block font-medium">Dateien (Video, Bild, Audio, SRT/VTT)</span>
        <input name="files" type="file" multiple required accept="video/*,image/*,audio/*,.srt,.vtt" className="text-sm" />
      </label>
      <label className="text-sm">
        <span className="mb-1 block font-medium">Nutzungsrechte</span>
        <select name="rights" required defaultValue="" className={input}>
          <option value="" disabled>Bitte wählen</option>
          <option value="own">Eigenes Material (selbst erstellt, abgebildete Personen einverstanden)</option>
          <option value="licensed">Lizenziert (Lizenz in Notiz angeben)</option>
          <option value="unknown">Ungeklärt (wird nicht gerendert)</option>
        </select>
      </label>
      <label className="text-sm">
        <span className="mb-1 block font-medium">Rechte-Notiz / Lizenz</span>
        <input name="note" className={input} placeholder="z.B. Artlist-Lizenz #123, Dreh 12.11." />
      </label>
      <label className="text-sm">
        <span className="mb-1 block font-medium">Tags</span>
        <input name="tags" className={input} placeholder="talking-head, büro" />
      </label>
      <label className="text-sm">
        <span className="mb-1 block font-medium">Verwendung</span>
        <select name="kind" className={input} defaultValue="">
          <option value="">Automatisch</option>
          <option value="logo">Logo</option>
        </select>
      </label>
      <div className="flex items-center gap-3 md:col-span-2">
        <button disabled={busy} className="rounded-lg bg-slate-900 px-3 py-1.5 text-sm font-medium text-white disabled:opacity-50">
          {busy ? "Lädt …" : "Hochladen"}
        </button>
        {status ? <span className="text-sm text-slate-600">{status}</span> : null}
      </div>
    </form>
  );
}
