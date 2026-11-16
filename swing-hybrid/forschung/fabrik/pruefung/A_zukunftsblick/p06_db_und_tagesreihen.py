"""Stichprobe: Datenbankzeile und Tagesreihe (tage_<gen>.npy, Zeile = Spalte "zeile") gegen Neuberechnung mit einstieg + kern.sim.
Liest nur T und V1. Zweck: Die gespeicherten Ergebnisse gehören zu genau diesen Speichern und diesem Code (keine verrutschten Zeilen)."""
import json, sqlite3, sys
sys.path.insert(0, 'forschung')
import numpy as np
from fabrik import daten as D, lauf as L, kern as FK, signale as S, generator as G, evolution as E

L._init()
AUSST = {**G.AUSSTIEGE, **E.NEUE_AUSSTIEGE}
con = sqlite3.connect('file:data/fabrik/forschung.sqlite?mode=ro', uri=True); con.row_factory = sqlite3.Row
rng = np.random.default_rng(11)
fehler = 0
for gen in ("gen1", "gen2"):
    zeilen = con.execute("SELECT * FROM kandidaten WHERE gen=? AND n_t >= 200 ORDER BY id", (gen,)).fetchall()
    wahl = [zeilen[int(i)] for i in rng.choice(len(zeilen), 40, replace=False)]
    tage = np.load(D.SPEICHER / f"tage_{gen}.npy", mmap_mode="r")
    slip = np.asarray(L._g["slip_bp"]) * 2.0
    ok_tage = ok_db = 0
    for z in wahl:
        a = {"si": S.NAMEN.index(z["signal"]), "signal": z["signal"], "th": z["th"], "r": z["r"], "f": z["f"], "k": z["k"]}
        if z["best"]:
            b = json.loads(z["best"]); a["best"] = {"si": S.NAMEN.index(b[0]), "th": b[1], "r": b[2]}
        tief = z["braucht"] == "t" or (z["best"] and S.SIGNALE[S.NAMEN.index(json.loads(z["best"])[0])][3] == "t")
        t0, v0, ende = L.SEGMENTE["t" if tief else "k"]
        i0 = L.I_T + t0 * 288
        halte, sl, tp, tr, ta, sx = AUSST[z["x"]]
        ohne_btc = z["signal"].startswith(("btcfuehrt", "relstaerke", "korrbruch"))
        M = np.array([c for c in G.MAERKTE[z["m"]] if not (ohne_btc and c == 0)])
        arr = [np.zeros((len(D.COINS), L.N_TAGE)) for _ in range(6)]
        for j in M:
            ein, wert = L.einstieg(a, j)
            FK.sim(L._g["o"][j], L._g["h"][j], L._g["l"][j], L._g["fcum"][j], ein, wert, L._g["sigma"][j], L._g["tag"], i0, L.I_ENDE, halte, sl, tp, tr, ta,
                   np.nan if sx is None else sx, slip[j], L.KOSTEN85, *(x[j] for x in arr), 0)
        reihe = ((arr[0][M].sum(0) - arr[1][M].sum(0) * L.KOSTEN85) / len(M)).astype(np.float32)
        g1 = np.array_equal(reihe, np.asarray(tage[z["zeile"]]))
        T_, V_ = L.kennzahlen(arr, M, t0, v0, slip), L.kennzahlen(arr, M, v0, ende, slip)
        g2 = (T_["n"] == z["n_t"] and abs(T_["roh"] - z["roh_t"]) < 6e-4 and abs(T_["t85"] - z["t85_t"]) < 6e-4 and V_["n"] == z["n_v"] and abs(V_["n85"] - z["n85_v"]) < 6e-4)
        ok_tage += g1; ok_db += g2
        if not (g1 and g2):
            fehler += 1
            print("  ABWEICHUNG", gen, z["id"], z["signal"], z["x"], z["m"], "Tagesreihe gleich:", g1, "| DB gleich:", g2, "| n_t", T_["n"], z["n_t"], "roh_t", round(T_["roh"], 3), z["roh_t"])
    print(f"{gen}: {len(wahl)} Kandidaten geprüft | Tagesreihe bitgleich: {ok_tage} | Kennzahlen (n_t, roh_t, t85_t, n_v, n85_v) gleich: {ok_db}")
print("ABWEICHUNGEN:", fehler)
