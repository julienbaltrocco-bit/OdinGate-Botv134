"""Runde 12: Statistical Arbitrage über Coin-Paare mit Z-Score (Stundenkerzen).

Für jedes Paar (i, j) laufend über W Stunden: Korrelation der Renditen, Hedge-Verhältnis beta aus der Regression von
log(P_i) auf log(P_j), Spread s = log(P_i) - beta*log(P_j) und dessen Z-Score. Alles nur aus Daten bis zur aktuellen
Kerze; gehandelt wird zum Open der Folgekerze.
"""
import numpy as np
from numba import njit


@njit(cache=True)
def simulate(o, c, fund, sw, W, z_ein, z_aus, z_stop, rho_min, max_halten, K, coin_max, kosten, filter_swing):
    """o, c: Open/Schluss je Stunde [Zeit, Coin]; fund: Funding-Rate je Stunde; sw: Swing-Gewicht je Stunde (für den Filter).

    kosten: je Order als Anteil des Ordervolumens, ein Wert je Coin.
    Rückgabe: Stundenreihen (Kursgewinn kumuliert, Kosten kumuliert, Funding kumuliert, Einsatz), Trades, Zähler.
    Einheiten: Topf = 1. Je Paar Einsatz 1/K (Long- und Short-Seite zusammen).
    """
    T, N = c.shape
    lp = np.log(c)
    for i in range(N):                                   # auf den Startkurs beziehen: kleinere Zahlen, stabilere Summen
        lp[:, i] -= lp[0, i]
    ret = np.zeros((T, N))
    for t in range(1, T):
        for i in range(N):
            ret[t, i] = lp[t, i] - lp[t - 1, i]
    P = N * (N - 1) // 2
    pi = np.empty(P, np.int64); pj = np.empty(P, np.int64)
    k = 0
    for i in range(N):
        for j in range(i + 1, N):
            pi[k] = i; pj[k] = j; k += 1
    # gleitende Summen
    Sa = np.zeros(N); Saa = np.zeros(N); Ra = np.zeros(N); Raa = np.zeros(N)
    Sab = np.zeros(P); Rab = np.zeros(P)
    # Zustand je Paar
    offen = np.zeros(P, np.bool_); beta_e = np.zeros(P); richt = np.zeros(P); qi = np.zeros(P); qj = np.zeros(P)
    ein_t = np.zeros(P, np.int64); ein_pi = np.zeros(P); ein_pj = np.zeros(P); gesperrt_bis = np.zeros(P, np.int64)
    auftrag = np.zeros(P, np.int64)                     # 0 nichts, 1 eröffnen, 2 schließen (für die Folgekerze)
    grund = np.zeros(P, np.int64); z_merk = np.zeros(P); beta_merk = np.zeros(P)
    legs = np.zeros(N, np.int64)
    kurs_kum = np.zeros(T); kost_kum = np.zeros(T); fund_kum = np.zeros(T); einsatz = np.zeros(T); vol_kum = np.zeros(T)
    trades = np.zeros((400000, 7)); nt = 0
    real = 0.0; kost = 0.0; fu = 0.0; vol = 0.0
    n_offen = 0
    u = 1.0 / K
    kand_z = np.zeros(P); kand_p = np.zeros(P, np.int64)

    for t in range(T):
        # ---- 1) Aufträge aus der Vorkerze zum Open dieser Kerze ausführen ----
        for p in range(P):
            if auftrag[p] == 2 and offen[p]:
                i, j = pi[p], pj[p]
                g = qi[p] * (o[t, i] - ein_pi[p]) + qj[p] * (o[t, j] - ein_pj[p])
                v = abs(qi[p]) * o[t, i] + abs(qj[p]) * o[t, j]
                real += g
                kost += abs(qi[p]) * o[t, i] * kosten[i] + abs(qj[p]) * o[t, j] * kosten[j]
                vol += v
                if nt < trades.shape[0]:
                    trades[nt, 0] = p; trades[nt, 1] = ein_t[p]; trades[nt, 2] = t; trades[nt, 3] = g
                    trades[nt, 4] = grund[p]; trades[nt, 5] = z_merk[p]; trades[nt, 6] = beta_e[p]
                nt += 1
                offen[p] = False; qi[p] = 0.0; qj[p] = 0.0
                legs[i] -= 1; legs[j] -= 1; n_offen -= 1
            auftrag[p] = 0 if auftrag[p] == 2 else auftrag[p]
        for idx in range(P):                              # Eröffnungen in der Reihenfolge der Signalstärke
            p = kand_p[idx]
            if auftrag[p] != 1:
                continue
            auftrag[p] = 0
            i, j = pi[p], pj[p]
            if offen[p] or n_offen >= K or legs[i] >= coin_max or legs[j] >= coin_max:
                continue
            b = beta_merk[p]
            d = -1.0 if z_merk[p] > 0 else 1.0            # Spread zu hoch: i short, j long
            ni = u / (1.0 + b); nj = u * b / (1.0 + b)    # Einsatz je Seite, nach beta gewichtet
            qi[p] = d * ni / o[t, i]; qj[p] = -d * nj / o[t, j]
            ein_pi[p] = o[t, i]; ein_pj[p] = o[t, j]; ein_t[p] = t; beta_e[p] = b; richt[p] = d
            kost += ni * kosten[i] + nj * kosten[j]; vol += ni + nj
            offen[p] = True; legs[i] += 1; legs[j] += 1; n_offen += 1

        # ---- 2) Funding auf offene Positionen ----
        for p in range(P):
            if offen[p]:
                i, j = pi[p], pj[p]
                fu -= qi[p] * c[t, i] * fund[t, i] + qj[p] * c[t, j] * fund[t, j]

        # ---- 3) gleitende Summen bis einschließlich Kerze t ----
        for i in range(N):
            Sa[i] += lp[t, i]; Saa[i] += lp[t, i] * lp[t, i]; Ra[i] += ret[t, i]; Raa[i] += ret[t, i] * ret[t, i]
            if t >= W:
                x = lp[t - W, i]; y = ret[t - W, i]
                Sa[i] -= x; Saa[i] -= x * x; Ra[i] -= y; Raa[i] -= y * y
        for p in range(P):
            i, j = pi[p], pj[p]
            Sab[p] += lp[t, i] * lp[t, j]; Rab[p] += ret[t, i] * ret[t, j]
            if t >= W:
                Sab[p] -= lp[t - W, i] * lp[t - W, j]; Rab[p] -= ret[t - W, i] * ret[t - W, j]

        # ---- 4) Signale am Schluss von Kerze t (Ausführung in Kerze t+1) ----
        nk = 0
        if t >= W and t < T - 1:
            for p in range(P):
                i, j = pi[p], pj[p]
                mi = Sa[i] / W; mj = Sa[j] / W
                vi = Saa[i] / W - mi * mi; vj = Saa[j] / W - mj * mj
                cij = Sab[p] / W - mi * mj
                if vi <= 1e-14 or vj <= 1e-14:
                    continue
                if offen[p]:
                    b = beta_e[p]
                    var = vi + b * b * vj - 2.0 * b * cij
                    if var <= 1e-14:
                        continue
                    z = (lp[t, i] - b * lp[t, j] - (mi - b * mj)) / np.sqrt(var)
                    g = 0
                    if abs(z) >= z_stop:
                        g = 2
                    elif abs(z) <= z_aus or z * (-richt[p]) < 0.0:   # zurück am Mittel oder darüber hinaus
                        g = 1
                    elif t - ein_t[p] >= max_halten:
                        g = 3
                    if g > 0:
                        auftrag[p] = 2; grund[p] = g
                        if g == 2:
                            gesperrt_bis[p] = t + W // 4
                else:
                    if t < gesperrt_bis[p]:
                        continue
                    b = cij / vj
                    if b < 0.5 or b > 2.0:
                        continue
                    ri = Ra[i] / W; rj = Ra[j] / W
                    rvi = Raa[i] / W - ri * ri; rvj = Raa[j] / W - rj * rj
                    if rvi <= 0.0 or rvj <= 0.0:
                        continue
                    rho = (Rab[p] / W - ri * rj) / np.sqrt(rvi * rvj)
                    var = vi + b * b * vj - 2.0 * b * cij
                    if rho < rho_min or var <= 1e-14:
                        continue
                    z = (lp[t, i] - b * lp[t, j] - (mi - b * mj)) / np.sqrt(var)
                    if abs(z) >= z_ein and abs(z) < z_stop:
                        d = -1.0 if z > 0 else 1.0
                        if filter_swing and (sw[t, i] * d < 0.0 or sw[t, j] * (-d) < 0.0):
                            continue                              # eine Seite liefe gegen den Swing
                        auftrag[p] = 1; z_merk[p] = z; beta_merk[p] = b
                        kand_z[nk] = -abs(z); kand_p[nk] = p; nk += 1
        if nk > 1:
            reihen = np.argsort(kand_z[:nk])
            tmp = kand_p[:nk].copy()
            for a in range(nk):
                kand_p[a] = tmp[reihen[a]]
        # Ältere Einträge in kand_p lösen in Schritt 1 nichts aus: `auftrag` steht nur bei Kandidaten dieser Kerze auf 1.

        # ---- 5) Stand am Kerzenschluss ----
        mtm = 0.0; brutto_einsatz = 0.0
        for p in range(P):
            if offen[p]:
                i, j = pi[p], pj[p]
                mtm += qi[p] * (c[t, i] - ein_pi[p]) + qj[p] * (c[t, j] - ein_pj[p])
                brutto_einsatz += abs(qi[p]) * c[t, i] + abs(qj[p]) * c[t, j]
        kurs_kum[t] = real + mtm; kost_kum[t] = kost; fund_kum[t] = fu; einsatz[t] = brutto_einsatz; vol_kum[t] = vol

    return kurs_kum, kost_kum, fund_kum, einsatz, vol_kum, trades[: min(nt, trades.shape[0])], pi, pj


# --------------------------------------------------------------------- Hüllen ----
def stundenfelder(m):
    """Stundenwerte aus dem 5-Minuten-Markt: Open, Schluss, Funding-Summe je Stunde. [Zeit, Coin]"""
    import pandas as pd
    n = (m.c.shape[1] // 12) * 12
    o = np.ascontiguousarray(m.o[:, :n:12].T)
    c = np.ascontiguousarray(m.c[:, 11:n:12].T)
    f = np.ascontiguousarray(m.fund[:, :n].reshape(len(m.coins), -1, 12).sum(axis=2).T)
    return o, c, f, pd.DatetimeIndex(m.index[:n:12])


def lauf(m, W, z_ein, kosten, sw=None, filter_swing=False, z_aus=0.5, z_stop=4.0, rho_min=0.7, K=10, coin_max=3):
    """Ein Lauf. Gibt Tagesreihen (Kursgewinn, Kosten, Funding, Umsatz, Einsatz) und die Trade-Liste zurück."""
    import pandas as pd
    o, c, f, idx = stundenfelder(m)
    kosten = np.full(len(m.coins), float(kosten)) if np.isscalar(kosten) else np.ascontiguousarray(kosten, dtype=np.float64)
    sw = np.zeros_like(c) if sw is None else np.ascontiguousarray(sw, dtype=np.float64)
    kurs, kost, fu, einsatz, vol, tr, pi, pj = simulate(o, c, f, sw, int(W), float(z_ein), z_aus, z_stop, rho_min, int(W) // 2,
                                                        int(K), int(coin_max), kosten, bool(filter_swing))
    h = pd.DataFrame({"kurs": kurs, "kosten": kost, "funding": fu, "umsatz": vol}, index=idx)
    tag = h.groupby(idx.normalize()).last().diff().fillna(h.groupby(idx.normalize()).last().iloc[0] * 0 + h.groupby(idx.normalize()).last().iloc[0])
    tag["einsatz"] = pd.Series(einsatz, index=idx).groupby(idx.normalize()).mean()
    tag["brutto"] = tag["kurs"] + tag["funding"]
    tag["netto"] = tag["brutto"] - tag["kosten"]
    t = pd.DataFrame(tr, columns=["paar", "ein", "aus", "gewinn", "grund", "z", "beta"])
    t["coin_i"] = [m.coins[pi[int(p)]] for p in t["paar"]]
    t["coin_j"] = [m.coins[pj[int(p)]] for p in t["paar"]]
    t["ein_zeit"] = idx[t["ein"].astype(int)]
    t["stunden"] = t["aus"] - t["ein"]
    t["grund"] = t["grund"].map({1.0: "ziel", 2.0: "stop", 3.0: "zeit"})
    return tag, t


def kennzahlen(tag, von=None, bis=None, spalte="netto"):
    import pandas as pd
    x = tag
    if von is not None:
        x = x[x.index >= pd.Timestamp(von)]
    if bis is not None:
        x = x[x.index < pd.Timestamp(bis)]
    n = x[spalte]
    konto = 1.0 + n.cumsum()
    spitze = np.maximum.accumulate(np.maximum(konto.to_numpy(), 1.0))
    return {"G": float(x["brutto"].sum()), "N": float(n.sum()), "kosten": float(x["kosten"].sum()), "funding": float(x["funding"].sum()),
            "dd": float(((spitze - konto.to_numpy()) / spitze).max()) if len(x) else 0.0,
            "sharpe": float(n.mean() / n.std() * np.sqrt(365)) if n.std() > 0 else 0.0,
            "jahr_N": float(n.mean() * 365), "umsatz_tag": float(x["umsatz"].mean()), "einsatz": float(x["einsatz"].mean()), "tage": int(len(x))}
