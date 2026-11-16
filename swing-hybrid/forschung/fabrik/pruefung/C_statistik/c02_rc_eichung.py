"""C02 Eichung des Reality Check wie in trichter.statistik (zentriert, durch die FESTE Streuung der Originalreihe geteilt).
(a) Welten ohne jeden Vorteil -> der p-Wert muss etwa gleichverteilt sein (Anteil p <= 0,05 nahe 5 %).
(b) ein Kandidat mit echtem Vorteil -> kleiner p-Wert.
Verglichen wird mit der Variante, bei der jede Bootstrap-Stichprobe durch ihre eigene Streuung geteilt wird (so ist die Prüfgröße
der echten Daten gebildet: Mittel / eigene Streuung)."""
import sys, math, time
import numpy as np
from scipy import stats
sys.path.insert(0, 'forschung/fabrik/pruefung/C_statistik')
import c_lib as C
from fabrik import lauf as L

TAGE, B, BLOCK = 685, 400, 10


def idx_schnell(tage, B, block, rng):
    """Stationärer Bootstrap, vektorisiert (gleiche Verteilung wie c_lib.gewichte)."""
    neu = rng.random((B, tage)) < 1.0 / block
    neu[:, 0] = True
    starts = rng.integers(0, tage, (B, tage))
    lauf = np.arange(tage)[None, :]
    letzter = np.maximum.accumulate(np.where(neu, lauf, 0), axis=1)
    return (np.take_along_axis(starts, letzter, 1) + lauf - letzter) % tage


def welt(art, n, rng, echt=None):
    if art == "normal":
        return rng.normal(0, 1, (n, TAGE))
    if art in ("schief+", "schief-", "gemischt"):
        aktiv = rng.random((n, TAGE)) < 0.25
        x = np.where(aktiv, np.exp(rng.normal(0, 1, (n, TAGE))) - math.exp(0.5), 0.0)      # Erwartungswert genau null
        if art == "schief-":
            x = -x
        if art == "gemischt":
            x[: n // 2] *= -1
        return x
    if art == "echt":                                   # echte Tagesreihen (T), je Reihe auf Mittel null gesetzt, Tage blockweise neu gezogen
        ix = idx_schnell(TAGE, 1, BLOCK, rng)[0]
        return echt[:, ix]
    raise ValueError(art)


def lauf(art, n, wiederholungen, rng, echt=None, vorteil_t=None):
    ps, ps2, tb, md = [], [], [], []
    for w in range(wiederholungen):
        X = welt(art, n, rng, echt)
        if vorteil_t is not None:
            X[0] = X[0] + vorteil_t / math.sqrt(TAGE) * X[0].std(ddof=1)
        idx = idx_schnell(TAGE, B, BLOCK, rng)
        t1, p1, m1 = C.rc_gewichte(X, idx)
        t2, p2, m2 = C.rc_gewichte(X, idx, selbst=True)
        ps.append(p1); ps2.append(p2); tb.append(t1); md.append(np.median(m1))
    ps, ps2 = np.array(ps), np.array(ps2)
    f = lambda p: f"p<=0,05: {np.mean(p <= 0.05):.3f}  p<=0,10: {np.mean(p <= 0.10):.3f}  p<=0,50: {np.mean(p <= 0.5):.3f}  Mittel {p.mean():.3f}  KS-p {stats.kstest(p, 'uniform').pvalue:.4f}"
    print(f"{art:<9} n={n} Wdh={wiederholungen}{'' if vorteil_t is None else f' Vorteil t={vorteil_t}'}: bestes t im Mittel {np.mean(tb):.2f}, Bootstrap-Maximum (Median) im Mittel {np.mean(md):.2f}")
    print(f"     wie trichter (feste Streuung):  {f(ps)}")
    print(f"     eigene Streuung je Stichprobe:  {f(ps2)}", flush=True)
    return ps, ps2


if __name__ == "__main__":
    rng = np.random.default_rng(2026)
    # Gleichheit der schnellen Rechnung mit der ausdrücklichen (und damit mit trichter.statistik, siehe C01)
    X = welt("gemischt", 300, rng); idx = idx_schnell(TAGE, 50, BLOCK, rng)
    a, b = C.rc_eigen(X, idx), C.rc_gewichte(X, idx)
    a2, b2 = C.rc_eigen(X, idx, selbst=True), C.rc_gewichte(X, idx, selbst=True)
    print("schnelle Rechnung = ausdrückliche Rechnung:", np.allclose(a[2], b[2]), np.allclose(a2[2], b2[2]), "| mittlere Blocklänge der Ziehung:",
          round(TAGE / (np.diff(idx, axis=1) % TAGE != 1).sum(1).mean(), 2))
    t0 = time.time()
    print("\n(a) Welten OHNE Vorteil, 5.000 Kandidaten")
    lauf("normal", 5000, 200, rng)
    lauf("schief+", 5000, 100, rng)
    lauf("schief-", 5000, 100, rng)
    lauf("gemischt", 5000, 100, rng)
    print("\n(b) EIN Kandidat mit echtem Vorteil unter 5.000 (erwarteter t-Wert 4,5 bzw. 6)")
    lauf("normal", 5000, 60, rng, vorteil_t=4.5)
    lauf("normal", 5000, 60, rng, vorteil_t=6.0)
    print(f"Rechenzeit {time.time() - t0:.0f} s")
