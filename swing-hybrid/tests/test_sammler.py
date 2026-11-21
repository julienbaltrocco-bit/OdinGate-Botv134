"""Datensammler: Rechenteil an echten Beispielantworten, ganze Durchläufe mit nachgestellten Börsen und einem lokalen Ziel-Repository."""
import csv
import datetime as dt
import gzip
import io
import json
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from sammler import kern, lauf as L

FIX = Path(__file__).parent / "fixtures"
TICKER = json.loads((FIX / "sammler_ticker.json").read_text())
NVDA = json.loads((FIX / "sammler_buch_NVDAUSDT.json").read_text())
BTC = json.loads((FIX / "sammler_buch_BTCUSDT.json").read_text())
T0 = int(dt.datetime(2026, 11, 21, 12, 0, tzinfo=dt.timezone.utc).timestamp())      # volle Stunde, zugleich Lauf-Nummer durch 12 teilbar
assert (T0 // 300) % 12 == 0 and (T0 // 300) % 3 == 0
BAENDER, GROESSEN = [5, 10, 20, 50, 100, 200, 500], [1500, 5000, 25000]


def cfg(ziel=None, **mehr):
    return {"aktiv": True, "coins": ["BTCUSDT", "DOTUSDT"], "reihum": ["NVDAUSDT", "QQQUSDT", "XAUUSDT", "NDX100USDT"], "tiefe_teile": 3, "tiefe_threads": 2,
            "pause_s": 0.0, "alle_jede": 12, "binance": True, "binance_jede": 3, "baender_bp": BAENDER, "groessen_usd": GROESSEN, "frist_s": 30,
            "frist_gesamt_s": 60, "pause_nach_bremse_s": 3600, "platz_mb": 1500, "zweig": "marktdaten", "ziel": str(ziel) if ziel else "", **mehr}


class Boersen:
    """Nachgestellte Börsen: beantwortet die Abrufe des Sammlers aus den Beispielantworten und zählt sie."""

    def __init__(self):
        self.abrufe, self.stoerung = [], {}

    def __call__(self, url, timeout=8.0):
        self.abrufe.append(url)
        for teil, fehler in self.stoerung.items():
            if teil in url:
                raise fehler
        if "fapi/v1/ticker/bookTicker" in url:
            return [{"symbol": s, "bidPrice": "10.0", "bidQty": "5", "askPrice": "10.1", "askQty": "7", "time": 1} for s in ("BTCUSDT", "NVDAUSDT", "XAUUSDT", "FREMDUSDT")]
        if "fapi/v1/premiumIndex" in url:
            return [{"symbol": s, "markPrice": "10.05", "indexPrice": "10.04", "lastFundingRate": "0.0001"} for s in ("BTCUSDT", "NVDAUSDT")]
        if "orderbooks" in url:
            sym = url.split("symbol=")[1]
            d = json.loads(json.dumps(BTC if sym in ("BTCUSDT", "DOTUSDT") else NVDA))
            d["data"]["s"] = sym
            return d
        if url.endswith("/tickers"):
            return TICKER
        raise RuntimeError("unbekannter Abruf " + url)

    def zahl(self, teil):
        return sum(1 for u in self.abrufe if teil in u)


def ziel_anlegen(tmp_path) -> Path:
    ziel = tmp_path / "ziel.git"
    subprocess.run(["git", "init", "-q", "--bare", str(ziel)], check=True)
    return ziel


def im_ziel(ziel: Path, zweig: str) -> dict:
    """{Pfad: Inhalt} aller Dateien des Zweigs im Ziel-Repository (gepackte Dateien entpackt)."""
    namen = subprocess.run(["git", "-C", str(ziel), "ls-tree", "-r", "--name-only", zweig], capture_output=True, text=True).stdout.split()
    out = {}
    for n in namen:
        roh = subprocess.run(["git", "-C", str(ziel), "show", f"{zweig}:{n}"], capture_output=True, check=True).stdout
        out[n] = gzip.decompress(roh).decode() if n.endswith(".gz") else roh.decode()
    return out


def zeilen(text: str) -> list:
    return list(csv.DictReader(io.StringIO(text)))


still = lambda *_: None


# ---------------------------------------------------------------- Rechenteil ----
def test_ticker_zeilen_gruppe_und_alle():
    liste = TICKER["data"]["list"]
    a = kern.ticker_zeilen(liste, 7, {"BTCUSDT", "NVDAUSDT"}, False)
    assert [z["sym"] for z in a] == ["BTCUSDT", "NVDAUSDT"] and set(a[0]) == set(kern.TICKER)
    nvda = next(x for x in liste if x["symbol"] == "NVDAUSDT")
    assert a[1] == {"t": 7, "sym": "NVDAUSDT", "geld": nvda["bidPrice"], "brief": nvda["askPrice"], "mark": nvda["markPrice"],
                    "index": nvda["indexPrice"], "oi": nvda["openInterest"], "funding_ppm": nvda["fundingRate"]}       # Text der Börse, unverändert
    assert len(kern.ticker_zeilen(liste, 7, {"BTCUSDT"}, True)) == len(liste) == 9
    assert kern.ticker_zeilen([{"bidPrice": "1"}, {"symbol": ""}], 7, set(), True) == []                               # ohne Symbol: ausgelassen


def test_tiefe_auswahl_jeder_kontrakt_einmal_je_runde():
    coins, reihum = ["A", "B"], [f"R{i}" for i in range(10)]
    for teile in (1, 3, 4):
        gesehen = []
        for n in range(1000, 1000 + teile):
            wahl = kern.tiefe_auswahl(coins, reihum, n, teile)
            assert wahl[:2] == coins
            gesehen += wahl[2:]
        assert sorted(gesehen) == sorted(reihum)                                                                       # in `teile` Läufen jeder genau einmal
    assert kern.tiefe_auswahl(coins, reihum, 5, 0) == coins + reihum                                                   # unsinnige Einstellung: alles


def test_buch_merkmale_von_hand():
    # Mitte 100. Geld: 99,95 (10 Stück), 99,5 (20), 98 (30). Brief: 100,05 (10), 100,4 (5), 103 (40). Yubit liefert beide Seiten aufsteigend.
    d = {"s": "X", "ts": 1795261644135860, "b": [["98", "30"], ["99.5", "20"], ["99.95", "10"]], "a": [["100.05", "10"], ["100.4", "5"], ["103", "40"]]}
    z = kern.buch_merkmale(d, 42, [10, 50, 200, 500], [500, 1500, 10000])
    assert (z["t"], z["sym"], z["versatz_ms"]) == (42, "X", 1795261644135 - 42000)                                      # Buchzeit minus Laufbeginn, in ms
    assert (z["geld"], z["geld_menge"], z["brief"], z["brief_menge"]) == ("99.95", "10", "100.05", "10")
    assert (z["stufen_geld"], z["stufen_brief"]) == (3, 3)
    nah = lambda x: pytest.approx(x, abs=0.51)                                                                          # Volumen steht in ganzen USDT
    assert int(z["summe_geld"]) == nah(98 * 30 + 99.5 * 20 + 99.95 * 10) and int(z["summe_brief"]) == nah(100.05 * 10 + 100.4 * 5 + 103 * 40)
    assert int(z["g10"]) == nah(999.5) and int(z["b10"]) == nah(1000.5)                                                 # ±0,1 %: nur die beste Stufe
    assert int(z["g50"]) == nah(999.5 + 1990) and int(z["b50"]) == nah(1000.5 + 502)                                    # ±0,5 %: 99,5 und 100,4 gehören dazu
    assert int(z["g200"]) == nah(999.5 + 1990 + 2940) and int(z["b200"]) == nah(1000.5 + 502)                           # ±2 %: 98 ja, 103 nein
    assert int(z["b500"]) == nah(1000.5 + 502 + 4120) and z["g10"].isdigit() and z["summe_brief"].isdigit()
    assert float(z["k500"]) == pytest.approx(5.0) and float(z["v500"]) == pytest.approx(5.0)                             # halbe Spanne
    # Kauf über 1.500 $: 1.000,5 zu 100,05 und 499,5 zu 100,4 -> Durchschnitt = 1500 / (10 + 499,5/100,4)
    schnitt = 1500 / (10 + 499.5 / 100.4)
    assert float(z["k1500"]) == pytest.approx((schnitt / 100 - 1) * 1e4, abs=0.01)
    assert z["k10000"] == "" and z["v10000"] == ""                                                                      # sichtbares Buch reicht nicht
    um = dict(d, b=d["b"][::-1], a=d["a"][::-1])                                                                        # Reihenfolge der Börse darf keine Rolle spielen
    assert kern.buch_merkmale(um, 42, [10, 50, 200, 500], [500, 1500, 10000]) == z
    assert kern.buch_merkmale(dict(d, b=d["b"] + [["97", "0"]]), 42, [10], [500])["stufen_geld"] == 3                   # Stufen ohne Menge zählen nicht
    for kaputt in (dict(d, b=[]), dict(d, a=[]), dict(d, b=[["100.2", "1"]])):
        with pytest.raises(ValueError):
            kern.buch_merkmale(kaputt, 42, [10], [500])


def test_buch_merkmale_echtes_buch():
    z = kern.buch_merkmale(NVDA["data"], 1, BAENDER, GROESSEN)
    assert list(z) == kern.tiefe_spalten(BAENDER, GROESSEN)
    assert float(z["geld"]) < float(z["brief"]) and z["stufen_geld"] == 76 and z["stufen_brief"] == 117
    for seite in "gb":
        werte = [float(z[f"{seite}{b}"]) for b in BAENDER]
        assert werte == sorted(werte) and werte[-1] <= float(z["summe_geld" if seite == "g" else "summe_brief"]) + 1      # breiteres Band, mehr Volumen
    halbe_spanne = (float(z["brief"]) - float(z["geld"])) / (float(z["brief"]) + float(z["geld"])) * 1e4
    kosten = [float(z[f"k{g}"]) for g in GROESSEN]
    assert kosten == sorted(kosten) and kosten[0] >= halbe_spanne - 0.01 and float(z["v1500"]) >= halbe_spanne - 0.01
    assert kern.buch_merkmale(BTC["data"], 1, BAENDER, GROESSEN)["stufen_geld"] == 50


def test_binance_zeilen():
    b = [{"symbol": "NVDAUSDT", "bidPrice": "1", "bidQty": "2", "askPrice": "3", "askQty": "4"}, {"symbol": "FREMD", "bidPrice": "9"}, "kaputt"]
    p = [{"symbol": "NVDAUSDT", "markPrice": "5", "indexPrice": "6", "lastFundingRate": "0.0002"}]
    b[0]["time"] = 1795263300123
    assert kern.binance_zeilen(b, p, 9, {"NVDAUSDT"}) == [{"t": 9, "sym": "NVDAUSDT", "zeit_ms": 1795263300123, "geld": "1", "geld_menge": "2", "brief": "3",
                                                           "brief_menge": "4", "mark": "5", "index": "6", "funding": "0.0002"}]
    assert kern.binance_zeilen(b, [], 9, {"NVDAUSDT"})[0]["mark"] == "" and kern.binance_zeilen(None, None, 9, {"NVDAUSDT"}) == []
    assert kern.binance_zeilen({"code": -1}, "kaputt", 9, {"NVDAUSDT"}) == []                                          # Fehlerantwort statt Liste


def test_beste_stufe_ohne_menge_und_bandgrenze_auf_einer_stufe():
    # Ganz vorn steht je eine Stufe ohne Menge: bester Kurs, Menge, Mitte und Bänder müssen alle von derselben Stufe ausgehen.
    d = {"s": "X", "ts": 0, "b": [["99.95", "10"], ["99.97", "0"]], "a": [["100.03", "0"], ["100.05", "10"]]}
    z = kern.buch_merkmale(d, 1, [10], [500])
    assert (z["geld"], z["geld_menge"], z["brief"], z["brief_menge"]) == ("99.95", "10", "100.05", "10") and z["k500"] == "5" and z["v500"] == "5"
    # Grenze eingeschlossen, auch wenn die Gleitkommarechnung knapp daneben liegt. Mitte m (zwei Nachkommastellen), je eine Stufe genau
    # 50 Basispunkte darunter und darüber; in die Prüfung kommen nur Mitten, bei denen diese Stufen als Kurs mit höchstens vier
    # Nachkommastellen exakt darstellbar sind.
    from fractions import Fraction
    geprueft = 0
    for cent in range(200, 100200, 200):                                         # Mitte 2,00 … 1002,00: 0,5 % davon hat höchstens zwei Nachkommastellen
        m = Fraction(cent, 100)
        unten, oben = m * Fraction(995, 1000), m * Fraction(1005, 1000)
        text = lambda x: f"{float(x):.4f}"
        if Fraction(text(unten)) != unten or Fraction(text(oben)) != oben:
            continue
        innen_g, innen_b = m - Fraction(1, 100), m + Fraction(1, 100)
        d = {"s": "X", "ts": 0, "b": [[text(unten), "1"], [text(innen_g), "1"]], "a": [[text(innen_b), "1"], [text(oben), "1"]]}
        z = kern.buch_merkmale(d, 1, [50], [1])
        assert abs(int(z["g50"]) - float(unten + innen_g)) <= 0.5 and abs(int(z["b50"]) - float(oben + innen_b)) <= 0.5, (float(m), z["g50"], z["b50"])
        geprueft += 1
    assert geprueft >= 400


# ----------------------------------------------------------------- Durchläufe ----
def laeufe(daten, c, api, zeiten, **kw):
    """Mehrere Läufe nacheinander; gibt das Ergebnis des letzten zurück."""
    r = None
    for t in zeiten:
        r = L.lauf(daten, c, t, api, still, **kw)
    return r


def zweige(ziel: Path) -> list:
    return subprocess.run(["git", "-C", str(ziel), "for-each-ref", "--format=%(refname:short)", "refs/heads"], capture_output=True, text=True, check=True).stdout.split()


def test_lauf_schreibt_packt_und_veroeffentlicht(tmp_path):
    ziel, daten, api = ziel_anlegen(tmp_path), tmp_path / "daten", Boersen()
    c = cfg(ziel)
    r = L.lauf(daten, c, T0, api, still)
    # Erster Lauf (Nummer 0): Ticker aller Kontrakte (9), Orderbücher der zwei Coins und jedes dritten der vier übrigen, Binance
    assert r["stat"]["lauf_nr"] == 0 and r["stat"]["ticker"] == 9 and r["stat"]["tiefe_soll"] == r["stat"]["tiefe_ist"] == len(kern.tiefe_auswahl(c["coins"], c["reihum"], 0, 3)) == 4
    assert r["stat"]["binance"] == 3 and r["fehler"] == [] and r["neu"] == {} and r["push_offen"] == []
    assert api.zahl("/tickers") == 1 and api.zahl("orderbooks") == 4 and api.zahl("fapi") == 2
    assert all("depth=500" in u for u in api.abrufe if "orderbooks" in u)
    offen = sorted(p.name for p in (daten / "offen").iterdir())
    assert offen == ["binance_2026-11-21_12.csv", "laeufe_2026-11-21_12.csv", "ticker_2026-11-21_12.csv", "tiefe_2026-11-21_12.csv"]
    assert not list(daten.glob("zweig-*")) and not (daten / "bereit").exists()              # die laufende Stunde bleibt offen
    for i in range(1, 12):                                                                    # Rest der Stunde
        r = L.lauf(daten, c, T0 + 300 * i, api, still)
        assert r["stat"]["lauf_nr"] == i and r["stat"]["ticker"] == 6 and r["stat"]["binance"] == (3 if i % 3 == 0 else 0) and r["neu"] == {}
    r = L.lauf(daten, c, T0 + 3600, api, still)                                               # erster Lauf der nächsten Stunde: packen und pushen
    assert r["neu"] == {"2026-11": ["binance/2026-11-21/12.csv.gz", "laeufe/2026-11-21/12.csv.gz", "ticker/2026-11-21/12.csv.gz", "tiefe/2026-11-21/12.csv.gz"]}
    assert r["push_offen"] == [] and r["fehler"] == []
    d = im_ziel(ziel, "marktdaten-2026-11")
    assert sorted(d) == ["binance/2026-11-21/12.csv.gz", "laeufe/2026-11-21/12.csv.gz", "status.json", "ticker/2026-11-21/12.csv.gz", "tiefe/2026-11-21/12.csv.gz"]
    tk, tf, bn, lf = (zeilen(d[f"{a}/2026-11-21/12.csv.gz"]) for a in ("ticker", "tiefe", "binance", "laeufe"))
    assert len(tk) == 9 + 11 * 6 and list(tk[0]) == kern.TICKER and {z["t"] for z in tk} == {str(T0 + 300 * i) for i in range(12)}
    assert len(lf) == 12 and list(lf[0]) == kern.LAEUFE and all(z["fehler"] == "" for z in lf) and [z["lauf_nr"] for z in lf] == [str(i) for i in range(12)]
    assert len(bn) == 4 * 3 and list(bn[0]) == kern.BINANCE and {z["sym"] for z in bn} == {"BTCUSDT", "NVDAUSDT", "XAUUSDT"} and bn[0]["zeit_ms"] == "1"
    assert list(tf[0]) == kern.tiefe_spalten(BAENDER, GROESSEN)
    je_sym = {s: sum(1 for z in tf if z["sym"] == s) for s in c["coins"] + c["reihum"]}
    assert je_sym == {"BTCUSDT": 12, "DOTUSDT": 12, "NVDAUSDT": 4, "QQQUSDT": 4, "XAUUSDT": 4, "NDX100USDT": 4}   # Coins jeder Lauf, die übrigen jeder dritte
    st = json.loads(d["status.json"])
    assert st["letzter_lauf"]["t"] == T0 + 3600 and st["heute"]["laeufe"] == 13 and st["heute"]["laeufe_mit_fehler"] == 0 and st["voll"] is False
    assert st["zweig"] == "marktdaten-2026-11"
    assert sorted(p.name for p in (daten / "offen").iterdir()) == [f"{a}_2026-11-21_13.csv" for a in ("binance", "laeufe", "ticker", "tiefe")]
    # Veröffentlichtes liegt lokal nicht mehr herum: bereit/ ist leer, im Arbeitsordner steht nur noch status.json
    assert L.bereit_dateien(daten, "2026-11") == [] and sorted(p.name for p in (daten / "zweig-2026-11").iterdir() if p.is_file()) == ["status.json"]
    # zweite Stunde: ein weiterer Commit, die erste bleibt unverändert im Zweig
    laeufe(daten, c, api, [T0 + 300 * i for i in range(13, 25)])
    d2 = im_ziel(ziel, "marktdaten-2026-11")
    assert "ticker/2026-11-21/13.csv.gz" in d2 and all(d2[k] == v for k, v in d.items() if k != "status.json") and len(d2) == len(d) + 4
    log = subprocess.run(["git", "-C", str(ziel), "log", "--format=%an <%ae>|%s", "marktdaten-2026-11"], capture_output=True, text=True).stdout.splitlines()
    assert len(log) == 2 and all(x.startswith("OdinGate Sammler <odingate-sammler@users.noreply.github.com>|Marktdaten bis ") for x in log)
    assert zweige(ziel) == ["marktdaten-2026-11"]


def test_identitaet_kommt_nicht_aus_der_umgebung_des_bots(tmp_path, monkeypatch):
    for k in ("GIT_AUTHOR_NAME", "GIT_COMMITTER_NAME"):
        monkeypatch.setenv(k, "OdinGate Bot (Server)")
    for k in ("GIT_AUTHOR_EMAIL", "GIT_COMMITTER_EMAIL"):
        monkeypatch.setenv(k, "bot@example.invalid")
    ziel, daten, api = ziel_anlegen(tmp_path), tmp_path / "daten", Boersen()
    laeufe(daten, cfg(ziel), api, [T0, T0 + 3600])
    wer = subprocess.run(["git", "-C", str(ziel), "log", "-1", "--format=%an|%ae|%cn|%ce", "marktdaten-2026-11"], capture_output=True, text=True).stdout.strip()
    assert wer == "OdinGate Sammler|odingate-sammler@users.noreply.github.com|OdinGate Sammler|odingate-sammler@users.noreply.github.com"


def test_laufnummer_zaehlt_laeufe_nicht_die_uhrzeit(tmp_path):
    # Auf dem Server beginnt der Sammler gut eine Minute neben dem Fünf-Minuten-Raster und nie gleich: Die Runde hängt am eigenen Zähler.
    daten, api, c = tmp_path / "daten", Boersen(), cfg()
    zeiten = [T0 + 62, T0 + 300 + 58, T0 + 600 + 71, T0 + 900 - 3, T0 + 1500 + 2, T0 + 1500 + 290]     # mal knapp vor, mal nach einer Grenze, eine Lücke
    for i, t in enumerate(zeiten):
        r = L.lauf(daten, c, t, api, still, mit_git=False)
        assert r["stat"]["lauf_nr"] == i and r["stat"]["ticker"] == (9 if i == 0 else 6) and r["stat"]["binance"] == (3 if i % 3 == 0 else 0)
    tf = zeilen((daten / "offen" / "tiefe_2026-11-21_12.csv").read_text())
    assert {s: sum(1 for z in tf if z["sym"] == s) for s in c["reihum"]} == {"NVDAUSDT": 2, "QQQUSDT": 2, "XAUUSDT": 2, "NDX100USDT": 2}
    assert json.loads((daten / "zustand.json").read_text())["lauf_nr"] == 5


def test_takt_einstellungen_wirken(tmp_path):
    api = Boersen()
    c = cfg(alle_jede=2, binance_jede=2, tiefe_teile=2)
    ergebnis = [L.lauf(tmp_path / "d", c, T0 + 300 * i, api, still, mit_git=False)["stat"] for i in range(4)]
    assert [s["ticker"] for s in ergebnis] == [9, 6, 9, 6] and [s["binance"] for s in ergebnis] == [3, 0, 3, 0] and [s["tiefe_soll"] for s in ergebnis] == [4, 4, 4, 4]
    api2 = Boersen()
    assert L.lauf(tmp_path / "ohne", cfg(binance=False), T0, api2, still, mit_git=False)["stat"]["binance"] == 0 and api2.zahl("fapi") == 0


def test_bremse_pausiert_nur_die_betroffene_boerse(tmp_path):
    daten, api, c = tmp_path / "daten", Boersen(), cfg(binance_jede=1)
    api.stoerung["orderbooks"] = L.Gebremst("HTTP 429")
    r = L.lauf(daten, c, T0, api, still, mit_git=False)
    assert r["stat"]["ticker"] == 9 and r["stat"]["tiefe_ist"] == 0 and r["stat"]["binance"] == 3
    assert any("Yubit bremst" in f for f in r["fehler"]) and api.zahl("orderbooks") <= c["tiefe_threads"]              # sofort aufgehört
    assert json.loads((daten / "zustand.json").read_text())["yubit_pause_bis"] == T0 + 3600
    api.stoerung.clear(); api.abrufe.clear()
    r = L.lauf(daten, c, T0 + 900, api, still, mit_git=False)                                                           # innerhalb der Stunde: kein Abruf an Yubit
    assert api.zahl("yubit") == 0 and r["stat"]["ticker"] == 0 and r["stat"]["binance"] == 3 and any("Pause" in f for f in r["fehler"])
    assert L.lauf(daten, c, T0 + 3599, api, still, mit_git=False)["stat"]["ticker"] == 0                                # eine Sekunde vor Ablauf noch nicht
    r = L.lauf(daten, c, T0 + 3600, api, still, mit_git=False)                                                          # nach einer Stunde wieder
    assert r["stat"]["ticker"] == 6 and r["stat"]["tiefe_ist"] == r["stat"]["tiefe_soll"] > 0
    # Binance bremst (auch erst beim zweiten Abruf): Yubit läuft weiter, Binance pausiert eine Stunde
    api.stoerung["premiumIndex"] = L.Gebremst("HTTP 418"); api.abrufe.clear()
    r = L.lauf(daten, c, T0 + 4500, api, still, mit_git=False)
    assert r["stat"]["ticker"] == 6 and r["stat"]["binance"] == 0 and any("Binance bremst" in f for f in r["fehler"]) and api.zahl("fapi") == 2
    api.stoerung.clear(); api.abrufe.clear()
    assert L.lauf(daten, c, T0 + 4500 + 3599, api, still, mit_git=False)["stat"]["binance"] == 0 and api.zahl("fapi") == 0
    assert L.lauf(daten, c, T0 + 4500 + 3600, api, still, mit_git=False)["stat"]["binance"] == 3
    for sperre in (403, 418, 429):                                                                                      # Bremse schon beim Ticker: keine Orderbücher, Pause gemerkt
        api2 = Boersen(); api2.stoerung["/tickers"] = L.Gebremst(f"HTTP {sperre}")
        r = L.lauf(tmp_path / f"d{sperre}", c, T0, api2, still, mit_git=False)
        assert r["stat"]["tiefe_soll"] == 0 and api2.zahl("orderbooks") == 0 and any("Yubit bremst" in f for f in r["fehler"])
        api2.stoerung.clear(); api2.abrufe.clear()
        assert L.lauf(tmp_path / f"d{sperre}", c, T0 + 300, api2, still, mit_git=False)["stat"]["ticker"] == 0 and api2.zahl("yubit") == 0
    # Die Dauer der Pause kommt aus der Einstellung
    api3 = Boersen(); api3.stoerung["/tickers"] = L.Gebremst("HTTP 429")
    L.lauf(tmp_path / "kurz", cfg(pause_nach_bremse_s=600), T0, api3, still, mit_git=False); api3.stoerung.clear()
    assert L.lauf(tmp_path / "kurz", cfg(pause_nach_bremse_s=600), T0 + 599, api3, still, mit_git=False)["stat"]["ticker"] == 0
    assert L.lauf(tmp_path / "kurz", cfg(pause_nach_bremse_s=600), T0 + 600, api3, still, mit_git=False)["stat"]["ticker"] == 6


def test_drosselung_im_antwortkoerper_gilt_als_bremse(tmp_path):
    api = Boersen(); alt = api.__call__
    def hole(url, timeout=8.0):
        return {"code": 10006, "message": "Too many visits. Exceeded the API Rate Limit.", "data": {}} if "orderbooks" in url else alt(url)
    r = L.lauf(tmp_path / "d", cfg(), T0, hole, still, mit_git=False)
    assert r["stat"]["ticker"] == 9 and r["stat"]["tiefe_ist"] == 0 and any("Yubit bremst" in f for f in r["fehler"])
    assert json.loads((tmp_path / "d" / "zustand.json").read_text())["yubit_pause_bis"] == T0 + 3600
    with pytest.raises(RuntimeError) as e:                                                    # ein gewöhnlicher Parameterfehler ist keine Bremse
        L.yubit(lambda url: {"code": 14310001, "message": "params error: limit too large"}, "/x")
    assert not isinstance(e.value, L.Gebremst)
    with pytest.raises(L.Gebremst):
        L.yubit(lambda url: {"code": 1, "message": "request too frequent"}, "/x")


def test_fuenf_fehler_in_folge_beenden_die_runde_und_drei_solche_laeufe_pausieren(tmp_path):
    daten, api = tmp_path / "daten", Boersen()
    c = cfg(reihum=[f"R{i}USDT" for i in range(60)], tiefe_teile=1, tiefe_threads=1)        # 62 Orderbücher je Lauf, nacheinander
    api.stoerung["orderbooks"] = RuntimeError("HTTP 502")
    for i in range(2):
        api.abrufe.clear()
        r = L.lauf(daten, c, T0 + 300 * i, api, still, mit_git=False)
        assert api.zahl("orderbooks") == 5 and r["stat"]["tiefe_ist"] == 0 and any("5 Fehlern in Folge" in f for f in r["fehler"])
        assert "yubit_pause_bis" not in json.loads((daten / "zustand.json").read_text())
    r = L.lauf(daten, c, T0 + 600, api, still, mit_git=False)                                 # dritter gestörter Lauf nacheinander: Pause
    assert any("gestörte Läufe" in f for f in r["fehler"]) and json.loads((daten / "zustand.json").read_text())["yubit_pause_bis"] == T0 + 600 + 3600
    api.abrufe.clear()
    assert L.lauf(daten, c, T0 + 900, api, still, mit_git=False)["stat"]["ticker"] == 0 and api.zahl("yubit") == 0
    # Einzelne Fehler zwischen gelungenen Abrufen beenden die Runde nicht, und ein guter Lauf setzt den Zähler zurück
    api2, d2 = Boersen(), tmp_path / "d2"
    api2.stoerung["orderbooks"] = RuntimeError("HTTP 502")
    L.lauf(d2, c, T0, api2, still, mit_git=False); L.lauf(d2, c, T0 + 300, api2, still, mit_git=False)
    api2.stoerung.clear(); api2.stoerung["symbol=R7USDT"] = RuntimeError("HTTP 500")
    r = L.lauf(d2, c, T0 + 600, api2, still, mit_git=False)
    assert r["stat"]["tiefe_ist"] == 61 and json.loads((d2 / "zustand.json").read_text()).get("yubit_stoerlaeufe") == 0
    api2.stoerung["orderbooks"] = RuntimeError("HTTP 502")
    L.lauf(d2, c, T0 + 900, api2, still, mit_git=False)
    assert "yubit_pause_bis" not in json.loads((d2 / "zustand.json").read_text())             # erst wieder der erste gestörte Lauf


def test_einzelne_fehler_stoeren_den_rest_nicht(tmp_path):
    daten, api, c = tmp_path / "daten", Boersen(), cfg()
    api.stoerung["/tickers"] = RuntimeError("HTTP 500")
    api.stoerung["symbol=NVDAUSDT"] = TimeoutError("zu langsam")
    api.stoerung["premiumIndex"] = RuntimeError("HTTP 502")
    r = L.lauf(daten, c, T0, api, still, mit_git=False)
    soll = kern.tiefe_auswahl(c["coins"], c["reihum"], 0, 3)
    assert "NVDAUSDT" in soll and r["stat"]["ticker"] == 0 and r["stat"]["tiefe_ist"] == len(soll) - 1 and r["stat"]["binance"] == 3
    assert any(f.startswith("ticker:") for f in r["fehler"]) and any("NVDAUSDT" in f for f in r["fehler"]) and any("premiumIndex" in f for f in r["fehler"])
    bn = zeilen((daten / "offen" / "binance_2026-11-21_12.csv").read_text())
    assert len(bn) == 3 and all(z["mark"] == "" for z in bn)                                                            # Spanne da, Mark fehlt
    lf = zeilen((daten / "offen" / "laeufe_2026-11-21_12.csv").read_text())
    assert len(lf) == 1 and "ticker:" in lf[0]["fehler"]
    # Eine unbrauchbare Antwort der Börse (Fehlercode im Körper, auch mit vollständigem Buch) zählt als Fehler, nicht als Daten
    api2 = Boersen(); alt = api2.__call__
    def hole(url, timeout=8.0):
        a = alt(url)
        return dict(a, code=14310001, message="params error") if "orderbooks" in url else a
    r = L.lauf(tmp_path / "d2", c, T0, hole, still, mit_git=False)
    assert r["stat"]["tiefe_ist"] == 0 and r["stat"]["ticker"] == 9 and any("gescheitert" in f for f in r["fehler"])
    assert not (tmp_path / "d2" / "offen" / "tiefe_2026-11-21_12.csv").exists()
    # Antwortet die Börse mit einem anderen Symbol im Buch, steht in der Zeile trotzdem das angefragte, in der Reihenfolge der Auswahl
    api3 = Boersen(); alt3 = api3.__call__
    def fremd(url, timeout=8.0):
        a = alt3(url)
        if "orderbooks" in url:
            a["data"]["s"] = "ANDERS"
        return a
    L.lauf(tmp_path / "d3", c, T0, fremd, still, mit_git=False)
    assert [z["sym"] for z in zeilen((tmp_path / "d3" / "offen" / "tiefe_2026-11-21_12.csv").read_text())] == soll


def test_main_endet_immer_mit_null(tmp_path, monkeypatch, capsys):
    konf = tmp_path / "c.json"; konf.write_text(json.dumps(cfg()))
    monkeypatch.setattr(L, "lauf", lambda *a, **k: (_ for _ in ()).throw(RuntimeError("kaputt")))
    assert L.main(["--daten", str(tmp_path / "d"), "--config", str(konf)]) == 0 and "unerwarteter Fehler" in capsys.readouterr().out
    assert L.main(["--daten", str(tmp_path / "d"), "--config", str(tmp_path / "gibt_es_nicht.json")]) == 0
    monkeypatch.setattr(L, "lauf", lambda *a, **k: (_ for _ in ()).throw(SystemExit(3)))
    assert L.main(["--daten", str(tmp_path / "d"), "--config", str(konf)]) == 0


def test_unvollstaendige_einstellung_und_nicht_beschreibbarer_ordner_ohne_abruf(tmp_path, monkeypatch):
    api = Boersen()
    for kaputt in ({k: v for k, v in cfg().items() if k != "baender_bp"}, cfg(reihum=[]), cfg(coins="BTCUSDT")):
        with pytest.raises(ValueError):
            L.lauf(tmp_path / "a", kaputt, T0, api, still, mit_git=False)
    assert api.abrufe == []
    # Lässt sich der Zustand nicht schreiben (Ordner voll oder schreibgeschützt), wird gar nicht erst abgerufen
    monkeypatch.setattr(L, "zustand_speichern", lambda *a: (_ for _ in ()).throw(OSError("No space left on device")))
    with pytest.raises(OSError):
        L.lauf(tmp_path / "b", cfg(), T0, api, still, mit_git=False)
    assert api.abrufe == []


def test_ausgelieferte_einstellung_ist_lesbar_und_wie_festgelegt():
    c = json.loads((Path(L.__file__).parent / "config.json").read_text())
    assert c["aktiv"] is True and len(c["coins"]) == 10 and len(c["reihum"]) == 222 and len(set(c["coins"] + c["reihum"])) == 232
    assert all(s.endswith("USDT") for s in c["coins"] + c["reihum"]) and {"NDX100USDT", "SP500USDT", "NVDAUSDT", "XAUUSDT"} <= set(c["reihum"])
    assert (c["tiefe_teile"], c["binance_jede"], c["alle_jede"], c["pause_nach_bremse_s"], c["platz_mb"]) == (3, 3, 12, 3600, 1500)
    assert c["tiefe_threads"] <= 2 and c["pause_s"] >= 0.25 and c["frist_s"] <= 45 < c["frist_gesamt_s"] <= 95        # passt in die 120 s von stunde.sh
    assert c["baender_bp"] == BAENDER and c["groessen_usd"] == GROESSEN and "ziel" not in c and c["zweig"] == "odingate-marktdaten"
    assert not [k for k in L.PFLICHT if not c.get(k)]
    je_lauf = len(kern.tiefe_auswahl(c["coins"], c["reihum"], 0, c["tiefe_teile"]))
    assert je_lauf == 84 and 1 + je_lauf <= 90                                                                          # Abrufe an Yubit je Lauf


def test_ziel_ist_ohne_einstellung_das_repository_des_bot_klons(tmp_path, monkeypatch):
    bot = tmp_path / "bot"
    subprocess.run(["git", "init", "-q", str(bot)], check=True)
    subprocess.run(["git", "-C", str(bot), "remote", "add", "origin", "git@example.invalid:irgendwer/repo.git"], check=True)
    (bot / "swing-hybrid" / "sammler").mkdir(parents=True)
    monkeypatch.setattr(L, "HIER", bot / "swing-hybrid" / "sammler")
    assert L.ziel_repo({}) == "git@example.invalid:irgendwer/repo.git" and L.ziel_repo({"ziel": "/x"}) == "/x"
    leer = tmp_path / "kein_repo"; leer.mkdir()
    monkeypatch.setattr(L, "HIER", leer)                                                      # kein Repository: klare Meldung statt eines falschen Ziels
    monkeypatch.setenv("GIT_CEILING_DIRECTORIES", str(tmp_path))
    with pytest.raises(RuntimeError):
        L.ziel_repo({})


def test_ausschalten_und_stopp(tmp_path):
    api = Boersen()
    assert L.lauf(tmp_path / "a", cfg(aktiv=False), T0, api, still, mit_git=False) == {"aus": True}
    (tmp_path / "b").mkdir(); (tmp_path / "b" / "STOPP").write_text("")
    assert L.lauf(tmp_path / "b", cfg(), T0, api, still, mit_git=False) == {"aus": True}
    assert api.abrufe == [] and not (tmp_path / "a" / "offen").exists() and not (tmp_path / "b" / "offen").exists()


def test_zeitgrenze_laesst_orderbuecher_aus(tmp_path):
    api = Boersen()
    r = L.lauf(tmp_path / "d", cfg(frist_s=-1), T0, api, still, mit_git=False)                # Frist schon abgelaufen
    assert r["stat"]["ticker"] == 9 and r["stat"]["tiefe_ist"] == 0 and api.zahl("orderbooks") == 0 and api.zahl("fapi") == 0
    assert any("Zeitgrenze" in f for f in r["fehler"])


def test_gesamtfrist_verschiebt_das_veroeffentlichen(tmp_path):
    ziel, daten, api = ziel_anlegen(tmp_path), tmp_path / "daten", Boersen()
    L.lauf(daten, cfg(ziel), T0, api, still)
    r = L.lauf(daten, cfg(ziel, frist_gesamt_s=-1), T0 + 3600, api, still)                    # keine Zeit mehr für git
    assert r["push_offen"] == ["2026-11"] and any("Zeitgrenze" in f for f in r["fehler"]) and zweige(ziel) == []
    assert len(L.bereit_dateien(daten, "2026-11")) == 4                                       # gepackt liegt es bereit
    r = L.lauf(daten, cfg(ziel), T0 + 3900, api, still)                                       # der nächste Lauf holt es nach, ohne auf die volle Stunde zu warten
    assert r["push_offen"] == [] and "ticker/2026-11-21/12.csv.gz" in im_ziel(ziel, "marktdaten-2026-11")


def test_push_scheitert_und_wird_nachgeholt(tmp_path):
    daten, api = tmp_path / "daten", Boersen()
    ziel = tmp_path / "ziel.git"                                                              # gibt es noch nicht: das Ziel ist nicht erreichbar
    c = cfg(ziel)
    L.lauf(daten, c, T0, api, still)
    r = L.lauf(daten, c, T0 + 3600, api, still)
    assert r["push_offen"] == ["2026-11"] and any("veröffentlichen" in f and "nicht erreichbar" in f for f in r["fehler"])
    assert (daten / "bereit" / "2026-11" / "ticker" / "2026-11-21" / "12.csv.gz").exists() and not (daten / "offen" / "ticker_2026-11-21_12.csv").exists()
    assert not (daten / "zweig-2026-11").exists()                                             # kein halb eingerichteter Ordner bleibt zurück
    for i in range(1, 5):                                                                     # weitere Fehlversuche: kein neuer Zweig, kein Wachstum
        L.lauf(daten, c, T0 + 3600 + 300 * i, api, still)
    assert json.loads((daten / "zustand.json").read_text()).get("zweig_nr", {}).get("2026-11", 1) == 1
    ziel_anlegen(tmp_path)                                                                    # Ziel wieder erreichbar
    r = L.lauf(daten, c, T0 + 3600 + 1500, api, still)                                        # mitten in der Stunde: nichts Neues, aber es wird nachgeholt
    assert r["neu"] == {} and r["push_offen"] == [] and "ticker/2026-11-21/12.csv.gz" in im_ziel(ziel, "marktdaten-2026-11")
    assert len(subprocess.run(["git", "-C", str(ziel), "log", "--format=%s", "marktdaten-2026-11"], capture_output=True, text=True).stdout.splitlines()) == 1


def test_verlorener_ordner_fuehrt_zu_einem_weiteren_zweig_ohne_etwas_zu_ueberschreiben(tmp_path):
    import shutil
    ziel, daten, api = ziel_anlegen(tmp_path), tmp_path / "daten", Boersen()
    c = cfg(ziel)
    laeufe(daten, c, api, [T0, T0 + 3600])
    vorher = im_ziel(ziel, "marktdaten-2026-11")
    shutil.rmtree(daten / "zweig-2026-11")                                                    # Arbeitsordner auf dem Server ging verloren
    r = L.lauf(daten, c, T0 + 7200, api, still)
    assert r["push_offen"] == [] and r["fehler"] == []
    assert zweige(ziel) == ["marktdaten-2026-11", "marktdaten-2026-11-2"]
    assert im_ziel(ziel, "marktdaten-2026-11") == vorher                                      # der erste Zweig ist unangetastet
    zweiter = im_ziel(ziel, "marktdaten-2026-11-2")
    assert sorted(k for k in zweiter if k != "status.json") == [f"{a}/2026-11-21/13.csv.gz" for a in ("laeufe", "ticker", "tiefe")]   # Binance war in dieser Stunde nicht an der Reihe
    assert json.loads(zweiter["status.json"])["zweig"] == "marktdaten-2026-11-2"
    L.lauf(daten, c, T0 + 10800, api, still)                                                  # danach geht es auf dem zweiten Zweig weiter
    assert "ticker/2026-11-21/14.csv.gz" in im_ziel(ziel, "marktdaten-2026-11-2") and zweige(ziel) == ["marktdaten-2026-11", "marktdaten-2026-11-2"]


def test_halb_eingerichteter_ordner_wird_neu_aufgesetzt(tmp_path):
    ziel, daten, api = ziel_anlegen(tmp_path), tmp_path / "daten", Boersen()
    c = cfg(ziel)
    L.lauf(daten, c, T0, api, still)
    ordner = daten / "zweig-2026-11"                                                          # Abbruch zwischen „git init“ und dem Rest der Einrichtung
    ordner.mkdir(parents=True); subprocess.run(["git", "-C", str(ordner), "init", "-q"], check=True)
    r = L.lauf(daten, c, T0 + 3600, api, still)
    assert r["push_offen"] == [] and r["fehler"] == [] and "ticker/2026-11-21/12.csv.gz" in im_ziel(ziel, "marktdaten-2026-11")
    assert (ordner / ".git" / "eingerichtet").read_text().strip() == "marktdaten-2026-11"


def test_abgelehnter_push_fuehrt_nach_drei_versuchen_auf_einen_neuen_zweig(tmp_path):
    ziel, daten, api = ziel_anlegen(tmp_path), tmp_path / "daten", Boersen()
    c = cfg(ziel)
    laeufe(daten, c, api, [T0, T0 + 3600])                                                    # Stunde 12 liegt im Zweig
    fremd = tmp_path / "fremd"                                                                # jemand anderes schreibt in den Daten-Zweig
    subprocess.run(["git", "clone", "-q", "--branch", "marktdaten-2026-11", str(ziel), str(fremd)], check=True)
    (fremd / "fremd.txt").write_text("x")
    for a in (["add", "fremd.txt"], ["-c", "user.name=F", "-c", "user.email=f@example.invalid", "commit", "-q", "-m", "fremd"], ["push", "-q"]):
        subprocess.run(["git", "-C", str(fremd), *a], check=True)
    fremder_stand = im_ziel(ziel, "marktdaten-2026-11")
    r = L.lauf(daten, c, T0 + 7200, api, still)                                               # Stunde 13: Push wird abgelehnt (Zweig beim Ziel ist weiter)
    assert r["push_offen"] == ["2026-11"] and any("git push" in f for f in r["fehler"]) and len(L.bereit_dateien(daten, "2026-11")) == 3
    L.lauf(daten, c, T0 + 7500, api, still)
    r = L.lauf(daten, c, T0 + 7800, api, still)                                               # dritter Versuch: Wechsel auf einen neuen Zweig
    assert any("weiter auf neuem Zweig" in f for f in r["fehler"]) and zweige(ziel) == ["marktdaten-2026-11"]
    r = L.lauf(daten, c, T0 + 8100, api, still)
    assert r["push_offen"] == [] and zweige(ziel) == ["marktdaten-2026-11", "marktdaten-2026-11-2"]
    assert im_ziel(ziel, "marktdaten-2026-11") == fremder_stand                               # nichts überschrieben, nichts gelöscht
    assert "ticker/2026-11-21/13.csv.gz" in im_ziel(ziel, "marktdaten-2026-11-2") and L.bereit_dateien(daten, "2026-11") == []


def test_belegte_datei_wird_nicht_ueberschrieben(tmp_path):
    daten = tmp_path / "daten"
    frei = lambda *a: False
    L.anhaengen(daten, "ticker", T0, kern.TICKER, [{"t": T0, "sym": "A"}])
    assert L.stunden_abschliessen(daten, T0 + 3600, frei) == ({"2026-11": ["ticker/2026-11-21/12.csv.gz"]}, [])
    erste = (daten / "bereit/2026-11/ticker/2026-11-21/12.csv.gz").read_bytes()
    L.anhaengen(daten, "ticker", T0, kern.TICKER, [{"t": T0, "sym": "A"}])                    # derselbe Inhalt noch einmal (Abbruch zwischen Packen und Löschen)
    assert L.stunden_abschliessen(daten, T0 + 3600, frei) == ({"2026-11": ["ticker/2026-11-21/12.csv.gz"]}, [])
    assert (daten / "bereit/2026-11/ticker/2026-11-21/12.csv.gz").read_bytes() == erste and not list((daten / "offen").iterdir())
    for n in (1, 2, 3):                                                                       # anderer Inhalt für dieselbe Stunde: erster, zweiter, dritter Nachtrag
        L.anhaengen(daten, "ticker", T0 + 60 * n, kern.TICKER, [{"t": T0 + 60 * n, "sym": "B"}])
        assert L.stunden_abschliessen(daten, T0 + 3600, frei) == ({"2026-11": [f"ticker/2026-11-21/12_nachtrag{n}.csv.gz"]}, [])
    assert (daten / "bereit/2026-11/ticker/2026-11-21/12.csv.gz").read_bytes() == erste
    assert L.packen(b"abc") == L.packen(b"abc") and gzip.decompress(L.packen(b"abc")) == b"abc" and L.packen(b"abc")[4:8] == b"\x00\x00\x00\x00"   # ohne Zeitstempel
    # Ein Name, der schon veröffentlicht ist, wird nicht noch einmal vergeben (auch wenn in bereit/ nichts mehr liegt)
    d2 = tmp_path / "d2"
    L.anhaengen(d2, "ticker", T0, kern.TICKER, [{"t": T0, "sym": "C"}])
    assert L.stunden_abschliessen(d2, T0 + 3600, lambda daten, monat, rel: rel.endswith("/12.csv.gz")) == ({"2026-11": ["ticker/2026-11-21/12_nachtrag1.csv.gz"]}, [])
    # Leere Tabelle: keine Datei. Eine unlesbare Datei in bereit/ hält die übrigen Tabellen nicht auf.
    L.anhaengen(d2, "binance", T0, kern.BINANCE, [])
    assert not (d2 / "offen" / "binance_2026-11-21_12.csv").exists()
    L.anhaengen(d2, "tiefe", T0 + 3600, ["t", "sym"], [{"t": 1, "sym": "D"}]); L.anhaengen(d2, "laeufe", T0 + 3600, ["t"], [{"t": 1}])
    (d2 / "bereit/2026-11/tiefe/2026-11-21").mkdir(parents=True); (d2 / "bereit/2026-11/tiefe/2026-11-21/13.csv.gz").write_bytes(b"kein gzip")
    neu, fehler = L.stunden_abschliessen(d2, T0 + 7200, frei)
    assert neu == {"2026-11": ["laeufe/2026-11-21/13.csv.gz", "tiefe/2026-11-21/13.csv.gz"]} and fehler == []
    assert gzip.decompress((d2 / "bereit/2026-11/tiefe/2026-11-21/13.csv.gz").read_bytes()) == b"t,sym\n1,D\n"
    assert (d2 / "bereit/2026-11/tiefe/2026-11-21/13.csv.gz.kaputt").exists()


def test_schon_veroeffentlichte_stunde_wird_bei_spaeten_zeilen_zum_nachtrag(tmp_path):
    ziel, daten, api = ziel_anlegen(tmp_path), tmp_path / "daten", Boersen()
    c = cfg(ziel)
    laeufe(daten, c, api, [T0, T0 + 3600])
    erste = im_ziel(ziel, "marktdaten-2026-11")["ticker/2026-11-21/12.csv.gz"]
    L.anhaengen(daten, "ticker", T0, kern.TICKER, [{"t": T0 + 1, "sym": "SPAET"}])            # Zeilen für die schon veröffentlichte Stunde 12 tauchen noch auf
    L.lauf(daten, c, T0 + 3900, api, still)
    d = im_ziel(ziel, "marktdaten-2026-11")
    assert d["ticker/2026-11-21/12.csv.gz"] == erste and "SPAET" in d["ticker/2026-11-21/12_nachtrag1.csv.gz"]


def test_anhaengen_flickt_halbe_zeilen_und_beginnt_bei_anderen_spalten_neu(tmp_path):
    daten = tmp_path / "daten"
    L.anhaengen(daten, "ticker", T0, ["t", "sym"], [{"t": 1, "sym": "A"}])
    datei = daten / "offen" / "ticker_2026-11-21_12.csv"
    assert datei.read_bytes() == b"t,sym\n1,A\n"                                              # Unix-Zeilenende, Kopfzeile einmal
    with open(datei, "ab") as f:
        f.write(b"2,HAL")                                                                     # Abbruch mitten in der Zeile
    L.anhaengen(daten, "ticker", T0 + 300, ["t", "sym"], [{"t": 3, "sym": "C"}])
    assert datei.read_bytes() == b"t,sym\n1,A\n2,HAL\n3,C\n"                                  # die halbe Zeile ist abgeschlossen, die neue steht für sich
    L.anhaengen(daten, "ticker", T0 + 600, ["t", "sym", "neu"], [{"t": 4, "sym": "D", "neu": 9}])   # Einstellung geändert: andere Spalten
    assert datei.read_bytes() == b"t,sym,neu\n4,D,9\n"
    assert (daten / "offen" / "ticker-alt1_2026-11-21_12.csv").read_bytes() == b"t,sym\n1,A\n2,HAL\n3,C\n"
    neu, fehler = L.stunden_abschliessen(daten, T0 + 3600, lambda *a: False)                  # beide Dateien werden gepackt, jede unter eigenem Namen
    assert neu == {"2026-11": ["ticker-alt1/2026-11-21/12.csv.gz", "ticker/2026-11-21/12.csv.gz"]} and fehler == []
    leer = daten / "offen" / "laeufe_2026-11-21_12.csv"; leer.write_bytes(b"")                 # leere Datei (Abbruch vor dem ersten Byte): Kopfzeile kommt
    L.anhaengen(daten, "laeufe", T0, ["t"], [{"t": 5}])
    assert leer.read_bytes() == b"t\n5\n"


def test_dateien_und_zeiten_in_utc_auch_bei_anderer_ortszeit(tmp_path):
    import os, time
    alt = os.environ.get("TZ")
    os.environ["TZ"] = "XXX-9"; time.tzset()                                                  # Ortszeit neun Stunden vor UTC
    try:
        L.anhaengen(tmp_path, "ticker", T0, ["t"], [{"t": 1}])
        assert (tmp_path / "offen" / "ticker_2026-11-21_12.csv").exists() and L.zeitteile(T0) == ("2026-11", "2026-11-21", "12")
    finally:
        if alt is None:
            os.environ.pop("TZ", None)
        else:
            os.environ["TZ"] = alt
        time.tzset()


def test_monatswechsel_und_aufraeumen(tmp_path):
    ziel, daten, api = ziel_anlegen(tmp_path), tmp_path / "daten", Boersen()
    c = cfg(ziel)
    ende_nov = int(dt.datetime(2026, 11, 30, 23, 55, tzinfo=dt.timezone.utc).timestamp())
    L.lauf(daten, c, ende_nov, api, still)
    r = L.lauf(daten, c, ende_nov + 300, api, still)                                          # 01.12. 00:00: die letzte November-Stunde gehört in den November-Zweig
    assert list(r["neu"]) == ["2026-11"] and "ticker/2026-11-30/23.csv.gz" in im_ziel(ziel, "marktdaten-2026-11")
    L.lauf(daten, c, ende_nov + 300 + 3600, api, still)
    assert "ticker/2026-12-01/00.csv.gz" in im_ziel(ziel, "marktdaten-2026-12")
    assert (daten / "zweig-2026-11").exists()                                                 # der Vormonat bleibt liegen
    silvester = int(dt.datetime(2026, 12, 31, 12, 0, tzinfo=dt.timezone.utc).timestamp())    # am 31. ist der Vormonat weiterhin November
    L.lauf(daten, c, silvester, api, still)
    assert (daten / "zweig-2026-11").exists()
    januar = int(dt.datetime(2027, 1, 1, 1, 0, tzinfo=dt.timezone.utc).timestamp())
    laeufe(daten, c, api, [januar, januar + 3600])
    assert not (daten / "zweig-2026-11").exists() and (daten / "zweig-2026-12").exists() and (daten / "zweig-2027-01").exists()
    # Ein alter Monat, für den noch etwas bereitliegt, wird nicht entfernt (sein Ordner und seine Dateien bleiben)
    (daten / "zweig-2026-09").mkdir(); (daten / "bereit" / "2026-09" / "ticker" / "2026-09-30").mkdir(parents=True)
    (daten / "bereit" / "2026-09" / "ticker" / "2026-09-30" / "23.csv.gz").write_bytes(L.packen(b"t\n1\n"))
    L.alte_monate_entfernen(daten, januar, L.monate_bereit(daten))
    assert (daten / "zweig-2026-09").exists() and L.bereit_dateien(daten, "2026-09")
    r = L.lauf(daten, c, januar + 3900, api, still)                                           # der Lauf veröffentlicht es noch und räumt danach auf
    assert "ticker/2026-09-30/23.csv.gz" in im_ziel(ziel, "marktdaten-2026-09") and r["push_offen"] == []
    assert not (daten / "zweig-2026-09").exists() and not (daten / "bereit" / "2026-09").exists()


def test_abbruch_am_monatswechsel_verliert_nichts(tmp_path, monkeypatch):
    # Der Lauf packt die letzte Stunde des Monats und wird dann hart beendet (hier: das Veröffentlichen wirft). Was bereitliegt, bleibt
    # liegen und geht mit dem nächsten Lauf hinaus, auch wenn für den alten Monat kein Stundenabschluss mehr kommt.
    ziel, daten, api = ziel_anlegen(tmp_path), tmp_path / "daten", Boersen()
    c = cfg(ziel)
    ende_nov = int(dt.datetime(2026, 11, 30, 23, 55, tzinfo=dt.timezone.utc).timestamp())
    L.lauf(daten, c, ende_nov, api, still)
    echt = L.veroeffentlichen
    monkeypatch.setattr(L, "veroeffentlichen", lambda *a, **k: (_ for _ in ()).throw(KeyboardInterrupt()))
    with pytest.raises(KeyboardInterrupt):
        L.lauf(daten, c, ende_nov + 300, api, still)
    monkeypatch.setattr(L, "veroeffentlichen", echt)
    (daten / "zustand.json").unlink()                                                         # selbst ohne Merkzettel
    r = L.lauf(daten, c, ende_nov + 600, api, still)
    assert r["push_offen"] == [] and "ticker/2026-11-30/23.csv.gz" in im_ziel(ziel, "marktdaten-2026-11")


def test_platzgrenze_haelt_das_mitschreiben_an_und_loest_sich_von_selbst(tmp_path):
    ziel, daten, api = ziel_anlegen(tmp_path), tmp_path / "daten", Boersen()
    L.lauf(daten, cfg(ziel), T0, api, still)
    api.abrufe.clear()
    r = L.lauf(daten, cfg(ziel, platz_mb=-1, binance_jede=1), T0 + 3600, api, still)          # Grenze überschritten: nichts Neues, auch nicht von Binance
    assert api.abrufe == [] and r["stat"]["ticker"] == 0 and any("Platzgrenze" in f for f in r["fehler"])
    assert not (daten / "offen" / "laeufe_2026-11-21_13.csv").exists()                        # auch keine Laufzeile
    d = im_ziel(ziel, "marktdaten-2026-11")                                                   # was schon mitgeschrieben war, wird noch veröffentlicht
    assert "ticker/2026-11-21/12.csv.gz" in d and json.loads(d["status.json"])["voll"] is True
    r = L.lauf(daten, cfg(ziel), T0 + 3900, api, still)                                       # wieder Platz: es geht von selbst weiter
    assert r["stat"]["ticker"] == 6 and not any("Platzgrenze" in f for f in r["fehler"])
    (tmp_path / "gross").mkdir(); (tmp_path / "gross" / "x").write_bytes(b"0" * 2_500_000)
    assert 2.4 < L.platz_mb(tmp_path / "gross") < 2.6                                          # gemessen wird in Megabyte


def test_liegengebliebenes_und_sperren_werden_nachgeholt(tmp_path):
    ziel, daten, api = ziel_anlegen(tmp_path), tmp_path / "daten", Boersen()
    c = cfg(ziel)
    laeufe(daten, c, api, [T0, T0 + 3600])                                                    # Stunde 12 veröffentlicht
    ordner = daten / "zweig-2026-11"
    # Ein abgebrochener Lauf hat Stunde 13 gepackt, aber nicht veröffentlicht, und eine Sperre sowie eine halbe Datei hinterlassen
    liegen = daten / "bereit" / "2026-11" / "ticker" / "2026-11-21"
    liegen.mkdir(parents=True, exist_ok=True); (liegen / "13.csv.gz").write_bytes(L.packen(b"t,sym\n1,LIEGENGEBLIEBEN\n")); (liegen / "14.csv.gz.teil").write_bytes(b"halb")
    (ordner / ".git" / "index.lock").write_text("")
    r = L.lauf(daten, c, T0 + 3900, api, still)                                               # mitten in der Stunde: nichts Neues zu packen, aber es liegt etwas bereit
    assert r["neu"] == {} and r["push_offen"] == [] and r["fehler"] == []
    d = im_ziel(ziel, "marktdaten-2026-11")
    assert "LIEGENGEBLIEBEN" in d["ticker/2026-11-21/13.csv.gz"] and not any(n.endswith(".teil") for n in d)
    assert "ticker/2026-11-21/12.csv.gz" in d and not (ordner / ".git" / "index.lock").exists()
    L.lauf(daten, c, T0 + 7500, api, still)                                                   # die echte Stunde 13 kommt als Nachtrag dazu, nichts wird überschrieben
    d = im_ziel(ziel, "marktdaten-2026-11")
    assert "LIEGENGEBLIEBEN" in d["ticker/2026-11-21/13.csv.gz"] and "NVDAUSDT" in d["ticker/2026-11-21/13_nachtrag1.csv.gz"]


def test_pause_und_hoechstzahl_gleichzeitiger_abrufe(tmp_path):
    import threading, time
    aktiv, hoechst, schloss, api = [0], [0], threading.Lock(), Boersen()
    def hole(url, timeout=8.0):
        if "orderbooks" in url:
            with schloss:
                aktiv[0] += 1; hoechst[0] = max(hoechst[0], aktiv[0])
            time.sleep(0.02)
            with schloss:
                aktiv[0] -= 1
        return api(url)
    c = cfg(reihum=[f"R{i}USDT" for i in range(20)], tiefe_teile=1, tiefe_threads=9, pause_s=0.0)
    L.lauf(tmp_path / "a", c, T0, hole, still, mit_git=False)
    assert hoechst[0] <= 4                                                                    # nie mehr als vier gleichzeitig, was auch eingestellt ist
    hoechst[0] = 0
    L.lauf(tmp_path / "b", cfg(tiefe_threads=1), T0, hole, still, mit_git=False)
    assert hoechst[0] == 1
    beginn = time.monotonic()
    L.lauf(tmp_path / "c", cfg(tiefe_threads=1, pause_s=0.1), T0, api, still, mit_git=False)  # vier Orderbücher nacheinander mit je 0,1 s Pause
    assert time.monotonic() - beginn >= 0.4


def test_holen_entpackt_erkennt_die_bremse_und_begrenzt_die_dauer(monkeypatch):
    import urllib.error

    class Antwort(io.BytesIO):
        headers = {"Content-Encoding": "gzip"}
        def __enter__(self): return self
        def __exit__(self, *a): return False
    gesehen = []
    def oeffner(req, timeout=0):
        gesehen.append(req); return Antwort(gzip.compress(b'{"code":0}'))
    monkeypatch.setattr("urllib.request.urlopen", oeffner)
    assert L.holen("https://example.invalid/x") == {"code": 0}
    kopf = {k.lower(): v for k, v in gesehen[0].header_items()}
    assert kopf["user-agent"] == "marktdaten/1.0" and kopf["accept-encoding"] == "gzip"
    for code, art in ((429, L.Gebremst), (418, L.Gebremst), (403, L.Gebremst), (500, RuntimeError)):
        def wirft(req, timeout=0, code=code):
            raise urllib.error.HTTPError("u", code, "x", {}, None)
        monkeypatch.setattr("urllib.request.urlopen", wirft)
        with pytest.raises(art) as e:
            L.holen("https://example.invalid/x")
        assert isinstance(e.value, L.Gebremst) == (art is L.Gebremst)

    class Troepfelt:                                                                          # jede Leseportion kommt an, aber insgesamt dauert es zu lange
        headers = {}
        def __init__(self): self.n = 0
        def __enter__(self): return self
        def __exit__(self, *a): return False
        def read(self, n):
            self.n += 1; uhr[0] += 5.0
            return b"x" if self.n < 100 else b""
    uhr = [0.0]
    monkeypatch.setattr(L.time, "monotonic", lambda: uhr[0])
    monkeypatch.setattr("urllib.request.urlopen", lambda req, timeout=0: Troepfelt())
    with pytest.raises(TimeoutError):
        L.holen("https://example.invalid/x", timeout=8.0, hoechstens=12.0)
    assert uhr[0] <= 20.0                                                                     # abgebrochen nach wenigen Portionen, nicht nach hundert


def test_kopfzeilen_woertlich(tmp_path):
    # Die Spaltennamen sind Teil der Daten: Eine stille Änderung würde alte und neue Dateien unvergleichbar machen.
    assert kern.TICKER == ["t", "sym", "geld", "brief", "mark", "index", "oi", "funding_ppm"]
    assert kern.BINANCE == ["t", "sym", "zeit_ms", "geld", "geld_menge", "brief", "brief_menge", "mark", "index", "funding"]
    assert kern.LAEUFE == ["t", "lauf_nr", "boersenzeit_ms", "ticker", "tiefe_soll", "tiefe_ist", "binance", "dauer_s", "fehler"]
    assert kern.tiefe_spalten([20, 100], [1500]) == ["t", "sym", "versatz_ms", "geld", "geld_menge", "brief", "brief_menge", "stufen_geld", "stufen_brief",
                                                     "summe_geld", "summe_brief", "g20", "g100", "b20", "b100", "k1500", "v1500"]
    api = Boersen()
    L.lauf(tmp_path, cfg(), T0, api, still, mit_git=False)
    erste = lambda art: (tmp_path / "offen" / f"{art}_2026-11-21_12.csv").read_text().splitlines()[0]
    assert erste("ticker") == "t,sym,geld,brief,mark,index,oi,funding_ppm" and erste("binance") == "t,sym,zeit_ms,geld,geld_menge,brief,brief_menge,mark,index,funding"
    assert erste("laeufe") == "t,lauf_nr,boersenzeit_ms,ticker,tiefe_soll,tiefe_ist,binance,dauer_s,fehler"
    lf = zeilen((tmp_path / "offen" / "laeufe_2026-11-21_12.csv").read_text())[0]
    assert lf["boersenzeit_ms"] == str(TICKER["time"]) and lf["t"] == str(T0) and lf["lauf_nr"] == "0"


def test_tageszaehler_und_lauf_ohne_git(tmp_path):
    ziel, daten, api = ziel_anlegen(tmp_path), tmp_path / "daten", Boersen()
    c = cfg(ziel)
    api.stoerung["symbol=DOTUSDT"] = RuntimeError("HTTP 500")
    laeufe(daten, c, api, [T0, T0 + 300], mit_git=False)
    api.stoerung.clear()
    r = L.lauf(daten, c, T0 + 3600, api, still, mit_git=False)                                # ohne git: gepackt wird, veröffentlicht nicht
    z = json.loads((daten / "zustand.json").read_text())
    assert z["heute"] == {"tag": "2026-11-21", "laeufe": 3, "ticker": 9 + 6 + 6, "tiefe": 3 + 2 + 3, "binance": 3, "laeufe_mit_fehler": 2}
    assert r["neu"] == {"2026-11": [f"{a}/2026-11-21/12.csv.gz" for a in ("binance", "laeufe", "ticker", "tiefe")]} and r["push_offen"] == ["2026-11"]
    assert len(L.bereit_dateien(daten, "2026-11")) == 4 and zweige(ziel) == [] and not (daten / "zweig-2026-11").exists()
    morgen = T0 + 86400
    L.lauf(daten, c, morgen, api, still, mit_git=False)                                       # neuer Tag: Zähler beginnt von vorn
    assert json.loads((daten / "zustand.json").read_text())["heute"] == {"tag": "2026-11-22", "laeufe": 1, "ticker": 6, "tiefe": 4, "binance": 3, "laeufe_mit_fehler": 0}
    (daten / "zustand.json").write_text("kein json")                                          # unlesbarer Zustand hält den Sammler nicht an
    assert L.lauf(daten, c, morgen + 300, api, still, mit_git=False)["stat"]["lauf_nr"] == 0
