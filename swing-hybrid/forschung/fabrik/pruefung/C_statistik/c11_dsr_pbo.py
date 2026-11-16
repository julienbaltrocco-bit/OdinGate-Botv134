"""C11 (a) Deflated Sharpe Ratio: in Abschnitt 19 als Prüfgröße angekündigt, im Code nicht gerechnet (phi_inv ist definiert, wird aber nirgends benutzt).
       Hier nachgerechnet für den besten Kandidaten je Gruppe (Lauf A, nur T).
   (b) phi_inv gegen scipy.
   (c) PBO und 'bester verliert im anderen Teil' in künstlichen Welten: reines Rauschen; Rauschen mit unterschiedlich hohen Kosten (niemand hat einen Vorteil)."""
import sys, math, inspect, re
import numpy as np
from scipy import stats
sys.path.insert(0, 'forschung/fabrik/pruefung/C_statistik')
import c_lib as C
from fabrik import lauf as L, trichter as T

print("Code-Stand:", C.stand())
quelle = "".join(open(f"forschung/fabrik/{n}.py").read() for n in ("trichter", "lauf", "evolution", "bericht", "freigabe"))
print("(a) Vorkommen im Code: 'phi_inv(' ", len(re.findall(r"phi_inv\(", quelle)), "(davon 1 Definition und 1 Selbstaufruf) | 'deflat' / 'DSR':", len(re.findall(r"(?i)deflat|\bdsr\b", quelle)),
      "| Schlüssel in statistik.json:", sorted(__import__('json').load(open('forschung/fabrik/ergebnisse/statistik.json'))['gruppen'].popitem()[1]))
con = C.ro()
EM = 0.5772156649
for gruppe, wo, seg in (("Kurs/Volumen/Derivate", "braucht != 't' AND (best IS NULL OR best NOT LIKE '%tiefe%' AND best NOT LIKE '%liq_entzug%')", "k"),
                        ("Orderbuch-Tiefe", "(braucht = 't' OR best LIKE '%tiefe%' OR best LIKE '%liq_entzug%')", "t")):
    z = con.execute(f"SELECT gen, zeile, sharpe_t, t85_t, id FROM kandidaten WHERE n_t >= 200 AND {wo}").fetchall()
    d0, d1 = L.SEGMENTE[seg][:2]; tage = d1 - d0
    sr_alle = np.array([r["sharpe_t"] for r in z]) / math.sqrt(365)            # Sharpe je Tag
    b = max(z, key=lambda r: r["t85_t"])
    x = np.asarray(np.load(C.ECHT_AUS / f"tage_{b['gen']}.npy", mmap_mode="r")[b["zeile"]], dtype=np.float64)[d0:d1]
    sr = x.mean() / x.std(ddof=1); g3 = stats.skew(x); g4 = stats.kurtosis(x, fisher=False)
    n = len(z)
    emax = (1 - EM) * stats.norm.ppf(1 - 1 / n) + EM * stats.norm.ppf(1 - 1 / (n * math.e))
    for name, var in (("Streuung der Sharpe-Werte über alle Versuche", sr_alle.var(ddof=1)), ("nur Stichprobenstreuung 1/Tage (alle Versuche ohne Vorteil und ohne Kosten)", 1 / tage)):
        sr0 = math.sqrt(var) * emax
        dsr = stats.norm.cdf((sr - sr0) * math.sqrt(tage - 1) / math.sqrt(1 - g3 * sr + (g4 - 1) / 4 * sr ** 2))
        print(f"   {gruppe}: bester {b['id']} t {b['t85_t']}, Sharpe/Tag {sr:.4f} (p.a. {sr * math.sqrt(365):.2f}), Schiefe {g3:+.2f}, Wölbung {g4:.1f}, Versuche {n}, erwartetes Maximum {emax:.2f} Streuungen"
              f" | {name}: Schwelle {sr0:.4f}/Tag -> Deflated Sharpe Ratio {dsr:.3f} (als gesichert gälte > 0,95)")

print("\n(b) phi_inv gegen scipy.stats.norm.ppf:", max(abs(T.phi_inv(p) - stats.norm.ppf(p)) for p in [1e-9, 1e-6, 1e-4, 0.001, 0.02, 0.02425, 0.3, 0.5, 0.7, 0.98, 0.999, 1 - 1e-6]))

print("\n(c) PBO in künstlichen Welten (eigene Nachrechnung, in C01 gleich der Rechnung in trichter.statistik), je 40 Welten, 400 Kandidaten, 1.051 Tage")
rng = np.random.default_rng(8)
for name in ("reines Rauschen, Mittel null", "Rauschen, Kosten je Kandidat verschieden (0 bis 0,3 Streuungen je Tag), niemand hat einen Vorteil",
             "wie zuvor, dazu gemeinsamer Marktanteil mit steigendem Markt (Beta 0 bis 1, Markt +0,05 Streuungen je Tag)"):
    pb, vl = [], []
    for w in range(40):
        X = rng.normal(0, 1, (400, 1051))
        if "Kosten" in name or "zuvor" in name:
            X -= rng.uniform(0, 0.3, (400, 1))
        if "zuvor" in name:
            X += rng.uniform(0, 1, (400, 1)) * (rng.normal(0.05, 1, 1051))[None, :]
        a, b, _ = C.pbo_eigen(X, 0, 1051)
        pb.append(a); vl.append(b)
    print(f"   {name}: PBO im Mittel {np.mean(pb):.3f}, 'bester verliert im anderen Teil' im Mittel {np.mean(vl):.3f}")
