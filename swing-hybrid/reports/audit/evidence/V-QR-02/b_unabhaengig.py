"""V-QR-02 (b): eigene Rechnung ohne src/hybrid (kein engine2, kein runner, kein research).
Liest nur die Rohkerzen (5 Minuten), das Funding und die Yubit-Stichprobe. Hebel 1, 10 Coins je 1/10 Kapital,
feste Stueckzahl je Position (Nominal 0,1 beim Einstieg), Wechsel zum Open der ersten 5-Minuten-Kerze nach Stundenschluss.
Aufruf (aus swing-hybrid/): .venv/bin/python -I -B -W ignore <dieses Skript>
"""
import numpy as np
import pandas as pd

COINS = ["BTC", "ETH", "SOL", "XRP", "DOT", "DOGE", "ADA", "LINK", "AVAX", "LTC"]
START, ENDE, SPLIT = pd.Timestamp("2021-08-15"), pd.Timestamp("2026-10-24"), pd.Timestamp("2025-04-01")
TAKER, L = 0.0008, 336
S = 1.0 / len(COINS)

sp = pd.read_csv("data/processed/yubit_spannen_stichprobe.csv")
sp["halb"] = (sp["brief"] - sp["geld"]) / (sp["brief"] + sp["geld"])
halb = sp.groupby("symbol")["halb"].mean()


def rechne(slip_fn):
    """Gibt je Fenster zurueck: G (vor Gebuehr, inkl. Slippage und Funding), Umsatz, Funding."""
    idx = pd.date_range(START, ENDE, freq="5min", inclusive="left")
    a = idx.searchsorted(SPLIT)
    tot = {f: dict(G=0.0, umsatz=0.0, funding=0.0, orders=0) for f in ("Entwicklung", "Pruefung")}
    tage_G = 0
    eq_all = np.zeros(len(idx)); vol_all = np.zeros(len(idx))
    for coin in COINS:
        k = pd.read_parquet(f"data/candles/5m/{coin}USDT.parquet")
        k.index = k.index.astype("datetime64[ns]")
        k = k[~k.index.duplicated()].sort_index()
        # Stundenschluss = Schluss der letzten vorhandenen 5-Minuten-Kerze der Stunde
        h = k["close"].resample("1h").last().dropna()
        sig = np.sign(h / h.shift(L) - 1).fillna(0.0)
        sig.index = sig.index + pd.Timedelta(hours=1)          # bekannt bei Stundenschluss
        ziel = sig.reindex(idx.union(sig.index)).ffill().reindex(idx).fillna(0.0).to_numpy()
        kk = k.reindex(idx)
        c = kk["close"].ffill().bfill().to_numpy()
        o = kk["open"].where(kk["close"].notna(), kk["close"].ffill().bfill()).to_numpy()
        fr = pd.read_parquet(f"data/candles/funding/{coin}USDT.parquet")["rate"]
        fr.index = fr.index.astype("datetime64[ns]").floor("5min")
        fund = fr[~fr.index.duplicated()].reindex(idx).fillna(0.0).to_numpy()
        slip = slip_fn(coin)
        n = len(idx)
        cash = 0.0; pos = 0.0; gehalten = 0.0; fu = 0.0; vol = 0.0
        cash_t = np.zeros(n); pos_t = np.zeros(n); fu_t = np.zeros(n); vol_t = np.zeros(n)
        wechsel = np.flatnonzero(np.diff(ziel, prepend=0.0) != 0.0)
        fund_i = np.flatnonzero(fund != 0.0)
        ereignisse = np.union1d(np.union1d(wechsel, fund_i), [n - 1])
        letzte = 0
        orders = 0
        for t in ereignisse:
            cash_t[letzte:t] = cash; pos_t[letzte:t] = pos; fu_t[letzte:t] = fu; vol_t[letzte:t] = vol
            if t == n - 1:                                      # Schlussabrechnung zum Open der letzten Kerze
                if pos != 0.0:
                    px = o[t] * (1.0 - np.sign(pos) * slip)
                    cash += pos * px; vol += abs(pos) * px; pos = 0.0; orders += 1
            else:
                if fund[t] != 0.0 and pos != 0.0:               # Funding auf den Bestand vor dem Wechsel
                    fu -= pos * o[t] * fund[t]
                if t > 0 and ziel[t] != gehalten:
                    neu = ziel[t] * S / o[t]
                    q = neu - pos
                    px = o[t] * (1.0 + np.sign(q) * slip)
                    cash -= q * px; vol += abs(q) * px; pos = neu; gehalten = ziel[t]; orders += 1
            letzte = t
        cash_t[letzte:] = cash; pos_t[letzte:] = pos; fu_t[letzte:] = fu; vol_t[letzte:] = vol
        eq = cash_t + pos_t * c + fu_t
        eq_all += eq; vol_all += vol_t
        for f, (x, y) in (("Entwicklung", (0, a)), ("Pruefung", (a, n))):
            b0 = eq[x - 1] if x > 0 else 0.0
            v0 = vol_t[x - 1] if x > 0 else 0.0
            f0 = fu_t[x - 1] if x > 0 else 0.0
            tot[f]["G"] += eq[y - 1] - b0
            tot[f]["umsatz"] += vol_t[y - 1] - v0
            tot[f]["funding"] += fu_t[y - 1] - f0
        tot["Pruefung"]["orders"] += orders
    tot["_tag"] = (eq_all, vol_all, idx, a)
    return tot


def bericht(name, tot):
    eq, vol, idx, a = tot["_tag"]
    for f in ("Entwicklung", "Pruefung"):
        G, V = tot[f]["G"], tot[f]["umsatz"]
        F = TAKER * V
        zeile = f"{name:10s} {f:11s} G={G:+.4f} Umsatz={V:8.2f} F={F:.4f} Funding={tot[f]['funding']:+.4f}"
        x, y = (0, a) if f == "Entwicklung" else (a, len(idx))
        for rb in (0.0, 0.5, 0.85):
            netto = eq - TAKER * (1 - rb) * vol
            tagend = pd.Series(netto, index=idx).resample("1D").last()
            tg = tagend.diff(); tg.iloc[0] = tagend.iloc[0]
            tg = tg[(tg.index >= idx[x].normalize()) & (tg.index <= idx[y - 1].normalize())]
            zeile += f" | Rebate {int(rb*100):2d} %: N={G - F * (1 - rb):+.4f} Sharpe={tg.mean() / tg.std() * np.sqrt(365):+.3f}"
        zeile += f" | Rebate fuer Null: {(F - G) / F * 100:.1f} %"
        print(zeile)


echt = lambda coin: max(0.00005, 2.0 * float(halb[coin + "USDT"]))
bericht("slip_echt", rechne(echt))
bericht("slip_0", rechne(lambda coin: 0.0))
bericht("slip_2x", rechne(lambda coin: 2 * echt(coin)))
bericht("slip_5bp", rechne(lambda coin: 0.0005))
bericht("slip_10bp", rechne(lambda coin: 0.001))
