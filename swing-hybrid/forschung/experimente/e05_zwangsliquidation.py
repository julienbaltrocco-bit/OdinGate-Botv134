"""E05 Zwangsliquidationen: Gegenposition nach starker Stundenbewegung mit fallendem Open Interest."""
import sys, time
from pathlib import Path
import numpy as np, pandas as pd
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from alpha import kern as K

start = time.time()
slip = K.slippage_bp(K.COINS)
E_VON = pd.Timestamp("2022-01-01")                    # Open Interest ab 12/2021, 30 Tage Vorlauf


def ereignisse(coin):
    k = K.lesen("5m", coin)
    c1 = k["close"].resample("1h").last()                              # Schluss der Stunde, Index = Stundenbeginn
    r = c1.pct_change()
    oi = K.lesen("metrics", coin)["oi"].reindex(c1.index)              # letzter Stand innerhalb der Stunde
    doi = oi.pct_change()
    zr, zo = r / r.rolling(720).std().shift(1), doi / doi.rolling(720).std().shift(1)
    d = pd.DataFrame({"zr": zr, "zo": zo}).dropna()
    d["pos"] = k.index.get_indexer(d.index + pd.Timedelta(minutes=65))  # Einstieg 5 Minuten nach Stundenschluss
    return k, d[d["pos"] >= 0]


def lauf(halte_h, oi_faellt=True):
    ts = []
    for coin in K.COINS:
        k, d = ereignisse(coin)
        s = d[(np.abs(d["zr"]) >= 2) & ((d["zo"] <= -1.5) if oi_faellt else (d["zo"] >= 1.5))]
        ein = s["pos"].to_numpy(); aus = ein + 12 * halte_h; ri = -np.sign(s["zr"].to_numpy())
        ok = K.ohne_ueberlappung(ein, aus)
        ts.append(K.trades(coin, k, ein[ok], aus[ok], ri[ok], K.lesen("funding", coin)))
    return pd.concat(ts)


erg = {}
for name, (h, f) in {"haupt_4h": (4, True), "1h": (1, True), "12h": (12, True), "kontrolle_oi_steigt_4h": (4, False)}.items():
    t = lauf(h, f)
    erg[name] = K.stufe0(t, slip, E_VON, K.E_BIS)
    print(K.zeile(name, erg[name]["gesamt"]), "| bestanden" if erg[name]["bestanden"] else "| nicht bestanden")
    if name.startswith("haupt"):
        tn = K.netto(t, slip); tn = tn[(tn["ein"] >= E_VON) & (tn["ein"] < K.E_BIS)]
        erg["haupt_je_richtung"] = {str(r): K.kennzahlen(tn[tn["richtung"] == r]) for r in (-1.0, 1.0)}
        for r in ("-1.0", "1.0"): print("   ", K.zeile("Richtung " + r, erg["haupt_je_richtung"][r]))
K.speichern("e05_zwangsliquidation", {"zeitraum": "Entwicklung ab 01/2022", "ergebnis": erg}, start)
