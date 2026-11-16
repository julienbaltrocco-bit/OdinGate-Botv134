"""Schritt 5/6: alle Varianten über den ganzen Zeitraum rechnen und speichern (Auswahl passiert erst in walkforward.py)."""
import pickle
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from hybrid import data, runner

ZIEL = Path(__file__).resolve().parents[1] / "data/processed/laeufe"
ZIEL.mkdir(parents=True, exist_ok=True)


def name(p):
    return f"hybrid_dip{p['dip']}_tp{p['tp']}_{'trail' if p['trail'] else 'fest'}"


for strat in ("trail_beide", "momentum_vol_ls"):
    m = data.laden(strat)
    varianten = dict(runner.VARIANTEN)
    varianten.update({name(p): runner.hybrid(**p) for p in runner.RASTER})
    t0 = time.time()
    for hebel in (3.0, 1.0):
        erg = {}
        for n, p in varianten.items():
            l = runner.lauf(m, hebel, **p)
            erg[n] = {"params": p, "eq_gross": l.eq_gross[11::12].copy(), "eq5": l.eq_gross, "MV": l.MV, "TV": l.TV,
                      "FU": l.FU, "ORD": l.ORD, "FIL": l.FIL, "daily": l.daily, "trades": l.trades, "st": l.st}
        with open(ZIEL / f"{strat}_hebel{hebel:g}.pkl", "wb") as f:
            pickle.dump({"index": m.index, "days": m.days, "coins": m.coins, "laeufe": erg}, f)
    print(f"{strat}: {2 * len(varianten)} Läufe in {time.time() - t0:.0f} s")
