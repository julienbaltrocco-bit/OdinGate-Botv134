"""Zusatztests zur Tagesregel (Test 4), entstanden aus der Mutationsprüfung des Commits 28fdaa0.

Jeder Test schließt eine Lücke, durch die ein einzeln eingebauter Fehler in tests/test_vorwaertstest_bot.py unbemerkt
blieb. Am unveränderten Stand sind alle grün. Die Kennung in Klammern nennt die Mutanten, die der Test findet
(Liste: werkzeug/mutanten.py im Ordner des Prüfers).

Zwei Tests halten Verhalten fest, das Abschnitt 53 nicht vorschreibt (dort jeweils vermerkt): Sie schreiben nur fest,
was der Code heute tut, damit eine spätere Änderung auffällt.
"""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from vorwaertstest import bot
from vorwaertstest.yubit import YubitFehler

from test_vorwaertstest_bot import CFG, CFG_TAG, DD, H, M, TAG, TagBoerse, stunden, zustand

MIN = 60_000
TAG0, TAG1 = bot.utc(M)[:10], bot.utc(M + TAG)[:10]


class Mitschrift(TagBoerse):
    """Schreibt bei Abrufen mit Startzeit auch die verlangte Kerzenlänge mit."""

    def __init__(self, *a, **kw):
        super().__init__(*a, **kw)
        self.fenster = []

    def kerzen(self, sym, minuten=60, limit=3, start_ms=None, ende_ms=None):
        if start_ms is not None:
            self.fenster.append((sym.removesuffix("USDT"), minuten, start_ms))
        return super().kerzen(sym, minuten, limit, start_ms, ende_ms)


# ------------------------------------------------------------------ tagesrichtung_lesen ----
def test_tagesrichtung_fragt_stundenkerzen_ab_und_vergleicht_mit_336_stunden_vor_dem_tageswechsel():
    """(A07, A14, A16; schärfer für A11, A12) Beim Aufholen spät am Tag zählt der Schluss 336 Stunden vor der Kerze zum
    Tageswechsel, nicht 336 Stunden vor der laufenden Stunde; abgefragt werden Stundenkerzen (60 Minuten)."""
    alt = stunden((-337, 90.0), *((h, 120.0) for h in (-339, -338, -336, -335, -334, -333)))   # nur die richtige Kerze liegt unter 100
    api = Mitschrift({"AAA": 100.0}, {"AAA": 120.0}, {"AAA": {**stunden((-1, 100.0)), **alt}})
    for jetzt in (M + 4 * MIN, M + 3 * H + 14 * MIN, M + 23 * H + 59 * MIN):
        api.fenster.clear()
        assert bot.tagesrichtung_lesen(api, "AAA", jetzt) == {"tag": TAG0, "richtung": 1, "schluss": 100.0, "schluss_alt": 90.0}
        assert api.fenster == [("AAA", 60, M - H), ("AAA", 60, M - H - 336 * H)]


def test_tagesrichtung_nimmt_keine_nachbarkerze_wenn_die_gesuchte_fehlt():
    """(A06, A15, A17) Fehlt genau die gesuchte Kerze, darf keine andere aus der Antwort einspringen; die Meldung nennt den Coin."""
    # Kerze 23:00 fehlt, die laufende Kerze ab 00:00 ist da und läge unter dem Stand vor 14 Tagen
    api = TagBoerse({"AAA": 100.0}, {"AAA": 90.0}, {"AAA": stunden((0, 70.0))})
    with pytest.raises(YubitFehler, match="AAA: keine Stundenkerze zum Tageswechsel"):
        bot.tagesrichtung_lesen(api, "AAA", M + 4 * MIN)
    # Sechs Tage später: Kerze zum Tageswechsel da, die von 336 Stunden davor fehlt, ihre Nachbarin ist da
    start = M + 6 * TAG - H
    k = {start: 100.0, start - 335 * H: 120.0}
    assert start - 336 * H >= M - 200 * H                                              # in diesem Bereich gibt es nur, was in k steht
    with pytest.raises(YubitFehler, match="AAA: keine Kerze von 14 Tagen vor dem Tageswechsel"):
        bot.tagesrichtung_lesen(TagBoerse({"AAA": 100.0}, {"AAA": 90.0}, {"AAA": k}), "AAA", M + 6 * TAG + 4 * MIN)


def test_tagesregel_ohne_vergleichskerze_kein_handel_und_hinweis_mit_coin(tmp_path):
    """(A17) Im Lauf: Stundensignal vorhanden, aber die Vergleichskerze der Tagesrichtung fehlt -> kein Handel, Hinweis nennt den Coin."""
    start = M + 6 * TAG - H                                                            # Kerze zum Tageswechsel am Tag 6
    k = {start: 100.0, start + 2 * H: 100.0, start + 3 * H: 100.0, start + 3 * H - 336 * H: 90.0}   # Vergleich nur für die Stunde des Laufs
    api = TagBoerse({"AAA": 100.0}, {"AAA": 90.0}, {"AAA": k})
    r = api.lauf({**CFG_TAG, "coins": ["AAA"]}, tmp_path, M + 6 * TAG + 3 * H + 14 * MIN)
    assert bot.markt_lesen(api, "AAA", api.jetzt)["richtung"] == 1                      # das Stundensignal wäre Long
    assert r["orders"] == 0 and zustand(tmp_path)["tagesrichtung"] == {} and zustand(tmp_path)["pos"].get("AAA", 0.0) == 0.0
    assert [w for w in r["warnungen"] if "AAA: keine Kerze von 14 Tagen vor dem Tageswechsel" in w and "Tagesrichtung noch nicht übernommen" in w]


# ------------------------------------------------------------------ schritt mit Tagesregel ----
def test_tagesregel_handelt_nicht_mit_der_richtung_des_vortags(tmp_path):
    """(C02, B14) Abschnitt 53: Solange für den laufenden Tag keine Richtung vorliegt, wird nicht gehandelt. Nach einem Tageslimit
    ist das Konto flach; am nächsten Tag ohne Kerze darf die Richtung des Vortags keinen Einstieg auslösen."""
    k = {"AAA": stunden((-2, 100.0), (-1, 100.0), (3, 100.0), (4, 100.0), (22, 100.0)),
         "BBB": stunden((-2, 70.0), (-1, 70.0), (3, 70.0), (4, 70.0), (22, 70.0))}
    api = TagBoerse({"AAA": 100.0, "BBB": 70.0}, {"AAA": 90.0, "BBB": 60.0}, k)
    assert api.lauf(CFG_TAG, tmp_path, M + 4 * MIN)["orders"] == 2                       # Tag 0: beide Long
    api.kurse["BBB"] = 45.0                                                             # −3,6 % vom Kapital: Tageslimit
    assert api.lauf(CFG_TAG, tmp_path, M + 5 * H + 4 * MIN)["orders"] == 2
    z = zustand(tmp_path)
    assert z["gesperrt_tag"] == TAG0 and z["pos"] == {"AAA": 0.0, "BBB": 0.0}
    assert {x["grund"] for x in bot.lesen(tmp_path / "protokoll.csv")[-2:]} == {"tageslimit"}
    vortag = z["tagesrichtung"]
    assert vortag == {"AAA": {"tag": TAG0, "richtung": 1, "schluss": 100.0, "schluss_alt": 90.0},
                      "BBB": {"tag": TAG0, "richtung": 1, "schluss": 70.0, "schluss_alt": 60.0}}
    api.kurse.update(AAA=100.0, BBB=70.0)
    r = api.lauf(CFG_TAG, tmp_path, M + TAG + 4 * MIN)                                   # Tag 1: Kerze zum Tageswechsel fehlt für beide
    z = zustand(tmp_path)
    assert r["orders"] == 0 and z["pos"] == {"AAA": 0.0, "BBB": 0.0} and z["gesperrt_tag"] == TAG0
    assert z["tagesrichtung"] == vortag                                                 # (B14) der Eintrag des Vortags bleibt unverändert stehen
    assert len([w for w in r["warnungen"] if "Tagesrichtung noch nicht übernommen" in w]) == 2
    api.schluss["AAA"][M + 23 * H] = 100.0; api.schluss["BBB"][M + 23 * H] = 50.0        # die Kerzen erscheinen: AAA Long, BBB Short
    r = api.lauf(CFG_TAG, tmp_path, M + TAG + 9 * MIN)
    z = zustand(tmp_path)
    assert r["orders"] == 2 and z["pos"]["AAA"] > 0 and z["pos"]["BBB"] < 0 and not r["warnungen"]


def test_tagesregel_faengt_auch_unlesbare_antworten_ab(tmp_path):
    """(B13) Wie beim Stundensignal bricht eine unlesbare Antwort (ValueError, KeyError, IndexError) den Lauf nicht ab:
    der Coin wird ausgelassen, die übrigen werden gehandelt."""
    class Unlesbar(TagBoerse):
        fehler = ValueError("unlesbare Antwort")

        def kerzen(self, sym, minuten=60, limit=3, start_ms=None, ende_ms=None):
            if sym == "AAAUSDT" and start_ms == M - H:                                  # nur die Kerze zum Tageswechsel von AAA
                raise self.fehler
            return super().kerzen(sym, minuten, limit, start_ms, ende_ms)

    k = {"AAA": stunden((-2, 100.0), (-1, 100.0)), "BBB": stunden((-2, 50.0), (-1, 50.0))}
    for i, fehler in enumerate((ValueError("unlesbare Antwort"), KeyError("close"), IndexError("list index out of range"))):
        api = Unlesbar({"AAA": 100.0, "BBB": 50.0}, {"AAA": 90.0, "BBB": 60.0}, k)
        api.fehler = fehler
        r = api.lauf(CFG_TAG, tmp_path / str(i), M + 4 * MIN)
        z = zustand(tmp_path / str(i))
        assert r["orders"] == 1 and z["pos"]["BBB"] < 0 and z["pos"].get("AAA", 0.0) == 0.0 and set(z["tagesrichtung"]) == {"BBB"}
        assert len([w for w in r["warnungen"] if "Tagesrichtung noch nicht übernommen" in w]) == 1


def test_tagesrichtung_wird_nur_fuer_coins_mit_marktdaten_geholt(tmp_path):
    """(B04) NICHT in Abschnitt 53 vorgeschrieben, hält nur das heutige Verhalten fest: Für einen Coin ohne Marktdaten in
    diesem Lauf wird keine Tagesrichtung abgerufen und keine gespeichert. Für die Orders macht das keinen Unterschied."""
    class Ausgesetzt(TagBoerse):
        def kontrakt(self, sym):
            return {**super().kontrakt(sym), "status": "Halt" if sym == "BBBUSDT" else "Trading"}

    k = {"AAA": stunden((-2, 100.0), (-1, 100.0)), "BBB": stunden((-2, 50.0), (-1, 50.0))}
    api = Ausgesetzt({"AAA": 100.0, "BBB": 50.0}, {"AAA": 90.0, "BBB": 60.0}, k)
    r = api.lauf(CFG_TAG, tmp_path, M + 4 * MIN)
    assert r["orders"] == 1 and any("Handel ausgesetzt" in w for w in r["warnungen"])
    assert set(zustand(tmp_path)["tagesrichtung"]) == {"AAA"} and ("BBB", M - H) not in api.abrufe
    assert "tagesrichtung_tag" not in DD().bauen(CFG_TAG, tmp_path)["kennzahlen"][0]


# ------------------------------------------------------------------ Dashboard und Bericht ----
def test_dashboard_nennt_den_aeltesten_tag_und_nur_wenn_alle_coins_entschieden_sind(tmp_path):
    """(E03, E04, E07) tagesrichtung_tag ist der älteste Tag über ALLE Coins der Einstellung; fehlt einem Coin die Tagesrichtung
    ganz, fehlt das Feld."""
    # a) der zweite Coin hängt einen Tag zurück (seine Kerze zum Tageswechsel fehlt am Tag 1)
    k = {"AAA": stunden((-2, 100.0), (-1, 100.0), (22, 100.0), (23, 100.0)), "BBB": stunden((-2, 50.0), (-1, 50.0), (22, 50.0))}
    api = TagBoerse({"AAA": 100.0, "BBB": 50.0}, {"AAA": 90.0, "BBB": 60.0}, k)
    a = tmp_path / "a"
    api.lauf(CFG_TAG, a, M + 4 * MIN); api.lauf(CFG_TAG, a, M + TAG + 4 * MIN)
    assert {c: v["tag"] for c, v in zustand(a)["tagesrichtung"].items()} == {"AAA": TAG1, "BBB": TAG0}
    kz = DD().bauen(CFG_TAG, a)["kennzahlen"][0]
    assert kz["tagesregel"] is True and kz["tagesrichtung_tag"] == TAG0
    # b) neues Konto, für den zweiten Coin gab es noch nie eine Tagesrichtung
    b = tmp_path / "b"
    api = TagBoerse({"AAA": 100.0, "BBB": 50.0}, {"AAA": 90.0, "BBB": 60.0}, {"AAA": stunden((-2, 100.0), (-1, 100.0)), "BBB": stunden((-2, 50.0))})
    assert api.lauf(CFG_TAG, b, M + 4 * MIN)["orders"] == 1 and set(zustand(b)["tagesrichtung"]) == {"AAA"}
    kz = DD().bauen(CFG_TAG, b)["kennzahlen"][0]
    assert kz["tagesregel"] is True and "tagesrichtung_tag" not in kz


def test_bericht_nennt_die_tagesregel_im_kopf_vor_der_leerzeile(tmp_path):
    """(D03) Die Zeile steht im Kopf des Berichts direkt nach der Kapital-Zeile, vor der Leerzeile und der ersten Überschrift;
    mit nachgerechnet_bis folgt dessen Zeile danach."""
    api = TagBoerse({"AAA": 100.0, "BBB": 50.0}, {"AAA": 90.0, "BBB": 60.0}, {"AAA": stunden((-2, 100.0), (-1, 100.0)), "BBB": stunden((-2, 50.0), (-1, 50.0))})
    api.lauf(CFG_TAG, tmp_path, M + 4 * MIN)
    z = bot.bericht(CFG_TAG, tmp_path).split("\n")
    i = next(n for n, x in enumerate(z) if x.startswith("- Tagesregel:"))
    assert z[i - 1].startswith("- Kapital ") and z[i + 1] == "" and z[i + 2].startswith("## ")
    assert "einmal am Tag" in z[i] and "00:00 UTC" in z[i]
    z = bot.bericht({**CFG_TAG, "nachgerechnet_bis": bot.utc(M + 4 * MIN)}, tmp_path).split("\n")
    i = next(n for n, x in enumerate(z) if x.startswith("- Tagesregel:"))
    assert z[i - 1].startswith("- Kapital ") and "nachgerechnet" in z[i + 1] and z[i + 2] == "" and z[i + 3].startswith("## ")


# ------------------------------------------------------------------ Nachrechnung ----
def test_nachrechnen_mit_tagesregel_bei_start_in_der_letzten_stunde_des_tages(tmp_path):
    """(F01, F02) Präzisierung 2: nachrechnen lädt einen Tag mehr Stundenkerzen. Beginnt die Quelle spät am Tag (hier 23:21 UTC;
    Test 1 begann um 13:21 UTC), liegt die Vergleichskerze der Tagesrichtung bis zu 360 Stunden vor der Stunde des ersten Laufs."""
    from vorwaertstest import nachrechnen as N
    k = {c: stunden(*((h, s) for h in (-2, -1, 21, 22, 23, 24))) for c, s in (("AAA", 100.0), ("BBB", 50.0))}
    api = TagBoerse({"AAA": 100.0, "BBB": 50.0}, {"AAA": 90.0, "BBB": 60.0}, k)
    quelle, ziel = tmp_path / "quelle", tmp_path / "ziel"
    zeiten = (M + 23 * H + 21 * MIN, M + 23 * H + 26 * MIN, M + TAG + 4 * MIN, M + TAG + H + 4 * MIN)
    for jetzt in zeiten:
        api.lauf(CFG, quelle, jetzt)
    q = bot.lesen(quelle / "protokoll.csv")
    assert len(q) == 2 and {x["zeit"] for x in q} == {bot.utc(zeiten[0])}                 # Quelle: zwei Einstiege im ersten Lauf, sonst nichts
    r = N.nachrechnen(CFG_TAG, quelle, ziel, True, api=api, melden=lambda *_: None)
    assert r["laeufe"] == 4 and bot.lesen(ziel / "protokoll.csv") == q                   # Tagesregel: dieselben Einstiege zur selben Zeit
    st, sq = bot.lesen(ziel / "stand.csv"), bot.lesen(quelle / "stand.csv")
    assert [(x["zeit"], x["long"], x["short"], x["orders"]) for x in st] == [(x["zeit"], x["long"], x["short"], x["orders"]) for x in sq]
    z = zustand(ziel)
    assert z["pos"] == {"AAA": 5.0, "BBB": -10.0}
    assert z["tagesrichtung"] == {"AAA": {"tag": TAG1, "richtung": 1, "schluss": 100.0, "schluss_alt": 90.0},
                                  "BBB": {"tag": TAG1, "richtung": -1, "schluss": 50.0, "schluss_alt": 60.0}}


# ------------------------------------------- Tagesregel zusammen mit Stop (nicht festgelegte Kombination) ----
def test_tagesregel_mit_stop_richtet_stop_und_pause_an_der_tagesrichtung_aus(tmp_path):
    """(C11, C12, C13, C14, C15) NICHT in Abschnitt 53 festgelegt (Test 4 hat weder Ziel noch Stop) und in keiner der vier
    Einstellungen so geschaltet. Hält nur fest, was der Code heute tut, wenn tagesregel und sl zusammen gesetzt sind:
    Stop und Pause richten sich nach der Tagesrichtung, nicht nach dem Stundensignal."""
    cfg = {**CFG_TAG, "coins": ["AAA"], "sl": 0.05}
    k = {"AAA": stunden((-2, 100.0), (-1, 100.0), (3, 80.0), (4, 80.0), (5, 80.0), (6, 90.0), (22, 80.0), (23, 80.0))}
    api = TagBoerse({"AAA": 100.0}, {"AAA": 90.0}, k)
    assert api.lauf(cfg, tmp_path, M + 4 * MIN)["orders"] == 1 and zustand(tmp_path)["pos"]["AAA"] == pytest.approx(10.0)   # ein Coin: 1.000 $
    # 05:04: Kurs 6 % unter dem Einstieg, das Stundensignal steht inzwischen auf Short. Tagesrichtung Long -> Stop greift
    api.kurse["AAA"] = 94.0
    api.jetzt = M + 5 * H + 4 * MIN
    assert bot.markt_lesen(api, "AAA", api.jetzt)["richtung"] == -1
    assert api.lauf(cfg, tmp_path, M + 5 * H + 4 * MIN)["orders"] == 1
    z = zustand(tmp_path)
    assert z["pos"]["AAA"] == 0.0 and z["sperre"]["AAA"] == 1 and bot.lesen(tmp_path / "protokoll.csv")[-1]["grund"] == "stop"
    # 06:04: Stundensignal Short, Tagesrichtung weiter Long -> Pause bleibt, kein Wiedereinstieg
    assert api.lauf(cfg, tmp_path, M + 6 * H + 4 * MIN)["orders"] == 0 and zustand(tmp_path)["sperre"]["AAA"] == 1
    # 07:04: Stundensignal Gleichstand -> Pause bleibt, kein Wiedereinstieg
    api.jetzt = M + 7 * H + 4 * MIN
    assert bot.markt_lesen(api, "AAA", api.jetzt)["richtung"] == 0
    assert api.lauf(cfg, tmp_path, M + 7 * H + 4 * MIN)["orders"] == 0 and zustand(tmp_path)["sperre"]["AAA"] == 1
    # nächster Tageswechsel: Tagesrichtung Short -> Pause endet, Einstieg Short
    api.kurse["AAA"] = 80.0
    assert api.lauf(cfg, tmp_path, M + TAG + 4 * MIN)["orders"] == 1
    z = zustand(tmp_path)
    assert z["pos"]["AAA"] < 0 and z["sperre"]["AAA"] == 0 and bot.lesen(tmp_path / "protokoll.csv")[-1]["grund"] == "einstieg"


# ------------------------------------------- bestehende Varianten (Test 2 und 3), Zeilen mit `signal` ----
def test_stop_variante_gleichstand_loest_die_pause(tmp_path):
    """(T04) Test 2/3 wie bisher: Steht das Signal nach einem Stop auf Gleichstand (0), endet die Pause; kehrt das Signal
    danach in die alte Richtung zurück, wird wieder eingestiegen."""
    cfg, still = {**CFG, "tp": 0.15, "sl": 0.05}, (lambda *_: None)
    from test_vorwaertstest_bot import Boerse, JETZT
    api = Boerse({"AAA": 100.0, "BBB": 50.0}, {"AAA": 90.0, "BBB": 60.0})              # AAA Long, BBB Short
    bot.schritt(cfg, api, tmp_path, JETZT, melden=still)
    api.kurse["BBB"] = 53.0                                                             # 6 % gegen den Short: Stop
    bot.schritt(cfg, api, tmp_path, JETZT + H // 4, melden=still)
    assert zustand(tmp_path)["pos"]["BBB"] == 0.0 and zustand(tmp_path)["sperre"]["BBB"] == -1
    api.kurse["BBB"] = 60.0                                                             # Schluss gleich dem vor 14 Tagen
    assert bot.schritt(cfg, api, tmp_path, JETZT + 2 * (H // 4), melden=still)["orders"] == 0
    assert zustand(tmp_path)["sperre"]["BBB"] == 0
    api.kurse["BBB"] = 55.0                                                             # wieder Short-Signal
    assert bot.schritt(cfg, api, tmp_path, JETZT + 3 * (H // 4), melden=still)["orders"] == 1
    assert zustand(tmp_path)["pos"]["BBB"] < 0 and bot.lesen(tmp_path / "protokoll.csv")[-1]["grund"] == "einstieg"


def test_stop_varianten_dreh_mit_verlust_ist_schliessen_und_keine_pause(tmp_path):
    """(T08) Test 2/3 wie bisher: Dreht das Signal gegen die Position, wird geschlossen und gedreht, auch wenn der Kurs unter
    dem Stop liegt. Grund 'schliessen', keine Pause, kein 'wartet' auf dem Board."""
    from test_vorwaertstest_bot import Boerse, JETZT
    for i, cfg in enumerate(({**CFG, "tp": 0.15, "sl": 0.05}, {**CFG, "trail": 0.05})):
        ordner, still = tmp_path / str(i), (lambda *_: None)
        api = Boerse({"AAA": 100.0, "BBB": 50.0}, {"AAA": 90.0, "BBB": 60.0})          # AAA Long, BBB Short
        bot.schritt(cfg, api, ordner, JETZT, melden=still)
        api.kurse["AAA"] = 80.0                                                         # −20 % und Signal jetzt Short
        assert bot.schritt(cfg, api, ordner, JETZT + H // 4, melden=still)["orders"] == 2
        z, pr = zustand(ordner), bot.lesen(ordner / "protokoll.csv")
        assert z["pos"]["AAA"] < 0 and [x["grund"] for x in pr[-2:]] == ["schliessen", "einstieg"]
        assert not z.get("sperre", {}).get("AAA", 0)
        assert not next(p for p in DD().bauen(cfg, ordner)["positionen"] if p["coin"] == "AAA")["wartet"]


def test_stop_variante_pause_uebersteht_den_tag_mit_tageslimit(tmp_path):
    """(T05, T14) Test 2/3 wie bisher: Am Tag des Tageslimits bleibt eine bestehende Pause bestehen, und ein Stop, der im
    selben Lauf erreicht ist, setzt die Pause (Grund der Order: tageslimit). Am nächsten Tag kein Wiedereinstieg, solange
    das Signal nicht dreht."""
    cfg = {**CFG, "sl": 0.05}
    k = {"AAA": stunden((-2, 100.0), (-1, 100.0), (0, 100.0), (1, 70.0), (22, 70.0), (23, 70.0)),
         "BBB": stunden((-2, 50.0), (-1, 50.0), (0, 53.0), (1, 53.0), (22, 53.0), (23, 53.0))}
    api = TagBoerse({"AAA": 100.0, "BBB": 50.0}, {"AAA": 60.0, "BBB": 60.0}, k)       # AAA Long, BBB Short, bleibt den ganzen Test so
    assert api.lauf(cfg, tmp_path, M + 4 * MIN)["orders"] == 2
    api.kurse["BBB"] = 53.0                                                             # BBB: Stop, Pause Short
    assert api.lauf(cfg, tmp_path, M + H + 4 * MIN)["orders"] == 1
    z = zustand(tmp_path)
    assert z["sperre"]["BBB"] == -1 and not z["gesperrt_tag"] and bot.lesen(tmp_path / "protokoll.csv")[-1]["grund"] == "stop"
    api.kurse["AAA"] = 70.0                                                             # AAA −30 %: Tageslimit und zugleich Stop
    assert api.lauf(cfg, tmp_path, M + 2 * H + 4 * MIN)["orders"] == 1
    z = zustand(tmp_path)
    assert z["gesperrt_tag"] == TAG0 and z["pos"] == {"AAA": 0.0, "BBB": 0.0} and z["sperre"] == {"AAA": 1, "BBB": -1}
    assert bot.lesen(tmp_path / "protokoll.csv")[-1]["grund"] == "tageslimit"
    r = api.lauf(cfg, tmp_path, M + TAG + 4 * MIN)                                       # nächster Tag, Signale unverändert: beide pausieren
    z = zustand(tmp_path)
    assert r["orders"] == 0 and z["pos"] == {"AAA": 0.0, "BBB": 0.0} and z["sperre"] == {"AAA": 1, "BBB": -1}
