"""Vorwärtstest des Kandidaten (14-Tage-Trend, stündlich) auf Yubit.

Aufruf einmal pro Stunde, kurz nach der vollen Stunde:

    python -m vorwaertstest.bot schritt        # ein Durchlauf
    python -m vorwaertstest.bot bericht        # daten/bericht.md neu schreiben
    python -m vorwaertstest.bot selbsttest     # Verbindung und Formate prüfen, ohne Orders

Stufe 1, „papier“ (Standard): keine Orders, kein Konto, kein Schlüssel. Der Bot liest öffentliche Yubit-Kurse und
rechnet jede Order gegen das echte Orderbuch dieses Moments ab. Zusätzlich misst er jede Stunde für jeden Coin,
was eine Order in Standardgröße gekostet hätte (daten/spannen.csv).

Stufe 2, „live“: echte Orders in Kleinstgröße. Nur mit API-Schlüssel, IP-Freigabe von Yubit, `"modus": "live"`
in der Konfiguration UND der Umgebungsvariable YUBIT_LIVE=ja. Die Datei daten/STOPP hält den Bot sofort an.
"""
import argparse
import csv
import datetime as dt
import json
import os
import statistics
import sys
import time
from pathlib import Path

from . import kern
from .yubit import Yubit, YubitFehler

HIER = Path(__file__).resolve().parent
PROTOKOLL = ["zeit", "coin", "seite", "signalkurs", "fuellkurs", "volumen", "gebuehr", "rebate", "menge", "geld", "brief",
             "spanne_bp", "slippage_bp", "grund", "modus"]
SPANNEN = ["zeit", "coin", "geld", "brief", "spanne_bp", "volumen", "kauf_bp", "verkauf_bp"]
STAND = ["zeit", "brutto", "gebuehr", "rebate", "funding", "netto_ohne_rebate", "netto_mit_rebate", "long", "short",
         "einsatz", "orders"]


def utc(ms: int) -> str:
    return dt.datetime.fromtimestamp(ms / 1000, dt.timezone.utc).strftime("%Y-%m-%d %H:%M")


def konfig(pfad: Path | None = None) -> dict:
    c = json.loads((pfad or HIER / "config.json").read_text())
    if c["modus"] not in ("papier", "live"):
        raise ValueError("modus muss 'papier' oder 'live' sein")
    if not 0 < c["hebel"] <= 5:
        raise ValueError("hebel muss zwischen 0 und 5 liegen")
    return c


def anhaengen(datei: Path, spalten: list, zeilen: list[dict]) -> None:
    if not zeilen:
        return
    neu = not datei.exists()
    with open(datei, "a", newline="") as f:
        w = csv.DictWriter(f, fieldnames=spalten)
        if neu:
            w.writeheader()
        for z in zeilen:
            w.writerow({k: z.get(k, "") for k in spalten})


def lesen(datei: Path) -> list[dict]:
    if not datei.exists():
        return []
    with open(datei, newline="") as f:
        return list(csv.DictReader(f))


def zustand_laden(daten: Path, kapital: float) -> dict:
    p = daten / "zustand.json"
    return json.loads(p.read_text()) if p.exists() else kern.neuer_zustand(kapital)


def zustand_speichern(daten: Path, z: dict) -> None:
    tmp = daten / "zustand.json.tmp"
    tmp.write_text(json.dumps(z, indent=1, sort_keys=True))
    tmp.replace(daten / "zustand.json")


# ------------------------------------------------------------------- Marktdaten ----
def markt_lesen(api: Yubit, coin: str, jetzt_ms: int) -> dict:
    """Alles, was der Durchlauf für einen Coin braucht. Wirft YubitFehler, wenn etwas fehlt oder veraltet ist."""
    sym = coin + "USDT"
    fertig = [k for k in api.kerzen(sym, 60, 3) if k["start"] + kern.STUNDE_MS <= jetzt_ms]
    if not fertig:
        raise YubitFehler(f"{coin}: keine abgeschlossene Stundenkerze")
    letzte = fertig[-1]
    if jetzt_ms - (letzte["start"] + kern.STUNDE_MS) > 2 * kern.STUNDE_MS:
        raise YubitFehler(f"{coin}: Kerzen sind veraltet ({utc(letzte['start'])})")
    ref = letzte["start"] - kern.RUECKBLICK_STUNDEN * kern.STUNDE_MS
    alt = [k for k in api.kerzen(sym, 60, 3, ref, ref + kern.STUNDE_MS) if k["start"] == ref]
    if not alt:
        raise YubitFehler(f"{coin}: keine Kerze von vor 14 Tagen ({utc(ref)})")
    kt = api.kontrakt(sym)
    if kt["status"] != "Trading":
        raise YubitFehler(f"{coin}: Handel ausgesetzt ({kt['status']})")
    tk = api.ticker(sym)
    buch = api.buch(sym)
    if not buch["geld"] or not buch["brief"]:
        raise YubitFehler(f"{coin}: leeres Orderbuch")
    return {"sym": sym, "kerze": letzte["start"], "schluss": letzte["close"], "schluss_alt": alt[0]["close"],
            "richtung": kern.richtung(letzte["close"], alt[0]["close"]), "kontrakt": kt, "ticker": tk, "buch": buch,
            "mitte": kern.mitte(buch)}


def tagesrichtung_lesen(api: Yubit, coin: str, jetzt_ms: int) -> dict:
    """Tagesregel (Test 4): Richtung aus der Stundenkerze, die um 00:00 UTC des laufenden Tages schließt, gegen den Schluss
    336 Stunden davor. Gilt für den ganzen Tag, egal wann der Lauf stattfindet. Wirft YubitFehler, wenn eine Kerze fehlt."""
    sym = coin + "USDT"
    start = jetzt_ms // kern.TAG_MS * kern.TAG_MS - kern.STUNDE_MS          # Kerze von 23:00 bis 00:00 UTC
    neu = [k for k in api.kerzen(sym, 60, 3, start, start + kern.STUNDE_MS) if k["start"] == start]
    if not neu:
        raise YubitFehler(f"{coin}: keine Stundenkerze zum Tageswechsel ({utc(start)})")
    ref = start - kern.RUECKBLICK_STUNDEN * kern.STUNDE_MS
    alt = [k for k in api.kerzen(sym, 60, 3, ref, ref + kern.STUNDE_MS) if k["start"] == ref]
    if not alt:
        raise YubitFehler(f"{coin}: keine Kerze von 14 Tagen vor dem Tageswechsel ({utc(ref)})")
    return {"tag": utc(jetzt_ms)[:10], "richtung": kern.richtung(neu[0]["close"], alt[0]["close"]),
            "schluss": neu[0]["close"], "schluss_alt": alt[0]["close"]}


# --------------------------------------------------------------- Live-Ausführung ----
def live_erlaubt(cfg: dict, api: Yubit) -> bool:
    return cfg["modus"] == "live" and os.environ.get("YUBIT_LIVE") == "ja" and bool(api.key and api.secret)


def live_positionen(api: Yubit, coins: list) -> dict:
    """Netto-Stückzahl je Coin laut Börse (Long-Seite positiv, Short-Seite negativ)."""
    out = {c: 0.0 for c in coins}
    for p in api.positionen("USDT"):
        coin = str(p.get("symbol", "")).removesuffix("USDT")
        if coin in out:
            groesse = float(p.get("size") or 0)
            out[coin] += groesse if int(p.get("positionIdx") or 0) == 1 else -groesse
    return out


def live_order(api: Yubit, m: dict, kauf: bool, menge: float, position_idx: int, reduce_only: bool, cfg: dict) -> tuple:
    """Limit mit Preisgrenze einstellen, Fills abholen, Rest streichen. Gibt (Kurs, Menge, Gebühr) zurück."""
    kt, buch = m["kontrakt"], m["buch"]
    tick = kt["tick"]
    if kauf:
        preis = -(-buch["brief"][0][0] * (1 + cfg["preisgrenze"]) // tick) * tick      # aufrunden
    else:
        preis = (buch["geld"][0][0] * (1 - cfg["preisgrenze"]) // tick) * tick          # abrunden
    if menge * preis > cfg["max_order_usd"]:
        raise YubitFehler(f"Order über dem Sicherheitsdeckel ({menge * preis:.0f} > {cfg['max_order_usd']} USDT)")
    stellen = max(0, len(f"{tick:.10f}".rstrip("0").split(".")[1]))
    r = api.order(m["sym"], "Buy" if kauf else "Sell", kern.als_text(menge, kt["schritt"]), f"{preis:.{stellen}f}",
                  position_idx, reduce_only)
    time.sleep(1.5)
    fills = api.fills(m["sym"], r["order_id"]) if r["order_id"] else []
    q = sum(float(f.get("execQty") or 0) for f in fills)
    wert = sum(float(f.get("execQty") or 0) * float(f.get("execPrice") or 0) for f in fills)
    gebuehr = sum(abs(float(f.get("execFee") or 0)) for f in fills)
    if q < menge - 1e-12 and r["order_id"]:
        try:
            api.storno(m["sym"], r["order_id"])       # Rest nicht im Buch liegen lassen
        except YubitFehler:
            pass                                       # schon vollständig gefüllt oder bereits gestrichen
    return (wert / q if q > 0 else 0.0), q, gebuehr


# -------------------------------------------------------------------- Durchlauf ----
def schritt(cfg: dict, api: Yubit, daten: Path, jetzt_ms: int | None = None, melden=print) -> dict:
    daten.mkdir(parents=True, exist_ok=True)
    if (daten / "STOPP").exists():
        melden("STOPP-Datei gefunden: kein Durchlauf.")
        return {"gestoppt": True}
    jetzt_ms = jetzt_ms or int(time.time() * 1000)
    zeit = utc(jetzt_ms)
    live = live_erlaubt(cfg, api)
    if cfg["modus"] == "live" and not live:
        raise SystemExit("modus ist 'live', aber YUBIT_LIVE=ja oder der API-Schlüssel fehlt. Abbruch ohne Order.")
    modus = "live" if live else "papier"
    z = zustand_laden(daten, cfg["kapital_usd"])
    z.setdefault("kurs", {})
    if not z["start"]:
        z["start"] = zeit
    coins = cfg["coins"]
    nominal = cfg["kapital_usd"] * cfg["hebel"] / len(coins)

    markt, warnungen = {}, []
    for coin in coins:
        try:
            markt[coin] = markt_lesen(api, coin, jetzt_ms)
            z["kurs"][coin] = markt[coin]["mitte"]
        except (YubitFehler, KeyError, ValueError, IndexError) as e:
            warnungen.append(str(e))
    if not markt:
        raise SystemExit("Keine Marktdaten erhalten: " + "; ".join(warnungen))
    tagesregel = bool(cfg.get("tagesregel"))
    if tagesregel:   # Test 4: Richtung je Coin nur einmal am Tag übernehmen (Stundenschluss 00:00 UTC) und im Zustand festhalten
        tr = z.setdefault("tagesrichtung", {})
        # In der ersten Minute des Tages wird noch nicht übernommen: Ein verspäteter Lauf von 23:59 soll nicht Sekunden nach dem
        # Tageswechsel mit einem womöglich noch nicht endgültigen Schlusskurs entscheiden. Planmäßig übernimmt der Lauf um 00:04.
        for coin in (markt if jetzt_ms % kern.TAG_MS >= kern.TAGESREGEL_KARENZ_MS else ()):
            if (tr.get(coin) or {}).get("tag") != zeit[:10]:
                try:
                    tr[coin] = tagesrichtung_lesen(api, coin, jetzt_ms)
                except (YubitFehler, KeyError, ValueError, IndexError) as e:
                    warnungen.append(f"{e}; Tagesrichtung noch nicht übernommen, Position bleibt")

    if live:   # Buch und Börse müssen übereinstimmen, sonst wird nicht gehandelt
        echt = live_positionen(api, coins)
        for coin in coins:
            if abs(echt[coin] - z["pos"].get(coin, 0.0)) > 1e-9:
                raise SystemExit(f"{coin}: Position laut Börse {echt[coin]} weicht vom Protokoll {z['pos'].get(coin, 0.0)} ab. "
                                 "Kein Handel. Bitte prüfen (daten/STOPP anlegen, Position von Hand schließen).")

    # Funding für die gehaltene Position der letzten Stunde (Näherung mit der aktuellen Rate)
    for coin, m in markt.items():
        n = kern.funding_faellig(z["funding_zeit"].get(coin, 0), jetzt_ms, m["kontrakt"]["funding_minuten"])
        if n and z["pos"].get(coin, 0.0):
            z["funding"] -= z["pos"][coin] * m["ticker"]["mark"] * m["ticker"]["funding"] * n
        z["funding_zeit"][coin] = jetzt_ms

    # Tagesverlust-Limit
    heute = zeit[:10]
    v = kern.vermoegen(z, z["kurs"])
    if z["tag"] != heute:
        z["tag"], z["tag_start"] = heute, v["netto_ohne_rebate"]
    if z["gesperrt_tag"] != heute and v["netto_ohne_rebate"] - z["tag_start"] <= -cfg["tagesverlust_limit"] * cfg["kapital_usd"]:
        z["gesperrt_tag"] = heute
        melden(f"Tagesverlust-Limit erreicht ({v['netto_ohne_rebate'] - z['tag_start']:.2f} USDT): alles schließen, heute Pause.")
    gesperrt = z["gesperrt_tag"] == heute

    protokoll, spannen = [], []
    for coin, m in markt.items():
        buch, kt, mitte = m["buch"], m["kontrakt"], m["mitte"]
        standard = kern.menge_runden(nominal, mitte, kt["schritt"], kt["min_menge"])
        if standard > 0:   # stündliche Messung: was hätte eine Order in Standardgröße jetzt gekostet?
            kp, kq = kern.buch_fill(True, standard, buch)
            vp, vq = kern.buch_fill(False, standard, buch)
            spannen.append({"zeit": zeit, "coin": coin, "geld": buch["geld"][0][0], "brief": buch["brief"][0][0],
                            "spanne_bp": round(kern.spanne_bp(buch), 3), "volumen": round(standard * mitte, 2),
                            "kauf_bp": round(kern.slippage(True, kp, mitte) * 1e4, 3) if kq >= standard - 1e-12 else "",
                            "verkauf_bp": round(kern.slippage(False, vp, mitte) * 1e4, 3) if vq >= standard - 1e-12 else ""})
        signal = m["richtung"]
        if tagesregel:   # maßgeblich ist die heute übernommene Tagesrichtung; liegt sie noch nicht vor, wird nicht gehandelt
            heute_richtung = z["tagesrichtung"].get(coin) or {}
            if heute_richtung.get("tag") == heute:
                signal = heute_richtung["richtung"]
            elif not gesperrt:
                continue
        ziel = 0 if gesperrt else signal
        ist = z["pos"].get(coin, 0.0)
        ist_richtung = (ist > 0) - (ist < 0)
        anlass = None
        tp, sl, trail = cfg.get("tp", 0.0), cfg.get("sl", 0.0), cfg.get("trail", 0.0)
        if tp or sl or trail:   # Varianten mit Gewinnziel / Stop / nachgezogenem Stop: nach dem Ausstieg Pause, bis das Signal dreht
            sperre = z.setdefault("sperre", {})
            if sperre.get(coin, 0) and sperre[coin] != signal:
                sperre[coin] = 0
            ein = z.setdefault("einstieg", {}).get(coin, 0.0)
            if ist_richtung and ist_richtung == signal and ein > 0:
                r = (mitte / ein - 1) * ist_richtung
                anlass = "ziel" if tp and r >= tp else "stop" if sl and r <= -sl else None
                if trail and not anlass:   # nachgezogener Stop: Abstand zum günstigsten Mittelkurs seit dem Einstieg
                    beste = z.setdefault("beste", {})
                    b = beste.get(coin) or ein
                    b = max(b, mitte) if ist_richtung > 0 else min(b, mitte)
                    beste[coin] = b
                    if (mitte / b - 1) * ist_richtung <= -trail:
                        anlass = "nachzug"
                if anlass:
                    sperre[coin] = ist_richtung
            if signal != 0 and sperre.get(coin, 0) == signal:
                ziel = 0
        if ziel == ist_richtung:
            continue
        auftraege = []   # (kauf, menge, position_idx, reduce_only)
        if ist != 0:
            auftraege.append((ist < 0, abs(ist), 1 if ist > 0 else 2, True))
        if ziel != 0:
            if standard > 0:
                auftraege.append((ziel > 0, standard, 1 if ziel > 0 else 2, False))
            else:
                warnungen.append(f"{coin}: Zielbetrag {nominal:.0f} USDT liegt unter der Mindestordergröße, kein Einstieg")
        schon = 0.0      # im Papier-Modus zehrt die zweite Order vom selben Buch
        for kauf, menge, idx, reduce in auftraege:
            grund = "tageslimit" if gesperrt else ((anlass or "schliessen") if reduce else "einstieg")
            try:
                if live:
                    kurs, q, gebuehr = live_order(api, m, kauf, menge, idx, reduce, cfg)
                    rebate = 0.0                       # wird von Yubit getrennt gutgeschrieben, hier nicht sichtbar
                else:
                    gesamt_kurs, gesamt_q = kern.buch_fill(kauf, schon + menge, buch)
                    vor_kurs, vor_q = kern.buch_fill(kauf, schon, buch) if schon else (0.0, 0.0)
                    q = gesamt_q - vor_q
                    kurs = (gesamt_kurs * gesamt_q - vor_kurs * vor_q) / q if q > 0 else 0.0
                    schon += menge
                    gebuehr = kern.TAKER * q * kurs
                    rebate = kern.REBATE * gebuehr
            except YubitFehler as e:
                warnungen.append(f"{coin}: Order fehlgeschlagen ({e})")
                break
            if q <= 0:
                warnungen.append(f"{coin}: nichts gefüllt")
                break
            kern.buchen(z, coin, q if kauf else -q, kurs, gebuehr, rebate)
            if not reduce:
                z.setdefault("einstieg", {})[coin] = kurs
                if cfg.get("trail"):
                    z.setdefault("beste", {})[coin] = kurs   # neuer Einstieg: der nachgezogene Stop beginnt wieder am Einstiegskurs
            protokoll.append({"zeit": zeit, "coin": coin, "seite": "kauf" if kauf else "verkauf", "signalkurs": mitte,
                              "fuellkurs": round(kurs, 10), "volumen": round(q * kurs, 4), "gebuehr": round(gebuehr, 6),
                              "rebate": round(rebate, 6), "menge": q, "geld": buch["geld"][0][0], "brief": buch["brief"][0][0],
                              "spanne_bp": round(kern.spanne_bp(buch), 3),
                              "slippage_bp": round(kern.slippage(kauf, kurs, mitte) * 1e4, 3), "grund": grund, "modus": modus})
            if q < menge - 1e-12:
                warnungen.append(f"{coin}: nur {q} von {menge} gefüllt")
                break

    v = kern.vermoegen(z, z["kurs"])
    long = sum(1 for c in coins if z["pos"].get(c, 0.0) > 0)
    short = sum(1 for c in coins if z["pos"].get(c, 0.0) < 0)
    einsatz = sum(abs(z["pos"].get(c, 0.0)) * z["kurs"].get(c, 0.0) for c in coins)
    anhaengen(daten / "protokoll.csv", PROTOKOLL, protokoll)
    anhaengen(daten / "spannen.csv", SPANNEN, spannen)
    anhaengen(daten / "stand.csv", STAND, [{"zeit": zeit, **{k: round(x, 4) for k, x in v.items()}, "long": long, "short": short,
                                            "einsatz": round(einsatz, 2), "orders": z["orders"]}])
    z["letzte_kerze"] = max(m["kerze"] for m in markt.values())
    zustand_speichern(daten, z)
    melden(f"{zeit} UTC [{modus}] {len(protokoll)} Orders, {long} Long / {short} Short, Einsatz {einsatz:.0f} USDT, "
           f"netto mit Rebate {v['netto_mit_rebate']:+.2f} USDT ({api.aufrufe} Abrufe)")
    for w in warnungen:
        melden("  Hinweis: " + w)
    return {"orders": len(protokoll), "warnungen": warnungen, "vermoegen": v, "modus": modus}


# ---------------------------------------------------------------------- Bericht ----
def _pz(x: float, n: int = 3) -> str:
    return f"{x:.{n}f} %".replace(".", ",").replace("-", "−")


def _n(x: float, n: int = 0) -> str:
    return f"{x:,.{n}f}".replace(",", "X").replace(".", ",").replace("X", ".")


def _usd(x: float) -> str:
    return (f"{x:+,.2f} $").replace(",", "X").replace(".", ",").replace("X", ".").replace("-", "−")


def bericht(cfg: dict, daten: Path) -> str:
    sp, pr, st = lesen(daten / "spannen.csv"), lesen(daten / "protokoll.csv"), lesen(daten / "stand.csv")
    z = [f"# Vorwärtstest Yubit: Zwischenstand", "",
         "Historische bzw. Papier-Messung, keine Anlageberatung. Stufe „papier“ setzt keine echten Orders.", ""]
    if not st:
        return "\n".join(z + ["Noch keine Daten."])
    tage = max((dt.datetime.fromisoformat(st[-1]["zeit"]) - dt.datetime.fromisoformat(st[0]["zeit"])).total_seconds() / 86400, 1 / 24)
    z += [f"- Zeitraum: {st[0]['zeit']} bis {st[-1]['zeit']} UTC ({_n(tage, 1)} Tage, {len(st)} Durchläufe)",
          f"- Kapital {_n(cfg['kapital_usd'])} $, Hebel {_n(cfg['hebel'], 2)}, {len(cfg['coins'])} Coins, Modus {pr[-1]['modus'] if pr else cfg['modus']}", ""]
    if cfg.get("tagesregel"):                               # Test 4: einmal am Tag entscheiden
        z.insert(-1, "- Tagesregel: Die Richtung wird je Coin einmal am Tag übernommen (Stundenschluss 00:00 UTC) und bis zum nächsten Tag gehalten.")
    if cfg.get("nachgerechnet_bis"):                        # Abschnitt aus den Aufzeichnungen von Test 1: als Nachrechnung kennzeichnen
        z.insert(-1, f"- Bis {cfg['nachgerechnet_bis']} UTC aus den Aufzeichnungen von Test 1 nachgerechnet (kein Vorwärtstest), danach live.")

    werte = [(r["coin"], (float(r["kauf_bp"]) + float(r["verkauf_bp"])) / 2, float(r["spanne_bp"])) for r in sp
             if r["kauf_bp"] != "" and r["verkauf_bp"] != ""]
    z += ["## Was eine Order zur vollen Stunde gekostet hätte", ""]
    if werte:
        alle = sorted(w[1] for w in werte)
        mittel, median, p90 = statistics.fmean(alle), statistics.median(alle), alle[min(len(alle) - 1, int(len(alle) * 0.9))]
        urteil = ("unter der Annahme aus dem Backtest (0,05 %)" if mittel <= 5 else
                  "über der Annahme, aber unter der Schmerzgrenze (rund 0,07 %)" if mittel <= 7 else
                  "ÜBER der Schmerzgrenze: so trägt der Kandidat nicht")
        z += [f"Gemessen am echten Orderbuch, Order in Standardgröße, {len(alle)} Messungen.", "",
              f"- **Slippage im Mittel: {_pz(mittel / 100)}** ({urteil})",
              f"- Median {_pz(median / 100)}, schlechteste 10 % ab {_pz(p90 / 100)}", "",
              "| Coin | Messungen | Slippage im Mittel | Schlechteste 10 % ab | Spanne Geld/Brief im Mittel |", "|---|---|---|---|---|"]
        for coin in cfg["coins"]:
            w = sorted(x[1] for x in werte if x[0] == coin)
            if w:
                s = statistics.fmean(x[2] for x in werte if x[0] == coin)
                z.append(f"| {coin} | {len(w)} | {_pz(statistics.fmean(w) / 100)} | {_pz(w[min(len(w) - 1, int(len(w) * 0.9))] / 100)} | {_pz(s / 100)} |")
        fehlend = [c for c in cfg["coins"] if not any(x[0] == c for x in werte)]
        if fehlend:
            z += ["", "Ohne Messung (Zielbetrag unter der Mindestordergröße oder keine Daten): " + ", ".join(fehlend) + "."]
    else:
        z.append("Noch keine Messungen.")

    z += ["", "## Orders des Kandidaten", ""]
    if pr:
        vol = sum(float(r["volumen"]) for r in pr)
        slip = sum(float(r["slippage_bp"]) * float(r["volumen"]) for r in pr) / vol
        z += [f"- {len(pr)} Orders, Volumen {_n(vol)} $" + (f" ({_n(vol / tage)} $ pro Tag)" if tage >= 1 else ""),
              f"- Slippage nach Volumen gewichtet: {_pz(slip / 100)}",
              f"- Gebühr gezahlt: {_usd(sum(float(r['gebuehr']) for r in pr)).lstrip('+')} (das sind {_pz(sum(float(r['gebuehr']) for r in pr) / vol * 100)} vom Volumen)"]
        if len(pr) < 200:
            z.append(f"- Hinweis: Erst {len(pr)} Orders. Unter etwa 200 ist das Mittel noch unsicher.")
    else:
        z.append("Noch keine Orders.")

    l = st[-1]
    z += ["", "## Ergebnis seit Start", "", "| | Betrag | Anteil am Kapital |", "|---|---|---|"]
    for name, k in (("Handel vor Gebühren", "brutto"), ("Gebühr", "gebuehr"), ("Funding", "funding"),
                    ("Nach voller Gebühr, ohne Rebate", "netto_ohne_rebate"), ("Rebate (85 %, gerechnet)", "rebate"),
                    ("**Netto mit Rebate**", "netto_mit_rebate")):
        x = float(l[k]) * (-1 if k == "gebuehr" else 1)
        z.append(f"| {name} | {_usd(x)} | {_pz(x / cfg['kapital_usd'] * 100, 2)} |")
    z += ["", f"Offen: {l['long']} Long, {l['short']} Short, Einsatz {_n(float(l['einsatz']))} $.",
          "", "Wenige Wochen sagen über den Gewinn fast nichts. Aussagekräftig ist hier vor allem die Slippage.", ""]
    text = "\n".join(z)
    (daten / "bericht.md").write_text(text)
    return text


def selbsttest(cfg: dict, api: Yubit) -> None:
    jetzt = int(time.time() * 1000)
    print("Öffentliche Kursdaten:")
    for coin in cfg["coins"]:
        try:
            m = markt_lesen(api, coin, jetzt)
            kt = m["kontrakt"]
            print(f"  {coin:5s} ok  Richtung {m['richtung']:+d}  Spanne {kern.spanne_bp(m['buch']):6.2f} bp  "
                  f"Mindestorder {kt['min_menge'] * m['mitte']:8.2f} $  Schritt {kt['schritt'] * m['mitte']:8.2f} $")
        except (YubitFehler, KeyError, ValueError, IndexError) as e:
            print(f"  {coin:5s} FEHLER: {e}")
    if not (api.key and api.secret):
        print("Kein API-Schlüssel gesetzt: Kontoteil übersprungen (für Stufe „papier“ nicht nötig).")
        return
    print("Konto (nur lesend, es wird nichts geordert):")
    for name, fn in (("Guthaben", api.guthaben_roh), ("Gebühren BTCUSDT", lambda: api.gebuehren_roh("BTCUSDT")),
                     ("Positionen", lambda: api.positionen("USDT"))):
        try:
            d = fn()
            print(f"  {name}: ok ->", json.dumps(d)[:400])
        except YubitFehler as e:
            print(f"  {name}: FEHLER: {e}")


def main(argv=None) -> None:
    p = argparse.ArgumentParser(description="Vorwärtstest Yubit")
    p.add_argument("befehl", choices=["schritt", "bericht", "selbsttest"])
    p.add_argument("--config", type=Path)
    p.add_argument("--daten", type=Path)
    a = p.parse_args(argv)
    cfg = konfig(a.config)
    daten = a.daten or HIER / cfg.get("daten", "daten")
    api = Yubit(os.environ.get("YUBIT_API_KEY", ""), os.environ.get("YUBIT_API_SECRET", ""))
    if a.befehl == "schritt":
        schritt(cfg, api, daten)
        bericht(cfg, daten)
    elif a.befehl == "bericht":
        print(bericht(cfg, daten))
    else:
        selbsttest(cfg, api)


if __name__ == "__main__":
    main()
