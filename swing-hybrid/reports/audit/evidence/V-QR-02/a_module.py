"""V-QR-02 (a): Gegenpruefung mit den Modulen aus src/hybrid. Nur Kostenannahmen werden variiert, keine Strategieparameter.
Aufruf (aus swing-hybrid/): NUMBA_CACHE_DIR=<scratch>/numba .venv/bin/python -I -B -W ignore <dieses Skript>
"""
import sys
sys.path.insert(0, "src")
import numpy as np
import pandas as pd
from hybrid import research as R, runner, mutationen as M
from hybrid.fees import Fees

FEN = {"Entwicklung": (None, R.SPLIT), "Pruefung": (R.SPLIT, None)}


def teil(x, von, bis):
    if von is not None:
        x = x[x.index >= pd.Timestamp(von)]
    if bis is not None:
        x = x[x.index < pd.Timestamp(bis)]
    return x


def sharpe(x):
    return float(x.mean() / x.std() * np.sqrt(365))


m = R.markt(R.GRUPPE_A, vor=True)
sig = R.tsmom(m, 336)
print("Signal R.tsmom(336) == mutationen.basis:", bool((sig == M.basis(m)).all().all()))
w = R.auf_raster(m, sig)
kA, fehlt = R.yubit_kosten(R.GRUPPE_A)
print("Slippage je Coin (bp):", dict(zip(R.GRUPPE_A, np.round(kA * 1e4, 3))), "fehlt:", fehlt, "Mittel bp:", round(kA.mean() * 1e4, 3))
print("Gebuehren config: maker", runner.MAKER, "taker", runner.TAKER, "rebate", runner.MIT.rebate)
print("Fenster:", m.index[0], "bis", m.index[-1], "SPLIT", R.SPLIT)

laeufe = {"slip_echt": kA, "slip_0": 0.0, "slip_2x": 2 * kA, "slip_3x": 3 * kA, "slip_5bp": 0.0005, "slip_10bp": 0.001}
rows = []
zer = {}
for name, slip in laeufe.items():
    l = R.lauf(m, w, taker=True, slip=slip, day_limit=9.0)
    assert int(l.st[4]) == 0, "Tageslimit darf nicht greifen"
    for f, (von, bis) in FEN.items():
        k = runner.kennzahlen(l, von, bis)
        V = k["volumen_tag"] * k["tage"]
        F = runner.TAKER * V
        G = k["rendite_brutto"]
        zer[(name, f)] = dict(tage=k["tage"], umsatz=V, gebuehr_voll=F, G_vor_gebuehr=G, funding=k["funding"],
                              netto_ohne=k["rendite_ohne"], netto_mit85=k["rendite_mit"],
                              rebate85=0.85 * F, breakeven_rebate=(F - G) / F, maker_vol=float(l.MV[-1]))
        for rb in (0.85, 0.7, 0.5, 0.3, 0.0):
            x = teil(l.daily_pnl(Fees(runner.MAKER, runner.TAKER, rb)).sum(axis=1), von, bis)
            rows.append(dict(lauf=name, fenster=f, rebate=rb, N=float(x.sum()), jahr=float(x.mean() * 365), sharpe=sharpe(x)))
t = pd.DataFrame(rows)
print("\nEmpfindlichkeit (Hebel 1, ohne Tageslimit): N = Summe der Tagesergebnisse im Fenster")
print(t.pivot_table(index=["lauf", "rebate"], columns="fenster", values=["N", "sharpe"]).round(4).to_string())
print("\nZerlegung:")
print(pd.DataFrame(zer).T.round(4).to_string())

# Pruefzeitraum: Gebuehr je Coin und Anteil Umsatz
l = R.lauf(m, w, taker=True, slip=kA, day_limit=9.0)
a = int(m.index.searchsorted(pd.Timestamp(R.SPLIT)))
print("\nKontrolle Identitaet im Pruefzeitraum: G - F =", round(zer[("slip_echt", "Pruefung")]["G_vor_gebuehr"] - zer[("slip_echt", "Pruefung")]["gebuehr_voll"], 6),
      "netto_ohne =", round(zer[("slip_echt", "Pruefung")]["netto_ohne"], 6))
# Slippage-Kosten im Pruefzeitraum = Differenz G(slip_0) - G(slip_echt)
print("Slippage-Kosten Pruefzeitraum (G bei Slippage 0 minus G echt):",
      round(zer[("slip_0", "Pruefung")]["G_vor_gebuehr"] - zer[("slip_echt", "Pruefung")]["G_vor_gebuehr"], 4))
# pauschale Slippage, bei der das Ergebnis mit 85 % Rebate im Pruefzeitraum null wird (lineare Interpolation 5bp..10bp)
n5 = zer[("slip_5bp", "Pruefung")]["netto_mit85"]; n10 = zer[("slip_10bp", "Pruefung")]["netto_mit85"]
print("Pauschale Slippage mit Null-Ergebnis im Pruefzeitraum bei 85 % Rebate (interpoliert, bp):", round(5 + 5 * n5 / (n5 - n10), 2))
# Wochentag der Stichprobe
d = pd.read_csv("data/processed/yubit_spannen_stichprobe.csv")
z = pd.to_datetime(d["zeit"])
print("Stichprobe:", z.min(), "bis", z.max(), z.min().day_name(), "Messzeitpunkte:", z.nunique())
