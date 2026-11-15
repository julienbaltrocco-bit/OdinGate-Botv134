"""INF: Idempotenz, Neustart, Absturz, Wettlauf, Ausfall und fehlende Marktdaten des Papier-Bots.

Alle Versuche laufen in temporaeren Verzeichnissen mit einer nachgestellten Boerse (Muster aus
tests/test_vorwaertstest_bot.py:22-46, hier um eine laufende Uhr und gezielte Fehler erweitert).
Die echten Lauf-Verzeichnisse und das Netz werden nicht beruehrt.

Aufruf (aus swing-hybrid):  .venv/bin/python -I -B <dieses Skript>
"""
import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, "/home/user/OdinGate-Botv134/swing-hybrid")
from vorwaertstest import bot, dashboard_daten, kern          # noqa: E402
from vorwaertstest.yubit import YubitFehler                   # noqa: E402

H = kern.STUNDE_MS
T0 = 1_800_000_000_000 - (1_800_000_000_000 % H) + 5 * 60_000      # 5 Minuten nach einer vollen Stunde
CFG = {"modus": "papier", "kapital_usd": 5000, "hebel": 3.0, "coins": ["AAA", "BBB"], "tagesverlust_limit": 1.0,
       "preisgrenze": 0.0005, "max_order_usd": 2000, "daten": "x"}
TPSL = {**CFG, "tp": 0.15, "sl": 0.05}
still = lambda *_: None


class Boerse:
    """Nachgestellte Boerse mit eigener Uhr. kaputt: Coins, deren Abruf scheitert. haken: einmaliger Eingriff beim ersten Abruf."""
    key = secret = ""

    def __init__(self, kurse, alt, jetzt=T0):
        self.kurse, self.alt, self.jetzt, self.kaputt, self.haken, self.stau_h, self.aufrufe = kurse, alt, jetzt, set(), None, 0, 0

    def kerzen(self, sym, minuten=60, limit=3, start_ms=None, ende_ms=None):
        c = sym.removesuffix("USDT")
        if self.haken:
            h, self.haken = self.haken, None
            h()
        if c in self.kaputt:
            raise YubitFehler(f"HTTP 429 bei /klines ({c})")
        if start_ms is not None:
            return [{"start": start_ms, "open": 0, "high": 0, "low": 0, "close": self.alt[c]}]
        neueste = self.jetzt - self.jetzt % H - self.stau_h * H          # stau_h = 0: die neueste Kerze laeuft noch
        return [{"start": neueste - H, "open": 0, "high": 0, "low": 0, "close": self.kurse[c]},
                {"start": neueste, "open": 0, "high": 0, "low": 0, "close": self.kurse[c]}]

    def kontrakt(self, sym):
        return {"status": "Trading", "min_menge": 0.1, "schritt": 0.1, "tick": 0.01, "funding_minuten": 480}

    def ticker(self, sym):
        p = self.kurse[sym.removesuffix("USDT")]
        return {"geld": p - 0.05, "brief": p + 0.05, "letzter": p, "mark": p, "funding": 0.0001, "umsatz24h": 1e6}

    def buch(self, sym, tiefe=25):
        p = self.kurse[sym.removesuffix("USDT")]
        return {"geld": [(p - 0.05, 1e6)], "brief": [(p + 0.05, 1e6)]}


def lauf(cfg, api, d, t):
    api.jetzt = t
    return bot.schritt(cfg, api, d, t, melden=still)


def lage(d):
    z = json.loads((d / "zustand.json").read_text())
    pr, st, sp = bot.lesen(d / "protokoll.csv"), bot.lesen(d / "stand.csv"), bot.lesen(d / "spannen.csv")
    return z, pr, st, sp


def titel(t):
    print("\n" + "=" * 110 + "\n" + t + "\n" + "-" * 110)


def tmp():
    return Path(tempfile.mkdtemp(prefix="inf_"))


# ------------------------------------------------------------------------------------------------ V1
titel("V1  Zweifache Ausfuehrung im selben Augenblick (derselbe Zeitstempel)")
d = tmp(); api = Boerse({"AAA": 100.0, "BBB": 50.0}, {"AAA": 90.0, "BBB": 60.0})
r1 = lauf(CFG, api, d, T0); r2 = lauf(CFG, api, d, T0)
z, pr, st, sp = lage(d)
print(f"Orders im 1. Lauf: {r1['orders']}, im 2. Lauf: {r2['orders']}  -> Handel ist ueber den Zustand idempotent: {r2['orders'] == 0}")
print(f"stand.csv: {len(st)} Zeilen, Zeitstempel {[r['zeit'] for r in st]}  -> doppelte Zeile mit gleichem Zeitstempel: {st[0]['zeit'] == st[1]['zeit']}")
print(f"spannen.csv: {len(sp)} Zeilen fuer 2 Coins (jede Messung doppelt)")
print("Im Zustand steht letzte_kerze =", z["letzte_kerze"], "- das Feld wird in bot.py nur geschrieben (Zeile 280), nie gelesen.")

# ------------------------------------------------------------------------------------------------ V2
titel("V2  Absturz zwischen dem Anhaengen an die CSV-Dateien (bot.py:276-279) und zustand_speichern (bot.py:281)")
d = tmp(); api = Boerse({"AAA": 100.0, "BBB": 50.0}, {"AAA": 90.0, "BBB": 60.0})
echt = bot.zustand_speichern
def absturz(*a):
    raise OSError("simulierter Absturz vor dem Schreiben von zustand.json")
bot.zustand_speichern = absturz
try:
    lauf(CFG, api, d, T0)
except OSError as e:
    print("1. Lauf:", e, "| zustand.json vorhanden:", (d / "zustand.json").exists(), "| Zeilen protokoll.csv:", len(bot.lesen(d / "protokoll.csv")))
bot.zustand_speichern = echt
r = lauf(CFG, api, d, T0 + 5 * 60_000)
z, pr, st, sp = lage(d)
print(f"2. Lauf (Neustart): {r['orders']} Orders. protokoll.csv hat jetzt {len(pr)} Orders, zustand.orders = {z['orders']}, Positionen {z['pos']}")
vol = sum(float(x["volumen"]) for x in pr); geb = sum(float(x["gebuehr"]) for x in pr)
print(f"Summe Volumen laut protokoll.csv {vol:.2f} USDT, Gebuehr {geb:.4f}; laut Zustand Gebuehr {z['gebuehr']:.4f}  -> Protokoll zaehlt doppelt: {abs(geb - 2 * z['gebuehr']) < 0.01}")
dash = dashboard_daten.bauen(CFG, d)["kennzahlen"][0]
print(f"Dashboard: orders {dash['orders']}, volumen_usd {dash['volumen_usd']}, gebuehr_usd {dash['gebuehr_usd']} (Gebuehr stammt aus stand.csv, Orders und Volumen aus protokoll.csv)")
text = bot.bericht(CFG, d)
print("bericht.md:", [x for x in text.splitlines() if "Orders, Volumen" in x or "Gebühr gezahlt" in x])
print(f"stand.csv: {len(st)} Zeilen fuer 2 Versuche (die Zeile des abgestuerzten Laufs bleibt stehen): {[(x['zeit'], x['orders']) for x in st]}")

# ------------------------------------------------------------------------------------------------ V3
titel("V3  Zwei gleichzeitig laufende Instanzen auf demselben Datenordner (kein Sperrmechanismus in bot.py oder stunde.sh)")
d = tmp()
a = Boerse({"AAA": 100.0, "BBB": 50.0}, {"AAA": 90.0, "BBB": 60.0}); b = Boerse({"AAA": 100.0, "BBB": 50.0}, {"AAA": 90.0, "BBB": 60.0})
a.haken = lambda: lauf(CFG, b, d, T0 + 1000)          # Instanz B laeuft vollstaendig, waehrend A noch Marktdaten liest
ra = lauf(CFG, a, d, T0)
z, pr, st, sp = lage(d)
print(f"Instanz A meldet {ra['orders']} Orders. protokoll.csv: {len(pr)} Orders, zustand.orders = {z['orders']}, Positionen {z['pos']}")
print("Orders im Protokoll:", [(x["coin"], x["seite"], x["menge"]) for x in pr])
soll = {}
for x in pr:
    soll[x["coin"]] = soll.get(x["coin"], 0.0) + float(x["menge"]) * (1 if x["seite"] == "kauf" else -1)
print(f"Position laut Protokoll {soll} gegen Zustand {z['pos']}  -> Protokoll und Zustand widersprechen sich: {soll != z['pos']}")
print("Im Live-Modus waeren das vier echte Orders (doppelte Positionsgroesse an der Boerse); erst der naechste Lauf wuerde am Abgleich bot.py:177-182 abbrechen.")

# ------------------------------------------------------------------------------------------------ V4
titel("V4  Ausfall des Zeitgebers: 10 Stunden kein Lauf, Konto mit Stop 5 % / Ziel 15 % (Konfiguration wie Test 2)")
d = tmp(); api = Boerse({"AAA": 100.0, "BBB": 50.0}, {"AAA": 90.0, "BBB": 60.0})
lauf(TPSL, api, d, T0)
z0 = json.loads((d / "zustand.json").read_text())
api.kurse.update({"AAA": 100.0, "BBB": 60.0}); api.alt.update({"BBB": 70.0})        # BBB steigt 20 % gegen den Short, Signal bleibt Short
r = lauf(TPSL, api, d, T0 + 10 * H)
z, pr, st, sp = lage(d)
aus = pr[-1]
verlust = (float(aus["fuellkurs"]) / z0["einstieg"]["BBB"] - 1) * 100
print(f"Erster Lauf nach dem Ausfall: {r['orders']} Order, Grund '{aus['grund']}', Ausstieg BBB bei {aus['fuellkurs']} nach Einstieg {z0['einstieg']['BBB']}: {verlust:.1f} % gegen die Position (Stop war 5 %)")
print(f"Hinweise des Laufs zur Luecke: {r['warnungen']}  | stand.csv-Zeitstempel: {[x['zeit'] for x in st]} (Luecke von 10 Stunden ohne Kennzeichnung)")
print(f"Funding: {z['funding']:.4f} USDT fuer {kern.funding_faellig(T0, T0 + 10 * H, 480)} Termin(e), nachtraeglich mit Rate und Kurs des Wiederanlaufs gebucht (bot.py:185-189)")

# ------------------------------------------------------------------------------------------------ V5
titel("V5  Marktdaten eines Coins fehlen in genau dem Lauf, in dem sein Signal dreht")
d = tmp(); api = Boerse({"AAA": 100.0, "BBB": 50.0}, {"AAA": 90.0, "BBB": 60.0})
lauf(CFG, api, d, T0)
api.kurse["BBB"] = 66.0; api.kaputt = {"BBB"}                                       # BBB dreht auf Long, Abruf scheitert
r = lauf(CFG, api, d, T0 + H)
z, pr, st, sp = lage(d)
print(f"Lauf mit Fehler: {r['orders']} Orders, Rueckgabe-Hinweise {r['warnungen']}")
print(f"Position BBB bleibt {z['pos']['BBB']} (Short), bewertet mit altem Kurs {z['kurs']['BBB']} statt 66.0; stand.csv brutto {st[-1]['brutto']}")
wahr = kern.vermoegen(z, {"AAA": 100.0, "BBB": 66.0})["brutto"]
print(f"Tatsaechliches Brutto bei Kurs 66: {wahr:.2f} USDT  -> stand.csv weicht um {float(st[-1]['brutto']) - wahr:.2f} USDT ab, ohne Kennzeichnung in der Zeile")
print(f"spannen.csv fuer diesen Lauf: {[x['coin'] for x in sp if x['zeit'] == st[-1]['zeit']]} | Dateien im Datenordner: {sorted(p.name for p in d.iterdir())} (keine Protokolldatei mit dem Hinweis)")
api.kaputt = set()
r = lauf(CFG, api, d, T0 + 2 * H)
print(f"Naechster Lauf ohne Fehler: {r['orders']} Orders (Dreh wird einen Takt spaeter nachgeholt)")
api.kaputt = {"AAA", "BBB"}
try:
    lauf(CFG, api, d, T0 + 3 * H)
except SystemExit as e:
    print("Alle Coins fehlen -> SystemExit:", str(e)[:90], "| stand.csv unveraendert:", len(bot.lesen(d / "stand.csv")) == len(st) + 1)

# ------------------------------------------------------------------------------------------------ V6
titel("V6  Veraltete Kerzen: wie alt darf die letzte abgeschlossene Stundenkerze sein (bot.py:88)?")
for stau, versatz in ((0, 5), (1, 5), (2, 5), (2, 59), (3, 0), (3, 5)):
    d = tmp(); api = Boerse({"AAA": 100.0, "BBB": 50.0}, {"AAA": 90.0, "BBB": 60.0}); api.stau_h = stau
    t = T0 - 5 * 60_000 + versatz * 60_000
    try:
        r = lauf(CFG, api, d, t)
        z = json.loads((d / "zustand.json").read_text())
        alter = (t - (z["letzte_kerze"] + H)) / 60_000
        print(f"neueste gelieferte Kerze beginnt {stau} h vor der laufenden Stunde, Lauf {versatz:2d} min nach voller Stunde: {r['orders']} Orders, Schluss der verwendeten Kerze ist {alter:.0f} min alt, Hinweise {r['warnungen']}")
    except SystemExit as e:
        print(f"neueste gelieferte Kerze beginnt {stau} h vor der laufenden Stunde, Lauf {versatz:2d} min nach voller Stunde: Abbruch ({str(e)[:70]})")

# ------------------------------------------------------------------------------------------------ V7
titel("V7  Abgeschnittene letzte Zeile in protokoll.csv (Absturz mitten im Schreiben)")
d = tmp(); api = Boerse({"AAA": 100.0, "BBB": 50.0}, {"AAA": 90.0, "BBB": 60.0})
lauf(CFG, api, d, T0)
p = d / "protokoll.csv"; roh = p.read_text(); p.write_text(roh[: len(roh) - 60])   # letzte Zeile unvollstaendig, kein Zeilenende
for name, f in (("bot.bericht", lambda: bot.bericht(CFG, d)), ("dashboard_daten.bauen", lambda: dashboard_daten.bauen(CFG, d))):
    try:
        f(); print(name, "laeuft durch")
    except Exception as e:                                                        # noqa: BLE001
        print(f"{name} bricht ab: {type(e).__name__}: {str(e)[:80]}")
api.kurse["AAA"] = 80.0
r = lauf(CFG, api, d, T0 + H)                                                      # AAA dreht: neue Orders werden angehaengt
print("Naechster Lauf haengt an die kaputte Zeile an:", repr(p.read_text().splitlines()[2][:150]))

# ------------------------------------------------------------------------------------------------ V8
titel("V8  STOPP-Datei: das Board zeigt weiter einen frischen 'Bot-Stand'")
d = tmp(); api = Boerse({"AAA": 100.0, "BBB": 50.0}, {"AAA": 90.0, "BBB": 60.0})
lauf(CFG, api, d, T0)
(d / "STOPP").write_text("")
r = lauf(CFG, api, d, T0 + 6 * H)
dd = dashboard_daten.bauen(CFG, d)
print(f"Rueckgabe {r}; Dashboard: letzter_lauf {dd['kennzahlen'][0]['letzter_lauf']} (Bot-Uhr T0), geschrieben {dd['geschrieben']} (Wanduhr jetzt), takt_minuten {dd['takt_minuten']}")
print("docs/index.html:477 zeigt das Alter aus 'geschrieben' an; 'letzter_lauf' wird im Board nicht verwendet (grep).")
