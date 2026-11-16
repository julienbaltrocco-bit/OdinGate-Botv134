"""Tageszuordnung und Marktbereinigung (Nachtrag zu Abschnitt 19): Trades werden auf den Tag des EINSTIEGS gebucht, laufen aber bis zu 12 Stunden.
Die Regression in trichter.marktbereinigt nimmt nur die Marktrendite desselben Tages. Prüfung auf den gespeicherten Tagesreihen (T und V1, Kerzen < I_ENDE):
ändert sich das Urteil (Alpha > 0, t >= 2), wenn zusätzlich die Marktrendite des Folgetags erklärt (in dem ein Teil des Trades tatsächlich liegt)?"""
import sqlite3, sys, math
import numpy as np
sys.path.insert(0, 'forschung/fabrik/pruefung/B_buchung')
import pruef_lib as P
from fabrik import lauf as L, generator as G, daten as D
con = sqlite3.connect('file:data/fabrik/forschung.sqlite?mode=ro', uri=True)
con.row_factory = sqlite3.Row
zeilen = [dict(r) for r in con.execute("SELECT * FROM kandidaten WHERE status IN ('final','stufe3') OR (status = 'verworfen_3' AND grund = 'nach Abzug des Marktes kein gesicherter Ertrag')")]
tage = {g: np.load(f'data/fabrik/tage_{g}.npy', mmap_mode='r') for g in ("gen1", "gen2")}
def ols(y, X):
    k = np.linalg.solve(X.T @ X, X.T @ y)
    rest = y - X @ k
    cov = (rest @ rest) / (len(y) - X.shape[1]) * np.linalg.inv(X.T @ X)
    return k, k / np.sqrt(np.diag(cov))
markt_cache = {}
def markt(M, i0):
    key = (tuple(M), i0)
    if key not in markt_cache:
        s = P.c[list(M)][:, i0 - 1::288]
        markt_cache[key] = (s[:, 1:] / s[:, :-1] - 1).mean(0) * 1e4
    return markt_cache[key]
erg = []
for z in zeilen:
    i_t0, i_v0, d_t0, d_v0 = P.segment(z)
    M = P.markt(z)                                              # wie trichter.marktbereinigt: Markt = G.MAERKTE ohne BTC nur bei btcfuehrt/relstaerke/korrbruch als Hauptsignal
    m = markt(M, i_t0)
    p = np.asarray(tage[z['gen']][z['zeile']], dtype=np.float64)[d_t0:]
    assert len(p) == len(m)
    k1, t1 = ols(p, np.column_stack([np.ones(len(p)), m]))
    k2, t2 = ols(p[:-1], np.column_stack([np.ones(len(p) - 1), m[:-1], m[1:]]))     # letzter Tag entfällt: sein Folgetag läge in V2 (gesperrt)
    tm = p.mean() / p.std(ddof=1) * math.sqrt(len(p))
    erg.append((z, k1[0], t1[0], k1[1], k2[0], t2[0], k2[1], k2[2], t2[2], tm, m.mean()))
a = np.array([[e[i] for i in range(1, 11)] for e in erg])
print("Kandidaten:", len(erg), "| Marktrendite im Mittel (bp je Tag) über die Fälle:", round(float(a[:, 9].mean()), 2))
print(f"Regression wie im Trichter: Beta Median {np.median(a[:, 2]):+.4f} (5 %/95 %: {np.percentile(a[:, 2], 5):+.4f}/{np.percentile(a[:, 2], 95):+.4f}); t(Alpha) < 2: {(a[:, 1] < 2).sum()}")
print(f"mit Folgetag: Beta Folgetag Median {np.median(a[:, 6]):+.4f}, |t| > 2 bei {(np.abs(a[:, 7]) > 2).sum()} von {len(erg)}; t(Alpha) < 2: {(a[:, 4] < 2).sum()}; Urteil kippt (>=2 -> <2): {((a[:, 1] >= 2) & (a[:, 4] < 2)).sum()}")
print(f"t des rohen Tagesmittels über T+V1 (ohne Marktbereinigung) < 2: {(a[:, 8] < 2).sum()}; mittlere Änderung t(Alpha) - t(Mittel): {np.mean(a[:, 1] - a[:, 8]):+.3f}; größte Senkung {np.min(a[:, 1] - a[:, 8]):+.3f}")
print(f"mittlere Änderung des Alpha gegenüber dem rohen Tagesmittel: {np.mean([e[1] - np.asarray(tage[e[0]['gen']][e[0]['zeile']], dtype=np.float64)[P.segment(e[0])[2]:].mean() for e in erg]):+.4f} bp je Tag")
