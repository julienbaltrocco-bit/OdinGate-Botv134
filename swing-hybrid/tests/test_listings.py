import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from hybrid import listings as L

IDX = pd.date_range("2024-01-01", periods=200, freq="D")
NULL = pd.Series(0.0, index=IDX)


def test_paar_verdient_wenn_coin_schwaecher_als_btc():
    coin = pd.Series(np.linspace(100, 50, 200), index=IDX)       # Coin halbiert sich
    btc = pd.Series(100.0, index=IDX)
    p = L.paar(coin, btc, NULL, NULL, IDX[10], 90, 0.0, 0.0)
    assert p["grund"] == "zeit" and p["ausstieg"] == IDX[100]
    assert p["kurs"].sum() == pytest.approx(-(coin[IDX[100]] / coin[IDX[10]] - 1))    # Short verdient den Kursrückgang
    assert p["volumen"].sum() == pytest.approx(2 + coin[IDX[100]] / coin[IDX[10]] + 1)


def test_btc_seite_sichert_den_markt_ab():
    kurs = pd.Series(np.linspace(100, 200, 200), index=IDX)       # beide verdoppeln sich gleich
    p = L.paar(kurs, kurs, NULL, NULL, IDX[10], 90, 0.0, 0.0)
    assert p["kurs"].sum() == pytest.approx(0.0, abs=1e-12)


def test_stop_bei_voller_einsatzhoehe():
    coin = pd.Series(100.0, index=IDX)
    coin.iloc[20:] = 250.0                                         # Coin springt auf das 2,5-Fache
    btc = pd.Series(100.0, index=IDX)
    p = L.paar(coin, btc, NULL, NULL, IDX[10], 90, 0.0, 0.0)
    assert p["grund"] == "stop" and p["ausstieg"] == IDX[20] and p["kurs"].sum() == pytest.approx(-1.5)


def test_funding_richtung_und_kosten():
    flach = pd.Series(100.0, index=IDX)
    f = pd.Series(0.001, index=IDX)                                # positives Funding: Long zahlt, Short erhält
    p = L.paar(flach, flach, f, NULL, IDX[10], 90, 0.0015, 0.00005)
    assert p["funding"].sum() == pytest.approx(0.09)               # Short im Coin erhält 90 Tage lang 0,1 %
    q = L.paar(flach, flach, NULL, f, IDX[10], 90, 0.0015, 0.00005)
    assert q["funding"].sum() == pytest.approx(-0.09)              # Long in BTC zahlt
    assert p["slippage"].sum() == pytest.approx(2 * (0.0015 + 0.00005)) and p["volumen"].sum() == pytest.approx(4.0)
    assert p["ergebnis"] == pytest.approx(0.09 - 2 * 0.00155 - 0.0008 * 0.15 * 4)


def test_kein_blick_in_die_zukunft_und_datenende():
    rng = np.random.default_rng(1)
    coin = pd.Series(100 * np.exp(np.cumsum(rng.normal(0, 0.03, 200))), index=IDX)
    btc = pd.Series(100 * np.exp(np.cumsum(rng.normal(0, 0.02, 200))), index=IDX)
    a = L.paar(coin, btc, NULL, NULL, IDX[10], 90, 0.001, 0.0)
    coin2 = coin.copy(); coin2.iloc[150:] *= 3                     # Änderung nach dem Ausstieg ändert nichts
    b = L.paar(coin2, btc, NULL, NULL, IDX[10], 90, 0.001, 0.0)
    assert a["ergebnis"] == pytest.approx(b["ergebnis"])
    kurz = L.paar(coin.iloc[:50], btc, NULL, NULL, IDX[10], 90, 0.0, 0.0)
    assert kurz["grund"] == "datenende" and kurz["ausstieg"] == IDX[49]
    assert L.paar(coin, btc, NULL, NULL, pd.Timestamp("2030-01-01"), 90, 0.0, 0.0) is None


def test_portfolio_summiert_und_misst_einbruch():
    coin = pd.Series(np.linspace(100, 50, 200), index=IDX)
    btc = pd.Series(100.0, index=IDX)
    p = L.paar(coin, btc, NULL, NULL, IDX[10], 90, 0.0, 0.0)
    pf = L.portfolio({"A": p, "B": p}, IDX)
    assert pf["kurs"].sum() == pytest.approx(2 * 0.05 * p["kurs"].sum())
    assert pf["offen"].max() == 2 and pf["einsatz"].max() == pytest.approx(0.2)
    assert L.einbruch(pd.Series([0.1, -0.2, 0.05])) == pytest.approx(0.2 / 1.1)
