"""Runde 18: Binance-Minutenkerzen und Funding für die Coins mit starken Plimaflow-Signalen laden."""
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import kerzen_laden as K

ROOT = Path(__file__).resolve().parents[1]
ZIEL = ROOT / "data/candles/pump_1m"
FUND = ROOT / "data/candles/pump_funding"
ZIEL.mkdir(parents=True, exist_ok=True); FUND.mkdir(parents=True, exist_ok=True)
TAG = "https://data.binance.vision/data/futures/um/daily"
MONATE = ["2026-08", "2026-09", "2026-10"]
TAGE = [str(d.date()) for d in pd.date_range("2026-11-01", "2026-11-18")]


def kerzen(sym, url):
    c = K.holen(url)
    if c is None:
        return None
    df = K.csv_aus_zip(c)
    df.columns = K.SPALTEN[: len(df.columns)]
    df.index = pd.to_datetime(df["open_time"].astype("int64"), unit="ms")
    return df[["open", "high", "low", "close"]].astype("float64")


def coin(sym):
    urls = [f"{K.BASIS}/klines/{sym}/1m/{sym}-1m-{m}.zip" for m in MONATE] + [f"{TAG}/klines/{sym}/1m/{sym}-1m-{t}.zip" for t in TAGE]
    teile = [x for x in (kerzen(sym, u) for u in urls) if x is not None]
    if not teile:
        return sym, None, None
    d = pd.concat(teile).sort_index()
    d = d[~d.index.duplicated()]
    d.to_parquet(ZIEL / f"{sym}.parquet")
    f = []
    for m in MONATE:
        c = K.holen(f"{K.BASIS}/fundingRate/{sym}/{sym}-fundingRate-{m}.zip")
        if c is not None:
            x = K.csv_aus_zip(c)
            f.append(pd.Series(x.iloc[:, -1].astype(float).to_numpy(), index=pd.to_datetime(x.iloc[:, 0].astype("int64"), unit="ms")))
    if f:
        pd.DataFrame({"rate": pd.concat(f).sort_index()}).to_parquet(FUND / f"{sym}.parquet")
    return sym, (str(d.index[0]), str(d.index[-1]), len(d)), len(f)


h = pd.read_parquet(ROOT / "data/raw/plimaflow/historie.parquet")
syms = sorted(h[h.p_win >= 0.6].symbol.str.replace("-", "").unique())
with ThreadPoolExecutor(6) as ex:
    for sym, k, f in ex.map(coin, syms):
        print(sym, k, f)
