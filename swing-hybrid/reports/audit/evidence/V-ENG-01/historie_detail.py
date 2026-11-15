"""V-ENG-01: Aufteilung der Deckel-Faelle nach Vorperiode / Entwicklungszeitraum und Detail zweier Short-Faelle (5-Minuten-Kurse).
Nur Zaehlung im Zeitraum vor 2025-04-01, keine Parameterwahl."""
import sys
sys.path.insert(0, "src")
import numpy as np, pandas as pd
from hybrid import research as R, mutationen as M

voll = R.markt(R.GRUPPE_A, vor=True)
c = R._close(voll); sig = M.basis(voll)
grenze = pd.Timestamp(R.SPLIT); start = pd.Timestamp(R.START)
c, sig = c[c.index < grenze], sig[sig.index < grenze]
z = []
for coin in c.columns:
    s = sig[coin].to_numpy(); p = c[coin].to_numpy(); t = c.index
    w = np.flatnonzero(np.r_[True, s[1:] != s[:-1]])
    for a, b in zip(w, np.r_[w[1:], len(s)]):
        if s[a] != 0 and b < len(s) and not (np.isnan(p[a]) or np.isnan(p[b])):
            z.append((coin, int(s[a]), t[a], t[b], p[a], p[b], p[b] / p[a]))
tr = pd.DataFrame(z, columns=["coin", "richtung", "ein", "aus", "ein_kurs", "aus_kurs", "verh"])
for name, teil in (("Vorperiode (Ausstieg vor 2021-08-15)", tr[tr.aus < start]), ("Entwicklungszeitraum (Ausstieg 2021-08-15 bis 2025-03-31)", tr[tr.aus >= start])):
    print(name, "| Trades", len(teil))
    for bez, sch in (("Deckel/Nominal 1,5 (config.json)", 1.5 / 1.0005), ("Deckel/Nominal 1,333 (config_lauf*.json)", 2000 / 1500 / 1.0005)):
        b = teil[teil.verh > sch]
        print(f"  {bez}: abgelehnte Schliess-Orders {len(b)} | Short {int((b.richtung < 0).sum())} | Long {int((b.richtung > 0).sum())}")
    print(f"  groesstes Kursverhaeltnis bei faelligem Ausstieg: Short {teil[teil.richtung < 0].verh.max():.3f} | Long {teil[teil.richtung > 0].verh.max():.3f}")

def detail(coin, ein, aus, stunden_danach=6):
    roh = R._lesen("5m", coin, True)
    e = c.loc[pd.Timestamp(ein), coin]
    print(f"\n{coin} Short, Einstieg zum Stundenschluss der Kerze {ein} = {e:.6g}; Ausstieg faellig nach Schluss der Kerze {aus}")
    t0 = pd.Timestamp(aus) + pd.Timedelta(hours=1)          # Zeitpunkt, zu dem der Stundenschluss bekannt ist
    for k in range(0, stunden_danach * 12 + 1):
        ts = t0 + pd.Timedelta(minutes=5 * k)
        if (k <= 2 or k % 12 in (0, 1)) and ts in roh.index:
            o = float(roh.loc[ts, "open"])
            print(f"   {ts}  5m-Eroeffnung {o:.6g}  Verhaeltnis zum Einstieg {o / e:.3f}")
detail("DOGE", "2021-01-27 06:00", "2021-01-28 04:00")
detail("XRP", "2021-04-24 07:00", "2021-04-30 10:00", 2)
detail("AVAX", "2020-10-07 07:00", "2020-10-12 16:00", 2)
detail("ADA", "2025-02-24 23:00", "2025-03-02 16:00", 2)
e = c.loc[pd.Timestamp("2021-01-27 06:00"), "DOGE"]
nach = c.loc[pd.Timestamp("2021-01-28 05:00"):, "DOGE"]
print(f"\nDOGE nach 2021-01-28 05:00 bis 2025-03-31: tiefster Stundenschluss {nach.min():.6g} = {nach.min() / e:.2f} x Einstieg; hoechster {nach.max():.6g} = {nach.max() / e:.1f} x Einstieg")
