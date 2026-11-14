"""Runde 3: dieselben 10 Trend-Einstellungen, gemessen ohne Tageslimit und unter zwei Ausführungsarten. Stufen 1–5."""
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
AUS = 9.0  # Tageslimit aus (Stufen 1–4)
ARTEN = {"passiv": dict(taker=False), "sofort": dict(taker=True)}


def name(fam, p):
    return fam + "_" + "_".join(f"{k}{v}" for k, v in p.items())


def tab(d):
    return pd.DataFrame(d).T[SP].round(3).to_string()


t0 = time.time()
mA = R.markt(R.GRUPPE_A)
zeilen, W = [], {}
for fam, p in KONFIG:
    w = W[name(fam, p)] = R.auf_raster(mA, R.FAMILIEN[fam](mA, **p))
    z = {"name": name(fam, p), "familie": fam, "params": json.dumps(p)}
    ok, sharpes = True, []
    for art, kw in ARTEN.items():
        l = R.lauf(mA, w, day_limit=AUS, **kw)
        for f in ("D1", "D2"):
            s = R.sicht(l, *FENSTER[f])
            ok = ok and s["G"] > 0 and s["N"] > 0
            sharpes.append(s["sharpe"])
            z.update({f"{art}_{f}_{k}": s[k] for k in ("G", "F", "N", "bp_je_umsatz", "dd_mit", "vol_tag", "sharpe")})
    z["bestanden"], z["score"] = ok, min(sharpes)
    zeilen.append(z)
t = pd.DataFrame(zeilen)
t.to_csv(ROOT / "reports/suche_runde3_stufe1.csv", index=False)
print("STUFE 1 (Entwicklung, Gruppe A, Hebel 1, ohne Tageslimit)")
print(t[["name", "bestanden", "score", "passiv_D1_G", "passiv_D1_N", "passiv_D2_G", "passiv_D2_N", "sofort_D1_G", "sofort_D1_N",
         "sofort_D2_G", "sofort_D2_N", "sofort_D1_bp_je_umsatz", "sofort_D2_bp_je_umsatz", "sofort_D1_dd_mit", "sofort_D2_dd_mit",
         "sofort_D2_vol_tag"]].round(3).to_string())
fin = t[t["bestanden"]].sort_values("score", ascending=False).head(2)
print("Finalisten:", list(fin["name"]))
erg = {"stufe1": zeilen, "finalisten": {}}
mB = None
for _, r in fin.iterrows():
    n, fam, p = r["name"], r["familie"], json.loads(r["params"])
    wA = W[n]
    e = erg["finalisten"][n] = {"familie": fam, "params": p, "stufen": {}}
    print(f"\n######## {n}")
    ls = R.lauf(mA, wA, adverse=0.0001, day_limit=AUS)
    s2 = {k: R.sicht(ls, *FENSTER[k]) for k in ("D1", "D2")}
    ok2 = all(x["N"] > 0 for x in s2.values())
    e["stufen"]["2_stress"] = {"ok": ok2, **s2}
    print(f"Stufe 2 passiv, Füllpreis 0,01 % schlechter: {'bestanden' if ok2 else 'DURCHGEFALLEN'}"); print(tab(s2))
    if not ok2:
        continue
    if mB is None:
        mB = R.markt(R.GRUPPE_B)
    wB = R.auf_raster(mB, R.FAMILIEN[fam](mB, **p))
    s3, ok3, laeufe = {}, True, {}
    for art, kw in ARTEN.items():
        lA = laeufe[art] = R.lauf(mA, wA, day_limit=AUS, **kw)
        lB = R.lauf(mB, wB, day_limit=AUS, **kw)
        a = {k: R.sicht(lA, *FENSTER[k]) for k in ("D1", "D2", "Entwicklung", "Pruefung", "Gesamt")}
        b = {k: R.sicht(lB, *FENSTER[k]) for k in ("Entwicklung", "Pruefung", "Gesamt")}
        s3[art] = {"A": a, "B": b}
        ok3 = ok3 and a["Pruefung"]["G"] > 0 and a["Pruefung"]["N"] > 0 and b["Entwicklung"]["N"] > 0 and b["Pruefung"]["N"] > 0
        print(f"--- {art}: Gruppe A"); print(tab(a)); print(f"--- {art}: Gruppe B"); print(tab(b))
    e["stufen"]["3_pruefung"] = {"ok": ok3, **s3}
    print(f"Stufe 3 Prüfzeitraum + Gruppe B, beide Ausführungsarten: {'bestanden' if ok3 else 'DURCHGEFALLEN'}")
    if not ok3:
        continue
    rng = np.random.default_rng(7)
    echt = s3["sofort"]["A"]["Gesamt"]["N"]
    T = wA.shape[1]
    zufall = [R.sicht(R.lauf(mA, np.ascontiguousarray(np.roll(wA, int(rng.integers(288 * 30, T - 288 * 30)), axis=1)),
                             taker=True, day_limit=AUS), None, None)["N"] for _ in range(200)]
    pct = float((np.array(zufall) < echt).mean() * 100)
    ok4 = pct >= 90
    e["stufen"]["4_zufall"] = {"ok": ok4, "perzentil": pct, "echt_N": echt, "zufall_median": float(np.median(zufall)),
                               "zufall_p90": float(np.percentile(zufall, 90)), "zufall_max": float(np.max(zufall))}
    print(f"Stufe 4 Zufallstest: Perzentil {pct:.1f} ({'bestanden' if ok4 else 'DURCHGEFALLEN'}); echt {echt:.3f}, "
          f"Zufall Median {np.median(zufall):.3f}, 90 % {np.percentile(zufall, 90):.3f}, Max {np.max(zufall):.3f}")
    if not ok4:
        continue
    gewaehlt, lh = None, None
    for h in (5, 4, 3, 2.5, 2, 1.5, 1, 0.75, 0.5, 0.4, 0.3, 0.25, 0.2, 0.15, 0.1):
        l = R.lauf(mA, wA, hebel=h, taker=True)
        if R.sicht(l, *FENSTER["Entwicklung"])["dd_mit"] <= 0.10:
            gewaehlt, lh = h, l
            break
    if gewaehlt is None:
        e["stufen"]["5_hebel"] = {"ok": False, "grund": "kein Hebel ab 0,1 hält 10 % Einbruch in der Entwicklung"}
        print("Stufe 5: DURCHGEFALLEN (kein Hebel ab 0,1 hält 10 %)")
        continue
    h5 = {k: R.sicht(lh, *FENSTER[k]) for k in ("Entwicklung", "Pruefung", "Gesamt")}
    pr = h5["Pruefung"]
    ok5 = pr["dd_mit"] < 0.15 and pr["G"] > 0 and pr["N"] > 0 and pr["R"] > pr["N"] - pr["R"]
    e["stufen"]["5_hebel"] = {"ok": ok5, "hebel": gewaehlt, **h5, "orders": runner.order_statistik(lh)}
    print(f"Stufe 5 Hebel {gewaehlt} mit Tageslimit 3 %: {'bestanden' if ok5 else 'DURCHGEFALLEN'}"); print(tab(h5))
    print("  ", runner.order_statistik(lh))
    e["loesung"] = bool(ok5)
(ROOT / "reports/suche_runde3.json").write_text(json.dumps(erg, indent=1, default=float))
print(f"fertig in {time.time() - t0:.0f} s")
