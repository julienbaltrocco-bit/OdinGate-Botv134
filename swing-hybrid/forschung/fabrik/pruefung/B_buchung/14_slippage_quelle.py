"""slip_bp.npy gegen die Rohstichprobe der Yubit-Spannen: Slippage je Order = 2 x mittlere halbe Spanne, mindestens 0,5 bp (Abschnitt 4 und 19)."""
import sys
import numpy as np, pandas as pd
sys.path.insert(0, 'forschung')
from fabrik import daten as D
d = pd.read_csv('data/processed/yubit_spannen_stichprobe.csv')
print("Spalten:", list(d.columns), "| Zeilen:", len(d))
slip = np.asarray(D.laden("slip_bp"))
for j, coin in enumerate(D.COINS):
    x = d[d["symbol"] == coin + "USDT"]
    halb = ((x["brief"] - x["geld"]) / (x["brief"] + x["geld"])).mean() * 1e4          # halbe Spanne relativ zur Mitte, in bp
    soll = max(0.5, 2 * halb)
    print(f"{coin:<5} Messungen {len(x):>4}  halbe Spanne {halb:6.3f} bp  -> je Order {soll:6.3f} bp | slip_bp.npy {slip[j]:6.3f} | Abw. {abs(soll - slip[j]):.2e} | "
          f"je Trade (2 Orders) {2*slip[j]:6.3f} bp, doppelt {4*slip[j]:6.3f} bp | Untergrenze greift: {2*halb < 0.5}")
