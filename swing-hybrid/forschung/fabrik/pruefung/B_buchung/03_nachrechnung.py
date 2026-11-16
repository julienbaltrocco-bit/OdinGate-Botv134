"""Schritt 1: Tagesreihe netto mit Rebate und Kennzahlen mit eigenem Simulator nachrechnen und mit tage_gen1.npy und der Datenbank vergleichen.
Liest nur Kerzen < I_ENDE (2024-07-01). Toleranz 0,01 bp."""
import json, sys, time
import numpy as np
sys.path.insert(0, 'forschung'); sys.path.insert(0, 'forschung/fabrik/pruefung/B_buchung')
from fabrik import daten as D, lauf as L, generator as G, signale as S
import eigen as E

L._init()
I_ENDE = L.I_ENDE
o, h, l = (np.asarray(D.laden(x)[:, :I_ENDE]) for x in ("o", "h", "l"))
fc = np.asarray(D.laden("fcum")[:, :I_ENDE])
frate = np.diff(fc, axis=1, prepend=0.0)                       # Rate je Kerze (Termin = Kerzenöffnung), geprüft in 02_funding_roh.py
sigma = np.asarray(D.laden("sigma")[:, :I_ENDE])
slip_bp = np.asarray(D.laden("slip_bp"))
tage_mm = np.load('data/fabrik/tage_gen1.npy', mmap_mode='r')
wahl = json.load(open('forschung/fabrik/pruefung/B_buchung/01_auswahl.json'))
nur = sys.argv[1:]
TOL = 0.01
alle_ok = True
for z in wahl:
    if nur and z['id'] not in nur:
        continue
    t_start = time.time()
    si = S.NAMEN.index(z['signal'])
    a = {"si": si, "signal": z['signal'], "familie": z['familie'], "braucht": z['braucht'], "th": z['th'], "r": z['r'], "f": z['f'], "k": z['k']}
    halte, sl, tp, tr, ta, sx = G.AUSSTIEGE[z['x']]
    # Protokoll: Tiefe-Signale T 2023, V1 01-06/2024; sonst T 15.08.2021-30.06.2023, V1 bis 30.06.2024
    tief = z['braucht'] == 't'
    T0 = np.datetime64('2023-01-01') if tief else np.datetime64('2021-08-15')
    V0 = np.datetime64('2024-01-01') if tief else np.datetime64('2023-07-01')
    i_t0 = int(np.searchsorted(D.RASTER.values, T0)); i_v0 = int(np.searchsorted(D.RASTER.values, V0))
    tag_von = int(np.searchsorted(D.RASTER.values, np.datetime64('2021-08-15')))
    n_tage = (I_ENDE - tag_von) // 288
    d_t0, d_v0 = (i_t0 - tag_von) // 288, (i_v0 - tag_von) // 288
    markt = list(G.MAERKTE[z['m']])
    if z['signal'].startswith(('btcfuehrt', 'relstaerke', 'korrbruch')):
        markt = [c for c in markt if c != 0]                   # BTC kann sich nicht selbst führen
    roh_tag, n_tag, arten = np.zeros((len(markt), n_tage)), np.zeros((len(markt), n_tage)), {}
    for q, j in enumerate(markt):
        ein, wert = L.einstieg(a, j)
        tr_ = E.trades(o[j], h[j], l[j], frate[j], ein, wert, sigma[j], i_t0, I_ENDE, halte, sl, tp, tr, ta, sx)
        roh_tag[q], n_tag[q], _ = E.tagesfelder(tr_, 2 * slip_bp[j], tag_von, n_tage)
        for x in tr_:
            arten[x[6]] = arten.get(x[6], 0) + 1
    slip_rt = 2 * slip_bp[markt]
    p85 = (roh_tag.sum(0) - 2.4 * n_tag.sum(0)) / len(markt)
    gesp = np.asarray(tage_mm[z['zeile']], dtype=np.float64)
    abw_tag = float(np.abs(p85 - gesp).max())
    mitte = (d_t0 + d_v0) // 2
    T, H1, H2, V = (E.kennzahlen(roh_tag, n_tag, slip_rt, x, y) for x, y in ((d_t0, d_v0), (d_t0, mitte), (mitte, d_v0), (d_v0, n_tage)))
    paare = [("n_t", T["n"]), ("roh_t", T["roh"]), ("n85_t", T["n85"]), ("t_roh_t", T["t_roh"]), ("t85_t", T["t85"]), ("n85_h1", H1["n85"]), ("n85_h2", H2["n85"]),
             ("n85_2x_t", T["n85_2x"]), ("n_v", V["n"]), ("roh_v", V["roh"]), ("n85_v", V["n85"]), ("t85_v", V["t85"])]
    abw = {k: (v, z[k], abs(v - z[k])) for k, v in paare}
    schlecht = {k: x for k, x in abw.items() if x[2] > TOL}
    ok = abw_tag <= TOL and not schlecht
    alle_ok &= ok
    # eigener Status nach Abschnitt 19
    if T["n"] < 200: st = "ungültig"
    elif not (T["roh"] > 0 and T["t_roh"] >= 2): st = "verworfen_1"
    elif not (T["n85"] > 0 and T["t85"] >= 2 and H1["n85"] > 0 and H2["n85"] > 0 and T["n85_2x"] > 0): st = "verworfen_2"
    else: st = "stufe2"
    print(f"{z['id']} {z['signal']:<14} th {z['th']} r {z['r']:+d} {z['f']:<11} k{z['k']:<2} {z['x']:<20} {z['m']:<6} Coins {len(markt):>2} | Trades {int(n_tag.sum()):>6} {arten} | "
          f"max. Abw. Tagesreihe {abw_tag:.5f} bp | n_t {T['n']}/{z['n_t']} n_v {V['n']}/{z['n_v']} | Status eigen {st} / DB {z['status']} | "
          f"{'OK' if ok and st == z['status'] else 'ABWEICHUNG ' + json.dumps({k: [round(float(x[0]), 4), x[1]] for k, x in schlecht.items()})}  ({time.time() - t_start:.1f}s)", flush=True)
    print("     " + "  ".join(f"{k} {float(x[0]):.3f}/{x[1]}" for k, x in abw.items() if k not in ("n_t", "n_v")), flush=True)
print("ALLE INNERHALB 0,01 bp:" , alle_ok)
