"""E10 Ausstiegs-Engine für „Orderbuch-Stütze“: Einstiege wie Version 1.0, acht Ausstiegsarten (nur Entwicklung).

Stops werden gegen Hoch und Tief jeder 5-Minuten-Kerze geprüft. Trifft eine Kerze den Stop, gilt der Stopkurs
(bei Kurslücke der schlechtere Eröffnungskurs). Der nachgezogene Stop benutzt nur Kurse früherer Kerzen.
"""
import sys, time
from pathlib import Path
import numpy as np, pandas as pd
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from alpha import kern as K, konto, orderbuch_stuetze as S
from hybrid.mutationen import reality_check

start = time.time()
COINS = ["BTC", "ETH", "SOL"]
slip = K.slippage_bp(COINS)
E = (pd.Timestamp("2023-01-02"), pd.Timestamp("2024-04-01")); V = (pd.Timestamp("2024-04-01"), pd.Timestamp("2025-04-01"))
MITTE = E[0] + (E[1] - E[0]) / 2
# name: (Zeitlimit in Kerzen, Signal-Ausstieg, Stop in sigma, Trail in sigma, Trail aktiv ab Gewinn in sigma, Break-even ab Gewinn in sigma)
VARIANTEN = {"X0_zeit60": (12, False, 0, 0, 0, 0), "X1_zeit120": (24, False, 0, 0, 0, 0), "X2_zeit240": (48, False, 0, 0, 0, 0),
             "X3_signal": (48, True, 0, 0, 0, 0), "X4_stop2s": (48, False, 2.0, 0, 0, 0), "X5_trail1.5s": (48, False, 0, 1.5, 0, 0),
             "X6_trailtp": (48, False, 0, 0.5, 1.0, 0), "X7_breakeven": (48, False, 0, 0, 0, 1.0)}


def lauf(coin, var, bis, coins_slip=None):
    limit, signal, stop_s, trail_s, akt_s, be_s = VARIANTEN[var]
    k, z = S.z_wert(coin)
    k = k[k.index < bis]; z = z[: len(k)]
    o, h, l, c = (k[x].to_numpy() for x in ("open", "high", "low", "close"))
    r60 = k["close"].pct_change(12)
    sig = r60.rolling(288).std().shift(1).to_numpy()
    ein, aus, ri, preis = [], [], [], []
    frei = 0
    for i in np.flatnonzero(np.abs(z) >= 3.0):
        a = i + 1
        if a < frei or a + limit >= len(o) or not np.isfinite(sig[i]):
            continue
        r, e, s = np.sign(z[i]), o[a], sig[i]
        best, stop, b, px = e, (e * (1 - r * stop_s * s) if stop_s else None), a + limit, None
        for j in range(a, a + limit):
            if stop is not None and (l[j] <= stop if r > 0 else h[j] >= stop):
                b, px = j, (min(o[j], stop) if r > 0 else max(o[j], stop)); break
            best = max(best, h[j]) if r > 0 else min(best, l[j])
            gewinn = r * (best / e - 1)
            if trail_s and gewinn >= akt_s * s:
                neu = best * (1 - r * trail_s * s)
                stop = neu if stop is None else (max(stop, neu) if r > 0 else min(stop, neu))
            if be_s and gewinn >= be_s * s:
                stop = e if stop is None else (max(stop, e) if r > 0 else min(stop, e))
            if signal and z[j] * r < 1.0:
                b = j + 1; break
        ein.append(a); aus.append(b); ri.append(r); preis.append(px); frei = b + (1 if px is not None else 0)
    t = K.trades(coin, k, np.array(ein, int), np.array(aus, int), np.array(ri, float), K.lesen("funding", coin))
    px = np.array([np.nan if p is None else p for p in preis])[: len(t)]
    g = np.isfinite(px)
    t.loc[g, "roh"] = (t["richtung"].to_numpy() * (px / o[np.array(ein)[: len(t)]] - 1) * 1e4)[g]
    t["stop"] = g
    A, B, r = np.array(ein)[: len(t)], np.array(aus)[: len(t)], t["richtung"].to_numpy()
    t["schlimmst"] = [((l[x:y + 1].min() if s2 > 0 else h[x:y + 1].max()) / o[x] - 1) * s2 * 1e4 for x, y, s2 in zip(A, B, r)]
    ok = (B + 1 < len(o))                                # Stress: Ein- und Ausstieg je eine Kerze später
    t["roh_spaeter"] = np.where(g, t["roh"], np.where(ok, r * (o[np.minimum(B + 1, len(o) - 1)] / o[np.minimum(A + 1, len(o) - 1)] - 1) * 1e4, np.nan))
    return t


def alle(var, bis=E[1], coins=COINS):
    return K.netto(pd.concat([lauf(c, var, bis) for c in coins], ignore_index=True), K.slippage_bp(coins))


if __name__ == "__main__":
    tage = pd.date_range(E[0], E[1] - pd.Timedelta(days=1), freq="D")
    erg, reihen = {}, {}
    for var in VARIANTEN:
        t = alle(var); t = t[(t["ein"] >= E[0]) & (t["ein"] < E[1])]
        kz = K.kennzahlen(t)
        tag = konto.tagesreihe(t, "n85", *E, len(COINS))
        erg[var] = {"gesamt": kz, "h1_n85": K.kennzahlen(t, E[0], MITTE)["n85"], "h2_n85": K.kennzahlen(t, MITTE, E[1])["n85"],
                    "konto": konto.kennzahlen(tag), "stop_anteil": round(float(t["stop"].mean()), 3)}
        reihen[var] = tag
        print(K.zeile(var, kz), f"| H1/H2 {erg[var]['h1_n85']}/{erg[var]['h2_n85']} | Jahr {erg[var]['konto']['ertrag_jahr_pct']} % Sharpe {erg[var]['konto']['sharpe']} "
              f"Rückgang {erg[var]['konto']['rueckgang_pct_startkapital']} % | Stops {erg[var]['stop_anteil']}", flush=True)
    basis = reihen["X0_zeit60"].to_numpy()
    diff = np.column_stack([reihen[v].to_numpy() - basis for v in VARIANTEN if v != "X0_zeit60"])
    mittel, schwelle, p = reality_check(diff, ziehungen=3000, block=10, seed=7)
    namen = [v for v in VARIANTEN if v != "X0_zeit60"]
    beste = namen[int(np.argmax(mittel))]
    ok = p <= 0.10 and erg[beste]["h1_n85"] > 0 and erg[beste]["h2_n85"] > 0
    print(f"\nBeste gegen Basis: {beste}, Vorsprung {mittel.max()*365*100:.1f} Punkte pro Jahr, Zufallsschwelle {schwelle*365*100:.1f}, p = {p:.3f} → "
          + ("Mutation geht in die Validierung" if ok else "Basis bleibt"))
    K.speichern("e10_ausstiege", {"zeitraum": "Entwicklung", "ergebnis": erg, "beste": beste, "p": p, "mutation_angenommen": bool(ok)}, start)
