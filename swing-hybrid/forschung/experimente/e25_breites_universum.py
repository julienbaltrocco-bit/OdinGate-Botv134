"""E25: die Trendregel über alle Kontrakte (H24 bis H26).

Festlegung: forschung/protokoll.md, Abschnitt 47. Tagesregel auf Binance-Tageskursen der Kontrakte, die Yubit führt.
Teil 1 (Krypto breit, mit Urteil) lädt nichts nach dem 30.06.2024. Teil 2 (neue Kontrakte, nur Bericht) lädt nur
Kontrakte mit erstem Handelstag ab 01.07.2024.

  .venv/bin/python -I forschung/experimente/e25_breites_universum.py
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from numba import njit

F = Path(__file__).resolve().parents[1]
ROOT = F.parent
sys.path.insert(0, str(F))
from experimente import e23_marktstruktur as E  # noqa: E402
from fabrik import daten as D  # noqa: E402

START = pd.Timestamp("2021-07-01")
V1_ENDE, DATEN_ENDE, NEU_AB = pd.Timestamp("2024-06-30"), pd.Timestamp("2026-10-31"), pd.Timestamp("2024-07-01")
GEB_BP = 8.0 * (1 - 0.85)                                            # Gebühr je Order mit Rebate
WARTE, RUECK, LIQ_TAGE, GUT_TAGE, LIQ_N = 60, 14, 30, 180, 30
BASIS_SYM = [c + "USDT" for c in D.COINS]
ERGEBNIS = F / "ergebnisse/e25_breites_universum.json"


# ------------------------------------------------------------------------------------------------------- Daten
def symbole():
    """Alle Kontrakte mit Tageskursen: Symbol, erster Handelstag, ob Aktie/Index/Rohstoff (Liste aus Runde 10)."""
    inv = pd.read_csv(ROOT / "data/processed/listings_inventur.csv", parse_dates=["erster_tag"])
    aus = {x.strip() for x in (ROOT / "scripts/listings_ausschluss.txt").read_text().splitlines() if x.strip() and not x.startswith("#")}
    # Die Liste aus Runde 10 ging nach Namen und enthält zwei Krypto-Kontrakte (BTCUSDT als damaliges Gegenstück, MDTUSDT wegen
    # Namensgleichheit mit einer Aktie). Aktien-Kontrakte gibt es erst seit 2026: Einträge mit erstem Handelstag vor 2025 sind Krypto.
    inv["tradfi"] = inv["symbol"].isin(aus) & (inv["erster_tag"] >= pd.Timestamp("2025-01-01"))
    return inv[["symbol", "erster_tag", "tradfi"]].sort_values("symbol").reset_index(drop=True)


def spannen() -> dict:
    """Slippage je Order in bp: Median der gemessenen Yubit-Spanne je Symbol, mindestens 0,5 bp."""
    s = pd.read_csv(ROOT / "data/processed/yubit_spannen_stichprobe.csv")
    bp = (s["brief"] - s["geld"]) / ((s["brief"] + s["geld"]) / 2) * 1e4
    return bp.groupby(s["symbol"]).median().clip(lower=0.5).to_dict()


def laden(syms: list, bis: pd.Timestamp):
    """Felder [Symbol, Tag] auf dem Kalender START … bis: Eröffnung, Schluss, Umsatz, Funding-Summe; vor dem ersten Tag nan.
    Zeilen nach `bis` werden sofort verworfen."""
    kal = pd.date_range(START, bis, freq="D")
    o, c, qv, fr = (np.full((len(syms), len(kal)), np.nan) for _ in range(4))
    for i, s in enumerate(syms):
        d = pd.read_parquet(ROOT / f"data/candles/1d/{s}.parquet")
        d = d[d.index <= bis].reindex(kal)
        o[i], c[i], qv[i] = d["open"].to_numpy(), d["close"].to_numpy(), d["quote_volume"].to_numpy()
        f = pd.read_parquet(ROOT / f"data/candles/funding_1d/{s}.parquet")["rate"]
        fr[i] = f[f.index <= bis].reindex(kal).to_numpy()
    return kal, o, c, qv, fr


# ------------------------------------------------------------------------------------------------------ Regeln
def richtung(c: np.ndarray) -> np.ndarray:
    """d[i, t] = Vorzeichen von (Schluss t − Schluss t−14), bekannt am Schluss von t; ohne beide Kurse 0."""
    d = np.zeros(c.shape, np.int8)
    diff = c[:, RUECK:] - c[:, :-RUECK]
    d[:, RUECK:] = np.where(np.isfinite(diff), np.sign(diff), 0).astype(np.int8)
    return d


def dabei_ab(c: np.ndarray) -> np.ndarray:
    """Index des ersten Tages, an dem ein Kontrakt dabei ist: 60 Tage nach seinem ersten Handelstag; Kontrakte, deren
    Daten am ersten Kalendertag beginnen (schon vorher gelistet), von Anfang an."""
    erster = np.array([int(np.argmax(np.isfinite(x))) if np.isfinite(x).any() else c.shape[1] for x in c])
    return np.where(erster == 0, 0, erster + WARTE)


@njit(cache=True)
def tag_lauf(o, c, f, ziel, brut, nord):
    """Ein Kontrakt. ziel[t]: Sollrichtung ab der Eröffnung des Tages t. Schreibt je Tag das Ergebnis vor Orderkosten (Kurs und
    Funding, in Anteilen des Einsatzes beim Einstieg) und die Zahl der Orders."""
    pos, e, ref = 0, 0.0, 0.0
    for t in range(len(c)):
        if not (c[t] == c[t] and o[t] == o[t]):                     # vor dem ersten Handelstag
            continue
        z = ziel[t]
        if z != pos:
            if pos != 0:
                brut[t] += pos * (o[t] - ref) / e
                nord[t] += 1
                pos = 0
            if z != 0:
                pos, e, ref = z, o[t], o[t]
                nord[t] += 1
        if pos != 0:
            brut[t] += pos * (c[t] - ref) / e
            ref = c[t]
            if f[t] == f[t]:
                brut[t] -= pos * f[t]                               # eine am Tag t gehaltene Position zahlt die Funding-Summe des Tages


def monatsanfaenge(kal: pd.DatetimeIndex) -> list:
    """(Index des ersten Tages, Index nach dem letzten Tag) je Kalendermonat."""
    m = kal.to_period("M")
    grenzen = [0] + [i for i in range(1, len(kal)) if m[i] != m[i - 1]] + [len(kal)]
    return list(zip(grenzen[:-1], grenzen[1:]))


def einzelreihen(o, c, fr, d, ab):
    """Jeder Kontrakt für sich, sobald er dabei ist (Grundlage für die Auswahl GUT/SCHLECHT): brut, nord je Tag."""
    n, T_ = c.shape
    brut, nord = np.zeros((n, T_)), np.zeros((n, T_))
    for i in range(n):
        ziel = np.zeros(T_, np.int8)
        ziel[1:] = d[i, :-1]
        ziel[:ab[i]] = 0
        tag_lauf(o[i], c[i], fr[i], ziel, brut[i], nord[i])
    return brut, nord


def mitglieder(kal, qv, ab, netto_einzel, basis_idx):
    """Mitglieder je Korb und Monat, bestimmt nur aus Daten bis zum letzten Tag des Vormonats. Rückgabe: {Korb: bool[Symbol, Tag]}."""
    n, T_ = qv.shape
    m = {k: np.zeros((n, T_), bool) for k in ("BASIS", "ALLE", "LIQ30", "KLEIN", "GUT", "SCHLECHT")}
    for t0, t1 in monatsanfaenge(kal):
        alle = np.nonzero(ab <= t0)[0]                               # am ersten Tag des Monats dabei
        m["ALLE"][alle, t0:t1] = True
        m["BASIS"][[i for i in basis_idx if ab[i] <= t0], t0:t1] = True
        if t0 >= LIQ_TAGE and len(alle):
            umsatz = np.nanmean(qv[alle, t0 - LIQ_TAGE:t0], axis=1)
            rang = alle[np.argsort(-umsatz, kind="stable")]
            m["LIQ30"][rang[:LIQ_N], t0:t1] = True
            m["KLEIN"][rang[LIQ_N:], t0:t1] = True
        lang = alle[ab[alle] + GUT_TAGE <= t0]                       # mindestens 180 Tage dabei
        k = len(lang) // 3
        if k > 0:
            leistung = netto_einzel[lang, t0 - GUT_TAGE:t0].sum(axis=1)
            rang = lang[np.argsort(-leistung, kind="stable")]
            m["GUT"][rang[:k], t0:t1] = True
            m["SCHLECHT"][rang[-k:], t0:t1] = True
    return m


def korb(o, c, fr, d, ab, mit, slip_bp, stress=False):
    """Tagesreihe eines Korbs (Einsatz 1, gleich verteilt auf die Mitglieder des Monats). Rückgabe: netto, vor Kosten, Orders, Mitgliederzahl."""
    n, T_ = c.shape
    anzahl = mit.sum(axis=0)
    netto, vor, orders = np.zeros(T_), np.zeros(T_), np.zeros(T_)
    f = 2.0 if stress else 1.0
    for i in np.nonzero(mit.any(axis=1))[0]:
        ziel = np.zeros(T_, np.int8)
        ziel[1:] = d[i, :-1]
        ziel[~mit[i]] = 0
        ziel[:ab[i]] = 0
        b, no = np.zeros(T_), np.zeros(T_)
        tag_lauf(o[i], c[i], fr[i], ziel, b, no)
        gew = np.where(anzahl > 0, 1.0 / np.maximum(anzahl, 1), 0.0)
        # Orders eines ausscheidenden Mitglieds fallen am ersten Tag ohne Mitgliedschaft an: Gewicht des Vormonats
        gew_order = np.where(mit[i], gew, np.concatenate([[0.0], gew[:-1]]))
        vor += b * gew_order
        netto += (b - no * (f * slip_bp[i] + GEB_BP) / 1e4) * gew_order
        orders += no
    return netto, vor, orders, anzahl


# -------------------------------------------------------------------------------------------------- Auswertung
def zahlen(x: np.ndarray) -> dict:
    return {"summe_pct": round(float(x.sum() * 100), 2), "sharpe": round(E.sharpe(x), 3), "einbruch_pct": round(E.einbruch(x) * 100, 2), "tage": int(len(x))}


def teil1():
    inv = symbole()
    krypto = inv[~inv["tradfi"] & (inv["erster_tag"] <= V1_ENDE)]["symbol"].tolist()
    kal, o, c, qv, fr = laden(krypto, V1_ENDE)
    slip = spannen()
    slip_bp = np.array([slip[s] for s in krypto])
    d, ab = richtung(c), dabei_ab(c)
    brut_e, nord_e = einzelreihen(o, c, fr, d, ab)
    netto_e = brut_e - nord_e * (slip_bp[:, None] + GEB_BP) / 1e4
    mit = mitglieder(kal, qv, ab, netto_e, [krypto.index(s) for s in BASIS_SYM])
    reihen, out = {}, {"koerbe": {}}
    for name, m in mit.items():
        netto, vor, orders, anzahl = korb(o, c, fr, d, ab, m, slip_bp)
        stress = korb(o, c, fr, d, ab, m, slip_bp, stress=True)[0]
        e = {}
        for zr in ("T", "V1"):
            sl = E.tage(zr)
            reihen[(name, zr)], reihen[(name + "_stress", zr)] = netto[sl], stress[sl]
            e[zr] = {**zahlen(netto[sl]), "vor_kosten_pct": round(float(vor[sl].sum() * 100), 2), "stress_pct": round(float(stress[sl].sum() * 100), 2),
                     "mitglieder_mittel": round(float(anzahl[sl].mean()), 1), "orders_je_tag": round(float(orders[sl].sum() / (sl.stop - sl.start)), 2),
                     "erster_tag_mit_mitgliedern": str(kal[sl][np.argmax(anzahl[sl] > 0)].date()) if (anzahl[sl] > 0).any() else None}
        out["koerbe"][name] = e
    out["urteil"] = urteil1(reihen, {k: v for k, v in mit.items()}, kal)
    for name in ("ALLE", "LIQ30", "KLEIN", "GUT", "SCHLECHT"):      # Mischung je zur Hälfte mit BASIS (nur Bericht)
        for zr in ("T", "V1"):
            mix = 0.5 * reihen[("BASIS", zr)] + 0.5 * reihen[(name, zr)]
            out["koerbe"][name][zr]["mischung_sharpe"] = round(E.sharpe(mix), 3)
            out["koerbe"][name][zr]["mischung_einbruch_pct"] = round(E.einbruch(mix) * 100, 2)
            out["koerbe"][name][zr]["gleichlauf_mit_basis"] = round(float(np.corrcoef(reihen[("BASIS", zr)], reihen[(name, zr)])[0, 1]), 3)
    b0 = np.load(F / "ergebnisse/e23_marktstruktur_tage.npz")        # Einordnung: Tagesregel gegen Stundenregel auf den zehn Coins
    out["tagesregel_gegen_stundenregel"] = {zr: {"sharpe_tag": round(E.sharpe(reihen[("BASIS", zr)]), 3), "sharpe_stunde": round(E.sharpe(b0[f"B0_{zr}"]), 3),
                                                 "summe_tag_pct": round(float(reihen[("BASIS", zr)].sum() * 100), 2), "summe_stunde_pct": round(float(b0[f"B0_{zr}"].sum() * 100), 2),
                                                 "gleichlauf": round(float(np.corrcoef(reihen[("BASIS", zr)], b0[f"B0_{zr}"])[0, 1]), 3)} for zr in ("T", "V1")}
    out["kontrakte"] = len(krypto)
    return out, reihen


def urteil1(reihen: dict, mit: dict, kal) -> dict:
    """Bedingungen 1 bis 5. Für GUT (und SCHLECHT) beginnt der Vergleich in T mit dem ersten Tag, an dem GUT Mitglieder hat;
    BASIS wird auf dieselben Tage beschnitten."""
    for x in reihen.values():
        if not np.isfinite(x).all():
            raise SystemExit("Tagesreihe mit ungültigen Werten: kein Urteil.")
    out = {}
    for name in ("ALLE", "LIQ30", "KLEIN", "GUT"):
        u = {}
        for zr in ("T", "V1"):
            sl = E.tage(zr)
            hat = mit[name][:, sl].any(axis=0)
            a = int(np.argmax(hat)) if hat.any() else len(hat)       # erster Tag mit Mitgliedern
            x, b, s = reihen[(name, zr)][a:], reihen[("BASIS", zr)][a:], reihen[(name + "_stress", zr)][a:]
            p = E.stichprobe(x, b) if len(x) > 40 else 1.0
            u[zr] = {"ab_tag": str(kal[sl][a].date()) if a < len(hat) else None, "sharpe": round(E.sharpe(x), 3), "basis_sharpe": round(E.sharpe(b), 3),
                     "anteil_ohne_vorteil": round(p, 4), "summe_pct": round(float(x.sum() * 100), 2), "basis_summe_pct": round(float(b.sum() * 100), 2),
                     "stress_pct": round(float(s.sum() * 100), 2),
                     "besser": bool(E.sharpe(x) > E.sharpe(b) and p <= E.GRENZE[zr]), "netto_positiv": bool(x.sum() > 0), "stress_positiv": bool(s.sum() > 0)}
            if name == "GUT":
                g = reihen[("SCHLECHT", zr)][a:]
                u[zr]["schlecht_sharpe"] = round(E.sharpe(g), 3)
                u[zr]["ueber_schlecht"] = bool(E.sharpe(x) > E.sharpe(g))
        u["bedingungen"] = {"1_T": u["T"]["besser"], "2_V1": u["V1"]["besser"], "3_netto_positiv": u["T"]["netto_positiv"] and u["V1"]["netto_positiv"],
                            "4_stress_positiv": u["T"]["stress_positiv"] and u["V1"]["stress_positiv"]}
        if name == "GUT":
            u["bedingungen"]["5_ueber_schlecht"] = u["T"]["ueber_schlecht"] and u["V1"]["ueber_schlecht"]
        u["besteht_T_und_V1"] = all(u["bedingungen"].values())
        out[name] = u
    return out


def teil2():
    """Neue Kontrakte (erster Handelstag ab 01.07.2024), nur Bericht, bis 31.10.2026."""
    inv = symbole()
    neu = inv[inv["erster_tag"] >= NEU_AB]
    slip = spannen()
    out = {}
    for gruppe, tradfi in (("krypto_neu", False), ("aktien_index_rohstoff", True)):
        syms = neu[neu["tradfi"] == tradfi]["symbol"].tolist()
        kal, o, c, qv, fr = laden(syms, DATEN_ENDE)
        slip_bp = np.array([slip[s] for s in syms])
        d, ab = richtung(c), dabei_ab(c)
        mit = np.zeros(c.shape, bool)
        for t0, t1 in monatsanfaenge(kal):
            mit[np.nonzero(ab <= t0)[0], t0:t1] = True
        netto, vor, orders, anzahl = korb(o, c, fr, d, ab, mit, slip_bp)
        stress = korb(o, c, fr, d, ab, mit, slip_bp, stress=True)[0]
        a = int(np.argmax(anzahl > 0)) if (anzahl > 0).any() else len(kal)
        brut_e, nord_e = einzelreihen(o, c, fr, d, ab)
        einzeln = (brut_e - nord_e * (slip_bp[:, None] + GEB_BP) / 1e4).sum(axis=1)
        dabei = np.array([ab[i] < len(kal) for i in range(len(syms))])
        quartale = pd.Series(netto[a:], index=kal[a:]).groupby(kal[a:].to_period("Q")).sum()
        out[gruppe] = {"kontrakte": len(syms), "kontrakte_mit_ergebnis": int(dabei.sum()), "von": str(kal[a].date()) if a < len(kal) else None, "bis": str(kal[-1].date()),
                       "kontrakt_tage": int(mit.sum()), **zahlen(netto[a:]), "vor_kosten_pct": round(float(vor[a:].sum() * 100), 2),
                       "stress_pct": round(float(stress[a:].sum() * 100), 2), "mitglieder_am_ende": int(anzahl[-1]),
                       "orders_je_tag": round(float(orders[a:].sum() / max(1, len(kal) - a)), 2),
                       "anteil_kontrakte_im_plus_pct": round(float((einzeln[dabei] > 0).mean() * 100), 1) if dabei.any() else None,
                       "je_quartal_pct": {str(k): round(float(v * 100), 2) for k, v in quartale.items()}}
    return out


def hauptlauf():
    t1, reihen = teil1()
    out = {"experiment": "E25", "festlegung": "forschung/protokoll.md Abschnitt 47", "teil_1": t1, "teil_2": teil2()}
    best = [k for k, u in t1["urteil"].items() if u["besteht_T_und_V1"]]
    out["besteher_T_und_V1"] = best
    out["einstufung_teil_1"] = "offen: V2 für " + ", ".join(best) if best else "A (verworfen)"
    ERGEBNIS.write_text(json.dumps(out, ensure_ascii=False, indent=1) + "\n")
    np.savez_compressed(ERGEBNIS.with_name("e25_breites_universum_tage.npz"), **{f"{k}_{z}": v for (k, z), v in reihen.items()})
    return out


if __name__ == "__main__":
    e = hauptlauf()
    print(e["einstufung_teil_1"])
