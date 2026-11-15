"""V-ENG-02 Teil 2: Wie gross wird der Positionswert bei fester Stueckzahl (Hebel 3), und was geschah am 2024-12-09?
Nur Entwicklungszeitraum, nur lesend, eigene Rechnung ohne engine2 (Stundenraster), keine Parameterwahl.
Aufruf: cd swing-hybrid && NUMBA_CACHE_DIR=$(mktemp -d) .venv/bin/python -I -B reports/audit/evidence/V-ENG-02/v2_einsatz.py
"""
import sys
sys.path.insert(0, "src")
import numpy as np, pandas as pd
from hybrid import research as R, runner, mutationen as M

voll = R.markt(R.GRUPPE_A, vor=True)
ende = int(voll.index.searchsorted(pd.Timestamp(R.SPLIT))); idx = voll.index[:ende]; N = len(voll.coins)
o, c, h, l = (np.ascontiguousarray(getattr(voll, k)[:, :ende]) for k in ("o", "c", "h", "l"))
w = np.ascontiguousarray(R.auf_raster(voll, M.basis(voll))[:, :ende])
S = 3.0 / N; H = ende // 12
pos = np.zeros(N); held = np.zeros(N)
einsatz = np.zeros(H); netto = np.zeros(H); P = np.zeros((N, H))
for k in range(H):
    t0 = 12 * k
    for j in range(N):
        tgt = w[j, t0]
        if tgt != held[j]:
            pos[j] = tgt * S / o[j, 1 if k == 0 else t0]; held[j] = tgt
    P[:, k] = pos
    einsatz[k] = np.abs(pos * c[:, t0 + 11]).sum(); netto[k] = (pos * c[:, t0 + 11]).sum()
st = idx[11::12]
print(f"Positionswert (Summe |Stueck x Kurs|) in Einheiten des Startkapitals, Hebel 3: Median {np.median(einsatz):.2f}, 95 % {np.quantile(einsatz, 0.95):.2f}, "
      f"99 % {np.quantile(einsatz, 0.99):.2f}, max {einsatz.max():.2f} am {st[int(einsatz.argmax())]}")
print(f"Anteil der Stunden mit Positionswert > 3,3: {np.mean(einsatz > 3.3) * 100:.1f} %, > 4: {np.mean(einsatz > 4) * 100:.1f} %, > 5: {np.mean(einsatz > 5) * 100:.1f} %")
print(f"Anteil der Stunden, in denen alle 10 Coins dieselbe Richtung haben: {np.mean(np.abs(np.sign(P).sum(axis=0)) == N) * 100:.1f} %; mindestens 8 von 10: "
      f"{np.mean(np.abs(np.sign(P).sum(axis=0)) >= 6) * 100:.1f} %")
a = int(idx.searchsorted(pd.Timestamp("2024-12-09 20:00"))); b = a + 12; k = a // 12
print(f"\n2024-12-09 20:00 bis 21:00 UTC: Positionswert davor {np.abs(P[:, k] * o[:, a]).sum():.2f} (netto {(P[:, k] * o[:, a]).sum():+.2f})")
z = []
for j, coin in enumerate(voll.coins):
    ein = S / abs(P[j, k]) if P[j, k] else float("nan")
    z.append({"coin": coin, "richtung": int(np.sign(P[j, k])), "einstiegskurs": ein, "kurs_20h": o[j, a], "wert_in_startkapital": abs(P[j, k]) * o[j, a],
              "kurs_21h": c[j, b - 1], "tief_der_stunde": l[j, a:b].min(), "rendite_std_pct": (c[j, b - 1] / o[j, a] - 1) * 100,
              "bis_tief_pct": (l[j, a:b].min() / o[j, a] - 1) * 100, "pnl_startkapital": P[j, k] * (c[j, b - 1] - o[j, a])})
t = pd.DataFrame(z); print(t.round(4).to_string(index=False))
print(f"Summe Ergebnis der Stunde (Schlusskurse): {t['pnl_startkapital'].sum():+.3f} Startkapital; zum Tief jeder Kerze (Obergrenze, Tiefs nicht zeitgleich): "
      f"{float((P[:, k] * (l[:, a:b].min(axis=1) - o[:, a])).sum()):+.3f}")
