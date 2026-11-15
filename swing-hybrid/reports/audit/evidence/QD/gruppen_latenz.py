"""QD-Audit: (a) Kandidat je Coin-Gruppe nachrechnen (Runde 4, 5, gesamt_60, Runde 22), (b) Empfindlichkeit gegen verzoegerte Ausfuehrung."""
import sys, time, json
sys.path.insert(0, "/home/user/OdinGate-Botv134/swing-hybrid/src")
import numpy as np, pandas as pd
from hybrid import research as R, runner, mutationen as M
from hybrid.config import DATA

t0 = time.time(); ROOT = "/home/user/OdinGate-Botv134/swing-hybrid/reports/"; out = {}
r4 = json.load(open(ROOT + "suche_runde4.json")); r5 = json.load(open(ROOT + "suche_runde5.json")); g60 = json.load(open(ROOT + "gesamt_60.json"))
r6 = json.load(open(ROOT + "suche_runde6.json")); r22 = json.load(open(ROOT + "suche_runde22.json"))
SPLIT = pd.Timestamp(R.SPLIT)
def sh(x): return float(x.mean() / x.std() * np.sqrt(365)) if x.std() > 0 else 0.0
print("=== (a) Kandidat je Gruppe, Hebel 1, ohne Tageslimit, 5 bp (gesamt_60.json) und Yubit-Kosten, nur bei Yubit gelistete Coins (suche_runde22.json)")
G5 = {"A": R.GRUPPE_A, "B": R.GRUPPE_B, "C": r4["gruppe_c"], "D": r5["gruppe_d"]}
for g, coins in G5.items():
    m = R.markt(coins); w = R.auf_raster(m, R.variante(m, "basis"))
    l = R.lauf(m, w, taker=True, day_limit=9.0)
    e, p = R.sicht(l, None, R.SPLIT), R.sicht(l, R.SPLIT, None)
    ref = g60["gruppen"][g]
    print(f"Gruppe {g} ({len(coins)} Coins) 5 bp: Entwicklung N {e['N']:+.4f} (JSON {ref['Entwicklung']['N']:+.4f}), Pruefzeitraum N {p['N']:+.4f} (JSON {ref['Pruefung']['N']:+.4f}), Sharpe {e['sharpe']:.3f}/{p['sharpe']:.3f}")
    out[f"5bp_{g}"] = {"entw_N": e["N"], "pruef_N": p["N"], "json_entw_N": ref["Entwicklung"]["N"], "json_pruef_N": ref["Pruefung"]["N"]}
    cy = r6["gruppen"][g]
    my = R.markt(cy, vor=True); wy = R.auf_raster(my, M.basis(my))
    ty = R.lauf(my, wy, taker=True, slip=R.yubit_kosten(cy)[0], day_limit=9.0).daily_pnl(runner.MIT).sum(axis=1)
    py = ty[ty.index >= SPLIT]; ey = ty[ty.index < SPLIT]
    print(f"         ({len(cy)} bei Yubit) Yubit-Kosten: Sharpe Entwicklung {sh(ey):.3f}, Pruefzeitraum {sh(py):.4f} (JSON Runde 22: {r22['gruppen_pruefzeitraum'][g]['kandidat']:.4f}); Ertrag/Jahr {ey.mean()*365:+.3f} / {py.mean()*365:+.3f}")
    out[f"yubit_{g}"] = {"sharpe_entw": sh(ey), "sharpe_pruef": sh(py), "json_sharpe_pruef": r22["gruppen_pruefzeitraum"][g]["kandidat"], "jahr_entw": float(ey.mean() * 365), "jahr_pruef": float(py.mean() * 365)}
    del m, my
alle = R.GRUPPE_A + R.GRUPPE_B + r4["gruppe_c"]
cv = [c for c in alle if (DATA / "candles/5m_vor" / f"{c}USDT.parquet").exists()]
mv = R.markt(cv, R.VOR_START, R.VOR_ENDE, vor=True)
sv = R.sicht(R.lauf(mv, R.auf_raster(mv, R.tsmom(mv, 336)), taker=True, day_limit=9.0), None, None)
print(f"Vorperiode 02/2020-08/2021, {len(cv)} Coins, 5 bp: N {sv['N']:+.4f} (JSON {r4['vorperiode']['alle']['N']:+.4f}), Sharpe {sv['sharpe']:.3f}")
out["vorperiode_alle"] = {"N": sv["N"], "json_N": r4["vorperiode"]["alle"]["N"], "coins": len(cv)}
del mv

print("\n=== (b) Verzoegerte Ausfuehrung: Gruppe A, Hebel 1, Yubit-Kosten, ohne Tageslimit; Gewichte um k Kerzen (je 5 Minuten) spaeter")
m = R.markt(R.GRUPPE_A, vor=True); w = R.auf_raster(m, M.basis(m)); K = R.yubit_kosten(R.GRUPPE_A)[0]
for k in (0, 1, 2, 3, 6, 12):
    ws = w.copy()
    if k: ws[:, k:] = w[:, :-k]; ws[:, :k] = 0.0
    tg = R.lauf(m, ws, taker=True, slip=K, day_limit=9.0).daily_pnl(runner.MIT).sum(axis=1)
    e, p = tg[tg.index < SPLIT], tg[tg.index >= SPLIT]
    print(f"Verzoegerung {5*k:3d} Minuten: Entwicklung {e.mean()*365:+.3f}/Jahr, Sharpe {sh(e):.3f} | Pruefzeitraum {p.mean()*365:+.3f}/Jahr, Sharpe {sh(p):.3f}")
    out[f"latenz_{5*k}min"] = {"entw_jahr": float(e.mean() * 365), "entw_sharpe": sh(e), "pruef_jahr": float(p.mean() * 365), "pruef_sharpe": sh(p)}
json.dump(out, open("/home/user/OdinGate-Botv134/swing-hybrid/reports/audit/evidence/QD/gruppen_latenz.json", "w"), indent=1, default=float)
print(f"\nfertig nach {time.time() - t0:.0f} s")
