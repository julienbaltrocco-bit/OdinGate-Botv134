"""QD-Audit: Kandidat unabhaengig nachrechnen (nur lesend; schreibt nichts nach reports/)."""
import sys, time, json
sys.path.insert(0, "/home/user/OdinGate-Botv134/swing-hybrid/src")
import numpy as np, pandas as pd
from hybrid import research as R, runner, mutationen as M

t0 = time.time()
G = json.loads(open("/home/user/OdinGate-Botv134/swing-hybrid/reports/suche_runde6.json").read())["gruppen"]
A = G["A"]
assert A == R.GRUPPE_A
K = R.yubit_kosten(A)[0]
print("Yubit-Slippage je Coin (bp):", dict(zip(A, np.round(K * 1e4, 3))), "Mittel", round(K.mean() * 1e4, 3))
FEN = {"D1": (None, R.D1_ENDE), "D2": (R.D1_ENDE, R.SPLIT), "Entwicklung": (None, R.SPLIT), "Pruefung": (R.SPLIT, None), "Gesamt": (None, None)}

def sharpe(x):
    return float(x.mean() / x.std() * np.sqrt(365)) if x.std() > 0 else 0.0

def teil(x, von=None, bis=None):
    if von is not None: x = x[x.index >= pd.Timestamp(von)]
    if bis is not None: x = x[x.index < pd.Timestamp(bis)]
    return x

def dd_tag(x):
    k = 1.0 + x.cumsum(); return float(((k.cummax() - k) / k.cummax()).max())

def zeile(name, l):
    out = {}
    for f, (a, b) in FEN.items():
        s = R.sicht(l, a, b)
        tg = teil(l.daily_pnl(runner.MIT).sum(axis=1), a, b)
        to = teil(l.daily_pnl(runner.OHNE).sum(axis=1), a, b)
        out[f] = {"N": s["N"], "jahr_N": s["jahr_N"], "sharpe": s["sharpe"], "dd_5min": s["dd_mit"], "dd_tag": dd_tag(tg), "G": s["G"],
                  "F": s["F"], "R": s["R"], "ohne_rebate_N": s["handel"], "sharpe_ohne_rebate": sharpe(to), "vol_tag": s["vol_tag"],
                  "trades": s["trades"], "halte_h": s["halte_h"], "tage": len(tg)}
    print(f"\n## {name}")
    print(pd.DataFrame(out).T.round(4).to_string())
    return out

res = {}
for vor in (True, False):
    m = R.markt(A, vor=vor)
    print(f"\nMarkt geladen (vor={vor}) nach {time.time() - t0:.0f} s; Kerzen {len(m.index)}; {m.index[0]} .. {m.index[-1]}")
    w = R.auf_raster(m, M.basis(m))
    w2 = R.auf_raster(m, R.variante(m, "basis"))
    w3 = R.auf_raster(m, R.tsmom(m, 336))
    print("  Gewichte identisch (mutationen.basis / research.variante / research.tsmom):", np.array_equal(w, w2), np.array_equal(w, w3))
    l = R.lauf(m, w, taker=True, slip=K, day_limit=9.0)
    res[f"yubit_hebel1_ohneLimit_vor{vor}"] = zeile(f"Kandidat, Gruppe A, Hebel 1, ohne Tageslimit, Yubit-Kosten, vor={vor}", l)
    if not vor:
        l5 = R.lauf(m, w, taker=True, day_limit=9.0)
        res["5bp_hebel1_ohneLimit"] = zeile("Kandidat, Hebel 1, ohne Tageslimit, 5 bp Slippage (Runde 3)", l5)
        l02 = R.lauf(m, w, hebel=0.2, taker=True, slip=K)
        res["yubit_hebel0.2_mitLimit"] = zeile("Kandidat, Hebel 0,2 mit Tageslimit 3 %, Yubit-Kosten (Runde 6 Teil 1)", l02)
        l02b = R.lauf(m, w, hebel=0.2, taker=True)
        res["5bp_hebel0.2_mitLimit"] = zeile("Kandidat, Hebel 0,2 mit Tageslimit 3 %, 5 bp (Runde 3 Stufe 5)", l02b)
        l2x = R.lauf(m, w, taker=True, slip=2 * K, day_limit=9.0)
        res["yubit2x_hebel1"] = zeile("Kandidat, Hebel 1, doppelte Yubit-Slippage", l2x)
    else:
        mkeep, wkeep, lkeep = m, w, l
json.dump(res, open("/home/user/OdinGate-Botv134/swing-hybrid/reports/audit/evidence/QD/repro_kandidat.json", "w"), indent=1, default=float)
print(f"\nfertig nach {time.time() - t0:.0f} s")
