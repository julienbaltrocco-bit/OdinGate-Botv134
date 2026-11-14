"""Alles auf ein gemeinsames 5-Minuten-Raster bringen: Binance-Futures-Kerzen, Swing-Zielgewicht, Stunden-ATR, Funding."""
from dataclasses import dataclass

import numpy as np
import pandas as pd

from . import swing
from .config import DATA

# Simulationszeitraum je Swing-Quelle: Beginn = Ende des Vorlaufs der Swing-Strategie (wie im Labor),
# Ende = letzte sicher abgeschlossene Kerze im Labor-Cache.
ZEITRAUM = {
    "trail_beide": ("2021-10-07 00:00", "2026-10-24 00:00"),
    "momentum_vol_ls": ("2022-07-20 16:00", "2026-10-24 00:00"),
}


@dataclass
class Markt:
    index: pd.DatetimeIndex      # 5-Minuten-Raster (Kerzen-Open, UTC)
    coins: list
    o: np.ndarray                # [Coin, Zeit]
    h: np.ndarray
    l: np.ndarray
    c: np.ndarray
    w: np.ndarray                # Swing-Zielgewicht, das ab dem Open dieser Kerze gilt
    atr: np.ndarray              # ATR(14) der Stundenkerzen, nur abgeschlossene Stunden
    fund: np.ndarray             # Funding-Rate, fällig zum Open dieser Kerze (sonst 0)
    day: np.ndarray              # laufende Tagesnummer (UTC)
    hour_start: np.ndarray       # True zur vollen Stunde
    days: pd.DatetimeIndex


def kerzen_5m(coin: str) -> pd.DataFrame:
    return pd.read_parquet(DATA / "candles/5m" / f"{coin}USDT.parquet")


def stunden_atr(df5: pd.DataFrame, n: int = 14) -> pd.Series:
    h1 = df5.resample("1h").agg({"open": "first", "high": "max", "low": "min", "close": "last"}).dropna()
    prev = h1["close"].shift(1)
    tr = pd.concat([h1["high"] - h1["low"], (h1["high"] - prev).abs(), (h1["low"] - prev).abs()], axis=1).max(axis=1)
    a = tr.rolling(n).mean()
    a.index = a.index + pd.Timedelta(hours=1)  # erst nach Stundenschluss bekannt
    return a


def laden(strategie: str, coins=None) -> Markt:
    coins = coins or swing.COINS
    start, ende = (pd.Timestamp(x) for x in ZEITRAUM[strategie])
    idx = pd.date_range(start, ende, freq="5min", inclusive="left")
    felder = {k: np.empty((len(coins), len(idx))) for k in ("o", "h", "l", "c", "w", "atr", "fund")}
    for j, coin in enumerate(coins):
        df = kerzen_5m(coin)
        df.index = df.index.astype("datetime64[ns]")
        k = df.reindex(idx)
        luecke = k["close"].isna()
        close = k["close"].ffill()
        if close.isna().any():
            raise ValueError(f"{coin}: keine Binance-Kerzen am Beginn des Zeitraums")
        for name, spalte in (("o", "open"), ("h", "high"), ("l", "low")):
            felder[name][j] = k[spalte].where(~luecke, close).to_numpy()  # Lücke: Kerze ohne Handel, kein Fill möglich
        felder["c"][j] = close.to_numpy()
        z = swing.ziel_ab(coin, strategie)
        z.index = z.index.astype("datetime64[ns]")
        felder["w"][j] = z.reindex(idx.union(z.index)).ffill().reindex(idx).fillna(0.0).to_numpy()
        a = stunden_atr(df)
        felder["atr"][j] = a.reindex(idx.union(a.index)).ffill().reindex(idx).to_numpy()
        f = pd.read_parquet(DATA / "candles/funding" / f"{coin}USDT.parquet")["rate"]
        f.index = f.index.astype("datetime64[ns]").floor("5min")
        felder["fund"][j] = f[~f.index.duplicated()].reindex(idx).fillna(0.0).to_numpy()
    tage = idx.normalize()
    day = np.asarray((tage - tage[0]).days, dtype=np.int64)
    return Markt(idx, list(coins), felder["o"], felder["h"], felder["l"], felder["c"], felder["w"], felder["atr"],
                 felder["fund"], day, np.asarray(idx.minute == 0), pd.DatetimeIndex(tage.unique()))
