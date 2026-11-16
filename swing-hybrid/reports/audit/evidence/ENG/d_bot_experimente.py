"""ENG-D: Experimente am Papier-Bot mit nachgestellter Boerse in temporaeren Verzeichnissen.
Kein Netz, keine echten Schluessel, keine Schreibzugriffe ausserhalb des uebergebenen Arbeitsverzeichnisses.
Aufruf: .venv/bin/python -I -B d_bot_experimente.py <arbeitsverzeichnis>"""
import json, os, shutil, sys, tempfile
from pathlib import Path
sys.path.insert(0, "/home/user/OdinGate-Botv134/swing-hybrid")
from vorwaertstest import bot, kern, dashboard_daten
from vorwaertstest.yubit import YubitFehler

ARB = Path(sys.argv[1]); ARB.mkdir(parents=True, exist_ok=True)
H = kern.STUNDE_MS
JETZT = 1_800_000_000_000 - (1_800_000_000_000 % H) + 5 * 60_000        # 5 Minuten nach voller Stunde
still = lambda *_: None
bot.time.sleep = lambda *_: None                                         # live_order wartet sonst 1,5 s


class Boerse:
    key = secret = ""

    def __init__(self, kurse, alt, min_menge=0.1, schritt=0.1, tiefe=1e9, spanne=0.1, funding=0.0001, f_min=480):
        self.kurse, self.alt, self.min, self.schritt, self.tiefe, self.spanne = dict(kurse), dict(alt), min_menge, schritt, tiefe, spanne
        self.funding, self.f_min, self.aufrufe, self.jetzt, self.verzug, self.ohne_alt = funding, f_min, 0, JETZT, 0, set()

    def kerzen(self, sym, minuten=60, limit=3, start_ms=None, ende_ms=None):
        c = sym.removesuffix("USDT")
        if start_ms is not None:
            return [] if c in self.ohne_alt else [{"start": start_ms, "open": 0, "high": 0, "low": 0, "close": self.alt[c]}]
        letzte = self.jetzt - self.jetzt % H - H - self.verzug * H
        return [{"start": letzte, "open": 0, "high": 0, "low": 0, "close": self.kurse[c]}] + \
               ([] if self.verzug else [{"start": letzte + H, "open": 0, "high": 0, "low": 0, "close": self.kurse[c]}])

    def kontrakt(self, sym):
        return {"status": "Trading", "min_menge": self.min, "schritt": self.schritt, "tick": 0.01, "funding_minuten": self.f_min}

    def ticker(self, sym):
        p = self.kurse[sym.removesuffix("USDT")]
        return {"geld": p - self.spanne / 2, "brief": p + self.spanne / 2, "letzter": p, "mark": p, "funding": self.funding, "umsatz24h": 1e6}

    def buch(self, sym, tiefe=25):
        p = self.kurse[sym.removesuffix("USDT")]; s = self.spanne / 2
        return {"geld": [(p - s, self.tiefe), (p - 3 * s, self.tiefe)], "brief": [(p + s, self.tiefe), (p + 3 * s, self.tiefe)]}


class LiveBoerse(Boerse):
    """Nachgestelltes Konto: fuellt jede Order sofort zum Limit-Preis (kein Netz)."""
    key = secret = "nachgestellt"

    def __init__(self, *a, fills_spaet=False, **k):
        super().__init__(*a, **k)
        self.pos, self.orders, self.fills_spaet = {}, [], fills_spaet

    def positionen(self, settle="USDT"):
        return [{"symbol": s, "size": abs(q), "positionIdx": 1 if q > 0 else 2} for s, q in self.pos.items() if q]

    def order(self, sym, seite, menge, preis, position_idx, reduce_only):
        q = float(menge) * (1 if seite == "Buy" else -1)
        self.pos[sym] = round(self.pos.get(sym, 0.0) + q, 9)
        self.orders.append({"sym": sym, "seite": seite, "menge": menge, "preis": preis, "idx": position_idx, "reduce": reduce_only})
        return {"order_id": str(len(self.orders)), "link_id": "x"}

    def fills(self, sym, order_id):
        if self.fills_spaet:
            return []
        o = self.orders[int(order_id) - 1]
        return [{"execQty": o["menge"], "execPrice": o["preis"], "execFee": str(0.0008 * float(o["menge"]) * float(o["preis"]))}]

    def storno(self, sym, order_id):
        raise YubitFehler("schon gefuellt")


def lauf(cfg, api, d, t, **k):
    api.jetzt = t - api.verzug_extra if hasattr(api, 'verzug_extra') else t
    return bot.schritt(cfg, api, d, t, **k)


def frisch(name):
    d = ARB / name
    shutil.rmtree(d, ignore_errors=True); d.mkdir(parents=True)
    return d

def zst(d):
    return json.loads((d / "zustand.json").read_text())

CFG = {"modus": "papier", "kapital_usd": 5000, "hebel": 3.0, "coins": ["AAA", "BBB"], "tagesverlust_limit": 1.0,
       "preisgrenze": 0.0005, "max_order_usd": 100000, "daten": "x"}
E = {}

# ---- D1: Gleichstand -> flach, danach Wiedereinstieg; loest ausserdem die Stop-Sperre ----
d = frisch("d1"); api = Boerse({"AAA": 100.0, "BBB": 50.0}, {"AAA": 90.0, "BBB": 60.0})
lauf(CFG, api, d, JETZT, melden=still)
api.alt["AAA"] = 100.0                                                    # Schluss == Schluss vor 336 h
r1 = lauf(CFG, api, d, JETZT + H, melden=still); p1 = zst(d)["pos"]["AAA"]
api.alt["AAA"] = 99.99
r2 = lauf(CFG, api, d, JETZT + 2 * H, melden=still); p2 = zst(d)["pos"]["AAA"]
pr = bot.lesen(d / "protokoll.csv")
E["D1_gleichstand"] = {"orders_bei_gleichstand": r1["orders"], "pos_nach_gleichstand": p1, "orders_stunde_danach": r2["orders"], "pos_danach": p2,
                       "gebuehr_fuer_rundlauf_usd": round(sum(float(x["gebuehr"]) for x in pr[2:]), 4),
                       "kern.richtung(100,100)": kern.richtung(100, 100)}
d = frisch("d1b"); api = Boerse({"AAA": 100.0, "BBB": 50.0}, {"AAA": 90.0, "BBB": 60.0}); cfg2 = {**CFG, "tp": 0.15, "sl": 0.05}
lauf(cfg2, api, d, JETZT, melden=still)
api.kurse["AAA"] = 94.0; api.alt["AAA"] = 80.0                            # -6 % -> Stop, Signal bleibt Long
lauf(cfg2, api, d, JETZT + H, melden=still); s1 = dict(zst(d)["sperre"]); q1 = zst(d)["pos"]["AAA"]
api.alt["AAA"] = 94.0                                                     # Gleichstand: Sperre faellt
lauf(cfg2, api, d, JETZT + 2 * H, melden=still); s2 = dict(zst(d)["sperre"])
api.alt["AAA"] = 93.99                                                    # wieder Long: Wiedereinstieg ohne echten Dreh
lauf(cfg2, api, d, JETZT + 3 * H, melden=still)
E["D1b_gleichstand_loest_sperre"] = {"sperre_nach_stop": s1, "pos_nach_stop": q1, "sperre_nach_gleichstand": s2, "pos_nach_wiedereinstieg": zst(d)["pos"]["AAA"]}

# ---- D2: Teilfuellung beim Einstieg bleibt bis zum Dreh bestehen ----
d = frisch("d2"); api = Boerse({"AAA": 100.0, "BBB": 50.0}, {"AAA": 90.0, "BBB": 60.0}, tiefe=3.0)   # Buch: 2 Stufen x 3 Stueck
r = lauf(CFG, api, d, JETZT, melden=still); a = zst(d)["pos"]["AAA"]
api.tiefe = 1e9
r2 = lauf(CFG, api, d, JETZT + H, melden=still)
E["D2_teilfuellung"] = {"soll_stueck": kern.menge_runden(7500, 100.0, 0.1, 0.1), "ist_nach_lauf1": a, "warnungen": r["warnungen"][:2],
                        "orders_naechster_lauf_bei_vollem_buch": r2["orders"], "pos_danach": zst(d)["pos"]["AAA"],
                        "spannen_kauf_bp_leer": bot.lesen(d / "spannen.csv")[0]["kauf_bp"] == ""}

# ---- D3/D4: Rundung ----
E["D4_menge_runden"] = {"schritt_0.25 (10 USD bei 13)": kern.menge_runden(10, 13, 0.25, 0.25), "erwartet": 0.75,
                        "schritt_0.025 (10 USD bei 130)": kern.menge_runden(10, 130, 0.025, 0.025), "erwartet2": 0.075,
                        "als_text(0.75, 0.25)": kern.als_text(0.75, 0.25), "schritt_0.001": kern.menge_runden(1500, 65720.15, 0.001, 0.001)}

# ---- D5: Funding: Vorzeichen, Satz NACH dem Termin, n x aktueller Satz ----
EIN = {**CFG, "coins": ["AAA"]}                                           # ein Coin, 15.000 USD Long
d = frisch("d5"); api = Boerse({"AAA": 100.0, "BBB": 50.0}, {"AAA": 90.0, "BBB": 60.0}, funding=0.0001)
t0 = (JETZT // (480 * 60_000)) * 480 * 60_000 + 470 * 60_000              # 10 Minuten vor einem 8-h-Termin
lauf(EIN, api, d, t0, melden=still); z0 = zst(d)
api.funding = -0.0003                                                     # nach dem Termin zeigt der Ticker den Satz der NAECHSTEN Periode
lauf(EIN, api, d, t0 + 15 * 60_000, melden=still); z1 = zst(d)
nominal = z0["pos"]["AAA"] * 100.0
lauf(EIN, api, d, t0 + 15 * 60_000 + 3 * 480 * 60_000, melden=still); z2 = zst(d)   # drei weitere Termine ohne Lauf dazwischen
E["D5_funding"] = {"pos_AAA_long_usd": nominal, "satz_vor_termin": 0.0001, "satz_im_ticker_nach_termin": -0.0003,
                   "gebucht": round(z1["funding"], 6),
                   "richtig_mit_abgerechnetem_satz": round(-nominal * 0.0001, 6),
                   "nach_3_verpassten_terminen_zusaetzlich_gebucht": round(z2["funding"] - z1["funding"], 6),
                   "funding_faellig(3 Termine)": kern.funding_faellig(t0 + 15 * 60_000, t0 + 15 * 60_000 + 3 * 480 * 60_000, 480)}
d = frisch("d5b"); api = Boerse({"AAA": 100.0, "BBB": 50.0}, {"AAA": 90.0, "BBB": 60.0}, funding=0.0001)
lauf(EIN, api, d, t0, melden=still); lauf(EIN, api, d, t0 + 15 * 60_000, melden=still)
E["D5_funding"]["vorzeichen_long_zahlt_bei_positivem_satz"] = round(zst(d)["funding"], 6)
d = frisch("d5c"); api = Boerse({"AAA": 100.0, "BBB": 50.0}, {"AAA": 110.0, "BBB": 60.0}, funding=0.0001)
lauf(EIN, api, d, t0, melden=still); lauf(EIN, api, d, t0 + 15 * 60_000, melden=still)
E["D5_funding"]["vorzeichen_short_erhaelt_bei_positivem_satz"] = round(zst(d)["funding"], 6)

# ---- D6: veraltete Kerze: bis 2 h nach Schluss stillschweigend akzeptiert, danach Abbruch ----
d = frisch("d6"); api = Boerse({"AAA": 100.0, "BBB": 50.0}, {"AAA": 90.0, "BBB": 60.0}); api.verzug = 1
r = lauf(CFG, api, d, JETZT, melden=still)
api2 = Boerse({"AAA": 100.0, "BBB": 50.0}, {"AAA": 90.0, "BBB": 60.0}); api2.verzug = 2
try:
    lauf(CFG, api2, frisch("d6b"), JETZT, melden=still); x = "kein Abbruch"
except SystemExit as e:
    x = "SystemExit: " + str(e)[:70]
E["D6_veraltete_kerze"] = {"kerze_1h05_nach_schluss": {"orders": r["orders"], "warnungen": r["warnungen"]}, "kerze_2h05_nach_schluss": x}

# ---- D7: Referenzkerze fehlt -> Coin wird uebersprungen, Position bleibt (Backtest: Signal 0 = flach) ----
d = frisch("d7"); api = Boerse({"AAA": 100.0, "BBB": 50.0}, {"AAA": 90.0, "BBB": 60.0})
lauf(CFG, api, d, JETZT, melden=still); api.ohne_alt.add("AAA"); api.kurse["AAA"] = 70.0
r = lauf(CFG, api, d, JETZT + H, melden=still)
E["D7_fehlende_referenz"] = {"warnungen": r["warnungen"], "pos_AAA_bleibt": zst(d)["pos"]["AAA"], "kurs_im_zustand_veraltet": zst(d)["kurs"]["AAA"],
                             "brutto_laut_bot": round(r["vermoegen"]["brutto"], 2), "brutto_bei_echtem_kurs_70": round(kern.vermoegen(zst(d), {"AAA": 70.0, "BBB": 50.0})["brutto"], 2)}

# ---- D10: Tageslimit 1.0 = praktisch aus; kein Margin-/Liquidationsmodell ----
TAG = 24 * H
d = frisch("d10"); api = Boerse({"AAA": 100.0, "BBB": 100.0}, {"AAA": 110.0, "BBB": 110.0})      # beide Short, je 7.500 USD (Hebel 3)
lauf(CFG, api, d, JETZT, melden=still)
api.kurse.update(AAA=130.0, BBB=130.0); api.alt.update(AAA=150.0, BBB=150.0)                      # +30 % gegen die Shorts am selben Tag
r = lauf(CFG, api, d, JETZT + H, melden=still)
a1 = {"netto_ohne_rebate": round(r["vermoegen"]["netto_ohne_rebate"], 2), "konto_rest": round(5000 + r["vermoegen"]["netto_ohne_rebate"], 2),
      "orders": r["orders"], "pos": dict(zst(d)["pos"]), "gesperrt_tag": zst(d)["gesperrt_tag"]}
api.kurse.update(AAA=131.0, BBB=131.0)
lauf(CFG, api, d, JETZT + TAG, melden=still)                                                       # neuer Tag: Tagesstart wird neu gesetzt
api.kurse.update(AAA=150.0, BBB=150.0); api.alt.update(AAA=170.0, BBB=170.0)
r = lauf(CFG, api, d, JETZT + TAG + H, melden=still)
a2 = {"netto_ohne_rebate": round(r["vermoegen"]["netto_ohne_rebate"], 2), "konto_rest": round(5000 + r["vermoegen"]["netto_ohne_rebate"], 2),
      "orders": r["orders"], "pos": dict(zst(d)["pos"]), "gesperrt_tag": zst(d)["gesperrt_tag"]}
E["D10_kein_limit_keine_liquidation"] = {"tag1_plus30pct": a1, "tag2_weiter_auf_plus50pct": a2}
d = frisch("d10b"); api = Boerse({"AAA": 100.0, "BBB": 100.0}, {"AAA": 110.0, "BBB": 110.0})
cfg3 = {**CFG, "tagesverlust_limit": 0.03}
lauf(cfg3, api, d, JETZT, melden=still)
api.kurse.update(AAA=101.5, BBB=101.5)                                                            # -1,5 % x Hebel 3 = -4,5 % vom Kapital
r = lauf(cfg3, api, d, JETZT + H, melden=still)
E["D10b_limit_3pct_bei_hebel3"] = {"netto_ohne_rebate": round(r["vermoegen"]["netto_ohne_rebate"], 2), "pos": zst(d)["pos"], "gesperrt_tag": zst(d)["gesperrt_tag"],
                                   "gruende": [x["grund"] for x in bot.lesen(d / "protokoll.csv")]}

# ---- D9: STOPP-Datei ----
d = frisch("d9"); api = Boerse({"AAA": 100.0, "BBB": 50.0}, {"AAA": 90.0, "BBB": 60.0})
lauf(CFG, api, d, JETZT, melden=still); vor = (d / "zustand.json").read_text(); (d / "STOPP").write_text("")
api.kurse["AAA"] = 50.0; api.alt["AAA"] = 90.0                                                    # Signal dreht, Verlust laeuft
r = lauf(CFG, api, d, JETZT + H, melden=still)
E["D9_stopp"] = {"rueckgabe": r, "zustand_unveraendert": vor == (d / "zustand.json").read_text(), "pos_bleibt_offen": zst(d)["pos"], "stand_zeilen": len(bot.lesen(d / "stand.csv"))}

# ---- D11: Kontoidentitaeten nach mehreren Laeufen (Dreh, Funding) ----
d = frisch("d11"); api = Boerse({"AAA": 100.0, "BBB": 50.0}, {"AAA": 90.0, "BBB": 60.0}, spanne=0.2)
kurse = [(100, 50), (104, 49), (97, 52), (88, 58), (92, 63), (101, 61)]; alt = [(90, 60), (90, 60), (99, 51), (99, 51), (90, 60), (90, 60)]
for i, ((a, b), (aa, bb)) in enumerate(zip(kurse, alt)):
    api.kurse.update(AAA=float(a), BBB=float(b)); api.alt.update(AAA=float(aa), BBB=float(bb)); lauf(CFG, api, d, JETZT + i * 4 * H, melden=still)
z = zst(d); pr = bot.lesen(d / "protokoll.csv"); st = bot.lesen(d / "stand.csv")
# unabhaengig aus dem Orderprotokoll: realisiert + offen je Coin
netto_protokoll = 0.0
for coin in CFG["coins"]:
    kasse = sum((-1 if x["seite"] == "kauf" else 1) * float(x["menge"]) * float(x["fuellkurs"]) for x in pr if x["coin"] == coin)
    menge = sum((1 if x["seite"] == "kauf" else -1) * float(x["menge"]) for x in pr if x["coin"] == coin)
    netto_protokoll += kasse + menge * z["kurs"][coin]
geb = sum(float(x["gebuehr"]) for x in pr); reb = sum(float(x["rebate"]) for x in pr)
v = kern.vermoegen(z, z["kurs"]); dash = dashboard_daten.bauen(CFG, d); k = dash["kennzahlen"][0]
browser_brutto = sum(p["kasse"] + p["menge"] * p["kurs"] for p in dash["positionen"])
browser_mit = browser_brutto - k["gebuehr_usd"] + k["funding_usd"] + k["rebate_usd"]
E["D11_identitaeten"] = {"orders": len(pr), "brutto_kern": round(v["brutto"], 6), "brutto_aus_protokoll": round(netto_protokoll, 6),
                         "gebuehr_kern": round(v["gebuehr"], 6), "gebuehr_protokoll": round(geb, 6), "rebate/gebuehr": round(reb / geb, 6),
                         "gebuehr/volumen": round(geb / sum(float(x["volumen"]) for x in pr), 8),
                         "netto_mit_kern": round(v["netto_mit_rebate"], 4), "stand_csv_letzte": float(st[-1]["netto_mit_rebate"]),
                         "dashboard_mit_rebate_usd": k["mit_rebate_usd"], "browser_formel_mit": round(browser_mit, 4),
                         "funding": round(v["funding"], 6), "einbruch_pct_dashboard": k["einbruch_pct"],
                         "einbruch_nachgerechnet": None}
sp, dd = 0.0, 0.0
for row in st:
    x = float(row["netto_mit_rebate"]) / CFG["kapital_usd"] * 100; sp = max(sp, x); dd = max(dd, (sp - x) / (100 + sp) * 100)
E["D11_identitaeten"]["einbruch_nachgerechnet"] = round(dd, 3)

# ---- D12: Dreh = zwei Orders, laufen kumulativ durchs selbe Buch ----
d = frisch("d12"); api = Boerse({"AAA": 100.0, "BBB": 50.0}, {"AAA": 90.0, "BBB": 60.0}, tiefe=100.0, spanne=0.2)   # 100 Stueck je Stufe
lauf({**CFG, "coins": ["AAA"]}, api, d, JETZT, melden=still)       # Long 75 Stueck (7.500 USD bei Hebel 3 / 2 Coins -> hier 1 Coin: 15.000)
q0 = zst(d)["pos"]["AAA"]
api.alt["AAA"] = 110.0
lauf({**CFG, "coins": ["AAA"]}, api, d, JETZT + H, melden=still)
pr = bot.lesen(d / "protokoll.csv")[-2:]
ges_kurs, ges_q = kern.buch_fill(False, float(pr[0]["menge"]) + float(pr[1]["menge"]), api.buch("AAAUSDT"))
E["D12_dreh_zwei_orders"] = {"pos_vor": q0, "orders": [(x["seite"], x["grund"], float(x["menge"]), float(x["fuellkurs"])) for x in pr],
                             "volumen_summe": round(sum(float(x["volumen"]) for x in pr), 4), "eine_order_gleiches_buch_volumen": round(ges_kurs * ges_q, 4)}

# ---- D13: Test 2: Stop bei einem Lauf INNERHALB der Stunde; am Stundenschluss waere er nicht ausgeloest ----
import numpy as np
sys.path.insert(0, "/home/user/OdinGate-Botv134/swing-hybrid/src")
from hybrid import tpsl
d = frisch("d13"); api = Boerse({"AAA": 100.0, "BBB": 50.0}, {"AAA": 90.0, "BBB": 40.0}); cfg2 = {**CFG, "tp": 0.15, "sl": 0.05}
lauf(cfg2, api, d, JETZT, melden=still)                                   # Long, Einstieg 100,05
api_k = api.kerzen                                                        # Stundenkerze bleibt bei 100 (letzte volle Stunde)
api.kerzen = lambda sym, minuten=60, limit=3, start_ms=None, ende_ms=None: [dict(k, close=(100.0 if sym.startswith("AAA") and start_ms is None else k["close"])) for k in api_k(sym, minuten, limit, start_ms, ende_ms)]
api.kurse["AAA"] = 94.5                                                   # Mittelkurs 20 Minuten spaeter: -5,5 %
r = lauf(cfg2, api, d, JETZT + 20 * 60_000, melden=still)
bot_grund = [x["grund"] for x in bot.lesen(d / "protokoll.csv") if x["coin"] == "AAA"]
ruck = tpsl._zustand(np.array([100.0, 99.0, 99.5]), np.array([1.0, 1.0, 1.0]), 0.15, 0.05, 0.0)   # Stundenschluesse 100, 99, 99,5
E["D13_stop_innerhalb_der_stunde"] = {"bot_orders_AAA": bot_grund, "bot_pos_AAA": zst(d)["pos"]["AAA"], "bot_sperre": zst(d)["sperre"],
                                      "rueckrechnung_tpsl_position_bei_schluessen_100_99_99.5": ruck.tolist()}

# ---- D14: zweiter Lauf in derselben Minute: keine Order, aber doppelte Zeilen ----
d = frisch("d14"); api = Boerse({"AAA": 100.0, "BBB": 50.0}, {"AAA": 90.0, "BBB": 60.0})
lauf(CFG, api, d, JETZT, melden=still); r = lauf(CFG, api, d, JETZT + 1000, melden=still)
E["D14_doppellauf"] = {"orders_zweiter_lauf": r["orders"], "stand_zeilen": len(bot.lesen(d / "stand.csv")), "gleiche_zeit": len({x["zeit"] for x in bot.lesen(d / "stand.csv")}) == 1}

# ---- D8: Live-Schranken mit nachgestelltem Konto ----
os.environ.pop("YUBIT_LIVE", None)
d = frisch("d8a"); api = LiveBoerse({"AAA": 100.0, "BBB": 50.0}, {"AAA": 110.0, "BBB": 60.0})
LIVE = {**CFG, "modus": "live", "hebel": 0.04, "max_order_usd": 150}      # 100 USD je Coin, Deckel 150 USD (wie config.json)
try:
    lauf(LIVE, api, d, JETZT, melden=still); a = "kein Abbruch"
except SystemExit as e:
    a = "SystemExit: " + str(e)[:60]
E["D8_live"] = {"ohne_YUBIT_LIVE": a, "orders_an_boerse": len(api.orders)}
os.environ["YUBIT_LIVE"] = "ja"
r = lauf({**CFG, "hebel": 0.04}, api, d, JETZT, melden=still)      # modus papier + Umgebungsvariable + Schluessel: bleibt Papier
E["D8_live"]["papier_trotz_env_und_schluessel"] = {"modus": r["modus"], "orders_an_boerse": len(api.orders)}
d = frisch("d8b"); api = LiveBoerse({"AAA": 100.0, "BBB": 50.0}, {"AAA": 110.0, "BBB": 60.0})     # beide Short, je 100 USD
r = lauf(LIVE, api, d, JETZT, melden=still)
E["D8_live"]["einstieg"] = {"modus": r["modus"], "orders": [(o["sym"], o["seite"], o["menge"], o["preis"], o["reduce"]) for o in api.orders], "pos_boerse": dict(api.pos)}
# Kurs steigt 60 % gegen den Short, Signal dreht auf Long: Schliessen noetig, aber Deckel 150 USD < 1,0 x 160
api.kurse["AAA"] = 160.0; api.alt["AAA"] = 110.0; n = len(api.orders)
r = lauf(LIVE, api, d, JETZT + H, melden=still)
E["D8_live"]["deckel_blockiert_schliessen"] = {"warnungen": r["warnungen"], "neue_orders_AAA": [o for o in api.orders[n:] if o["sym"] == "AAAUSDT"],
                                               "pos_boerse_AAA": api.pos["AAAUSDT"], "verlust_usd": round(r["vermoegen"]["brutto"], 2)}
api.kurse["AAA"] = 200.0; n = len(api.orders)
r = lauf({**LIVE, "tagesverlust_limit": 0.001}, api, d, JETZT + 2 * H, melden=still)       # selbst das Tageslimit kann nicht schliessen
E["D8_live"]["deckel_blockiert_auch_tageslimit"] = {"warnungen": r["warnungen"], "pos_boerse_AAA": api.pos["AAAUSDT"], "gesperrt_tag": zst(d)["gesperrt_tag"],
                                                    "neue_orders": [(o["sym"], o["seite"], o["reduce"]) for o in api.orders[n:]]}
# Fills kommen spaeter als 1,5 s: Bot bucht nichts, Boerse hat Position -> naechster Lauf bricht ab, Position unverwaltet
d = frisch("d8c"); api = LiveBoerse({"AAA": 100.0, "BBB": 50.0}, {"AAA": 110.0, "BBB": 60.0}, fills_spaet=True)
r = lauf(LIVE, api, d, JETZT, melden=still)
try:
    lauf(LIVE, api, d, JETZT + H, melden=still); b = "kein Abbruch"
except SystemExit as e:
    b = "SystemExit: " + str(e)[:110]
E["D8_live"]["fills_spaet"] = {"warnungen_lauf1": r["warnungen"], "pos_boerse": dict(api.pos), "pos_protokoll": zst(d)["pos"], "lauf2": b}
os.environ.pop("YUBIT_LIVE", None)

print(json.dumps(E, indent=1, default=str, ensure_ascii=False))
