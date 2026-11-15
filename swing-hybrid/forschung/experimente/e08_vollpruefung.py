"""E08 Vollprüfung „Orderbuch-Stütze“ 1.0: Entwicklung und (einmalig) Validierung, Stress, Hebel, Starttage, Kontrolle."""
import sys, time
from pathlib import Path
import numpy as np, pandas as pd
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from alpha import kern as K, konto, orderbuch_stuetze as S

start = time.time()
COINS = sys.argv[1:] or ["BTC", "ETH", "SOL"]
NAME = "e08_vollpruefung" if COINS == ["BTC", "ETH", "SOL"] else "e09_frische_coins"
slip = K.slippage_bp(COINS)
E = (pd.Timestamp("2023-01-02"), pd.Timestamp("2024-04-01")); V = (pd.Timestamp("2024-04-01"), pd.Timestamp("2025-04-01"))
ZEIT = {"E": E, "V": V, "E+V": (E[0], V[1])}

roh = pd.concat([S.trades(c) for c in COINS], ignore_index=True)
t = K.netto(roh, slip)
erg = {"coins": COINS, "version": S.VERSION, "parameter": S.PARAMETER, "slippage_bp_je_order": slip}
for z, (a, b) in ZEIT.items():
    erg[z] = K.kennzahlen(t, a, b)
    print(K.zeile(z, erg[z]))
for z in ("E", "V"):
    a, b = ZEIT[z]
    erg[f"{z}_je_coin"] = {c: K.kennzahlen(t[t["coin"] == c], a, b) for c in COINS}
    for c in COINS: print("   ", K.zeile(f"{z} {c}", erg[f"{z}_je_coin"][c]))
    erg[f"{z}_je_richtung"] = {str(r): K.kennzahlen(t[t["richtung"] == r], a, b) for r in (-1.0, 1.0)}
    for r in ("-1.0", "1.0"): print("   ", K.zeile(f"{z} Richtung {r}", erg[f"{z}_je_richtung"][r]))
erg["je_quartal"] = {str(q): K.kennzahlen(g) for q, g in t[(t["ein"] >= E[0]) & (t["ein"] < V[1])].groupby(t["ein"].dt.to_period("Q"))}
print("    Quartale N85:", {q: k["n85"] for q, k in erg["je_quartal"].items()})

print("\nStress:")
t2 = K.netto(roh, slip, 2.0)
tv = K.netto(pd.concat([S.trades(c, verzug=1) for c in COINS], ignore_index=True), slip)
for z in ("E", "V"):
    a, b = ZEIT[z]
    erg[f"{z}_doppelte_slippage"], erg[f"{z}_eine_kerze_spaeter"] = K.kennzahlen(t2, a, b), K.kennzahlen(tv, a, b)
    print("   ", K.zeile(f"{z} doppelte Slippage", erg[f"{z}_doppelte_slippage"])); print("   ", K.zeile(f"{z} eine Kerze später", erg[f"{z}_eine_kerze_spaeter"]))

print("\nKonto (feste Größe je Coin, ohne Zinseszins):")
for z, (a, b) in ZEIT.items():
    for sp in ("n85", "n50", "n0"):
        erg[f"konto_{z}_{sp}"] = konto.kennzahlen(konto.tagesreihe(t, sp, a, b, len(COINS)))
    k = erg[f"konto_{z}_n85"]
    erg[f"verlustserie_{z}"] = konto.verlustserie(t[(t["ein"] >= a) & (t["ein"] < b)], "n85")
    print(f"    {z:<4} Hebel 1, N85: {k} | längste Verlustserie {erg[f'verlustserie_{z}']} Trades | N0 pro Jahr {erg[f'konto_{z}_n0']['ertrag_jahr_pct']} %")
for h in (1, 3, 5):
    for z in ("E", "V"):
        a, b = ZEIT[z]
        erg[f"starttage_{z}_hebel{h}"] = konto.starttage(t, "n85", a, b, len(COINS), h)
        print(f"    Starttage {z} Hebel {h}: {erg[f'starttage_{z}_hebel{h}']}")
tt = t[(t["ein"] >= E[0]) & (t["ein"] < V[1])]
erg["schlimmster_kurs_im_trade_bp"] = {"p1": round(float(tt["schlimmst"].quantile(0.01)), 1), "min": round(float(tt["schlimmst"].min()), 1)}
print("    Ungünstigster Kurs innerhalb eines Trades (bp):", erg["schlimmster_kurs_im_trade_bp"])

if NAME == "e08_vollpruefung":
    print("\nKontrolle: Gegenbewegung zur Stundenbewegung ohne Orderbuch (gleiche Trade-Zahl in E):")
    ziel = erg["E"]["trades"]
    def kontrolle(schwelle):
        ts = []
        for c in COINS:
            k = K.lesen("5m", c); k = k[k.index >= "2023-01-01"]
            r = k["close"].pct_change(12)
            zz = (r / r.rolling(288).std().shift(1)).to_numpy()
            i = np.flatnonzero(np.abs(zz) >= schwelle)
            ein, aus = i + 1, i + 13
            ok = K.ohne_ueberlappung(ein, aus)
            ts.append(K.trades(c, k, ein[ok], aus[ok], -np.sign(zz[i])[ok], K.lesen("funding", c)))
        return K.netto(pd.concat(ts), slip)
    lo, hi = 0.5, 8.0
    for _ in range(18):
        mid = (lo + hi) / 2
        n = K.kennzahlen(kontrolle(mid), *E)["trades"]
        lo, hi = (mid, hi) if n > ziel else (lo, mid)
    kt = kontrolle((lo + hi) / 2)
    erg["kontrolle_schwelle"] = round((lo + hi) / 2, 3)
    for z in ("E", "V"):
        erg[f"kontrolle_{z}"] = K.kennzahlen(kt, *ZEIT[z])
        print("   ", K.zeile(f"{z} Kontrolle", erg[f"kontrolle_{z}"]))

a = erg["E"]; v = erg["V"]; ev = erg["E+V"]
if NAME == "e08_vollpruefung":
    h = {"n85_E_positiv": a["n85"] > 0, "n85_V_positiv": v["n85"] > 0, "t_EV_mind_2": ev["t_n85"] >= 2,
         "kein_tag_ueber_20pct": (erg["konto_E+V_n85"]["anteil_bester_tag"] or 1) <= 0.20,
         "keine_liquidation_hebel3": erg["starttage_E_hebel3"]["liquidationen"] + erg["starttage_V_hebel3"]["liquidationen"] == 0}
else:
    h = {"roh_EV_positiv": ev["roh"] > 0, "t_roh_EV_mind_2": ev["t_roh"] >= 2}
erg["huerden"], erg["bestanden"] = {k: bool(x) for k, x in h.items()}, bool(all(h.values()))
print("\nHürden:", erg["huerden"], "→", "BESTANDEN" if erg["bestanden"] else "NICHT BESTANDEN")
if NAME == "e09_frische_coins":
    f = t[~t["coin"].isin(["ADA", "DOT"])]
    erg["fuenf_handelbare"] = {z: K.kennzahlen(f, a, b) for z, (a, b) in ZEIT.items()}
    for z in ZEIT: print(K.zeile(f"5 handelbare {z}", erg["fuenf_handelbare"][z]))
t[(t["ein"] >= E[0]) & (t["ein"] < V[1])].to_csv(K.ERG / f"{NAME}_trades.csv", index=False)
K.speichern(NAME, erg, start)
