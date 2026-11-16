"""t-Werte nach Tagen: Voraussetzungen auf den gespeicherten Tagesreihen der Finalisten (T und V1): Autokorrelation der Tagesergebnisse
(Buchung am Einstiegstag bei Trades bis 12 h), Anteil der Tage mit Trades, Gewicht einzelner Tage. Dazu: Trades über die Grenze T/V1."""
import sqlite3, sys, random
import numpy as np
sys.path.insert(0, 'forschung/fabrik/pruefung/B_buchung')
import pruef_lib as P
from fabrik import lauf as L
con = sqlite3.connect('file:data/fabrik/forschung.sqlite?mode=ro', uri=True)
con.row_factory = sqlite3.Row
zeilen = [dict(r) for r in con.execute("SELECT * FROM kandidaten WHERE status = 'final'")]
tage = {g: np.load(f'data/fabrik/tage_{g}.npy', mmap_mode='r') for g in ("gen1", "gen2")}
ak, anteil_tage, top1, t_korr = [], [], [], []
for z in zeilen:
    i_t0, i_v0, d_t0, d_v0 = P.segment(z)
    p = np.asarray(tage[z['gen']][z['zeile']], dtype=np.float64)[d_t0:d_v0]
    q = p - p.mean()
    rho = float((q[1:] * q[:-1]).sum() / (q * q).sum())
    ak.append(rho)
    anteil_tage.append(float((p != 0).mean()))
    top1.append(float(p.max() / p.sum()))
    # t-Wert mit Newey-West (5 Verzögerungen) gegen den einfachen t-Wert
    n = len(p); g0 = (q * q).sum() / n
    lrv = g0 + 2 * sum((1 - k / 6) * (q[k:] * q[:-k]).sum() / n for k in range(1, 6))
    t_korr.append(float(p.mean() / np.sqrt(max(lrv, 1e-12) / n)) / z['t85_t'])
ak, anteil_tage, top1, t_korr = map(np.array, (ak, anteil_tage, top1, t_korr))
print(f"Finalisten {len(zeilen)}: Autokorrelation der Tagesergebnisse (1 Tag) in T: Mittel {ak.mean():+.3f}, 5 %/95 % {np.percentile(ak, 5):+.3f}/{np.percentile(ak, 95):+.3f}")
print(f"t-Wert mit Newey-West (5 Tage) im Verhältnis zum gespeicherten t85_t: Median {np.median(t_korr):.3f}, 5 % {np.percentile(t_korr, 5):.3f}; t unter 2 nach Korrektur: {int(((t_korr * np.array([z['t85_t'] for z in zeilen])) < 2).sum())}")
print(f"Anteil der T-Tage mit Trades: Median {np.median(anteil_tage):.2f}, 5 % {np.percentile(anteil_tage, 5):.2f}")
print(f"Anteil des besten Tages am T-Ergebnis: Median {np.median(top1):.2f}, 95 % {np.percentile(top1, 95):.2f}, Maximum {top1.max():.2f}; über 20 %: {(top1 > 0.2).sum()}")
# Trades über die Grenze T/V1 und am Datenende (eigener Simulator, Stichprobe)
rng = random.Random(15)
n_tr = n_grenze = n_ende = 0; s_grenze = s_t = 0.0
for z in rng.sample(zeilen, 60):
    r = P.nachbau(z, mit_trades=True)
    i_t0, i_v0, d_t0, d_v0 = r["seg"]
    for (j, i, a, b, d, e, px, art, fund, roh) in r["trades"]:
        n_tr += 1
        if a < i_v0:
            s_t += roh - 2.4
            if b >= i_v0:
                n_grenze += 1; s_grenze += roh - 2.4
        n_ende += art == "datenende"
print(f"60 Finalisten, {n_tr} Trades: in T gebucht mit Ausstieg in V1: {n_grenze} (Summe {s_grenze:.0f} bp von {s_t:.0f} bp T-Ergebnis); am Datenende (30.06.2024) vorzeitig geschlossen: {n_ende}")
