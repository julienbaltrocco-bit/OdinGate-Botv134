"""V-ENG-02 Teil 3: 5-Minuten-Verlauf am 2024-12-09 (Entwicklungszeitraum), Hebel 3 feste Groesse. Nur lesend.
Aufruf: cd swing-hybrid && NUMBA_CACHE_DIR=$(mktemp -d) .venv/bin/python -I -B reports/audit/evidence/V-ENG-02/v3_stunde.py
"""
import sys
sys.path.insert(0, "src")
import numpy as np, pandas as pd
from hybrid import research as R, runner, mutationen as M
voll = R.markt(R.GRUPPE_A, vor=True)
ende = int(voll.index.searchsorted(pd.Timestamp(R.SPLIT)))
from types import SimpleNamespace
m = SimpleNamespace(index=voll.index[:ende], coins=voll.coins, day=voll.day[:ende], days=voll.days[:voll.day[ende - 1] + 1], h1=voll.h1,
                    **{k: np.ascontiguousarray(getattr(voll, k)[:, :ende]) for k in ("o", "h", "l", "c", "atr", "fund")})
w = np.ascontiguousarray(R.auf_raster(voll, M.basis(voll))[:, :ende])
l3 = R.lauf(m, w, hebel=3.0, taker=True, slip=R.yubit_kosten(m.coins)[0], day_limit=9.0)
e = l3.equity(runner.MIT)
a = int(m.index.searchsorted(pd.Timestamp("2024-12-09 19:55"))); b = int(m.index.searchsorted(pd.Timestamp("2024-12-09 23:05")))
print("Kontostand (1 + Ergebnis, durchgehender Lauf seit 2021) zum Schluss jeder 5-Minuten-Kerze; Kursaenderung je Coin gegen 20:00 in %")
basis = m.o[:, a + 1]
for t in list(range(a, a + 20)) + list(range(a + 20, b, 6)):
    print(f"  {m.index[t].strftime('%H:%M')}  Konto {1 + e[t]:.3f}  Aenderung zur Vorkerze {e[t] - e[t - 1]:+.3f}  " +
          " ".join(f"{c}:{(m.c[j, t] / basis[j] - 1) * 100:+.1f}" for j, c in enumerate(m.coins)) + "  w=" + "".join("+" if x > 0 else "-" if x < 0 else "0" for x in w[:, t]))
d = np.diff(e); k = np.argsort(d)[:8]
print("\nGroesste Verluste in EINER 5-Minuten-Kerze (Startkapital):", ", ".join(f"{m.index[i + 1]} {d[i]:+.3f}" for i in k))
print("Tiefs der Kerze 2024-12-09 21:00 gegen ihren Eroeffnungskurs in %:", {c: round((m.l[j, a + 13] / m.o[j, a + 13] - 1) * 100, 1) for j, c in enumerate(m.coins)})
print("Schluss derselben Kerze gegen Eroeffnung in %:", {c: round((m.c[j, a + 13] / m.o[j, a + 13] - 1) * 100, 1) for j, c in enumerate(m.coins)})
