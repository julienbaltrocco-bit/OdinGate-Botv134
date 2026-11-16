"""V-QD-01: unabhaengige Gegenpruefung von QD-01, Teil 2 (Auswahl-Korrektur in der Entwicklung).
Nur lesend: importiert src/hybrid, schreibt ausschliesslich nach stdout."""
import sys, time, math, json
sys.path.insert(0, "/home/user/OdinGate-Botv134/swing-hybrid/src")
import numpy as np, pandas as pd
from hybrid import research as R, runner, mutationen as M

t0 = time.time()
A = R.GRUPPE_A; SPLIT = pd.Timestamp(R.SPLIT); D1 = pd.Timestamp(R.D1_ENDE)
K = R.yubit_kosten(A)[0]
K10 = ([("tsmom", dict(L=L, bias=b)) for L in (48, 96, 168, 336) for b in (False, True)] + [("ensemble", dict(bias=b)) for b in (False, True)])
K30 = ([("tsmom", dict(L=L, bias=b)) for L in (12, 24, 48, 96, 168) for b in (False, True)] + [("ensemble", dict(bias=b)) for b in (False, True)]
       + [("reversal", dict(n=n, k=k, bias=b)) for n in (24, 72) for k in (1.5, 2.0, 2.5) for b in (False, True)]
       + [("querschnitt", dict(L=L, modus=mo)) for L in (4, 24, 72) for mo in ("mom", "rev")])
name = lambda fam, p: fam + "_" + "_".join(f"{k}{v}" for k, v in p.items())
ZIEL = "tsmom_L336_biasFalse"


def sh(x):
    return x.mean(axis=0) / x.std(axis=0, ddof=1) * math.sqrt(365)


def stationaer(n, ziehungen, block, rng):
    nb = int(n / block * 3) + 30
    idx = np.empty((ziehungen, n), dtype=np.int64)
    for b in range(ziehungen):
        while True:
            lens = rng.geometric(1.0 / block, nb)
            if lens.sum() >= n:
                break
        starts = rng.integers(0, n, nb)
        ende = np.cumsum(lens)
        idx[b] = (np.repeat(starts, lens)[:n] + np.arange(n) - np.repeat(ende - lens, lens)[:n]) % n
    return idx


def omega_hac(X, block):
    """Standardabweichung von sqrt(n) x Mittel je Spalte, Kern des stationaeren Bootstraps (Hansen 2005, Gl. zu kappa)."""
    n, k = X.shape; q = 1.0 / block; e = X - X.mean(axis=0)
    v = (e * e).mean(axis=0)
    for i in range(1, n):
        kap = (n - i) / n * (1 - q) ** i + i / n * (1 - q) ** (n - i)
        if kap < 1e-8 and i > 5 * block:
            break
        v = v + 2 * kap * (e[i:] * e[:-i]).sum(axis=0) / n
    return np.sqrt(np.maximum(v, 1e-30))


def tests(X, i_ziel, ziehungen=10000, block=20, seed=4711):
    """Eigene Umsetzung: White (roh), White studentisiert (= SPA_u), Hansen SPA_c und SPA_l, Sharpe-Maximum, p allein."""
    rng = np.random.default_rng(seed); n, k = X.shape
    mu = X.mean(axis=0); idx = stationaer(n, ziehungen, block, rng)
    bm = np.stack([X[:, j][idx].mean(axis=1) for j in range(k)], axis=1)        # Ziehungen x k
    om = omega_hac(X, block)
    out = {}
    out["p_allein"] = float(((bm[:, i_ziel] - mu[i_ziel]) >= mu[i_ziel]).mean())
    out["white_roh"] = float(((bm - mu).max(axis=1) >= mu.max()).mean())
    T = max(0.0, float((math.sqrt(n) * mu / om).max()))
    zu = math.sqrt(n) * (bm - mu) / om
    out["white_stud"] = float((np.maximum(zu.max(axis=1), 0) >= T).mean())
    schw = -math.sqrt(2 * math.log(math.log(n)))
    g_c = np.where(math.sqrt(n) * mu / om >= schw, 0.0, mu)                     # schlechte Modelle behalten ihr (negatives) Mittel
    out["spa_c"] = float((np.maximum((math.sqrt(n) * (bm - mu + g_c) / om).max(axis=1), 0) >= T).mean())
    g_l = np.minimum(mu, 0.0)
    out["spa_l"] = float((np.maximum((math.sqrt(n) * (bm - mu + g_l) / om).max(axis=1), 0) >= T).mean())
    # Sharpe als Pruefgroesse: Maximum ueber die Einstellungen, Nullverteilung aus zentrierten Reihen
    Z = X - mu
    bs = np.stack([(lambda z: z.mean(axis=1) / z.std(axis=1, ddof=1))(Z[:, j][idx]) for j in range(k)], axis=1) * math.sqrt(365)
    s = sh(X)
    out["sharpe_allein"] = float((bs[:, i_ziel] >= s[i_ziel]).mean())
    out["sharpe_max"] = float((bs.max(axis=1) >= s.max()).mean())
    out["bonferroni"] = min(1.0, out["p_allein"] * k); out["k"] = k
    return out


def matrix(m, konfig, slip):
    sp, nm = [], []
    for fam, p in konfig:
        x = R.lauf(m, R.auf_raster(m, R.FAMILIEN[fam](m, **p)), taker=True, slip=slip, day_limit=9.0).daily_pnl(runner.MIT).sum(axis=1)
        sp.append(x); nm.append(name(fam, p))
    return pd.concat(sp, axis=1, keys=nm)


print("=== 1. Abgleich mit gespeicherter Stufe 1 der Runde 3 (reports/suche_runde3_stufe1.csv), sofortige Ausfuehrung, 5 bp, ohne Vorlauf")
m0 = R.markt(A)
X0 = matrix(m0, K10, 0.0005)
gesp = pd.read_csv("/home/user/OdinGate-Botv134/swing-hybrid/reports/suche_runde3_stufe1.csv").set_index("name")
abw = 0.0
for nmx in X0.columns:
    d1, d2 = X0[nmx][X0.index < D1], X0[nmx][(X0.index >= D1) & (X0.index < SPLIT)]
    abw = max(abw, abs(float(d1.mean() / d1.std() * math.sqrt(365)) - gesp.loc[nmx, "sofort_D1_sharpe"]),
              abs(float(d2.mean() / d2.std() * math.sqrt(365)) - gesp.loc[nmx, "sofort_D2_sharpe"]),
              abs(float(d1.sum()) - gesp.loc[nmx, "sofort_D1_N"]), abs(float(d2.sum()) - gesp.loc[nmx, "sofort_D2_N"]))
print(f"groesste Abweichung (Sharpe und Netto je Haelfte, 10 Einstellungen) gegen die gespeicherte Datei: {abw:.2e}")
print("gespeichert: bestanden/score ->", {k: (bool(v["bestanden"]), round(float(v["score"]), 3)) for k, v in gesp.iterrows()})
fin = gesp[gesp["bestanden"]].sort_values("score", ascending=False).head(2)
print("Finalisten nach gespeicherter Regel (scripts/suche_runde3.py:54):", list(fin.index))

print("\n=== 2. Auswahl-Korrektur ueber die 10 Trend-Einstellungen, nur Entwicklung (15.08.2021-31.03.2025)")
m1 = R.markt(A, vor=True)
for bez, m, slip in (("5 bp, ohne Vorlauf (Aufbau Runde 3)", m0, 0.0005), ("5 bp, mit Vorlauf", m1, 0.0005), ("Yubit-Kosten, mit Vorlauf (ab Runde 6)", m1, K)):
    Xd = (X0 if (m is m0) else matrix(m, K10, slip))
    Xd = Xd[Xd.index < SPLIT]; X = Xd.to_numpy(); iz = list(Xd.columns).index(ZIEL)
    s = sh(X)
    print(f"--- {bez}: Tage {len(X)}; bestes Tagesmittel {Xd.columns[int(np.argmax(X.mean(axis=0)))]}; bester Sharpe {Xd.columns[int(np.argmax(s))]}; "
          f"Kandidat {X[:, iz].mean()*365:+.3f}/Jahr, Sharpe {s[iz]:.3f}")
    print("    Sharpe aller 10:", dict(zip(Xd.columns, np.round(s, 2).tolist())))
    _, _, p_proj = M.reality_check(X, block=20, seed=3)
    _, _, p_proj1 = M.reality_check(X[:, [iz]], block=20, seed=3)
    _, _, p_proj21 = M.reality_check(X, block=20, seed=21)
    print(f"    Projektfunktion mutationen.reality_check: p allein {p_proj1:.4f} | White ueber 10: seed 3 -> {p_proj:.4f}, seed 21 -> {p_proj21:.4f}")
    e = tests(X, iz)
    print("    eigene Umsetzung (10.000 Ziehungen, Block 20, anderer Zufallsstart): " + " | ".join(f"{k} {v:.4f}" if k != "k" else f"k {v}" for k, v in e.items()))
    for bl in (5, 40):
        e2 = tests(X, iz, ziehungen=4000, block=bl, seed=99 + bl)
        print(f"    Block {bl:2d}: p_allein {e2['p_allein']:.4f} | white_roh {e2['white_roh']:.4f} | white_stud {e2['white_stud']:.4f} | spa_c {e2['spa_c']:.4f} | sharpe_max {e2['sharpe_max']:.4f}")
    if bez.startswith("Yubit"):
        X_y = Xd

print("\n=== 3. A fortiori: alle bis Runde 3 getesteten Signal-Einstellungen (30 aus Runde 1 + 2 neue mit L=336), sofortige Ausfuehrung, Entwicklung")
print("    Hinweis: Runde 1 hat diese 30 mit passiver Ausfuehrung und Tageslimit gemessen; hier einheitlich gemessen, nur als Groessenordnung.")
neu = [kk for kk in K30 if name(*kk) not in X_y.columns]
for bez, slip in (("5 bp", 0.0005), ("Yubit-Kosten", K)):
    alt = matrix(m1, K10, slip); zus = matrix(m1, neu, slip)
    Xa = pd.concat([alt, zus], axis=1); Xa = Xa[Xa.index < SPLIT]; X = Xa.to_numpy(); iz = list(Xa.columns).index(ZIEL)
    s = sh(X)
    e = tests(X, iz, ziehungen=5000)
    print(f"--- {bez}: {X.shape[1]} Einstellungen; bestes Tagesmittel {Xa.columns[int(np.argmax(X.mean(axis=0)))]}; bester Sharpe {Xa.columns[int(np.argmax(s))]} ({s.max():.3f}); "
          f"Sharpe-Spanne [{s.min():.2f}, {s.max():.2f}]")
    print("    " + " | ".join(f"{k} {v:.4f}" if k != "k" else f"k {v}" for k, v in e.items()))
print(f"\nfertig nach {time.time() - t0:.0f} s")
