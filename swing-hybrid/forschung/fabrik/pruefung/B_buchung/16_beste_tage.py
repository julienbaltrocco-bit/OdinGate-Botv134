"""Welche Tage tragen die Finalisten? (gespeicherte Tagesreihen, T und V1) – Suche nach Datenartefakten an den ertragreichsten Tagen."""
import sqlite3, sys, collections
import numpy as np
sys.path.insert(0, 'forschung/fabrik/pruefung/B_buchung')
import pruef_lib as P
from fabrik import daten as D, lauf as L
con = sqlite3.connect('file:data/fabrik/forschung.sqlite?mode=ro', uri=True)
con.row_factory = sqlite3.Row
zeilen = [dict(r) for r in con.execute("SELECT * FROM kandidaten WHERE status = 'final' AND braucht != 't' AND (best IS NULL OR (best NOT LIKE '%tiefe%' AND best NOT LIKE '%liq_entzug%'))")]
tage = {g: np.load(f'data/fabrik/tage_{g}.npy', mmap_mode='r') for g in ("gen1", "gen2")}
M = np.stack([np.asarray(tage[z['gen']][z['zeile']], dtype=np.float64) for z in zeilen])
T = M[:, :685]
anteil = T / T.sum(1, keepdims=True)
best = T.argmax(1)
zahl = collections.Counter(best.tolist())
datum = lambda t: str(D.RASTER[P.TAG_VON + 288 * t].date())
print("Finalisten im Kurs-Segment:", len(zeilen))
print("Häufigster bester Tag (Tag, Zahl der Finalisten, mittlerer Anteil am T-Ergebnis über ALLE Finalisten):")
for t, n in zahl.most_common(8):
    j_rng = []
    for j, coin in enumerate(D.COINS):
        a = P.TAG_VON + 288 * t
        hi, lo, op = P.h[j, a:a + 288].max(), P.l[j, a:a + 288].min(), P.o[j, a]
        j_rng.append(f"{coin} {1e4*(hi/lo-1):.0f}")
    print(f"  {datum(t)}: {n:>4} Finalisten, mittlerer Anteil {anteil[:, t].mean():.3f} | Tagesspanne Hoch/Tief in bp: {', '.join(j_rng)} | ungültige Kerzen: {int((~P.gueltig[:, P.TAG_VON + 288 * t:P.TAG_VON + 288 * (t + 1)]).sum())}")
mittel = anteil.mean(0)
top = np.argsort(-mittel)[:10]
print("Die 10 Tage mit dem größten mittleren Anteil am T-Ergebnis:", [(datum(t), round(float(mittel[t]), 3)) for t in top], "| Summe", round(float(mittel[top].sum()), 3))
ohne = np.delete(T, top, axis=1)
tw = ohne.mean(1) / ohne.std(1, ddof=1) * np.sqrt(ohne.shape[1])
print(f"t85 in T ohne diese 10 von 685 Tagen: Median {np.median(tw):.2f} (mit: {np.median([z['t85_t'] for z in zeilen]):.2f}); unter 2: {(tw < 2).sum()} von {len(zeilen)}; nicht mehr positiv: {(ohne.sum(1) <= 0).sum()}")
