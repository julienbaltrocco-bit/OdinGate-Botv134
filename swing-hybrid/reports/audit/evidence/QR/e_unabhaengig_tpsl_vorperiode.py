"""QR (e): zwei weitere Protokollzahlen mit der unabhaengigen Minimal-Rechnung (kein Modul aus src/hybrid):

1. Runde 24, Variante sl5_tp15 (Stop 5 %, Ziel 15 %): Regel nach dem Protokolltext nachgebaut.
   Pruefung am Stundenschluss, Handel zur naechsten Stunde, danach Pause bis das Signal dreht.
   Zwei Lesarten des "Ergebnis seit Einstieg": (A) gegen den Stundenschluss beim Signal, (B) gegen den Fuellkurs.
2. Runde 4, Vorperiode Gruppe A (01.02.2020-14.08.2021), Slippage pauschal 0,05 %.

Aufruf aus swing-hybrid/:  .venv/bin/python -I -B <dieses Skript> <ausgabe.json>
"""
import json
import sys

import numpy as np
import pandas as pd

AUS_JSON = sys.argv[1]
COINS = ["BTC", "ETH", "SOL", "XRP", "DOT", "DOGE", "ADA", "LINK", "AVAX", "LTC"]
L, TAKER, REBATE = 336, 0.0008, 0.85


def laden(start, ende, ordner):
    stunden = pd.date_range(start - pd.Timedelta(hours=L + 48), ende, freq="1h", inclusive="left")
    Cn, O, FU = {}, {}, {}
    for c in COINS:
        k = pd.concat([pd.read_parquet(f"data/candles/{o}/{c}USDT.parquet") for o in ordner])
        k.index = pd.DatetimeIndex(k.index).astype("datetime64[ns]")
        k = k[~k.index.duplicated()].sort_index()
        Cn[c] = k["close"].resample("1h").last().reindex(stunden)
        O[c] = k["open"].resample("1h").first().reindex(stunden)
        f = pd.concat([pd.read_parquet(f"data/candles/{o.replace('5m', 'funding')}/{c}USDT.parquet") for o in ordner])["rate"]
        f.index = pd.DatetimeIndex(f.index).astype("datetime64[ns]").floor("1h")
        FU[c] = f[~f.index.duplicated()].sort_index().reindex(stunden).fillna(0.0)
    Cn, O, FU = pd.DataFrame(Cn), pd.DataFrame(O), pd.DataFrame(FU)
    C = Cn.ffill()
    O = O.fillna(C.shift(1))
    return stunden, Cn, C, O, FU


def rechnen(start, ende, ordner, slip, tp=0.0, sl=0.0, bezug="schluss", luecke_wie_modul=True):
    stunden, Cn, C, O, FU = laden(start, ende, ordner)
    quelle = Cn if luecke_wie_modul else C
    sig = np.sign(quelle / quelle.shift(L) - 1.0).fillna(0.0)
    handel = stunden[(stunden >= start) & (stunden < ende)]
    S = 1.0 / len(COINS)
    eq = {}; im_markt = {}; orders = 0
    for c in COINS:
        cc, oo, ff = (x[c].reindex(handel).to_numpy() for x in (C, O, FU))
        s_vor = sig[c].shift(1).reindex(handel).fillna(0.0).to_numpy()        # Signal der Vorstunde
        c_vor = C[c].shift(1).reindex(handel).to_numpy()                      # Schluss der Vorstunde
        pos = halte = kasse = geb = fund = ein = gesperrt = 0.0
        e = np.empty(len(handel)); drin = np.zeros(len(handel))
        for i in range(len(handel)):
            if ff[i] != 0.0 and pos != 0.0:
                fund -= pos * oo[i] * ff[i]
            s = s_vor[i]
            ziel = halte
            if not np.isfinite(oo[i]) or not np.isfinite(cc[i]):              # noch kein Kurs: keine Position
                e[i] = kasse + fund - geb
                continue
            if gesperrt != 0.0 and s != gesperrt:
                gesperrt = 0.0
            if halte != 0.0 and s != halte:
                ziel = 0.0
            if ziel == 0.0 and s != 0.0 and gesperrt == 0.0:
                ziel = s
            elif halte != 0.0 and ziel == halte and (tp > 0 or sl > 0):
                r = (c_vor[i] / ein - 1.0) * halte
                if (tp > 0 and r >= tp) or (sl > 0 and r <= -sl):
                    ziel = 0.0; gesperrt = halte
            if ziel != halte:
                neu = ziel * S / oo[i]
                dq = neu - pos
                if dq != 0.0:
                    px = oo[i] * (1.0 + np.sign(dq) * slip[c])
                    kasse -= dq * px; geb += abs(dq) * px * TAKER * (1.0 - REBATE); orders += 1
                    if ziel != 0.0:
                        ein = c_vor[i] if bezug == "schluss" else px
                pos, halte = neu, ziel
            e[i] = kasse + pos * cc[i] + fund - geb
            drin[i] = 1.0 if halte != 0.0 else 0.0
        eq[c] = pd.Series(e, index=handel); im_markt[c] = drin
    g = pd.DataFrame(eq).sum(axis=1)
    t = g.groupby(g.index.normalize()).last()
    return t.diff().fillna(t.iloc[0]), float(np.mean([v.mean() for v in im_markt.values()])), orders


def kenn(x):
    k = 1.0 + x.cumsum()
    return {"tage": int(len(x)), "N": float(x.sum()), "jahr": float(x.mean() * 365), "sharpe": float(x.mean() / x.std() * np.sqrt(365)),
            "dd_tag": float(((k.cummax() - k) / k.cummax()).max())}


sp = pd.read_csv("data/processed/yubit_spannen_stichprobe.csv")
sp["halb"] = (sp["brief"] - sp["geld"]) / (sp["brief"] + sp["geld"])
halb = sp.groupby("symbol")["halb"].mean()
SLIP = {c: max(0.00005, 2.0 * float(halb[c + "USDT"])) for c in COINS}
START, D1_ENDE, SPLIT, ENDE = (pd.Timestamp(x) for x in ("2021-08-15", "2023-07-01", "2025-04-01", "2026-10-24"))
out = {}

# ---- 1) Runde 24: sl5_tp15 (nur Entwicklungszeitraum, wie im Protokoll berichtet) ----
g24 = json.load(open("reports/suche_runde24.json"))["varianten"]["sl5_tp15"]
for bezug in ("schluss", "fuellkurs"):
    tg, drin, orders = rechnen(START, SPLIT, ["5m"], SLIP, tp=0.15, sl=0.05, bezug=bezug)
    out[f"sl5_tp15_{bezug}"] = {"D1": kenn(tg[tg.index < D1_ENDE]), "D2": kenn(tg[tg.index >= D1_ENDE]), "Entwicklung": kenn(tg),
                                "im_markt": drin, "orders": orders}
out["sl5_tp15_gespeichert"] = {"D1": g24["D1"]["sharpe"], "D2": g24["D2"]["sharpe"], "Entwicklung": g24["Entwicklung"]["sharpe"],
                               "jahr": g24["jahr"], "dd": g24["dd"], "im_markt": g24["im_markt"]}
# Gegenprobe: ohne tp/sl muss dieselbe Funktion den Kandidaten liefern
tg0, _, _ = rechnen(START, SPLIT, ["5m"], SLIP)
out["kandidat_gegenprobe_entwicklung"] = kenn(tg0)

# ---- 2) Runde 4: Vorperiode Gruppe A, Slippage 0,05 % ----
VS, VE = pd.Timestamp("2020-02-01"), pd.Timestamp("2021-08-15")
g4 = json.load(open("reports/suche_runde4.json"))["vorperiode"]["A"]
for name, wie in (("luecke_wie_modul", True), ("luecke_ffill", False)):
    tv, _, orders = rechnen(VS, VE, ["5m_vor", "5m"], {c: 0.0005 for c in COINS}, luecke_wie_modul=wie)
    out[f"vorperiode_A_{name}"] = {**kenn(tv), "orders": orders}
out["vorperiode_A_gespeichert"] = {k: g4[k] for k in ("N", "sharpe", "jahr_N", "dd_mit", "trades")}
# Datenlage der Vorperiode: erster Kurs je Coin
erste = {}
for c in COINS:
    k = pd.read_parquet(f"data/candles/5m_vor/{c}USDT.parquet", columns=["close"])
    idx = pd.DatetimeIndex(k.index)
    voll = pd.date_range(idx[0], idx[-1], freq="5min")
    erste[c] = {"erste_kerze": str(idx[0]), "fehlende_5m": int(len(voll) - len(idx))}
out["vorperiode_daten"] = erste
json.dump(out, open(AUS_JSON, "w"), indent=1, default=float)

for k in ("sl5_tp15_schluss", "sl5_tp15_fuellkurs"):
    e = out[k]
    print(k, {f: round(e[f]["sharpe"], 4) for f in ("D1", "D2", "Entwicklung")}, "jahr", round(e["Entwicklung"]["jahr"], 4),
          "dd", round(e["Entwicklung"]["dd_tag"], 4), "im_markt", round(e["im_markt"], 4), "orders", e["orders"])
print("gespeichert:", {k: round(v, 4) for k, v in out["sl5_tp15_gespeichert"].items()})
print("Gegenprobe Kandidat (Entwicklung):", {k: round(v, 4) for k, v in out["kandidat_gegenprobe_entwicklung"].items()})
for k in ("vorperiode_A_luecke_wie_modul", "vorperiode_A_luecke_ffill"):
    print(k, {a: round(b, 4) for a, b in out[k].items()})
print("gespeichert:", {k: round(v, 4) for k, v in out["vorperiode_A_gespeichert"].items()})
print("Vorperiode Daten:", json.dumps(erste))
