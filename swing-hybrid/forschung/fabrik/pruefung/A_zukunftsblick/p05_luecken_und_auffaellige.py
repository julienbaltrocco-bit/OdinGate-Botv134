"""Datenlücken im Speicher (nur Kerzen < I_ENDE) und Blick auf auffällig gute Kandidaten: Woher kommt das Ergebnis?

Fragen: (a) Wo liegen die Lücken, was steht dort im Speicher, wie verhalten sich Signale direkt danach?
        (b) Hängt das Ergebnis auffälliger Kandidaten an Trades rund um Lücken oder an wenigen Einzeltrades?
"""
import sqlite3, sys
sys.path.insert(0, 'forschung')
import numpy as np, pandas as pd
from fabrik import daten as D, lauf as L, kern as FK, signale as S, generator as G, evolution as E

I_ENDE = L.I_ENDE
L._init()
g = np.asarray(L._g["gueltig"][:, :I_ENDE])
print("##### (a) Lücken")
luecken = {}
for j, coin in enumerate(D.COINS):
    u = np.flatnonzero(~g[j])
    if len(u):
        bl = np.split(u, np.flatnonzero(np.diff(u) > 1) + 1)
        luecken[j] = [(int(b[0]), int(b[-1])) for b in bl]
        for b in bl:
            seg = "T" if b[0] < L.I_V1 else "V1"
            c = np.asarray(L._g["o"][j, b[0] - 1:b[-1] + 3])
            print(f"  {coin}: {len(b)} Kerzen {D.RASTER[b[0]]} bis {D.RASTER[b[-1]]} ({seg}); Kurs vor Lücke {c[0]:.4f}, erste Eröffnung danach {c[-2]:.4f} ({(c[-2] / c[0] - 1) * 100:+.1f} %)")
            for name in ("mom_3", "boll_144", "vwap_48", "ausbruch_48", "rsi_14"):
                w = np.asarray(L._g["signale"][S.NAMEN.index(name), j, b[-1] + 1:b[-1] + 289])
                print(f"     {name:<12} in den 288 Kerzen nach der Lücke: |Wert|>=3.5 an {int((np.abs(w) >= 3.5).sum())} Kerzen, max |Wert| {np.nanmax(np.abs(w)):.1f}, erste Werte {np.round(w[:3], 1).tolist()}")
print("  Coins ohne Lücke:", [c for j, c in enumerate(D.COINS) if j not in luecken])

print("\n##### (b) auffällige Kandidaten (gen1, hohe Netto-Ergebnisse je Trade bei kurzer Haltedauer)")
con = sqlite3.connect('file:data/fabrik/forschung.sqlite?mode=ro', uri=True); con.row_factory = sqlite3.Row
kand = con.execute("SELECT * FROM kandidaten WHERE gen='gen1' AND status IN ('stufe2','stufe3','final','verworfen_3') AND x IN ('h15','h60') ORDER BY n85_t DESC LIMIT 6").fetchall()
kand += con.execute("SELECT * FROM kandidaten WHERE gen='gen1' AND status IN ('stufe2','stufe3','final','verworfen_3') ORDER BY t85_t DESC LIMIT 4").fetchall()
AUSST = {**G.AUSSTIEGE, **E.NEUE_AUSSTIEGE}
for z in kand:
    a = {"si": S.NAMEN.index(z["signal"]), "signal": z["signal"], "th": z["th"], "r": z["r"], "f": z["f"], "k": z["k"]}
    t0, v0, _ = L.SEGMENTE["t" if z["braucht"] == "t" else "k"]
    i0 = L.I_T + t0 * 288
    halte, sl, tp, tr, ta, sx = AUSST[z["x"]]
    alle = []
    for j in G.MAERKTE[z["m"]]:
        if j == 0 and z["signal"].startswith(("btcfuehrt", "relstaerke", "korrbruch")):
            continue
        ein, wert = L.einstieg(a, j)
        aus = np.zeros((200000, 6))
        n = FK.trades_liste(L._g["o"][j], L._g["h"][j], L._g["l"][j], L._g["fcum"][j], ein, wert, L._g["sigma"][j], i0, I_ENDE, halte, sl, tp, tr, ta,
                            np.nan if sx is None else sx, float(np.asarray(L._g["slip_bp"])[j]) * 2.0, aus)
        t = pd.DataFrame(aus[:n, :4], columns=["a", "b", "d", "roh"]); t["j"] = j
        nah = np.zeros(n, bool)
        for (l0, l1) in luecken.get(j, []):
            nah |= (t["a"].to_numpy() >= l0 - 300) & (t["a"].to_numpy() <= l1 + 2016 + 300)       # in der Lücke oder bis 7 Tage danach
        t["luecke"] = nah
        # Sprung zwischen Signalkerzen-Schluss und Einstiegskurs
        ai = t["a"].to_numpy().astype(int)
        t["sprung_bp"] = (np.asarray(L._g["o"][j, :I_ENDE])[ai] / np.asarray(D.laden("c")[j, :I_ENDE])[ai - 1] - 1) * 1e4 * t["d"].to_numpy()   # nur Kerzen < I_ENDE
        alle.append(t)
    t = pd.concat(alle)
    t = t[(t["a"] - L.I_T) // 288 < v0]                                         # nur Training
    n85 = t["roh"] - L.KOSTEN85
    top = n85.sort_values(ascending=False)
    monat = pd.Series(n85.to_numpy(), index=D.RASTER[t["a"].to_numpy().astype(int)]).resample("MS").sum()
    print(f"\n  {z['id']} {z['signal']} th {z['th']} r {z['r']:+d} {z['f']} k{z['k']} {z['x']} {z['m']} | DB n_t {z['n_t']} n85_t {z['n85_t']} t {z['t85_t']} | nachgerechnet n {len(t)} n85 {n85.mean():.3f}")
    print(f"     Median {n85.median():.1f} bp, Gewinnquote {(n85 > 0).mean():.2f}; Anteil der Summe aus den besten 1 % der Trades: {top.head(max(1, len(top) // 100)).sum() / n85.sum():.2f}; ohne die besten 1 %: Mittel {top.iloc[max(1, len(top) // 100):].mean():.2f} bp")
    print(f"     Trades in/nach Lücken (bis 7 Tage): {int(t['luecke'].sum())}, deren Mittel {n85[t['luecke']].mean() if t['luecke'].any() else float('nan'):.1f} bp; Mittel ohne sie {n85[~t['luecke']].mean():.3f} bp")
    print(f"     stärkste Monate (Summe bp): {[(str(m.date())[:7], int(v)) for m, v in monat.sort_values(ascending=False).head(3).items()]} von gesamt {int(n85.sum())}; Monate positiv {int((monat > 0).sum())}/{int((monat != 0).sum())}")
    print(f"     Sprung Schluss Signalkerze -> Einstiegskurs (in Trade-Richtung, bp): Mittel {t['sprung_bp'].mean():+.2f}, |max| {t['sprung_bp'].abs().max():.1f}")
