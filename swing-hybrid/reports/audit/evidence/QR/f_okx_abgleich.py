"""QR (f): Binance-5m-Schlusskurse gegen die lokal vorhandenen OKX-Tageskerzen (data/processed/okx_1D_*.parquet).
OKX-Tageskerze beginnt 16:00 UTC; verglichen wird mit dem Schluss der Binance-Kerze 15:55 des Folgetags.
Aufruf aus swing-hybrid/:  .venv/bin/python -I -B -W ignore <dieses Skript>"""
import pandas as pd
pd.set_option("display.width", 220)
A = ["BTC", "ETH", "SOL", "XRP", "DOT", "DOGE", "ADA", "LINK", "AVAX", "LTC"]
rows = []
for c in A:
    o = pd.read_parquet(f"data/processed/okx_1D_{c}.parquet")
    oc = pd.Series(o["close"].to_numpy(), index=pd.DatetimeIndex(o.index).astype("datetime64[ns]"))
    k = pd.read_parquet(f"data/candles/5m/{c}USDT.parquet", columns=["close"]); k.index = pd.DatetimeIndex(k.index).astype("datetime64[ns]")
    b = k["close"]; b = b[(b.index.hour == 15) & (b.index.minute == 55)]
    b.index = b.index + pd.Timedelta(minutes=5) - pd.Timedelta(days=1)
    j = pd.concat([b.rename("bin"), oc.rename("okx")], axis=1, sort=True).dropna().loc["2021-08-15":"2026-10-23"]
    rel = (j.bin / j.okx - 1); rb, ro = j.bin.pct_change(), j.okx.pct_change()
    rows.append((c, str(oc.index[0])[:10], str(oc.index[-1])[:10], len(j), round(float(rel.abs().median()) * 1e4, 2), round(float(rel.abs().quantile(0.99)) * 1e4, 1),
                 round(float(rel.abs().max()) * 1e4, 1), str(rel.abs().idxmax().date()), round(float(rb.corr(ro)), 5), int((rel.abs() > 0.01).sum())))
print("Abgleich Binance-5m-Schluss (15:55-Kerze) gegen OKX-Tagesschluss (Tageskerze ab 16:00 UTC), 15.08.2021-23.10.2026")
print(pd.DataFrame(rows, columns=["coin", "okx_von", "okx_bis", "n_gemeinsam", "abw_median_bp", "abw_p99_bp", "abw_max_bp", "tag_max", "korr_tagesrendite", "tage_abw_ueber_1pct"]).to_string(index=False))
