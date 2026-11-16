"""V-QR-01 (5): Papier-Bot mit der laufenden Konfiguration (config_lauf.json, nur gelesen) gegen eine nachgestellte Boerse
in einem temporaeren Verzeichnis. Zehn Shorts, Kurse steigen an drei Tagen um je 12 %. Greift irgendeine Bremse?"""
import json, sys
from pathlib import Path
sys.path.insert(0, ".")
from vorwaertstest import bot, kern

cfg = json.loads(Path("vorwaertstest/config_lauf.json").read_text())
daten = Path(sys.argv[1]); assert "scratchpad" in str(daten)
H = kern.STUNDE_MS
T0 = 1_800_000_000_000 - (1_800_000_000_000 % (24 * H)) + 5 * 60_000     # 00:05 UTC

class Boerse:
    key = secret = ""
    def __init__(self, kurse, alt): self.kurse, self.alt, self.aufrufe, self.jetzt = kurse, alt, 0, T0
    def kerzen(self, sym, minuten=60, limit=3, start_ms=None, ende_ms=None):
        c = sym.removesuffix("USDT")
        if start_ms is not None:
            return [{"start": start_ms, "open": 0, "high": 0, "low": 0, "close": self.alt[c]}]
        letzte = self.jetzt - self.jetzt % H - H
        return [{"start": letzte, "open": 0, "high": 0, "low": 0, "close": self.kurse[c]}, {"start": letzte + H, "open": 0, "high": 0, "low": 0, "close": self.kurse[c]}]
    def kontrakt(self, sym): return {"status": "Trading", "min_menge": 0.001, "schritt": 0.001, "tick": 0.01, "funding_minuten": 480}
    def ticker(self, sym):
        p = self.kurse[sym.removesuffix("USDT")]; return {"geld": p - 0.01, "brief": p + 0.01, "letzter": p, "mark": p, "funding": 0.0, "umsatz24h": 1e9}
    def buch(self, sym, tiefe=25):
        p = self.kurse[sym.removesuffix("USDT")]; return {"geld": [(p - 0.01, 1e9)], "brief": [(p + 0.01, 1e9)]}

api = Boerse({c: 100.0 for c in cfg["coins"]}, {c: 250.0 for c in cfg["coins"]})   # Kurs weit unter dem von vor 14 Tagen: Short
meld = []
for tag in range(4):
    for std in (0, 12):
        api.jetzt = T0 + (tag * 24 + std) * H
        r = bot.schritt(cfg, api, daten, api.jetzt, melden=meld.append)
        z = json.loads((daten / "zustand.json").read_text())
        v = r["vermoegen"]["netto_mit_rebate"]
        print(f"Tag {tag} {std:02d}:05  Kurs {api.kurse['BTC']:7.2f}  Orders {r['orders']:2d}  Shorts {sum(1 for q in z['pos'].values() if q < 0)}  "
              f"Einsatz {sum(abs(q) * api.kurse[c] for c, q in z['pos'].items()):8.0f} $  Ergebnis {v:9.2f} $  Konto {cfg['kapital_usd'] + v:9.2f} $  gesperrt_tag={z['gesperrt_tag']!r}")
        for c in api.kurse: api.kurse[c] *= 1.06
print("Meldungen mit 'Limit':", [m for m in meld if "Limit" in m])
