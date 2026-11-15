"""QR (i): Lage des Kandidaten beim Kurssturz am 10.10.2025 und schlechteste Stunden in Signalrichtung.
Aufruf aus swing-hybrid/:  .venv/bin/python -I -B -W ignore <dieses Skript> <a_tagesreihe.csv>"""
import sys
import numpy as np, pandas as pd
pd.set_option("display.width", 220)
A = ["BTC", "ETH", "SOL", "XRP", "DOT", "DOGE", "ADA", "LINK", "AVAX", "LTC"]
a = pd.read_csv(sys.argv[1], index_col=0, parse_dates=True)["vor_True"]
print("Tagesergebnis Kandidat (Hebel 1, netto mit Rebate) um den 10.10.2025:"); print(a["2025-10-08":"2025-10-13"].round(4).to_string())
C, LO, HI = {}, {}, {}
for c in A:
    k = pd.read_parquet(f"data/candles/5m/{c}USDT.parquet"); k.index = pd.DatetimeIndex(k.index).astype("datetime64[ns]")
    C[c] = k.close.resample("1h").last(); LO[c] = k.low.resample("1h").min(); HI[c] = k.high.resample("1h").max()
C, LO, HI = pd.DataFrame(C), pd.DataFrame(LO), pd.DataFrame(HI)
sig = np.sign(C / C.shift(336) - 1)
t = pd.Timestamp("2025-10-10 21:00")
print("Signal je Coin, gueltig fuer die Stunde 21:00:", sig.shift(1).loc[t].astype(int).to_dict())
print("Stunde 21:00: Tief gegen Schluss der Vorstunde:", (LO.loc[t] / C.shift(1).loc[t] - 1).round(3).to_dict())
print("Stunde 21:00: Schluss gegen Schluss der Vorstunde:", (C.loc[t] / C.shift(1).loc[t] - 1).round(3).to_dict())
z = sig.shift(1); r = C.pct_change()
gegen = (r * z).loc["2021-08-15":"2026-10-23"]
ext = pd.DataFrame(np.where(z > 0, LO / C.shift(1) - 1, np.where(z < 0, -(HI / C.shift(1) - 1), 0.0)), index=C.index, columns=C.columns).loc["2021-08-15":"2026-10-23"]
print("Schlechteste Stunden des gleichgewichteten Korbs in Signalrichtung (Schluss zu Schluss, Hebel 1):"); print(gegen.mean(axis=1).nsmallest(5).round(4).to_string())
print("Dasselbe, alle Coins gleichzeitig am unguenstigsten Kurs der Stunde (Obergrenze):"); print(ext.mean(axis=1).nsmallest(5).round(4).to_string())
print("Schlechteste Einzel-Coin-Stunde am unguenstigsten Kurs:", ext.min().round(3).to_dict())
