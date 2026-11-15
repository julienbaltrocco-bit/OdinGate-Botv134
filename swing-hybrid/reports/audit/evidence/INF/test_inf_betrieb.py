"""Audit INF: Regressionstests zum Betriebsverhalten des Papier-Bots (Stand Commit 3dfd5b2).

Die Tests halten das HEUTIGE Verhalten fest, bevor etwas geaendert wird. Tests mit dem Praefix `test_ist_` dokumentieren
einen Befund (die Zahl im Namen verweist auf die Befund-ID): Wird der Befund behoben, muss der Test bewusst angepasst werden.
Tests mit dem Praefix `test_ok_` halten Verhalten fest, das in Ordnung ist und erhalten bleiben soll.

Aufruf im Ordner swing-hybrid (schreibt nichts ins Repo):
    .venv/bin/python -I -B -m pytest -q -p no:cacheprovider reports/audit/evidence/INF/test_inf_betrieb.py
"""
import datetime as dt
import http.client
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))
from vorwaertstest import bot, dashboard_daten, kern          # noqa: E402
from vorwaertstest.yubit import Yubit, YubitFehler            # noqa: E402

H = kern.STUNDE_MS
T0 = 1_800_000_000_000 - (1_800_000_000_000 % H) + 5 * 60_000
CFG = {"modus": "papier", "kapital_usd": 5000, "hebel": 3.0, "coins": ["AAA", "BBB"], "tagesverlust_limit": 1.0,
       "preisgrenze": 0.0005, "max_order_usd": 2000, "daten": "x"}
still = lambda *_: None


class Boerse:
    """Nachgestellte Boerse mit eigener Uhr (Muster aus tests/test_vorwaertstest_bot.py)."""
    key = secret = ""

    def __init__(self):
        self.kurse, self.alt = {"AAA": 100.0, "BBB": 50.0}, {"AAA": 90.0, "BBB": 60.0}      # AAA Long, BBB Short
        self.jetzt, self.kaputt, self.haken, self.stau_h, self.aufrufe = T0, set(), None, 0, 0

    def kerzen(self, sym, minuten=60, limit=3, start_ms=None, ende_ms=None):
        c = sym.removesuffix("USDT")
        if self.haken:
            h, self.haken = self.haken, None
            h()
        if c in self.kaputt:
            raise YubitFehler(f"HTTP 429 ({c})")
        if start_ms is not None:
            return [{"start": start_ms, "open": 0, "high": 0, "low": 0, "close": self.alt[c]}]
        neueste = self.jetzt - self.jetzt % H - self.stau_h * H
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


def zustand(d):
    return json.loads((d / "zustand.json").read_text())


# ----------------------------------------------------------------------------------- in Ordnung ----
def test_ok_zweiter_lauf_zur_selben_zeit_handelt_nicht(tmp_path):
    api = Boerse()
    assert lauf(CFG, api, tmp_path, T0)["orders"] == 2
    assert lauf(CFG, api, tmp_path, T0)["orders"] == 0
    assert zustand(tmp_path)["orders"] == 2 and len(bot.lesen(tmp_path / "protokoll.csv")) == 2


def test_ok_zustand_wird_ueber_zwischendatei_ersetzt(tmp_path):
    lauf(CFG, Boerse(), tmp_path, T0)
    assert (tmp_path / "zustand.json").exists() and not (tmp_path / "zustand.json.tmp").exists()


def test_ok_protokoll_und_zustand_stimmen_nach_normalem_lauf(tmp_path):
    api = Boerse()
    lauf(CFG, api, tmp_path, T0)
    api.kurse["AAA"] = 80.0                                               # AAA dreht
    lauf(CFG, api, tmp_path, T0 + H)
    z, pr = zustand(tmp_path), bot.lesen(tmp_path / "protokoll.csv")
    pos = {}
    for r in pr:
        pos[r["coin"]] = pos.get(r["coin"], 0.0) + float(r["menge"]) * (1 if r["seite"] == "kauf" else -1)
    assert len(pr) == z["orders"] == 4
    assert all(pos[c] == pytest.approx(z["pos"][c]) for c in CFG["coins"])
    assert sum(float(r["gebuehr"]) for r in pr) == pytest.approx(z["gebuehr"], abs=1e-4)


def test_ok_ohne_marktdaten_wird_nichts_geschrieben(tmp_path):
    api = Boerse(); api.kaputt = {"AAA", "BBB"}
    with pytest.raises(SystemExit):
        lauf(CFG, api, tmp_path, T0)
    assert not (tmp_path / "stand.csv").exists() and not (tmp_path / "zustand.json").exists()


def test_ok_kerze_aelter_als_zwei_stunden_wird_abgelehnt(tmp_path):
    api = Boerse(); api.stau_h = 3                                        # Schluss der letzten Kerze 2 h 05 min alt
    with pytest.raises(SystemExit):
        lauf(CFG, api, tmp_path, T0)


def test_ok_client_meldet_http_fehler_als_yubitfehler():
    def oeffner(req, timeout=20):
        raise TimeoutError("timed out")
    with pytest.raises(YubitFehler):
        Yubit(pause=0, oeffner=oeffner).ticker("BTCUSDT")


# ------------------------------------------------------------------------- heutiges Verhalten ----
def test_ist_inf03_absturz_vor_zustand_verdoppelt_das_protokoll(tmp_path, monkeypatch):
    """bot.py:276-281: erst CSV anhaengen, dann Zustand speichern. Absturz dazwischen: Orders stehen doppelt im Protokoll."""
    api = Boerse()
    def absturz(*a):
        raise OSError("Absturz")
    monkeypatch.setattr(bot, "zustand_speichern", absturz)
    with pytest.raises(OSError):
        lauf(CFG, api, tmp_path, T0)
    monkeypatch.undo()
    lauf(CFG, api, tmp_path, T0 + 5 * 60_000)
    assert len(bot.lesen(tmp_path / "protokoll.csv")) == 4 and zustand(tmp_path)["orders"] == 2
    assert dashboard_daten.bauen(CFG, tmp_path)["kennzahlen"][0]["orders"] == 4


def test_ist_inf03_zwei_instanzen_schreiben_ohne_sperre(tmp_path):
    """Kein Sperrmechanismus: laeuft Instanz B, waehrend A Marktdaten liest, stehen vier Orders im Protokoll, zwei im Zustand."""
    a, b = Boerse(), Boerse()
    a.haken = lambda: lauf(CFG, b, tmp_path, T0 + 1000)
    lauf(CFG, a, tmp_path, T0)
    assert len(bot.lesen(tmp_path / "protokoll.csv")) == 4 and zustand(tmp_path)["orders"] == 2


def test_ist_inf01_ausfall_wird_nicht_gemeldet_und_stop_weit_ueberschritten(tmp_path):
    """Stop 5 %: nach 10 Stunden ohne Lauf wird bei rund 20 % Verlust ausgestiegen, ohne Hinweis auf die Luecke."""
    cfg = {**CFG, "tp": 0.15, "sl": 0.05}
    api = Boerse()
    lauf(cfg, api, tmp_path, T0)
    ein = zustand(tmp_path)["einstieg"]["BBB"]
    api.kurse["BBB"] = 60.0; api.alt["BBB"] = 70.0
    r = lauf(cfg, api, tmp_path, T0 + 10 * H)
    aus = bot.lesen(tmp_path / "protokoll.csv")[-1]
    assert aus["grund"] == "stop" and float(aus["fuellkurs"]) / ein - 1 > 0.19 and r["warnungen"] == []


def test_ist_inf05_fehlender_coin_wird_still_mit_altem_kurs_bewertet(tmp_path):
    api = Boerse()
    lauf(CFG, api, tmp_path, T0)
    api.kurse["BBB"] = 66.0; api.kaputt = {"BBB"}                          # Signal dreht, Abruf scheitert
    r = lauf(CFG, api, tmp_path, T0 + H)
    z = zustand(tmp_path)
    assert r["orders"] == 0 and z["pos"]["BBB"] < 0 and z["kurs"]["BBB"] == pytest.approx(50.0)
    assert sorted(p.name for p in tmp_path.iterdir()) == ["protokoll.csv", "spannen.csv", "stand.csv", "zustand.json"]   # kein Fehlerprotokoll


def test_ist_inf05_verbindungsabbruch_wird_nicht_abgefangen(tmp_path):
    """yubit.py:80-83 faengt URLError, TimeoutError, JSONDecodeError. Ein Abbruch ohne Antwort beendet den ganzen Lauf."""
    def oeffner(req, timeout=20):
        raise http.client.RemoteDisconnected("Remote end closed connection without response")
    api = Yubit(pause=0, oeffner=oeffner)
    with pytest.raises(http.client.RemoteDisconnected):
        bot.schritt(CFG, api, tmp_path, T0, melden=still)


def test_ist_inf05_kerze_bis_zwei_stunden_alt_wird_ohne_hinweis_benutzt(tmp_path):
    api = Boerse(); api.stau_h = 2                                        # Schluss der letzten Kerze 65 min alt
    r = lauf(CFG, api, tmp_path, T0)
    assert r["orders"] == 2 and r["warnungen"] == []


def test_ist_inf09_gleiche_minute_ergibt_doppelte_zeilen(tmp_path):
    api = Boerse()
    lauf(CFG, api, tmp_path, T0); lauf(CFG, api, tmp_path, T0 + 20_000)
    st = bot.lesen(tmp_path / "stand.csv")
    assert len(st) == 2 and st[0]["zeit"] == st[1]["zeit"] and len(bot.lesen(tmp_path / "spannen.csv")) == 4


def test_ist_inf09_abgeschnittene_zeile_laesst_bericht_und_dashboard_abbrechen(tmp_path):
    lauf(CFG, Boerse(), tmp_path, T0)
    p = tmp_path / "protokoll.csv"
    p.write_text(p.read_text()[:-60])
    with pytest.raises(TypeError):
        bot.bericht(CFG, tmp_path)
    with pytest.raises(TypeError):
        dashboard_daten.bauen(CFG, tmp_path)


def test_ist_inf06_board_zeit_stammt_nicht_vom_letzten_lauf(tmp_path):
    """dashboard_daten.py:73 schreibt die Wanduhr; mit STOPP-Datei bleibt 'geschrieben' frisch, obwohl kein Schritt lief."""
    api = Boerse()
    lauf(CFG, api, tmp_path, T0)
    (tmp_path / "STOPP").write_text("")
    assert lauf(CFG, api, tmp_path, T0 + 6 * H) == {"gestoppt": True}
    d = dashboard_daten.bauen(CFG, tmp_path)
    g = dt.datetime.strptime(d["geschrieben"], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=dt.timezone.utc)
    assert d["kennzahlen"][0]["letzter_lauf"] == bot.utc(T0) and d["takt_minuten"] == 60
    assert abs((dt.datetime.now(dt.timezone.utc) - g).total_seconds()) < 120          # Wanduhr, nicht Zeit des letzten Schritts


# ------------------------------------------------- Live-Pfad, nur mit nachgestellter Boerse im Prozess ----
class LiveBoerse(Boerse):
    """Nachgestellte Boerse mit Kontoteil. Kein Netz, kein echter Schluessel: `key`/`secret` sind Platzhalter."""
    key = secret = "nur-test"

    def __init__(self):
        super().__init__()
        self.orders, self.echt, self.fills_kaputt_ab = [], {}, None

    def positionen(self, settle="USDT"):
        return [{"symbol": c + "USDT", "size": abs(q), "positionIdx": 1 if q > 0 else 2} for c, q in self.echt.items() if q]

    def order(self, sym, seite, menge, preis, idx, reduce):
        self.orders.append((sym, seite, float(menge)))
        c = sym.removesuffix("USDT")
        self.echt[c] = self.echt.get(c, 0.0) + float(menge) * (1 if seite == "Buy" else -1)      # Boerse fuellt sofort
        return {"order_id": str(len(self.orders)), "link_id": "x"}

    def fills(self, sym, order_id):
        if self.fills_kaputt_ab and len(self.orders) >= self.fills_kaputt_ab:
            raise ConnectionResetError("Connection reset by peer")
        s, _, m = self.orders[int(order_id) - 1]
        return [{"execQty": m, "execPrice": self.kurse[s.removesuffix("USDT")], "execFee": 0.0}]

    def storno(self, sym, order_id):
        return {}


def test_ist_inf03_live_absturz_nach_order_hinterlaesst_unbekannte_positionen(tmp_path, monkeypatch):
    """bot.py:244 sendet Orders in der Schleife, bot.py:281 speichert den Zustand erst danach. Bricht der Lauf nach der ersten
    Order ab (hier: Verbindungsabbruch beim Abholen der Fills, nicht abgefangen), kennt der Bot seine Positionen nicht mehr
    und verweigert im naechsten Lauf den Handel (bot.py:177-182). Die Positionen bleiben an der Boerse offen."""
    monkeypatch.setenv("YUBIT_LIVE", "ja")
    monkeypatch.setattr(bot.time, "sleep", lambda s: None)
    cfg = {**CFG, "modus": "live", "max_order_usd": 1e9}
    api = LiveBoerse(); api.fills_kaputt_ab = 2
    with pytest.raises(ConnectionResetError):
        lauf(cfg, api, tmp_path, T0)
    assert len(api.orders) == 2 and api.echt["AAA"] > 0 and api.echt["BBB"] < 0          # zwei Orders sind an der Boerse
    assert not (tmp_path / "zustand.json").exists() and not (tmp_path / "protokoll.csv").exists()   # lokal ist nichts festgehalten
    api.fills_kaputt_ab = None
    with pytest.raises(SystemExit) as e:
        lauf(cfg, api, tmp_path, T0 + H)
    assert "weicht vom Protokoll" in str(e.value) and len(api.orders) == 2                 # kein Handel mehr, Positionen bleiben offen
