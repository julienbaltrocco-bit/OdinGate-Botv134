"""Zusatztests zu E28 (Prüfer „Gegenlesen“). Schließen Lücken, die eingebaute Fehler in tests/test_e28_nichtkrypto.py nicht finden.

Lauf (eigenständig):
    cd <beliebig> && PYTHONPATH=/home/user/OdinGate-Botv134/swing-hybrid \
        /home/user/OdinGate-Botv134/swing-hybrid/.venv/bin/python -m pytest <diese Datei> -q -p no:cacheprovider

Nur künstliche Daten. Ausnahme: test_kontraktlisten_wie_in_praezisierung_1 liest die Tageskurse und die Spannen-Stichprobe
(schon bekannte Angaben, keine Ergebnisse) und wird übersprungen, wenn diese Dateien fehlen.
e28_nichtkrypto.haupt() läuft hier nur in test_hauptlauf_… mit umgebogenen Pfaden auf künstlichen Dateien, nie auf den echten Daten.
"""
import datetime as dt
import io
import json
import sys
import types
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from forschung.experimente import e28_daten as D
from forschung.experimente import e28_nichtkrypto as E
from forschung.papier import runner as R
from forschung.papier.strategien import orderbuch_stuetze as OS

UTC = dt.timezone.utc
K = 300_000
H = 3_600_000
P = {"tiefe_pct": 5, "fenster": 288, "min_perioden": 200, "einstieg_z": 3.0, "ausstieg_z": 1.0, "zeitlimit": 48}
LEER = (np.array([], dtype=np.int64), np.array([]))


def ms(*a):
    return int(dt.datetime(*a, tzinfo=UTC).timestamp() * 1000)


T0 = ms(2026, 6, 1)


def reihe(n, start=T0, kurs=100.0):
    return start + K * np.arange(n, dtype=np.int64), np.full((n, 4), kurs)


def ruhig(n):
    return 0.01 * np.sin(np.arange(n))


def trade(ein, n85, sym="AUSDT", richtung=1, aus=None):
    return {"sym": sym, "ein": ein, "aus": ein + K if aus is None else aus, "richtung": richtung, "z": 3.0, "roh_bp": n85 + 5, "slip_bp": 2.0,
            "funding_bp": 0.0, "n85_bp": n85, "n0_bp": n85 - 13.6}


# ------------------------------------------------------------------ festgelegte Zahlen ----
def test_festgelegte_zahlen_stehen_so_im_programm():
    """Schwellen und Stichtage aus Abschnitt 56; ein Tippfehler in einer dieser Zahlen fiele sonst keinem Test auf."""
    assert (E.TAKER_BP, E.REBATE, E.SPANNE_MIN_BP, E.VORLAUF_TAGE) == (8.0, 0.85, 0.5, 2)
    assert (E.ZIEHUNGEN, E.STARTWERT, E.P_GRENZE, E.MIN_TRADES, E.MIN_KONTRAKTE_WE) == (5000, 28, 0.025, 300, 30)
    assert E.HAELFTE_AB == ms(2026, 9, 1)
    assert E.ROHSTOFF == {x + "USDT" for x in ("XAU", "XAG", "CL", "BZ", "PAXG")} and E.FONDS == {x + "USDT" for x in ("SOXL", "SOXS", "QQQ", "EWY", "DRAM", "MUU")}
    assert D.ENDE_TEIL1 == dt.date(2026, 11, 20) and D.ERSTER_SPAETESTENS == pd.Timestamp("2026-07-31") and D.UMSATZ_BIS == pd.Timestamp("2026-10-31")
    assert (D.SPANNE_HOECHSTENS_BP, D.ANZAHL_TEIL1, D.TIEFE_PCT) == (10.0, 30, 5)
    assert D.YUBIT_BIS == dt.datetime(2026, 11, 17, tzinfo=UTC)                      # bis einschließlich Montag, 16.11.2026


# ------------------------------------------------------------------------ Teil 1 ----
def test_vorlauf_endet_genau_48_stunden_nach_der_ersten_kerze():
    """So rechnet das Programm: Einstiege zählen ab erster Kerze + 48 h (576 Kerzen Vorlauf wie im Papier-Runner), nicht ab 00:00 UTC
    des dritten Kalendertags. Beginnt die Reihe mitten am Tag (hier 13:40), unterscheiden sich beide Lesarten."""
    n = 288 * 4
    start = T0 + 164 * K                                                             # erste Kerze 13:40 UTC
    zeit, ohlc = reihe(n, start)

    def lauf(i):
        u = ruhig(n)
        u[i] = 0.5
        return E.trades_kontrakt("XUSDT", zeit, ohlc, u, *LEER, 1.0, P)
    assert lauf(574) == []                                                           # Einstiegskerze läge 5 Minuten vor Ablauf der 48 h
    assert [x["ein"] for x in lauf(575)] == [start + 2 * E.TAG]                      # genau 48 h nach der ersten Kerze: zählt
    assert lauf(500) == []                                                           # dritter Kalendertag (ab Kerze 412), aber noch im Vorlauf


def test_fehlendes_uebergewicht_kein_einstieg_und_ausstieg_erst_am_zeitlimit():
    n = 288 * 6
    zeit, ohlc = reihe(n)
    s = 288 * 4 + 50
    u = ruhig(n)
    u[s] = np.nan                                                                    # an der Signalkerze fehlt das Übergewicht: kein Einstieg
    assert E.trades_kontrakt("XUSDT", zeit, ohlc, u, *LEER, 1.0, P) == []
    u = ruhig(n)
    u[s] = 0.5
    u[s + 1: s + 101] = np.nan                                                       # nach dem Einstieg fehlt die Tiefe: kein Ausstieg über z, erst das Zeitlimit
    t = E.trades_kontrakt("XUSDT", zeit, ohlc, u, *LEER, 1.0, P)
    assert [(x["ein"], x["aus"]) for x in t] == [(int(zeit[s + 1]), int(zeit[s + 1 + 48]))]
    u = ruhig(n)
    a0 = 288 * 3
    u[a0: a0 + 288] = np.nan                                                         # ein ganzer Tag ohne Tiefe (wie am 08.10.2026)
    u[a0 + 288 + 100] = u[a0 + 288 + 250] = 0.5                                      # Ausschlag nach 100 neuen Werten (zu wenige) und nach 250
    t = E.trades_kontrakt("XUSDT", zeit, ohlc, u, *LEER, 1.0, P)
    assert [x["ein"] for x in t] == [int(zeit[a0 + 288 + 251])]                      # erst wieder mit mindestens 200 Werten im Fenster


def test_kerzenluecke_regel_zaehlt_in_kerzen_und_die_luecke_wird_gemeldet(monkeypatch):
    """Die Regel zählt in Kerzen: Fehlen nach dem Signal Kerzen, wird an der nächsten vorhandenen Kerze eingestiegen (hier einen Tag später).
    Das ist das Verhalten von OS-1.1; der Test hält es fest und prüft, dass teil1 die Lücke je Kontrakt zählt."""
    n = 288 * 7
    zeit, ohlc = reihe(n)
    u = ruhig(n)
    s = 288 * 4 + 50
    u[s] = 0.5
    da = np.ones(n, bool)
    da[s + 1: s + 1 + 288] = False
    t = E.trades_kontrakt("XUSDT", zeit[da], ohlc[da], u[da], *LEER, 1.0, P)
    assert [x["ein"] for x in t] == [int(zeit[s + 1 + 288])]
    monkeypatch.setattr(OS, "trades", lambda kz, uu, p, start: [])
    r = E.teil1(["XUSDT"], lambda sym: {"zeit": zeit[da], "ohlc": ohlc[da], "u": u[da], "fund_zeit": LEER[0], "fund_rate": LEER[1]}, {"XUSDT": 1.0})
    assert r["je_kontrakt"]["XUSDT"]["luecken"] == 1 and r["je_kontrakt"]["XUSDT"]["kerzen"] == n - 288


def test_tag_eines_trades_ist_der_utc_tag_des_einstiegs():
    t0 = ms(2026, 7, 1)
    spaet = trade(t0 + 23 * H + 55 * 60_000, 1.0, aus=t0 + E.TAG + 30 * 60_000)      # Einstieg 23:55, Ausstieg am Folgetag
    frueh = trade(t0 + 10 * H, 2.0)
    assert E.urteil1([spaet, frueh])["tage_mit_einstieg"] == 1
    assert E.urteil1([spaet, trade(t0 + E.TAG, 2.0)])["tage_mit_einstieg"] == 2      # 00:00 UTC gehört zum neuen Tag


def test_zufallspruefung_gegen_eine_unabhaengige_nachrechnung():
    """Rechnet die Ziehung Tag für Tag nach (Startwert 28, 5.000 Ziehungen, so viele Tage wie vorhanden, Mittel über alle Trades der
    gezogenen Tage, Anteil ≤ 0). Findet falschen Startwert, falsche Zahl der Ziehungen oder Tage und ein Mittel über Tagesmittel."""
    r0 = np.random.default_rng(1)
    tag = r0.integers(100, 140, 500)
    wert = r0.normal(1.0, 30.0, 500)
    tage = np.unique(tag)
    je_tag = [wert[tag == t] for t in tage]
    rng = np.random.default_rng(28)
    zug = rng.integers(0, len(tage), size=(5000, len(tage)))
    nicht_positiv = sum(float(np.concatenate([je_tag[i] for i in z]).mean()) <= 0 for z in zug)
    p = E.tage_stichprobe(tag, wert)
    assert p == pytest.approx(nicht_positiv / 5000, abs=1e-12) and 0.02 < p < 0.98
    assert E.tage_stichprobe(np.array([1, 2, 3]), np.zeros(3)) == 1.0                # Mittel genau null zählt als „nicht über null“


def test_einstufung_teil_1_an_den_grenzen():
    tag = E.TAG
    juli, okt = ms(2026, 7, 1), ms(2026, 10, 1)
    gut = [trade(juli + i * tag // 4, 5.0 + (i % 3)) for i in range(150)] + [trade(okt + i * tag // 4, 4.0 + (i % 3)) for i in range(150)]
    assert len(gut) == 300 and E.urteil1(gut)["einstufung"] == "C"                   # genau 300 Trades genügen
    assert E.urteil1(gut[1:])["einstufung"] == "B"                                   # 299 nicht
    # p zwischen 2,5 % und 5 %: positiv in beiden Hälften, genug Trades, aber nicht gesichert -> B (nicht C)
    rng = np.random.default_rng(6)
    werte = rng.normal(2.6, 40.0, 800)
    knapp = [trade((juli if i < 400 else okt) + (i % 400) * tag // 10, float(x)) for i, x in enumerate(werte)]
    u = E.urteil1(knapp)
    assert u["erste_haelfte"]["n85_bp"] > 0 and u["zweite_haelfte"]["n85_bp"] > 0 and u["alle"]["trades"] == 800
    assert 0.025 <= u["p"] < 0.05 and u["einstufung"] == "B"


def test_teil_1_ergebnis_laesst_sich_ablegen_auch_mit_leerer_und_kurzer_reihe(monkeypatch):
    zeit, ohlc = reihe(288 * 5)
    u = np.zeros(len(zeit))
    daten = {"AUSDT": (zeit, ohlc, u), "KURZUSDT": (zeit[:150], ohlc[:150], u[:150]),
             "LEERUSDT": (zeit[:0], ohlc[:0], u[:0])}
    sa = ms(2026, 6, 6, 12)
    monkeypatch.setattr(OS, "trades", lambda kz, uu, p, start: [
        {"ein": sa, "aus": sa + K, "richtung": 1.0, "ein_kurs": 100.0, "aus_kurs": 100.5, "z": 3.0, "schlimmst_bp": 0.0}])
    r = E.teil1(list(daten), lambda s: {"zeit": daten[s][0], "ohlc": daten[s][1], "u": daten[s][2], "fund_zeit": LEER[0], "fund_rate": LEER[1]},
                {s: 1.0 for s in daten})
    assert r["alle"]["trades"] == 1 and r["je_kontrakt"]["KURZUSDT"]["trades"] == 0 and r["je_kontrakt"]["LEERUSDT"] == {
        "trades": 0, "gruppe": "Einzelwert", "spanne_bp": 1.0, "kerzen": 0, "u_fehlt": 0, "luecken": 0, "von": "",
        "funding_fehlt_monate": [], "fehlende_dateien": []}
    assert r["zweite_haelfte"] == {"trades": 0} and r["einstufung"] == "B"            # positiv, aber nur eine Hälfte und zu wenige Trades
    text = json.dumps(E.sauber(r), allow_nan=False)
    assert json.loads(text)["je_kontrakt"]["AUSDT"]["trades"] == 1


# ------------------------------------------------------------------------ Teil 2 ----
def kurse_bauen(steigung, n_kontrakte=45, n_we=14, rauschen=0.004, seed=11, ohne=(), gleich=()):
    rng = np.random.default_rng(seed)
    kurse = {f"K{i:02d}USDT": {} for i in range(n_kontrakte)}
    we = E.wochenenden(ms(2026, 6, 1), ms(2026, 6, 1) + (n_we * 7 + 3) * E.TAG)
    for j, (a, b, c) in enumerate(we):
        w = rng.normal(0, 0.02, n_kontrakte)
        m = steigung * w + rng.normal(0, rauschen, n_kontrakte)
        if j in gleich:
            w = np.zeros(n_kontrakte)                                                # alle Kontrakte über das Wochenende unverändert
        for i, s in enumerate(sorted(kurse)):
            if (j, i) in ohne:
                continue
            kurse[s][a] = 100.0
            kurse[s][b] = 100.0 * (1 + w[i])
            kurse[s][c] = 100.0 * (1 + w[i]) * (1 + m[i])
    return kurse, we


def test_teil_2_genau_30_kontrakte_zaehlen_29_nicht():
    kurse, we = kurse_bauen(-0.4, n_kontrakte=30, ohne={(0, 0)})
    r = E.teil2(kurse, {s: 2.0 for s in kurse}, we[-1][2] + 1)
    assert r["wochenenden"] == 13 and r["ausgelassen"] == [{"samstag": "2026-06-06", "kontrakte": 29}]
    assert all(x["kontrakte"] == 30 for x in r["je_wochenende"])


def test_teil_2_haelften_t_wert_und_einstufung(monkeypatch):
    """13 Wochenenden: die erste Hälfte hat eines mehr (7 gegen 6). C nur mit Mittel > 0, t > 2 und beiden Hälften positiv."""
    kurse, we = kurse_bauen(-0.4, n_we=13)
    sp = {s: 2.0 for s in kurse}

    def mit(n85):
        folge = iter(n85)
        monkeypatch.setattr(E, "handel", lambda w, m, s, vz: dict.fromkeys(("brutto", "n85", "n0"), next(folge)))
        return E.teil2(kurse, sp, we[-1][2] + 1)
    steigend = [i / 1000 for i in range(1, 14)]
    r = mit(steigend)
    assert r["wochenenden"] == 13 and r["gesichert"] and r["einstufung"] == "C"
    assert r["handel"]["n85_erste_haelfte"] == pytest.approx(0.004) and r["handel"]["n85_zweite_haelfte"] == pytest.approx(0.0105)
    erste_negativ = [-0.001] * 7 + [0.010, 0.011, 0.010, 0.011, 0.010, 0.011]
    r = mit(erste_negativ)
    assert r["handel"]["n85_mittel"] > 0 and r["handel"]["t_n85"] > 2 and r["handel"]["n85_erste_haelfte"] < 0 and r["einstufung"] == "B"
    schwankend = [0.005 if i % 2 == 0 else -0.004 for i in range(13)]
    r = mit(schwankend)
    assert r["handel"]["n85_mittel"] > 0 and 0 < r["handel"]["t_n85"] < 2 and r["handel"]["n85_erste_haelfte"] > 0 and r["handel"]["n85_zweite_haelfte"] > 0
    assert r["einstufung"] == "B"                                                    # positiv in beiden Hälften, aber t unter 2


def test_teil_2_p_zwischen_2_5_und_5_prozent_ist_nicht_gesichert(monkeypatch):
    """Zweiseitig bei 2,5 %: Eine einseitige Prüfung oder eine Grenze von 5 % würde dieses Beispiel als gesichert einstufen."""
    from scipy import stats
    kurse, we = kurse_bauen(-0.4, n_we=13)
    werte = [-0.9, 0.3, -0.5, -0.1, -0.7, 0.2, -0.4, -0.6, 0.1, -0.2, -0.8, 0.4, -0.3]
    p = float(stats.ttest_1samp(werte, 0.0).pvalue)
    assert 0.025 < p < 0.05
    folge = iter(werte)
    monkeypatch.setattr(E, "steigung", lambda w, m: next(folge))
    r = E.teil2(kurse, {s: 2.0 for s in kurse}, we[-1][2] + 1)
    assert r["p"] == pytest.approx(p) and not r["gesichert"] and r["einstufung"] == "A" and "handel" not in r


def test_teil_2_wochenende_ohne_streuung_darf_das_ergebnis_nicht_still_entwerten():
    """Präzisierung 9: Ein Wochenende ohne Streuung von W zählt nicht und steht unter „ausgelassen“ (vorher machte es t und p unbestimmt)."""
    kurse, we = kurse_bauen(-0.4, gleich={3})
    r = E.teil2(kurse, {s: 2.0 for s in kurse}, we[-1][2] + 1)
    assert r["p"] is not None and np.isfinite(r["p"]) and r["gesichert"]             # die übrigen 13 Wochenenden zeigen die Umkehr deutlich
    samstag = str(dt.datetime.fromtimestamp(we[3][0] / 1000, UTC).date())
    assert r["wochenenden"] == 13 and r["ausgelassen"] == [{"samstag": samstag, "kontrakte": 45, "grund": "keine Streuung"}]
    assert samstag not in [x["samstag"] for x in r["je_wochenende"]] and len(r["handel"]["je_wochenende_n85"]) == 13
    assert len(r["handel"]["je_wochenende_brutto"]) == 13 and len(r["handel"]["je_wochenende_n0"]) == 13
    assert all(b > n85 > n0 for b, n85, n0 in zip(r["handel"]["je_wochenende_brutto"], r["handel"]["je_wochenende_n85"], r["handel"]["je_wochenende_n0"]))


def test_teil_2_zu_wenige_wochenenden_ist_a_und_nennt_die_ausgelassenen():
    kurse, we = kurse_bauen(-0.4, n_we=3, gleich={1})
    r = E.teil2(kurse, {s: 2.0 for s in kurse}, we[-1][2] + 1)
    assert r["wochenenden"] == 2 and r["einstufung"] == "A" and r["hinweis"] == "zu wenige Wochenenden" and len(r["ausgelassen"]) == 1


# ------------------------------------------------ Funding-Lücke (Präzisierung 6) ----
def test_monate_ohne_funding_und_kennzeichnung_der_trades(monkeypatch):
    start = ms(2026, 9, 28)
    zeit, ohlc = reihe(288 * 40, start=start)                                        # 28.09. bis 06.11.2026
    fund_zeit = np.array([ms(2026, 9, 29, 8), ms(2026, 10, 31, 16)], dtype=np.int64)  # September und Oktober vorhanden, November fehlt
    fund_rate = np.array([0.0001, 0.0002])
    assert E.monate_ohne_funding(zeit, fund_zeit) == ["2026-11"]
    assert E.monate_ohne_funding(zeit, fund_zeit[:1]) == ["2026-10", "2026-11"] and E.monate_ohne_funding(zeit[:0], fund_zeit) == []
    okt, grenze, nov = ms(2026, 10, 31, 15, 55), ms(2026, 10, 31, 23, 55), ms(2026, 11, 3, 12)
    monkeypatch.setattr(OS, "trades", lambda kz, uu, p, s: [
        {"ein": okt, "aus": okt + 3 * K, "richtung": 1.0, "ein_kurs": 100.0, "aus_kurs": 101.0, "z": 3.0, "schlimmst_bp": 0.0},      # ganz im Oktober, mit Funding
        {"ein": grenze, "aus": grenze + 2 * K, "richtung": 1.0, "ein_kurs": 100.0, "aus_kurs": 101.0, "z": 3.0, "schlimmst_bp": 0.0},  # endet im November
        {"ein": nov, "aus": nov + K, "richtung": -1.0, "ein_kurs": 100.0, "aus_kurs": 101.0, "z": -3.0, "schlimmst_bp": 0.0}])
    t = E.trades_kontrakt("AUSDT", zeit, ohlc, np.zeros(len(zeit)), fund_zeit, fund_rate, 1.0, P)
    assert [x["funding_fehlt"] for x in t] == [False, True, True]
    assert t[0]["funding_bp"] == pytest.approx(-2.0) and t[1]["funding_bp"] == 0.0 and t[2]["funding_bp"] == 0.0
    monkeypatch.setattr(E, "os11", lambda: P)
    aus = []
    r = E.teil1(["AUSDT"], lambda s: {"zeit": zeit, "ohlc": ohlc, "u": np.zeros(len(zeit)), "fund_zeit": fund_zeit, "fund_rate": fund_rate,
                                      "fehlend": ["2026-10-07 tiefe"]}, {"AUSDT": 1.0}, aus)
    assert r["funding_fehlt"]["trades"] == 2 and r["funding_fehlt"]["nur_trades_mit_funding_angabe"]["trades"] == 1
    assert r["je_kontrakt"]["AUSDT"]["funding_fehlt_monate"] == ["2026-11"] and r["je_kontrakt"]["AUSDT"]["fehlende_dateien"] == ["2026-10-07 tiefe"]
    assert len(aus) == 3 and r["alle"]["trades"] == 3


# ------------------------------------------------ Hauptlauf auf künstlichen Dateien ----
def test_hauptlauf_liest_eroeffnungskurse_und_legt_ergebnis_und_trades_ab(monkeypatch, tmp_path):
    """haupt() nur mit umgebogenen Pfaden und künstlichen Dateien: Teil 2 nimmt die Eröffnung der Stundenkerze (Spalte 0), das Datenende
    kommt aus e28_daten, Kontrakte ohne Datei oder ohne Kerzen fehlen ohne Abbruch, Ergebnisdatei und Trade-Tabelle entstehen."""
    kurse, we = kurse_bauen(-0.4, n_kontrakte=32, n_we=6)
    syms = sorted(kurse)
    (tmp_path / "teil1").mkdir(); (tmp_path / "teil2").mkdir()
    for s in syms[:-1]:                                                              # der letzte Kontrakt hat keine Datei
        zeit = np.array(sorted(kurse[s]), dtype=np.int64)
        ohlc = np.array([[kurse[s][int(z)], 999.0, 0.5, 777.0] for z in zeit])        # nur Spalte 0 trägt den richtigen Kurs
        np.savez_compressed(tmp_path / "teil2" / f"{s}.npz", zeit=zeit, ohlc=ohlc)
    np.savez_compressed(tmp_path / "teil2" / "LEERUSDT.npz", zeit=np.array([], dtype=np.int64), ohlc=np.zeros((0, 4)))
    zeit, ohlc = reihe(288 * 5)
    np.savez_compressed(tmp_path / "teil1" / "AUSDT.npz", zeit=zeit, ohlc=ohlc, u=np.zeros(len(zeit)), fund_zeit=np.array([T0 + 100 * K], dtype=np.int64),
                        fund_rate=np.array([0.0001]), fehlend=np.array(json.dumps([["2026-06-02", "tiefe"]])))
    sa = ms(2026, 6, 4, 12)
    monkeypatch.setattr(OS, "trades", lambda kz, uu, p, start: [
        {"ein": sa, "aus": sa + K, "richtung": -1.0, "ein_kurs": 100.0, "aus_kurs": 99.0, "z": -3.25, "schlimmst_bp": 0.0}])
    tabelle = pd.DataFrame({"symbol": syms + ["LEERUSDT", "AUSDT"], "spanne_bp": 2.0})
    monkeypatch.setattr(D, "ZIEL", tmp_path)
    monkeypatch.setattr(D, "kandidaten", lambda: tabelle)
    monkeypatch.setattr(D, "universum_teil1", lambda: tabelle[tabelle.symbol == "AUSDT"])
    monkeypatch.setattr(D, "universum_teil2", lambda: tabelle[tabelle.symbol != "AUSDT"])
    monkeypatch.setattr(D, "YUBIT_BIS", dt.datetime.fromtimestamp((we[-1][2] + H) / 1000, UTC))
    monkeypatch.setattr(E, "os11", lambda: P)
    monkeypatch.setattr(E, "ERGEBNIS", tmp_path / "aus" / "e.json")
    monkeypatch.setattr(E, "TRADES", tmp_path / "aus" / "t.csv")
    erg = E.haupt()
    abgelegt = json.loads((tmp_path / "aus" / "e.json").read_text())
    assert abgelegt["teil_2"]["kontrakte_mit_daten"] == 31 and abgelegt["teil_2"]["wochenenden"] == 6
    assert abgelegt["teil_2"]["steigung_mittel"] == pytest.approx(-0.4, abs=0.1) and abgelegt["teil_2"]["je_wochenende"][0]["kontrakte"] == 31
    assert abgelegt["teil_1"]["alle"]["trades"] == 1 and abgelegt["teil_1"]["je_kontrakt"]["AUSDT"]["fehlende_dateien"] == ["2026-06-02 tiefe"]
    assert abgelegt["daten"] == {"teil_1_bis": str(D.ENDE_TEIL1), "teil_2_bis": str(D.YUBIT_BIS.date()), "trades_tabelle": "t.csv"}
    assert erg["teil_1"]["einstufung"] == abgelegt["teil_1"]["einstufung"] == "B"
    zeilen = (tmp_path / "aus" / "t.csv").read_text().splitlines()
    assert zeilen[0] == ",".join(E.SPALTEN) and len(zeilen) == 2
    werte = dict(zip(E.SPALTEN, zeilen[1].split(",")))
    assert werte["sym"] == "AUSDT" and int(werte["ein"]) == sa and werte["richtung"] == "-1" and float(werte["roh_bp"]) == pytest.approx(100.0)
    assert float(werte["n85_bp"]) == pytest.approx(100.0 - 4.0 - 2.4) and werte["funding_fehlt"] == "0"
    # Datenende: ein Wochenende, dessen Montagskurs nicht mehr vor dem Datenende liegt, zählt nicht
    monkeypatch.setattr(D, "YUBIT_BIS", dt.datetime.fromtimestamp(we[-1][2] / 1000, UTC))
    assert E.haupt()["teil_2"]["wochenenden"] == 5


def test_laden_schreibt_erst_vollstaendig_und_vermerkt_fehlenden_funding_monat(monkeypatch, tmp_path):
    monkeypatch.setattr(D, "ZIEL", tmp_path)
    monkeypatch.setattr(D, "ENDE_TEIL1", dt.date(2026, 6, 1))
    t = ms(2026, 5, 31)
    monkeypatch.setattr(D.R, "kerzen_tag", lambda sym, tag, cache: [(ms(tag.year, tag.month, tag.day) + i * K, 1.0, 1.0, 1.0, 1.0) for i in range(288)])
    monkeypatch.setattr(D.R, "tiefe_tag", lambda sym, tag, stufe, cache: {})
    monkeypatch.setattr(D.R, "funding_monat", lambda sym, monat, cache: {t + 8 * H: 0.0001} if monat == "2026-05" else None)
    r = D.laden_teil1("XUSDT", dt.date(2026, 5, 31))
    assert r["fehlende_dateien"] == 1 and r["funding"] == 1
    with np.load(tmp_path / "teil1" / "XUSDT.npz") as z:
        assert json.loads(str(z["fehlend"])) == [["2026-06", "funding"]]
    assert sorted(p.name for p in (tmp_path / "teil1").iterdir()) == ["XUSDT.npz"]    # keine halbe Datei bleibt liegen


# ------------------------------------------------------- e28_daten: Kontraktlisten ----
PRAEZISIERUNG_1 = ("SNDK, XAU, SOXL, SKHYNIX, SPCX, XAG, CL, MU, SKHY, BZ, SOXS, SAMSUNG, DRAM, CRCL, QQQ, INTC, MRVL, NVDA, PAXG, EWY, MUU, MSTR, "
                   "TSLA, NBIS, LITE, AMD, AAOI, CBRS, GOOGL, ZHIPU").split(", ")


def test_kontraktlisten_wie_in_praezisierung_1():
    if not ((D.ROOT / "data/candles/1d/SNDKUSDT.parquet").exists() and (D.ROOT / "data/processed/yubit_spannen_stichprobe.csv").exists()
            and (D.ROOT / "data/processed/listings_inventur.csv").exists()):
        pytest.skip("Tageskurse oder Spannen-Stichprobe liegen hier nicht vor")
    u1, u2 = D.universum_teil1(), D.universum_teil2()
    assert [s[:-4] for s in u1.symbol] == PRAEZISIERUNG_1
    assert u1.erster_tag.max() <= pd.Timestamp("2026-07-31") and round(float(u1.spanne_bp.max()), 1) == 6.7 and 39e6 < u1.umsatz.min() < 41e6
    assert len(u2) == 134 and (u2.spanne_bp <= 10.0).all() and set(u1.symbol) <= set(u2.symbol) and list(u2.symbol) == sorted(u2.symbol)
    assert not {"KORUUSDT", "SNXXUSDT"} & set(u2.symbol)                             # fallen wegen ihrer Spanne heraus


def test_kontraktregel_auf_kuenstlichen_angaben(monkeypatch):
    """Erster Tag bis 31.07. (einschließlich), Spanne höchstens 10 bp (einschließlich), Rang nach dem Median des Werktagsumsatzes bis 31.10."""
    namen = [f"T{i:02d}USDT" for i in range(40)]
    erster = {s: pd.Timestamp("2026-05-04") for s in namen}
    erster["T02USDT"], erster["T03USDT"] = pd.Timestamp("2026-07-31"), pd.Timestamp("2026-08-01")
    spanne = {s: 2.0 for s in namen}
    spanne["T00USDT"], spanne["T01USDT"] = 10.0, 10.01
    spanne["KRYPTOUSDT"] = 1.0
    tage = pd.date_range("2026-06-01", "2026-11-20", freq="D")

    def umsatz(sym):
        i = int(sym[1:3])
        v = np.full(len(tage), 1000.0 - 10 * min(i, 34))                              # T34 und T35 gleich: das Symbol entscheidet
        if i == 4:
            v[:] = np.where(tage.day_of_week < 5, 1.0, 1e9)                           # nur am Wochenende viel Umsatz
        if i == 5:
            v[:] = np.where(tage <= pd.Timestamp("2026-10-31"), 1.0, 1e9)             # erst im November viel Umsatz
        if i == 6:
            v[:] = 1.0
            v[2] = 1e12                                                               # ein einzelner Ausreißer-Werktag (Mittel hoch, Median nicht)
        return pd.DataFrame({"quote_volume": v}, index=pd.DatetimeIndex(tage, name="open_time"))

    inventur = pd.DataFrame({"symbol": namen + ["KRYPTOUSDT"], "erster_tag": [erster[s] for s in namen] + [pd.Timestamp("2026-05-04")],
                             "tradfi": [True] * 40 + [False]})
    monkeypatch.setattr(D.E25, "symbole", lambda: inventur.copy())
    monkeypatch.setattr(D.E25, "spannen", lambda: dict(spanne))
    monkeypatch.setattr(D.pd, "read_parquet", lambda pfad, columns=None: umsatz(Path(pfad).stem))
    u1 = D.universum_teil1()
    assert list(u1.symbol) == ["T00USDT", "T02USDT"] + [f"T{i:02d}USDT" for i in range(7, 35)]
    u2 = D.universum_teil2()
    assert list(u2.symbol) == [s for s in namen if s != "T01USDT"]


# ------------------------------------------------------------- e28_daten: Laden ----
def zip_csv(text: str) -> bytes:
    puffer = io.BytesIO()
    with zipfile.ZipFile(puffer, "w") as z:
        z.writestr("datei.csv", text)
    return puffer.getvalue()


def test_tiefe_tag_ordnet_schnappschuesse_der_kerze_zu_in_der_sie_liegen(monkeypatch):
    """Kein Blick in die Zukunft: Ein Schnappschuss um 00:04:59 gehört zur Kerze 00:00, einer um 00:05:00 schon zur Kerze 00:05."""
    text = ("timestamp,percentage,depth,notional\n"
            "2026-06-01 00:00:10,-5,1,300\n2026-06-01 00:00:10,5,1,100\n2026-06-01 00:00:10,-1,1,999\n2026-06-01 00:00:10,1,1,1\n"
            "2026-06-01 00:04:59,-5,1,500\n2026-06-01 00:04:59,5,1,100\n"
            "2026-06-01 00:05:00,-5,1,100\n2026-06-01 00:05:00,5,1,300\n"
            "2026-06-01 00:10:30,-5,1,100\n")                                        # nur eine Seite: kein Wert für diese Kerze
    monkeypatch.setattr(R, "holen", lambda url, cache: zip_csv(text))
    u = R.tiefe_tag("XUSDT", dt.date(2026, 6, 1), 5, Path("/nirgends"))
    assert u == {T0: pytest.approx((400 - 100) / (400 + 100)), T0 + K: pytest.approx(-0.5)}


def test_laden_teil1_reihe_ohne_verschiebung_doppelte_weg_fehlende_tage_vermerkt(monkeypatch, tmp_path):
    monkeypatch.setattr(D, "ZIEL", tmp_path)
    monkeypatch.setattr(D, "ENDE_TEIL1", dt.date(2026, 6, 3))
    u_von = lambda z: ((z // K) % 997) / 997 - 0.5                                    # eindeutig je Kerze: jede Verschiebung fällt auf

    def kerzen(sym, tag, cache):
        if tag == dt.date(2026, 6, 3):
            return None                                                              # Kerzen dieses Tages fehlen
        t = ms(tag.year, tag.month, tag.day)
        k = [(t + i * K, 100.0 + i, 101.0 + i, 99.0 + i, 100.5 + i) for i in range(288)]
        if tag == dt.date(2026, 6, 2):
            k = k[::-1] + [k[0]] + [(t - K, 1.0, 1.0, 1.0, 1.0)]                      # unsortiert, eine Kerze doppelt, letzte Kerze des Vortags noch einmal (anders)
        return k

    def tiefe(sym, tag, stufe, cache):
        assert stufe == 5 and Path(cache).is_dir() and Path(cache).parent == tmp_path
        if tag == dt.date(2026, 6, 1):
            return None                                                              # Tiefe dieses Tages fehlt
        t = ms(tag.year, tag.month, tag.day)
        return {t + i * K: u_von(t + i * K) for i in range(288) if i != 7}           # eine einzelne Kerze ohne Wert

    f1, f2, f3 = ms(2026, 5, 31, 16), ms(2026, 6, 1, 0), ms(2026, 6, 1, 8)
    monkeypatch.setattr(D.R, "kerzen_tag", kerzen)
    monkeypatch.setattr(D.R, "tiefe_tag", tiefe)
    monkeypatch.setattr(D.R, "funding_monat", lambda sym, monat, cache: {"2026-05": {f1: 0.0001}, "2026-06": {f3: 0.0003, f2: -0.0002}}[monat])
    r = D.laden_teil1("XUSDT", dt.date(2026, 5, 31))
    assert r == {"sym": "XUSDT", "kerzen": 864, "u_vorhanden": 2 * 287, "funding": 3, "fehlende_dateien": 2}
    with np.load(tmp_path / "teil1" / "XUSDT.npz") as z:
        assert set(z.keys()) == {"zeit", "ohlc", "u", "fund_zeit", "fund_rate", "fehlend"}
        zeit, ohlc, u = z["zeit"], z["ohlc"], z["u"]
        assert json.loads(str(z["fehlend"])) == [["2026-06-01", "tiefe"], ["2026-06-03", "kerzen"]]
        assert z["fund_zeit"].tolist() == [f1, f2, f3] and z["fund_rate"].tolist() == [0.0001, -0.0002, 0.0003]
    t31, t1, t2 = ms(2026, 5, 31), ms(2026, 6, 1), ms(2026, 6, 2)
    assert zeit.tolist() == [t31 + i * K for i in range(864)] and ohlc.shape == (864, 4)
    assert ohlc[287].tolist() == [387.0, 388.0, 386.0, 387.5] and ohlc[575].tolist() == [1.0, 1.0, 1.0, 1.0]   # bei doppelten Kerzen gilt die zuletzt gelesene
    assert ohlc[576].tolist() == [100.0, 101.0, 99.0, 100.5]
    tag1 = (zeit >= t1) & (zeit < t2)
    assert np.isnan(u[tag1]).all() and np.isnan(u[7]) and np.isnan(u[576 + 7]) and int(np.isfinite(u).sum()) == 2 * 287
    ok = np.isfinite(u)
    assert np.allclose(u[ok], [u_von(int(x)) for x in zeit[ok]], rtol=0, atol=1e-15)                          # U steht an seiner eigenen Kerze
    assert D.laden_teil1("XUSDT", dt.date(2026, 5, 31)) == {"sym": "XUSDT", "schon_da": True}
    assert not [p for p in tmp_path.iterdir() if p.name.startswith("tmp")]                                    # die Tiefe-Zwischenordner sind wieder weg


def test_laden_teil2_fenster_schliessen_luecken_und_ueberlappungsfrei_an(monkeypatch, tmp_path):
    von, bis = dt.datetime(2026, 1, 1, tzinfo=UTC), dt.datetime(2026, 3, 1, tzinfo=UTC)                       # 1.416 Stunden: zwei Abrufe
    v, e = int(von.timestamp() * 1000), int(bis.timestamp() * 1000)
    gelistet = v + 30 * H
    abrufe = []

    class Yubit:
        def __init__(self, pause=0.0):
            self.aufrufe = 0

        def kerzen(self, symbol, minuten=60, limit=3, start_ms=None, ende_ms=None):
            self.aufrufe += 1
            abrufe.append((symbol, minuten, limit, start_ms, ende_ms))
            stunden = [h for h in range(start_ms, ende_ms + 1, H) if h >= gelistet][:limit]                  # Grenzen einschließlich, wie die Börse
            return [{"start": h, "open": h / H, "high": h / H + 1, "low": h / H - 1, "close": h / H + 0.5} for h in stunden][::-1]

    monkeypatch.setitem(sys.modules, "vorwaertstest.yubit", types.SimpleNamespace(Yubit=Yubit))
    monkeypatch.setattr(D, "ZIEL", tmp_path)
    monkeypatch.setattr(D, "YUBIT_VON", von)
    monkeypatch.setattr(D, "YUBIT_BIS", bis)
    r = D.laden_teil2("XUSDT")
    assert abrufe == [("XUSDT", 60, 1000, v, v + 999 * H), ("XUSDT", 60, 1000, v + 1000 * H, e)]
    assert r == {"sym": "XUSDT", "stunden": 1416 - 30, "von": "2026-01-02 06:00:00", "abrufe": 2}
    with np.load(tmp_path / "teil2" / "XUSDT.npz") as z:
        zeit, ohlc = z["zeit"], z["ohlc"]
    assert zeit.tolist() == list(range(gelistet, e, H))                                                      # lückenlos, sortiert, die Kerze um 00:00 des Endtags gehört nicht dazu
    assert ohlc[:, 0].tolist() == [h / H for h in zeit.tolist()] and ohlc.shape == (len(zeit), 4)            # Spalte 0 ist die Eröffnung


# ------------------------------------------------ Nachträge: Wochentag, Gleichlauf mit dem Papier-Runner ----
def test_teil_1_wochenende_ist_samstag_und_sonntag_utc(monkeypatch):
    zeit, ohlc = reihe(288 * 5)
    fr, sa, so, mo = ms(2026, 6, 5, 23, 55), ms(2026, 6, 6, 0, 0), ms(2026, 6, 7, 23, 55), ms(2026, 6, 8, 0, 0)
    monkeypatch.setattr(OS, "trades", lambda kz, uu, p, start: [
        {"ein": e, "aus": e + K, "richtung": 1.0, "ein_kurs": 100.0, "aus_kurs": 100.0 + i, "z": 3.0, "schlimmst_bp": 0.0} for i, e in enumerate((fr, sa, so, mo))])
    r = E.teil1(["AUSDT"], lambda s: {"zeit": zeit, "ohlc": ohlc, "u": np.zeros(len(zeit)), "fund_zeit": LEER[0], "fund_rate": LEER[1]}, {"AUSDT": 1.0})
    assert r["wochenende"]["trades"] == 2 and r["wochenende"]["roh_bp"] == pytest.approx(150.0)      # Samstag 00:00 und Sonntag 23:55
    assert r["werktag"]["trades"] == 2 and r["werktag"]["roh_bp"] == pytest.approx(150.0)            # Freitag 23:55 und Montag 00:00


def test_abrechnung_wie_im_papier_runner_auf_derselben_kuenstlichen_reihe(monkeypatch, tmp_path):
    """Dieselbe künstliche Reihe einmal durch runner.lauf() (ohne Schreiben) und einmal durch E.trades_kontrakt: gleiche Trades,
    gleiche Roh- und Nettozahlen, gleiches Funding, gleiche Slippage."""
    tage_n, sl = 9, 1.7
    n = 288 * tage_n
    rng = np.random.default_rng(56)
    zeit = T0 + K * np.arange(n, dtype=np.int64)
    schluss = 100.0 * np.exp(np.cumsum(rng.normal(0, 0.0006, n)))
    offen = np.concatenate([[100.0], schluss[:-1]]) * (1 + rng.normal(0, 0.0001, n))
    ohlc = np.column_stack([offen, np.maximum(offen, schluss) * 1.0002, np.minimum(offen, schluss) * 0.9998, schluss])
    u = rng.normal(0, 0.01, n) + np.where(rng.random(n) < 0.03, rng.choice([-0.12, 0.12], n), 0.0)
    u[288 * 5 + 20: 288 * 5 + 40] = np.nan                                                            # einzelne Kerzen ohne Tiefe
    fz = np.arange(T0, T0 + tage_n * E.TAG, 15 * 60_000, dtype=np.int64)                              # künstlich dicht (alle 15 Minuten), damit viele Trades eine Abrechnung treffen, auch genau am Ein- und Ausstieg
    fr = rng.normal(0.0001, 0.0004, len(fz))

    def tag_index(tag):
        return int((ms(tag.year, tag.month, tag.day) - T0) // K)
    monkeypatch.setattr(R, "kerzen_tag", lambda sym, tag, cache: [(int(zeit[i]), *map(float, ohlc[i])) for i in range(tag_index(tag), tag_index(tag) + 288)])
    monkeypatch.setattr(R, "tiefe_tag", lambda sym, tag, stufe, cache: {int(zeit[i]): float(u[i]) for i in range(tag_index(tag), tag_index(tag) + 288) if np.isfinite(u[i])})
    monkeypatch.setattr(R, "funding_monat", lambda sym, monat, cache: {int(z): float(r) for z, r in zip(fz, fr)} if monat == "2026-06" else None)
    cfg = json.loads((Path(R.__file__).resolve().parent / "OS-1.1" / "konfiguration.json").read_text())
    cfg.update(coins=["X"], start="2026-06-03T00:00:00Z", vorlauf_tage=2, kapital_usd=1e9, anzahl_letzte_trades=10_000)
    cfg["kosten"] = {"taker_bp": 8.0, "rebate": 0.85, "slippage_bp_je_order": {"X": sl}}
    doc = R.lauf("OS-1.1", heute=dt.date(2026, 6, 1) + dt.timedelta(days=tage_n), cache=tmp_path, schreiben=False, cfg=cfg, steuer={"status": "laufend"})
    assert doc["status"] == "läuft" and doc["fehler"] == []
    t = E.trades_kontrakt("XUSDT", zeit, ohlc, u, fz, fr, sl, cfg["parameter"])
    assert len(t) >= 15 and doc["trades"] == len(t)
    assert sum(1 for x in t if x["funding_bp"] != 0) >= 5                                              # die Probe enthält Trades über eine Funding-Abrechnung
    assert any(x["ein"] in set(fz.tolist()) for x in t) and any(x["aus"] in set(fz.tolist()) for x in t)   # auch genau am Ein- und Ausstieg
    runner = sorted(doc["letzte_trades"], key=lambda x: x["ein"])
    assert [(x["ein"], x["aus"]) for x in runner] == [(R.iso(x["ein"]), R.iso(x["aus"])) for x in t]
    assert [x["netto_bp"] for x in runner] == [round(x["n85_bp"], 1) for x in t]
    groesse = doc["positionsgroesse_usd"]
    assert doc["netto_je_trade_bp"] == round(float(np.mean([x["n85_bp"] for x in t])), 2) and doc["roh_je_trade_bp"] == round(float(np.mean([x["roh_bp"] for x in t])), 2)
    assert doc["funding_usd"] == pytest.approx(sum(groesse * x["funding_bp"] / 1e4 for x in t), abs=0.006)
    assert doc["slippage_usd"] == pytest.approx(len(t) * groesse * 2 * sl / 1e4, abs=0.006)
    assert doc["rendite_ohne_rebate_pct"] <= doc["rendite_mit_rebate_pct"]


# ------------------------------------------------ Diagnose: Signal eine Stunde früher (Abschnitt 57) ----
def test_diagnose_erkennt_messfehler_im_gemeinsamen_kurs_und_echte_umkehr():
    from forschung.experimente import e28_diagnose as DG
    rng = np.random.default_rng(5)

    def bauen(echt, fehler):
        """echt: Anteil der Wochenend-Bewegung, den der Montag zurückholt; fehler: Messfehler nur im Kurs von Sonntag 23:00."""
        kurse = {f"K{i:02d}USDT": {} for i in range(60)}
        we = E.wochenenden(ms(2026, 6, 1), ms(2026, 6, 1) + (20 * 7 + 3) * E.TAG)
        for a, b, c in we:
            for s in kurse:
                w, f = rng.normal(0, 0.02), rng.normal(0, fehler)
                kurse[s][a] = 100.0
                kurse[s][b - H] = 100.0 * (1 + w)
                kurse[s][b] = 100.0 * (1 + w) * (1 + f)
                kurse[s][c] = 100.0 * (1 + w) * (1 - echt * w + rng.normal(0, 0.005))
        return kurse, we[-1][2] + 1
    sp = {f"K{i:02d}USDT": 2.0 for i in range(60)}
    kurse, bis = bauen(0.0, 0.01)                                                    # nur Messfehler: Hauptfassung zeigt Schein-Umkehr, die Diagnose nicht
    d = DG.diagnose(kurse, sp, bis)
    assert d["wochenenden"] == 20 and d["hauptfassung_auf_denselben_kontrakten"]["steigung_mittel"] < -0.1
    assert abs(d["signal_eine_stunde_frueher"]["steigung_mittel"]) < 0.05
    kurse, bis = bauen(0.5, 0.0)                                                     # echte Umkehr: beide Fassungen zeigen sie
    d = DG.diagnose(kurse, sp, bis)
    assert d["hauptfassung_auf_denselben_kontrakten"]["steigung_mittel"] == pytest.approx(-0.5, abs=0.05)
    assert d["signal_eine_stunde_frueher"]["steigung_mittel"] == pytest.approx(-0.5, abs=0.05)
    del kurse["K00USDT"][sorted(kurse["K00USDT"])[1]]                                # ein Kontrakt ohne den Kurs von 22:00 an einem Wochenende
    d = DG.diagnose(kurse, sp, bis)
    assert d["kontrakte_teil_2"][0] == 60 and d["kontrakte_mit_vier_kursen"][0] == 59
