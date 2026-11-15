"""V-QR-01 (4): Gegenprobe ohne src/hybrid und ohne numba: reines pandas auf Stundenbasis aus den Rohkerzen.
Frischer Start an einem Tag, Hebel 3, je Coin 0,3 x Startkapital beim Einstieg, Stueckzahl fest bis zum Signalwechsel,
Ausfuehrung zum Open der Folgestunde, Gebuehr 0,012 % netto, Funding. Keine Slippage (guenstiger als die Rueckrechnung)."""
import numpy as np, pandas as pd
A = ["BTC", "ETH", "SOL", "XRP", "DOT", "DOGE", "ADA", "LINK", "AVAX", "LTC"]
C, O, F = {}, {}, {}
for c in A:
    k = pd.read_parquet(f"data/candles/5m/{c}USDT.parquet"); k.index = pd.DatetimeIndex(k.index).astype("datetime64[ns]")
    C[c] = k.close.resample("1h").last(); O[c] = k.open.resample("1h").first()
    f = pd.read_parquet(f"data/candles/funding/{c}USDT.parquet")["rate"]; f.index = pd.DatetimeIndex(f.index).astype("datetime64[ns]").floor("1h")
    F[c] = f[~f.index.duplicated()]
C, O = pd.DataFrame(C), pd.DataFrame(O); F = pd.DataFrame(F).reindex(C.index).fillna(0.0)
sig = np.sign(C / C.shift(336) - 1).shift(1)          # gilt fuer die Stunde, bekannt seit dem Schluss der Vorstunde
C = C.ffill(); O = O.fillna(C.shift(1))

def lauf(start, ende, hebel=3.0):
    idx = C.loc[start:ende].index[:-1]
    konto = pd.Series(0.0, index=idx)
    for c in A:
        s = sig[c].reindex(idx).fillna(0.0).to_numpy(); o = O[c].reindex(idx).to_numpy(); cl = C[c].reindex(idx).to_numpy(); fr = F[c].reindex(idx).to_numpy()
        pos = 0.0; halte = 0.0; kasse = 0.0; e = np.empty(len(idx))
        for i in range(len(idx)):
            if fr[i] != 0 and pos != 0: kasse -= pos * o[i] * fr[i]
            if s[i] != halte:
                neu = s[i] * hebel / 10 / o[i]
                kasse -= (neu - pos) * o[i] + abs(neu - pos) * o[i] * 0.0008 * 0.15
                pos, halte = neu, s[i]
            e[i] = kasse + pos * cl[i]
        konto += e
    return 1.0 + konto

for start, ende in (("2021-08-15", "2025-04-01"), ("2024-08-05", "2025-04-01"), ("2023-02-01", "2025-04-01"), ("2025-04-01", "2026-10-24"), ("2025-07-20", "2026-10-24"), ("2026-02-25", "2026-10-24")):
    k = lauf(start, ende)
    null = k[k <= 0]
    print(f"Start {start}: Konto-Tief {k.min():.3f} am {k.idxmin()}, erstes Konto <= 0: {null.index[0] if len(null) else 'nie'}, erstes <= 0,5: {k[k <= 0.5].index[0] if (k <= 0.5).any() else 'nie'}, Ende {k.iloc[-1]:.3f}")
