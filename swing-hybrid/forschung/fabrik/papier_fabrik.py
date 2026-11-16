"""Papier-Test (Schattentest) für einen Kandidaten der Strategie-Fabrik.

Diese Datei und der Ordner fabrik/ daneben sind eine eingefrorene Kopie des Codes vom Tag der Freigabe. Der Test rechnet
mit genau diesem Stand weiter, auch wenn die Fabrik später neue Signale bekommt. Gerechnet wird wie in der Rückrechnung:
dieselben Signal-, Einstiegs- und Simulator-Funktionen, nur auf einem Datenfenster aus den täglich veröffentlichten
Binance-Archivdateien (ein Tag Verzug, keine Orders). Braucht numpy, pandas und numba.
"""
import datetime as dt
import hashlib
import json
import sys
import tempfile
import zipfile
import io
from pathlib import Path

import numpy as np
import pandas as pd

HIER = Path(__file__).resolve().parent
sys.path.insert(0, str(HIER))
from fabrik import daten as D, generator as G, kern as FK, lauf as L, signale as S

ARCHIV = "https://data.binance.vision/data/futures/um"
UTC = dt.timezone.utc


def pruefsumme(cfg) -> str:
    h = hashlib.sha256()
    for p in sorted(HIER.rglob("*.py")):
        h.update(p.name.encode()); h.update(p.read_bytes())
    h.update(json.dumps(cfg["kandidat"], sort_keys=True).encode())
    return h.hexdigest()


def _csv(inhalt, namen, n):
    with zipfile.ZipFile(io.BytesIO(inhalt)) as z:
        roh = z.read(z.namelist()[0])
    kopf = roh[:1].decode("ascii", "ignore").isalpha()
    d = pd.read_csv(io.BytesIO(roh), header=0 if kopf else None)
    d = d.iloc[:, :n]
    d.columns = namen[:n]
    return d


def fenster(cfg, tage, cache, R):
    """Lädt je benötigtem Coin die Archivdateien der Tage und baut die Reihen auf dem 5-Minuten-Raster (wie fabrik/daten.py)."""
    raster = pd.date_range(pd.Timestamp(tage[0]), pd.Timestamp(tage[-1]) + pd.Timedelta(hours=23, minutes=55), freq="5min")
    n, nc = len(raster), len(D.COINS)
    f64 = {k: np.full((nc, n), np.nan) for k in ("o", "h", "l", "c")}
    f32 = {k: np.full((nc, n), np.nan, np.float32) for k in ("qv", "tq", "tqv", "frate", "oi", "konten_ls", "profis_ls", "taker_log", "prem", "b1", "a1", "b3", "a3", "b5", "a5", "b1l", "a1l")}
    fcum, gueltig, bis, ausstehend, luecken_archiv = np.zeros((nc, n)), np.zeros((nc, n), bool), None, set(), []
    art = cfg["daten"]
    for j in sorted(set(cfg["coin_index"]) | {0, 1}):                 # BTC und ETH immer (Leitmärkte, BTC-Filter)
        sym = D.COINS[j] + "USDT"
        je_tag = []
        for tag in tage:
            stueck = {"k": R.holen(f"{ARCHIV}/daily/klines/{sym}/5m/{sym}-5m-{tag}.zip", cache / "kerzen" / f"{sym}-{tag}.zip")}
            if "minuten" in art:
                stueck["m1"] = R.holen(f"{ARCHIV}/daily/klines/{sym}/1m/{sym}-1m-{tag}.zip", cache / "minuten" / f"{sym}-{tag}.zip")
            if "aufschlag" in art:
                stueck["prem"] = R.holen(f"{ARCHIV}/daily/premiumIndexKlines/{sym}/5m/{sym}-5m-{tag}.zip", cache / "aufschlag" / f"{sym}-{tag}.zip")
            if "positionen" in art:
                stueck["met"] = R.holen(f"{ARCHIV}/daily/metrics/{sym}/{sym}-metrics-{tag}.zip", cache / "positionen" / f"{sym}-{tag}.zip")
            if "tiefe" in art and j in cfg["coin_index"]:
                stueck["tiefe"] = R.holen(f"{ARCHIV}/daily/bookDepth/{sym}/{sym}-bookDepth-{tag}.zip", cache / "tiefe" / f"{sym}-{tag}.zip")
            je_tag.append(stueck)
        # Datenstand des Coins: der letzte Tag, bis zu dem jede benötigte Art schon einmal veröffentlicht ist. Ein einzelner fehlender
        # Tag davor ist eine Lücke im Archiv (Werte fehlen dann, wie in der Rückrechnung), kein Ende des Datenstands.
        letzte = [max((i for i, st in enumerate(je_tag) if st[a] is not None), default=-1) for a in je_tag[0]]
        ende = min(letzte)
        letzter = tage[ende] if ende >= 0 else None
        teile = {a: [st[a] for st in je_tag[:ende + 1] if st.get(a) is not None] for a in ("k", "m1", "prem", "met", "tiefe")}
        for i, st in enumerate(je_tag[:ende + 1]):
            for a, v in st.items():
                if v is None:
                    luecken_archiv.append(f"{sym} {tage[i]}: Archivdatei fehlt ({a})")
        bis = letzter if bis is None or (letzter is not None and letzter < bis) else bis
        if letzter is None:
            bis = tage[0] - dt.timedelta(days=1)
            continue
        KS = ["open_time", "open", "high", "low", "close", "volume", "close_time", "quote_volume", "count", "taker_base", "taker_quote"]
        k = pd.concat([_csv(c, KS, 11) for c in teile["k"]])
        k.index = pd.to_datetime(k["open_time"].astype("int64"), unit="ms")
        k = k[~k.index.duplicated()].reindex(raster)
        for x, sp in (("o", "open"), ("h", "high"), ("l", "low"), ("c", "close")):
            f64[x][j] = k[sp].astype(float).to_numpy()
        gueltig[j] = np.isfinite(f64["c"][j])
        cf = pd.Series(f64["c"][j]).ffill().to_numpy()
        for x in ("o", "h", "l", "c"):
            f64[x][j] = np.where(gueltig[j], f64[x][j], cf)
        f32["qv"][j] = k["quote_volume"].astype(float).to_numpy()
        if teile["m1"]:
            m = pd.concat([_csv(c, KS, 11) for c in teile["m1"]])
            m.index = pd.to_datetime(m["open_time"].astype("int64"), unit="ms")
            g = m[~m.index.duplicated()][["taker_quote", "quote_volume"]].astype(float).resample("5min").sum(min_count=1).reindex(raster)
            f32["tq"][j], f32["tqv"][j] = g["taker_quote"].to_numpy(), g["quote_volume"].to_numpy()
        if teile["prem"]:
            p = pd.concat([_csv(c, KS, 5) for c in teile["prem"]])
            p.index = pd.to_datetime(p["open_time"].astype("int64"), unit="ms")
            f32["prem"][j] = p[~p.index.duplicated()]["close"].astype(float).reindex(raster).to_numpy()
        if teile["met"]:
            m = pd.concat([_csv(c, ["create_time", "symbol", "oi", "oi_wert", "profis_konten", "profis_ls", "konten_ls", "taker"], 8) for c in teile["met"]])
            m.index = pd.to_datetime(m["create_time"])
            m = m[~m.index.duplicated()].sort_index()
            st = pd.DataFrame({"oi": m["oi"].astype(float).resample("1h").last(), "konten_ls": m["konten_ls"].astype(float).resample("1h").last(),
                               "profis_ls": m["profis_ls"].astype(float).resample("1h").last(), "taker_log": np.log(m["taker"].astype(float)).resample("1h").mean()})
            st.index = st.index + pd.Timedelta(hours=1)               # Stundenwert erst ab der Folgestunde nutzbar
            for sp in st.columns:
                f32[sp][j] = st[sp].reindex(raster, method="ffill", limit=12).to_numpy()
        if teile["tiefe"]:
            t = pd.concat([_csv(c, ["zeit", "stufe", "menge", "wert"], 4) for c in teile["tiefe"]])
            t["zeit"] = pd.to_datetime(t["zeit"]); t["stufe"] = t["stufe"].astype(float).astype(int)
            piv = t.pivot_table(index="zeit", columns="stufe", values="wert", aggfunc="last").resample("5min", label="left", closed="left").mean().astype("float32").reindex(raster)
            for stufe in (1, 3, 5):
                f32[f"b{stufe}"][j], f32[f"a{stufe}"][j] = piv[-stufe].to_numpy(), piv[stufe].to_numpy()
            letzt = t[t["stufe"].isin((-1, 1))].pivot_table(index="zeit", columns="stufe", values="wert", aggfunc="last").resample("5min", label="left", closed="left").last().astype("float32").reindex(raster)
            f32["b1l"][j], f32["a1l"][j] = letzt[-1].to_numpy(), letzt[1].to_numpy()      # letzter Schnappschuss der Kerze (Signale der Generation 4)
        raten = {}
        for monat in sorted({str(t)[:7] for t in tage}):
            f = R.funding_monat(sym, monat, cache)
            if f is None:
                ausstehend.add(monat)
            else:
                raten.update(f)
        if raten:
            fr = pd.Series(raten); fr.index = pd.to_datetime(fr.index, unit="ms").floor("5min")
            r = fr[~fr.index.duplicated()].reindex(raster)
            fcum[j] = r.fillna(0.0).cumsum().to_numpy()
            f32["frate"][j] = r.ffill().shift(1).to_numpy()
    return raster, {**f64, **f32, "fcum": fcum, "gueltig": gueltig}, bis, ausstehend, luecken_archiv


def lauf(ordner, cfg, steuer, basis, heute, cache, schreiben, R, tmp=None):
    if pruefsumme(cfg) != cfg["strategie_sha256"]:
        return {**basis, "status": "Fehler", "fehler": ["Der eingefrorene Code oder die Einstellung dieses Tests wurde verändert. Der Test läuft erst weiter, wenn der Stand der Freigabe wiederhergestellt ist."]}
    if steuer["status"] == "pausiert":
        return {**basis, "status": "pausiert", "fehler": []}
    cache = Path(cache) if cache else R.HIER / ".cache"
    start = pd.Timestamp(cfg["start"]).tz_localize(None)
    heute = heute or dt.datetime.now(UTC).date()
    erster = (start - pd.Timedelta(days=cfg["vorlauf_tage"])).date()
    tage = [erster + dt.timedelta(days=i) for i in range((heute - erster).days)]
    luecken, fehler = [], []
    raster, felder, bis, ausstehend, luecken_archiv = fenster(cfg, tage, cache, R)
    luecken += luecken_archiv[:10]
    if bis is None or bis < erster:
        return R.abrechnen(cfg, basis, steuer, [], None, R.ms(cfg["start"]), luecken, fehler)[0] | {"status": "wartet auf Daten"}
    n = int((pd.Timestamp(bis) + pd.Timedelta(days=1) - raster[0]) / pd.Timedelta(minutes=5))
    live = cfg.get("modus") == "live"
    if live:
        # Live-Betrieb: Der laufende Tag ist unvollständig. Das Fenster endet an der letzten Kerze, die für alle gebrauchten Coins vorliegt.
        # Dahinter stehen zwei Platzhalter-Kerzen zum letzten Schlusskurs (der Simulator braucht sie, um einen Einstieg oder Ausstieg
        # "jetzt", zur Eröffnung der laufenden Kerze, zu buchen). Sie tragen keine neue Information; im nächsten Lauf ersetzen echte Kerzen sie.
        brauch = sorted(set(cfg["coin_index"]) | {0, 1})
        da = np.flatnonzero(felder["gueltig"][brauch][:, :n].all(axis=0))
        if len(da) == 0 or len(raster) < int(da[-1]) + 3:
            return R.abrechnen(cfg, basis, steuer, [], None, R.ms(cfg["start"]), luecken, fehler)[0] | {"status": "wartet auf Daten"}
        letzte = int(da[-1])
        n = letzte + 3
        felder["gueltig"][:, letzte + 1:n] = felder["gueltig"][:, letzte:letzte + 1]
    raster = raster[:n]
    with tempfile.TemporaryDirectory(dir=tmp) as td:                  # eigener kleiner Datenspeicher nur für diesen Lauf
        D.SPEICHER, D.RASTER, D.N = Path(td), raster, n
        for name, a in felder.items():
            np.save(D.SPEICHER / f"{name}.npy", a[:, :n])
        np.save(D.SPEICHER / "slip_bp.npy", np.array([cfg["kosten"]["slippage_bp_je_order"].get(c, 99.0) for c in D.COINS]))
        np.lib.format.open_memmap(D.SPEICHER / "signale.npy", mode="w+", dtype=np.float32, shape=(len(S.NAMEN), len(D.COINS), n))
        np.lib.format.open_memmap(D.SPEICHER / "filter.npy", mode="w+", dtype=np.int8, shape=(4, len(D.COINS), n))
        np.lib.format.open_memmap(D.SPEICHER / "sigma.npy", mode="w+", dtype=np.float32, shape=(len(D.COINS), n))
        for j in cfg["coin_index"]:
            S._coin(j)
        L._g.clear(); L._init(); L.I_ENDE = n
        kd = cfg["kandidat"]
        a = {"si": S.NAMEN.index(kd["signal"]), "signal": kd["signal"], "th": kd["th"], "r": kd["r"], "f": kd["f"], "k": kd["k"]}
        if kd.get("best"):
            a["best"] = {"si": S.NAMEN.index(kd["best"][0]), "signal": kd["best"][0], "th": kd["best"][1], "r": kd["best"][2]}
        halte, sl, tp, tr, ta, sx = kd["ausstieg"]
        i0 = int((start - raster[0]) / pd.Timedelta(minutes=5)) - 1    # Signal am Schluss der Kerze vor dem Start -> Einstieg zur Starteröffnung
        ende_ms = R.ms(steuer["ende"]) if steuer["status"] == "beendet" else None
        k, gebuehr = cfg["kosten"], 2 * cfg["kosten"]["taker_bp"]
        zeit = np.array([int(t.timestamp() * 1000) for t in raster.tz_localize("UTC")])
        trades = []
        for j in cfg["coin_index"]:
            coin = D.COINS[j]
            ein, wert = L.einstieg(a, j)
            o, h, l = (np.asarray(L._g[x][j], dtype=np.float64) for x in ("o", "h", "l"))
            aus = np.zeros((5000, 6))
            m = FK.trades_liste(o, h, l, np.zeros(n), ein, wert, np.asarray(L._g["sigma"][j]), max(i0, 0), n, halte, sl, tp, tr, ta, np.nan if sx is None else sx, np.zeros(n), aus)
            fc = np.asarray(L._g["fcum"][j])
            cc = np.asarray(L._g["c"][j], dtype=np.float64)
            je_order = np.maximum(k["slippage_bp_je_order"][coin], k.get("slippage_anteil_spanne", 0.0) * (h - l) / cc * 1e4)   # Slippage wächst mit der Spanne der letzten Kerze
            for e in aus[:m]:
                ia, ib, d, offen = int(e[0]), int(e[1]), e[2], bool(e[5])
                if live and ia >= n - 1:
                    continue                                          # Einstieg erst in der zweiten Platzhalter-Kerze: liegt in der Zukunft
                if live and ib >= n - 2:
                    offen = True                                      # Ausstieg in einer Platzhalter-Kerze: gilt erst, wenn die echte Kerze vorliegt (Kurs steht dann fest)
                if zeit[ia] < R.ms(cfg["start"]) or (ende_ms is not None and zeit[ia] >= ende_ms):
                    continue
                fund = -d * (fc[ib] - fc[ia]) * 1e4
                pend = any(str(raster[x])[:7] in ausstehend for x in (ia, ib))
                slip = float(je_order[ia - 1] + je_order[ib - 1])
                trades.append({"trade_id": f"{cfg['id']}|{coin}|{zeit[ia]}", "coin": coin, "ein": int(zeit[ia]), "aus": None if offen else int(zeit[ib]), "richtung": float(d),
                               "ein_kurs": float(o[ia]), "aus_kurs": float(o[ia] * (1 + d * e[3] / 1e4)), "z": round(float(wert[ia - 1] * a["r"]), 3), "offen": offen,
                               "roh_bp": float(e[3]), "slip_bp": slip, "funding_bp": float(fund), "funding_ausstehend": pend, "schlimmst_bp": round(float(e[4]), 1),
                               "n85_bp": float(e[3]) - slip + fund - gebuehr * (1 - k["rebate"]), "n0_bp": float(e[3]) - slip + fund - gebuehr})
        liste = [(c, np.asarray(L._g["gueltig"][D.COINS.index(c)])) for c in cfg["coins"]]
        for c, g in liste:
            if not g[max(i0, 0):].all():
                luecken.append(f"{c}: {int((~g[max(i0, 0):]).sum())} fehlende 5-Minuten-Kerzen seit dem Start.")
    trades.sort(key=lambda t: (t["ein"], t["coin"]))
    daten_bis = int(zeit[-2]) if live else int(zeit[-1])            # live: Eröffnung der laufenden Kerze
    fehlend = (heute - dt.timedelta(days=1) - bis).days
    if fehlend > 3:
        luecken.append(f"Archivdaten fehlen seit {fehlend} Tagen (letzter Stand {bis}).")
    stand, gebucht = R.abrechnen(cfg, basis, steuer, trades, daten_bis, R.ms(cfg["start"]), luecken, fehler)
    if schreiben:
        R.speichern(cfg["id"], stand, gebucht)
    return stand
