"""Schneller Simulator der Fabrik (numba): ein Coin, eine Einstiegsreihe, eine Ausstiegsregel -> Tagesergebnisse.

Regeln wie in protokoll.md Abschnitt 19: Signal am Schluss der Kerze i, Einstieg zur Eröffnung von i+1, eine Position
je Coin. Stops gegen Hoch und Tief jeder Kerze (bei Kurslücke der schlechtere Eröffnungskurs); trifft eine Kerze Stop
und Ziel, zählt der Stop. Der nachgezogene Stop kennt nur frühere Kerzen. Ergebnis je Trade in Basispunkten nach
Slippage und Funding, vor Gebühr ("roh"); gebucht auf den Tag des Einstiegs.
"""
import numpy as np
from numba import njit

NAN = np.nan


@njit(cache=True, nogil=True)
def sim(o, h, l, fcum, ein, wert, sigma, tag, i0, i1, halte, sl, tp, trail, trail_ab, sx, slip, kosten85,
        roh_tag, n_tag, gew_tag, pos_tag, neg_tag, dauer_tag, verzug):
    """ein[i]: gewünschte Richtung am Schluss der Kerze i (+1/-1/0). wert[i]*Richtung < sx beendet den Trade (sx = nan: aus).
    slip[i]: Slippage in bp für eine Order, die nach dem Schluss der Kerze i gestellt wird (Einstieg: Kerze vor dem Einstieg,
    Ausstieg: Kerze vor dem Ausstieg). verzug: zusätzliche Kerzen Verzögerung für Ein- und Ausstieg zur Eröffnung (Stress).
    Gibt die Zahl der Trades zurück."""
    stops = sl > 0 or tp > 0 or trail > 0
    i, n, schlimmst = i0, 0, 0.0
    while i < i1 - 2 - verzug:
        d = ein[i]
        if d == 0:
            i += 1
            continue
        a = i + 1 + verzug
        s = sigma[i]
        if stops and not (s > 0):
            i += 1
            continue
        e = o[a]
        stop = e * (1 - d * sl * s) if sl > 0 else NAN
        ziel = e * (1 + d * tp * s) if tp > 0 else NAN
        best, b, px = e, -1, NAN
        ende = min(a + halte, i1 - 1)
        j = a
        while j < ende:
            if stop == stop:
                if d > 0 and l[j] <= stop:
                    px = min(o[j], stop); b = j; break
                if d < 0 and h[j] >= stop:
                    px = max(o[j], stop); b = j; break
            if ziel == ziel:
                if d > 0 and h[j] >= ziel:
                    px = max(o[j], ziel); b = j; break
                if d < 0 and l[j] <= ziel:
                    px = min(o[j], ziel); b = j; break
            best = max(best, h[j]) if d > 0 else min(best, l[j])
            if trail > 0 and d * (best / e - 1) >= trail_ab * s:
                neu = best * (1 - d * trail * s)
                if stop != stop:
                    stop = neu
                else:
                    stop = max(stop, neu) if d > 0 else min(stop, neu)
            if sx == sx and wert[j - verzug] * d < sx:          # Signal am Schluss der Kerze j-verzug -> Ausstieg zur Eröffnung von j+1
                b = min(j + 1, ende); break
            j += 1
        am_open = px != px
        if b < 0:
            b = ende
        if am_open:
            px = o[b]
        roh = d * (px / e - 1) * 1e4 - slip[a - 1] - slip[b - 1] - d * (fcum[b] - fcum[a]) * 1e4
        t = tag[a]
        roh_tag[t] += roh
        n_tag[t] += 1
        n85 = roh - kosten85
        if n85 > 0:
            gew_tag[t] += 1; pos_tag[t] += n85
        else:
            neg_tag[t] += n85
        dauer_tag[t] += b - a
        n += 1
        i = b - 1 - verzug if am_open else b - verzug
        if i < a - verzug:
            i = a - verzug
    return n


@njit(cache=True, nogil=True)
def trades_liste(o, h, l, fcum, ein, wert, sigma, i0, i1, halte, sl, tp, trail, trail_ab, sx, slip, aus):
    """Wie sim, aber mit Einzel-Trades (für Paritätstest, Risikoprüfung, Papier-Tests). aus: Feld [k, 6] =
    Einstiegskerze, Ausstiegskerze, Richtung, roh (bp), ungünstigster Kurs im Trade (bp), 1 wenn noch offen."""
    stops = sl > 0 or tp > 0 or trail > 0
    i, n = i0, 0
    while i < i1 - 2 and n < aus.shape[0]:
        d = ein[i]
        if d == 0:
            i += 1
            continue
        a = i + 1
        s = sigma[i]
        if stops and not (s > 0):
            i += 1
            continue
        e = o[a]
        stop = e * (1 - d * sl * s) if sl > 0 else NAN
        ziel = e * (1 + d * tp * s) if tp > 0 else NAN
        best, b, px, tief = e, -1, NAN, 0.0
        ende = min(a + halte, i1 - 1)
        j = a
        while j < ende:
            adv = d * ((l[j] if d > 0 else h[j]) / e - 1) * 1e4
            tief = min(tief, adv)
            if stop == stop:
                if d > 0 and l[j] <= stop:
                    px = min(o[j], stop); b = j; break
                if d < 0 and h[j] >= stop:
                    px = max(o[j], stop); b = j; break
            if ziel == ziel:
                if d > 0 and h[j] >= ziel:
                    px = max(o[j], ziel); b = j; break
                if d < 0 and l[j] <= ziel:
                    px = min(o[j], ziel); b = j; break
            best = max(best, h[j]) if d > 0 else min(best, l[j])
            if trail > 0 and d * (best / e - 1) >= trail_ab * s:
                neu = best * (1 - d * trail * s)
                if stop != stop:
                    stop = neu
                else:
                    stop = max(stop, neu) if d > 0 else min(stop, neu)
            if sx == sx and wert[j] * d < sx:
                b = j + 1; break
            j += 1
        am_open = px != px
        offen = 0.0
        if b < 0:
            b = ende
            if a + halte > i1 - 1:
                offen = 1.0                                   # Daten enden vor dem regulären Ausstieg
        elif b > ende:
            b = ende
        if am_open:
            px = o[b]
        aus[n, 0], aus[n, 1], aus[n, 2] = a, b, d
        aus[n, 3] = d * (px / e - 1) * 1e4 - slip[a - 1] - slip[b - 1] - d * (fcum[b] - fcum[a]) * 1e4
        aus[n, 4], aus[n, 5] = tief, offen
        n += 1
        i = max(b - 1 if am_open else b, a)
    return n
