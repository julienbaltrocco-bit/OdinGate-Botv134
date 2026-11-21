"""Tests zu E25 (Trendregel über alle Kontrakte), Festlegung in forschung/protokoll.md Abschnitt 47."""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "forschung"))
pytest.importorskip("numba")
from experimente import e25_breites_universum as X  # noqa: E402


def markt(n, tage, seed, spaet=()):
    rng = np.random.default_rng(seed)
    c = 100 * np.exp(np.cumsum(rng.normal(0, 0.03, (n, tage)), axis=1))
    o = np.concatenate([np.full((n, 1), 100.0), c[:, :-1]], axis=1) * (1 + rng.normal(0, 0.002, (n, tage)))
    qv = np.exp(rng.normal(15, 1, (n, 1))) * np.exp(rng.normal(0, 0.3, (n, tage)))
    fr = rng.normal(0.0002, 0.0005, (n, tage))
    for i, start in spaet:
        o[i, :start] = c[i, :start] = qv[i, :start] = fr[i, :start] = np.nan
    return o, c, qv, fr


def test_richtung_und_dabei():
    o, c, qv, fr = markt(3, 80, 1, spaet=[(1, 10), (2, 79)])
    d, ab = X.richtung(c), X.dabei_ab(c)
    assert (d[:, :14] == 0).all() and d[0, 30] == np.sign(c[0, 30] - c[0, 16])
    assert (d[1, :24] == 0).all() and d[1, 24] == np.sign(c[1, 24] - c[1, 10])
    assert ab.tolist() == [0, 70, 139]
    leer = np.full((1, 80), np.nan)
    assert X.dabei_ab(leer)[0] > 80


def test_tag_lauf_einstieg_drehung_funding_und_offene_position():
    o = np.array([np.nan, 10.0, 10.0, 12.0, 11.0, 11.0])
    c = np.array([np.nan, 10.0, 12.0, 11.0, 11.0, 13.0])
    f = np.array([np.nan, 0.01, 0.02, np.nan, 0.01, 0.0])
    ziel = np.array([1, 0, 1, -1, -1, 0], np.int8)
    brut, nord = np.zeros(6), np.zeros(6)
    X.tag_lauf(o, c, f, ziel, brut, nord)
    assert nord.tolist() == [0, 0, 1, 2, 0, 1]                    # Tag 0 ohne Kurs; Einstieg, Drehung (zwei Orders), Schließen
    assert brut[2] == pytest.approx((12 - 10) / 10 - 0.02)        # long ab Eröffnung 10, Funding des Haltetags
    assert brut[3] == pytest.approx((12 - 12) / 10 + -1 * (11 - 12) / 12)   # Schließen zur Eröffnung, short neu zu 12, ohne Funding (nan)
    assert brut[4] == pytest.approx(-1 * (11 - 11) / 12 + 0.01)   # Short erhält positives Funding
    assert brut[5] == pytest.approx(-1 * (11 - 11) / 12)          # geschlossen zur Eröffnung, kein Funding mehr
    ziel2 = np.array([0, 1, 1, 1, 1, 1], np.int8)
    b2, n2 = np.zeros(6), np.zeros(6)
    X.tag_lauf(o, c, f, ziel2, b2, n2)
    assert n2.sum() == 1 and b2.sum() == pytest.approx((13 - 10) / 10 - 0.01 - 0.02 - 0.01)   # bleibt offen, bewertet zum letzten Schluss


def einfach(o, c, fr, d, ab, mit, slip_bp, stress=False):
    """Langsame Vergleichsrechnung eines Korbs, Tag für Tag."""
    n, T_ = c.shape
    netto = np.zeros(T_)
    anz = mit.sum(axis=0)
    for i in range(n):
        pos, e, ref = 0, 0.0, 0.0
        for t in range(T_):
            if not np.isfinite(c[i, t]):
                continue
            soll = int(d[i, t - 1]) if (t > 0 and mit[i, t] and t >= ab[i]) else 0
            erg, orders = 0.0, 0
            if soll != pos:
                if pos != 0:
                    erg += pos * (o[i, t] - ref) / e; orders += 1; pos = 0
                if soll != 0:
                    pos, e, ref = soll, o[i, t], o[i, t]; orders += 1
            if pos != 0:
                erg += pos * (c[i, t] - ref) / e - (pos * fr[i, t] if np.isfinite(fr[i, t]) else 0.0)
                ref = c[i, t]
            erg -= orders * ((2 if stress else 1) * slip_bp[i] + 1.2) / 1e4
            w = anz[t] if mit[i, t] else (anz[t - 1] if t > 0 else 0)
            if erg != 0.0:
                assert w > 0
                netto[t] += erg / w
    return netto


BASIS = [0, 1, 2, 3, 4, 9, 10, 11, 12, 13]                       # zehn Kontrakte, die von Anfang an Kurse haben


def aufbau(seed=3, n=45, tage=420):
    kal = pd.date_range("2021-07-01", periods=tage, freq="D")
    o, c, qv, fr = markt(n, tage, seed, spaet=[(5, 40), (6, 100), (7, 250), (8, 400)])
    d, ab = X.richtung(c), X.dabei_ab(c)
    slip = np.random.default_rng(seed).uniform(0.5, 20, n)
    be, ne = X.einzelreihen(o, c, fr, d, ab)
    netto_e = be - ne * (slip[:, None] + X.GEB_BP) / 1e4
    mit = X.mitglieder(kal, qv, ab, netto_e, BASIS)
    return kal, o, c, qv, fr, d, ab, slip, netto_e, mit


def test_koerbe_wie_die_einfache_rechnung_und_auswahl_nur_aus_der_vergangenheit():
    kal, o, c, qv, fr, d, ab, slip, netto_e, mit = aufbau()
    for name, m in mit.items():
        for stress in (False, True):
            netto = X.korb(o, c, fr, d, ab, m, slip, stress)[0]
            assert np.allclose(netto, einfach(o, c, fr, d, ab, m, slip, stress), atol=1e-12), name
        assert np.abs(X.korb(o, c, fr, d, ab, m, slip)[0]).sum() > 0.5
    for t0, t1 in X.monatsanfaenge(kal):
        alle = set(np.nonzero(ab <= t0)[0])
        assert set(np.nonzero(mit["ALLE"][:, t0])[0]) == alle and (mit["ALLE"][:, t0:t1] == mit["ALLE"][:, [t0]]).all()
        if t0 >= 30:
            liq, klein = set(np.nonzero(mit["LIQ30"][:, t0])[0]), set(np.nonzero(mit["KLEIN"][:, t0])[0])
            assert len(liq) == min(30, len(alle)) and liq | klein == alle and not (liq & klein)
            u = np.nanmean(qv[:, t0 - 30:t0], axis=1)
            assert not klein or min(u[list(liq)]) >= max(u[list(klein)])
        gut, schlecht = set(np.nonzero(mit["GUT"][:, t0])[0]), set(np.nonzero(mit["SCHLECHT"][:, t0])[0])
        lang = [i for i in alle if ab[i] + 180 <= t0]
        assert len(gut) == len(schlecht) == len(lang) // 3 and not (gut & schlecht)
        if gut:
            leist = netto_e[:, t0 - 180:t0].sum(axis=1)
            assert min(leist[list(gut)]) >= max(leist[list(schlecht)]) and gut <= set(lang)
    assert mit["BASIS"][BASIS].all() and mit["BASIS"].sum(axis=0).max() == 10
    assert not mit["GUT"][:, :180].any() and mit["GUT"][:, 190:].any()
    # Störung: alles ab Tag 300 verfälscht; Mitglieder der Monate bis dahin und alle Tagesergebnisse davor bleiben gleich
    o2, c2, qv2, fr2 = (x.copy() for x in (o, c, qv, fr))
    rng = np.random.default_rng(9)
    c2[:, 300:] *= np.exp(np.cumsum(rng.normal(0.01, 0.05, c2[:, 300:].shape), axis=1)); o2[:, 301:] = c2[:, 300:-1]; qv2[:, 300:] *= 50; fr2[:, 300:] = 0.01
    d2 = X.richtung(c2)
    be, ne = X.einzelreihen(o2, c2, fr2, d2, ab)
    mit2 = X.mitglieder(kal, qv2, ab, be - ne * (slip[:, None] + X.GEB_BP) / 1e4, BASIS)
    grenze = [t1 for t0, t1 in X.monatsanfaenge(kal) if t0 <= 300][-1]          # der Monat, der Tag 300 enthält, steht schon vorher fest
    for name in mit:
        assert np.array_equal(mit[name][:, :grenze], mit2[name][:, :grenze]), name
        a, b = X.korb(o, c, fr, d, ab, mit[name], slip)[0], X.korb(o2, c2, fr2, d2, ab, mit2[name], slip)[0]
        assert np.array_equal(a[:300], b[:300]) and not np.array_equal(a[300:], b[300:]), name


def test_urteil_vergleicht_gut_erst_ab_dem_ersten_tag_mit_mitgliedern():
    kal = pd.date_range("2021-07-01", "2024-06-30", freq="D")
    rng = np.random.default_rng(2)
    T_, V_ = X.E.tage("T"), X.E.tage("V1")
    basis = {"T": rng.normal(0.0005, 0.02, 685), "V1": rng.normal(0.0005, 0.02, 366)}
    mit = {k: np.ones((3, len(kal)), bool) for k in ("ALLE", "LIQ30", "KLEIN", "GUT", "SCHLECHT")}
    mit["GUT"][:, :184] = False; mit["SCHLECHT"][:, :184] = False     # erste Mitglieder am 01.01.2022 (Tag 184)
    reihen = {("BASIS", zr): x for zr, x in basis.items()}
    for name in ("ALLE", "LIQ30", "KLEIN", "GUT", "SCHLECHT"):
        for zr in ("T", "V1"):
            x = basis[zr] + (0.004 if name in ("ALLE", "GUT") else -0.004)
            if name in ("GUT", "SCHLECHT") and zr == "T":
                x[:184 - T_.start] = 0.0                               # vorher ohne Mitglieder: flach
            reihen[(name, zr)] = x
            reihen[(name + "_stress", zr)] = x - (0.01 if name == "ALLE" else 0.0005)
    u = X.urteil1(reihen, mit, kal)
    assert u["GUT"]["T"]["ab_tag"] == "2022-01-01" and u["GUT"]["besteht_T_und_V1"] and u["GUT"]["bedingungen"]["5_ueber_schlecht"]
    assert u["ALLE"]["bedingungen"] == {"1_T": True, "2_V1": True, "3_netto_positiv": True, "4_stress_positiv": False} and not u["ALLE"]["besteht_T_und_V1"]
    assert not u["LIQ30"]["bedingungen"]["1_T"] and u["ALLE"]["T"]["ab_tag"] == "2021-08-15"
    reihen[("KLEIN", "T")] = np.full(685, np.nan)
    with pytest.raises(SystemExit):
        X.urteil1(reihen, mit, kal)
