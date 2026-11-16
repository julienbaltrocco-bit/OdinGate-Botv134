"""Kleine Regressionstests für das Rechenwerkzeug der Alpha-Forschung (ohne Marktdaten)."""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from alpha import kern as K, konto


def _kerzen(preise):
    idx = pd.date_range("2024-01-01", periods=len(preise), freq="5min")
    p = np.array(preise, float)
    return pd.DataFrame({"open": p, "high": p, "low": p, "close": p}, index=idx)


def test_trade_kosten_und_rebate():
    k = _kerzen([100, 100, 101, 101])
    t = K.netto(K.trades("BTC", k, np.array([1]), np.array([2]), np.array([1.0])), {"BTC": 0.5})
    z = t.iloc[0]
    assert abs(z["roh"] - 100.0) < 1e-9                      # +1 % = 100 bp
    assert abs(z["g"] - 99.0) < 1e-9                         # 2 x 0,5 bp Slippage
    assert abs(z["n0"] - 83.0) < 1e-9                        # volle Gebühr 16 bp
    assert abs(z["n85"] - 96.6) < 1e-9 and abs(z["n50"] - 91.0) < 1e-9


def test_funding_long_zahlt_short_erhaelt():
    k = _kerzen([100] * 6)
    f = pd.DataFrame({"rate": [0.0003]}, index=[k.index[3]])
    lang = K.trades("BTC", k, np.array([1]), np.array([4]), np.array([1.0]), f).iloc[0]
    kurz = K.trades("BTC", k, np.array([1]), np.array([4]), np.array([-1.0]), f).iloc[0]
    davor = K.trades("BTC", k, np.array([1]), np.array([2]), np.array([-1.0]), f).iloc[0]
    assert abs(lang["funding"] + 3.0) < 1e-9 and abs(kurz["funding"] - 3.0) < 1e-9 and davor["funding"] == 0.0


def test_eine_position_je_coin():
    ok = K.ohne_ueberlappung(np.array([1, 3, 13, 14]), np.array([13, 15, 25, 26]))
    assert ok.tolist() == [True, False, True, False]


def test_starttage_erkennt_liquidation():
    t = pd.DataFrame({"ein": pd.to_datetime(["2024-01-02", "2024-03-01"]), "aus": pd.to_datetime(["2024-01-02 01:00", "2024-03-01 01:00"]),
                      "n85": [10.0, -9000.0], "schlimmst": [-5.0, -9950.0]})
    s = konto.starttage(t, "n85", pd.Timestamp("2024-01-01"), pd.Timestamp("2024-06-01"), 1, 1.0)
    assert s["liquidationen"] > 0 and s["tiefster_kontostand"] < 0.01   # Kontostand unter der Erhaltungsmargin von 1 %
    assert konto.starttage(t.iloc[:1], "n85", pd.Timestamp("2024-01-01"), pd.Timestamp("2024-06-01"), 1, 1.0)["liquidationen"] == 0
