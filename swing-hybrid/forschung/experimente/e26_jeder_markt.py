"""E26: die Trendregel auf jedem einzelnen Markt (Vollständigkeit).

Festlegung: forschung/protokoll.md, Abschnitt 49 mit den Korrekturen nach der Gegenprüfung. Nicht-Krypto auf Tageskursen
wie Runde 14 (tagestrend.py), jeder Markt einmal über seine ganze Historie; Krypto-Kontrakte einzeln aus der Tagesrechnung
von E25 (alte Kontrakte nur T und V1; neue Kontrakte seit ihrer Einführung, nur als Bericht).

  .venv/bin/python -I forschung/experimente/e26_jeder_markt.py
"""
import csv
import glob
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

F = Path(__file__).resolve().parents[1]
ROOT = F.parent
sys.path.insert(0, str(F))
sys.path.insert(0, str(ROOT / "src"))
from experimente import e23_marktstruktur as E  # noqa: E402
from experimente import e25_breites_universum as X25  # noqa: E402
from hybrid import tagestrend as T  # noqa: E402

TAKER, REBATE = 0.0008, 0.85
LABOR = ROOT / "data/raw/labor-daten/trading-labor/trading-labor/runs/aktien-breit-vorwaerts"
LABOR_ETF = ["DIA", "EEM", "EFA", "IWM", "QQQ", "SPY", "XLE", "XLF", "XLK", "XLV"]
ETF_MIT_KONTRAKT = ("SPY", "QQQ", "IWM", "EWJ", "EWY", "XLE")       # ETF-Kontrakte bei Yubit mit gemessener Spanne (Grundlage des Medians)
ETF_OHNE_KONTRAKT = ("DIA", "EEM", "EFA", "XLF", "XLK", "XLV")      # DIAUSDT bei Yubit ist ein Krypto-Token, kein Dow-ETF
RUNDE14 = ["EWJ", "EWY", "XAU", "XAG", "XPT", "XPD", "COPPER", "CL", "BZ", "NATGAS", "TBT"]          # ohne SPY, QQQ, IWM (stehen bei den Labor-ETFs)
KEINE_AKTIEN = {"CL", "BZ"}                                          # in Runde 17 als Aktien geladen (Colgate, Kanzhun); die Yubit-Kontrakte sind WTI und Brent
WTI_AB = pd.Timestamp("2020-04-22")                                  # davor negative Kurse (20./21.04.2020), die ein Kontrakt nicht abbilden kann
ETF_TROTZ_NAME = {"XLEUSDT", "EWZUSDT"}                              # ETF-Kontrakte, die in der Namensliste aus Runde 10 fehlen
NAMEN = {"XAU": "Gold", "XAG": "Silber", "XPT": "Platin", "XPD": "Palladium", "COPPER": "Kupfer", "CL": "WTI-Öl", "BZ": "Brent-Öl",
         "NATGAS": "Erdgas", "TBT": "TBT (US-Anleihen short)", "EWJ": "EWJ (Japan)", "EWY": "EWY (Korea)"}
PERIODEN = {"P0": (None, "2021-08-14"), "T": ("2021-08-15", "2023-06-30"), "V1": ("2023-07-01", "2024-06-30"),
            "V2": ("2024-07-01", "2025-03-31"), "P3": ("2025-04-01", None)}
MIN_TAGE, MIN_PERIODEN = 60, 4
ERGEBNIS = F / "ergebnisse/e26_jeder_markt.json"


# ------------------------------------------------------------------------------------------------------- Daten
def labor_etf(name: str) -> pd.DataFrame:
    """Tageskurse eines ETFs aus dem Labor (yfinance, um Dividenden bereinigt, 2016 bis 10/2026)."""
    pfad = sorted(glob.glob(str(LABOR / f"buy_and_hold__{name}__1D__*/artifacts/ohlcv_{name}.csv")))[0]
    d = pd.read_csv(pfad, parse_dates=["trade_date"]).set_index("trade_date")[["open", "close"]].astype(float)
    return d[~d.index.duplicated()].sort_index()


def aktien_liste() -> list:
    info = json.loads((ROOT / "reports/runde17_aktien.json").read_text())
    return sorted(k for k, v in info.items() if v["ok"] and k not in KEINE_AKTIEN)


def kosten() -> dict:
    """Slippage je Order als Anteil: gemessene Yubit-Spanne (mindestens 0,5 bp); ETFs ohne Kontrakt: Median der sechs ETF-Kontrakte."""
    k14 = json.loads((ROOT / "reports/runde14_kosten.json").read_text())
    bp = {n: k14[n]["spanne_bp"] for n in k14 if not n.startswith("_")}
    bp["XLE"] = X25.spannen()["XLEUSDT"]
    etf_median = float(np.median([bp[n] for n in ETF_MIT_KONTRAKT]))
    for n in ETF_OHNE_KONTRAKT:
        bp[n] = etf_median
    info = json.loads((ROOT / "reports/runde17_aktien.json").read_text())
    gem = pd.Series({k: info[k]["spanne_bp"] for k in aktien_liste()}, dtype=float)
    for k, v in gem.fillna(gem.median()).items():
        bp["AKTIE:" + k] = v
    return {n: max(0.00005, v / 1e4) for n, v in bp.items()}


def maerkte() -> dict:
    """{Kennung: (Gruppe, Anzeigename, Tageskurse)} für alle Nicht-Krypto-Märkte mit Tageskursen der Basiswerte."""
    out = {n: ("labor_etf", n, labor_etf(n)) for n in LABOR_ETF}
    for n in RUNDE14:
        d = pd.read_parquet(ROOT / f"data/candles/tradfi_1d/{n}.parquet")[["open", "close"]]
        out[n] = ("runde14", NAMEN[n], d[d.index >= WTI_AB] if n == "CL" else d)
    for k in aktien_liste():
        out["AKTIE:" + k] = ("aktie", "Aktie " + k, pd.read_parquet(ROOT / f"data/candles/aktien_1d/{k}.parquet")[["open", "close"]])
    for ken, (_, _, d) in out.items():
        if not (d > 0).all().all():
            raise SystemExit(f"{ken}: Kurse, die nicht größer als null sind.")
    return out


# ---------------------------------------------------------------------------------------------------- Rechnung
def markt_reihe(d: pd.DataFrame, slip: float, stress: bool = False) -> pd.Series:
    """Tagesergebnis netto mit Rebate, Einsatz 1, über die ganze Historie des Marktes (Kalendertage). Die Position wird zur
    Eröffnung des letzten Börsentags des Marktes geschlossen (wie tagestrend.py)."""
    kal = pd.date_range(d.index[0], d.index[-1], freq="D")
    f = 2.0 if stress else 1.0
    t = T.lauf_markt(d, kal, 1.0, f * slip, f * TAKER, 0.10 if stress else 0.0)
    return t["brutto"] - (1.0 - REBATE) * t["gebuehr"] + t["funding"]


def periode(x: pd.Series, name: str) -> pd.Series:
    a, b = PERIODEN[name]
    if a is not None:
        x = x[x.index >= a]
    if b is not None:
        x = x[x.index <= b]
    return x


def zeile(netto: pd.Series, stress: pd.Series, handelstage: pd.DatetimeIndex, perioden=tuple(PERIODEN)) -> dict:
    """Kennzahlen eines Marktes. Ein Zeitraum zählt nur mit mindestens 60 Börsentagen; Summe, Stress, Sharpe-Zahl und t-Wert
    gehen nur über gezählte Zeiträume. Entschieden wird auf ungerundeten Werten."""
    roh = {}
    for p in perioden:
        tage = periode(pd.Series(0, index=handelstage), p)
        roh[p] = float(periode(netto, p).sum()) if len(tage) >= MIN_TAGE else None
    gueltig = [p for p in perioden if roh[p] is not None]
    x = pd.concat([periode(netto, p) for p in gueltig]) if gueltig else netto.iloc[:0]
    s = pd.concat([periode(stress, p) for p in gueltig]) if gueltig else stress.iloc[:0]
    xt = x[x.index.isin(handelstage)].to_numpy()
    t = float(xt.mean() / xt.std(ddof=1) * np.sqrt(len(xt))) if len(xt) > 2 and xt.std(ddof=1) > 0 else 0.0
    z = {"je_zeitraum_pct": {p: (None if roh[p] is None else round(roh[p] * 100, 2)) for p in perioden}, "zeitraeume": len(gueltig),
         "summe_pct": round(float(x.sum() * 100), 2), "stress_pct": round(float(s.sum() * 100), 2),
         "sharpe": round(E.sharpe(x.to_numpy()), 3) if len(x) > 2 else 0.0, "t_wert": round(t, 2),
         "groesster_tag_pct": round(float(np.abs(xt).max() * 100), 1) if len(xt) else 0.0,
         "alle_zeitraeume_positiv": bool(gueltig and all(roh[p] > 0 for p in gueltig))}
    z["auffaellig"] = bool(z["alle_zeitraeume_positiv"] and len(gueltig) >= MIN_PERIODEN and s.sum() > 0 and t >= 2.0)
    return z


def nicht_krypto() -> tuple:
    slip = kosten()
    zeilen, reihen = {}, {}
    for ken, (gruppe, name, d) in maerkte().items():
        n, s = markt_reihe(d, slip[ken]), markt_reihe(d, slip[ken], stress=True)
        zeilen[ken] = {"gruppe": gruppe, "name": name, "von": str(d.index[0].date()), "bis": str(d.index[-1].date()),
                       "slippage_bp": round(slip[ken] * 1e4, 2), **zeile(n, s, d.index)}
        reihen[ken] = n
    return zeilen, reihen


def gruppen_koerbe(zeilen: dict, reihen: dict) -> dict:
    """Gleichgewichteter Korb je Gruppe: Mittel der Tagesergebnisse der Märkte, die an dem Tag schon Kurse haben."""
    out = {}
    for g in ("labor_etf", "runde14", "aktie"):
        df = pd.DataFrame({k: reihen[k] for k in reihen if zeilen[k]["gruppe"] == g})
        if df.shape[1] == 0:
            continue
        korb = df.mean(axis=1, skipna=True).fillna(0.0)
        out[g] = {"maerkte": int(df.shape[1]), "je_zeitraum_pct": {p: round(float(periode(korb, p).sum() * 100), 2) for p in PERIODEN},
                  "summe_pct": round(float(korb.sum() * 100), 2), "sharpe": round(E.sharpe(korb.to_numpy()), 3)}
    return out


def _t(x: np.ndarray) -> float:
    return float(x.mean() / x.std(ddof=1) * np.sqrt(len(x))) if len(x) > 2 and x.std(ddof=1) > 0 else 0.0


def krypto() -> dict:
    """Jeder der alten Krypto-Kontrakte einzeln (Tagesregel von E25, Einsatz 1 ab dem Tag, an dem er dabei ist), nur T und V1.
    Dazu der Rest gegen den Korb ALLE: Ein Kontrakt gilt nur dann als eigenständig auffällig, wenn auch sein Ergebnis abzüglich
    des Korbs in T und V1 positiv ist und einen t-Wert von mindestens 2 hat."""
    inv = X25.symbole()
    syms = inv[~inv["tradfi"] & (inv["erster_tag"] <= X25.V1_ENDE)]["symbol"].tolist()
    kal, o, c, qv, fr = X25.laden(syms, X25.V1_ENDE)
    slip = X25.spannen()
    sb = np.array([slip[s] for s in syms])
    d, ab = X25.richtung(c), X25.dabei_ab(c)
    be, ne = X25.einzelreihen(o, c, fr, d, ab)
    netto = be - ne * (sb[:, None] + X25.GEB_BP) / 1e4
    stress = be - ne * (2 * sb[:, None] + X25.GEB_BP) / 1e4          # wie E25: nur die Slippage doppelt, Funding wie gebucht
    alle = X25.korb(o, c, fr, d, ab, X25.grundmenge(kal, qv, ab), sb)[0]
    out = {}
    tag = np.arange(len(kal))
    for i, s in enumerate(syms):
        je, rest_je, masken = {}, {}, {}
        for zr in ("T", "V1"):
            sl = E.tage(zr)
            aktiv = np.isfinite(c[i, sl]) & (tag[sl] >= ab[i])
            masken[zr] = tag[sl] >= ab[i]
            zaehlt = aktiv.sum() >= MIN_TAGE
            je[zr] = float(netto[i, sl].sum()) if zaehlt else None
            rest_je[zr] = float((netto[i, sl] - alle[sl])[masken[zr]].sum()) if zaehlt else None
        gueltig = [zr for zr in ("T", "V1") if je[zr] is not None]
        if not gueltig:
            out[s] = {"zu_kurz": True, "je_zeitraum_pct": {"T": None, "V1": None}}
            continue
        x = np.concatenate([netto[i, E.tage(zr)][masken[zr]] for zr in gueltig])
        r = np.concatenate([(netto[i, E.tage(zr)] - alle[E.tage(zr)])[masken[zr]] for zr in gueltig])
        st = sum(float(stress[i, E.tage(zr)].sum()) for zr in gueltig)
        beide = len(gueltig) == 2 and je["T"] > 0 and je["V1"] > 0
        out[s] = {"zu_kurz": False, "je_zeitraum_pct": {zr: (None if je[zr] is None else round(je[zr] * 100, 2)) for zr in ("T", "V1")},
                  "summe_pct": round(float(x.sum() * 100), 2), "stress_pct": round(st * 100, 2), "t_wert": round(_t(x), 2),
                  "rest_gegen_korb_pct": {zr: (None if rest_je[zr] is None else round(rest_je[zr] * 100, 2)) for zr in ("T", "V1")},
                  "rest_t_wert": round(_t(r), 2), "beide_positiv": bool(beide), "auffaellig": bool(beide and _t(x) >= 2.0),
                  "eigenstaendig_auffaellig": bool(beide and _t(x) >= 2.0 and rest_je["T"] > 0 and rest_je["V1"] > 0 and _t(r) >= 2.0)}
    return out


def neue_kontrakte() -> dict:
    """Nur Bericht: jeder Kontrakt mit erstem Handelstag ab 01.07.2024 für sich, vom ersten Teilnahmetag bis 31.10.2026.
    Zu kurz für eine Einstufung; die Zeilen stehen da, damit kein Paar fehlt."""
    inv = X25.symbole()
    neu = inv[inv["erster_tag"] >= X25.NEU_AB].copy()
    neu.loc[neu["symbol"].isin(ETF_TROTZ_NAME), "tradfi"] = True
    slip = X25.spannen()
    out = {}
    for gruppe, tradfi in (("krypto_neu", False), ("kontrakt_aktie_index_rohstoff", True)):
        syms = neu[neu["tradfi"] == tradfi]["symbol"].tolist()
        kal, o, c, qv, fr = X25.laden(syms, X25.DATEN_ENDE)
        sb = np.array([slip[s] for s in syms])
        d, ab = X25.richtung(c), X25.dabei_ab(c)
        be, ne = X25.einzelreihen(o, c, fr, d, ab)
        netto = be - ne * (sb[:, None] + X25.GEB_BP) / 1e4
        for i, s in enumerate(syms):
            if ab[i] >= len(kal):
                out[s] = {"gruppe": gruppe, "zu_kurz": True, "tage": 0}
                continue
            x = netto[i, ab[i]:][np.isfinite(c[i, ab[i]:])]
            out[s] = {"gruppe": gruppe, "zu_kurz": len(x) < MIN_TAGE, "von": str(kal[ab[i]].date()), "tage": int(len(x)),
                      "summe_pct": round(float(x.sum() * 100), 2), "t_wert": round(_t(x), 2),
                      "groesster_tag_pct": round(float(np.abs(x).max() * 100), 1) if len(x) else 0.0}
    return out


def ohne_kursdaten() -> list:
    """Yubit-Symbole, für die es im Projekt überhaupt keine Kurse gibt."""
    yubit = {x.strip() for x in (ROOT / "data/processed/yubit_symbole.txt").read_text().splitlines() if x.strip()}
    return sorted(yubit - set(X25.symbole()["symbol"]))


def hauptlauf():
    zeilen, reihen = nicht_krypto()
    kr, neu = krypto(), neue_kontrakte()
    vier = [z for z in zeilen.values() if z["zeitraeume"] >= MIN_PERIODEN]
    kr_ok = [z for z in kr.values() if not z["zu_kurz"]]
    kr_beide = [z for z in kr_ok if z["je_zeitraum_pct"]["T"] is not None and z["je_zeitraum_pct"]["V1"] is not None]
    neu_ok = [z for z in neu.values() if not z["zu_kurz"]]
    ohne = ohne_kursdaten()
    out = {"experiment": "E26", "festlegung": "forschung/protokoll.md Abschnitt 49", "nicht_krypto": zeilen, "gruppen": gruppen_koerbe(zeilen, reihen),
           "krypto": kr, "neue_kontrakte_nur_bericht": neu, "ohne_kursdaten": ohne,
           "zaehlung": {"nicht_krypto_maerkte": len(zeilen), "mit_mindestens_vier_zeitraeumen": len(vier),
                        "davon_alle_zeitraeume_positiv": sum(z["alle_zeitraeume_positiv"] for z in vier),
                        "auffaellig": sorted(k for k, z in zeilen.items() if z["auffaellig"]),
                        "summe_positiv": sum(z["summe_pct"] > 0 for z in zeilen.values()),
                        "krypto_kontrakte": len(kr), "krypto_mit_zeile": len(kr_ok), "krypto_mit_T_und_V1": len(kr_beide),
                        "krypto_beide_positiv": sum(z["beide_positiv"] for z in kr_ok),
                        "krypto_auffaellig": sorted(k for k, z in kr.items() if not z["zu_kurz"] and z["auffaellig"]),
                        "krypto_eigenstaendig_auffaellig": sorted(k for k, z in kr.items() if not z["zu_kurz"] and z["eigenstaendig_auffaellig"]),
                        "neue_kontrakte": len(neu), "neue_kontrakte_mit_60_tagen": len(neu_ok),
                        "neue_kontrakte_im_plus": {g: [sum(z["summe_pct"] > 0 for z in neu_ok if z["gruppe"] == g), sum(z["gruppe"] == g for z in neu_ok)]
                                                   for g in ("krypto_neu", "kontrakt_aktie_index_rohstoff")},
                        "yubit_symbole_ohne_kursdaten": len(ohne)}}
    ERGEBNIS.write_text(json.dumps(out, ensure_ascii=False, indent=1) + "\n")
    with open(ERGEBNIS.with_suffix(".csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["markt", "gruppe", "von", "bis", "P0", "T", "V1", "V2", "P3", "summe_pct", "stress_pct", "sharpe", "t_wert", "auffaellig"])
        for k, z in zeilen.items():
            w.writerow([z["name"], z["gruppe"], z["von"], z["bis"]] + [z["je_zeitraum_pct"][p] for p in PERIODEN] + [z["summe_pct"], z["stress_pct"], z["sharpe"], z["t_wert"], z["auffaellig"]])
        for k, z in kr.items():
            if z["zu_kurz"]:
                w.writerow([k, "krypto", "", "", "", "", "", "", "", "", "", "", "", "zu kurz"])
            else:
                w.writerow([k, "krypto", "", "", "", z["je_zeitraum_pct"]["T"], z["je_zeitraum_pct"]["V1"], "", "", z["summe_pct"], z["stress_pct"], "", z["t_wert"], z["auffaellig"]])
        for k, z in neu.items():
            w.writerow([k, z["gruppe"], z.get("von", ""), "2026-10-31", "", "", "", "", "", z.get("summe_pct", ""), "", "", z.get("t_wert", ""), "nur Bericht" if not z["zu_kurz"] else "zu kurz"])
    return out


if __name__ == "__main__":
    e = hauptlauf()
    print(json.dumps(e["zaehlung"], ensure_ascii=False))
