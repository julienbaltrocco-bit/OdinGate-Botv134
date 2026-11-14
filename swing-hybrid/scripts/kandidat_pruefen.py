"""Belastungsproben für den Kandidaten aus Runde 3 (keine Auswahl mehr, nur Einordnung)."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
import numpy as np
import pandas as pd
from hybrid import research as R, runner

ROOT = Path(__file__).resolve().parents[1]
pd.set_option("display.width", 250, "display.max_columns", 40)
r3 = json.loads((ROOT / "reports/suche_runde3.json").read_text())
name = next(n for n, e in r3["finalisten"].items() if e.get("loesung"))
e = r3["finalisten"][name]
H = e["stufen"]["5_hebel"]["hebel"]
mA, mB = R.markt(R.GRUPPE_A), R.markt(R.GRUPPE_B)
wA = R.auf_raster(mA, R.FAMILIEN[e["familie"]](mA, **e["params"]))
wB = R.auf_raster(mB, R.FAMILIEN[e["familie"]](mB, **e["params"]))
F = {"Entwicklung": (None, R.SPLIT), "Pruefung": (R.SPLIT, None), "Gesamt": (None, None)}
KEYS = ["G", "F", "R", "handel", "N", "dd_mit", "vol_tag", "bp_je_umsatz", "trades", "halte_h", "sharpe", "jahr_N"]
out = {"name": name, "hebel": H, "params": e["params"]}


def drei(l):
    return {k: {x: R.sicht(l, *F[k])[x] for x in KEYS} for k in F}


# 1) Slippage
out["slippage"] = {}
for bp in (0, 2.5, 5, 7.5, 10):
    out["slippage"][str(bp)] = drei(R.lauf(mA, wA, hebel=H, taker=True, slip=bp / 1e4))
print("Slippage (Gruppe A, Hebel", H, "):")
print(pd.DataFrame({bp: {f"{k}_{x}": v[k][x] for k in ("Entwicklung", "Pruefung") for x in ("G", "N")} for bp, v in out["slippage"].items()}).round(3).to_string())
# 2) Jahr für Jahr
l = R.lauf(mA, wA, hebel=H, taker=True)
jahre = {}
for name_f, fees in (("G", runner.BRUTTO), ("ohne", runner.OHNE), ("N", runner.MIT)):
    tg = l.daily_pnl(fees).sum(axis=1)
    jahre[name_f] = tg.groupby(tg.index.year).sum()
j = pd.DataFrame(jahre)
j["F"] = j["G"] - j["ohne"]; j["R"] = j["N"] - j["ohne"]
out["jahre"] = {str(k): v for k, v in j.round(5).T.to_dict().items()}
print("Jahr für Jahr (Gruppe A, Hebel", H, "):"); print(j.round(3).to_string())
tg = l.daily_pnl(runner.MIT).sum(axis=1)
mon = tg.groupby(tg.index.to_period("M")).sum()
out["monate_positiv"] = float((mon > 0).mean()); out["monate"] = int(len(mon))
out["schlechtester_monat"] = float(mon.min()); out["bester_monat"] = float(mon.max())
t = l.trades
netto = t["brutto"] - runner.MAKER * (1 - 0.85) * t["maker_vol"] - runner.TAKER * (1 - 0.85) * t["taker_vol"]
out["trefferquote"] = float((netto > 0).mean()); out["trades_tag"] = float(len(t) / (len(mA.index) / 288))
out["orders"] = runner.order_statistik(l)
out["basis"] = drei(l)
# 3) passiv beim selben Hebel, mit Tageslimit
out["passiv"] = drei(R.lauf(mA, wA, hebel=H))
# 4) Gruppe B und beide Gruppen zusammen
out["gruppe_b"] = drei(R.lauf(mB, wB, hebel=H, taker=True))
print("Gruppe B:", {k: {x: round(v[x], 3) for x in ("G", "N", "dd_mit")} for k, v in out["gruppe_b"].items()})
print("passiv:", {k: {x: round(v[x], 3) for x in ("G", "handel", "N", "R", "dd_mit")} for k, v in out["passiv"].items()})
# 5) Zufallstest nur im Prüfzeitraum
rng = np.random.default_rng(11)
echt = R.sicht(R.lauf(mA, wA, taker=True, day_limit=9.0), R.SPLIT, None)["N"]
T = wA.shape[1]
z = [R.sicht(R.lauf(mA, np.ascontiguousarray(np.roll(wA, int(rng.integers(288 * 30, T - 288 * 30)), axis=1)), taker=True, day_limit=9.0),
             R.SPLIT, None)["N"] for _ in range(200)]
out["zufall_pruefung"] = {"perzentil": float((np.array(z) < echt).mean() * 100), "echt": echt, "median": float(np.median(z)),
                          "p90": float(np.percentile(z, 90)), "max": float(np.max(z))}
print("Zufallstest nur Prüfzeitraum:", out["zufall_pruefung"])
# 6) Kapital
p = out["basis"]["Pruefung"]; g = out["basis"]["Gesamt"]
tage_p = (mA.index[-1] - pd.Timestamp(R.SPLIT)).days + 1; tage_g = (mA.index[-1] - mA.index[0]).days + 1
out["tage"] = {"Pruefung": tage_p, "Gesamt": tage_g}
print("Tage:", out["tage"], "| Prüfung: Volumen/Tag", round(p["vol_tag"], 3), "Rebate/Tag", round(p["R"] / tage_p, 6), "Netto/Tag", round(p["N"] / tage_p, 6))
print("Orders:", out["orders"], "Treffer", round(out["trefferquote"], 3), "Monate positiv", round(out["monate_positiv"], 2))
(ROOT / "reports/kandidat.json").write_text(json.dumps(out, indent=1, default=float))
