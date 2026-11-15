"""QR (g): Datenpruefung. (1) Luecken im 5-Minuten-Raster aller Kerzendateien in data/candles/5m,
(2) Vollstaendigkeit der Funding-Daten Gruppe A, (3) groesste 5-Minuten-Bewegungen Gruppe A.
Aufruf aus swing-hybrid/:  .venv/bin/python -I -B -W ignore <dieses Skript>"""
import glob, os
import pandas as pd
pd.set_option("display.width", 250)
A = ["BTC", "ETH", "SOL", "XRP", "DOT", "DOGE", "ADA", "LINK", "AVAX", "LTC"]
rows = []
for f in sorted(glob.glob("data/candles/5m/*.parquet")):
    k = pd.read_parquet(f, columns=["close"]); idx = pd.DatetimeIndex(k.index)
    d = idx.to_series().diff(); g = d[d > pd.Timedelta(minutes=5)]
    voll = pd.date_range(idx[0], idx[-1], freq="5min")
    rows.append((os.path.basename(f)[:-12], str(idx[0])[:10], str(idx[-1])[:10], len(voll) - len(idx), int(idx.duplicated().sum()),
                 "; ".join(f"{(t - x + pd.Timedelta(minutes=5))} bis {t - pd.Timedelta(minutes=5)}" for t, x in g.items())))
df = pd.DataFrame(rows, columns=["coin", "erste", "letzte", "fehlende_5m_kerzen", "doppelte", "luecken"])
print("(1) Kerzendateien mit Luecken:", int((df.fehlende_5m_kerzen > 0).sum()), "von", len(df))
print(df[df.fehlende_5m_kerzen > 0].to_string(index=False))
print("    davon Gruppe A:", [c for c in A if int(df.set_index('coin').loc[c, 'fehlende_5m_kerzen']) > 0])
rows = []
for c in A:
    f = pd.read_parquet(f"data/candles/funding/{c}USDT.parquet")["rate"]; f.index = pd.DatetimeIndex(f.index).astype("datetime64[ns]")
    x = f.loc["2021-08-15":"2026-10-23 23:59"]; d = x.index.to_series().diff().dropna()
    rows.append((c, len(x), 5688, int((d > pd.Timedelta(hours=8, minutes=5)).sum()), str(d.max()), int((d < pd.Timedelta(hours=7, minutes=55)).sum()),
                 round(float(x.mean()) * 3 * 365 * 100, 2), round(float(x.abs().max()) * 100, 3)))
print("\n(2) Funding-Daten Gruppe A, 15.08.2021-23.10.2026 (erwartet 3 je Tag x 1896 Tage = 5688)")
print(pd.DataFrame(rows, columns=["coin", "ereignisse", "erwartet", "abstaende_ueber_8h", "groesster_abstand", "abstaende_unter_8h", "mittel_pro_jahr_pct", "max_abs_satz_pct"]).to_string(index=False))
print("\n(3) Groesste 5-Minuten-Bewegungen (Schluss zu Schluss) je Coin, 15.08.2021-23.10.2026")
for c in A:
    k = pd.read_parquet(f"data/candles/5m/{c}USDT.parquet"); k.index = pd.DatetimeIndex(k.index); k = k.loc["2021-08-15":"2026-10-23"]
    r = k.close.pct_change(); top = r.abs().nlargest(3)
    print(f"  {c:5s}", [(str(t), round(float(r[t]), 4)) for t in top.index], "| Kerzen ohne Umsatz:", int((k.volume == 0).sum()), "| high<low:", int((k.high < k.low).sum()))
