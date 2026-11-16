"""Große Zufallsstichprobe: eigener Nachbau gegen tage_<gen>.npy und Datenbank (nur lesend). Toleranz 0,01 bp.
Aufruf: 05_stichprobe_gross.py <gen> <n je Schicht>"""
import sqlite3, sys, random, time, json
import numpy as np
sys.path.insert(0, 'forschung/fabrik/pruefung/B_buchung')
import pruef_lib as P

gen, n_je = sys.argv[1], int(sys.argv[2])
con = sqlite3.connect('file:data/fabrik/forschung.sqlite?mode=ro', uri=True)
con.row_factory = sqlite3.Row
tage = np.load(f'data/fabrik/tage_{gen}.npy', mmap_mode='r')
rng = random.Random(20261115)
URSPR = {"stufe3": "stufe2", "final": "stufe2", "verworfen_3": "stufe2", "validiert": "stufe2", "verworfen_4": "stufe2"}   # Stufe 3/4 überschreiben den Status später
xs = [r[0] for r in con.execute("SELECT DISTINCT x FROM kandidaten WHERE gen = ?", (gen,))]
wahl = []
for x in xs:
    for wo in ("status IN ('stufe2','stufe3','final','verworfen_3')", "status = 'verworfen_2'", "status = 'verworfen_1'", "status = 'ungültig' AND n_t > 0"):
        ids = [r[0] for r in con.execute(f"SELECT id FROM kandidaten WHERE gen = ? AND x = ? AND {wo}", (gen, x))]
        for i in rng.sample(ids, min(n_je, len(ids))):
            wahl.append(dict(con.execute("SELECT * FROM kandidaten WHERE gen = ? AND id = ?", (gen, i)).fetchone()))
print(gen, "Stichprobe:", len(wahl), "Kandidaten", flush=True)
start, n_ok, n_bad, max_abw, trades, je_status = time.time(), 0, 0, 0.0, 0, {}
for z in wahl:
    r = P.nachbau(z)
    gesp = np.asarray(tage[z['zeile']], dtype=np.float64)
    abw = float(np.abs(r["p85"] - gesp).max())
    max_abw = max(max_abw, abw)
    diff = P.vergleich(z, r)
    st_db = URSPR.get(z['status'], z['status'])
    trades += r["K"]["T"]["n"] + r["K"]["V"]["n"]
    je_status[st_db] = je_status.get(st_db, 0) + 1
    if abw > 0.01 or diff or r["status"] != st_db:
        n_bad += 1
        print(f"ABWEICHUNG {z['id']} {z['signal']} th {z['th']} r {z['r']} {z['f']} k{z['k']} {z['x']} {z['m']} best {z['best']} | Tagesreihe {abw:.4f} bp | {json.dumps(diff)} | Status eigen {r['status']} / DB {z['status']}", flush=True)
    else:
        n_ok += 1
print(f"{gen}: geprüft {len(wahl)} ({je_status}), nachgerechnete Trades {trades}, übereinstimmend {n_ok}, abweichend {n_bad}, größte Abweichung der Tagesreihe {max_abw:.5f} bp, {time.time()-start:.0f} s")
