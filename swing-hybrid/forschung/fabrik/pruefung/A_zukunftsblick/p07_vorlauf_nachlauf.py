"""Datengetriebene Gegenprobe über den ganzen Zeitraum (Kerzen < I_ENDE, alle Coins): Hängt eine Reihe stärker mit der
VERGANGENEN/laufenden oder mit der KOMMENDEN Kursbewegung zusammen? Eine in die Zukunft verrutschte Reihe würde sich hier verraten.
"""
import sys
sys.path.insert(0, 'forschung')
import numpy as np, pandas as pd
from fabrik import daten as D, lauf as L, signale as S

I = L.I_ENDE
lad = lambda n, j: np.asarray(np.load(D.SPEICHER / f"{n}.npy", mmap_mode="r")[j, :I]).astype(np.float64)


def korr(a, b):
    m = np.isfinite(a) & np.isfinite(b)
    return float(np.corrcoef(a[m], b[m])[0, 1]) if m.sum() > 100 else float("nan")


minute = D.RASTER[:I].minute.to_numpy()
zeilen = []
for j, coin in enumerate(D.COINS):
    c, o = lad("c", j), lad("o", j)
    r = np.full(I, np.nan); r[1:] = c[1:] / c[:-1] - 1                        # Rendite der Kerze i
    r_next = np.full(I, np.nan); r_next[:-1] = r[1:]                          # Rendite der Kerze i+1
    vor_h = np.full(I, np.nan); vor_h[13:] = c[12:-1] / c[:-13] - 1           # Stunde VOR der Kerze i: Schluss i-13 -> Schluss i-1
    nach_h = np.full(I, np.nan); nach_h[1:-11] = c[12:] / c[:-12][0:len(c[12:])] - 1 if False else np.nan
    nach_h = np.full(I, np.nan); nach_h[1:I - 11] = c[12:I] / c[0:I - 12] - 1  # Stunde AB der Kerze i: Schluss i-1 -> Schluss i+11
    voll = minute == 0
    tk = lad("taker_log", j)
    oi = lad("oi", j); doi = np.full(I, np.nan); doi[12:] = np.abs(np.log(oi[12:] / oi[:-12]))
    kl = lad("konten_ls", j); dkl = np.full(I, np.nan); dkl[12:] = np.log(kl[12:] / kl[:-12])
    p = lad("prem", j); dp = np.full(I, np.nan); dp[1:] = p[1:] - p[:-1]
    b1, a1 = lad("b1", j), lad("a1", j); u = (b1 - a1) / (b1 + a1); du = np.full(I, np.nan); du[1:] = u[1:] - u[:-1]
    tq, tqv = lad("tq", j), lad("tqv", j); kd = np.where(tqv > 0, (2 * tq - tqv) / np.where(tqv > 0, tqv, 1), np.nan)
    zeilen.append(dict(coin=coin,
        taker_vorstunde=korr(tk[voll], vor_h[voll]), taker_folgestunde=korr(tk[voll], nach_h[voll]),
        oi_vorstunde=korr(doi[voll], np.abs(vor_h[voll])), oi_folgestunde=korr(doi[voll], np.abs(nach_h[voll])),
        konten_vorstunde=korr(dkl[voll], vor_h[voll]), konten_folgestunde=korr(dkl[voll], nach_h[voll]),
        prem_gleiche=korr(dp, r), prem_naechste=korr(dp, r_next),
        tiefe_gleiche=korr(du, r), tiefe_naechste=korr(du, r_next),
        kaufdruck_gleiche=korr(kd, r), kaufdruck_naechste=korr(kd, r_next)))
t = pd.DataFrame(zeilen).set_index("coin").round(3)
print("Korrelation je Coin (vor = vergangene Stunde / gleiche Kerze, nach = kommende Stunde / nächste Kerze):")
print(t.to_string())
print("\nMittel über Coins:"); print(t.mean().round(3).to_string())

print("\nAlle 63 normierten Signale: Korrelation Signal[i] mit der Rendite der NÄCHSTEN Kerze (Eröffnung i+1 -> Eröffnung i+2) und der GLEICHEN Kerze")
sig = np.load(D.SPEICHER / "signale.npy", mmap_mode="r")
erg = []
for j in (0, 2, 5, 8):
    o, c = lad("o", j), lad("c", j)
    naechste = np.full(I, np.nan); naechste[:-2] = o[2:] / o[1:-1] - 1
    gleiche = np.full(I, np.nan); gleiche[1:] = c[1:] / c[:-1] - 1
    for i, name in enumerate(S.NAMEN):
        w = np.asarray(sig[i, j, L.I_T:I], dtype=np.float64)
        w = np.clip(w, -10, 10)
        erg.append((name, D.COINS[j], korr(w, naechste[L.I_T:]), korr(w, gleiche[L.I_T:])))
e = pd.DataFrame(erg, columns=["signal", "coin", "k_naechste", "k_gleiche"])
print("größte |Korrelation| mit der nächsten Kerze:"); print(e.reindex(e["k_naechste"].abs().sort_values(ascending=False).index).head(8).round(4).to_string(index=False))
print("zum Vergleich größte |Korrelation| mit der gleichen Kerze:"); print(e.reindex(e["k_gleiche"].abs().sort_values(ascending=False).index).head(5).round(4).to_string(index=False))
print(f"Median |Korrelation| nächste Kerze {e['k_naechste'].abs().median():.4f}; Anzahl mit |Korrelation| > 0,05: {int((e['k_naechste'].abs() > 0.05).sum())} von {len(e)}")
