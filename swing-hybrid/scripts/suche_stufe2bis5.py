"""Stufen 2–5 für die Finalisten aus Stufe 1, in der Reihenfolge des Protokolls. Wer eine Stufe nicht besteht, scheidet aus."""
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
import numpy as np
import pandas as pd
from hybrid import research as R

ROOT = Path(__file__).resolve().parents[1]
pd.set_option("display.width", 260, "display.max_columns", 60)
FENSTER = {"D1": (None, R.D1_ENDE), "D2": (R.D1_ENDE, R.SPLIT), "Entwicklung": (None, R.SPLIT), "Pruefung": (R.SPLIT, None),
           "Gesamt": (None, None)}
SP = ["G", "F", "R", "handel", "N", "rebate_anteil", "dd_mit", "vol_tag", "bp_je_umsatz", "maker", "of", "trades", "halte_h",
      "sharpe", "jahr_N", "anteil_coin", "anteil_monat"]


def tabelle(d):
    return pd.DataFrame(d).T[SP].round(3).to_string()


finalisten = json.loads((ROOT / "reports/suche_finalisten.json").read_text())
mA = R.markt(R.GRUPPE_A)
mB = R.markt(R.GRUPPE_B)
erg = {}
for f in finalisten:
    n, fam, p = f["name"], f["familie"], f["params"]
    print(f"\n######## {n}")
    e = erg[n] = {"familie": fam, "params": p, "stufen": {}}
    wA = R.auf_raster(mA, R.FAMILIEN[fam](mA, **p))
    # ---- Stufe 2: Füll-Stress in der Entwicklung
    ls = R.lauf(mA, wA, adverse=0.0001, delay=1)
    s2 = {k: R.sicht(ls, *FENSTER[k]) for k in ("D1", "D2")}
    ok2 = all(x["N"] > 0 for x in s2.values())
    e["stufen"]["2_stress"] = {"ok": ok2, **s2}
    print(f"Stufe 2 Füll-Stress (Entwicklung): {'bestanden' if ok2 else 'DURCHGEFALLEN'}"); print(tabelle(s2))
    if not ok2:
        continue
    # ---- Stufe 3: Prüfzeitraum Gruppe A (einmalig) und Gruppe B
    lA = R.lauf(mA, wA)
    a = {k: R.sicht(lA, *FENSTER[k]) for k in ("D1", "D2", "Pruefung", "Gesamt")}
    wB = R.auf_raster(mB, R.FAMILIEN[fam](mB, **p))
    lB = R.lauf(mB, wB)
    b = {k: R.sicht(lB, *FENSTER[k]) for k in ("Entwicklung", "Pruefung", "Gesamt")}
    ok3 = a["Pruefung"]["G"] > 0 and a["Pruefung"]["N"] > 0 and b["Entwicklung"]["N"] > 0 and b["Pruefung"]["N"] > 0
    e["stufen"]["3_pruefung"] = {"ok": ok3, "A": a, "B": b}
    print(f"Stufe 3 Prüfzeitraum + Gruppe B: {'bestanden' if ok3 else 'DURCHGEFALLEN'}")
    print("Gruppe A:"); print(tabelle(a)); print("Gruppe B:"); print(tabelle(b))
    stress_p = R.sicht(ls, *FENSTER["Pruefung"])
    e["stufen"]["3_pruefung"]["A_stress_pruefung"] = stress_p
    print("Gruppe A, Prüfzeitraum unter Füll-Stress: N", round(stress_p["N"], 3), "G", round(stress_p["G"], 3))
    if not ok3:
        continue
    # ---- Stufe 4: Zufallstest (Signal zeitlich verschoben), ganzer Zeitraum, Gruppe A
    rng = np.random.default_rng(7)
    echt = a["Gesamt"]["N"]
    T = wA.shape[1]
    zufall = []
    t0 = time.time()
    for _ in range(200):
        k = int(rng.integers(288 * 30, T - 288 * 30))
        zufall.append(R.sicht(R.lauf(mA, np.ascontiguousarray(np.roll(wA, k, axis=1))), None, None)["N"])
    pct = float((np.array(zufall) < echt).mean() * 100)
    ok4 = pct >= 90
    e["stufen"]["4_zufall"] = {"ok": ok4, "perzentil": pct, "echt_N": echt, "zufall_median": float(np.median(zufall)),
                               "zufall_p90": float(np.percentile(zufall, 90)), "zufall_max": float(np.max(zufall))}
    print(f"Stufe 4 Zufallstest: Perzentil {pct:.1f} ({'bestanden' if ok4 else 'DURCHGEFALLEN'}), echt {echt:.3f}, "
          f"Zufall Median {np.median(zufall):.3f}, 90 % {np.percentile(zufall, 90):.3f}, Max {np.max(zufall):.3f} ({time.time() - t0:.0f} s)")
    if not ok4:
        continue
    # ---- Stufe 5: Hebel so, dass der Einbruch in der Entwicklung <= 10 % ist
    dd1 = R.sicht(lA, *FENSTER["Entwicklung"])["dd_mit"]
    kandidaten = [h for h in (5, 4, 3, 2.5, 2, 1.5, 1, 0.75, 0.5) if True]
    gewaehlt, lh = None, None
    for h in kandidaten:
        l = R.lauf(mA, wA, hebel=h)
        if R.sicht(l, *FENSTER["Entwicklung"])["dd_mit"] <= 0.10:
            gewaehlt, lh = h, l
            break
    if gewaehlt is None:
        e["stufen"]["5_hebel"] = {"ok": False, "grund": "kein Hebel >= 0,5 hält 10 % Einbruch in der Entwicklung", "dd_hebel1": dd1}
        print("Stufe 5: DURCHGEFALLEN (Einbruch bei Hebel 1 in der Entwicklung:", round(dd1, 3), ")")
        continue
    h5 = {k: R.sicht(lh, *FENSTER[k]) for k in ("Entwicklung", "Pruefung", "Gesamt")}
    ok5 = h5["Pruefung"]["dd_mit"] < 0.15
    from hybrid import runner
    e["stufen"]["5_hebel"] = {"ok": ok5, "hebel": gewaehlt, **h5, "orders": runner.order_statistik(lh)}
    print(f"Stufe 5 Hebel {gewaehlt}: {'bestanden' if ok5 else 'DURCHGEFALLEN'}"); print(tabelle(h5))
    print("  ", runner.order_statistik(lh))
    p = h5["Pruefung"]
    e["loesung"] = bool(ok5 and p["G"] > 0 and p["N"] > 0 and p["R"] > p["N"] - p["R"])
    print("ALLE BEDINGUNGEN IM PRÜFZEITRAUM:", e["loesung"])
(ROOT / "reports/suche_ergebnis.json").write_text(json.dumps(erg, indent=1, default=float))
