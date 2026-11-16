"""RSK 01: Kandidat bei Hebel 1 und 3 rechnen, Rechenkern gegen eigenen Nachbau prüfen, Reihen zwischenspeichern."""
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import numpy as np
import pandas as pd
from rsk_common import A, M, R, SCRATCH, kandidat, maerkte, nachbau, runner

t0 = time.time()
mv, mh = maerkte()
print(f"Märkte geladen nach {time.time() - t0:.0f} s; Vorperiode {mv.index[0]} .. {mv.index[-1]}, Haupt {mh.index[0]} .. {mh.index[-1]}")
slip = R.yubit_kosten(A)[0]
print("Yubit-Slippage je Coin (Anteil):", dict(zip(A, np.round(slip, 6))), "nicht gefunden:", R.yubit_kosten(A)[1])
print("Gebühren: Taker", runner.TAKER, "Rebate", runner.MIT.rebate, "-> effektiv", runner.TAKER * (1 - runner.MIT.rebate))

for name, m in (("vor", mv), ("haupt", mh)):
    l1, w = kandidat(m, 1.0)
    l3, _ = kandidat(m, 3.0)
    e1, e3 = l1.equity(runner.MIT), l3.equity(runner.MIT)
    print(f"\n[{name}] Lauf fertig nach {time.time() - t0:.0f} s. Sperrtage (Tageslimit ausgelöst): H1 {int(l1.st[4])}, H3 {int(l3.st[4])}; "
          f"Trades H1 {len(l1.trades)}; größte Abweichung eq(H3) - 3*eq(H1): {np.abs(e3 - 3 * e1).max():.3e}")
    # unabhängiger Nachbau
    pos, brutto, tv, fu = nachbau(m, w, 1.0 / len(A), slip)
    eq_nb = brutto.sum(axis=0) - runner.TAKER * (1 - runner.MIT.rebate) * tv.sum(axis=0) + fu.sum(axis=0)
    print(f"[{name}] Nachbau gegen Rechenkern: größte Abweichung Kontoverlauf {np.abs(eq_nb - e1).max():.3e}, "
          f"brutto {np.abs(brutto.sum(axis=0) - l1.eq_gross).max():.3e}, Volumen {np.abs(tv.sum(axis=0) - l1.TV).max():.3e}, "
          f"Funding {np.abs(fu.sum(axis=0) - l1.FU).max():.3e}; Maker-Volumen im Kern {l1.MV[-1]:.3e}")
    netto_coin = brutto - runner.TAKER * (1 - runner.MIT.rebate) * tv + fu          # je Coin, Hebel 1, Einheiten des Startkapitals
    np.savez_compressed(SCRATCH / f"lauf_{name}.npz", index=m.index.as_unit("ns").asi8, eq1=e1, eq3=e3, w=w.astype(np.int8), pos=pos,
                        netto_coin=netto_coin, fu_coin=fu, tv_coin=tv, brutto_coin=brutto,
                        o=m.o, h=m.h, l=m.l, c=m.c, fund=m.fund)
    l1.trades.to_pickle(SCRATCH / f"trades_{name}.pkl")
    tg = l1.daily_pnl(runner.MIT)
    tg.to_pickle(SCRATCH / f"tage_{name}.pkl")
    if name == "haupt":
        s = tg.sum(axis=1)
        for fen, (a, b) in {"D1": (None, R.D1_ENDE), "D2": (R.D1_ENDE, R.SPLIT), "Entwicklung": (None, R.SPLIT), "Pruefzeitraum": (R.SPLIT, None)}.items():
            x = s
            if a is not None:
                x = x[x.index >= pd.Timestamp(a)]
            if b is not None:
                x = x[x.index < pd.Timestamp(b)]
            k = 1.0 + x.cumsum()
            print(f"  {fen:14s} Tage {len(x):5d}  N {x.sum():+.4f}  pro Jahr {x.mean() * 365:+.4f}  Sharpe {x.mean() / x.std() * np.sqrt(365):.4f}  "
                  f"Einbruch (Tagesschluss, wie Runde 24) {((k.cummax() - k) / k.cummax()).max():.4f}")
    else:
        s = tg.sum(axis=1)
        print(f"  Vorperiode Tage {len(s)}  N {s.sum():+.4f}  pro Jahr {s.mean() * 365:+.4f}  Sharpe {s.mean() / s.std() * np.sqrt(365):.4f}")
        erste = {c: str(m.h1[c].index[0]) for c in A}
        print("  erste Stundenkerze je Coin:", erste)
print(f"fertig nach {time.time() - t0:.0f} s")
