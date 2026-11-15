"""V-ENG-02 Teil 4: Papier-Bot mit nachgestellter Boerse in einem temporaeren Verzeichnis (kein Netz, kein Schluessel).
Aufruf: cd swing-hybrid && .venv/bin/python -I -B reports/audit/evidence/V-ENG-02/v4_bot.py "$(mktemp -d)"   (Arbeitsverzeichnis ausserhalb des Repos). Konfiguration wie vorwaertstest/config_lauf.json, nur Coins ersetzt."""
import json, shutil, sys
from pathlib import Path
sys.path.insert(0, "/home/user/OdinGate-Botv134/swing-hybrid")
from vorwaertstest import bot, kern, dashboard_daten

ARB = Path(sys.argv[1]).resolve(); assert not str(ARB).startswith("/home/user/OdinGate-Botv134"), "Arbeitsverzeichnis muss ausserhalb des Repos liegen"
H = kern.STUNDE_MS; TAG = 24 * H
T0 = 1_800_000_000_000 - (1_800_000_000_000 % TAG) + 5 * 60_000          # 00:05 UTC
echt = json.loads(Path("/home/user/OdinGate-Botv134/swing-hybrid/vorwaertstest/config_lauf.json").read_text())
COINS = [f"C{i}" for i in range(10)]
CFG = {**echt, "coins": COINS, "daten": "x"}
print("Konfiguration aus config_lauf.json:", {k: echt[k] for k in ("modus", "kapital_usd", "hebel", "tagesverlust_limit", "max_order_usd")})
still = lambda *_: None


class Boerse:
    key = secret = ""

    def __init__(self, kurs, alt):
        self.kurs, self.alt, self.jetzt, self.aufrufe = dict(kurs), dict(alt), T0, 0

    def kerzen(self, sym, minuten=60, limit=3, start_ms=None, ende_ms=None):
        c = sym.removesuffix("USDT")
        if start_ms is not None:
            return [{"start": start_ms, "open": 0, "high": 0, "low": 0, "close": self.alt[c]}]
        letzte = self.jetzt - self.jetzt % H - H
        return [{"start": letzte, "open": 0, "high": 0, "low": 0, "close": self.kurs[c]}, {"start": letzte + H, "open": 0, "high": 0, "low": 0, "close": self.kurs[c]}]

    def kontrakt(self, sym):
        return {"status": "Trading", "min_menge": 0.001, "schritt": 0.001, "tick": 0.01, "funding_minuten": 480}

    def ticker(self, sym):
        p = self.kurs[sym.removesuffix("USDT")]
        return {"geld": p - 0.005, "brief": p + 0.005, "letzter": p, "mark": p, "funding": 0.0, "umsatz24h": 1e9}

    def buch(self, sym, tiefe=25):
        p = self.kurs[sym.removesuffix("USDT")]
        return {"geld": [(p - 0.005, 1e9)], "brief": [(p + 0.005, 1e9)]}


def lauf(api, d, t):
    api.jetzt = t
    return bot.schritt(CFG, api, d, t, melden=still)


def frisch(name):
    d = ARB / name; shutil.rmtree(d, ignore_errors=True); d.mkdir(parents=True); return d


def zeile(d, r, was):
    z = json.loads((d / "zustand.json").read_text()); v = r["vermoegen"]; k = dashboard_daten.bauen(CFG, d)["kennzahlen"][0]
    print(f"  {was:44s} netto ohne Rebate {v['netto_ohne_rebate']:+9.0f} USD | Kontostand {CFG['kapital_usd'] + v['netto_mit_rebate']:+8.0f} USD | Orders {r['orders']} | "
          f"Short-Positionen {sum(1 for q in z['pos'].values() if q < 0)}, Long {sum(1 for q in z['pos'].values() if q > 0)} | Positionswert {k['positionswert_usd']:.0f} | "
          f"margin_pct {k['margin_pct']} | einbruch_pct {k['einbruch_pct']} | gesperrt_tag '{z['gesperrt_tag']}'")


# ---- Szenario 1: zehn Shorts (wie der laufende Test), Kurse steigen ueber drei Tage um 12 % je Tag; Signal bleibt Short ----
print("\nSzenario 1: 10 Coins short, je 1.500 USD; Anstieg je Tag +12 % (Referenzkurs von vor 14 Tagen bleibt darueber)")
d = frisch("s1"); api = Boerse({c: 100.0 for c in COINS}, {c: 200.0 for c in COINS})
zeile(d, lauf(api, d, T0), "Start 00:05, alle short bei 100")
for tag, kurs in ((1, 112.0), (2, 125.44), (3, 140.49)):
    api.kurs = {c: kurs for c in COINS}
    zeile(d, lauf(api, d, T0 + tag * TAG), f"Tag {tag}, Kurs {kurs} ({(kurs / 100 - 1) * 100:+.1f} %)")
api.kurs = {c: 160.0 for c in COINS}
zeile(d, lauf(api, d, T0 + 4 * TAG), "Tag 4, Kurs 160 (+60 %)")

# ---- Szenario 2: erst Gewinn, dann Rueckgabe: Einbruchskennzahl des Dashboards gegen Verlust in Startkapital ----
print("\nSzenario 2: 10 Coins long ab 100, Anstieg auf 133,4 (+100 % vom Kapital), danach zurueck auf 100 (Signal bleibt Long)")
d = frisch("s2"); api = Boerse({c: 100.0 for c in COINS}, {c: 50.0 for c in COINS})
zeile(d, lauf(api, d, T0), "Start, alle long bei 100")
api.kurs = {c: 133.4 for c in COINS}; zeile(d, lauf(api, d, T0 + TAG), "Tag 1, Kurs 133,4")
api.kurs = {c: 116.7 for c in COINS}; zeile(d, lauf(api, d, T0 + 2 * TAG), "Tag 2, Kurs 116,7")
api.kurs = {c: 100.0 for c in COINS}; r = lauf(api, d, T0 + 3 * TAG); zeile(d, r, "Tag 3, Kurs 100")
st = bot.lesen(d / "stand.csv"); x = [float(s["netto_mit_rebate"]) for s in st]
print(f"  Rueckgang vom Hoechststand: {max(x) - x[-1]:.0f} USD = {(max(x) - x[-1]) / CFG['kapital_usd'] * 100:.1f} % des Startkapitals; "
      f"einbruch_pct im Dashboard: {dashboard_daten.bauen(CFG, d)['kennzahlen'][0]['einbruch_pct']} %")

# ---- Szenario 3: Tageslimit 1.0 greift erst, wenn an EINEM UTC-Tag mehr als das ganze Kapital verloren ist ----
print("\nSzenario 3: wann greift tagesverlust_limit = 1.0?")
d = frisch("s3"); api = Boerse({c: 100.0 for c in COINS}, {c: 200.0 for c in COINS})
lauf(api, d, T0)
api.kurs = {c: 133.0 for c in COINS}; zeile(d, lauf(api, d, T0 + 2 * H), "selber Tag, +33 %")
api.kurs = {c: 134.0 for c in COINS}; zeile(d, lauf(api, d, T0 + 3 * H), "selber Tag, +34 %")
