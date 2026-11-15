"""ENG-J: Laeufe, in denen nicht fuer alle 10 Coins Marktdaten vorlagen (Kopie der Lauf-Daten, nur lesend).
Aufruf: .venv/bin/python -I -B j_teilausfall.py <verzeichnis mit Kopien von lauf/ und lauf_tpsl/>"""
import collections, csv, sys
from pathlib import Path
for n in ("lauf", "lauf_tpsl"):
    d = Path(sys.argv[1]) / n
    sp = list(csv.DictReader(open(d / "spannen.csv", newline=""))); st = list(csv.DictReader(open(d / "stand.csv", newline="")))
    c = collections.Counter(r["zeit"] for r in sp)
    print(f"{n}: {len(st)} Laeufe; Laeufe mit weniger als 10 Coins in spannen.csv: { {z: k for z, k in c.items() if k != 10} }")
    for z, k in c.items():
        if k != 10:
            print("   vorhanden:", [r["coin"] for r in sp if r["zeit"] == z], "| Zeile in stand.csv:", next(r for r in st if r["zeit"] == z))
