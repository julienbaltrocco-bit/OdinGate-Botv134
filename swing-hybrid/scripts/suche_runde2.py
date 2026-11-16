"""Runde 2: Trend-Familie mit marktfähigem Limit (sofortiger Fill, Taker). Stufen 1–5 laut Protokoll."""
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
import numpy as np
import pandas as pd
from hybrid import research as R, runner

ROOT = Path(__file__).resolve().parents[1]
pd.set_option("display.width", 260, "display.max_columns", 60, "display.max_rows", 100)
KONFIG = ([("tsmom", dict(L=L, bias=b)) for L in (48, 96, 168, 336) for b in (False, True)]
          + [("ensemble", dict(bias=b)) for b in (False, True)])
FENSTER = {"D1": (None, R.D1_ENDE), "D2": (R.D1_ENDE, R.SPLIT), "Entwicklung": (None, R.SPLIT), "Pruefung": (R.SPLIT, None),
           "Gesamt": (None, None)}
SP = ["G", "F", "R", "handel", "N", "rebate_anteil", "dd_mit", "vol_tag", "bp_je_umsatz", "of", "trades", "halte_h",
      "sharpe", "jahr_N", "anteil_coin", "anteil_monat"]


def name(fam, p):
    return fam + "_" + "_".join(f"{k}{v}" for k, v in p.items())


def tab(d):
    return pd.DataFrame(d).T[SP].round(3).to_string()


t0 = time.time()
mA = R.markt(R.GRUPPE_A)
# ---------------- Stufe 1
zeilen, W = [], {}
for fam, p in KONFIG:
    w = W[name(fam, p)] = R.auf_raster(mA, R.FAMILIEN[fam](mA, **p))
    l = R.lauf(mA, w, taker=True)
    d1, d2 = R.sicht(l, *FENSTER["D1"]), R.sicht(l, *FENSTER["D2"])
    zeilen.append({"name": name(fam, p), "familie": fam, "params": json.dumps(p),
                   "bestanden": all(x["G"] > 0 and x["N"] > 0 for x in (d1, d2)), "score": min(d1["sharpe"], d2["sharpe"]),
                   **{f"D1_{k}": v for k, v in d1.items()}, **{f"D2_{k}": v for k, v in d2.items()}})
t = pd.DataFrame(zeilen)
t.to_csv(ROOT / "reports/suche_runde2_stufe1.csv", index=False)
print("STUFE 1 (Entwicklung, Gruppe A, Hebel 1, Taker mit 0,05 % Slippage)")
print(t[["name", "bestanden", "score", "D1_G", "D1_F", "D1_N", "D2_G", "D2_F", "D2_N", "D1_bp_je_umsatz", "D2_bp_je_umsatz",
         "D2_vol_tag", "D1_dd_mit", "D2_dd_mit", "D2_rebate_anteil", "D2_halte_h"]].round(3).to_string())
fin = t[t["bestanden"]].sort_values("score", ascending=False).head(2)
print("Finalisten:", list(fin["name"]))
erg = {"stufe1": zeilen, "finalisten": {}}
mB = None
for _, r in fin.iterrows():
    n, fam, p = r["name"], r["familie"], json.loads(r["params"])
    wA = W[n]
    e = erg["finalisten"][n] = {"familie": fam, "params": p, "stufen": {}}
    print(f"\n######## {n}")
    # ---------------- Stufe 2
    ls = R.lauf(mA, wA, taker=True, slip=0.001)
    s2 = {k: R.sicht(ls, *FENSTER[k]) for k in ("D1", "D2")}
    ok2 = all(x["N"] > 0 for x in s2.values())
    e["stufen"]["2_stress"] = {"ok": ok2, **s2}
    print(f"Stufe 2 doppelte Slippage: {'bestanden' if ok2 else 'DURCHGEFALLEN'}"); print(tab(s2))
    if not ok2:
        continue
    # ---------------- Stufe 3
    lA = R.lauf(mA, wA, taker=True)
    a = {k: R.sicht(lA, *FENSTER[k]) for k in ("D1", "D2", "Entwicklung", "Pruefung", "Gesamt")}
    if mB is None:
        mB = R.markt(R.GRUPPE_B)
    wB = R.auf_raster(mB, R.FAMILIEN[fam](mB, **p))
    lB = R.lauf(mB, wB, taker=True)
    b = {k: R.sicht(lB, *FENSTER[k]) for k in ("Entwicklung", "Pruefung", "Gesamt")}
    ok3 = a["Pruefung"]["G"] > 0 and a["Pruefung"]["N"] > 0 and b["Entwicklung"]["N"] > 0 and b["Pruefung"]["N"] > 0
    stress_p = R.sicht(ls, *FENSTER["Pruefung"])
    e["stufen"]["3_pruefung"] = {"ok": ok3, "A": a, "B": b, "A_stress_pruefung": stress_p}
    print(f"Stufe 3 Prüfzeitraum + Gruppe B: {'bestanden' if ok3 else 'DURCHGEFALLEN'}")
    print("Gruppe A:"); print(tab(a)); print("Gruppe B:"); print(tab(b))
    print("Gruppe A, Prüfzeitraum bei doppelter Slippage: G", round(stress_p["G"], 3), "N", round(stress_p["N"], 3))
    if not ok3:
        continue
    # ---------------- Stufe 4
    rng = np.random.default_rng(7)
    echt = a["Gesamt"]["N"]
    T = wA.shape[1]
    zufall = [R.sicht(R.lauf(mA, np.ascontiguousarray(np.roll(wA, int(rng.integers(288 * 30, T - 288 * 30)), axis=1)), taker=True),
                      None, None)["N"] for _ in range(200)]
    pct = float((np.array(zufall) < echt).mean() * 100)
    ok4 = pct >= 90
    e["stufen"]["4_zufall"] = {"ok": ok4, "perzentil": pct, "echt_N": echt, "zufall_median": float(np.median(zufall)),
                               "zufall_p90": float(np.percentile(zufall, 90)), "zufall_max": float(np.max(zufall))}
    print(f"Stufe 4 Zufallstest: Perzentil {pct:.1f} ({'bestanden' if ok4 else 'DURCHGEFALLEN'}); echt {echt:.3f}, "
          f"Zufall Median {np.median(zufall):.3f}, 90 % {np.percentile(zufall, 90):.3f}, Max {np.max(zufall):.3f}")
    if not ok4:
        continue
    # ---------------- Stufe 5
    gewaehlt, lh = None, None
    for h in (5, 4, 3, 2.5, 2, 1.5, 1, 0.75, 0.5):
        l = R.lauf(mA, wA, hebel=h, taker=True)
        if R.sicht(l, *FENSTER["Entwicklung"])["dd_mit"] <= 0.10:
            gewaehlt, lh = h, l
            break
    if gewaehlt is None:
        e["stufen"]["5_hebel"] = {"ok": False, "grund": "kein Hebel ab 0,5 hält 10 % Einbruch in der Entwicklung",
                                  "dd_hebel1_entwicklung": a["Entwicklung"]["dd_mit"], "dd_hebel1_pruefung": a["Pruefung"]["dd_mit"]}
        print("Stufe 5: DURCHGEFALLEN. Einbruch bei Hebel 1: Entwicklung", round(a["Entwicklung"]["dd_mit"], 3),
              "Prüfung", round(a["Pruefung"]["dd_mit"], 3))
        continue
    h5 = {k: R.sicht(lh, *FENSTER[k]) for k in ("Entwicklung", "Pruefung", "Gesamt")}
    ok5 = h5["Pruefung"]["dd_mit"] < 0.15
    e["stufen"]["5_hebel"] = {"ok": ok5, "hebel": gewaehlt, **h5, "orders": runner.order_statistik(lh)}
    print(f"Stufe 5 Hebel {gewaehlt}: {'bestanden' if ok5 else 'DURCHGEFALLEN'}"); print(tab(h5)); print("  ", runner.order_statistik(lh))
    pr = h5["Pruefung"]
    e["loesung"] = bool(ok5 and pr["G"] > 0 and pr["N"] > 0 and pr["R"] > pr["N"] - pr["R"])
    print("ALLE BEDINGUNGEN:", e["loesung"])
(ROOT / "reports/suche_runde2.json").write_text(json.dumps(erg, indent=1, default=float))
print(f"fertig in {time.time() - t0:.0f} s")
