"""Walk-Forward: Parameter nur im Lernfenster wählen, im Prüffenster unverändert messen. Entscheidungsregeln prüfen.

Auswahlregel (vor dem Blick auf das Prüffenster festgelegt, wie im Labor):
- Kennzahl: Sharpe der Tagesgewinne netto OHNE Rebate im Lernfenster.
- Kombinationen mit Order-zu-Fill über 5 im Lernfenster sind ausgeschlossen (harte Regel).
- Gewählt wird die Kombination mit dem besten Median aus sich selbst und ihren Raster-Nachbarn (Plateau statt Spitze).
"""
import pickle
import statistics
from types import SimpleNamespace

import numpy as np
import pandas as pd

from . import runner
from .config import DATA

E = runner.CFG["entscheidung"]
MAX_OF = runner.CFG["ausfuehrung"]["max_order_zu_fill"]
ACHSEN = {"dip": (0.5, 1.0, 1.5), "tp": (0.5, 1.0, 2.0), "trail": (False, True)}


def name(p):
    return f"hybrid_dip{p['dip']}_tp{p['tp']}_{'trail' if p['trail'] else 'fest'}"


def laden(strategie: str, hebel: float = 3.0) -> dict:
    with open(DATA / "processed/laeufe" / f"{strategie}_hebel{hebel:g}.pkl", "rb") as f:
        d = pickle.load(f)
    markt = SimpleNamespace(index=d["index"], days=d["days"], coins=d["coins"])
    return {n: runner.Lauf(markt, hebel, x["params"], x["eq5"], x["MV"], x["TV"], x["FU"], x["daily"], x["trades"],
                           x["st"], x["ORD"], x["FIL"]) for n, x in d["laeufe"].items()}


def nachbarn(p):
    out = []
    for achse, werte in ACHSEN.items():
        i = werte.index(p[achse])
        for j in (i - 1, i + 1):
            if 0 <= j < len(werte):
                out.append({**p, achse: werte[j]})
    return out


def waehlen(laeufe: dict, von, bis) -> tuple[dict, pd.DataFrame]:
    """Plateau-Wahl im Fenster [von, bis). Gibt die gewählten Parameter und die Lerntabelle zurück."""
    zeilen = {}
    for p in runner.RASTER:
        k = runner.kennzahlen(laeufe[name(p)], von, bis)
        erlaubt = k["order_zu_fill"] <= MAX_OF
        zeilen[name(p)] = {**p, "sharpe": k["sharpe_ohne"], "rendite_ohne": k["rendite_ohne"], "dd_ohne": k["dd_ohne"],
                           "order_zu_fill": k["order_zu_fill"], "trades": k["trades"], "erlaubt": erlaubt,
                           "score": k["sharpe_ohne"] if erlaubt else -9.0}
    for p in runner.RASTER:
        werte = [zeilen[name(p)]["score"]] + [zeilen[name(q)]["score"] for q in nachbarn(p)]
        zeilen[name(p)]["plateau"] = statistics.median(werte) if zeilen[name(p)]["erlaubt"] else -9.0
    t = pd.DataFrame(zeilen).T
    beste = t["plateau"].astype(float).idxmax()
    return {k: zeilen[beste][k] for k in ACHSEN}, t


def urteil(hyb: dict, base: dict, stat: dict) -> list[dict]:
    """Die nicht verhandelbaren Entscheidungsregeln, jeweils mit Messwert."""
    def z(x):
        return x == x  # nicht NaN
    regeln = [
        ("Netto ohne Rebate ≥ reine Swing-Baseline", hyb["rendite_ohne"] >= base["rendite_ohne"],
         f"{hyb['rendite_ohne']:+.1%} gegen {base['rendite_ohne']:+.1%}"),
        ("Ergebnis vor Gebühren ≥ 0", hyb["rendite_brutto"] >= E["vor_gebuehren_min"], f"{hyb['rendite_brutto']:+.1%}"),
        ("Max. Drawdown < 15 %", hyb["dd_ohne"] < E["max_drawdown"], f"{hyb['dd_ohne']:.1%}"),
        ("≥ 300 Trades", hyb["trades"] >= E["min_trades_oos"], f"{hyb['trades']}"),
        ("Kein Paar > 50 % des Gewinns", z(hyb["anteil_coin"]) and hyb["anteil_coin"] <= E["max_anteil_paar"],
         f"{hyb['anteil_coin']:.0%} ({hyb['top_coin']})" if z(hyb["anteil_coin"]) else "kein Gewinn"),
        ("Kein Monat > 50 % des Gewinns", z(hyb["anteil_monat"]) and hyb["anteil_monat"] <= E["max_anteil_monat"],
         f"{hyb['anteil_monat']:.0%} ({hyb['top_monat']})" if z(hyb["anteil_monat"]) else "kein Gewinn"),
        ("Order-zu-Fill ≤ 5:1", hyb["order_zu_fill"] <= MAX_OF, f"{hyb['order_zu_fill']:.2f}:1"),
        # Der Rechenkern stellt solche Orders gar nicht erst ein; gezählt wird, wie oft er das verhindern musste.
        ("Nie Orders, die gegeneinander laufen", True, f"0 Fälle ({stat['verstoesse_beide_seiten']} Order vorsorglich nicht eingestellt)"),
        ("Mindest-Standzeit ≥ 5 Minuten", stat["min_standzeit_min"] >= 5, f"{stat['min_standzeit_min']:.0f} Min."),
    ]
    return [{"regel": r, "ok": bool(ok), "wert": w} for r, ok, w in regeln]


def split_datum(index: pd.DatetimeIndex, anteil: float) -> pd.Timestamp:
    return (index[0] + (index[-1] - index[0]) * anteil).normalize()


def rollierend(laeufe: dict, lern_monate: int, test_monate: int) -> pd.DataFrame:
    """Rollierende Fenster: je Fenster im Lernteil wählen, im folgenden Testteil messen."""
    idx = laeufe["baseline"].markt.index
    start = idx[0].normalize() + pd.offsets.MonthBegin(1)
    zeilen = []
    while True:
        lern_ende = start + pd.DateOffset(months=lern_monate)
        test_ende = lern_ende + pd.DateOffset(months=test_monate)
        if test_ende > idx[-1]:
            break
        p, _ = waehlen(laeufe, start, lern_ende)
        h = runner.kennzahlen(laeufe[name(p)], lern_ende, test_ende)
        b = runner.kennzahlen(laeufe["baseline"], lern_ende, test_ende)
        s = runner.kennzahlen(laeufe["swing_limit"], lern_ende, test_ende)
        zeilen.append({"test_von": lern_ende.date(), "test_bis": test_ende.date(), **{f"p_{k}": v for k, v in p.items()},
                       "hybrid_ohne": h["rendite_ohne"], "hybrid_mit": h["rendite_mit"], "hybrid_brutto": h["rendite_brutto"],
                       "baseline_ohne": b["rendite_ohne"], "baseline_mit": b["rendite_mit"],
                       "swing_limit_ohne": s["rendite_ohne"], "hybrid_dd": h["dd_ohne"], "baseline_dd": b["dd_ohne"],
                       "hybrid_trades": h["trades"], "hybrid_vol_tag": h["volumen_tag"], "baseline_vol_tag": b["volumen_tag"]})
        start = start + pd.DateOffset(months=test_monate)
    return pd.DataFrame(zeilen)
