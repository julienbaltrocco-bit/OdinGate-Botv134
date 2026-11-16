"""Sonderfälle: a) Bestätigungssignal btcfuehrt_3 (gen2): BTC handelt nie, zählt aber im Teiler und im Markt.
b) Signal-Ausstieg bei NaN-Signalwert. c) Einstiege/Ausstiege in ungültigen Kerzen (veralteter Kurs). d) übrige Kennzahlen der Datenbank (quote, pf, dauer, sharpe, rueck)."""
import sqlite3, sys, json, random
import numpy as np
sys.path.insert(0, 'forschung/fabrik/pruefung/B_buchung')
import pruef_lib as P
from fabrik import lauf as L, generator as G, daten as D
con = sqlite3.connect('file:data/fabrik/forschung.sqlite?mode=ro', uri=True)
con.row_factory = sqlite3.Row
rng = random.Random(12)
tage = {g: np.load(f'data/fabrik/tage_{g}.npy', mmap_mode='r') for g in ("gen1", "gen2")}

print("a) Bestätigungssignal btcfuehrt_3")
zeilen = [dict(r) for r in con.execute("SELECT * FROM kandidaten WHERE best LIKE '%btcfuehrt%' AND status IN ('final','stufe3') AND m IN ('top3','alle10')")]
print("   Kandidaten final/stufe3 mit Bestätigung btcfuehrt_3 und BTC im Markt:", len(zeilen), "| davon final:", sum(1 for z in zeilen if z['status'] == 'final'))
btc_einstiege = 0
for z in rng.sample(zeilen, 6):
    a = P.aufgabe(z)
    ein0, _ = L.einstieg(a, 0)
    btc_einstiege += int(np.count_nonzero(ein0))
    r = P.nachbau(z)                                           # eigener Nachbau mit allen Coins des Marktes (wie lauf.py)
    M_voll, M_handelbar = list(G.MAERKTE[z['m']]), [c for c in G.MAERKTE[z['m']] if c != 0]
    n_je_coin = r["n_tag"].sum(1)
    gesp = np.asarray(tage[z['gen']][z['zeile']], dtype=np.float64)
    p_handelbar = (r["roh_tag"].sum(0) - 2.4 * r["n_tag"].sum(0)) / len(M_handelbar)
    kum = lambda p: float((np.maximum.accumulate(np.cumsum(p[:685])) - np.cumsum(p[:685])).max()) / 100
    print(f"   {z['id']} {z['signal']} + {z['best']} {z['x']} {z['m']} ({z['status']}): Signale BTC {int(np.count_nonzero(ein0))}, Trades je Coin {n_je_coin.astype(int).tolist()} | "
          f"Speicher = Summe/{len(M_voll)} (Abw. {np.abs(gesp - r['p85']).max():.5f}); mit Teiler {len(M_handelbar)} wäre das Tagesergebnis {len(M_voll)/len(M_handelbar):.2f}-fach | "
          f"Rückgang T: DB {z['rueck_t']} %, mit handelbaren Coins {kum(p_handelbar):.3f} %")
print("   Signale auf BTC in der Stichprobe insgesamt:", btc_einstiege)

print("b) Signal-Ausstieg und NaN-Signalwerte; c) ungültige Kerzen")
zeilen = [dict(r) for r in con.execute("SELECT * FROM kandidaten WHERE status IN ('final','stufe3')")]
st = rng.sample([z for z in zeilen if P.AUSSTIEGE[z['x']][5] is not None], 40) + rng.sample([z for z in zeilen if P.AUSSTIEGE[z['x']][5] is None], 60)
n_tr = n_nan = n_ein_ung = n_aus_ung = 0
roh_ung, roh_alle = 0.0, 0.0
for z in st:
    r = P.nachbau(z, mit_trades=True)
    a = P.aufgabe(z)
    wert = {j: L.einstieg(a, j)[1] for j in r["M"]} if P.AUSSTIEGE[z['x']][5] is not None else None
    for (j, i, ea, eb, d, e, px, art, fund, roh) in r["trades"]:
        n_tr += 1; roh_alle += roh
        if wert is not None and np.isnan(wert[j][ea:eb]).any():
            n_nan += 1
        u1, u2 = not P.gueltig[j, ea], not P.gueltig[j, eb]
        n_ein_ung += u1; n_aus_ung += u2
        if u1 or u2: roh_ung += roh
print(f"   {len(st)} Kandidaten (final/stufe3), {n_tr} Trades: Signalwert NaN während eines Trades mit Signal-Ausstieg: {n_nan}; Einstieg in ungültiger Kerze: {n_ein_ung}; "
      f"Ausstieg in ungültiger Kerze: {n_aus_ung}; Summe roh dieser Trades {roh_ung:.0f} bp von {roh_alle:.0f} bp")

print("d) übrige Kennzahlen (eigene Rechnung / Datenbank)")
schlecht = 0
for z in rng.sample(zeilen, 25) + json.load(open('forschung/fabrik/pruefung/B_buchung/01_auswahl.json')):
    r = P.nachbau(z, mit_trades=True)
    i_t0, i_v0, d_t0, d_v0 = r["seg"]
    tr = [x for x in r["trades"] if d_t0 <= (x[2] - P.TAG_VON) // 288 < d_v0]
    n85 = np.array([x[9] for x in tr]) - 2.4
    quote = float((n85 > 0).mean()); pf = float(n85[n85 > 0].sum() / -n85[n85 <= 0].sum()) if (n85 <= 0).any() and n85[n85 <= 0].sum() < 0 else 0.0
    dauer = float(np.mean([x[3] - x[2] for x in tr])) * 5
    p = r["p85"][d_t0:d_v0]; pv = r["p85"][d_v0:]
    sharpe = float(p.mean() / p.std(ddof=1) * np.sqrt(365)); sharpe_v = float(pv.mean() / pv.std(ddof=1) * np.sqrt(365)) if pv.std() > 0 else 0.0
    rueck = float((np.maximum.accumulate(np.cumsum(p)) - np.cumsum(p)).max()) / 100
    paare = {"quote_t": quote, "pf_t": pf, "dauer_min": dauer, "sharpe_t": sharpe, "sharpe_v": sharpe_v, "rueck_t": rueck}
    ab = {k: (round(v, 4), z[k]) for k, v in paare.items() if abs(v - z[k]) > (0.06 if k == "dauer_min" else 0.002)}
    schlecht += bool(ab)
    if ab: print("   ABWEICHUNG", z['id'], z['x'], ab)
print("   abweichend:", schlecht, "von", 25 + 16)
