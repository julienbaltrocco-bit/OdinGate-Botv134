"""Zufallsvergleich: Bot-Schritt (vorwaertstest.bot.schritt) gegen die unabhängige Referenz (referenz.py).

Aufruf (Beispiele):
    python vergleich.py                                   # 300 Szenarien, Tagesregel UND Stundenregel, Bot-Kopie daneben
    python vergleich.py --szenarien 40 --regel tag        # nur Test 4
    python vergleich.py --bot /pfad/zu/swing-hybrid       # andere Bot-Kopie (z. B. eine mit absichtlichem Fehler)

Eigene nachgestellte Börse (`EigeneBoerse`), eigener Szenario-Erzeuger (`szenario`), Vergleich nach JEDEM Lauf:
Vorzeichen der Position je Coin, Zahl der Orders, und ob der Lauf mangels Marktdaten abbricht.
"""
import argparse
import collections
import json
import multiprocessing
import random
import shutil
import sys
import tempfile
import time
from pathlib import Path

HIER = Path(__file__).resolve().parent
sys.path.insert(0, str(HIER))
import referenz as ref                                                     # noqa: E402
from referenz import H, TAG, RUECKBLICK                                    # noqa: E402

MIN = 60_000
BASIS_TAG = (1_800_000_000_000 // TAG) * TAG                               # ein 00:00 UTC (Januar 2027)
NIE = 10 ** 16
CFG = {"modus": "papier", "kapital_usd": 5000, "hebel": 0.2, "coins": [], "tagesverlust_limit": 100,
       "preisgrenze": 0.0005, "max_order_usd": 150, "daten": "daten"}
BASISKURS = {"AAA": 100.0, "BBB": 50.0, "CCC": 7.5}
STARTWERT = 5311


# ------------------------------------------------------------------ nachgestellte Börse ----
class EigeneBoerse:
    """Liefert, was die Tabelle `kerzen` (referenz.Kerzen) zur Uhrzeit `jetzt` hergibt. Wie die echte Börse gibt sie
    auch die noch LAUFENDE Stundenkerze zurück, mit einem vorläufigen Schluss (`laufend`), der absichtlich vom
    endgültigen abweicht. Bereichsabfragen liefern alle vorhandenen Kerzen mit start_ms <= Start <= ende_ms."""
    key = secret = ""

    def __init__(self, kerzen, laufend):
        self.k, self.laufend, self.jetzt, self.aufrufe, self.abrufe = kerzen, laufend, 0, 0, []

    def _kerze(self, coin, s):
        t = self.jetzt
        if not self.k.vorhanden(coin, s, t):
            return None
        x = self.k.schluss[coin][s] if s + H <= t else self.laufend[coin][s]
        return {"start": s, "open": x, "high": x, "low": x, "close": x}

    def kerzen(self, sym, minuten=60, limit=3, start_ms=None, ende_ms=None):
        self.aufrufe += 1
        if minuten != 60:
            raise AssertionError("nur Stundenkerzen nachgestellt")
        coin, t = sym.removesuffix("USDT"), self.jetzt
        if start_ms is None:                                                # die jüngsten `limit` vorhandenen Kerzen
            out, s = [], t - t % H
            while len(out) < limit and s >= t - 12 * H:
                k = self._kerze(coin, s)
                if k:
                    out.append(k)
                s -= H
            return out[::-1]
        self.abrufe.append((coin, start_ms, ende_ms))
        out, s = [], -(-start_ms // H) * H
        while s <= ende_ms:
            k = self._kerze(coin, s)
            if k:
                out.append(k)
            s += H
        return out[-limit:]

    def kontrakt(self, sym):
        self.aufrufe += 1
        return {"status": "Trading", "min_menge": 0.1, "schritt": 0.1, "tick": 0.01, "funding_minuten": 480}

    def _preis(self, sym):
        return BASISKURS[sym.removesuffix("USDT")] * (1 + 0.0005 * ((self.jetzt // (5 * MIN)) % 9 - 4))

    def ticker(self, sym):
        self.aufrufe += 1
        p = self._preis(sym)
        return {"geld": p - 0.01, "brief": p + 0.01, "letzter": p, "mark": p, "funding": 0.0001, "umsatz24h": 1e6}

    def buch(self, sym, tiefe=25):
        self.aufrufe += 1
        p = self._preis(sym)
        return {"geld": [(p - 0.01, 1e6), (p - 0.03, 1e6)], "brief": [(p + 0.01, 1e6), (p + 0.03, 1e6)]}


# ---------------------------------------------------------------------------- Szenarien ----
def _deltas(rng, art, stunden):
    """Abstand des Stundenschlusses zum 14-Tage-Vergleichskurs in Achteln (0 = exakter Gleichstand)."""
    out, v = {}, rng.choice([-1, 1])
    for s in stunden:
        mitternacht = (s + H) % TAG == 0                                    # diese Kerze schließt um 00:00 UTC
        if art == "iid":
            d = 0 if rng.random() < 0.12 else rng.choice([-3, -2, -1, 1, 2, 3])
        elif art == "zaeh":
            if rng.random() < 0.2:
                v = -v
            d = 0 if rng.random() < 0.05 else v * rng.randint(1, 3)
        else:                                                               # "gegen": die Mitternachtskerze steht gegen ihre Nachbarn
            if (s + H) % TAG == H:                                          # 00:00-01:00: Vorzeichen des neuen Tages würfeln
                v = rng.choice([-1, 1])
            d = (0 if rng.random() < 0.15 else -v * rng.randint(1, 3)) if mitternacht else v * rng.randint(1, 3)
        out[s] = d
    return out


def szenario(nr, startwert=STARTWERT):
    """Ein zufälliges, aus (startwert, nr) wiederholbares Szenario."""
    rng = random.Random(f"{startwert}/{nr}")
    tage = rng.randint(3, 8)
    coins = ["AAA", "BBB", "CCC"][:rng.randint(1, 3)]
    d0 = BASIS_TAG + rng.randint(0, 300) * TAG
    ende = d0 + tage * TAG
    stunden = list(range(d0 - 8 * H, ende + 6 * H, H))
    grenzen = list(range(d0, ende + 1, TAG))                                # alle Tageswechsel im Szenario
    schluss, laufend, fehlt = {}, {}, {}
    p_tag = rng.choice([0.0, 0.15, 0.35, 0.6])                              # fehlende Kerzen zum Tageswechsel
    p_markt = rng.choice([0.0, 0.0, 0.03, 0.1])                             # fehlende Stundenkerzen irgendwann
    p_flacker = rng.choice([0.0, 0.0, 0.3])                                 # Tageskerze verschwindet später wieder
    for c in coins:
        art = rng.choice(["iid", "iid", "zaeh", "gegen"])
        dl = _deltas(rng, art, stunden)
        schluss[c], laufend[c], fehlt[c] = {}, {}, collections.defaultdict(list)
        for s in stunden:
            alt = BASISKURS[c] + 0.125 * rng.randint(-16, 16)
            schluss[c][s - RUECKBLICK] = alt
            schluss[c][s] = alt + 0.125 * dl[s]
            vorl = (-dl[s] if dl[s] else rng.choice([-2, 2])) if rng.random() < 0.7 else rng.randint(-3, 3)
            laufend[c][s] = alt + 0.125 * vorl                              # vorläufiger Schluss der laufenden Kerze
            laufend[c][s - RUECKBLICK] = alt + 0.125
        for d in grenzen:
            if rng.random() < p_tag:
                bis = d + rng.choice([2 * MIN, 4 * MIN, 6 * MIN, 12 * MIN, 59 * MIN, 61 * MIN, 150 * MIN, 7 * H,
                                      23 * H + 50 * MIN, 24 * H + 3 * MIN, 30 * H, 50 * H, NIE])
                for s in rng.choice([[d - H], [d - H - RUECKBLICK], [d - H, d - H - RUECKBLICK]]):
                    fehlt[c][s].append((0, bis))
            if rng.random() < p_flacker:
                von = d + rng.choice([10 * MIN, 2 * H, 9 * H, 20 * H])
                fehlt[c][rng.choice([d - H, d - H - RUECKBLICK])].append((von, von + rng.choice([10 * MIN, 2 * H, 6 * H])))
        for s in stunden:
            if rng.random() < p_markt:
                fehlt[c][s].append((0, s + H + rng.choice([6 * MIN, 30 * MIN, 65 * MIN, 130 * MIN, 210 * MIN])))
            if rng.random() < p_markt / 2:
                fehlt[c][s - RUECKBLICK].append((s + H, s + H + rng.choice([6 * MIN, 30 * MIN, 65 * MIN, 130 * MIN])))
        fehlt[c] = dict(fehlt[c])

    art_lauf = rng.choice(["alle5", "ausfaelle", "ausfaelle"])
    versatz = rng.choice([4 * MIN, 4 * MIN, 4 * MIN, 0, 5 * MIN - 1])        # 00:04, genau 00:00, 00:04:59.999
    zittern = rng.choice([0, 0, 50_000])
    anfang = d0 + rng.choice([0, 0, rng.randrange(0, TAG, 5 * MIN)])
    schluss_zeit = ende + rng.choice([0, 10 * MIN, 2 * H])
    laeufe = [t + (rng.randrange(zittern) if zittern else 0) for t in range(anfang + versatz, schluss_zeit + 1, 5 * MIN)]
    ausfall = []
    if art_lauf == "ausfaelle":
        for _ in range(rng.randint(1, 6)):
            von = rng.randrange(anfang, ende)
            ausfall.append((von, von + rng.choice([10 * MIN, 40 * MIN, 2 * H, 5 * H, 13 * H, 25 * H, 49 * H])))
        for d in grenzen:
            if rng.random() < 0.4:                                          # Ausfall über Mitternacht, auch ganze Tage
                ausfall.append((d - rng.choice([MIN, 20 * MIN, 3 * H, 26 * H]),
                                d + rng.choice([6 * MIN, 58 * MIN, 62 * MIN, 4 * H, 11 * H, 23 * H + 56 * MIN,
                                                24 * H + 10 * MIN, 47 * H])))
        laeufe = [t for t in laeufe if not any(a <= t < b for a, b in ausfall)]
    for d in grenzen:                                                       # Läufe genau am Tageswechsel
        if rng.random() < 0.5:
            laeufe.append(d)                                                # 00:00:00.000
        if rng.random() < 0.5:
            laeufe.append(d - 1)                                            # 23:59:59.999
        if rng.random() < 0.1:
            laeufe += [d + H - 1, d + H]
    laeufe = sorted({t for t in laeufe if anfang <= t <= schluss_zeit})
    return {"nr": nr, "coins": coins, "kerzen": ref.Kerzen(schluss, fehlt), "laufend": laufend, "laeufe": laeufe,
            "art": art_lauf, "tage": tage, "d0": d0, "grenzen": grenzen, "ausfall": ausfall,
            "p": (p_tag, p_markt, p_flacker)}


# ------------------------------------------------------------------------------ Vergleich ----
def uhr(ms):
    s, rest = divmod(ms, 1000)
    return time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime(s)) + f".{rest:03d}"


def _vz(x):
    return (x > 0) - (x < 0)


def _beleg_soll(b):
    """So muss der Bot die übernommene Tagesrichtung im Zustand festhalten (Abschnitt 53, „Betrieb“: Tag, Richtung,
    beide Schlusskurse). Die Feldnamen stammen aus dem Bot-Code, die Werte aus der Referenz."""
    return {"tag": time.strftime("%Y-%m-%d", time.gmtime(b[0] // 1000)), "richtung": b[1], "schluss": b[2], "schluss_alt": b[3]}


def pruefen(bot, sz, tagesregel, markt_noetig=True, arbeit=None, zustand_pruefen=None):
    """Treibt den Bot durch ein Szenario und vergleicht nach jedem Lauf mit der Referenz. Gibt Abweichungen (höchstens
    die erste je Art) und Kennzahlen zurück.

    Verglichen wird nach jedem Lauf: Vorzeichen der Position je Coin ("richtung"), Zahl der Orders ("orders"), Abbruch
    mangels Marktdaten ("abbruch"); mit Tagesregel zusätzlich der Eintrag `tagesrichtung` im Zustand ("beleg"), ohne
    Tagesregel, dass dieser Eintrag nicht entsteht ("feld")."""
    coins, laeufe, k = sz["coins"], sz["laeufe"], sz["kerzen"]
    verlauf = (ref.tagesregel(k, coins, laeufe, markt_noetig) if tagesregel else ref.stundenregel(k, coins, laeufe))
    cfg = {**CFG, "coins": coins}
    if tagesregel:
        cfg["tagesregel"] = True
    ordner = Path(tempfile.mkdtemp(prefix=f"sz{sz['nr']}_", dir=arbeit))
    api = EigeneBoerse(k, sz["laufend"])
    abw, zahl = [], collections.Counter()
    vorher, orders_soll, belege = {c: 0 for c in coins}, 0, {}
    try:
        for i, t in enumerate(laeufe):
            soll = verlauf[i]
            api.jetzt = t
            abbruch = False
            try:
                bot.schritt(cfg, api, ordner, t, melden=lambda *_: None)
            except SystemExit:
                abbruch = True
            p = ordner / "zustand.json"
            z = json.loads(p.read_text()) if p.exists() else {"pos": {}, "orders": 0}
            orders_soll += sum(ref.orders_erwartet(vorher[c], soll["richtung"][c]) for c in coins)
            zahl["laeufe"] += 1
            zahl["abbruch"] += abbruch
            if abbruch != soll["entfaellt"] and not any(a["was"] == "abbruch" for a in abw):
                abw.append({"was": "abbruch", "lauf": i, "zeit": uhr(t), "bot": abbruch, "referenz": soll["entfaellt"]})
            for c in coins:
                ist = _vz(z["pos"].get(c, 0.0))
                if ist != soll["richtung"][c]:
                    abw.append({"was": "richtung", "lauf": i, "zeit": uhr(t), "coin": c, "bot": ist,
                                "referenz": soll["richtung"][c], "ereignis": soll["ereignis"][c]})
            if z.get("orders", 0) != orders_soll and not any(a["was"] in ("orders", "richtung") for a in abw):
                abw.append({"was": "orders", "lauf": i, "zeit": uhr(t), "bot": z.get("orders", 0), "referenz": orders_soll})
            if tagesregel and markt_noetig:
                belege.update(soll["beleg"])
                for c in coins:
                    ist_b = z.get("tagesrichtung", {}).get(c)
                    soll_b = _beleg_soll(belege[c]) if c in belege else None
                    if ist_b != soll_b and not any(a["was"] == "beleg" for a in abw):
                        abw.append({"was": "beleg", "lauf": i, "zeit": uhr(t), "coin": c, "bot": ist_b, "referenz": soll_b})
            if not tagesregel and "tagesrichtung" in z and not any(a["was"] == "feld" for a in abw):
                abw.append({"was": "feld", "lauf": i, "zeit": uhr(t), "bot": "tagesrichtung im Zustand", "referenz": "kein neues Feld"})
            if zustand_pruefen:
                abw += zustand_pruefen(z, soll, sz, i) or []
            if any(a["was"] == "richtung" for a in abw):
                break                                                       # erste Richtungsabweichung beendet das Szenario
            vorher = dict(soll["richtung"])
    finally:
        shutil.rmtree(ordner, ignore_errors=True)
    zahl["orders"] = orders_soll
    zahl["abrufe"] = len(api.abrufe)
    return {"nr": sz["nr"], "abweichungen": abw, "zahl": dict(zahl)}


def kennzahlen(sz):
    """Was das Szenario enthält (damit man sieht, dass die schwierigen Fälle wirklich vorkommen)."""
    coins, laeufe, k = sz["coins"], sz["laeufe"], sz["kerzen"]
    tag = ref.tagesregel(k, coins, laeufe, True)
    woertlich = ref.tagesregel(k, coins, laeufe, False)
    stunde = ref.stundenregel(k, coins, laeufe)
    z = collections.Counter()
    z["laeufe"] = len(laeufe)
    z["laeufe_0000"] = sum(1 for t in laeufe if t % TAG == 0)
    z["laeufe_235959999"] = sum(1 for t in laeufe if t % TAG == TAG - 1)
    tage_mit_lauf = {t - t % TAG for t in laeufe}
    z["tage_mit_lauf"] = len(tage_mit_lauf)
    z["tage_ohne_lauf"] = sum(1 for d in range(min(tage_mit_lauf), max(tage_mit_lauf) + 1, TAG) if d not in tage_mit_lauf)
    vor = {c: 0 for c in coins}
    uebernommen = set()
    for a, w, s in zip(tag, woertlich, stunde):
        t = a["zeit"]
        for c in coins:
            e = a["ereignis"][c]
            if e == "uebernommen":
                uebernommen.add((c, t - t % TAG))
                z["uebernahmen"] += 1
                z["uebernahme_planmaessig" if t % TAG < 5 * MIN else "uebernahme_aufgeholt"] += 1
                z["uebernahme_aufgeholt_nach_01uhr"] += t % TAG >= H
                z["uebernahme_gleichstand"] += a["richtung"][c] == 0
                z["uebernahme_dreht"] += a["richtung"][c] == -vor[c] != 0
                z["uebernahme_mit_wechsel"] += a["richtung"][c] != vor[c]
            elif e == "Tageskerze fehlt":
                z["lauf_coin_tageskerze_fehlt"] += 1
            elif e == "erste Minute":
                z["lauf_coin_erste_minute"] += 1
            elif e == "keine Marktdaten":
                z["lauf_coin_keine_marktdaten"] += 1
            z["lauf_coin"] += 1
            z["lauf_coin_tag_ungleich_stunde"] += a["richtung"][c] != s["richtung"][c]
            z["lauf_coin_lesarten_ungleich"] += a["richtung"][c] != w["richtung"][c]
            vor[c] = a["richtung"][c]
        z["lauf_entfaellt"] += a["entfaellt"]
    z["coin_tage_ohne_uebernahme"] = sum(1 for c in coins for d in tage_mit_lauf if (c, d) not in uebernommen)
    z["szenario_lesarten_ungleich"] = int(z["lauf_coin_lesarten_ungleich"] > 0)
    z["szenario_" + sz["art"]] = 1
    return z


_BOT = None


def bot_laden(pfad):
    global _BOT
    sys.path.insert(0, str(pfad))
    from vorwaertstest import bot
    if Path(bot.__file__).resolve().parents[1] != Path(pfad).resolve():
        raise SystemExit(f"falscher Bot geladen: {bot.__file__}")
    _BOT = bot
    return bot


def _arbeit(auftrag):
    nr, startwert, regel, markt_noetig, arbeit = auftrag
    sz = szenario(nr, startwert)
    return pruefen(_BOT, sz, regel == "tag", markt_noetig, arbeit), kennzahlen(sz)


def lauf(bot_pfad, szenarien, startwert, regel, markt_noetig=True, prozesse=4, erste=0):
    bot_laden(bot_pfad)
    arbeit = Path(tempfile.mkdtemp(prefix="tagesregel_vergleich_"))        # nichts in den Testordner schreiben
    auftraege = [(nr, startwert, regel, markt_noetig, arbeit) for nr in range(erste, erste + szenarien)]
    if prozesse > 1:
        with multiprocessing.get_context("fork").Pool(prozesse) as pool:
            ergebnisse = pool.map(_arbeit, auftraege, chunksize=4)
    else:
        ergebnisse = [_arbeit(a) for a in auftraege]
    shutil.rmtree(arbeit, ignore_errors=True)
    summe, inhalt, fehler = collections.Counter(), collections.Counter(), []
    for e, kz in ergebnisse:
        summe.update(e["zahl"])
        inhalt.update(kz)
        if e["abweichungen"]:
            fehler.append(e)
    return {"regel": regel, "markt_noetig": markt_noetig, "szenarien": szenarien, "startwert": startwert,
            "szenarien_mit_abweichung": len(fehler), "summe": dict(summe), "inhalt": dict(inhalt), "fehler": fehler}


def drucken(r, zeigen=5):
    name = {"tag": "Tagesregel (Test 4)", "stunde": "Stundenregel (Test 1)"}[r["regel"]]
    lesart = "" if r["regel"] == "stunde" else (" [Lesart: Marktdaten nötig]" if r["markt_noetig"] else " [Lesart: wörtlich, ohne Marktdaten-Bedingung]")
    print(f"== {name}{lesart}: {r['szenarien']} Szenarien (Startwert {r['startwert']}), {r['summe'].get('laeufe', 0)} Läufe verglichen, "
          f"{r['szenarien_mit_abweichung']} Szenarien mit Abweichung")
    print("   Bot:", json.dumps(r["summe"], sort_keys=True))
    print("   Inhalt:", json.dumps(r["inhalt"], sort_keys=True))
    arten = collections.Counter(a["was"] for e in r["fehler"] for a in e["abweichungen"])
    if arten:
        print("   Abweichungen nach Art:", dict(arten))
    for e in r["fehler"][:zeigen]:
        print(f"   Szenario {e['nr']}:")
        for a in e["abweichungen"][:4]:
            print("      ", json.dumps(a, ensure_ascii=False))


def main(argv=None):
    p = argparse.ArgumentParser()
    p.add_argument("--bot", type=Path, default=HIER / "swing-hybrid")
    p.add_argument("--szenarien", type=int, default=300)
    p.add_argument("--erste", type=int, default=0)
    p.add_argument("--startwert", type=int, default=STARTWERT)
    p.add_argument("--regel", choices=["tag", "stunde", "beide"], default="beide")
    p.add_argument("--woertlich", action="store_true", help="Tagesregel ohne Marktdaten-Bedingung vergleichen")
    p.add_argument("--prozesse", type=int, default=4)
    p.add_argument("--json", type=Path)
    a = p.parse_args(argv)
    ergebnisse = []
    for regel in (["tag", "stunde"] if a.regel == "beide" else [a.regel]):
        t0 = time.time()
        r = lauf(a.bot, a.szenarien, a.startwert, regel, not a.woertlich, a.prozesse, a.erste)
        drucken(r)
        print(f"   ({time.time() - t0:.0f} s)")
        ergebnisse.append(r)
    if a.json:
        a.json.write_text(json.dumps(ergebnisse, indent=1, ensure_ascii=False))
    return 1 if any(r["szenarien_mit_abweichung"] for r in ergebnisse) else 0


if __name__ == "__main__":
    sys.exit(main())
