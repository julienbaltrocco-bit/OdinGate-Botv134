"""Tests zu E27 aus der unabhängigen Gegenprüfung (21.11.2026), angepasst an die Korrektur danach (Vorprüfungen vor der Sperre).

Nur künstliche Eingaben: Kein Test liest den Datenspeicher (laden() ist gesperrt), rechne() bzw. coin_daten() sind ersetzt,
das Ergebnis liegt in einem temporären Verzeichnis.
"""
import json
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

FORSCHUNG = Path(os.environ.get("E27_FORSCHUNG", Path(__file__).resolve().parents[1] / "forschung"))
sys.path.insert(0, str(FORSCHUNG))
pytest.importorskip("numba")
from experimente import e23_marktstruktur as E  # noqa: E402
from experimente import e27_tagesvariante as X  # noqa: E402

NT = X.D.N // E.TAG                                                  # 1370 Tage im Speicher
T_TAGE, V1_TAGE, V2_TAGE = slice(45, 730), slice(730, 1096), slice(1096, 1370)   # von Hand aus dem Kalender, nicht aus E.tage
SOLL_REGELN = {"B0": (1, 0), "TAG": (24, 0), "TAG_04": (24, 4), "TAG_08": (24, 8), "TAG_12": (24, 12), "TAG_16": (24, 16), "TAG_20": (24, 20),
               "ALLE_4H": (4, 0), "ALLE_12H": (12, 0)}                # Abschnitt 51: (Abstand in Stunden, Uhrzeit UTC)


@pytest.fixture(autouse=True)
def kein_echter_speicher(tmp_path, monkeypatch):
    def zu(*a, **k):
        raise AssertionError("Der Datenspeicher darf in diesen Tests nicht gelesen werden.")
    monkeypatch.setattr(X.D, "laden", zu)
    monkeypatch.setattr(X, "ERGEBNIS", tmp_path / "e27_tagesvariante.json")


# ------------------------------------------------------------------------------------------------ künstliche Kurse
def kurs(n, seed, luecken=()):
    """Zufallskurs; in Lücken flache Kerzen zum letzten Schluss und gueltig = False (wie im Speicher)."""
    rng = np.random.default_rng(seed)
    c = 100 * np.exp(np.cumsum(rng.normal(0, 0.003, n)))
    g = np.ones(n, bool)
    for a, b in luecken:
        g[a:b], c[a:b] = False, c[a - 1]
    o = np.concatenate([[100.0], c[:-1]])
    h, l = np.maximum(o, c) * 1.001, np.minimum(o, c) * 0.999
    for a, b in luecken:
        o[a:b] = h[a:b] = l[a:b] = c[a - 1]
    return o, h, l, c, g


def laufe(o, h, l, c, g, dh, fs=None, slip=1.0, nt=None):
    n = len(c)
    nt = n // E.TAG + 1 if nt is None else nt
    leer, leer8, od = np.zeros(1), np.zeros(1, np.int8), np.zeros((20000, 4))
    brut, nord, slipb = np.zeros((2, nt)), np.zeros((2, nt)), np.zeros((2, nt))
    no = E.lauf(o, h, l, c, g, np.zeros(n) if fs is None else fs, slip, np.ascontiguousarray(dh, np.int8), 12, 3, leer, leer, leer, leer, leer8, leer8,
                E.B0, n, brut, nord, slipb, np.zeros(nt), np.zeros(7), od)
    assert no <= len(od)
    return od[:no], brut, nord, slipb


def position(od, n):
    pos = np.zeros(n, int)
    for kerze, seite, anlass, _ in od:
        pos[int(kerze):] = int(seite) if anlass == 1 else 0
    return pos


def soll_richtung(d, abstand, phase):
    """Einfache Schleife nach dem Text: Die Stundenkerze t schließt t+1 Stunden nach dem 01.07.2021 00:00 UTC."""
    out, halte = np.zeros(len(d), np.int8), 0
    for t in range(len(d)):
        if (t + 1) % abstand == phase % abstand:
            halte = d[t]
        out[t] = halte
    return out


# ------------------------------------------------------------------------------------- Tagesrichtung im Rechenkern
def test_regeln_tragen_abstand_und_uhrzeit_der_festlegung():
    assert X.regeln(True) == SOLL_REGELN
    assert X.regeln(False) == {k: v for k, v in SOLL_REGELN.items() if not k.startswith("ALLE")}


@pytest.mark.parametrize("ken", list(SOLL_REGELN))
def test_ausfuehrung_zur_uhrzeit_und_richtung_der_uebernahmestunde(ken):
    abstand, phase = SOLL_REGELN[ken]
    n = 288 * 100
    o, h, l, c, g = kurs(n, 4)
    d = E.richtung_stunden(c)
    dh = d if abstand == 1 else X.richtung_abgefragt(d, abstand, phase)
    od = laufe(o, h, l, c, g, dh)[0]
    assert len(od) >= 4
    minute = (od[:, 0] * 5) % (60 * abstand)                       # Uhrzeit der Eröffnung der Ausführungskerze, modulo Abstand
    assert (minute == 60 * phase + 5).all()                        # TAG: 00:05 UTC, TAG_08: 08:05 UTC, ALLE_4H: 00:05, 04:05, ...
    pos = position(od, n)
    for t in range(len(d) - abstand):                              # Stundenkerze t schließt zur Stunde t+1; ab der Kerze danach gilt d[t]
        if (t + 1 - phase) % abstand == 0:
            assert (pos[12 * (t + 1) + 1:12 * (t + 1 + abstand) + 1] == d[t]).all(), t
    erste = next(t for t in range(len(d)) if (t + 1 - phase) % abstand == 0)
    assert (pos[:12 * (erste + 1) + 1] == 0).all()


@pytest.mark.parametrize("phase,erste_mit_vorlauf", [(0, 359), (4, 339), (8, 343), (12, 347), (16, 351), (20, 355)])
def test_vor_erster_uebernahme_und_vor_336_stunden_flach(phase, erste_mit_vorlauf):
    eins = np.ones(24 * 30, np.int8)
    r = X.richtung_abgefragt(eins, 24, phase)
    erste = phase - 1 if phase else 23                             # erste Stundenkerze, die zur Uhrzeit `phase` schließt
    assert (r[:erste] == 0).all() and (r[erste:] == 1).all()
    n = 288 * 30
    c = 100 * np.exp(np.arange(n) * 1e-5)                          # stetig steigend: d = +1 ab Stunde 336
    o = np.concatenate([[100.0], c[:-1]])
    d = E.richtung_stunden(c)
    assert (d[:336] == 0).all() and (d[336:] == 1).all()
    r = X.richtung_abgefragt(d, 24, phase)
    assert (r[:erste_mit_vorlauf] == 0).all() and (r[erste_mit_vorlauf:] == 1).all()
    od = laufe(o, c * 1.001, o * 0.999, c, np.ones(n, bool), r)[0]
    assert len(od) == 1 and od[0, 0] == 12 * (erste_mit_vorlauf + 1) + 1 and od[0, 1] == 1    # TAG: Kerze 4321 = 16.07.2021 00:05 UTC


@pytest.mark.parametrize("abstand,phase", [(1, 0), (24, 0), (24, 8), (24, 20), (4, 0), (12, 0)])
def test_spaetere_kerzen_aendern_nichts_bis_zur_naechsten_uebernahme(abstand, phase):
    """Störung ab Kerze K: Alle Orders bis zur Ausführung der nächsten Übernahme, deren Stunde K enthält oder später liegt,
    bleiben gleich. Der gehaltene Wert enthält also nichts aus späteren Stunden."""
    n = 288 * 70
    o, h, l, c, g = kurs(n, 11)

    def orders(o, h, l, c):
        d = E.richtung_stunden(c)
        return laufe(o, h, l, c, g, d if abstand == 1 else X.richtung_abgefragt(d, abstand, phase))[0]

    basis = orders(o, h, l, c)
    rng = np.random.default_rng(99)
    schnitte = [288 * m + 12 * phase + x for m in range(16, 66, 2) for x in (0, 3)]     # in der Stunde direkt nach einer Übernahme
    schnitte += [288 * 30 + x for x in (-13, -12, -1, 1, 2, 11, 12, 13)] + [int(x) for x in rng.integers(288 * 16, n - 300, 40)]
    geaendert = 0
    for K in schnitte:
        o2, h2, l2, c2 = (x.copy() for x in (o, h, l, c))
        c2[K:] = c[K - 1] * np.exp(np.cumsum(rng.normal(0, 0.1, n - K)))
        o2[K:] = np.concatenate([[c[K - 1] * np.exp(rng.normal(0, 0.1))], c2[K:-1]])
        h2[K:], l2[K:] = np.maximum(o2, c2)[K:] * 1.001, np.minimum(o2, c2)[K:] * 0.999
        neu = orders(o2, h2, l2, c2)
        t = K // 12                                                # erste Stundenkerze mit gestörten Kerzen
        while (t + 1 - phase) % abstand:
            t += 1
        grenze = 12 * (t + 1)                                      # letzte Ausführungskerze, die nur von Stunden vor K abhängt
        a, b = basis[basis[:, 0] <= grenze], neu[neu[:, 0] <= grenze]
        assert np.array_equal(a[:, :3], b[:, :3]), K
        assert np.array_equal(a[a[:, 0] < K], b[b[:, 0] < K]), K
        geaendert += not np.array_equal(basis[:, :3], neu[:, :3])
    assert geaendert > len(schnitte) // 2                           # die Störung wirkt (danach), sonst wäre der Test blind


def test_luecke_zur_uebernahme_wird_bei_der_naechsten_pruefung_nachgeholt():
    """Abschnitt 51 sagt dazu nichts ausdrücklich; der Kern holt nach (Präzisierung 5 zu Abschnitt 43: Prüfung nur ohne Lücke,
    die Sollrichtung ist ein Zustand). Fällt die Prüfung um 00:05 UTC aus, handelt TAG bei der nächsten Prüfung, die
    stattfindet, mit dem Wert von 00:00 UTC; die Übernahme geht nicht für den ganzen Tag verloren. B0 verhält sich gleich."""
    n = 288 * 120
    o, h, l, c, g = kurs(n, 5)
    d = E.richtung_stunden(c)
    ohne = laufe(o, h, l, c, g, X.richtung_abgefragt(d, 24, 0))[0]
    wechsel = [int(k) for k, _, a, _ in ohne if a == 1 and 288 * 20 < k < n - 600]
    k0 = wechsel[len(wechsel) // 2]
    m = k0 // 288
    assert k0 == 288 * m + 1
    for ende, ausfuehrung in ((7, 8), (14, 15), (200, 201)):       # Lücke ab 00:00 UTC über 35 Minuten, 70 Minuten, knapp 17 Stunden
        o2, h2, l2, c2, g2 = kurs(n, 5, luecken=[(288 * m, 288 * m + ende)])
        tag2 = X.richtung_abgefragt(E.richtung_stunden(c2), 24, 0)
        assert tag2[24 * m] == d[24 * m - 1]                       # gehalten wird d der Stunde, die um 00:00 UTC schloss
        mit = laufe(o2, h2, l2, c2, g2, tag2)[0]
        hier = mit[(mit[:, 0] > 288 * m) & (mit[:, 0] <= 288 * (m + 1))]
        soll = ohne[ohne[:, 0] == k0]
        assert (hier[:, 0] == 288 * m + ausfuehrung).all() and np.array_equal(hier[:, 1:3], soll[:, 1:3])
        assert (position(mit, n)[288 * m + ausfuehrung:288 * (m + 1) + 1] == d[24 * m - 1]).all()
    b0 = laufe(o, h, l, c, g, d)[0]                                 # Stundenregel: gleiche Mechanik
    kb = int(b0[len(b0) // 2, 0])
    assert kb % 12 == 1
    o2, h2, l2, c2, g2 = kurs(n, 5, luecken=[(kb - 1, kb + 6)])
    assert np.array_equal(E.richtung_stunden(c2), d)
    mit = laufe(o2, h2, l2, c2, g2, d)[0]
    soll = b0[:, :3].copy()
    soll[soll[:, 0] == kb, 0] = kb + 7
    assert np.array_equal(mit[:, :3], soll)


def test_rechne_verdrahtet_jede_regel_mit_abstand_und_uhrzeit(monkeypatch):
    n = 288 * 60
    aufrufe = []

    def daten(ci, i_ende):
        aufrufe.append((ci, i_ende))
        o, h, l, c, g = kurs(n, 100 + ci, luecken=[(288 * 30 + 280, 288 * 30 + 295)] if ci == 3 else ())
        fs = np.random.default_rng(ci).normal(0, 1e-5, n)
        return o[:i_ende], h[:i_ende], l[:i_ende], c[:i_ende], g[:i_ende], fs[:i_ende], 1.0 + ci

    monkeypatch.setattr(E, "coin_daten", daten)
    erg, orders = X.rechne(n, True, mit_orders=20000)
    assert aufrufe == [(ci, n) for ci in range(10)] and set(erg) == set(SOLL_REGELN)
    for ci in (0, 3, 9):
        o, h, l, c, g, fs, slip = daten(ci, n)
        d = E.richtung_stunden(c)
        for ken, (abstand, phase) in SOLL_REGELN.items():
            od, brut, nord, slipb = laufe(o, h, l, c, g, soll_richtung(d, abstand, phase), fs=fs, slip=slip, nt=NT)
            assert len(od) > 2 and np.array_equal(orders[ken][X.D.COINS[ci]], od), (ken, ci)
            r = erg[ken]
            assert np.array_equal(r["brut"][ci], brut) and np.array_equal(r["nord"][ci], nord) and np.array_equal(r["slipb"][ci], slipb)
            assert r["slip_coin"][ci] == slip and r["nord"][ci].sum() == len(od)
    assert set(X.rechne(n, False)[0]) == {k for k in SOLL_REGELN if not k.startswith("ALLE")}


def test_tagesfelder_vor_dem_schnitt_haengen_nicht_vom_ende_ab(monkeypatch):
    """Grundlage der Prüfung in Stufe 2 (T und V1 bitgleich): Ob bis zum Schnitt oder darüber hinaus gerechnet wird,
    die Tage vor dem Schnitt kommen gleich heraus, und hinter dem Schnitt steht bei der kurzen Rechnung nichts."""
    n1, n2 = 288 * 40, 288 * 60

    def daten(ci, i_ende):
        o, h, l, c, g = kurs(n2, 200 + ci, luecken=[(n1 - 3, n1 + 4)] if ci == 2 else ())
        fs = np.random.default_rng(ci).normal(0, 1e-5, n2)
        return o[:i_ende], h[:i_ende], l[:i_ende], c[:i_ende], g[:i_ende], fs[:i_ende], 1.0 + ci

    monkeypatch.setattr(E, "coin_daten", daten)
    kurz, lang = X.rechne(n1, True)[0], X.rechne(n2, True)[0]
    for ken in SOLL_REGELN:
        for feld in ("brut", "nord", "slipb"):
            assert np.array_equal(kurz[ken][feld][:, :, :40], lang[ken][feld][:, :, :40]), (ken, feld)
            assert not kurz[ken][feld][:, :, 40:].any()
        assert lang[ken]["nord"][:, :, 40:].any() and kurz[ken]["nord"][:, :, :40].any()


# --------------------------------------------------------------------------------------- Tagesreihen und Bedingungen
def test_reihen_zeitraum_konto_als_mittel_der_coins_und_orders_im_zeitraum():
    rng = np.random.default_rng(3)
    erg = {}
    for ken in ("B0", "TAG"):
        nord = rng.integers(0, 4, (10, 2, NT)).astype(float)
        erg[ken] = {"brut": rng.normal(0, 0.01, (10, 2, NT)), "nord": nord, "slipb": nord * rng.uniform(1, 5, (10, 2, NT)), "slip_coin": rng.uniform(1, 3, 10)}
    for zr, sl in (("T", T_TAGE), ("V1", V1_TAGE), ("V2", V2_TAGE)):
        assert E.tage(zr) == sl
        reihen, orders = X.reihen_zeitraum(erg, zr)
        assert set(reihen) == {(k, ko, rb) for k in erg for ko in ("bewegt", "ruhig") for rb in ("mit", "ohne")}
        for ken, r in erg.items():
            assert orders[ken] == sum(r["nord"][ci, ri, t] for ci in range(10) for ri in (0, 1) for t in range(sl.start, sl.stop))
            for ko in ("bewegt", "ruhig"):
                for rb, gebuehr in (("mit", 1.2), ("ohne", 8.0)):
                    soll = np.zeros(sl.stop - sl.start)
                    for ci in range(10):
                        for ri in (0, 1):                          # long und short
                            no = r["nord"][ci, ri, sl]
                            slip = r["slipb"][ci, ri, sl] if ko == "bewegt" else no * r["slip_coin"][ci]
                            soll += (r["brut"][ci, ri, sl] - (slip + no * gebuehr) / 1e4) / 10
                    assert reihen[(ken, ko, rb)].shape == soll.shape and np.allclose(reihen[(ken, ko, rb)], soll, rtol=0, atol=1e-15), (ken, ko, rb)
    erg["TAG"]["brut"][4, 1, 800] = np.nan
    with pytest.raises(SystemExit):
        X.reihen_zeitraum(erg, "V1")
    X.reihen_zeitraum(erg, "T")                                      # der ungültige Wert liegt nicht in T


RAUSCH = np.random.default_rng(1).normal(0, 0.01, 300)
RAUSCH -= RAUSCH.mean()


def reihen(**abweichend):
    """Alle Reihen gleich (Rauschen + 0,001 je Tag); abweichend: z. B. TAG_bewegt_ohne=Reihe."""
    r = {(k, ko, rb): RAUSCH + 0.001 for k in ["B0"] + [X.name_phase(p) for p in X.PHASEN] for ko in ("bewegt", "ruhig") for rb in ("mit", "ohne")}
    for name, x in abweichend.items():
        ken, ko, rb = name.rsplit("_", 2)
        r[(ken, ko, rb)] = x
    return r


ORD = {"TAG": 100.0, "B0": 300.0}
GUT, SCHLECHT = RAUSCH + 0.002, RAUSCH + 0.0005


def test_bedingung_a_verlangt_summe_und_sharpe_ohne_rebate_bei_bewegten_kosten():
    a = lambda **kw: X.bedingungen(reihen(**kw), ORD)["A_ohne_rebate_besser"]
    assert not a()                                                   # gleich ist nicht höher
    assert a(TAG_bewegt_ohne=GUT)
    assert not a(TAG_bewegt_ohne=3 * RAUSCH + 0.002)                 # Summe höher, Sharpe-Zahl niedriger
    assert not a(TAG_bewegt_ohne=0.1 * RAUSCH + 0.0005)              # Sharpe-Zahl höher, Summe niedriger
    assert a(TAG_bewegt_ohne=GUT, TAG_bewegt_mit=SCHLECHT, TAG_ruhig_ohne=SCHLECHT, TAG_ruhig_mit=SCHLECHT)
    assert not a(TAG_bewegt_ohne=SCHLECHT, TAG_bewegt_mit=GUT, TAG_ruhig_ohne=GUT, TAG_ruhig_mit=GUT)
    assert a(TAG_bewegt_ohne=RAUSCH + 0.001 + 1e-9)                  # entschieden wird ungerundet


def test_bedingung_b_zwei_drittel_mit_rebate_und_vorzeichen_von_b0():
    b = lambda **kw: X.bedingungen(reihen(**kw), ORD)["B_mit_rebate_nicht_schlechter"]
    assert b()
    assert b(TAG_bewegt_mit=RAUSCH + 0.00067) and not b(TAG_bewegt_mit=RAUSCH + 0.00066)
    assert not b(TAG_bewegt_mit=RAUSCH + 0.00066, TAG_bewegt_ohne=GUT, TAG_ruhig_mit=GUT, TAG_ruhig_ohne=GUT)
    assert b(TAG_bewegt_mit=RAUSCH + 0.00067, TAG_bewegt_ohne=RAUSCH - 1, TAG_ruhig_mit=RAUSCH - 1, TAG_ruhig_ohne=RAUSCH - 1)
    assert not b(TAG_bewegt_mit=RAUSCH + 0.00065, B0_ruhig_mit=RAUSCH + 0.0005, B0_bewegt_ohne=RAUSCH + 0.0005)
    null, minus = np.zeros(300), np.full(300, -0.002)
    assert b(B0_bewegt_mit=null, TAG_bewegt_mit=null)                # B0 nicht positiv: TAG ≥ B0 genügt
    assert not b(B0_bewegt_mit=null, TAG_bewegt_mit=null - 1e-9)
    assert b(B0_bewegt_mit=minus, TAG_bewegt_mit=minus) and b(B0_bewegt_mit=minus, TAG_bewegt_mit=minus / 2)
    assert not b(B0_bewegt_mit=minus, TAG_bewegt_mit=minus - 1e-9)
    assert not b(TAG_bewegt_mit=null) and not b(TAG_bewegt_mit=minus)  # B0 positiv: TAG muss positiv sein


def test_bedingung_c_grenze_ein_drittel():
    c = lambda t, b: X.bedingungen(reihen(), {"TAG": t, "B0": b})["C_hoechstens_ein_drittel_der_orders"]
    assert c(100.0, 300.0) and c(100.0, 301.0) and not c(101.0, 300.0) and not c(100.0, 299.0)


def test_bedingung_d_zaehlt_sechs_uhrzeiten_einschliesslich_00_uhr():
    def d(*gute):
        out = X.bedingungen(reihen(**{f"{k}_bewegt_ohne": GUT for k in gute}), ORD)
        assert out["A_je_uhrzeit"] == {X.name_phase(p): X.name_phase(p) in gute for p in X.PHASEN}
        assert out["alle"] == (out["A_ohne_rebate_besser"] and out["B_mit_rebate_nicht_schlechter"] and out["C_hoechstens_ein_drittel_der_orders"]
                               and out["D_mindestens_vier_von_sechs_uhrzeiten"])
        return out["D_mindestens_vier_von_sechs_uhrzeiten"], out["alle"]
    assert d("TAG", "TAG_04", "TAG_08", "TAG_12") == (True, True)
    assert d("TAG", "TAG_04", "TAG_16", "TAG_20") == (True, True)
    assert d("TAG", "TAG_04", "TAG_08") == (False, False)
    assert d("TAG_04", "TAG_08", "TAG_12", "TAG_16") == (True, False)   # vier Uhrzeiten, aber 00 Uhr selbst erfüllt A nicht
    assert d("TAG_04", "TAG_08", "TAG_12") == (False, False)
    assert d("TAG", "TAG_04", "TAG_08", "TAG_12", "TAG_16", "TAG_20") == (True, True)
    gut = reihen(**{f"{X.name_phase(p)}_bewegt_ohne": GUT for p in X.PHASEN})
    assert X.bedingungen(gut, ORD)["alle"] and not X.bedingungen(gut, {"TAG": 101.0, "B0": 300.0})["alle"]
    gut[("TAG", "bewegt", "mit")] = RAUSCH + 0.0005
    assert not X.bedingungen(gut, ORD)["alle"]


def test_bericht_felder_und_stichprobe_ohne_rebate():
    eigen = np.random.default_rng(2).normal(0, 0.002, 300)
    r = reihen(TAG_bewegt_ohne=RAUSCH + 0.001 + eigen - eigen.mean(), TAG_bewegt_mit=RAUSCH - 0.01, TAG_ruhig_mit=RAUSCH + 0.004)
    r = {k: v for k, v in r.items() if k[0] in ("B0", "TAG")}
    out = X.bericht(r, {"B0": 6850.0, "TAG": 1370.0}, "T")
    assert set(out) == {"B0", "TAG"} and out["B0"]["orders_je_tag"] == 10.0 and out["TAG"]["orders_je_tag"] == 2.0     # T hat 685 Tage
    assert X.bericht(r, {"B0": 366.0, "TAG": 0.0}, "V1")["B0"]["orders_je_tag"] == 1.0 and X.bericht(r, {"B0": 274.0, "TAG": 0.0}, "V2")["B0"]["orders_je_tag"] == 1.0
    assert "anteil_ohne_vorteil_ohne_rebate" not in out["B0"]
    soll = E.stichprobe(r[("TAG", "bewegt", "ohne")], r[("B0", "bewegt", "ohne")])
    assert 0 < soll < 1 and out["TAG"]["anteil_ohne_vorteil_ohne_rebate"] == round(soll, 4)
    for ko in ("bewegt", "ruhig"):
        for rb in ("mit", "ohne"):
            x = r[("TAG", ko, rb)]
            assert out["TAG"][f"{ko}_{rb}_rebate"] == {"summe_pct": round(float(x.sum() * 100), 2), "sharpe": round(E.sharpe(x), 3), "einbruch_pct": round(E.einbruch(x) * 100, 2)}


# ---------------------------------------------------------------------------------------------- Sperre und Datenschnitt
def kunst_ergebnis(i_ende, mit_abstaenden, schlecht=None):
    """Tagesfelder wie aus rechne(): TAG braucht ein Fünftel der Orders und besteht überall, außer an den Tagen `schlecht`."""
    rausch = np.random.default_rng(7).normal(0, 0.01, NT)
    erg = {}
    for ken in X.regeln(mit_abstaenden):
        brut, nord = np.zeros((10, 2, NT)), np.zeros((10, 2, NT))
        brut[:, 0, :] = rausch + 0.002
        if ken != "B0" and schlecht is not None:
            brut[:, 0, schlecht] -= 0.004
        nord[:, 0, :] = 1.0 if ken == "B0" else 0.2
        slipb = nord * 2.0
        for a in (brut, nord, slipb):
            a[:, :, i_ende // E.TAG:] = 0.0                          # was hinter i_ende liegt, ist nicht gerechnet
        erg[ken] = {"brut": brut, "nord": nord, "slipb": slipb, "markt": np.zeros((10, NT)), "zahl": np.zeros((10, 7)), "slip_coin": np.full(10, 1.5)}
    return erg


class Rekorder:
    """Ersatz für rechne(): merkt sich je Aufruf (i_ende, mit_abstaenden, Stand der Ergebnisdatei in diesem Augenblick)."""

    def __init__(self, schlecht=None, stoerung_tag=None, absturz_bei=None):
        self.schlecht, self.stoerung_tag, self.absturz_bei, self.aufrufe = schlecht, stoerung_tag, absturz_bei, []

    def __call__(self, i_ende, mit_abstaenden, mit_orders=0):
        self.aufrufe.append((i_ende, mit_abstaenden, json.loads(X.ERGEBNIS.read_text()) if X.ERGEBNIS.exists() else None))
        if self.absturz_bei == len(self.aufrufe):
            raise RuntimeError("Absturz mitten in der Rechnung")
        erg = kunst_ergebnis(i_ende, mit_abstaenden, self.schlecht)
        if self.stoerung_tag is not None and i_ende > E.ENDE_V1:
            erg["TAG_16"]["brut"][3, 1, self.stoerung_tag] += 1e-9   # ein Coin, ein Tag, eine Regel: 1e-10 in der Tagesreihe
        return erg, {}


@pytest.fixture
def rek(monkeypatch):
    def einsetzen(**kw):
        r = Rekorder(**kw)
        monkeypatch.setattr(X, "rechne", r)
        monkeypatch.setattr(E, "stichprobe", lambda *a, **k: 0.5)   # hier nicht Gegenstand, spart Zeit
        return r
    return einsetzen


SPERRE = {"stand": "geöffnet, Rechnung läuft"}
V2_NPZ = "e27_tagesvariante_tage_v2.npz"


def test_stufe1_laedt_nur_bis_30_06_2024_und_gibt_nur_frei_wenn_t_und_v1_bestehen(rek):
    assert E.ENDE_V1 == 315648 == 1096 * 288 and str(X.D.RASTER[E.ENDE_V1]) == "2024-07-01 00:00:00"
    r = rek()
    out = X.stufe1()
    assert [(a, b) for a, b, _ in r.aufrufe] == [(315648, True)]    # ein Aufruf, Ende vor der ersten Kerze von V2
    assert out == json.loads(X.ERGEBNIS.read_text()) and "V2" not in out and out["v2_frei"] is True and out["einstufung"].startswith("offen")
    assert set(out["T"]["regeln"]) == set(SOLL_REGELN) == set(out["V1"]["regeln"]) and out["T"]["bedingungen"]["alle"] and out["V1"]["bedingungen"]["alle"]
    tage = np.load(X.ERGEBNIS.with_name("e27_tagesvariante_tage.npz"))
    assert set(tage.files) == {f"{k}_{ko}_{rb}_{zr}" for k in SOLL_REGELN for ko in ("bewegt", "ruhig") for rb in ("mit", "ohne") for zr in ("T", "V1")}
    assert {len(tage[f]) for f in tage.files} == {685, 366}
    for schlecht, zr in ((T_TAGE, "T"), (V1_TAGE, "V1")):            # nur einer der beiden Zeiträume besteht: keine Freigabe
        r = rek(schlecht=schlecht)
        out = X.stufe1()
        assert not out[zr]["bedingungen"]["alle"] and out["v2_frei"] is False and out["einstufung"].startswith("A (verworfen)")
        with pytest.raises(SystemExit):
            X.stufe2()
        assert len(r.aufrufe) == 1 and "V2" not in json.loads(X.ERGEBNIS.read_text())


@pytest.mark.parametrize("v2_besteht", [True, False])
def test_stufe2_einmal_sperre_vor_der_rechnung_und_einstufung(rek, v2_besteht):
    r = rek(schlecht=None if v2_besteht else V2_TAGE)
    eins = X.stufe1()
    assert eins["v2_frei"]
    zwei = X.stufe2()
    assert [(a, b) for a, b, _ in r.aufrufe] == [(315648, True), (315648, False), (X.D.N, False)]
    assert "V2" not in r.aufrufe[1][2]                              # Wiederholung von Stufe 1: noch ohne Sperre
    assert r.aufrufe[2][2]["V2"] == SPERRE                          # die Sperre stand in der Datei, bevor rechne() für V2 lief
    assert zwei == json.loads(X.ERGEBNIS.read_text()) and zwei["T"] == eins["T"] and zwei["V1"] == eins["V1"]
    assert set(zwei["V2"]["regeln"]) == {k for k in SOLL_REGELN if not k.startswith("ALLE")}      # alle 4/12 Stunden nicht in V2
    assert zwei["V2"]["bedingungen"]["alle"] is v2_besteht
    assert zwei["einstufung"].startswith("C (Kandidat" if v2_besteht else "B (interessant)")
    assert X.ERGEBNIS.with_name(V2_NPZ).exists()
    vorher = X.ERGEBNIS.read_text()
    for stufe in (X.stufe2, X.stufe1):                               # kein zweites Öffnen, kein Überschreiben
        with pytest.raises(SystemExit):
            stufe()
    assert len(r.aufrufe) == 3 and X.ERGEBNIS.read_text() == vorher


def test_stufe2_bricht_vor_der_sperre_ab_wenn_der_speicher_nicht_mit_v2_endet(rek, monkeypatch):
    r = rek()
    X.stufe1()
    vorher = X.ERGEBNIS.read_text()
    n = X.D.N
    for name, wert in (("N", n + 288), ("N", n - 288), ("RASTER", pd.date_range("2021-07-01", "2025-04-01 23:55", freq="5min")),
                       ("RASTER", pd.date_range("2021-07-02", "2025-04-01 23:55", freq="5min"))):      # zweite: gleiche Länge, endet aber im April 2025
        with monkeypatch.context() as mp:
            mp.setattr(X.D, name, wert)
            with pytest.raises(SystemExit):
                X.stufe2()
        assert len(r.aufrufe) == 1 and X.ERGEBNIS.read_text() == vorher and not X.ERGEBNIS.with_name(V2_NPZ).exists()


@pytest.mark.parametrize("tag", [100, 900])
def test_stufe2_bricht_ab_wenn_t_oder_v1_nicht_bitgleich_sind_und_die_sperre_bleibt(rek, tag):
    r = rek(stoerung_tag=tag)
    X.stufe1()
    with pytest.raises(SystemExit):
        X.stufe2()
    stand = json.loads(X.ERGEBNIS.read_text())
    assert stand["V2"] == SPERRE and not X.ERGEBNIS.with_name(V2_NPZ).exists()   # keine Zahl aus V2 geschrieben, aber geöffnet
    for stufe in (X.stufe2, X.stufe1):
        with pytest.raises(SystemExit):
            stufe()
    assert len(r.aufrufe) == 3


def test_absturz_nach_der_sperre_laesst_v2_als_geoeffnet_stehen(rek):
    r = rek(absturz_bei=3)
    X.stufe1()
    with pytest.raises(RuntimeError):
        X.stufe2()
    assert json.loads(X.ERGEBNIS.read_text())["V2"] == SPERRE
    for stufe in (X.stufe2, X.stufe1):                               # kein zweiter Versuch ohne Eingriff von Hand
        with pytest.raises(SystemExit):
            stufe()
    assert len(r.aufrufe) == 3


def test_absturz_oder_abweichung_bei_der_wiederholung_verbraucht_die_oeffnung_nicht(rek, monkeypatch):
    r = rek(absturz_bei=2)                                           # Absturz in der Wiederholung von Stufe 1: vor der Sperre
    X.stufe1()
    vorher = X.ERGEBNIS.read_text()
    with pytest.raises(RuntimeError):
        X.stufe2()
    assert X.ERGEBNIS.read_text() == vorher and "V2" not in json.loads(vorher)
    echt = X.rechne

    def abweichend(i_ende, mit_abstaenden, mit_orders=0):            # die Wiederholung liefert eine andere Zahl als Stufe 1
        erg, o = echt(i_ende, mit_abstaenden, mit_orders)
        if not mit_abstaenden and i_ende == E.ENDE_V1:
            erg["TAG"]["brut"][2, 0, 500] += 1e-9
        return erg, o
    monkeypatch.setattr(X, "rechne", abweichend)
    with pytest.raises(SystemExit):
        X.stufe2()
    assert X.ERGEBNIS.read_text() == vorher and not X.ERGEBNIS.with_name(V2_NPZ).exists()
    assert all(a <= E.ENDE_V1 for a, _, _ in r.aufrufe)              # nichts nach dem 30.06.2024 gerechnet


def test_rechne_verweigert_v2_ohne_oeffnung(monkeypatch):
    with pytest.raises(SystemExit):
        X.rechne(E.ENDE_V1 + 1, False)                               # Abbruch vor dem ersten Zugriff auf den Speicher
    with pytest.raises(SystemExit):
        X.rechne(X.D.N, True)


def test_stufe2_ohne_ergebnisdatei_oder_ohne_freigabe_rechnet_nichts(rek):
    r = rek()
    with pytest.raises(FileNotFoundError):
        X.stufe2()
    for inhalt in ({}, {"v2_frei": False}, {"v2_frei": True, "V2": SPERRE}):
        X.ERGEBNIS.write_text(json.dumps(inhalt))
        with pytest.raises(SystemExit):
            X.stufe2()
        assert json.loads(X.ERGEBNIS.read_text()) == inhalt
    assert r.aufrufe == []


def test_fehlende_tagesdatei_wird_vor_der_sperre_bemerkt(rek):
    r = rek()
    X.stufe1()
    X.ERGEBNIS.with_name("e27_tagesvariante_tage.npz").unlink()
    with pytest.raises((SystemExit, FileNotFoundError)):
        X.stufe2()
    assert "V2" not in json.loads(X.ERGEBNIS.read_text()) and len(r.aufrufe) == 1
