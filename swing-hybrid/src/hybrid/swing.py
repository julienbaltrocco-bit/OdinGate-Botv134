"""Swing-Signale aus dem Labor nachrechnen (identische Regeln, identische OKX-Kerzen).

Die beiden Strategien sind 1:1 aus `strategien/trail_beide` und `strategien/momentum_vol_ls` des Labors übernommen.
Parameter stammen aus der Plateau-Wahl des Labors im Lernzeitraum (berichte/<reihe>/ergebnis.json).
Das Signal einer Kerze gilt ab dem Open der nächsten Kerze (wie im Labor).
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd

from .config import DATA

LABOR = DATA / "raw/labor-daten/trading-labor/trading-labor"
COINS = ["BTC", "ETH", "SOL", "XRP", "DOT", "DOGE", "ADA", "LINK", "AVAX", "LTC"]

QUELLEN = {
    "trail_beide": {"reihe": "futures-beide-4h", "intervall": "4H", "schritt": pd.Timedelta(hours=4)},
    "momentum_vol_ls": {"reihe": "futures-1d-breit", "intervall": "1D", "schritt": pd.Timedelta(days=1)},
}


def labor_params(strategie: str) -> dict:
    d = json.loads((LABOR / "berichte" / QUELLEN[strategie]["reihe"] / "ergebnis.json").read_text())
    return d["strategien"][strategie]["params"]


def okx_kerzen(coin: str, strategie: str) -> pd.DataFrame:
    """OKX-Kerzen, wie das Labor sie benutzt hat: aus Prüf- und Vorwärtsläufen zusammengesetzt."""
    q = QUELLEN[strategie]
    ziel = DATA / "processed" / f"okx_{q['intervall']}_{coin}.parquet"
    if ziel.exists():
        return pd.read_parquet(ziel)
    sym = f"{coin}-USDT"
    teile = []
    for ordner in (q["reihe"], q["reihe"] + "-vorwaerts"):
        for f in (LABOR / "runs" / ordner).glob(f"{strategie}__{sym}__{q['intervall']}__*/artifacts/ohlcv_{sym}.csv"):
            teile.append(pd.read_csv(f, index_col=0, parse_dates=True))
    df = pd.concat(teile)
    df = df[~df.index.duplicated(keep="last")].sort_index()
    luecken = int((df.index.to_series().diff().dropna() != q["schritt"]).sum())
    if luecken:
        print(f"  Hinweis {coin} {q['intervall']}: {luecken} Lücken in den OKX-Kerzen")
    ziel.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(ziel)
    return df


# ---------------------------------------------------------------- trail_beide (4H) ----
REST = 0.6666666667
LONG_SL_ATR, LONG_TRAIL_ATR, SHORT_TRAIL_ATR = 2.5, 4.0, 3.0
ZEITSTOPP, N_BARS, TAGE = 30, 30, 30


def _atr(df, n):
    prev = df["close"].shift(1)
    tr = pd.concat([df["high"] - df["low"], (df["high"] - prev).abs(), (df["low"] - prev).abs()], axis=1).max(axis=1)
    return tr.rolling(n).mean()


def _rsi(close, n):
    d = close.diff()
    auf = d.clip(lower=0).ewm(alpha=1 / n, adjust=False).mean()
    ab = (-d.clip(upper=0)).ewm(alpha=1 / n, adjust=False).mean()
    return 100 - 100 / (1 + auf / ab.replace(0, np.nan))


def _bars_pro_tag(index):
    # unabhängig von der Zeitauflösung des Index (pandas 3 nutzt nicht mehr immer Nanosekunden)
    schritt = pd.Series(pd.DatetimeIndex(index)).diff().median()
    return max(int(round(pd.Timedelta(days=1) / schritt)), 1)


def _erschoepfung(df, a, r):
    o, h, l, c, v = df["open"], df["high"], df["low"], df["close"], df["volume"]
    ema = c.ewm(span=50, adjust=False).mean()
    s1 = ((c - ema) / a).rolling(3).max() >= 3
    s2 = (r.rolling(3).max() >= 70) & (r < r.shift(1))
    s3 = (h.rolling(3).max() >= h.rolling(20).max().shift(3)) & (r.rolling(3).max() < r.rolling(20).max().shift(3))
    hoch30 = h.rolling(30).max().shift(3)
    s4 = (h.rolling(3).max() > hoch30) & (c < hoch30)
    koerper = (c - o).abs()
    docht = h - pd.concat([o, c], axis=1).max(axis=1)
    lage = (c - l) / (h - l).replace(0, np.nan)
    s5 = ((docht >= 2 * koerper) & (lage <= 0.35)).rolling(2).max() > 0
    s6 = (v.rolling(3).max() >= 2.5 * v.rolling(20).mean().shift(3)) & (c.shift(3) > c.shift(13))
    return sum(x.fillna(False).astype(int) for x in (s1, s2, s3, s4, s5, s6))


def trail_beide(df: pd.DataFrame, params: dict) -> pd.Series:
    schwelle, k_short = int(params["schwelle"]), float(params["sl_atr"])
    c_s = df["close"]
    a_s = _atr(df, 14)
    punkte = _erschoepfung(df, a_s, _rsi(c_s, 14)).to_numpy()
    trend = (c_s / c_s.shift(TAGE * _bars_pro_tag(df.index)) - 1).to_numpy()
    hoch = df["high"].rolling(N_BARS).max().shift(1).to_numpy()
    a, c, o = a_s.to_numpy(), c_s.to_numpy(), df["open"].to_numpy()
    sig = np.zeros(len(df))
    richtung, tp1, einstieg, sl, risiko, extrem, dauer = 0, False, 0.0, 0.0, 0.0, 0.0, 0
    for i in range(len(df)):
        if np.isnan(a[i]) or np.isnan(trend[i]) or np.isnan(hoch[i]):
            continue
        if richtung == 0:
            if trend[i] > 0 and c[i] > hoch[i]:
                richtung, einstieg, sl = 1, c[i], c[i] - LONG_SL_ATR * a[i]
            elif punkte[i] >= schwelle and c[i] < o[i]:
                richtung, einstieg, sl = -1, c[i], c[i] + k_short * a[i]
            if richtung != 0:
                risiko = abs(einstieg - sl)
                if risiko > 0:
                    tp1, extrem, dauer = False, c[i], 0
                else:
                    richtung = 0
        else:
            dauer += 1
            gestoppt = richtung * (c[i] - sl) <= 0
            raus = (richtung == 1 and trend[i] <= 0) or (richtung == -1 and not tp1 and dauer >= ZEITSTOPP)
            if gestoppt or raus:
                richtung = 0
            else:
                extrem = max(extrem, c[i]) if richtung == 1 else min(extrem, c[i])
                if not tp1 and richtung * (c[i] - einstieg) >= risiko:
                    tp1 = True
                if tp1:
                    if richtung == 1:
                        sl = max(sl, einstieg, extrem - LONG_TRAIL_ATR * a[i])
                    else:
                        sl = min(sl, einstieg, extrem + SHORT_TRAIL_ATR * a[i])
        sig[i] = richtung * (REST if tp1 else 1.0)
    return pd.Series(sig, index=df.index)


# ------------------------------------------------------------ momentum_vol_ls (1D) ----
def momentum_vol_ls(df: pd.DataFrame, params: dict) -> pd.Series:
    close = df["close"]
    trend = close / close.shift(int(params["lookback"])) - 1
    vol = close.pct_change().rolling(20).std() * np.sqrt(float(params["jahr"]))
    groesse = (float(params["zielvol"]) / vol).clip(0, 1)
    richtung = np.sign(trend).fillna(0)
    stufe = np.floor(groesse.fillna(0) * 4) / 4
    return (richtung * stufe).fillna(0).astype(float)


STRATEGIEN = {"trail_beide": trail_beide, "momentum_vol_ls": momentum_vol_ls}


def signal(coin: str, strategie: str) -> pd.Series:
    """Zielgewicht je Kerze (Index = Kerzen-Open, Signal gilt ab dem Open der NÄCHSTEN Kerze)."""
    return STRATEGIEN[strategie](okx_kerzen(coin, strategie), labor_params(strategie))


def ziel_ab(coin: str, strategie: str) -> pd.Series:
    """Zielgewicht mit dem Zeitpunkt, ab dem es gehalten werden soll (Open der Folgekerze)."""
    s = signal(coin, strategie)
    s.index = s.index + QUELLEN[strategie]["schritt"]
    return s


def labor_ziel(coin: str, strategie: str) -> pd.Series:
    """Zielgewichte, die das Labor selbst gespeichert hat (zur Kontrolle der Nachrechnung)."""
    q = QUELLEN[strategie]
    d = json.loads((LABOR / "berichte" / q["reihe"] / "ergebnis.json").read_text())
    pfad = d["strategien"][strategie]["laeufe"]["1x"][f"{coin}-USDT"].replace("\\", "/")
    t = pd.read_csv(LABOR / pfad / "artifacts/target_positions.csv", index_col=0, parse_dates=True)
    return t.iloc[:, 0]
