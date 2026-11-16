"""E01 Orderbuch-Tiefe: Position in Richtung des Übergewichts der Aufträge nahe am Kurs (Protokoll Abschnitt 5)."""
import sys, time
from pathlib import Path
import numpy as np, pandas as pd
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from alpha import kern as K

start = time.time()
COINS = ["BTC", "ETH", "SOL"]
slip = K.slippage_bp(COINS)
E_VON, E_BIS = pd.Timestamp("2023-01-02"), pd.Timestamp("2024-04-01")


def z_wert(coin, stufe):
    k = K.lesen("5m", coin); k = k[k.index >= "2023-01-01"]
    d = K.lesen("tiefe_5m", coin).reindex(k.index)
    u = (d[f"w-{stufe}"] - d[f"w+{stufe}"]) / (d[f"w-{stufe}"] + d[f"w+{stufe}"])
    return k, ((u - u.rolling(288, min_periods=200).mean()) / u.rolling(288, min_periods=200).std()).to_numpy()


def lauf(stufe, schwelle, halte):
    ts = []
    for coin in COINS:
        k, z = z_wert(coin, stufe)
        i = np.flatnonzero(np.abs(z) >= schwelle)
        ein, aus = i + 1, i + 1 + halte
        ok = K.ohne_ueberlappung(ein, aus)
        ts.append(K.trades(coin, k, ein[ok], aus[ok], np.sign(z[i])[ok], K.lesen("funding", coin)))
    return pd.concat(ts)


erg = {}
for name, (st, s, h) in {"haupt_1pct_z2_60m": (1, 2.0, 12), "1pct_z2_15m": (1, 2.0, 3), "1pct_z2_240m": (1, 2.0, 48),
                         "5pct_z2_60m": (5, 2.0, 12)}.items():
    t = lauf(st, s, h)
    erg[name] = K.stufe0(t, slip, E_VON, E_BIS)
    print(K.zeile(name, erg[name]["gesamt"]), "| bestanden" if erg[name]["bestanden"] else "| nicht bestanden")
    if name.startswith("haupt"):
        tn = K.netto(t, slip); tn = tn[(tn["ein"] >= E_VON) & (tn["ein"] < E_BIS)]
        erg["haupt_je_coin"] = {c: K.kennzahlen(tn[tn["coin"] == c]) for c in COINS}
        erg["haupt_je_richtung"] = {str(r): K.kennzahlen(tn[tn["richtung"] == r]) for r in (-1.0, 1.0)}
        for c in COINS: print("   ", K.zeile(c, erg["haupt_je_coin"][c]))
        for r in ("-1.0", "1.0"): print("   ", K.zeile("Richtung " + r, erg["haupt_je_richtung"][r]))
        print("   ", K.zeile("Hälfte 1", erg[name]["haelfte1"])); print("   ", K.zeile("Hälfte 2", erg[name]["haelfte2"]))
K.speichern("e01_orderbuch_tiefe", {"zeitraum": "Entwicklung 01/2023 bis 03/2024", "ergebnis": erg}, start)
