"""E26: die Trendregel auf jedem einzelnen Markt (Vollständigkeit).

Festlegung: forschung/protokoll.md, Abschnitt 49. Nicht-Krypto auf Tageskursen wie Runde 14 (tagestrend.py), jeder Markt
einmal über seine ganze Historie; Krypto-Kontrakte einzeln aus der Tagesrechnung von E25 (nur T und V1).

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
RUNDE14 = ["EWJ", "EWY", "XAU", "XAG", "XPT", "XPD", "COPPER", "CL", "BZ", "NATGAS", "TBT"]          # ohne SPY, QQQ, IWM (stehen bei den Labor-ETFs)
NAMEN = {"XAU": "Gold", "XAG": "Silber", "XPT": "Platin", "XPD": "Palladium", "COPPER": "Kupfer", "CL": "WTI-Öl", "BZ": "Brent-Öl",
         "NATGAS": "Erdgas", "TBT": "TBT (US-Anleihen short)", "EWJ": "EWJ (Japan)", "EWY": "EWY (Korea)"}
PERIODEN = {"P0": (None, "2021-08-14"), "T": ("2021-08-15", "2023-06-30"), "V1": ("2023-07-01", "2024-06-30"),
            "V2": ("2024-07-01", "2025-03-31"), "P3": ("2025-04-01", None)}
MIN_TAGE, MIN_PERIODEN = 60, 4
ERGEBNIS = F / "ergebnisse/e26_jeder_markt.json"


# ------------------------------------------------------------------------------------------------------- Daten
def labor_etf(name: str) -> pd.DataFrame:
    """Tageskurse eines ETFs aus dem Labor (yfinance, 2016 bis 10/2026)."""
    pfad = sorted(glob.glob(str(LABOR / f"buy_and_hold__{name}__1D__*/artifacts/ohlcv_{name}.csv")))[0]
    d = pd.read_csv(pfad, parse_dates=["trade_date"]).set_index("trade_date")[["open", "close"]].astype(float)
    return d[~d.index.duplicated()].sort_index()


def kosten() -> dict:
    """Slippage je Order als Anteil: gemessene Yubit-Spanne (mindestens 0,5 bp); ETFs ohne Kontrakt: Median der ETF-Kontrakte."""
    k14 = json.loads((ROOT / "reports/runde14_kosten.json").read_text())
    stich = X25.spannen()
    bp = {n: k14[n]["spanne_bp"] for n in k14 if not n.startswith("_")}
    bp["DIA"], bp["XLE"] = stich["DIAUSDT"], stich["XLEUSDT"]
    etf_median = float(np.median([bp[n] for n in ("SPY", "QQQ", "IWM", "EWJ", "EWY", "DIA", "XLE")]))
    for n in ("EEM", "EFA", "XLF", "XLK", "XLV"):
        bp[n] = etf_median
    info = json.loads((ROOT / "reports/runde17_aktien.json").read_text())
    gem = pd.Series({k: v["spanne_bp"] for k, v in info.items() if v["ok"]}, dtype=float)
    for k, v in gem.fillna(gem.median()).items():
        bp["AKTIE:" + k] = v
    return {n: max(0.00005, v / 1e4) for n, v in bp.items()}


def maerkte() -> dict:
    """{Kennung: (Gruppe, Anzeigename, Tageskurse)} für alle Nicht-Krypto-Märkte."""
    out = {n: ("labor_etf", n, labor_etf(n)) for n in LABOR_ETF}
    for n in RUNDE14:
        out[n] = ("runde14", NAMEN[n], pd.read_parquet(ROOT / f"data/candles/tradfi_1d/{n}.parquet")[["open", "close"]])
    info = json.loads((ROOT / "reports/runde17_aktien.json").read_text())
    for k in sorted(k for k, v in info.items() if v["ok"]):
        out["AKTIE:" + k] = ("aktie", k, pd.read_parquet(ROOT / f"data/candles/aktien_1d/{k}.parquet")[["open", "close"]])
    return out


# ---------------------------------------------------------------------------------------------------- Rechnung
def markt_reihe(d: pd.DataFrame, slip: float, stress: bool = False) -> pd.Series:
    """Tagesergebnis netto mit Rebate, Einsatz 1, über die ganze Historie des Marktes (Kalendertage)."""
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
    """Kennzahlen eines Marktes. Ein Zeitraum zählt nur mit mindestens 60 Börsentagen."""
    je = {}
    for p in perioden:
        tage = periode(pd.Series(0, index=handelstage), p)
        je[p] = round(float(periode(netto, p).sum() * 100), 2) if len(tage) >= MIN_TAGE else None
    gueltig = [p for p in perioden if je[p] is not None]
    x = pd.concat([periode(netto, p) for p in gueltig]) if gueltig else netto.iloc[:0]
    s = pd.concat([periode(stress, p) for p in gueltig]) if gueltig else stress.iloc[:0]
    xt = x[x.index.isin(handelstage)].to_numpy()
    t = float(xt.mean() / xt.std(ddof=1) * np.sqrt(len(xt))) if len(xt) > 2 and xt.std(ddof=1) > 0 else 0.0
    z = {"je_zeitraum_pct": je, "zeitraeume": len(gueltig), "summe_pct": round(float(x.sum() * 100), 2), "stress_pct": round(float(s.sum() * 100), 2),
         "sharpe": round(E.sharpe(x.to_numpy()), 3) if len(x) > 2 else 0.0, "t_wert": round(t, 2),
         "alle_zeitraeume_positiv": bool(gueltig and all(je[p] > 0 for p in gueltig))}
    z["auffaellig"] = bool(z["alle_zeitraeume_positiv"] and len(gueltig) >= MIN_PERIODEN and s.sum() > 0 and t >= 2.0)
    return z


def nicht_krypto() -> tuple:
    slip = kosten()
    zeilen, reihen = {}, {}
    for ken, (gruppe, name, d) in maerkte().items():
        if len(d) < 30:
            zeilen[ken] = {"gruppe": gruppe, "name": name, "ohne_daten": True}
            continue
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
        korb = df.mean(axis=1, skipna=True).fillna(0.0)
        out[g] = {"maerkte": int(df.shape[1]), "je_zeitraum_pct": {p: round(float(periode(korb, p).sum() * 100), 2) for p in PERIODEN},
                  "summe_pct": round(float(korb.sum() * 100), 2), "sharpe": round(E.sharpe(korb.to_numpy()), 3)}
    return out


def krypto() -> dict:
    """Jeder Krypto-Kontrakt einzeln (Tagesregel von E25, Einsatz 1 ab dem Tag, an dem er dabei ist), nur T und V1."""
    inv = X25.symbole()
    syms = inv[~inv["tradfi"] & (inv["erster_tag"] <= X25.V1_ENDE)]["symbol"].tolist()
    kal, o, c, qv, fr = X25.laden(syms, X25.V1_ENDE)
    slip = X25.spannen()
    sb = np.array([slip[s] for s in syms])
    d, ab = X25.richtung(c), X25.dabei_ab(c)
    be, ne = X25.einzelreihen(o, c, fr, d, ab)
    netto = be - ne * (sb[:, None] + X25.GEB_BP) / 1e4
    stress = be - ne * (2 * sb[:, None] + X25.GEB_BP) / 1e4
    out = {}
    for i, s in enumerate(syms):
        je, n_tage = {}, {}
        for zr in ("T", "V1"):
            sl = E.tage(zr)
            aktiv = np.isfinite(c[i, sl]) & (np.arange(sl.start, sl.stop) >= ab[i])
            n_tage[zr] = int(aktiv.sum())
            je[zr] = round(float(netto[i, sl].sum() * 100), 2) if aktiv.sum() >= MIN_TAGE else None
        gueltig = [zr for zr in ("T", "V1") if je[zr] is not None]
        if not gueltig:
            continue
        x = np.concatenate([netto[i, E.tage(zr)][np.arange(E.tage(zr).start, E.tage(zr).stop) >= ab[i]] for zr in gueltig])
        st = sum(float(stress[i, E.tage(zr)].sum()) for zr in gueltig)
        t = float(x.mean() / x.std(ddof=1) * np.sqrt(len(x))) if len(x) > 2 and x.std(ddof=1) > 0 else 0.0
        out[s] = {"je_zeitraum_pct": je, "summe_pct": round(float(x.sum() * 100), 2), "stress_pct": round(st * 100, 2), "t_wert": round(t, 2),
                  "beide_positiv": bool(len(gueltig) == 2 and je["T"] > 0 and je["V1"] > 0),
                  "auffaellig": bool(len(gueltig) == 2 and je["T"] > 0 and je["V1"] > 0 and t >= 2.0)}
    return out


def hauptlauf():
    zeilen, reihen = nicht_krypto()
    kr = krypto()
    mit = [z for z in zeilen.values() if not z.get("ohne_daten")]
    vier = [z for z in mit if z["zeitraeume"] >= MIN_PERIODEN]
    out = {"experiment": "E26", "festlegung": "forschung/protokoll.md Abschnitt 49", "nicht_krypto": zeilen, "gruppen": gruppen_koerbe(zeilen, reihen),
           "krypto": kr,
           "zaehlung": {"nicht_krypto_maerkte": len(zeilen), "mit_daten": len(mit), "mit_mindestens_vier_zeitraeumen": len(vier),
                        "davon_alle_zeitraeume_positiv": sum(z["alle_zeitraeume_positiv"] for z in vier),
                        "auffaellig": sorted(k for k, z in zeilen.items() if z.get("auffaellig")),
                        "summe_positiv": sum(z["summe_pct"] > 0 for z in mit),
                        "krypto_kontrakte": len(kr), "krypto_mit_T_und_V1": sum(z["je_zeitraum_pct"]["T"] is not None and z["je_zeitraum_pct"]["V1"] is not None for z in kr.values()),
                        "krypto_beide_positiv": sum(z["beide_positiv"] for z in kr.values()),
                        "krypto_auffaellig": sorted(k for k, z in kr.items() if z["auffaellig"])}}
    ERGEBNIS.write_text(json.dumps(out, ensure_ascii=False, indent=1) + "\n")
    with open(ERGEBNIS.with_suffix(".csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["markt", "gruppe", "von", "bis", "P0", "T", "V1", "V2", "P3", "summe_pct", "stress_pct", "sharpe", "t_wert", "auffaellig"])
        for k, z in zeilen.items():
            if not z.get("ohne_daten"):
                w.writerow([z["name"], z["gruppe"], z["von"], z["bis"]] + [z["je_zeitraum_pct"][p] for p in PERIODEN] + [z["summe_pct"], z["stress_pct"], z["sharpe"], z["t_wert"], z["auffaellig"]])
        for k, z in kr.items():
            w.writerow([k, "krypto", "", "", "", z["je_zeitraum_pct"]["T"], z["je_zeitraum_pct"]["V1"], "", "", z["summe_pct"], z["stress_pct"], "", z["t_wert"], z["auffaellig"]])
    return out


if __name__ == "__main__":
    e = hauptlauf()
    print(json.dumps(e["zaehlung"], ensure_ascii=False))
