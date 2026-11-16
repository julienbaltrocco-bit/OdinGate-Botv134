"""Binance-Positionierungsdaten (metrics, 5-Minuten-Raster) laden und auf Stunden verdichten.

    .venv/bin/python -I scripts/positionierung_laden.py BTCUSDT ETHUSDT ...

Ergebnis: data/candles/metrics/<SYMBOL>.parquet mit Stundenwerten:
  oi (offene Kontrakte, Stundenende), konten_ls (Long/Short aller Konten), profis_ls (Long/Short der größten Händler,
  nach Position), taker_log (Mittel des Logarithmus Kauf-/Verkaufs-Marktorders in der Stunde).
Fehlende Tage werden gezählt und gemeldet.
"""
import io
import sys
import time
import zipfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np
import pandas as pd
import requests

ROOT = Path(__file__).resolve().parents[1]
ZIEL = ROOT / "data/candles/metrics"
BASIS = "https://data.binance.vision/data/futures/um/daily/metrics"
TAGE = [d.strftime("%Y-%m-%d") for d in pd.date_range("2021-07-01", "2026-10-31", freq="D")]
SPALTEN = ["create_time", "sum_open_interest", "sum_toptrader_long_short_ratio", "count_long_short_ratio",
           "sum_taker_long_short_vol_ratio"]


def tag(sym: str, d: str):
    url = f"{BASIS}/{sym}/{sym}-metrics-{d}.zip"
    for versuch in range(5):
        try:
            r = requests.get(url, timeout=60)
            if r.status_code == 404:
                return None
            r.raise_for_status()
            with zipfile.ZipFile(io.BytesIO(r.content)) as z:
                return pd.read_csv(io.BytesIO(z.read(z.namelist()[0])), usecols=SPALTEN)
        except Exception:
            if versuch == 4:
                raise
            time.sleep(2 ** (versuch + 1))


def lauf(sym: str) -> None:
    ziel = ZIEL / f"{sym}.parquet"
    if ziel.exists():
        return
    with ThreadPoolExecutor(32) as ex:
        teile = list(ex.map(lambda d: tag(sym, d), TAGE))
    fehlt = sum(1 for t in teile if t is None)
    df = pd.concat([t for t in teile if t is not None])
    df.index = pd.to_datetime(df.pop("create_time")).astype("datetime64[ns]")
    df = df[~df.index.duplicated()].sort_index().apply(pd.to_numeric, errors="coerce")
    df = df.where(df > 0)                                   # 0 und negative Werte sind Datenfehler
    h = pd.DataFrame({
        "oi": df["sum_open_interest"].resample("1h").last(),
        "konten_ls": df["count_long_short_ratio"].resample("1h").last(),
        "profis_ls": df["sum_toptrader_long_short_ratio"].resample("1h").last(),
        "taker_log": np.log(df["sum_taker_long_short_vol_ratio"]).resample("1h").mean(),
    })
    ziel.parent.mkdir(parents=True, exist_ok=True)
    h.to_parquet(ziel)
    print(f"{sym}: {len(h)} Stunden {h.index[0]} – {h.index[-1]}; fehlende Tage {fehlt} von {len(TAGE)}; "
          f"leere Stunden {int(h['konten_ls'].isna().sum())}", flush=True)


if __name__ == "__main__":
    for s in sys.argv[1:]:
        try:
            lauf(s)
        except ValueError as e:
            print(f"{s}: keine Daten ({e})", flush=True)
