"""Runde 22: Funding-Filter gegen den Kandidaten auf zeitlich unabhängigen Daten (Prüfzeitraum, Vorperiode)."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
import numpy as np
import pandas as pd
from hybrid import mutationen as M, research as R, runner

ROOT = Path(__file__).resolve().parents[1]
pd.set_option("display.width", 220)
G = json.loads((ROOT / "reports/suche_runde6.json").read_text())["gruppen"]
SPLIT = pd.Timestamp(R.SPLIT)
sharpe = lambda x: float(x.mean() / x.std() * np.sqrt(365)) if x.std() > 0 else 0.0


def tage(m, fn, kosten=1.0):
    l = R.lauf(m, R.auf_raster(m, fn(m)), taker=True, slip=kosten * R.yubit_kosten(m.coins)[0], day_limit=9.0)
    fees = runner.MIT if kosten == 1.0 else runner.Fees(runner.MAKER * kosten, runner.TAKER * kosten, runner.MIT.rebate)
    return l.daily_pnl(fees).sum(axis=1)


def rechnen(kosten):
    teile = {}
    for g, coins in G.items():
        m = R.markt(coins, vor=True)
        b, v = tage(m, M.basis, kosten), tage(m, M.funding_filter, kosten)
        f = float(b[b.index < SPLIT].std() / v[v.index < SPLIT].std())
        hat_vor = [c for c in coins if (R.DATA / "candles/5m_vor" / f"{c}USDT.parquet").exists()]
        e = {"n": len(coins), "faktor": f, "p_b": b[b.index >= SPLIT], "p_v": f * v[v.index >= SPLIT], "n_vor": len(hat_vor)}
        del m
        if hat_vor:
            mv = R.markt(hat_vor, start=R.VOR_START, ende=R.VOR_ENDE, vor=True)
            e["v_b"], e["v_v"] = tage(mv, M.basis, kosten), f * tage(mv, M.funding_filter, kosten)
            del mv
        teile[g] = e
    return teile


def portfolio(teile, a, b, gewicht):
    n = sum(e[gewicht] for e in teile.values() if a in e)
    return (sum(e[a] * e[gewicht] for e in teile.values() if a in e) / n, sum(e[b] * e[gewicht] for e in teile.values() if b in e) / n)


out = {}
t = rechnen(1.0)
pb, pv = portfolio(t, "p_b", "p_v", "n")
vb, vv = portfolio(t, "v_b", "v_v", "n_vor")
out["pruefzeitraum"] = {"kandidat": sharpe(pb), "variante": sharpe(pv), "N_kandidat": float(pb.sum()), "N_variante": float(pv.sum()), "tage": len(pb)}
out["vorperiode"] = {"kandidat": sharpe(vb), "variante": sharpe(vv), "N_kandidat": float(vb.sum()), "N_variante": float(vv.sum()), "tage": len(vb),
                     "coins": int(sum(e["n_vor"] for e in t.values()))}
out["gruppen_pruefzeitraum"] = {g: {"kandidat": sharpe(e["p_b"]), "variante": sharpe(e["p_v"]), "faktor": e["faktor"]} for g, e in t.items()}
out["gruppen_vorperiode"] = {g: {"kandidat": sharpe(e["v_b"]), "variante": sharpe(e["v_v"]), "coins": e["n_vor"]} for g, e in t.items() if "v_b" in e}
ok1 = out["pruefzeitraum"]["variante"] > out["pruefzeitraum"]["kandidat"] and out["vorperiode"]["variante"] > out["vorperiode"]["kandidat"]
ok2 = sum(v["variante"] > v["kandidat"] for v in out["gruppen_pruefzeitraum"].values()) >= 3
d = pd.concat([vv - vb, pv - pb]).to_numpy()
rng = np.random.default_rng(22)
n = len(d); z = np.empty(5000)
for i in range(5000):
    neu = rng.random(n) < 1 / 20; neu[0] = True
    start = rng.integers(0, n, n); idx = np.empty(n, dtype=np.int64); pos = 0
    for j in range(n):
        pos = start[j] if neu[j] else (pos + 1) % n
        idx[j] = pos
    z[i] = d[idx].mean()
out["zufall"] = {"anteil_positiv": float((z > 0).mean()), "vorsprung_jahr": float(d.mean() * 365), "p5_jahr": float(np.percentile(z, 5) * 365)}
ok3 = out["zufall"]["anteil_positiv"] >= 0.95
t2 = rechnen(2.0)
pb2, pv2 = portfolio(t2, "p_b", "p_v", "n"); vb2, vv2 = portfolio(t2, "v_b", "v_v", "n_vor")
out["doppelte_kosten"] = {"pruefzeitraum": {"kandidat": sharpe(pb2), "variante": sharpe(pv2)}, "vorperiode": {"kandidat": sharpe(vb2), "variante": sharpe(vv2)}}
ok4 = sharpe(pv2) > sharpe(pb2) and sharpe(vv2) > sharpe(vb2)
out["huerden"] = {"1": bool(ok1), "2": bool(ok2), "3": bool(ok3), "4": bool(ok4)}
out["bestanden"] = bool(ok1 and ok2 and ok3 and ok4)
for k in ("pruefzeitraum", "vorperiode", "gruppen_pruefzeitraum", "gruppen_vorperiode", "zufall", "doppelte_kosten", "huerden"):
    print(k, json.dumps(out[k], default=float, indent=None)[:900])
print("BESTANDEN:", out["bestanden"])
(ROOT / "reports/suche_runde22.json").write_text(json.dumps(out, indent=1, default=float))
