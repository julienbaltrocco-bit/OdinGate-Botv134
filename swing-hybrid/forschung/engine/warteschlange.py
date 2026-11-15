"""Lokale Experiment-Warteschlange: führt vollständig festgelegte Rechnungen ohne KI aus.

  python3 -m forschung.engine.warteschlange            (aus swing-hybrid/)

warteschlange.json: Liste von {"id", "befehl": [Skript, Argumente...], "status": "wartet"}. Ein Eintrag darf erst
aufgenommen werden, wenn seine Festlegung im Protokoll steht und gesichert ist. Die Schlange rechnet einen Eintrag
nach dem anderen (Sperre gegen Doppelläufe), prüft vorher Speicher, Arbeitsspeicher und Last, schreibt den Status
nach jedem Schritt atomar und setzt nach einem Absturz dort wieder an. Neue Ideen entwickelt sie nicht; das braucht
eine KI-Sitzung (siehe AUFTRAG.md). Nur Standardbibliothek; die Experimente selbst brauchen die Python-Umgebung.
"""
import fcntl
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

F = Path(__file__).resolve().parents[1]
DATEI = F / "engine/warteschlange.json"
PY = F.parent / ".venv/bin/python"
ZEITLIMIT = 3600


def speichern(q):
    tmp = DATEI.with_suffix(".teil")
    tmp.write_text(json.dumps(q, ensure_ascii=False, indent=1))
    tmp.replace(DATEI)


def ressourcen():
    frei_gb = shutil.disk_usage(F).free / 2 ** 30
    ram_gb = next((int(z.split()[1]) / 2 ** 20 for z in open("/proc/meminfo") if z.startswith("MemAvailable")), 99.0)
    last = os.getloadavg()[0] / (os.cpu_count() or 1)
    grund = "Speicherplatz unter 2 GB" if frei_gb < 2 else "Arbeitsspeicher unter 1 GB" if ram_gb < 1 else "Last über 150 %" if last > 1.5 else None
    return grund, {"frei_gb": round(frei_gb, 1), "ram_gb": round(ram_gb, 1), "last": round(last, 2)}


def haupt():
    (F / "engine/protokolle").mkdir(exist_ok=True)
    sperre = open(F / "engine/protokolle/warteschlange.sperre", "w")
    try:
        fcntl.flock(sperre, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        print("Warteschlange läuft bereits"); return 3
    q = json.loads(DATEI.read_text()) if DATEI.exists() else []
    for e in q:                                           # Absturz während einer Rechnung: einmal neu versuchen
        if e["status"] == "läuft":
            e["status"] = "wartet" if e.get("versuche", 0) < 2 else "gescheitert"
    speichern(q)
    for e in q:
        if e["status"] != "wartet":
            continue
        grund, r = ressourcen()
        if grund:
            print("Pause:", grund, r); return 4           # kritischer Zustand: nichts starten, Stand bleibt gesichert
        e.update(status="läuft", begonnen=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), versuche=e.get("versuche", 0) + 1)
        speichern(q)
        log = F / "engine/protokolle" / f"{e['id']}.log"
        try:
            with open(log, "w") as f:
                code = subprocess.run([str(PY), "-I", *e["befehl"]], cwd=F.parent, stdout=f, stderr=subprocess.STDOUT, timeout=ZEITLIMIT).returncode
        except subprocess.TimeoutExpired:
            code = -9
        e.update(status="fertig" if code == 0 else "gescheitert", beendet=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), rueckgabe=code, ressourcen=r)
        speichern(q)
        print(e["id"], e["status"])
    return 0


if __name__ == "__main__":
    sys.exit(haupt())
