"""QD-Audit: (a) tatsaechliches Marktengagement bei 'Einsatz 100 %' (Groesse wird beim Einstieg festgelegt),
(b) Neustart mit Hebel 3 und fester Groesse wie im Papier-Bot, (c) Kandidat auf den wegen Delisting ausgeschlossenen Coins."""
import sys, time, json
sys.path.insert(0, "/home/user/OdinGate-Botv134/swing-hybrid/src")
import numpy as np, pandas as pd
from hybrid import research as R, runner, mutationen as M

t0 = time.time()
A = R.GRUPPE_A; K = R.yubit_kosten(A)[0]; SPLIT = pd.Timestamp(R.SPLIT)
m = R.markt(A, vor=True)
w = R.auf_raster(m, M.basis(m))
out = {}

print("=== (a) Engagement: Summe |Stueckzahl x Kurs| in Einheiten des Startkapitals, Hebel 1")
T = w.shape[1]
expo = np.zeros(T); netto = np.zeros(T)
S = 1.0 / len(A)
for j in range(len(A)):
    tgt = w[j].copy(); tgt[0] = 0.0
    wechsel = np.flatnonzero(np.diff(np.concatenate([[0.0], tgt])) != 0)
    units = np.zeros(T)
    for a, b in zip(wechsel, list(wechsel[1:]) + [T]):
        if tgt[a] != 0.0:
            units[a:b] = tgt[a] * S / m.o[j, a]
    expo += np.abs(units) * m.c[j]; netto += units * m.c[j]
e = pd.Series(expo, index=m.index); nt = pd.Series(netto, index=m.index)
l1 = R.lauf(m, w, taker=True, slip=K, day_limit=9.0)
konto = 1.0 + pd.Series(l1.equity(runner.MIT), index=m.index)
rel = e / konto
for nm, x in (("gesamt", e), ("Entwicklung", e[e.index < SPLIT]), ("Pruefzeitraum", e[e.index >= SPLIT])):
    print(f"{nm:14s} Brutto-Engagement / Startkapital: Mittel {x.mean():.3f}, Median {x.median():.3f}, 95-%-Wert {x.quantile(0.95):.3f}, Maximum {x.max():.3f} am {x.idxmax()}")
    out[f"engagement_{nm}"] = {"mittel": float(x.mean()), "median": float(x.median()), "p95": float(x.quantile(0.95)), "max": float(x.max()), "max_zeit": str(x.idxmax())}
print(f"Brutto-Engagement / laufender Kontostand: Mittel {rel.mean():.3f}, Maximum {rel.max():.3f}")
tag = "2024-12-09"
print(f"Am {tag} 00:00: Brutto-Engagement {e[tag].iloc[0]:.3f}, Netto-Engagement {nt[tag].iloc[0]:.3f}, Kontostand {konto[tag].iloc[0]:.3f} (Startkapital = 1)")
tg = l1.daily_pnl(runner.MIT).sum(axis=1)
print("fuenf schlechteste Tage (Hebel 1, Anteil am Startkapital):", {str(k.date()): round(float(v), 4) for k, v in tg.nsmallest(5).items()})
out["schlechteste_tage"] = {str(k.date()): float(v) for k, v in tg.nsmallest(5).items()}
out["engagement_2024_12_09"] = {"brutto": float(e[tag].iloc[0]), "netto": float(nt[tag].iloc[0]), "konto": float(konto[tag].iloc[0])}

print("\n=== (b) Neustart mit Hebel 3, feste Groesse je Einstieg, ohne Tageslimit (wie config_lauf.json), Yubit-Kosten mit Rebate")
print("    Start an jedem 7. Tag; betrachtet wird der Kontoverlauf (5-Minuten-Werte) der folgenden 365 Tage bzw. bis Datenende")
starts = np.arange(0, T - 288 * 30, 288 * 7)
zeilen = []
for s0 in starts:
    ws = w.copy(); ws[:, :s0] = 0.0
    l = R.lauf(m, ws, hebel=3.0, taker=True, slip=K, day_limit=9.0)
    eq = l.equity(runner.MIT)
    e365 = eq[s0:min(T, s0 + 288 * 365)]
    zeilen.append((m.index[s0], float(e365.min()), float(eq[s0:].min()), float(e365[-1]), len(e365) / 288))
z = pd.DataFrame(zeilen, columns=["start", "tief_365", "tief_bis_ende", "stand_nach_365", "tage"]).set_index("start")
voll = z[z["tage"] >= 364.9]
for nm, d in (("alle Starttage", z), ("nur Starts mit vollen 365 Tagen", voll), ("Starts im Pruefzeitraum", z[z.index >= SPLIT]), ("Starts in der Entwicklung (volle 365 Tage)", voll[voll.index < SPLIT])):
    e_ = {"starts": int(len(d)), **{f"verlust_ge_{int(g*100)}": float((d["tief_365"] <= -g).mean()) for g in (0.3, 0.5, 0.75, 1.0)},
          "median_tief": float(d["tief_365"].median()), "median_stand_nach_365": float(d["stand_nach_365"].median())}
    out[f"neustart_{nm}"] = e_
    print(f"{nm:44s} n={e_['starts']:3d}  Anteil mit Kontotief <= -30 %: {e_['verlust_ge_30']:.2f}  <= -50 %: {e_['verlust_ge_50']:.2f}  <= -75 %: {e_['verlust_ge_75']:.2f}  <= -100 %: {e_['verlust_ge_100']:.2f}  "
          f"Median Tief {e_['median_tief']:+.2f}  Median Stand nach 365 Tagen {e_['median_stand_nach_365']:+.2f}")
z.round(4).to_csv("/home/user/OdinGate-Botv134/swing-hybrid/reports/audit/evidence/QD/neustart_hebel3.csv")

print("\n=== (c) Coins, die wegen unvollstaendiger Historie (Delisting) aus Gruppe D ausgeschlossen wurden; Kandidat unveraendert, 5 bp Slippage, Hebel 1, ohne Tageslimit")
AUS = ["LRC", "OCEAN", "STORJ", "ICX", "DENT"]
for c in AUS:
    d = R._lesen("5m", c, False)
    print(f"   {c}: Kerzen {d.index[0]} bis {d.index[-1]}")
mx = R.markt(AUS)
lx = R.lauf(mx, R.auf_raster(mx, R.variante(mx, "basis")), taker=True, day_limit=9.0)
r5 = json.load(open("/home/user/OdinGate-Botv134/swing-hybrid/reports/suche_runde5.json"))
for f, (a, b) in (("Entwicklung", (None, R.SPLIT)), ("Pruefung", (R.SPLIT, None))):
    s = R.sicht(lx, a, b); ref = r5["D"]["basis"][f]
    print(f"   {f}: ausgeschlossene 5 Coins N {s['N']:+.3f} (G {s['G']:+.3f}, Sharpe {s['sharpe']:.2f}) | Gruppe D laut suche_runde5.json N {ref['N']:+.3f} (G {ref['G']:+.3f}, Sharpe {ref['sharpe']:.2f})")
    out[f"delisted_{f}"] = {"N": s["N"], "G": s["G"], "sharpe": s["sharpe"], "gruppe_D_N": ref["N"]}
pc = lx.daily_pnl(runner.MIT)
print("   je Coin, Pruefzeitraum N:", pc[pc.index >= SPLIT].sum().round(3).to_dict(), "| Entwicklung N:", pc[pc.index < SPLIT].sum().round(3).to_dict())
json.dump(out, open("/home/user/OdinGate-Botv134/swing-hybrid/reports/audit/evidence/QD/hebel3_engagement_delisting.json", "w"), indent=1, default=float)
print(f"\nfertig nach {time.time() - t0:.0f} s")
