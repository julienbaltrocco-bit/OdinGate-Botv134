"""Was leistet der Kandidat mit wenig Kapital und bei unterschiedlichem Hebel? Beschreibung, keine Suche.

Gruppe A, echte Yubit-Kosten (2 x halbe Spanne), Tageslimit 3 %. Dazu: welche Coins bei welchem Kapital handelbar sind.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
import numpy as np
import pandas as pd
from hybrid import research as R, runner

ROOT = Path(__file__).resolve().parents[1]
pd.set_option("display.width", 250)
A = R.GRUPPE_A
m = R.markt(A)
K = R.yubit_kosten(A)[0]
w = R.auf_raster(m, R.variante(m, "basis"))
tage_p = (m.index[-1] - pd.Timestamp(R.SPLIT)).days + 1
tage_e = (pd.Timestamp(R.SPLIT) - m.index[0]).days
z = []
for h in (0.2, 0.5, 1.0, 2.0, 3.0):
    l = R.lauf(m, w, hebel=h, taker=True, slip=K)
    e, p = R.sicht(l, None, R.SPLIT), R.sicht(l, R.SPLIT, None)
    tg = l.daily_pnl(runner.MIT).sum(axis=1)
    jahr = tg.groupby(tg.index.year).sum()
    z.append({"hebel": h, "entw_N_jahr": e["N"] / tage_e * 365, "entw_einbruch": e["dd_mit"], "pruef_N_jahr": p["N"] / tage_p * 365,
              "pruef_einbruch": p["dd_mit"], "pruef_rebate_jahr": p["R"] / tage_p * 365, "schlechtestes_jahr": float(jahr.min()),
              "bestes_jahr": float(jahr.max()), "sperrtage": int(l.st[4]), "schlechtester_tag": float(tg.min())})
t = pd.DataFrame(z)
print("Hebel-Tabelle (Gruppe A, echte Kosten, Tageslimit 3 %):"); print(t.round(3).to_string())
# Mindestgrößen bei Yubit (Momentaufnahme)
y = pd.read_csv(ROOT / "data/processed/yubit_coins.csv")
y = y[y["gruppe"] == "A"].set_index("coin")["min_order_usd"]
kap = []
for kapital in (100, 300, 500, 1000, 3000, 5000):
    for h in (0.2, 1.0):
        je_coin = kapital * h / len(A)
        ok = [c for c in A if y[c] <= je_coin]
        kap.append({"kapital": kapital, "hebel": h, "je_coin_usd": je_coin, "handelbar": len(ok), "nicht": ",".join(c for c in A if c not in ok)})
kt = pd.DataFrame(kap)
print("\nHandelbare Coins je Kapital (Mindestordergröße bei Yubit):"); print(kt.to_string())
# Kleines Konto: ohne BTC und ETH
klein = [c for c in A if c not in ("BTC", "ETH")]
mk = R.markt(klein)
lk = R.lauf(mk, R.auf_raster(mk, R.variante(mk, "basis")), hebel=0.2, taker=True, slip=R.yubit_kosten(klein)[0])
ek, pk = R.sicht(lk, None, R.SPLIT), R.sicht(lk, R.SPLIT, None)
print(f"\nOhne BTC und ETH (8 Coins), Hebel 0,2: Entwicklung N {ek['N']:.4f} (Einbruch {ek['dd_mit']:.3f}), Prüfung N {pk['N']:.4f} (Einbruch {pk['dd_mit']:.3f})")
json.dump({"hebel": z, "kapital": kap, "ohne_btc_eth": {"entw_N": ek["N"], "entw_dd": ek["dd_mit"], "pruef_N": pk["N"], "pruef_dd": pk["dd_mit"]},
           "mindestorder_usd": y.round(2).to_dict(), "tage": {"entw": tage_e, "pruef": tage_p}},
          open(ROOT / "reports/diagnose_kapital.json", "w"), indent=1, default=float)
