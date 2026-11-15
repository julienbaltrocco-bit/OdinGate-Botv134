"""E13 Version 1.1 (Signal-Ausstieg) einmalig in der Validierung, im Vergleich mit Version 1.0."""
import sys, time
from pathlib import Path
import numpy as np, pandas as pd
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from alpha import kern as K, konto
import e10_ausstiege as X

start = time.time()
E, V = X.E, X.V
ZEIT = {"E": E, "V": V, "E+V": (E[0], V[1])}
erg = {"version": "1.1", "parameter": {"tiefe_pct": 5, "einstieg_z": 3.0, "ausstieg_z": 1.0, "zeitlimit_kerzen": 48, "kerze": "5m"}}
t11, t10 = X.alle("X3_signal", V[1]), X.alle("X0_zeit60", V[1])
for name, t in (("Version 1.1", t11), ("Version 1.0", t10)):
    for z, (a, b) in ZEIT.items():
        kz = K.kennzahlen(t, a, b); kt = konto.kennzahlen(konto.tagesreihe(t, "n85", a, b, 3))
        erg[f"{name} {z}"] = {"trades": kz, "konto_hebel1": kt, "konto_n0": konto.kennzahlen(konto.tagesreihe(t, "n0", a, b, 3)),
                              "konto_n50": konto.kennzahlen(konto.tagesreihe(t, "n50", a, b, 3)), "verlustserie": konto.verlustserie(t[(t["ein"] >= a) & (t["ein"] < b)], "n85")}
        print(K.zeile(f"{name} {z}", kz), f"| Jahr {kt['ertrag_jahr_pct']} % Sharpe {kt['sharpe']} Rückgang {kt['rueckgang_pct_startkapital']} % bester Tag {kt['anteil_bester_tag']}")
for c in X.COINS:
    erg[f"V_{c}"] = K.kennzahlen(t11[t11["coin"] == c], *V); print("   ", K.zeile(f"1.1 V {c}", erg[f"V_{c}"]))
for r in (-1.0, 1.0):
    print("   ", K.zeile(f"1.1 V Richtung {r}", K.kennzahlen(t11[t11["richtung"] == r], *V)))
q = t11[(t11["ein"] >= E[0]) & (t11["ein"] < V[1])]
erg["je_quartal_n85"] = {str(p): K.kennzahlen(g)["n85"] for p, g in q.groupby(q["ein"].dt.to_period("Q"))}
print("    Quartale N85:", erg["je_quartal_n85"])
d2 = X.K.netto(t11.drop(columns=["slip", "g", "n0", "n50", "n85"]), X.slip, 2.0)
sp = t11.drop(columns=["slip", "g", "n0", "n50", "n85"]).copy(); sp["roh"] = sp["roh_spaeter"]; sp = K.netto(sp.dropna(subset=["roh"]), X.slip)
erg["V_doppelte_slippage"], erg["V_eine_kerze_spaeter"] = K.kennzahlen(d2, *V), K.kennzahlen(sp, *V)
erg["E_eine_kerze_spaeter"] = K.kennzahlen(sp, *E)
print("   ", K.zeile("1.1 V doppelte Slippage", erg["V_doppelte_slippage"])); print("   ", K.zeile("1.1 V eine Kerze später", erg["V_eine_kerze_spaeter"]))
print("   ", K.zeile("1.1 E eine Kerze später", erg["E_eine_kerze_spaeter"]))
for h in (1, 3, 5):
    for z in ("E", "V"):
        erg[f"starttage_{z}_hebel{h}"] = konto.starttage(t11, "n85", *ZEIT[z], 3, h)
        print(f"    Starttage {z} Hebel {h}: {erg[f'starttage_{z}_hebel{h}']}")
tt = t11[(t11["ein"] >= E[0]) & (t11["ein"] < V[1])]
erg["schlimmster_kurs_im_trade_bp"] = {"p1": round(float(tt["schlimmst"].quantile(0.01)), 1), "min": round(float(tt["schlimmst"].min()), 1)}
print("    Ungünstigster Kurs im Trade (bp):", erg["schlimmster_kurs_im_trade_bp"], "| Haltedauer Median (min):", float(((tt["aus"] - tt["ein"]).dt.total_seconds() / 60).median()))
tag11, tag10 = konto.tagesreihe(t11, "n85", *V, 3), konto.tagesreihe(t10, "n85", *V, 3)
h = {"n85_V_positiv": erg["Version 1.1 V"]["trades"]["n85"] > 0, "besser_als_1.0_in_V": float(tag11.mean()) > float(tag10.mean()),
     "doppelte_slippage_positiv": erg["V_doppelte_slippage"]["n85"] > 0, "eine_kerze_spaeter_positiv": erg["V_eine_kerze_spaeter"]["n85"] > 0,
     "keine_liquidation_hebel3": erg["starttage_E_hebel3"]["liquidationen"] + erg["starttage_V_hebel3"]["liquidationen"] == 0}
erg["huerden"], erg["bestanden"] = {k: bool(x) for k, x in h.items()}, bool(all(h.values()))
print("\nHürden:", erg["huerden"], "→", "BESTANDEN" if erg["bestanden"] else "NICHT BESTANDEN")
FR = ["XRP", "DOGE", "LINK", "AVAX", "LTC"]
tf = X.alle("X3_signal", V[1], FR)
erg["frische_fuenf"] = {z: K.kennzahlen(tf, *ZEIT[z]) for z in ZEIT}
for z in ZEIT: print(K.zeile(f"1.1 frische fünf {z}", erg["frische_fuenf"][z]))
tt.drop(columns=["roh_spaeter"]).to_csv(K.ERG / "e13_version11_trades.csv", index=False)
K.speichern("e13_version11", erg, start)
