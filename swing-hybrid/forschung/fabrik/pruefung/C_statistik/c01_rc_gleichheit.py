"""C01 Reality Check und PBO: die ECHTE trichter.statistik() auf künstlichen Datenbanken gegen die eigene Nachrechnung.
Gleiche Zufallszahlen (Startwert 19, gleiche Reihenfolge der Ziehungen) -> die Zahlen müssen übereinstimmen."""
import sys, math
import numpy as np
sys.path.insert(0, 'forschung/fabrik/pruefung/C_statistik')
import c_lib as C
from fabrik import lauf as L

rng = np.random.default_rng(1)
print("Code-Stand:", C.stand())
for braucht in ("k", "t"):
    seg = L.SEGMENTE[braucht]
    d0, d1, e1 = seg
    for fall in range(3):
        n = 1500
        X = rng.normal(0, 1, (n, L.N_TAGE))
        if fall == 1:                                   # dünn besetzt und schief
            X = np.where(rng.random(X.shape) < 0.25, np.exp(rng.normal(0, 1, X.shape)) - math.exp(0.5), 0.0)
        if fall == 2:                                   # ein Kandidat mit echtem Vorteil, einer ohne jede Streuung
            X[7] += 0.25
            X[9] = 0.0
        X[:, :d0] = 0.0                                 # vor Beginn von T steht in den echten Reihen null
        C.kuenstliche_welt(n, braucht)
        echt = C.echte_statistik(X)
        X32 = X.astype(np.float32).astype(np.float64)
        idx = C.gewichte(d1 - d0, 400, 10, np.random.default_rng(19))
        tb, p, mx = C.rc_eigen(X32[:, d0:d1], idx)
        pbo, verl, nk = C.pbo_eigen(X32, d0, e1)
        gleich = (abs(echt["bester_t_wert_T"] - round(tb, 2)) < 0.011 and abs(echt["reality_check_p"] - p) < 1e-9 and abs(echt["zufalls_maximum_median"] - np.median(mx)) < 0.011
                  and abs(echt["zufalls_maximum_95"] - np.percentile(mx, 95)) < 0.011 and abs(echt["pbo"] - pbo) < 0.0006 and abs(echt["bester_verliert_im_anderen_teil"] - verl) < 0.0006)
        print(f"Gruppe {braucht} Fall {fall}: trichter t_best {echt['bester_t_wert_T']} p {echt['reality_check_p']} Median {echt['zufalls_maximum_median']} 95% {echt['zufalls_maximum_95']} "
              f"PBO {echt['pbo']} verliert {echt['bester_verliert_im_anderen_teil']} | eigen t_best {tb:.3f} p {p:.4f} Median {np.median(mx):.3f} 95% {np.percentile(mx, 95):.3f} "
              f"PBO {pbo:.3f} verliert {verl:.3f} ({nk} Kombinationen) ->", "GLEICH" if gleich else "ABWEICHUNG")
