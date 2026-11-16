"""Unabhängige Nachrechnung einzelner Kandidaten für EINEN Coin über 3 Monate im Training.

Eigene Seite: pandas direkt aus data/candles/*.parquet, zeitbezogene Fenster ("24h", "7D", "30D") und zeitbezogene Verschiebungen,
eigener Simulator (ref_sim.py). Kein fabrik.signale, kein fabrik.kern, kein Datenspeicher (Ausnahme: die Konstante slip_bp.npy).
Es werden nur Rohzeilen VOR dem Fensterende gelesen; die eigene Seite kann also nichts aus der Zukunft wissen.
Fabrik-Seite: lauf.einstieg + kern.trades_liste auf den gespeicherten Signalen, gleiche Fenstergrenzen.
"""
import json, sys
from pathlib import Path
sys.path.insert(0, 'forschung')
HIER = Path(__file__).resolve().parent
sys.path.insert(0, str(HIER))
import numpy as np, pandas as pd
from ref_sim import ref_trades

m5 = pd.Timedelta(minutes=5)
COINS = ['BTC', 'ETH', 'SOL', 'XRP', 'DOT', 'DOGE', 'ADA', 'LINK', 'AVAX', 'LTC']
MAERKTE = {"top3": [0, 1, 2], "alle10": list(range(10)), "alt7": list(range(3, 10))}
AUSSTIEGE = {"h720_zielnachzug": (144, 0, 0, 0.5, 1.0, None), "h240_stop2": (48, 2.0, 0, 0, 0, None), "signal_h720": (144, 0, 0, 0, 0, 0.5),
             "h240_stop1.5_ziel3": (48, 1.5, 3.0, 0, 0, None), "h720": (144, 0, 0, 0, 0, None)}   # aus generator.py abgeschrieben (Festlegung)
START = pd.Timestamp("2021-07-01")


# ------------------------------------------------------------------ eigene Seite
def roh(art, coin, bis):
    d = pd.read_parquet(f"data/candles/{art}/{coin}USDT.parquet")
    return d[d.index < bis]


def kerzen(coin, bis):
    k = roh("5m", coin, bis)
    gitter = pd.date_range(START, bis - m5, freq="5min")
    k = k.reindex(gitter)
    gueltig = k["close"].notna()
    c = k["close"].ffill()
    for sp in ("open", "high", "low"):
        k[sp] = k[sp].where(gueltig, c)
    k["close"] = c
    k["gueltig"] = gueltig
    return k


def aenderung(x, minuten):                       # relative Änderung gegen den Wert vor `minuten` (zeitbezogen)
    return x / x.shift(freq=pd.Timedelta(minutes=minuten)).reindex(x.index) - 1


def schwankung_24h(c):                           # Standardabweichung der 5-Minuten-Renditen der letzten 24 h (288 Werte nötig)
    return aenderung(c, 5).rolling("24h", min_periods=288).std()


def normiert(x):
    x = x.replace([np.inf, -np.inf], np.nan)
    sd = x.rolling("7D", min_periods=576).std()
    sd = sd.shift(freq=m5).reindex(x.index)      # nur bis zur Vorkerze
    return (x / sd).where(sd > 0).astype(np.float32)


def stundenwert(coin, spalte, gitter, bis):
    """Wert der letzten abgeschlossenen Stunde: Beschriftung H enthält Messungen bis H+1h, nutzbar ab Kerze H+1h; höchstens 1 h fortgeschrieben."""
    m = roh("metrics", coin, bis)[spalte]
    verf = pd.DataFrame({"t": (m.index + pd.Timedelta(hours=1)).astype("datetime64[ns]"), "w": m.to_numpy(np.float64)})
    q = pd.DataFrame({"t": gitter.astype("datetime64[ns]")})
    x = pd.merge_asof(q, verf.assign(tv=verf["t"]), on="t")
    w = np.where((x["t"] - x["tv"]) <= pd.Timedelta(hours=1), x["w"], np.nan)
    return pd.Series(w.astype(np.float32).astype(np.float64), index=gitter)          # der Speicher hält float32


def signal_roh(name, coin, k, bis):
    c, g = k["close"], k.index
    s1 = schwankung_24h(c)
    if name == "vwap_48":
        qv = k["quote_volume"].astype(np.float32).astype(np.float64)
        vw = (c * qv).rolling("4h", min_periods=48).sum() / qv.rolling("4h", min_periods=48).sum()
        return (c - vw) / (c * s1 * np.sqrt(48))
    if name == "btcfuehrt_3":
        cb = kerzen("BTC", bis)["close"]
        return aenderung(cb, 15) / (schwankung_24h(cb) * np.sqrt(3))
    if name.startswith("tiefe_"):
        st = name.split("_")[1]
        t = roh("tiefe_5m", coin, bis).reindex(g)
        b, a = t[f"w-{st}"].astype(np.float64), t[f"w+{st}"].astype(np.float64)
        u = (b - a) / (b + a)
        return (u - u.rolling("24h", min_periods=200).mean()) / u.rolling("24h", min_periods=200).std()
    if name == "liq_entzug":
        t = roh("tiefe_5m", coin, bis).reindex(g)
        summe = t["w-5"].astype(np.float64) + t["w+5"].astype(np.float64)
        return np.sign(aenderung(c, 60)) * (-aenderung(summe, 60)).clip(lower=0)
    if name == "konten_ls":
        kl = stundenwert(coin, "konten_ls", g, bis)
        return (kl - kl.rolling("30D", min_periods=8640).mean()) / kl.rolling("30D", min_periods=8640).std()
    if name == "oi_kurs_4h":
        oi = stundenwert(coin, "oi", g, bis)
        doi = aenderung(oi, 240)
        sd = doi.rolling("30D", min_periods=8640).std().shift(freq=m5).reindex(g)
        return doi / sd * np.sign(aenderung(c, 240))
    raise ValueError(name)


def rang_30d(s1, pos):
    """Rang (Anteil) des aktuellen Werts unter den Werten der letzten 30 Tage (8640 Kerzen einschl. der aktuellen), mind. 2016 gültige."""
    x = s1.to_numpy()
    aus = np.full(len(pos), np.nan)
    for n, i in enumerate(pos):
        if i < 0 or np.isnan(x[i]):
            continue
        w = x[max(0, i - 8639): i + 1]
        w = w[~np.isnan(w)]
        if len(w) >= 2016:
            aus[n] = ((w < x[i]).sum() + ((w == x[i]).sum() + 1) / 2) / len(w)
    return aus


def filter_maske(name, coin, k, d, w0i, bis):
    g, c = k.index, k["close"]
    ok = np.zeros(len(g), bool)
    pos = np.arange(w0i, len(g))
    if name == "kein":
        ok[pos] = True
    elif name in ("asien", "europa", "usa"):
        ok[pos] = (g.hour.to_numpy()[pos] // 8) == ("asien", "europa", "usa").index(name)
    elif name in ("vol_hoch", "vol_niedrig"):
        r = rang_30d(schwankung_24h(c), pos)
        ok[pos] = (r >= 2 / 3) if name == "vol_hoch" else (r < 1 / 3)
    elif name in ("trend_mit", "trend_gegen"):
        tr = np.sign(aenderung(c, 14 * 24 * 60)).fillna(0).to_numpy()
        ok[pos] = (tr[pos] == d[pos]) if name == "trend_mit" else (tr[pos] == -d[pos])
    elif name in ("btc_auf", "btc_ab"):
        cb = kerzen("BTC", bis)["close"]
        tb = np.sign(aenderung(cb, 24 * 60)).fillna(0).to_numpy()
        ok[pos] = tb[pos] == (1 if name == "btc_auf" else -1)
    else:
        raise ValueError(name)
    return ok


def eigene_rechnung(z, coin, w0, w1):
    k = kerzen(coin, w1)
    g = k.index
    w0i = int((w0 - START) / m5)
    sig = normiert(signal_roh(z["signal"], coin, k, w1))
    w = sig.to_numpy(np.float64)
    d = np.where(w >= z["th"], 1, np.where(w <= -z["th"], -1, 0)) * z["r"]
    ok = filter_maske(z["f"], coin, k, d, w0i, w1) & k["gueltig"].to_numpy()
    schluss = g + m5
    ok &= np.asarray((schluss.hour * 60 + schluss.minute) % (5 * z["k"]) == 0)                 # Takt: Kerze schließt auf dem Takt-Raster
    ein = np.where(ok, d, 0).astype(np.int8)
    sigma = aenderung(k["close"], 60).rolling("24h", min_periods=288).std().to_numpy(np.float32)
    halte, sl, tp, tr, ta, sx = AUSSTIEGE[z["x"]]
    o, h, l = (k[x].to_numpy(np.float64) for x in ("open", "high", "low"))
    tr_ = ref_trades(o, h, l, ein, w * z["r"], sigma, w0i, len(g), halte, sl, tp, tr, ta, sx)
    fu = roh("funding", coin, w1 + pd.Timedelta(days=1))["rate"]
    slip = float(np.load("data/fabrik/slip_bp.npy")[COINS.index(coin)]) * 2.0
    zeilen = []
    for a, b, dd, e, px, innen in tr_:
        ta_, tb_ = g[a], g[b]
        fund = float(fu[(fu.index > ta_) & (fu.index <= tb_)].sum())                           # Termine nach dem Einstieg bis einschließlich Ausstiegskerze
        zeilen.append((ta_, tb_, dd, dd * (px / e - 1) * 1e4 - slip - dd * fund * 1e4))
    return pd.DataFrame(zeilen, columns=["ein", "aus", "richtung", "roh"]), sig, ein


# ------------------------------------------------------------------ Fabrik-Seite
def fabrik_rechnung(z, coin, w0, w1):
    from fabrik import daten as D, lauf as L, kern as FK, signale as S, generator as G
    if not L._g:
        L._init()
    j = D.COINS.index(coin)
    a = {"si": S.NAMEN.index(z["signal"]), "signal": z["signal"], "th": z["th"], "r": z["r"], "f": z["f"], "k": z["k"]}
    ein, wert = L.einstieg(a, j)
    halte, sl, tp, tr, ta, sx = G.AUSSTIEGE[z["x"]]
    i0, i1 = L.idx(w0), L.idx(w1)
    assert i1 <= L.I_ENDE
    aus = np.zeros((20000, 6))
    slip = float(np.asarray(L._g["slip_bp"])[j]) * 2.0
    n = FK.trades_liste(L._g["o"][j], L._g["h"][j], L._g["l"][j], L._g["fcum"][j], ein, wert, L._g["sigma"][j], i0, i1, halte, sl, tp, tr, ta, np.nan if sx is None else sx, slip, aus)
    t = pd.DataFrame({"ein": D.RASTER[aus[:n, 0].astype(int)], "aus": D.RASTER[aus[:n, 1].astype(int)], "richtung": aus[:n, 2].astype(int), "roh": aus[:n, 3]})
    return t, np.asarray(L._g["signale"][a["si"], j, i0:i1]), ein[i0:i1]


def db_abgleich(z):
    """Fabrik-Simulator über das ganze Training für den Markt des Kandidaten gegen die Datenbankzeile (n_t, roh_t)."""
    from fabrik import daten as D, lauf as L, kern as FK, signale as S, generator as G
    a = {"si": S.NAMEN.index(z["signal"]), "signal": z["signal"], "th": z["th"], "r": z["r"], "f": z["f"], "k": z["k"]}
    t0, v0, _ = L.SEGMENTE["t" if z["braucht"] == "t" else "k"]
    i0 = L.I_T + t0 * 288
    halte, sl, tp, tr, ta, sx = G.AUSSTIEGE[z["x"]]
    n_ges, roh_ges = 0, 0.0
    for j in MAERKTE[z["m"]]:
        if j == 0 and z["signal"].startswith(("btcfuehrt", "relstaerke", "korrbruch")):
            continue
        ein, wert = L.einstieg(a, j)
        aus = np.zeros((200000, 6))
        n = FK.trades_liste(L._g["o"][j], L._g["h"][j], L._g["l"][j], L._g["fcum"][j], ein, wert, L._g["sigma"][j], i0, L.I_ENDE, halte, sl, tp, tr, ta,
                            np.nan if sx is None else sx, float(np.asarray(L._g["slip_bp"])[j]) * 2.0, aus)
        tg = (aus[:n, 0].astype(int) - L.I_T) // 288
        im_t = (tg >= t0) & (tg < v0)
        n_ges += int(im_t.sum()); roh_ges += float(aus[:n, 3][im_t].sum())
    return n_ges, roh_ges / max(n_ges, 1)


if __name__ == "__main__":
    kand = json.loads((HIER / "p04a_auswahl.json").read_text())
    for z in kand:
        z["art"] = "Zufall"
    zusatz = json.loads((HIER / "p04_zusatz.json").read_text()) if (HIER / "p04_zusatz.json").exists() else []
    for z in zusatz:
        z["art"] = "Zusatz (gezielt gewählt)"
    rng = np.random.default_rng(4711)
    summe = []
    for z in kand + zusatz:
        tief = z["braucht"] == "t"
        coins = [c for c in MAERKTE[z["m"]] if not (c == 0 and z["signal"].startswith("btcfuehrt"))]
        coin = COINS[int(rng.choice(coins))]
        monate = pd.period_range("2023-01", "2023-10", freq="M") if tief else pd.period_range("2021-09", "2023-04", freq="M")
        w0 = monate[int(rng.integers(len(monate)))].to_timestamp()
        w1 = w0 + pd.DateOffset(months=3)
        print(f"\n=== {z['art']}: {z['id']} {z['signal']} th {z['th']} r {z['r']:+d} Filter {z['f']} Takt {z['k']} Ausstieg {z['x']} Markt {z['m']} | Coin {coin}, Fenster {w0.date()} bis {w1.date()}")
        te, sig_e, ein_e = eigene_rechnung(z, coin, w0, w1)
        tf, sig_f, ein_f = fabrik_rechnung(z, coin, w0, w1)
        w0i = int((w0 - START) / m5)
        se = sig_e.to_numpy()[w0i:]
        gleich = (se == sig_f) | (np.isnan(se) & np.isnan(sig_f))
        mit = np.isfinite(se) & np.isfinite(sig_f)
        print(f"  Signalwerte im Fenster: {len(se)} Kerzen, bitgleich {int(gleich.sum())}, größte Abweichung {float(np.abs(se[mit] - sig_f[mit]).max()) if mit.any() else float('nan'):.2e}, nur einseitig NaN {int((np.isfinite(se) != np.isfinite(sig_f)).sum())}")
        print(f"  Einstiegswünsche (ein != 0) eigene {int((ein_e[w0i:] != 0).sum())} / Fabrik {int((ein_f != 0).sum())}, ungleiche Kerzen {int((ein_e[w0i:] != ein_f).sum())}")
        print(f"  Trades: eigene {len(te)} / Fabrik {len(tf)}")
        gl_zeit = len(te) == len(tf) and bool((te["ein"].to_numpy() == tf["ein"].to_numpy()).all())
        if gl_zeit:
            gl_aus = bool((te["aus"].to_numpy() == tf["aus"].to_numpy()).all()); gl_r = bool((te["richtung"].to_numpy() == tf["richtung"].to_numpy()).all())
            dmax = float(np.abs(te["roh"].to_numpy() - tf["roh"].to_numpy()).max()) if len(te) else 0.0
            print(f"  Einstiegszeiten gleich: True | Ausstiegszeiten gleich: {gl_aus} | Richtung gleich: {gl_r} | größte Abweichung roh je Trade: {dmax:.2e} bp | roh Mittel eigene {te['roh'].mean():.4f} / Fabrik {tf['roh'].mean():.4f} bp")
        else:
            nur_e = sorted(set(te["ein"]) - set(tf["ein"])); nur_f = sorted(set(tf["ein"]) - set(te["ein"]))
            print(f"  Einstiegszeiten gleich: False | nur eigene: {len(nur_e)} {nur_e[:5]} | nur Fabrik: {len(nur_f)} {nur_f[:5]}")
        n_db, roh_db = db_abgleich(z)
        print(f"  Datenbank-Abgleich (ganzes Training, ganzer Markt, Fabrik-Simulator neu): n_t {n_db} (DB {z['n_t']}), roh_t {roh_db:.3f} (DB {z['roh_t']})")
        if len(te):
            print("  erste Trades (eigene):", "; ".join(f"{r.ein} {'L' if r.richtung > 0 else 'S'} -> {r.aus} {r.roh:+.1f}bp" for r in te.head(3).itertuples()))
        summe.append((z["id"], coin, str(w0.date()), len(te), len(tf), gl_zeit))
    print("\nZUSAMMENFASSUNG:", summe)
