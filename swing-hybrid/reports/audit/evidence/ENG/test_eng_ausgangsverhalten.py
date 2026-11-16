"""Audit ENG: Regressionstests, die das AUSGANGSVERHALTEN der Rechenkerne und des Papier-Bots festhalten (Stand 0e92022).

Tests mit `ist_` im Namen dokumentieren ein im Audit beanstandetes Verhalten (Befund-ID im Docstring). Sie laufen auf dem
heutigen Code gruen; wer den Befund behebt, muss den Test bewusst umdrehen. Kein Netz, keine echten Schluessel, nur tmp_path.

Aufruf (aus swing-hybrid/):
    .venv/bin/python -I -B -m pytest -q -p no:cacheprovider reports/audit/evidence/ENG/test_eng_ausgangsverhalten.py
"""
import json
import sys
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pandas as pd
import pytest

WURZEL = next((p for p in Path(__file__).resolve().parents if (p / "vorwaertstest" / "bot.py").exists()),
              Path("/home/user/OdinGate-Botv134/swing-hybrid"))
sys.path.insert(0, str(WURZEL))
sys.path.insert(0, str(WURZEL / "src"))
from hybrid import engine2, research as R, tpsl          # noqa: E402
from vorwaertstest import bot, dashboard_daten, kern     # noqa: E402
from vorwaertstest.yubit import YubitFehler              # noqa: E402

H = kern.STUNDE_MS
JETZT = 1_800_000_000_000 - (1_800_000_000_000 % H) + 5 * 60_000
still = lambda *_: None
CFG = {"modus": "papier", "kapital_usd": 5000, "hebel": 3.0, "coins": ["AAA", "BBB"], "tagesverlust_limit": 1.0,
       "preisgrenze": 0.0005, "max_order_usd": 100000, "daten": "x"}


class Boerse:
    """Nachgestellte Boerse (wie tests/test_vorwaertstest_bot.py, mit einstellbarer Uhr, Tiefe und Funding)."""
    key = secret = ""

    def __init__(self, kurse, alt, schritt=0.1, tiefe=1e9, spanne=0.1, funding=0.0001):
        self.kurse, self.alt, self.schritt, self.tiefe, self.spanne, self.funding = dict(kurse), dict(alt), schritt, tiefe, spanne, funding
        self.jetzt, self.aufrufe, self.ohne_alt = JETZT, 0, set()

    def kerzen(self, sym, minuten=60, limit=3, start_ms=None, ende_ms=None):
        c = sym.removesuffix("USDT")
        if start_ms is not None:
            return [] if c in self.ohne_alt else [{"start": start_ms, "open": 0, "high": 0, "low": 0, "close": self.alt[c]}]
        letzte = self.jetzt - self.jetzt % H - H
        return [{"start": letzte + i * H, "open": 0, "high": 0, "low": 0, "close": self.kurse[c]} for i in (0, 1)]

    def kontrakt(self, sym):
        return {"status": "Trading", "min_menge": self.schritt, "schritt": self.schritt, "tick": 0.01, "funding_minuten": 480}

    def ticker(self, sym):
        p = self.kurse[sym.removesuffix("USDT")]
        return {"geld": p - self.spanne / 2, "brief": p + self.spanne / 2, "letzter": p, "mark": p, "funding": self.funding, "umsatz24h": 1e6}

    def buch(self, sym, tiefe=25):
        p, s = self.kurse[sym.removesuffix("USDT")], self.spanne / 2
        return {"geld": [(p - s, self.tiefe), (p - 3 * s, self.tiefe)], "brief": [(p + s, self.tiefe), (p + 3 * s, self.tiefe)]}


class LiveBoerse(Boerse):
    key = secret = "nachgestellt"

    def __init__(self, *a, **k):
        super().__init__(*a, **k)
        self.pos, self.orders = {}, []

    def positionen(self, settle="USDT"):
        return [{"symbol": s, "size": abs(q), "positionIdx": 1 if q > 0 else 2} for s, q in self.pos.items() if q]

    def order(self, sym, seite, menge, preis, position_idx, reduce_only):
        self.pos[sym] = round(self.pos.get(sym, 0.0) + float(menge) * (1 if seite == "Buy" else -1), 9)
        self.orders.append({"sym": sym, "seite": seite, "menge": menge, "preis": preis, "reduce": reduce_only})
        return {"order_id": str(len(self.orders)), "link_id": "x"}

    def fills(self, sym, order_id):
        o = self.orders[int(order_id) - 1]
        return [{"execQty": o["menge"], "execPrice": o["preis"], "execFee": "0"}]

    def storno(self, sym, order_id):
        raise YubitFehler("schon gefuellt")


def lauf(cfg, api, d, t):
    api.jetzt = t
    return bot.schritt(cfg, api, d, t, melden=still)


def zustand(d):
    return json.loads((d / "zustand.json").read_text())


# ------------------------------------------------------------------ Signal ----
def test_signal_bot_und_rueckrechnung_sind_dieselbe_regel():
    rng = np.random.default_rng(1)
    c = pd.Series(np.round(100 * np.exp(np.cumsum(rng.normal(0, 0.01, 1200))), 1))    # grobe Ticks -> es gibt Gleichstaende
    c.iloc[700] = c.iloc[700 - 336]                                                  # ein sicherer Gleichstand
    rueck = np.sign(c / c.shift(336) - 1).fillna(0.0).to_numpy()                     # research._trend / mutationen.basis
    botsig = [0 if i < 336 else kern.richtung(c.iloc[i], c.iloc[i - 336]) for i in range(len(c))]
    assert list(rueck) == botsig and rueck[700] == 0 and kern.RUECKBLICK_STUNDEN == 336


def test_stundensignal_gilt_erst_ab_stundenschluss():
    idx = pd.date_range("2024-01-01", periods=36, freq="5min")
    m = SimpleNamespace(index=idx, coins=["AAA"])
    sig = pd.DataFrame({"AAA": [1.0, -1.0, 1.0]}, index=pd.date_range("2024-01-01", periods=3, freq="1h"))   # Index = Stundenbeginn
    w = R.auf_raster(m, sig)[0]
    assert list(w[:12]) == [0.0] * 12            # in der ersten Stunde ist noch nichts bekannt
    assert list(w[12:24]) == [1.0] * 12          # Signal der Stunde 00:00 gilt ab 01:00
    assert list(w[24:36]) == [-1.0] * 12


# ------------------------------------------------------------------ engine2 ----
def test_engine2_taker_stueckzahl_dreh_gebuehr_funding():
    o = np.array([[100.0, 100.0, 110.0, 120.0, 115.0]]); c = o.copy(); h = o * 1.001; l = o * 0.999
    w = np.array([[0.0, 1.0, 1.0, -1.0, -1.0]]); fund = np.array([[0.0, 0.0, 0.0001, 0.0, 0.0]])
    S, slip = 1.0, 0.001
    eq, MV, TV, FU, daily, tr, st, nt, ORD, FIL = engine2.simulate_target(
        o, h, l, c, w, np.ones_like(o), fund, np.zeros(5, np.int64), S, 3, 1e-4, np.array([slip]), 0.0, 0, 0.0, 0.0004, 0.0008, 9.0, 100, True)
    q1 = S / 100.0; p1 = 100.0 * (1 + slip)                   # Einstieg Long zum Open + Slippage
    q2 = S / 120.0; p2 = 120.0 * (1 - slip)                   # Dreh: EINE Order ueber q1 + q2, Verkauf zum Open - Slippage
    p3 = 115.0 * (1 + slip)                                   # Schlussabrechnung: Short zurueckkaufen
    brutto = q1 * (p2 - p1) + q2 * (p2 - p3)
    umsatz = q1 * p1 + (q1 + q2) * p2 + q2 * p3
    assert eq[-1] == pytest.approx(brutto) and TV[-1] == pytest.approx(umsatz) and MV[-1] == 0.0
    assert FU[-1] == pytest.approx(-q1 * 110.0 * 0.0001)      # Long zahlt bei positivem Satz, Basis = Open des Funding-Bars
    assert nt == 2 and st[1] == 3                             # zwei abgeschlossene Trades, drei Fills
    netto_mit = eq[-1] - 0.0008 * (1 - 0.85) * TV[-1] + FU[-1]
    assert netto_mit == pytest.approx(brutto - 0.00012 * umsatz - q1 * 110.0 * 0.0001)


def test_engine2_ist_linear_im_hebel_und_kennt_keine_liquidation():
    """ENG-02: Der Rechenkern rechnet mit negativem Konto weiter (kein Margin-/Liquidationsmodell)."""
    o = np.array([[100.0, 100.0, 150.0, 200.0, 200.0]]); w = np.array([[0.0, -1.0, -1.0, -1.0, -1.0]])
    arg = (o, o, o, o, w, np.ones_like(o), np.zeros_like(o), np.zeros(5, np.int64))
    rest = (3, 1e-4, np.array([0.0]), 0.0, 0, 0.0, 0.0004, 0.0008, 9.0, 100, True)
    e1 = engine2.simulate_target(*arg, 1.0, *rest)[0]; e3 = engine2.simulate_target(*arg, 3.0, *rest)[0]
    assert e3 == pytest.approx(3 * e1) and e3[3] == pytest.approx(-3.0)      # Short bei +100 %: -300 % des Startkapitals, Lauf geht weiter


# ------------------------------------------------------------------ Papier-Bot ----
def test_bot_groesse_gebuehr_rebate_und_kontoidentitaeten(tmp_path):
    api = Boerse({"AAA": 100.0, "BBB": 50.0}, {"AAA": 90.0, "BBB": 60.0}, spanne=0.2)
    kurse = [(100, 50), (104, 49), (97, 52), (88, 58), (92, 63)]; alt = [(90, 60), (90, 60), (99, 51), (99, 51), (90, 60)]
    for i, ((a, b), (aa, bb)) in enumerate(zip(kurse, alt)):
        api.kurse.update(AAA=float(a), BBB=float(b)); api.alt.update(AAA=float(aa), BBB=float(bb))
        lauf(CFG, api, tmp_path, JETZT + i * H)
    z, pr, st = zustand(tmp_path), bot.lesen(tmp_path / "protokoll.csv"), bot.lesen(tmp_path / "stand.csv")
    assert float(pr[0]["menge"]) == pytest.approx(75.0)          # nominal = 5000 x 3 / 2 = 7500 USD je Coin; Stueckzahl aus dem MITTELkurs 100,00
    assert float(pr[0]["volumen"]) == pytest.approx(75.0 * 100.1)   # gefuellt zum Briefkurs 100,10
    for x in pr:
        assert float(x["gebuehr"]) == pytest.approx(0.0008 * float(x["volumen"]), abs=1e-6)
        assert float(x["rebate"]) == pytest.approx(0.85 * float(x["gebuehr"]), abs=1e-6)
    brutto = 0.0
    for coin in CFG["coins"]:
        vz = lambda x: 1 if x["seite"] == "kauf" else -1
        kasse = sum(-vz(x) * float(x["menge"]) * float(x["fuellkurs"]) for x in pr if x["coin"] == coin)
        menge = sum(vz(x) * float(x["menge"]) for x in pr if x["coin"] == coin)
        assert menge == pytest.approx(z["pos"][coin])
        brutto += kasse + menge * z["kurs"][coin]
    v = kern.vermoegen(z, z["kurs"])
    assert v["brutto"] == pytest.approx(brutto) and v["netto_ohne_rebate"] == pytest.approx(brutto - z["gebuehr"] + z["funding"])
    assert v["netto_mit_rebate"] == pytest.approx(v["netto_ohne_rebate"] + 0.85 * z["gebuehr"])
    assert float(st[-1]["netto_mit_rebate"]) == pytest.approx(v["netto_mit_rebate"], abs=1e-4)
    d = dashboard_daten.bauen(CFG, tmp_path); k = d["kennzahlen"][0]
    browser = sum(p["kasse"] + p["menge"] * p["kurs"] for p in d["positionen"]) - k["gebuehr_usd"] + k["funding_usd"] + k["rebate_usd"]   # docs/index.html konto()
    assert k["mit_rebate_usd"] == pytest.approx(v["netto_mit_rebate"], abs=0.006) and browser == pytest.approx(v["netto_mit_rebate"], abs=0.02)
    sp, dd = 0.0, 0.0
    for r in st:
        x = float(r["netto_mit_rebate"]) / 50; sp = max(sp, x); dd = max(dd, (sp - x) / (100 + sp) * 100)
    assert k["einbruch_pct"] == pytest.approx(dd, abs=2e-3)
    assert k["margin_usd"] == pytest.approx(float(st[-1]["einsatz"]) / 3.0, abs=0.51)


def test_bot_dreh_sind_zwei_orders_durch_dasselbe_buch(tmp_path):
    cfg = {**CFG, "coins": ["AAA"]}
    api = Boerse({"AAA": 100.0}, {"AAA": 90.0}, tiefe=100.0, spanne=0.2)
    lauf(cfg, api, tmp_path, JETZT)
    api.alt["AAA"] = 110.0
    lauf(cfg, api, tmp_path, JETZT + H)
    a, b = bot.lesen(tmp_path / "protokoll.csv")[-2:]
    assert (a["grund"], b["grund"]) == ("schliessen", "einstieg") and a["seite"] == b["seite"] == "verkauf"
    kurs, q = kern.buch_fill(False, float(a["menge"]) + float(b["menge"]), api.buch("AAAUSDT"))
    assert float(a["volumen"]) + float(b["volumen"]) == pytest.approx(kurs * q)       # zusammen wie eine Order


def test_bot_gleichstand_bedeutet_flach_und_loest_die_stop_sperre(tmp_path):
    cfg = {**CFG, "tp": 0.15, "sl": 0.05}
    api = Boerse({"AAA": 100.0, "BBB": 50.0}, {"AAA": 90.0, "BBB": 60.0})
    lauf(cfg, api, tmp_path, JETZT)
    api.kurse["AAA"] = 94.0; api.alt["AAA"] = 80.0
    lauf(cfg, api, tmp_path, JETZT + H)
    assert zustand(tmp_path)["sperre"]["AAA"] == 1 and zustand(tmp_path)["pos"]["AAA"] == 0.0
    api.alt["AAA"] = 94.0                                        # Gleichstand
    lauf(cfg, api, tmp_path, JETZT + 2 * H)
    assert zustand(tmp_path)["sperre"]["AAA"] == 0
    api.alt["AAA"] = 93.99                                       # wieder Long, ohne dass das Signal je Short war
    lauf(cfg, api, tmp_path, JETZT + 3 * H)
    assert zustand(tmp_path)["pos"]["AAA"] > 0
    assert list(tpsl._zustand(np.array([100.0, 94.0, 94.0, 94.0]), np.array([1.0, 1.0, 0.0, 1.0]), 0.15, 0.05, 0.0)) == [1.0, 0.0, 0.0, 1.0]   # Rueckrechnung genauso


def test_bot_funding_vorzeichen(tmp_path):
    t0 = (JETZT // (480 * 60_000)) * 480 * 60_000 + 470 * 60_000
    for name, alt, erwartet in (("long", 90.0, -1.5), ("short", 110.0, 1.5)):
        d = tmp_path / name
        api = Boerse({"AAA": 100.0}, {"AAA": alt}, funding=0.0001)
        lauf({**CFG, "coins": ["AAA"]}, api, d, t0); lauf({**CFG, "coins": ["AAA"]}, api, d, t0 + 15 * 60_000)
        assert zustand(d)["funding"] == pytest.approx(erwartet)   # 15.000 USD x 0,01 %: Long zahlt, Short erhaelt
    assert kern.funding_faellig(t0, t0 + 5 * 60_000, 480) == 0 and kern.funding_faellig(t0, t0 + 15 * 60_000, 480) == 1


def test_ist_funding_nimmt_den_satz_nach_dem_termin_mal_anzahl_termine(tmp_path):
    """ENG-06: gebucht wird der Ticker-Satz zum Zeitpunkt des Laufs NACH dem Termin (Satz der naechsten Periode), mal Anzahl Termine."""
    t0 = (JETZT // (480 * 60_000)) * 480 * 60_000 + 470 * 60_000
    cfg = {**CFG, "coins": ["AAA"]}
    api = Boerse({"AAA": 100.0}, {"AAA": 90.0}, funding=0.0001)
    lauf(cfg, api, tmp_path, t0)
    api.funding = -0.0003
    lauf(cfg, api, tmp_path, t0 + 15 * 60_000)
    assert zustand(tmp_path)["funding"] == pytest.approx(+4.5)    # richtig waere -1,5 (abgerechneter Satz +0,01 %)
    lauf(cfg, api, tmp_path, t0 + 15 * 60_000 + 3 * 480 * 60_000)
    assert zustand(tmp_path)["funding"] == pytest.approx(4.5 + 3 * 4.5)


def test_ist_stop_wird_bei_jedem_lauf_geprueft_rueckrechnung_nur_am_stundenschluss(tmp_path):
    """ENG-03: Bot loest den Stop 20 Minuten nach der vollen Stunde aus; hybrid.tpsl bleibt bei denselben Stundenschluessen investiert."""
    cfg = {**CFG, "tp": 0.15, "sl": 0.05}
    api = Boerse({"AAA": 100.0, "BBB": 50.0}, {"AAA": 90.0, "BBB": 40.0})
    lauf(cfg, api, tmp_path, JETZT)
    roh = api.kerzen
    api.kerzen = lambda sym, *a, **k: [dict(x, close=100.0) if sym.startswith("AAA") and not (a[2:] or k.get("start_ms")) else x for x in roh(sym, *a, **k)]
    api.kurse["AAA"] = 94.5                                      # nur der Mittelkurs faellt, die Stundenkerze steht bei 100
    lauf(cfg, api, tmp_path, JETZT + 20 * 60_000)
    assert bot.lesen(tmp_path / "protokoll.csv")[-1]["grund"] == "stop" and zustand(tmp_path)["pos"]["AAA"] == 0.0
    assert list(tpsl._zustand(np.array([100.0, 99.0, 99.5]), np.array([1.0, 1.0, 1.0]), 0.15, 0.05, 0.0)) == [1.0, 1.0, 1.0]


def test_ist_teilfuellung_beim_einstieg_wird_nicht_nachgefuehrt(tmp_path):
    """ENG-08: Reicht die Buchtiefe nicht, bleibt die Position bis zum naechsten Dreh zu klein."""
    api = Boerse({"AAA": 100.0, "BBB": 50.0}, {"AAA": 90.0, "BBB": 60.0}, tiefe=3.0)
    lauf(CFG, api, tmp_path, JETZT)
    assert zustand(tmp_path)["pos"]["AAA"] == pytest.approx(6.0)
    api.tiefe = 1e9
    assert lauf(CFG, api, tmp_path, JETZT + H)["orders"] == 0 and zustand(tmp_path)["pos"]["AAA"] == pytest.approx(6.0)


def test_ist_runden_bei_schrittweite_ohne_zehnerpotenz():
    """ENG-08: 0,75 Stueck bei Schrittweite 0,25 werden zu 0,8 (kein Vielfaches, ueber dem Zielbetrag)."""
    assert kern.menge_runden(1500, 65720.15, 0.001, 0.001) == pytest.approx(0.022)     # richtig bei Zehnerpotenzen
    assert kern.menge_runden(10, 13, 0.25, 0.25) == pytest.approx(0.8) and kern.als_text(0.75, 0.25) == "0.8"


def test_ist_fehlende_referenzkerze_position_bleibt_und_wird_alt_bewertet(tmp_path):
    """ENG-07: Der Coin wird uebersprungen; stand.csv rechnet mit dem letzten bekannten Kurs weiter (Rueckrechnung: Signal 0 = flach)."""
    api = Boerse({"AAA": 100.0, "BBB": 50.0}, {"AAA": 90.0, "BBB": 60.0})
    lauf(CFG, api, tmp_path, JETZT)
    api.ohne_alt.add("AAA"); api.kurse["AAA"] = 70.0
    r = lauf(CFG, api, tmp_path, JETZT + H)
    assert any("keine Kerze von vor 14 Tagen" in w for w in r["warnungen"]) and zustand(tmp_path)["pos"]["AAA"] > 0
    assert zustand(tmp_path)["kurs"]["AAA"] == pytest.approx(100.0) and r["vermoegen"]["brutto"] > -50


def test_ist_tageslimit_1_0_haelt_positionen_bei_negativem_konto(tmp_path):
    """ENG-02 / ENG-04: Mit tagesverlust_limit 1.0 (beide laufenden Tests) und Hebel 3 gibt es keine Verlustgrenze und keine Liquidation."""
    api = Boerse({"AAA": 100.0, "BBB": 100.0}, {"AAA": 110.0, "BBB": 110.0})
    lauf(CFG, api, tmp_path, JETZT)
    api.kurse.update(AAA=130.0, BBB=130.0); api.alt.update(AAA=150.0, BBB=150.0)
    lauf(CFG, api, tmp_path, JETZT + H)
    api.kurse.update(AAA=131.0, BBB=131.0)
    lauf(CFG, api, tmp_path, JETZT + 24 * H)
    api.kurse.update(AAA=150.0, BBB=150.0); api.alt.update(AAA=170.0, BBB=170.0)
    r = lauf(CFG, api, tmp_path, JETZT + 25 * H)
    z = zustand(tmp_path)
    assert CFG["kapital_usd"] + r["vermoegen"]["netto_ohne_rebate"] < 0 and z["pos"]["AAA"] < 0 and z["gesperrt_tag"] == ""


def test_tageslimit_3_prozent_schliesst_bei_hebel_3_nach_anderthalb_prozent_kursbewegung(tmp_path):
    cfg = {**CFG, "tagesverlust_limit": 0.03}
    api = Boerse({"AAA": 100.0, "BBB": 100.0}, {"AAA": 110.0, "BBB": 110.0})
    lauf(cfg, api, tmp_path, JETZT)
    api.kurse.update(AAA=101.5, BBB=101.5)
    lauf(cfg, api, tmp_path, JETZT + H)
    z = zustand(tmp_path)
    assert z["pos"]["AAA"] == 0.0 and z["gesperrt_tag"] and bot.lesen(tmp_path / "protokoll.csv")[-1]["grund"] == "tageslimit"


def test_stopp_datei_haelt_an_ohne_positionen_zu_schliessen(tmp_path):
    api = Boerse({"AAA": 100.0, "BBB": 50.0}, {"AAA": 90.0, "BBB": 60.0})
    lauf(CFG, api, tmp_path, JETZT)
    vorher = (tmp_path / "zustand.json").read_text()
    (tmp_path / "STOPP").write_text("")
    api.alt["AAA"] = 110.0
    assert lauf(CFG, api, tmp_path, JETZT + H) == {"gestoppt": True}
    assert (tmp_path / "zustand.json").read_text() == vorher and len(bot.lesen(tmp_path / "stand.csv")) == 1


# ------------------------------------------------------------------ Live-Schranken (nachgestelltes Konto) ----
LIVE = {**CFG, "modus": "live", "hebel": 0.04, "max_order_usd": 150}         # 100 USD je Coin, Deckel 150 USD


def test_live_nur_mit_modus_umgebungsvariable_und_schluessel(tmp_path, monkeypatch):
    monkeypatch.setattr(bot.time, "sleep", lambda *_: None)
    api = LiveBoerse({"AAA": 100.0, "BBB": 50.0}, {"AAA": 110.0, "BBB": 60.0})
    monkeypatch.delenv("YUBIT_LIVE", raising=False)
    with pytest.raises(SystemExit):
        lauf(LIVE, api, tmp_path, JETZT)
    monkeypatch.setenv("YUBIT_LIVE", "ja")
    assert lauf({**LIVE, "modus": "papier"}, api, tmp_path / "p", JETZT)["modus"] == "papier" and api.orders == []
    assert lauf(LIVE, api, tmp_path, JETZT)["modus"] == "live" and len(api.orders) == 2


def test_ist_live_sicherheitsdeckel_blockiert_auch_das_schliessen(tmp_path, monkeypatch):
    """ENG-01: Steigt der Wert einer Short-Position ueber max_order_usd, wird die Schliess-Order abgelehnt, auch beim Tageslimit."""
    monkeypatch.setattr(bot.time, "sleep", lambda *_: None)
    monkeypatch.setenv("YUBIT_LIVE", "ja")
    api = LiveBoerse({"AAA": 100.0, "BBB": 50.0}, {"AAA": 110.0, "BBB": 60.0})
    lauf(LIVE, api, tmp_path, JETZT)
    assert api.pos["AAAUSDT"] == -1.0
    api.kurse["AAA"] = 160.0; api.alt["AAA"] = 110.0                          # Signal dreht auf Long, Short muss geschlossen werden
    r = lauf(LIVE, api, tmp_path, JETZT + H)
    assert any("Sicherheitsdeckel" in w for w in r["warnungen"]) and api.pos["AAAUSDT"] == -1.0
    api.kurse["AAA"] = 200.0
    r = lauf({**LIVE, "tagesverlust_limit": 0.001}, api, tmp_path, JETZT + 2 * H)
    assert zustand(tmp_path)["gesperrt_tag"] and api.pos["AAAUSDT"] == -1.0   # Tageslimit greift, kann aber nicht schliessen
