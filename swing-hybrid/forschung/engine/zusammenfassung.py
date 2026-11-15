"""Automatische Zusammenfassung nach jeweils zehn abgeschlossenen Experimenten (forschung/berichte/zusammenfassung_NNN.md).

Liest das Experiment-Buch (experimente.json), die Hypothesenliste, die Papier-Tests und deren letzten Stand.
Schreibt nur Blöcke, für die noch keine Datei existiert. Unterbricht nichts. Nur Standardbibliothek.
"""
import json
from pathlib import Path

F = Path(__file__).resolve().parents[1]
STUFEN = {"A": "verworfen", "B": "interessant, unbestätigt", "C": "vorläufig vielversprechend", "D": "Prüfung formal bestanden", "–": "Analyse"}


def schreiben():
    buch = json.loads((F / "engine/experimente.json").read_text())
    hyp = json.loads((F / "engine/hypothesen.json").read_text())
    (F / "berichte").mkdir(exist_ok=True)
    neu = []
    for block in range(len(buch) // 10):
        ziel = F / "berichte" / f"zusammenfassung_{block + 1:03d}.md"
        if ziel.exists():
            continue
        teil = buch[block * 10: block * 10 + 10]
        z = [f"# Zusammenfassung {block + 1}: Experimente {teil[0]['nr']} bis {teil[-1]['nr']}", "",
             "Automatisch erzeugt aus `engine/experimente.json`. Rückrechnungen, kein echtes Geld, keine Anlageberatung.", "",
             "## Experimente", "", "| Nr. | ID | Idee | Einstufung | Ergebnis |", "|---|---|---|---|---|"]
        z += [f"| {e['nr']} | {e['id']} | {e['titel']} | {e['einstufung']} ({STUFEN.get(e['einstufung'], '')}) | {e['kurz']} |" for e in teil]
        zahl = {s: sum(1 for e in teil if e["einstufung"] == s) for s in STUFEN}
        z += ["", "Verteilung: " + ", ".join(f"{n} × {STUFEN[s]}" for s, n in zahl.items() if n) + ".", "", "## Papier-Tests", ""]
        tests = sorted(F.glob("papier/*/konfiguration.json"))
        if not tests:
            z.append("Keine neuen Papier-Tests.")
        for c in tests:
            cfg = json.loads(c.read_text())
            st = F / "papier/ausgabe" / f"{cfg['id']}.json"
            d = json.loads(st.read_text()) if st.exists() else {}
            z.append(f"- **{cfg['id']} {cfg['name']} {cfg['version']}** (Start {cfg['start'][:10]}, Hebel {cfg['hebel']:g}): Status {d.get('status', 'noch kein Lauf')}, "
                     f"Trades {d.get('trades', 0)}, Kontostand {d.get('kontostand', cfg['kapital_usd'])} $, mit Rebate {d.get('rendite_mit_rebate_pct', 0)} %, "
                     f"ohne Rebate {d.get('rendite_ohne_rebate_pct', 0)} %. {cfg['validierung']}")
        for tid in ("T1", "T2"):
            st = F / "papier/ausgabe" / f"{tid}.json"
            if st.exists():
                d = json.loads(st.read_text())
                z.append(f"- **{d.get('name', tid)}**: Status {d.get('status')}, Kontostand {d.get('kontostand')} $, mit Rebate {d.get('rendite_mit_rebate_pct')} %, Stand {d.get('letzter_lauf')}.")
        z += ["", "## Offene Forschungsfragen", ""] + [f"- {h['id']} {h['titel']}: {h['mechanismus']}" for h in hyp if h["status"] == "offen"]
        z += ["", "## Risiken", "", "- Rebate von 85 % unbestätigt; ohne Rebate ist bisher keine kurzfristige Regel positiv.",
              "- Signale stammen aus Binance-Daten, gehandelt würde bei Yubit.", "- Margin- und Liquidationsregeln von Yubit sind unbekannt; gerechnet wird mit Annahmen.", ""]
        ziel.write_text("\n".join(z))
        neu.append(ziel.name)
    print("Zusammenfassungen:", neu or "keine neue fällig", f"({len(buch)} Experimente im Buch)")


if __name__ == "__main__":
    schreiben()
