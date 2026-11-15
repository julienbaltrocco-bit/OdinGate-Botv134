"""V-QR-01 (1): Modul-Lauf des Kandidaten, Messvorschrift des Einbruchs, Hebel 0,2/0,25/3. Nur lesend."""
import json, sys
sys.path.insert(0, "src")
import numpy as np, pandas as pd
from hybrid import mutationen as M, research as R, runner

AUS = sys.argv[1]
mA = R.markt(R.GRUPPE_A, vor=True)
wA = R.auf_raster(mA, M.basis(mA))
kA = R.yubit_kosten(R.GRUPPE_A)[0]
l1 = R.lauf(mA, wA, taker=True, slip=kA, day_limit=9.0)
tg = l1.daily_pnl(runner.MIT).sum(axis=1)
tg.to_csv(AUS + "/v1_tagesreihe_hebel1.csv", float_format="%.10f", header=["pnl"])
eq = l1.equity(runner.MIT)
np.save(AUS + "/v1_eq5m.npy", eq)
SPLIT = pd.Timestamp(R.SPLIT)
def dd_rel(x):
    k = 1.0 + x.cumsum(); return float(((k.cummax() - k) / k.cummax()).max())
def dd_abs(x):
    k = x.cumsum(); return float((k.cummax().clip(lower=0.0) - k).max())
for name, x in (("Entwicklung", tg[tg.index < SPLIT]), ("Pruefung", tg[tg.index >= SPLIT])):
    k = 1.0 + x.cumsum()
    print(name, "Tage", len(x), "Summe", round(x.sum(), 4), "Ertrag/Jahr", round(x.mean() * 365, 4), "Sharpe", round(x.mean() / x.std() * np.sqrt(365), 4),
          "| Einbruch rel. Spitze (wie runde24.py:62)", round(dd_rel(x), 4), "| abs. Rueckgang (Startkapital)", round(dd_abs(x), 4),
          "| Kontohoch", round(k.max(), 3), k.idxmax().date(), "| schlechtester Tag", round(x.min(), 4), x.idxmin().date(), "| Tage < -10 %", int((x < -0.10).sum()))
g24 = json.load(open("reports/suche_runde24.json"))["kandidat"]["Entwicklung"]
print("gespeichert runde24 kandidat Entwicklung:", {k: round(v, 4) for k, v in g24.items()})
# Hebel mit Tageslimit 3 % (Stufe 5 der Forschung)
for h in (0.2, 0.25, 1.0, 3.0):
    l = R.lauf(mA, wA, hebel=h, taker=True, slip=kA)
    s = R.sicht(l, None, R.SPLIT); p = R.sicht(l, R.SPLIT, None)
    print(f"Hebel {h} MIT Tageslimit 3 %: Einbruch Entw {s['dd_mit']:.4f} Pruef {p['dd_mit']:.4f} N Entw {s['N']:.4f} Pruef {p['N']:.4f} Sperrtage {int(l.st[4])}")
# Hebel 3 ohne Tageslimit: linear?
l3 = R.lauf(mA, wA, hebel=3.0, taker=True, slip=kA, day_limit=9.0)
e3 = l3.equity(runner.MIT)
print("Hebel 3 ohne Tageslimit: max |eq3 - 3*eq1| =", float(np.abs(e3 - 3 * eq).max()), "| Sperrtage", int(l3.st[4]))
idx = mA.index
for name, von, bis in (("Start 2021-08-15 bis Split", None, R.SPLIT), ("Start 2025-04-01 bis Ende", R.SPLIT, None), ("Start 2021-08-15 bis Ende", None, None)):
    a = 0 if von is None else int(idx.searchsorted(pd.Timestamp(von))); b = len(idx) if bis is None else int(idx.searchsorted(pd.Timestamp(bis)))
    e = e3[a:b] - (e3[a - 1] if a > 0 else 0.0); k = 1 + e; sp = np.maximum.accumulate(np.maximum(k, 1.0))
    print(f"  {name}: Konto-Tief {k.min():.4f} am {idx[a + int(np.argmin(k))]}, Ende {k[-1]:.4f}, Einbruch rel. Spitze {((sp - k) / sp).max():.4f}, Konto<=0: {bool((k <= 0).any())}")
