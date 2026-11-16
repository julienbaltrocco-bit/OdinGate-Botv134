"""Wählt die Stichprobe aus gen1 (Datenbank nur lesend) und legt sie als JSON ab, damit spätere Statusänderungen (Stufe 3) die Auswahl nicht verschieben."""
import sqlite3, json, random
con = sqlite3.connect('file:data/fabrik/forschung.sqlite?mode=ro', uri=True)
con.row_factory = sqlite3.Row
rng = random.Random(4711)
wahl = []
def nimm(wo, arg=(), n=1):
    z = con.execute(f"SELECT * FROM kandidaten WHERE gen='gen1' AND {wo} ORDER BY id", arg).fetchall()
    for r in rng.sample(z, min(n, len(z))):
        wahl.append(dict(r))
# Pflichtfünf: je ein Ausstieg, verschiedene Märkte, mindestens einer stufe2
nimm("x='h60' AND m='alle10' AND status='stufe2'")
nimm("x='h240_stop2' AND m='top3' AND n_t>=200 AND status='stufe2'")
nimm("x='h240_stop1.5_ziel3' AND m='alt7' AND n_t>=200")
nimm("x='h720_zielnachzug' AND m='alle10' AND n_t>=2000")
nimm("x='signal_h720' AND m='top3' AND n_t>=200")
# Zusatz: Sonderfälle (Tiefe-Segment, ohne BTC, Filter mit Richtung, Takt 12, h15, Nachzug ab 0, Fund-Signal, wenige Trades)
nimm("x='signal_h720' AND braucht='t' AND m='alle10' AND n_t>=200")
nimm("x='h720_nachzug2' AND signal LIKE 'relstaerke%' AND m='top3' AND n_t>=200")
nimm("x='h60_stop1.5_ziel1.5' AND signal LIKE 'btcfuehrt%' AND m='alle10' AND k=1 AND n_t>=5000")
nimm("x='h15' AND f='trend_mit' AND k=1 AND m='alt7' AND n_t>=20000")
nimm("x='h720' AND signal='fund' AND m='alle10' AND n_t>=200")
nimm("x='h240' AND signal LIKE 'korrbruch%' AND m='alt7' AND n_t>=200")
nimm("x='h240_stop1.5_ziel3' AND status='stufe2' AND braucht='t'")
nimm("x='h720_zielnachzug' AND status='stufe2' AND m='alt7'")
nimm("x='signal_h720' AND status='stufe2'")
nimm("x='h720' AND status='stufe2' AND k=12")
nimm("n_t BETWEEN 1 AND 150 AND x='h240_stop2'")
json.dump(wahl, open('forschung/fabrik/pruefung/B_buchung/01_auswahl.json', 'w'), indent=1, ensure_ascii=False)
for w in wahl:
    print(w['id'], w['zeile'], w['signal'], w['th'], w['r'], w['f'], w['k'], w['x'], w['m'], w['braucht'], '| n_t', w['n_t'], 'n85_t', w['n85_t'], 't85_t', w['t85_t'], '|', w['status'], w['grund'])
