"""C08 Wie viele Kandidaten kommen rein zufällig durch den Trichter? (Lauf A, nur lesend, nur T und V1)
1) Zählung aus der Datenbank: Bestehen von V1 je nach Abschneiden in T (trägt das Training überhaupt in die Auswahlprüfung?).
2) Rechnung ohne Daten: unabhängige Kandidaten mit Erwartungswert null.
3) Bootstrap auf echten Tagesreihen (gen1, Gruppe Kurs/Volumen/Derivate, 20.000 zufällige gültige Kandidaten), zwei Annahmen "ohne Vorteil":
   N0: Netto-Ergebnis im Mittel null (großzügig: die Kosten wären im Mittel gerade verdient);
   N1: kein Wissen: je Trade gehen im Mittel Slippage und Gebühr verloren (näherungsweise als gleichmäßiger Abzug je Tag).
   T-Tage werden je Hälfte, V1-Tage getrennt blockweise neu gezogen; gezählt wird: t85 >= 2 in T, beide Hälften positiv, V1 positiv mit t >= 1."""
import sys, math
import numpy as np, pandas as pd
from scipy import stats
sys.path.insert(0, 'forschung/fabrik/pruefung/C_statistik')
import c_lib as C
import c02_rc_eichung as E
from fabrik import lauf as L, generator as G

con = C.ro()
K = "braucht != 't' AND (best IS NULL OR best NOT LIKE '%tiefe%' AND best NOT LIKE '%liq_entzug%')"
d = pd.read_sql(f"SELECT gen, zeile, signal, m, n_t, n_v, n85_t, t85_t, t_roh_t, n85_h1, n85_h2, n85_v, t85_v, status, grund, ({K}) AS kurs FROM kandidaten WHERE n_t >= 200", con)
d["kurs"] = d["kurs"].fillna(0).astype(bool)
d["v1"] = (d["n85_v"] > 0) & (d["t85_v"] >= 1)
d["s2"] = d["status"].isin(["stufe2", "stufe3", "final", "validiert", "verworfen_3", "verworfen_4"])
d["robust"] = d["status"].isin(["stufe3", "final"])
print("1) V1 bestanden (netto mit Rebate > 0 und t >= 1) je nach t-Wert im Training; gen1 = unausgewählte Grundmenge")
for gen in ("gen1", "gen2"):
    for kurs in (True, False):
        g = d[(d["gen"] == gen) & (d["kurs"] == kurs)]
        klassen = pd.cut(g["t85_t"], [-99, -2, -1, 0, 1, 2, 99], labels=["< -2", "-2..-1", "-1..0", "0..1", "1..2", ">= 2"])
        tab = g.groupby(klassen, observed=True)["v1"].agg(["size", "mean"])
        print(f"   {gen} {'Kurs/Volumen/Derivate' if kurs else 'Orderbuch-Tiefe'}: gültig {len(g)}, V1 bestanden insgesamt {g['v1'].mean():.3f} | Stufe 2 bestanden {g['s2'].sum()}, davon V1 bestanden {g.loc[g['s2'], 'v1'].sum()} = {g.loc[g['s2'], 'v1'].mean():.3f} | robust (nach allen Bedingungen der Stufe 3) {g['robust'].sum()}")
        print("      t85 in T:  " + "  ".join(f"{k}: {int(r['size'])} / {r['mean']:.3f}" for k, r in tab.iterrows()))

print("\n2) Rechnung ohne Daten (unabhängige Kandidaten, Erwartungswert null, Normalverteilung)")
rng = np.random.default_rng(11)
z1, z2 = rng.normal(size=4_000_000), rng.normal(size=4_000_000)
p_t = np.mean(((z1 + z2) / math.sqrt(2) >= 2) & (z1 > 0) & (z2 > 0))
p_v = 1 - stats.norm.cdf(1)
print(f"   P(t >= 2 in T und beide Hälften positiv) = {p_t:.5f} (ohne Hälften-Bedingung {1 - stats.norm.cdf(2):.5f}); P(t >= 1 in V1) = {p_v:.4f}; zusammen {p_t * p_v:.6f}")
for name, n in (("gen1, gültig", int((d["gen"] == "gen1").sum())), ("alle 340.200 Kandidaten der ersten Generation", 340200)):
    print(f"   {name}: {n} -> Stufe 2 zufällig {n * p_t:.0f}, danach V1 zufällig {n * p_t * p_v:.0f}")

print("\n3) Bootstrap auf echten Tagesreihen, gen1 Kurs/Volumen/Derivate")
g = d[(d["gen"] == "gen1") & d["kurs"]].reset_index(drop=True)
wahl = np.sort(rng.choice(len(g), 20000, replace=False))
s = g.iloc[wahl].reset_index(drop=True)
mm = np.load(C.ECHT_AUS / 'tage_gen1.npy', mmap_mode='r')
X = np.asarray(mm[s["zeile"].to_numpy()], dtype=np.float64)
assert X.shape[1] == L.N_TAGE == 1051
slip = np.load('data/fabrik/slip_bp.npy')
ohne = s["signal"].str.startswith(("btcfuehrt", "relstaerke", "korrbruch")).to_numpy()
kosten_tag = np.empty(len(s))
for i, (m, o, nt, nv) in enumerate(zip(s["m"], ohne, s["n_t"], s["n_v"])):
    M = [c for c in G.MAERKTE[m] if not (o and c == 0)]
    kosten_tag[i] = (2 * slip[M].mean() + L.KOSTEN85) * (nt + nv) / (len(M) * 1051)
h = 342                                                       # Mitte von T wie in lauf.rechne: (0 + 685) // 2
beob2 = ((s["t85_t"] >= 2) & (s["n85_t"] > 0) & (s["n85_h1"] > 0) & (s["n85_h2"] > 0)).to_numpy()
print(f"   Stichprobe 20.000 von {len(g)}; in der Stichprobe erfüllen t85 >= 2 und beide Hälften positiv: {beob2.sum()} ({beob2.mean():.4f}); davon V1 bestanden: {(beob2 & s['v1'].to_numpy()).sum()}")
print(f"   mittlerer Kostenabzug unter N1: {kosten_tag.mean():.2f} bp je Tag (Median {np.median(kosten_tag):.2f}); tatsächliches Tagesmittel der Stichprobe: {X.mean():.2f} bp")
B = 200
fak = len(g) / len(s)
for name, mittel in (("N0 (netto im Mittel null)", np.zeros(len(s))), ("N1 (Slippage und Gebühr gehen verloren)", -kosten_tag)):
    Xn = X.copy()                                              # jede Ziehungsschicht (Hälfte 1, Hälfte 2, V1) für sich auf den Erwartungswert der Annahme gesetzt
    for a, b in ((0, h), (h, 685), (685, 1051)):
        Xn[:, a:b] += mittel[:, None] - Xn[:, a:b].mean(1, keepdims=True)
    def boot(teil, n):
        idx = E.idx_schnell(n, B, 10, rng)
        W = np.stack([np.bincount(ix, minlength=n) for ix in idx]).astype(np.float64) / n
        return teil @ W.T, (teil * teil) @ W.T                 # Mittel und zweites Moment je Welt
    m1, q1 = boot(Xn[:, :h], h); m2, q2 = boot(Xn[:, h:685], 685 - h); mv, qv = boot(Xn[:, 685:], 366)
    mt = (m1 * h + m2 * (685 - h)) / 685; qt = (q1 * h + q2 * (685 - h)) / 685
    def tw(mu, q, n):
        var = np.maximum(q - mu ** 2, 0) * n / (n - 1)
        return np.where(var > 0, mu / np.sqrt(np.where(var > 0, var, 1)) * math.sqrt(n), 0)
    s2 = (tw(mt, qt, 685) >= 2) & (m1 > 0) & (m2 > 0)
    v1 = (tw(mv, qv, 366) >= 1) & (mv > 0)
    print(f"   {name}: je Kandidat P(Stufe 2) = {s2.mean():.5f}, P(V1) = {v1.mean():.4f}, P(beides) = {(s2 & v1).mean():.6f}")
    print(f"      hochgerechnet auf {len(g)} gültige Kandidaten: Stufe 2 zufällig {s2.mean() * len(g):.0f} (Streuung über Welten {s2.mean(0).std() * len(g):.0f}), "
          f"Stufe 2 und V1 zufällig {(s2 & v1).mean() * len(g):.0f} (Streuung {(s2 & v1).mean(0).std() * len(g):.0f})")
k = d[(d["gen"] == "gen1") & d["kurs"]]
print(f"   beobachtet in gen1 Kurs/Volumen/Derivate: Stufe 2 bestanden {k['s2'].sum()}, davon V1 bestanden {(k['s2'] & k['v1']).sum()}, robust nach Stufe 3 {k['robust'].sum()}")
