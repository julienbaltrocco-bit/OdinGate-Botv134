"""QD-Audit: White's Reality Check pruefen. (a) R21 und R24 nachrechnen, (b) eigene Umsetzung gegen mutationen.reality_check,
(c) Groessentest unter der Nullhypothese, (d) Reality Check fuer die Auswahl des Kandidaten in Runde 3 (nur Entwicklung)."""
import sys, time, json, math
sys.path.insert(0, "/home/user/OdinGate-Botv134/swing-hybrid/src")
import numpy as np, pandas as pd
from hybrid import research as R, runner, mutationen as M, tpsl

t0 = time.time()
ROOT = "/home/user/OdinGate-Botv134/swing-hybrid/reports/"
A = R.GRUPPE_A; K = R.yubit_kosten(A)[0]; SPLIT = pd.Timestamp(R.SPLIT)
m = R.markt(A, vor=True)
def tage(fn, **kw):
    kw = {"taker": True, "slip": K, "day_limit": 9.0, **kw}
    return R.lauf(m, R.auf_raster(m, fn(m)), **kw).daily_pnl(runner.MIT).sum(axis=1)
def sh(x): return float(x.mean() / x.std() * np.sqrt(365)) if x.std() > 0 else 0.0
out = {}

def eigen_rc(diff, ziehungen=5000, block=20, seed=99, studentisiert=False):
    """Unabhaengige Umsetzung: stationaerer Bootstrap, vektorisiert; optional studentisiert (Hansen-Art, ohne Schwellenkorrektur)."""
    rng = np.random.default_rng(seed); n, k = diff.shape
    mu = diff.mean(axis=0)
    neu = rng.random((ziehungen, n)) < 1.0 / block; neu[:, 0] = True
    start = rng.integers(0, n, (ziehungen, n)); idx = np.empty((ziehungen, n), dtype=np.int64)
    pos = start[:, 0].copy(); idx[:, 0] = pos
    for i in range(1, n):
        pos = np.where(neu[:, i], start[:, i], (pos + 1) % n); idx[:, i] = pos
    bm = np.empty((ziehungen, k))
    for j in range(k):
        bm[:, j] = diff[:, j][idx].mean(axis=1)
    z = bm - mu
    if studentisiert:
        s = z.std(axis=0); stat = (mu / s).max(); mx = (z / s).max(axis=1)
        return float((mx >= stat).mean())
    mx = z.max(axis=1)
    return mu, float(np.percentile(mx, 95)), float((mx >= mu.max()).mean())

print("=== (a) Runde 21 und 24 nachgerechnet")
basis = tage(M.basis); bd = basis[basis.index < SPLIT]
for runde, varianten, datei in (("21", M.VARIANTEN, "suche_runde21.json"), ("24", tpsl.VARIANTEN, "suche_runde24.json")):
    ref = json.load(open(ROOT + datei))
    diffs, namen, zeilen = [], [], []
    for n, fn in varianten.items():
        x = tage(fn); xd = x[x.index < SPLIT]; f = float(bd.std() / xd.std())
        d1, d2 = xd[xd.index < pd.Timestamp(R.D1_ENDE)], xd[xd.index >= pd.Timestamp(R.D1_ENDE)]
        diffs.append((f * xd - bd).to_numpy()); namen.append(n)
        r = ref["varianten"][n]
        zeilen.append((n, sh(d1), r["D1"]["sharpe"], sh(d2), r["D2"]["sharpe"], sh(xd), r["Entwicklung"]["sharpe"], f, r["faktor"]))
    D = np.column_stack(diffs)
    mittel, schwelle, p = M.reality_check(D)
    mu2, schw2, p2 = eigen_rc(D, seed=5)
    p_stud = eigen_rc(D, seed=5, studentisiert=True)
    maxabw = max(max(abs(z[1] - z[2]), abs(z[3] - z[4]), abs(z[5] - z[6]), abs(z[7] - z[8])) for z in zeilen)
    beste = namen[int(np.argmax(mittel))]
    print(f"Runde {runde}: Kandidat Sharpe D1/D2/Entw {sh(bd[bd.index < pd.Timestamp(R.D1_ENDE)]):.4f}/{sh(bd[bd.index >= pd.Timestamp(R.D1_ENDE)]):.4f}/{sh(bd):.4f}; "
          f"max. Abweichung Sharpe/Faktor gegen JSON {maxabw:.2e}")
    print(f"   mutationen.reality_check: Schwelle {schwelle:.10f} (JSON {ref['reality_check']['schwelle_95']:.10f}), p {p:.4f} (JSON {ref['reality_check']['p_beste']:.4f}), "
          f"beste Variante {beste} mit Vorsprung {mittel.max()*365:+.4f}/Jahr, Schwelle/Jahr {schwelle*365:.4f}")
    print(f"   eigene Umsetzung (anderer Zufallsstart): Schwelle/Jahr {schw2*365:.4f}, p {p2:.4f}; studentisierte Variante p {p_stud:.4f}")
    print("   Streuung der Tagesdifferenzen je Variante (pro Jahr):", {n: round(float(D[:, i].std() * math.sqrt(365)), 3) for i, n in enumerate(namen)})
    out[f"runde{runde}"] = {"schwelle": schwelle, "p": p, "json_schwelle": ref["reality_check"]["schwelle_95"], "json_p": ref["reality_check"]["p_beste"], "beste": beste,
                            "eigen_p": p2, "eigen_schwelle": schw2, "p_studentisiert": p_stud, "max_abweichung": maxabw}

# Der Groessentest steht in reality2.py (sauberer Aufbau: wahre Mittel = 0, ohne nachtraegliches Ersetzen des Stichprobenmittels).

print("\n=== (d) Auswahl in Runde 3: 10 Trend-Einstellungen, Entwicklung, sofortige Ausfuehrung, 5 bp, ohne Tageslimit; Massstab null")
KONFIG = ([("tsmom", dict(L=L, bias=b)) for L in (48, 96, 168, 336) for b in (False, True)] + [("ensemble", dict(bias=b)) for b in (False, True)])
sp, nm = [], []
for fam, p in KONFIG:
    x = tage(lambda mm: R.FAMILIEN[fam](mm, **p), slip=0.0005)
    xd = x[x.index < SPLIT]; sp.append(xd.to_numpy()); nm.append(fam + "_" + "_".join(f"{a}{b}" for a, b in p.items()))
X = np.column_stack(sp)
# auf gleiche Schwankung bringen (wie in Runde 21), damit das Mittel dem Sharpe entspricht
Xs = X / X.std(axis=0) * X[:, nm.index("tsmom_L336_biasFalse")].std()
for bez, mat in (("Rohertrag", X), ("gleiche Schwankung", Xs)):
    mittel, schwelle, p = M.reality_check(mat, block=20, seed=3)
    print(f"{bez}: bestes Tagesmittel {nm[int(np.argmax(mittel))]} = {mittel.max()*365:+.3f}/Jahr; 95-%-Schwelle des groessten Zufallswerts {schwelle*365:.3f}/Jahr; p-Wert der besten von 10: {p:.4f}")
    out[f"runde3_rc_{bez}"] = {"beste": nm[int(np.argmax(mittel))], "mittel_jahr": float(mittel.max() * 365), "schwelle_jahr": schwelle * 365, "p": p}
print("Sharpe je Einstellung (Entwicklung):", {n: round(sh(pd.Series(X[:, i])), 3) for i, n in enumerate(nm)})
x336 = X[:, nm.index("tsmom_L336_biasFalse")]
_, _, p1 = M.reality_check(x336[:, None], block=20, seed=3)
print(f"zum Vergleich: p-Wert des Kandidaten allein, ohne Auswahl-Korrektur: {p1:.4f}")
out["runde3_p_allein"] = p1
json.dump(out, open("/home/user/OdinGate-Botv134/swing-hybrid/reports/audit/evidence/QD/reality_check.json", "w"), indent=1, default=float)
print(f"\nfertig nach {time.time() - t0:.0f} s")
