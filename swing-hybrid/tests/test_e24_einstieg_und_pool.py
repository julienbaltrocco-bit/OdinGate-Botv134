"""Tests zu E24 (bessere Einstiege und breiterer Pool), Festlegung in forschung/protokoll.md Abschnitt 45."""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "forschung"))
pytest.importorskip("numba")
from experimente import e23_marktstruktur as E  # noqa: E402
from experimente import e24_einstieg_und_pool as X  # noqa: E402


def kurs(n, seed):
    rng = np.random.default_rng(seed)
    return 100 * np.exp(np.cumsum(rng.normal(0, 0.003, n)))


def test_ausdehnung_wie_einfache_schleife_und_ohne_blick_in_die_zukunft():
    c = kurs(12 * 24 * 60, 1)
    z = X.ausdehnung(c)
    ch = c[11::12]
    assert np.isnan(z[:720]).all() and np.isfinite(z[720:]).all()
    for t in (720, 721, 900, len(ch) - 1):
        lr = [np.log(ch[u] / ch[u - 1]) for u in range(t - 719, t + 1)]
        assert len(lr) == 720
        assert z[t] == pytest.approx(abs(np.log(ch[t] / ch[t - 336])) / (np.std(lr, ddof=1) * np.sqrt(336)), rel=1e-9)
    c2 = c.copy(); stich = 12 * 1000 + 7
    c2[stich:] *= 1.3
    z2 = X.ausdehnung(c2)
    assert np.array_equal(z[:stich // 12], z2[:stich // 12], equal_nan=True)   # Stundenkerzen, die vor der Störung schließen
    flach = np.full(12 * 24 * 60, 50.0)
    assert np.isnan(X.ausdehnung(flach)).all()                    # ohne Schwankung ist z nicht bestimmt


def test_alter_und_gefilterte_richtung():
    d = np.array([0, 1, 1, 1, -1, -1, 0, 0, 1], np.int8)
    assert X.alter_stunden(d).tolist() == [0, 0, 1, 2, 0, 1, 0, 1, 0]
    z = np.array([np.nan, 0.2, 1.0, 1.6, 2.5, 0.4, 0.1, 3.0, 1.5])
    assert X.richtung_gefiltert(d, z, "max", 1.5).tolist() == [0, 1, 1, 0, 0, -1, 0, 0, 1]
    assert X.richtung_gefiltert(d, z, "min", 1.0).tolist() == [0, 0, 1, 1, -1, 0, 0, 0, 1]
    assert [k for k, _, _ in X.kandidaten_a()] == ["A1_z_bis_1.0", "A1_z_bis_1.5", "A1_z_bis_2.0", "A2_z_ab_0.25", "A2_z_ab_0.5", "A2_z_ab_1.0"]


def test_gefilterte_richtung_im_kern_handelt_nur_wenn_die_bedingung_gilt():
    n = 12 * 24 * 60
    c = kurs(n, 3)
    o = np.concatenate([[100.0], c[:-1]]); h = np.maximum(o, c) * 1.001; l = np.minimum(o, c) * 0.999
    d, z = E.richtung_stunden(c), X.ausdehnung(c)
    da = X.richtung_gefiltert(d, z, "max", 1.0)
    nt = n // E.TAG + 1
    leer, od = np.zeros(1), np.zeros((20000, 4))
    no = E.lauf(o, h, l, c, np.ones(n, bool), np.zeros(n), 1.0, da, 12, 3, leer, leer, leer, leer, leer.astype(np.int8), leer.astype(np.int8), E.B0, n,
                np.zeros((2, nt)), np.zeros((2, nt)), np.zeros((2, nt)), np.zeros(nt), np.zeros(7), od)
    pos = np.zeros(n, int)
    for kerze, seite, anlass, _ in od[:no]:
        pos[int(kerze):] = int(seite) if anlass == 1 else 0
    assert no > 10
    for j in range(12 * 721, n - 1):                              # Position ab Kerze j+1 = gefilterte Richtung der letzten bekannten Stunde
        assert pos[j + 1] == da[j // 12 - 1]


def tageskurse(seed, tage=900):
    rng = np.random.default_rng(seed)
    idx = pd.bdate_range("2021-01-04", periods=tage)
    c = 100 * np.exp(np.cumsum(rng.normal(0.0002, 0.015, tage)))
    return pd.DataFrame({"open": np.concatenate([[100.0], c[:-1]]) * (1 + rng.normal(0, 0.004, tage)), "close": c}, index=idx)


def test_tagesrechnung_mit_signal_gleich_tagestrend():
    d = tageskurse(5)
    kal = pd.date_range("2021-08-15", "2024-06-30", freq="D")
    alt = X.T.lauf_markt(d, kal, 0.25, 0.0004, 0.0008, 0.10)
    neu = X.lauf_signal(d, X.T.signal(d["close"]).shift(1).fillna(0.0), kal, 0.25, 0.0004, 0.0008, 0.10)
    assert np.allclose(alt.to_numpy(), neu.to_numpy(), atol=1e-12) and alt["umsatz"].sum() > 1


def test_signal_aus_dem_vortag_kennt_den_handelstag_nicht():
    idx = pd.date_range("2021-07-01", periods=200, freq="D")
    tag = pd.Series(kurs(200, 9), index=idx)
    s = X.signal_vortag(tag)
    for i in (20, 57, 199):
        assert s.iloc[i] == np.sign(tag.iloc[i - 1] - tag.iloc[i - 15])
    assert (s.iloc[:15] == 0).all()
    tag2 = tag.copy(); tag2.iloc[100:] *= 2.0                     # alles ab Tag 100 verfälscht
    assert s.iloc[:101].equals(X.signal_vortag(tag2).iloc[:101])   # das Signal für Tag 100 nutzt nur Schlüsse bis Tag 99


def test_baustein_urteil_und_nachbarn():
    rng = np.random.default_rng(4)
    kal = X.KAL
    b0 = {"T": rng.normal(0.0005, 0.03, 685), "V1": rng.normal(0.0005, 0.03, 366)}
    gut = pd.Series(rng.normal(0.004, 0.01, len(kal)), index=kal)
    u = X.baustein_urteil(gut, gut - 0.001, b0)
    assert u["besteht_T_und_V1"] and u["huerden"] == {"1_netto_positiv": True, "2_stress_positiv": True, "3_mischung_besser": True}
    schlecht = pd.Series(rng.normal(-0.002, 0.01, len(kal)), index=kal)
    u = X.baustein_urteil(schlecht, schlecht - 0.001, b0)
    assert not u["besteht_T_und_V1"] and not u["huerden"]["1_netto_positiv"]
    assert u["T"]["summe_pct"] == round(float(schlecht[:685].sum() * 100), 2)
    reihen = {("B0", zr): x for zr, x in b0.items()}
    for ken, _, _ in X.kandidaten_a():
        for zr in ("T", "V1"):
            reihen[(ken, zr)] = b0[zr] * 0.5 - 0.002
    for zr in ("T", "V1"):
        reihen[("A1_z_bis_2.0", zr)] = b0[zr] + 0.006             # klar besser, Nachbar 1,5 nicht
        reihen[("A2_z_ab_0.5", zr)] = b0[zr] + 0.006              # klar besser, Nachbar 0,25 knapp besser
        reihen[("A2_z_ab_0.25", zr)] = b0[zr] + 1e-7
    ua = X.urteil_a(reihen)
    assert not ua["A1_z_bis_2.0"]["urteil"]["4_nachbar"] and not ua["A1_z_bis_2.0"]["urteil"]["besteht_T_und_V1"]
    assert ua["A2_z_ab_0.5"]["urteil"]["besteht_T_und_V1"] and not ua["A2_z_ab_1.0"]["urteil"]["1_T"]
