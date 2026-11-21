"""Vorwärtstest-Bot: Rechenlogik, ein kompletter Papier-Durchlauf mit nachgestellter Börse, Sicherungen, Client."""
import collections
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
        assert "trail" not in k and "nachgerechnet_bis" not in k and "netto_nachgerechnet_usd" not in k
        assert "nachgerechnet" not in (ordner / "bericht.md").read_text() if (ordner / "bericht.md").exists() else True
        assert "nachgerechnet" not in bot.bericht(cfg, ordner)


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
    # Kennzeichnung: Bericht und Dashboard-Daten nennen den nachgerechneten Abschnitt und das Ergebnis an dessen Ende
    assert "nachgerechnet (kein Vorwärtstest)" in (tmp_path / "ziel/bericht.md").read_text()
    cfg3 = {**CFG, "trail": 0.05, "nachgerechnet_bis": r["bis"]}
    k = __import__("vorwaertstest.dashboard_daten", fromlist=["bauen"]).bauen(cfg3, tmp_path / "ziel")["kennzahlen"][0]
    assert k["nachgerechnet_bis"] == r["bis"] and k["netto_nachgerechnet_usd"] == pytest.approx(r["netto_mit_rebate"], abs=0.01)


def test_nachrechnen_uebernimmt_nur_die_fuellungen_des_ersten_laufs(tmp_path):
    from vorwaertstest import nachrechnen as N
    quelle = tmp_path / "quelle"; api = Boerse({"AAA": 100.0, "BBB": 50.0}, {"AAA": 90.0, "BBB": 60.0})
    bot.schritt(CFG, api, quelle, JETZT, melden=lambda *_: None)
    api.kurse["AAA"] = 99.0                                                    # AAA (Long) fällt um 1 %: die Variante mit Stop steigt aus
    bot.schritt(CFG, api, quelle, JETZT + H // 12, melden=lambda *_: None)

    class Verlauf(Boerse):
        def kerzen(self, sym, minuten=60, limit=3, start_ms=None, ende_ms=None):
            c = sym.removesuffix("USDT"); letzte = JETZT - JETZT % H - H
            return [{"start": t, "open": 0, "high": 0, "low": 0, "close": self.kurse[c] if t >= letzte else self.alt[c]} for t in range(start_ms - start_ms % H, ende_ms, H)]

    def rechnen(ziel):
        N.nachrechnen({**CFG, "sl": 0.005}, quelle, ziel, True, api=Verlauf({"AAA": 100.0, "BBB": 50.0}, {"AAA": 90.0, "BBB": 60.0}), melden=lambda *_: None)
        return bot.lesen(ziel / "protokoll.csv")
    vorher = rechnen(tmp_path / "a")
    stops = [x for x in vorher if x["grund"] == "stop"]
    assert len(stops) == 1 and stops[0]["coin"] == "AAA" and stops[0]["zeit"] == bot.utc(JETZT + H // 12)
    # Hätte die Quelle später zur selben Minute und auf derselben Seite gehandelt, darf deren Füllkurs hier nichts bestimmen
    q = bot.lesen(quelle / "protokoll.csv")
    with open(quelle / "protokoll.csv", "a") as f:
        f.write(",".join(dict(q[0], zeit=stops[0]["zeit"], coin="AAA", seite=stops[0]["seite"], fuellkurs="1.0", grund="schliessen")[k] for k in q[0]) + "\n")
    nachher = rechnen(tmp_path / "b")
    assert [x["fuellkurs"] for x in nachher] == [x["fuellkurs"] for x in vorher]
    assert [float(x["fuellkurs"]) for x in nachher[:2]] == [float(x["fuellkurs"]) for x in q[:2]]   # Einstiege weiter wie in der Quelle


def test_nachrechnen_lehnt_doppelte_minuten_der_quelle_ab(tmp_path):
    from vorwaertstest import nachrechnen as N
    quelle = tmp_path / "quelle"; api = Boerse({"AAA": 100.0, "BBB": 50.0}, {"AAA": 90.0, "BBB": 60.0})
    bot.schritt(CFG, api, quelle, JETZT, melden=lambda *_: None)
    bot.schritt(CFG, api, quelle, JETZT + 1000, melden=lambda *_: None)          # zweiter Lauf in derselben Minute
    with pytest.raises(SystemExit):
        N.nachrechnen({**CFG, "trail": 0.05}, quelle, tmp_path / "ziel", True, api=api, melden=lambda *_: None)


# ------------------------------------------------- Test 4: Tagesregel (Richtung einmal am Tag) ----
TAG = kern.TAG_MS
M = (JETZT // TAG + 1) * TAG                                                   # ein Tageswechsel (00:00 UTC)
CFG_TAG = {**CFG, "tagesregel": True}
DD = lambda: __import__("vorwaertstest.dashboard_daten", fromlist=["bauen"])


class TagBoerse(Boerse):
    """Börse mit Stundenkerzen je Startzeit. Kerzen, die mehr als 200 Stunden vor M liegen, haben den festen Schluss `alt`;
    jüngere gibt es nur, wenn sie in `schluss` stehen (sonst fehlt die Kerze). `jetzt` ist die Uhrzeit des Laufs."""

    def __init__(self, kurse, alt, schluss, **kw):
        super().__init__(kurse, alt, **kw)
        self.schluss, self.jetzt, self.abrufe = schluss, M, []

    def _kerze(self, c, t):
        if t in self.schluss.get(c, {}):
            return {"start": t, "open": 0, "high": 0, "low": 0, "close": self.schluss[c][t]}
        if t < M - 200 * H:
            return {"start": t, "open": 0, "high": 0, "low": 0, "close": self.alt[c]}
        return None

    def kerzen(self, sym, minuten=60, limit=3, start_ms=None, ende_ms=None):
        c = sym.removesuffix("USDT")
        if start_ms is not None:
            self.abrufe.append((c, start_ms))
            return [k for k in (self._kerze(c, t) for t in range(start_ms - start_ms % H, ende_ms + 1, H)) if k]
        letzte = self.jetzt - self.jetzt % H - H
        return [k for k in (self._kerze(c, t) for t in (letzte - H, letzte)) if k]

    def lauf(self, cfg, ordner, jetzt):
        self.jetzt = jetzt
        return bot.schritt(cfg, self, ordner, jetzt, melden=lambda *_: None)


def stunden(*paare):
    """{Startzeit der Stundenkerze: Schluss} aus (Abstand zu M in Stunden, Schluss)."""
    return {M + int(h) * H: s for h, s in paare}


def zustand(ordner):
    return json.loads((ordner / "zustand.json").read_text())


def test_tagesrichtung_nimmt_die_kerze_die_um_mitternacht_schliesst():
    api = TagBoerse({"AAA": 100.0}, {"AAA": 90.0}, {"AAA": stunden((-1, 100.0), (-25, 80.0), (0, 70.0))})
    for jetzt in (M, M + 4 * 60_000, M + 23 * H + 59 * 60_000, M + TAG - 1):          # ganzer Tag: immer die Kerze 23:00–00:00 davor
        r = bot.tagesrichtung_lesen(api, "AAA", jetzt)
        assert r == {"tag": bot.utc(M)[:10], "richtung": 1, "schluss": 100.0, "schluss_alt": 90.0}
    assert bot.tagesrichtung_lesen(api, "AAA", M - 1)["richtung"] == -1                # eine Millisekunde früher: die Kerze des Vortags (80 < 90)
    assert (bot.tagesrichtung_lesen(api, "AAA", M - 1)["tag"], bot.tagesrichtung_lesen(api, "AAA", M - 1)["schluss"]) == (bot.utc(M - 1)[:10], 80.0)
    assert ("AAA", M - H) in api.abrufe and ("AAA", M - H - 336 * H) in api.abrufe      # genau diese zwei Kerzen: Tageswechsel und 336 Stunden davor
    with pytest.raises(YubitFehler):                                                   # Kerze zum Tageswechsel fehlt
        bot.tagesrichtung_lesen(TagBoerse({"AAA": 100.0}, {"AAA": 90.0}, {"AAA": {}}), "AAA", M + H)


def test_tagesregel_entscheidet_nur_zum_tageswechsel(tmp_path):
    # Tag 0: AAA über dem Stand vor 14 Tagen (Long), BBB darunter (Short). Um 04:00 UTC kippt das Stundensignal von AAA auf Short
    # und bleibt dort; die Kerze zum nächsten Tageswechsel schließt ebenfalls darunter.
    k = {"AAA": stunden((-2, 100.0), (-1, 100.0), (3, 100.0), (4, 80.0), (22, 80.0), (23, 80.0)),
         "BBB": stunden((-2, 50.0), (-1, 50.0), (3, 50.0), (4, 50.0), (22, 50.0), (23, 50.0))}
    api = TagBoerse({"AAA": 100.0, "BBB": 50.0}, {"AAA": 90.0, "BBB": 60.0}, k)
    tag, std = tmp_path / "tag", tmp_path / "stunde"
    assert api.lauf(CFG_TAG, tag, M + 4 * 60_000)["orders"] == 2 and api.lauf(CFG, std, M + 4 * 60_000)["orders"] == 2
    z = zustand(tag)
    assert z["pos"]["AAA"] > 0 and z["pos"]["BBB"] < 0
    assert z["tagesrichtung"] == {"AAA": {"tag": bot.utc(M)[:10], "richtung": 1, "schluss": 100.0, "schluss_alt": 90.0},
                                  "BBB": {"tag": bot.utc(M)[:10], "richtung": -1, "schluss": 50.0, "schluss_alt": 60.0}}
    api.kurse["AAA"] = 80.0
    api.abrufe.clear()
    assert api.lauf(CFG, std, M + 5 * H + 4 * 60_000)["orders"] == 2                    # Stundenregel (Test 1) dreht sofort
    n_std = len(api.abrufe); api.abrufe.clear()
    assert api.lauf(CFG_TAG, tag, M + 5 * H + 4 * 60_000)["orders"] == 0                # Tagesregel hält bis zum Tageswechsel
    assert zustand(tag)["pos"]["AAA"] > 0 and zustand(std)["pos"]["AAA"] < 0
    assert len(api.abrufe) == n_std                                                    # heute schon entschieden: keine zusätzlichen Abrufe
    api.abrufe.clear()
    r = api.lauf(CFG_TAG, tag, M + TAG + 4 * 60_000)                                    # nächster Tageswechsel: jetzt wird gedreht
    z = zustand(tag)
    assert r["orders"] == 2 and z["pos"]["AAA"] < 0 and z["pos"]["BBB"] < 0
    assert z["tagesrichtung"]["AAA"] == {"tag": bot.utc(M + TAG)[:10], "richtung": -1, "schluss": 80.0, "schluss_alt": 90.0}
    # Abrufe mit Startzeit in diesem Lauf, je Coin: einmal die Kerze zum Tageswechsel, zweimal die von 336 Stunden davor
    # (einmal für das Stundensignal des Laufs, einmal für die Tagesrichtung)
    assert collections.Counter(api.abrufe) == {(c, t): n for c in ("AAA", "BBB") for t, n in ((M + 23 * H, 1), (M + 23 * H - 336 * H, 2))}
    pr = bot.lesen(tag / "protokoll.csv")
    assert [x["grund"] for x in pr] == ["einstieg", "einstieg", "schliessen", "einstieg"] and len(bot.lesen(std / "protokoll.csv")) == 4
    assert "Tagesregel" in bot.bericht(CFG_TAG, tag)
    kz = DD().bauen(CFG_TAG, tag)["kennzahlen"][0]
    assert kz["tagesregel"] is True and kz["tagesrichtung_tag"] == bot.utc(M + TAG)[:10]


def test_tagesregel_holt_nach_einem_ausfall_die_richtung_vom_tageswechsel_nach(tmp_path):
    # Tag 0 Long. Am Tag 1 fällt der Lauf um 00:04 aus; der erste Lauf ist um 03:14. Die Kerze zum Tageswechsel schloss unter dem
    # Stand vor 14 Tagen (Short), die laufende Stunde liegt wieder darüber (Stundensignal Long). Maßgeblich ist der Tageswechsel.
    k = {"AAA": stunden((-2, 100.0), (-1, 100.0), (22, 80.0), (23, 80.0), (25, 95.0), (26, 95.0))}
    api = TagBoerse({"AAA": 100.0}, {"AAA": 90.0}, k)
    cfg = {**CFG_TAG, "coins": ["AAA"]}
    assert api.lauf(cfg, tmp_path, M + 4 * 60_000)["orders"] == 1 and zustand(tmp_path)["pos"]["AAA"] > 0
    api.kurse["AAA"] = 95.0
    jetzt = M + TAG + 3 * H + 14 * 60_000
    api.jetzt = jetzt
    assert bot.markt_lesen(api, "AAA", jetzt)["richtung"] == 1                          # das Stundensignal dieses Laufs zeigt Long
    r = api.lauf(cfg, tmp_path, jetzt)
    z = zustand(tmp_path)
    assert r["orders"] == 2 and z["pos"]["AAA"] < 0                                     # gedreht auf Short: Richtung der 00:00-Kerze
    assert z["tagesrichtung"]["AAA"] == {"tag": bot.utc(jetzt)[:10], "richtung": -1, "schluss": 80.0, "schluss_alt": 90.0}
    assert api.lauf(cfg, tmp_path, jetzt + 5 * 60_000)["orders"] == 0                   # danach bleibt es für den Tag dabei


def test_tagesregel_ohne_kerze_wird_nicht_gehandelt_und_spaeter_nachgeholt(tmp_path):
    # Tag 0: beide Long. Am Tag 1 fehlt um 00:04 die Kerze zum Tageswechsel für AAA (BBB hat sie und dreht). Kein Handel in AAA,
    # auch wenn das Stundensignal Short zeigt; sobald die Kerze da ist, wird nachgeholt.
    k = {"AAA": stunden((-2, 100.0), (-1, 100.0), (22, 80.0)), "BBB": stunden((-2, 70.0), (-1, 70.0), (22, 50.0), (23, 50.0))}
    api = TagBoerse({"AAA": 100.0, "BBB": 70.0}, {"AAA": 90.0, "BBB": 60.0}, k)
    assert api.lauf(CFG_TAG, tmp_path, M + 4 * 60_000)["orders"] == 2
    api.kurse.update(AAA=80.0, BBB=50.0)
    tag0 = dict(zustand(tmp_path)["tagesrichtung"]["AAA"])
    r = api.lauf(CFG_TAG, tmp_path, M + TAG + 4 * 60_000 + 30_000)                      # Kerze 23:00 von AAA fehlt; als letzte Stunde gilt 22:00
    z = zustand(tmp_path)
    assert r["orders"] == 2 and z["pos"]["BBB"] < 0 and z["pos"]["AAA"] > 0             # BBB dreht, AAA bleibt
    assert any("Tagesrichtung noch nicht übernommen" in w and "AAA" in w for w in r["warnungen"])
    assert z["tagesrichtung"]["AAA"] == tag0                                            # der Eintrag des Vortags bleibt unverändert stehen
    assert DD().bauen(CFG_TAG, tmp_path)["kennzahlen"][0]["tagesrichtung_tag"] == tag0["tag"]   # das Board nennt den ältesten Tag
    api.schluss["AAA"][M + 23 * H] = 80.0                                               # die Kerze erscheint
    r = api.lauf(CFG_TAG, tmp_path, M + TAG + 9 * 60_000)
    assert r["orders"] == 2 and zustand(tmp_path)["pos"]["AAA"] < 0 and not r["warnungen"]
    # Neues Konto ohne Kerze zum Tageswechsel: kein Einstieg, bis sie vorliegt
    neu = tmp_path / "neu"; api2 = TagBoerse({"AAA": 100.0}, {"AAA": 90.0}, {"AAA": stunden((-2, 100.0))})
    r = api2.lauf({**CFG_TAG, "coins": ["AAA"]}, neu, M + 4 * 60_000)
    assert r["orders"] == 0 and zustand(neu)["pos"].get("AAA", 0.0) == 0.0 and zustand(neu)["tagesrichtung"] == {}


def test_tagesregel_gleichstand_und_tageslimit(tmp_path):
    k = {"AAA": stunden((-2, 100.0), (-1, 100.0), (22, 90.0), (23, 90.0), (46, 90.0)), "BBB": stunden((-2, 70.0), (-1, 70.0), (22, 70.0), (23, 70.0), (46, 70.0))}
    api = TagBoerse({"AAA": 100.0, "BBB": 70.0}, {"AAA": 90.0, "BBB": 60.0}, k)
    assert api.lauf(CFG_TAG, tmp_path, M + 4 * 60_000)["orders"] == 2                   # beide Long
    api.kurse["AAA"] = 90.0
    r = api.lauf(CFG_TAG, tmp_path, M + TAG + 4 * 60_000)                               # AAA: Schluss gleich dem vor 14 Tagen -> keine Position
    z = zustand(tmp_path)
    assert z["tagesrichtung"]["AAA"]["richtung"] == 0 and z["pos"]["AAA"] == 0.0 and z["pos"]["BBB"] > 0
    assert [x["grund"] for x in bot.lesen(tmp_path / "protokoll.csv")][-1] == "schliessen"
    # Tageslimit schließt auch dann, wenn für den Tag noch keine Richtung übernommen werden konnte (Kerze von BBB fehlt am Tag 2)
    assert api.lauf(CFG_TAG, tmp_path, M + 2 * TAG + 4 * 60_000 + 30_000)["orders"] == 0   # Tag 2 ohne Kerze: nichts tun
    api.kurse["BBB"] = 45.0                                                             # im Lauf des Tages: BBB Long (500 $) von 70 auf 45, −3,6 % vom Kapital
    r = api.lauf(CFG_TAG, tmp_path, M + 2 * TAG + 9 * 60_000 + 30_000)
    z = zustand(tmp_path)
    assert z["tagesrichtung"]["BBB"]["tag"] == bot.utc(M + TAG)[:10]                    # für Tag 2 liegt keine Richtung vor
    assert z["gesperrt_tag"] and z["pos"]["BBB"] == 0.0 and bot.lesen(tmp_path / "protokoll.csv")[-1]["grund"] == "tageslimit"
    # Gegenprobe ohne Limit: derselbe Lauf ohne Tagesrichtung lässt die Position stehen
    ohne = tmp_path / "ohne"; cfg = {**CFG_TAG, "tagesverlust_limit": 1.0}
    api.kurse.update(AAA=100.0, BBB=70.0); api.lauf(cfg, ohne, M + 4 * 60_000)
    api.kurse.update(AAA=90.0, BBB=45.0); api.lauf(cfg, ohne, M + TAG + 4 * 60_000)
    r = api.lauf(cfg, ohne, M + 2 * TAG + 4 * 60_000 + 30_000)
    assert r["orders"] == 0 and zustand(ohne)["pos"]["BBB"] > 0 and any("Tagesrichtung noch nicht übernommen" in w for w in r["warnungen"])


def test_ohne_tagesregel_keine_neuen_felder_und_keine_zusaetzlichen_abrufe(tmp_path):
    k = {c: stunden((-2, s), (-1, s), (3, s), (4, s)) for c, s in (("AAA", 100.0), ("BBB", 50.0))}
    for i, cfg in enumerate((CFG, {**CFG, "tp": 0.15, "sl": 0.05}, {**CFG, "trail": 0.05})):   # Test 1, 2 und 3
        api = TagBoerse({"AAA": 100.0, "BBB": 50.0}, {"AAA": 90.0, "BBB": 60.0}, k)
        ordner = tmp_path / str(i)
        api.lauf(cfg, ordner, M + 4 * 60_000); api.lauf(cfg, ordner, M + 5 * H + 4 * 60_000)
        assert "tagesrichtung" not in zustand(ordner)
        assert sorted(api.abrufe) == sorted((c, t - 336 * H) for c in ("AAA", "BBB") for t in (M - H, M + 4 * H))   # nur die Kerze von vor 14 Tagen, je Lauf
        kz = DD().bauen(cfg, ordner)["kennzahlen"][0]
        assert "tagesregel" not in kz and "tagesrichtung_tag" not in kz and "Tagesregel" not in bot.bericht(cfg, ordner)


def test_nachrechnen_mit_tagesregel_haelt_ueber_wechsel_der_quelle_hinweg(tmp_path):
    from vorwaertstest import nachrechnen as N
    # Quelle (Stundenregel): AAA dreht um 04:00 auf Short und um 08:00 zurück auf Long. Die Tagesregel sieht davon nichts.
    k = {"AAA": stunden((-2, 100.0), (-1, 100.0), (2, 100.0), (3, 100.0), (4, 80.0), (5, 80.0), (7, 80.0), (8, 100.0), (9, 100.0)),
         "BBB": stunden((-2, 50.0), (-1, 50.0), (2, 50.0), (3, 50.0), (4, 50.0), (5, 50.0), (7, 50.0), (8, 50.0), (9, 50.0))}
    api = TagBoerse({"AAA": 100.0, "BBB": 50.0}, {"AAA": 90.0, "BBB": 60.0}, k)
    quelle = tmp_path / "quelle"
    for h, kurs in ((0, 100.0), (4, 100.0), (5, 80.0), (9, 100.0), (10, 100.0)):
        api.kurse["AAA"] = kurs
        api.lauf(CFG, quelle, M + h * H + 4 * 60_000)
    assert len(bot.lesen(quelle / "protokoll.csv")) == 6                                # zwei Einstiege und zwei Drehs von AAA
    r = N.nachrechnen(CFG_TAG, quelle, tmp_path / "ziel", True, api=api, melden=lambda *_: None)
    pr, q = bot.lesen(tmp_path / "ziel/protokoll.csv"), bot.lesen(quelle / "protokoll.csv")
    assert r["laeufe"] == 5 and len(pr) == 2 and [x["grund"] for x in pr] == ["einstieg", "einstieg"]
    assert [(x["coin"], x["seite"], x["fuellkurs"], x["menge"]) for x in pr] == [(x["coin"], x["seite"], x["fuellkurs"], x["menge"]) for x in q[:2]]
    assert zustand(tmp_path / "ziel")["pos"] == {c: v for c, v in zip(("AAA", "BBB"), (5.0, -10.0))}
    # Ohne Wechsel in der Quelle ist die Nachrechnung mit Tagesregel Zeile für Zeile gleich der Quelle
    ruhig = tmp_path / "ruhig"
    api = TagBoerse({"AAA": 100.0, "BBB": 50.0}, {"AAA": 90.0, "BBB": 60.0}, {c: stunden(*((h, s) for h in range(-2, 6))) for c, s in (("AAA", 100.0), ("BBB", 50.0))})
    for h, kurs in ((0, 100.0), (2, 101.0), (3, 103.0), (5, 97.0)):
        api.kurse["AAA"] = kurs
        api.lauf(CFG, ruhig, M + h * H + 4 * 60_000)
    assert len(bot.lesen(ruhig / "protokoll.csv")) == 2 and len(bot.lesen(ruhig / "stand.csv")) == 4
    N.nachrechnen(CFG_TAG, ruhig, tmp_path / "ziel2", True, api=api, melden=lambda *_: None)
    assert bot.lesen(tmp_path / "ziel2/protokoll.csv") == bot.lesen(ruhig / "protokoll.csv")
    assert bot.lesen(tmp_path / "ziel2/stand.csv") == bot.lesen(ruhig / "stand.csv")


def test_tagesregel_uebernimmt_erst_eine_minute_nach_dem_tageswechsel(tmp_path):
    # Tag 0 Long; die Kerze zum nächsten Tageswechsel schließt unter dem Stand vor 14 Tagen (Short). Ein Lauf in der ersten Minute
    # des neuen Tages (z. B. der verspätete Lauf von 23:59) übernimmt noch nicht, handelt nicht und fragt die Tageskerze nicht ab.
    k = {"AAA": stunden((-2, 100.0), (-1, 100.0), (22, 80.0), (23, 80.0))}
    api = TagBoerse({"AAA": 100.0}, {"AAA": 90.0}, k)
    cfg = {**CFG_TAG, "coins": ["AAA"]}
    assert api.lauf(cfg, tmp_path, M + 4 * 60_000)["orders"] == 1
    tag0 = dict(zustand(tmp_path)["tagesrichtung"]["AAA"])
    api.kurse["AAA"] = 80.0
    for spaet in (0, 5_000, kern.TAGESREGEL_KARENZ_MS - 1):
        api.abrufe.clear()
        r = api.lauf(cfg, tmp_path, M + TAG + spaet)
        z = zustand(tmp_path)
        assert r["orders"] == 0 and z["pos"]["AAA"] > 0 and z["tagesrichtung"]["AAA"] == tag0 and r["warnungen"] == []
        assert api.abrufe == [("AAA", M + 23 * H - 336 * H)]                              # nur der Abruf für das Stundensignal des Laufs
    r = api.lauf(cfg, tmp_path, M + TAG + kern.TAGESREGEL_KARENZ_MS)                      # genau eine Minute nach dem Tageswechsel: Übernahme
    z = zustand(tmp_path)
    assert kern.TAGESREGEL_KARENZ_MS == 60_000 and r["orders"] == 2 and z["pos"]["AAA"] < 0
    assert z["tagesrichtung"]["AAA"] == {"tag": bot.utc(M + TAG)[:10], "richtung": -1, "schluss": 80.0, "schluss_alt": 90.0}
    # Neues Konto in der ersten Minute des Tages: kein Einstieg; eine Minute später schon
    neu = tmp_path / "neu"
    api.kurse["AAA"] = 100.0
    assert api.lauf(cfg, neu, M + 30_000)["orders"] == 0 and zustand(neu)["tagesrichtung"] == {}
    assert api.lauf(cfg, neu, M + 60_000)["orders"] == 1 and zustand(neu)["pos"]["AAA"] > 0
    # Ohne Tagesregel gibt es keine solche Wartezeit: Test 1 handelt auch in der ersten Minute
    std = tmp_path / "std"
    assert api.lauf(CFG | {"coins": ["AAA"]}, std, M + 30_000)["orders"] == 1
