"""E11 Kombination: „Orderbuch-Stütze“ 1.0 neben dem bisherigen 14-Tage-Trend (01/2023 bis 03/2025, beschreibend)."""
import sys, time
from pathlib import Path
import numpy as np, pandas as pd
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from alpha import kern as K, konto
from hybrid import research as R, runner

start = time.time()
VON, BIS = pd.Timestamp("2023-01-02"), pd.Timestamp("2025-04-01")
t = pd.read_csv(K.ERG / "e08_vollpruefung_trades.csv", parse_dates=["ein", "aus"])
erg = {}
m = R.markt(R.GRUPPE_A, ende="2025-03-31 23:55")
l = R.lauf(m, R.auf_raster(m, R._trend(m)), taker=True, slip=R.yubit_kosten(m.coins)[0], day_limit=9.0)
for sicht, sp, konto_art in (("mit 85 % Rebate", "n85", runner.MIT), ("ohne Rebate", "n0", runner.OHNE)):
    ob = konto.tagesreihe(t, sp, VON, BIS, 3)
    tr = l.daily_pnl(konto_art).sum(axis=1); tr = tr[(tr.index >= VON) & (tr.index < BIS)].reindex(ob.index, fill_value=0.0)
    f = tr.std() / ob.std()                                   # Orderbuch-Regel auf die Schwankung des Trends hochgerechnet
    mix = 0.5 * tr + 0.5 * f * ob
    erg[sicht] = {"orderbuch": konto.kennzahlen(ob), "trend": konto.kennzahlen(tr), "mischung_gleiches_risiko": konto.kennzahlen(mix),
                  "korrelation_tage": round(float(np.corrcoef(ob, tr)[0, 1]), 3), "hebel_orderbuch_fuer_gleiches_risiko": round(float(f), 2),
                  "gemeinsame_verlusttage": round(float(((ob < 0) & (tr < 0)).mean()), 3)}
    print(sicht)
    for k2, v in erg[sicht].items(): print("   ", k2, v)
K.speichern("e11_kombination", {"zeitraum": "01/2023 bis 03/2025 (Entwicklung und Validierung der Orderbuch-Regel)", "ergebnis": erg}, start)
