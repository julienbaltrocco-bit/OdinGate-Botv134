"""ENG-F: (1) Gleichstand (Signal 0) je Coin und Jahr in den Binance-Daten. (2) Kandidat bei Hebel 3 mit fester Positionsgroesse:
tiefster Kontostand je Startzeitpunkt (kein Margin-/Liquidationsmodell in engine2 und im Bot). Nur lesend, keine Parameterwahl."""
import sys
sys.path.insert(0, "src")
import numpy as np, pandas as pd
from hybrid import research as R, runner, mutationen as M
m = R.markt(R.GRUPPE_A, vor=True)
b = M.basis(m).loc[R.START:]
c = R._close(m).loc[R.START:]
gl = (b == 0) & c.notna() & c.shift(336).notna()
print("(1) Stunden mit exaktem Gleichstand (Schluss == Schluss vor 336 h), je Jahr:")
print(gl.groupby(gl.index.year).sum().to_string())
ereignis = (gl & ~gl.shift(1, fill_value=False)).sum()
print("    Ereignisse (zusammenhaengende Gleichstands-Phasen) gesamt:", ereignis.to_dict())
print("    mittlerer Kurs 2026:", c.loc["2026"].mean().round(4).to_dict())

slip = R.yubit_kosten(m.coins)[0]
w = R.auf_raster(m, M.basis(m))
l1 = R.lauf(m, w, taker=True, slip=slip, day_limit=9.0)
l3 = R.lauf(m, w, hebel=3.0, taker=True, slip=slip, day_limit=9.0)
e1, e3 = l1.equity(runner.MIT), l3.equity(runner.MIT)
print(f"\n(2) Linearitaet: equity(Hebel 3) / equity(Hebel 1) am Ende = {e3[-1] / e1[-1]:.6f}; groesste Abweichung |e3 - 3*e1| = {np.abs(e3 - 3 * e1).max():.2e}")
ohne = l3.equity(runner.OHNE)
idx = m.index
for name, e in (("mit Rebate", e3), ("ohne Rebate", ohne)):
    # je Starttag s: tiefster Stand eines frisch gestarteten Kontos (Kapital 1, feste Groesse 3 x Startkapital) in den folgenden 365 Tagen
    tag = e[287::288]                                             # Tagesschluss
    n = len(tag); H = 365
    start = np.r_[0.0, tag[:-1]]
    tief = np.array([tag[i:i + H].min() - start[i] for i in range(n - H)])
    intratief = np.array([e[i * 288:(i + H) * 288].min() - start[i] for i in range(0, n - H, 7)])
    print(f"    {name}: Starttage {n - H}; Anteil mit Kontostand <= 0 binnen 365 Tagen (Tagesschluss): {np.mean(1 + tief <= 0) * 100:.1f} %; "
          f"<= 50 % des Startkapitals: {np.mean(1 + tief <= 0.5) * 100:.1f} %; schlechtester Fall {1 + tief.min():+.2f}; "
          f"auf 5-Minuten-Basis (jeder 7. Starttag) <= 0: {np.mean(1 + intratief <= 0) * 100:.1f} %")
split = int(idx.searchsorted(pd.Timestamp(R.SPLIT)))
for name, a, bb in (("Entwicklung", 0, split), ("Pruefzeitraum (frisches Konto ab 2025-04-01)", split, len(idx))):
    seg = e3[a:bb] - (e3[a - 1] if a else 0.0)
    print(f"    {name}: Kontostand Hebel 3 min {1 + seg.min():+.3f} am {idx[a + int(seg.argmin())]}, Ende {1 + seg[-1]:+.3f}, "
          f"groesster Rueckgang in Einheiten des Startkapitals {float((np.maximum.accumulate(np.maximum(seg, 0)) - seg).max()):.3f}, "
          f"runner.max_drawdown (relativ zur Spitze) {runner.max_drawdown(seg):.3f}")
# Tagesverlust-Limit 3 % der Forschung (config.yaml) bei Hebel 3 -- nur Entwicklungszeitraum
l3lim = R.lauf(m, w, hebel=3.0, taker=True, slip=slip)            # day_limit=None -> config.yaml 0.03
t = pd.Series(l3lim.daily_pnl(runner.MIT).sum(axis=1)); t0 = l3.daily_pnl(runner.MIT).sum(axis=1)
d = t[t.index < pd.Timestamp(R.SPLIT)]; d0 = t0[t0.index < pd.Timestamp(R.SPLIT)]
sperr = int(R.sicht(l3lim, None, R.SPLIT)["trades"])
print(f"\n(3) Entwicklung, Hebel 3: ohne Tageslimit Ertrag/Jahr {d0.mean() * 365:.3f}, mit Tageslimit 3 % (config.yaml) {d.mean() * 365:.3f}; Sperrtage gesamter Lauf {int(l3lim.st[4])} von {len(m.days)} Tagen")
