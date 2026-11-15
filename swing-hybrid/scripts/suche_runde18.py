"""Runde 18: Plimaflow-Signale (Score >= 0,60) als Short mit Ziel 10 % / Stop 8 % auf Binance-Minutenkerzen."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
import numpy as np
import pandas as pd
from hybrid import pumpshort as P

ROOT = Path(__file__).resolve().parents[1]
pd.set_option("display.width", 220)
EINSATZ, TEILUNG, ERSATZ_AB = 0.10, pd.Timestamp("2026-10-01"), pd.Timestamp("2026-11-01")
h = pd.read_parquet(ROOT / "data/raw/plimaflow/historie.parquet")
q = h[h.p_win >= 0.6].sort_values("signal_time")
q = q.assign(sym=q.symbol.str.replace("-", ""))
sp = pd.read_csv(ROOT / "data/processed/yubit_spannen_stichprobe.csv")
sp["halb"] = (sp["brief"] - sp["geld"]) / (sp["brief"] + sp["geld"])
spanne = sp.groupby("symbol")["halb"].mean() * 2
coins = sorted(q.sym.unique())
slip_y = pd.Series({c: max(0.00005, float(spanne[c])) for c in coins if c in spanne.index})
slip_median = float(slip_y.median())

alle, ohne_kurs = [], []
for c in coins:
    p = ROOT / f"data/candles/pump_1m/{c}.parquet"
    if not p.exists():
        ohne_kurs.append(c); continue
    s = q[q.sym == c]
    t = pd.DataFrame(P.trades_coin(pd.read_parquet(p), list(s.signal_time)))
    if t.empty:
        continue
    slip = float(slip_y.get(c, slip_median))
    fp = ROOT / f"data/candles/pump_funding/{c}.parquet"
    raten = pd.read_parquet(fp)["rate"] if fp.exists() else None
    ers = s.set_index("signal_time")["funding_rate"].reindex(t["signal"]).fillna(0.0).to_numpy()
    t["coin"], t["yubit"], t["slip"] = c, c in slip_y.index, slip
    t["funding"] = P.funding(t, raten, pd.Series(ers), ERSATZ_AB)
    t["k_mit"] = P.kosten(t, slip); t["k_ohne"] = P.kosten(t, slip, rebate=0.0); t["k_stress"] = P.kosten(t, slip, slip_faktor=2.0)
    alle.append(t)
t = pd.concat(alle, ignore_index=True).sort_values("ein_zeit").reset_index(drop=True)
t["netto"] = t["roh"] + t["funding"] - t["k_mit"]
t["netto_ohne"] = t["roh"] + t["funding"] - t["k_ohne"]
t["netto_stress"] = t["roh"] + t["funding"] - t["k_stress"]
t["stunden"] = (t["aus_zeit"] - t["ein_zeit"]).dt.total_seconds() / 3600
t.to_csv(ROOT / "reports/suche_runde18_trades.csv", index=False)


def block(x):
    if x.empty:
        return {"trades": 0}
    return {"trades": int(len(x)), "coins": int(x.coin.nunique()), "ziel": float((x.art == "ziel").mean()), "stop": float((x.art == "stop").mean()),
            "zeit": float(x.art.isin(["zeit", "ende"]).mean()), "roh_mittel": float(x.roh.mean()), "funding_mittel": float(x.funding.mean()),
            "kosten_mittel": float(x.k_mit.mean()), "netto_mittel": float(x.netto.mean()), "netto_ohne_mittel": float(x.netto_ohne.mean()),
            "netto_stress_mittel": float(x.netto_stress.mean()), "konto_netto": float(x.netto.sum() * EINSATZ),
            "konto_ohne_rebate": float(x.netto_ohne.sum() * EINSATZ), "konto_stress": float(x.netto_stress.sum() * EINSATZ),
            "schlechtester": float(x.netto.min()), "stunden_median": float(x.stunden.median())}


out = {"signale": int(len(q)), "coins": len(coins), "ohne_binance_kurs": ohne_kurs, "slip_median": slip_median,
       "alle": block(t), "haelfte_1": block(t[t.ein_zeit < TEILUNG]), "haelfte_2": block(t[t.ein_zeit >= TEILUNG]),
       "nur_yubit": block(t[t.yubit]), "nur_yubit_h1": block(t[t.yubit & (t.ein_zeit < TEILUNG)]), "nur_yubit_h2": block(t[t.yubit & (t.ein_zeit >= TEILUNG)])}
print(pd.DataFrame({k: out[k] for k in ("alle", "haelfte_1", "haelfte_2", "nur_yubit", "nur_yubit_h1", "nur_yubit_h2")}).round(4).to_string())
rng = np.random.default_rng(18)
tage = t.groupby(t.ein_zeit.dt.date)["netto"].agg(["sum", "count"])
z = []
for _ in range(2000):
    i = rng.integers(0, len(tage), len(tage))
    z.append(tage["sum"].to_numpy()[i].sum() / tage["count"].to_numpy()[i].sum())
out["zufall"] = {"anteil_positiv": float((np.array(z) > 0).mean()), "p5": float(np.percentile(z, 5)), "p95": float(np.percentile(z, 95)), "handelstage": int(len(tage))}
je = t.groupby("coin")["netto"].agg(["sum", "count"]).sort_values("sum")
gewinn = je["sum"][je["sum"] > 0]
out["groesster_coin_anteil"] = float(gewinn.max() / t.netto.sum()) if t.netto.sum() > 0 else None
out["je_coin"] = je.round(4).to_dict("index")
a = out["alle"]
out["huerden"] = {"1": bool(out["haelfte_1"].get("konto_netto", -1) > 0 and out["haelfte_2"].get("konto_netto", -1) > 0 and a["trades"] >= 100),
                  "2": bool(a["konto_stress"] > 0), "3": bool(out["zufall"]["anteil_positiv"] >= 0.95),
                  "4": bool(out["groesster_coin_anteil"] is not None and out["groesster_coin_anteil"] <= 0.5)}
print("Zufallstest:", out["zufall"]); print("Hürden:", out["huerden"], "| größter Coin-Anteil:", out["groesster_coin_anteil"])
print(pd.concat([je.head(6), je.tail(6)]).round(3).to_string())
m = t.groupby(t.ein_zeit.dt.to_period("M"))["netto"].agg(["sum", "count", "mean"]); print(m.round(4).to_string())
out["monate"] = {str(k): v for k, v in m.round(5).to_dict("index").items()}
(ROOT / "reports/suche_runde18.json").write_text(json.dumps(out, indent=1, default=float))
