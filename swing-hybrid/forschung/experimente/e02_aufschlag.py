"""E02 Aufschlag des Kontrakts auf den Index: Gegenposition bei extremem Aufschlag (Protokoll Abschnitt 5)."""
import sys, time
from pathlib import Path
import numpy as np, pandas as pd
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from alpha import kern as K

start = time.time()
slip = K.slippage_bp(K.COINS)
FENSTER = 288


def signale(coin, schwelle, limit):
    k = K.lesen("5m", coin)
    p = K.lesen("premium_5m", coin)["close"].reindex(k.index)
    z = ((p - p.rolling(FENSTER).mean()) / p.rolling(FENSTER).std()).to_numpy()
    idx = np.flatnonzero(np.abs(z) >= schwelle)
    ein, aus, ri = [], [], []
    frei = 0
    for i in idx:                                   # Signal am Schluss der Kerze i, Einstieg Open i+1
        if i + 1 < frei:
            continue
        r = -np.sign(z[i])
        j = i + 1
        while j < i + limit and j < len(z) and not (z[j] * z[i] <= 0):   # Ausstieg, wenn d die Null kreuzt
            j += 1
        ein.append(i + 1); aus.append(j + 1); ri.append(r); frei = j + 1
    return K.trades(coin, k, np.array(ein, int), np.array(aus, int), np.array(ri, float), K.lesen("funding", coin))


erg = {}
for name, (s, lim) in {"haupt_z2.5_60m": (2.5, 12), "z2.0_60m": (2.0, 12), "z3.0_60m": (3.0, 12),
                       "z2.5_15m": (2.5, 3), "z2.5_240m": (2.5, 48)}.items():
    t = pd.concat([signale(c, s, lim) for c in K.COINS])
    erg[name] = K.stufe0(t, slip)
    print(K.zeile(name, erg[name]["gesamt"]), "| bestanden" if erg[name]["bestanden"] else "| nicht bestanden")
    if name.startswith("haupt"):
        tn = K.netto(t, slip); tn = tn[(tn["ein"] >= K.E_VON) & (tn["ein"] < K.E_BIS)]
        erg["haupt_je_coin"] = {c: K.kennzahlen(tn[tn["coin"] == c]) for c in K.COINS}
        erg["haupt_je_richtung"] = {str(r): K.kennzahlen(tn[tn["richtung"] == r]) for r in (-1.0, 1.0)}
        for c in K.COINS: print("   ", K.zeile(c, erg["haupt_je_coin"][c]))
K.speichern("e02_aufschlag", {"zeitraum": "Entwicklung", "ergebnis": erg}, start)
