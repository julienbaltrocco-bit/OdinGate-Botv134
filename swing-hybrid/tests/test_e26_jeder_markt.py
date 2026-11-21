"""Tests zu E26 (die Trendregel auf jedem einzelnen Markt), Festlegung in forschung/protokoll.md Abschnitt 49."""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "forschung"))
pytest.importorskip("numba")
from experimente import e26_jeder_markt as X  # noqa: E402


def kurse(von, bis, seed, drift=0.0):
    idx = pd.bdate_range(von, bis)
    rng = np.random.default_rng(seed)
    c = 100 * np.exp(np.cumsum(rng.normal(drift, 0.012, len(idx))))
    return pd.DataFrame({"open": np.concatenate([[100.0], c[:-1]]) * (1 + rng.normal(0, 0.003, len(idx))), "close": c}, index=idx)


def test_zeitraeume_und_mindestens_60_boersentage():
    d = kurse("2023-05-01", "2026-10-16", 1)
    netto, stress = X.markt_reihe(d, 0.0002), X.markt_reihe(d, 0.0002, stress=True)
    z = X.zeile(netto, stress, d.index)
    assert z["je_zeitraum_pct"]["P0"] is None and z["je_zeitraum_pct"]["T"] is None            # T hätte nur 44 Börsentage
    assert z["zeitraeume"] == 3 and not z["auffaellig"]                                        # weniger als vier Zeiträume: nie auffällig
    for p, (a, b) in (("V1", ("2023-07-01", "2024-06-30")), ("V2", ("2024-07-01", "2025-03-31")), ("P3", ("2025-04-01", "2026-12-31"))):
        assert z["je_zeitraum_pct"][p] == round(float(netto[(netto.index >= a) & (netto.index <= b)].sum() * 100), 2)
    gez = netto[netto.index >= "2023-07-01"]
    assert z["summe_pct"] == pytest.approx(float(gez.sum() * 100), abs=0.02)
    assert stress.sum() < netto.sum()                                                          # Stress kostet immer mehr


def test_auffaellig_nur_bei_allen_drei_bedingungen():
    idx = pd.bdate_range("2020-01-02", "2026-10-16")
    kal = pd.date_range(idx[0], idx[-1], freq="D")
    rng = np.random.default_rng(3)
    gut = pd.Series(0.0, index=kal); gut[idx] = rng.normal(0.002, 0.01, len(idx))
    z = X.zeile(gut, gut - 0.0001 * gut.index.isin(idx), idx)
    assert z["zeitraeume"] == 5 and z["alle_zeitraeume_positiv"] and z["t_wert"] >= 2 and z["auffaellig"]
    assert not X.zeile(gut, gut - 0.005 * gut.index.isin(idx), idx)["auffaellig"]              # im Stress negativ
    einer = gut.copy(); einer[(einer.index >= "2024-07-01") & (einer.index <= "2025-03-31")] = -0.0001
    z = X.zeile(einer, einer, idx)
    assert not z["alle_zeitraeume_positiv"] and not z["auffaellig"] and z["je_zeitraum_pct"]["V2"] < 0
    schwach = pd.Series(0.0, index=kal); schwach[idx] = rng.normal(0.00005, 0.01, len(idx))
    assert not X.zeile(schwach, schwach, idx)["auffaellig"]                                    # ohne t-Wert 2


def test_labor_etf_laden_und_kosten(tmp_path, monkeypatch):
    ordner = tmp_path / "buy_and_hold__ABC__1D__0123456789/artifacts"
    ordner.mkdir(parents=True)
    kurse("2016-01-04", "2016-03-31", 5).rename_axis("trade_date").assign(high=1.0, low=1.0, volume=5).to_csv(ordner / "ohlcv_ABC.csv")
    monkeypatch.setattr(X, "LABOR", tmp_path)
    d = X.labor_etf("ABC")
    assert list(d.columns) == ["open", "close"] and d.index[0] == pd.Timestamp("2016-01-04") and d.index.is_monotonic_increasing and len(d) == 64
    k = X.kosten()
    etf = [k[n] for n in ("SPY", "QQQ", "IWM", "EWJ", "EWY", "XLE")]
    assert k["EEM"] == k["XLK"] == k["DIA"] == pytest.approx(float(np.median(etf))) and min(k.values()) >= 0.00005
    assert sum(n.startswith("AKTIE:") for n in k) == 132 and all(n in k for n in X.LABOR_ETF + X.RUNDE14)


def test_gruppen_korb_mittelt_nur_vorhandene_maerkte():
    a = pd.Series(0.01, index=pd.date_range("2020-01-01", "2020-01-10"))
    b = pd.Series(0.03, index=pd.date_range("2020-01-06", "2020-01-10"))
    zeilen = {"A": {"gruppe": "labor_etf"}, "B": {"gruppe": "labor_etf"}, "C": {"gruppe": "runde14"}, "D": {"gruppe": "aktie"}}
    g = X.gruppen_koerbe(zeilen, {"A": a, "B": b, "C": a, "D": b})
    assert g["labor_etf"]["maerkte"] == 2 and g["labor_etf"]["summe_pct"] == pytest.approx((5 * 0.01 + 5 * 0.02) * 100)


def _kunstlader(cs, kal, tradfi=()):
    n = len(kal)
    inv = pd.DataFrame({"symbol": list(cs), "erster_tag": [kal[int(np.argmax(np.isfinite(v)))] for v in cs.values()], "tradfi": [s in tradfi for s in cs]})

    def laden(syms, bis):
        c = np.array([cs[s] for s in syms])[:, :len(pd.date_range(kal[0], bis))]
        o = np.concatenate([c[:, :1], c[:, :-1]], axis=1)
        return pd.date_range(kal[0], bis), np.where(np.isfinite(o), o, c), c, np.where(np.isfinite(c), 1e6, np.nan), np.where(np.isfinite(c), 0.0, np.nan)
    return inv, laden


def test_krypto_gleichlauf_mit_dem_korb_ist_nicht_eigenstaendig(monkeypatch):
    kal = pd.date_range("2021-07-01", "2024-06-30")
    i = np.arange(len(kal))
    trend = 100 * np.exp(0.004 * i + 0.02 * np.sin(i))
    cs = {"AAAUSDT": trend, "BBBUSDT": trend.copy(), "CCCUSDT": trend.copy()}        # drei gleiche Kontrakte: jeder ist der Korb
    inv, laden = _kunstlader(cs, kal)
    monkeypatch.setattr(X.X25, "symbole", lambda: inv)
    monkeypatch.setattr(X.X25, "laden", laden)
    monkeypatch.setattr(X.X25, "spannen", lambda: {s: 2.0 for s in cs})
    kr = X.krypto()
    for s in cs:
        assert kr[s]["auffaellig"] and not kr[s]["eigenstaendig_auffaellig"]
        assert abs(kr[s]["rest_gegen_korb_pct"]["T"]) < 0.01 and abs(kr[s]["rest_gegen_korb_pct"]["V1"]) < 0.01


def test_neue_kontrakte_nur_bericht_und_ohne_kursdaten(monkeypatch, tmp_path):
    kal = pd.date_range("2021-07-01", "2026-10-31")
    n = len(kal)

    def ab(start, g):
        c = np.full(n, np.nan)
        i0 = int(kal.get_loc(pd.Timestamp(start)))
        c[i0:] = 100 * np.exp(g * np.arange(n - i0))
        return c
    cs = {"ALTUSDT": ab("2021-07-01", 0.001), "NEUUSDT": ab("2025-01-10", 0.003), "XLEUSDT": ab("2026-06-10", -0.002), "AKTUSDT": ab("2026-02-01", 0.001),
          "KURZUSDT": ab("2026-10-01", 0.001)}
    inv, laden = _kunstlader(cs, kal, tradfi=("AKTUSDT",))
    gerufen = []
    monkeypatch.setattr(X.X25, "symbole", lambda: inv)
    monkeypatch.setattr(X.X25, "laden", lambda syms, bis: (gerufen.append(list(syms)), laden(syms, bis))[1])
    monkeypatch.setattr(X.X25, "spannen", lambda: {s: 2.0 for s in cs})
    neu = X.neue_kontrakte()
    assert "ALTUSDT" not in neu and all("ALTUSDT" not in g for g in gerufen)                  # alte Kontrakte werden nicht über den 30.06.2024 hinaus geladen
    assert neu["NEUUSDT"]["gruppe"] == "krypto_neu" and neu["XLEUSDT"]["gruppe"] == neu["AKTUSDT"]["gruppe"] == "kontrakt_aktie_index_rohstoff"
    assert neu["NEUUSDT"]["von"] == "2025-03-11" and neu["NEUUSDT"]["summe_pct"] > 0 and not neu["NEUUSDT"]["zu_kurz"]     # 60 Tage nach dem ersten Handelstag
    assert neu["XLEUSDT"]["summe_pct"] > 0                                                     # fallender Kurs: short verdient
    assert neu["KURZUSDT"] == {"gruppe": "krypto_neu", "zu_kurz": True, "tage": 0}
    (tmp_path / "data/processed").mkdir(parents=True)
    (tmp_path / "data/processed/yubit_symbole.txt").write_text("NEUUSDT\nFEHLTUSDT\nALTUSDT\n\n")
    monkeypatch.setattr(X, "ROOT", tmp_path)
    assert X.ohne_kursdaten() == ["FEHLTUSDT"]
