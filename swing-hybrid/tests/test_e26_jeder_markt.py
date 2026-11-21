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
    etf = [k[n] for n in ("SPY", "QQQ", "IWM", "EWJ", "EWY", "DIA", "XLE")]
    assert k["EEM"] == k["XLK"] == pytest.approx(float(np.median(etf))) and min(k.values()) >= 0.00005
    assert sum(n.startswith("AKTIE:") for n in k) == 134 and all(n in k for n in X.LABOR_ETF + X.RUNDE14)


def test_gruppen_korb_mittelt_nur_vorhandene_maerkte():
    a = pd.Series(0.01, index=pd.date_range("2020-01-01", "2020-01-10"))
    b = pd.Series(0.03, index=pd.date_range("2020-01-06", "2020-01-10"))
    zeilen = {"A": {"gruppe": "labor_etf"}, "B": {"gruppe": "labor_etf"}, "C": {"gruppe": "runde14"}, "D": {"gruppe": "aktie"}}
    g = X.gruppen_koerbe(zeilen, {"A": a, "B": b, "C": a, "D": b})
    assert g["labor_etf"]["maerkte"] == 2 and g["labor_etf"]["summe_pct"] == pytest.approx((5 * 0.01 + 5 * 0.02) * 100)
