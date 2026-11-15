"""V-QD-03: unabhaengige Nachrechnung des Kandidaten OHNE hybrid.engine2 / hybrid.research / hybrid.runner.

Liest nur die Parquet-Kerzen und das Funding (nur lesend), rechnet den 14-Tage-Trend mit eigener Schleife
und zerlegt das Ergebnis in: vor Gebuehren (G, inkl. Funding und Slippage), Gebuehr (F), Rebate (R), Netto.
Schreibt nichts ins Repo; Ausgabe nur auf stdout.
"""
import sys
import numpy as np
import pandas as pd

DATA = "/home/user/OdinGate-Botv134/swing-hybrid/data"
COINS = ["BTC", "ETH", "SOL", "XRP", "DOT", "DOGE", "ADA", "LINK", "AVAX", "LTC"]
START, ENDE = "2021-08-15 00:00", "2026-10-24 00:00"
D1_ENDE, SPLIT = "2023-07-01", "2025-04-01"
TAKER = 0.0008
L = 336


def slippage_yubit(faktor=2.0, boden=0.00005):
    d = pd.read_csv(DATA + "/processed/yubit_spannen_stichprobe.csv")
    d["halb"] = (d["brief"] - d["geld"]) / (d["brief"] + d["geld"])
    mittel = d.groupby("symbol")["halb"].mean()
    return np.array([max(boden, faktor * float(mittel[c + "USDT"])) for c in COINS])


def coin_lauf(coin, slip, S):
    """Gibt je 5-Minuten-Kerze zurueck: Brutto-Konto (Kasse + Position*Close), kumuliertes Volumen, kumuliertes Funding."""
    df = pd.read_parquet(DATA + f"/candles/5m/{coin}USDT.parquet")
    df.index = df.index.astype("datetime64[ns]")
    df = df[~df.index.duplicated()].sort_index()
    idx = pd.date_range(START, ENDE, freq="5min", inclusive="left")
    k = df.reindex(idx)
    n_luecke = int(k["close"].isna().sum())
    close = k["close"].ffill().bfill()
    opn = k["open"].where(k["close"].notna(), close)
    # Stundenschluss aus den Rohdaten (auch vor START, damit das Signal am ersten Tag schon steht)
    h_close = df["close"].resample("1h").last().dropna()
    sig = np.sign(h_close / h_close.shift(L) - 1).fillna(0.0)
    sig.index = sig.index + pd.Timedelta(hours=1)          # bekannt erst bei Stundenschluss
    ziel = sig.reindex(idx.union(sig.index)).ffill().reindex(idx).fillna(0.0).to_numpy()
    fr = pd.read_parquet(DATA + f"/candles/funding/{coin}USDT.parquet")["rate"]
    fr.index = fr.index.astype("datetime64[ns]").floor("5min")
    fund = fr[~fr.index.duplicated()].reindex(idx).fillna(0.0).to_numpy()

    o = opn.to_numpy(); c = close.to_numpy(); T = len(idx)
    kasse = 0.0; pos = 0.0; vol = 0.0; fu = 0.0; gehalten = 0.0; n_order = 0
    brutto = np.empty(T); VOL = np.empty(T); FU = np.empty(T)
    for t in range(T):
        tg = 0.0 if t == T - 1 else ziel[t]
        # Funding auf die Position VOR einer Order dieser Kerze
        if fund[t] != 0.0 and pos != 0.0:
            fu -= pos * o[t] * fund[t]
        if t > 0 and tg != gehalten:
            if t == T - 1:
                q = -pos
            else:
                q = -pos + tg * S / o[t]
            if q != 0.0:
                px = o[t] * (1.0 + (1.0 if q > 0 else -1.0) * slip)
                kasse -= q * px; pos += q; vol += abs(q) * px; n_order += 1
                if abs(pos) < 1e-15:
                    pos = 0.0
            gehalten = tg
        brutto[t] = kasse + pos * c[t]; VOL[t] = vol; FU[t] = fu
    return idx, brutto, VOL, FU, n_order, n_luecke


def tageswerte(idx, x):
    s = pd.Series(x, index=idx)
    return s.groupby(idx.normalize()).last()


def auswertung(name, slip_feld, hebel=1.0):
    S = hebel / len(COINS)
    G = V = FUN = None
    orders = 0
    for j, coin in enumerate(COINS):
        idx, b, v, f, n, nl = coin_lauf(coin, float(slip_feld[j]), S)
        G = b if G is None else G + b
        V = v if V is None else V + v
        FUN = f if FUN is None else FUN + f
        orders += n
    g_tag = tageswerte(idx, G + FUN)       # vor Gebuehren, inkl. Funding (wie rendite_brutto im Repo)
    v_tag = tageswerte(idx, V)
    fu_tag = tageswerte(idx, FUN)
    d_g = g_tag.diff().fillna(g_tag.iloc[0])
    d_v = v_tag.diff().fillna(v_tag.iloc[0])
    d_fu = fu_tag.diff().fillna(fu_tag.iloc[0])
    fen = {"D1": (None, D1_ENDE), "D2": (D1_ENDE, SPLIT), "Entwicklung": (None, SPLIT), "Pruefung": (SPLIT, None), "Gesamt": (None, None)}
    zeilen = {}
    for f, (a, b) in fen.items():
        m = np.ones(len(d_g), bool)
        if a: m &= d_g.index >= pd.Timestamp(a)
        if b: m &= d_g.index < pd.Timestamp(b)
        g, v = d_g[m], d_v[m]
        fee = TAKER * v
        ohne = g - fee
        mit = g - 0.15 * fee
        tage = int(m.sum())
        sh = lambda x: float(x.mean() / x.std() * np.sqrt(365))
        Gs, Fs = float(g.sum()), float(fee.sum())
        zeilen[f] = {"tage": tage, "G_vor_Gebuehr": Gs, "davon_Funding": float(d_fu[m].sum()), "F_Gebuehr": Fs, "R_Rebate85": 0.85 * Fs,
                     "N_mit_Rebate": float(mit.sum()), "N_ohne_Rebate": float(ohne.sum()),
                     "jahr_mit": float(mit.sum()) / tage * 365, "jahr_ohne": float(ohne.sum()) / tage * 365,
                     "sharpe_mit": sh(mit), "sharpe_ohne": sh(ohne),
                     "t_mit": sh(mit) * np.sqrt(tage / 365), "t_ohne": sh(ohne) * np.sqrt(tage / 365),
                     "umsatz_je_tag": float(v.sum()) / tage,
                     "rebate_satz_fuer_null": (1.0 - Gs / Fs) if Fs > 0 else float("nan")}
    print(f"\n## {name}  (Orders gesamt: {orders})")
    print(pd.DataFrame(zeilen).T.round(4).to_string())
    return zeilen, (d_g, d_v)


if __name__ == "__main__":
    K = slippage_yubit()
    print("Slippage je Coin (bp), eigene Rechnung aus der Yubit-Stichprobe:", dict(zip(COINS, np.round(K * 1e4, 3))))
    z1, (dg, dv) = auswertung("Hebel 1, Yubit-Slippage (2 x halbe Spanne)", K)
    z2, _ = auswertung("Hebel 1, 5 bp Slippage", np.full(len(COINS), 0.0005))
    z0, _ = auswertung("Hebel 1, NULL Slippage (guenstigster denkbarer Fall, nur zur Einordnung)", np.zeros(len(COINS)))
    # Staffel Rebate-Satz im Pruefzeitraum
    m = dg.index >= pd.Timestamp(SPLIT)
    g, fee = dg[m], TAKER * dv[m]
    print("\n## Pruefzeitraum (ab 2025-04-01), Hebel 1, Yubit-Slippage: Netto je Rebate-Satz")
    for r in (0.0, 0.2, 0.3, 0.366, 0.4, 0.5, 0.6, 0.7, 0.85):
        x = g - (1 - r) * fee
        print(f"  Rebate {r:5.1%}: netto {x.sum():+.4f}  je Jahr {x.sum() / m.sum() * 365:+.4f}  Sharpe {x.mean() / x.std() * np.sqrt(365):+.3f}")
    # Rebate-Verzug: wie viel Gebuehr laeuft in 30 Tagen auf (in Anteilen des Kapitals, Hebel 1; Hebel 3 = mal 3)
    f30 = fee.rolling(30).sum()
    print(f"\n## Vorfinanzierung bei verzoegerter Rebate-Auszahlung (Pruefzeitraum, Hebel 1):"
          f" Gebuehr je 30 Tage im Mittel {f30.mean():.4f}, maximal {f30.max():.4f}; davon 85 % Rebate offen:"
          f" Mittel {0.85 * f30.mean():.4f}, max {0.85 * f30.max():.4f} (bei Hebel 3 mal 3)")
    # Moving-Block-Bootstrap fuer den Pruefzeitraum ohne Rebate (nur Einordnung der Unsicherheit)
    rng = np.random.default_rng(20261115)
    x = (g - fee).to_numpy(); n = len(x); B = 20
    sums = []
    for _ in range(5000):
        starts = rng.integers(0, n - B + 1, size=n // B + 1)
        s = np.concatenate([x[a:a + B] for a in starts])[:n]
        sums.append(s.sum())
    sums = np.array(sums)
    print(f"\n## Block-Bootstrap (Bloecke 20 Tage, 5000 Zuege) Pruefzeitraum ohne Rebate: Summe {x.sum():+.4f},"
          f" 5%/50%/95%-Quantil {np.quantile(sums, 0.05):+.3f} / {np.quantile(sums, 0.5):+.3f} / {np.quantile(sums, 0.95):+.3f},"
          f" Anteil > 0: {np.mean(sums > 0):.1%}")
    y = (g - 0.15 * fee).to_numpy()
    sums2 = []
    for _ in range(5000):
        starts = rng.integers(0, n - B + 1, size=n // B + 1)
        s = np.concatenate([y[a:a + B] for a in starts])[:n]
        sums2.append(s.sum())
    sums2 = np.array(sums2)
    print(f"## Block-Bootstrap Pruefzeitraum MIT Rebate: Summe {y.sum():+.4f},"
          f" 5%/50%/95%-Quantil {np.quantile(sums2, 0.05):+.3f} / {np.quantile(sums2, 0.5):+.3f} / {np.quantile(sums2, 0.95):+.3f},"
          f" Anteil > 0: {np.mean(sums2 > 0):.1%}")
