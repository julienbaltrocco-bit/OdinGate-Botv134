"""C04 trichter.marktbereinigt und trichter.tagesreihe in einer KÜNSTLICHEN Welt (keine echten Daten, nichts ab 2024-07-01):
Test A  Regel, die jeden Tag von 00:00 bis 24:00 long ist -> Tagesergebnis = Marktrendite des Tages minus Kosten. Erwartet: Beta 1, Alpha = -Kosten.
        Wäre das Tagesergebnis gegen die Marktrendite um einen Tag verschoben, käme Beta nahe 0 heraus.
Test B  Eingesetzte Reihe genau beta * Marktrendite (und um einen Tag vor/zurück verschoben).
Test C  Regel ohne jedes Wissen: zufällige Long-Einstiege, 12 Stunden Haltedauer, Kosten null, steigender Markt. Echter Mehrertrag = 0.
        Der Trade wird ganz auf den Einstiegstag gebucht, liegt aber zum Teil im Folgetag -> wie oft meldet marktbereinigt trotzdem t(Alpha) >= 2?"""
import sys, math
import numpy as np
sys.path.insert(0, 'forschung/fabrik/pruefung/C_statistik')
import c_lib as C
from fabrik import daten as D, lauf as L, trichter as T, signale as S, generator as G

NC = len(D.COINS)
SI = S.NAMEN.index("mom_12")


def welt(n_tage, rng, drift_bp_tag, vol_bp_tag, p_signal, vorlauf=5):
    n = (n_tage + vorlauf) * 288
    gemeinsam = rng.normal(drift_bp_tag / 288 / 1e4, vol_bp_tag / math.sqrt(288) / 1e4, n)
    c = np.empty((NC, n)); o = np.empty((NC, n))
    for j in range(NC):
        r = 0.7 * gemeinsam + rng.normal(0.3 * drift_bp_tag / 288 / 1e4, 0.7 * vol_bp_tag / math.sqrt(288) / 1e4, n)
        c[j] = 100 * np.exp(np.cumsum(r))
        o[j, 0] = 100.0; o[j, 1:] = c[j, :-1]                       # Eröffnung = voriger Schluss (keine Lücken)
    sig = np.zeros((len(S.NAMEN), NC, n), np.float32)
    sig[SI] = np.where(rng.random((NC, n)) < p_signal, 5.0, 0.0)     # Signal 5 >= Schwelle -> long (r = +1)
    g = {"o": o, "h": np.maximum(o, c), "l": np.minimum(o, c), "fcum": np.zeros((NC, n)), "gueltig": np.ones((NC, n), bool), "signale": sig,
         "filter": np.zeros((4, NC, n), np.int8), "sigma": np.ones((NC, n), np.float32), "slip_bp": np.full(NC, 1.5), "pos": np.arange(n),
         "tag": np.zeros(n, np.int32), "c": c}
    return g, vorlauf * 288, n


def einsetzen(g, n):
    D.N = n
    D.laden = lambda name: g[name]                                   # nur in diesem Prozess: der "Datenspeicher" ist die künstliche Welt
    L._g.clear(); L._init()                                          # echte Initialisierung (handelbar, Slippage-Felder) auf der künstlichen Welt


Z = {"signal": "mom_12", "familie": "Momentum", "braucht": "k", "th": 1.5, "r": 1, "f": "kein", "k": 288, "x": "kuenstlich", "m": "top3", "best": None}
rng = np.random.default_rng(5)
print("Code-Stand:", C.stand())

print("Test A: immer long, Einstieg zur ersten Kerze jedes Tages, Haltedauer 288 Kerzen (ein Tag)")
g, i0, n = welt(400, rng, 20.0, 300.0, 1.0)
einsetzen(g, n)
T.ausstieg_aus = lambda z: (288, 0, 0, 0, 0, None)
p, ntr, roh = T.tagesreihe(Z, i0, n)
schluss = i0 - 1 + 288 * np.arange(len(p) + 1)
m_eigen = (g["c"][:3][:, schluss[1:]] / g["c"][:3][:, schluss[:-1]] - 1).mean(0) * 1e4
kosten = 2 * 1.5 + L.KOSTEN85
print(f"   Tage {len(p)}, Trades {ntr}; Tag 0 ohne Trade (erstes Signal am Tagesende): p[0] = {p[0]:.3f}")
print(f"   größte Abweichung p[d] - (Marktrendite[d] - Kosten {kosten}) für d = 1 .. vorletzter Tag: {np.abs(p[1:-1] - (m_eigen[1:-1] - kosten)).max():.2e} bp")
print(f"   Korrelation p[d] mit Markt[d-1], Markt[d], Markt[d+1]: {np.corrcoef(p[2:-1], m_eigen[1:-2])[0, 1]:+.3f} {np.corrcoef(p[1:-1], m_eigen[1:-1])[0, 1]:+.3f} {np.corrcoef(p[1:-2], m_eigen[2:-1])[0, 1]:+.3f}")
alpha, t_alpha, beta = T.marktbereinigt(Z, i0, n)
print(f"   trichter.marktbereinigt: Alpha {alpha:+.3f} bp/Tag (erwartet {-kosten:+.3f}), t {t_alpha:+.2f}, Beta {beta:.4f} (erwartet 1)")

print("\nTest B: eingesetzte Reihe = 0,37 * Marktrendite (+ 2 bp/Tag), ohne Rauschen und um einen Tag verschoben")
echt_tr = T.tagesreihe
for name, verschub in (("gleicher Tag", 0), ("Ergebnis einen Tag zu spät", 1), ("Ergebnis einen Tag zu früh", -1)):
    reihe = 2.0 + 0.37 * np.roll(m_eigen, verschub) + rng.normal(0, 0.01, len(m_eigen))
    T.tagesreihe = lambda z, a, b, reihe=reihe: (reihe, 1, 0.0)
    alpha, t_alpha, beta = T.marktbereinigt(Z, i0, n)
    print(f"   {name:<28} Alpha {alpha:+.3f} (Soll +2 bei gleichem Tag), Beta {beta:+.4f} (Soll 0,37 bei gleichem Tag)")
T.tagesreihe = echt_tr

print("\nTest C: zufällige Long-Einstiege, 12 h Haltedauer, Kosten 0, Markt steigt im Mittel 25 bp je Tag (Schwankung 300 bp); 547 Tage wie T+V1 der Orderbuch-Gruppe")
kosten_alt = L.KOSTEN85
L.KOSTEN85 = 0.0
T.ausstieg_aus = lambda z: (144, 0, 0, 0, 0, None)
Zc = dict(Z, k=1)
for p_signal, text in ((1 / 600, "selten (rund ein Einstieg je zwei Tage und Coin)"), (1 / 150, "häufig (meist investiert)")):
    ts, t2s, betas, b2s, ts_roh = [], [], [], [], []
    for w in range(150):
        g, i0, n = welt(547, rng, 25.0, 300.0, p_signal)
        g["slip_bp"] = np.zeros(NC)
        einsetzen(g, n)
        alpha, t_alpha, beta = T.marktbereinigt(Zc, i0, n)
        p, ntr, roh = T.tagesreihe(Zc, i0, n)
        schluss = i0 - 1 + 288 * np.arange(len(p) + 1)
        m = (g["c"][:3][:, schluss[1:]] / g["c"][:3][:, schluss[:-1]] - 1).mean(0) * 1e4
        X = np.column_stack([np.ones(len(p) - 1), m[:-1], m[1:]])       # eigene Rechnung: zusätzlich die Marktrendite des Folgetags
        k = np.linalg.solve(X.T @ X, X.T @ p[:-1]); rest = p[:-1] - X @ k
        se = math.sqrt(rest @ rest / (len(rest) - 3) * np.linalg.inv(X.T @ X)[0, 0])
        ts.append(t_alpha); betas.append(beta); t2s.append(k[0] / se); b2s.append(k[1] + k[2]); ts_roh.append(T.t_wert(p))
    ts, t2s = np.array(ts), np.array(t2s)
    print(f"   {text}: 150 Welten ohne Vorteil")
    print(f"      rohes Tagesmittel:            t im Mittel {np.mean(ts_roh):+.2f}, t >= 2 in {np.mean(np.array(ts_roh) >= 2):.1%}")
    print(f"      trichter.marktbereinigt:      Beta im Mittel {np.mean(betas):.3f}, t(Alpha) im Mittel {ts.mean():+.2f}, t(Alpha) >= 2 in {np.mean(ts >= 2):.1%} (richtig wären rund 2,3 %)")
    print(f"      mit Marktrendite des Folgetags: Beta-Summe im Mittel {np.mean(b2s):.3f}, t(Alpha) im Mittel {t2s.mean():+.2f}, t(Alpha) >= 2 in {np.mean(t2s >= 2):.1%}")
L.KOSTEN85 = kosten_alt
