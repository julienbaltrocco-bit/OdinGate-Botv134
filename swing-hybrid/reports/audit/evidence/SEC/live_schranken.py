"""SEC: Schranken vor echten Orders, nachgestellte Boerse, temporaere Verzeichnisse.

Aufruf (aus swing-hybrid):  .venv/bin/python -I <dieses Skript> <pfad-zu-swing-hybrid>
Es wird nichts im Repo geschrieben, kein Netz benutzt, kein echter Schluessel verwendet.
"""
import json
import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, sys.argv[1])
from vorwaertstest import bot, kern  # noqa: E402
from vorwaertstest.yubit import YubitFehler  # noqa: E402

H = kern.STUNDE_MS
JETZT = 1_800_000_000_000 - (1_800_000_000_000 % H) + 5 * 60_000
CFG = {"modus": "papier", "kapital_usd": 1000, "hebel": 3.0, "coins": ["AAA", "BBB"], "tagesverlust_limit": 1.0,
       "preisgrenze": 0.0005, "max_order_usd": 2000, "daten": "x"}


class Boerse:
    """Wie tests/test_vorwaertstest_bot.py::Boerse, zusaetzlich private Aufrufe (werden gezaehlt)."""

    def __init__(self, kurse, alt, key="", secret=""):
        self.kurse, self.alt, self.key, self.secret, self.aufrufe = kurse, alt, key, secret, 0
        self.privat, self.pos, self.letzte = [], {}, {}

    def kerzen(self, sym, minuten=60, limit=3, start_ms=None, ende_ms=None):
        c = sym.removesuffix("USDT")
        if start_ms is not None:
            return [{"start": start_ms, "open": 0, "high": 0, "low": 0, "close": self.alt[c]}]
        letzte = self.jetzt - self.jetzt % H - H
        return [{"start": letzte, "open": 0, "high": 0, "low": 0, "close": self.kurse[c]}]

    def kontrakt(self, sym):
        return {"status": "Trading", "min_menge": 0.1, "schritt": 0.1, "tick": 0.01, "funding_minuten": 480}

    def ticker(self, sym):
        p = self.kurse[sym.removesuffix("USDT")]
        return {"geld": p - 0.05, "brief": p + 0.05, "letzter": p, "mark": p, "funding": 0.0001, "umsatz24h": 1e6}

    def buch(self, sym, tiefe=25):
        p = self.kurse[sym.removesuffix("USDT")]
        return {"geld": [(p - 0.05, 1e6)], "brief": [(p + 0.05, 1e6)]}

    # ---- private Endpunkte (nur Stufe live) ----
    def positionen(self, settle="USDT"):
        self.privat.append("positionen")
        return [{"symbol": c + "USDT", "size": abs(q), "positionIdx": 1 if q > 0 else 2} for c, q in self.pos.items() if q]

    def order(self, symbol, seite, menge, preis, position_idx, reduce_only):
        self.privat.append(f"order {symbol} {seite} {menge} @ {preis} reduce={reduce_only}")
        c = symbol.removesuffix("USDT")
        q = float(menge) * (1 if seite == "Buy" else -1)
        self.pos[c] = round(self.pos.get(c, 0.0) + q, 8)
        self.letzte = {"execQty": menge, "execPrice": preis, "execFee": "0"}
        return {"order_id": "1", "link_id": "x"}

    def fills(self, symbol, order_id):
        self.privat.append("fills")
        return [self.letzte]

    def storno(self, symbol, order_id):
        self.privat.append("storno")
        return {}


def lauf(cfg, api, daten, jetzt):
    api.jetzt = jetzt
    try:
        r = bot.schritt(cfg, api, Path(daten), jetzt, melden=lambda *_: None)
        return f"modus={r.get('modus')} orders={r.get('orders')}", r
    except SystemExit as e:
        return f"SystemExit: {str(e)[:70]}", None


bot.time.sleep = lambda s: None          # 1,5 s Wartezeit in live_order ueberspringen

print("== 1. Matrix der drei Schranken (modus x YUBIT_LIVE x Schluessel) ==")
print(f"{'modus':7s} {'YUBIT_LIVE':11s} {'Schluessel':10s} -> Ergebnis | private Aufrufe")
for modus in ("papier", "live"):
    for env in (None, "nein", "JA", "ja ", "1", "true", "ja"):
        for schluessel in (False, True):
            if env is None:
                os.environ.pop("YUBIT_LIVE", None)
            else:
                os.environ["YUBIT_LIVE"] = env
            api = Boerse({"AAA": 100.0, "BBB": 50.0}, {"AAA": 90.0, "BBB": 60.0},
                         key="k" if schluessel else "", secret="s" if schluessel else "")
            with tempfile.TemporaryDirectory() as d:
                text, _ = lauf({**CFG, "modus": modus}, api, d, JETZT)
            orders = sum(1 for x in api.privat if x.startswith("order"))
            print(f"{modus:7s} {str(env)!r:11s} {str(schluessel):10s} -> {text:60s} | privat={len(api.privat)} echte_orders={orders}")

print()
print("== 2. Live-Modus: Sicherheitsdeckel max_order_usd gilt auch fuer das Schliessen ==")
os.environ["YUBIT_LIVE"] = "ja"
api = Boerse({"AAA": 100.0, "BBB": 50.0}, {"AAA": 110.0, "BBB": 60.0}, key="k", secret="s")   # beide Short, je 1500 USDT
cfg = {**CFG, "modus": "live", "coins": ["AAA", "BBB"]}
with tempfile.TemporaryDirectory() as d:
    text, r = lauf(cfg, api, d, JETZT)
    z = json.loads((Path(d) / "zustand.json").read_text())
    print("Einstieg:", text, "| Positionen:", z["pos"])
    # AAA steigt um 40 % gegen den Short; Signal dreht auf Long (Kurs jetzt > Kurs vor 14 Tagen)
    api.kurse["AAA"] = 140.0
    api.privat.clear()
    text, r = lauf(cfg, api, d, JETZT + H)
    z = json.loads((Path(d) / "zustand.json").read_text())
    print("Nach +40 %, Signal dreht auf Long:", text)
    print("  Warnungen:", r["warnungen"] if r else None)
    print("  Position AAA laut Buch nach dem Lauf:", z["pos"]["AAA"], "(Short bleibt offen)" if z["pos"]["AAA"] < 0 else "")
    print("  private Aufrufe:", api.privat)
os.environ.pop("YUBIT_LIVE", None)
