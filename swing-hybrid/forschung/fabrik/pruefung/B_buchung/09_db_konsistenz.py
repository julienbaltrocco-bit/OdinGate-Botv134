"""Datenbankweite Konsistenz (nur lesend): Status gegen die gespeicherten Kennzahlen, Zeilenzuordnung tage_<gen>.npy gegen n85_t/n_t/t85_t,
Aufgaben-Vermerke, doppelte Kennungen."""
import sqlite3, sys, random, json
import numpy as np
sys.path.insert(0, 'forschung')
from fabrik import lauf as L, generator as G
con = sqlite3.connect('file:data/fabrik/forschung.sqlite?mode=ro', uri=True)
con.row_factory = sqlite3.Row
print("Aufgaben-Vermerke je Lauf:", [tuple(r) for r in con.execute("SELECT substr(key, 1, instr(key, '|') - 1) g, COUNT(*), MIN(fertig), MAX(fertig) FROM aufgaben GROUP BY g")])
print("Läufe:", [tuple(r) for r in con.execute("SELECT * FROM laeufe")])
print("Kennungen in beiden Generationen:", con.execute("SELECT COUNT(*) FROM (SELECT id FROM kandidaten GROUP BY id HAVING COUNT(*) > 1)").fetchone()[0])
print("gleiche Einstellung mehrfach (signal, th, r, f, k, x, m, best):", con.execute(
    "SELECT COUNT(*) FROM (SELECT 1 FROM kandidaten GROUP BY signal, th, r, f, k, x, m, IFNULL(best, '') HAVING COUNT(*) > 1)").fetchone()[0])
for gen in ("gen1", "gen2"):
    n, nd, mx = con.execute("SELECT COUNT(*), COUNT(DISTINCT zeile), MAX(zeile) FROM kandidaten WHERE gen = ?", (gen,)).fetchone()
    print(gen, "Kandidaten", n, "verschiedene Zeilen", nd, "höchste Zeile", mx, "| Zeilen im Speicher", np.load(f'data/fabrik/tage_{gen}.npy', mmap_mode='r').shape[0])
# 1 Status aus den gespeicherten (gerundeten) Kennzahlen neu ableiten
URSPR = {"stufe3": "stufe2", "final": "stufe2", "verworfen_3": "stufe2", "validiert": "stufe2", "verworfen_4": "stufe2"}
ab, n, knapp = {}, 0, 0
for z in con.execute("SELECT id, gen, n_t, roh_t, n85_t, t_roh_t, t85_t, n85_h1, n85_h2, n85_2x_t, n0_t, status, grund FROM kandidaten"):
    n += 1
    if z["n_t"] < 200: st = "ungültig"
    elif not (z["roh_t"] > 0 and z["t_roh_t"] >= 2): st = "verworfen_1"
    elif not (z["n85_t"] > 0 and z["t85_t"] >= 2 and z["n85_h1"] > 0 and z["n85_h2"] > 0 and z["n85_2x_t"] > 0): st = "verworfen_2"
    else: st = "stufe2"
    if abs(z["n85_t"] - (z["roh_t"] - 2.4)) > 0.0011 or abs(z["n0_t"] - (z["roh_t"] - 16.0)) > 0.0011:
        ab["Kostenabzug"] = ab.get("Kostenabzug", 0) + 1
    if st != URSPR.get(z["status"], z["status"]):
        rand = abs(z["t_roh_t"] - 2) < 0.0006 or abs(z["t85_t"] - 2) < 0.0006 or min(abs(z["roh_t"]), abs(z["n85_t"]), abs(z["n85_h1"]), abs(z["n85_h2"]), abs(z["n85_2x_t"])) < 0.0006
        if rand: knapp += 1
        else:
            ab[f"{z['status']}->{st}"] = ab.get(f"{z['status']}->{st}", 0) + 1
print(f"Status neu abgeleitet für {n} Kandidaten: Abweichungen {ab}, nur wegen Rundung an der Schwelle: {knapp}")
# 2 Zeilenzuordnung: Summe der Tagesreihe über T mal Zahl der Coins = n85_t * n_t; t-Wert der Tagesreihe = t85_t; ebenso V1
rng = random.Random(3)
for gen in ("gen1", "gen2"):
    tage = np.load(f'data/fabrik/tage_{gen}.npy', mmap_mode='r')
    alle = con.execute("SELECT id, zeile, signal, braucht, best, m, n_t, n85_t, t85_t, n_v, n85_v, t85_v FROM kandidaten WHERE gen = ? AND n_t > 0", (gen,)).fetchall()
    wahl = sorted(rng.sample(alle, 20000), key=lambda z: z["zeile"])
    schlecht, maxd, maxt, vor_t0 = 0, 0.0, 0.0, 0
    for z in wahl:
        tief = z["braucht"] == "t" or (z["best"] and ("tiefe" in z["best"] or "liq_entzug" in z["best"]))
        t0, v0, e = L.SEGMENTE["t" if tief else "k"]
        m = len([c for c in G.MAERKTE[z["m"]] if not (c == 0 and z["signal"].startswith(("btcfuehrt", "relstaerke", "korrbruch")))])
        r = np.asarray(tage[z["zeile"]], dtype=np.float64)
        vor_t0 += bool(np.any(r[:t0] != 0))
        sT, sV = r[t0:v0].sum() * m, r[v0:e].sum() * m
        tw = lambda p: p.mean() / p.std(ddof=1) * np.sqrt(len(p)) if p.std(ddof=1) > 0 else 0.0
        d = max(abs(sT / z["n_t"] - z["n85_t"]), abs(sV / z["n_v"] - z["n85_v"]) if z["n_v"] else 0.0)
        dt = max(abs(tw(r[t0:v0]) - z["t85_t"]), abs(tw(r[v0:e]) - z["t85_v"]))
        maxd, maxt = max(maxd, d), max(maxt, dt)
        schlecht += d > 0.01 or dt > 0.01
    print(f"{gen}: 20000 zufällige Zeilen: Tagesreihe passt nicht zu n85/t85 der Datenbank: {schlecht} | größte Abweichung n85 {maxd:.5f} bp, t {maxt:.5f} | Zeilen mit Buchungen vor dem T-Beginn: {vor_t0}")
