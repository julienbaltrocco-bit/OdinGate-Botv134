"""Runde 6: echte Yubit-Kosten je Coin; Kandidat neu bewertet; marktneutrale Rangfolge; Kombination. Laut Protokoll."""
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
import numpy as np
import pandas as pd
from hybrid import research as R, runner

ROOT = Path(__file__).resolve().parents[1]
pd.set_option("display.width", 260, "display.max_columns", 60)
AUS = 9.0
FEN = {"D1": (None, R.D1_ENDE), "D2": (R.D1_ENDE, R.SPLIT), "Entwicklung": (None, R.SPLIT), "Pruefung": (R.SPLIT, None),
       "Gesamt": (None, None)}
SP = ["G", "F", "R", "handel", "N", "dd_mit", "vol_tag", "bp_je_umsatz", "trades", "halte_h", "sharpe", "jahr_N"]
HEBEL = (5, 4, 3, 2.5, 2, 1.5, 1, 0.75, 0.5, 0.4, 0.35, 0.3, 0.25, 0.2, 0.15, 0.1)
r4 = json.loads((ROOT / "reports/suche_runde4.json").read_text())
r5 = json.loads((ROOT / "reports/suche_runde5.json").read_text())


def gelistet(coins):
    _, fehlt = R.yubit_kosten(coins)
    return [c for c in coins if c not in fehlt]


G = {"A": gelistet(R.GRUPPE_A), "B": gelistet(R.GRUPPE_B), "C": gelistet(r4["gruppe_c"]), "D": gelistet(r5["gruppe_d"])}


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
out = {"gruppen": G}
stich = pd.read_csv(R.DATA / "processed/yubit_spannen_stichprobe.csv")
out["stichprobe"] = {"messungen": int(stich["zeit"].nunique()), "von": stich["zeit"].min(), "bis": stich["zeit"].max()}
M = {g: R.markt(c) for g, c in G.items()}
K = {g: R.yubit_kosten(c)[0] for g, c in G.items()}
out["kosten_bp"] = {g: {c: round(float(k) * 1e4, 3) for c, k in zip(G[g], K[g])} for g in G}
print("Stichprobe:", out["stichprobe"])
for g in G:
    print(f"Gruppe {g}: {len(G[g])} Coins, Slippage-Annahme Mittel {K[g].mean() * 1e4:.2f} bp, Median {np.median(K[g]) * 1e4:.2f} bp, max {K[g].max() * 1e4:.2f} bp")
AB = G["A"] + G["B"]
mAB = R.markt(AB)
kAB = np.concatenate([K["A"], K["B"]])

# ---------------------------------------------------------------- Teil 1: Kandidat mit echten Kosten
print("\n===== TEIL 1: Kandidat (14-Tage-Trend) mit echten Yubit-Kosten")
t1 = {}
for name, m, k in (("A", M["A"], K["A"]), ("A+B", mAB, kAB)):
    w = R.auf_raster(m, R.variante(m, "basis"))
    h, l = hebel_lauf(m, w, k)
    alt = fen(R.lauf(m, w, hebel=h, taker=True, slip=0.0005))
    t1[name] = {"hebel": h, **fen(l), "alt_5bp": alt, "stress_2x": fen(R.lauf(m, w, hebel=h, taker=True, slip=2 * k)),
                "jahre": {str(i): x for i, x in jahre(l).round(5).T.to_dict().items()}}
    print(f"-- Gruppe {name}, Hebel {h} mit Tageslimit, echte Kosten:"); print(tab(fen(l)))
    print("   mit altem Wert 0,05 %: Prüfung N", round(alt["Pruefung"]["N"], 4), "| doppelte Kosten: Prüfung N",
          round(t1[name]["stress_2x"]["Pruefung"]["N"], 4))
out["teil1"] = t1

# ---------------------------------------------------------------- Teil 2: Rangfolge
print("\n===== TEIL 2: Rangfolge marktneutral, Entwicklung Gruppe A (Hebel 1, ohne Tageslimit)")
KONFIG = [(L, T) for L in (72, 168, 336) for T in (4, 24)]
zeilen, W = [], {}
for L, T in KONFIG:
    n = f"rang_L{L}_T{T}"
    W[n] = R.auf_raster(M["A"], R.rangfolge(M["A"], L, T))
    d = fen(R.lauf(M["A"], W[n], taker=True, slip=K["A"], day_limit=AUS), ("D1", "D2", "Entwicklung"))
    zeilen.append({"name": n, "L": L, "T": T, "bestanden": all(d[f]["G"] > 0 and d[f]["N"] > 0 for f in ("D1", "D2")),
                   "score": min(d["D1"]["sharpe"], d["D2"]["sharpe"]),
                   **{f"{f}_{k}": d[f][k] for f in ("D1", "D2") for k in ("G", "N", "sharpe", "bp_je_umsatz")},
                   **{k: d["Entwicklung"][k] for k in ("G", "F", "N", "dd_mit", "vol_tag", "sharpe", "jahr_N")}})
t = pd.DataFrame(zeilen)
t.to_csv(ROOT / "reports/suche_runde6_stufe1.csv", index=False)
print(t.round(3).to_string())
out["teil2"] = {"stufe1": zeilen}
fin = t[t["bestanden"]].sort_values("score", ascending=False).head(1)
finalist, ok_alle = (fin.iloc[0]["name"] if len(fin) else None), False
print("Finalist:", finalist)
if finalist:
    L, T = int(fin.iloc[0]["L"]), int(fin.iloc[0]["T"])
    e = out["teil2"]["finalist"] = {"name": finalist, "L": L, "T": T, "stufen": {}}
    wA = W[finalist]
    s2 = fen(R.lauf(M["A"], wA, taker=True, slip=2 * K["A"], day_limit=AUS), ("D1", "D2"))
    ok2 = all(x["N"] > 0 for x in s2.values())
    e["stufen"]["2_stress"] = {"ok": ok2, **s2}
    print(f"Stufe 2 doppelte Kosten: {'bestanden' if ok2 else 'DURCHGEFALLEN'}"); print(tab(s2))
    if ok2:
        s3, ok3 = {}, True
        for g in ("A", "B", "C", "D"):
            w = wA if g == "A" else R.auf_raster(M[g], R.rangfolge(M[g], L, T))
            s3[g] = fen(R.lauf(M[g], w, taker=True, slip=K[g], day_limit=AUS))
            print(f"-- Gruppe {g} ({len(G[g])} Coins):"); print(tab(s3[g]))
        ok3 = (s3["A"]["Pruefung"]["G"] > 0 and s3["A"]["Pruefung"]["N"] > 0
               and all(s3[g][f]["N"] > 0 for g in ("B", "C") for f in ("Entwicklung", "Pruefung")))
        e["stufen"]["3_bestaetigung"] = {"ok": ok3, **s3}
        print(f"Stufe 3 Bestätigung (A Prüfzeitraum, B und C): {'bestanden' if ok3 else 'DURCHGEFALLEN'}")
        if ok3:
            rng = np.random.default_rng(7)
            echt = s3["A"]["Gesamt"]["N"]
            Tn = wA.shape[1]
            z = [R.sicht(R.lauf(M["A"], np.ascontiguousarray(np.roll(wA, int(rng.integers(288 * 30, Tn - 288 * 30)), axis=1)),
                                taker=True, slip=K["A"], day_limit=AUS), None, None)["N"] for _ in range(200)]
            pct = float((np.array(z) < echt).mean() * 100)
            ok4 = pct >= 90
            e["stufen"]["4_zufall"] = {"ok": ok4, "perzentil": pct, "echt": echt, "median": float(np.median(z)),
                                       "p90": float(np.percentile(z, 90)), "max": float(np.max(z))}
            print(f"Stufe 4 Zufallstest: Perzentil {pct:.1f} ({'bestanden' if ok4 else 'DURCHGEFALLEN'}); echt {echt:.3f}, "
                  f"Median {np.median(z):.3f}, 90 % {np.percentile(z, 90):.3f}")
            if ok4:
                h, lh = hebel_lauf(M["A"], wA, K["A"])
                if h is None:
                    e["stufen"]["5_hebel"] = {"ok": False}
                    print("Stufe 5: DURCHGEFALLEN (kein Hebel hält 10 %)")
                else:
                    h5 = fen(lh)
                    p = h5["Pruefung"]
                    ok5 = p["dd_mit"] < 0.15 and p["G"] > 0 and p["N"] > 0
                    e["stufen"]["5_hebel"] = {"ok": ok5, "hebel": h, **h5, "orders": runner.order_statistik(lh),
                                              "jahre": {str(i): x for i, x in jahre(lh).round(5).T.to_dict().items()}}
                    print(f"Stufe 5 Hebel {h} mit Tageslimit: {'bestanden' if ok5 else 'DURCHGEFALLEN'}"); print(tab(h5))
                    print(jahre(lh).round(3).to_string()); print("  ", runner.order_statistik(lh))
                    ok_alle = ok5
    e["alle_stufen"] = ok_alle

# ---------------------------------------------------------------- Teil 3: Kombination auf A+B
kombi_staerker = False
if finalist:
    print("\n===== TEIL 3: Kombination Kandidat + Finalist auf A+B (20 Coins), echte Kosten")
    L, T = out["teil2"]["finalist"]["L"], out["teil2"]["finalist"]["T"]
    w_t = R.auf_raster(mAB, R.variante(mAB, "basis"))
    w_r = R.auf_raster(mAB, R.rangfolge(mAB, L, T))
    t3 = {}
    for name, w in (("trend", w_t), ("rangfolge", w_r), ("kombination", 0.5 * w_t + 0.5 * w_r)):
        h, l = hebel_lauf(mAB, w, kAB)
        if h is None:
            t3[name] = {"hebel": None}
            print(f"-- {name}: kein Hebel hält 10 %")
            continue
        t3[name] = {"hebel": h, **fen(l), "stress_2x": fen(R.lauf(mAB, w, hebel=h, taker=True, slip=2 * kAB)),
                    "alt_5bp": fen(R.lauf(mAB, w, hebel=h, taker=True, slip=0.0005)),
                    "orders": runner.order_statistik(l), "jahre": {str(i): x for i, x in jahre(l).round(5).T.to_dict().items()}}
        print(f"-- {name}: Hebel {h} mit Tageslimit"); print(tab(fen(l)))
        print("   doppelte Kosten: Prüfung N", round(t3[name]["stress_2x"]["Pruefung"]["N"], 4),
              "| alt 0,05 %: Prüfung N", round(t3[name]["alt_5bp"]["Pruefung"]["N"], 4))
        if name == "kombination":
            print(jahre(l).round(3).to_string())
    out["teil3"] = t3
    if t3["kombination"].get("hebel") and t3["trend"].get("hebel"):
        kombi_staerker = all(t3["kombination"][f]["N"] > t3["trend"][f]["N"] for f in ("Entwicklung", "Pruefung"))
    out["tage"] = {"Pruefung": (mAB.index[-1] - pd.Timestamp(R.SPLIT)).days + 1, "Gesamt": (mAB.index[-1] - mAB.index[0]).days + 1}
out["kombination_staerker"] = bool(kombi_staerker)
out["staerkerer_edge"] = bool(ok_alle or kombi_staerker)
print("\nFinalist besteht alle Stufen:", ok_alle, "| Kombination stärker als Kandidat:", kombi_staerker,
      "| STÄRKERER EDGE:", out["staerkerer_edge"])
(ROOT / "reports/suche_runde6.json").write_text(json.dumps(out, indent=1, default=float))
print(f"fertig in {time.time() - t0:.0f} s")
