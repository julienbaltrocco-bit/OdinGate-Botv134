"""C02c Reality Check auf den ECHTEN Daten (nur T, lesend), eigene Rechnung über alle gültigen Kandidaten beider Gruppen:
(1) so wie trichter.statistik rechnet (gleiche Zufallszahlen, Startwert 19) -> muss statistik.json treffen;
(2) mit eigener Streuung je Bootstrap-Stichprobe (so wie die Prüfgröße der echten Daten gebildet ist)."""
import sys, math, json, time
import numpy as np
sys.path.insert(0, 'forschung/fabrik/pruefung/C_statistik')
import c_lib as C
from fabrik import lauf as L, daten as D

con = C.ro()
soll = json.load(open('forschung/fabrik/ergebnisse/statistik.json'))["gruppen"]
t0 = time.time()
for (gruppe, wo), sollwert in zip((("Kurs/Volumen/Derivate", "braucht != 't' AND (best IS NULL OR best NOT LIKE '%tiefe%' AND best NOT LIKE '%liq_entzug%')"),
                                   ("Orderbuch-Tiefe", "(braucht = 't' OR best LIKE '%tiefe%' OR best LIKE '%liq_entzug%')")), soll.values()):
    z = con.execute(f"SELECT gen, zeile, id FROM kandidaten WHERE n_t >= 200 AND {wo}").fetchall()
    d0, d1 = L.SEGMENTE["t" if "Tiefe" in gruppe else "k"][:2]
    tage = d1 - d0
    idx = C.gewichte(tage, 400, 10, np.random.default_rng(19))
    W = np.stack([np.bincount(ix, minlength=tage) for ix in idx]).astype(np.float32) / tage
    max_fest, max_selbst = np.full(400, -np.inf), np.full(400, -np.inf)
    t_best, wer, schiefe_best = -np.inf, None, None
    for gen in ("gen1", "gen2"):
        zeilen = np.sort(np.array([r["zeile"] for r in z if r["gen"] == gen]))
        mm = np.load(f'data/fabrik/tage_{gen}.npy', mmap_mode='r')
        assert mm.shape[1] == L.N_TAGE                                   # die Tagesdateien enden am 30.06.2024
        for c0 in range(0, len(zeilen), 20000):
            t = np.asarray(mm[zeilen[c0:c0 + 20000]])[:, d0:d1]
            mu, sd = t.mean(1), t.std(1, ddof=1)
            ok = sd > 0
            tw = np.where(ok, mu / np.where(ok, sd, 1) * math.sqrt(tage), 0)
            if tw.max() > t_best:
                k = int(tw.argmax()); t_best, wer = float(tw.max()), (gen, int(zeilen[c0 + k]))
                x = t[k].astype(np.float64); schiefe_best = float(((x - x.mean()) ** 3).mean() / x.std() ** 3)
            mb = t @ W.T
            fest = (mb - mu[:, None]) / np.where(ok, sd, 1)[:, None] * math.sqrt(tage)
            max_fest = np.maximum(max_fest, np.where(ok[:, None], fest, -np.inf).max(0))
            vb = np.maximum((t * t) @ W.T - mb ** 2, 0) * tage / (tage - 1)
            g = ok[:, None] & (vb > 1e-12)
            selbst = np.where(g, (mb - mu[:, None]) / np.sqrt(np.where(g, vb, 1)) * math.sqrt(tage), -np.inf)
            max_selbst = np.maximum(max_selbst, selbst.max(0))
    print(f"{gruppe}: {len(z)} Kandidaten, {tage} Tage | bestes t {t_best:.3f} (Zeile {wer}, Schiefe seiner Tagesreihe {schiefe_best:+.2f})")
    print(f"   wie trichter:      p = {np.mean(max_fest >= t_best):.4f}  Zufalls-Maximum Median {np.median(max_fest):.2f}, 95 % {np.percentile(max_fest, 95):.2f}"
          f"   | statistik.json: p {sollwert['reality_check_p']}, Median {sollwert['zufalls_maximum_median']}, 95 % {sollwert['zufalls_maximum_95']}, t {sollwert['bester_t_wert_T']}")
    print(f"   eigene Streuung:   p = {np.mean(max_selbst >= t_best):.4f}  Zufalls-Maximum Median {np.median(max_selbst):.2f}, 95 % {np.percentile(max_selbst, 95):.2f}", flush=True)
print(f"Rechenzeit {time.time() - t0:.0f} s")
