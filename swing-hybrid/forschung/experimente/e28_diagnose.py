"""E28, nachträgliche Diagnose zu Grenze (a) (Protokoll Abschnitt 57): Signal eine Stunde früher gemessen, damit Signal und Ertrag
keinen Kurs teilen. Kein Urteil; die Einstufung aus e28_nichtkrypto bleibt.

    python -m forschung.experimente.e28_diagnose            (aus swing-hybrid/; schreibt ergebnisse/e28_diagnose.json)
"""
import datetime as dt
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from forschung.experimente import e28_nichtkrypto as E

ERGEBNIS = ROOT / "forschung/ergebnisse/e28_diagnose.json"


def fassung(je_we: list) -> dict:
    """je_we: Liste von (w, m, spannen) je Wochenende. Steigungen, t-Test und Handelsfassung in Richtung Umkehr."""
    from scipy import stats
    st = np.array([E.steigung(w, m) for w, m, _ in je_we])
    t, p = stats.ttest_1samp(st, 0.0)
    n85 = np.array([E.handel(w, m, sp, -1)["n85"] for w, m, sp in je_we])
    return {"steigung_mittel": float(st.mean()), "steigung_median": float(np.median(st)), "t": float(t), "p": float(p),
            "anteil_negativ": float(np.mean(st < 0)), "handel_n85_mittel": float(n85.mean()),
            "handel_t_n85": float(n85.mean() / (n85.std(ddof=1) / np.sqrt(len(n85)))), "handel_anteil_positiv": float(np.mean(n85 > 0))}


def diagnose(kurse: dict, spannen: dict, bis_ms: int) -> dict:
    syms = sorted(kurse)
    von = min(min(k) for k in kurse.values() if k)
    frueh, haupt, zahl = [], [], []
    for a, b, c in E.wochenenden(von, bis_ms):
        vor = b - E.H                                                  # Sonntag 22:00 UTC
        haupt_dabei = [s for s in syms if a in kurse[s] and b in kurse[s] and c in kurse[s]]
        if len(haupt_dabei) < E.MIN_KONTRAKTE_WE:
            continue                                                   # dieselben Wochenenden wie in Teil 2
        dabei = [s for s in haupt_dabei if vor in kurse[s]]
        sp = np.array([spannen[s] for s in dabei])
        m = np.array([kurse[s][c] / kurse[s][b] - 1 for s in dabei])
        w0 = np.array([kurse[s][b] / kurse[s][a] - 1 for s in dabei])
        w1 = np.array([kurse[s][vor] / kurse[s][a] - 1 for s in dabei])
        if len(dabei) < E.MIN_KONTRAKTE_WE or not np.isfinite(E.steigung(w0, m)) or not np.isfinite(E.steigung(w1, m)):
            continue
        haupt.append((w0, m, sp)); frueh.append((w1, m, sp)); zahl.append((len(haupt_dabei), len(dabei)))
    return {"wochenenden": len(zahl), "kontrakte_teil_2": [x for x, _ in zahl], "kontrakte_mit_vier_kursen": [y for _, y in zahl],
            "hauptfassung_auf_denselben_kontrakten": fassung(haupt), "signal_eine_stunde_frueher": fassung(frueh)}


def haupt() -> dict:
    from forschung.experimente import e28_daten as D
    sp = {r.symbol: float(r.spanne_bp) for r in D.kandidaten().itertuples()}
    kurse = {}
    for sym in D.universum_teil2().symbol:
        datei = D.ZIEL / "teil2" / f"{sym}.npz"
        if datei.exists():
            with np.load(datei) as z:
                if len(z["zeit"]):
                    kurse[sym] = dict(zip((int(x) for x in z["zeit"]), (float(x) for x in z["ohlc"][:, 0])))
    erg = dict(diagnose(kurse, sp, int(D.YUBIT_BIS.timestamp() * 1000)), festlegung="forschung/protokoll.md Abschnitt 57 (nachträgliche Diagnose, kein Urteil)")
    ERGEBNIS.write_text(json.dumps(E.sauber(erg), ensure_ascii=False, indent=1, allow_nan=False))
    return erg


if __name__ == "__main__":
    e = haupt()
    print(e["wochenenden"], "Wochenenden; Kontrakte mit vier Kursen:", min(e["kontrakte_mit_vier_kursen"]), "bis", max(e["kontrakte_mit_vier_kursen"]))
    for k in ("hauptfassung_auf_denselben_kontrakten", "signal_eine_stunde_frueher"):
        print(k, {a: round(b, 4) for a, b in e[k].items()})
