"""Überblick: Datenbank (nur lesend), Datenspeicher (nur bis I_ENDE), Kostenparameter."""
import sqlite3, sys, json
import numpy as np
sys.path.insert(0, 'forschung')
from fabrik import daten as D, lauf as L, generator as G, signale as S

con = sqlite3.connect('file:data/fabrik/forschung.sqlite?mode=ro', uri=True)
con.row_factory = sqlite3.Row
print("Spalten:", [r[1] for r in con.execute("PRAGMA table_info(kandidaten)")])
for r in con.execute("SELECT gen, status, COUNT(*) c FROM kandidaten GROUP BY gen, status"):
    print(dict(r))
print("gen1 Zeilen:", con.execute("SELECT COUNT(*), COUNT(DISTINCT zeile), MIN(zeile), MAX(zeile) FROM kandidaten WHERE gen='gen1'").fetchone()[:])
print("gen1 x:", [r[0] for r in con.execute("SELECT DISTINCT x FROM kandidaten WHERE gen='gen1'")])
print("gen1 m:", [r[0] for r in con.execute("SELECT DISTINCT m FROM kandidaten WHERE gen='gen1'")])
print("I_T, I_TIEFE, I_V1, I_ENDE, N_TAGE, D.N:", L.I_T, L.I_TIEFE, L.I_V1, L.I_ENDE, L.N_TAGE, D.N)
print("SEGMENTE:", L.SEGMENTE)
print("RASTER[I_T], [I_V1], [I_ENDE]:", D.RASTER[L.I_T], D.RASTER[L.I_V1], D.RASTER[L.I_ENDE])
print("COINS:", D.COINS)
print("slip_bp:", np.asarray(D.laden("slip_bp")))
t = np.load('data/fabrik/tage_gen1.npy', mmap_mode='r')
print("tage_gen1:", t.shape, t.dtype)
g = D.laden("gueltig")
for j, c in enumerate(D.COINS):
    gg = np.asarray(g[j, L.I_T:L.I_ENDE])
    print(f"  {c:<5} ungültige Kerzen in [I_T, I_ENDE): {int((~gg).sum())}  erste gültige: {int(np.argmax(np.asarray(g[j, :L.I_ENDE])))}")
