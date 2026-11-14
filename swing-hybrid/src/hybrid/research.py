"""Suche nach einer Strategie mit viel Umsatz: Daten, Signal-Familien, Läufe, Kennzahlen.

Regeln der Suche (vorab festgelegt, siehe reports/suche_protokoll.md):
- Entwickelt wird nur im Entwicklungszeitraum (erste 70 %), geteilt in zwei Hälften D1 und D2.
- Der Prüfzeitraum (letzte 30 %) wird je Finalist genau einmal angesehen.
- Coin-Gruppe B wird nie zur Auswahl benutzt, nur zur Gegenprobe.
"""
from types import SimpleNamespace

import numpy as np
import pandas as pd

from . import engine2, runner
from .config import DATA

GRUPPE_A = ["BTC", "ETH", "SOL", "XRP", "DOT", "DOGE", "ADA", "LINK", "AVAX", "LTC"]
GRUPPE_B = ["BNB", "TRX", "ATOM", "BCH", "ETC", "FIL", "UNI", "NEAR", "XLM", "AAVE"]
START, ENDE = "2021-08-15 00:00", "2026-10-24 00:00"
D1_ENDE, SPLIT = "2023-07-01", "2025-04-01"   # Entwicklung: D1 bis 30.06.2023, D2 bis 31.03.2025; danach Prüfzeitraum
TTL = 3            # 15 Minuten Standzeit je Order
BARS_H = 12


VOR_START, VOR_ENDE = "2020-02-01 00:00", START   # Vorperiode für die Bestätigung (Runde 4)


def _lesen(art: str, coin: str, vor: bool) -> pd.DataFrame:
    teile = []
    for ordner in ([art + "_vor", art] if vor else [art]):
        pfad = DATA / "candles" / ordner / f"{coin}USDT.parquet"
        if pfad.exists():
            d = pd.read_parquet(pfad)
            d.index = d.index.astype("datetime64[ns]")
            teile.append(d)
    df = pd.concat(teile)
    return df[~df.index.duplicated()].sort_index()


def markt(coins, start=START, ende=ENDE, vor=False) -> SimpleNamespace:
    """`vor=True` nimmt die Vorperiode dazu. Vor dem Handelsstart eines Coins steht der Kurs still (kein Signal, kein Handel)."""
    idx = pd.date_range(start, ende, freq="5min", inclusive="left")
    f = {k: np.empty((len(coins), len(idx))) for k in ("o", "h", "l", "c", "atr", "fund")}
    h1 = {}
    for j, coin in enumerate(coins):
        df = _lesen("5m", coin, vor)
        k = df.reindex(idx)
        luecke = k["close"].isna()
        close = k["close"].ffill().bfill()
        if close.isna().any():
            raise ValueError(f"{coin}: keine Kerzen im Zeitraum")
        for name, sp in (("o", "open"), ("h", "high"), ("l", "low")):
            f[name][j] = k[sp].where(~luecke, close).to_numpy()
        f["c"][j] = close.to_numpy()
        st = df.resample("1h").agg({"open": "first", "high": "max", "low": "min", "close": "last",
                                    "quote_volume": "sum"}).dropna()
        h1[coin] = st
        prev = st["close"].shift(1)
        tr = pd.concat([st["high"] - st["low"], (st["high"] - prev).abs(), (st["low"] - prev).abs()], axis=1).max(axis=1)
        a = tr.rolling(14).mean()
        a.index = a.index + pd.Timedelta(hours=1)
        f["atr"][j] = a.reindex(idx.union(a.index)).ffill().reindex(idx).to_numpy()
        fr = _lesen("funding", coin, vor)["rate"]
        fr.index = fr.index.floor("5min")
        f["fund"][j] = fr[~fr.index.duplicated()].reindex(idx).fillna(0.0).to_numpy()
    tage = idx.normalize()
    return SimpleNamespace(index=idx, coins=list(coins), day=np.asarray((tage - tage[0]).days, dtype=np.int64),
                           days=pd.DatetimeIndex(tage.unique()), h1=h1, **f)


def auf_raster(m, sig: pd.DataFrame) -> np.ndarray:
    """Stundensignal (Index = Stunden-Open, bekannt bei Stundenschluss) auf das 5-Minuten-Raster legen."""
    s = sig.copy()
    s.index = s.index + pd.Timedelta(hours=1)
    w = s.reindex(m.index.union(s.index)).ffill().reindex(m.index).fillna(0.0)
    return np.ascontiguousarray(w[m.coins].to_numpy().T)


# ------------------------------------------------------------------ Signal-Familien ----
def _close(m):
    return pd.DataFrame({c: m.h1[c]["close"] for c in m.coins})


def tagestrend(m, tage=60):
    """Swing-Bias: Vorzeichen der Rendite über `tage` Tage (wie momentum_vol_ls), stündlich aktualisiert."""
    c = _close(m)
    return np.sign(c / c.shift(tage * 24) - 1).fillna(0.0)


def tsmom(m, L, bias=False):
    """Trend: Long, wenn der Kurs über L Stunden gestiegen ist, sonst Short."""
    c = _close(m)
    w = np.sign(c / c.shift(L) - 1).fillna(0.0)
    return w.where(w == tagestrend(m), 0.0) if bias else w


def ensemble(m, bias=False, laengen=(12, 24, 48, 96, 168, 336)):
    """Mittel aus sechs Trendlängen: Position wächst, je mehr Längen dieselbe Richtung zeigen."""
    c = _close(m)
    w = sum(np.sign(c / c.shift(L) - 1) for L in laengen) / len(laengen)
    w = (np.round(w.fillna(0.0) * 3) / 3)
    return w.where(np.sign(w) == tagestrend(m), 0.0) if bias else w


def reversal(m, n, k, bias=False):
    """Gegenbewegung: Kurs k Standardabweichungen unter dem n-Stunden-Mittel -> Long bis zurück am Mittel (Short gespiegelt)."""
    c = _close(m)
    z = ((c - c.rolling(n).mean()) / c.rolling(n).std()).to_numpy()
    b = tagestrend(m).to_numpy() if bias else None
    out = np.zeros_like(z)
    for j in range(z.shape[1]):
        p = 0.0
        for i in range(z.shape[0]):
            x = z[i, j]
            if x != x:
                p = 0.0
            elif p == 0.0:
                if x < -k and (b is None or b[i, j] > 0):
                    p = 1.0
                elif x > k and (b is None or b[i, j] < 0):
                    p = -1.0
            elif (p > 0 and x >= 0) or (p < 0 and x <= 0):
                p = 0.0
            out[i, j] = p
    return pd.DataFrame(out, index=c.index, columns=c.columns)


def querschnitt(m, L, modus, takt=4, n_top=3):
    """Rangfolge alle `takt` Stunden: stärkste 3 Coins gegen schwächste 3 (modus 'mom') oder umgekehrt ('rev')."""
    c = _close(m)
    r = (c / c.shift(L) - 1)
    rang = r.rank(axis=1, ascending=False)
    n = r.notna().sum(axis=1)
    w = pd.DataFrame(0.0, index=c.index, columns=c.columns)
    w[rang <= n_top] = 1.0
    w[rang.gt(n - n_top, axis=0)] = -1.0
    w[r.isna()] = 0.0
    if modus == "rev":
        w = -w
    halten = (np.arange(len(w)) % takt) != 0
    w[halten] = np.nan
    return w.ffill().fillna(0.0)


FAMILIEN = {"tsmom": tsmom, "ensemble": ensemble, "reversal": reversal, "querschnitt": querschnitt}


# ----------------------------------------------------------------------------- Lauf ----
def lauf(m, w: np.ndarray, hebel=1.0, stop_atr=0.0, eps=None, adverse=0.0, delay=0, ttl=TTL, taker=False, slip=None,
         day_limit=None):
    S = hebel / len(m.coins)
    eq, MV, TV, FU, daily, tr, st, nt, ORD, FIL = engine2.simulate_target(
        m.o, m.h, m.l, m.c, w, m.atr, m.fund, m.day, S, ttl, runner.EPS if eps is None else eps,
        runner.SLIP if slip is None else slip, adverse, delay, stop_atr, runner.MAKER, runner.TAKER,
        runner.CFG["risiko"]["tagesverlust_limit"] if day_limit is None else day_limit, 4_000_000, taker)
    if nt > len(tr):
        raise RuntimeError("Trade-Speicher zu klein")
    t = pd.DataFrame(tr, columns=["coin", "art", "richtung", "ein", "aus", "brutto", "maker_vol", "taker_vol"])
    t["coin"] = [m.coins[int(i)] for i in t["coin"]]
    t["art"] = t["art"].map({0.0: "limit", 2.0: "sperre_ende", 3.0: "stop"})
    t["ein_zeit"] = m.index[t["ein"].astype(int)]
    t["aus_zeit"] = m.index[t["aus"].astype(int)]
    t["stunden"] = (t["aus"] - t["ein"]) * 5 / 60
    return runner.Lauf(m, hebel, {}, eq, MV, TV, FU, daily, t, st, ORD, FIL)


def sicht(l, von=None, bis=None) -> dict:
    """Kennzahlen in der Rebate-Sicht. G = vor Gebühren, F = Gebühr, R = Rebate, N = netto mit Rebate."""
    k = runner.kennzahlen(l, von, bis)
    F = k["gebuehr_tag"] * k["tage"]
    R = k["rebate_tag"] * k["tage"]
    V = k["volumen_tag"] * k["tage"]
    tg = l.daily_pnl(runner.MIT).sum(axis=1)
    a = pd.Timestamp(von) if von is not None else tg.index[0]
    b = pd.Timestamp(bis) if bis is not None else tg.index[-1] + pd.Timedelta(days=1)
    tg = tg[(tg.index >= a) & (tg.index < b)]
    N = k["rendite_mit"]
    return {"G": k["rendite_brutto"], "F": F, "R": R, "handel": k["rendite_ohne"], "N": N,
            "rebate_anteil": R / N if N > 0 else float("nan"), "dd_mit": k["dd_mit"], "vol_tag": k["volumen_tag"],
            "bp_je_umsatz": k["rendite_brutto"] / V * 1e4 if V > 0 else float("nan"),
            "maker": k["maker_anteil"], "of": k["order_zu_fill"], "trades": k["trades"], "halte_h": k["haltedauer_h"],
            "sharpe": float(tg.mean() / tg.std() * np.sqrt(365)) if tg.std() > 0 else 0.0,
            "jahr_N": N / k["tage"] * 365, "anteil_coin": k["anteil_coin"], "anteil_monat": k["anteil_monat"]}
