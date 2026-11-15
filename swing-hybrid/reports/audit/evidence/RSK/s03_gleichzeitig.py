"""RSK 03: gleichzeitige Verluste aller Positionen, größte Bewegung eines Coins gegen die gehaltene Richtung (1 h / 24 h),
größte Gegenbewegung je Trade (für die Liquidationsrechnung bei isolierter Margin). Liest die Zwischenspeicher aus s01.
Alle Angaben für die durchlaufenden Läufe (Vorperiode, Hauptzeitraum); Fenster nach Datum getrennt."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import numpy as np
import pandas as pd
from numba import njit
from rsk_common import A, R, SCRATCH

OUT = {}
N = len(A)


@njit
def gegen_24h(o, h, l, pos, schritt, fenster):
    """Je Startkerze (alle `schritt` Kerzen) mit Position: größte Bewegung gegen die Richtung innerhalb `fenster` Kerzen,
    solange die Richtung unverändert gehalten wird. Bezug: Open der Startkerze. Gibt Feld (Start, Bewegung) zurück."""
    T = len(o)
    n = (T - 1) // schritt + 1
    out = np.zeros(n)
    for i in range(n):
        s = i * schritt
        d = 1.0 if pos[s] > 0 else (-1.0 if pos[s] < 0 else 0.0)
        if d == 0.0:
            continue
        ref = o[s]; worst = 0.0
        for t in range(s, min(T, s + fenster)):
            dt = 1.0 if pos[t] > 0 else (-1.0 if pos[t] < 0 else 0.0)
            if dt != d:
                # in der Kerze des Drehs wird zum Open geschlossen: nur das Open zählt noch
                x = (ref - o[t]) / ref if d > 0 else (o[t] - ref) / ref
                if x > worst:
                    worst = x
                break
            x = (ref - l[t]) / ref if d > 0 else (h[t] - ref) / ref
            if x > worst:
                worst = x
        out[i] = worst
    return out


@njit
def trades_mae(o, h, l, pos, slip):
    """Je Haltephase (konstante Richtung): Einstiegskerze, Ausstiegskerze, Richtung, Einstiegspreis, größte Gegenbewegung
    relativ zum Einstiegspreis (Hochs für Shorts, Tiefs für Longs, einschließlich Ausstiegs-Open), Ergebnis beim Ausstieg."""
    T = len(o)
    res = np.zeros((T // 2 + 2, 6)); k = 0
    d = 0.0; ein = 0; px = 0.0; worst = 0.0
    for t in range(T):
        dt = 1.0 if pos[t] > 0 else (-1.0 if pos[t] < 0 else 0.0)
        if dt != d:
            if d != 0.0:
                x = (px - o[t]) / px if d > 0 else (o[t] - px) / px
                if x > worst:
                    worst = x
                res[k, 0] = ein; res[k, 1] = t; res[k, 2] = d; res[k, 3] = px; res[k, 4] = worst
                res[k, 5] = d * (o[t] / px - 1.0)
                k += 1
            d = dt
            if d != 0.0:
                ein = t; px = o[t] * (1.0 + d * slip); worst = 0.0
        if d != 0.0:
            x = (px - l[t]) / px if d > 0 else (h[t] - px) / px
            if x > worst:
                worst = x
    return res[:k]


SLIP = R.yubit_kosten(A)[0]
zeilen = []
alle_trades = []
for name in ("vor", "haupt"):
    d = np.load(SCRATCH / f"lauf_{name}.npz")
    idx = pd.DatetimeIndex(d["index"])
    nc, pos, o, h, l, c = d["netto_coin"], d["pos"], d["o"], d["h"], d["l"], d["c"]
    T = len(idx)
    fenster = {"Vorperiode": (0, T)} if name == "vor" else {"Entwicklung": (0, int(idx.searchsorted(pd.Timestamp(R.SPLIT)))),
                                                             "Pruefzeitraum": (int(idx.searchsorted(pd.Timestamp(R.SPLIT))), T)}
    richtung = np.sign(pos)
    for fname, (a, b) in fenster.items():
        e = OUT[fname] = {}
        print(f"\n=== {fname} ({idx[a]} bis {idx[b - 1]}) ===")
        # ---- gleichzeitige Verluste: Stunden (ausgerichtet), Tage, rollierend 24 h im Stundenschritt ----
        for wname, n, schritt in (("1 Stunde (volle Stunden)", 12, 12), ("24 Stunden (rollierend, Stundenschritt)", 288, 12), ("Kalendertag", 288, 288)):
            st = np.arange(a, b - n, schritt)
            dn = nc[:, st + n] - nc[:, st]                               # Ergebnis je Coin im Fenster (Hebel 1, Anteil am Startkapital)
            offen = (richtung[:, st] != 0).sum(axis=0)
            verl = (dn < 0).sum(axis=0)
            summe = dn.sum(axis=0)
            alle10 = (offen == N) & (verl == N)
            ab8 = (offen == N) & (verl >= 8)
            i = int(summe.argmin())
            top = np.argsort(summe)[:5]
            k = {"fenster": int(len(st)), "anteil_alle_zehn_verlieren": float(alle10.mean()), "anteil_mind_acht_verlieren": float(ab8.mean()),
                 "groesster_verlust_h1": float(summe[i]), "groesster_verlust_zeit": str(idx[st[i]]), "verlierer_dabei": int(verl[i]),
                 "long_dabei": int((richtung[:, st[i]] > 0).sum()), "short_dabei": int((richtung[:, st[i]] < 0).sum()),
                 "groesster_verlust_alle_zehn_h1": float(summe[alle10].min()) if alle10.any() else None,
                 "top5": [{"start": str(idx[st[j]]), "h1": float(summe[j]), "h3": float(3 * summe[j]), "verlierer": int(verl[j]),
                           "long": int((richtung[:, st[j]] > 0).sum()), "short": int((richtung[:, st[j]] < 0).sum())} for j in top]}
            # Anteil des Gesamtverlusts aller Verlustfenster, der in Fenstern mit >= 8 Verlierern entsteht
            neg = summe < 0
            k["verlustanteil_aus_fenstern_mit_mind_acht_verlierern"] = float(summe[neg & (verl >= 8)].sum() / summe[neg].sum())
            e[wname] = k
            print(f"  {wname}: {k['fenster']} Fenster; alle zehn Positionen gleichzeitig im Verlust in {k['anteil_alle_zehn_verlieren']:.1%}, mindestens acht in {k['anteil_mind_acht_verlieren']:.1%} der Fenster; "
                  f"{k['verlustanteil_aus_fenstern_mit_mind_acht_verlierern']:.0%} aller Verluste entstehen in Fenstern mit mindestens acht Verlierern")
            for t5 in k["top5"]:
                print(f"      {t5['start'][:16]}: Hebel 1 {t5['h1']:+.1%}, Hebel 3 {t5['h3']:+.1%} des Startkapitals; {t5['verlierer']} von 10 im Verlust ({t5['long']} Long / {t5['short']} Short)")
        # ---- größte Bewegung eines einzelnen Coins gegen die gehaltene Richtung ----
        for wname, n in (("1 Stunde", 12), ("24 Stunden", 288)):
            best = []
            for j, coin in enumerate(A):
                g = gegen_24h(o[j, a:b], h[j, a:b], l[j, a:b], pos[j, a:b], 12, n)
                i = int(g.argmax())
                best.append({"coin": coin, "bewegung": float(g[i]), "start": str(idx[a + i * 12]), "richtung": "Long" if pos[j, a + i * 12] > 0 else "Short",
                             "q999": float(np.quantile(g[g > 0], 0.999)) if (g > 0).any() else 0.0})
            best.sort(key=lambda x: -x["bewegung"])
            e[f"gegenbewegung {wname}"] = best
            print(f"  Größte Bewegung gegen die gehaltene Richtung innerhalb {wname} (5-Minuten-Hochs/-Tiefs, solange die Richtung gehalten wird):")
            print("      " + "; ".join(f"{x['coin']} {x['bewegung']:.1%} ({x['richtung']}, ab {x['start'][:16]})" for x in best[:5]))
            print("      0,1 % der Startstunden schlimmer als: " + ", ".join(f"{x['coin']} {x['q999']:.1%}" for x in best))
            bestc = []
            for j, coin in enumerate(A):
                g = gegen_24h(o[j, a:b], c[j, a:b], c[j, a:b], pos[j, a:b], 12, n)
                i = int(g.argmax())
                bestc.append({"coin": coin, "bewegung": float(g[i]), "start": str(idx[a + i * 12]), "richtung": "Long" if pos[j, a + i * 12] > 0 else "Short",
                              "q99": float(np.quantile(g[g > 0], 0.99)) if (g > 0).any() else 0.0, "q999": float(np.quantile(g[g > 0], 0.999)) if (g > 0).any() else 0.0})
            bestc.sort(key=lambda x: -x["bewegung"])
            e[f"gegenbewegung {wname} schlusskurse"] = bestc
            print(f"    dasselbe nur mit 5-Minuten-Schlusskursen (ohne Dochte):")
            print("      " + "; ".join(f"{x['coin']} {x['bewegung']:.1%} ({x['richtung']}, ab {x['start'][:16]})" for x in bestc))
            print("      1 % der Startstunden schlimmer als: " + ", ".join(f"{x['coin']} {x['q99']:.1%}" for x in bestc))
        # ---- größte Gegenbewegung je Trade ----
        for j, coin in enumerate(A):
            tr = trades_mae(o[j], h[j], l[j], pos[j], float(SLIP[j]))
            trc = trades_mae(o[j], c[j], c[j], pos[j], float(SLIP[j]))
            for r, rc in zip(tr, trc):
                if a <= r[0] < b:
                    alle_trades.append({"fenster": fname, "coin": coin, "ein": idx[int(r[0])], "aus": idx[int(r[1])], "richtung": int(r[2]),
                                        "einstieg": float(r[3]), "mae": float(r[4]), "mae_schluss": float(rc[4]), "ergebnis": float(r[5])})

t = pd.DataFrame(alle_trades)
t["stunden"] = (t["aus"] - t["ein"]).dt.total_seconds() / 3600
t.to_pickle(SCRATCH / "trades_mae.pkl")
print("\n=== Größte Gegenbewegung je Trade (Einstieg bis Dreh, relativ zum Einstiegspreis, 5-Minuten-Hochs/-Tiefs) ===")
OUT["trades"] = {}
for fname, g in list(t.groupby("fenster", sort=False)) + [("alle", t)]:
    jahre = (g["aus"].max() - g["ein"].min()).days / 365.25
    k = {"trades": int(len(g)), "jahre": float(jahre), "haltedauer_h_mittel": float(g["stunden"].mean()), "haltedauer_h_median": float(g["stunden"].median()),
         "mae_median": float(g["mae"].median()), "mae_p99": float(g["mae"].quantile(0.99)), "mae_max": float(g["mae"].max()),
         "ergebnis_schlechtestes": float(g["ergebnis"].min())}
    for sw in (0.03, 0.045, 0.05, 0.075, 0.095, 0.10, 0.175, 0.19, 0.195, 0.20, 0.308, 0.323, 0.328, 0.333, 0.5, 1.0):
        k[f"mae_ab_{sw}"] = int((g["mae"] >= sw).sum())
    OUT["trades"][fname] = k
    print(f"  {fname:13s}: {k['trades']} Trades in {jahre:.1f} Jahren, Haltedauer Mittel {k['haltedauer_h_mittel']:.0f} h / Median {k['haltedauer_h_median']:.0f} h; "
          f"Gegenbewegung Median {k['mae_median']:.1%}, 99-%-Quantil {k['mae_p99']:.1%}, Maximum {k['mae_max']:.1%}; schlechtestes Trade-Ergebnis {k['ergebnis_schlechtestes']:.1%}")
    print("      Trades mit Gegenbewegung ab: " + ", ".join(f"{sw:.1%}: {k[f'mae_ab_{sw}']}" for sw in (0.05, 0.10, 0.20, 0.308, 0.323, 0.328, 0.333, 0.5, 1.0)))
print("\n  Dasselbe nur mit 5-Minuten-Schlusskursen (ohne Dochte):")
for fname, g in list(t.groupby("fenster", sort=False)) + [("alle", t)]:
    k = OUT["trades"][fname]
    for sw in (0.05, 0.10, 0.20, 0.308, 0.323, 0.328, 0.333, 0.5):
        k[f"mae_schluss_ab_{sw}"] = int((g["mae_schluss"] >= sw).sum())
    k["mae_schluss_max"] = float(g["mae_schluss"].max())
    print(f"  {fname:13s}: Maximum {k['mae_schluss_max']:.1%}; Trades mit Gegenbewegung ab: " + ", ".join(f"{sw:.1%}: {k[f'mae_schluss_ab_{sw}']}" for sw in (0.05, 0.10, 0.20, 0.308, 0.323, 0.328, 0.333, 0.5)))
print("\n  Die 12 Trades mit der größten Gegenbewegung:")
for _, r in t.sort_values("mae", ascending=False).head(12).iterrows():
    print(f"      {r['coin']:5s} {'Long ' if r['richtung'] > 0 else 'Short'} {str(r['ein'])[:16]} bis {str(r['aus'])[:16]} ({r['stunden']:.0f} h): Gegenbewegung {r['mae']:.1%} (nur Schlusskurse {r['mae_schluss']:.1%}), Ergebnis beim Ausstieg {r['ergebnis']:+.1%} [{r['fenster']}]")
print("\n  Long gegen Short:")
for rn, g in t.groupby("richtung"):
    print(f"      {'Long ' if rn > 0 else 'Short'}: {len(g)} Trades, Gegenbewegung 99-%-Quantil {g['mae'].quantile(0.99):.1%}, Maximum {g['mae'].max():.1%}, ab 30,8 %: {(g['mae'] >= 0.308).sum()}, ab 20 %: {(g['mae'] >= 0.20).sum()}, ab 10 %: {(g['mae'] >= 0.10).sum()}")
(SCRATCH / "s03.json").write_text(json.dumps(OUT, indent=1, default=str))
