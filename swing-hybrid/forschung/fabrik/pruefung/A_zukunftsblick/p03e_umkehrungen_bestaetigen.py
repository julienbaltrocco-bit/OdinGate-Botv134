"""Bestätigung der in p03c gefundenen Umkehrungen NUR mit dem unveränderten kern.sim: "eine Kerze Verzögerung" wird als verzug=0 auf um
eine Kerze nach hinten verschobenen Eingaben gerechnet (für alle anderen Ausstiege ist das nachweislich dasselbe wie verzug=1, siehe p03d).
Liest nur T und V1; schreibt nichts außer der eigenen Ausgabe."""
import json, sqlite3, sys
from pathlib import Path
sys.path.insert(0, 'forschung')
import numpy as np
from fabrik import daten as D, lauf as L, kern as FK, generator as G, trichter as T

L._init()
HIER = Path(__file__).resolve().parent
umk = json.loads((HIER / "p03c_umkehrungen.json").read_text())
con = sqlite3.connect('file:data/fabrik/forschung.sqlite?mode=ro', uri=True); con.row_factory = sqlite3.Row
slip = np.asarray(L._g["slip_bp"]) * 2.0
gleich = bestaetigt = 0
final = []
for u in umk:
    z = con.execute("SELECT * FROM kandidaten WHERE id=? AND gen=?", (u["id"], u["gen"])).fetchone()
    a = T.aufgabe_aus(z); halte, sl, tp, tr, ta, sx = T.ausstieg_aus(z)
    tief = z["braucht"] == "t" or (z["best"] and ("tiefe" in z["best"] or "liq_entzug" in z["best"]))
    i0 = L.I_TIEFE if tief else L.I_T
    M = [c for c in G.MAERKTE[z["m"]] if not (c == 0 and z["signal"].startswith(("btcfuehrt", "relstaerke", "korrbruch")))]
    n_tage = (L.I_ENDE - i0) // 288
    tag = np.clip((np.arange(D.N) - i0) // 288, 0, n_tage - 1).astype(np.int32)
    summe = {0: [0.0, 0], 1: [0.0, 0]}
    for j in M:
        ein, wert = L.einstieg(a, j)
        sigma = np.asarray(L._g["sigma"][j, :L.I_ENDE])
        ein_s = np.concatenate([[0], ein[:-1]]).astype(np.int8); ein_s[:i0 + 1] = 0
        wert_s = np.concatenate([[np.nan], wert[:-1]]); sigma_s = np.concatenate([[np.nan], sigma[:-1]]).astype(np.float32)
        for art, (e_, w_, s_, vz) in {0: (ein_s, wert_s, sigma_s, 0), 1: (ein, wert, sigma, 1)}.items():
            arr = [np.zeros(n_tage) for _ in range(6)]
            FK.sim(L._g["o"][j], L._g["h"][j], L._g["l"][j], L._g["fcum"][j], e_, w_, s_, tag, i0, L.I_ENDE, halte, sl, tp, tr, ta, sx, slip[j], L.KOSTEN85, *arr, vz)
            summe[art][0] += arr[0].sum(); summe[art][1] += arr[1].sum()
    roh_versch = summe[0][0] / summe[0][1]; roh_verzug1 = summe[1][0] / summe[1][1]
    gleich += int(abs(roh_versch - u["roh_einfach"]) < 2e-3 and abs(roh_verzug1 - u["roh_doppelt"]) < 2e-3)
    ok_richtig = roh_versch - L.KOSTEN85 > 0; ok_istzustand = roh_verzug1 - L.KOSTEN85 > 0
    bestaetigt += int(ok_richtig != ok_istzustand)
    if z["status"] == "final" or u["status"] == "final":
        final.append((u["gen"], u["id"], z["signal"], z["th"], z["r"], z["f"], z["k"], z["x"], z["m"], f"verzug=1: {roh_verzug1:.2f} bp", f"eine Kerze verschoben: {roh_versch:.2f} bp", f"Hürde > {L.KOSTEN85}"))
print(f"{len(umk)} Umkehrungen aus p03c | Ergebnis mit Verschiebung == Ergebnis der korrigierten Kopie: {gleich} | Urteil kehrt sich auch hier um: {bestaetigt}")
print("Betroffene Finalisten (Status final, bestanden nur wegen der doppelten Verzögerung):")
for f in final:
    print("  ", f)
fin = json.loads(Path("forschung/fabrik/ergebnisse/finalisten.json").read_text())
ids = {(f["gen"], f["id"]) for f in fin["finalisten"]}
print("davon in ergebnisse/finalisten.json (eingefroren", fin["eingefroren"], "):", sum(((u["gen"], u["id"]) in ids) for u in umk), "von", len(fin["finalisten"]), "Finalisten")
