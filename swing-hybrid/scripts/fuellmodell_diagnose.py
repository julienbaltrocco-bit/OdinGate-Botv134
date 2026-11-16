"""Diagnose des Füllmodells (nur Entwicklungszeitraum): Wie stark hängt das Ergebnis an der Ausführungsannahme?"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
import numpy as np
import pandas as pd
from hybrid import engine, research as R, runner

ROOT = Path(__file__).resolve().parents[1]
m = R.markt(R.GRUPPE_A)
fin = json.loads((ROOT / "reports/suche_finalisten.json").read_text())
pd.set_option("display.width", 250)
out = {}
for f in fin:
    w = R.auf_raster(m, R.FAMILIEN[f["familie"]](m, **f["params"]))
    z = {}
    def eintrag(nm, l):
        s = R.sicht(l, None, R.SPLIT)
        z[nm] = {"G": s["G"], "N": s["N"], "bp_je_umsatz": s["bp_je_umsatz"], "vol_tag": s["vol_tag"], "maker": s["maker"], "of": s["of"]}
    eintrag("Limit, Basis", R.lauf(m, w))
    eintrag("Limit, 0,01 % schlechter", R.lauf(m, w, adverse=0.0001))
    eintrag("Limit, 0,05 % durchhandeln", R.lauf(m, w, eps=0.0005))
    eintrag("Limit, eine Kerze später (alter Preis)", R.lauf(m, w, delay=1))
    # Market zum Open ohne Slippage: was das Signal zu Eröffnungskursen wert ist
    S = 1.0 / len(m.coins)
    hour = np.asarray(m.index.minute == 0)
    for nm, slip in (("Market zum Open, ohne Slippage", 0.0), ("Market zum Open, 0,05 % Slippage", 0.0005)):
        eq, MV, TV, FU, daily, tr, st, nt, ORD, FIL = engine.simulate(
            m.o, m.h, m.l, m.c, w, m.atr, m.fund, m.day, hour, S, 1.0, True, 0, 0.0, 0.0, False, 3, 0.0001, slip,
            runner.MAKER, runner.TAKER, 9.0, 4_000_000)
        t = pd.DataFrame(tr, columns=["coin", "art", "richtung", "ein", "aus", "brutto", "maker_vol", "taker_vol"])
        t["stunden"] = (t["aus"] - t["ein"]) * 5 / 60
        eintrag(nm, runner.Lauf(m, 1.0, {}, eq, MV, TV, FU, daily, t, st, ORD, FIL))
    print("\n", f["name"], "(Entwicklung, Hebel 1)")
    print(pd.DataFrame(z).T.round(3).to_string())
    out[f["name"]] = z
(ROOT / "reports/fuellmodell_diagnose.json").write_text(json.dumps(out, indent=1))
