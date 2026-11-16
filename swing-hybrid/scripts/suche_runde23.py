"""Runde 23: Short nach Pump mit eigenem Signal, 15 Varianten, gemeinsame Zufallsprüfung, Prüfzeitraum."""
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
import numpy as np
import pandas as pd
from hybrid import mutationen as M, pumpmerkmale as F, pumpshort as P

ROOT = Path(__file__).resolve().parents[1]
pd.set_option("display.width", 250)
EINSATZ = 0.10
A, MITTE, SPLIT, E = (pd.Timestamp(x) for x in ("2023-01-01", "2024-03-01", "2025-04-01", "2026-11-01"))
sp = pd.read_csv(ROOT / "data/processed/yubit_spannen_stichprobe.csv")
sp["halb"] = (sp["brief"] - sp["geld"]) / (sp["brief"] + sp["geld"])
spanne = (sp.groupby("symbol")["halb"].mean() * 2).clip(lower=0.00005)
t0 = time.time()
roh = {n: [] for n in F.VARIANTEN}
verworfen = 0
dateien = sorted((ROOT / "data/candles/pump_5m").glob("*.parquet"))
for nr, p in enumerate(dateien):
    sym = p.stem
    if sym not in spanne.index:
        continue
    k = pd.read_parquet(p)
    fp = ROOT / f"data/candles/pump_5m_funding/{sym}.parquet"
    fund = pd.read_parquet(fp)["rate"] if fp.exists() else None
    m = F.merkmale(k, fund)
    slip = float(spanne[sym])
    for n, fn in F.VARIANTEN.items():
        ok = fn(m).to_numpy()
        if not ok.any():
            continue
        t = pd.DataFrame(P.trades_coin(k, list(k.index[ok] + pd.Timedelta(minutes=4, seconds=59))))
        if t.empty:
            continue
        lang = (t["aus_zeit"] - t["ein_zeit"]) > pd.Timedelta(hours=73)
        verworfen += int((lang | (t["art"] == "ende")).sum()) if n == "roh" else 0
        t = t[~lang & (t["art"] != "ende")].reset_index(drop=True)
        if t.empty:
            continue
        t["coin"] = sym
        t["funding"] = P.funding(t, fund, pd.Series(np.zeros(len(t))), pd.Timestamp("2100-01-01")) if fund is not None else 0.0
        t["k"] = P.kosten(t, slip); t["k2"] = P.kosten(t, slip, slip_faktor=2.0); t["k_ohne"] = P.kosten(t, slip, rebate=0.0)
        roh[n].append(t)
    if nr % 40 == 0:
        print(nr, sym, f"{time.time() - t0:.0f} s", flush=True)

tr = {}
for n, teile in roh.items():
    t = F.begrenzen(pd.concat(teile, ignore_index=True)) if teile else pd.DataFrame()
    if len(t):
        t["vor"] = t["roh"] + t["funding"]
        t["netto"] = t["vor"] - t["k"]; t["netto2"] = t["vor"] - t["k2"]; t["netto_ohne"] = t["vor"] - t["k_ohne"]
        t.to_csv(ROOT / f"data/processed/runde23_{n}.csv", index=False)
    tr[n] = t


def block(t, a, b):
    x = t[(t.ein_zeit >= a) & (t.ein_zeit < b)] if len(t) else t
    if not len(x):
        return {"trades": 0, "konto": 0.0, "netto_mittel": 0.0, "konto_vor": 0.0, "konto2": 0.0}
    return {"trades": int(len(x)), "coins": int(x.coin.nunique()), "ziel": float((x.art == "ziel").mean()), "vor_mittel": float(x.vor.mean()),
            "netto_mittel": float(x.netto.mean()), "konto_vor": float(x.vor.sum() * EINSATZ), "konto": float(x.netto.sum() * EINSATZ),
            "konto2": float(x.netto2.sum() * EINSATZ), "konto_ohne_rebate": float(x.netto_ohne.sum() * EINSATZ)}


out = {"coins": len(dateien), "verworfen_roh": verworfen, "varianten": {}}
tage = pd.date_range(A, SPLIT - pd.Timedelta(days=1), freq="D")
spalten = []
for n, t in tr.items():
    e = {"H1": block(t, A, MITTE), "H2": block(t, MITTE, SPLIT), "Entwicklung": block(t, A, SPLIT)}
    e["ok1"] = bool(e["Entwicklung"]["trades"] >= 300 and e["H1"]["konto"] > 0 and e["H2"]["konto"] > 0)
    e["ok3"] = bool(e["Entwicklung"]["konto2"] > 0)
    out["varianten"][n] = e
    d = (t[t.ein_zeit < SPLIT].groupby(t.ein_zeit.dt.normalize())["netto"].sum() * EINSATZ) if len(t) else pd.Series(dtype=float)
    spalten.append(d.reindex(tage).fillna(0.0).to_numpy())
mittel, schwelle, p = M.reality_check(np.column_stack(spalten), block=5, seed=23)
out["reality_check"] = {"schwelle_tag": schwelle, "p_beste": p}
for n, mw in zip(tr, mittel):
    out["varianten"][n]["ok2"] = bool(mw > schwelle)
    out["varianten"][n]["tagesmittel"] = float(mw)
tab = pd.DataFrame({n: {"Trades": e["Entwicklung"]["trades"], "Ziel": e["Entwicklung"].get("ziel", 0), "vor/Trade": e["Entwicklung"].get("vor_mittel", 0),
                        "netto/Trade": e["Entwicklung"]["netto_mittel"], "Konto H1": e["H1"]["konto"], "Konto H2": e["H2"]["konto"],
                        "S1": e["ok1"], "S2": e["ok2"], "S3": e["ok3"]} for n, e in out["varianten"].items()}).T
print(tab.to_string()); print("Reality Check:", out["reality_check"], "Schwelle Konto/Jahr:", round(schwelle * 365, 3))
final = [n for n, e in out["varianten"].items() if e["ok1"] and e["ok2"] and e["ok3"]]
out["finalisten"] = final
print("Finalisten:", final)
out["pruefung"] = {}
for n in final:
    t = tr[n]; x = t[t.ein_zeit >= SPLIT]
    e = block(t, SPLIT, E)
    rng = np.random.default_rng(23)
    tg = x.groupby(x.ein_zeit.dt.date)["netto"].agg(["sum", "count"])
    z = [(lambda i: tg["sum"].to_numpy()[i].sum() / tg["count"].to_numpy()[i].sum())(rng.integers(0, len(tg), len(tg))) for _ in range(2000)] if len(tg) else [0]
    e["zufall_positiv"] = float((np.array(z) > 0).mean())
    je = x.groupby("coin")["netto"].sum()
    e["groesster_coin"] = float(je.max() / x.netto.sum()) if x.netto.sum() > 0 else None
    kt = (t.groupby(t.aus_zeit.dt.normalize())["netto"].sum() * EINSATZ)
    konto = 1 + kt.cumsum()
    e["dd_gesamt"] = float(((konto.cummax() - konto) / konto.cummax()).max())
    e["jahre"] = {str(j): float(v) for j, v in (t.groupby(t.ein_zeit.dt.year)["netto"].sum() * EINSATZ).items()}
    e["ok4"] = bool(e["konto"] > 0 and e["konto_vor"] > 0 and e["trades"] >= 100 and e["zufall_positiv"] >= 0.95)
    e["ok5"] = bool(e["groesster_coin"] is not None and e["groesster_coin"] <= 0.25 and e["dd_gesamt"] < 0.15)
    out["pruefung"][n] = e
    print(n, json.dumps(e, default=float))
out["bestanden"] = [n for n in final if out["pruefung"][n]["ok4"] and out["pruefung"][n]["ok5"]]
print("BESTANDEN:", out["bestanden"])
(ROOT / "reports/suche_runde23.json").write_text(json.dumps(out, indent=1, default=float))
print(f"fertig in {time.time() - t0:.0f} s")
