"""Runde 11: Massentest einfacher Einstiegsregeln in Richtung des Swing-Bias (Stundenkerzen, eine Position je Coin).

Signal am Schluss der Kerze t, Einstieg zum Open von t+1. Alle Indikatoren nutzen nur Daten bis einschließlich t.
"""
import numpy as np
import pandas as pd
from numba import njit

GEBUEHR_TAKER = 0.0016     # Ein- und Ausstieg als Taker, volle Gebühr
GEBUEHR_MAKER = 0.0008


# ----------------------------------------------------------------- Indikatoren ----
def rsi(c: pd.Series, n: int) -> pd.Series:
    d = c.diff()
    auf = d.clip(lower=0).ewm(alpha=1 / n, adjust=False).mean()
    ab = (-d.clip(upper=0)).ewm(alpha=1 / n, adjust=False).mean()
    return 100 - 100 / (1 + auf / ab.replace(0, np.nan))


def atr(df: pd.DataFrame, n: int = 14) -> pd.Series:
    prev = df["close"].shift(1)
    tr = pd.concat([df["high"] - df["low"], (df["high"] - prev).abs(), (df["low"] - prev).abs()], axis=1).max(axis=1)
    return tr.rolling(n).mean()


def bias(c: pd.Series, tage: int) -> pd.Series:
    return np.sign(c / c.shift(tage * 24) - 1).fillna(0.0)


def einstiege(df: pd.DataFrame, b: pd.Series) -> dict:
    """Alle Einstiegsregeln für einen Coin. b = Bias (+1/-1/0). Gibt Name -> bool-Reihe zurück (True = Einstieg in Bias-Richtung)."""
    o, h, l, c, v = df["open"], df["high"], df["low"], df["close"], df["quote_volume"]
    lang, kurz = b > 0, b < 0
    ret1 = c.pct_change()
    vol = ret1.rolling(72).std()
    out = {}
    for n in (2, 6, 14):
        r = rsi(c, n)
        for x in (10, 20, 30):
            out[f"rsi{n}_unter{x}"] = (lang & (r < x)) | (kurz & (r > 100 - x))
    for n in (24, 72):
        m, s = c.rolling(n).mean(), c.rolling(n).std()
        for k in (1.5, 2.0, 2.5):
            out[f"boll{n}_k{k}"] = (lang & (c < m - k * s)) | (kurz & (c > m + k * s))
    for N in (6, 12, 24, 48, 96):
        hoch, tief = h.rolling(N).max().shift(1), l.rolling(N).min().shift(1)
        out[f"ausbruch{N}"] = (lang & (c > hoch)) | (kurz & (c < tief))
    for m_ in (1, 3, 6):
        rm = c / c.shift(m_) - 1
        for z in (1.5, 2.5):
            grenze = z * vol * np.sqrt(m_)
            out[f"impuls{m_}_z{z}"] = (lang & (rm > grenze)) | (kurz & (rm < -grenze))
            out[f"ruecksetzer{m_}_z{z}"] = (lang & (rm < -grenze)) | (kurz & (rm > grenze))
    vm = v.rolling(72).mean().shift(1)
    for z in (2.0, 3.0):
        spitze = v > z * vm
        out[f"volumen_mit_z{z}"] = spitze & ((lang & (c > o)) | (kurz & (c < o)))
        out[f"volumen_gegen_z{z}"] = spitze & ((lang & (c < o)) | (kurz & (c > o)))
    stunde = pd.Series(df.index.hour, index=df.index)
    for hh in (0, 4, 8, 12, 16, 20):
        out[f"uhr{hh:02d}"] = (b != 0) & (((stunde + 1) % 24) == hh)       # Einstieg zum Open der Stunde hh
    out["immer"] = b != 0
    return {k: x.fillna(False).to_numpy(dtype=np.bool_) for k, x in out.items()}


# ---------------------------------------------------------------------- Trades ----
@njit(cache=True)
def trades_fest(o, c, sig, richtung, H):
    """Feste Haltedauer: Einstieg Open t+1, Ausstieg Schluss t+H. Gibt (Einstiegsindex, Ertrag vor Kosten) zurück."""
    T = len(c)
    ein = np.empty(T, np.int64); ret = np.empty(T); n = 0
    t = 0
    while t < T - H - 1:
        if sig[t] and richtung[t] != 0.0 and o[t + 1] > 0.0:
            ein[n] = t + 1
            ret[n] = richtung[t] * (c[t + H] / o[t + 1] - 1.0)
            n += 1
            t += H                                   # bis zum Ausstieg keine neue Position
        else:
            t += 1
    return ein[:n], ret[:n]


@njit(cache=True)
def trades_ziel(o, h, l, c, sig, richtung, a, k, limit):
    """Gewinnziel und Stop je k x ATR um den Einstieg, Zeitlimit `limit` Kerzen. Trifft eine Kerze beide, zählt der Stop."""
    T = len(c)
    ein = np.empty(T, np.int64); ret = np.empty(T); n = 0
    t = 0
    while t < T - limit - 1:
        if sig[t] and richtung[t] != 0.0 and o[t + 1] > 0.0 and a[t] == a[t] and a[t] > 0.0:
            d = richtung[t]; p0 = o[t + 1]; abst = k * a[t]
            ziel, stop = p0 + d * abst, p0 - d * abst
            aus, u = c[t + limit], t + limit
            for s in range(t + 1, t + limit + 1):
                if (d > 0 and l[s] <= stop) or (d < 0 and h[s] >= stop):
                    aus, u = stop, s
                    break
                if (d > 0 and h[s] >= ziel) or (d < 0 and l[s] <= ziel):
                    aus, u = ziel, s
                    break
            ein[n] = t + 1
            ret[n] = d * (aus / p0 - 1.0)
            n += 1
            t = u
        else:
            t += 1
    return ein[:n], ret[:n]


AUSSTIEGE = [("halte1", 1), ("halte2", 2), ("halte4", 4), ("halte8", 8), ("halte24", 24), ("ziel1atr", -1.0), ("ziel2atr", -2.0)]


def coin_trades(df: pd.DataFrame, bias_tage: int) -> dict:
    """Alle Regel-Varianten für einen Coin: Name -> (Einstiegszeiten, Erträge vor Kosten)."""
    b = bias(df["close"], bias_tage)
    sig = einstiege(df, b)
    o, h, l, c = (df[k].to_numpy(dtype=np.float64) for k in ("open", "high", "low", "close"))
    a = atr(df).to_numpy(dtype=np.float64)
    richtung = b.to_numpy(dtype=np.float64)
    out = {}
    for name, s in sig.items():
        for aus, par in AUSSTIEGE:
            if par > 0:
                ein, ret = trades_fest(o, c, s, richtung, int(par))
            else:
                ein, ret = trades_ziel(o, h, l, c, s, richtung, a, -par, 24)
            out[f"b{bias_tage}_{name}_{aus}"] = (df.index[ein], ret)
    return out
