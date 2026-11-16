"""Kontrolle: stimmen die nachgerechneten Swing-Signale mit den vom Labor gespeicherten Zielgewichten überein?"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
import pandas as pd
from hybrid import swing

for strat in swing.QUELLEN:
    print(strat, swing.labor_params(strat))
    for coin in swing.COINS:
        s = swing.signal(coin, strat)
        lab = swing.labor_ziel(coin, strat)
        best = None
        for shift in (0, 1):
            mine = s.shift(shift).reindex(lab.index)
            diff = int(((mine - lab).abs() > 1e-6).sum())
            best = (diff, shift) if best is None or diff < best[0] else best
        print(f"  {coin:5s} Kerzen {s.index[0]} – {s.index[-1]} | Labor {lab.index[0].date()}–{lab.index[-1].date()} "
              f"n={len(lab)} | Abweichungen {best[0]} (Versatz {best[1]}) | aktiv {float((s != 0).mean()):.0%}")
