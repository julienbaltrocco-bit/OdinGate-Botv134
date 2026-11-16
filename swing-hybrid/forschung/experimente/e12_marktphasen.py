"""E12 Marktphasen: In welchen Phasen wirkt „Orderbuch-Stütze“ 1.0? (nur Entwicklung, beschreibend, keine Auswahl)."""
import sys, time
from pathlib import Path
import numpy as np, pandas as pd
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from alpha import kern as K

start = time.time()
E = (pd.Timestamp("2023-01-02"), pd.Timestamp("2024-04-01"))
t = pd.read_csv(K.ERG / "e08_vollpruefung_trades.csv", parse_dates=["ein", "aus"])
t = t[(t["ein"] >= E[0]) & (t["ein"] < E[1])].copy()
teile = []
for coin, g in t.groupby("coin"):
    k = K.lesen("5m", coin); c = k["close"]
    vol = c.pct_change().rolling(288).std().shift(1)                     # Schwankung der letzten 24 Stunden
    rang = vol.rolling(288 * 90, min_periods=288 * 20).rank(pct=True)   # eingeordnet in die letzten 90 Tage (nur Vergangenheit)
    trend = np.sign(c.shift(1) / c.shift(1 + 288 * 14) - 1)             # 14-Tage-Trend
    g = g.copy()
    g["vol_rang"] = rang.reindex(g["ein"]).to_numpy(); g["trend"] = trend.reindex(g["ein"]).to_numpy()
    g["stunde"] = g["ein"].dt.hour
    teile.append(g)
t = pd.concat(teile)
erg = {"schwankung_niedrig": K.kennzahlen(t[t["vol_rang"] < 1 / 3]), "schwankung_mittel": K.kennzahlen(t[(t["vol_rang"] >= 1 / 3) & (t["vol_rang"] < 2 / 3)]),
       "schwankung_hoch": K.kennzahlen(t[t["vol_rang"] >= 2 / 3]),
       "mit_14_tage_trend": K.kennzahlen(t[t["trend"] == t["richtung"]]), "gegen_14_tage_trend": K.kennzahlen(t[t["trend"] == -t["richtung"]]),
       "asien_0_8": K.kennzahlen(t[t["stunde"] < 8]), "europa_8_16": K.kennzahlen(t[(t["stunde"] >= 8) & (t["stunde"] < 16)]),
       "usa_16_24": K.kennzahlen(t[t["stunde"] >= 16])}
for n, kz in erg.items(): print(K.zeile(n, kz))
K.speichern("e12_marktphasen", {"zeitraum": "Entwicklung", "ergebnis": erg}, start)
