"""Runde 12: Stat-Arb (Paare, Z-Score) allein und fusioniert mit den Swing-Strategien des Labors. Laut Protokoll."""
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
import numpy as np
import pandas as pd
from hybrid import data, research as R, runner, statarb as S, swing

ROOT = Path(__file__).resolve().parents[1]
pd.set_option("display.width", 250, "display.max_columns", 40)
G = json.loads((ROOT / "reports/suche_runde6.json").read_text())["gruppen"]
LABOR = 0.001                                   # 0,05 % Gebühr + 0,05 % Slippage je Order
D1, SPLIT = R.D1_ENDE, R.SPLIT
SP = ["G", "kosten", "funding", "N", "dd", "sharpe", "jahr_N", "umsatz_tag", "einsatz"]


def drei(tag):
    return {"D1": S.kennzahlen(tag, None, D1), "D2": S.kennzahlen(tag, D1, SPLIT), "Entwicklung": S.kennzahlen(tag, None, SPLIT),
            "Pruefung": S.kennzahlen(tag, SPLIT, None), "Gesamt": S.kennzahlen(tag)}


def tab(d, sp=SP):
    return pd.DataFrame(d).T[sp].round(3).to_string()


t0 = time.time()
M = {g: R.markt(G[g]) for g in ("A", "B", "C")}
out = {}
# ------------------------------------------------------------ Stufe 1: Raster auf Gruppe A (nur Entwicklung zeigen)
zeilen, LAEUFE = [], {}
for W in (168, 336, 720):
    for z in (1.5, 2.0, 2.5):
        n = f"W{W // 24}T_z{z}"
        tag, tr = S.lauf(M["A"], W, z, LABOR)
        LAEUFE[n] = (W, z, tag, tr)
        d = drei(tag)
        zeilen.append({"name": n, "W_tage": W // 24, "z_ein": z,
                       "bestanden": all(d[f]["G"] > 0 and d[f]["N"] > 0 for f in ("D1", "D2")),
                       "score": min(d["D1"]["sharpe"], d["D2"]["sharpe"]), "trades": int((tr["ein_zeit"] < SPLIT).sum()),
                       **{f"{f}_{k}": d[f][k] for f in ("D1", "D2") for k in ("G", "N", "sharpe")},
                       **{f"Entw_{k}": d["Entwicklung"][k] for k in ("G", "kosten", "N", "dd", "umsatz_tag", "einsatz")}})
t = pd.DataFrame(zeilen)
t.to_csv(ROOT / "reports/suche_runde12_stufe1.csv", index=False)
print("STUFE 1: Stat-Arb auf Gruppe A, Entwicklung (Topf = 1, Labor-Kosten 0,10 % je Order)")
print(t.round(3).to_string())
bestanden = t[t["bestanden"]]
wahl = (bestanden if len(bestanden) else t).sort_values("score", ascending=False).iloc[0]
name = wahl["name"]
W, z, tagA, trA = LAEUFE[name]
print(f"\nGewählt: {name} ({'besteht Stufe 1' if len(bestanden) else 'KEINE Einstellung besteht Stufe 1; beste nach Score, nur zur Berichterstattung'})")
e = out["statarb"] = {"stufe1": zeilen, "wahl": name, "W": int(W), "z_ein": float(z), "stufe1_ok": bool(len(bestanden) > 0)}
a = drei(tagA)
stress = drei(S.lauf(M["A"], W, z, 2 * LABOR)[0])
e["A"], e["A_stress"] = a, stress
e["stufe2_ok"] = bool(all(stress[f]["N"] > 0 for f in ("D1", "D2")))
print("Gruppe A:"); print(tab(a))
print(f"Stufe 2 (doppelte Kosten): {'bestanden' if e['stufe2_ok'] else 'DURCHGEFALLEN'} (D1 N {stress['D1']['N']:.3f}, D2 N {stress['D2']['N']:.3f})")
for g in ("B", "C"):
    e[g] = drei(S.lauf(M[g], W, z, LABOR)[0])
    print(f"Gruppe {g}:"); print(tab({k: e[g][k] for k in ("Entwicklung", "Pruefung", "Gesamt")}))
e["stufe3_ok"] = bool(a["Pruefung"]["N"] > 0 and all(e[g][f]["N"] > 0 for g in ("B", "C") for f in ("Entwicklung", "Pruefung")))
print(f"Stufe 3 (Prüfzeitraum A, Gruppen B und C): {'bestanden' if e['stufe3_ok'] else 'DURCHGEFALLEN'}")
trA2 = trA.assign(netto=lambda x: x["gewinn"])   # Kursgewinn je Paar-Trade, vor Kosten
e["trades"] = {"anzahl": int(len(trA)), "gewinner_vor_kosten": float((trA["gewinn"] > 0).mean()), "stunden_mittel": float(trA["stunden"].mean()),
               "gruende": trA["grund"].value_counts().to_dict(), "gewinn_je_grund": trA.groupby("grund")["gewinn"].sum().round(4).to_dict(),
               "mittel_gewinn_je_trade": float(trA["gewinn"].mean()), "kosten_je_trade": float(4 * LABOR / 10 / 2 * 1)}
print("Trades Gruppe A:", json.dumps(e["trades"], default=float))
kY = 0.0008 * 0.15 + R.yubit_kosten(G["A"])[0]
e["A_yubit_kosten"] = drei(S.lauf(M["A"], W, z, kY)[0])
e["A_ohne_kosten"] = drei(S.lauf(M["A"], W, z, 0.0)[0])
print(f"Zum Vergleich mit Yubit-Kosten nach Rebate: Entwicklung N {e['A_yubit_kosten']['Entwicklung']['N']:.3f}, Prüfung N {e['A_yubit_kosten']['Pruefung']['N']:.3f}"
      f" | ganz ohne Kosten: Entwicklung {e['A_ohne_kosten']['Entwicklung']['N']:.3f}, Prüfung {e['A_ohne_kosten']['Pruefung']['N']:.3f}")

# ------------------------------------------------------------ Fusion mit den Swing-Strategien
_, _, _, hidx = S.stundenfelder(M["A"])
out["fusion"] = {}
for strat in ("trail_beide", "momentum_vol_ls"):
    md = data.laden(strat, G["A"])
    ls = runner.lauf(md, 1.0, **runner.VARIANTEN["baseline"])
    d = ls.daily
    kum = (d[:, :, 0] - 0.0005 * (d[:, :, 1] + d[:, :, 2]) + d[:, :, 3]).sum(axis=0)     # Labor-Kosten: 0,05 % Gebühr; Slippage steckt im Kurs
    brutto = (d[:, :, 0] + d[:, :, 3]).sum(axis=0)
    sw_tag = pd.DataFrame({"netto": np.diff(np.concatenate([[0.0], kum])), "brutto": np.diff(np.concatenate([[0.0], brutto]))}, index=md.days)
    sw_tag["kosten"] = sw_tag["brutto"] - sw_tag["netto"]; sw_tag["funding"] = 0.0; sw_tag["umsatz"] = 0.0; sw_tag["einsatz"] = 0.0
    sw = np.column_stack([swing.ziel_ab(c, strat).pipe(lambda s: s.set_axis(s.index.astype("datetime64[ns]")))
                          .reindex(hidx.union(swing.ziel_ab(c, strat).index.astype("datetime64[ns]"))).ffill().reindex(hidx).fillna(0.0).to_numpy()
                          for c in G["A"]])
    sa_frei = tagA
    sa_filter, tr_f = S.lauf(M["A"], W, z, LABOR, sw=sw, filter_swing=True)
    idx = sw_tag.index.intersection(sa_frei.index)
    def kombi(x):
        k = 0.5 * sw_tag.loc[idx, ["netto", "brutto", "kosten"]] + 0.5 * x.loc[idx, ["netto", "brutto", "kosten"]]
        k["funding"] = 0.0; k["umsatz"] = 0.0; k["einsatz"] = 0.0
        return k
    f = {"swing_allein": drei(sw_tag.loc[idx]), "statarb_allein": drei(sa_frei.loc[idx]), "statarb_gefiltert": drei(sa_filter.loc[idx]),
         "F1_zwei_toepfe": drei(kombi(sa_frei)), "F2_swing_als_filter": drei(kombi(sa_filter)),
         "trades_gefiltert": int(len(tr_f)), "trades_frei": int(len(trA)),
         "korrelation_tagesgewinne": float(sw_tag.loc[idx, "netto"].corr(sa_frei.loc[idx, "netto"]))}
    for k in ("F1_zwei_toepfe", "F2_swing_als_filter"):
        f[k + "_besser"] = bool(all(f[k][w]["sharpe"] > f["swing_allein"][w]["sharpe"] and f[k][w]["dd"] < f["swing_allein"][w]["dd"]
                                    for w in ("Entwicklung", "Pruefung")))
    out["fusion"][strat] = f
    print(f"\n===== FUSION mit {strat} (Hebel 1, Labor-Kosten), Zeitraum {idx[0].date()} – {idx[-1].date()}; "
          f"Korrelation der Tagesgewinne Swing/Stat-Arb {f['korrelation_tagesgewinne']:.2f}")
    for k in ("swing_allein", "statarb_allein", "statarb_gefiltert", "F1_zwei_toepfe", "F2_swing_als_filter"):
        print(f"-- {k}:"); print(pd.DataFrame({w: f[k][w] for w in ("Entwicklung", "Pruefung", "Gesamt")}).T[["G", "N", "dd", "sharpe", "jahr_N"]].round(3).to_string())
    print("F1 besser als Swing allein:", f["F1_zwei_toepfe_besser"], "| F2 besser:", f["F2_swing_als_filter_besser"],
          f"| Trades frei {f['trades_frei']}, gefiltert {f['trades_gefiltert']}")
(ROOT / "reports/suche_runde12.json").write_text(json.dumps(out, indent=1, default=float))
print(f"\nfertig in {time.time() - t0:.0f} s")
