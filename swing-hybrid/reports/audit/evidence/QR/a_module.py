"""QR (a): Reproduktion der Kandidaten-Kennzahlen mit den vorhandenen Modulen aus src/hybrid.

Aufruf (aus swing-hybrid/):
  NUMBA_CACHE_DIR=<scratch>/numba .venv/bin/python -I -B <dieses Skript> <ausgabe.json> <tagesreihe.csv>
Schreibt nichts in das Repo ausser den beiden genannten Zieldateien (Evidenz).
"""
import json
import sys

sys.path.insert(0, "src")
import numpy as np
import pandas as pd
from hybrid import mutationen as M, research as R, runner, tpsl

AUS_JSON, AUS_CSV = sys.argv[1], sys.argv[2]
FEN = {"D1": (None, R.D1_ENDE), "D2": (R.D1_ENDE, R.SPLIT), "Entwicklung": (None, R.SPLIT), "Pruefung": (R.SPLIT, None),
       "Gesamt": (None, None)}


def teil(x, von=None, bis=None):
    if von is not None:
        x = x[x.index >= pd.Timestamp(von)]
    if bis is not None:
        x = x[x.index < pd.Timestamp(bis)]
    return x


def sharpe(x):
    return float(x.mean() / x.std() * np.sqrt(365)) if x.std() > 0 else 0.0


def dd_tag(x):
    """Einbruch wie in scripts/suche_runde24.py: Konto = 1 + kumulierte Tagesergebnisse, relativ zum Hoechststand."""
    k = 1.0 + x.cumsum()
    return float(((k.cummax() - k) / k.cummax()).max())


def kenn(x):
    return {"tage": int(len(x)), "N": float(x.sum()), "jahr": float(x.mean() * 365), "sharpe": sharpe(x), "dd_tag": dd_tag(x)}


out = {}
slipA = R.yubit_kosten(R.GRUPPE_A)[0]
out["slip_bp"] = {c: float(s * 1e4) for c, s in zip(R.GRUPPE_A, slipA)}
out["fees"] = {"maker": runner.MAKER, "taker": runner.TAKER, "rebate": runner.MIT.rebate}

reihen = {}
for name, vor in (("vor_False", False), ("vor_True", True)):
    m = R.markt(R.GRUPPE_A, vor=vor)
    sig = R.variante(m, "basis")
    assert sig.equals(M.basis(m)), "variante(basis) != mutationen.basis"
    w = R.auf_raster(m, sig)
    l = R.lauf(m, w, taker=True, slip=slipA, day_limit=9.0)
    tg = l.daily_pnl(runner.MIT).sum(axis=1)
    reihen[name] = tg
    e = {f: kenn(teil(tg, *v)) for f, v in FEN.items()}
    # Einbruch auf 5-Minuten-Raster (runner.kennzahlen) und Zusatzgroessen
    for f, (von, bis) in FEN.items():
        k = runner.kennzahlen(l, von, bis)
        e[f].update({"dd_5m": k["dd_mit"], "rendite_brutto": k["rendite_brutto"], "rendite_ohne": k["rendite_ohne"],
                     "rendite_mit": k["rendite_mit"], "funding": k["funding"], "volumen_tag": k["volumen_tag"],
                     "trades": k["trades"], "haltedauer_h": k["haltedauer_h"], "sharpe_ohne": k["sharpe_ohne"],
                     "tage_fenster": k["tage"]})
    e["order_statistik"] = runner.order_statistik(l)
    # Signal-Statistik
    s = sig.loc[R.START:pd.Timestamp(R.ENDE) - pd.Timedelta(hours=2)]
    e["signal_null_stunden"] = int((s == 0).sum().sum())
    e["h1_zeilen"] = int(len(sig)); e["h1_erste"] = str(sig.index[0]); e["h1_letzte"] = str(sig.index[-1])
    voll = pd.date_range(sig.index[0], sig.index[-1], freq="1h")
    e["h1_fehlende_stunden_im_index"] = int(len(voll.difference(sig.index)))
    out[name] = e
    if name == "vor_True":
        mA, basis = m, tg
        lA = l

pd.DataFrame(reihen).to_csv(AUS_CSV, float_format="%.10f")
out["max_abw_vor"] = float((reihen["vor_False"] - reihen["vor_True"]).abs().max())

# --- Runde 24: sl5_tp15 und Runde 21: funding_filter ueber dieselbe Rechnung wie die Skripte ---
def tage(m, fn):
    l = R.lauf(m, R.auf_raster(m, fn(m)), taker=True, slip=R.yubit_kosten(m.coins)[0], day_limit=9.0)
    return l.daily_pnl(runner.MIT).sum(axis=1)


bd = teil(basis, None, R.SPLIT)
extra = {}
r24 = {n: tage(mA, fn) for n, fn in tpsl.VARIANTEN.items()}
diffs, namen = [], []
for n, x in r24.items():
    xd = teil(x, None, R.SPLIT)
    fak = float(bd.std() / xd.std())
    e = {f: kenn(teil(x, *v)) for f, v in FEN.items() if f in ("D1", "D2", "Entwicklung")}
    e["faktor"] = fak
    e["im_markt"] = float((tpsl.VARIANTEN[n](mA).abs().sum(axis=1) / len(R.GRUPPE_A)).loc[R.START:R.SPLIT].mean())
    e["korrelation"] = float(np.corrcoef(bd, xd)[0, 1])
    e["vorsprung_jahr"] = float((fak * xd - bd).mean() * 365)
    extra[n] = e
    diffs.append((fak * xd - bd).to_numpy()); namen.append(n)
mittel, schwelle, p = M.reality_check(np.column_stack(diffs))
out["runde24"] = {"varianten": extra, "reality_check": {"schwelle_95": schwelle, "p_beste": p, "tage": int(len(bd))}}

x = tage(mA, M.funding_filter)
xd = teil(x, None, R.SPLIT)
out["runde21_funding_filter"] = {f: kenn(teil(x, *v)) for f, v in FEN.items() if f in ("D1", "D2", "Entwicklung")}
out["runde21_funding_filter"]["vorsprung_jahr"] = float((bd.std() / xd.std() * xd - bd).mean() * 365)

# --- Vergleich mit gespeicherten Ergebnissen ---
g21 = json.load(open("reports/suche_runde21.json")); g24 = json.load(open("reports/suche_runde24.json"))
out["gespeichert"] = {"runde21_kandidat": g21["kandidat"], "runde24_kandidat": g24["kandidat"],
                      "runde24_sl5_tp15": g24["varianten"]["sl5_tp15"], "runde24_rc": g24["reality_check"],
                      "runde21_funding_filter": g21["varianten"]["funding_filter"], "runde21_rc": g21["reality_check"]}
json.dump(out, open(AUS_JSON, "w"), indent=1, default=float)

for name in ("vor_False", "vor_True"):
    print(name)
    print(pd.DataFrame({f: out[name][f] for f in FEN}).T.round(4).to_string())
    print("  Orderstatistik:", out[name]["order_statistik"], "Signal==0-Stunden:", out[name]["signal_null_stunden"],
          "fehlende Stunden im H1-Index:", out[name]["h1_fehlende_stunden_im_index"])
print("max. Abweichung der Tagesreihen vor=False gegen vor=True:", out["max_abw_vor"])
print("Slippage je Coin (bp):", {k: round(v, 3) for k, v in out["slip_bp"].items()})
print("Runde 24 nachgerechnet:")
print(pd.DataFrame({n: {"S_D1": e["D1"]["sharpe"], "S_D2": e["D2"]["sharpe"], "S_Entw": e["Entwicklung"]["sharpe"],
                        "jahr": e["Entwicklung"]["jahr"], "dd": e["Entwicklung"]["dd_tag"], "im_markt": e["im_markt"],
                        "vorsprung": e["vorsprung_jahr"]} for n, e in extra.items()}).T.round(4).to_string())
print("Reality Check Runde 24:", out["runde24"]["reality_check"], "gespeichert:", g24["reality_check"])
print("Runde 21 funding_filter:", {f: round(v["sharpe"], 4) for f, v in out["runde21_funding_filter"].items() if isinstance(v, dict)},
      "Vorsprung/Jahr", round(out["runde21_funding_filter"]["vorsprung_jahr"], 4))
