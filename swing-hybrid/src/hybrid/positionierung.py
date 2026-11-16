"""Runde 7: Signale aus Binance-Positionierungsdaten (Open Interest, Long/Short-Verhältnisse, Marktorder-Fluss).

Alle Größen sind Stundenwerte mit dem Etikett „Stundenbeginn“ und erst nach Stundenschluss bekannt, wie die
Schlusskurse. `research.auf_raster` verschiebt das Signal um eine Stunde auf das 5-Minuten-Raster.
"""
import numpy as np
import pandas as pd

from . import research as R
from .config import DATA

FENSTER_Z = 720      # 30 Tage für „ungewöhnlich hoch / niedrig“
FENSTER_7T = 168     # 7 Tage


def metrik(m, spalte: str) -> pd.DataFrame:
    """Stundenwerte einer Kennzahl für alle Coins, auf dem Stundenraster der Kurse. Lücken bis 6 Stunden werden gefüllt."""
    idx = R._close(m).index
    d = {}
    for coin in m.coins:
        quelle = m.metrik[coin] if hasattr(m, "metrik") else pd.read_parquet(DATA / "candles/metrics" / f"{coin}USDT.parquet")
        x = quelle[spalte]
        d[coin] = x.reindex(idx.union(x.index)).ffill(limit=6).reindex(idx)
    return pd.DataFrame(d)


def _z(x: pd.DataFrame, n: int = FENSTER_Z) -> pd.DataFrame:
    return (x - x.rolling(n, min_periods=n // 2).mean()) / x.rolling(n, min_periods=n // 2).std()


def long_short(score: pd.DataFrame, takt: int = 24, anteil: float = 0.3) -> pd.DataFrame:
    """Höchste `anteil` der Werte long, niedrigste short, umgeschichtet alle `takt` Stunden (Uhrzeit-Raster)."""
    n = score.notna().sum(axis=1)
    k = np.maximum((n * anteil).round(), 1)
    rang = score.rank(axis=1, ascending=False)
    w = pd.DataFrame(0.0, index=score.index, columns=score.columns)
    w[rang.le(k, axis=0)] = 1.0
    w[rang.gt(n - k, axis=0)] = -1.0
    w[score.isna()] = 0.0
    w[n < 4] = 0.0
    stunde = ((score.index - pd.Timestamp(0)) // pd.Timedelta(hours=1)).to_numpy() + 1   # Signal von H gilt ab H+1
    w[stunde % takt != 0] = np.nan
    return w.ffill().fillna(0.0)


def profis_gegen_menge(m) -> pd.DataFrame:
    """S1: große Händler stärker long als die Masse -> kaufen; umgekehrt -> verkaufen."""
    x = np.log(metrik(m, "profis_ls")) - np.log(metrik(m, "konten_ls"))
    return long_short(_z(x))


def gegen_die_menge(m) -> pd.DataFrame:
    """S2: ungewöhnlich viele Konten long -> verkaufen; ungewöhnlich wenige -> kaufen."""
    return long_short(-_z(np.log(metrik(m, "konten_ls"))))


def trend_frisches_geld(m) -> pd.DataFrame:
    """S3: der 14-Tage-Trend, aber nur solange das Open Interest höher ist als vor 7 Tagen."""
    oi = metrik(m, "oi")
    steigt = (oi > oi.shift(FENSTER_7T)).astype(float)       # fehlende Werte zählen als „steigt nicht“
    return R._trend(m) * steigt


def orderfluss(m) -> pd.DataFrame:
    """S4: 7 Tage Überhang der Kauf-Marktorders -> kaufen; Überhang der Verkäufe -> verkaufen."""
    return long_short(metrik(m, "taker_log").rolling(FENSTER_7T, min_periods=FENSTER_7T // 2).mean())


SIGNALE = {"profis_gegen_menge": profis_gegen_menge, "gegen_die_menge": gegen_die_menge,
           "trend_frisches_geld": trend_frisches_geld, "orderfluss": orderfluss}
NEUTRAL = {"profis_gegen_menge", "gegen_die_menge", "orderfluss"}
