"""Papier-Runner der OdinGate-Forschung: führt einen registrierten Vorwärtstest als Schattentest aus.

Schattentest heißt: Das Signal wird aus den täglich veröffentlichten Binance-Archivdateien des Vortags gebildet
(Orderbuch-Tiefe, 5-Minuten-Kerzen), die Trades werden zu Binance-Eröffnungskursen mit dem eingefrorenen Kostenmodell
gebucht. Es werden keine Orders gesendet, an keiner Börse. Der Stand ist jederzeit vollständig aus den öffentlichen
Archivdaten neu berechenbar: Jeder Lauf rechnet den Test vom Start an neu. Dadurch gibt es keine doppelten Orders,
und ein Absturz hinterlässt keinen halben Zustand.

  python3 -m forschung.papier.runner OS-1.1          (aus swing-hybrid/)

Schreibt: forschung/papier/zustand/<ID>.sqlite (transaktional, lokal), forschung/papier/ausgabe/<ID>.json (Dashboard),
          forschung/papier/protokolle/<ID>.log. Nur Standardbibliothek.
"""
import csv
import datetime as dt
import fcntl
import hashlib
import importlib
import io
import json
import os
import shutil
import sqlite3
import sys
import time
import urllib.error
import urllib.request
import zipfile
from pathlib import Path

HIER = Path(__file__).resolve().parent
ARCHIV = "https://data.binance.vision/data/futures/um"
TAG_MS, KERZE_MS = 86_400_000, 300_000
UTC = dt.timezone.utc


def ms(t: str) -> int:
    return int(dt.datetime.fromisoformat(t.replace("Z", "+00:00")).timestamp() * 1000)


def iso(m) -> str:
    return dt.datetime.fromtimestamp(m / 1000, UTC).strftime("%Y-%m-%d %H:%M")


def holen(url: str, cache: Path):
    """Datei aus dem Archiv, mit lokalem Zwischenspeicher. None, wenn sie (noch) nicht veröffentlicht ist."""
    if cache.exists():
        return cache.read_bytes()
    for versuch in range(4):
        try:
            with urllib.request.urlopen(url, timeout=90) as r:
                inhalt = r.read()
            cache.parent.mkdir(parents=True, exist_ok=True)
            tmp = cache.with_suffix(".teil")
            tmp.write_bytes(inhalt)
            tmp.replace(cache)                                   # erst vollständig schreiben, dann umbenennen
            return inhalt
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return None
            fehler = e
        except Exception as e:                                   # Netzfehler: mit Pause erneut versuchen
            fehler = e
        time.sleep(2 ** (versuch + 1))
    raise RuntimeError(f"Abruf gescheitert: {url}: {fehler}")


def zeilen(inhalt: bytes):
    with zipfile.ZipFile(io.BytesIO(inhalt)) as z:
        text = z.read(z.namelist()[0]).decode("ascii", "ignore")
    r = csv.reader(io.StringIO(text))
    erste = next(r, None)
    if erste and not erste[0][:1].isalpha():
        yield erste
    yield from r


def kerzen_tag(sym, tag, cache):
    c = holen(f"{ARCHIV}/daily/klines/{sym}/5m/{sym}-5m-{tag}.zip", cache / "kerzen" / f"{sym}-{tag}.zip")
    return None if c is None else [(int(z[0]), float(z[1]), float(z[2]), float(z[3]), float(z[4])) for z in zeilen(c)]


def tiefe_tag(sym, tag, stufe, cache):
    """Übergewicht U je 5-Minuten-Kerze: Mittel des Auftragswerts bis `stufe` % unter und über dem Kurs."""
    c = holen(f"{ARCHIV}/daily/bookDepth/{sym}/{sym}-bookDepth-{tag}.zip", cache / "tiefe" / f"{sym}-{tag}.zip")
    if c is None:
        return None
    je_zeit = {}
    for z in zeilen(c):
        s = int(float(z[1]))
        if abs(s) == stufe:
            je_zeit.setdefault(z[0], {})[s] = float(z[3])        # letzter Wert je Zeitstempel und Stufe
    summe = {}
    for zeit, w in je_zeit.items():
        b = ms(zeit.replace(" ", "T") + "Z") // KERZE_MS * KERZE_MS
        e = summe.setdefault(b, [0.0, 0, 0.0, 0])
        if -stufe in w:
            e[0] += w[-stufe]; e[1] += 1
        if stufe in w:
            e[2] += w[stufe]; e[3] += 1
    out = {}
    for b, (k, nk, v, nv) in summe.items():
        if nk and nv and (k / nk + v / nv) > 0:
            out[b] = (k / nk - v / nv) / (k / nk + v / nv)
    return out


def funding_monat(sym, monat, cache):
    c = holen(f"{ARCHIV}/monthly/fundingRate/{sym}/{sym}-fundingRate-{monat}.zip", cache / "funding" / f"{sym}-{monat}.zip")
    return None if c is None else {int(z[0]) // 60_000 * 60_000: float(z[-1]) for z in zeilen(c)}


def pruefsumme(cfg) -> str:
    quelle = (HIER / "strategien" / f"{cfg['strategie']}.py").read_bytes()
    return hashlib.sha256(quelle + json.dumps(cfg["parameter"], sort_keys=True).encode()).hexdigest()


def lauf(test_id: str, heute=None, cache=None, schreiben=True, cfg=None, steuer=None) -> dict:
    ordner = HIER / test_id
    cfg = cfg or json.loads((ordner / "konfiguration.json").read_text())
    steuer = steuer or (json.loads((ordner / "steuerung.json").read_text()) if (ordner / "steuerung.json").exists() else {"status": "laufend"})
    cache = Path(cache) if cache else HIER / ".cache"
    lauf_id = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime()) + "-" + os.urandom(3).hex()
    basis = {"id": cfg["id"], "name": cfg["name"], "version": cfg["version"], "art": cfg["art"], "lauf_id": lauf_id,
             "letzter_lauf": time.strftime("%Y-%m-%d %H:%M UTC", time.gmtime()), "aktualisiert": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
             "takt_stunden": 24, "start": cfg["start"], "kapital": cfg["kapital_usd"],
             "hebel": cfg["hebel"], "maerkte": cfg["coins"], "regel": cfg["regel"], "validierung": cfg["validierung"], "eingefroren": cfg["eingefroren"]}
    if pruefsumme(cfg) != cfg["strategie_sha256"]:
        return {**basis, "status": "Fehler", "fehler": ["Die eingefrorene Regel oder ihre Parameter wurden verändert. Der Test läuft erst weiter, wenn der Stand der Freigabe wiederhergestellt ist."]}
    if steuer["status"] == "pausiert":
        return {**basis, "status": "pausiert", "fehler": []}

    strat = importlib.import_module(f"forschung.papier.strategien.{cfg['strategie']}")
    p, start_ms = cfg["parameter"], ms(cfg["start"])
    ende_ms = ms(steuer["ende"]) if steuer["status"] == "beendet" else None
    heute = heute or dt.datetime.now(UTC).date()
    erster = (dt.datetime.fromtimestamp(start_ms / 1000, UTC) - dt.timedelta(days=cfg["vorlauf_tage"])).date()
    tage = [erster + dt.timedelta(days=i) for i in range((heute - erster).days)]          # bis einschließlich gestern
    luecken, fehler, daten = [], [], {}
    for coin in cfg["coins"]:
        sym, kz, u = coin + "USDT", [], {}
        for tag in tage:
            k, t = kerzen_tag(sym, tag, cache), tiefe_tag(sym, tag, p["tiefe_pct"], cache)
            if k is None or t is None:
                break                                             # noch nicht veröffentlicht: hier endet der Datenstand
            kz += k; u.update(t)
        daten[coin] = (kz, u)
    enden = [kz[-1][0] if kz else None for kz, _ in daten.values()]
    daten_bis = None if None in enden else min(enden)             # gemeinsamer Datenstand aller Coins
    fehlende = (heute - dt.timedelta(days=1) - (dt.datetime.fromtimestamp(daten_bis / 1000, UTC).date() if daten_bis else erster - dt.timedelta(days=1))).days
    if fehlende > 3:
        luecken.append(f"Archivdaten fehlen seit {fehlende} Tagen (letzter Stand {iso(daten_bis) if daten_bis else 'keiner'}).")

    groesse = cfg["kapital_usd"] * cfg["hebel"] / len(cfg["coins"])
    k = cfg["kosten"]
    gebuehr_bp = 2 * k["taker_bp"]
    trades, fund_cache = [], {}
    for coin, (kz, u) in daten.items():
        kz = [x for x in kz if daten_bis is not None and x[0] <= daten_bis]
        for a, b in zip(kz, kz[1:]):
            if b[0] - a[0] != KERZE_MS:
                luecken.append(f"{coin}: Kerzen fehlen zwischen {iso(a[0])} und {iso(b[0])}.")
        if len(kz) < p["min_perioden"]:
            continue
        for t in strat.trades(kz, [u.get(x[0], float("nan")) for x in kz], p, start_ms):
            if ende_ms is not None and t["ein"] >= ende_ms:
                continue
            offen = t["aus"] is None
            bis = kz[-1][0] if offen else t["aus"]
            fund, ausstehend = 0.0, False
            for monat in {iso(t["ein"])[:7], iso(bis)[:7]}:
                if (coin, monat) not in fund_cache:
                    fund_cache[(coin, monat)] = funding_monat(coin + "USDT", monat, cache)
                f = fund_cache[(coin, monat)]
                if f is None:
                    ausstehend = True
                else:
                    fund += sum(-t["richtung"] * r * 1e4 for z, r in f.items() if t["ein"] < z <= bis)
            roh = t["richtung"] * (t["aus_kurs"] / t["ein_kurs"] - 1) * 1e4
            slip = 2 * k["slippage_bp_je_order"][coin]
            trades.append({"trade_id": f"{cfg['id']}|{coin}|{t['ein']}", "coin": coin, "ein": t["ein"], "aus": t["aus"], "richtung": t["richtung"],
                           "ein_kurs": t["ein_kurs"], "aus_kurs": t["aus_kurs"], "z": t["z"], "offen": offen, "roh_bp": roh, "slip_bp": slip,
                           "funding_bp": fund, "funding_ausstehend": ausstehend, "schlimmst_bp": t["schlimmst_bp"],
                           "n85_bp": roh - slip + fund - gebuehr_bp * (1 - k["rebate"]), "n0_bp": roh - slip + fund - gebuehr_bp})
    trades.sort(key=lambda t: (t["ein"], t["coin"]))

    # Konto: feste Größe je Coin. Liquidationsprüfung pessimistisch: gleichzeitige Trades alle zum ungünstigsten Kurs.
    risiko, status, ereignis = cfg["risiko"], "läuft", None
    kosten85 = gebuehr_bp * (1 - k["rebate"])
    gebucht = []
    for t in trades:
        t["usd85"], t["usd0"] = groesse * t["n85_bp"] / 1e4, groesse * t["n0_bp"] / 1e4
        real_vorher = sum(x["usd85"] for x in gebucht if not x["offen"] and x["aus"] <= t["ein"])
        parallel = [x for x in gebucht if x["offen"] or x["aus"] > t["ein"]] + [t]
        tief = cfg["kapital_usd"] + real_vorher + sum(groesse * (x["schlimmst_bp"] - x["slip_bp"] - kosten85) / 1e4 for x in parallel)
        gebucht.append(t)
        if tief <= risiko["mmr"] * groesse * len(parallel):
            status, ereignis = "gescheitert", "Liquidation im Modell (gemeinsame Margin, Erhaltungsmargin %.0f %%) am %s" % (risiko["mmr"] * 100, iso(t["ein"]))
            for x in parallel:                                    # alle offenen Trades zum ungünstigsten Kurs schließen
                x.update(offen=False, aus=t["ein"] if x is t or x["offen"] or x["aus"] > t["ein"] else x["aus"],
                         n85_bp=x["schlimmst_bp"] - x["slip_bp"] - kosten85, n0_bp=x["schlimmst_bp"] - x["slip_bp"] - gebuehr_bp)
                x["usd85"], x["usd0"] = groesse * x["n85_bp"] / 1e4, groesse * x["n0_bp"] / 1e4
            break

    def kurve(liste):
        stand = hoch = rueck = 0.0
        punkte = []
        for t in sorted((x for x in liste if not x["offen"]), key=lambda x: x["aus"]):
            stand += t["usd85"]
            hoch = max(hoch, stand); rueck = max(rueck, hoch - stand)
            punkte.append((t["aus"], stand))
        return punkte, stand, hoch, rueck

    verlauf, stand, hoch, max_rueck = kurve(gebucht)
    grenze = (risiko["abbruch_kontostand"] - 1) * cfg["kapital_usd"]
    if not ereignis:
        zeit = next((aus for aus, st in verlauf if st <= grenze), None)
        if zeit is not None:                                      # Verlustgrenze: danach werden keine neuen Trades mehr eröffnet
            status, ereignis = "abgebrochen", "Verlustgrenze erreicht (Kontostand unter %.0f %% des Startkapitals) am %s" % (risiko["abbruch_kontostand"] * 100, iso(zeit))
            gebucht = [t for t in gebucht if t["ein"] < zeit]
            verlauf, stand, hoch, max_rueck = kurve(gebucht)
    geschlossen = sorted((t for t in gebucht if not t["offen"]), key=lambda t: t["aus"])
    if steuer["status"] == "beendet" and not ereignis:
        status = "abgeschlossen"
    offene = [t for t in gebucht if t["offen"]]
    n = len(geschlossen)
    s85, s0 = sum(t["usd85"] for t in geschlossen), sum(t["usd0"] for t in geschlossen)
    unreal = sum(t["usd85"] for t in offene)
    gew = [t["usd85"] for t in geschlossen if t["usd85"] > 0]
    verl = [t["usd85"] for t in geschlossen if t["usd85"] <= 0]
    tage_lauf = max(0.0, ((daten_bis or start_ms) - start_ms) / TAG_MS)
    gebuehr = n * groesse * gebuehr_bp / 1e4
    tageswerte = {}
    for aus, st in verlauf:
        tageswerte[iso(aus)[:10]] = round(cfg["kapital_usd"] + st, 2)
    if daten_bis is None or daten_bis < start_ms:
        status = "wartet auf Daten" if status == "läuft" else status
    stand_doc = {**basis, "status": status, "ereignis": ereignis, "daten_bis": iso(daten_bis) + " UTC" if daten_bis else None,
                 "laufzeit_tage": round(tage_lauf, 2), "kontostand": round(cfg["kapital_usd"] + s85 + unreal, 2),
                 "rendite_mit_rebate_pct": round((s85 + unreal) / cfg["kapital_usd"] * 100, 3), "rendite_ohne_rebate_pct": round((s0 + sum(t["usd0"] for t in offene)) / cfg["kapital_usd"] * 100, 3),
                 "realisiert_usd": round(s85, 2), "unrealisiert_usd": round(unreal, 2), "trades": n, "trades_je_tag": round(n / tage_lauf, 2) if tage_lauf >= 1 else None,
                 "gewinnquote": round(len(gew) / n, 3) if n else None, "netto_je_trade_bp": round(sum(t["n85_bp"] for t in geschlossen) / n, 2) if n else None,
                 "roh_je_trade_bp": round(sum(t["roh_bp"] for t in geschlossen) / n, 2) if n else None,
                 "profit_factor": round(sum(gew) / -sum(verl), 3) if verl and sum(verl) < 0 else None,
                 "haltedauer_min": round(sum((t["aus"] - t["ein"]) for t in geschlossen) / n / 60000, 1) if n else None,
                 "gebuehr_usd": round(gebuehr, 2), "rebate_usd_angenommen": round(gebuehr * k["rebate"], 2),
                 "funding_usd": round(sum(groesse * t["funding_bp"] / 1e4 for t in geschlossen), 2), "funding_ausstehend": sum(1 for t in geschlossen if t["funding_ausstehend"]),
                 "slippage_usd": round(sum(groesse * t["slip_bp"] / 1e4 for t in geschlossen), 2), "volumen_usd": round(2 * n * groesse, 0),
                 "rueckgang_max_pct": round(max_rueck / cfg["kapital_usd"] * 100, 2), "rueckgang_aktuell_pct": round((hoch - stand) / cfg["kapital_usd"] * 100, 2),
                 "offene_positionen": [{"coin": t["coin"], "richtung": "Long" if t["richtung"] > 0 else "Short", "seit": iso(t["ein"]), "einstieg": t["ein_kurs"],
                                        "ergebnis_usd": round(t["usd85"], 2)} for t in offene],
                 "verlauf": [{"tag": d, "kontostand": w} for d, w in sorted(tageswerte.items())][-400:],
                 "letzte_trades": [{"coin": t["coin"], "richtung": "Long" if t["richtung"] > 0 else "Short", "ein": iso(t["ein"]), "aus": iso(t["aus"]),
                                    "netto_bp": round(t["n85_bp"], 1), "usd": round(t["usd85"], 2)} for t in geschlossen[-cfg.get("anzahl_letzte_trades", 40):]][::-1],
                 "datenluecken": luecken[:20], "fehler": fehler, "positionsgroesse_usd": round(groesse, 2)}
    if schreiben:
        speichern(test_id, stand_doc, gebucht)
    return stand_doc


def speichern(test_id, stand_doc, trades):
    """Ein Lauf = eine Transaktion. Die Trade-Kennung ist eindeutig, eine Wiederholung überschreibt, statt zu verdoppeln."""
    (HIER / "zustand").mkdir(exist_ok=True); (HIER / "ausgabe").mkdir(exist_ok=True)
    db = sqlite3.connect(HIER / "zustand" / f"{test_id}.sqlite", timeout=30)
    try:
        with db:
            db.execute("CREATE TABLE IF NOT EXISTS laeufe (lauf_id TEXT PRIMARY KEY, zeit TEXT, daten_bis TEXT, trades INTEGER, status TEXT, kontostand REAL)")
            db.execute("CREATE TABLE IF NOT EXISTS trades (trade_id TEXT PRIMARY KEY, coin TEXT, ein INTEGER, aus INTEGER, richtung REAL, ein_kurs REAL, aus_kurs REAL, "
                       "roh_bp REAL, n85_bp REAL, n0_bp REAL, funding_bp REAL, offen INTEGER, lauf_id TEXT)")
            alt = {r[0]: r[1:] for r in db.execute("SELECT trade_id, ein_kurs, aus_kurs, richtung FROM trades WHERE offen = 0")}
            abweichung = [t["trade_id"] for t in trades if not t["offen"] and t["trade_id"] in alt and
                          (abs(alt[t["trade_id"]][0] - t["ein_kurs"]) > 1e-9 or abs(alt[t["trade_id"]][1] - t["aus_kurs"]) > 1e-9 or alt[t["trade_id"]][2] != t["richtung"])]
            verschwunden = [i for i in alt if i not in {t["trade_id"] for t in trades}]
            if abweichung or verschwunden:
                stand_doc["fehler"].append(f"Neuberechnung weicht vom gespeicherten Stand ab: {len(abweichung)} geändert, {len(verschwunden)} verschwunden.")
            db.executemany("INSERT OR REPLACE INTO trades VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
                           [(t["trade_id"], t["coin"], t["ein"], t["aus"], t["richtung"], t["ein_kurs"], t["aus_kurs"], t["roh_bp"], t["n85_bp"], t["n0_bp"],
                             t["funding_bp"], int(t["offen"]), stand_doc["lauf_id"]) for t in trades])
            db.execute("INSERT INTO laeufe VALUES (?,?,?,?,?,?)", (stand_doc["lauf_id"], stand_doc["letzter_lauf"], stand_doc["daten_bis"], stand_doc["trades"],
                                                                 stand_doc["status"], stand_doc.get("kontostand")))
    finally:
        db.close()
    ziel = HIER / "ausgabe" / f"{test_id}.json"
    tmp = ziel.with_suffix(".teil")
    tmp.write_text(json.dumps(stand_doc, ensure_ascii=False, indent=1))
    tmp.replace(ziel)


def haupt(test_id: str) -> int:
    for o in ("zustand", "protokolle", "ausgabe"):
        (HIER / o).mkdir(exist_ok=True)
    frei = shutil.disk_usage(HIER).free / 2 ** 30
    sperre = open(HIER / "zustand" / f"{test_id}.sperre", "w")
    try:
        fcntl.flock(sperre, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        print(f"{test_id}: ein anderer Lauf ist aktiv, dieser Lauf endet ohne Änderung")
        return 3
    try:
        if frei < 1.0:
            raise RuntimeError(f"zu wenig Speicherplatz ({frei:.1f} GB frei)")
        d = lauf(test_id)
        zeile = (f"{d['letzter_lauf']} {d['lauf_id']} {test_id} Status={d['status']} Daten bis {d.get('daten_bis')} Trades={d.get('trades')} "
                 f"Konto={d.get('kontostand')} Fehler={len(d.get('fehler', []))} Lücken={len(d.get('datenluecken', []))}")
        if d["status"] in ("Fehler", "pausiert"):
            (HIER / "ausgabe" / f"{test_id}.json").write_text(json.dumps(d, ensure_ascii=False, indent=1))
        code = 0 if d["status"] != "Fehler" else 2
    except Exception as e:                                       # Fehler sichtbar machen, nicht verschlucken
        zeile = f"{time.strftime('%Y-%m-%d %H:%M UTC', time.gmtime())} {test_id} FEHLER {type(e).__name__}: {e}"
        (HIER / "ausgabe" / f"{test_id}.json").write_text(json.dumps({"id": test_id, "status": "Fehler", "fehler": [str(e)],
                                                                     "letzter_lauf": time.strftime("%Y-%m-%d %H:%M UTC", time.gmtime())}, ensure_ascii=False))
        code = 1
    with open(HIER / "protokolle" / f"{test_id}.log", "a") as f:
        f.write(zeile + "\n")
    print(zeile)
    return code


if __name__ == "__main__":
    sys.exit(haupt(sys.argv[1]))
