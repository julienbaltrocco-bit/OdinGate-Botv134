"""E07 Ursachenanalyse Orderbuch-Tiefe (nur Entwicklung 01/2023 bis 03/2024): Raster, Kontrollen, gemeinsame Zufallsprüfung."""
import sys, time
from pathlib import Path
import numpy as np, pandas as pd
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from alpha import kern as K
from hybrid.mutationen import reality_check

start = time.time()
COINS = ["BTC", "ETH", "SOL"]
slip = K.slippage_bp(COINS)
E_VON, E_BIS = pd.Timestamp("2023-01-02"), pd.Timestamp("2024-04-01")
MITTE = E_VON + (E_BIS - E_VON) / 2
cache = {}


def z_wert(coin, stufe):
    if (coin, stufe) not in cache:
        k = K.lesen("5m", coin); k = k[(k.index >= "2023-01-01") & (k.index < E_BIS)]
        d = K.lesen("tiefe_5m", coin).reindex(k.index)
        u = (d[f"w-{stufe}"] - d[f"w+{stufe}"]) / (d[f"w-{stufe}"] + d[f"w+{stufe}"])
        cache[(coin, stufe)] = (k, ((u - u.rolling(288, min_periods=200).mean()) / u.rolling(288, min_periods=200).std()).to_numpy())
    return cache[(coin, stufe)]


def lauf(stufe, schwelle, halte):
    ts = []
    for coin in COINS:
        k, z = z_wert(coin, stufe)
        i = np.flatnonzero(np.abs(z) >= schwelle)
        ein, aus = i + 1, i + 1 + halte
        ok = K.ohne_ueberlappung(ein, aus)
        t = K.trades(coin, k, ein[ok], aus[ok], np.sign(z[i])[ok], K.lesen("funding", coin))
        c = k["close"].to_numpy(); j = (ein[ok] - 1)[: len(t)]
        t["vor_1h"] = np.sign(c[j] / c[np.maximum(j - 12, 0)] - 1) * t["richtung"].to_numpy()
        t["vor_24h"] = np.sign(c[j] / c[np.maximum(j - 288, 0)] - 1) * t["richtung"].to_numpy()
        ts.append(t)
    t = K.netto(pd.concat(ts), slip)
    return t[(t["ein"] >= E_VON) & (t["ein"] < E_BIS)]


tage = pd.date_range(E_VON, E_BIS - pd.Timedelta(days=1), freq="D")
erg, reihen = {}, {}
plan = {f"{s}pct_z2_{h*5}m": (s, 2.0, h) for s in (1, 2, 3, 4, 5) for h in (3, 12, 48)}
for name, (s, z, h) in plan.items():
    t = lauf(s, z, h)
    erg[name] = {"gesamt": K.kennzahlen(t), "h1_roh": K.kennzahlen(t, E_VON, MITTE)["roh"], "h2_roh": K.kennzahlen(t, MITTE, E_BIS)["roh"]}
    reihen[name] = t.groupby(t["ein"].dt.floor("D"))["n85"].sum().reindex(tage, fill_value=0.0)
    print(K.zeile(name, erg[name]["gesamt"]), f"| Hälften roh {erg[name]['h1_roh']} / {erg[name]['h2_roh']}", flush=True)
beste_tiefe = max((1, 2, 3, 4, 5), key=lambda s: erg[f"{s}pct_z2_60m"]["gesamt"]["t_n85"])
for z in (1.0, 3.0):
    name = f"{beste_tiefe}pct_z{z:g}_60m"
    t = lauf(beste_tiefe, z, 12)
    erg[name] = {"gesamt": K.kennzahlen(t), "h1_roh": K.kennzahlen(t, E_VON, MITTE)["roh"], "h2_roh": K.kennzahlen(t, MITTE, E_BIS)["roh"]}
    reihen[name] = t.groupby(t["ein"].dt.floor("D"))["n85"].sum().reindex(tage, fill_value=0.0)
    print(K.zeile(name, erg[name]["gesamt"]), f"| Hälften roh {erg[name]['h1_roh']} / {erg[name]['h2_roh']}", flush=True)

m = pd.DataFrame(reihen).to_numpy()
_, schwelle, p_roh = reality_check(m, ziehungen=3000, block=10, seed=7)
_, _, p_stud = reality_check(m / m.std(axis=0), ziehungen=3000, block=10, seed=7)
zulaessig = [n for n in erg if erg[n]["h1_roh"] > 0 and erg[n]["h2_roh"] > 0]
wahl = max(zulaessig, key=lambda n: erg[n]["gesamt"]["t_n85"]) if zulaessig else None
print(f"\nReality Check über {m.shape[1]} Einstellungen: p roh {p_roh:.3f}, p bei gleicher Schwankung {p_stud:.3f} | Wahl nach Regel: {wahl}")

if wahl:
    s, z, h = plan.get(wahl) or (beste_tiefe, float(wahl.split("_z")[1].split("_")[0]), 12)
    t = lauf(s, z, h)
    det = {"je_coin": {c: K.kennzahlen(t[t["coin"] == c]) for c in COINS},
           "je_richtung": {str(r): K.kennzahlen(t[t["richtung"] == r]) for r in (-1.0, 1.0)},
           "je_quartal": {str(q): K.kennzahlen(g) for q, g in t.groupby(t["ein"].dt.to_period("Q"))},
           "mit_1h_bewegung": K.kennzahlen(t[t["vor_1h"] > 0]), "gegen_1h_bewegung": K.kennzahlen(t[t["vor_1h"] < 0]),
           "mit_24h_bewegung": K.kennzahlen(t[t["vor_24h"] > 0]), "gegen_24h_bewegung": K.kennzahlen(t[t["vor_24h"] < 0])}
    for gruppe in ("je_coin", "je_richtung", "je_quartal"):
        for n2, kz in det[gruppe].items(): print("   ", K.zeile(f"{gruppe} {n2}", kz))
    for n2 in ("mit_1h_bewegung", "gegen_1h_bewegung", "mit_24h_bewegung", "gegen_24h_bewegung"): print("   ", K.zeile(n2, det[n2]))
    tag = reihen[wahl]
    det["anteil_bester_tag"] = round(float(tag.max() / tag.sum()), 3) if tag.sum() > 0 else None
    det["sharpe_jahr_n85"] = round(float(tag.mean() / tag.std() * np.sqrt(365)), 2)
    print("    Anteil des besten Tages am Gesamtgewinn:", det["anteil_bester_tag"], "| Sharpe pro Jahr (Tagesreihe N85):", det["sharpe_jahr_n85"])
    erg["wahl_details"] = det
K.speichern("e07_tiefe_ursache", {"zeitraum": "Entwicklung 01/2023 bis 03/2024", "einstellungen": m.shape[1], "p_roh": p_roh,
                                  "p_gleiche_schwankung": p_stud, "wahl": wahl, "ergebnis": erg}, start)
