import json
from pathlib import Path
import pandas as pd
pd.set_option("display.width", 250, "display.max_columns", 60, "display.max_rows", 100)
R = Path("/home/user/OdinGate-Botv134/swing-hybrid/reports")
def j(n): return json.loads((R/n).read_text())
def f(x, nd=4): return round(x, nd) if isinstance(x, (int, float)) else x
s1 = pd.read_csv(R/"suche_stufe1.csv")
print("R1: Einstellungen", len(s1), "bestanden", int(s1["bestanden"].sum()), list(s1[s1.bestanden]["name"]))
print(s1[s1.bestanden][["name","score","D1_G","D1_N","D2_G","D2_N"]].round(3).to_string())
print("   Summe N D1+D2 der Finalisten (vor Stress):", {r["name"]: round(r["D1_N"]+r["D2_N"],3) for _, r in s1[s1.bestanden].iterrows()})
e = j("suche_ergebnis.json")
print("   unter Stress N D1+D2:", {n: round(v["stufen"]["2_stress"]["D1"]["N"]+v["stufen"]["2_stress"]["D2"]["N"],3) for n, v in e.items()})
print("   Familienzaehlung:", s1["familie"].value_counts().to_dict())
r10 = j("suche_runde10.json")
print("R10: neu", r10["neu"], "paare", r10["paare"], {k: f(r10["hebel1"][k]["N"]) for k in r10["hebel1"]}, "stufen", {k: (v.get("ok") if isinstance(v, dict) else v) for k, v in r10["stufen"].items()})
print("   paar_statistik", json.dumps(r10["paar_statistik"], default=float)[:600]); print("   placebo", json.dumps(r10["placebo"], default=float)[:300])
r11 = j("suche_runde11.json"); print("R11: varianten", r11["varianten"], "stufe1", len(r11["stufe1"]), "stufe2", r11["stufe2"], {k: (f(v["entw_median"],2), f(v["pruef_median"],2), f(v["maker_pruef_median"],2)) for k, v in r11["frontier"].items()})
u = pd.read_csv(R/"suche_runde11_uebersicht.csv"); print("   uebersicht: Zeilen", len(u), "mit n_D1>=200 und n_D2>=200:", int(((u.n_D1>=200)&(u.n_D2>=200)).sum()), "| A_Pruef nicht leer:", int(u.A_Pruef.notna().sum()))
b = u[u.regel=="b14_volumen_mit_z3.0_halte24"]; print("   beste:", b[["regel","A_D1","A_D2","A_Pruef","C_Entw","C_Pruef"]].round(2).to_string(index=False))
r12 = j("suche_runde12.json")
print("R12 statarb keys", list(r12["statarb"].keys()))
for z in r12["statarb"]["stufe1"]: print("   ", z["name"], z["bestanden"], "D1_N", f(z["D1_N"],3), "D2_N", f(z["D2_N"],3), "Entw_G", f(z["Entw_G"],3), "Entw_N", f(z["Entw_N"],3))
for k, v in r12["statarb"].items():
    if k != "stufe1": print("   ", k, json.dumps(v, default=float)[:700])
print("   fusion keys", list(r12["fusion"].keys())); print("   ", json.dumps(r12["fusion"], default=float)[:1200])
r14 = j("suche_runde14.json"); print("R14 kandidat", {k: (f(v["sharpe"],2), f(v["N"],3), f(v["dd"],3)) for k, v in r14["kandidat"].items()}, "mischung", {k: (f(v["sharpe"],2), f(v["N"],3), f(v["dd"],3)) for k, v in r14["mischung"].items()}, "huerden", r14["huerden"])
r15 = j("suche_runde15.json"); print("R15 mischung", {k: (f(v["sharpe"],2), f(v["N"],3), f(v["dd"],3)) for k, v in r15["mischung"].items()}, "korr", f(r15["korrelation_tag"],3), "huerden", r15["huerden"])
r16 = j("suche_runde16.json"); print("R16 H2 keys", list(r16["H2"].keys())); print("   ", json.dumps(r16["H2"], default=float)[:1500]); print("   H1 mischung", {k: f(v["sharpe"],2) for k, v in r16["H1"]["mischung"].items()})
r17 = j("suche_runde17.json"); print("R17 H2 keys", list(r17["H2"].keys())); print("   netto", {k: (f(v["N"],3), f(v["sharpe"],2)) for k, v in r17["H2"]["netto"].items()}, "mischung", {k: (f(v["sharpe"],2), f(v["dd"],2)) for k, v in r17["H2"]["mischung"].items()})
for n in ("suche_runde18.json","suche_runde19.json","suche_runde20a.json","suche_runde20b.json","suche_runde23.json"):
    d = j(n); print(n, "keys", list(d.keys())); print("   ", json.dumps(d, default=float)[:1100])
