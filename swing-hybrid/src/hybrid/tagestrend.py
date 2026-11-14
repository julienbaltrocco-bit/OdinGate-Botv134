"""Runde 14: der 14-Tage-Trend auf Tageskursen (Nicht-Krypto-Märkte), einfache Tagesrechnung.

Signal nach Tagesschluss, Handel zur Eröffnung des nächsten Börsentags plus Slippage. Größe beim Einstieg fest.
Alle Beträge als Anteil am Kapital; `einsatz` ist der Gesamteinsatz, gleich verteilt auf die Märkte.
"""
import numpy as np
import pandas as pd

TAGE = 14


def signal(close: pd.Series, tage: int = TAGE) -> pd.Series:
    """+1 / −1 / 0 je Börsentag: Schluss gegen den letzten Schluss, der mindestens `tage` Kalendertage alt ist."""
    alt = pd.Series(close.to_numpy(), index=close.index + pd.Timedelta(days=tage))
    frueher = alt.reindex(close.index.union(alt.index)).ffill().reindex(close.index)
    return np.sign(close - frueher).fillna(0.0)


def lauf_markt(d: pd.DataFrame, kalender: pd.DatetimeIndex, S: float, slip: float, gebuehr: float,
               funding_jahr: float = 0.0, tage: int = TAGE) -> pd.DataFrame:
    """Tages-P&L eines Marktes auf dem Kalenderraster. Spalten: brutto, gebuehr, funding, umsatz."""
    d = d[(d.index >= kalender[0] - pd.Timedelta(days=tage + 46)) & (d.index <= kalender[-1])]
    sig = signal(d["close"], tage).shift(1).fillna(0.0)          # gilt ab der Eröffnung des Folgetags
    o, c, s = d["open"].to_numpy(), d["close"].to_numpy(), sig.to_numpy()
    n = len(d)
    brutto, geb, fund, ums = np.zeros(n), np.zeros(n), np.zeros(n), np.zeros(n)
    pos, richtung, cash, wert_alt = 0.0, 0.0, 0.0, 0.0
    tag_abstand = np.diff(d.index.to_numpy(), prepend=d.index.to_numpy()[:1]).astype("timedelta64[D]").astype(float)
    aktiv = d.index >= kalender[0]
    for i in range(n):
        if pos != 0.0:
            fund[i] -= funding_jahr / 365.0 * abs(pos) * c[i - 1] * tag_abstand[i]
        ziel = s[i] if aktiv[i] and i < n - 1 else 0.0
        if ziel != richtung:
            if pos != 0.0:                                       # schließen
                px = o[i] * (1.0 - np.sign(pos) * slip)
                cash += pos * px; ums[i] += abs(pos) * px; pos = 0.0
            if ziel != 0.0:                                      # öffnen
                px = o[i] * (1.0 + ziel * slip)
                pos = ziel * S / px
                cash -= pos * px; ums[i] += abs(pos) * px
            richtung = ziel
        wert = cash + pos * c[i]
        brutto[i] = wert - wert_alt
        wert_alt = wert
        geb[i] = gebuehr * ums[i]
    t = pd.DataFrame({"brutto": brutto, "gebuehr": geb, "funding": fund, "umsatz": ums}, index=d.index)
    return t.reindex(kalender).fillna(0.0)


def lauf(kurse: dict, kalender: pd.DatetimeIndex, slip: dict, gebuehr: float, einsatz: float = 1.0,
         funding_jahr: float = 0.0, tage: int = TAGE) -> dict:
    S = einsatz / len(kurse)
    return {n: lauf_markt(d, kalender, S, slip[n], gebuehr, funding_jahr, tage) for n, d in kurse.items()}


def netto(l: dict, rebate: float = 0.0) -> pd.DataFrame:
    return pd.DataFrame({n: t["brutto"] - (1.0 - rebate) * t["gebuehr"] + t["funding"] for n, t in l.items()})


def kennzahlen(tag: pd.Series, von=None, bis=None) -> dict:
    x = tag
    if von is not None:
        x = x[x.index >= pd.Timestamp(von)]
    if bis is not None:
        x = x[x.index < pd.Timestamp(bis)]
    konto = 1.0 + x.cumsum().to_numpy()
    spitze = np.maximum.accumulate(np.maximum(konto, 1.0))
    return {"N": float(x.sum()), "jahr_N": float(x.mean() * 365), "dd": float(((spitze - konto) / spitze).max()),
            "sharpe": float(x.mean() / x.std() * np.sqrt(365)) if x.std() > 0 else 0.0, "tage": int(len(x))}
