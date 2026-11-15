"""QR (k): Stop 5 % / Ziel 15 % mit Pruefung je Stunde (Runde 24, tpsl.py) gegen Pruefung alle 5 Minuten
(so arbeitet der Papier-Bot von Test 2: bot.py prueft bei JEDEM Durchlauf gegen den aktuellen Mittelkurs,
stunde.sh laeuft etwa alle fuenf Minuten). Unabhaengige Rechnung auf 5-Minuten-Kerzen, kein Modul aus src/hybrid.

NUR Entwicklungszeitraum 15.08.2021-31.03.2025 (der Pruefzeitraum bleibt fuer diese Variante unberuehrt, wie in Runde 24).
Aufruf aus swing-hybrid/:  .venv/bin/python -I -B <dieses Skript> <ausgabe.json>
"""
import json
import sys

import numpy as np
import pandas as pd

AUS_JSON = sys.argv[1]
COINS = ["BTC", "ETH", "SOL", "XRP", "DOT", "DOGE", "ADA", "LINK", "AVAX", "LTC"]
START, D1_ENDE, SPLIT = (pd.Timestamp(x) for x in ("2021-08-15", "2023-07-01", "2025-04-01"))
L, TAKER, REBATE, S = 336, 0.0008, 0.85, 0.1
sp = pd.read_csv("data/processed/yubit_spannen_stichprobe.csv")
sp["halb"] = (sp["brief"] - sp["geld"]) / (sp["brief"] + sp["geld"])
halb = sp.groupby("symbol")["halb"].mean()
SLIP = {c: max(0.00005, 2.0 * float(halb[c + "USDT"])) for c in COINS}
raster = pd.date_range(START, SPLIT, freq="5min", inclusive="left")
stunden = pd.date_range(START - pd.Timedelta(hours=L + 48), SPLIT, freq="1h", inclusive="left")
erste_der_stunde = (raster.minute == 0)

daten = {}
for c in COINS:
    k = pd.read_parquet(f"data/candles/5m/{c}USDT.parquet")
    k.index = pd.DatetimeIndex(k.index).astype("datetime64[ns]")
    hc = k["close"].resample("1h").last().reindex(stunden)
    sig = np.sign(hc / hc.shift(L) - 1.0).fillna(0.0)
    sig.index = sig.index + pd.Timedelta(hours=1)                   # gilt ab der Folgestunde
    s5 = sig.reindex(raster.union(sig.index)).ffill().reindex(raster).fillna(0.0).to_numpy()
    k5 = k.reindex(raster)
    c5 = k5["close"].ffill().bfill().to_numpy()
    o5 = k5["open"].where(k5["close"].notna(), pd.Series(c5, index=raster)).to_numpy()
    f = pd.read_parquet(f"data/candles/funding/{c}USDT.parquet")["rate"]
    f.index = pd.DatetimeIndex(f.index).astype("datetime64[ns]").floor("5min")
    f5 = f[~f.index.duplicated()].reindex(raster).fillna(0.0).to_numpy()
    daten[c] = (o5, c5, s5, f5)


def rechnen(tp, sl, takt):
    """takt: 'stunde' = Pruefung nur zur vollen Stunde (am letzten Stundenschluss), '5min' = an jedem 5-Minuten-Schluss."""
    gesamt = np.zeros(len(raster)); drin = 0.0; orders = 0; ausstiege = {"stop": 0, "ziel": 0}
    for c in COINS:
        o5, c5, s5, f5 = daten[c]
        slip = SLIP[c]
        pos = halte = kasse = geb = fund = ein = gesperrt = 0.0
        e = np.empty(len(raster)); im = 0
        for t in range(len(raster)):
            if f5[t] != 0.0 and pos != 0.0:
                fund -= pos * o5[t] * f5[t]
            s = s5[t]
            ziel = halte
            if gesperrt != 0.0 and s != gesperrt:
                gesperrt = 0.0
            if halte != 0.0 and s != halte:
                ziel = 0.0
            if ziel == 0.0 and s != 0.0 and gesperrt == 0.0:
                ziel = s
            elif halte != 0.0 and ziel == halte and t > 0 and (takt == "5min" or erste_der_stunde[t]):
                r = (c5[t - 1] / ein - 1.0) * halte
                if tp > 0 and r >= tp:
                    ziel = 0.0; gesperrt = halte; ausstiege["ziel"] += 1
                elif sl > 0 and r <= -sl:
                    ziel = 0.0; gesperrt = halte; ausstiege["stop"] += 1
            if ziel != halte:
                neu = ziel * S / o5[t]
                dq = neu - pos
                if dq != 0.0:
                    px = o5[t] * (1.0 + np.sign(dq) * slip)
                    kasse -= dq * px; geb += abs(dq) * px * TAKER * (1.0 - REBATE); orders += 1
                    if ziel != 0.0:
                        ein = px
                pos, halte = neu, ziel
            e[t] = kasse + pos * c5[t] + fund - geb
            im += halte != 0.0
        gesamt += e; drin += im / len(raster) / len(COINS)
    g = pd.Series(gesamt, index=raster)
    tg = g.groupby(g.index.normalize()).last()
    tg = tg.diff().fillna(tg.iloc[0])
    return tg, drin, orders, ausstiege


def kenn(x):
    k = 1.0 + x.cumsum()
    return {"N": float(x.sum()), "jahr": float(x.mean() * 365), "sharpe": float(x.mean() / x.std() * np.sqrt(365)),
            "dd_tag": float(((k.cummax() - k) / k.cummax()).max())}


out = {}
for name, tp, sl, takt in (("kandidat", 0.0, 0.0, "stunde"), ("sl5_tp15_stunde", 0.15, 0.05, "stunde"), ("sl5_tp15_5min", 0.15, 0.05, "5min")):
    tg, drin, orders, aus = rechnen(tp, sl, takt)
    out[name] = {"D1": kenn(tg[tg.index < D1_ENDE]), "D2": kenn(tg[tg.index >= D1_ENDE]), "Entwicklung": kenn(tg), "im_markt": drin,
                 "orders": orders, "ausstiege": aus}
    e = out[name]
    print(f"{name:18s} Sharpe D1/D2/Entw {e['D1']['sharpe']:.3f} / {e['D2']['sharpe']:.3f} / {e['Entwicklung']['sharpe']:.3f} | Ertrag/Jahr {e['Entwicklung']['jahr']:.3f}"
          f" | Einbruch {e['Entwicklung']['dd_tag']:.3f} | im Markt {drin:.3f} | Orders {orders} | Ausstiege {aus}")
g = json.load(open("reports/suche_runde24.json"))["varianten"]["sl5_tp15"]
out["gespeichert_runde24_sl5_tp15"] = {"D1": g["D1"]["sharpe"], "D2": g["D2"]["sharpe"], "Entwicklung": g["Entwicklung"]["sharpe"], "jahr": g["jahr"], "dd": g["dd"], "im_markt": g["im_markt"]}
print("gespeichert Runde 24 sl5_tp15:", {k: round(v, 4) for k, v in out["gespeichert_runde24_sl5_tp15"].items()})
json.dump(out, open(AUS_JSON, "w"), indent=1, default=float)
