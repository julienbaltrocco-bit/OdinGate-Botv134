"""Schritt 2: fabrik.kern.sim auf kleinen, von Hand gebauten Reihen gegen die Regeln aus Abschnitt 19 (Erwartung von Hand gerechnet)."""
import sys
import numpy as np
sys.path.insert(0, 'forschung')
from fabrik import kern as FK

def lauf(o, h, l, frate, ein, wert=None, sigma=None, halte=3, sl=0.0, tp=0.0, trail=0.0, trail_ab=0.0, sx=np.nan, slip_rt=0.0, verzug=0, i1=None):
    n = len(o)
    o, h, l = (np.asarray(x, float) for x in (o, h, l))
    fcum = np.cumsum(np.asarray(frate, float))
    ein = np.asarray(ein, np.int8)
    wert = np.zeros(n) if wert is None else np.asarray(wert, float)
    sigma = np.full(n, 0.01, np.float32) if sigma is None else np.asarray(sigma, np.float32)
    tag = np.arange(n, dtype=np.int32)                      # jede Kerze ein eigener "Tag": so sieht man jeden Trade einzeln (Tag = Einstiegskerze)
    z = [np.zeros(n) for _ in range(6)]
    k = FK.sim(o, h, l, fcum, ein, wert, sigma, tag, 0, n if i1 is None else i1, halte, sl, tp, trail, trail_ab, sx, slip_rt, 2.4, *z, verzug)
    return k, {int(t): (round(float(z[0][t]), 4), int(z[5][t])) for t in np.flatnonzero(z[1])}, z

ok_alle = True
def pruef(name, ist, soll):
    global ok_alle
    gut = ist == soll
    ok_alle &= gut
    print(f"{'OK  ' if gut else 'FEHL'} {name}: ist {ist} | soll {soll}")

N = 12
flach = [100.0] * N
null = [0.0] * N
e1 = [1] + [0] * (N - 1)

# 1 Slippage und Gebühr: flacher Kurs, slip_bp 1,5 je Order -> 2 Orders = 3,0 bp; netto85 = -3,0 - 2,4
k, t, z = lauf(flach, flach, flach, null, e1, slip_rt=2 * 1.5)
pruef("1 Slippage 2 Orders x slip_bp, roh vor Gebühr", t, {1: (-3.0, 3)})
pruef("1 netto mit Rebate = roh - 2,4 (Verlustsumme)", round(float(z[4][1]), 4), -5.4)

# 2 Funding: Einstieg Eröffnung Kerze 1, Ausstieg Eröffnung Kerze 4. Raten: Kerze 1 = 10 bp, Kerze 3 = 1 bp, Kerze 4 = 100 bp, Kerze 5 = 1000 bp
fr = [0, 10e-4, 0, 1e-4, 100e-4, 1000e-4] + [0] * (N - 6)
k, t, z = lauf(flach, flach, flach, fr, e1)
pruef("2 Funding Long: zahlt Termine NACH Einstieg bis EINSCHLIESSLICH Ausstiegskerze (1+100), nicht den Termin der Einstiegskerze", t, {1: (-101.0, 3)})
k, t, z = lauf(flach, flach, flach, fr, [-1] + [0] * (N - 1))
pruef("2 Funding Short: erhält dieselben Termine", t, {1: (101.0, 3)})

# 3 Stop bei Kurslücke (Long, Stop 1 sigma = 1 % unter 100 = 99): Kerze 2 eröffnet 97, Tief 96 -> 97; ohne Lücke: Eröffnung 99,5 Tief 98 -> 99
o = flach[:]; h = flach[:]; l = flach[:]
o[2], h[2], l[2] = 97.0, 97.5, 96.0
k, t, z = lauf(o, h, l, null, e1, halte=6, sl=1.0)
pruef("3 Stop Long mit Lücke -> Eröffnungskurs 97 = -300 bp", t, {1: (-300.0, 1)})
o[2], h[2], l[2] = 99.5, 99.6, 98.0
k, t, z = lauf(o, h, l, null, e1, halte=6, sl=1.0)
pruef("3 Stop Long ohne Lücke -> Stopkurs 99 = -100 bp", t, {1: (-100.0, 1)})
o = flach[:]; h = flach[:]; l = flach[:]
o[2], h[2], l[2] = 103.0, 104.0, 102.5
k, t, z = lauf(o, h, l, null, [-1] + [0] * (N - 1), halte=6, sl=1.0)
pruef("3 Stop Short mit Lücke nach oben -> Eröffnungskurs 103 = -300 bp", t, {1: (-300.0, 1)})

# 4 Stop und Ziel in derselben Kerze -> Stop zählt
o = flach[:]; h = flach[:]; l = flach[:]
h[2], l[2] = 102.0, 98.0
k, t, z = lauf(o, h, l, null, e1, halte=6, sl=1.0, tp=1.0)
pruef("4 Stop vor Ziel in derselben Kerze (Long)", t, {1: (-100.0, 1)})
k, t, z = lauf(o, h, l, null, [-1] + [0] * (N - 1), halte=6, sl=1.0, tp=1.0)
pruef("4 Stop vor Ziel in derselben Kerze (Short)", t, {1: (-100.0, 1)})
# 4b Stop und Ziel schon in der Einstiegskerze
o = flach[:]; h = flach[:]; l = flach[:]
h[1], l[1] = 102.0, 98.0
k, t, z = lauf(o, h, l, null, e1, halte=6, sl=1.0, tp=1.0)
pruef("4b Stop in der Einstiegskerze", t, {1: (-100.0, 0)})
# 4c Ziel mit günstiger Lücke -> Eröffnungskurs (besser als Ziel)
o = flach[:]; h = flach[:]; l = flach[:]
o[2], h[2], l[2] = 103.0, 103.5, 102.9
k, t, z = lauf(o, h, l, null, e1, halte=6, tp=1.0)
pruef("4c Ziel Long mit Lücke nach oben -> Eröffnung 103 (+300 statt +100)", t, {1: (300.0, 1)})

# 5 Ausstieg am Datenende: Signal an Kerze 8 von 12, Haltedauer 6 -> Ausstieg zur Eröffnung der letzten Kerze 11
o = [100.0 + i for i in range(N)]
k, t, z = lauf(o, o, o, null, [0] * 8 + [1] + [0] * 3, halte=6)
pruef("5 Datenende: Einstieg Eröffnung 9 (109), Ausstieg Eröffnung 11 (111)", t, {9: (round((111 / 109 - 1) * 1e4, 4), 2)})
k, t, z = lauf(o, o, o, null, [0] * 10 + [1, 1], halte=6)
pruef("5 Datenende: Signale in den letzten 2 Kerzen (10, 11) werden nicht mehr gehandelt (kein Einstieg ohne spätere Ausstiegskerze)", (k, t), (0, {}))
k, t, z = lauf(o, o, o, null, [0] * 9 + [1, 1, 1], halte=6)
pruef("5 Datenende: Signal an Kerze 9 -> Einstieg 10 (110), Ausstieg Eröffnung 11 (111), Dauer 1 statt 6", (k, t), (1, {10: (round((111 / 110 - 1) * 1e4, 4), 1)}))

# 6 Eine Position je Coin: Dauersignal, Haltedauer 3 -> Einstiege an Kerze 1, 4, 7 (Ausstieg und neuer Einstieg zur selben Eröffnung), keine Überlappung
k, t, z = lauf(flach, flach, flach, null, [1] * N, halte=3, slip_rt=1.0)
pruef("6 Dauersignal: Einstiege 1, 4, 7 (je voll bezahlt), letzter 10 -> 11 am Datenende? (i < n-2 = 10: Signal 9 zählt)", (k, t), (4, {1: (-1.0, 3), 4: (-1.0, 3), 7: (-1.0, 3), 10: (-1.0, 1)}))
# 6b Nach Stop innerhalb der Kerze b: neuer Einstieg erst zur Eröffnung von b+1 (nicht noch einmal in b)
o = flach[:]; h = flach[:]; l = flach[:]
l[2] = 98.0
k, t, z = lauf(o, h, l, null, [1] * N, halte=3, sl=1.0)
pruef("6b nach Stop in Kerze 2: nächster Einstieg Kerze 3", sorted(t)[:2], [1, 3])

# 7 Signal-Ausstieg: Wert unter 0,5 am Schluss der Kerze 2 -> Ausstieg zur Eröffnung von Kerze 3
o = [100.0, 100.0, 101.0, 102.0, 103.0, 104.0, 105.0, 106.0, 107.0, 108.0, 109.0, 110.0]
w = [2.0, 2.0, 0.4, 2.0, 2.0, 2.0, 2.0, 2.0, 2.0, 2.0, 2.0, 2.0]
k, t, z = lauf(o, o, o, null, e1, wert=w, halte=8, sx=0.5)
pruef("7 Signal-Ausstieg ohne Verzug: Einstieg 1 (100), Signal fällt an Kerze 2, Ausstieg Eröffnung 3 (102)", t, {1: (200.0, 2)})
k, t, z = lauf(o, o, o, null, e1, wert=w, halte=8, sx=0.5, verzug=1)
print("     7 mit verzug=1: Einstieg an Kerze", list(t), "Dauer", list(t.values())[0][1], "-> Ausstieg an Kerze", list(t)[0] + list(t.values())[0][1],
      "| erwartet bei EINER Kerze Verzögerung: Einstieg 2, Ausstieg 4 (Signal Kerze 2 -> Eröffnung 3 + 1)")
k, t, z = lauf(o, o, o, null, e1, halte=3, verzug=1)
pruef("7 Zeit-Ausstieg mit verzug=1: Einstieg 2 (101), Ausstieg 5 (104)", t, {2: (round((104 / 101 - 1) * 1e4, 4), 3)})

# 8 Nachzug kennt nur frühere Kerzen: Kerze 2 Hoch 103 und Tief 99 (unter dem neuen Stop 103*(1-0,01)=101,97) -> kein Ausstieg in Kerze 2; Kerze 3 eröffnet 100 -> Ausstieg 100
o = flach[:]; h = flach[:]; l = flach[:]
h[2], l[2] = 103.0, 99.5
k, t, z = lauf(o, h, l, null, e1, halte=8, trail=1.0, trail_ab=1.0)
pruef("8 Nachzug: Stop aus Kerze 2 wirkt ab Kerze 3; Kerze 3 eröffnet unter dem Stop -> Eröffnung 100 (0 bp), Dauer 2", t, {1: (0.0, 2)})
print("ALLE SYNTHETISCHEN PRÜFUNGEN OK:", ok_alle)
