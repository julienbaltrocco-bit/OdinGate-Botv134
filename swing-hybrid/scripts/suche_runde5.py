"""Runde 5: Risikosteuerung, Trend-Mischung und Funding-Carry auf 40 Coins; Gruppe D als frische Gegenprobe."""
import json
import re
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
import numpy as np
import pandas as pd
from hybrid import research as R, runner
from hybrid.config import DATA

ROOT = Path(__file__).resolve().parents[1]
pd.set_option("display.width", 260, "display.max_columns", 60)
AUS = 9.0
FEN = {"D1": (None, R.D1_ENDE), "D2": (R.D1_ENDE, R.SPLIT), "Entwicklung": (None, R.SPLIT), "Pruefung": (R.SPLIT, None),
       "Gesamt": (None, None)}
SP = ["G", "F", "R", "handel", "N", "dd_mit", "vol_tag", "bp_je_umsatz", "trades", "sharpe", "jahr_N"]
r4 = json.loads((ROOT / "reports/suche_runde4.json").read_text())
C = r4["gruppe_c"]
LISTE_D = ("IOTA NEO ONT QTUM XTZ RUNE KAVA BAT ZRX YFI HBAR LRC OCEAN ONE STORJ ANKR RLC BAND KNC ZEN CELR COTI SKL IOST ICX "
           "RVN TRB MTL CHR HOT DENT").split()


def vollstaendig(coin):
    log = "".join((DATA / "candles" / f).read_text() for f in ("download3.log", "download5.log"))
    return all(re.search(rf"^{art} {coin}USDT: .*fehlende Monate: keine$", log, re.M) for art in ("5m", "funding"))


def tab(d, sp=SP):
    return pd.DataFrame(d).T[sp].round(3).to_string()


def fenster(l, namen):
    return {k: R.sicht(l, *FEN[k]) for k in namen}


def hebel_lauf(m, w):
    for h in (5, 4, 3, 2.5, 2, 1.5, 1, 0.75, 0.5, 0.4, 0.35, 0.3, 0.25, 0.2, 0.15, 0.1):
        l = R.lauf(m, w, hebel=h, taker=True)
        if R.sicht(l, *FEN["Entwicklung"])["dd_mit"] <= 0.10:
            return h, l
    return None, None


t0 = time.time()
m = R.markt(R.GRUPPE_A + R.GRUPPE_B + C)
W, dev = {}, {}
for v in ("basis", "vol_coin", "vol_markt", "vol_beide", "mischung", "carry"):
    W[v] = R.auf_raster(m, R.variante(m, v))
    dev[v] = fenster(R.lauf(m, W[v], taker=True, day_limit=AUS), ("D1", "D2", "Entwicklung"))


def score(v):
    return min(dev[v]["D1"]["sharpe"], dev[v]["D2"]["sharpe"])


def besteht(v):
    return all(dev[v][f]["G"] > 0 and dev[v][f]["N"] > 0 for f in ("D1", "D2"))


trend = [v for v in ("basis", "vol_coin", "vol_markt", "vol_beide", "mischung")]
bester_trend = max(trend, key=lambda v: score(v) if besteht(v) else -9)
if besteht("carry"):
    W["trend_carry"] = 0.5 * W[bester_trend] + 0.5 * W["carry"]
    dev["trend_carry"] = fenster(R.lauf(m, W["trend_carry"], taker=True, day_limit=AUS), ("D1", "D2", "Entwicklung"))
print("ENTWICKLUNG (40 Coins, Hebel 1, ohne Tageslimit)")
z = {v: {"besteht": besteht(v), "score": score(v), **{f"{f}_{k}": dev[v][f][k] for f in ("D1", "D2") for k in ("G", "N", "sharpe")},
         **{k: dev[v]["Entwicklung"][k] for k in ("G", "N", "dd_mit", "vol_tag", "bp_je_umsatz", "sharpe", "jahr_N")}} for v in dev}
print(pd.DataFrame(z).T.round(3).to_string())
kandidaten = [v for v in dev if v != "basis" and besteht(v) and score(v) >= score("basis") + 0.10]
gewinner = max(kandidaten, key=score) if kandidaten else "basis"
print("Bester Trend:", bester_trend, "| carry besteht allein:", besteht("carry"), "| Gewinnerin:", gewinner)
out = {"entwicklung": z, "gewinnerin": gewinner, "bester_trend": bester_trend, "mehrwert": gewinner != "basis"}

# ---- Hebel und Prüfzeitraum für Basis und Gewinnerin
for v in dict.fromkeys(["basis", gewinner]):
    h, l = hebel_lauf(m, W[v])
    e = out[f"hebel_{v}"] = {"hebel": h}
    if h is None:
        print(v, ": kein Hebel hält 10 %"); continue
    e.update(fenster(l, ("Entwicklung", "Pruefung", "Gesamt")))
    e["orders"] = runner.order_statistik(l)
    jahre = {}
    for nm, fees in (("G", runner.BRUTTO), ("ohne", runner.OHNE), ("N", runner.MIT)):
        tg = l.daily_pnl(fees).sum(axis=1)
        jahre[nm] = tg.groupby(tg.index.year).sum()
    j = pd.DataFrame(jahre); j["R"] = j["N"] - j["ohne"]
    e["jahre"] = {str(k): x for k, x in j.round(5).T.to_dict().items()}
    e["slippage"] = {str(bp): {k: R.sicht(R.lauf(m, W[v], hebel=h, taker=True, slip=bp / 1e4), *FEN["Pruefung"])[k] for k in ("G", "N")}
                     for bp in (0, 2.5, 5, 7.5, 10)}
    print(f"\n{v}: Hebel {h} mit Tageslimit"); print(tab({k: e[k] for k in ("Entwicklung", "Pruefung", "Gesamt")}))
    print(j.round(3).to_string()); print("Slippage Prüfzeitraum N:", {k: round(x["N"], 3) for k, x in e["slippage"].items()})

# ---- Gruppe D (frisch)
D = [c for c in LISTE_D if vollstaendig(c)][:20]
out["gruppe_d"] = D
print("\nGruppe D:", D)
mD = R.markt(D)
d = {}
for v in dict.fromkeys(["basis", gewinner]):
    if v == "trend_carry":
        w = 0.5 * R.auf_raster(mD, R.variante(mD, bester_trend)) + 0.5 * R.auf_raster(mD, R.variante(mD, "carry"))
    else:
        w = R.auf_raster(mD, R.variante(mD, v))
    d[v] = fenster(R.lauf(mD, w, taker=True, day_limit=AUS), ("Entwicklung", "Pruefung", "Gesamt"))
    d[v]["n_je_dd"] = d[v]["Gesamt"]["N"] / d[v]["Gesamt"]["dd_mit"]
    print(f"Gruppe D, {v} (Hebel 1, ohne Tageslimit): Netto je Einbruch {d[v]['n_je_dd']:.2f}"); print(tab({k: d[v][k] for k in ("Entwicklung", "Pruefung", "Gesamt")}))
out["D"] = d
g = d[gewinner]
out["bestaetigt"] = bool(gewinner != "basis" and g["Entwicklung"]["N"] > 0 and g["Pruefung"]["N"] > 0 and g["n_je_dd"] > d["basis"]["n_je_dd"])
out["basis_auf_D_positiv"] = bool(d["basis"]["Entwicklung"]["N"] > 0 and d["basis"]["Pruefung"]["N"] > 0)
print("Gewinnerin auf Gruppe D bestätigt:", out["bestaetigt"], "| Basis auf Gruppe D positiv:", out["basis_auf_D_positiv"])
out["tage"] = {"Pruefung": (m.index[-1] - pd.Timestamp(R.SPLIT)).days + 1, "Gesamt": (m.index[-1] - m.index[0]).days + 1}
(ROOT / "reports/suche_runde5.json").write_text(json.dumps(out, indent=1, default=float))
print(f"fertig in {time.time() - t0:.0f} s")
