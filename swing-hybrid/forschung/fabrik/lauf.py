"""Massen-Rückrechnung der Fabrik: verteilt Einstiegsregeln auf Rechenkerne, speichert jedes Ergebnis, ist wiederaufnehmbar.

  .venv/bin/python -I forschung/fabrik/lauf.py gen1                 (alle Kandidaten der ersten Generation)
  .venv/bin/python -I forschung/fabrik/lauf.py <name> <aufgaben.json>   (eigene Aufgabenliste, z. B. aus der Evolution)

Gelesen werden nur Training T und Auswahlprüfung V1 (bis 30.06.2024). Stufe 1 und 2 des Trichters werden gleich
mitbewertet. Ergebnisse: data/fabrik/forschung.sqlite (Tabelle kandidaten) und data/fabrik/tage_<name>.npy
(Tagesergebnis netto mit Rebate je Kandidat). Ein abgebrochener Lauf setzt bei der nächsten offenen Aufgabe fort.
"""
import json
import os
import sqlite3
import sys
import time
import multiprocessing
from pathlib import Path

import numpy as np

F = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(F))
from fabrik import daten as D, generator as G, kern as FK, signale as S

AUS = Path(os.environ.get("FABRIK_AUS", D.SPEICHER))             # Ergebnisordner (Datenbank, Tagesreihen, Aufgabenlisten)
DB = AUS / "forschung.sqlite"
KOSTEN85, GEBUEHR = 2.4, 16.0
idx = lambda t: int(np.searchsorted(D.RASTER.values, np.datetime64(t)))
I_T, I_TIEFE, I_V1, I_ENDE = idx("2021-08-15"), idx("2023-01-01"), idx("2023-07-01"), idx("2024-07-01")
N_TAGE = (I_ENDE - I_T) // 288
tagnr = lambda t: (idx(t) - I_T) // 288
SEGMENTE = {"k": (0, tagnr("2023-07-01"), N_TAGE), "t": (tagnr("2023-01-01"), tagnr("2024-01-01"), N_TAGE)}   # T-Beginn, V1-Beginn, Ende (Tagesnummern)
SPALTEN = ("id gen signal familie braucht th r f k x m best eltern zeile n_t roh_t n85_t t_roh_t t85_t n85_h1 n85_h2 n85_2x_t n0_t sharpe_t pf_t quote_t "
           "dauer_min rueck_t n_v roh_v n85_v t85_v sharpe_v status grund").split()
_g = {}


def _init():
    for name in ("o", "h", "l", "c", "fcum", "gueltig", "signale", "filter", "sigma", "slip_bp"):
        _g[name] = D.laden(name)
    _g["tag"] = np.maximum((np.arange(D.N) - I_T) // 288, 0).astype(np.int32)
    _g["pos"] = np.arange(D.N)
    g = np.asarray(_g["gueltig"])
    kum = np.cumsum(~g, axis=1)
    fehl7 = kum - np.concatenate([np.zeros((g.shape[0], S.W7), kum.dtype), kum[:, :-S.W7]], axis=1) if g.shape[1] > S.W7 else kum
    nach = np.concatenate([g[:, 1:], np.zeros((g.shape[0], 1), bool)], axis=1)
    _g["handelbar"] = g & nach & (fehl7 == 0)                     # keine Datenlücke in den letzten 7 Tagen, Einstiegskerze vorhanden
    basis = np.asarray(_g["slip_bp"])
    _g["slip_basis"] = [np.full(D.N, b) for b in basis]           # gemessene Yubit-Slippage je Order, konstant
    _g["slip_bewegt"] = {}


SPANNEN_ANTEIL = 0.05                                             # Slippage in bewegtem Markt: 5 % der Spanne der letzten Kerze je Order


def slip_bewegt(j: int, faktor=1.0) -> np.ndarray:
    """Slippage je Order in bp: das Größere aus der gemessenen Yubit-Slippage und einem Anteil der Spanne (Hoch - Tief) der letzten Kerze."""
    key = (j, faktor)
    if key not in _g["slip_bewegt"]:
        h, l, c = (np.asarray(_g[x][j], dtype=np.float64) for x in ("h", "l", "c"))
        _g["slip_bewegt"][key] = np.maximum(float(_g["slip_bp"][j]), SPANNEN_ANTEIL * faktor * (h - l) / c * 1e4)
    return _g["slip_bewegt"][key]


def ohne_btc(a: dict) -> bool:
    """BTC handelt nicht, wenn Haupt- oder Bestätigungssignal BTC selbst als Leitmarkt benutzt."""
    namen = [a["signal"]] + ([a["best"]["signal"]] if a.get("best") else [])
    return any(n.startswith(("btcfuehrt", "relstaerke", "korrbruch")) for n in namen)


def einstieg(a: dict, j: int):
    """Gewünschte Richtung je Kerze für Coin j (int8) und der ausgerichtete Signalwert für den Signal-Ausstieg."""
    w = np.asarray(_g["signale"][a["si"], j, :I_ENDE], dtype=np.float64)
    d = (np.where(w >= a["th"], 1, np.where(w <= -a["th"], -1, 0)) * a["r"]).astype(np.int8)
    if a.get("best"):                                             # zweites Signal muss dieselbe Richtung anzeigen
        b = a["best"]
        w2 = np.asarray(_g["signale"][b["si"], j, :I_ENDE], dtype=np.float64)
        d2 = np.where(w2 >= b["th"], 1, np.where(w2 <= -b["th"], -1, 0)) * b["r"]
        d = np.where(d == d2, d, 0).astype(np.int8)
    ok = _g["handelbar"][j, :I_ENDE] & S.filter_maske(a["f"], _g["filter"][:, :, :I_ENDE], j, d)
    if a["k"] > 1:
        ok &= (_g["pos"][:I_ENDE] + 1) % a["k"] == 0
    return np.where(ok, d, 0).astype(np.int8), w * a["r"]


def kennzahlen(z, M, d0, d1, slip):
    roh, n = z[0][M, d0:d1], z[1][M, d0:d1]
    nt = n.sum()
    if nt == 0:
        return dict(n=0, roh=0.0, n85=0.0, t_roh=0.0, t85=0.0, n85_2x=0.0, sharpe=0.0, pf=0.0, quote=0.0, dauer=0.0, rueck=0.0)
    tage, m = d1 - d0, len(M)
    p_roh = roh.sum(0) / m
    p85 = (roh.sum(0) - n.sum(0) * KOSTEN85) / m
    sr, s85 = p_roh.std(ddof=1), p85.std(ddof=1)
    kum = np.cumsum(p85)
    neg = z[4][M, d0:d1].sum()
    return dict(n=int(nt), roh=roh.sum() / nt, n85=roh.sum() / nt - KOSTEN85, t_roh=p_roh.mean() / sr * np.sqrt(tage) if sr > 0 else 0.0,
                t85=p85.mean() / s85 * np.sqrt(tage) if s85 > 0 else 0.0, n85_2x=roh.sum() / nt - KOSTEN85 - (n.sum(1) * slip[M]).sum() / nt,
                sharpe=p85.mean() / s85 * np.sqrt(365) if s85 > 0 else 0.0, pf=z[3][M, d0:d1].sum() / -neg if neg < 0 else 0.0,
                quote=z[2][M, d0:d1].sum() / nt, dauer=z[5][M, d0:d1].sum() / nt * 5, rueck=float((np.maximum.accumulate(kum) - kum).max()) / 100)


def bewerte(T, H1, H2, V):
    if T["n"] < 200:
        return "ungültig", "zu wenige Trades"
    if not (T["roh"] > 0 and T["t_roh"] >= 2):
        return "verworfen_1", "kein Brutto-Vorteil"
    if not (T["n85"] > 0 and T["t85"] >= 2):
        return "verworfen_2", "netto nicht gesichert"
    if not (H1["n85"] > 0 and H2["n85"] > 0):
        return "verworfen_2", "eine Hälfte negativ"
    if not T["n85_2x"] > 0:
        return "verworfen_2", "doppelte Slippage"
    return "stufe2", ""


def rechne(paket):
    """Eine Aufgabe (Einstiegsregel) -> je Ausstieg und Markt ein Kandidat. Schreibt die Tagesreihen direkt in das Speicherabbild."""
    gen, a, zeile0 = paket
    slip = np.asarray(_g["slip_bp"]) * 2.0                         # gemessene Slippage für Ein- und Ausstieg zusammen (für den Stress)
    t0, v0, ende = SEGMENTE["t" if a["braucht"] == "t" or (a.get("best") or {}).get("braucht") == "t" else "k"]
    i0 = I_T + t0 * 288
    kein_btc = ohne_btc(a)
    ein, wert = zip(*(einstieg(a, j) for j in range(len(D.COINS))))
    tage = np.load(AUS / f"tage_{gen}.npy", mmap_mode="r+")
    zeilen, lokal = [], 0
    for xname, (halte, sl, tp, tr, ta, sx) in a["ausstiege"].items():
        z = [np.zeros((len(D.COINS), N_TAGE)) for _ in range(6)]
        for j in range(len(D.COINS)):
            if kein_btc and j == 0:
                continue
            FK.sim(_g["o"][j], _g["h"][j], _g["l"][j], _g["fcum"][j], ein[j], wert[j], _g["sigma"][j], _g["tag"], i0, I_ENDE, halte, sl, tp, tr, ta,
                   np.nan if sx is None else sx, _g["slip_basis"][j], KOSTEN85, *(x[j] for x in z), 0)
        for mname, M in a["maerkte"].items():
            M = np.array([c for c in M if not (kein_btc and c == 0)])
            mitte = (t0 + v0) // 2
            T, H1, H2, V = (kennzahlen(z, M, x, y, slip) for x, y in ((t0, v0), (t0, mitte), (mitte, v0), (v0, ende)))
            status, grund = bewerte(T, H1, H2, V)
            k = {"s": a["signal"], "th": a["th"], "r": a["r"], "f": a["f"], "k": a["k"], "x": [halte, sl, tp, tr, ta, sx], "m": mname}
            if a.get("best"):
                k["b"] = [a["best"]["signal"], a["best"]["th"], a["best"]["r"]]
            tage[zeile0 + lokal] = ((z[0][M].sum(0) - z[1][M].sum(0) * KOSTEN85) / len(M)).astype(np.float32)
            zeilen.append((G.kennung(k), gen, a["signal"], a["familie"], a["braucht"], a["th"], a["r"], a["f"], a["k"], xname, mname,
                           json.dumps(k.get("b")) if a.get("best") else None, a.get("eltern"), zeile0 + lokal,
                           T["n"], round(T["roh"], 3), round(T["n85"], 3), round(T["t_roh"], 3), round(T["t85"], 3), round(H1["n85"], 3), round(H2["n85"], 3),
                           round(T["n85_2x"], 3), round(T["roh"] - GEBUEHR, 3), round(T["sharpe"], 3), round(T["pf"], 3), round(T["quote"], 4),
                           round(T["dauer"], 1), round(T["rueck"], 3), V["n"], round(V["roh"], 3), round(V["n85"], 3), round(V["t85"], 3), round(V["sharpe"], 3),
                           status, grund))
            lokal += 1
    tage.flush()
    return a["key"], zeilen


def haupt(gen: str, aufgaben: list):
    AUS.mkdir(parents=True, exist_ok=True)
    je = max(len(a["ausstiege"]) * len(a["maerkte"]) for a in aufgaben)
    for i, a in enumerate(aufgaben):
        a["key"] = f"{gen}|{i}"
    pfad = AUS / f"tage_{gen}.npy"
    if not pfad.exists():
        np.lib.format.open_memmap(pfad, mode="w+", dtype=np.float32, shape=(len(aufgaben) * je, N_TAGE))
    db = sqlite3.connect(DB, timeout=60)
    db.execute("PRAGMA journal_mode=WAL")
    db.execute(f"CREATE TABLE IF NOT EXISTS kandidaten ({', '.join(SPALTEN)}, PRIMARY KEY (id, gen))")
    db.execute("CREATE TABLE IF NOT EXISTS aufgaben (key TEXT PRIMARY KEY, fertig TEXT)")
    db.execute("CREATE TABLE IF NOT EXISTS laeufe (gen TEXT, begonnen TEXT, beendet TEXT, aufgaben INTEGER, kandidaten INTEGER, sekunden REAL, kandidaten_je_minute REAL, kerne INTEGER)")
    fertig = {r[0] for r in db.execute("SELECT key FROM aufgaben")}
    offen = [(gen, a, i * je) for i, a in enumerate(aufgaben) if a["key"] not in fertig]
    print(f"{gen}: {len(aufgaben)} Aufgaben, davon offen {len(offen)}; je Aufgabe bis zu {je} Kandidaten; Tage {N_TAGE}", flush=True)
    _init()
    z = [np.zeros(4) for _ in range(6)]                           # Simulator einmal übersetzen, bevor die Rechenkerne starten
    FK.sim(np.ones(8), np.ones(8), np.ones(8), np.zeros(8), np.zeros(8, np.int8), np.zeros(8), np.ones(8, np.float32), np.zeros(8, np.int32), 0, 8, 3, 0.0, 0.0, 0.0, 0.0, np.nan, np.zeros(8), 2.4, *z, 0)
    kerne = min(4, os.cpu_count() or 1)
    start, n_kand, n_auf, letzte = time.time(), 0, 0, time.time()
    begonnen = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    with multiprocessing.get_context("spawn").Pool(kerne, initializer=_init) as pool:      # frische Prozesse: kein geerbter Thread-Zustand
        puffer, keys = [], []
        for key, zeilen in pool.imap_unordered(rechne, offen, chunksize=4):
            puffer += zeilen; keys.append(key); n_kand += len(zeilen); n_auf += 1
            if len(keys) >= 200 or n_auf == len(offen):
                with db:                                           # eine Transaktion je Paket: Ergebnisse und Erledigt-Vermerk gemeinsam
                    db.executemany(f"INSERT OR REPLACE INTO kandidaten VALUES ({','.join('?' * len(SPALTEN))})", puffer)
                    db.executemany("INSERT OR REPLACE INTO aufgaben VALUES (?, ?)", [(k, time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())) for k in keys])
                puffer, keys = [], []
            if time.time() - letzte > 20:
                letzte = time.time()
                ram = next((int(x.split()[1]) / 2 ** 20 for x in open("/proc/meminfo") if x.startswith("MemAvailable")), 0)
                print(f"  {n_auf}/{len(offen)} Aufgaben, {n_kand} Kandidaten, {n_kand / (time.time() - start) * 60:,.0f} je Minute, Last {os.getloadavg()[0]:.1f}, RAM frei {ram:.1f} GB", flush=True)
    sek = time.time() - start
    with db:
        db.execute("INSERT INTO laeufe VALUES (?,?,?,?,?,?,?,?)", (gen, begonnen, time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), n_auf, n_kand, round(sek, 1),
                                                                   round(n_kand / sek * 60, 0) if sek > 0 else 0, kerne))
    print(f"fertig: {n_kand} Kandidaten in {sek:.0f} s = {n_kand / max(sek, 1e-9) * 60:,.0f} je Minute auf {kerne} Kernen", flush=True)
    for status, n in db.execute("SELECT status, COUNT(*) FROM kandidaten WHERE gen = ? GROUP BY status", (gen,)):
        print(f"  {status:<12} {n}")
    db.close()


if __name__ == "__main__":
    gen = sys.argv[1]
    if len(sys.argv) > 2:
        aufg = json.loads(Path(sys.argv[2]).read_text())
    else:
        aufg = [dict(a, ausstiege=G.AUSSTIEGE, maerkte=G.MAERKTE) for a in G.aufgaben()]
    if os.environ.get("FABRIK_PROBE"):
        aufg = aufg[:: int(os.environ["FABRIK_PROBE"])]
    haupt(gen, aufg)
