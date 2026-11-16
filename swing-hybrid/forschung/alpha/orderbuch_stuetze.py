"""Strategie „Orderbuch-Stütze“ Version 1.0 (eingefroren in forschung/protokoll.md, Abschnitt 10).

Signal: Übergewicht der Kauf- gegenüber den Verkaufsaufträgen bis 5 % um den Kurs, 5-Minuten-Mittel, als Abweichung
vom eigenen 24-Stunden-Mittel in Standardabweichungen (z). z >= +3 -> Long, z <= -3 -> Short, 60 Minuten halten.
"""
import numpy as np
import pandas as pd

from . import kern as K

VERSION = "1.0"
PARAMETER = {"tiefe_pct": 5, "fenster_kerzen": 288, "schwelle_z": 3.0, "haltedauer_kerzen": 12, "kerze": "5m"}


def z_wert(coin: str, tiefe=5, fenster=288):
    k = K.lesen("5m", coin)
    k = k[k.index >= "2023-01-01"]
    d = K.lesen("tiefe_5m", coin).reindex(k.index)
    u = (d[f"w-{tiefe}"] - d[f"w+{tiefe}"]) / (d[f"w-{tiefe}"] + d[f"w+{tiefe}"])
    return k, ((u - u.rolling(fenster, min_periods=200).mean()) / u.rolling(fenster, min_periods=200).std()).to_numpy()


def trades(coin: str, schwelle=3.0, halte=12, verzug=0, tiefe=5) -> pd.DataFrame:
    """Trades der Regel für einen Coin; `verzug` = zusätzliche Kerzen Verzögerung bei Ein- und Ausstieg."""
    k, z = z_wert(coin, tiefe)
    i = np.flatnonzero(np.abs(z) >= schwelle)
    ein, aus = i + 1 + verzug, i + 1 + verzug + halte
    ok = K.ohne_ueberlappung(ein, aus)
    t = K.trades(coin, k, ein[ok], aus[ok], np.sign(z[i])[ok], K.lesen("funding", coin))
    # ungünstigster Kurs während der Haltedauer (für Margin und Liquidation), in bp gegen die Position
    hoch, tief, o = k["high"].to_numpy(), k["low"].to_numpy(), k["open"].to_numpy()
    a, b, r = ein[ok][: len(t)], aus[ok][: len(t)], t["richtung"].to_numpy()
    t["schlimmst"] = [((tief[x:y].min() if s > 0 else hoch[x:y].max()) / o[x] - 1) * s * 1e4 for x, y, s in zip(a, b, r)]
    return t
