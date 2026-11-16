"""Auswirkung der doppelten Verzögerung beim Signal-Ausstieg (kern.sim, verzug=1) auf die Stufe-3-Prüfung "eine Kerze Verzögerung".

Rechnet nur T und V1 (Kerzen < I_ENDE), schreibt nichts in die Datenbank und führt stufe3/stufe4 NICHT aus. Benutzt wird
trichter.tagesreihe (reine Rechnung) einmal mit dem Simulator wie er ist und einmal mit einer Kopie, in der der Signal-Ausstieg genau
verzug Kerzen später erfolgt (Signal am Schluss s -> Ausstieg Eröffnung s+1+verzug). Die Kopie mit doppelt=True muss kern.sim genau
nachbilden (Kontrolle).
"""
import sqlite3, sys, time
sys.path.insert(0, 'forschung')
import numpy as np
from numba import njit
from fabrik import daten as D, lauf as L, kern as FK, trichter as T

NAN = np.nan


@njit(nogil=True)
def sim2(o, h, l, fcum, ein, wert, sigma, tag, i0, i1, halte, sl, tp, trail, trail_ab, sx, slip_rt, kosten85,
         roh_tag, n_tag, gew_tag, pos_tag, neg_tag, dauer_tag, verzug, doppelt):
    stops = sl > 0 or tp > 0 or trail > 0
    i, n = i0, 0
    while i < i1 - 2 - verzug:
        d = ein[i]
        if d == 0:
            i += 1
            continue
        a = i + 1 + verzug
        s = sigma[i]
        if stops and not (s > 0):
            i += 1
            continue
        e = o[a]
        stop = e * (1 - d * sl * s) if sl > 0 else NAN
        ziel = e * (1 + d * tp * s) if tp > 0 else NAN
        best, b, px = e, -1, NAN
        ende = min(a + halte, i1 - 1)
        j = a
        while j < ende:
            if stop == stop:
                if d > 0 and l[j] <= stop:
                    px = min(o[j], stop); b = j; break
                if d < 0 and h[j] >= stop:
                    px = max(o[j], stop); b = j; break
            if ziel == ziel:
                if d > 0 and h[j] >= ziel:
                    px = max(o[j], ziel); b = j; break
                if d < 0 and l[j] <= ziel:
                    px = min(o[j], ziel); b = j; break
            best = max(best, h[j]) if d > 0 else min(best, l[j])
            if trail > 0 and d * (best / e - 1) >= trail_ab * s:
                neu = best * (1 - d * trail * s)
                if stop != stop:
                    stop = neu
                else:
                    stop = max(stop, neu) if d > 0 else min(stop, neu)
            if sx == sx and wert[j - verzug] * d < sx:
                b = min(j + 1 + verzug, ende) if doppelt else min(j + 1, ende)      # <- einzige Änderung
                break
            j += 1
        am_open = px != px
        if b < 0:
            b = ende
        if am_open:
            px = o[b]
        roh = d * (px / e - 1) * 1e4 - slip_rt - d * (fcum[b] - fcum[a]) * 1e4
        t = tag[a]
        roh_tag[t] += roh
        n_tag[t] += 1
        n85 = roh - kosten85
        if n85 > 0:
            gew_tag[t] += 1; pos_tag[t] += n85
        else:
            neg_tag[t] += n85
        dauer_tag[t] += b - a
        n += 1
        i = b - 1 - verzug if am_open else b - verzug
        if i < a - verzug:
            i = a - verzug
    return n


ORIG = FK.sim
wie_ist = lambda *a: sim2(*a, True)
richtig = lambda *a: sim2(*a, False)


def urteil(z, i0, simfn):
    FK.sim = simfn
    try:
        p, n, roh = T.tagesreihe(z, i0, L.I_ENDE, verzug=1)
    finally:
        FK.sim = ORIG
    return n, roh, bool(n > 0 and roh - L.KOSTEN85 > 0)


if __name__ == "__main__":
    L._init()
    con = sqlite3.connect('file:data/fabrik/forschung.sqlite?mode=ro', uri=True); con.row_factory = sqlite3.Row
    alle = con.execute("SELECT * FROM kandidaten WHERE x LIKE 'signal%' AND (status IN ('stufe3','final') OR (status='verworfen_3' AND grund IN ('eine Kerze Verzögerung','nach Abzug des Marktes kein gesicherter Ertrag'))) ORDER BY gen, id").fetchall()
    grenze = int(sys.argv[1]) if len(sys.argv) > 1 else len(alle)
    if grenze < len(alle):
        alle = [alle[i] for i in np.random.default_rng(5).choice(len(alle), grenze, replace=False)]
    print(len(alle), "Kandidaten mit Signal-Ausstieg, die die Verzögerungsprüfung erreicht haben", flush=True)
    t0 = time.time()
    zahl = {"kontrolle_kopie_ungleich_kern": 0, "db_urteil_nicht_nachvollzogen": 0, "abgelehnt_waere_bestanden": 0, "bestanden_waere_abgelehnt": 0, "abgelehnt": 0, "bestanden": 0,
            "abgelehnt_waere_bestanden_und_alpha_ok": 0}
    diff, bsp, umk = [], [], []
    for q, z in enumerate(alle):
        tief = z["braucht"] == "t" or (z["best"] and ("tiefe" in z["best"] or "liq_entzug" in z["best"]))
        i0 = L.I_TIEFE if tief else L.I_T
        nA, rohA, okA = urteil(z, i0, wie_ist)
        nB, rohB, okB = urteil(z, i0, richtig)
        if q % 25 == 0:                                         # Kontrolle: Kopie (doppelt=True) == kern.sim
            nO, rohO, okO = urteil(z, i0, ORIG)
            zahl["kontrolle_kopie_ungleich_kern"] += int(not (nO == nA and rohO == rohA))
        db_abgelehnt = z["status"] == "verworfen_3" and z["grund"] == "eine Kerze Verzögerung"
        zahl["abgelehnt" if db_abgelehnt else "bestanden"] += 1
        zahl["db_urteil_nicht_nachvollzogen"] += int(okA == db_abgelehnt)
        diff.append(rohB - rohA)
        if db_abgelehnt and okB:
            zahl["abgelehnt_waere_bestanden"] += 1
            alpha, t_alpha, beta = T.marktbereinigt(z, i0, L.I_ENDE)
            zahl["abgelehnt_waere_bestanden_und_alpha_ok"] += int(alpha > 0 and t_alpha >= 2)
            if len(bsp) < 8:
                bsp.append((z["gen"], z["id"], z["signal"], z["th"], z["r"], z["f"], z["k"], z["x"], z["m"], f"roh mit doppelter Verzögerung {rohA:.2f} bp, mit einfacher {rohB:.2f} bp, Schwelle {L.KOSTEN85}", f"alpha t {t_alpha:.2f}"))
        if (not db_abgelehnt) and not okB:
            zahl["bestanden_waere_abgelehnt"] += 1
            zahl["davon_status_" + z["status"]] = zahl.get("davon_status_" + z["status"], 0) + 1
            umk.append({"gen": z["gen"], "id": z["id"], "status": z["status"], "grund": z["grund"], "art": "bestanden, wäre abgelehnt", "roh_doppelt": round(rohA, 3), "roh_einfach": round(rohB, 3)})
        if db_abgelehnt and okB:
            umk.append({"gen": z["gen"], "id": z["id"], "status": z["status"], "grund": z["grund"], "art": "abgelehnt, wäre bestanden", "roh_doppelt": round(rohA, 3), "roh_einfach": round(rohB, 3)})
    diff = np.array(diff)
    print(zahl)
    print(f"roh je Trade (bp): einfache minus doppelte Verzögerung: Mittel {diff.mean():+.3f}, Median {np.median(diff):+.3f}, min {diff.min():+.2f}, max {diff.max():+.2f}; Anteil > 0: {(diff > 0).mean():.2f}")
    for b in bsp:
        print("  Beispiel:", b)
    if grenze >= len(alle):
        import json
        from pathlib import Path
        (Path(__file__).resolve().parent / "p03c_umkehrungen.json").write_text(json.dumps(umk, ensure_ascii=False, indent=1))
    print(f"Rechenzeit {time.time() - t0:.0f} s")
