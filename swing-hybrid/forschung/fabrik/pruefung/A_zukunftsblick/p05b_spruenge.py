"""Sprünge zwischen Schluss einer Kerze und Eröffnung der nächsten im Speicher (Kerzen < I_ENDE): Häufigkeit und größte Fälle.
Zweck: Der Einstieg erfolgt zur Eröffnung i+1. Wäre die Eröffnung systematisch günstiger als der Schluss i, läge ein versteckter Vorteil vor."""
import sys
sys.path.insert(0, 'forschung')
import numpy as np, pandas as pd
from fabrik import daten as D, lauf as L
I = L.I_ENDE
for j, coin in enumerate(D.COINS):
    o, c, g = (np.asarray(np.load(D.SPEICHER / f"{n}.npy", mmap_mode="r")[j, :I]) for n in ("o", "c", "gueltig"))
    ok = g[1:] & g[:-1]
    s = (o[1:] / c[:-1] - 1) * 1e4
    s = np.where(ok, s, 0.0)
    k = int(np.argmax(np.abs(s)))
    print(f"{coin}: |Sprung| Median {np.median(np.abs(s[ok])):.2f} bp, 99,9 %-Quantil {np.quantile(np.abs(s[ok]), 0.999):.1f} bp, >20 bp: {int((np.abs(s) > 20).sum())} Kerzen, >100 bp: {int((np.abs(s) > 100).sum())}; "
          f"größter {s[k]:+.1f} bp bei {D.RASTER[k + 1]} (Schluss {c[k]:.5g}, Eröffnung {o[k + 1]:.5g}, Schluss danach {c[k + 1]:.5g})")
