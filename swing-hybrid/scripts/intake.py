"""Hochgeladene ZIP sicher nach data/raw/<name>/ entpacken und eine Inventur schreiben.

Aufruf (immer mit -I, die Daten sind fremd):
    .venv/bin/python -I scripts/intake.py <zip> [<name>]

Übersprungen wird alles, was wir nicht brauchen oder nicht sehen sollen: fremde Python-Umgebungen
(.venv, .python), Fremdcode (vendor) und Dateien mit Zugangsdaten (.env).

- prüft Pfade (kein ../, keine absoluten Pfade, keine Symlinks), führt nichts aus
- schreibt data/raw/<name>/_inventur.csv (Pfad, Endung, Größe)
"""
import csv
import sys
import zipfile
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKIP_ORDNER = {".venv", ".python", "vendor", "node_modules", "__pycache__", ".git"}
SKIP_DATEIEN = {".env"}


def entpacken(zip_pfad: Path, name: str) -> Path:
    ziel = ROOT / "data" / "raw" / name
    ziel.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_pfad) as z:
        for info in z.infolist():
            p = Path(info.filename)
            if p.is_absolute() or ".." in p.parts:
                raise ValueError(f"unsicherer Pfad in ZIP: {info.filename}")
            if info.is_dir() or SKIP_ORDNER & set(p.parts) or p.name in SKIP_DATEIEN:
                continue
            if (info.external_attr >> 16) & 0o170000 == 0o120000:
                print(f"  übersprungen (Symlink): {info.filename}")
                continue
            z.extract(info, ziel)
    return ziel


def inventur(ziel: Path) -> None:
    dateien = [p for p in ziel.rglob("*") if p.is_file() and p.name != "_inventur.csv"]
    with open(ziel / "_inventur.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["pfad", "endung", "bytes"])
        for p in sorted(dateien):
            w.writerow([p.relative_to(ziel), p.suffix.lower(), p.stat().st_size])
    endungen = Counter(p.suffix.lower() for p in dateien)
    groesse = sum(p.stat().st_size for p in dateien)
    print(f"{len(dateien)} Dateien, {groesse / 1e6:.1f} MB: {dict(endungen.most_common())}")


if __name__ == "__main__":
    zp = Path(sys.argv[1])
    nm = sys.argv[2] if len(sys.argv) > 2 else zp.stem
    inventur(entpacken(zp, nm))
