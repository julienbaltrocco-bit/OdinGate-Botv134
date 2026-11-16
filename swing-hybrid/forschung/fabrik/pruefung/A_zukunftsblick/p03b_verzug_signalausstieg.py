"""kern.sim mit verzug=1 und Signal-Ausstieg: um wie viele Kerzen verschiebt sich der Ausstieg?

Künstliche Reihe: Kurs o[k] = 100 + k (so lässt sich die Ausstiegskerze aus dem Ergebnis ablesen), Einstiegssignal am Schluss von
Kerze 10, Signalwert fällt am Schluss von Kerze 20 unter die Ausstiegsschwelle. Erwartung laut Docstring ("zusätzliche Kerzen
Verzögerung für Ein- und Ausstieg"): verzug=0 -> ein 11, aus 21; verzug=1 -> ein 12, aus 22.
"""
import sys
sys.path.insert(0, 'forschung')
import numpy as np
from fabrik import kern as FK

n = 400
o = 100.0 + np.arange(n); h = o + 0.5; l = o - 0.5
f = np.zeros(n); sig = np.ones(n, np.float32); tag = np.zeros(n, np.int32)
ein = np.zeros(n, np.int8); ein[10] = 1
wert = np.full(n, 2.0); wert[20:] = 0.0                       # ab Schluss von Kerze 20 unter sx = 0.5
for verzug in (0, 1, 2):
    z = [np.zeros(1) for _ in range(6)]
    k = FK.sim(o, h, l, f, ein, wert, sig, tag, 0, n, 144, 0.0, 0.0, 0.0, 0.0, 0.5, 0.0, 2.4, *z, verzug)
    a = 11 + verzug
    b = int(round((z[0][0] / 1e4 + 1) * o[a] - 100))          # aus roh = (o[b]/o[a]-1)*1e4
    print(f"verzug={verzug}: Trades {k}, Einstieg Kerze {a}, Ausstieg Kerze {b} (Dauer {int(z[5][0])}); erwartet Ausstieg {21 + verzug} -> Abweichung {b - (21 + verzug)} Kerze(n)")
# Zeitausstieg zum Vergleich (ohne Signal-Ausstieg): hier stimmt die Verschiebung
for verzug in (0, 1):
    z = [np.zeros(1) for _ in range(6)]
    FK.sim(o, h, l, f, ein, wert, sig, tag, 0, n, 12, 0.0, 0.0, 0.0, 0.0, np.nan, 0.0, 2.4, *z, verzug)
    a = 11 + verzug
    print(f"Zeitausstieg verzug={verzug}: Einstieg {a}, Ausstieg {int(round((z[0][0] / 1e4 + 1) * o[a] - 100))} (erwartet {23 + verzug})")
