"""Runde 24: Kandidat (14-Tage-Trend) mit Gewinnziel, Stop oder nachgezogenem Stop.

Einstieg, wenn das Signal dreht. Ausstieg, wenn das Ergebnis seit Einstieg (auf Stundenschlüssen) Ziel oder Stop
erreicht; danach keine Position, bis das Signal wieder dreht. Gewichte wie überall: Index = Stundenbeginn, bekannt bei
Stundenschluss.
"""
import numpy as np
import pandas as pd
from numba import njit

from . import mutationen as M, research as R


@njit(cache=True)
def _zustand(c, sig, tp, sl, trail):
    n = len(c)
    out = np.zeros(n)
    pos, ein, best, gesperrt = 0.0, 0.0, 0.0, 0.0
    for i in range(n):
        s = sig[i]
        if not np.isfinite(c[i]):
            out[i] = 0.0
            continue
        if gesperrt != 0.0 and s != gesperrt:
            gesperrt = 0.0
        if pos != 0.0 and s != pos:                        # Signal dreht: alte Position endet
            pos = 0.0
        if pos == 0.0 and s != 0.0 and gesperrt == 0.0:    # Einstieg
            pos, ein, best = s, c[i], c[i]
        elif pos != 0.0:
            r = (c[i] / ein - 1.0) * pos
            if pos > 0:
                best = max(best, c[i])
            else:
                best = min(best, c[i])
            zurueck = (best / c[i] - 1.0) if pos > 0 else (c[i] / best - 1.0)
            if (tp > 0 and r >= tp) or (sl > 0 and r <= -sl) or (trail > 0 and zurueck >= trail):
                gesperrt, pos = pos, 0.0
        out[i] = pos
    return out


def gewichte(m, tp=0.0, sl=0.0, trail=0.0) -> pd.DataFrame:
    c = R._close(m)
    b = M.basis(m)
    return pd.DataFrame({k: _zustand(c[k].to_numpy(dtype=np.float64), b[k].to_numpy(dtype=np.float64), tp, sl, trail) for k in c.columns}, index=c.index)


def _v(**kw):
    return lambda m: gewichte(m, **kw)


VARIANTEN = {"sl5": _v(sl=0.05), "sl10": _v(sl=0.10), "sl15": _v(sl=0.15), "tp10": _v(tp=0.10), "tp20": _v(tp=0.20), "tp30": _v(tp=0.30),
             "sl5_tp15": _v(sl=0.05, tp=0.15), "sl10_tp20": _v(sl=0.10, tp=0.20), "sl15_tp30": _v(sl=0.15, tp=0.30),
             "trail10": _v(trail=0.10), "trail15": _v(trail=0.15)}
