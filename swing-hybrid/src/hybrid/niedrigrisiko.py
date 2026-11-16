"""Runde 13: Niedrig-Risiko-Baustein („Betting against Beta“), marktneutral nach Beta.

Einmal pro Woche: die Coins mit dem niedrigsten Beta zum gleichgewichteten Korb long, die mit dem höchsten short.
Die Seiten werden so gewichtet, dass sich ihr Beta aufhebt. Signal-Etikett wie überall: Stundenbeginn, bekannt bei
Stundenschluss; `research.auf_raster` verschiebt um eine Stunde.
"""
import numpy as np
import pandas as pd

from . import research as R

FENSTER = 1440      # 60 Tage in Stunden
TAKT = 168          # wöchentlich
ANTEIL = 0.3


def beta(m, fenster=FENSTER) -> pd.DataFrame:
    r = R._close(m).pct_change(fill_method=None)
    korb = r.mean(axis=1)
    var = korb.rolling(fenster, min_periods=fenster).var()
    return pd.DataFrame({c: r[c].rolling(fenster, min_periods=fenster).cov(korb) / var for c in r.columns})


def gewichte(b: pd.DataFrame, anteil=ANTEIL, takt=TAKT) -> pd.DataFrame:
    """Aus Betas (Stundenraster) die Zielgewichte: niedrigste `anteil` long, höchste short, Beta beider Seiten gleich."""
    n = b.notna().sum(axis=1)
    k = np.maximum((n * anteil).round(), 1)
    rang = b.rank(axis=1, ascending=True)                 # 1 = niedrigstes Beta
    lang, kurz = rang.le(k, axis=0), rang.gt(n - k, axis=0)
    b_l = b.where(lang).mean(axis=1).clip(lower=0.05)
    b_k = b.where(kurz).mean(axis=1).clip(lower=0.05)
    g_l = (2.0 * b_k / (b_l + b_k)).clip(0.5, 1.5)         # g_l * b_l = g_k * b_k, g_l + g_k = 2
    g_k = 2.0 - g_l
    w = pd.DataFrame(0.0, index=b.index, columns=b.columns)
    w = w.where(~lang, g_l.to_numpy()[:, None] * np.ones(len(b.columns)))
    w = w.where(~kurz, -g_k.to_numpy()[:, None] * np.ones(len(b.columns)))
    w[b.isna()] = 0.0
    w[n < 6] = 0.0
    stunde = ((b.index - pd.Timestamp(0)) // pd.Timedelta(hours=1)).to_numpy() + 1
    w[stunde % takt != 0] = np.nan                         # Signal der Kerze H gilt ab H+1; nur dann umschichten
    return w.ffill().fillna(0.0)


def signal(m) -> pd.DataFrame:
    return gewichte(beta(m))
