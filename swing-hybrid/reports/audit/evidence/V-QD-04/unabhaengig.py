"""V-QD-04: unabhaengige Nachrechnung des Befunds QD-04 (Hebel 3 ohne Tageslimit).

Bewusst OHNE src/hybrid (kein engine2, kein research.lauf): eigener kleiner Rechenkern in numpy, der die Regeln des
Papier-Bots nachstellt (vorwaertstest/bot.py):
- Signal: Schluss der letzten vollen Stunde gegen Schluss 336 Stunden davor (zeitgenau, nicht zeilenweise).
- Groesse je Einstieg fest: Startkapital x Hebel / 10, Stueckzahl zum Kurs beim Einstieg, bis zur Umkehr unveraendert.
- Sofortausfuehrung zum Open der ersten 5-Minuten-Kerze der neuen Stunde plus Slippage je Coin (2 x halbe Yubit-Spanne,
  mindestens 0,5 bp), Taker 0,08 % auf den Positionswert, Rebate 85 %, Funding je Abrechnungszeitpunkt.
- Kein Tageslimit, keine Liquidation (wie der Papier-Bot mit tagesverlust_limit 1.0).
Nur lesend auf data/; schreibt ausschliesslich in das per Argument uebergebene Ausgabeverzeichnis.
"""
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path("/home/user/OdinGate-Botv134/swing-hybrid")
AUS = Path(sys.argv[1])
A = ["BTC", "ETH", "SOL", "XRP", "DOT", "DOGE", "ADA", "LINK", "AVAX", "LTC"]
START, ENDE, SPLIT = "2021-08-15", "2026-10-24", "2025-04-01"
TAKER, REBATE, L = 0.0008, 0.85, 336
t0 = time.time()
idx = pd.date_range(START, ENDE, freq="5min", inclusive="left")
T, N = len(idx), len(A)
i_split = int(idx.searchsorted(pd.Timestamp(SPLIT)))


def lesen(ordner, coin):
    teile = [pd.read_parquet(ROOT / "data/candles" / o / f"{coin}USDT.parquet") for o in (ordner + "_vor", ordner)]
    d = pd.concat(teile)
    d.index = d.index.astype("datetime64[ns]")
    return d[~d.index.duplicated()].sort_index()


sp = pd.read_csv(ROOT / "data/processed/yubit_spannen_stichprobe.csv")
sp["halb"] = (sp["brief"] - sp["geld"]) / (sp["brief"] + sp["geld"])
halb = sp.groupby("symbol")["halb"].mean()
SLIP = np.array([max(0.00005, 2.0 * float(halb[c + "USDT"])) for c in A])

O = np.empty((N, T)); C = np.empty((N, T)); LO = np.empty((N, T)); HI = np.empty((N, T)); F = np.zeros((N, T)); W = np.zeros((N, T))
luecken = {}
for j, coin in enumerate(A):
    d = lesen("5m", coin)
    k = d.reindex(idx)
    fehlt = k["close"].isna()
    cl = k["close"].ffill().bfill()
    O[j] = k["open"].where(~fehlt, cl).to_numpy(); C[j] = cl.to_numpy()
    LO[j] = k["low"].where(~fehlt, cl).to_numpy(); HI[j] = k["high"].where(~fehlt, cl).to_numpy()
    h = d["close"].resample("1h").last()                       # Index = Stundenbeginn, Wert = Schluss der Stunde
    sig = np.sign(h - h.shift(freq=pd.Timedelta(hours=L)).reindex(h.index)).fillna(0.0)   # zeitgenau 336 h
    sig.index = sig.index + pd.Timedelta(hours=1)              # gilt ab der Folgestunde
    W[j] = sig.reindex(idx.union(sig.index)).ffill().reindex(idx).fillna(0.0).to_numpy()
    fr = lesen("funding", coin)["rate"]
    fr.index = fr.index.floor("5min")
    F[j] = fr[~fr.index.duplicated()].reindex(idx).fillna(0.0).to_numpy()
    luecken[coin] = {"fehlende_5m_kerzen": int(fehlt.sum()), "fehlende_stunden": int(h.loc[START:ENDE].isna().sum())}
print("Slippage je Coin (bp):", dict(zip(A, np.round(SLIP * 1e4, 2))))
print("Datenluecken:", luecken)


def pfad(s0, e0, hebel):
    """Kontoverlauf ab Neustart in Kerze s0 (flach, sofortiger Einstieg nach Signal) bis e0. Einheiten des Startkapitals.
    Gibt (netto mit Rebate, netto ohne Rebate) je 5-Minuten-Kerze zurueck."""
    S = hebel / N
    n = e0 - s0
    brutto = np.zeros(n); tv = np.zeros(n); fu = np.zeros(n)
    for j in range(N):
        tg = W[j, s0:e0]
        b = np.concatenate([[0], np.flatnonzero(tg[1:] != tg[:-1]) + 1])
        d = tg[b]; p = O[j, s0 + b]
        u = d * S / p                                           # Stueckzahl fest ab Einstieg
        dq = np.diff(np.concatenate([[0.0], u]))
        px = p * (1.0 + np.sign(dq) * SLIP[j])
        laenge = np.diff(np.concatenate([b, [n]]))
        uf = np.repeat(u, laenge)
        brutto += np.repeat(np.cumsum(-dq * px), laenge) + uf * C[j, s0:e0]
        tv += np.repeat(np.cumsum(np.abs(dq) * px), laenge)
        vor = np.concatenate([[0.0], uf[:-1]])                  # Position vor dem Handel dieser Kerze
        fu += np.cumsum(-vor * O[j, s0:e0] * F[j, s0:e0])
    return brutto - TAKER * (1 - REBATE) * tv + fu, brutto - TAKER * tv + fu


def einbruch_rel(eq):
    konto = 1.0 + eq
    spitze = np.maximum.accumulate(np.maximum(konto, 1.0))
    return float(((spitze - konto) / spitze).max())


def rueckgang_abs(eq):
    return float((np.maximum.accumulate(np.maximum(eq, 0.0)) - eq).max())


out = {"slip_bp": dict(zip(A, (SLIP * 1e4).round(3).tolist())), "luecken": luecken}
print("\n=== 1. Durchgehender Lauf ab 2021-08-15 (eigener Rechenkern)")
for hebel in (1.0, 3.0):
    mit, ohne = pfad(0, T, hebel)
    tag = pd.Series(mit, index=idx).resample("1D").last()
    tg = tag.diff().fillna(tag.iloc[0])
    for nm, a, b in (("Entwicklung", 0, i_split), ("Pruefzeitraum", i_split, T)):
        basis = mit[a - 1] if a > 0 else 0.0
        seg = mit[a:b] - basis
        x = tg[(tg.index >= idx[a].normalize()) & (tg.index <= idx[b - 1].normalize())]
        tage = (b - a) / 288
        e = {"N": float(seg[-1]), "N_jahr": float(seg[-1] / tage * 365), "sharpe": float(x.mean() / x.std() * np.sqrt(365)),
             "einbruch_rel": einbruch_rel(seg), "rueckgang_abs": rueckgang_abs(seg), "schlechtester_tag": float(x.min()),
             "schlechtester_tag_datum": str(x.idxmin().date()), "tief_konto": float(seg.min())}
        out[f"durchgehend_hebel{hebel:g}_{nm}"] = e
        print(f"Hebel {hebel:g} {nm:14s} N {e['N']:+.3f} ({e['N_jahr']:+.3f}/Jahr) Sharpe {e['sharpe']:.3f}  Einbruch rel. zum Hoechststand "
              f"{e['einbruch_rel']:.3f}  groesster Rueckgang (Startkapital) {e['rueckgang_abs']:.3f}  schlechtester Tag {e['schlechtester_tag']:+.3f} am {e['schlechtester_tag_datum']}")
    # groesster Tagesverlust innerhalb eines UTC-Tags (ohne Rebate, wie die Limit-Pruefung des Bots)
    s = pd.Series(ohne, index=idx)
    tagstart = s.groupby(idx.normalize()).transform("first")
    intr = (s - tagstart)
    print(f"Hebel {hebel:g}: groesster Verlust innerhalb eines UTC-Tags (ohne Rebate, 5-Minuten-Werte) {intr.min():+.3f} am {intr.idxmin()}")
    out[f"intratag_min_hebel{hebel:g}"] = {"wert": float(intr.min()), "zeit": str(intr.idxmin())}


def neustarts(schritt_tage, hebel=3.0, name=""):
    starts = np.arange(0, T - 288 * 30, 288 * schritt_tage)
    z = []
    for s0 in starts:
        e0 = min(T, s0 + 288 * 365)
        mit, ohne = pfad(s0, e0, hebel)
        unter = np.flatnonzero(mit <= -1.0)
        s = pd.Series(ohne, index=idx[s0:e0])
        intr = float((s - s.groupby(s.index.normalize()).transform("first")).min())
        z.append({"start": idx[s0], "tief_365": float(mit.min()), "tief_zeit": idx[s0 + int(mit.argmin())],
                  "stand_ende": float(mit[-1]), "tage": (e0 - s0) / 288,
                  "erstes_unter_minus100": idx[s0 + int(unter[0])] if len(unter) else pd.NaT,
                  "tage_bis_minus100": float(unter[0] / 288) if len(unter) else np.nan,
                  "hoch_vor_tief": float(mit[: int(mit.argmin()) + 1].max()), "intratag_min_ohne": intr})
    return pd.DataFrame(z).set_index("start")


def bericht(z, titel):
    print(f"\n--- {titel}")
    voll = z[z["tage"] >= 364.9]
    sp_ = pd.Timestamp(SPLIT)
    e = {}
    for nm, d in (("alle Starttage", z), ("nur volle 365 Tage", voll), ("Starts im Pruefzeitraum", z[z.index >= sp_]),
                  ("Starts in der Entwicklung (volle 365 Tage)", voll[voll.index < sp_])):
        r = {"starts": int(len(d)), **{f"tief_le_{int(g * 100)}": float((d["tief_365"] <= -g).mean()) for g in (0.3, 0.5, 0.75, 1.0)},
             "median_tief": float(d["tief_365"].median()), "median_stand_ende": float(d["stand_ende"].median())}
        e[nm] = r
        print(f"{nm:44s} n={r['starts']:4d}  <= -30 %: {r['tief_le_30']:.3f}  <= -50 %: {r['tief_le_50']:.3f}  <= -75 %: {r['tief_le_75']:.3f}  "
              f"<= -100 %: {r['tief_le_100']:.3f}  Median Tief {r['median_tief']:+.2f}  Median Stand am Ende {r['median_stand_ende']:+.2f}")
    return e


print("\n=== 2. Neustart mit Hebel 3, feste Groesse, kein Tageslimit; Kontotief (5-Minuten-Schlusskurse) in den folgenden 365 Tagen")
z7 = neustarts(7)
out["neustart_7_tage"] = bericht(z7, "Start an jedem 7. Tag (Raster des Pruefers)")
z7.round(4).to_csv(AUS / "neustart_hebel3_unabhaengig.csv")
z1 = neustarts(1)
out["neustart_taeglich"] = bericht(z1, "Start an jedem Tag")
z1.round(4).to_csv(AUS / "neustart_hebel3_taeglich.csv")
print(f"\ngroesster Verlust innerhalb eines UTC-Tags ueber alle Neustart-Pfade (ohne Rebate): 7-Tage-Raster {z7['intratag_min_ohne'].min():+.3f}, taeglich {z1['intratag_min_ohne'].min():+.3f}"
      f"  -> Limit des Bots (-1,00) {'waere ausgeloest worden' if min(z7['intratag_min_ohne'].min(), z1['intratag_min_ohne'].min()) <= -1.0 else 'waere nie ausgeloest worden'}")
out["intratag_min_neustart"] = {"raster7": float(z7["intratag_min_ohne"].min()), "taeglich": float(z1["intratag_min_ohne"].min())}

print("\n=== 3. Wie viele unabhaengige Ereignisse stecken hinter den Totalverlusten? (taegliche Starts)")
r = z1.dropna(subset=["erstes_unter_minus100"]).copy()
r["monat"] = r["erstes_unter_minus100"].dt.to_period("M").astype(str)
grp = r.groupby("monat").agg(starts=("tief_365", "size"), erster_start=("tage", lambda x: str(x.index.min().date())),
                             letzter_start=("tage", lambda x: str(x.index.max().date())), median_tage_bis=("tage_bis_minus100", "median"))
print("Monat, in dem das Konto erstmals <= -100 % steht -> Anzahl betroffener Starttage:")
print(grp.to_string())
out["ruin_monate"] = {k: int(v) for k, v in grp["starts"].items()}
print(f"Tage vom Start bis zum ersten Stand <= -100 %: Minimum {r['tage_bis_minus100'].min():.1f}, Median {r['tage_bis_minus100'].median():.1f}, Maximum {r['tage_bis_minus100'].max():.1f}")
print(f"Anteil der Totalverlust-Starts, bei denen das Konto vor dem Tief nie ueber +10 % lag: {(r['hoch_vor_tief'] < 0.10).mean():.2f}")
jahr = z1.assign(jahr=z1.index.year).groupby("jahr").agg(starts=("tief_365", "size"), le50=("tief_365", lambda x: float((x <= -0.5).mean())),
                                                           le100=("tief_365", lambda x: float((x <= -1.0).mean())))
print("\nnach Startjahr (taegliche Starts): Anteil mit Kontotief <= -50 % / <= -100 %")
print(jahr.round(3).to_string())
out["nach_startjahr"] = jahr.round(4).to_dict("index")

print("\n=== 4. Dieselbe Neustart-Rechnung fuer andere Hebel (nur zur Einordnung, keine Auswahl)")
for hb in (0.2, 1.0, 2.0):
    zz = neustarts(7, hebel=hb)
    r_ = {f"tief_le_{int(g * 100)}": float((zz["tief_365"] <= -g).mean()) for g in (0.3, 0.5, 0.75, 1.0)}
    out[f"neustart_hebel{hb:g}"] = {**r_, "median_tief": float(zz["tief_365"].median()), "schlechtestes_tief": float(zz["tief_365"].min())}
    print(f"Hebel {hb:g}: <= -30 %: {r_['tief_le_30']:.3f}  <= -50 %: {r_['tief_le_50']:.3f}  <= -75 %: {r_['tief_le_75']:.3f}  <= -100 %: {r_['tief_le_100']:.3f}  "
          f"Median Tief {zz['tief_365'].median():+.3f}  schlechtestes Tief {zz['tief_365'].min():+.3f}")

json.dump(out, open(AUS / "unabhaengig.json", "w"), indent=1, default=str)
print(f"\nfertig nach {time.time() - t0:.0f} s")
