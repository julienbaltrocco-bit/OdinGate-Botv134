"""Tageskerzen und Funding von Binance für alle bei Yubit handelbaren Kontrakte laden (für die Listing-Hypothese).

    .venv/bin/python -I scripts/listings_laden.py

Ergebnis: data/candles/1d/<SYMBOL>.parquet (open, high, low, close, quote_volume je Tag)
          data/candles/funding_1d/<SYMBOL>.parquet (Summe der Funding-Raten je Tag)
          data/processed/listings_inventur.csv (erster und letzter Handelstag je Symbol bei Binance)
Symbole ohne Binance-Daten werden gezählt und übersprungen.
"""
import io
import time
import zipfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pandas as pd
import requests

ROOT = Path(__file__).resolve().parents[1]
ZIEL = ROOT / "data/candles"
BASIS = "https://data.binance.vision/data/futures/um/monthly"
MONATE = [str(p) for p in pd.period_range("2021-07", "2026-10", freq="M")]
SYMBOLE = (ROOT / "data/processed/yubit_symbole.txt").read_text().split()


def holen(url):
    for versuch in range(5):
        try:
            r = requests.get(url, timeout=60)
            if r.status_code == 404:
                return None
            r.raise_for_status()
            with zipfile.ZipFile(io.BytesIO(r.content)) as z:
                roh = z.read(z.namelist()[0])
            return pd.read_csv(io.BytesIO(roh), header=0 if roh[:1].isalpha() else None)
        except Exception:
            if versuch == 4:
                raise
            time.sleep(2 ** (versuch + 1))


def kerzen(job):
    sym, monat = job
    df = holen(f"{BASIS}/klines/{sym}/1d/{sym}-1d-{monat}.zip")
    if df is None:
        return sym, monat, None
    df = df.iloc[:, [0, 1, 2, 3, 4, 7]]
    df.columns = ["open_time", "open", "high", "low", "close", "quote_volume"]
    df.index = pd.to_datetime(df.pop("open_time").astype("int64"), unit="ms")
    return sym, monat, df.astype("float64")


def funding(job):
    sym, monat = job
    df = holen(f"{BASIS}/fundingRate/{sym}/{sym}-fundingRate-{monat}.zip")
    if df is None:
        return sym, monat, None
    df = df.iloc[:, [0, 2]]
    df.columns = ["zeit", "rate"]
    df.index = pd.to_datetime(df.pop("zeit").astype("int64"), unit="ms")
    return sym, monat, df.astype("float64")


if __name__ == "__main__":
    t0 = time.time()
    with ThreadPoolExecutor(48) as ex:
        k = list(ex.map(kerzen, [(s, m) for s in SYMBOLE for m in MONATE]))
    je = {}
    for sym, monat, df in k:
        if df is not None:
            je.setdefault(sym, {})[monat] = df
    print(f"Kerzen: {len(je)} von {len(SYMBOLE)} Symbolen haben Binance-Daten ({time.time() - t0:.0f} s)", flush=True)
    with ThreadPoolExecutor(48) as ex:
        f = list(ex.map(funding, [(s, m) for s in je for m in je[s]]))
    fj = {}
    for sym, monat, df in f:
        if df is not None:
            fj.setdefault(sym, []).append(df)
    (ZIEL / "1d").mkdir(parents=True, exist_ok=True)
    (ZIEL / "funding_1d").mkdir(parents=True, exist_ok=True)
    inv = []
    for sym, monate in je.items():
        d = pd.concat(monate.values()).sort_index()
        d = d[~d.index.duplicated()]
        d.to_parquet(ZIEL / "1d" / f"{sym}.parquet")
        fehl = [m for m in MONATE if str(d.index[0].to_period("M")) <= m <= str(d.index[-1].to_period("M")) and m not in monate]
        if sym in fj:
            r = pd.concat(fj[sym]).sort_index()["rate"]
            r.groupby(r.index.normalize()).sum().to_frame("rate").to_parquet(ZIEL / "funding_1d" / f"{sym}.parquet")
        inv.append({"symbol": sym, "erster_tag": d.index[0].date(), "letzter_tag": d.index[-1].date(), "tage": len(d),
                    "fehlende_monate": len(fehl), "funding": sym in fj})
    pd.DataFrame(inv).to_csv(ROOT / "data/processed/listings_inventur.csv", index=False)
    print(f"fertig: {len(inv)} Symbole, {time.time() - t0:.0f} s", flush=True)
