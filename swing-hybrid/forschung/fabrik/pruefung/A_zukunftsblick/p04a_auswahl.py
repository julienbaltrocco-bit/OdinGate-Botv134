"""Zufallsauswahl (fester Startwert) von 3 Kandidaten status='stufe2', gen='gen1'; einer davon aus Derivate/Mikrostruktur."""
import json, sqlite3, sys
from pathlib import Path
import numpy as np
con = sqlite3.connect('file:data/fabrik/forschung.sqlite?mode=ro', uri=True)
con.row_factory = sqlite3.Row
z = con.execute("SELECT * FROM kandidaten WHERE status='stufe2' AND gen='gen1' ORDER BY id").fetchall()
print("stufe2/gen1:", len(z))
fam = {}
for r in z:
    fam[r["familie"]] = fam.get(r["familie"], 0) + 1
print("Familien:", fam)
sig = {}
for r in z:
    sig[r["signal"]] = sig.get(r["signal"], 0) + 1
print("Signale:", dict(sorted(sig.items(), key=lambda kv: -kv[1])))
rng = np.random.default_rng(20261115)
dm = [r for r in z if r["familie"] in ("Derivate", "Mikrostruktur")]
rest = [r for r in z if r["familie"] not in ("Derivate", "Mikrostruktur")]
wahl = [dm[int(rng.integers(len(dm)))]] + [z[int(i)] for i in rng.choice(len(z), 2, replace=False)]
aus = [{k: r[k] for k in r.keys()} for r in wahl]
for a in aus:
    print(json.dumps(a, ensure_ascii=False))
(Path(__file__).resolve().parent / "p04a_auswahl.json").write_text(json.dumps(aus, ensure_ascii=False, indent=1))
