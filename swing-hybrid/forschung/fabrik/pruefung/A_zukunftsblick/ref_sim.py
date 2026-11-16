"""Unabhängiger Vergleichs-Simulator, geschrieben nach den Regeln aus protokoll.md Abschnitt 19 (ohne fabrik.kern).

Arbeitsweise bewusst anders als kern.py: je Trade werden die Ausstiegsbedingungen als ganze Reihen über die Haltedauer gebildet
(Stop-Niveau, das zu BEGINN jeder Kerze gilt; erste Kerze, die es berührt), statt Kerze für Kerze einen Zustand fortzuschreiben.

Regeln: Signal am Schluss der Kerze i -> Einstieg zur Eröffnung von i+1. Eine Position. Stop/Ziel in Vielfachen von sigma[i] gegen
Hoch/Tief; bei Kurslücke der schlechtere Eröffnungskurs (Stop) bzw. der Eröffnungskurs (Ziel). Trifft eine Kerze Stop und Ziel, zählt
der Stop. Nachgezogener Stop: Niveau aus dem besten Kurs der FRÜHEREN Kerzen (ab Gewinn trail_ab*sigma), Abstand trail*sigma.
Signal-Ausstieg: wert*Richtung < sx am Schluss der Kerze j -> Ausstieg Eröffnung j+1. Spätestens Eröffnung der Kerze a+halte.
Nach einem Ausstieg zur Eröffnung von b darf das Signal vom Schluss b-1 sofort wieder einsteigen (Eröffnung b); nach einem Stop
innerhalb der Kerze b frühestens das Signal vom Schluss b.
"""
import numpy as np


def ref_trades(o, h, l, ein, wert, sigma, i0, i1, halte, sl, tp, trail, trail_ab, sx):
    """Gibt Liste (a, b, d, kurs_ein, kurs_aus, innerhalb_der_kerze) zurück."""
    aus = []
    signale = np.flatnonzero(np.asarray(ein[:i1]) != 0)
    signale = signale[(signale >= i0) & (signale < i1 - 2)]
    braucht_sigma = sl > 0 or tp > 0 or trail > 0
    frueh = i0                                           # frühestes Signal, das wieder einsteigen darf
    for i in signale:
        if i < frueh:
            continue
        d = int(ein[i]); s = float(sigma[i])
        if braucht_sigma and not s > 0:
            continue
        a = i + 1
        e = float(o[a])
        letzte = min(a + halte, i1 - 1)                 # spätester Ausstieg: Eröffnung dieser Kerze
        O, H, Lo = (np.asarray(x[a:letzte], dtype=np.float64) for x in (o, h, l))
        n = len(O)
        niveau = np.full(n, np.nan)                     # Stop, der zu Beginn der Kerze gilt
        if sl > 0:
            niveau[:] = e * (1 - d * sl * s)
        if trail > 0:
            gut = np.maximum.accumulate(np.maximum(H, e)) if d > 0 else np.minimum.accumulate(np.minimum(Lo, e))   # bester Kurs bis einschl. Kerze
            nach = np.where(d * (gut / e - 1) >= trail_ab * s, gut * (1 - d * trail * s), np.nan)
            nach = np.fmax.accumulate(nach) if d > 0 else np.fmin.accumulate(nach)
            vor = np.concatenate([[np.nan], nach[:-1]])  # nur frühere Kerzen
            niveau = np.fmax(niveau, vor) if d > 0 else np.fmin(niveau, vor)
        stop_hit = (Lo <= niveau) if d > 0 else (H >= niveau)                    # NaN -> False
        if tp > 0:
            ziel = e * (1 + d * tp * s)
            ziel_hit = (H >= ziel) if d > 0 else (Lo <= ziel)
        else:
            ziel, ziel_hit = np.nan, np.zeros(n, bool)
        hit = stop_hit | ziel_hit
        k_hit = int(np.argmax(hit)) if hit.any() else n + 10
        if sx is not None and sx == sx:
            w = np.asarray(wert[a:letzte], dtype=np.float64) * d
            sig = w < sx
            k_sig = int(np.argmax(sig)) if sig.any() else n + 10
        else:
            k_sig = n + 10
        if k_hit <= k_sig and k_hit < n:                 # Stop/Ziel innerhalb der Kerze a+k_hit (Stop geht vor)
            b = a + k_hit
            if stop_hit[k_hit]:
                px = min(O[k_hit], niveau[k_hit]) if d > 0 else max(O[k_hit], niveau[k_hit])
            else:
                px = max(O[k_hit], ziel) if d > 0 else min(O[k_hit], ziel)
            innen = True
        else:
            b = min(a + k_sig + 1, letzte) if k_sig < n else letzte
            px = float(o[b]); innen = False
        aus.append((a, b, d, e, float(px), innen))
        frueh = max(b if innen else b - 1, a)
    return aus


def roh_bp(trades, fcum, slip_rt):
    return np.array([d * (px / e - 1) * 1e4 - slip_rt - d * (fcum[b] - fcum[a]) * 1e4 for a, b, d, e, px, _ in trades])
