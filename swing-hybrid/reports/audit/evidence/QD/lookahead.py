"""QD-Audit: Look-ahead-Pruefung.
(1) Stoertest: alle 5-Minuten-Kerzen ab T0 werden verfremdet; Gewichte bis einschliesslich T0 und Kontoverlauf vor T0 muessen gleich bleiben.
(2) Unabhaengige Nachrechnung des Kandidaten ohne engine2/auf_raster (reines numpy/pandas auf Zeitstempeln).
"""
import sys, time, json
sys.path.insert(0, "/home/user/OdinGate-Botv134/swing-hybrid/src")
import numpy as np, pandas as pd
from hybrid import research as R, runner, mutationen as M, tpsl

A = R.GRUPPE_A
K = R.yubit_kosten(A)[0]
orig_lesen = R._lesen
T0 = pd.Timestamp("2024-06-03 13:00")

def gestoert(art, coin, vor):
    d = orig_lesen(art, coin, vor).copy()
    rng = np.random.default_rng(abs(hash((art, coin))) % 2**32)
    sp = d.index >= T0
    if art == "5m":
        f = np.exp(np.cumsum(rng.normal(0, 0.004, sp.sum())))          # anderer Kursverlauf ab T0
        for c in ("open", "high", "low", "close"):
            d.loc[sp, c] = d.loc[sp, c].to_numpy() * f
        d.loc[sp, "quote_volume"] = d.loc[sp, "quote_volume"].to_numpy() * rng.uniform(0.2, 5, sp.sum())
    else:
        d.loc[sp, "rate"] = rng.normal(0, 0.0005, sp.sum())
    return d

print("=== (1) Stoertest ab", T0)
m0 = R.markt(A, vor=True)
fehler = 0
SIG = {"research.tsmom(336)": lambda m: R.tsmom(m, 336), "research.tsmom(168,bias)": lambda m: R.tsmom(m, 168, True),
       "research.ensemble": lambda m: R.ensemble(m), "research.reversal(24,2)": lambda m: R.reversal(m, 24, 2.0),
       "research.querschnitt(72,mom)": lambda m: R.querschnitt(m, 72, "mom"), "research.rangfolge(168,24)": lambda m: R.rangfolge(m, 168, 24),
       "research.vol_beide": lambda m: R.variante(m, "vol_beide"), "research.mischung": lambda m: R.variante(m, "mischung"),
       "research.carry": lambda m: R.variante(m, "carry")}
SIG.update({"mutationen." + n: fn for n, fn in M.VARIANTEN.items()})
SIG.update({"tpsl." + n: fn for n, fn in tpsl.VARIANTEN.items()})
# Erst ALLE Signale mit Originaldaten rechnen (einige Signale lesen Funding/BTC selbst nach), dann stoeren und neu rechnen.
W0 = {n: R.auf_raster(m0, fn(m0)) for n, fn in SIG.items()}
R._lesen = gestoert
m1 = R.markt(A, vor=True)
W1 = {n: R.auf_raster(m1, fn(m1)) for n, fn in SIG.items()}
i0 = int(m0.index.searchsorted(T0))
print("Kurse vor T0 gleich:", np.array_equal(m0.c[:, :i0], m1.c[:, :i0]), "| Kurse ab T0 verschieden:", not np.allclose(m0.c[:, i0:], m1.c[:, i0:]))
print("ATR-Feld bis einschl. T0 gleich:", np.array_equal(m0.atr[:, :i0 + 1], m1.atr[:, :i0 + 1], equal_nan=True))
print("Funding-Feld vor T0 gleich:", np.array_equal(m0.fund[:, :i0], m1.fund[:, :i0]), "| ab T0 verschieden:", not np.array_equal(m0.fund[:, i0:], m1.fund[:, i0:]))
zeilen = []
for n, fn in SIG.items():
    w0, w1 = W0[n], W1[n]
    gleich_bis = np.array_equal(w0[:, :i0 + 1], w1[:, :i0 + 1])       # Gewicht der Kerze T0 gilt ab deren Open: darf nur Daten < T0 nutzen
    spaeter = not np.array_equal(w0[:, i0 + 1:], w1[:, i0 + 1:])
    zeilen.append((n, gleich_bis, spaeter)); fehler += (not gleich_bis)
for z in zeilen:
    print(f"  {z[0]:32s} Gewichte bis T0 unveraendert: {z[1]}   danach veraendert (Test hat Wirkung): {z[2]}")
# Kontoverlauf des Kandidaten: vor T0 identisch?
w0, w1 = W0["mutationen.nur_long"] * 0 + W0["research.tsmom(336)"], W1["research.tsmom(336)"]
l0 = R.lauf(m0, w0, taker=True, slip=K, day_limit=9.0); l1 = R.lauf(m1, w1, taker=True, slip=K, day_limit=9.0)
e0, e1 = l0.equity(runner.MIT), l1.equity(runner.MIT)
print("Kontoverlauf (netto mit Rebate) vor T0 identisch:", np.array_equal(e0[:i0], e1[:i0]), "| max. Abweichung danach:", float(np.abs(e0[i0:] - e1[i0:]).max()))
# passiver Pfad
p0 = R.lauf(m0, w0, day_limit=9.0); p1 = R.lauf(m1, w1, day_limit=9.0)
print("Kontoverlauf passiver Pfad vor T0 identisch:", np.array_equal(p0.equity(runner.MIT)[:i0], p1.equity(runner.MIT)[:i0]))
print("ANZAHL SIGNALE MIT BLICK VORAUS:", fehler)
R._lesen = orig_lesen

print("\n=== (2) Unabhaengige Nachrechnung des Kandidaten (Hebel 1, Yubit-Kosten, ohne Tageslimit)")
idx = m0.index
S = 1.0 / len(A)
tage = idx.normalize()
net_tag = {}
abw_sig = 0
for j, coin in enumerate(A):
    df = orig_lesen("5m", coin, True)
    df = df[~df.index.duplicated()].sort_index()
    cl = df["close"]
    # Stundenschluss = letzter 5-Minuten-Schluss der Stunde, Zeitstempel = Stundenende
    hc = cl.groupby(cl.index.floor("h")).last()
    ende = hc.copy(); ende.index = ende.index + pd.Timedelta(hours=1)
    alt = hc.copy(); alt.index = alt.index + pd.Timedelta(hours=337)          # Schluss von 336 Stunden zuvor, am selben Stundenende
    sig = np.sign(ende / alt.reindex(ende.index) - 1.0).fillna(0.0)           # bekannt am Stundenende
    tgt = sig.reindex(idx.union(sig.index)).ffill().reindex(idx).fillna(0.0).to_numpy()
    abw_sig += int((tgt != w0[j]).sum())
    k = df.reindex(idx); lue = k["close"].isna()
    c = k["close"].ffill().bfill().to_numpy(); o = k["open"].where(~lue, pd.Series(c, index=idx)).to_numpy()
    fr = orig_lesen("funding", coin, True)["rate"]; fr.index = fr.index.floor("5min")
    fund = fr[~fr.index.duplicated()].reindex(idx).fillna(0.0).to_numpy()
    T = len(idx)
    tgt2 = tgt.copy(); tgt2[0] = 0.0; tgt2[-1] = 0.0                            # erste Kerze: keine Order; letzte Kerze: Schlussabrechnung
    units = np.zeros(T); cash = np.zeros(T); tv = np.zeros(T); fu = np.zeros(T)
    u = 0.0; ca = 0.0; vol = 0.0; f = 0.0; held = 0.0
    for t in range(T):
        if fund[t] != 0.0 and u != 0.0:
            f -= u * o[t] * fund[t]
        if tgt2[t] != held:
            neu = tgt2[t] * S / o[t]
            dq = neu - u
            px = o[t] * (1.0 + np.sign(dq) * K[j])
            ca -= dq * px; vol += abs(dq) * px; u = neu; held = tgt2[t]
        units[t] = u; cash[t] = ca; tv[t] = vol; fu[t] = f
    eq = cash + units * c - 0.0008 * (1 - 0.85) * tv + fu
    s = pd.Series(eq, index=idx).groupby(tage).last()
    net_tag[coin] = s.diff().fillna(s.iloc[0])
mein = pd.DataFrame(net_tag).sum(axis=1)
kern = l0.daily_pnl(runner.MIT).sum(axis=1)
print("abweichende Zielgewichte (5-Minuten-Kerzen x Coins) zwischen eigener Signalrechnung und auf_raster:", abw_sig)
print("max. Abweichung Tagesergebnis eigene Rechnung gegen engine2:", float((mein - kern).abs().max()))
def sh(x): return float(x.mean() / x.std() * np.sqrt(365))
for nm, a, b in (("Entwicklung", None, R.SPLIT), ("Pruefung", R.SPLIT, None)):
    x = mein; y = kern
    if a: x = x[x.index >= pd.Timestamp(a)]; y = y[y.index >= pd.Timestamp(a)]
    if b: x = x[x.index < pd.Timestamp(b)]; y = y[y.index < pd.Timestamp(b)]
    print(f"  {nm}: eigene Rechnung N {x.sum():.4f}, pro Jahr {x.mean()*365:.4f}, Sharpe {sh(x):.4f} | engine2 N {y.sum():.4f}, Sharpe {sh(y):.4f}")
# Luecken in den Stundenreihen
cc = R._close(m0)
voll = pd.date_range(cc.index[0], cc.index[-1], freq="1h")
print("\nStundenraster: fehlende Stunden insgesamt (alle Coins gleichzeitig):", len(voll.difference(cc.index)), "| NaN je Coin im Hauptzeitraum:",
      cc.loc[R.START:].isna().sum().to_dict())
