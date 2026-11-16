"""Runde 7: vier Hypothesen aus Positionierungsdaten, jede mit genau einer Einstellung. Hürden laut Protokoll."""
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
import numpy as np
import pandas as pd
from hybrid import positionierung as P, research as R, runner

ROOT = Path(__file__).resolve().parents[1]
pd.set_option("display.width", 260, "display.max_columns", 60)
AUS = 9.0
FEN = {"D1": (None, R.D1_ENDE), "D2": (R.D1_ENDE, R.SPLIT), "Entwicklung": (None, R.SPLIT), "Pruefung": (R.SPLIT, None),
       "Gesamt": (None, None)}
SP = ["G", "F", "R", "handel", "N", "dd_mit", "vol_tag", "bp_je_umsatz", "trades", "halte_h", "sharpe", "jahr_N"]
HEBEL = (5, 4, 3, 2.5, 2, 1.5, 1, 0.75, 0.5, 0.4, 0.35, 0.3, 0.25, 0.2, 0.15, 0.1)
r6 = json.loads((ROOT / "reports/suche_runde6.json").read_text())
G = r6["gruppen"]


def tab(d, sp=SP):
    return pd.DataFrame(d).T[sp].round(3).to_string()


def fen(l, namen=("Entwicklung", "Pruefung", "Gesamt")):
    return {k: R.sicht(l, *FEN[k]) for k in namen}


def hebel_lauf(m, w, slip):
    for h in HEBEL:
        l = R.lauf(m, w, hebel=h, taker=True, slip=slip)
        if R.sicht(l, *FEN["Entwicklung"])["dd_mit"] <= 0.10:
            return h, l
    return None, None


def jahre(l):
    j = {}
    for nm, fees in (("G", runner.BRUTTO), ("ohne", runner.OHNE), ("N", runner.MIT)):
        tg = l.daily_pnl(fees).sum(axis=1)
        j[nm] = tg.groupby(tg.index.year).sum()
    j = pd.DataFrame(j)
    j["R"] = j["N"] - j["ohne"]
    return j


t0 = time.time()
M = {g: R.markt(G[g]) for g in ("A", "B", "C", "D")}
K = {g: R.yubit_kosten(G[g])[0] for g in G}
AB = G["A"] + G["B"]
mAB = R.markt(AB)
kAB = np.concatenate([K["A"], K["B"]])
w_trend_AB = R.auf_raster(mAB, R.variante(mAB, "basis"))
h_t, l_t = hebel_lauf(mAB, w_trend_AB, kAB)
kandidat = fen(l_t)
print(f"Vergleichsmaßstab: Kandidat auf A+B, Hebel {h_t}: Entwicklung N {kandidat['Entwicklung']['N']:.4f}, Prüfung N {kandidat['Pruefung']['N']:.4f}")
out = {"kandidat_AB": {"hebel": h_t, **kandidat}, "signale": {}}

for name, fn in P.SIGNALE.items():
    print(f"\n################ {name}")
    e = out["signale"][name] = {"stufen": {}, "staerker": False}
    wA = R.auf_raster(M["A"], fn(M["A"]))
    d = fen(R.lauf(M["A"], wA, taker=True, slip=K["A"], day_limit=AUS), ("D1", "D2", "Entwicklung"))
    ok1 = all(d[f]["G"] > 0 and d[f]["N"] > 0 for f in ("D1", "D2"))
    e["stufen"]["1_entwicklung"] = {"ok": ok1, **d}
    print(f"Stufe 1 Entwicklung Gruppe A (Hebel 1, ohne Tageslimit): {'bestanden' if ok1 else 'DURCHGEFALLEN'}"); print(tab(d))
    if not ok1:
        continue
    s2 = fen(R.lauf(M["A"], wA, taker=True, slip=2 * K["A"], day_limit=AUS), ("D1", "D2"))
    ok2 = all(x["N"] > 0 for x in s2.values())
    e["stufen"]["2_stress"] = {"ok": ok2, **s2}
    print(f"Stufe 2 doppelte Kosten: {'bestanden' if ok2 else 'DURCHGEFALLEN'}"); print(tab(s2))
    if not ok2:
        continue
    s3 = {}
    for g in ("A", "B", "C", "D"):
        w = wA if g == "A" else R.auf_raster(M[g], fn(M[g]))
        s3[g] = fen(R.lauf(M[g], w, taker=True, slip=K[g], day_limit=AUS))
        print(f"-- Gruppe {g} ({len(G[g])} Coins):"); print(tab(s3[g]))
    ok3 = (s3["A"]["Pruefung"]["G"] > 0 and s3["A"]["Pruefung"]["N"] > 0
           and all(s3[g][f]["N"] > 0 for g in ("B", "C") for f in ("Entwicklung", "Pruefung")))
    e["stufen"]["3_bestaetigung"] = {"ok": ok3, **s3}
    print(f"Stufe 3 Bestätigung: {'bestanden' if ok3 else 'DURCHGEFALLEN'}")
    if not ok3:
        continue
    rng = np.random.default_rng(7)
    echt = s3["A"]["Gesamt"]["N"]
    Tn = wA.shape[1]
    z = [R.sicht(R.lauf(M["A"], np.ascontiguousarray(np.roll(wA, int(rng.integers(288 * 30, Tn - 288 * 30)), axis=1)),
                        taker=True, slip=K["A"], day_limit=AUS), None, None)["N"] for _ in range(200)]
    pct = float((np.array(z) < echt).mean() * 100)
    ok4 = pct >= 90
    e["stufen"]["4_zufall"] = {"ok": ok4, "perzentil": pct, "echt": echt, "median": float(np.median(z)), "p90": float(np.percentile(z, 90))}
    print(f"Stufe 4 Zufallstest: Perzentil {pct:.1f} ({'bestanden' if ok4 else 'DURCHGEFALLEN'}); echt {echt:.3f}, Median {np.median(z):.3f}")
    if not ok4:
        continue
    h, lh = hebel_lauf(M["A"], wA, K["A"])
    if h is None:
        e["stufen"]["5_hebel"] = {"ok": False}
        print("Stufe 5: DURCHGEFALLEN (kein Hebel hält 10 %)")
        continue
    h5 = fen(lh)
    p = h5["Pruefung"]
    ok5 = p["dd_mit"] < 0.15 and p["G"] > 0 and p["N"] > 0
    e["stufen"]["5_hebel"] = {"ok": ok5, "hebel": h, **h5, "orders": runner.order_statistik(lh)}
    print(f"Stufe 5 Hebel {h}: {'bestanden' if ok5 else 'DURCHGEFALLEN'}"); print(tab(h5))
    if not ok5:
        continue
    w_s = R.auf_raster(mAB, fn(mAB))
    w_mix = w_s if name not in P.NEUTRAL else 0.5 * w_trend_AB + 0.5 * w_s
    hm, lm = hebel_lauf(mAB, w_mix, kAB)
    if hm is None:
        e["stufen"]["6_vergleich"] = {"ok": False}
        continue
    v = fen(lm)
    ok6 = all(v[f]["N"] > kandidat[f]["N"] for f in ("Entwicklung", "Pruefung"))
    e["stufen"]["6_vergleich"] = {"ok": ok6, "hebel": hm, **v, "stress_2x": fen(R.lauf(mAB, w_mix, hebel=hm, taker=True, slip=2 * kAB)),
                                  "jahre": {str(i): x for i, x in jahre(lm).round(5).T.to_dict().items()},
                                  "orders": runner.order_statistik(lm)}
    print(f"Stufe 6 Vergleich mit dem Kandidaten auf A+B, Hebel {hm}: {'STÄRKER' if ok6 else 'nicht stärker'}"); print(tab(v))
    print(jahre(lm).round(3).to_string())
    e["staerker"] = bool(ok6)

out["staerkerer_edge"] = any(e["staerker"] for e in out["signale"].values())
out["tage"] = {"Pruefung": (mAB.index[-1] - pd.Timestamp(R.SPLIT)).days + 1, "Gesamt": (mAB.index[-1] - mAB.index[0]).days + 1}
print("\nSTÄRKERER EDGE:", out["staerkerer_edge"], {n: e["staerker"] for n, e in out["signale"].items()})
(ROOT / "reports/suche_runde7.json").write_text(json.dumps(out, indent=1, default=float))
print(f"fertig in {time.time() - t0:.0f} s")
