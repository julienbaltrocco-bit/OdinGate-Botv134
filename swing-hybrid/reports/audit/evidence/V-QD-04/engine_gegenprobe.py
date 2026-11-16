"""V-QD-04: Gegenprobe mit dem Rechenkern des Projekts (nur lesend): gespeicherte Hebel-3-Zeile aus diagnose_kapital.json
nachrechnen (Tageslimit 3 %) und denselben Lauf ohne Limit bzw. mit dem Limit 1,0 aus config_lauf.json."""
import json, sys
sys.path.insert(0, "/home/user/OdinGate-Botv134/swing-hybrid/src")
import numpy as np, pandas as pd
from hybrid import research as R, runner
A = R.GRUPPE_A; K = R.yubit_kosten(A)[0]
m = R.markt(A)
w = R.auf_raster(m, R.variante(m, "basis"))
tage_p = (m.index[-1] - pd.Timestamp(R.SPLIT)).days + 1; tage_e = (pd.Timestamp(R.SPLIT) - m.index[0]).days
dk = {z["hebel"]: z for z in json.load(open("/home/user/OdinGate-Botv134/swing-hybrid/reports/diagnose_kapital.json"))["hebel"]}
for h, lim, nm in ((3.0, None, "Tageslimit 3 % (wie diagnose_kapital.py)"), (3.0, 1.0, "Limit 1,0 (wie config_lauf.json)"), (3.0, 9.0, "Limit aus"),
                   (0.2, None, "Tageslimit 3 %, Hebel 0,2 (regelkonform)")):
    l = R.lauf(m, w, hebel=h, taker=True, slip=K, day_limit=lim)
    e, p = R.sicht(l, None, R.SPLIT), R.sicht(l, R.SPLIT, None)
    eq = l.equity(runner.MIT)
    print(f"Hebel {h:g}, {nm:42s}: Entwicklung {e['N'] / tage_e * 365:+.3f}/Jahr, Einbruch {e['dd_mit']:.3f} | Pruefzeitraum {p['N'] / tage_p * 365:+.3f}/Jahr, "
          f"Einbruch {p['dd_mit']:.3f} | Sperrtage {int(l.st[4])} | tiefster Kontostand (Start = 1) {1 + eq.min():+.3f}")
    if lim is None:
        print(f"      gespeichert: Entwicklung {dk[h]['entw_N_jahr']:+.3f}/Jahr, Einbruch {dk[h]['entw_einbruch']:.3f} | Pruefzeitraum {dk[h]['pruef_N_jahr']:+.3f}/Jahr, Einbruch {dk[h]['pruef_einbruch']:.3f} | Sperrtage {dk[h]['sperrtage']}")
