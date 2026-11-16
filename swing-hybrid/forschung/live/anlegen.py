"""Legt zu einem bestehenden Fabrik-Papier-Test die Live-Fassung an (gleiche Regel, gleicher Start, Daten in Echtzeit).

  python3 forschung/live/anlegen.py B-dc1d27a3

Die Live-Fassung bekommt eine eigene, eingefrorene Kopie des Codes (mit Live-Modus im Papier-Rechner) und die
unveränderte Einstellung des Kandidaten. Der Schattentest bleibt als Kontrolle über die Archivdaten bestehen.
"""
import hashlib
import json
import shutil
import sys
import time
from pathlib import Path

F = Path(__file__).resolve().parents[1]
PAPIER = F / "papier"


def anlegen(quelle: str) -> int:
    alt = PAPIER / quelle
    cfg = json.loads((alt / "konfiguration.json").read_text())
    tid = "L-" + quelle.split("-", 1)[1]
    neu = PAPIER / tid
    if neu.exists():
        print(tid, "existiert bereits; nichts geändert."); return 0
    code = neu / "code"
    (code / "fabrik").mkdir(parents=True)
    for name in ("__init__", "daten", "signale", "kern", "lauf", "generator"):
        shutil.copy(F / "fabrik" / f"{name}.py", code / "fabrik" / f"{name}.py")
    shutil.copy(F / "fabrik/papier_fabrik.py", code / "papier_fabrik.py")
    # Die Handelsregel muss dieselbe sein wie im Schattentest: Signale, Simulator und Massenlauf-Kern Datei für Datei gleich
    for name in ("signale", "kern", "lauf", "generator", "daten"):
        if (code / "fabrik" / f"{name}.py").read_bytes() != (alt / "code/fabrik" / f"{name}.py").read_bytes():
            shutil.rmtree(neu); print(f"Abbruch: fabrik/{name}.py weicht vom eingefrorenen Stand des Schattentests ab."); return 2
    cfg.update(id=tid, modus="live", ersetzt=quelle, name=cfg["name"].replace("Beobachtung", "Live-Beobachtung"),
               art="Live-Papierhandel (Binance-Daten in Echtzeit, eigener Server, keine Orders)", eingefroren=time.strftime("%Y-%m-%d", time.gmtime()),
               freigabe=cfg.get("freigabe", "") + " Live-Fassung auf dem Server des Auftraggebers, auf dessen Wunsch (16.11.2026).")
    cfg["strategie_sha256"] = hashlib.sha256(b"".join(p.name.encode() + p.read_bytes() for p in sorted(code.rglob("*.py")))
                                             + json.dumps(cfg["kandidat"], sort_keys=True).encode()).hexdigest()
    (neu / "konfiguration.json").write_text(json.dumps(cfg, ensure_ascii=False, indent=1))
    (neu / "steuerung.json").write_text(json.dumps({"status": "laufend", "hinweis": "Pausieren: status 'pausiert'. Beenden: status 'beendet' und 'ende' (UTC)."}, ensure_ascii=False, indent=1))
    if (alt / "board.json").exists():
        b = json.loads((alt / "board.json").read_text())
        (neu / "board.json").write_text(json.dumps(b, ensure_ascii=False, indent=1))
    (neu / "plan.md").write_text(f"# Live-Test {tid}\n\nLive-Fassung von `{quelle}`: dieselbe eingefrorene Regel, derselbe Start ({cfg['start']}), dasselbe Papier-Konto-Modell.\n"
                                 f"Unterschied: Die Binance-Daten kommen in Echtzeit (alle fünf Minuten) statt mit einem Tag Verzug aus dem Archiv, und bei jedem neuen\n"
                                 f"Einstieg wird gemessen, was er am Yubit-Orderbuch gekostet hätte. Wertung, Erfolg und Abbruch wie in `papier/{quelle}/plan.md`.\n"
                                 f"Maßgeblich bleibt der Schattentest; weichen beide voneinander ab, gilt die Live-Fassung als fehlerhaft, bis die Ursache geklärt ist.\n")
    print(tid, "angelegt aus", quelle, "| Prüfsumme", cfg["strategie_sha256"][:12])
    return 0


if __name__ == "__main__":
    sys.exit(anlegen(sys.argv[1]))
