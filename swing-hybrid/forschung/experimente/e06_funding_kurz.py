"""E06 Funding-Abgriff mit kurzer Haltedauer: 5 Minuten vor bis 5 Minuten nach dem Termin (Mutation von E03)."""
import sys, time
from pathlib import Path
import numpy as np, pandas as pd
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from alpha import kern as K

start = time.time()
slip_alle = K.slippage_bp(K.COINS)
COINS = [c for c in K.COINS if 2 * slip_alle[c] <= 5.0]
slip = {c: slip_alle[c] for c in COINS}


def ereignisse(coin):
    k, f = K.lesen("5m", coin), K.lesen("funding", coin)
    p = K.lesen("premium_5m", coin)["close"]
    kum = p.fillna(0).cumsum(); anz = p.notna().cumsum()
    T = f.index.floor("min")
    zeilen = []
    for a, b, rate in zip(T[:-1], T[1:], f["rate"].to_numpy()[1:]):
        bis = b - pd.Timedelta(minutes=15)             # letzte Kerze mit Schluss 10 Minuten vor dem Termin
        if bis <= a or a not in kum.index or bis not in kum.index or anz[bis] - anz[a] < 6:
            continue
        mp = (kum[bis] - kum[a]) / (anz[bis] - anz[a])
        zeilen.append((b, mp + np.clip(0.0001 - mp, -0.0005, 0.0005), rate))
    e = pd.DataFrame(zeilen, columns=["termin", "erwartet", "rate"])
    pos = k.index.get_indexer(e["termin"])
    return k, f, e[pos >= 0].assign(pos=pos[pos >= 0])


def lauf(schwelle):
    ts = []
    for coin in COINS:
        k, f, e = ereignisse(coin)
        s = e[np.abs(e["erwartet"]) >= schwelle]
        pos = s["pos"].to_numpy()
        ts.append(K.trades(coin, k, pos - 1, pos + 1, -np.sign(s["erwartet"].to_numpy()), f))
    return pd.concat(ts)


erg = {"coins": COINS}
for name, s in {"haupt_0.03": 0.0003, "0.02": 0.0002, "0.05": 0.0005}.items():
    t = lauf(s)
    erg[name] = K.stufe0(t, slip)
    print(K.zeile(name, erg[name]["gesamt"]), "| bestanden" if erg[name]["bestanden"] else "| nicht bestanden", erg[name]["huerden"])
    if name.startswith("haupt"):
        tn = K.netto(t, slip); tn = tn[(tn["ein"] >= K.E_VON) & (tn["ein"] < K.E_BIS)]
        erg["haupt_je_coin"] = {c: K.kennzahlen(tn[tn["coin"] == c]) for c in COINS}
        erg["haupt_je_richtung"] = {str(r): K.kennzahlen(tn[tn["richtung"] == r]) for r in (-1.0, 1.0)}
        erg["haupt_je_halbjahr"] = {str(p): K.kennzahlen(g) for p, g in tn.groupby(tn["ein"].dt.to_period("6M"))}
        for c in COINS: print("   ", K.zeile(c, erg["haupt_je_coin"][c]))
        for r in ("-1.0", "1.0"): print("   ", K.zeile("Richtung " + r, erg["haupt_je_richtung"][r]))
        for p, kz in erg["haupt_je_halbjahr"].items(): print("   ", K.zeile(p, kz))
        print("    Streuung roh (bp):", round(float(tn["roh"].std()), 1), "| doppelte Slippage N85:", erg[name]["doppelte_slippage_n85"])
K.speichern("e06_funding_kurz", {"zeitraum": "Entwicklung", "ergebnis": erg}, start)
