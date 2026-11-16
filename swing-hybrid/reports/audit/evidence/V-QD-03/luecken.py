"""V-QD-03: erklaert die kleine Abweichung in D1 zwischen eigener Rechnung und Repo (Datenluecken -> Signal 0 im Repo)."""
import sys
sys.path.insert(0, "/home/user/OdinGate-Botv134/swing-hybrid/src")
import numpy as np, pandas as pd
from hybrid import research as R
m = R.markt(R.GRUPPE_A)
c = R._close(m)
print("Stundenkerzen im Verbund-Index:", len(c), "| fehlende Stundenschluesse je Coin:", c.isna().sum().to_dict())
fehl = c[c.isna().any(axis=1)]
print("Zeitpunkte mit fehlenden Stunden (erste/letzte):", fehl.index.min(), fehl.index.max(), "Anzahl", len(fehl))
print(fehl.index.to_series().dt.to_period("M").value_counts().sort_index().to_string())
sig = R.tsmom(m, 336)
s = sig[(sig.index >= "2021-08-15") & (sig.index < "2026-10-24")]
print("Stunden mit Signal 0 je Coin im Auswertungszeitraum:", (s == 0).sum().to_dict())
print("davon ab 2025-04-01:", (s[s.index >= "2025-04-01"] == 0).sum().to_dict())
idx = m.index
for coin in R.GRUPPE_A:
    df = R._lesen("5m", coin, False).reindex(idx)
    n = int(df["close"].isna().sum())
    if n:
        t = df.index[df["close"].isna()]
        print(coin, "fehlende 5-Minuten-Kerzen:", n, "von", t.min(), "bis", t.max())
