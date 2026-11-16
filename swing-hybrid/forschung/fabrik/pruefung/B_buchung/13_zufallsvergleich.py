"""Zufallsvergleich fabrik.kern.sim gegen den eigenen Simulator auf künstlichen Reihen mit harten Randfällen
(Kurslücken, Sigma 0/NaN, Signalwert NaN, alle Ausstiegsarten gemischt, Verzug 0/1, verschobene Segmentgrenzen, Funding an jeder Kerze)."""
import sys
import numpy as np
sys.path.insert(0, 'forschung'); sys.path.insert(0, 'forschung/fabrik/pruefung/B_buchung')
from fabrik import kern as FK
import eigen as E

rng = np.random.default_rng(2026)
faelle = abw = trades_ges = 0
arten = {}
for fall in range(3000):
    n = int(rng.integers(40, 400))
    ret = rng.normal(0, 0.004, n) * (1 + 4 * (rng.random(n) < 0.03))
    c = 100 * np.exp(np.cumsum(ret))
    o = np.empty(n); o[0] = 100.0
    o[1:] = c[:-1] * (1 + rng.normal(0, 0.0015, n - 1) * (rng.random(n - 1) < 0.25))      # Kurslücken bei einem Viertel der Kerzen
    h = np.maximum(o, c) * (1 + np.abs(rng.normal(0, 0.002, n)))
    l = np.minimum(o, c) * (1 - np.abs(rng.normal(0, 0.002, n)))
    frate = rng.normal(0, 2e-4, n) * (rng.random(n) < 0.3)
    fcum = np.cumsum(frate)
    ein = rng.choice(np.array([-1, 0, 1], np.int8), n, p=[0.15, 0.7, 0.15]) if rng.random() < 0.8 else rng.choice(np.array([-1, 1], np.int8), n)
    wert = rng.normal(0.6, 1.0, n)
    wert[rng.random(n) < 0.05] = np.nan
    sigma = np.abs(rng.normal(0.008, 0.003, n)).astype(np.float32)
    sigma[rng.random(n) < 0.03] = 0.0
    sigma[rng.random(n) < 0.03] = np.nan
    halte = int(rng.choice([1, 2, 3, 12, 48, 144]))
    sl = float(rng.choice([0, 0, 0.5, 1.5, 2.0]))
    tp = float(rng.choice([0, 0, 0.5, 1.5, 3.0]))
    trail = float(rng.choice([0, 0, 0.5, 2.0]))
    trail_ab = float(rng.choice([0.0, 1.0]))
    sx = None if rng.random() < 0.6 else float(rng.choice([0.0, 0.5, 1.0]))
    verzug = int(rng.random() < 0.3)
    i0 = int(rng.integers(0, 10)); i1 = n - int(rng.integers(0, 10))
    slip = float(rng.choice([0.0, 1.0, 26.4]))
    tag = (np.arange(n) // 7).astype(np.int32)
    z = [np.zeros(n // 7 + 1) for _ in range(6)]
    k = FK.sim(o, h, l, fcum, ein, wert, sigma, tag, i0, i1, halte, sl, tp, trail, trail_ab, np.nan if sx is None else sx, slip, 2.4, *z, verzug)
    tr = E.trades(o, h, l, np.diff(fcum, prepend=0.0), ein, wert, sigma, i0, i1, halte, sl, tp, trail, trail_ab, sx, verzug)
    roh_tag, n_tag, roh = E.tagesfelder(tr, slip, 0, n // 7 + 1) if False else (np.zeros(n // 7 + 1), np.zeros(n // 7 + 1), [])
    dauer = np.zeros(n // 7 + 1)
    for (i, a, b, d, e, px, art, fund) in tr:
        r = d * (px / e - 1) * 1e4 - slip + fund
        roh_tag[a // 7] += r; n_tag[a // 7] += 1; dauer[a // 7] += b - a
        arten[art] = arten.get(art, 0) + 1
    faelle += 1; trades_ges += len(tr)
    if k != len(tr) or np.abs(z[0] - roh_tag).max() > 1e-6 or np.abs(z[1] - n_tag).max() > 0 or np.abs(z[5] - dauer).max() > 0:
        abw += 1
        if abw <= 5:
            print("ABWEICHUNG Fall", fall, dict(n=n, halte=halte, sl=sl, tp=tp, trail=trail, trail_ab=trail_ab, sx=sx, verzug=verzug, i0=i0, i1=i1), "Trades kern", k, "eigen", len(tr),
                  "max. Abw. roh", float(np.abs(z[0] - roh_tag).max()))
print(f"Fälle {faelle}, Trades {trades_ges}, Ausstiegsarten {arten}, Abweichungen {abw}")
