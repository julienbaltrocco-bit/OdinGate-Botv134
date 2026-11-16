"""Runde 13: Niedrig-Risiko-Baustein (Betting against Beta) auf A+B, Bestätigung auf C und D. Hürden laut Protokoll."""
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
import numpy as np
import pandas as pd
from hybrid import niedrigrisiko as NR, research as R, runner

ROOT = Path(__file__).resolve().parents[1]
pd.set_option("display.width", 260, "display.max_columns", 60)
AUS = 9.0
FEN = {"D1": (None, R.D1_ENDE), "D2": (R.D1_ENDE, R.SPLIT), "Entwicklung": (None, R.SPLIT), "Pruefung": (R.SPLIT, None),
       "Gesamt": (None, None)}
SP = ["G", "F", "R", "handel", "N", "dd_mit", "vol_tag", "bp_je_umsatz", "trades", "halte_h", "sharpe", "jahr_N"]
HEBEL = (5, 4, 3, 2.5, 2, 1.5, 1, 0.75, 0.5, 0.4, 0.35, 0.3, 0.25, 0.2, 0.15, 0.1)
G = json.loads((ROOT / "reports/suche_runde6.json").read_text())["gruppen"]


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


def schluss(out, t0):
    out["besser"] = bool(out.get("stufen", {}).get("6_vergleich", {}).get("ok", False))
    print("\nBESSER ALS DER KANDIDAT ALLEIN:", out["besser"])
    (ROOT / "reports/suche_runde13.json").write_text(json.dumps(out, indent=1, default=float))
    print(f"fertig in {time.time() - t0:.0f} s")
    sys.exit(0)


t0 = time.time()
AB = G["A"] + G["B"]
mAB = R.markt(AB)
kAB = R.yubit_kosten(AB)[0]
wS = R.auf_raster(mAB, NR.signal(mAB))
out = {"stufen": {}}
e = out["stufen"]

d = fen(R.lauf(mAB, wS, taker=True, slip=kAB, day_limit=AUS), ("D1", "D2", "Entwicklung"))
ok = all(d[f]["G"] > 0 and d[f]["N"] > 0 for f in ("D1", "D2"))
e["1_entwicklung"] = {"ok": ok, **d}
print(f"Stufe 1 Entwicklung A+B (Hebel 1, ohne Tageslimit): {'bestanden' if ok else 'DURCHGEFALLEN'}"); print(tab(d))
if not ok:
    schluss(out, t0)

s2 = fen(R.lauf(mAB, wS, taker=True, slip=2 * kAB, day_limit=AUS), ("D1", "D2"))
ok = all(x["N"] > 0 for x in s2.values())
e["2_stress"] = {"ok": ok, **s2}
print(f"Stufe 2 doppelte Kosten: {'bestanden' if ok else 'DURCHGEFALLEN'}"); print(tab(s2))
if not ok:
    schluss(out, t0)

s3 = {"AB": fen(R.lauf(mAB, wS, taker=True, slip=kAB, day_limit=AUS))}
print("-- A+B:"); print(tab(s3["AB"]))
for g in ("C", "D"):
    m = R.markt(G[g])
    s3[g] = fen(R.lauf(m, R.auf_raster(m, NR.signal(m)), taker=True, slip=R.yubit_kosten(G[g])[0], day_limit=AUS))
    print(f"-- Gruppe {g} ({len(G[g])} Coins):"); print(tab(s3[g]))
    del m
ok = (s3["AB"]["Pruefung"]["G"] > 0 and s3["AB"]["Pruefung"]["N"] > 0
      and all(s3[g][f]["N"] > 0 for g in ("C", "D") for f in ("Entwicklung", "Pruefung")))
e["3_bestaetigung"] = {"ok": ok, **s3}
print(f"Stufe 3 Bestätigung: {'bestanden' if ok else 'DURCHGEFALLEN'}")
if not ok:
    schluss(out, t0)

rng = np.random.default_rng(13)
echt = s3["AB"]["Gesamt"]["N"]
Tn = wS.shape[1]
z = [R.sicht(R.lauf(mAB, np.ascontiguousarray(np.roll(wS, int(rng.integers(288 * 30, Tn - 288 * 30)), axis=1)),
                    taker=True, slip=kAB, day_limit=AUS), None, None)["N"] for _ in range(200)]
pct = float((np.array(z) < echt).mean() * 100)
ok = pct >= 90
e["4_zufall"] = {"ok": ok, "perzentil": pct, "echt": echt, "median": float(np.median(z)), "p90": float(np.percentile(z, 90))}
print(f"Stufe 4 Zufallstest: Perzentil {pct:.1f} ({'bestanden' if ok else 'DURCHGEFALLEN'}); echt {echt:.3f}, Median {np.median(z):.3f}")
if not ok:
    schluss(out, t0)

h, lh = hebel_lauf(mAB, wS, kAB)
if h is None:
    e["5_hebel"] = {"ok": False}
    print("Stufe 5: DURCHGEFALLEN (kein Hebel hält 10 %)")
    schluss(out, t0)
h5 = fen(lh)
p = h5["Pruefung"]
ok = p["dd_mit"] < 0.15 and p["G"] > 0 and p["N"] > 0
e["5_hebel"] = {"ok": ok, "hebel": h, **h5, "orders": runner.order_statistik(lh)}
print(f"Stufe 5 Hebel {h}: {'bestanden' if ok else 'DURCHGEFALLEN'}"); print(tab(h5))
if not ok:
    schluss(out, t0)

wT = R.auf_raster(mAB, R.variante(mAB, "basis"))
hT, lT = hebel_lauf(mAB, wT, kAB)
kand = fen(lT)
hM, lM = hebel_lauf(mAB, 0.5 * wT + 0.5 * wS, kAB)
mix = fen(lM)
ok = all(mix[f]["N"] > kand[f]["N"] and mix[f]["sharpe"] > kand[f]["sharpe"] for f in ("Entwicklung", "Pruefung"))
e["6_vergleich"] = {"ok": ok, "kandidat": {"hebel": hT, **kand}, "mischung": {"hebel": hM, **mix}}
print(f"Stufe 6: Kandidat allein (Hebel {hT}):"); print(tab(kand))
print(f"Mischung (Hebel {hM}):"); print(tab(mix))
schluss(out, t0)
