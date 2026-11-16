"""C12 Dieselben Proben auf dem NEUEN Lauf B (data/fabrik_b, nur lesend, nur T; Lauf B wurde während der Prüfung gerechnet):
Anteil Stufe 1 getrennt nach Generation, und der Reality Check in beiden Rechenweisen."""
import sys, math, json, sqlite3
import numpy as np
sys.path.insert(0, 'forschung/fabrik/pruefung/C_statistik')
import c_lib as C
from fabrik import lauf as L

B = 'data/fabrik_b'
con = sqlite3.connect(f'file:{B}/forschung.sqlite?mode=ro', uri=True); con.row_factory = sqlite3.Row
print("Code-Stand:", C.stand())
soll = json.load(open('forschung/fabrik/ergebnisse/statistik.json'))
print("statistik.json Stand:", soll["stand"])
print("Läufe:", [tuple(r) for r in con.execute("SELECT gen, begonnen, kandidaten FROM laeufe")])
for (gruppe, wo), (name, sw) in zip((("Kurs/Volumen/Derivate", "braucht != 't' AND (best IS NULL OR best NOT LIKE '%tiefe%' AND best NOT LIKE '%liq_entzug%')"),
                                     ("Orderbuch-Tiefe", "(braucht = 't' OR best LIKE '%tiefe%' OR best LIKE '%liq_entzug%')")), soll["gruppen"].items()):
    for gen in ("gen1", "gen2"):
        n, s1 = con.execute(f"SELECT COUNT(*), SUM(status != 'verworfen_1') FROM kandidaten WHERE n_t >= 200 AND gen = ? AND {wo}", (gen,)).fetchone()
        print(f"{gruppe} {gen}: gültig {n}, Stufe 1 bestanden {s1} = {s1 / n:.4f}")
    print(f"   statistik.json weist aus: anteil_stufe1 {sw['anteil_stufe1']} gegen zufallserwartung_stufe1 {sw['zufallserwartung_stufe1']}")
    z = con.execute(f"SELECT gen, zeile FROM kandidaten WHERE n_t >= 200 AND {wo}").fetchall()
    d0, d1 = L.SEGMENTE["t" if "Tiefe" in gruppe else "k"][:2]
    tage = d1 - d0
    idx = C.gewichte(tage, 400, 10, np.random.default_rng(19))
    W = np.stack([np.bincount(ix, minlength=tage) for ix in idx]).astype(np.float32) / tage
    mf, ms, t_best = np.full(400, -np.inf), np.full(400, -np.inf), -np.inf
    for gen in ("gen1", "gen2"):
        zeilen = np.sort(np.array([r["zeile"] for r in z if r["gen"] == gen]))
        mm = np.load(f'{B}/tage_{gen}.npy', mmap_mode='r')
        assert mm.shape[1] == L.N_TAGE
        for c0 in range(0, len(zeilen), 20000):
            t = np.asarray(mm[zeilen[c0:c0 + 20000]])[:, d0:d1]
            mu, sd = t.mean(1), t.std(1, ddof=1); ok = sd > 0
            tw = np.where(ok, mu / np.where(ok, sd, 1) * math.sqrt(tage), 0); t_best = max(t_best, float(tw.max()))
            mb = t @ W.T
            mf = np.maximum(mf, np.where(ok[:, None], (mb - mu[:, None]) / np.where(ok, sd, 1)[:, None] * math.sqrt(tage), -np.inf).max(0))
            vb = np.maximum((t * t) @ W.T - mb ** 2, 0) * tage / (tage - 1); g = ok[:, None] & (vb > 1e-12)
            ms = np.maximum(ms, np.where(g, (mb - mu[:, None]) / np.sqrt(np.where(g, vb, 1)) * math.sqrt(tage), -np.inf).max(0))
    print(f"   Reality Check: bestes t {t_best:.3f} | wie trichter p = {np.mean(mf >= t_best):.4f} (statistik.json: {sw['reality_check_p']}, t {sw['bester_t_wert_T']}) | mit eigener Streuung je Stichprobe p = {np.mean(ms >= t_best):.4f}")
