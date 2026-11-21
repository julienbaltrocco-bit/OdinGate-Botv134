"""E23: Marktstruktur als Zusatz zur Trendregel von Test 1 bis 3 (H20).

Festlegung und Präzisierungen: forschung/protokoll.md, Abschnitt 43. Der Code folgt dem Text dort Punkt für Punkt.

  .venv/bin/python -I forschung/experimente/e23_marktstruktur.py                  # T und V1 (V2 wird nicht gerechnet)
  .venv/bin/python -I forschung/experimente/e23_marktstruktur.py --v2 V2_4h_k3    # Schlussprüfung, nur für Besteher, einmal
  .venv/bin/python -I forschung/experimente/e23_marktstruktur.py --orders BTC V1 1 3 aus.csv   # Orderliste (Kontrolle)
"""
import json
import sys
from pathlib import Path

import numpy as np
from numba import njit

F = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(F))
from fabrik import daten as D  # noqa: E402

B0, V1, V2, V3, K1, K2, K3 = 0, 1, 2, 3, 4, 5, 6
ART = {"B0": B0, "V1": V1, "V2": V2, "V3": V3, "K1": K1, "K2": K2, "K3": K3}
TITEL = {"B0": "Basis (Regel von Test 1)", "V1": "Struktur-Stop", "V2": "Struktur-Stop mit Wiedereinstieg", "V3": "Struktur-Filter",
         "K1": "fester Stop 5 %", "K2": "Stop 5 % und Ziel 15 % (Regel von Test 2)", "K3": "nachgezogener Stop 5 % (Regel von Test 3)"}
EINSTELLUNGEN = [(1, 3), (1, 5), (4, 3), (4, 5)]                     # (TF in Stunden, Stärke k)
GEB_BP, REBATE = 8.0, 0.85                                          # Taker je Order; mit Rebate bleiben 1,2 bp
RUECK = 336                                                          # Stunden für die Richtung d
TAG = 288                                                            # 5-Minuten-Kerzen je UTC-Tag
ZEITRAUM = {"T": ("2021-08-15", "2023-06-30"), "V1": ("2023-07-01", "2024-06-30"), "V2": ("2024-07-01", "2025-03-31")}
ENDE_V1 = int(np.searchsorted(D.RASTER.values, np.datetime64("2024-07-01")))    # erste Kerze der Schlussprüfung
GRUND = {1: "einstieg", 2: "signalwechsel", 3: "stop", 4: "ziel", 5: "nachzug", 6: "wiedereinstieg", 7: "filter"}


def tf_kerzen(h: np.ndarray, l: np.ndarray, c: np.ndarray, m: int):
    """Hoch, Tief, Schluss der TF-Kerzen aus je m 5-Minuten-Kerzen, ab Kerze 0 (Präzisierung 1)."""
    n = len(c) // m
    return h[:n * m].reshape(n, m).max(1), l[:n * m].reshape(n, m).min(1), c[m - 1:n * m:m].copy()


def richtung_stunden(c: np.ndarray) -> np.ndarray:
    """d je Stundenkerze: Vorzeichen von (Schluss − Schluss vor 336 Stunden); davor 0 (Präzisierung 3)."""
    ch = c[11::12]
    d = np.zeros(len(ch), np.int8)
    d[RUECK:] = np.sign(ch[RUECK:] - ch[:-RUECK]).astype(np.int8)
    return d


@njit(cache=True)
def struktur(H, L, C, k):
    """Zustand nach dem Schluss jeder TF-Kerze t (Präzisierung 4).

    sh/sl: gültiges, ungebrochenes Zwischenhoch/-tief (nan: keines oder gebrochen); shn/sln: bei t neu bekannt gewordenes
    Niveau (sonst nan); br: Bruch bei t (+1 oben, −1 unten, 0 keiner); s: Strukturrichtung nach t.
    """
    n = len(C)
    sh, sl = np.full(n, np.nan), np.full(n, np.nan)
    shn, sln = np.full(n, np.nan), np.full(n, np.nan)
    br, s = np.zeros(n, np.int8), np.zeros(n, np.int8)
    ah, al, hb, lb, richt = np.nan, np.nan, True, True, 0
    for t in range(n):
        j = t - k                                                   # Kerze, die mit dem Schluss von t bekannt werden kann
        if j - k >= 0:
            ok = True
            for q in range(j - k, j):
                if not H[j] > H[q]:
                    ok = False
                    break
            if ok:
                for q in range(j + 1, j + k + 1):
                    if not H[j] >= H[q]:
                        ok = False
                        break
            if ok:
                ah, hb = H[j], False
                shn[t] = ah
            ok = True
            for q in range(j - k, j):
                if not L[j] < L[q]:
                    ok = False
                    break
            if ok:
                for q in range(j + 1, j + k + 1):
                    if not L[j] <= L[q]:
                        ok = False
                        break
            if ok:
                al, lb = L[j], False
                sln[t] = al
        if (not hb) and C[t] > ah:
            br[t], hb, richt = 1, True, 1
        elif (not lb) and C[t] < al:
            br[t], lb, richt = -1, True, -1
        if not hb:
            sh[t] = ah
        if not lb:
            sl[t] = al
        s[t] = richt
    return sh, sl, shn, sln, br, s


@njit(cache=True)
def lauf(o, h, l, c, gueltig, fs, slip_coin, dh, m, k, sh, sl, shn, sln, br, s, art, i_ende, brut, nord, slipb, markt, zahl, orders):
    """Ein Coin, eine Regel. Schreibt Tagesreihen je Richtung (Zeile 0 long, 1 short): brut (Kurs und Funding, in Anteilen
    des Einsatzes), nord (Orders), slipb (Slippage in bewegtem Markt, bp). markt: Kerzen mit Position je Tag.
    zahl: [Einstiege, Signalwechsel-Schließungen, Stops, Ziele, Nachzug-Stops, Wiedereinstiege, Filter-Ausstiege].
    orders: [n, 4] = Ausführungskerze, Seite (+1 Kauf, −1 Verkauf), Anlass, Kurs. Gibt die Zahl der Orders zurück."""
    pos, e, ref, stop, best, sperre, a = 0, 0.0, 0.0, np.nan, 0.0, 0, 0
    zu, auf, g_zu, g_auf, n_stop = False, 0, 0, 0, np.nan           # bei der letzten Prüfung beschlossen, auszuführen zur nächsten Eröffnung
    w, no = (2 * k + 1) * m, 0
    for j in range(i_ende):
        tg = j // TAG
        ri = 0 if pos > 0 else 1
        if pos != 0 and j > a:                                      # Funding der Kerzen a+1 bis b (Präzisierung 9)
            brut[ri, tg] -= pos * fs[j]
        if zu or auf != 0:
            sb = max(slip_coin, 500.0 * (h[j - 1] - l[j - 1]) / c[j - 1])    # 5 % der Spanne der Kerze davor, in bp
            if zu:
                brut[ri, tg] += pos * (o[j] - ref) / e
                nord[ri, tg] += 1
                slipb[ri, tg] += sb
                zahl[g_zu - 1] += 1
                if no < orders.shape[0]:
                    orders[no, 0], orders[no, 1], orders[no, 2], orders[no, 3] = j, -pos, g_zu, o[j]
                no += 1
                pos = 0
            if auf != 0:
                pos, e, ref, a, stop, best = auf, o[j], o[j], j, n_stop, o[j]
                ri = 0 if pos > 0 else 1
                nord[ri, tg] += 1
                slipb[ri, tg] += sb
                zahl[0 if g_auf == 1 else 5] += 1
                if no < orders.shape[0]:
                    orders[no, 0], orders[no, 1], orders[no, 2], orders[no, 3] = j, pos, g_auf, o[j]
                no += 1
            zu, auf = False, 0
        if pos != 0:                                                # Kursänderung der offenen Position bis zum Schluss von j
            brut[ri, tg] += pos * (c[j] - ref) / e
            ref = c[j]
            markt[tg] += 1
        if j + 1 >= i_ende or not (gueltig[j] and gueltig[j + 1]):  # Prüfung nur ohne Datenlücke (Präzisierung 5)
            continue
        th = j // 12 - 1
        d = dh[th] if th >= 0 else 0
        t = j // m - 1                                              # letzte bekannte TF-Kerze (Präzisierung 2)
        ev = t >= 0 and j % m == 0                                  # sie ist genau bei dieser Prüfung erstmals bekannt
        if sperre != 0 and sperre != d:                             # (a) Pause endet
            sperre = 0
        pause_vorher = sperre != 0
        grund = 0
        if pos != 0 and pos == d:                                   # (b) Stop bzw. Ausstieg
            if art == V1 or art == V2:
                if ev:
                    lvl = shn[t] if pos < 0 else sln[t]
                    if lvl == lvl:
                        if pos < 0 and lvl < stop and lvl > c[j]:
                            stop = lvl
                        if pos > 0 and lvl > stop and lvl < c[j]:
                            stop = lvl
                if (pos < 0 and c[j] > stop) or (pos > 0 and c[j] < stop):
                    grund = 3
            elif art == K1 or art == K2:
                r = (c[j] / e - 1.0) * pos
                if art == K2 and r >= 0.15:
                    grund = 4
                elif r <= -0.05:
                    grund = 3
            elif art == K3:
                best = max(best, c[j]) if pos > 0 else min(best, c[j])
                if (c[j] / best - 1.0) * pos <= -0.05:
                    grund = 5
            if grund != 0:
                sperre = pos
        wieder = False
        if art == B0:                                               # (c) Sollrichtung
            soll = d
        elif art == V3:
            soll = d if (d != 0 and t >= 0 and s[t] == d) else 0
        else:
            soll = d
            if d != 0 and sperre == d:
                soll = 0
                if art == V2 and pause_vorher and ev and br[t] == d:
                    sperre, soll, wieder = 0, d, True
        if soll != pos:                                             # (d) schließen und gegebenenfalls neu eröffnen
            if pos != 0:
                zu = True
                g_zu = grund if grund != 0 else (7 if (art == V3 and d == pos) else 2)
            if soll != 0:
                auf, g_auf, n_stop = soll, (6 if wieder else 1), np.nan
                if art == V1 or art == V2:                          # Stop-Niveau (Präzisierung 7)
                    i0 = max(0, j - w + 1)
                    if soll < 0:
                        lvl = sh[t] if t >= 0 else np.nan
                        n_stop = lvl if (lvl == lvl and lvl > c[j]) else np.max(h[i0:j + 1])
                    else:
                        lvl = sl[t] if t >= 0 else np.nan
                        n_stop = lvl if (lvl == lvl and lvl < c[j]) else np.min(l[i0:j + 1])
    return no


# --------------------------------------------------------------------------------------------- Rechnung und Auswertung
def coin_daten(j: int, i_ende: int):
    """Nur die Kerzen vor i_ende: Was danach liegt, wird gar nicht erst geladen (Schlussprüfung bleibt zu)."""
    o, h, l, c = (np.array(D.laden(x)[j, :i_ende], np.float64) for x in "ohlc")
    fc = np.array(D.laden("fcum")[j, :i_ende], np.float64)
    return o, h, l, c, np.array(D.laden("gueltig")[j, :i_ende]), np.diff(fc, prepend=0.0), float(np.load(D.SPEICHER / "slip_bp.npy")[j])


def regeln():
    """Alle 16 Regeln: Basis, drei Vergleichsregeln, zwölf Kandidaten. (Kennung, Art, TF, k)"""
    out = [("B0", B0, 1, 3), ("K1", K1, 1, 3), ("K2", K2, 1, 3), ("K3", K3, 1, 3)]
    return out + [(f"{v}_{tf}h_k{k}", ART[v], tf, k) for v in ("V1", "V2", "V3") for tf, k in EINSTELLUNGEN]


def rechne(i_ende: int, nur=None, mit_orders=0):
    """Tagesreihen je Regel und Coin bis Kerze i_ende (ausschließlich). Rückgabe: {Kennung: dict der Felder [Coin, Richtung, Tag]}."""
    ntage = D.N // TAG
    erg = {}
    for ken, art, tf, k in regeln():
        if nur is not None and ken not in nur:
            continue
        erg[ken] = {x: np.zeros((len(D.COINS), 2, ntage)) for x in ("brut", "nord", "slipb")}
        erg[ken].update(markt=np.zeros((len(D.COINS), ntage)), zahl=np.zeros((len(D.COINS), 7)), slip_coin=np.zeros(len(D.COINS)), orders={})
    for ci, coin in enumerate(D.COINS):
        o, h, l, c, g, fs, slip = coin_daten(ci, i_ende)
        dh = richtung_stunden(c)
        st = {}
        for tf, k in EINSTELLUNGEN:
            st[(tf, k)] = struktur(*tf_kerzen(h, l, c, 12 * tf), k)
        for ken, art, tf, k in regeln():
            if ken not in erg:
                continue
            r = erg[ken]
            orders = np.zeros((mit_orders, 4))
            n = lauf(o, h, l, c, g, fs, slip, dh, 12 * tf, k, *st[(tf, k)], art, i_ende, r["brut"][ci], r["nord"][ci], r["slipb"][ci],
                     r["markt"][ci], r["zahl"][ci], orders)
            r["slip_coin"][ci] = slip
            if mit_orders:
                r["orders"][coin] = orders[:min(n, mit_orders)]
    return erg


def netto(r: dict, bewegt=True, rebate=True) -> np.ndarray:
    """Tagesergebnis je Coin und Richtung netto: Kurs und Funding minus Slippage und Gebühr je Order (auf den Einsatz)."""
    slip = r["slipb"] if bewegt else r["nord"] * r["slip_coin"][:, None, None]
    return r["brut"] - (slip + r["nord"] * GEB_BP * ((1 - REBATE) if rebate else 1.0)) / 1e4


def tage(zeitraum: str) -> slice:
    a, b = ZEITRAUM[zeitraum]
    t0 = np.datetime64("2021-07-01")
    return slice(int((np.datetime64(a) - t0) / np.timedelta64(1, "D")), int((np.datetime64(b) - t0) / np.timedelta64(1, "D")) + 1)


def sharpe(x: np.ndarray) -> float:
    sd = x.std(ddof=1)
    return float(x.mean() / sd * np.sqrt(365)) if sd > 0 else 0.0


def einbruch(x: np.ndarray) -> float:
    k = np.concatenate([[0.0], np.cumsum(x)])
    return float(np.max(np.maximum.accumulate(k) - k))


def stichprobe(kand: np.ndarray, basis: np.ndarray, block=20, zuege=5000, start=23) -> float:
    """Anteil der Ziehungen, in denen die Sharpe-Zahl des Kandidaten nicht über der der Basis liegt (Präzisierung 10)."""
    n = len(kand)
    rng = np.random.default_rng(start)
    nb = -(-n // block)
    ohne = 0
    for _ in range(zuege):
        idx = ((rng.integers(0, n, nb)[:, None] + np.arange(block)[None, :]) % n).ravel()[:n]
        if not sharpe(kand[idx]) > sharpe(basis[idx]):
            ohne += 1
    return ohne / zuege


def kennzahlen(r: dict, zr: str) -> dict:
    sl = tage(zr)
    nt = netto(r)[:, :, sl]
    konto = nt.sum(1).mean(0)                                        # Mittel über die zehn Coins (Einsatz 1 × Konto)
    n_tage = konto.size
    jahre = {}
    t0 = np.datetime64("2021-07-01")
    datum = t0 + np.arange(sl.start, sl.stop).astype("timedelta64[D]")
    for jahr in sorted(set(datum.astype("datetime64[Y]").astype(int) + 1970)):
        mask = (datum.astype("datetime64[Y]").astype(int) + 1970) == jahr
        jahre[str(int(jahr))] = round(float(konto[mask].sum() * 100), 2)
    return {"sharpe": round(sharpe(konto), 3), "ertrag_pa_pct": round(float(konto.mean() * 365 * 100), 2),
            "summe_pct": round(float(konto.sum() * 100), 2), "einbruch_pct": round(einbruch(konto) * 100, 2),
            "orders_je_tag": round(float(r["nord"][:, :, sl].sum() / n_tage), 2),
            "umsatz_je_tag_x_konto": round(float(r["nord"][:, :, sl].sum() / n_tage / len(D.COINS)), 3),
            "zeit_im_markt_pct": round(float(r["markt"][:, sl].sum() / (n_tage * TAG * len(D.COINS)) * 100), 1),
            "long_pct": round(float(nt[:, 0].sum(1).mean() * 100), 2), "short_pct": round(float(nt[:, 1].sum(1).mean() * 100), 2),
            "ruhige_kosten": {"sharpe": round(sharpe(netto(r, bewegt=False)[:, :, sl].sum(1).mean(0)), 3),
                              "summe_pct": round(float(netto(r, bewegt=False)[:, :, sl].sum() / len(D.COINS) * 100), 2)},
            "ohne_rebate": {"sharpe": round(sharpe(netto(r, rebate=False)[:, :, sl].sum(1).mean(0)), 3),
                            "summe_pct": round(float(netto(r, rebate=False)[:, :, sl].sum() / len(D.COINS) * 100), 2)},
            "je_jahr_pct": jahre}, konto


def nachbarn(ken: str) -> list:
    v, tf, k = ken.split("_")
    tf, k = int(tf[:-1]), int(k[1:])
    return [f"{v}_{a}h_k{b}" for a, b in EINSTELLUNGEN if (a == tf) != (b == k)]


GRENZE = {"T": 0.025, "V1": 0.16}                                   # höchstens dieser Anteil der Ziehungen ohne Vorteil


def urteil(reihen: dict) -> dict:
    """Die vier Bedingungen für die zwölf Kandidaten, gerechnet auf den ungerundeten Tagesreihen des Kontos.
    reihen: {(Kennung, Zeitraum): Tagesreihe}; verlangt B0 und alle Kandidaten in T und V1."""
    for x in reihen.values():
        if not np.isfinite(x).all():
            raise SystemExit("Tagesreihe mit ungültigen Werten: kein Urteil.")
    kand = sorted({k for k, _ in reihen if k[0] == "V"})
    sh = {key: sharpe(x) for key, x in reihen.items()}
    ueber = lambda k: all(sh[(k, zr)] > sh[("B0", zr)] for zr in ("T", "V1"))
    out = {}
    for ken in kand:
        u = {}
        for zr in ("T", "V1"):
            p = stichprobe(reihen[(ken, zr)], reihen[("B0", zr)])
            u[zr] = {"differenz": sh[(ken, zr)] - sh[("B0", zr)], "anteil_ohne_vorteil": p,
                     "bedingung": bool(sh[(ken, zr)] > sh[("B0", zr)] and p <= GRENZE[zr])}
        u["urteil"] = {"1_T": u["T"]["bedingung"], "2_V1": u["V1"]["bedingung"],
                       "3_netto_positiv": bool(reihen[(ken, "T")].sum() > 0 and reihen[(ken, "V1")].sum() > 0),
                       "4_nachbar": bool(any(ueber(x) for x in nachbarn(ken)))}
        u["urteil"]["besteht_T_und_V1"] = all(u["urteil"].values())
        out[ken] = u
    return out


ERGEBNIS = F / "ergebnisse/e23_marktstruktur.json"


def hauptlauf():
    if ERGEBNIS.exists() and "V2" in json.loads(ERGEBNIS.read_text()):
        raise SystemExit("Die Schlussprüfung ist schon geöffnet; das Ergebnis wird nicht überschrieben.")
    erg = rechne(ENDE_V1)
    out = {"experiment": "E23", "festlegung": "forschung/protokoll.md Abschnitt 43", "gerechnet_bis": "2024-06-30 (V2 nicht gerechnet)",
           "kosten": "Taker 8 bp je Order, 85 % Rebate; Slippage: größerer Wert aus gemessener Yubit-Slippage und 5 % der Spanne der Kerze davor",
           "regeln": {}}
    reihen = {}
    for ken, r in erg.items():
        e = {"titel": TITEL[ken[:2]], "zaehler_ganzer_lauf_ab_2021_07": dict(zip(("einstiege", "signalwechsel", "stops", "ziele", "nachzug", "wiedereinstiege", "filter_aus"),
                                                             (int(x) for x in r["zahl"].sum(0))))}
        for zr in ("T", "V1"):
            e[zr], reihen[(ken, zr)] = kennzahlen(r, zr)
        out["regeln"][ken] = e
    for ken, u in urteil(reihen).items():
        e = out["regeln"][ken]
        for zr in ("T", "V1"):
            e[zr].update(sharpe_minus_basis=round(u[zr]["differenz"], 3), anteil_ohne_vorteil=round(u[zr]["anteil_ohne_vorteil"], 4),
                         bedingung=u[zr]["bedingung"])
        e["urteil"] = u["urteil"]
    best = [k for k, e in out["regeln"].items() if e.get("urteil", {}).get("besteht_T_und_V1")]
    out["besteher_T_und_V1"] = best
    out["einstufung"] = "A (verworfen), V2 bleibt geschlossen" if not best else "offen: Schlussprüfung V2 für " + ", ".join(best)
    ERGEBNIS.parent.mkdir(exist_ok=True)
    ERGEBNIS.write_text(json.dumps(out, ensure_ascii=False, indent=1) + "\n")
    np.savez_compressed(ERGEBNIS.with_name("e23_marktstruktur_tage.npz"), **{f"{k}_{z}": v for (k, z), v in reihen.items()})
    return out


def schlusspruefung(kennungen: list):
    alt = json.loads(ERGEBNIS.read_text())
    if "V2" in alt:
        raise SystemExit("Die Schlussprüfung wurde schon geöffnet (einmalig).")
    if sorted(kennungen) != sorted(alt["besteher_T_und_V1"]) or not kennungen:
        raise SystemExit("V2 wird nur für genau die Besteher von T und V1 geöffnet: " + ", ".join(alt["besteher_T_und_V1"]))
    alt["V2"] = {"stand": "geöffnet, Rechnung läuft"}                # Sperre steht, bevor die erste Zahl aus V2 entsteht
    ERGEBNIS.write_text(json.dumps(alt, ensure_ascii=False, indent=1) + "\n")
    erg = rechne(D.N, nur=set(kennungen) | {"B0"})
    v2, reihe = {}, {}
    for ken, r in erg.items():
        v2[ken], reihe[ken] = kennzahlen(r, "V2")
        if not np.isfinite(reihe[ken]).all():
            raise SystemExit("Tagesreihe mit ungültigen Werten: kein Urteil.")
    for ken in kennungen:
        v2[ken]["besteht"] = bool(sharpe(reihe[ken]) > sharpe(reihe["B0"]) and reihe[ken].sum() > 0)
    alt["V2"] = v2
    alt["gerechnet_bis"] = "2025-03-31 (V2 einmal geöffnet für: " + ", ".join(kennungen) + ")"
    alt["einstufung"] = "C (Kandidat für Test 4): " + ", ".join(k for k in kennungen if v2[k]["besteht"]) if any(v2[k]["besteht"] for k in kennungen) \
        else "B (interessant): besteht T und V1, nicht V2"
    ERGEBNIS.write_text(json.dumps(alt, ensure_ascii=False, indent=1) + "\n")
    np.savez_compressed(ERGEBNIS.with_name("e23_marktstruktur_tage_v2.npz"), **reihe)
    return alt


def orders_csv(coin: str, variante: str, tf: int, k: int, ziel: str, i_ende: int = ENDE_V1):
    ken = variante if variante[0] in "BK" else f"{variante}_{tf}h_k{k}"
    r = rechne(i_ende, nur={ken}, mit_orders=200000)[ken]
    o = r["orders"][coin]
    with open(ziel, "w") as f:
        f.write("kerze,zeit,seite,anlass,kurs\n")
        for z in o:
            f.write(f"{int(z[0])},{D.RASTER[int(z[0])]},{'kauf' if z[1] > 0 else 'verkauf'},{GRUND[int(z[2])]},{z[3]:.10g}\n")
    ci = D.COINS.index(coin)
    print(f"{ken} {coin}: {len(o)} Orders; Summe netto bis Kerze {i_ende}: {netto(r)[ci].sum():.8f}")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--orders":
        orders_csv(sys.argv[2], sys.argv[3], int(sys.argv[4]), int(sys.argv[5]), sys.argv[6])
    elif len(sys.argv) > 1 and sys.argv[1] == "--v2":
        print(json.dumps(schlusspruefung(sys.argv[2:])["V2"], ensure_ascii=False, indent=1))
    else:
        a = hauptlauf()
        print("Besteher T und V1:", a["besteher_T_und_V1"] or "keiner", "|", a["einstufung"])
