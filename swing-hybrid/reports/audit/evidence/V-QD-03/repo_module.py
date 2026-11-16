"""V-QD-03: Kandidat mit den Modulen des Repos nachrechnen (nur lesend, schreibt nichts ins Repo).
Eigene Zerlegung aus den Rohfeldern des Laufs (eq_gross, TV, FU), nicht ueber research.sicht."""
import sys
sys.path.insert(0, "/home/user/OdinGate-Botv134/swing-hybrid/src")
import numpy as np
import pandas as pd
from hybrid import research as R, runner

A = R.GRUPPE_A
K = R.yubit_kosten(A)[0]
print("config: MAKER", runner.MAKER, "TAKER", runner.TAKER, "Rebate", runner.MIT.rebate)
m = R.markt(A)
w = R.auf_raster(m, R.tsmom(m, 336))
FEN = {"D1": (None, R.D1_ENDE), "D2": (R.D1_ENDE, R.SPLIT), "Entwicklung": (None, R.SPLIT), "Pruefung": (R.SPLIT, None), "Gesamt": (None, None)}


def zerlegung(name, l, hebel=1.0):
    idx = m.index
    out = {}
    for f, (a, b) in FEN.items():
        ia = 0 if a is None else int(idx.searchsorted(pd.Timestamp(a)))
        ib = len(idx) if b is None else int(idx.searchsorted(pd.Timestamp(b)))
        d = lambda x: float(x[ib - 1] - (x[ia - 1] if ia > 0 else 0.0))
        G_roh = d(l.eq_gross); FU = d(l.FU); TV = d(l.TV); MV = d(l.MV)
        F = runner.TAKER * TV + runner.MAKER * MV
        tage = (ib - ia) / 288
        tg_o = l.daily_pnl(runner.OHNE).sum(axis=1); tg_m = l.daily_pnl(runner.MIT).sum(axis=1)
        sel = np.ones(len(tg_o), bool)
        if a: sel &= tg_o.index >= pd.Timestamp(a)
        if b: sel &= tg_o.index < pd.Timestamp(b)
        sh = lambda x: float(x.mean() / x.std() * np.sqrt(365))
        out[f] = {"tage": tage, "Kurs+Slip": G_roh, "Funding": FU, "G": G_roh + FU, "F": F, "R": 0.85 * F,
                  "N_mit": G_roh + FU - 0.15 * F, "N_ohne": G_roh + FU - F, "jahr_mit": (G_roh + FU - 0.15 * F) / tage * 365,
                  "jahr_ohne": (G_roh + FU - F) / tage * 365, "sharpe_mit": sh(tg_m[sel]), "sharpe_ohne": sh(tg_o[sel]),
                  "t_ohne": sh(tg_o[sel]) * np.sqrt(sel.sum() / 365), "MV": MV, "umsatz_tag": (TV + MV) / tage,
                  "satz_fuer_null": 1 - (G_roh + FU) / F}
    print(f"\n## {name}")
    print(pd.DataFrame(out).T.round(4).to_string())
    return out


l1 = R.lauf(m, w, taker=True, slip=K, day_limit=9.0)
zerlegung("Repo-Module: Hebel 1, ohne Tageslimit, Yubit-Kosten", l1)
l5 = R.lauf(m, w, taker=True, day_limit=9.0)
zerlegung("Repo-Module: Hebel 1, ohne Tageslimit, 5 bp", l5)
l0 = R.lauf(m, w, taker=True, slip=0.0, day_limit=9.0)
zerlegung("Repo-Module: Hebel 1, ohne Tageslimit, NULL Slippage (nur Einordnung)", l0)
l3 = R.lauf(m, w, hebel=3.0, taker=True, slip=K, day_limit=9.0)
zerlegung("Repo-Module: Hebel 3 (wie Papier-Test), ohne Tageslimit, Yubit-Kosten; Anteile des festen Startkapitals", l3)

# Pruefzeitraum je Coin ohne Rebate (zeigt, ob der Verlust an einem Coin haengt)
d = l1.daily_pnl(runner.OHNE); dm = l1.daily_pnl(runner.MIT)
sel = d.index >= pd.Timestamp(R.SPLIT)
print("\n## Pruefzeitraum je Coin, Hebel 1, Yubit-Kosten: netto ohne / mit Rebate")
print(pd.DataFrame({"ohne": d[sel].sum(), "mit": dm[sel].sum()}).round(4).T.to_string())
# Pruefzeitraum je Quartal ohne / mit Rebate
q = pd.DataFrame({"ohne": d[sel].sum(axis=1), "mit": dm[sel].sum(axis=1)})
print("\n## Pruefzeitraum je Quartal")
print(q.groupby(q.index.to_period("Q")).sum().round(4).T.to_string())
