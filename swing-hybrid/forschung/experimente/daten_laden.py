"""Neue Datenquellen für die Alpha-Forschung laden (Binance-Archiv, nur bis 31.03.2025: der Prüfzeitraum bleibt unberührt).

  premium  : Aufschlag des Kontrakts auf den Index (premiumIndexKlines, 5 Minuten), 10 Coins
  minuten  : 1-Minuten-Kerzen mit Kauf-Marktorder-Volumen, 10 Coins
  tiefe    : Orderbuch-Tiefe (bookDepth, ab 01.01.2023), je 5 Minuten gemittelt, BTC/ETH/SOL

Aufruf: python -I forschung/experimente/daten_laden.py premium|minuten|tiefe
"""
import io
import sys
import zipfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
import kerzen_laden as K

COINS = ["BTC", "ETH", "SOL", "XRP", "DOT", "DOGE", "ADA", "LINK", "AVAX", "LTC"]
MONATE = [str(p) for p in pd.period_range("2021-07", "2025-03", freq="M")]
ZIEL = ROOT / "data/candles"


def _monat(art, sym, m, intervall):
    c = K.holen(f"{K.BASIS}/{art}/{sym}/{intervall}/{sym}-{intervall}-{m}.zip")
    if c is None:
        return None
    df = K.csv_aus_zip(c)
    df = df.iloc[:, :11]
    df.columns = ["open_time", "open", "high", "low", "close", "volume", "close_time", "quote_volume", "count", "taker_base", "taker_quote"]
    df.index = pd.to_datetime(df["open_time"].astype("int64"), unit="ms")
    return df


def premium(coin):
    ziel = ZIEL / "premium_5m" / f"{coin}USDT.parquet"
    if ziel.exists():
        return coin, -1
    with ThreadPoolExecutor(8) as ex:
        teile = [t for t in ex.map(lambda m: _monat("premiumIndexKlines", coin + "USDT", m, "5m"), MONATE) if t is not None]
    d = pd.concat(teile).sort_index()
    d[~d.index.duplicated()][["open", "high", "low", "close"]].astype("float64").to_parquet(ziel)
    return coin, len(teile)


def minuten(coin):
    ziel = ZIEL / "1m" / f"{coin}USDT.parquet"
    if ziel.exists():
        return coin, -1
    with ThreadPoolExecutor(6) as ex:
        teile = [t for t in ex.map(lambda m: _monat("klines", coin + "USDT", m, "1m"), MONATE) if t is not None]
    d = pd.concat(teile).sort_index()
    d = d[~d.index.duplicated()][["open", "high", "low", "close", "quote_volume", "taker_quote"]]
    d.astype({"open": "float64", "high": "float64", "low": "float64", "close": "float64", "quote_volume": "float32", "taker_quote": "float32"}).to_parquet(ziel)
    return coin, len(teile)


def _tiefe_tag(sym, tag):
    c = K.holen(f"https://data.binance.vision/data/futures/um/daily/bookDepth/{sym}/{sym}-bookDepth-{tag}.zip")
    if c is None:
        return None
    with zipfile.ZipFile(io.BytesIO(c)) as z:
        df = pd.read_csv(io.BytesIO(z.read(z.namelist()[0])), header=0)
    df.columns = ["zeit", "stufe", "menge", "wert"]
    df["zeit"] = pd.to_datetime(df["zeit"]); df["stufe"] = df["stufe"].astype(float).astype(int); df["wert"] = df["wert"].astype(float)
    p = df.pivot_table(index="zeit", columns="stufe", values="wert", aggfunc="last")
    p.columns = [f"w{int(s):+d}" for s in p.columns]
    g = p.resample("5min", label="left", closed="left")
    out = g.mean(); out["letzt_w-1"] = g["w-1"].last(); out["letzt_w+1"] = g["w+1"].last(); out["n"] = g["w-1"].count()
    return out.astype("float32")


def tiefe(coin):
    ziel = ZIEL / "tiefe_5m" / f"{coin}USDT.parquet"
    if ziel.exists():
        return coin, -1
    tage = [str(t.date()) for t in pd.date_range("2023-01-01", "2025-03-31")]
    with ThreadPoolExecutor(12) as ex:
        teile = [t for t in ex.map(lambda t: _tiefe_tag(coin + "USDT", t), tage) if t is not None]
    d = pd.concat(teile).sort_index()
    d[~d.index.duplicated()].to_parquet(ziel)
    return coin, len(teile)


if __name__ == "__main__":
    art = sys.argv[1]
    (ZIEL / {"premium": "premium_5m", "minuten": "1m", "tiefe": "tiefe_5m"}[art]).mkdir(parents=True, exist_ok=True)
    fn, coins = {"premium": (premium, COINS), "minuten": (minuten, COINS), "tiefe": (tiefe, ["BTC", "ETH", "SOL"])}[art]
    with ThreadPoolExecutor(3) as ex:
        for coin, n in ex.map(fn, coins):
            print(art, coin, n, flush=True)
    print("fertig", art)
