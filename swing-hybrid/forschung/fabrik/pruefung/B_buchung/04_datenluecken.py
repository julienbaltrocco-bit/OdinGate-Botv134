"""Datenlücken und Kerzen-Plausibilität im Datenspeicher (nur Kerzen < I_ENDE). Was macht der Simulator an Lücken?"""
import sys
import numpy as np, pandas as pd
sys.path.insert(0, 'forschung')
from fabrik import daten as D, lauf as L
E = L.I_ENDE
o, h, l, c = (np.asarray(D.laden(x)[:, :E]) for x in "ohlc")
g = np.asarray(D.laden("gueltig")[:, :E])
sig = np.asarray(D.laden("sigma")[:, :E])
for j, coin in enumerate(D.COINS):
    u = np.flatnonzero(~g[j, L.I_T:]) + L.I_T
    if len(u):
        bl = np.split(u, np.flatnonzero(np.diff(u) > 1) + 1)
        for b in bl:
            a, e = b[0], b[-1]
            print(f"{coin}: Lücke {D.RASTER[a]} bis {D.RASTER[e]} ({len(b)} Kerzen) | Schluss davor {c[j, a-1]:.4f}, Eröffnung danach {o[j, e+1]:.4f} "
                  f"(Sprung {1e4*(o[j, e+1]/c[j, a-1]-1):+.0f} bp) | sigma letzte Kerze davor {sig[j, a-1]:.5f}, erste danach {sig[j, e+1]:.5f}, 1 Tag danach {sig[j, e+1+288]:.5f}")
    v = g[j, L.I_T:]
    oo, hh, ll, cc = o[j, L.I_T:][v], h[j, L.I_T:][v], l[j, L.I_T:][v], c[j, L.I_T:][v]
    bad = (hh < np.maximum(oo, cc)) | (ll > np.minimum(oo, cc)) | (ll <= 0)
    spr = np.abs(o[j, L.I_T + 1:] / c[j, L.I_T:-1] - 1) * 1e4
    print(f"{coin:<5} unplausible Kerzen (H<max(O,C) oder T>min(O,C)): {int(bad.sum())} | |Eröffnung/Vorschluss-1| > 20 bp: {int((spr > 20).sum())} Kerzen, max {spr.max():.0f} bp | "
          f"größte Kerzenspanne {((hh-ll)/oo).max()*1e4:.0f} bp | sigma<=0 oder NaN in [I_T,I_ENDE): {int((~(sig[j, L.I_T:] > 0)).sum())}")
