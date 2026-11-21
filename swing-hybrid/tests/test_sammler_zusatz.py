"""Zusatztests zum Datensammler aus der Mutationsprüfung (Commit 9acb0fcc): Jeder Test schließt eine Lücke, durch die ein
eingebauter Fehler unbemerkt durch tests/test_sammler.py kam. Welcher Fehler zu welchem Test gehört, steht am Test.
Eigenständige Datei; nimmt nur die Hilfen (nachgestellte Börsen, Einstellung, Ziel-Repository) aus test_sammler.py.

Nach der Gegenprüfung wurde das Veröffentlichen umgebaut (Ordner bereit/, eigener Laufzähler, neue Spalten zeit_ms und lauf_nr).
16 der ursprünglich 42 Tests beschrieben den alten Aufbau; ihr Gegenstand wird jetzt in test_sammler.py mit dem neuen Aufbau
geprüft (Kopfzeilen, Pausen und ihre Dauer, Platzgrenze, Gesamtfrist, Nachträge, Monatswechsel, UTC, Tageszähler, Lauf ohne git).
Hier stehen die 26 Tests, die unverändert gelten."""
import datetime as dt
import gzip
import json
import os
import subprocess
import sys
import threading
import time
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from sammler import kern, lauf as L
from test_sammler import BAENDER, GROESSEN, NVDA, T0, TICKER, Boersen, cfg, im_ziel, still, zeilen, ziel_anlegen

STUNDE = "2026-11-21_12"


def zustand(daten: Path) -> dict:
    return json.loads((daten / "zustand.json").read_text())


def zweige(repo: Path) -> list:
    return subprocess.run(["git", "-C", str(repo), "for-each-ref", "--format=%(refname:short)", "refs/heads"], capture_output=True, text=True, check=True).stdout.split()


def offen(daten: Path, art: str, stunde: str = STUNDE) -> list:
    return zeilen((daten / "offen" / f"{art}_{stunde}.csv").read_text())


def stempel(*a) -> int:
    return int(dt.datetime(*a, tzinfo=dt.timezone.utc).timestamp())


@pytest.fixture
def ortszeit_plus_neun():
    """Ortszeit des Rechners neun Stunden vor UTC (wie Tokio); der Sammler muss trotzdem in UTC ablegen."""
    alt = os.environ.get("TZ")
    os.environ["TZ"] = "XXX-9"
    time.tzset()
    try:
        assert dt.datetime.fromtimestamp(T0).hour == 21                                       # die Umstellung wirkt
        yield
    finally:
        if alt is None:
            os.environ.pop("TZ", None)
        else:
            os.environ["TZ"] = alt
        time.tzset()


# ---------------------------------------------------------------- Rechenteil ----


def test_briefseite_ohne_menge_zaehlt_nicht():
    # Mutant K23: test_sammler.py prüft Stufen ohne Menge nur auf der Geldseite.
    d = {"s": "X", "ts": 0, "b": [["99.95", "10"]], "a": [["100.05", "10"], ["100.4", "5"], ["101", "0"]]}
    z = kern.buch_merkmale(d, 0, [500], [500])
    assert z["stufen_brief"] == 2 and z["stufen_geld"] == 1


def test_gleicher_geld_und_briefkurs_gilt_als_gekreuzt():
    # Mutant K25: die Grenze (Geld gleich Brief) war ungeprüft.
    with pytest.raises(ValueError):
        kern.buch_merkmale({"s": "X", "ts": 0, "b": [["100", "1"]], "a": [["100", "1"]]}, 0, [10], [50])


def test_mitte_und_baender_bei_weiter_spanne():
    # Mutanten K28 (geometrische Mitte), K51, K52 (Bänder um den besten Kurs statt um die Mitte): bei 10 Basispunkten Spanne
    # wie im Handbeispiel von test_sammler.py fällt beides nicht auf, bei einem dünnen Buch mit weiter Spanne schon.
    d = {"s": "X", "ts": 0, "b": [["80", "10"], ["88.5", "10"], ["90", "10"]], "a": [["110", "10"], ["111.5", "10"], ["125", "10"]]}
    z = kern.buch_merkmale(d, 0, [1100, 2100], [500])                                         # Mitte 100
    assert (z["g1100"], z["b1100"]) == ("900", "1100")                                        # ±11 %: 89 bis 111 -> nur die besten Stufen
    assert (z["g2100"], z["b2100"]) == ("2585", "2215")                                       # ±21 %: 79 bis 121 -> Geld alle drei, Brief zwei
    assert (z["k500"], z["v500"]) == ("1000", "1000")                                         # 110 und 90 gegen 100: je 10 % = 1.000 Basispunkte


def test_mengen_der_besten_stufen():
    # Mutanten K36, K37: im Handbeispiel von test_sammler.py haben beide besten Stufen dieselbe Menge (10).
    d = {"s": "X", "ts": 0, "b": [["99.95", "3"], ["99.5", "20"]], "a": [["100.05", "7"], ["100.4", "5"]]}
    z = kern.buch_merkmale(d, 0, [10], [100])
    assert (z["geld"], z["geld_menge"], z["brief"], z["brief_menge"]) == ("99.95", "3", "100.05", "7")
    z = kern.buch_merkmale(NVDA["data"], 1, BAENDER, GROESSEN)                                # echtes Buch: Text der Börse
    assert (z["geld"], z["geld_menge"], z["brief"], z["brief_menge"]) == ("129.19", "2.60", "129.22", "97")


def test_briefband_grenze_gehoert_dazu():
    # Mutant K43: auf der Geldseite liegt im Handbeispiel eine Stufe genau auf der Grenze, auf der Briefseite nicht.
    # Mitte 100, Band 100 Basispunkte: 99 und 101 liegen genau auf der Grenze (in Gleitkomma hier exakt 99.0 und 101.0).
    assert 100 * (1 + 100 / 1e4) == 101.0 and 100 * (1 - 100 / 1e4) == 99.0
    d = {"s": "X", "ts": 0, "b": [["99", "2"], ["98", "1"]], "a": [["101", "3"], ["102", "1"]]}
    z = kern.buch_merkmale(d, 0, [100, 200], [100])
    assert (z["g100"], z["b100"], z["g200"], z["b200"]) == ("198", "303", "296", "405")


def test_buch_reicht_knapp_nicht():
    # Mutant K66: 'reicht nicht' war nur weit weg von der Grenze geprüft (5.622 gegen 10.000 USDT).
    d = {"s": "X", "ts": 0, "b": [["99", "15.15"]], "a": [["100", "14.995"]]}                 # 1.499,85 und 1.499,50 USDT
    z = kern.buch_merkmale(d, 0, [10], [1500])
    assert z["k1500"] == "" and z["v1500"] == ""
    d = {"s": "X", "ts": 0, "b": [["99", "15.16"]], "a": [["100", "15"]]}                     # 1.500,84 und genau 1.500 USDT
    z = kern.buch_merkmale(d, 0, [10], [1500])
    assert z["k1500"] == "50.25" and z["v1500"] == "50.25"                                    # Mitte 99,5


def test_kosten_als_text_ohne_ueberfluessige_nullen():
    # Mutanten K68 ("5.00"), K69 (rstrip("0.") macht aus "10.00" eine "1"): test_sammler.py liest die Kosten nur als Zahl.
    d = {"s": "X", "ts": 0, "b": [["99.95", "10"]], "a": [["100.05", "10"]]}
    z = kern.buch_merkmale(d, 0, [10], [500])
    assert (z["k500"], z["v500"]) == ("5", "5")
    d = {"s": "X", "ts": 0, "b": [["99.9", "100"]], "a": [["100.1", "100"]]}                  # halbe Spanne 10 Basispunkte
    z = kern.buch_merkmale(d, 0, [10], [500])
    assert (z["k500"], z["v500"]) == ("10", "10")
    d = {"s": "X", "ts": 0, "b": [["99", "100"]], "a": [["101", "100"]]}                      # 100 Basispunkte
    assert kern.buch_merkmale(d, 0, [10], [500])["k500"] == "100"
    d = {"s": "X", "ts": 0, "b": [["99.875", "100"]], "a": [["100.125", "100"]]}              # 12,5 Basispunkte
    assert kern.buch_merkmale(d, 0, [10], [500])["k500"] == "12.5"


def test_volumen_wird_gerundet_nicht_abgeschnitten():
    # Mutant K70: test_sammler.py lässt beim Volumen eine Abweichung von 0,51 zu; Abschneiden fiel deshalb nicht auf.
    d = {"s": "X", "ts": 0, "b": [["10", "0.07"]], "a": [["10.2", "0.17"]]}                   # 0,70 und 1,734 USDT
    z = kern.buch_merkmale(d, 0, [500], [1])
    assert (z["summe_geld"], z["summe_brief"], z["g500"], z["b500"]) == ("1", "2", "1", "2")


# ------------------------------------------------------------------- Abruf ----


def test_zeile_traegt_das_angefragte_symbol(tmp_path):
    # Mutant L102: die nachgestellte Börse von test_sammler.py antwortet immer mit dem angefragten Symbol im Feld "s".
    api = Boersen(); alt = api.__call__

    def hole(url, timeout=8.0):
        a = alt(url)
        if "orderbooks" in url:
            a["data"]["s"] = "ANDERS"
        return a
    c = cfg()
    r = L.lauf(tmp_path, c, T0, hole, still, mit_git=False)
    assert r["fehler"] == [] and [z["sym"] for z in offen(tmp_path, "tiefe")] == kern.tiefe_auswahl(c["coins"], c["reihum"], T0 // 300, 3)


def test_tiefe_zeilen_stehen_in_der_reihenfolge_der_auswahl(tmp_path):
    # Mutant L103 (Sortieren entfällt): die erste Antwort kommt hier als letzte.
    api = Boersen(); alt = api.__call__

    def hole(url, timeout=8.0):
        if url.endswith("symbol=BTCUSDT"):
            time.sleep(0.4)
        return alt(url)
    c = cfg(tiefe_teile=1)
    L.lauf(tmp_path, c, T0, hole, still, mit_git=False)
    assert [z["sym"] for z in offen(tmp_path, "tiefe")] == c["coins"] + c["reihum"]


def test_nach_jedem_orderbuch_abruf_wird_pausiert(tmp_path, monkeypatch):
    # Mutant L105 (Pause entfällt): test_sammler.py läuft durchweg mit pause_s = 0.
    pausen = []
    monkeypatch.setattr(L.time, "sleep", pausen.append)
    r = L.lauf(tmp_path, cfg(pause_s=0.25), T0, Boersen(), still, mit_git=False)
    assert r["stat"]["tiefe_soll"] == 4 and pausen == [0.25] * 4


class Gezaehlt(Boersen):
    """Nachgestellte Börse, die mitzählt, wie viele Orderbuch-Abrufe gleichzeitig laufen."""

    def __init__(self, dauer: float):
        super().__init__()
        self.schloss, self.laufend, self.hoechst, self.dauer = threading.Lock(), 0, 0, dauer

    def __call__(self, url, timeout=8.0):
        if "orderbooks" not in url:
            return super().__call__(url, timeout)
        with self.schloss:
            self.laufend += 1; self.hoechst = max(self.hoechst, self.laufend)
        try:
            time.sleep(self.dauer)
            return super().__call__(url, timeout)
        finally:
            with self.schloss:
                self.laufend -= 1


def test_gleichzeitige_abrufe_wie_eingestellt_und_hoechstens_vier(tmp_path):
    # Mutanten L112 (immer acht), L113 (Obergrenze entfällt): die Zahl gleichzeitiger Abrufe war nirgends gemessen.
    for threads, hoechstens in ((1, 1), (2, 2), (9, 4)):
        api = Gezaehlt(0.15)
        r = L.lauf(tmp_path / f"d{threads}", cfg(tiefe_teile=1, tiefe_threads=threads), T0, api, still, mit_git=False)
        assert r["stat"]["tiefe_ist"] == 6 and 1 <= api.hoechst <= hoechstens, (threads, api.hoechst)
        assert threads == 1 or api.hoechst >= 2                                               # und es läuft wirklich nebeneinander


# ------------------------------------------------------------------ Ablage ----


def test_csv_zeilenende(tmp_path):
    # Mutant L15: test_sammler.py liest die Dateien nur über den CSV-Leser, dem das Zeilenende gleich ist.
    L.lauf(tmp_path, cfg(), T0, Boersen(), still, mit_git=False)
    L.lauf(tmp_path, cfg(), T0 + 300, Boersen(), still, mit_git=False)
    for datei in (tmp_path / "offen").iterdir():
        roh = datei.read_bytes()
        assert b"\r" not in roh and roh.endswith(b"\n") and not roh.endswith(b"\n\n"), datei.name


def test_packen_haengt_nicht_an_der_uhrzeit(monkeypatch):
    # Mutant L16 (mtime=0 entfällt): test_sammler.py packt zweimal in derselben Sekunde, da ist auch der Zeitstempel gleich.
    monkeypatch.setattr(time, "time", lambda: 1_800_000_000.0)
    a = L.packen(b"abc" * 100)
    monkeypatch.setattr(time, "time", lambda: 1_800_000_777.0)
    b = L.packen(b"abc" * 100)
    assert a == b and a[4:8] == b"\x00\x00\x00\x00" and gzip.decompress(a) == b"abc" * 100


# ------------------------------------------------------------- Platzgrenze ----
def test_platz_wird_in_megabyte_gemessen(tmp_path):
    # Mutant L30 (GB statt MB): test_sammler.py prüft die Grenze nur mit -1; die Messung selbst war ungeprüft.
    (tmp_path / "a" / "b").mkdir(parents=True)
    (tmp_path / "a" / "b" / "x.bin").write_bytes(b"\0" * 2_500_000)
    (tmp_path / "a" / "y.bin").write_bytes(b"\0" * 500_000)
    assert L.platz_mb(tmp_path / "a") == pytest.approx(3.0, abs=0.001)
    for name, ballast, voll in (("mit", 2_000_000, True), ("ohne", 0, False)):               # Grenze 1 MB, einmal liegen schon 2 MB im Ordner
        daten = tmp_path / name
        daten.mkdir()
        if ballast:
            (daten / "ballast.bin").write_bytes(b"\0" * ballast)
        L.lauf(daten, cfg(platz_mb=1), T0, Boersen(), still, mit_git=False)
        L.lauf(daten, cfg(platz_mb=1), T0 + 3600, Boersen(), still, mit_git=False)            # beim Packen wird gemessen
        assert zustand(daten)["voll"] is voll and zustand(daten)["platz_mb"] == pytest.approx(ballast / 1e6, abs=0.5)


# ------------------------------------------------------------------ Bremse ----


def test_bremse_beim_zweiten_binance_abruf_pausiert_binance(tmp_path):
    # Mutant L50: in test_sammler.py bremst Binance immer schon beim ersten der zwei Abrufe.
    daten, api, c = tmp_path / "daten", Boersen(), cfg()
    api.stoerung["premiumIndex"] = L.Gebremst("HTTP 429")
    r = L.lauf(daten, c, T0, api, still, mit_git=False)
    assert any("Binance bremst" in f for f in r["fehler"]) and r["stat"]["ticker"] == 9 and api.zahl("fapi") == 2
    api.stoerung.clear(); api.abrufe.clear()
    r = L.lauf(daten, c, T0 + 900, api, still, mit_git=False)
    assert api.zahl("fapi") == 0 and r["stat"]["binance"] == 0 and r["stat"]["ticker"] == 6


# -------------------------------------------------------------------- Takt ----
def test_takt_gilt_auch_neben_dem_fuenf_minuten_raster(tmp_path):
    # Mutant L97 (Lauf-Nummer in Minuten): test_sammler.py startet jeden Lauf auf die Sekunde genau im Fünf-Minuten-Raster.
    # Auf dem Server beginnt der Sammler erst nach den vier Tests, gut eine Minute später und nie gleich.
    daten, api, c = tmp_path / "daten", Boersen(), cfg()
    versatz = [71, 64, 75, 61, 119, 70, 66, 73, 62, 74, 68, 65]
    ticker, binance = [], []
    for i, v in enumerate(versatz):
        r = L.lauf(daten, c, T0 + 300 * i + v, api, still, mit_git=False)
        ticker.append(r["stat"]["ticker"]); binance.append(r["stat"]["binance"])
    assert ticker == [9] + [6] * 11                                                           # alle Kontrakte genau einmal je Stunde
    assert binance == [3, 0, 0] * 4                                                           # Binance alle 15 Minuten
    tf = offen(daten, "tiefe")
    assert {s: sum(1 for z in tf if z["sym"] == s) for s in c["coins"] + c["reihum"]} == {"BTCUSDT": 12, "DOTUSDT": 12, "NVDAUSDT": 4, "QQQUSDT": 4, "XAUUSDT": 4, "NDX100USDT": 4}


def test_takt_einstellungen_wirken(tmp_path):
    # Mutanten L99, L100, L101 (alle_jede, binance_jede, tiefe_teile fest verdrahtet): test_sammler.py kennt nur 12, 3 und 3.
    daten, api, c = tmp_path / "daten", Boersen(), cfg(alle_jede=2, binance_jede=4, tiefe_teile=2)
    for i in range(12):
        r = L.lauf(daten, c, T0 + 300 * i, api, still, mit_git=False)
        assert r["stat"]["ticker"] == (9 if i % 2 == 0 else 6), i
        assert r["stat"]["binance"] == (3 if i % 4 == 0 else 0), i
        assert r["stat"]["tiefe_soll"] == r["stat"]["tiefe_ist"] == 2 + 2, i
    tf = offen(daten, "tiefe")
    assert {s: sum(1 for z in tf if z["sym"] == s) for s in c["coins"] + c["reihum"]} == {"BTCUSDT": 12, "DOTUSDT": 12, "NVDAUSDT": 6, "QQQUSDT": 6, "XAUUSDT": 6, "NDX100USDT": 6}


def test_binance_abschaltbar(tmp_path):
    # Mutant L96 (Schalter binance wird ignoriert).
    api = Boersen()
    r = L.lauf(tmp_path, cfg(binance=False), T0, api, still, mit_git=False)
    assert api.zahl("fapi") == 0 and r["stat"]["binance"] == 0 and r["fehler"] == [] and r["stat"]["ticker"] == 9
    assert not (tmp_path / "offen" / f"binance_{STUNDE}.csv").exists()


# ------------------------------------------------------------- Laufzeile ----
def test_boersenzeit_in_der_laufzeile(tmp_path):
    # Mutant L106: der Inhalt der Spalte boersenzeit_ms war ungeprüft.
    L.lauf(tmp_path, cfg(), T0, Boersen(), still, mit_git=False)
    lf = offen(tmp_path, "laeufe")
    assert len(lf) == 1 and lf[0]["boersenzeit_ms"] == str(TICKER["time"]) == "1795261471986" and lf[0]["t"] == str(T0)
    assert (lf[0]["ticker"], lf[0]["tiefe_soll"], lf[0]["tiefe_ist"], lf[0]["binance"]) == ("9", "4", "4", "3")


def test_unlesbarer_zustand_haelt_den_sammler_nicht_an(tmp_path):
    # Mutant L111: eine halb geschriebene zustand.json würde jeden weiteren Lauf scheitern lassen (main meldet nur und endet mit 0).
    for i, inhalt in enumerate(('{"push_offen": ["2026-1', "")):
        daten = tmp_path / str(i)
        daten.mkdir()
        (daten / "zustand.json").write_text(inhalt)
        r = L.lauf(daten, cfg(), T0, Boersen(), still, mit_git=False)
        assert r["stat"]["ticker"] == 9 and r["fehler"] == [] and zustand(daten)["heute"]["laeufe"] == 1


# ---------------------------------------------------------- Veröffentlichen ----


def test_ziel_ist_ohne_einstellung_das_repository_des_bot_klons(tmp_path, monkeypatch):
    # Mutant L74: so läuft der Sammler auf dem Server (sammler/config.json nennt kein Ziel), aber jeder Test in
    # test_sammler.py gibt das Ziel ausdrücklich vor; der Weg über "git remote get-url origin" war ungeprüft.
    assert not json.loads((Path(L.__file__).parent / "config.json").read_text()).get("ziel")
    ziel, bot = ziel_anlegen(tmp_path), tmp_path / "bot"
    subprocess.run(["git", "init", "-q", str(bot)], check=True)
    subprocess.run(["git", "-C", str(bot), "remote", "add", "origin", str(ziel)], check=True)
    subprocess.run(["git", "-C", str(bot), "remote", "add", "upstream", str(tmp_path / "anderswo.git")], check=True)
    (bot / "swing-hybrid" / "sammler").mkdir(parents=True)
    monkeypatch.setattr(L, "HIER", bot / "swing-hybrid" / "sammler")
    assert L.ziel_repo({}) == L.ziel_repo({"ziel": ""}) == str(ziel) and L.ziel_repo({"ziel": "vorgegeben"}) == "vorgegeben"
    daten, api, c = tmp_path / "daten", Boersen(), cfg()                                      # cfg() ohne Ziel
    L.lauf(daten, c, T0, api, still)
    r = L.lauf(daten, c, T0 + 3600, api, still)
    assert r["push_offen"] == [] and r["fehler"] == [] and "ticker/2026-11-21/12.csv.gz" in im_ziel(ziel, "marktdaten-2026-11")
    assert zweige(bot) == [] and list((bot / "swing-hybrid" / "sammler").iterdir()) == []     # der Klon des Bots bleibt unberührt


def test_halb_angelegter_zweig_ordner_wird_neu_angelegt(tmp_path, monkeypatch):
    # Mutant L116 (.git bleibt nach einer Panne beim Anlegen stehen): der nächste Lauf hielte den Ordner für fertig,
    # obwohl die Gegenstelle fehlt, und jeder Push scheiterte.
    ziel, daten, api = ziel_anlegen(tmp_path), tmp_path / "daten", Boersen()
    c, echt = cfg(ziel), L.git

    def git_mit_panne(ordner, *a, **k):
        if a[:2] == ("remote", "add"):
            return subprocess.CompletedProcess(a, 1, "", "nachgestellte Panne")
        return echt(ordner, *a, **k)
    L.lauf(daten, c, T0, api, still)
    monkeypatch.setattr(L, "git", git_mit_panne)
    r = L.lauf(daten, c, T0 + 3600, api, still)
    assert r["push_offen"] == ["2026-11"] and any("git remote" in f for f in r["fehler"])
    monkeypatch.setattr(L, "git", echt)
    r = L.lauf(daten, c, T0 + 3900, api, still)
    assert r["push_offen"] == [] and r["fehler"] == [] and "ticker/2026-11-21/12.csv.gz" in im_ziel(ziel, "marktdaten-2026-11")


# -------------------------------------------------------------------- main ----
def test_main_reicht_strg_c_durch(tmp_path, monkeypatch):
    # Mutant L89: KeyboardInterrupt soll als einziges nicht verschluckt werden.
    def strg_c(*a, **k):
        raise KeyboardInterrupt
    monkeypatch.setattr(L, "lauf", strg_c)
    konf = tmp_path / "c.json"; konf.write_text(json.dumps(cfg()))
    with pytest.raises(KeyboardInterrupt):
        L.main(["--daten", str(tmp_path / "d"), "--config", str(konf)])


def test_main_schalter_ohne_git_und_einstellung(tmp_path, monkeypatch):
    # Mutant L90 (--ohne-git wirkt umgekehrt): test_sammler.py ersetzt lauf() in main und sieht die Übergabe nicht an.
    rufe = []
    monkeypatch.setattr(L, "lauf", lambda daten, c, **k: rufe.append((daten, c, k)))
    assert L.main(["--daten", str(tmp_path / "d")]) == 0 and L.main(["--daten", str(tmp_path / "d"), "--ohne-git"]) == 0
    assert [k for _, _, k in rufe] == [{"mit_git": True}, {"mit_git": False}]
    assert rufe[0][0] == tmp_path / "d" and rufe[0][1] == json.loads((Path(L.__file__).parent / "config.json").read_text())   # ohne --config: sammler/config.json


# ------------------------------------------------------------- Einstellung ----
def test_einstellung_des_servers_ist_lesbar_vollstaendig_und_wie_festgelegt(tmp_path):
    # Mutanten C01 bis C07 (Fehler in sammler/config.json): test_sammler.py liest die ausgelieferte Einstellung nie.
    # Ein fehlender Schlüssel oder ein Tippfehler dort fiele erst auf dem Server auf, und dort endet main trotzdem mit 0.
    c = json.loads((Path(L.__file__).parent / "config.json").read_text())
    assert c["aktiv"] is True and c["binance"] is True and not c.get("ziel") and c["zweig"] == "odingate-marktdaten"
    alle = c["coins"] + c["reihum"]
    assert (len(c["coins"]), len(c["reihum"]), len(set(alle))) == (10, 222, 232)              # Protokoll 54: zehn Coins, 222 Kontrakte, keiner doppelt
    assert all(isinstance(s, str) and s.endswith("USDT") and s == s.upper() and " " not in s for s in alle)
    assert {"NVDAUSDT", "NDX100USDT", "SP500USDT"} <= set(c["reihum"]) and "ANTHROPICUSDT" not in alle and "BTCUSDT" in c["coins"]
    assert (c["tiefe_teile"], c["binance_jede"], c["alle_jede"]) == (3, 3, 12)                # 15 Minuten, 15 Minuten, einmal je Stunde
    assert c["baender_bp"] == [5, 10, 20, 50, 100, 200, 500] and c["groessen_usd"] == [1500, 5000, 25000]
    assert c["pause_nach_bremse_s"] == 3600 and c["platz_mb"] == 1500 and c["tiefe_threads"] == 2 and 0 < c["pause_s"] <= 1
    assert 0 < c["frist_s"] < c["frist_gesamt_s"] < 120                                       # stunde.sh bricht nach 120 s ab
    api = Boersen()                                                                           # ein ganzer Durchlauf mit genau dieser Einstellung
    r = L.lauf(tmp_path, dict(c, pause_s=0.0), T0, api, still, mit_git=False)
    assert r["fehler"] == [] and r["stat"]["ticker"] == 9 and r["stat"]["binance"] == 3
    assert r["stat"]["tiefe_soll"] == r["stat"]["tiefe_ist"] == 10 + 74 == api.zahl("orderbooks")   # "rund 84 Abrufe je Lauf"
    assert list(offen(tmp_path, "tiefe")[0]) == kern.tiefe_spalten(c["baender_bp"], c["groessen_usd"])
