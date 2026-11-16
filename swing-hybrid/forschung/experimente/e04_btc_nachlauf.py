"""E04 Nachlauf hinter BTC: Altcoin in BTC-Richtung kaufen, wenn er einer starken BTC-Bewegung noch nicht gefolgt ist."""
import sys, time
from pathlib import Path
import numpy as np, pandas as pd
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from alpha import kern as K

start = time.time()
ALT = [c for c in K.COINS if c != "BTC"]
slip = K.slippage_bp(K.COINS)
btc = K.lesen("1m", "BTC"); btc = btc[btc.index < K.E_BIS]            # Stufe 0 braucht nur die Entwicklung
rb = btc["close"].pct_change(5)
sb = rb.rolling(1440).std().shift(1)


def lauf(coin, schwelle, halte):
    k = K.lesen("1m", coin); k = k[k.index < K.E_BIS].reindex(btc.index)
    k[["open", "close"]] = k[["open", "close"]].ffill()
    ra = k["close"].pct_change(5)
    beta = (ra.rolling(10080).cov(rb) / rb.rolling(10080).var()).shift(1)
    stark = (rb.abs() >= schwelle * sb).to_numpy()
    r = np.sign(rb.to_numpy())
    zurueck = (r * ra.to_numpy()) < 0.5 * np.abs((beta * rb).to_numpy())
    i = np.flatnonzero(stark & zurueck & np.isfinite(beta.to_numpy()))
    ein, aus = i + 1, i + 1 + halte
    ok = K.ohne_ueberlappung(ein, aus)
    return K.trades(coin, k, ein[ok], aus[ok], r[i][ok], K.lesen("funding", coin))


erg = {}
for name, (s, h) in {"haupt_3s_15m": (3.0, 15), "3s_5m": (3.0, 5), "3s_60m": (3.0, 60), "2s_15m": (2.0, 15), "4s_15m": (4.0, 15)}.items():
    t = pd.concat([lauf(c, s, h) for c in ALT])
    erg[name] = K.stufe0(t, slip)
    print(K.zeile(name, erg[name]["gesamt"]), "| bestanden" if erg[name]["bestanden"] else "| nicht bestanden", flush=True)
    if name.startswith("haupt"):
        tn = K.netto(t, slip); tn = tn[(tn["ein"] >= K.E_VON) & (tn["ein"] < K.E_BIS)]
        erg["haupt_je_coin"] = {c: K.kennzahlen(tn[tn["coin"] == c]) for c in ALT}
        for c in ALT: print("   ", K.zeile(c, erg["haupt_je_coin"][c]))
        print("   ", K.zeile("Hälfte 1", erg[name]["haelfte1"])); print("   ", K.zeile("Hälfte 2", erg[name]["haelfte2"]))
K.speichern("e04_btc_nachlauf", {"zeitraum": "Entwicklung", "ergebnis": erg}, start)
