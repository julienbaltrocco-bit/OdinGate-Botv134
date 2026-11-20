"""Vorwärtstest-Bot: Rechenlogik, ein kompletter Papier-Durchlauf mit nachgestellter Börse, Sicherungen, Client."""
import hashlib
import hmac
import io
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from vorwaertstest import bot, kern
from vorwaertstest.yubit import Yubit, YubitFehler

FIX = Path(__file__).parent / "fixtures"
H = kern.STUNDE_MS
JETZT = 1_800_000_000_000 - (1_800_000_000_000 % H) + 5 * 60_000      # 5 Minuten nach einer vollen Stunde
CFG = {"modus": "papier", "kapital_usd": 5000, "hebel": 0.2, "coins": ["AAA", "BBB"], "tagesverlust_limit": 0.03,
       "preisgrenze": 0.0005, "max_order_usd": 150, "daten": "daten"}


class Boerse:
    """Nachgestellte Börse: je Coin Kurs jetzt, Kurs vor 14 Tagen, Spanne."""
    key = secret = ""

    def __init__(self, kurse, alt, min_menge=0.1, schritt=0.1, tiefe=1000.0):
        self.kurse, self.alt, self.min, self.schritt, self.tiefe, self.aufrufe = kurse, alt, min_menge, schritt, tiefe, 0

    def kerzen(self, sym, minuten=60, limit=3, start_ms=None, ende_ms=None):
        c = sym.removesuffix("USDT")
        if start_ms is not None:
            return [{"start": start_ms, "open": 0, "high": 0, "low": 0, "close": self.alt[c]}]
        letzte = JETZT - JETZT % H - H
        return [{"start": letzte, "open": 0, "high": 0, "low": 0, "close": self.kurse[c]},
                {"start": letzte + H, "open": 0, "high": 0, "low": 0, "close": self.kurse[c]}]   # läuft noch

    def kontrakt(self, sym):
        return {"status": "Trading", "min_menge": self.min, "schritt": self.schritt, "tick": 0.01, "funding_minuten": 480}

    def ticker(self, sym):
        p = self.kurse[sym.removesuffix("USDT")]
        return {"geld": p - 0.05, "brief": p + 0.05, "letzter": p, "mark": p, "funding": 0.0001, "umsatz24h": 1e6}

    def buch(self, sym, tiefe=25):
        p = self.kurse[sym.removesuffix("USDT")]
        return {"geld": [(p - 0.05, self.tiefe), (p - 0.15, self.tiefe)], "brief": [(p + 0.05, self.tiefe), (p + 0.15, self.tiefe)]}


def test_richtung_und_runden():
    assert kern.richtung(101, 100) == 1 and kern.richtung(99, 100) == -1 and kern.richtung(100, 100) == 0
    assert kern.menge_runden(100, 66450, 0.001, 0.001) == 0.001          # BTC: 100 $ reichen für genau eine Einheit
    assert kern.menge_runden(20, 66450, 0.001, 0.001) == 0.0             # 20 $ liegen unter der Mindestgröße
    assert kern.menge_runden(100, 0.9858, 0.1, 0.1) == pytest.approx(101.4)


def test_buch_fill_laeuft_durch_die_stufen():
    buch = {"geld": [(99.0, 1.0), (98.0, 5.0)], "brief": [(101.0, 1.0), (102.0, 5.0)]}
    kurs, q = kern.buch_fill(True, 3.0, buch)
    assert q == 3.0 and kurs == pytest.approx((101 + 2 * 102) / 3)
    kurs, q = kern.buch_fill(False, 10.0, buch)                          # mehr als sichtbar: Rest bleibt
    assert q == 6.0
    assert kern.slippage(True, 101.0, 100.0) == pytest.approx(0.01) and kern.slippage(False, 99.0, 100.0) == pytest.approx(0.01)


def test_papier_durchlauf_oeffnet_dreht_und_bucht(tmp_path):
    api = Boerse({"AAA": 100.0, "BBB": 50.0}, {"AAA": 90.0, "BBB": 60.0})
    r = bot.schritt(CFG, api, tmp_path, JETZT, melden=lambda *_: None)
    z = json.loads((tmp_path / "zustand.json").read_text())
    assert r["orders"] == 2 and z["pos"]["AAA"] == pytest.approx(5.0) and z["pos"]["BBB"] == pytest.approx(-10.0)
    pr = bot.lesen(tmp_path / "protokoll.csv")
    assert pr[0]["seite"] == "kauf" and float(pr[0]["fuellkurs"]) == pytest.approx(100.05)     # zum Briefkurs gekauft
    assert float(pr[0]["slippage_bp"]) == pytest.approx(5.0)                                    # halbe Spanne
    assert float(pr[0]["gebuehr"]) == pytest.approx(0.0008 * 5 * 100.05)
    assert len(bot.lesen(tmp_path / "spannen.csv")) == 2
    # nächste Stunde, unverändert: keine neue Order
    assert bot.schritt(CFG, api, tmp_path, JETZT + H, melden=lambda *_: None)["orders"] == 0
    # AAA dreht: schließen (Verkauf 5) und Gegenseite öffnen (Verkauf zum neuen Kurs)
    api.kurse["AAA"] = 80.0
    r = bot.schritt(CFG, api, tmp_path, JETZT + 2 * H, melden=lambda *_: None)
    z = json.loads((tmp_path / "zustand.json").read_text())
    assert r["orders"] == 2 and z["pos"]["AAA"] == pytest.approx(-6.2)   # 500 $ / 79,95 auf 0,1 abgerundet
    v = kern.vermoegen(z, {"AAA": 80.0, "BBB": 50.0})
    assert v["brutto"] < -90                                              # Long von 100,05 auf 79,95: rund −100 $
    assert "Netto mit Rebate" in bot.bericht(CFG, tmp_path)


def test_unter_mindestgroesse_wird_ausgelassen(tmp_path):
    api = Boerse({"AAA": 100.0, "BBB": 50.0}, {"AAA": 90.0, "BBB": 60.0}, min_menge=100.0, schritt=100.0)
    r = bot.schritt(CFG, api, tmp_path, JETZT, melden=lambda *_: None)
    assert r["orders"] == 0 and any("Mindestordergröße" in w for w in r["warnungen"])


def test_tagesverlust_limit_schliesst_alles(tmp_path):
    api = Boerse({"AAA": 100.0, "BBB": 50.0}, {"AAA": 90.0, "BBB": 40.0})
    bot.schritt(CFG, api, tmp_path, JETZT, melden=lambda *_: None)      # beide Long, je 500 $
    api.kurse.update(AAA=80.0, BBB=40.0)                                 # −200 $ = −4 % vom Kapital
    api.alt.update(AAA=70.0, BBB=30.0)                                   # Signal bliebe Long
    bot.schritt(CFG, api, tmp_path, JETZT + H, melden=lambda *_: None)
    z = json.loads((tmp_path / "zustand.json").read_text())
    assert z["pos"]["AAA"] == 0 and z["pos"]["BBB"] == 0 and z["gesperrt_tag"]
    assert bot.schritt(CFG, api, tmp_path, JETZT + 2 * H, melden=lambda *_: None)["orders"] == 0   # heute Pause


def test_stopp_datei_und_live_sperre(tmp_path, monkeypatch):
    api = Boerse({"AAA": 100.0, "BBB": 50.0}, {"AAA": 90.0, "BBB": 60.0})
    (tmp_path / "STOPP").write_text("")
    assert bot.schritt(CFG, api, tmp_path, JETZT, melden=lambda *_: None) == {"gestoppt": True}
    (tmp_path / "STOPP").unlink()
    monkeypatch.delenv("YUBIT_LIVE", raising=False)
    with pytest.raises(SystemExit):                                       # live ohne Schlüssel und Freigabe: Abbruch
        bot.schritt({**CFG, "modus": "live"}, api, tmp_path, JETZT, melden=lambda *_: None)
    assert not (tmp_path / "protokoll.csv").exists()


def test_veraltete_kerzen_fuehren_zu_keiner_order(tmp_path):
    api = Boerse({"AAA": 100.0, "BBB": 50.0}, {"AAA": 90.0, "BBB": 60.0})
    with pytest.raises(SystemExit):
        bot.schritt(CFG, api, tmp_path, JETZT + 10 * H, melden=lambda *_: None)


# ------------------------------------------------------------------ Client ----
class Antwort(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


def oeffner(aufgezeichnet):
    def f(req, timeout=20):
        aufgezeichnet.append(req)
        for name in ("ticker", "book", "klines", "instr"):
            if {"ticker": "tickers", "book": "orderbooks", "klines": "klines", "instr": "instruments"}[name] in req.full_url:
                return Antwort((FIX / f"yubit_{name}.json").read_bytes())
        return Antwort(b'{"code":0,"data":{"orderId":"1"}}')
    return f


def test_client_liest_echte_antwortformate():
    api = Yubit(pause=0, oeffner=oeffner([]))
    t, b, k, i = api.ticker("BTCUSDT"), api.buch("BTCUSDT"), api.kerzen("BTCUSDT"), api.kontrakt("BTCUSDT")
    assert t["geld"] < t["brief"] and t["funding"] == pytest.approx(0.0001)
    assert b["geld"][0][0] == max(p for p, _ in b["geld"]) < b["brief"][0][0] == min(p for p, _ in b["brief"])
    assert [x["start"] for x in k] == sorted(x["start"] for x in k) and k[1]["start"] - k[0]["start"] == H
    assert i == {"status": "Trading", "min_menge": 0.001, "schritt": 0.001, "tick": 0.1, "funding_minuten": 480}


def test_signatur_wie_im_offiziellen_paket(monkeypatch):
    gesehen = []
    api = Yubit("schluessel", "geheim", pause=0, oeffner=oeffner(gesehen))
    monkeypatch.setattr("time.time", lambda: 1_700_000_000.0)
    api.order("XRPUSDT", "Buy", "10.0", "0.9860", 1, False)
    req = gesehen[-1]
    body = req.data.decode()
    assert json.loads(body)["positionIdx"] == 1 and " " not in body
    soll = hmac.new(b"geheim", ("1700000000000" + "schluessel" + "5000" + body).encode(), hashlib.sha256).hexdigest()
    kopf = {k.upper(): v for k, v in req.header_items()}
    assert kopf["MF-ACCESS-SIGN"] == soll and kopf["MF-ACCESS-API-KEY"] == "schluessel"
    with pytest.raises(YubitFehler):
        Yubit(pause=0, oeffner=oeffner([])).positionen()                  # ohne Schlüssel kein Kontozugriff


def test_gewinnziel_stop_und_pause_bis_zum_dreh(tmp_path):
    cfg = {**CFG, "tp": 0.15, "sl": 0.05}
    still = lambda *_: None
    api = Boerse({"AAA": 100.0, "BBB": 50.0}, {"AAA": 90.0, "BBB": 60.0})      # AAA Long, BBB Short
    bot.schritt(cfg, api, tmp_path, JETZT, melden=still)
    z = json.loads((tmp_path / "zustand.json").read_text())
    assert z["einstieg"]["AAA"] == pytest.approx(100.05) and z["einstieg"]["BBB"] == pytest.approx(49.95)
    # AAA +10 %: noch kein Ziel; BBB steigt 6 % gegen den Short: Stop
    api.kurse.update({"AAA": 110.0, "BBB": 53.0})
    bot.schritt(cfg, api, tmp_path, JETZT + H // 4, melden=still)
    z = json.loads((tmp_path / "zustand.json").read_text())
    assert z["pos"]["AAA"] == pytest.approx(5.0) and z["pos"]["BBB"] == 0.0 and z["sperre"]["BBB"] == -1
    assert bot.lesen(tmp_path / "protokoll.csv")[-1]["grund"] == "stop"
    # AAA +16 %: Gewinnziel; BBB bleibt Short-Signal: kein Wiedereinstieg
    api.kurse.update({"AAA": 116.2, "BBB": 52.0})
    r = bot.schritt(cfg, api, tmp_path, JETZT + 2 * (H // 4), melden=still)
    z = json.loads((tmp_path / "zustand.json").read_text())
    assert r["orders"] == 1 and z["pos"]["AAA"] == 0.0 and z["pos"]["BBB"] == 0.0
    assert bot.lesen(tmp_path / "protokoll.csv")[-1]["grund"] == "ziel"
    assert bot.schritt(cfg, api, tmp_path, JETZT + 3 * (H // 4), melden=still)["orders"] == 0     # beide pausieren
    # BBB dreht auf Long: Sperre fällt, Einstieg in die neue Richtung; AAA pausiert weiter
    api.kurse["BBB"] = 61.0
    bot.schritt(cfg, api, tmp_path, JETZT + 4 * (H // 4), melden=still)
    z = json.loads((tmp_path / "zustand.json").read_text())
    assert z["pos"]["BBB"] > 0 and z["sperre"]["BBB"] == 0 and z["pos"]["AAA"] == 0.0
    d = __import__("vorwaertstest.dashboard_daten", fromlist=["bauen"]).bauen(cfg, tmp_path)
    aaa = next(p for p in d["positionen"] if p["coin"] == "AAA"); bbb = next(p for p in d["positionen"] if p["coin"] == "BBB")
    assert aaa["wartet"] and aaa["ziel_kurs"] is None
    assert bbb["ziel_kurs"] == pytest.approx(bbb["einstieg"] * 1.15) and bbb["stop_kurs"] == pytest.approx(bbb["einstieg"] * 0.95)


def test_ohne_ziel_und_stop_bleibt_alles_wie_bisher(tmp_path):
    api = Boerse({"AAA": 100.0, "BBB": 50.0}, {"AAA": 90.0, "BBB": 60.0})
    bot.schritt(CFG, api, tmp_path, JETZT, melden=lambda *_: None)
    api.kurse.update({"AAA": 130.0, "BBB": 58.0})                              # weit über Ziel bzw. Stop der Variante
    assert bot.schritt(CFG, api, tmp_path, JETZT + H, melden=lambda *_: None)["orders"] == 0


def test_nachgezogener_stop_folgt_dem_besten_kurs_und_pausiert(tmp_path):
    cfg = {**CFG, "trail": 0.05}
    still = lambda *_: None
    api = Boerse({"AAA": 100.0, "BBB": 50.0}, {"AAA": 90.0, "BBB": 60.0})      # AAA Long, BBB Short
    bot.schritt(cfg, api, tmp_path, JETZT, melden=still)
    z = json.loads((tmp_path / "zustand.json").read_text())
    assert z["beste"]["AAA"] == pytest.approx(100.05) and z["beste"]["BBB"] == pytest.approx(49.95)
    # AAA steigt auf 120: Stop wandert mit. BBB fällt auf 44 (gut für den Short): bester Kurs 44
    api.kurse.update({"AAA": 120.0, "BBB": 44.0})
    assert bot.schritt(cfg, api, tmp_path, JETZT + H // 4, melden=still)["orders"] == 0
    z = json.loads((tmp_path / "zustand.json").read_text())
    assert z["beste"]["AAA"] == pytest.approx(120.0) and z["beste"]["BBB"] == pytest.approx(44.0)
    d = __import__("vorwaertstest.dashboard_daten", fromlist=["bauen"]).bauen(cfg, tmp_path)
    aaa = next(p for p in d["positionen"] if p["coin"] == "AAA"); bbb = next(p for p in d["positionen"] if p["coin"] == "BBB")
    assert aaa["stop_kurs"] == pytest.approx(114.0) and bbb["stop_kurs"] == pytest.approx(46.2) and d["kennzahlen"][0]["trail"] == 0.05
    # AAA 115: 4,2 % unter dem Hoch, noch kein Stop. BBB 46,5: 5,7 % über dem Tief, Stop obwohl 7 % im Gewinn
    api.kurse.update({"AAA": 115.0, "BBB": 46.5})
    assert bot.schritt(cfg, api, tmp_path, JETZT + 2 * (H // 4), melden=still)["orders"] == 1
    z = json.loads((tmp_path / "zustand.json").read_text())
    assert z["pos"]["BBB"] == 0.0 and z["sperre"]["BBB"] == -1 and z["pos"]["AAA"] > 0
    assert bot.lesen(tmp_path / "protokoll.csv")[-1]["grund"] == "nachzug"
    # AAA 113,9: mehr als 5 % unter dem Hoch von 120: Stop. BBB bleibt Short-Signal: Pause
    api.kurse.update({"AAA": 113.9, "BBB": 40.0})
    assert bot.schritt(cfg, api, tmp_path, JETZT + 3 * (H // 4), melden=still)["orders"] == 1
    assert bot.schritt(cfg, api, tmp_path, JETZT + 4 * (H // 4), melden=still)["orders"] == 0
    # BBB dreht auf Long: Wiedereinstieg, der nachgezogene Stop beginnt neu am Einstiegskurs
    api.kurse["BBB"] = 61.0
    bot.schritt(cfg, api, tmp_path, JETZT + 5 * (H // 4), melden=still)
    z = json.loads((tmp_path / "zustand.json").read_text())
    assert z["pos"]["BBB"] > 0 and z["beste"]["BBB"] == pytest.approx(61.05) and z["sperre"]["BBB"] == 0


def test_ohne_nachzug_entstehen_keine_neuen_felder(tmp_path):
    for cfg in (CFG, {**CFG, "tp": 0.15, "sl": 0.05}):                         # Test 1 und Test 2: Zustand und Ausgabe wie bisher
        ordner = tmp_path / str(len(cfg)); api = Boerse({"AAA": 100.0, "BBB": 50.0}, {"AAA": 90.0, "BBB": 60.0})
        bot.schritt(cfg, api, ordner, JETZT, melden=lambda *_: None)
        api.kurse.update({"AAA": 104.0, "BBB": 51.0})
        bot.schritt(cfg, api, ordner, JETZT + H // 4, melden=lambda *_: None)
        assert "beste" not in json.loads((ordner / "zustand.json").read_text())
        k = __import__("vorwaertstest.dashboard_daten", fromlist=["bauen"]).bauen(cfg, ordner)["kennzahlen"][0]
        assert "trail" not in k and "nachgerechnet_bis" not in k


def test_nachrechnen_folgt_den_aufzeichnungen(tmp_path):
    from vorwaertstest import nachrechnen as N
    quelle = tmp_path / "quelle"; api = Boerse({"AAA": 100.0, "BBB": 50.0}, {"AAA": 90.0, "BBB": 60.0})
    zeiten = [JETZT + i * (H // 12) for i in range(6)]
    for i, kurs in enumerate((50.0, 46.0, 44.0, 45.0, 46.5, 47.0)):            # BBB (Short) fällt und erholt sich
        api.kurse["BBB"] = kurs
        bot.schritt(CFG, api, quelle, zeiten[i], melden=lambda *_: None)
    assert json.loads((quelle / "zustand.json").read_text())["pos"]["BBB"] < 0  # die Quelle (ohne Stop) hält weiter

    class Verlauf(Boerse):                                                     # Stundenkerzen wie in der Quelle, Kontrakte wie dort
        def kerzen(self, sym, minuten=60, limit=3, start_ms=None, ende_ms=None):
            c = sym.removesuffix("USDT"); letzte = JETZT - JETZT % H - H
            return [{"start": t, "open": 0, "high": 0, "low": 0, "close": self.kurse[c] if t >= letzte else self.alt[c]} for t in range(start_ms - start_ms % H, ende_ms, H)]
    r = N.nachrechnen({**CFG, "trail": 0.05}, quelle, tmp_path / "ziel", True, api=Verlauf({"AAA": 100.0, "BBB": 50.0}, {"AAA": 90.0, "BBB": 60.0}), melden=lambda *_: None)
    z, pr = json.loads((tmp_path / "ziel/zustand.json").read_text()), bot.lesen(tmp_path / "ziel/protokoll.csv")
    q = bot.lesen(quelle / "protokoll.csv")
    assert [float(x["fuellkurs"]) for x in pr[:2]] == [float(x["fuellkurs"]) for x in q[:2]]      # Einstiege wie in der Quelle
    assert r["laeufe"] == 6 and z["pos"]["BBB"] == 0.0 and pr[-1]["grund"] == "nachzug" and pr[-1]["zeit"] == bot.utc(zeiten[4])
    assert float(pr[-1]["fuellkurs"]) == pytest.approx(46.55)                  # Rückkauf zum damals gemessenen Briefkurs
