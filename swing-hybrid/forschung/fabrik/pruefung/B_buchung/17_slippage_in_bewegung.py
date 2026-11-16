"""Kostenannahme gegen die Art der Trades: Die Slippage ist eine feste Zahl je Coin (30 Messungen in ruhigem Markt, BTC/ETH 0,5 bp je Order).
Woher kommt der Ertrag der Finalisten? Trades nach der Spanne der Signalkerze (Hoch-Tief in bp) – eigener Simulator, Stichprobe von 150 Finalisten, nur T und V1.
Kennzahl ohne eigene Annahme: Um wie viel Prozent der Spanne der Signalkerze dürfte der Einstieg schlechter sein, bis das T-Ergebnis null ist?"""
import sqlite3, sys, random
import numpy as np
sys.path.insert(0, 'forschung/fabrik/pruefung/B_buchung')
import pruef_lib as P
con = sqlite3.connect('file:data/fabrik/forschung.sqlite?mode=ro', uri=True)
con.row_factory = sqlite3.Row
zeilen = [dict(r) for r in con.execute("SELECT * FROM kandidaten WHERE status = 'final'")]
rng = random.Random(17)
st = rng.sample(zeilen, 150)
grenzen = [0, 30, 100, 300, 1e9]
summe, zahl = np.zeros(4), np.zeros(4)
kstar, anteil_gross, spanne_med, slip_ant = [], [], [], []
for z in st:
    r = P.nachbau(z, mit_trades=True)
    i_t0, i_v0, d_t0, d_v0 = r["seg"]
    tr = [x for x in r["trades"] if x[2] < i_v0]
    sp = np.array([(P.h[x[0], x[1]] / P.l[x[0], x[1]] - 1) * 1e4 for x in tr])
    n85 = np.array([x[9] for x in tr]) - 2.4
    for b in range(4):
        m = (sp >= grenzen[b]) & (sp < grenzen[b + 1])
        summe[b] += n85[m].sum() / n85.sum(); zahl[b] += m.mean()
    kstar.append(n85.sum() / sp.sum())
    anteil_gross.append(n85[sp >= 100].sum() / n85.sum())
    spanne_med.append(np.median(sp))
    slip_ant.append(np.mean([2 * P.slip_bp[x[0]] for x in tr]) / np.mean(sp))
print("150 Finalisten, Trades in T. Mittel über die Kandidaten:")
for b, name in enumerate(("Spanne der Signalkerze < 30 bp", "30 bis 100 bp", "100 bis 300 bp", "über 300 bp")):
    print(f"  {name:<32} Anteil der Trades {zahl[b]/150:.2f} | Anteil am T-Ergebnis {summe[b]/150:.2f}")
kstar = np.array(kstar)
print(f"Median der Spanne der Signalkerze: {np.median(spanne_med):.0f} bp; angesetzte Slippage je Trade im Verhältnis zur mittleren Spanne der Signalkerze: Median {np.median(slip_ant)*100:.1f} %")
print(f"Anteil des T-Ergebnisses aus Trades nach Signalkerzen mit über 100 bp Spanne: Median {np.median(anteil_gross):.2f}, bei {int((np.array(anteil_gross) > 0.5).sum())} von 150 über die Hälfte")
print(f"Tragfähigkeit: T-Ergebnis = null, wenn der Einstieg um k % der Spanne der Signalkerze schlechter ausfällt: Median k = {np.median(kstar)*100:.1f} %, "
      f"25 %/75 % {np.percentile(kstar, 25)*100:.1f} %/{np.percentile(kstar, 75)*100:.1f} %; k unter 5 %: {int((kstar < 0.05).sum())} von 150; k unter 10 %: {int((kstar < 0.10).sum())}")
