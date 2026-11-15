"""QR (c): Erklaerung der Abweichung (a) gegen (b) und Kenngroessen zur Einordnung von "Einsatz 100 %" und "Einbruch".

Unabhaengig von src/hybrid (nur pandas/numpy). Aufruf aus swing-hybrid/:
  .venv/bin/python -I -B <dieses Skript> <a_tagesreihe.csv> <ausgabe.json>

Teil 1: dieselbe Minimal-Rechnung wie b_unabhaengig.py, aber mit der Lueckenbehandlung der Module
        (Signal 0 in Stunden ohne Kerzen UND 336 Stunden danach; Kurs steht in der Luecke still).
Teil 2: tatsaechlicher Einsatz (Summe |Stueck| x Kurs) im Zeitverlauf bei fester Stueckzahl.
Teil 3: Verlustgroessen in Einheiten des Startkapitals (nicht relativ zum gewachsenen Konto): schlechtester Tag,
        schlechteste 7/30 Tage, groesster absoluter Rueckgang; daraus rein rechnerisch die Folge fuer Hebel 3.
"""
import json
import sys

import numpy as np
import pandas as pd

A_CSV, AUS_JSON = sys.argv[1], sys.argv[2]
COINS = ["BTC", "ETH", "SOL", "XRP", "DOT", "DOGE", "ADA", "LINK", "AVAX", "LTC"]
START, D1_ENDE, SPLIT, ENDE = (pd.Timestamp(x) for x in ("2021-08-15", "2023-07-01", "2025-04-01", "2026-10-24"))
L, TAKER, REBATE, S = 336, 0.0008, 0.85, 0.1

sp = pd.read_csv("data/processed/yubit_spannen_stichprobe.csv")
sp["halb"] = (sp["brief"] - sp["geld"]) / (sp["brief"] + sp["geld"])
halb = sp.groupby("symbol")["halb"].mean()
SLIP = {c: max(0.00005, 2.0 * float(halb[c + "USDT"])) for c in COINS}

stunden = pd.date_range(START - pd.Timedelta(hours=L + 48), ENDE, freq="1h", inclusive="left")
Cn, C, O, FU = {}, {}, {}, {}
for c in COINS:
    k = pd.read_parquet(f"data/candles/5m/{c}USDT.parquet")
    k.index = pd.DatetimeIndex(k.index).astype("datetime64[ns]")
    Cn[c] = k["close"].resample("1h").last().reindex(stunden)          # mit NaN in Luecken
    C[c] = Cn[c].ffill()
    O[c] = k["open"].resample("1h").first().reindex(stunden).fillna(C[c].shift(1))
    f = pd.read_parquet(f"data/candles/funding/{c}USDT.parquet")["rate"]
    f.index = pd.DatetimeIndex(f.index).astype("datetime64[ns]").floor("1h")
    FU[c] = f[~f.index.duplicated()].reindex(stunden).fillna(0.0)
Cn, C, O, FU = (pd.DataFrame(x) for x in (Cn, C, O, FU))
handel = stunden[(stunden >= START) & (stunden < ENDE)]


def rechnen(sig):
    ziel = sig.shift(1).reindex(handel)
    eq, ein = {}, {}
    for c in COINS:
        cc, oo, ff, zz = C[c].reindex(handel).to_numpy(), O[c].reindex(handel).to_numpy(), FU[c].reindex(handel).to_numpy(), ziel[c].to_numpy()
        pos = halte = kasse = geb = fund = 0.0
        e = np.empty(len(handel)); x = np.empty(len(handel))
        for i in range(len(handel)):
            if ff[i] != 0.0 and pos != 0.0:
                fund -= pos * oo[i] * ff[i]
            if zz[i] != halte:
                neu = zz[i] * S / oo[i]
                dq = neu - pos
                if dq != 0.0:
                    px = oo[i] * (1.0 + np.sign(dq) * SLIP[c])
                    kasse -= dq * px; geb += abs(dq) * px * TAKER * (1.0 - REBATE)
                pos, halte = neu, zz[i]
            e[i] = kasse + pos * cc[i] + fund - geb
            x[i] = abs(pos) * cc[i]
        eq[c], ein[c] = pd.Series(e, index=handel), pd.Series(x, index=handel)
    return pd.DataFrame(eq), pd.DataFrame(ein)


def tage(e):
    t = e.groupby(e.index.normalize()).last()
    return t.diff().fillna(t.iloc[0])


def kenn(x):
    k = 1.0 + x.cumsum()
    return {"N": float(x.sum()), "jahr": float(x.mean() * 365), "sharpe": float(x.mean() / x.std() * np.sqrt(365)),
            "dd_tag": float(((k.cummax() - k) / k.cummax()).max())}


FEN = {"D1": (START, D1_ENDE), "D2": (D1_ENDE, SPLIT), "Entwicklung": (START, SPLIT), "Pruefung": (SPLIT, ENDE)}
out = {}
# ---- Teil 1 ----
sig_modul = np.sign(Cn / Cn.shift(L) - 1.0).fillna(0.0)
EQm, _ = rechnen(sig_modul)
tm = tage(EQm.sum(axis=1))
a = pd.read_csv(A_CSV, index_col=0, parse_dates=True)["vor_True"]
out["teil1_wie_modul"] = {f: kenn(tm[(tm.index >= v[0]) & (tm.index < v[1])]) for f, v in FEN.items()}
out["teil1_modul_a"] = {f: kenn(a[(a.index >= v[0]) & (a.index < v[1])]) for f, v in FEN.items()}
d = (a - tm)
out["teil1_restabweichung"] = {"summe": float(d.sum()), "max_abs_tag": float(d.abs().max()), "tage_ueber_1e-3": int((d.abs() > 1e-3).sum()),
                               "groesste": {str(t.date()): float(v) for t, v in d[d.abs() > 1e-3].items()}}

# ---- Teil 2 und 3: mit der Minimal-Regel (b) ----
sig_b = np.sign(C / C.shift(L) - 1.0)
EQ, EIN = rechnen(sig_b)
eq = EQ.sum(axis=1)
einsatz = EIN.sum(axis=1)
konto = 1.0 + eq
e2 = {}
for f, (v0, v1) in {**FEN, "Gesamt": (START, ENDE)}.items():
    x = einsatz[(einsatz.index >= v0) & (einsatz.index < v1)]
    e2[f] = {"mittel": float(x.mean()), "median": float(x.median()), "p95": float(x.quantile(0.95)), "max": float(x.max()),
             "max_zeit": str(x.idxmax()), "anteil_ueber_1.5": float((x > 1.5).mean()), "anteil_ueber_2": float((x > 2.0).mean())}
out["teil2_einsatz_in_startkapital"] = e2
mx = einsatz.idxmax()
out["teil2_einsatz_max_je_coin"] = {c: float(EIN.loc[mx, c]) for c in COINS}

tg = tage(eq)
e3 = {}
for f, (v0, v1) in FEN.items():
    x = tg[(tg.index >= v0) & (tg.index < v1)]
    kum = x.cumsum()
    absdd = (kum.cummax().clip(lower=0.0) - kum)
    eh = eq[(eq.index >= v0) & (eq.index < v1)]
    absdd_h = (np.maximum.accumulate(eh.to_numpy()) - eh.to_numpy())
    r7, r30 = x.rolling(7).sum(), x.rolling(30).sum()
    # Start an jedem Tag mit Hebel 3 (3 x dieselbe Tagesreihe, feste Groesse am Startkapital): faellt das Konto je auf <= 0?
    v = x.to_numpy(); n = len(v); ruin3 = 0; halb3 = 0
    kumv = np.concatenate([[0.0], np.cumsum(v)])
    sufmin = np.minimum.accumulate(kumv[::-1])[::-1]            # kleinster kumulierter Stand ab Tag i
    for i in range(n):
        tief = sufmin[i + 1] - kumv[i]
        ruin3 += 3.0 * tief <= -1.0
        halb3 += 3.0 * tief <= -0.5
    e3[f] = {"schlechtester_tag": float(x.min()), "tag": str(x.idxmin().date()), "tage_unter_-10%": int((x < -0.10).sum()),
             "tage_unter_-5%": int((x < -0.05).sum()), "schlechteste_7_tage": float(r7.min()), "bis": str(r7.idxmin().date()),
             "schlechteste_30_tage": float(r30.min()), "bis30": str(r30.idxmin().date()),
             "abs_rueckgang_tag": float(absdd.max()), "abs_rueckgang_tag_tief": str(absdd.idxmax().date()),
             "abs_rueckgang_stunde": float(absdd_h.max()),
             "hebel3_anteil_starttage_konto_null": float(ruin3 / n), "hebel3_anteil_starttage_minus50": float(halb3 / n),
             "tage": n}
out["teil3_verlust_in_startkapital_hebel1"] = e3
# schlechtester Tag je Coin (Entwicklung)
t_coin = EQ.groupby(EQ.index.normalize()).last().diff()
st = pd.Timestamp(e3["Entwicklung"]["tag"])
out["teil3_schlechtester_tag_je_coin"] = {c: float(t_coin.loc[st, c]) for c in COINS}
out["teil3_einsatz_am_vortag"] = float(einsatz[einsatz.index < st].iloc[-1])
out["teil3_konto_am_vortag"] = float(konto[konto.index < st].iloc[-1])
tk = C.groupby(C.index.normalize()).last().pct_change()
out["teil3_kursaenderung_am_tag"] = {c: float(tk.loc[st, c]) for c in COINS}
json.dump(out, open(AUS_JSON, "w"), indent=1, default=float)

print("Teil 1: Minimal-Rechnung mit Lueckenbehandlung der Module / Module (a)")
print(pd.DataFrame(out["teil1_wie_modul"]).T.round(4).to_string()); print(pd.DataFrame(out["teil1_modul_a"]).T.round(4).to_string())
print("Restabweichung:", out["teil1_restabweichung"])
print("Teil 2: Einsatz (Summe |Position| x Kurs) in Vielfachen des Startkapitals bei Hebel 1")
print(pd.DataFrame(e2).T.round(3).to_string()); print("  je Coin am Maximum:", {k: round(v, 3) for k, v in out["teil2_einsatz_max_je_coin"].items()})
print("Teil 3: Verluste in Einheiten des Startkapitals, Hebel 1"); print(pd.DataFrame(e3).T.to_string())
print("  schlechtester Tag je Coin:", {k: round(v, 4) for k, v in out["teil3_schlechtester_tag_je_coin"].items()})
print("  Kursaenderung an dem Tag:", {k: round(v, 4) for k, v in out["teil3_kursaenderung_am_tag"].items()})
print("  Einsatz am Vortag:", round(out["teil3_einsatz_am_vortag"], 3), "Konto (1 + Gewinn) am Vortag:", round(out["teil3_konto_am_vortag"], 3))
