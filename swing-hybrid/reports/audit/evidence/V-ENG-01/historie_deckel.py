"""V-ENG-01: Wie oft haette der Deckel im ENTWICKLUNGSZEITRAUM (bis 2025-03-31) eine Schliess-Order der Grundregel abgelehnt?

Nur Zaehlung, keine Parameterwahl, kein Blick in den Pruefzeitraum. Stundenschluesse der zehn Coins (Binance-Futures),
Signal = Vorzeichen(Schluss / Schluss vor 336 h - 1) wie mutationen.basis. Einstieg und Ausstieg zum Stundenschluss des
Signalwechsels (der Bot handelt wenige Minuten spaeter zum dann gueltigen Orderbuch). Stueckzahl fest ab Einstieg
(Nominal / Einstiegskurs, Rundung vernachlaessigt). Die Schliess-Order wird abgelehnt, wenn
Stueck x Limitkurs > Deckel, also Kursverhaeltnis Ausstieg/Einstieg x 1,0005 > Deckel / Nominal.
"""
import sys
sys.path.insert(0, "src")
import numpy as np, pandas as pd
from hybrid import research as R, mutationen as M

voll = R.markt(R.GRUPPE_A, vor=True)
c = R._close(voll)
sig = M.basis(voll)
grenze = pd.Timestamp(R.SPLIT)
c, sig = c[c.index < grenze], sig[sig.index < grenze]
print("Stundenschluesse", c.index[0], "bis", c.index[-1], "| Coins", list(c.columns))
zeilen = []
for coin in c.columns:
    s = sig[coin].to_numpy(); p = c[coin].to_numpy(); t = c.index
    ok = ~np.isnan(p)
    wechsel = np.flatnonzero(np.r_[True, s[1:] != s[:-1]])
    for a, b in zip(wechsel, np.r_[wechsel[1:], len(s)]):
        if s[a] == 0 or b >= len(s) or not (ok[a] and ok[b]):
            continue
        zeilen.append({"coin": coin, "richtung": int(s[a]), "ein": t[a], "aus": t[b], "ein_kurs": p[a], "aus_kurs": p[b],
                       "verh": p[b] / p[a], "ia": a, "ib": b})
tr = pd.DataFrame(zeilen)
print("Trades (Entwicklungszeitraum inkl. Vorperiode):", len(tr), "| Long", int((tr.richtung > 0).sum()), "| Short", int((tr.richtung < 0).sum()))
for name, deckel, nominal in (("config.json (150 / 100 USD)", 150.0, 100.0), ("config_lauf*.json (2000 / 1500 USD)", 2000.0, 1500.0)):
    schwelle = deckel / nominal / 1.0005
    bl = tr[tr.verh > schwelle]
    print(f"\n{name}: Schliess-Order abgelehnt ab Kursverhaeltnis Ausstieg/Einstieg > {schwelle:.4f}")
    print(f"  betroffene Ausstiege: {len(bl)} von {len(tr)} | davon Short (Verlust-Trade): {int((bl.richtung < 0).sum())} | Long (Gewinn-Trade): {int((bl.richtung > 0).sum())}")
    aus = []
    for _, z in bl.iterrows():
        p = c[z.coin].to_numpy(); i = int(z.ib)
        j = i
        while j < len(p) and p[j] / z.ein_kurs > schwelle:
            j += 1
        spitze = np.nanmax(p[i:max(j, i + 1)]) / z.ein_kurs
        aus.append({"coin": z.coin, "richtung": z.richtung, "ein": z.ein, "aus_faellig": z.aus, "verh_bei_ausstieg": round(z.verh, 3),
                    "stunden_blockiert": j - i if j < len(p) else f">{j - i}", "hoechstes_verh_solange_blockiert": round(float(spitze), 3)})
    if aus:
        print(pd.DataFrame(aus).sort_values(["richtung", "verh_bei_ausstieg"]).to_string(index=False))
# groesstes Kursverhaeltnis bei faelligem Ausstieg je Richtung
for r, n in ((-1, "Short"), (1, "Long")):
    x = tr[tr.richtung == r].verh
    print(f"\n{n}: Kursverhaeltnis bei faelligem Ausstieg: Median {x.median():.3f}, 99 % {x.quantile(0.99):.3f}, Maximum {x.max():.3f}")
