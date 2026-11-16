"""ARC: Stille Standardwerte und Schnittstellen-Drift zwischen runner (Kern 1) und research/engine2 (Kern 2).
Nur Entwicklungszeitraum (bis 2025-04-01), keine Auswahl, keine Parameteraenderung. Schreibt nichts ins Repo.
Aufruf aus swing-hybrid: .venv/bin/python -I -B <skript>
"""
import inspect, sys
sys.path.insert(0, "src")
import numpy as np, pandas as pd
from hybrid import research as R, runner, mutationen as M, engine, engine2

print("=== E5: Standardwerte von research.lauf ===")
print("  Signatur:", inspect.signature(R.lauf))
print("  runner.SLIP =", runner.SLIP, "| runner.EPS =", runner.EPS, "| CFG['risiko'] =", runner.CFG["risiko"])
m = R.markt(R.GRUPPE_A, vor=True)
w = R.auf_raster(m, M.basis(m))
slip = R.yubit_kosten(m.coins)[0]
print("  Yubit-Slippage je Coin (yubit_kosten):", dict(zip(m.coins, np.round(slip * 1e4, 2))), "bp")
def zeile(name, l):
    s = R.sicht(l, None, R.SPLIT)
    st = runner.order_statistik(l)
    print(f"  {name:58s} N={s['N']:+.3f} jahr_N={s['jahr_N']:+.3f} Sharpe={s['sharpe']:.3f} dd={s['dd_mit']:.3f} Sperrtage={st['sperrtage']}")
    return s, st
print("  Entwicklungszeitraum", m.index[0], "bis", R.SPLIT, "(Gruppe A, sofortige Ausfuehrung, Yubit-Kosten, mit Rebate):")
a, _ = zeile("Hebel 1, day_limit=9.0 (so in Runde 21/24 gerechnet)", R.lauf(m, w, taker=True, slip=slip, day_limit=9.0))
b, _ = zeile("Hebel 1, Standardaufruf (day_limit aus config.yaml = 0.03)", R.lauf(m, w, taker=True, slip=slip))
c, _ = zeile("Hebel 3, day_limit=9.0 (entspricht config_lauf.json)", R.lauf(m, w, hebel=3.0, taker=True, slip=slip, day_limit=9.0))
d, _ = zeile("Hebel 3, Standardaufruf (day_limit 0.03)", R.lauf(m, w, hebel=3.0, taker=True, slip=slip))
e, _ = zeile("Hebel 1, Standard-Slippage runner.SLIP statt Yubit-Messung", R.lauf(m, w, taker=True, day_limit=9.0))

print()
print("=== E6: runner.order_statistik / runner.kennzahlen auf einem engine2-Lauf (Beschriftung aus Kern 1) ===")
T = 400
rng = np.random.default_rng(0)
c_ = 100 * np.exp(np.cumsum(rng.normal(0, 0.01, T)))[None, :]
o_ = np.concatenate([c_[:, :1], c_[:, :-1]], axis=1); h_ = np.maximum(o_, c_) * 1.002; l_ = np.minimum(o_, c_) * 0.998
idx = pd.date_range("2024-01-01", periods=T, freq="5min")
from types import SimpleNamespace
mk = SimpleNamespace(index=idx, coins=["X"], o=o_, h=h_, l=l_, c=c_, atr=np.ones((1, T)), fund=np.zeros((1, T)),
                     day=np.asarray((idx.normalize() - idx.normalize()[0]).days, dtype=np.int64), days=pd.DatetimeIndex(idx.normalize().unique()))
ww = np.ones((1, T))
l2 = R.lauf(mk, ww, stop_atr=1.0, taker=True, day_limit=9.0)
print("  engine2-Zaehler st (Kommentar engine2.py:40: 5 = Stops):", l2.st.tolist())
print("  runner.order_statistik:", runner.order_statistik(l2))
k = runner.kennzahlen(l2)
print("  runner.kennzahlen: trades =", k["trades"], "| trades_kern =", k["trades_kern"], "| trades_taktik =", k["trades_taktik"],
      "| Trade-Arten im Lauf:", l2.trades["art"].value_counts().to_dict())
print("  Tagesverlust-Limit: Kern 1 schliesst nur die Taktik (engine.py Kopf), Kern 2 schliesst alles (engine2.py:62-77);")
print("  beide lesen denselben Schluessel risiko.tagesverlust_limit.")
