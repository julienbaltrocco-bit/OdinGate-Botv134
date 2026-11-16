"""Wie groß ist die Kostenhürde je Trade im Verhältnis zur typischen Stundenbewegung? (Gruppe A, Stundenkerzen)"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
import pandas as pd
from hybrid import research as R

m = R.markt(R.GRUPPE_A)
c = pd.DataFrame({k: m.h1[k]["close"] for k in m.coins})
r = c.pct_change()[c.index >= R.START]
huerde = 0.0016 + 2 * R.yubit_kosten(R.GRUPPE_A)[0]
out = {"bewegung_median": float(r.abs().median().mean()), "standardabweichung": float(r.std().mean()), "huerde": float(huerde.mean()),
       "huerde_zu_bewegung": float((huerde / r.abs().median().values).mean()), "huerde_zu_std": float((huerde / r.std().values).mean())}
json.dump(out, open(Path(__file__).resolve().parents[1] / "reports/diagnose_huerde.json", "w"), indent=1)
print(out)
