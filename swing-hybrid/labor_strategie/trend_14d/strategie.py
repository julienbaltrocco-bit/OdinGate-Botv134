"""Trend über 14 Tage, stündlich nachgeführt, Long UND Short (Kandidat aus der Suche, siehe reports/suche_bericht.md).

Kurs höher als vor 14 Tagen -> Long, tiefer -> Short. Jeder Coin gleich groß (Gewicht +1 / -1).
Gedacht für Stundenkerzen (L = 336 Kerzen). Auf anderen Zeitrahmen L so anpassen, dass es 14 Tage bleiben.
Signal auf Basis der Daten bis einschließlich Bar t. KEIN eigenes .shift(1): die Engine führt zum Open t+1 aus.
Nur sinnvoll mit `markt: futures`. Die Größe je Coin bestimmt der Hebel (in der Suche: 20 % des Kontos über 10 Coins).
"""
import numpy as np
import pandas as pd

PARAMS = {"L": 336}
WARMUP = 360
ANPASSUNG = "rebalance"


class SignalEngine:
    def generate(self, data_map):
        out = {}
        L = int(PARAMS["L"])
        for code, df in data_map.items():
            close = df["close"]
            out[code] = np.sign(close / close.shift(L) - 1).fillna(0.0).astype(float)
        return out
