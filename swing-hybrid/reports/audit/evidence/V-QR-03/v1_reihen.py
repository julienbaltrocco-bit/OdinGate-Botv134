"""V-QR-03 Schritt 1: Tagesreihen fuer die Gegenpruefung erzeugen (nur lesend auf data/, schreibt nur ins Ausgabeverzeichnis).

Aufruf aus swing-hybrid/:
  NUMBA_CACHE_DIR=<scratch>/numba .venv/bin/python -I -B -W ignore <dieses Skript> <ausgabeverzeichnis>

Erzeugt:
  reihen_slip_5bp.csv, reihen_slip_yubit.csv : 32 Einstellungen (Runden 1-3), sofortige Ausfuehrung, Hebel 1, ohne Tageslimit,
                                              Tagesergebnis netto mit Rebate, ganzer Zeitraum 08/2021-10/2026
  reihen_passiv_5bp.csv                      : die 10 Trend-Einstellungen der Runde 3 in passiver Ausfuehrung (zweite Auswahl-Sicht)
  vorperiode_kandidat.csv                    : Kandidat in der Vorperiode 02/2020-08/2021 (Gruppe A; 5bp und Yubit-Kosten)
  eigen_kandidat.csv                         : Kandidat OHNE engine2 nachgerechnet (eigene Schleife), zum Abgleich
"""
import sys

sys.path.insert(0, "src")
import numpy as np
import pandas as pd
from hybrid import research as R, runner

AUS = sys.argv[1]
K1 = ([("tsmom", dict(L=L, bias=b)) for L in (12, 24, 48, 96, 168) for b in (False, True)]
      + [("ensemble", dict(bias=b)) for b in (False, True)]
      + [("reversal", dict(n=n, k=k, bias=b)) for n in (24, 72) for k in (1.5, 2.0, 2.5) for b in (False, True)]
      + [("querschnitt", dict(L=L, modus=mo)) for L in (4, 24, 72) for mo in ("mom", "rev")])          # wie scripts/suche_stufe1.py:12-15
K2 = ([("tsmom", dict(L=L, bias=b)) for L in (48, 96, 168, 336) for b in (False, True)]
      + [("ensemble", dict(bias=b)) for b in (False, True)])                                           # wie scripts/suche_runde2.py:14-15


def name(fam, p):
    return fam + "_" + "_".join(f"{k}{v}" for k, v in p.items())


alle = {}
for fam, p in K1 + K2:
    alle.setdefault(name(fam, p), (fam, p))
print("Einstellungen Runde 1:", len(K1), "| Runde 2/3:", len(K2), "| verschieden zusammen:", len(alle))
print("neu in Runde 2/3:", sorted(set(name(*x) for x in K2) - set(name(*x) for x in K1)))

m = R.markt(R.GRUPPE_A)
W = {n: R.auf_raster(m, R.FAMILIEN[f](m, **p)) for n, (f, p) in alle.items()}
ky = R.yubit_kosten(R.GRUPPE_A)[0]
print("Yubit-Slippage je Coin:", dict(zip(R.GRUPPE_A, np.round(ky, 6))))
for kosten, slip in (("slip_5bp", 0.0005), ("slip_yubit", ky)):
    d = pd.DataFrame({n: R.lauf(m, w, taker=True, slip=slip, day_limit=9.0).daily_pnl(runner.MIT).sum(axis=1) for n, w in W.items()})
    d.to_csv(f"{AUS}/reihen_{kosten}.csv", float_format="%.12g")
    print(kosten, d.shape, "von", d.index[0].date(), "bis", d.index[-1].date())
r3 = [name(*x) for x in K2]
d = pd.DataFrame({n: R.lauf(m, W[n], day_limit=9.0).daily_pnl(runner.MIT).sum(axis=1) for n in r3})
d.to_csv(f"{AUS}/reihen_passiv_5bp.csv", float_format="%.12g")

# Vorperiode (bei der Auswahl nicht benutzt)
mv = R.markt(R.GRUPPE_A, R.VOR_START, R.VOR_ENDE, vor=True)
wv = R.auf_raster(mv, R.tsmom(mv, 336))
v = pd.DataFrame({"slip_5bp": R.lauf(mv, wv, taker=True, day_limit=9.0).daily_pnl(runner.MIT).sum(axis=1),
                  "slip_yubit": R.lauf(mv, wv, taker=True, slip=ky, day_limit=9.0).daily_pnl(runner.MIT).sum(axis=1)})
v.to_csv(f"{AUS}/vorperiode_kandidat.csv", float_format="%.12g")
print("Vorperiode", v.shape, v.index[0].date(), v.index[-1].date())

# ---- Kandidat ohne engine2: eigene, einfache Abrechnung (fester Einsatz 1/10 je Coin bei jedem Einstieg/Dreh) ----
idx = m.index
tag = np.asarray(m.day)
nd = int(tag[-1]) + 1
letzte = np.r_[np.flatnonzero(np.diff(tag) != 0), len(idx) - 1]            # letzte Kerze je Tag
TAKER, REB = 0.0008, 0.85
eig = {}
for kosten, slip in (("slip_5bp", np.full(10, 0.0005)), ("slip_yubit", ky)):
    kum = np.zeros(nd)
    for j, coin in enumerate(m.coins):
        st = m.h1[coin]["close"]
        ziel_h = np.sign(st / st.shift(336) - 1).fillna(0.0)
        ziel_h.index = ziel_h.index + pd.Timedelta(hours=1)                # bekannt bei Stundenschluss
        ziel = ziel_h.reindex(idx.union(ziel_h.index)).ffill().reindex(idx).fillna(0.0).to_numpy()
        o, c, f = m.o[j], m.c[j], m.fund[j]
        S = 1.0 / 10
        bar, vol, fu, pos, halt = 0.0, 0.0, 0.0, 0.0, 0.0
        wert = np.zeros(nd)
        e = 0
        for t in range(len(idx)):
            z = 0.0 if t == len(idx) - 1 else ziel[t]
            if t > 0 and z != halt:
                q = -pos + z * S / o[t]
                px = o[t] * (1.0 + np.sign(q) * slip[j])
                bar -= q * px
                vol += abs(q) * px
                pos += q
                if abs(pos) < 1e-15:
                    pos = 0.0
                halt = z
            if f[t] != 0.0 and pos != 0.0:
                fu -= pos * o[t] * f[t]
            if t == letzte[e]:
                wert[e] = bar + pos * c[t] - TAKER * (1 - REB) * vol + fu
                e += 1
        kum += wert
    eig[kosten] = pd.Series(np.diff(np.r_[0.0, kum]), index=m.days)
pd.DataFrame(eig).to_csv(f"{AUS}/eigen_kandidat.csv", float_format="%.12g")
print("fertig")
