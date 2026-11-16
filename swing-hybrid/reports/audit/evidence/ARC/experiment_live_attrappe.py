"""ARC: bot.live_order mit einer Attrappe (kein Netz, kein Schluessel, keine Umgebungsvariable, kein Zustand).
Zeigt nur das Verhalten der Funktion, wenn die Boerse die Ausfuehrung erst nach der Wartezeit von 1,5 s meldet.
Aufruf aus swing-hybrid: .venv/bin/python -I -B <skript>
"""
import sys
sys.path.insert(0, ".")
from vorwaertstest import bot
from vorwaertstest.yubit import YubitFehler
bot.time.sleep = lambda s: None                      # Wartezeit ueberspringen

class Attrappe:
    """Order wird angenommen und sofort voll gefuellt; die Fill-Abfrage liefert das aber erst beim zweiten Mal."""
    def __init__(self): self.ruf = []; self.n = 0
    def order(self, sym, seite, menge, preis, idx, reduce):
        self.ruf.append(("order", seite, menge, preis, idx, reduce)); return {"order_id": "1", "link_id": "x"}
    def fills(self, sym, oid):
        self.n += 1; self.ruf.append(("fills", self.n))
        return [] if self.n == 1 else [{"execQty": "15.0", "execPrice": "100.05", "execFee": "1.2"}]
    def storno(self, sym, oid):
        self.ruf.append(("storno",)); raise YubitFehler("Order bereits gefuellt")

m = {"sym": "AAAUSDT", "kontrakt": {"tick": 0.01, "schritt": 0.1}, "buch": {"geld": [(100.0, 1e9)], "brief": [(100.05, 1e9)]}}
cfg = {"preisgrenze": 0.0005, "max_order_usd": 2000}
api = Attrappe()
kurs, q, gebuehr = bot.live_order(api, m, True, 15.0, 1, False, cfg)
print("Aufrufe an die Boerse:", api.ruf)
print("Rueckgabe von live_order: Kurs", kurs, "| Menge", q, "| Gebuehr", gebuehr)
print("Folge in bot.schritt (bot.py:257-259): q <= 0 -> Hinweis 'nichts gefuellt', Zustand unveraendert;")
print("die Boerse haelt aber 15 Stueck. Der naechste Lauf bricht in bot.py:177-182 mit SystemExit ab (Position weicht ab).")
