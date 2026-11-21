"""Einfache zweite Rechnung zu E24, geschrieben von einem unabhängigen Prüfer nur nach dem Text der Festlegung
(forschung/protokoll.md Abschnitt 45 und Runde 14). Dient den Tests als Vergleich für die Bausteine von E24.
"""
import numpy as np, pandas as pd
from numpy.lib.stride_tricks import sliding_window_view

Z_ST = ((0.0, 0.5), (0.5, 1.0), (1.0, 1.5), (1.5, 2.0), (2.0, np.inf))
A_ST = ((0, 24), (24, 72), (72, 168), (168, 336), (336, 10 ** 12))


def z_naiv(c):
    ch = c[11::12]; n = len(ch)
    z = np.full(n, np.nan)
    if n <= 720:
        return z
    lr = np.log(ch[1:] / ch[:-1])                       # lr[i] = Rendite der Stunde i+1
    for a in range(720, n, 4000):
        b = min(n, a + 4000)
        w = sliding_window_view(lr[a - 720:b - 1], 720)   # Zeile i: Renditen der Stunden a+i-719 .. a+i
        sd = w.std(axis=1, ddof=1)
        num = np.abs(np.log(ch[a:b] / ch[a - 336:b - 336]))
        with np.errstate(divide='ignore', invalid='ignore'):
            zz = num / (sd * np.sqrt(336))
        z[a:b] = np.where(sd > 0, zz, np.nan)
    return z


def d_naiv(c):
    ch = c[11::12]; d = np.zeros(len(ch), int)
    d[336:] = np.sign(ch[336:] - ch[:-336])
    return d


def alter_naiv(d):
    out = np.zeros(len(d), int)
    for t in range(1, len(d)):
        out[t] = out[t - 1] + 1 if d[t] == d[t - 1] else 0
    return out


def richtungen(c):
    d, z = d_naiv(c), z_naiv(c); alt = alter_naiv(d)
    r = {'B0': d}
    with np.errstate(invalid='ignore'):
        for x in (1.0, 1.5, 2.0):
            r[f'A1_z_bis_{x}'] = np.where(z <= x, d, 0)
        for x in (0.25, 0.5, 1.0):
            r[f'A2_z_ab_{x}'] = np.where(z >= x, d, 0)
        for i, (a, b) in enumerate(Z_ST):
            r[f'z_{i}'] = np.where((z >= a) & (z < b), d, 0)
    for i, (a, b) in enumerate(A_ST):
        r[f'alter_{i}'] = np.where((alt >= a) & (alt < b), d, 0)
    return r, d, z, alt


def orders_naiv(o, g, r, i_ende):
    """Pruefung j (Kerzen j und j+1 gueltig, j+1 < i_ende): Soll = r[j//12 - 1]; Ausfuehrung zu o[j+1]."""
    pos, out = 0, []
    j = np.arange(i_ende - 1)
    ok = g[:i_ende - 1] & g[1:i_ende]
    th = j // 12 - 1
    soll = np.where(th >= 0, r[np.maximum(th, 0)], 0)
    js = j[ok]; s = soll[ok]
    vor = np.concatenate([[0], s[:-1]])
    for k in np.nonzero(s != vor)[0]:
        e = js[k] + 1
        if vor[k] != 0: out.append((e, -vor[k], 2, o[e]))
        if s[k] != 0: out.append((e, s[k], 1, o[e]))
    return np.array(out, float).reshape(-1, 4)


def signal14(dates, close):
    """Je Boersentag i: Vorzeichen(close[i] - letzter Schluss, der mindestens 14 Kalendertage alt ist); 0 ohne solchen."""
    out = np.zeros(len(close))
    for i in range(len(close)):
        k = np.searchsorted(dates, dates[i] - np.timedelta64(14, 'D'), side='right') - 1
        if k >= 0:
            out[i] = np.sign(close[i] - close[k])
    return out


def tagesrechnung(d, kal, S, slip, fee, fund_jahr=0.0, sig=None, rebate=0.85):
    """Netto je Kalendertag. sig=None: eigener 14-Tage-Trend (Signal nach Schluss, Handel naechste Eroeffnung);
    sonst sig = Reihe je Kalendertag, gueltig ab der Eroeffnung dieses Boersentags."""
    d = d[(d.index >= kal[0] - pd.Timedelta(days=60)) & (d.index <= kal[-1])]
    dates = d.index.to_numpy().astype('datetime64[D]'); o = d['open'].to_numpy(); c = d['close'].to_numpy(); n = len(d)
    netto = pd.Series(0.0, index=kal)
    if n == 0:
        return netto
    if sig is None:
        s14 = signal14(dates, c)
        ziel = np.concatenate([[0.0], s14[:-1]])
    else:
        ziel = np.array([float(sig.get(pd.Timestamp(x), 0.0)) for x in dates])
    k0 = np.datetime64(kal[0].date())
    menge, ri = 0.0, 0.0
    for i in range(n):
        z = ziel[i] if (dates[i] >= k0 and i < n - 1) else 0.0
        pnl, geb, fund = 0.0, 0.0, 0.0
        if menge != 0.0:
            tage = (dates[i] - dates[i - 1]).astype(int)
            fund = -fund_jahr / 365.0 * abs(menge) * c[i - 1] * tage
            pnl += menge * (o[i] - c[i - 1])                       # ueber Nacht bis zur Eroeffnung (ohne Slippage)
        if z != ri:
            if menge != 0.0:
                px = o[i] * (1 - np.sign(menge) * slip)
                pnl += menge * (px - o[i]); geb += fee * abs(menge) * px; menge = 0.0
            if z != 0.0:
                px = o[i] * (1 + z * slip)
                menge = z * S / px
                pnl += menge * (o[i] - px); geb += fee * abs(menge) * px
            ri = z
        pnl += menge * (c[i] - o[i])
        t = pd.Timestamp(dates[i])
        if t in netto.index:
            netto[t] = pnl - (1 - rebate) * geb + fund
        else:
            assert pnl == 0 and geb == 0 and fund == 0
    return netto


def btc_sig_naiv(c5, kal):
    """Signal je Kalendertag D: Vorzeichen(Schluss 23:55-Kerze von D-1 minus Schluss 23:55-Kerze von D-15)."""
    t0 = pd.Timestamp('2021-07-01'); out = {}
    for D_ in kal:
        k = (D_ - t0).days
        out[D_] = float(np.sign(c5[288 * k - 1] - c5[288 * (k - 14) - 1])) if k >= 15 else 0.0
    return pd.Series(out)
