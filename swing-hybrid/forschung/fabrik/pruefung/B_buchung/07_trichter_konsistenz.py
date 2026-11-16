"""Die Buchungsfunktionen des Trichters (trichter.tagesreihe, trichter.marktbereinigt) NUR auf T und V1 (Kerzen < I_ENDE) gegen
gespeicherte Tagesreihen und eigene Rechnung. stufe3/stufe4 werden nicht ausgeführt, V2 wird nicht gelesen, nichts wird geschrieben."""
import json, sys, sqlite3, random, math
import numpy as np
sys.path.insert(0, 'forschung/fabrik/pruefung/B_buchung')
import pruef_lib as P
from fabrik import trichter as T, lauf as L, daten as D

assert T.I_V2 == L.I_ENDE
con = sqlite3.connect('file:data/fabrik/forschung.sqlite?mode=ro', uri=True)
con.row_factory = sqlite3.Row
rng = random.Random(7)
wahl = json.load(open('forschung/fabrik/pruefung/B_buchung/01_auswahl.json'))
for gen, wo, n in (("gen2", "best IS NOT NULL AND n_t >= 200", 6), ("gen2", "best IS NULL AND n_t >= 200", 6), ("gen1", "status IN ('final','stufe3')", 6), ("gen2", "status IN ('final','stufe3')", 6)):
    ids = [r[0] for r in con.execute(f"SELECT id FROM kandidaten WHERE gen = ? AND {wo}", (gen,))]
    wahl += [dict(con.execute("SELECT * FROM kandidaten WHERE gen = ? AND id = ?", (gen, i)).fetchone()) for i in rng.sample(ids, n)]
tage = {g: np.load(f'data/fabrik/tage_{g}.npy', mmap_mode='r') for g in ("gen1", "gen2")}
c = np.asarray(D.laden("c")[:, :L.I_ENDE])
schlecht = 0
for z in wahl:
    i_t0, i_v0, d_t0, d_v0 = P.segment(z)
    p, n, roh = T.tagesreihe(z, i_t0, L.I_ENDE)
    gesp = np.asarray(tage[z['gen']][z['zeile']], dtype=np.float64)[d_t0:]
    a1 = float(np.abs(p - gesp).max())
    r = P.nachbau(z)
    # doppelte Slippage: eigene Rechnung über T und V1 zusammen
    M = r["M"]
    nt = r["n_tag"].sum()
    roh_eigen = r["roh_tag"].sum() / nt if nt else 0.0
    roh2_eigen = roh_eigen - float((r["n_tag"].sum(1) * 2 * P.slip_bp[M]).sum() / nt) if nt else 0.0
    p2, n2, roh2 = T.tagesreihe(z, i_t0, L.I_ENDE, slip_faktor=2.0)
    # Verzögerung: eigener Simulator mit derselben Auslegung des Verzugs
    rv = P.nachbau(z, verzug=1)
    nv = rv["n_tag"].sum()
    rohv_eigen = rv["roh_tag"].sum() / nv if nv else 0.0
    pv, nvt, rohv = T.tagesreihe(z, i_t0, L.I_ENDE, verzug=1)
    # Marktbereinigung: eigene Regression
    al, tal, be = T.marktbereinigt(z, i_t0, L.I_ENDE)
    tagesschluss = c[M][:, i_t0 - 1::288]
    m = (tagesschluss[:, 1:] / tagesschluss[:, :-1] - 1).mean(0) * 1e4
    assert len(m) == len(p)
    X = np.column_stack([np.ones(len(m)), m])
    koef = np.linalg.solve(X.T @ X, X.T @ gesp)
    rest = gesp - X @ koef
    se = math.sqrt((rest @ rest) / (len(m) - 2) * np.linalg.inv(X.T @ X)[0, 0])
    ok = a1 < 0.01 and n == int(nt) and abs(roh - roh_eigen) < 0.01 and abs(roh2 - roh2_eigen) < 0.01 and int(nv) == nvt and abs(rohv - rohv_eigen) < 0.01 \
        and abs(al - koef[0]) < 1e-3 and abs(tal - koef[0] / se) < 1e-2 and abs(be - koef[1]) < 1e-4
    schlecht += not ok
    print(f"{'OK  ' if ok else 'FEHL'} {z['gen']} {z['id']} {z['signal']:<14} {z['x']:<20} {z['m']:<6} best {str(z['best'])[:28]:<28} | Tagesreihe Trichter gegen Speicher {a1:.5f} bp | "
          f"roh {roh:.3f}/{roh_eigen:.3f} | 2x Slippage {roh2:.3f}/{roh2_eigen:.3f} | Verzug n {nvt}/{int(nv)} roh {rohv:.3f}/{rohv_eigen:.3f} | "
          f"Alpha {al:.3f}/{koef[0]:.3f} t {tal:.2f}/{koef[0]/se:.2f} Beta {be:.4f}/{koef[1]:.4f}", flush=True)
print("abweichend:", schlecht, "von", len(wahl))
