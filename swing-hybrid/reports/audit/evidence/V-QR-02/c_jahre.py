"""V-QR-02 (c): Zerlegung je Kalenderjahr und rollierend (Hebel 1, Yubit-Kosten, ohne Tageslimit) sowie Vorperiode.
Reine Berichtsrechnung, keine Auswahl. Aufruf (aus swing-hybrid/): NUMBA_CACHE_DIR=<scratch>/numba .venv/bin/python -I -B -W ignore <Skript>
"""
import sys
sys.path.insert(0, "src")
import numpy as np
import pandas as pd
from hybrid import research as R, runner
from hybrid.fees import Fees

m = R.markt(R.GRUPPE_A, vor=True)
w = R.auf_raster(m, R.tsmom(m, 336))
kA = R.yubit_kosten(R.GRUPPE_A)[0]
l = R.lauf(m, w, taker=True, slip=kA, day_limit=9.0)
t = pd.DataFrame({"G": l.daily_pnl(runner.BRUTTO).sum(axis=1), "ohne": l.daily_pnl(runner.OHNE).sum(axis=1),
                  "mit85": l.daily_pnl(runner.MIT).sum(axis=1)})
t["F"] = t["G"] - t["ohne"]
j = t.groupby(t.index.year).sum()
j["rebate_fuer_null"] = (j["F"] - j["G"]) / j["F"]
j["tage"] = t.groupby(t.index.year).size()
print("Je Kalenderjahr (Anteile am Startkapital):"); print(j.round(4).to_string())
p = t[t.index >= pd.Timestamp(R.SPLIT)]
h = p.groupby(p.index.to_period("Q")).sum()
h["rebate_fuer_null"] = (h["F"] - h["G"]) / h["F"]
print("\nPruefzeitraum je Quartal:"); print(h.round(4).to_string())
print("\nPruefzeitraum: Quartale mit ohne<0:", int((h["ohne"] < 0).sum()), "von", len(h), "| mit85<0:", int((h["mit85"] < 0).sum()))
# je Coin im Pruefzeitraum
d0 = l.daily_pnl(runner.OHNE); d1 = l.daily_pnl(runner.MIT); dg = l.daily_pnl(runner.BRUTTO)
s = lambda d: d[d.index >= pd.Timestamp(R.SPLIT)].sum()
print("\nPruefzeitraum je Coin:"); print(pd.DataFrame({"G": s(dg), "ohne": s(d0), "mit85": s(d1)}).round(4).T.to_string())
# Vorperiode (02/2020-08/2021) mit denselben Yubit-Kosten und mit 5 bp
mv = R.markt(R.GRUPPE_A, R.VOR_START, R.VOR_ENDE, vor=True)
wv = R.auf_raster(mv, R.tsmom(mv, 336))
for name, slip in (("5bp (wie Runde 4)", None), ("Yubit-Stichprobe", kA)):
    lv = R.lauf(mv, wv, taker=True, slip=slip, day_limit=9.0)
    k = runner.kennzahlen(lv, None, None)
    print(f"\nVorperiode A, Slippage {name}: G={k['rendite_brutto']:+.4f} ohne Rebate={k['rendite_ohne']:+.4f} mit 85 %={k['rendite_mit']:+.4f} Tage={k['tage']:.0f}")
