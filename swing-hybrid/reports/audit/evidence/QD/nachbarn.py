"""QD-Audit: Parameter-Umgebung des Kandidaten, AUSSCHLIESSLICH im Entwicklungszeitraum (bis 31.03.2025). Kein Blick in den Pruefzeitraum,
keine Empfehlung fuer einen anderen Wert: geprueft wird nur, ob 336 Stunden auf einer Hochebene oder auf einer Spitze liegt."""
import sys, json
sys.path.insert(0, "/home/user/OdinGate-Botv134/swing-hybrid/src")
import numpy as np, pandas as pd
from hybrid import research as R, runner
A = R.GRUPPE_A; K = R.yubit_kosten(A)[0]; SPLIT = pd.Timestamp(R.SPLIT); D1 = pd.Timestamp(R.D1_ENDE)
m = R.markt(A, vor=True)
def sh(x): return float(x.mean() / x.std() * np.sqrt(365)) if x.std() > 0 else 0.0
out = {}
print("Rueckblick (h) | Sharpe D1 | Sharpe D2 | Sharpe Entwicklung | Ertrag/Jahr Entwicklung   (Gruppe A, Hebel 1, Yubit-Kosten mit Rebate, ohne Tageslimit)")
for L in (168, 192, 240, 288, 336, 384, 432, 504, 672, 1008, 1440):
    tg = R.lauf(m, R.auf_raster(m, R.tsmom(m, L)), taker=True, slip=K, day_limit=9.0).daily_pnl(runner.MIT).sum(axis=1)
    e = tg[tg.index < SPLIT]                       # nur Entwicklung
    a, b = e[e.index < D1], e[e.index >= D1]
    out[L] = {"D1": sh(a), "D2": sh(b), "Entwicklung": sh(e), "jahr": float(e.mean() * 365)}
    print(f"{L:5d}          | {sh(a):6.2f}    | {sh(b):6.2f}    | {sh(e):6.2f}             | {e.mean()*365:+.3f}")
json.dump(out, open("/home/user/OdinGate-Botv134/swing-hybrid/reports/audit/evidence/QD/nachbarn_entwicklung.json", "w"), indent=1)
