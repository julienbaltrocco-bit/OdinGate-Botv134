"""Runde 17: zwei marktneutrale Tagesrechnungen auf Nicht-Krypto-Märkten.

`paar`: Z-Wert des logarithmierten Preisverhältnisses; gegen die Abweichung handeln. Signal nach Tagesschluss,
Handel zur nächsten Eröffnung. `momentum`: Rangfolge nach 12-1-Monats-Rendite, monatliche Umschichtung.
Alle Beträge als Anteil am Kapital. Rückgabe je Tag: brutto, slip (Slippage-Kosten), umsatz, gehalten (Betragssumme).
"""
import numpy as np
import pandas as pd


def paar(a: pd.DataFrame, b: pd.DataFrame, S: float, slip_a: float, slip_b: float, start, fenster=30, z_ein=2.0,
         z_aus=0.5, z_stop=4.0) -> pd.DataFrame:
    idx = a.index.intersection(b.index)
    a, b = a.loc[idx], b.loc[idx]
    v = np.log(a["close"] / b["close"])
    roll = v.rolling(f"{fenster}D", min_periods=15)
    z = ((v - roll.mean()) / roll.std()).to_numpy()
    oa, ob, ca, cb = a["open"].to_numpy(), b["open"].to_numpy(), a["close"].to_numpy(), b["close"].to_numpy()
    n = len(idx)
    out = np.zeros((n, 4))
    qa = qb = 0.0
    richtung, gesperrt, wert_alt, cash = 0, 0, 0.0, 0.0
    aktiv = idx >= pd.Timestamp(start)
    for i in range(1, n):
        zz = z[i - 1]                                            # bekannt nach dem Schluss des Vortags
        ziel = richtung
        if not np.isfinite(zz):
            ziel = 0
        elif richtung != 0 and (abs(zz) <= z_aus or abs(zz) >= z_stop):
            if abs(zz) >= z_stop:
                gesperrt = richtung                              # nach Notausstieg erst wieder nach Rückkehr unter z_aus
            ziel = 0
        elif richtung == 0 and z_ein <= abs(zz) < z_stop and aktiv[i]:
            neu = -1 if zz > 0 else 1                            # Verhältnis zu hoch: A short, B long
            if gesperrt != neu:
                ziel = neu
        if gesperrt != 0 and np.isfinite(zz) and abs(zz) <= z_aus:
            gesperrt = 0
        if i == n - 1:
            ziel = 0
        if ziel != richtung:
            if richtung != 0:
                cash += qa * oa[i] + qb * ob[i]
                out[i, 1] += abs(qa) * oa[i] * slip_a + abs(qb) * ob[i] * slip_b
                out[i, 2] += abs(qa) * oa[i] + abs(qb) * ob[i]
                qa = qb = 0.0
            if ziel != 0:
                qa, qb = ziel * S / 2 / oa[i], -ziel * S / 2 / ob[i]
                cash -= qa * oa[i] + qb * ob[i]
                out[i, 1] += S / 2 * (slip_a + slip_b)
                out[i, 2] += S
            richtung = ziel
        wert = cash + qa * ca[i] + qb * cb[i]
        out[i, 0] = wert - wert_alt
        wert_alt = wert
        out[i, 3] = abs(qa) * ca[i] + abs(qb) * cb[i]
    return pd.DataFrame(out, index=idx, columns=["brutto", "slip", "umsatz", "gehalten"])


def momentum_gewichte(close: pd.DataFrame, min_tage=400, anteil=0.3) -> pd.DataFrame:
    """Zielgewichte je Monatsende (Zeile = letzter Börsentag des Monats). Summe der Beträge = 1."""
    lang = pd.DataFrame(close.to_numpy(), index=close.index + pd.Timedelta(days=365), columns=close.columns)
    kurz = pd.DataFrame(close.to_numpy(), index=close.index + pd.Timedelta(days=30), columns=close.columns)
    auf = lambda x: x.reindex(close.index.union(x.index)).ffill().reindex(close.index)
    r = auf(kurz) / auf(lang) - 1
    genug = close.notna().cumsum() >= int(min_tage * 252 / 365)
    r = r.where(genug & close.notna())
    letzte = close.index.to_series().groupby([close.index.year, close.index.month]).max().to_numpy()
    r = r.loc[letzte]
    n = r.notna().sum(axis=1)
    k = np.maximum((n * anteil).round(), 1)
    rang = r.rank(axis=1, ascending=False)
    w = pd.DataFrame(0.0, index=r.index, columns=r.columns)
    oben, unten = rang.le(k, axis=0), rang.gt(n - k, axis=0)
    w = w.where(~oben, (0.5 / k).to_numpy()[:, None] * np.ones(len(r.columns)))
    w = w.where(~unten, (-0.5 / k).to_numpy()[:, None] * np.ones(len(r.columns)))
    w[n < 10] = 0.0
    return w


def momentum(close: pd.DataFrame, slip: pd.Series, start, einsatz=1.0, **kw) -> pd.DataFrame:
    w = momentum_gewichte(close, **kw) * einsatz
    c = close.ffill()
    tage = close.index
    pos = {t: i for i, t in enumerate(tage)}
    handel = {tage[pos[t] + 1]: w.loc[t] for t in w.index if pos[t] + 1 < len(tage) and tage[pos[t] + 1] >= pd.Timestamp(start)}
    q = pd.Series(0.0, index=close.columns)
    out = np.zeros((len(tage), 4))
    cash, wert_alt = 0.0, 0.0
    sl = slip.reindex(close.columns).to_numpy()
    for i, t in enumerate(tage):
        px = c.iloc[i].to_numpy()
        ok = np.isfinite(px)
        if t in handel or i == len(tage) - 1:
            ziel = np.zeros(len(q)) if i == len(tage) - 1 else np.where(ok, handel[t].to_numpy() / np.where(ok, px, 1.0), 0.0)
            dq = ziel - q.to_numpy()
            betrag = np.where(ok, np.abs(dq) * np.where(ok, px, 0.0), 0.0)
            cash -= float(np.nansum(np.where(ok, dq * np.where(ok, px, 0.0), 0.0)))
            out[i, 1] = float((betrag * sl).sum()); out[i, 2] = float(betrag.sum())
            q = pd.Series(ziel, index=close.columns)
        wert = cash + float(np.nansum(q.to_numpy() * np.where(ok, px, 0.0)))
        out[i, 0] = wert - wert_alt
        wert_alt = wert
        out[i, 3] = float(np.nansum(np.abs(q.to_numpy()) * np.where(ok, px, 0.0)))
    return pd.DataFrame(out, index=tage, columns=["brutto", "slip", "umsatz", "gehalten"])


def netto(t: pd.DataFrame, kalender, taker: float, rebate: float, slip_faktor=1.0, funding_jahr=0.0) -> pd.Series:
    abstand = pd.Series(np.diff(t.index.to_numpy(), prepend=t.index.to_numpy()[:1]).astype("timedelta64[D]").astype(float), index=t.index)
    fund = funding_jahr / 365.0 * t["gehalten"].shift(1).fillna(0.0) * abstand
    return (t["brutto"] - slip_faktor * t["slip"] - taker * (1 - rebate) * t["umsatz"] - fund).reindex(kalender).fillna(0.0)
