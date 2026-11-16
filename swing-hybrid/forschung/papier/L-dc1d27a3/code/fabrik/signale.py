"""Signale und Filter der Fabrik. Jedes Signal ist eine Zahl je Coin und 5-Minuten-Kerze, bekannt am Schluss der Kerze.

Positiver Wert = spricht nach der Grundidee für steigende Kurse. Alle Signale (außer `fund`) werden durch ihre eigene
Schwankung der letzten 7 Tage geteilt (nur Vergangenheit), damit die Schwellen 1,5 / 2,5 / 3,5 vergleichbar sind.

  .venv/bin/python -I forschung/fabrik/signale.py      (rechnet alle Signale einmal und legt sie als Speicherabbild ab)
"""
import sys
from multiprocessing import Pool
from pathlib import Path

import numpy as np
import pandas as pd

F = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(F))
from fabrik import daten as D

W1, W7, W30 = 288, 2016, 8640            # 1 Tag, 7 Tage, 30 Tage in 5-Minuten-Kerzen

# (Name, Familie, Länge, braucht) – "braucht": k = nur Kerzen, d = Derivate-Daten, t = Orderbuch-Tiefe (ab 2023), x = BTC als Leitmarkt
SIGNALE = (
    [(f"mom_{L}", "Momentum", L, "k") for L in (3, 6, 12, 36, 72, 144, 288)]
    + [(f"ausbruch_{L}", "Momentum", L, "k") for L in (12, 48, 144, 288)]
    + [(f"beschl_{L}", "Momentum", L, "k") for L in (6, 12, 48)]
    + [(f"volmom_{L}", "Momentum", L, "k") for L in (3, 12, 48)]
    + [("mtf_12_144", "Momentum", 12, "k"), ("mtf_3_48", "Momentum", 3, "k")]
    + [(f"boll_{L}", "Mean Reversion", L, "k") for L in (12, 48, 144, 288)]
    + [(f"rsi_{L}", "Mean Reversion", L, "k") for L in (6, 14, 48)]
    + [(f"vwap_{L}", "Mean Reversion", L, "k") for L in (12, 48, 288)]
    + [("volspitze_1", "Volatilität", 1, "k"), ("volspitze_3", "Volatilität", 3, "k"), ("volenge", "Volatilität", 12, "k"), ("volweite", "Volatilität", 12, "k")]
    + [(f"btcfuehrt_{L}", "Cross-Asset", L, "x") for L in (1, 3, 12)]
    + [(f"relstaerke_{L}", "Cross-Asset", L, "x") for L in (12, 48, 288)]
    + [("ethbtc_48", "Cross-Asset", 48, "x"), ("ethbtc_288", "Cross-Asset", 288, "x"), ("korrbruch", "Cross-Asset", 48, "x")]
    + [("aufschlag", "Derivate", 288, "d"), ("aufschlag_d3", "Derivate", 3, "d"), ("aufschlag_d12", "Derivate", 12, "d"), ("fund", "Derivate", 96, "d")]
    + [("oi_kurs_1h", "Derivate", 12, "d"), ("oi_kurs_4h", "Derivate", 48, "d"), ("oi_abbau_1h", "Derivate", 12, "d"), ("oi_abbau_4h", "Derivate", 48, "d")]
    + [("konten_ls", "Derivate", 12, "d"), ("profis_gegen_konten", "Derivate", 12, "d"), ("taker_4h", "Derivate", 48, "d")]
    + [(f"tiefe_{k}", "Mikrostruktur", 288, "t") for k in (1, 3, 5)]
    + [("tiefe_d_1", "Mikrostruktur", 12, "t"), ("tiefe_d_5", "Mikrostruktur", 12, "t"), ("liq_entzug", "Mikrostruktur", 12, "t")]
    + [(f"kaufdruck_{L}", "Mikrostruktur", L, "k") for L in (1, 3, 12, 48)]
    # Generation 3 (16.11.2026, H10): wiederkehrende Tageszeit-Muster. Länge = Zeitfenster in Kerzen, zweite Zahl = Zahl der Vortage
    + [(f"tagzeit_{L}_{N}", "Saisonalität", L, "k") for L in (3, 12) for N in (7, 28)]
    + [(f"tagzeitrel_{L}_28", "Saisonalität", L, "k") for L in (3, 12)]
    # Generation 4 (16.11.2026, H16): Orderbuch-Tiefe 1 % aus dem letzten 30-Sekunden-Schnappschuss der Kerze statt aus dem Kerzenmittel
    + [("tiefe_letzt_1", "Mikrostruktur", 288, "t"), ("tiefe_frisch_1", "Mikrostruktur", 1, "t")]
)
NAMEN = [s[0] for s in SIGNALE]
FILTER = ["kein", "trend_mit", "trend_gegen", "vol_hoch", "vol_niedrig", "asien", "europa", "usa", "btc_auf", "btc_ab"]


def _roh(j: int) -> dict:
    """Alle Rohsignale eines Coins (pandas, nur rückwärts gerichtete Fenster)."""
    S = lambda name, k=j: pd.Series(np.asarray(D.laden(name)[k], dtype=np.float64))
    c, o, h, l, qv = S("c"), S("o"), S("h"), S("l"), S("qv")
    r1 = c.pct_change()
    s1 = r1.rolling(W1).std()
    mom = lambda L, x=c, s=s1: x.pct_change(L) / (s * np.sqrt(L))
    out = {}
    for L in (3, 6, 12, 36, 72, 144, 288):
        out[f"mom_{L}"] = mom(L)
    for L in (12, 48, 144, 288):
        pm, pn = h.rolling(L).max().shift(1), l.rolling(L).min().shift(1)
        out[f"ausbruch_{L}"] = ((c - pm).clip(lower=0) - (pn - c).clip(lower=0)) / (c * s1 * np.sqrt(L))
    for L in (6, 12, 48):
        out[f"beschl_{L}"] = mom(L) - mom(L).shift(L)
    for L in (3, 12, 48):
        out[f"volmom_{L}"] = mom(L) * (qv.rolling(L).mean() / qv.rolling(W1).mean()).clip(upper=4)
    for a, b in ((12, 144), (3, 48)):
        out[f"mtf_{a}_{b}"] = mom(a).where(np.sign(mom(a)) == np.sign(mom(b)), 0.0)
    for L in (12, 48, 144, 288):
        out[f"boll_{L}"] = (c - c.rolling(L).mean()) / c.rolling(L).std()
    d = c.diff()
    for L in (6, 14, 48):
        auf, ab = d.clip(lower=0).ewm(alpha=1 / L, adjust=False).mean(), (-d.clip(upper=0)).ewm(alpha=1 / L, adjust=False).mean()
        out[f"rsi_{L}"] = (100 - 100 / (1 + auf / ab) - 50) / 10
    for L in (12, 48, 288):
        vw = (c * qv).rolling(L).sum() / qv.rolling(L).sum()
        out[f"vwap_{L}"] = (c - vw) / (c * s1 * np.sqrt(L))
    sp = (h - l) / c
    zsp = (sp - sp.rolling(W1).mean()) / sp.rolling(W1).std()
    out["volspitze_1"] = zsp.clip(lower=0) * np.sign(c - o)
    out["volspitze_3"] = zsp.rolling(3).max().clip(lower=0) * np.sign(c - o.shift(2))
    enge = r1.rolling(12).std() / s1
    out["volenge"] = mom(3).where(enge < 0.6, 0.0)
    out["volweite"] = mom(3).where(enge > 1.8, 0.0)
    # Cross-Asset: BTC (Index 0) und ETH (Index 1) als Leitmärkte
    cb, ce = S("c", 0), S("c", 1)
    rb1 = cb.pct_change()
    sb1 = rb1.rolling(W1).std()
    for L in (1, 3, 12):
        out[f"btcfuehrt_{L}"] = mom(L, cb, sb1) if j != 0 else pd.Series(np.nan, index=c.index)
    ra12, rb12 = c.pct_change(12), cb.pct_change(12)
    beta = (ra12.rolling(W7).cov(rb12) / rb12.rolling(W7).var()).shift(1)
    rel = {L: (c.pct_change(L) - beta * cb.pct_change(L)) / (s1 * np.sqrt(L)) for L in (12, 48, 288)}
    for L in (12, 48, 288):
        out[f"relstaerke_{L}"] = rel[L] if j != 0 else pd.Series(np.nan, index=c.index)
    eb = ce / cb
    for L in (48, 288):
        out[f"ethbtc_{L}"] = eb.pct_change(L)
    korr = r1.rolling(W1).corr(rb1)
    kz = (korr - korr.rolling(W7).mean()) / korr.rolling(W7).std()
    out["korrbruch"] = rel[48].where(kz < -1.5, 0.0) if j != 0 else pd.Series(np.nan, index=c.index)
    # Derivate
    p = S("prem")
    out["aufschlag"] = (p - p.rolling(W1).mean()) / p.rolling(W1).std()
    out["aufschlag_d3"], out["aufschlag_d12"] = p.diff(3), p.diff(12)
    out["fund"] = S("frate") / 1e-4
    oi = S("oi")
    for name, L in (("1h", 12), ("4h", 48)):
        doi = oi.pct_change(L)
        zo = doi / doi.rolling(W30).std().shift(1)
        out[f"oi_kurs_{name}"] = zo * np.sign(c.pct_change(L))
        out[f"oi_abbau_{name}"] = (-mom(L)).where(zo < -1.5, 0.0)
    kl, pl = S("konten_ls"), S("profis_ls")
    out["konten_ls"] = (kl - kl.rolling(W30).mean()) / kl.rolling(W30).std()
    g = pl - kl
    out["profis_gegen_konten"] = (g - g.rolling(W30).mean()) / g.rolling(W30).std()
    out["taker_4h"] = S("taker_log").rolling(48).mean()
    # Mikrostruktur
    for k in (1, 3, 5):
        b, a = S(f"b{k}"), S(f"a{k}")
        u = (b - a) / (b + a)
        out[f"tiefe_{k}"] = (u - u.rolling(W1, min_periods=200).mean()) / u.rolling(W1, min_periods=200).std()
        if k in (1, 5):
            out[f"tiefe_d_{k}"] = u.diff(12)
    summe = S("b5") + S("a5")
    out["liq_entzug"] = np.sign(c.pct_change(12)) * (-summe.pct_change(12)).clip(lower=0)
    tq, tqv = S("tq"), S("tqv")
    ti = 2 * tq - tqv
    for L in (1, 3, 12, 48):
        out[f"kaufdruck_{L}"] = ti.rolling(L).sum() / tqv.rolling(L).sum()
    # Saisonalität (Generation 3): mittlere Rendite des jetzt beginnenden Zeitfensters (nächste L Kerzen) an den letzten N Vortagen.
    # Wert an Kerze i nutzt nur Schlusskurse bis i + L - 288, also mindestens einen Tag minus L Kerzen alte Daten.
    def tagzeit(x, L, N):
        v = (x.pct_change(L) / (x.pct_change().rolling(W1).std() * np.sqrt(L))).shift(W1 - L)      # Fenster gleicher Uhrzeit am Vortag
        return sum(v.shift(W1 * d) for d in range(N)) / N
    for L in (3, 12):
        for N in (7, 28):
            out[f"tagzeit_{L}_{N}"] = tagzeit(c, L, N)
        alle = [tagzeit(S("c", k), L, 28) for k in range(len(D.COINS))]
        out[f"tagzeitrel_{L}_28"] = alle[j] - sum(alle) / len(alle)                                # gegen den Durchschnitt der zehn Coins
    # Tiefe in feinerer Zeitauflösung (Generation 4): Stand des letzten Schnappschusses vor Kerzenschluss
    bl, al, bm, am = S("b1l"), S("a1l"), S("b1"), S("a1")
    ul, um = (bl - al) / (bl + al), (bm - am) / (bm + am)
    out["tiefe_letzt_1"] = (ul - ul.rolling(W1, min_periods=200).mean()) / ul.rolling(W1, min_periods=200).std()
    out["tiefe_frisch_1"] = ul - um                                                                 # jüngste Verschiebung innerhalb der Kerze
    return out


def _coin(j: int):
    roh = _roh(j)
    werte = np.load(D.SPEICHER / "signale.npy", mmap_mode="r+")
    for i, name in enumerate(NAMEN):
        s = roh[name].replace([np.inf, -np.inf], np.nan)
        if name != "fund":
            sd = s.rolling(W7, min_periods=576).std().shift(1)
            s = (s / sd).where(sd > 0)
        werte[i, j] = s.to_numpy(dtype=np.float32)
    werte.flush()
    # Filter und Hilfsreihen
    c = pd.Series(np.asarray(D.laden("c")[j], dtype=np.float64))
    cb = pd.Series(np.asarray(D.laden("c")[0], dtype=np.float64))
    s1 = c.pct_change().rolling(W1).std()
    rang = s1.rolling(W30, min_periods=W7).rank(pct=True)
    stunde = pd.DatetimeIndex(D.RASTER).hour.to_numpy()
    filt = np.load(D.SPEICHER / "filter.npy", mmap_mode="r+")
    filt[0, j] = np.sign(c / c.shift(14 * W1) - 1).fillna(0).to_numpy(np.int8)          # 14-Tage-Trend
    filt[1, j] = np.where(rang.isna(), -1, np.where(rang >= 2 / 3, 2, np.where(rang < 1 / 3, 0, 1))).astype(np.int8)
    filt[2, j] = (stunde // 8).astype(np.int8)                                           # 0 Asien, 1 Europa, 2 USA (UTC)
    filt[3, j] = np.sign(cb / cb.shift(W1) - 1).fillna(0).to_numpy(np.int8)              # BTC über 24 Stunden
    filt.flush()
    sig = np.load(D.SPEICHER / "sigma.npy", mmap_mode="r+")
    sig[j] = c.pct_change(12).rolling(W1).std().to_numpy(np.float32)                     # Schwankung der Stundenrendite (für Stops)
    sig.flush()
    return j


def alle_rechnen():
    n = len(D.COINS)
    np.lib.format.open_memmap(D.SPEICHER / "signale.npy", mode="w+", dtype=np.float32, shape=(len(NAMEN), n, D.N))
    np.lib.format.open_memmap(D.SPEICHER / "filter.npy", mode="w+", dtype=np.int8, shape=(4, n, D.N))
    np.lib.format.open_memmap(D.SPEICHER / "sigma.npy", mode="w+", dtype=np.float32, shape=(n, D.N))
    with Pool(4) as p:
        for j in p.imap_unordered(_coin, range(n)):
            print("Signale fertig:", D.COINS[j], flush=True)


def filter_maske(name: str, filt, j: int, richtung: np.ndarray) -> np.ndarray:
    """Maske je Kerze, ob ein Einstieg in `richtung` (+1/-1 je Kerze) unter dem Filter erlaubt ist."""
    if name == "kein":
        return np.ones(richtung.shape, bool)
    if name == "trend_mit":
        return filt[0, j] == richtung
    if name == "trend_gegen":
        return filt[0, j] == -richtung
    if name == "vol_hoch":
        return filt[1, j] == 2
    if name == "vol_niedrig":
        return filt[1, j] == 0
    if name in ("asien", "europa", "usa"):
        return filt[2, j] == ("asien", "europa", "usa").index(name)
    if name == "btc_auf":
        return filt[3, j] == 1
    if name == "btc_ab":
        return filt[3, j] == -1
    raise ValueError(name)


if __name__ == "__main__":
    alle_rechnen()
    w = np.load(D.SPEICHER / "signale.npy", mmap_mode="r")
    print(len(NAMEN), "Signale; Anteil gültiger Werte (BTC/SOL) und Anteil |Wert| >= 2,5:")
    for i, name in enumerate(NAMEN):
        x = np.asarray(w[i, 2])
        print(f"  {name:<22} gültig {np.isfinite(x).mean():.2f}  |x|>=2.5: {(np.abs(x) >= 2.5).mean():.4f}")
