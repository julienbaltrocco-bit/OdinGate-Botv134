"""Zweite, langsame Rechnung zu E23, geschrieben von einem unabhängigen Prüfer nur nach dem Text der Festlegung
(forschung/protokoll.md Abschnitt 43 mit Präzisierungen), in anderer Bauart als der schnelle Kern. Dient den Tests als
Vergleich: Orders und Tagesbuchung des Kerns müssen mit ihr übereinstimmen. Die Schalter für andere Lesarten
(k3_alle_schluesse, ereignis_nachholen, andere_rechenform, pause_endet_auch_ohne_pruefung) sind aus der Gegenprüfung
geblieben; maßgeblich ist die Rechnung ohne Schalter.
"""
import math
import numpy as np
NAN = float('nan')

def balken(h, l, c, m):
    n = len(c) // m
    H = np.array([h[t * m:(t + 1) * m].max() for t in range(n)])
    L = np.array([l[t * m:(t + 1) * m].min() for t in range(n)])
    C = np.array([c[(t + 1) * m - 1] for t in range(n)])
    return H, L, C

def bekannt(X, k, hoch):
    """out[t] = Niveau, das mit dem Schluss der TF-Kerze t bekannt wird (Kerze t-k), sonst nan"""
    n = len(X); out = np.full(n, np.nan)
    for j in range(k, n - k):
        li, re = X[j - k:j], X[j + 1:j + k + 1]
        ok = (X[j] > li.max() and X[j] >= re.max()) if hoch else (X[j] < li.min() and X[j] <= re.min())
        if ok:
            out[j + k] = X[j]
    return out

def gefuege(H, L, C, k):
    NH, NL = bekannt(H, k, True), bekannt(L, k, False)
    n = len(C)
    UH, UL, BR, S = np.full(n, np.nan), np.full(n, np.nan), np.zeros(n, int), np.zeros(n, int)
    lh = ll = None; s = 0; doppel = 0
    for t in range(n):
        if NH[t] == NH[t]: lh = NH[t]
        if NL[t] == NL[t]: ll = NL[t]
        up = lh is not None and C[t] > lh
        dn = ll is not None and C[t] < ll
        if up and dn: doppel += 1
        if up: BR[t], s, lh = 1, 1, None
        elif dn: BR[t], s, ll = -1, -1, None
        if lh is not None: UH[t] = lh
        if ll is not None: UL[t] = ll
        S[t] = s
    return NH, NL, UH, UL, BR, S, doppel

def sim(md, art, tf, k, n_end, k3_alle_schluesse=False, ereignis_nachholen=False, log=None, andere_rechenform=False, pause_endet_auch_ohne_pruefung=False):
    o, h, l, c, g, fs, slip = md
    m = 12 * tf
    H, L, C = balken(h[:n_end], l[:n_end], c[:n_end], m)
    NH, NL, UH, UL, BR, S, _ = gefuege(H, L, C, k)
    ol, hl, ll_, cl, gl = o.tolist(), h.tolist(), l.tolist(), c.tolist(), g.tolist()
    hc = c[11:n_end:12].tolist()
    pos = 0; pause = 0; stop = NAN; ein = NAN; best = NAN
    plan = []; orders = []
    verpasst = -1                                   # letzte TF-Kerze, deren Erstbekanntwerden schon verarbeitet wurde
    for i in range(n_end):
        for was, grund, p, st in plan:
            if was == 'zu':
                orders.append((i, -pos, grund, ol[i])); pos = 0
            else:
                orders.append((i, p, grund, ol[i])); pos = p; ein = ol[i]; stop = st; best = ol[i]
        plan = []
        if art == 'K3' and k3_alle_schluesse and pos != 0:
            best = max(best, cl[i]) if pos > 0 else min(best, cl[i])
        if i + 1 >= n_end:
            break
        if not (gl[i] and gl[i + 1]):
            if pause_endet_auch_ohne_pruefung and pause != 0:
                nh_ = i // 12 - 1
                if nh_ >= 336:
                    x_ = hc[nh_] - hc[nh_ - 336]
                    if (1 if x_ > 0 else (-1 if x_ < 0 else 0)) != pause: pause = 0
            continue
        nh = i // 12 - 1
        d = 0
        if nh >= 336:
            x = hc[nh] - hc[nh - 336]
            d = 1 if x > 0 else (-1 if x < 0 else 0)
        t = i // m - 1
        erst = t >= 0 and (t + 1) * m == i
        if ereignis_nachholen and t >= 0 and t > verpasst:
            erst_t = list(range(verpasst + 1, t + 1))   # alle seit der letzten Pruefung bekannt gewordenen TF-Kerzen
        else:
            erst_t = [t] if erst else []
        verpasst = max(verpasst, t)
        if pause != 0 and d != pause:
            pause = 0
        pause_vorher = pause != 0
        grund = None
        if pos != 0 and pos == d:
            if art in ('V1', 'V2'):
                for tt in erst_t:
                    lv = NH[tt] if pos < 0 else NL[tt]
                    if lv == lv:
                        if pos < 0 and lv < stop and lv > cl[i]:
                            if log is not None: log.append(('nachruecken', i, stop, lv))
                            stop = lv
                        if pos > 0 and lv > stop and lv < cl[i]:
                            if log is not None: log.append(('nachruecken', i, stop, lv))
                            stop = lv
                if (pos < 0 and cl[i] > stop) or (pos > 0 and cl[i] < stop):
                    grund = 'stop'
                    if log is not None: log.append(('stop', i, stop, cl[i]))
            elif art in ('K1', 'K2') and andere_rechenform:
                if art == 'K2' and ((pos > 0 and cl[i] >= ein * 1.15) or (pos < 0 and cl[i] <= ein * 0.85)): grund = 'ziel'
                elif (pos > 0 and cl[i] <= ein * 0.95) or (pos < 0 and cl[i] >= ein * 1.05): grund = 'stop'
            elif art == 'K3' and andere_rechenform:
                best = max(best, cl[i]) if pos > 0 else min(best, cl[i])
                if (pos > 0 and cl[i] <= best * 0.95) or (pos < 0 and cl[i] >= best * 1.05): grund = 'nachzug'
            elif art in ('K1', 'K2'):
                r = pos * (cl[i] / ein - 1.0)
                if art == 'K2' and r >= 0.15: grund = 'ziel'
                elif r <= -0.05: grund = 'stop'
            elif art == 'K3':
                best = max(best, cl[i]) if pos > 0 else min(best, cl[i])
                if pos * (cl[i] / best - 1.0) <= -0.05: grund = 'nachzug'
            if grund: pause = pos
        wieder = False
        if art == 'B0':
            soll = d
        elif art == 'V3':
            soll = d if (d != 0 and t >= 0 and S[t] == d) else 0
        else:
            soll = d
            if pause != 0:
                soll = 0
                if art == 'V2' and pause_vorher and any(BR[tt] == d for tt in erst_t):
                    soll, pause, wieder = d, 0, True
        if soll != pos:
            if pos != 0:
                plan.append(('zu', grund or ('filter' if (art == 'V3' and pos == d) else 'signalwechsel'), 0, NAN))
            if soll != 0:
                st = NAN
                if art in ('V1', 'V2'):
                    w = (2 * k + 1) * m
                    if soll < 0:
                        lv = UH[t] if t >= 0 else NAN
                        st = lv if (lv == lv and lv > cl[i]) else max(hl[max(0, i - w + 1):i + 1])
                    else:
                        lv = UL[t] if t >= 0 else NAN
                        st = lv if (lv == lv and lv < cl[i]) else min(ll_[max(0, i - w + 1):i + 1])
                    if log is not None: log.append(('einstieg', i, soll, st, lv, cl[i], 'wieder' if wieder else 'neu'))
                plan.append(('auf', 'wiedereinstieg' if wieder else 'einstieg', soll, st))
    return orders

def buchung(md, orders, n_end, TAG=288):
    """Tagesreihen je Richtung nur aus der Orderliste: brutto (Kurs+Funding), Orders, Slippage bp, Kerzen im Markt"""
    o, h, l, c, g, fs, slip = md
    nt = len(c) // TAG + 1
    brut, nord, slipb, markt = np.zeros((2, nt)), np.zeros((2, nt)), np.zeros((2, nt)), np.zeros(nt)
    offen = None
    def halte(a, b, p, e, zu):
        r = 0 if p > 0 else 1
        js = np.arange(a, b)                                   # Kerzen mit Position am Schluss
        marken = np.concatenate([[o[a]], c[a:b]])
        np.add.at(brut[r], js // TAG, p * np.diff(marken) / e)
        np.add.at(markt, js // TAG, 1)
        if zu:
            brut[r, b // TAG] += p * (o[b] - (c[b - 1] if b > a else o[a])) / e
        fj = np.arange(a + 1, b + 1 if zu else b)
        np.add.at(brut[r], fj // TAG, -p * fs[fj])
    for x, seite, grund, kurs in orders:
        sb = max(slip, 0.05 * (h[x - 1] - l[x - 1]) / c[x - 1] * 1e4)
        if grund in ('einstieg', 'wiedereinstieg'):
            assert offen is None
            offen = (x, seite, kurs)
            r = 0 if seite > 0 else 1
        else:
            a, p, e = offen
            assert seite == -p
            halte(a, x, p, e, True)
            r = 0 if p > 0 else 1
            offen = None
        nord[r, x // TAG] += 1; slipb[r, x // TAG] += sb
    if offen is not None:
        a, p, e = offen
        halte(a, n_end, p, e, False)
    return brut, nord, slipb, markt
