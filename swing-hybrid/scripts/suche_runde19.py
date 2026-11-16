"""Runde 19: Short nach Pump auf Gruppe A mit Schwelle im Maßstab der großen Coins. Ablauf laut Protokoll."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
import numpy as np
import pandas as pd
from hybrid import pumpshort as P, research as R, runner, tagestrend as T

ROOT = Path(__file__).resolve().parents[1]
pd.set_option("display.width", 220)
TRAIL = len(sys.argv) > 1 and sys.argv[1] == "trail"
EINSATZ = 0.10
START, ENDE, D1, SPLIT = (pd.Timestamp(x) for x in (R.START, R.ENDE, R.D1_ENDE, R.SPLIT))
FEN = {"D1": (START, D1), "D2": (D1, SPLIT), "Entwicklung": (START, SPLIT), "Pruefung": (SPLIT, ENDE), "Gesamt": (START, ENDE)}
EINST = {"fest5": None, "sigma2": 2.0, "sigma25": 2.5, "sigma3": 3.0}
_cache = {}


def daten(coin):
    if coin not in _cache:
        k = R._lesen("5m", coin, False)
        k = k[(k.index >= START - pd.Timedelta(days=120)) & (k.index < ENDE)][["open", "high", "low", "close"]]
        tag = k["close"].resample("1D").last().pct_change()
        sig = tag.rolling(90, min_periods=60).std().shift(1)             # nur abgeschlossene Tage
        sig = sig.reindex(k.index.normalize()).to_numpy()
        r24 = (k["close"] / k["close"].shift(288) - 1).to_numpy()
        _cache[coin] = (k, r24, sig, R._lesen("funding", coin, False)["rate"])
    return _cache[coin]


def trades(coins, name, slip_faktor=1.0):
    slips = R.yubit_kosten(coins)[0]
    alle = []
    for coin, slip in zip(coins, slips):
        k, r24, sig, fund = daten(coin)
        schwelle = np.full(len(k), 0.05) if EINST[name] is None else EINST[name] * sig
        ok = (r24 >= schwelle) & np.isfinite(schwelle) & np.asarray(k.index >= START)
        zeiten = list(k.index[ok] + pd.Timedelta(minutes=4, seconds=59))     # bekannt bei Kerzenschluss
        if not zeiten:
            continue
        if TRAIL:
            t = pd.DataFrame(P.trades_coin_trail(k, zeiten, sl=0.4 * schwelle[ok], akt=0.4 * schwelle[ok], schritt=0.25 * schwelle[ok]))
        else:
            t = pd.DataFrame(P.trades_coin(k, zeiten, tp=0.5 * schwelle[ok], sl=0.4 * schwelle[ok]))
        if t.empty:
            continue
        t["coin"] = coin
        t["funding"] = P.funding(t, fund, pd.Series(np.zeros(len(t))), pd.Timestamp("2100-01-01"))
        t["k"] = P.kosten(t, float(slip), slip_faktor=slip_faktor)
        t["k_ohne"] = P.kosten(t, float(slip), rebate=0.0)
        alle.append(t)
    t = pd.concat(alle, ignore_index=True).sort_values("ein_zeit").reset_index(drop=True)
    t["vor"] = t["roh"] + t["funding"]
    t["netto"] = t["vor"] - t["k"]
    t["netto_ohne"] = t["vor"] - t["k_ohne"]
    return t


def block(t, f):
    a, b = FEN[f]
    x = t[(t.ein_zeit >= a) & (t.ein_zeit < b)]
    if x.empty:
        return {"trades": 0, "netto_mittel": 0.0, "konto": 0.0, "vor_mittel": 0.0, "konto_vor": 0.0}
    return {"trades": int(len(x)), "ziel": float(x.art.isin(["ziel", "trail"]).mean()), "stop": float((x.art == "stop").mean()),
            "schwelle_mittel": float(x.tp.mean() * 2), "vor_mittel": float(x.vor.mean()), "netto_mittel": float(x.netto.mean()),
            "konto_vor": float(x.vor.sum() * EINSATZ), "konto": float(x.netto.sum() * EINSATZ),
            "konto_ohne_rebate": float(x.netto_ohne.sum() * EINSATZ)}


def tab(t, namen=("D1", "D2", "Entwicklung")):
    return pd.DataFrame({f: block(t, f) for f in namen}).round(4).to_string()


out = {"stufe1": {}}
tr = {}
for name in EINST:
    tr[name] = trades(R.GRUPPE_A, name)
    d = {f: block(tr[name], f) for f in ("D1", "D2", "Entwicklung")}
    ok = d["D1"]["konto"] > 0 and d["D2"]["konto"] > 0 and d["Entwicklung"]["trades"] >= 100
    out["stufe1"][name] = {"ok": bool(ok), **d}
    print(f"\n== {name}: {'bestanden' if ok else 'durchgefallen'}"); print(tab(tr[name]))
best = [n for n in EINST if out["stufe1"][n]["ok"]]


def schluss():
    (ROOT / ("reports/suche_runde20b.json" if TRAIL else "reports/suche_runde19.json")).write_text(json.dumps(out, indent=1, default=float))
    sys.exit(0)


if not best:
    print("\nStufe 1: keine Einstellung besteht."); out["finalist"] = None; schluss()
fin = max(best, key=lambda n: min(out["stufe1"][n]["D1"]["netto_mittel"], out["stufe1"][n]["D2"]["netto_mittel"]))
out["finalist"] = fin
print("\nFinalist:", fin)
t = tr[fin]
s2 = trades(R.GRUPPE_A, fin, slip_faktor=2.0)
out["stufe2"] = {"ok": bool(block(s2, "D1")["konto"] > 0 and block(s2, "D2")["konto"] > 0), "D1": block(s2, "D1"), "D2": block(s2, "D2")}
print("Stufe 2 doppelte Slippage:", out["stufe2"]["ok"]); print(tab(s2, ("D1", "D2")))
if not out["stufe2"]["ok"]:
    schluss()
tb = trades(R.GRUPPE_B, fin)
a_p = block(t, "Pruefung")
out["stufe3"] = {"A": {f: block(t, f) for f in ("Entwicklung", "Pruefung", "Gesamt")}, "B": {f: block(tb, f) for f in ("Entwicklung", "Pruefung", "Gesamt")}}
out["stufe3"]["ok"] = bool(a_p["konto_vor"] > 0 and a_p["konto"] > 0 and all(out["stufe3"]["B"][f]["konto"] > 0 for f in ("Entwicklung", "Pruefung")))
print("Stufe 3 Bestätigung:", out["stufe3"]["ok"]); print("A:"); print(tab(t, ("Entwicklung", "Pruefung", "Gesamt"))); print("B:"); print(tab(tb, ("Entwicklung", "Pruefung", "Gesamt")))
if not out["stufe3"]["ok"]:
    schluss()
rng = np.random.default_rng(19)
tg = t.groupby(t.ein_zeit.dt.date)["netto"].agg(["sum", "count"])
z = [(lambda i: tg["sum"].to_numpy()[i].sum() / tg["count"].to_numpy()[i].sum())(rng.integers(0, len(tg), len(tg))) for _ in range(2000)]
out["stufe4"] = {"anteil_positiv": float((np.array(z) > 0).mean()), "handelstage": int(len(tg))}
out["stufe4"]["ok"] = out["stufe4"]["anteil_positiv"] >= 0.95
print("Stufe 4 Zufallstest:", out["stufe4"])
if not out["stufe4"]["ok"]:
    schluss()
kal = pd.date_range(START.normalize(), ENDE.normalize() - pd.Timedelta(days=1), freq="D")
mA = R.markt(R.GRUPPE_A)
kr = R.lauf(mA, R.auf_raster(mA, R.variante(mA, "basis")), taker=True, slip=R.yubit_kosten(R.GRUPPE_A)[0],
            day_limit=9.0).daily_pnl(runner.MIT).sum(axis=1).reindex(kal).fillna(0.0)
pu = (t.groupby(t.aus_zeit.dt.normalize())["netto"].sum() * EINSATZ).reindex(kal).fillna(0.0)
f = kr[kr.index < SPLIT].std() / pu[pu.index < SPLIT].std()
mix = 0.5 * kr + 0.5 * f * pu
w = {"Entwicklung": (None, R.SPLIT), "Pruefung": (R.SPLIT, None), "Gesamt": (None, None)}
out["stufe5"] = {"kandidat": {k: T.kennzahlen(kr, *v) for k, v in w.items()}, "pump": {k: T.kennzahlen(pu, *v) for k, v in w.items()},
                 "mischung": {k: T.kennzahlen(mix, *v) for k, v in w.items()}, "korrelation": float(np.corrcoef(kr, pu)[0, 1])}
out["stufe5"]["ok"] = bool(all(out["stufe5"]["mischung"][k]["sharpe"] > out["stufe5"]["kandidat"][k]["sharpe"] for k in ("Entwicklung", "Pruefung")))
for k in ("kandidat", "pump", "mischung"):
    print(k); print(pd.DataFrame(out["stufe5"][k]).T[["N", "jahr_N", "dd", "sharpe"]].round(3).to_string())
print("Stufe 5:", out["stufe5"]["ok"], "Korrelation", round(out["stufe5"]["korrelation"], 3))
schluss()
