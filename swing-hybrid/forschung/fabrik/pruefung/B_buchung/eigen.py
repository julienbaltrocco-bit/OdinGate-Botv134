"""Eigener Simulator der Prüfung B (reines Python/numpy, ohne fabrik.kern), geschrieben nach protokoll.md Abschnitt 19:

- Signal am Schluss der Kerze i, Einstieg zur Eröffnung von i+1, alle Orders Taker.
- Eine Position je Coin: ein neuer Einstieg ist frühestens zur Eröffnung der Kerze möglich, zu deren Eröffnung die alte
  Position endet (Zeit- und Signal-Ausstieg), bzw. erst in der Kerze NACH einem Stop/Ziel innerhalb einer Kerze.
- Stop und Ziel in Einheiten der Stundenschwankung am Signal (sigma[i]); Stop gegen Hoch/Tief jeder Kerze, bei Lücke
  der schlechtere Eröffnungskurs; trifft eine Kerze Stop und Ziel, zählt der Stop.
- Nachzug: der Stop der Kerze j kennt nur Hoch/Tief bis j-1.
- Signal-Ausstieg: ausgerichteter Signalwert am Schluss der Kerze j unter sx -> Ausstieg zur Eröffnung von j+1.
- Zeit-Ausstieg zur Eröffnung der Kerze a+halte; am Datenende zur Eröffnung der letzten Kerze.
- Funding: jede Rate, deren Termin nach dem Einstieg und bis einschließlich der Ausstiegskerze liegt; Long zahlt positive Rate.
- roh (bp) = Kursbewegung - Slippage (slip_bp je Order mal 2 Orders) - Funding. Gebühr 16 bp, mit 85 % Rebate 2,4 bp.
- Buchung auf den Tag des Einstiegs (kern.py-Dokumentation).
"""
import numpy as np


def trades(o, h, l, frate_kerze, ein, wert, sigma, i0, i1, halte, sl, tp, trail, trail_ab, sx, verzug=0, sx_doppelt=True):
    """Gibt eine Liste von Trades zurück: (Signalkerze, Einstiegskerze, Ausstiegskerze, Richtung, Einstiegskurs, Ausstiegskurs,
    Art, Funding in bp aus Sicht des Trades (negativ = gezahlt)). frate_kerze[k] = Funding-Rate, deren Termin in Kerze k liegt."""
    braucht_sigma = sl > 0 or tp > 0 or trail > 0
    kand = np.flatnonzero(np.asarray(ein[i0:max(i0, i1 - 2 - verzug)])) + i0
    frei = -1
    aus = []
    for i in kand:
        i = int(i)
        a = i + 1 + verzug
        if a < frei:
            continue
        d = int(ein[i])
        s = float(sigma[i])
        if braucht_sigma and not (s > 0):
            continue
        e = float(o[a])
        stop = e * (1 - d * sl * s) if sl > 0 else None
        ziel = e * (1 + d * tp * s) if tp > 0 else None
        plan = min(a + halte, i1 - 1)
        guenstigst = e
        b, px, art = None, None, None
        j = a
        while j < plan:
            oj, hj, lj = float(o[j]), float(h[j]), float(l[j])
            if stop is not None:
                if d == 1 and lj <= stop:
                    b, px, art = j, (oj if oj < stop else stop), "stop"
                    break
                if d == -1 and hj >= stop:
                    b, px, art = j, (oj if oj > stop else stop), "stop"
                    break
            if ziel is not None:
                if d == 1 and hj >= ziel:
                    b, px, art = j, (oj if oj > ziel else ziel), "ziel"
                    break
                if d == -1 and lj <= ziel:
                    b, px, art = j, (oj if oj < ziel else ziel), "ziel"
                    break
            if d == 1:
                guenstigst = max(guenstigst, hj)
            else:
                guenstigst = min(guenstigst, lj)
            if trail > 0 and d * (guenstigst / e - 1) >= trail_ab * s:
                neu = guenstigst * (1 - d * trail * s)
                if stop is None:
                    stop = neu
                elif d == 1:
                    stop = max(stop, neu)
                else:
                    stop = min(stop, neu)
            if sx is not None and float(wert[j - verzug]) * d < sx:
                # sx_doppelt=True bildet kern.sim nach (Signal der Kerze j-verzug gelesen UND Ausstieg erst j+1+verzug = 2*verzug Kerzen später);
                # sx_doppelt=False ist genau EINE Kerze Verzögerung je verzug: Signal am Schluss von s=j-verzug -> Ausstieg zur Eröffnung s+1+verzug = j+1
                b, art = min(j + 1 + (verzug if sx_doppelt else 0), plan), "signal"
                px = float(o[b])
                break
            j += 1
        if b is None:
            b, px = plan, float(o[plan])
            art = "datenende" if a + halte > i1 - 1 else "zeit"
        fund = -d * float(frate_kerze[a + 1:b + 1].sum()) * 1e4
        aus.append((i, a, b, d, e, px, art, fund))
        frei = b if art in ("zeit", "signal", "datenende") else b + 1
    return aus


def tagesfelder(tr, slip_rt, tag_von, n_tage):
    """Trades eines Coins -> je Tag (Tag des Einstiegs): Summe roh, Zahl der Trades. slip_rt = Slippage für Ein- und Ausstieg zusammen."""
    roh_tag, n_tag = np.zeros(n_tage), np.zeros(n_tage)
    liste = []
    for (i, a, b, d, e, px, art, fund) in tr:
        roh = d * (px / e - 1) * 1e4 - slip_rt + fund
        t = (a - tag_von) // 288
        roh_tag[t] += roh
        n_tag[t] += 1
        liste.append(roh)
    return roh_tag, n_tag, np.array(liste)


def kennzahlen(roh_tag, n_tag, slip_rt, d0, d1, kosten=2.4):
    """roh_tag, n_tag: Felder [Coins des Marktes, Tage]; slip_rt je Coin des Marktes. Eigene Rechnung nach Abschnitt 19."""
    r, n = roh_tag[:, d0:d1], n_tag[:, d0:d1]
    nt = n.sum()
    if nt == 0:
        return dict(n=0, roh=0.0, n85=0.0, t_roh=0.0, t85=0.0, n85_2x=0.0)
    m = r.shape[0]
    tage = d1 - d0
    p_roh = r.sum(0) / m
    p85 = (r.sum(0) - kosten * n.sum(0)) / m
    t = lambda p: float(p.mean() / (p.std(ddof=1) / np.sqrt(tage))) if p.std(ddof=1) > 0 else 0.0
    roh = r.sum() / nt
    return dict(n=int(nt), roh=roh, n85=roh - kosten, t_roh=t(p_roh), t85=t(p85),
                n85_2x=roh - kosten - float((n.sum(1) * slip_rt).sum() / nt))
