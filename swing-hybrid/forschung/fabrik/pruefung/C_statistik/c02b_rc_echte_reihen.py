"""C02b Eichung des Reality Check auf ECHTEN Tagesreihen (nur Training T, Gruppe Kurs/Volumen/Derivate, gen1), ohne Vorteil:
5.000 zufällig gezogene gültige Kandidaten; jede Reihe wird auf Mittel null gesetzt (damit hat KEIN Kandidat einen Vorteil); daraus entstehen
"Welten", indem die 685 Tage blockweise neu gezogen werden (für alle Kandidaten dieselben Tage, Abhängigkeiten bleiben erhalten).
In jeder Welt wird der Reality Check so gerechnet wie in trichter.statistik. Richtig geeicht wäre: p <= 0,05 in etwa 5 % der Welten."""
import sys, math
import numpy as np
from scipy import stats
sys.path.insert(0, 'forschung/fabrik/pruefung/C_statistik')
import c_lib as C
import c02_rc_eichung as E
from fabrik import lauf as L

con = C.ro()
rng = np.random.default_rng(77)
d0, d1 = L.SEGMENTE["k"][0], L.SEGMENTE["k"][1]
z = con.execute("SELECT zeile, t85_t FROM kandidaten WHERE gen = 'gen1' AND n_t >= 200 AND braucht != 't'").fetchall()
zeilen = np.array([r[0] for r in z]); t_db = np.array([r[1] for r in z])
wahl = np.sort(rng.choice(len(zeilen), 5000, replace=False))
mm = np.load('data/fabrik/tage_gen1.npy', mmap_mode='r')
X = np.asarray(mm[zeilen[wahl]], dtype=np.float64)[:, d0:d1]
print("Stichprobe:", X.shape, "| Tage nur T:", d0, "bis", d1, "| größter Spaltenindex gelesen:", d1 - 1, "< N_TAGE", L.N_TAGE)
sch = stats.skew(X, axis=1); woe = stats.kurtosis(X, axis=1)
aktiv = (X != 0).mean(1)
print(f"Schiefe der Tagesreihen: 5 % {np.percentile(sch, 5):+.2f}  Median {np.median(sch):+.2f}  95 % {np.percentile(sch, 95):+.2f} | Anteil negativ {np.mean(sch < 0):.2f}")
print(f"Wölbung (Überschuss): Median {np.median(woe):.1f}  95 % {np.percentile(woe, 95):.1f} | Anteil der Tage mit Ergebnis ungleich null: Median {np.median(aktiv):.2f}")
t_echt = X.mean(1) / X.std(1, ddof=1) * math.sqrt(X.shape[1])
print(f"Probe: t85_t aus der Datenbank gegen eigene Rechnung aus der Tagesreihe, größte Abweichung {np.abs(t_echt - t_db[wahl]).max():.4f}")
print(f"Zusammenhang Schiefe / t-Wert in den echten Reihen (Rangkorrelation): {stats.spearmanr(sch, t_echt)[0]:+.3f}")
oben = np.argsort(-t_echt)[:50]
print(f"die 50 Kandidaten der Stichprobe mit dem höchsten t: Schiefe Median {np.median(sch[oben]):+.2f}, Anteil negativ {np.mean(sch[oben] < 0):.2f}")

Xc = X - X.mean(1, keepdims=True)
ps, ps2, tb, md = [], [], [], []
schiefe_des_besten, schiefe_boot = [], []
for w in range(120):
    ix = E.idx_schnell(685, 1, 10, rng)[0]
    Xw = Xc[:, ix]
    idx = E.idx_schnell(685, 400, 10, rng)
    t1, p1, m1 = C.rc_gewichte(Xw, idx)
    t2, p2, m2 = C.rc_gewichte(Xw, idx, selbst=True)
    ps.append(p1); ps2.append(p2); tb.append(t1); md.append(np.median(m1))
    tw = Xw.mean(1) / np.where(Xw.std(1) > 0, Xw.std(1, ddof=1), 1) * math.sqrt(685)
    schiefe_des_besten.append(stats.skew(Xw[int(tw.argmax())]))
ps, ps2 = np.array(ps), np.array(ps2)
f = lambda p: f"p<=0,05: {np.mean(p <= 0.05):.3f}  p<=0,10: {np.mean(p <= 0.10):.3f}  p<=0,50: {np.mean(p <= 0.5):.3f}  Mittel {p.mean():.3f}  KS-p {stats.kstest(p, 'uniform').pvalue:.4f}"
print(f"\n120 Welten ohne Vorteil: bestes t im Mittel {np.mean(tb):.2f} (5 %/95 %: {np.percentile(tb, 5):.2f}/{np.percentile(tb, 95):.2f}), Bootstrap-Maximum (Median) im Mittel {np.mean(md):.2f}")
print("   wie trichter (feste Streuung):  ", f(ps))
print("   eigene Streuung je Stichprobe:  ", f(ps2))
print(f"   Schiefe der Reihe, die in einer Welt ohne Vorteil das höchste t erreicht: Median {np.median(schiefe_des_besten):+.2f}, Anteil negativ {np.mean(np.array(schiefe_des_besten) < 0):.2f}")
