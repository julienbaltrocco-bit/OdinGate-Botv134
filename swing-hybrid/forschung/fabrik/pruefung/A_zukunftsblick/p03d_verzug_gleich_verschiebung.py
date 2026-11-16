"""Gegenprobe ohne eigene Simulator-Kopie: kern.sim(verzug=1) muss dasselbe liefern wie kern.sim(verzug=0) auf um eine Kerze nach
hinten verschobenen Eingaben (Einstiegswunsch, Signalwert, sigma). Das gilt für Zeit-, Stop-, Ziel- und Nachzug-Ausstiege; beim
Signal-Ausstieg weicht verzug=1 ab (Ausstieg zwei statt eine Kerze später). Echte Speicher, nur Kerzen < I_ENDE."""
import sys
sys.path.insert(0, 'forschung')
import numpy as np
from fabrik import daten as D, lauf as L, kern as FK, signale as S, generator as G, evolution as E

L._init()
AUSST = {**G.AUSSTIEGE, **E.NEUE_AUSSTIEGE}
rng = np.random.default_rng(3)
slip = np.asarray(L._g["slip_bp"]) * 2.0


def lauf(j, ein, wert, sigma, x, verzug):
    halte, sl, tp, tr, ta, sx = x
    z = [np.zeros(L.N_TAGE) for _ in range(6)]
    n = FK.sim(L._g["o"][j], L._g["h"][j], L._g["l"][j], L._g["fcum"][j], ein, wert, sigma, L._g["tag"], L.I_T, L.I_ENDE, halte, sl, tp, tr, ta,
               np.nan if sx is None else sx, slip[j], L.KOSTEN85, *z, verzug)
    return n, z


erg = {}
for q in range(40):
    si = int(rng.integers(len(S.NAMEN))); j = int(rng.integers(1, 10))
    a = {"si": si, "th": float(rng.choice([1.5, 2.5])), "r": int(rng.choice([1, -1])), "f": str(rng.choice(S.FILTER)), "k": int(rng.choice([1, 3, 12]))}
    ein, wert = L.einstieg(a, j)
    sigma = np.asarray(L._g["sigma"][j, :L.I_ENDE])
    ein_s = np.concatenate([[0], ein[:-1]]).astype(np.int8); wert_s = np.concatenate([[np.nan], wert[:-1]]); sigma_s = np.concatenate([[np.nan], sigma[:-1]]).astype(np.float32)
    for xname, x in AUSST.items():
        n1, z1 = lauf(j, ein, wert, sigma, x, 1)
        n0, z0 = lauf(j, ein_s, wert_s, sigma_s, x, 0)
        gleich = n1 == n0 and all(np.array_equal(u, v) for u, v in zip(z1, z0))
        art = "Signal-Ausstieg" if x[5] is not None else "andere Ausstiege"
        e = erg.setdefault(art, [0, 0, 0, 0.0, 0])
        e[0] += 1; e[1] += int(gleich); e[2] += n1
        if not gleich and n1:
            e[3] += (z1[5].sum() - z0[5].sum()) / max(n1, 1); e[4] += 1
for art, e in erg.items():
    print(f"{art}: {e[0]} Läufe, {e[2]} Trades; verzug=1 == Verschiebung um eine Kerze in {e[1]} Läufen" + (f"; mittlere Mehrdauer je Trade in den abweichenden Läufen {e[3] / max(e[4], 1):+.2f} Kerzen" if e[4] else ""))
