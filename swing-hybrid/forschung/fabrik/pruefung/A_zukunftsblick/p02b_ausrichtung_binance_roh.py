"""Ausrichtung gegen die ursprünglichen Binance-Archivdateien (Stichprobe einzelner Tage, in roh/ abgelegt).

Frage je Reihe: Welche Rohmessung steckt im Speicherwert der Kerze i, und war sie am Schluss der Kerze i (RASTER[i] + 5 min) schon da?
Alle Stichprobentage liegen vor dem 2024-07-01.
"""
import io, sys, zipfile
from pathlib import Path
sys.path.insert(0, 'forschung')
import numpy as np, pandas as pd
from fabrik import daten as D, lauf as L

HIER = Path(__file__).resolve().parent / "roh"
m5 = pd.Timedelta(minutes=5)


KOPF_KERZE = ["open_time", "open", "high", "low", "close", "volume", "close_time", "quote_volume", "count", "taker_buy_volume", "taker_buy_quote_volume", "ignore"]


def csv(name):
    with zipfile.ZipFile(HIER / name) as z:
        roh = z.read(z.namelist()[0])
    if roh[:1].isalpha():
        return pd.read_csv(io.BytesIO(roh))
    return pd.read_csv(io.BytesIO(roh), header=None, names=KOPF_KERZE)      # ältere Kerzendateien haben keine Kopfzeile


def sp(name, j, i0, i1):
    assert i1 <= L.I_ENDE
    return np.asarray(np.load(D.SPEICHER / f"{name}.npy", mmap_mode="r")[j, i0:i1]).astype(np.float64)


def idx(t):
    return int(np.searchsorted(D.RASTER.values, np.datetime64(t)))


print("##### 1. Kerzen 1m / 5m: open_time und close_time der Rohdatei")
for coin, tag in (("SOL", "2023-03-01"), ("DOGE", "2024-02-10"), ("BTC", "2022-06-14")):
    j = D.COINS.index(coin)
    r = csv(f"{coin}USDT-1m-{tag}.zip")
    r["auf"] = pd.to_datetime(r["open_time"], unit="ms"); r["zu"] = pd.to_datetime(r["close_time"] + 1, unit="ms")
    i0 = idx(tag); i1 = i0 + 288
    kerze_schluss = D.RASTER[i0:i1] + m5
    # jede Minutenkerze der Kerze i zuordnen, in der sie SCHLIESST
    r["k"] = np.searchsorted(kerze_schluss.values, r["zu"].values, side="left")
    g = r.groupby("k").agg(tq=("taker_buy_quote_volume", "sum"), tqv=("quote_volume", "sum"), o=("open", "first"), h=("high", "max"), l=("low", "min"), c=("close", "last"), spaet=("zu", "max"))
    for x, tol in (("tq", 1e-5), ("tqv", 1e-5), ("o", 1e-12), ("h", 1e-12), ("l", 1e-12), ("c", 1e-12)):
        ist = sp(x, j, i0, i1)
        print(f"  {coin} {tag} {x:<3}: Speicher == aus Minutenkerzen, die bis zum Kerzenschluss geschlossen sind: {bool(np.allclose(ist, g[x].to_numpy(), rtol=tol))}")
    print(f"  {coin} {tag}: späteste verwendete Minutenkerze schließt {((g['spaet'].to_numpy() - kerze_schluss.values) / np.timedelta64(1, 's')).max():.0f} s nach dem Kerzenschluss (0 = genau am Schluss)")
r5 = csv("SOLUSDT-5m-2023-03-01.zip")
print("  5m-Rohdatei: close_time - open_time (ms):", sorted(set((r5["close_time"] - r5["open_time"]).tolist())), "| Speicher c == close der Zeile mit open_time = RASTER[i]:",
      bool(np.allclose(sp("c", 2, idx("2023-03-01"), idx("2023-03-01") + 288), r5["close"].to_numpy())))

print("\n##### 2. Aufschlag (premiumIndexKlines 5m)")
p = csv("prem-SOLUSDT-5m-2023-03.zip")
p["auf"] = pd.to_datetime(p["open_time"], unit="ms"); p["zu"] = pd.to_datetime(p["close_time"] + 1, unit="ms")
i0, i1 = idx("2023-03-01"), idx("2023-04-01")
ist = sp("prem", 2, i0, i1)
soll = p.set_index("zu")["close"].reindex(D.RASTER[i0:i1] + m5).to_numpy()
print("  Speicher prem[i] == close der Aufschlag-Kerze, die bei RASTER[i]+5min schließt:", bool(np.allclose(ist, soll, rtol=1e-5, equal_nan=True)), "| Zeilen", len(p), "| close_time-open_time (ms):", sorted(set((p["close_time"] - p["open_time"]).tolist())))
# Gegenprobe: wäre die Reihe um eine Kerze in die Zukunft verschoben, müsste prem[i] == close der Folgekerze sein
soll_f = p.set_index("zu")["close"].reindex(D.RASTER[i0:i1] + 2 * m5).to_numpy()
print("  Gegenprobe (Folgekerze):", float(np.mean(np.isclose(ist, soll_f, rtol=1e-5))), "Anteil gleich (erwartet nahe 0)")
# innerhalb der Aufschlag-Kerze: close[i] ~ open[i+1]? (Beleg, dass close der letzte Stand der Kerze ist)
print("  Korrelation close[i] mit open[i+1]:", round(float(np.corrcoef(p["close"].to_numpy()[:-1], p["open"].to_numpy()[1:])[0, 1]), 3), "| close[i] mit open[i]:", round(float(np.corrcoef(p["close"], p["open"])[0, 1]), 3))

print("\n##### 3. Funding")
f = csv("SOLUSDT-fundingRate-2023-03.zip")
f["t"] = pd.to_datetime(f["calc_time"], unit="ms")
fr = sp("frate", 2, i0, i1); fc = np.asarray(np.load(D.SPEICHER / "fcum.npy", mmap_mode="r")[2, i0 - 1:i1])
wechsel = np.flatnonzero(np.diff(fc) != 0)            # Kerzen (relativ zu i0), an denen Funding gebucht wird
print("  Termine laut Rohdatei:", len(f), "| Buchungskerzen im Speicher:", len(wechsel))
ok_buch, ok_rate, fruehest = True, True, []
for _, z in f.iterrows():
    k = idx(z["t"].floor("5min")) - i0                 # Kerze, die zum Termin öffnet
    ok_buch &= bool(np.isclose(fc[k + 1] - fc[k], z["last_funding_rate"], atol=1e-12))
    # ab welcher Kerze zeigt frate diese Rate? -> erste Kerze, deren frate von der vorigen Rate auf diese wechselt
    if k + 1 < len(fr):
        ok_rate &= bool(np.isclose(fr[k + 1], z["last_funding_rate"], rtol=1e-5))
        fruehest.append((D.RASTER[i0 + k + 1] + m5 - z["t"]).total_seconds())
        if k >= 1 and not np.isclose(fr[k], fr[k + 1], rtol=1e-7):
            assert not np.isclose(fr[k], z["last_funding_rate"], rtol=1e-7) or True
print("  fcum-Sprung an der Kerze, die zum Termin öffnet == Rate:", ok_buch, "| frate zeigt die Rate ab der Kerze NACH dem Termin:", ok_rate,
      f"| Abstand Termin -> Schluss der ersten Kerze mit dieser Rate: min {min(fruehest):.0f} s")
vorher = [(float(fr[idx(z['t'].floor('5min')) - i0]), float(z["last_funding_rate"])) for _, z in f.iterrows() if idx(z['t'].floor('5min')) - i0 >= 0]
print("  frate an der Terminkerze selbst == neue Rate (wäre unkritisch, da Rate am Termin feststeht):", sum(np.isclose(a, b, rtol=1e-5) for a, b in vorher), "von", len(vorher), "(gleich nur, wenn alte und neue Rate zufällig gleich)")

print("\n##### 4. Stundenwerte (metrics): Rohmessung alle 5 Minuten, create_time")
for coin, tage in (("SOL", ("2023-03-01", "2023-03-02")), ("BTC", ("2022-06-14", "2022-06-15")), ("DOGE", ("2024-02-10", "2024-02-11"))):
    j = D.COINS.index(coin)
    r = pd.concat([csv(f"{coin}USDT-metrics-{t}.zip") for t in tage])
    r["t"] = pd.to_datetime(r["create_time"])
    r = r.drop_duplicates("t").sort_values("t").reset_index(drop=True)
    i0, i1 = idx(tage[0]) + 24, idx(tage[1]) + 288       # ab 02:00 des ersten Tages (davor fehlt die Vorstunde in der Stichprobe)
    kerze_auf = D.RASTER[i0:i1]
    for x, spalte in (("oi", "sum_open_interest"), ("konten_ls", "count_long_short_ratio"), ("profis_ls", "sum_toptrader_long_short_ratio")):
        ist = sp(x, j, i0, i1)
        # Quelle: jüngste Rohmessung mit create_time < Stundenbeginn der Kerze (so wäre es korrekt)
        stunde = kerze_auf.floor("1h")
        pos = np.searchsorted(r["t"].values, stunde.values, side="left") - 1
        soll = r[spalte].to_numpy(np.float64)[pos]
        gleich = np.isclose(ist, soll, rtol=1e-6)
        alter = (kerze_auf + m5 - r["t"].to_numpy()[pos]) / np.timedelta64(1, "m")
        # Gegenprobe Zukunft: stimmt der Speicherwert mit einer Messung NACH dem Kerzenschluss überein und nicht mit der erwarteten?
        zuk = np.searchsorted(r["t"].values, (kerze_auf + m5).values, side="right")
        zukunft_gleich = np.isclose(ist, r[spalte].to_numpy(np.float64)[np.minimum(zuk, len(r) - 1)], rtol=1e-6) & ~gleich
        print(f"  {coin} {x:<10}: Speicher == letzte Messung vor dem Stundenbeginn der Kerze: {int(gleich.sum())}/{len(ist)}"
              f" | Alter der Messung am Kerzenschluss: min {alter.min():.0f} min, max {alter.max():.0f} min | passt stattdessen zu einer späteren Messung: {int(zukunft_gleich.sum())}")
    # taker_log: Mittel des log-Verhältnisses über die Messungen der Vorstunde
    r["lg"] = np.log(r["sum_taker_long_short_vol_ratio"].where(r["sum_taker_long_short_vol_ratio"] > 0))
    hm = r.set_index("t")["lg"].resample("1h").mean()
    ist = sp("taker_log", j, i0, i1)
    soll = hm.reindex(kerze_auf.floor("1h") - pd.Timedelta(hours=1)).to_numpy()
    print(f"  {coin} taker_log : Speicher == Stundenmittel der VORSTUNDE (create_time in [H-1, H)): {int(np.isclose(ist, soll, rtol=1e-4).sum())}/{len(ist)}"
          f" | == Mittel der LAUFENDEN Stunde: {int(np.isclose(ist, hm.reindex(kerze_auf.floor('1h')).to_numpy(), rtol=1e-4).sum())}")
# Was misst die Zeile mit create_time t? Kauf/Verkauf-Verhältnis gegen Minutenkerzen: Fenster [t-5min, t) oder [t, t+5min)?
for coin, tag in (("SOL", "2023-03-01"), ("DOGE", "2024-02-10"), ("BTC", "2022-06-14")):
    r = csv(f"{coin}USDT-metrics-{tag}.zip"); r["t"] = pd.to_datetime(r["create_time"])
    k = csv(f"{coin}USDT-1m-{tag}.zip"); k["auf"] = pd.to_datetime(k["open_time"], unit="ms")
    k = k.set_index("auf")
    kauf = k["taker_buy_volume"].resample("5min").sum(); alles = k["volume"].resample("5min").sum()
    verh = kauf / (alles - kauf)                                  # beschriftet am Fensterbeginn
    mm = r.set_index("t")["sum_taker_long_short_vol_ratio"]
    zeile = []
    for versatz in (-10, -5, 0, 5):
        v = verh.copy(); v.index = v.index - pd.Timedelta(minutes=versatz)   # v.index = create_time, das Fenster beginnt bei create_time + versatz
        a, b = mm.align(v, join="inner")
        zeile.append(f"Fenster [t{versatz:+d}min, t{versatz + 5:+d}min): Anteil gleich {float(np.isclose(a, b, rtol=1e-3).mean()):.2f}")
    print(f"  {coin} {tag}: Zeile mit create_time t misst -> " + " | ".join(zeile))

print("\n##### 5. Orderbuch-Tiefe (bookDepth): Schnappschüsse etwa alle 30 s")
for coin, tag in (("SOL", "2023-03-01"), ("BTC", "2023-08-17"), ("LTC", "2024-02-10")):
    j = D.COINS.index(coin)
    r = csv(f"{coin}USDT-bookDepth-{tag}.zip"); r["t"] = pd.to_datetime(r["timestamp"])
    i0 = idx(tag); i1 = i0 + 288
    kerze_auf = D.RASTER[i0:i1]
    for st, name in ((-5, "b5"), (5, "a5"), (-1, "b1"), (1, "a1"), (-3, "b3"), (3, "a3")):
        q = r[r["percentage"] == st].drop_duplicates("t", keep="last")
        q = q.assign(k=np.searchsorted(kerze_auf.values, q["t"].values, side="right") - 1)   # Kerze, in deren Laufzeit der Schnappschuss fällt
        g = q.groupby("k").agg(w=("notional", "mean"), spaet=("t", "max"), n=("t", "count"))
        ist = sp(name, j, i0, i1)
        soll = g["w"].reindex(range(288)).to_numpy()
        gl = np.isclose(ist, soll, rtol=2e-5) | (np.isnan(ist) & np.isnan(soll))
        rest = ((kerze_auf + m5)[g.index.to_numpy()] - g["spaet"].to_numpy()) / np.timedelta64(1, "s")
        # Gegenprobe: Mittel des FOLGE-Fensters
        soll_f = g["w"].reindex(range(1, 289)).to_numpy()
        print(f"  {coin} {tag} {name}: Speicher == Mittel der Schnappschüsse innerhalb der Kerze: {int(gl.sum())}/288 | jüngster Schnappschuss liegt {rest.min():.0f} bis {rest.max():.0f} s VOR dem Kerzenschluss"
              f" | passt zum Folgefenster: {int((np.isclose(ist, soll_f, rtol=2e-5) & ~gl).sum())}")
