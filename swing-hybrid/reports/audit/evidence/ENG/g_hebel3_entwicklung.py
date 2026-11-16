"""ENG-G: Kandidat bei Hebel 3, feste Positionsgroesse, NUR Entwicklungszeitraum (bis 2025-04-01): frisches Konto je Starttag,
groesste Gegenbewegung je Trade (isolierte Margin), Tagesverlust-Limit 3 % der Forschung. Nur lesend, keine Parameterwahl."""
import sys
from types import SimpleNamespace
sys.path.insert(0, "src")
import numpy as np, pandas as pd
from hybrid import research as R, runner, mutationen as M
voll = R.markt(R.GRUPPE_A, vor=True)
ende = int(voll.index.searchsorted(pd.Timestamp(R.SPLIT)))
w_voll = R.auf_raster(voll, M.basis(voll))
m = SimpleNamespace(index=voll.index[:ende], coins=voll.coins, day=voll.day[:ende], days=voll.days[:voll.day[ende - 1] + 1], h1=voll.h1,
                    **{k: np.ascontiguousarray(getattr(voll, k)[:, :ende]) for k in ("o", "h", "l", "c", "atr", "fund")})
w = np.ascontiguousarray(w_voll[:, :ende])
slip = R.yubit_kosten(m.coins)[0]
l3 = R.lauf(m, w, hebel=3.0, taker=True, slip=slip, day_limit=9.0)
print("Entwicklungszeitraum", m.index[0], "bis", m.index[-1], "| Hebel 3, feste Groesse = 3 x Startkapital / 10 je Coin, ohne Tageslimit")
for name, fees in (("mit Rebate", runner.MIT), ("ohne Rebate", runner.OHNE)):
    e = l3.equity(fees)
    tag = e[287::288]; n = len(tag); start = np.r_[0.0, tag[:-1]]
    for Hz in (90, 365):
        tief = np.array([e[i * 288:(i + Hz) * 288].min() - start[i] for i in range(n - Hz)])
        print(f"  {name}, Horizont {Hz} Tage, {n - Hz} Starttage: Konto <= 0: {np.mean(1 + tief <= 0) * 100:5.1f} % | <= 50 %: {np.mean(1 + tief <= 0.5) * 100:5.1f} % | "
              f"schlechtester Tiefststand {1 + tief.min():+.2f} (Start {m.days[int(tief.argmin())].date()})")
    print(f"  {name}: Ertrag/Jahr {e[-1] / (ende / 288) * 365:.3f}; groesster Rueckgang in Einheiten des Startkapitals {float((np.maximum.accumulate(np.maximum(e, 0)) - e).max()):.3f}; "
          f"runner.max_drawdown (relativ zur Spitze) {runner.max_drawdown(e):.3f}")
# groesste Gegenbewegung je Trade (5m-Hoch/Tief gegen den Einstiegskurs)
t = l3.trades; idx = {c: j for j, c in enumerate(m.coins)}
mae = np.empty(len(t))
for i, (coin, a, b, d) in enumerate(zip(t["coin"], t["ein"].astype(int), t["aus"].astype(int), t["richtung"])):
    j = idx[coin]; p = m.o[j, a]
    mae[i] = (1 - m.l[j, a:b + 1].min() / p) if d > 0 else (m.h[j, a:b + 1].max() / p - 1)
print(f"  Trades {len(t)}; groesste Gegenbewegung je Trade: Median {np.median(mae) * 100:.2f} %, 99 % {np.quantile(mae, 0.99) * 100:.1f} %, max {mae.max() * 100:.1f} %; "
      f">= 20 %: {(mae >= 0.20).sum()}, >= 30 %: {(mae >= 0.30).sum()}, >= 33 %: {(mae >= 1 / 3).sum()}")
sch = t.assign(mae=mae).sort_values("mae", ascending=False).head(5)[["coin", "richtung", "ein_zeit", "aus_zeit", "stunden", "mae"]]
print(sch.to_string(index=False))
# Tagesverlust-Limit der Forschung / README (3 % vom Kapital) bei Hebel 3 und Hebel 1
for h in (1.0, 3.0):
    a = R.lauf(m, w, hebel=h, taker=True, slip=slip, day_limit=9.0); b = R.lauf(m, w, hebel=h, taker=True, slip=slip, day_limit=0.03)
    print(f"  Hebel {h:.0f}: ohne Tageslimit Ertrag/Jahr {a.equity(runner.MIT)[-1] / (ende / 288) * 365:+.3f} | mit Tageslimit 3 %: {b.equity(runner.MIT)[-1] / (ende / 288) * 365:+.3f}, "
          f"Sperrtage {int(b.st[4])} von {len(m.days)}, Market-Orders {int(b.st[7])} gegen {int(a.st[7])}")
