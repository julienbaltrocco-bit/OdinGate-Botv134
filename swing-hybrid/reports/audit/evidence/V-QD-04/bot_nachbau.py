"""V-QD-04: Nachbau der Entscheidungslogik von vorwaertstest/bot.py (schritt) als Schleife, fuer Test 1 und Test 2.

Unabhaengig von src/hybrid. Bildet zusaetzlich zu unabhaengig.py ab:
- das Tagesverlust-Limit des Bots genau wie konfiguriert (tagesverlust_limit 1.0 = 100 % des Startkapitals an einem
  UTC-Tag, gemessen ohne Rebate, geprueft je Durchlauf; danach alles schliessen und bis Tagesende flach),
- Stop 5 % / Gewinnziel 15 % von Test 2 (Pruefung je Durchlauf am Mittelkurs gegen den Einstiegs-Fuellkurs, danach
  Sperre der Richtung bis das Signal dreht),
- den Takt: einmal je Stunde um hh:05 (Entwurf) oder alle 5 Minuten (tatsaechlicher Betrieb laut Betreiber).
Schreibt nur in das per Argument uebergebene Verzeichnis.
"""
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
from numba import njit

ROOT = Path("/home/user/OdinGate-Botv134/swing-hybrid")
AUS = Path(sys.argv[1])
A = ["BTC", "ETH", "SOL", "XRP", "DOT", "DOGE", "ADA", "LINK", "AVAX", "LTC"]
START, ENDE, SPLIT = "2021-08-15", "2026-10-24", "2025-04-01"
TAKER, REBATE, L = 0.0008, 0.85, 336
t0 = time.time()
idx = pd.date_range(START, ENDE, freq="5min", inclusive="left")
T, N = len(idx), len(A)
i_split = int(idx.searchsorted(pd.Timestamp(SPLIT)))


def lesen(ordner, coin):
    d = pd.concat([pd.read_parquet(ROOT / "data/candles" / o / f"{coin}USDT.parquet") for o in (ordner + "_vor", ordner)])
    d.index = d.index.astype("datetime64[ns]")
    return d[~d.index.duplicated()].sort_index()


sp = pd.read_csv(ROOT / "data/processed/yubit_spannen_stichprobe.csv")
sp["halb"] = (sp["brief"] - sp["geld"]) / (sp["brief"] + sp["geld"])
halb = sp.groupby("symbol")["halb"].mean()
SLIP = np.array([max(0.00005, 2.0 * float(halb[c + "USDT"])) for c in A])
O = np.empty((N, T)); C = np.empty((N, T)); F = np.zeros((N, T)); W = np.zeros((N, T))
for j, coin in enumerate(A):
    d = lesen("5m", coin)
    k = d.reindex(idx)
    fehlt = k["close"].isna()
    cl = k["close"].ffill().bfill()
    O[j] = k["open"].where(~fehlt, cl).to_numpy(); C[j] = cl.to_numpy()
    h = d["close"].resample("1h").last()
    sig = np.sign(h - h.shift(freq=pd.Timedelta(hours=L)).reindex(h.index)).fillna(0.0)
    sig.index = sig.index + pd.Timedelta(hours=1)
    W[j] = sig.reindex(idx.union(sig.index)).ffill().reindex(idx).fillna(0.0).to_numpy()
    fr = lesen("funding", coin)["rate"]
    fr.index = fr.index.floor("5min")
    F[j] = fr[~fr.index.duplicated()].reindex(idx).fillna(0.0).to_numpy()


@njit(cache=False)
def sim(O, C, W, F, slip, s0, e0, S, tp, sl, limit, takt, versatz, taker, rebate):
    N = O.shape[0]; n = e0 - s0
    u = np.zeros(N); ein = np.zeros(N); sperre = np.zeros(N); kasse = np.zeros(N)
    tv = 0.0; fu = 0.0
    mit = np.zeros(n); ohne = np.zeros(n)
    tag = -1; tag_start = 0.0; gesperrt_tag = -2; sperrtage = 0; ausstiege = 0
    for i in range(n):
        t = s0 + i
        for j in range(N):
            if F[j, t] != 0.0 and u[j] != 0.0:
                fu -= u[j] * O[j, t] * F[j, t]
        if (t - versatz) % takt == 0:                       # ein Durchlauf des Bots
            brutto = 0.0
            for j in range(N):
                brutto += kasse[j] + u[j] * O[j, t]
            v = brutto - taker * tv + fu                   # netto ohne Rebate, wie bot.py:193
            d_ = t // 288
            if d_ != tag:
                tag = d_; tag_start = v
            if gesperrt_tag != d_ and v - tag_start <= -limit:
                gesperrt_tag = d_; sperrtage += 1
            gesperrt = gesperrt_tag == d_
            for j in range(N):
                mid = O[j, t]; d = W[j, t]
                ziel = 0.0 if gesperrt else d
                ist = 1.0 if u[j] > 0 else (-1.0 if u[j] < 0 else 0.0)
                if tp > 0.0 or sl > 0.0:
                    if sperre[j] != 0.0 and sperre[j] != d:
                        sperre[j] = 0.0
                    if ist != 0.0 and ist == d and ein[j] > 0.0:
                        r = (mid / ein[j] - 1.0) * ist
                        if (tp > 0.0 and r >= tp) or (sl > 0.0 and r <= -sl):
                            sperre[j] = ist; ausstiege += 1
                    if d != 0.0 and sperre[j] == d:
                        ziel = 0.0
                if ziel == ist:
                    continue
                if ist != 0.0:
                    px = mid * (1.0 - ist * slip[j])
                    kasse[j] += u[j] * px; tv += abs(u[j]) * px; u[j] = 0.0
                if ziel != 0.0:
                    q = ziel * S / mid
                    px = mid * (1.0 + ziel * slip[j])
                    kasse[j] -= q * px; tv += abs(q) * px; u[j] = q; ein[j] = px
        brutto = 0.0
        for j in range(N):
            brutto += kasse[j] + u[j] * C[j, t]
        ohne[i] = brutto - taker * tv + fu
        mit[i] = brutto - taker * (1.0 - rebate) * tv + fu
    return mit, ohne, sperrtage, ausstiege


def einbruch_rel(eq):
    konto = 1.0 + eq
    spitze = np.maximum.accumulate(np.maximum(konto, 1.0))
    return float(((spitze - konto) / spitze).max())


def lauf(s0, e0, hebel, tp, sl, limit, takt):
    return sim(O, C, W, F, SLIP, s0, e0, hebel / N, tp, sl, limit, takt, 1 if takt == 12 else 0, TAKER, REBATE)


out = {}
print("=== 1. Durchgehender Lauf ab 2021-08-15, Hebel 1, ohne Limit, Takt stuendlich (Abgleich mit dem Protokoll, Runde 24)")
for nm, tp, sl in (("Test 1 (nur Umkehr)", 0.0, 0.0), ("Test 2 (Stop 5 % / Ziel 15 %)", 0.15, 0.05)):
    mit, ohne, st, au = lauf(0, T, 1.0, tp, sl, 9.0, 12)
    tag = pd.Series(mit, index=idx).resample("1D").last()
    tg = tag.diff().fillna(tag.iloc[0])
    for fn, a, b in (("Entwicklung", 0, i_split), ("Pruefzeitraum", i_split, T)):
        basis = mit[a - 1] if a > 0 else 0.0
        seg = mit[a:b] - basis
        x = tg[(tg.index >= idx[a].normalize()) & (tg.index <= idx[b - 1].normalize())]
        e = {"N_jahr": float(seg[-1] / ((b - a) / 288) * 365), "sharpe": float(x.mean() / x.std() * np.sqrt(365)), "einbruch_rel": einbruch_rel(seg),
             "rueckgang_abs": float((np.maximum.accumulate(np.maximum(seg, 0.0)) - seg).max())}
        out[f"hebel1_{nm}_{fn}"] = e
        print(f"{nm:30s} {fn:14s} Ertrag/Jahr {e['N_jahr']:+.3f}  Sharpe {e['sharpe']:.2f}  Einbruch rel. {e['einbruch_rel']:.3f}  groesster Rueckgang (Startkapital) {e['rueckgang_abs']:.3f}")
print("   Protokoll Runde 24 (Entwicklung): Kandidat Sharpe 0,95 / 59 % / Einbruch 24,6 %; sl5_tp15 Sharpe 1,13 / 33 % / Einbruch 14,6 %")

print("\n=== 2. Neustart mit Hebel 3 (wie config_lauf.json / config_lauf_tpsl.json), Start an jedem 7. Tag und an jedem Tag")
print("    Kontotief = tiefster Stand netto mit Rebate (5-Minuten-Schlusskurse) in den 365 Tagen nach dem Start, in Einheiten des Startkapitals")
sp_ = pd.Timestamp(SPLIT)
tab = []
for nm, tp, sl in (("Test 1", 0.0, 0.0), ("Test 2", 0.15, 0.05)):
    for lim, ln in ((9.0, "Limit aus"), (1.0, "Limit 1,0 wie konfiguriert")):
        for takt, tn in ((12, "stuendlich"), (1, "alle 5 min")):
            for schritt in (7, 1):
                starts = np.arange(0, T - 288 * 30, 288 * schritt)
                tief = np.empty(len(starts)); ende = np.empty(len(starts)); sperr = np.zeros(len(starts)); voll = np.zeros(len(starts), bool)
                for i, s0 in enumerate(starts):
                    e0 = min(T, s0 + 288 * 365)
                    mit, ohne, st, au = lauf(int(s0), int(e0), 3.0, tp, sl, lim, takt)
                    tief[i] = mit.min(); ende[i] = mit[-1]; sperr[i] = st; voll[i] = (e0 - s0) == 288 * 365
                z = pd.DataFrame({"tief": tief, "ende": ende, "sperrtage": sperr, "voll": voll}, index=idx[starts])
                pz = z[z.index >= sp_]
                r = {"test": nm, "limit": ln, "takt": tn, "raster_tage": schritt, "starts": len(z),
                     **{f"le{int(g * 100)}": float((z["tief"] <= -g).mean()) for g in (0.5, 0.75, 1.0)},
                     **{f"pruef_le{int(g * 100)}": float((pz["tief"] <= -g).mean()) for g in (0.5, 0.75, 1.0)},
                     "median_tief": float(z["tief"].median()), "schlechtestes_tief": float(z["tief"].min()),
                     "median_ende_voll": float(z.loc[z["voll"], "ende"].median()), "starts_mit_sperrtag": int((z["sperrtage"] > 0).sum())}
                tab.append(r)
                if nm == "Test 2" and lim == 1.0 and takt == 1 and schritt == 1:
                    z.round(4).to_csv(AUS / "neustart_hebel3_test2_taeglich.csv")
t = pd.DataFrame(tab)
pd.set_option("display.width", 250, "display.max_columns", 30)
print(t.round(3).to_string(index=False))
out["neustart"] = tab

print("\n=== 3. Einzelne Starttage fuer den Abgleich mit dem Replay des echten Bot-Codes (bot_replay.py), Limit 1,0 wie konfiguriert")
abgleich = []
for tag_, tage_ in (("2025-07-20", 160), ("2026-02-08", 255), ("2024-06-23", 160)):
    s0 = int(idx.searchsorted(pd.Timestamp(tag_))); e0 = s0 + 288 * tage_
    for nm, tp, sl in (("Test 1", 0.0, 0.0), ("Test 2", 0.15, 0.05)):
        for takt in (12, 1):
            mit, ohne, st, au = lauf(s0, e0, 3.0, tp, sl, 1.0, takt)
            marken = mit[np.arange(11, len(mit), 12)]                  # Stand je Stunde (Schluss hh:00-Kerze ~ Durchlauf hh:05)
            unter = np.flatnonzero(mit <= -1.0)
            r = {"start": tag_, "tage": tage_, "test": nm, "takt": "stuendlich hh:05" if takt == 12 else "alle 5 min",
                 "tief_5min": float(mit.min()), "tief_stundenmarken": float(marken.min()), "tief_zeit": str(idx[s0 + int(mit.argmin())]),
                 "erstes_le_minus100": str(idx[s0 + int(unter[0])]) if len(unter) else "", "ende": float(mit[-1]), "sperrtage": int(st), "stop_ziel_ausstiege": int(au)}
            abgleich.append(r)
print(pd.DataFrame(abgleich).round(4).to_string(index=False))
out["abgleich"] = abgleich
json.dump(out, open(AUS / "bot_nachbau.json", "w"), indent=1, default=float)
print(f"\nfertig nach {time.time() - t0:.0f} s")
