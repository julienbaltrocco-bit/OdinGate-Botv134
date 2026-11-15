"""QR (b): unabhaengige Minimal-Rechnung des 14-Tage-Trends. Benutzt KEIN Modul aus src/hybrid.

Aufruf (aus swing-hybrid/):  .venv/bin/python -I -B <dieses Skript> <ausgabe.json> <tagesreihe.csv>

Regel (aus der Beschreibung des Betreibers, nicht aus dem Code abgeschrieben):
- Stundenschluss C[H] = Schluss der letzten 5-Minuten-Kerze der Stunde H (Binance-USD-M-Futures, data/candles/5m).
- Signal s[H] = Vorzeichen(C[H] / C[H - 336 h] - 1), Kalenderstunden.
- Wirksam ab der Folgestunde: gehandelt wird zur Eroeffnung der Stunde H+1 (Open der ersten 5-Minuten-Kerze).
- Feste Stueckzahl je Position: q = s * S / Open, S = 1/10 des Startkapitals; unveraendert bis zum Richtungswechsel.
- Kosten je Order auf das gehandelte Volumen: Taker 0,08 % * (1 - 85 % Rebate) + Slippage je Coin
  (2 x mittlere halbe Yubit-Spanne aus data/processed/yubit_spannen_stichprobe.csv, mindestens 0,5 bp).
- Funding: Satz * Positionswert zum Funding-Zeitpunkt (Long zahlt positives Funding), aus data/candles/funding.
- Tagesergebnis = Aenderung von (Kasse + Position * letzter Stundenschluss des UTC-Tages) - Gebuehren + Funding.
- Kennzahlen: Ertrag/Jahr = Tagesmittel * 365; Sharpe = Mittel / Standardabweichung * sqrt(365);
  Einbruch = groesster Rueckgang von 1 + kumuliertem Tagesergebnis relativ zum Hoechststand.
"""
import json
import sys

import numpy as np
import pandas as pd

AUS_JSON, AUS_CSV = sys.argv[1], sys.argv[2]
COINS = ["BTC", "ETH", "SOL", "XRP", "DOT", "DOGE", "ADA", "LINK", "AVAX", "LTC"]
START, D1_ENDE, SPLIT, ENDE = (pd.Timestamp(x) for x in ("2021-08-15", "2023-07-01", "2025-04-01", "2026-10-24"))
L = 336
TAKER, REBATE = 0.0008, 0.85
S = 1.0 / len(COINS)

sp = pd.read_csv("data/processed/yubit_spannen_stichprobe.csv")
sp["halb"] = (sp["brief"] - sp["geld"]) / (sp["brief"] + sp["geld"])
halb = sp.groupby("symbol")["halb"].mean()
SLIP = {c: max(0.00005, 2.0 * float(halb[c + "USDT"])) for c in COINS}

stunden = pd.date_range(START - pd.Timedelta(hours=L + 48), ENDE, freq="1h", inclusive="left")
C, O, FU, luecken = {}, {}, {}, {}
for c in COINS:
    k = pd.read_parquet(f"data/candles/5m/{c}USDT.parquet")
    k.index = pd.DatetimeIndex(k.index).astype("datetime64[ns]")
    k = k[~k.index.duplicated()].sort_index()
    raster = pd.date_range(k.index[0], k.index[-1], freq="5min")
    luecken[c] = {"erste": str(k.index[0]), "letzte": str(k.index[-1]), "fehlende_5m": int(len(raster.difference(k.index))),
                  "doppelte": int(pd.read_parquet(f"data/candles/5m/{c}USDT.parquet").index.duplicated().sum())}
    cl = k["close"].resample("1h").last()
    op = k["open"].resample("1h").first()
    luecken[c]["leere_stunden"] = int(cl.reindex(stunden).isna().sum())
    C[c] = cl.reindex(stunden).ffill()
    O[c] = op.reindex(stunden).fillna(C[c].shift(1))
    f = pd.read_parquet(f"data/candles/funding/{c}USDT.parquet")["rate"]
    f.index = pd.DatetimeIndex(f.index).astype("datetime64[ns]").floor("1h")
    f = f[~f.index.duplicated()]
    FU[c] = f.reindex(stunden).fillna(0.0)
C, O, FU = pd.DataFrame(C), pd.DataFrame(O), pd.DataFrame(FU)

sig = np.sign(C / C.shift(L) - 1.0)                 # bekannt am Ende der Stunde H
ziel = sig.shift(1)                                 # gilt fuer die Stunde H+1
handel = stunden[(stunden >= START) & (stunden < ENDE)]
tage = pd.date_range(START, ENDE, freq="1D", inclusive="left")

rows = {}
stat = {}
for c in COINS:
    cc, oo, ff, zz = (x[c].reindex(handel).to_numpy() for x in (C, O, FU, ziel))
    slip, fee = SLIP[c], TAKER * (1.0 - REBATE)
    pos = 0.0; halte = 0.0; kasse = 0.0; geb_voll = 0.0; fund = 0.0; umsatz = 0.0; orders = 0
    eq = np.empty(len(handel)); eq_ohne = np.empty(len(handel)); eq_brutto = np.empty(len(handel))
    for i in range(len(handel)):
        if ff[i] != 0.0 and pos != 0.0:             # Funding auf die Position, die in die Stunde hineingeht
            fund -= pos * oo[i] * ff[i]
        z = zz[i]
        if z != halte:                              # Richtungswechsel (oder erster Einstieg / Signal 0)
            neu = z * S / oo[i]
            dq = neu - pos
            if dq != 0.0:
                px = oo[i] * (1.0 + np.sign(dq) * slip)
                kasse -= dq * px
                geb_voll += abs(dq) * px * TAKER
                umsatz += abs(dq) * px
                orders += 1
            pos, halte = neu, z
        wert = kasse + pos * cc[i]
        eq_brutto[i] = wert + fund
        eq_ohne[i] = wert + fund - geb_voll
        eq[i] = wert + fund - geb_voll * (1.0 - REBATE)
    rows[c] = pd.Series(eq, index=handel)
    stat[c] = {"orders": orders, "umsatz": umsatz, "gebuehr_voll": geb_voll, "funding": fund,
               "netto_mit": float(eq[-1]), "netto_ohne": float(eq_ohne[-1]), "brutto_inkl_slip_funding": float(eq_brutto[-1]),
               "eq_ohne": pd.Series(eq_ohne, index=handel), "eq_brutto": pd.Series(eq_brutto, index=handel)}

EQ = pd.DataFrame(rows)
eq_h = EQ.sum(axis=1)
eq_ohne_h = sum(stat[c]["eq_ohne"] for c in COINS)
eq_brutto_h = sum(stat[c]["eq_brutto"] for c in COINS)


def tagesreihe(e):
    t = e.groupby(e.index.normalize()).last()
    return t.diff().fillna(t.iloc[0])


tg, tg_ohne, tg_brutto = tagesreihe(eq_h), tagesreihe(eq_ohne_h), tagesreihe(eq_brutto_h)
pd.DataFrame({"netto_mit_rebate": tg, "netto_ohne_rebate": tg_ohne, "vor_gebuehr": tg_brutto}).to_csv(AUS_CSV, float_format="%.10f")


def kenn(x, stunden_eq=None):
    k = 1.0 + x.cumsum()
    out = {"tage": int(len(x)), "N": float(x.sum()), "jahr": float(x.mean() * 365),
           "sharpe": float(x.mean() / x.std() * np.sqrt(365)), "dd_tag": float(((k.cummax() - k) / k.cummax()).max())}
    if stunden_eq is not None:
        kh = 1.0 + stunden_eq
        sp_ = np.maximum.accumulate(np.maximum(kh.to_numpy(), 1.0))
        out["dd_stunde"] = float(((sp_ - kh.to_numpy()) / sp_).max())
    return out


FEN = {"D1": (START, D1_ENDE), "D2": (D1_ENDE, SPLIT), "Entwicklung": (START, SPLIT), "Pruefung": (SPLIT, ENDE),
       "Gesamt": (START, ENDE)}
out = {"slip_bp": {c: SLIP[c] * 1e4 for c in COINS}, "luecken": luecken, "fenster": {}}
for name, (a, b) in FEN.items():
    x = tg[(tg.index >= a) & (tg.index < b)]
    eh = eq_h[(eq_h.index >= a) & (eq_h.index < b)]
    basis = eq_h[eq_h.index < a].iloc[-1] if (eq_h.index < a).any() else 0.0
    e = kenn(x, eh - basis)
    xo = tg_ohne[(tg_ohne.index >= a) & (tg_ohne.index < b)]
    xb = tg_brutto[(tg_brutto.index >= a) & (tg_brutto.index < b)]
    e["N_ohne_rebate"] = float(xo.sum()); e["sharpe_ohne_rebate"] = float(xo.mean() / xo.std() * np.sqrt(365))
    e["N_vor_gebuehr"] = float(xb.sum())
    out["fenster"][name] = e
out["je_coin"] = {c: {k: v for k, v in stat[c].items() if not isinstance(v, pd.Series)} for c in COINS}
out["orders"] = int(sum(stat[c]["orders"] for c in COINS))
out["umsatz_je_tag"] = float(sum(stat[c]["umsatz"] for c in COINS) / len(tage))
out["signal_null_coinstunden"] = int((sig.reindex(handel) == 0).sum().sum())

# ---- Korrelation der Tagesrenditen der zehn Coins ----
tc = C.groupby(C.index.normalize()).last()
def mittlere_korrelation(r):
    k = r.corr().to_numpy()
    return float(k[np.triu_indices_from(k, 1)].mean())
kor = {}
for art, r in (("einfach", tc.pct_change()), ("log", np.log(tc).diff())):
    for name, (a, b) in {"Gesamt": (START, ENDE), "Entwicklung": (START, SPLIT), "seit_04_2025": (SPLIT, ENDE)}.items():
        kor[f"{art}_{name}"] = mittlere_korrelation(r[(r.index >= a) & (r.index < b)])
rh = C.pct_change()
for name, (a, b) in {"Gesamt": (START, ENDE), "seit_04_2025": (SPLIT, ENDE)}.items():
    kor[f"stunde_{name}"] = mittlere_korrelation(rh[(rh.index >= a) & (rh.index < b)])
out["korrelation_tagesrenditen"] = kor

# ---- Anteil der Stunden mit allen zehn Signalen in derselben Richtung ----
z = ziel.reindex(handel)
gl = {}
for name, (a, b) in FEN.items():
    zz = z[(z.index >= a) & (z.index < b)]
    alle_long = (zz == 1).all(axis=1); alle_short = (zz == -1).all(axis=1)
    netto = zz.sum(axis=1)
    gl[name] = {"alle_gleich": float((alle_long | alle_short).mean()), "alle_long": float(alle_long.mean()),
                "alle_short": float(alle_short.mean()), "mind_8_gleich": float((netto.abs() >= 6).mean()),
                "mittel_abs_netto": float(netto.abs().mean() / len(COINS))}
out["gleiche_richtung"] = gl

json.dump(out, open(AUS_JSON, "w"), indent=1, default=float)
print(pd.DataFrame(out["fenster"]).T.round(4).to_string())
print("Orders:", out["orders"], "Umsatz/Tag:", round(out["umsatz_je_tag"], 4), "Signal==0 Coin-Stunden:", out["signal_null_coinstunden"])
print("Luecken:", json.dumps(luecken))
print("Korrelation:", {k: round(v, 4) for k, v in kor.items()})
print("Gleiche Richtung:"); print(pd.DataFrame(gl).T.round(4).to_string())
print("je Coin:"); print(pd.DataFrame(out["je_coin"]).T.round(4).to_string())
