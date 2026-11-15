"""V-QR-03 Schritt 3: Nachbar-Laengen des Kandidaten, NUR Entwicklungszeitraum (keine Auswahl, kein Blick in den Pruefzeitraum).

Frage: Liegt L = 336 auf einem breiten Plateau oder ist es eine einzelne Spitze? Der Kandidat war in den Runden 1-3 die
laengste getestete Laenge. Ausgegeben wird ausschliesslich der Zeitraum vor dem 01.04.2025.

Aufruf aus swing-hybrid/:  NUMBA_CACHE_DIR=<scratch>/numba .venv/bin/python -I -B -W ignore <dieses Skript>
"""
import sys

sys.path.insert(0, "src")
import numpy as np
import pandas as pd
from hybrid import research as R, runner

m = R.markt(R.GRUPPE_A)
ky = R.yubit_kosten(R.GRUPPE_A)[0]
SPLIT, D1 = pd.Timestamp(R.SPLIT), pd.Timestamp(R.D1_ENDE)
print("Rueckblick h | Sharpe D1 | Sharpe D2 | Sharpe Entwicklung | t-Wert Entwicklung   (Gruppe A, Hebel 1, Yubit-Kosten mit Rebate, ohne Tageslimit)")
for L in (168, 240, 288, 312, 336, 360, 384, 432, 504, 672):
    x = R.lauf(m, R.auf_raster(m, R.tsmom(m, L)), taker=True, slip=ky, day_limit=9.0).daily_pnl(runner.MIT).sum(axis=1)
    x = x[x.index < SPLIT]
    s = lambda v: float(v.mean() / v.std() * np.sqrt(365))
    print(f"  {L:5d}      |  {s(x[x.index < D1]):+.2f}    |  {s(x[x.index >= D1]):+.2f}    |  {s(x):+.2f}             |  {x.mean() / (x.std() / np.sqrt(len(x))):+.2f}")
