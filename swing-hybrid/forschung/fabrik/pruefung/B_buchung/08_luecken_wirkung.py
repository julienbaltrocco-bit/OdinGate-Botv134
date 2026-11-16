"""Wirkung der Datenlücken (SOL, XRP, LTC: 26.-28.02.2022 und 01.-02.04.2022) auf die Ergebnisse.
a) Über alle Kandidaten, die Stufe 2 bestanden hatten: Anteil des T-Ergebnisses, der auf Tage an den Lücken gebucht ist (gespeicherte Tagesreihen).
b) Für die am stärksten betroffenen: Trades mit eigenem Simulator, Kennzahlen mit und ohne die Lücken-Trades."""
import sqlite3, sys, json
import numpy as np, pandas as pd
sys.path.insert(0, 'forschung/fabrik/pruefung/B_buchung')
import pruef_lib as P
from fabrik import daten as D, lauf as L

con = sqlite3.connect('file:data/fabrik/forschung.sqlite?mode=ro', uri=True)
con.row_factory = sqlite3.Row
tagnr = lambda t: (int(np.searchsorted(D.RASTER.values, np.datetime64(t))) - P.TAG_VON) // 288
# Tage, an denen Trades der Lücken-Coins mit veralteten Kursen oder dem Sprung nach der Lücke zu tun haben
ltage = sorted(set(range(tagnr('2022-02-25'), tagnr('2022-03-02') + 1)) | set(range(tagnr('2022-03-31'), tagnr('2022-04-04') + 1)))
print("Lückentage (Tagesnummern):", ltage, [str(D.RASTER[P.TAG_VON + 288 * t].date()) for t in ltage])
zeilen = [dict(r) for r in con.execute("SELECT * FROM kandidaten WHERE status IN ('stufe2','stufe3','final','verworfen_3') AND braucht != 't' AND (best IS NULL OR (best NOT LIKE '%tiefe%' AND best NOT LIKE '%liq_entzug%'))")]
print("Kandidaten mit bestandener Stufe 2 (Kurs/Derivate-Segment):", len(zeilen))
tage = {g: np.load(f'data/fabrik/tage_{g}.npy', mmap_mode='r') for g in ("gen1", "gen2")}
erg = []
for z in zeilen:
    r = np.asarray(tage[z['gen']][z['zeile']][:685], dtype=np.float64)
    s, sl = r.sum(), r[ltage].sum()
    rest = np.delete(r, ltage)
    t_ohne = rest.mean() / rest.std(ddof=1) * np.sqrt(len(rest)) if rest.std() > 0 else 0.0
    erg.append((sl / s if s > 0 else np.nan, sl, s, t_ohne, z))
ant = np.array([e[0] for e in erg])
tohne = np.array([e[3] for e in erg])
t_mit = np.array([e[4]['t85_t'] for e in erg])
print(f"Anteil des T-Ergebnisses auf den {len(ltage)} Lückentagen (von 685): Median {np.nanmedian(ant):.3f}, 90 % {np.nanpercentile(ant, 90):.3f}, 99 % {np.nanpercentile(ant, 99):.3f}, Maximum {np.nanmax(ant):.3f}")
print(f"Kandidaten mit Anteil > 10 %: {(ant > 0.10).sum()}, > 20 %: {(ant > 0.20).sum()}, > 30 %: {(ant > 0.30).sum()}")
print(f"t85_t ohne die Lückentage < 2 (obwohl mit >= 2): {((tohne < 2) & (t_mit >= 2)).sum()} von {len(erg)}; davon heute Status final/stufe3: "
      f"{sum(1 for e in erg if e[3] < 2 and e[4]['t85_t'] >= 2 and e[4]['status'] in ('final', 'stufe3'))}")
erg.sort(key=lambda e: -(e[0] if e[0] == e[0] else -9))
ung = np.asarray(~P.gueltig)
print("\nDie 8 am stärksten betroffenen Kandidaten, Trades mit eigenem Simulator:")
for a_, sl, s, t_o, z in erg[:8]:
    r = P.nachbau(z, mit_trades=True)
    i_t0, i_v0, d_t0, d_v0 = r["seg"]
    tr = [x for x in r["trades"] if x[2] < i_v0]                           # (coin, i, a, b, d, e, px, art, fund, roh), Einstieg in T
    def an_luecke(x):
        j, i, a, b = x[0], x[1], x[2], x[3]
        return bool(ung[j, a] or ung[j, b] or ung[j, max(i - 288, 0):i + 1].any())      # Ein-/Ausstieg in der Lücke oder Signal bis 1 Tag nach der Lücke
    lt = [x for x in tr if an_luecke(x)]
    roh_alle = np.array([x[9] for x in tr]); roh_l = np.array([x[9] for x in lt])
    ohne = (roh_alle.sum() - roh_l.sum()) / max(len(tr) - len(lt), 1) - 2.4
    print(f"  {z['gen']} {z['id']} {z['signal']} th {z['th']} r {z['r']:+d} {z['f']} k{z['k']} {z['x']} {z['m']} | Status {z['status']} | T: Trades {len(tr)}, n85 {roh_alle.mean()-2.4:.2f} bp, t85 {z['t85_t']} | "
          f"Anteil Lückentage {a_:.2f} | Lücken-Trades {len(lt)}: Mittel {roh_l.mean() if len(lt) else 0:.0f} bp, Summe {roh_l.sum():.0f} von {roh_alle.sum():.0f} bp | n85 ohne Lücken-Trades {ohne:.2f} bp | t85 ohne Lückentage {t_o:.2f}")
    for x in sorted(lt, key=lambda x: -abs(x[9]))[:3]:
        print(f"      {D.COINS[x[0]]} Signal {D.RASTER[x[1]]} Richtung {x[4]:+d} Einstieg {D.RASTER[x[2]]} @ {x[5]:.4f} (Kerze gültig: {not ung[x[0], x[2]]}) Ausstieg {D.RASTER[x[3]]} @ {x[6]:.4f} (gültig: {not ung[x[0], x[3]]}) {x[7]} roh {x[9]:+.0f} bp")
