"""E03 Funding-Termin: Position vor dem Termin (a) und Gegenrichtung danach (b), wenn die erwartete Rate hoch ist."""
import sys, time
from pathlib import Path
import numpy as np, pandas as pd
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from alpha import kern as K

start = time.time()
slip = K.slippage_bp(K.COINS)


def ereignisse(coin):
    """Je Funding-Termin: erwartete Rate 65 Minuten vorher (nur aus bis dahin bekanntem Aufschlag) und tatsächliche Rate."""
    k, f = K.lesen("5m", coin), K.lesen("funding", coin)
    p = K.lesen("premium_5m", coin)["close"]
    kum = p.fillna(0).cumsum(); anz = p.notna().cumsum()
    T = f.index.floor("min")
    zeilen = []
    for a, b, rate in zip(T[:-1], T[1:], f["rate"].to_numpy()[1:]):
        bis = b - pd.Timedelta(minutes=70)             # letzte Kerze, deren Schluss 65 Minuten vor dem Termin liegt
        if bis <= a or a not in kum.index or bis not in kum.index:
            continue
        n = anz[bis] - anz[a]
        if n < 6:
            continue
        mp = (kum[bis] - kum[a]) / n
        zeilen.append((b, mp + np.clip(0.0001 - mp, -0.0005, 0.0005), rate))
    e = pd.DataFrame(zeilen, columns=["termin", "erwartet", "rate"])
    pos = k.index.get_indexer(e["termin"])
    return k, f, e[pos >= 0].assign(pos=pos[pos >= 0])


def lauf(schwelle):
    ta, tb = [], []
    for coin in K.COINS:
        k, f, e = ereignisse(coin)
        s = e[np.abs(e["erwartet"]) >= schwelle]
        r = -np.sign(s["erwartet"].to_numpy()); pos = s["pos"].to_numpy()
        ta.append(K.trades(coin, k, pos - 12, pos + 1, r, f))          # 60 Minuten vor bis 5 Minuten nach dem Termin
        tb.append(K.trades(coin, k, pos + 1, pos + 13, -r, f))         # danach 60 Minuten Gegenrichtung
    return pd.concat(ta), pd.concat(tb)


erg = {}
k, f, e = ereignisse("BTC")
e = e[e["termin"] < K.E_BIS]
erg["schaetzung_btc"] = {"korrelation_erwartet_tatsaechlich": round(float(np.corrcoef(e["erwartet"], e["rate"])[0, 1]), 3), "termine": len(e)}
print("Schätzgüte BTC:", erg["schaetzung_btc"])
for name, s in {"haupt_0.03": 0.0003, "0.02": 0.0002, "0.05": 0.0005}.items():
    a, b = lauf(s)
    erg[f"a_vor_{name}"], erg[f"b_nach_{name}"] = K.stufe0(a, slip), K.stufe0(b, slip)
    for n2 in (f"a_vor_{name}", f"b_nach_{name}"):
        print(K.zeile(n2, erg[n2]["gesamt"]), "| bestanden" if erg[n2]["bestanden"] else "| nicht bestanden")
    if name.startswith("haupt"):
        tn = K.netto(a, slip); tn = tn[(tn["ein"] >= K.E_VON) & (tn["ein"] < K.E_BIS)]
        erg["a_haupt_je_coin"] = {c: K.kennzahlen(tn[tn["coin"] == c]) for c in K.COINS}
        erg["a_haupt_je_richtung"] = {str(r): K.kennzahlen(tn[tn["richtung"] == r]) for r in (-1.0, 1.0)}
        for c in K.COINS: print("   ", K.zeile(c, erg["a_haupt_je_coin"][c]))
        for r in ("-1.0", "1.0"): print("   ", K.zeile("Richtung " + r, erg["a_haupt_je_richtung"][r]))
K.speichern("e03_funding_termin", {"zeitraum": "Entwicklung", "ergebnis": erg}, start)
