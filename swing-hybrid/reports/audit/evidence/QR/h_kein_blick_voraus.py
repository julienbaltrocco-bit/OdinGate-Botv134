"""QR (h): Stoerungstest gegen Blick voraus. Module aus src/hybrid, eigene Kopie des Marktes.

Alle Kurse AB einem Zeitpunkt T werden veraendert (x 1,5 bzw. x 0,5 je nach Coin). Wenn weder Signal noch Rechenkern
Daten aus der Zukunft benutzen, muss der Kontoverlauf bis zur letzten Kerze VOR T bitgenau gleich bleiben und die
Zielgewichte bis einschliesslich der Kerze T ebenso (das Gewicht der Kerze T stammt aus dem Stundenschluss vor T).

Aufruf aus swing-hybrid/:  NUMBA_CACHE_DIR=<scratch>/numba .venv/bin/python -I -B <dieses Skript>
"""
import copy
import sys

sys.path.insert(0, "src")
import numpy as np
import pandas as pd
from hybrid import mutationen as M, research as R, runner, tpsl

m = R.markt(R.GRUPPE_A, vor=True)
k = R.yubit_kosten(R.GRUPPE_A)[0]
ok = True
for T in ("2022-06-01 00:00", "2023-03-17 13:00", "2025-10-10 21:00"):
    iT = int(m.index.searchsorted(pd.Timestamp(T)))
    m2 = copy.copy(m)
    f = np.where(np.arange(len(m.coins)) % 2 == 0, 1.5, 0.5)[:, None]
    for name in ("o", "h", "l", "c"):
        a = getattr(m, name).copy(); a[:, iT:] *= f; setattr(m2, name, a)
    m2.h1 = {}
    for j, coin in enumerate(m.coins):
        st = m.h1[coin].copy()
        st.loc[st.index >= pd.Timestamp(T), ["open", "high", "low", "close"]] *= f[j, 0]
        m2.h1[coin] = st
    for name, fn in (("basis", M.basis), ("sl5_tp15", tpsl.VARIANTEN["sl5_tp15"]), ("funding_filter", M.funding_filter)):
        w1, w2 = R.auf_raster(m, fn(m)), R.auf_raster(m2, fn(m2))
        l1 = R.lauf(m, w1, taker=True, slip=k, day_limit=9.0)
        l2 = R.lauf(m2, w2, taker=True, slip=k, day_limit=9.0)
        gw = bool(np.array_equal(w1[:, :iT + 1], w2[:, :iT + 1]))
        ge = bool(np.array_equal(l1.equity(runner.MIT)[:iT], l2.equity(runner.MIT)[:iT]))
        anders = bool(not np.array_equal(l1.equity(runner.MIT)[iT:], l2.equity(runner.MIT)[iT:]))
        ok &= gw and ge and anders
        print(f"T={T} {name:15s} Gewichte bis T gleich: {gw} | Konto vor T gleich: {ge} | Konto ab T verschieden (Test wirkt): {anders}")
print("ERGEBNIS:", "kein Blick voraus gefunden" if ok else "ABWEICHUNG: bitte pruefen")
