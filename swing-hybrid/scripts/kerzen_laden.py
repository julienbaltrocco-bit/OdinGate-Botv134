"""Öffentliche Binance-USD-M-Futures-Kerzen (5m) und Funding-Raten vom Archiv data.binance.vision laden.

    .venv/bin/python -I scripts/kerzen_laden.py

Ergebnis: data/candles/5m/<SYMBOL>.parquet (UTC-Index, open/high/low/close/volume/quote_volume)
          data/candles/funding/<SYMBOL>.parquet
Fehlende Monate werden gemeldet, nicht stillschweigend übergangen.
"""
import io
import sys
import time
import zipfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pandas as pd
import requests

ROOT = Path(__file__).resolve().parents[1]
ZIEL = ROOT / "data/candles"
BASIS = "https://data.binance.vision/data/futures/um/monthly"
SYMBOLE = ["BTCUSDT", "ETHUSDT", "SOLUSDT", "XRPUSDT", "DOTUSDT", "DOGEUSDT", "ADAUSDT", "LINKUSDT", "AVAXUSDT", "LTCUSDT"]
MONATE = [str(p) for p in pd.period_range("2021-07", "2026-10", freq="M")]
SPALTEN = ["open_time", "open", "high", "low", "close", "volume", "close_time", "quote_volume", "count",
           "taker_buy_volume", "taker_buy_quote_volume", "ignore"]


def holen(url: str) -> bytes | None:
    for versuch in range(5):
        try:
            r = requests.get(url, timeout=120)
            if r.status_code == 404:
                return None
            r.raise_for_status()
            return r.content
        except Exception as e:  # Netzfehler: mit Pause erneut versuchen
            if versuch == 4:
                raise
            time.sleep(2 ** (versuch + 1))


def csv_aus_zip(inhalt: bytes) -> pd.DataFrame:
    with zipfile.ZipFile(io.BytesIO(inhalt)) as z:
        roh = z.read(z.namelist()[0])
    kopf = roh[:20].decode("ascii", "ignore")
    return pd.read_csv(io.BytesIO(roh), header=0 if kopf[0].isalpha() else None)


def kerzen_monat(sym: str, monat: str):
    c = holen(f"{BASIS}/klines/{sym}/5m/{sym}-5m-{monat}.zip")
    if c is None:
        return monat, None
    df = csv_aus_zip(c)
    df.columns = SPALTEN[: len(df.columns)]
    df.index = pd.to_datetime(df["open_time"].astype("int64"), unit="ms")
    return monat, df[["open", "high", "low", "close", "volume", "quote_volume"]].astype("float64")


def funding_monat(sym: str, monat: str):
    c = holen(f"{BASIS}/fundingRate/{sym}/{sym}-fundingRate-{monat}.zip")
    if c is None:
        return monat, None
    df = csv_aus_zip(c)
    df.columns = ["calc_time", "interval_hours", "rate"][: len(df.columns)]
    df.index = pd.to_datetime(df["calc_time"].astype("int64"), unit="ms").dt.round("1min")
    return monat, df[["rate"]].astype("float64")


def lauf(art: str, fn, sym: str):
    ziel = ZIEL / art / f"{sym}.parquet"
    if ziel.exists():
        return
    with ThreadPoolExecutor(6) as ex:
        teile = list(ex.map(lambda m: fn(sym, m), MONATE))
    fehlt = [m for m, d in teile if d is None]
    df = pd.concat([d for _, d in teile if d is not None]).sort_index()
    df = df[~df.index.duplicated()]
    ziel.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(ziel)
    print(f"{art} {sym}: {len(df)} Zeilen {df.index[0]} – {df.index[-1]}; fehlende Monate: {fehlt or 'keine'}", flush=True)


if __name__ == "__main__":
    # Aufruf: kerzen_laden.py [--vor] [SYMBOL ...]   (--vor lädt die Vorperiode 01/2020–06/2021 in eigene Ordner)
    args = sys.argv[1:]
    endung = ""
    if args and args[0] == "--vor":
        args = args[1:]
        MONATE[:] = [str(p) for p in pd.period_range("2020-01", "2021-06", freq="M")]
        endung = "_vor"
    for s in (args or SYMBOLE):
        try:
            lauf("5m" + endung, kerzen_monat, s)
            lauf("funding" + endung, funding_monat, s)
        except ValueError as e:  # keine einzige Monatsdatei vorhanden
            print(f"{s}: keine Daten ({e})", flush=True)
