"""ARC: Experimente am Papier-Bot mit nachgestellter Boerse in temporaeren Verzeichnissen.
Kein Netz, kein Schluessel, keine Beruehrung von vorwaertstest/lauf*, docs/ oder reports/ (ausser Ausgabe nach stdout).
Aufruf aus swing-hybrid: .venv/bin/python -I -B <skript>
"""
import json, sys, tempfile
from pathlib import Path
sys.path.insert(0, "src"); sys.path.insert(0, ".")
import numpy as np
from vorwaertstest import bot, kern, dashboard_daten
from vorwaertstest.yubit import YubitFehler
from hybrid import tpsl

H = kern.STUNDE_MS
JETZT = 1_800_000_000_000 - (1_800_000_000_000 % H) + 5 * 60_000
still = lambda *_: None

class Boerse:
    key = secret = ""
    def __init__(self, kurse, alt, tiefe=1e9, spanne=0.0):
        self.kurse, self.alt, self.tiefe, self.spanne, self.aufrufe = kurse, alt, tiefe, spanne, 0
        self.stunde = dict(kurse)                  # Schluss der letzten vollen Stunde (getrennt vom laufenden Kurs)
    def kerzen(self, sym, minuten=60, limit=3, start_ms=None, ende_ms=None):
        c = sym.removesuffix("USDT")
        if start_ms is not None:
            return [{"start": start_ms, "close": self.alt[c]}]
        letzte = self.jetzt - self.jetzt % H - H
        return [{"start": letzte, "close": self.stunde[c]}, {"start": letzte + H, "close": self.kurse[c]}]
    def kontrakt(self, sym): return {"status": "Trading", "min_menge": 0.001, "schritt": 0.001, "tick": 0.01, "funding_minuten": 480}
    def ticker(self, sym):
        p = self.kurse[sym.removesuffix("USDT")]
        return {"geld": p, "brief": p, "letzter": p, "mark": p, "funding": 0.0001, "umsatz24h": 1e6}
    def buch(self, sym, tiefe=25):
        p = self.kurse[sym.removesuffix("USDT")]
        return {"geld": [(p * (1 - self.spanne), self.tiefe)], "brief": [(p * (1 + self.spanne), self.tiefe)]}

def lauf(cfg, api, daten, jetzt):
    api.jetzt = jetzt
    return bot.schritt(cfg, api, daten, jetzt, melden=still)

CFG = {"modus": "papier", "kapital_usd": 5000, "hebel": 3.0, "coins": ["AAA"], "tagesverlust_limit": 1.0,
       "preisgrenze": 0.0005, "max_order_usd": 2000, "daten": "x", "tp": 0.15, "sl": 0.05}

print("=== E1: Stop/Ziel im Bot (jeder Aufruf, Mittelkurs) gegen Forschung tpsl._zustand (nur Stundenschluesse) ===")
with tempfile.TemporaryDirectory() as d:
    d = Path(d)
    api = Boerse({"AAA": 100.0}, {"AAA": 90.0})
    lauf(CFG, api, d, JETZT)                                     # Einstieg Long bei 100
    # innerhalb der Stunde faellt der Kurs kurz auf 94 (-6 %), die Stunde schliesst aber bei 97 (-3 %)
    pfad = [(10, 98.0), (15, 94.0), (20, 96.0), (55, 97.0)]
    for minute, kurs in pfad:
        api.kurse["AAA"] = kurs
        r = lauf(CFG, api, d, JETZT + minute * 60_000)
        z = json.loads((d / "zustand.json").read_text())
        print(f"  Aufruf +{minute:2d} min, Kurs {kurs:6.2f}: Orders {r['orders']}, Position {z['pos'].get('AAA', 0.0):.3f}, Sperre {z.get('sperre', {})}")
    pr = bot.lesen(d / "protokoll.csv")
    print("  Bot-Protokoll (Grund):", [(x["zeit"][-5:], x["grund"]) for x in pr])
c = np.array([100.0, 97.0, 98.0]); sig = np.array([1.0, 1.0, 1.0])
print("  Forschung, Stundenschluesse 100 -> 97 -> 98, sl=5 %, tp=15 %: Position", list(tpsl._zustand(c, sig, 0.15, 0.05, 0.0)), "(kein Stop)")
print("  Stuendlicher Aufruf (wie in bot.py-Kopf und README beschrieben) haette denselben Kursverlauf NICHT gestoppt:")
with tempfile.TemporaryDirectory() as d:
    d = Path(d)
    api = Boerse({"AAA": 100.0}, {"AAA": 90.0})
    lauf(CFG, api, d, JETZT)
    api.kurse["AAA"] = 97.0; api.stunde["AAA"] = 97.0
    r = lauf(CFG, api, d, JETZT + H)
    print("   Aufruf +60 min, Kurs 97.00: Orders", r["orders"], "Position", json.loads((d / "zustand.json").read_text())["pos"]["AAA"])

print()
print("=== E2: Absturz zwischen CSV-Anhaengen und Zustand-Speichern (bot.py:276-281) ===")
cfg2 = {**CFG, "coins": ["AAA", "BBB"]}; cfg2.pop("tp"); cfg2.pop("sl")
with tempfile.TemporaryDirectory() as d:
    d = Path(d)
    api = Boerse({"AAA": 100.0, "BBB": 50.0}, {"AAA": 90.0, "BBB": 60.0}, spanne=0.0005)
    echt = bot.zustand_speichern
    def kaputt(daten, z): raise OSError("simulierter Abbruch vor zustand.json")
    bot.zustand_speichern = kaputt
    try:
        lauf(cfg2, api, d, JETZT)
    except OSError as e:
        print("  1. Lauf:", e, "| zustand.json vorhanden:", (d / "zustand.json").exists(), "| Zeilen protokoll.csv:", len(bot.lesen(d / "protokoll.csv")))
    bot.zustand_speichern = echt
    lauf(cfg2, api, d, JETZT + 5 * 60_000)
    z = json.loads((d / "zustand.json").read_text())
    pr = bot.lesen(d / "protokoll.csv"); st = bot.lesen(d / "stand.csv")
    dash = dashboard_daten.bauen(cfg2, d)["kennzahlen"][0]
    print("  2. Lauf: zustand.orders =", z["orders"], "| Zeilen protokoll.csv =", len(pr), "| Zeilen stand.csv =", len(st))
    print("  Zustand: Gebuehr %.4f | Summe Gebuehr im Protokoll %.4f" % (z["gebuehr"], sum(float(x["gebuehr"]) for x in pr)))
    print("  Dashboard: orders =", dash["orders"], "| volumen_usd =", dash["volumen_usd"], "| tatsaechlich gehandelt laut Zustand:",
          round(sum(abs(q) * api.kurse[c] for c, q in z["pos"].items())))

print()
print("=== E3: Sicherheitsdeckel max_order_usd gilt auch fuer schliessende Orders (bot.live_order, ohne Netz, Attrappe) ===")
class Attrappe:
    def order(self, *a, **k): raise AssertionError("darf nicht erreicht werden")
m = {"sym": "AAAUSDT", "kontrakt": {"tick": 0.01, "schritt": 0.001}, "buch": {"geld": [(140.0, 1e9)], "brief": [(140.05, 1e9)]}}
cfg3 = {"preisgrenze": 0.0005, "max_order_usd": 2000}
menge = 15.0                                                    # Short 15 Stueck zu 100 $ = 1.500 $ eroeffnet; Kurs jetzt 140 $
try:
    bot.live_order(Attrappe(), m, True, menge, 2, True, cfg3)   # Kauf, positionIdx 2, reduce_only=True
except YubitFehler as e:
    print("  Schliessen einer Short-Position (1.500 $ Einstieg, Kurs +40 %):", e)
print("  Im Papier-Modus wird der Deckel nicht geprueft (bot.py:246-253): Stellen im Code, die max_order_usd lesen:")
src = Path("vorwaertstest/bot.py").read_text().splitlines()
for i, zeile in enumerate(src, 1):
    if "max_order_usd" in zeile or "preisgrenze" in zeile: print(f"    bot.py:{i}: {zeile.strip()[:120]}")

print()
print("=== E4: Tagesverlust-Limit 1.0 (config_lauf*.json) ===")
for name in ("config.json", "config_lauf.json", "config_lauf_tpsl.json"):
    c = json.loads(Path("vorwaertstest", name).read_text())
    print(f"  {name:24s} hebel {c['hebel']:<4} tagesverlust_limit {c['tagesverlust_limit']:<5} -> Schwelle {-c['tagesverlust_limit'] * c['kapital_usd']:8.0f} $ "
          f"| Nominal je Coin {c['kapital_usd'] * c['hebel'] / len(c['coins']):6.0f} $ | max_order_usd {c['max_order_usd']} | tp {c.get('tp', '-')} sl {c.get('sl', '-')}")
with tempfile.TemporaryDirectory() as d:
    d = Path(d)
    cfg4 = {**cfg2}
    api = Boerse({"AAA": 100.0, "BBB": 50.0}, {"AAA": 90.0, "BBB": 40.0})
    lauf(cfg4, api, d, JETZT)                                    # beide Long, je 7.500 $ (Hebel 3, 2 Coins)
    api.kurse.update(AAA=70.0, BBB=35.0); api.stunde.update(AAA=95.0, BBB=45.0)   # -30 % auf 15.000 $ Position = -4.500 $ = -90 % des Kapitals
    r = lauf(cfg4, api, d, JETZT + H)
    z = json.loads((d / "zustand.json").read_text())
    print("  Papier-Konto nach -30 %% Kursfall bei Hebel 3: netto %.0f $ von 5000 $ Kapital, gesperrt_tag = %r, Positionen offen: %s" %
          (r["vermoegen"]["netto_ohne_rebate"], z["gesperrt_tag"], {k: round(v, 1) for k, v in z["pos"].items()}))
    api.kurse.update(AAA=50.0, BBB=25.0)
    r = lauf(cfg4, api, d, JETZT + 2 * H)
    z = json.loads((d / "zustand.json").read_text())
    print("  nach -50 %%: netto %.0f $ (Konto rechnerisch %.0f $), gesperrt_tag = %r, Positionen offen: %s" %
          (r["vermoegen"]["netto_ohne_rebate"], 5000 + r["vermoegen"]["netto_ohne_rebate"], z["gesperrt_tag"], {k: round(v, 1) for k, v in z["pos"].items()}))
