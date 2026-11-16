"""Prüfung lauf.einstieg und kern.sim / kern.trades_liste auf echten Speichern (nur Kerzen < I_ENDE).

(1) einstieg: unabhängige Nachbildung der Regeln (Schwelle, Richtung, Bestätigung, Filter, Takt, gültig) elementweise.
(2) Störung: Signale, Filter, sigma, Kurse, Funding, gültig ab Kerze T verfälscht -> einstieg[:T] gleich; Trades mit Ausstieg < T
    vollständig gleich; alle Einstiege bis T gleich; Tagesfelder von sim für Tage, deren Trades vor T enden, gleich.
(3) trades_liste gegen den unabhängigen Vergleichs-Simulator (ref_sim.py) für alle 20 Ausstiege.
(4) sim (verzug=0) gegen trades_liste: Tagesfelder.
(5) Takt-Maske: Schlusszeit der Signalkerze.
"""
import json, sys
from pathlib import Path
sys.path.insert(0, 'forschung')
sys.path.insert(0, str(Path(__file__).resolve().parent))
import numpy as np, pandas as pd
from fabrik import daten as D, lauf as L, kern as FK, generator as G, signale as S, evolution as E
from ref_sim import ref_trades, roh_bp

I_ENDE = L.I_ENDE
rng = np.random.default_rng(7)
ECHT = {n: np.array(np.load(D.SPEICHER / f"{n}.npy", mmap_mode="r")[..., :I_ENDE]) for n in ("o", "h", "l", "fcum", "gueltig", "filter", "sigma")}
SIG = np.load(D.SPEICHER / "signale.npy", mmap_mode="r")
slip = np.load(D.SPEICHER / "slip_bp.npy") * 2.0
AUSST = {**G.AUSSTIEGE, **E.NEUE_AUSSTIEGE}


def setze(g, sig_teile):
    """_g für einstieg(): Signale nur für die gebrauchten (si) als dünnes Wörterbuch-Feld."""
    L._g.clear()
    for n in ("o", "h", "l", "fcum", "gueltig", "filter", "sigma"):
        L._g[n] = g[n]
    L._g["signale"] = sig_teile
    L._g["pos"] = np.arange(D.N)
    L._g["tag"] = np.maximum((np.arange(D.N) - L.I_T) // 288, 0).astype(np.int32)


class SigFeld:
    """Liefert signale[si, j, :I_ENDE] wie das Speicherabbild, optional ab T verfälscht."""
    def __init__(self, T=None, seed=0):
        self.T, self.seed, self.c = T, seed, {}
    def __getitem__(self, key):
        si, j, sl_ = key
        if (si, j) not in self.c:
            a = np.array(SIG[si, j, :I_ENDE])
            if self.T is not None:
                r = np.random.default_rng(self.seed + 1000 * si + j)
                a[self.T:] = r.normal(0, 2.5, I_ENDE - self.T).astype(np.float32)
            self.c[(si, j)] = a
        return self.c[(si, j)][sl_]


def zufalls_aufgabe():
    si = int(rng.integers(len(S.NAMEN)))
    a = {"si": si, "signal": S.NAMEN[si], "braucht": S.SIGNALE[si][3], "th": float(rng.choice([1.0, 1.5, 2.0, 2.5, 3.5])), "r": int(rng.choice([1, -1])),
         "f": str(rng.choice(S.FILTER)), "k": int(rng.choice([1, 3, 12]))}
    if rng.random() < 0.3:
        bi = int(rng.integers(len(S.NAMEN)))
        a["best"] = {"si": bi, "signal": S.NAMEN[bi], "th": 1.0, "r": int(rng.choice([1, -1])), "braucht": S.SIGNALE[bi][3]}
    return a


def einstieg_eigen(a, j, sig, g):
    """Eigene Nachbildung in Python-Schleifenlogik über Zeitstempel (ohne lauf.einstieg, ohne signale.filter_maske)."""
    w = np.asarray(sig[a["si"], j, slice(0, I_ENDE)], np.float64)
    lang, kurz = w >= a["th"], w <= -a["th"]
    d = np.where(lang, 1, np.where(kurz, -1, 0)) * a["r"]
    if a.get("best"):
        b = a["best"]
        w2 = np.asarray(sig[b["si"], j, slice(0, I_ENDE)], np.float64)
        d2 = np.where(w2 >= b["th"], 1, np.where(w2 <= -b["th"], -1, 0)) * b["r"]
        d = np.where(d == d2, d, 0)
    f = g["filter"][:, j]
    zeit = D.RASTER[:I_ENDE]
    schluss_minute = (zeit.hour * 60 + zeit.minute + 5).to_numpy()            # Minute des Kerzenschlusses
    erlaubt = {"kein": np.ones(I_ENDE, bool), "trend_mit": f[0] == d, "trend_gegen": f[0] == -d, "vol_hoch": f[1] == 2, "vol_niedrig": f[1] == 0,
               "asien": zeit.hour.to_numpy() < 8, "europa": (zeit.hour.to_numpy() >= 8) & (zeit.hour.to_numpy() < 16), "usa": zeit.hour.to_numpy() >= 16,
               "btc_auf": f[3] == 1, "btc_ab": f[3] == -1}[a["f"]]
    takt = schluss_minute % (5 * a["k"]) == 0                                   # Signal nur an Kerzen, die auf dem Takt-Raster schließen
    return np.where(erlaubt & takt & g["gueltig"][j], d, 0).astype(np.int8), w * a["r"]


def trades(g, ein, wert, j, i0, i1, x):
    halte, sl, tp, tr, ta, sx = x
    aus = np.zeros((60000, 6))
    n = FK.trades_liste(g["o"][j], g["h"][j], g["l"][j], g["fcum"][j], ein, wert, g["sigma"][j], i0, i1, halte, sl, tp, tr, ta, np.nan if sx is None else sx, slip[j], aus)
    return aus[:n].copy()


def sim(g, ein, wert, j, i0, i1, x, verzug=0):
    halte, sl, tp, tr, ta, sx = x
    z = [np.zeros(L.N_TAGE) for _ in range(6)]
    n = FK.sim(g["o"][j], g["h"][j], g["l"][j], g["fcum"][j], ein, wert, g["sigma"][j], L._g["tag"], i0, i1, halte, sl, tp, tr, ta, np.nan if sx is None else sx, slip[j], L.KOSTEN85, *z, verzug)
    return n, z


def verfaelscht(T, seed):
    r = np.random.default_rng(seed)
    g = {n: ECHT[n].copy() for n in ECHT}
    n = I_ENDE - T
    for j in range(len(D.COINS)):
        basis = g["o"][j, T - 1] * np.exp(np.cumsum(r.normal(0, 0.004, n)))
        g["o"][j, T:] = basis
        g["h"][j, T:] = basis * (1 + np.abs(r.normal(0, 0.004, n)))
        g["l"][j, T:] = basis * (1 - np.abs(r.normal(0, 0.004, n)))
        g["fcum"][j, T:] = g["fcum"][j, T - 1] + np.cumsum(r.normal(0, 1e-4, n) * (r.random(n) < 0.02))
        g["sigma"][j, T:] = np.abs(r.normal(0.01, 0.005, n)).astype(np.float32)
        g["gueltig"][j, T:] = r.random(n) < 0.97
    g["filter"][0, :, T:] = r.integers(-1, 2, (len(D.COINS), n)); g["filter"][1, :, T:] = r.integers(-1, 3, (len(D.COINS), n))
    g["filter"][2, :, T:] = r.integers(0, 3, (len(D.COINS), n)); g["filter"][3, :, T:] = r.integers(-1, 2, (len(D.COINS), n))
    return g


if __name__ == "__main__":
    n_aufg = int(sys.argv[1]) if len(sys.argv) > 1 else 30
    zaehler = dict(einstieg_ungleich=0, einstieg_geprueft=0, stoer_einstieg=0, stoer_trades=0, stoer_sim=0, stoer_geprueft=0, ref_ungleich=0, ref_geprueft=0, ref_trades=0,
                   sim_ungleich=0, sim_geprueft=0, n_diff=0)
    beispiele = []
    for q in range(n_aufg):
        a = zufalls_aufgabe()
        j = int(rng.integers(1 if a["signal"].startswith(("btcfuehrt", "relstaerke", "korrbruch")) else 0, len(D.COINS)))
        tief = a["braucht"] == "t" or (a.get("best") or {}).get("braucht") == "t"
        i0 = L.I_TIEFE if tief else L.I_T
        sig0 = SigFeld()
        setze(ECHT, sig0)
        ein, wert = L.einstieg(a, j)
        # (1) eigene Nachbildung
        ein_e, wert_e = einstieg_eigen(a, j, sig0, ECHT)
        zaehler["einstieg_geprueft"] += 1
        if not (np.array_equal(ein, ein_e) and np.array_equal(wert, wert_e, equal_nan=True)):
            zaehler["einstieg_ungleich"] += 1; beispiele.append(("einstieg", a, j, int(np.argmax(ein != ein_e))))
        # (2) Störung ab T
        T = int(rng.integers(i0 + 30000, I_ENDE - 2000))
        gB = verfaelscht(T, 100 + q)
        sigB = SigFeld(T, seed=q)
        setze(gB, sigB)
        einB, wertB = L.einstieg(a, j)
        setze(ECHT, sig0)
        zaehler["stoer_geprueft"] += 1
        if not (np.array_equal(ein[:T], einB[:T]) and np.array_equal(wert[:T], wertB[:T], equal_nan=True)):
            zaehler["stoer_einstieg"] += 1; beispiele.append(("stoerung einstieg", a, j, T))
        for xname in rng.choice(list(AUSST), 6, replace=False):
            x = AUSST[xname]
            tA = trades(ECHT, ein, wert, j, i0, I_ENDE, x)
            tB = trades(gB, einB, wertB, j, i0, I_ENDE, x)
            vorA, vorB = tA[tA[:, 1] < T], tB[tB[:, 1] < T]
            einA, einBB = tA[tA[:, 0] <= T][:, [0, 2]], tB[tB[:, 0] <= T][:, [0, 2]]
            if not (np.array_equal(vorA, vorB) and np.array_equal(einA, einBB)):
                zaehler["stoer_trades"] += 1; beispiele.append(("stoerung trades", a, j, T, xname))
            for verzug in (0, 1):
                nA, zA = sim(ECHT, ein, wert, j, i0, I_ENDE, x, verzug)
                nB, zB = sim(gB, einB, wertB, j, i0, I_ENDE, x, verzug)
                tag_sicher = (T - x[0] - 4 - 2 * verzug - L.I_T) // 288 - 1          # Tage, deren Trades sicher vor T enden
                tag_T = (T - L.I_T) // 288
                if not (all(np.array_equal(zA[k][:tag_sicher], zB[k][:tag_sicher]) for k in range(6)) and np.array_equal(zA[1][:tag_T], zB[1][:tag_T])):
                    zaehler["stoer_sim"] += 1; beispiele.append(("stoerung sim", a, j, T, xname, verzug))
            # (4) sim gegen trades_liste
            nS, zS = sim(ECHT, ein, wert, j, i0, I_ENDE, x, 0)
            tg = L._g["tag"][tA[:, 0].astype(int)]
            roh_tag = np.bincount(tg, weights=tA[:, 3], minlength=L.N_TAGE); n_tag = np.bincount(tg, minlength=L.N_TAGE)
            dauer = np.bincount(tg, weights=tA[:, 1] - tA[:, 0], minlength=L.N_TAGE)
            zaehler["sim_geprueft"] += 1
            if nS != len(tA):
                zaehler["n_diff"] += 1
            if not (np.allclose(zS[0], roh_tag, atol=1e-6) and np.array_equal(zS[1], n_tag) and np.array_equal(zS[5], dauer)):
                zaehler["sim_ungleich"] += 1; beispiele.append(("sim != trades_liste", a, j, xname, nS, len(tA)))
            # (3) unabhängiger Vergleichs-Simulator auf einem Teilfenster (120 Tage)
            w0 = int(rng.integers(i0, I_ENDE - 36000)); w1 = w0 + 34560
            tF = trades(ECHT, ein, wert, j, w0, w1, x)
            tR = ref_trades(ECHT["o"][j], ECHT["h"][j], ECHT["l"][j], ein, wert, ECHT["sigma"][j], w0, w1, *x)
            rR = roh_bp(tR, ECHT["fcum"][j], slip[j])
            zaehler["ref_geprueft"] += 1; zaehler["ref_trades"] += len(tF)
            gleich = len(tF) == len(tR) and (len(tF) == 0 or (np.array_equal(tF[:, 0], [t[0] for t in tR]) and np.array_equal(tF[:, 1], [t[1] for t in tR])
                                                               and np.array_equal(tF[:, 2], [t[2] for t in tR]) and np.allclose(tF[:, 3], rR, atol=1e-7)))
            if not gleich:
                zaehler["ref_ungleich"] += 1; beispiele.append(("ref != trades_liste", a, j, xname, w0, w1, len(tF), len(tR)))
    print(json.dumps(zaehler, indent=1))
    for b in beispiele[:15]:
        print("ABWEICHUNG:", b)
    # (5) Takt: Schlusszeiten der Signalkerzen
    setze(ECHT, SigFeld())
    for k in (1, 3, 12):
        a = {"si": S.NAMEN.index("mom_12"), "th": 1.5, "r": 1, "f": "kein", "k": k}
        ein, _ = L.einstieg(a, 2)
        i = np.flatnonzero(ein != 0)
        schluss = D.RASTER[i] + pd.Timedelta(minutes=5)
        print(f"Takt k={k}: {len(i)} Signale; Minuten des Kerzenschlusses: {sorted(set(schluss.minute.tolist()))}")
