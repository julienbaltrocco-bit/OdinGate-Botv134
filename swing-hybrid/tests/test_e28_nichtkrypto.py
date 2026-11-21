"""E28: Abrechnung der Orderbuch-Regel je Kontrakt, Zufallsprüfung über Tage, Einstufung; Wochenend-Rechnung. Nur künstliche Daten."""
import datetime as dt
import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from forschung.experimente import e28_nichtkrypto as E
from forschung.papier.strategien import orderbuch_stuetze as OS

UTC = dt.timezone.utc
K = 300_000                                                   # eine 5-Minuten-Kerze
T0 = int(dt.datetime(2026, 6, 1, tzinfo=UTC).timestamp() * 1000)
P = {"tiefe_pct": 5, "fenster": 288, "min_perioden": 200, "einstieg_z": 3.0, "ausstieg_z": 1.0, "zeitlimit": 48}


def reihe(n, kurs=100.0):
    zeit = T0 + K * np.arange(n, dtype=np.int64)
    ohlc = np.full((n, 4), kurs)
    return zeit, ohlc, np.zeros(n)


def trade(ein, n85, sym="AUSDT", richtung=1):
    return {"sym": sym, "ein": ein, "aus": ein + K, "richtung": richtung, "z": 3.0, "roh_bp": n85 + 5, "slip_bp": 2.0, "funding_bp": 0.0, "n85_bp": n85, "n0_bp": n85 - 13.6}


# ------------------------------------------------------------------------ Teil 1 ----
def test_regel_und_parameter_sind_die_von_os11():
    assert E.os11() == P


def test_abrechnung_eines_trades(monkeypatch):
    zeit, ohlc, u = reihe(2000)
    ein, aus = int(zeit[1000]), int(zeit[1010])
    monkeypatch.setattr(OS, "trades", lambda kz, uu, p, start: [
        {"ein": ein, "aus": aus, "richtung": -1.0, "ein_kurs": 100.0, "aus_kurs": 99.0, "z": -3.2, "schlimmst_bp": -5.0},
        {"ein": aus, "aus": None, "richtung": 1.0, "ein_kurs": 99.0, "aus_kurs": 98.0, "z": 3.1, "schlimmst_bp": 0.0}])
    fz = np.array([ein, ein + 1, aus, aus + 1], dtype=np.int64)          # Funding genau am Einstieg zählt nicht, am Ausstieg schon
    fr = np.array([0.01, 0.0002, -0.0001, 0.05])
    t = E.trades_kontrakt("XUSDT", zeit, ohlc, u, fz, fr, 1.5, P)
    assert len(t) == 1                                                  # der offene Trade zählt nicht
    x = t[0]
    assert x["roh_bp"] == pytest.approx(100.0) and x["slip_bp"] == pytest.approx(3.0)        # Short von 100 auf 99; zwei Orders zu je 1,5 bp
    assert x["funding_bp"] == pytest.approx(-(-1) * (0.0002 - 0.0001) * 1e4)                # Short erhält positives Funding
    assert x["n85_bp"] == pytest.approx(100.0 - 3.0 + 1.0 - 16 * 0.15) and x["n0_bp"] == pytest.approx(100.0 - 3.0 + 1.0 - 16.0)
    assert E.trades_kontrakt("XUSDT", zeit, ohlc, u, fz, fr, 0.1, P)[0]["slip_bp"] == pytest.approx(1.0)     # Spanne mindestens 0,5 bp je Order
    assert E.trades_kontrakt("XUSDT", zeit[:150], ohlc[:150], u[:150], fz, fr, 1.5, P) == []                 # zu kurze Reihe


def test_regel_laeuft_auf_der_reihe_und_wertet_erst_nach_zwei_tagen():
    n = 288 * 6
    zeit, ohlc, _ = reihe(n)
    u = 0.01 * np.sin(np.arange(n))                                      # ruhiges Übergewicht: z bleibt weit unter 3
    frueh, spaet = 288 + 50, 288 * 4 + 50                                # ein Ausschlag am zweiten Tag (Vorlauf) und einer am fünften
    u[frueh] = u[spaet] = 0.5
    ohlc[spaet + 1:, :] = 101.0                                          # nach dem späten Signal steht der Kurs 1 % höher
    ohlc[spaet + 1, 0] = 100.0                                           # Einstieg zur Eröffnung der nächsten Kerze, noch zum alten Kurs
    t = E.trades_kontrakt("XUSDT", zeit, ohlc, u, np.array([], dtype=np.int64), np.array([]), 1.0, P)
    assert [x["ein"] for x in t] == [int(zeit[spaet + 1])] and t[0]["richtung"] == 1          # nur der späte Ausschlag wird gehandelt
    assert t[0]["roh_bp"] == pytest.approx(100.0) and t[0]["aus"] == int(zeit[spaet + 2])    # z fällt sofort unter 1: Ausstieg eine Kerze später
    assert t[0]["n85_bp"] == pytest.approx(100.0 - 2.0 - 2.4)


def test_zufallspruefung_zieht_ganze_tage():
    tag = np.array([1, 1, 1, 2, 3, 4])
    assert E.tage_stichprobe(tag, np.array([1.0, 2, 3, 4, 5, 6])) == 0.0 and E.tage_stichprobe(tag, -np.array([1.0, 2, 3, 4, 5, 6])) == 1.0
    wert = np.array([-10.0] * 30 + [1.0] * 30)                           # ein schlechter Tag mit 30 Trades, 30 gute Tage mit je einem
    tage = np.array([0] * 30 + list(range(1, 31)))
    p = E.tage_stichprobe(tage, wert)
    assert p == E.tage_stichprobe(tage, wert) and 0.55 < p < 0.75        # wiederholbar; der schlechte Tag fehlt in rund 37 % der Ziehungen ganz
    einzeln = E.tage_stichprobe(np.arange(60), wert)                     # dieselben Trades als 60 einzelne Tage: fast immer negativ
    assert einzeln > 0.99
    assert E.tage_stichprobe(np.array([5, 5, 5]), np.array([1.0, -3.0, 1.0])) == 1.0          # ein einziger Tag: sein Mittel entscheidet


def test_einstufung_teil_1():
    tag = E.TAG
    juli, okt = int(dt.datetime(2026, 7, 1, tzinfo=UTC).timestamp() * 1000), int(dt.datetime(2026, 10, 1, tzinfo=UTC).timestamp() * 1000)
    gut = [trade(juli + i * tag // 4, 5.0 + (i % 3)) for i in range(200)] + [trade(okt + i * tag // 4, 4.0 + (i % 3)) for i in range(200)]
    u = E.urteil1(gut)
    assert u["einstufung"] == "C" and u["alle"]["trades"] == 400 and u["p"] == 0.0 and u["erste_haelfte"]["trades"] == 200 and u["zweite_haelfte"]["trades"] == 200
    assert E.urteil1(gut[:299])["einstufung"] == "B"                                          # zu wenige Trades (und nur eine Hälfte)
    eine_haelfte_negativ = [trade(juli + i * tag // 4, 9.0) for i in range(200)] + [trade(okt + i * tag // 4, -1.0) for i in range(200)]
    assert E.urteil1(eine_haelfte_negativ)["einstufung"] == "B"
    rng = np.random.default_rng(3)
    unsicher = [trade(juli + i * tag // 4, x) for i, x in enumerate(rng.normal(0.3, 40, 200))] + [trade(okt + i * tag // 4, x) for i, x in enumerate(rng.normal(0.3, 40, 200))]
    uu = E.urteil1(unsicher)
    assert uu["einstufung"] in ("A", "B") and (uu["einstufung"] == "B") == (uu["alle"]["n85_bp"] > 0) and uu["p"] > E.P_GRENZE
    assert E.urteil1([trade(juli, -1.0)] * 400)["einstufung"] == "A" and E.urteil1([])["einstufung"] == "A"
    grenze = E.urteil1([trade(E.HAELFTE_AB - 1, 1.0), trade(E.HAELFTE_AB, 1.0)])              # 31.08. 23:59:59.999 zählt zur ersten Hälfte, 01.09. 00:00 zur zweiten
    assert grenze["erste_haelfte"]["trades"] == 1 and grenze["zweite_haelfte"]["trades"] == 1
    assert E.gruppe("XAUUSDT") == "Rohstoff" and E.gruppe("QQQUSDT") == "Fonds" and E.gruppe("NVDAUSDT") == "Einzelwert"


def test_teil_1_ganz(monkeypatch):
    zeit, ohlc, u = reihe(288 * 5)
    u[10] = np.nan
    daten = {"AUSDT": (zeit, ohlc, u), "XAUUSDT": (zeit[:-1], ohlc[:-1], u[:-1])}
    sa = int(dt.datetime(2026, 6, 6, 12, tzinfo=UTC).timestamp() * 1000)                      # ein Samstag
    monkeypatch.setattr(OS, "trades", lambda kz, uu, p, start: [
        {"ein": sa, "aus": sa + K, "richtung": 1.0, "ein_kurs": 100.0, "aus_kurs": 100.5, "z": 3.0, "schlimmst_bp": 0.0},
        {"ein": sa + 3 * E.TAG, "aus": sa + 3 * E.TAG + K, "richtung": -1.0, "ein_kurs": 100.0, "aus_kurs": 100.2, "z": -3.0, "schlimmst_bp": 0.0}])
    leer = np.array([], dtype=np.int64)
    r = E.teil1(["AUSDT", "XAUUSDT"], lambda s: {"zeit": daten[s][0], "ohlc": daten[s][1], "u": daten[s][2], "fund_zeit": leer, "fund_rate": np.array([])},
                {"AUSDT": 1.0, "XAUUSDT": 0.2})
    assert r["alle"]["trades"] == 4 and r["wochenende"]["trades"] == 2 and r["werktag"]["trades"] == 2 and r["long"]["trades"] == 2
    assert r["je_gruppe"]["Rohstoff"]["trades"] == 2 and r["je_gruppe"]["Einzelwert"]["trades"] == 2 and r["je_gruppe"]["Fonds"] == {"trades": 0}
    assert r["je_kontrakt"]["AUSDT"]["u_fehlt"] == 1 and r["je_kontrakt"]["AUSDT"]["von"] == "2026-06-01" and r["je_kontrakt"]["XAUUSDT"]["spanne_bp"] == 0.2
    assert r["wochenende"]["roh_bp"] == pytest.approx(50.0) and r["werktag"]["roh_bp"] == pytest.approx(-20.0)
    assert r["je_kontrakt"]["XAUUSDT"]["slip_bp"] == pytest.approx(1.0) and r["einstufung"] in ("A", "B")


# ------------------------------------------------------------------------ Teil 2 ----
def ms(*a):
    return int(dt.datetime(*a, tzinfo=UTC).timestamp() * 1000)


def test_wochenenden_zeitpunkte():
    w = E.wochenenden(ms(2026, 6, 3), ms(2026, 6, 23))                    # Mittwoch bis Dienstag
    assert w == [(ms(2026, 6, 6, 1), ms(2026, 6, 7, 23), ms(2026, 6, 8, 21)), (ms(2026, 6, 13, 1), ms(2026, 6, 14, 23), ms(2026, 6, 15, 21)),
                 (ms(2026, 6, 20, 1), ms(2026, 6, 21, 23), ms(2026, 6, 22, 21))]
    for a, b, c in E.wochenenden(ms(2026, 1, 1), ms(2026, 11, 17)):       # Sommer- und Winterzeit: immer dieselben UTC-Stunden und Wochentage
        da, db, dc = (dt.datetime.fromtimestamp(x / 1000, UTC) for x in (a, b, c))
        assert (da.weekday(), da.hour, db.weekday(), db.hour, dc.weekday(), dc.hour) == (5, 1, 6, 23, 0, 21) and b - a == 46 * E.H and c - b == 22 * E.H
    assert E.wochenenden(ms(2026, 6, 6, 2), ms(2026, 6, 15, 21)) == []    # Beginn nach Samstag 01:00 und Ende genau am Montag 21:00: keines vollständig
    assert len(E.wochenenden(ms(2026, 6, 6, 1), ms(2026, 6, 8, 21) + 1)) == 1
    letzte = E.wochenenden(ms(2026, 1, 1), ms(2026, 11, 17))[-1]
    assert letzte[0] == ms(2026, 11, 14, 1) and letzte[2] == ms(2026, 11, 16, 21)             # das letzte volle Wochenende vor dem 17.11.


def test_stutzen_steigung_und_handel():
    w = np.arange(200, dtype=float); w[0], w[-1] = -1000.0, 5000.0
    g = E.gestutzt(w)
    assert abs(g.mean()) < 1e-9 and g.max() - g.min() < 200 and g.max() - g.min() == pytest.approx(np.percentile(w, 99) - np.percentile(w, 1))
    rng = np.random.default_rng(7)
    x = rng.normal(0, 0.02, 80)
    assert E.steigung(x, -0.5 * x + 0.003) == pytest.approx(-0.5, abs=1e-9) and E.steigung(x, 0.25 * x) == pytest.approx(0.25, abs=1e-9)
    assert E.steigung(x, np.full(80, 0.01)) == pytest.approx(0.0, abs=1e-12)
    m = -0.5 * x
    sp = np.full(80, 2.0)
    h = E.handel(x, m, sp, -1)                                            # Umkehr: gegen die Wochenend-Bewegung
    gew = -E.gestutzt(x) / np.abs(E.gestutzt(x)).sum()
    assert h["brutto"] == pytest.approx(float(np.sum(gew * m))) and h["brutto"] > 0
    assert h["n85"] == pytest.approx(h["brutto"] - 2 * (1.2 + 2.0) / 1e4) and h["n0"] == pytest.approx(h["brutto"] - 2 * (8.0 + 2.0) / 1e4)
    assert E.handel(x, m, sp, 1)["brutto"] == pytest.approx(-h["brutto"])                    # Fortsetzung ist das Spiegelbild
    assert E.handel(x, m, np.full(80, 0.1), -1)["n85"] == pytest.approx(h["brutto"] - 2 * (1.2 + 0.5) / 1e4)   # Spanne mindestens 0,5 bp
    assert E.handel(np.zeros(5), np.ones(5), np.ones(5), -1) == {"brutto": 0.0, "n85": 0.0, "n0": 0.0}


def kurse_bauen(steigung, n_kontrakte=45, n_we=14, rauschen=0.004, seed=11, ohne=()):
    rng = np.random.default_rng(seed)
    kurse = {f"K{i:02d}USDT": {} for i in range(n_kontrakte)}
    we = E.wochenenden(ms(2026, 6, 1), ms(2026, 6, 1) + (n_we * 7 + 3) * E.TAG)
    for j, (a, b, c) in enumerate(we):
        w = rng.normal(0, 0.02, n_kontrakte); m = steigung * w + rng.normal(0, rauschen, n_kontrakte)
        for i, s in enumerate(sorted(kurse)):
            if (j, i) in ohne:
                continue
            kurse[s][a] = 100.0; kurse[s][b] = 100.0 * (1 + w[i]); kurse[s][c] = 100.0 * (1 + w[i]) * (1 + m[i])
    return kurse, we


def test_teil_2_findet_eine_eingebaute_umkehr_und_handelt_sie():
    kurse, we = kurse_bauen(-0.4)
    sp = {s: 2.0 for s in kurse}
    r = E.teil2(kurse, sp, we[-1][2] + 1)
    assert r["wochenenden"] == len(we) == 14 and r["kontrakte_median"] == 45 and r["steigung_mittel"] == pytest.approx(-0.4, abs=0.05)
    assert r["gesichert"] and r["p"] < 1e-6 and r["anteil_negativ"] == 1.0 and r["handel"]["richtung"] == "Umkehr"
    assert r["handel"]["n85_mittel"] > 0 and r["handel"]["n85_mittel"] < r["handel"]["brutto_mittel"] and r["handel"]["n0_mittel"] < r["handel"]["n85_mittel"]
    assert r["einstufung"] == "C" and len(r["handel"]["je_wochenende_n85"]) == 14 and len(r["je_wochenende"]) == 14
    forts, _ = kurse_bauen(+0.4)
    assert E.teil2(forts, sp, we[-1][2] + 1)["handel"]["richtung"] == "Fortsetzung"
    teuer = E.teil2(kurse, {s: 60.0 for s in kurse}, we[-1][2] + 1)                           # Steigung gesichert, aber die Kosten fressen den Ertrag
    assert teuer["gesichert"] and teuer["handel"]["n85_mittel"] < 0 and teuer["einstufung"] == "B"
    E.sauber(r)                                                                               # lässt sich als JSON ablegen
    import json; json.dumps(E.sauber(r), allow_nan=False)


def test_teil_2_ohne_zusammenhang_und_mit_fehlenden_kursen():
    kurse, we = kurse_bauen(0.0, seed=5)
    r = E.teil2(kurse, {s: 2.0 for s in kurse}, we[-1][2] + 1)
    assert not r["gesichert"] and r["einstufung"] == "A" and "handel" not in r and abs(r["steigung_mittel"]) < 0.1
    # Am dritten Wochenende fehlt 20 Kontrakten ein Kurs: nur 25 übrig, das Wochenende zählt nicht. Am vierten fehlt einem Kontrakt der Montag.
    ohne = {(2, i) for i in range(20)} | {(3, 7)}
    kurse2, we2 = kurse_bauen(-0.4, ohne=ohne)
    r2 = E.teil2(kurse2, {s: 2.0 for s in kurse2}, we2[-1][2] + 1)
    assert r2["wochenenden"] == 13 and r2["ausgelassen"] == [{"samstag": str(dt.datetime.fromtimestamp(we2[2][0] / 1000, UTC).date()), "kontrakte": 25}]
    assert [x["kontrakte"] for x in r2["je_wochenende"]][2] == 44
    assert E.teil2(kurse, {s: 2.0 for s in kurse}, we[1][2] + 1)["einstufung"] == "A"         # nur zwei Wochenenden: zu wenig
