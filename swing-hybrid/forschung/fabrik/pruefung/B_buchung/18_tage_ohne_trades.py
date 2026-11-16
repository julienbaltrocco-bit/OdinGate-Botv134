"""Tage ohne Trades: lauf.kennzahlen rechnet den t-Wert über ALLE Kalendertage des Segments (Nulltage zählen mit).
Vergleich mit dem t-Wert nur über Tage mit Buchung (wie alpha.kern.t_tage in Abschnitt 4) auf den gespeicherten Tagesreihen aller Kandidaten mit bestandener Stufe 2."""
import sqlite3, sys
import numpy as np
sys.path.insert(0, 'forschung')
from fabrik import lauf as L
con = sqlite3.connect('file:data/fabrik/forschung.sqlite?mode=ro', uri=True)
con.row_factory = sqlite3.Row
zeilen = con.execute("SELECT gen, zeile, braucht, best, t85_t FROM kandidaten WHERE status IN ('final','stufe3','verworfen_3','stufe2') ORDER BY gen, zeile").fetchall()
tage = {g: np.load(f'data/fabrik/tage_{g}.npy', mmap_mode='r') for g in ("gen1", "gen2")}
v, groesser = [], 0
for z in zeilen:
    tief = z["braucht"] == "t" or (z["best"] and ("tiefe" in z["best"] or "liq_entzug" in z["best"]))
    t0, v0, e = L.SEGMENTE["t" if tief else "k"]
    p = np.asarray(tage[z["gen"]][z["zeile"]][t0:v0], dtype=np.float64)
    q = p[p != 0]
    t_alle = p.mean() / p.std(ddof=1) * np.sqrt(len(p))
    t_nur = q.mean() / q.std(ddof=1) * np.sqrt(len(q))
    assert abs(t_alle - z["t85_t"]) < 0.01
    v.append(t_alle / t_nur); groesser += t_alle > t_nur + 1e-9
v = np.array(v)
print(f"{len(zeilen)} Kandidaten: t (alle Kalendertage) / t (nur Tage mit Trades): Median {np.median(v):.3f}, Maximum {v.max():.4f}; Fälle, in denen die Nulltage den t-Wert ERHÖHEN: {groesser}")
