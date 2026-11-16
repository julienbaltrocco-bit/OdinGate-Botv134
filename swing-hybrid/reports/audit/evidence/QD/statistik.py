"""QD-Audit: statistische Belastbarkeit des Kandidaten (nur lesend)."""
import sys, time, json, math
sys.path.insert(0, "/home/user/OdinGate-Botv134/swing-hybrid/src")
import numpy as np, pandas as pd
from hybrid import research as R, runner, mutationen as M

t0 = time.time()
A = R.GRUPPE_A
K = R.yubit_kosten(A)[0]
m = R.markt(A, vor=True)
w = R.auf_raster(m, M.basis(m))
l = R.lauf(m, w, taker=True, slip=K, day_limit=9.0)
tg = l.daily_pnl(runner.MIT).sum(axis=1)
to = l.daily_pnl(runner.OHNE).sum(axis=1)
SPLIT = pd.Timestamp(R.SPLIT)
dev, pru = tg[tg.index < SPLIT], tg[tg.index >= SPLIT]
out = {}

def sh(x): return float(x.mean() / x.std() * np.sqrt(365)) if x.std() > 0 else 0.0

def stat_boot(x, n_draw=10000, block=20, seed=1):
    """Stationaerer Bootstrap (Politis/Romano), vektorisiert. Gibt Matrix der Indizes zurueck."""
    rng = np.random.default_rng(seed); n = len(x)
    neu = rng.random((n_draw, n)) < 1.0 / block; neu[:, 0] = True
    start = rng.integers(0, n, (n_draw, n))
    idx = np.empty((n_draw, n), dtype=np.int64)
    pos = start[:, 0].copy(); idx[:, 0] = pos
    for i in range(1, n):
        pos = np.where(neu[:, i], start[:, i], (pos + 1) % n); idx[:, i] = pos
    return idx

print("=== 1. Punkt- und Intervallschaetzung (Hebel 1, Yubit-Kosten mit 85 % Rebate, ohne Tageslimit, Gruppe A)")
for nm, x in (("Entwicklung", dev), ("Pruefzeitraum", pru), ("Pruefzeitraum ohne Rebate", to[to.index >= SPLIT]), ("Entwicklung ohne Rebate", to[to.index < SPLIT])):
    xv = x.to_numpy(); n = len(xv); jahre = n / 365
    t = xv.mean() / (xv.std(ddof=1) / math.sqrt(n))
    ac1 = float(pd.Series(xv).autocorr(1))
    idx = stat_boot(xv, 10000, 20, 7)
    b = xv[idx]
    bm = b.mean(axis=1) * 365; bs = b.mean(axis=1) / b.std(axis=1, ddof=1) * np.sqrt(365)
    e = {"tage": n, "ertrag_jahr": float(xv.mean() * 365), "sharpe": sh(x), "t_wert": float(t), "t_naeherung_sharpe_mal_wurzel_jahre": float(sh(x) * math.sqrt(jahre)),
         "autokorr_lag1": ac1, "bootstrap_ertrag_jahr_5_95": [float(np.percentile(bm, 5)), float(np.percentile(bm, 95))],
         "bootstrap_sharpe_5_95": [float(np.percentile(bs, 5)), float(np.percentile(bs, 95))], "bootstrap_anteil_mittel_le_0": float((bm <= 0).mean())}
    out[nm] = e
    print(f"{nm:28s} Tage {n}  Ertrag/Jahr {e['ertrag_jahr']:+.3f}  Sharpe {e['sharpe']:.3f}  t {t:.2f}  AK1 {ac1:+.3f}  "
          f"90-%-Band Ertrag/Jahr [{e['bootstrap_ertrag_jahr_5_95'][0]:+.3f}, {e['bootstrap_ertrag_jahr_5_95'][1]:+.3f}]  "
          f"Sharpe [{e['bootstrap_sharpe_5_95'][0]:+.2f}, {e['bootstrap_sharpe_5_95'][1]:+.2f}]  Anteil Ziehungen mit Mittel <= 0: {e['bootstrap_anteil_mittel_le_0']:.3f}")

print("\n=== 2. Unterschied Entwicklung gegen Pruefzeitraum")
d = dev.mean() - pru.mean(); se = math.sqrt(dev.var(ddof=1) / len(dev) + pru.var(ddof=1) / len(pru))
print(f"Tagesmittel Entwicklung {dev.mean()*365:+.3f}/Jahr, Pruefzeitraum {pru.mean()*365:+.3f}/Jahr; Differenz t = {d/se:.2f}")
out["differenz_t"] = float(d / se)

print("\n=== 3. Zufallstest des Projekts (Signal zeitlich verschoben), nur Pruefzeitraum, Yubit-Kosten, 200 Verschiebungen, seed 11")
rng = np.random.default_rng(11); T = w.shape[1]
echt_p = float(pru.sum()); echt_d = float(dev.sum()); zp, zd = [], []
for _ in range(200):
    k = int(rng.integers(288 * 30, T - 288 * 30))
    x = R.lauf(m, np.ascontiguousarray(np.roll(w, k, axis=1)), taker=True, slip=K, day_limit=9.0).daily_pnl(runner.MIT).sum(axis=1)
    zp.append(float(x[x.index >= SPLIT].sum())); zd.append(float(x[x.index < SPLIT].sum()))
zp, zd = np.array(zp), np.array(zd)
out["zufall_verschoben"] = {"pruef_perzentil": float((zp < echt_p).mean() * 100), "pruef_echt": echt_p, "pruef_median": float(np.median(zp)), "pruef_p90": float(np.percentile(zp, 90)),
                            "entw_perzentil": float((zd < echt_d).mean() * 100), "entw_echt": echt_d, "entw_median": float(np.median(zd)), "entw_p90": float(np.percentile(zd, 90))}
print(json.dumps(out["zufall_verschoben"], indent=None))

print("\n=== 4. Einbruch: Konventionen und Hebel 3")
eq = l.equity(runner.MIT)
i0 = int(m.index.searchsorted(SPLIT))
def abs_dd(e): return float((np.maximum.accumulate(e) - e).max())
for nm, e in (("Entwicklung", eq[:i0]), ("Pruefzeitraum", eq[i0:] - eq[i0 - 1]), ("Gesamt", eq)):
    konto = 1 + e; sp = np.maximum.accumulate(np.maximum(konto, 1.0)); rel = float(((sp - konto) / sp).max())
    a = abs_dd(np.concatenate([[0.0], e]))
    print(f"{nm:14s} Hebel 1: Einbruch relativ zum Hoechststand {rel:.3f}; groesster Rueckgang in Einheiten des Startkapitals {a:.3f}; dasselbe bei Hebel 3: {3*a:.3f}")
    out[f"einbruch_{nm}"] = {"relativ_hebel1": rel, "absolut_hebel1": a, "absolut_hebel3": 3 * a}
l3 = R.lauf(m, w, hebel=3.0, taker=True, slip=K, day_limit=9.0)
for nm, (a, b) in (("Entwicklung", (None, R.SPLIT)), ("Pruefzeitraum", (R.SPLIT, None))):
    s = R.sicht(l3, a, b)
    print(f"Hebel 3, ohne Tageslimit (wie config_lauf.json), {nm}: N {s['N']:+.3f}, Einbruch relativ zum Hoechststand {s['dd_mit']:.3f}, Sharpe {s['sharpe']:.3f}")
    out[f"hebel3_{nm}"] = {"N": s["N"], "dd": s["dd_mit"], "sharpe": s["sharpe"]}
# Start an jedem Tag neu mit Hebel 3 (feste Positionsgroesse wie im Bot): wie oft faellt das Konto bis Ende/innerhalb 365 Tagen um >= 50 %, 75 %, 100 %?
cum = np.concatenate([[0.0], tg.cumsum().to_numpy()]); n = len(tg)
def anteil(grenze, horizont):
    treffer = 0; gesamt = 0
    for s0 in range(0, n - 30):
        e = min(n, s0 + horizont); pfad = cum[s0 + 1:e + 1] - cum[s0]
        gesamt += 1; treffer += (3 * pfad.min() <= -grenze)
    return treffer / gesamt
for g in (0.5, 0.75, 1.0):
    out[f"neustart_hebel3_verlust_{int(g*100)}"] = {"365_tage": anteil(g, 365), "bis_ende": anteil(g, 10**6)}
    print(f"Anteil der Starttage (Tagesschlusswerte, Hebel 3, feste Groesse), nach denen das Konto um >= {int(g*100)} % des Startkapitals faellt: "
          f"binnen 365 Tagen {out[f'neustart_hebel3_verlust_{int(g*100)}']['365_tage']:.3f}, bis Datenende {out[f'neustart_hebel3_verlust_{int(g*100)}']['bis_ende']:.3f}")
# schlechteste Tage/Wochen bei Hebel 1
print("Schlechtester Tag Hebel 1:", float(tg.min()), tg.idxmin().date(), "| schlechteste 7 Tage:", float(tg.rolling(7).sum().min()), "| schlechteste 30 Tage:", float(tg.rolling(30).sum().min()))
out["schlechtester_tag_hebel1"] = float(tg.min()); out["schlechteste_30_tage_hebel1"] = float(tg.rolling(30).sum().min())

print("\n=== 5. Korrelation der zehn Coins")
c = R._close(m).loc[R.START:]
rh = np.log(c).diff(); rd = np.log(c.resample("1D").last()).diff()
def mk(x):
    k = x.corr().to_numpy(); return float(k[np.triu_indices_from(k, 1)].mean())
pc = l.daily_pnl(runner.MIT)
for nm, a, b in (("gesamt", None, None), ("Entwicklung", None, SPLIT), ("ab 04/2025", SPLIT, None)):
    f = lambda x: x[(x.index >= (a or x.index[0])) & (x.index < (b or x.index[-1] + pd.Timedelta(days=1)))]
    e = {"stundenrenditen": mk(f(rh)), "tagesrenditen": mk(f(rd)), "tages_pnl_je_coin_strategie": mk(f(pc))}
    out[f"korrelation_{nm}"] = e
    print(f"mittlere paarweise Korrelation {nm:12s}: Stundenrenditen {e['stundenrenditen']:.3f}, Tagesrenditen {e['tagesrenditen']:.3f}, Tagesergebnis der Strategie je Coin {e['tages_pnl_je_coin_strategie']:.3f}")
# gleiche Richtung
ws = pd.DataFrame(w.T, index=m.index, columns=A).iloc[::12]
netto = ws.sum(axis=1).abs()
print("Anteil der Stunden, in denen mindestens 8 von 10 Positionen dieselbe Richtung haben:", float((netto >= 6).mean()), "| alle 10:", float((netto == 10).mean()))
out["gleiche_richtung_8von10"] = float((netto >= 6).mean()); out["gleiche_richtung_10von10"] = float((netto == 10).mean())
json.dump(out, open("/home/user/OdinGate-Botv134/swing-hybrid/reports/audit/evidence/QD/statistik_kandidat.json", "w"), indent=1, default=float)
print(f"\nfertig nach {time.time() - t0:.0f} s")
