"""Überblick: Datenbank (nur lesend), Rasterkennzahlen, Rohdateien (nur Zeilen vor 2024-07-01)."""
import sqlite3, sys
sys.path.insert(0, 'forschung')
import numpy as np, pandas as pd
from fabrik import daten as D, lauf as L
print("N", D.N, "I_T", L.I_T, "I_TIEFE", L.I_TIEFE, "I_V1", L.I_V1, "I_ENDE", L.I_ENDE, "N_TAGE", L.N_TAGE, "COINS", D.COINS)
con = sqlite3.connect('file:data/fabrik/forschung.sqlite?mode=ro', uri=True)
for r in con.execute("SELECT gen, status, COUNT(*) FROM kandidaten GROUP BY gen, status"):
    print(r)
print(con.execute("SELECT * FROM laeufe").fetchall())
GRENZE = pd.Timestamp("2024-07-01")
for art in ("5m", "1m", "funding", "metrics", "premium_5m", "tiefe_5m"):
    d = pd.read_parquet(f"data/candles/{art}/SOLUSDT.parquet")
    d = d[d.index < GRENZE]
    print("\n==", art, d.shape, d.index.min(), d.index.max(), d.index.name, list(d.columns))
    print(d.loc["2023-03-01 07:50":"2023-03-01 08:10"].head(8).to_string())
