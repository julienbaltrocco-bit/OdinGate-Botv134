"""Ausrichtung jeder Reihe des Datenspeichers gegen die lokalen Rohdateien (data/candles/*), unabhängig von daten.py gerechnet.

Für jede Reihe wird je Kerze i (Eröffnung t = RASTER[i], Schluss t+5min) der Wert gebildet, der sich aus Rohzeilen ergibt,
deren VERFÜGBARKEITSZEIT <= t+5min ist, und mit dem Speicher verglichen. Es werden nur Kerzen < I_ENDE (2024-07-01) gelesen.
Verfügbarkeitszeit: Kerzen (5m/1m/Aufschlag) = open_time + Kerzenlänge; Funding = calc_time; Stundenwerte = Beschriftung + 1 h
(resample('1h') beschriftet am Stundenbeginn, enthält Messungen bis Stundenende); Tiefe = Fensterbeginn + 5 min.
"""
import sys
sys.path.insert(0, 'forschung')
import numpy as np, pandas as pd
from fabrik import daten as D, lauf as L

I_ENDE = L.I_ENDE
RA = D.RASTER[:I_ENDE]
GRENZE = RA[-1] + pd.Timedelta(minutes=5)
m5, h1 = pd.Timedelta(minutes=5), pd.Timedelta(hours=1)


def roh(art, coin):
    d = pd.read_parquet(f"data/candles/{art}/{coin}USDT.parquet")
    return d[d.index < GRENZE]


def sp(name, j):
    return np.asarray(np.load(D.SPEICHER / f"{name}.npy", mmap_mode="r")[j, :I_ENDE])


def vgl(name, ist, soll, rtol=2e-6):
    ist, soll = np.asarray(ist, np.float64), np.asarray(soll, np.float64)
    beide_nan = np.isnan(ist) & np.isnan(soll)
    nah = np.isclose(ist, soll, rtol=rtol, atol=0) | beide_nan
    return f"{name}: ungleich {int((~nah).sum())} (gültig {int(np.isfinite(ist).sum())})"


def asof(zeit_verfuegbar, werte, schluss, max_alter=None, exakt=True):
    """Letzter Wert mit Verfügbarkeitszeit <= Kerzenschluss (bzw. < bei exakt=False)."""
    q = pd.DataFrame({"t": schluss})
    r = pd.DataFrame({"t": pd.DatetimeIndex(zeit_verfuegbar).astype("datetime64[ns]"), "w": np.asarray(werte, np.float64)}).sort_values("t")
    q["t"] = q["t"].astype("datetime64[ns]")
    m = pd.merge_asof(q, r.assign(tv=r["t"]), on="t", direction="backward", allow_exact_matches=exakt)
    w = m["w"].to_numpy()
    if max_alter is not None:
        w = np.where((q["t"] - m["tv"]) <= max_alter, w, np.nan)
    return w, (q["t"] - m["tv"])


schluss = RA + m5
for j, coin in enumerate(D.COINS):
    aus = []
    k = roh("5m", coin)
    g = sp("gueltig", j)
    # Kerzen: Wert der Zeile, deren Schluss (open_time + 5 min) genau der Kerzenschluss ist
    ks = k.copy(); ks.index = ks.index + m5
    for x, spalte in (("o", "open"), ("h", "high"), ("l", "low"), ("c", "close"), ("qv", "quote_volume")):
        soll = ks[spalte].reindex(schluss).to_numpy()
        ist = sp(x, j).astype(np.float64)
        if x != "qv":
            ist = np.where(g, ist, np.nan)
        aus.append(vgl(x, ist, soll))
    aus.append(f"gueltig==Zeile vorhanden: {bool((g == ks['close'].reindex(schluss).notna().to_numpy()).all())}, Lücken {int((~g).sum())}")
    # Lücken: o/h/l/c = letzter Schluss davor (nur Vergangenheit)
    c_sp = sp("c", j)
    c_ff = ks["close"].reindex(schluss).ffill().to_numpy()
    aus.append(f"Lücken mit letztem Schluss gefüllt: {bool(np.allclose(c_sp[~g], c_ff[~g], equal_nan=True))}")
    # Kaufdruck: Summe der Minutenkerzen, die innerhalb der Kerze schließen
    m1 = roh("1m", coin)
    ende1 = m1.index + pd.Timedelta(minutes=1)                       # Verfügbarkeit der Minutenkerze
    grp = (ende1 - pd.Timedelta(microseconds=1)).floor("5min") + m5 # Schluss der 5-Minuten-Kerze, in der sie schließt
    s = m1[["taker_quote", "quote_volume"]].astype(np.float64).groupby(grp).sum()
    aus.append(vgl("tq", sp("tq", j), s["taker_quote"].reindex(schluss).to_numpy(), 1e-4))
    aus.append(vgl("tqv", sp("tqv", j), s["quote_volume"].reindex(schluss).to_numpy(), 1e-4))
    # Aufschlag
    p = roh("premium_5m", coin); p.index = p.index + m5
    aus.append(vgl("prem", sp("prem", j), p["close"].reindex(schluss).to_numpy(), 1e-5))
    # Funding: frate = letzte Rate mit calc_time < Eröffnung der Kerze (also sicher vor dem Schluss); fcum = Summe bis einschließlich Eröffnung
    fu = roh("funding", coin)["rate"]
    w, alter = asof(fu.index, fu.to_numpy(), RA, exakt=False)       # strikt vor der Eröffnung
    ist = sp("frate", j)
    aus.append(vgl("frate (letzte Rate strikt vor Kerzen-Eröffnung)", ist, w, 1e-5) + f"; kleinstes Alter {alter.min()}")
    fl = fu.copy(); fl.index = fl.index.floor("5min"); fl = fl[~fl.index.duplicated()]
    fc = fl.reindex(RA).fillna(0).cumsum().to_numpy()
    aus.append(vgl("fcum", sp("fcum", j), fc, 1e-9) + f"; Termine nicht auf 5-min-Raster: {int((fu.index != fu.index.floor('5min')).sum())}; doppelte nach floor: {int(fu.index.floor('5min').duplicated().sum())}")
    # Stundenwerte: verfügbar ab Beschriftung + 1 h; höchstens 12 Kerzen fortgeschrieben
    m = roh("metrics", coin)
    for x in ("oi", "konten_ls", "profis_ls", "taker_log"):
        ist = sp(x, j).astype(np.float64)
        w, alter = asof(m.index + h1, m[x].to_numpy(), RA, exakt=True)      # verfügbar spätestens zur Eröffnung der Kerze
        w = np.where(alter <= pd.Timedelta(minutes=60), w, np.nan)
        aus.append(vgl(x, ist, w, 1e-5) + f"; Alter der Stundenbeschriftung zur Kerzen-Eröffnung: min {alter[np.isfinite(ist)].min()} max {alter[np.isfinite(ist)].max()}")
    # Tiefe
    t = roh("tiefe_5m", coin); t.index = t.index + m5
    for st in (1, 3, 5):
        aus.append(vgl(f"b{st}", sp(f"b{st}", j), t[f"w-{st}"].reindex(schluss).to_numpy(), 1e-5))
        aus.append(vgl(f"a{st}", sp(f"a{st}", j), t[f"w+{st}"].reindex(schluss).to_numpy(), 1e-5))
    aus.append(f"Tiefe-Zeitstempel auf 5-min-Raster: {bool((t.index == t.index.floor('5min')).all())}; 5m-Kerzen auf Raster: {bool((k.index == k.index.floor('5min')).all())}; metrics auf Stundenraster: {bool((m.index == m.index.floor('1h')).all())}")
    print(f"== {coin}\n  " + "\n  ".join(aus), flush=True)
