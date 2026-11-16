"""Gesamtschätzung für den unveränderten Kandidaten über alle vier Coin-Gruppen (60 Coins). Keine Auswahl."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
import numpy as np
import pandas as pd
from hybrid import research as R, runner

ROOT = Path(__file__).resolve().parents[1]
pd.set_option("display.width", 250)
AUS = 9.0
r4 = json.loads((ROOT / "reports/suche_runde4.json").read_text())
r5 = json.loads((ROOT / "reports/suche_runde5.json").read_text())
G = {"A": R.GRUPPE_A, "B": R.GRUPPE_B, "C": r4["gruppe_c"], "D": r5["gruppe_d"]}
FEN = {"Entwicklung": (None, R.SPLIT), "Pruefung": (R.SPLIT, None), "Gesamt": (None, None)}
K = ["G", "F", "R", "handel", "N", "dd_mit", "vol_tag", "sharpe"]
out = {"gruppen": {}}
for g, coins in G.items():
    m = R.markt(coins)
    l = R.lauf(m, R.auf_raster(m, R.variante(m, "basis")), taker=True, day_limit=AUS)
    out["gruppen"][g] = {f: {k: R.sicht(l, *FEN[f])[k] for k in K} for f in FEN}
print("Je Gruppe, Hebel 1 ohne Tageslimit:")
print(pd.DataFrame({g: {f"{f}_{k}": v[f][k] for f in ("Entwicklung", "Pruefung") for k in ("G", "N", "dd_mit")} for g, v in out["gruppen"].items()}).round(3).to_string())
alle = sum(G.values(), [])
m = R.markt(alle)
w = R.auf_raster(m, R.variante(m, "basis"))
for h in (1, 0.75, 0.5, 0.4, 0.35, 0.3, 0.25, 0.2, 0.15, 0.1):
    l = R.lauf(m, w, hebel=h, taker=True)
    if R.sicht(l, *FEN["Entwicklung"])["dd_mit"] <= 0.10:
        break
out["hebel"] = h
out["alle"] = {f: {k: R.sicht(l, *FEN[f])[k] for k in K + ["trades", "halte_h"]} for f in FEN}
out["orders"] = runner.order_statistik(l)
jahre = {}
for nm, fees in (("G", runner.BRUTTO), ("ohne", runner.OHNE), ("N", runner.MIT)):
    tg = l.daily_pnl(fees).sum(axis=1)
    jahre[nm] = tg.groupby(tg.index.year).sum()
j = pd.DataFrame(jahre); j["R"] = j["N"] - j["ohne"]
out["jahre"] = {str(k): x for k, x in j.round(5).T.to_dict().items()}
out["slippage"] = {str(bp): {k: R.sicht(R.lauf(m, w, hebel=h, taker=True, slip=bp / 1e4), *FEN["Pruefung"])[k] for k in ("G", "N")}
                   for bp in (0, 2.5, 5, 7.5, 10)}
print(f"\nAlle {len(alle)} Coins, Hebel {h} mit Tageslimit:"); print(pd.DataFrame(out["alle"]).T.round(3).to_string())
print(j.round(3).to_string()); print("Slippage Prüfzeitraum N:", {k: round(x["N"], 3) for k, x in out["slippage"].items()})
l1 = R.lauf(m, w, taker=True, day_limit=AUS)
echt = R.sicht(l1, R.SPLIT, None)["N"]
rng = np.random.default_rng(17)
T = w.shape[1]
z = [R.sicht(R.lauf(m, np.ascontiguousarray(np.roll(w, int(rng.integers(288 * 30, T - 288 * 30)), axis=1)), taker=True, day_limit=AUS),
             R.SPLIT, None)["N"] for _ in range(200)]
out["zufall_pruefung"] = {"perzentil": float((np.array(z) < echt).mean() * 100), "echt": echt, "median": float(np.median(z)),
                          "p90": float(np.percentile(z, 90))}
print("Zufallstest Prüfzeitraum:", out["zufall_pruefung"])
out["tage"] = {"Pruefung": (m.index[-1] - pd.Timestamp(R.SPLIT)).days + 1, "Gesamt": (m.index[-1] - m.index[0]).days + 1}
out["n_coins"] = len(alle)
(ROOT / "reports/gesamt_60.json").write_text(json.dumps(out, indent=1, default=float))
