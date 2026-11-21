"""Tests zu E25 aus der unabhängigen Gegenprüfung (21.11.2026): Vergleich mit einer zweiten Rechnung nach dem Text,
Störungen an jedem Grenztag, Gleichstände, Lücken, Gewichte, Einteilung, Laden, Urteil.
Umgebungsvariable E25_FORSCHUNG: anderes forschung-Verzeichnis (für absichtlich verfälschte Kopien)."""
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

FORSCHUNG = Path(os.environ.get("E25_FORSCHUNG", str(Path(__file__).resolve().parents[1] / "forschung")))
sys.path.insert(0, str(FORSCHUNG))
pytest.importorskip("numba")
from experimente import e25_breites_universum as X  # noqa: E402

KOERBE = ("BASIS", "ALLE", "LIQ30", "KLEIN", "GUT", "SCHLECHT")
BASIS = list(range(10))


def test_richtige_datei():
    assert Path(X.__file__).parent.parent.resolve() == FORSCHUNG.resolve()


# ------------------------------------------------------------------ unabhängige Vergleichsrechnung nach dem Text
def ref_richtung(c):
    n, T = c.shape
    d = np.zeros((n, T), int)
    for i in range(n):
        for t in range(14, T):
            if np.isfinite(c[i, t]) and np.isfinite(c[i, t - 14]):
                d[i, t] = int(c[i, t] > c[i, t - 14]) - int(c[i, t] < c[i, t - 14])
    return d


def ref_ab(c):
    erster = [int(np.nonzero(np.isfinite(x))[0][0]) for x in c]
    return np.array([0 if e == 0 else e + 60 for e in erster])


def ref_reihe(o, c, f, soll, mitglied, gew, kosten):
    """Ergebnis je Tag = Änderung des Positionswerts Richtung*(Kurs/Einstieg-1), minus Funding, minus Orderkosten;
    Gewicht: das des letzten Tages, an dem der Kontrakt Mitglied war (Schlussorder = Gewicht des Vormonats)."""
    T = len(c)
    out, orders = np.zeros(T), np.zeros(T)
    pos, e, wert, letzter = 0, np.nan, 0.0, None
    for t in range(T):
        if not (np.isfinite(o[t]) and np.isfinite(c[t])):
            continue
        if mitglied[t]:
            letzter = t
        r = 0.0
        if soll[t] != pos:
            if pos != 0:
                r += pos * (o[t] / e - 1) - wert - kosten
                orders[t] += 1
                pos, wert = 0, 0.0
            if soll[t] != 0:
                pos, e = int(soll[t]), o[t]
                r -= kosten
                orders[t] += 1
        if pos != 0:
            neu = pos * (c[t] / e - 1)
            r += neu - wert
            wert = neu
            if np.isfinite(f[t]):
                r -= pos * f[t]
        if r != 0.0:
            out[t] = r * gew[letzter]
    return out, orders


def ref_einzel(o, c, fr, d, ab, slip):
    n, T = c.shape
    out = np.zeros((n, T))
    for i in range(n):
        mitgl = np.arange(T) >= ab[i]
        soll = np.array([d[i, t - 1] if (t > 0 and mitgl[t]) else 0 for t in range(T)])
        out[i] = ref_reihe(o[i], c[i], fr[i], soll, mitgl, np.ones(T), (slip[i] + 1.2) / 1e4)[0]
    return out


def ref_korb(o, c, fr, d, mit, slip, stress=False):
    n, T = c.shape
    anz = mit.sum(axis=0)
    gew = np.array([1.0 / a if a > 0 else 0.0 for a in anz])
    netto = np.zeros(T)
    for i in range(n):
        soll = np.array([d[i, t - 1] if (t > 0 and mit[i, t]) else 0 for t in range(T)])
        netto += ref_reihe(o[i], c[i], fr[i], soll, mit[i], gew, ((2 if stress else 1) * slip[i] + 1.2) / 1e4)[0]
    return netto


def ref_mitglieder(kal, qv, ab, einzel, basis):
    """Rückgabe: Mitglieder und Zahl der Monate, in denen ein Gleichstand genau an einer Auswahlgrenze liegt."""
    n, T = qv.shape
    m = {k: np.zeros((n, T), bool) for k in KOERBE}
    t0s = [t for t in range(T) if t == 0 or kal[t].month != kal[t - 1].month]
    grenzfall = {"LIQ30": 0, "GUT": 0, "SCHLECHT": 0}
    for a, b in zip(t0s, t0s[1:] + [T]):
        alle = [i for i in range(n) if ab[i] <= a]
        for i in alle:
            m["ALLE"][i, a:b] = True
            if i in basis:
                m["BASIS"][i, a:b] = True
        if a >= 30 and alle:
            um = {i: float(np.nanmean(qv[i, a - 30:a])) for i in alle}
            rg = sorted(alle, key=lambda i: (-um[i], i))
            for i in rg[:30]:
                m["LIQ30"][i, a:b] = True
            for i in rg[30:]:
                m["KLEIN"][i, a:b] = True
            grenzfall["LIQ30"] += len(rg) > 30 and um[rg[29]] == um[rg[30]]
        lang = [i for i in alle if a - ab[i] >= 180]
        k = len(lang) // 3
        if k:
            le = {i: float(einzel[i, a - 180:a].sum()) for i in lang}
            rg = sorted(lang, key=lambda i: (-le[i], i))
            for i in rg[:k]:
                m["GUT"][i, a:b] = True
            for i in rg[-k:]:
                m["SCHLECHT"][i, a:b] = True
            grenzfall["GUT"] += le[rg[k - 1]] == le[rg[k]]
            grenzfall["SCHLECHT"] += le[rg[-k]] == le[rg[-k - 1]]
    return m, grenzfall


def markt(seed=5, tage=440, luecken=True):
    """48 Kontrakte: 16 Grundreihen, 24 genaue Kopien (Gleichstände bei Umsatz und Leistung), 8 später gelistete
    (erster Tag 3 -> dabei ab 63, 63 + 180 = 243 = 01.03.2022; erster Tag 5 -> 245, zwei Tage zu spät für März;
    erster Tag 32 -> dabei ab 92 = 01.10.2021)."""
    rng = np.random.default_rng(seed)
    nb, T = 24, tage
    c = 100 * np.exp(np.cumsum(rng.normal(0, 0.03, (nb, T)), axis=1))
    o = np.concatenate([np.full((nb, 1), 100.0), c[:, :-1]], axis=1) * (1 + rng.normal(0, 0.003, (nb, T)))
    qv = np.round(np.exp(rng.normal(4, 1, (nb, 1))) * rng.uniform(0.5, 1.5, (nb, T)))
    fr = rng.normal(0.0002, 0.0005, (nb, T))
    fr[rng.random((nb, T)) < 0.05] = np.nan
    slip = rng.uniform(0.5, 20, nb)
    wahl = list(range(16)) + list(range(16)) + list(range(8)) + list(range(16, 24))
    o, c, qv, fr, slip = o[wahl].copy(), c[wahl].copy(), qv[wahl].copy(), fr[wahl].copy(), slip[wahl].copy()
    for i, start in zip(range(40, 48), (3, 32, 40, 100, 250, 5, 32, 420)):
        o[i, :start] = c[i, :start] = qv[i, :start] = fr[i, :start] = np.nan
    if luecken:                                                     # Lücken, nicht an einem Monatsersten
        for i, tt in ((9, (200, 201, 202)), (1, (280, 281)), (42, (366,)), (20, (300,))):
            for t in tt:
                o[i, t] = c[i, t] = qv[i, t] = np.nan
    kal = pd.date_range("2021-07-01", periods=T, freq="D")
    return kal, o, c, qv, fr, slip


def rechnen(kal, o, c, qv, fr, slip):
    d, ab = X.richtung(c), X.dabei_ab(c)
    be, ne = X.einzelreihen(o, c, fr, d, ab)
    netto_e = be - ne * (slip[:, None] + X.GEB_BP) / 1e4
    return d, ab, netto_e, X.mitglieder(kal, qv, ab, netto_e, BASIS)


# ------------------------------------------------------------------------------------------------------ Tests
def test_gebuehr_und_konstanten():
    assert X.GEB_BP == pytest.approx(1.2) and (X.WARTE, X.RUECK, X.LIQ_TAGE, X.GUT_TAGE, X.LIQ_N) == (60, 14, 30, 180, 30)
    assert X.V1_ENDE == pd.Timestamp("2024-06-30") and X.NEU_AB == pd.Timestamp("2024-07-01") and X.DATEN_ENDE == pd.Timestamp("2026-10-31")
    assert X.BASIS_SYM == [x + "USDT" for x in ("BTC", "ETH", "SOL", "XRP", "DOT", "DOGE", "ADA", "LINK", "AVAX", "LTC")]
    assert X.monatsanfaenge(pd.date_range("2021-07-01", "2021-09-02", freq="D")) == [(0, 31), (31, 62), (62, 64)]


def test_richtung_dabei_und_einzelreihen_wie_die_vergleichsrechnung():
    """Die Einzelreihen (Grundlage von GUT/SCHLECHT) dürfen die Richtung erst am Folgetag handeln."""
    kal, o, c, qv, fr, slip = markt()
    d, ab, netto_e, _ = rechnen(kal, o, c, qv, fr, slip)
    assert np.array_equal(d, ref_richtung(c)) and np.array_equal(ab, ref_ab(c))
    assert np.allclose(netto_e, ref_einzel(o, c, fr, ref_richtung(c), ref_ab(c), slip), atol=1e-12)
    assert np.abs(netto_e).sum() > 5


def test_mitglieder_genau_auch_bei_gleichstand_und_an_den_grenztagen():
    kal, o, c, qv, fr, slip = markt()
    d, ab, netto_e, mit = rechnen(kal, o, c, qv, fr, slip)
    soll, grenzfall = ref_mitglieder(kal, qv, ref_ab(c), ref_einzel(o, c, fr, ref_richtung(c), ref_ab(c), slip), BASIS)
    assert min(grenzfall.values()) >= 1, grenzfall                  # der Test enthält Gleichstände genau an den Grenzen
    for k in KOERBE:
        assert np.array_equal(mit[k], soll[k]), k
    assert mit["ALLE"][41, 92] and not mit["ALLE"][41, 91]           # dabei ab 92 = Monatserster: sofort Mitglied
    assert mit["GUT"][:, 243].sum() == (40 + 1) // 3 and not (mit["GUT"] | mit["SCHLECHT"])[45, :274].any()   # 63 + 180 = 243 zählt am 01.03.2022, 65 + 180 = 245 erst im April
    assert mit["GUT"][:, 242].sum() == 40 // 3


def test_koerbe_wie_die_vergleichsrechnung_mit_luecken():
    kal, o, c, qv, fr, slip = markt()
    d, ab, netto_e, mit = rechnen(kal, o, c, qv, fr, slip)
    for k in KOERBE:
        for stress in (False, True):
            assert np.allclose(X.korb(o, c, fr, d, ab, mit[k], slip, stress)[0], ref_korb(o, c, fr, d, mit[k], slip, stress), atol=1e-12), k
        netto, vor, orders, anzahl = X.korb(o, c, fr, d, ab, mit[k], slip)
        assert np.array_equal(anzahl, mit[k].sum(axis=0)) and (vor >= netto - 1e-15).all() and orders.sum() > 0


@pytest.mark.parametrize("p", [243, 273, 274, 275, 303, 304, 305, 320, 334, 335, 336, 365, 396])
def test_stoerung_an_jedem_grenztag(p):
    """Alles ab Tag p verfälscht (Eröffnung, Schluss, Umsatz, Funding, dazu ein Kontrakt ab p ohne Kurse):
    Richtungen, Einzelreihen und Korbergebnisse vor p und die Mitglieder aller Monate mit erstem Tag <= p bleiben gleich."""
    kal, o, c, qv, fr, slip = markt()
    d, ab, netto_e, mit = rechnen(kal, o, c, qv, fr, slip)
    rng = np.random.default_rng(100 + p)
    o2, c2, qv2, fr2 = (x.copy() for x in (o, c, qv, fr))
    n, T = c.shape
    c2[:, p:] *= np.exp(np.cumsum(rng.normal(0.02, 0.08, (n, T - p)), axis=1))
    o2[:, p:] *= np.exp(rng.normal(0, 0.05, (n, T - p)))
    qv2[:, p:] = np.round(qv2[:, p:] * rng.uniform(0.01, 100, (n, T - p)))
    fr2[:, p:] = rng.normal(0.01, 0.01, (n, T - p))
    o2[7, p:] = c2[7, p:] = qv2[7, p:] = fr2[7, p:] = np.nan
    d2, ab2, netto_e2, mit2 = rechnen(kal, o2, c2, qv2, fr2, slip)
    assert np.array_equal(ab, ab2) and np.array_equal(d[:, :p], d2[:, :p]) and np.array_equal(netto_e[:, :p], netto_e2[:, :p])
    fest = max(t1 for t0, t1 in X.monatsanfaenge(kal) if t0 <= p)
    for k in KOERBE:
        assert np.array_equal(mit[k][:, :fest], mit2[k][:, :fest]), k
        for stress in (False, True):
            a, b = X.korb(o, c, fr, d, ab, mit[k], slip, stress)[0], X.korb(o2, c2, fr2, d2, ab2, mit2[k], slip, stress)[0]
            assert np.array_equal(a[:p], b[:p]) and not np.array_equal(a[p:], b[p:]), k


def test_luecke_praezisierung_8():
    """Tag ohne Kurs: keine Order, keine Bewertung, kein Funding; d an dem Tag und 14 Tage später 0; schließen und neu eröffnen."""
    T = 60
    c = np.array([100.0 + t for t in range(T)])[None, :]
    o = c - 0.5
    f = np.full((1, T), 0.001)
    c[0, 30] = o[0, 30] = np.nan
    d, ab = X.richtung(c), X.dabei_ab(c)
    assert d[0, 30] == 0 and d[0, 44] == 0 and (np.delete(d[0, 14:], [16, 30]) == 1).all() and ab[0] == 0
    brut, nord = X.einzelreihen(o, c, f, d, ab)
    assert np.nonzero(nord[0])[0].tolist() == [15, 31, 32, 45, 46] and nord[0].sum() == 5
    assert brut[0, 30] == 0.0 and brut[0, 31] == pytest.approx((o[0, 31] - c[0, 29]) / o[0, 15])     # zu, ohne Funding
    assert brut[0, 45] == pytest.approx((o[0, 45] - c[0, 44]) / o[0, 32]) and brut[0, 46] == pytest.approx((c[0, 46] - o[0, 46]) / o[0, 46] - 0.001)


def hand(luecke):
    """Juli: Mitglieder A, B (Gewicht 1/2). August: B, C, D (1/3); A scheidet am 01.08. (Tag 31) aus."""
    T = 40
    c = np.full((4, T), 100.0)
    o = np.full((4, T), 100.0)
    c[0, 31:] = o[0, 31:] = 110.0
    if luecke:
        c[0, 31:33] = o[0, 31:33] = np.nan
    f = np.zeros((4, T))
    d = np.ones((4, T), np.int8)
    mit = np.zeros((4, T), bool)
    mit[[0, 1], :31] = True
    mit[[1, 2, 3], 31:] = True
    return o, c, f, d, np.zeros(4, int), mit, np.array([5.0, 7.0, 9.0, 11.0])


def test_schlussorder_zaehlt_mit_dem_gewicht_des_vormonats():
    o, c, f, d, ab, mit, slip = hand(False)
    netto, vor, orders, anzahl = X.korb(o, c, f, d, ab, mit, slip)
    assert netto[31] == pytest.approx((0.10 - 6.2e-4) / 2 - (10.2e-4 + 12.2e-4) / 3) and orders[31] == 3
    assert netto[1] == pytest.approx(-(6.2e-4 + 8.2e-4) / 2) and np.abs(netto[32:]).sum() == 0
    assert X.korb(o, c, f, d, ab, mit, slip, stress=True)[0][31] == pytest.approx((0.10 - 11.2e-4) / 2 - (19.2e-4 + 23.2e-4) / 3)
    mit[:, 31:] = False                                             # August ganz ohne Mitglieder: beide schließen mit 1/2
    netto = X.korb(o, c, f, d, ab, mit, slip)[0]
    assert netto[31] == pytest.approx((0.10 - 6.2e-4) / 2 - 8.2e-4 / 2) and np.abs(netto[32:]).sum() == 0


def test_schlussorder_nach_luecke_am_monatsersten():
    o, c, f, d, ab, mit, slip = hand(True)
    netto = X.korb(o, c, f, d, ab, mit, slip)[0]
    assert netto[31] == pytest.approx(-(10.2e-4 + 12.2e-4) / 3) and netto[32] == 0
    assert netto[33] == pytest.approx((0.10 - 6.2e-4) / 2)           # Vormonat: zwei Mitglieder


# ------------------------------------------------------------------------------------------- Daten und Kosten
def test_spannen_median_relativ_zur_mitte_mindestens_ein_halbes_bp(tmp_path, monkeypatch):
    (tmp_path / "data/processed").mkdir(parents=True)
    z = [("A", 100.0, 100.01), ("A", 100.0, 110.0), ("A", 100.0, 101.0), ("B", 100.0, 100.001), ("B", 100.0, 100.001), ("B", 100.0, 100.3)]
    pd.DataFrame([{"zeit": "2026-11-14 15:40:00", "symbol": s, "geld": g, "brief": b} for s, g, b in z]).to_csv(tmp_path / "data/processed/yubit_spannen_stichprobe.csv", index=False)
    monkeypatch.setattr(X, "ROOT", tmp_path)
    s = X.spannen()
    assert s["A"] == pytest.approx(1.0 / 100.5 * 1e4) and s["B"] == 0.5


def test_symbole_einteilung_nach_praezisierung_7(tmp_path, monkeypatch):
    (tmp_path / "data/processed").mkdir(parents=True)
    (tmp_path / "scripts").mkdir()
    z = [("ZZZUSDT", "2026-02-01"), ("BTCUSDT", "2021-07-01"), ("MDTUSDT", "2023-06-30"), ("GRENZUSDT", "2025-01-01"), ("VORUSDT", "2024-12-31"), ("NEUUSDT", "2025-06-01")]
    pd.DataFrame(z, columns=["symbol", "erster_tag"]).to_csv(tmp_path / "data/processed/listings_inventur.csv", index=False)
    (tmp_path / "scripts/listings_ausschluss.txt").write_text("# Kommentar\nZZZUSDT\nBTCUSDT\n\nMDTUSDT\nGRENZUSDT\nVORUSDT\n")
    monkeypatch.setattr(X, "ROOT", tmp_path)
    inv = X.symbole()
    assert inv["symbol"].tolist() == sorted(s for s, _ in z)
    assert dict(zip(inv["symbol"], inv["tradfi"])) == {"ZZZUSDT": True, "GRENZUSDT": True, "BTCUSDT": False, "MDTUSDT": False, "VORUSDT": False, "NEUUSDT": False}


def test_laden_schneidet_und_ordnet_nach_datum(tmp_path, monkeypatch):
    (tmp_path / "data/candles/1d").mkdir(parents=True)
    (tmp_path / "data/candles/funding_1d").mkdir(parents=True)
    tage = pd.date_range("2021-07-05", "2021-08-20", freq="D").delete(10)        # 15.07. fehlt
    k = pd.DataFrame({"open": np.arange(len(tage)) + 1.0, "high": 0.0, "low": 0.0, "close": np.arange(len(tage)) + 1000.0, "quote_volume": np.arange(len(tage)) + 5000.0},
                     index=pd.DatetimeIndex(tage, name="open_time"))
    k.to_parquet(tmp_path / "data/candles/1d/AAA.parquet")
    ft = pd.date_range("2021-07-04", "2021-08-20", freq="D")
    pd.DataFrame({"rate": np.arange(len(ft)) / 1e4}, index=pd.DatetimeIndex(ft, name="zeit")).to_parquet(tmp_path / "data/candles/funding_1d/AAA.parquet")
    monkeypatch.setattr(X, "ROOT", tmp_path)
    kal, o, c, qv, fr = X.laden(["AAA"], pd.Timestamp("2021-07-31"))
    assert kal[0] == pd.Timestamp("2021-07-01") and kal[-1] == pd.Timestamp("2021-07-31") and o.shape == c.shape == qv.shape == fr.shape == (1, 31)
    assert np.isnan(o[0, :4]).all() and np.isnan(c[0, 14]) and np.isnan(o[0, 14]) and np.isnan(qv[0, 14])
    assert (o[0, 4], c[0, 4], qv[0, 4]) == (1.0, 1000.0, 5000.0) and (o[0, 30], c[0, 30], qv[0, 30]) == (26.0, 1025.0, 5025.0)
    assert np.isnan(fr[0, :3]).all() and fr[0, 3] == 0.0 and fr[0, 30] == pytest.approx(27 / 1e4)
    assert np.nanmax(c) == 1025.0                                   # nichts nach dem Stichtag


def test_einteilung_und_spannen_auf_den_echten_listen():
    """Liest nur die Inventur, die Namensliste und die Spannen-Stichprobe (keine Kurse)."""
    inv = X.symbole()
    k = inv.set_index("symbol")["tradfi"]
    assert len(inv) == 529 and int(inv["tradfi"].sum()) == 197 and not k["BTCUSDT"] and not k["MDTUSDT"] and not k["ESPORTSUSDT"] and k["PAXGUSDT"]
    teil1 = inv[~inv["tradfi"] & (inv["erster_tag"] <= X.V1_ENDE)]
    neu = inv[inv["erster_tag"] >= X.NEU_AB]
    assert len(teil1) == 137 and set(X.BASIS_SYM) <= set(teil1["symbol"]) and not set(neu["symbol"]) & set(teil1["symbol"])
    assert len(neu) + len(teil1) == 529 and neu["erster_tag"].min() >= pd.Timestamp("2024-07-01")
    slip = X.spannen()
    assert set(inv["symbol"]) <= set(slip) and min(slip.values()) >= 0.5


# ------------------------------------------------------------------------------------------------------ Urteil
def urteil_eingabe(seed=4):
    kal = pd.date_range("2021-07-01", "2024-06-30", freq="D")
    rng = np.random.default_rng(seed)
    basis = {"T": rng.normal(0.0005, 0.02, 685), "V1": rng.normal(0.0005, 0.02, 366)}
    mit = {k: np.ones((2, len(kal)), bool) for k in ("ALLE", "LIQ30", "KLEIN", "GUT", "SCHLECHT")}
    reihen = {("BASIS", zr): x for zr, x in basis.items()}
    for name in ("ALLE", "LIQ30", "KLEIN", "GUT", "SCHLECHT"):
        for zr in ("T", "V1"):
            reihen[(name, zr)] = basis[zr] + (0.004 if name != "SCHLECHT" else 0.002)
            reihen[(name + "_stress", zr)] = basis[zr] + 0.003
    return kal, mit, reihen


@pytest.mark.parametrize("p, eins, zwei", [(0.025, True, True), (0.0252, False, True), (0.16, False, True), (0.1602, False, False)])
def test_urteil_schwellen_2_5_und_16_prozent(monkeypatch, p, eins, zwei):
    kal, mit, reihen = urteil_eingabe()
    monkeypatch.setattr(X.E, "stichprobe", lambda x, b: p)
    u = X.urteil1(reihen, mit, kal)
    for name in ("ALLE", "LIQ30", "KLEIN", "GUT"):
        assert (u[name]["bedingungen"]["1_T"], u[name]["bedingungen"]["2_V1"]) == (eins, zwei)
        assert u[name]["besteht_T_und_V1"] == (eins and zwei)


def test_urteil_jede_bedingung_einzeln(monkeypatch):
    monkeypatch.setattr(X.E, "stichprobe", lambda x, b: 0.0)
    kal, mit, reihen = urteil_eingabe()
    assert all(u["besteht_T_und_V1"] for u in X.urteil1(reihen, mit, kal).values())
    r = dict(reihen)                                                # Sharpe-Zahl nicht höher, obwohl die Stichprobe 0 meldet
    r[("ALLE", "V1")] = reihen[("BASIS", "V1")] - 0.0001
    u = X.urteil1(r, mit, kal)["ALLE"]
    assert u["bedingungen"]["1_T"] and not u["bedingungen"]["2_V1"] and not u["besteht_T_und_V1"]
    r = dict(reihen)                                                # netto nur in T positiv
    r[("LIQ30", "V1")] = reihen[("LIQ30", "V1")] - reihen[("LIQ30", "V1")].mean() - 1e-6
    u = X.urteil1(r, mit, kal)["LIQ30"]
    assert u["T"]["netto_positiv"] and not u["V1"]["netto_positiv"] and not u["bedingungen"]["3_netto_positiv"] and not u["besteht_T_und_V1"]
    r = dict(reihen)                                                # Stress nur in V1 positiv
    r[("KLEIN_stress", "T")] = reihen[("KLEIN_stress", "T")] - reihen[("KLEIN_stress", "T")].mean() - 1e-6
    u = X.urteil1(r, mit, kal)["KLEIN"]
    assert u["bedingungen"]["3_netto_positiv"] and not u["bedingungen"]["4_stress_positiv"] and not u["besteht_T_und_V1"]
    r = dict(reihen)                                                # GUT nur in T über SCHLECHT
    r[("SCHLECHT", "V1")] = reihen[("GUT", "V1")] + 0.002
    u = X.urteil1(r, mit, kal)
    assert u["GUT"]["T"]["ueber_schlecht"] and not u["GUT"]["V1"]["ueber_schlecht"] and not u["GUT"]["bedingungen"]["5_ueber_schlecht"] and not u["GUT"]["besteht_T_und_V1"]
    assert "5_ueber_schlecht" not in u["ALLE"]["bedingungen"] and u["ALLE"]["besteht_T_und_V1"]


def test_urteil_schneidet_basis_und_schlecht_auf_die_tage_von_gut():
    """Vor dem ersten Mitgliedstag von GUT ist BASIS überragend und SCHLECHT (fälschlich) auch: beides darf nicht zählen."""
    kal, mit, reihen = urteil_eingabe()
    a = 184 - X.E.tage("T").start
    mit["GUT"][:, :184] = False
    mit["SCHLECHT"][:, :184] = False
    rng = np.random.default_rng(8)
    basis = reihen[("BASIS", "T")].copy()
    basis[:a] = rng.normal(0.05, 0.01, a)
    reihen[("BASIS", "T")] = basis
    for name, plus in (("GUT", 0.004), ("SCHLECHT", 0.002)):
        x = basis + plus
        x[:a] = 0.0 if name == "GUT" else 0.06
        reihen[(name, "T")] = x
        reihen[(name + "_stress", "T")] = x - 0.0005
    u = X.urteil1(reihen, mit, kal)["GUT"]
    assert u["T"]["ab_tag"] == "2022-01-01" and u["T"]["besser"] and u["T"]["ueber_schlecht"] and u["besteht_T_und_V1"]
    assert u["T"]["basis_summe_pct"] == pytest.approx(round(float(basis[a:].sum() * 100), 2))
