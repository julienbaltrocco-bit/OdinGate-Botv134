"""Runde 21: 14 Abwandlungen des Kandidaten (14-Tage-Trend). Jede Funktion gibt Stunden-Zielgewichte zurück
(Index = Stundenbeginn, bekannt bei Stundenschluss; `research.auf_raster` verschiebt um eine Stunde)."""
import numpy as np
import pandas as pd

from . import research as R

L, HALB, SCHW = 336, 168, 2160          # 14 Tage, 7 Tage, 90 Tage in Stunden


def _c(m):
    return R._close(m)


def _r(c):
    return c / c.shift(L) - 1


def _schwankung(c):
    return _r(c).rolling(SCHW, min_periods=SCHW // 2).std()


def basis(m):
    return np.sign(_r(_c(m))).fillna(0.0)


def nur_long(m):
    return basis(m).clip(lower=0.0)


def asym_70_30(m):
    b = basis(m)
    return b.clip(lower=0.0) * 1.4 + b.clip(upper=0.0) * 0.6


def band(m):
    c = _c(m)
    r, s = _r(c), _schwankung(c)
    z = pd.DataFrame(np.nan, index=c.index, columns=c.columns)
    z = z.mask(r > 0.5 * s, 1.0).mask(r < -0.5 * s, -1.0)
    return z.ffill().fillna(0.0).where(c.notna(), 0.0)


def ema_kreuz(m):
    c = _c(m)
    d = c.ewm(span=84, adjust=False, min_periods=L).mean() - c.ewm(span=L, adjust=False, min_periods=L).mean()
    return np.sign(d).fillna(0.0)


def donchian(m):
    c = _c(m)
    v = c.shift(1)
    hoch, tief = v.rolling(L).max(), v.rolling(L).min()
    hoch2, tief2 = v.rolling(HALB).max(), v.rolling(HALB).min()
    out = np.zeros(c.shape)
    for j in range(c.shape[1]):
        x, h, t, h2, t2 = (a.iloc[:, j].to_numpy() for a in (c, hoch, tief, hoch2, tief2))
        p = 0.0
        for i in range(len(x)):
            if not np.isfinite(h[i]) or not np.isfinite(x[i]):
                out[i, j] = p if np.isfinite(x[i]) else 0.0
                continue
            if x[i] > h[i]:
                p = 1.0
            elif x[i] < t[i]:
                p = -1.0
            elif p > 0 and x[i] < t2[i]:
                p = 0.0
            elif p < 0 and x[i] > h2[i]:
                p = 0.0
            out[i, j] = p
    return pd.DataFrame(out, index=c.index, columns=c.columns)


def stetig(m):
    c = _c(m)
    w = (_r(c) / _schwankung(c)).clip(-1.0, 1.0)
    return (np.round(w * 4) / 4).fillna(0.0)


def ohne_letzten_tag(m):
    c = _c(m)
    return np.sign(c.shift(24) / c.shift(L) - 1).fillna(0.0)


def breite(m):
    c = _c(m)
    r = _r(c)
    b = np.sign(r).fillna(0.0)
    n = r.notna().sum(axis=1)
    ok_l = (b > 0).sum(axis=1) >= 0.7 * n
    ok_s = (b < 0).sum(axis=1) >= 0.7 * n
    return b.clip(lower=0.0).mul(ok_l, axis=0) + b.clip(upper=0.0).mul(ok_s, axis=0)


def _btc(m):
    if hasattr(m, "btc_close"):
        return m.btc_close
    return R._lesen("5m", "BTC", True)["close"].resample("1h").last().dropna()


def btc_regime(m):
    b = basis(m)
    btc = _btc(m)
    oben = (btc > btc.rolling(4800, min_periods=4800).mean()).reindex(b.index)
    unten = (btc < btc.rolling(4800, min_periods=4800).mean()).reindex(b.index)
    return b.clip(lower=0.0).mul(oben.fillna(False), axis=0) + b.clip(upper=0.0).mul(unten.fillna(False), axis=0)


def effizienz(m):
    c = _c(m)
    er = (c - c.shift(L)).abs() / c.diff().abs().rolling(L).sum()
    med = er.rolling(4320, min_periods=2160).median()
    return basis(m).where(er > med, 0.0)


def volumen(m):
    v = pd.DataFrame({coin: m.h1[coin]["quote_volume"] for coin in m.coins})
    return basis(m).where(v.rolling(L).mean() > v.rolling(SCHW).mean(), 0.0)


def _funding(m, coin):
    if hasattr(m, "fund_h"):
        return m.fund_h[coin]
    return R._lesen("funding", coin, True)["rate"]


def funding_filter(m, grenze=0.0003):
    b = basis(m)
    f = {}
    for coin in m.coins:
        s = _funding(m, coin).rolling("3D").sum() / 9.0
        s.index = s.index.floor("h")
        s = s[~s.index.duplicated(keep="last")]
        f[coin] = s.reindex(b.index.union(s.index)).ffill().reindex(b.index)
    f = pd.DataFrame(f).fillna(0.0)
    return b.where(~((b > 0) & (f > grenze)) & ~((b < 0) & (f < -grenze)), 0.0)


def markt_trend(m):
    c = _c(m)
    korb = (1.0 + c.pct_change(fill_method=None).mean(axis=1).fillna(0.0)).cumprod()
    s = np.sign(korb / korb.shift(L) - 1).fillna(0.0)
    w = pd.DataFrame(np.repeat(s.to_numpy()[:, None], c.shape[1], axis=1), index=c.index, columns=c.columns)
    return w.where(_r(c).notna(), 0.0)


def relativ_staerke(m):
    c = _c(m)
    r = _r(c)
    z = (r.abs() / _schwankung(c))
    n = z.notna().sum(axis=1)
    rang = z.rank(axis=1, ascending=False)
    stark = rang.le(n / 2, axis=0)
    g = pd.DataFrame(np.where(stark, 1.5, 0.5), index=c.index, columns=c.columns).where(z.notna(), 1.0)
    return (np.sign(r) * g).fillna(0.0)


VARIANTEN = {"nur_long": nur_long, "asym_70_30": asym_70_30, "band": band, "ema_kreuz": ema_kreuz, "donchian": donchian,
             "stetig": stetig, "ohne_letzten_tag": ohne_letzten_tag, "breite": breite, "btc_regime": btc_regime,
             "effizienz": effizienz, "volumen": volumen, "funding_filter": funding_filter, "markt_trend": markt_trend,
             "relativ_staerke": relativ_staerke}


def reality_check(diff: np.ndarray, ziehungen=5000, block=20, seed=21):
    """White's Reality Check mit stationärem Bootstrap. `diff`: Tage x Varianten (Vorsprung je Tag).
    Gibt (Mittelwerte, 95-%-Schwelle des größten Zufalls-Vorsprungs, p-Wert der besten) zurück."""
    rng = np.random.default_rng(seed)
    n, k = diff.shape
    mittel = diff.mean(axis=0)
    zentriert = diff - mittel
    maxima = np.empty(ziehungen)
    for b in range(ziehungen):
        neu = rng.random(n) < 1.0 / block
        neu[0] = True
        start = rng.integers(0, n, n)
        idx = np.empty(n, dtype=np.int64)
        pos = 0
        for i in range(n):
            pos = start[i] if neu[i] else (pos + 1) % n
            idx[i] = pos
        maxima[b] = zentriert[idx].mean(axis=0).max()
    return mittel, float(np.percentile(maxima, 95)), float((maxima >= mittel.max()).mean())
