"""Diagnose (keine Kandidatensuche): Was passiert mit dem Trend-Signal, wenn man es schneller macht?

Gruppe A, Hebel 1, ohne Tageslimit, sofortige Ausführung. Je Rückblick: Umsatz, Signalwert je umgesetztem Dollar
(ohne jede Kosten), Kosten je Dollar (gemessene Yubit-Slippage x 2 + Gebühr nach Rebate) und das Netto mit Rebate.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
import numpy as np
import pandas as pd
from hybrid import research as R

ROOT = Path(__file__).resolve().parents[1]
pd.set_option("display.width", 250)
m = R.markt(R.GRUPPE_A)
K = R.yubit_kosten(R.GRUPPE_A)[0]
z = []
for L in (6, 12, 24, 48, 96, 168, 336):
    w = R.auf_raster(m, R.tsmom(m, L))
    frei = R.lauf(m, w, taker=True, slip=0.0, day_limit=9.0)
    echt = R.lauf(m, w, taker=True, slip=K, day_limit=9.0)
    row = {"rueckblick_h": L}
    for name, (a, b) in (("entw", (None, R.SPLIT)), ("pruef", (R.SPLIT, None))):
        f, e = R.sicht(frei, a, b), R.sicht(echt, a, b)
        tage = (pd.Timestamp(R.SPLIT) - m.index[0]).days if name == "entw" else (m.index[-1] - pd.Timestamp(R.SPLIT)).days + 1
        V = e["vol_tag"] * tage
        row.update({f"{name}_umsatz_tag": e["vol_tag"], f"{name}_halte_h": e["halte_h"],
                    f"{name}_signal_bp": f["G"] / V * 1e4, f"{name}_slippage_bp": (f["G"] - e["G"]) / V * 1e4,
                    f"{name}_gebuehr_netto_bp": (e["F"] - e["R"]) / V * 1e4, f"{name}_netto_bp": e["N"] / V * 1e4,
                    f"{name}_N_jahr": e["N"] / tage * 365, f"{name}_rebate_jahr": e["R"] / tage * 365})
    z.append(row)
t = pd.DataFrame(z)
t.to_csv(ROOT / "reports/diagnose_frequenz.csv", index=False)
print(t.round(2).to_string())
