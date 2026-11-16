"""QD-Audit: (1) sauberer Groessentest fuer mutationen.reality_check, (2) Auswahl-Korrektur fuer den Kandidaten aus Runde 3
mit White (Projektfunktion) und Hansens SPA (eigene Umsetzung), nur Entwicklungszeitraum."""
import sys, time, json, math
sys.path.insert(0, "/home/user/OdinGate-Botv134/swing-hybrid/src")
import numpy as np, pandas as pd
from hybrid import research as R, runner, mutationen as M

t0 = time.time(); out = {}
print("=== (1) Groessentest: wahre Mittel = 0, k Spalten mit gemeinsamer Komponente und ungleicher Streuung, AR(1) = 0,1; n = 1325")
for k, rep in ((14, 300), (11, 300)):
    rng = np.random.default_rng(100 + k); n = 1325; abl = 0; ps = []
    for r in range(rep):
        e = 0.6 * rng.standard_normal(n)[:, None] + 0.8 * rng.standard_normal((n, k)) * rng.uniform(0.3, 2.0, k)
        x = np.empty_like(e); x[0] = e[0]
        for i in range(1, n): x[i] = 0.1 * x[i - 1] + e[i]
        mittel, schwelle, p = M.reality_check(x, ziehungen=500, block=20, seed=r)
        abl += (mittel.max() > schwelle); ps.append(p)
    se = math.sqrt(0.05 * 0.95 / rep)
    print(f"k={k}: Ablehnungsquote {abl/rep:.3f} (Soll 0,05 +- {2*se:.3f}); mittlerer p-Wert {np.mean(ps):.3f}; Anteil p<0,10: {(np.array(ps) < 0.10).mean():.3f}")
    out[f"groesse_k{k}"] = {"ablehnung": abl / rep, "p_mittel": float(np.mean(ps)), "p_lt_10": float((np.array(ps) < 0.10).mean()), "rep": rep}
print("Trennschaerfe: eine von 14 Spalten mit wahrem Vorsprung von 0,12 Standardabweichungen je Tag (deutlich), sonst wie oben")
rng = np.random.default_rng(7); n, k, rep, tr = 1325, 14, 100, 0
for r in range(rep):
    x = 0.6 * rng.standard_normal(n)[:, None] + 0.8 * rng.standard_normal((n, k)); x[:, 3] += 0.12
    mittel, schwelle, p = M.reality_check(x, ziehungen=500, block=20, seed=r); tr += (mittel[3] > schwelle)
print(f"   erkannt in {tr/rep:.2f} der Faelle"); out["trennschaerfe"] = tr / rep

def spa(X, ziehungen=5000, block=20, seed=3):
    """Hansen (2005) SPA, konsistente Variante, stationaerer Bootstrap. Gibt (p_SPA, p_White_studentisiert) zurueck."""
    rng = np.random.default_rng(seed); n, k = X.shape; mu = X.mean(axis=0)
    neu = rng.random((ziehungen, n)) < 1.0 / block; neu[:, 0] = True
    start = rng.integers(0, n, (ziehungen, n)); idx = np.empty((ziehungen, n), dtype=np.int64)
    pos = start[:, 0].copy(); idx[:, 0] = pos
    for i in range(1, n):
        pos = np.where(neu[:, i], start[:, i], (pos + 1) % n); idx[:, i] = pos
    bm = np.column_stack([X[:, j][idx].mean(axis=1) for j in range(k)])
    s = (bm - mu).std(axis=0)                                   # Standardfehler des Mittels aus dem Bootstrap
    T = max(0.0, (mu / s).max())
    g = np.where(mu / s >= -math.sqrt(2 * math.log(math.log(n))), mu, 0.0)   # schlechte Modelle werden nicht auf null zentriert
    z_c = ((bm - g) / s).max(axis=1); z_u = ((bm - mu) / s).max(axis=1)
    return float((np.maximum(z_c, 0) >= T).mean()), float((z_u >= T).mean())

print("\n=== (2) Auswahl in Runde 3: 10 Trend-Einstellungen, Entwicklung 15.08.2021-31.03.2025, sofortige Ausfuehrung, ohne Tageslimit; Massstab null")
A = R.GRUPPE_A; K = R.yubit_kosten(A)[0]; SPLIT = pd.Timestamp(R.SPLIT)
m = R.markt(A, vor=True)
KONFIG = ([("tsmom", dict(L=L, bias=b)) for L in (48, 96, 168, 336) for b in (False, True)] + [("ensemble", dict(bias=b)) for b in (False, True)])
for bez, slip in (("5 bp (Stand der Auswahl in Runde 3)", 0.0005), ("Yubit-Kosten (ab Runde 6)", K)):
    sp, nm = [], []
    for fam, p in KONFIG:
        x = R.lauf(m, R.auf_raster(m, R.FAMILIEN[fam](m, **p)), taker=True, slip=slip, day_limit=9.0).daily_pnl(runner.MIT).sum(axis=1)
        sp.append(x[x.index < SPLIT].to_numpy()); nm.append(fam + "_" + "_".join(f"{a}{b}" for a, b in p.items()))
    X = np.column_stack(sp); i336 = nm.index("tsmom_L336_biasFalse")
    mittel, schwelle, p_w = M.reality_check(X, block=20, seed=3)
    _, _, p_allein = M.reality_check(X[:, [i336]], block=20, seed=3)
    p_spa, p_ws = spa(X)
    sh = X.mean(axis=0) / X.std(axis=0) * math.sqrt(365)
    print(f"{bez}: beste = {nm[int(np.argmax(mittel))]} ({mittel.max()*365:+.3f}/Jahr, Sharpe {sh[i336]:.3f}); Sharpe aller 10: {np.round(sh, 2).tolist()}")
    print(f"   p allein (ohne Korrektur) {p_allein:.4f} | White ueber 10 (Projektfunktion) {p_w:.4f} | White studentisiert {p_ws:.4f} | Hansen SPA {p_spa:.4f}")
    out[bez] = {"p_allein": p_allein, "p_white": p_w, "p_white_stud": p_ws, "p_spa": p_spa, "sharpe": dict(zip(nm, sh.tolist()))}
json.dump(out, open("/home/user/OdinGate-Botv134/swing-hybrid/reports/audit/evidence/QD/reality_check_2.json", "w"), indent=1, default=float)
print(f"\nfertig nach {time.time() - t0:.0f} s")
