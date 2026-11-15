import numpy as np
import pandas as pd

from hybrid import pumpshort as P


def _k(preise):
    idx = pd.date_range("2026-09-01", periods=len(preise), freq="1min")
    p = np.asarray(preise, float)
    return pd.DataFrame({"open": p, "high": p * 1.001, "low": p * 0.999, "close": p}, index=idx)


def test_ziel_und_einstieg_nach_signal():
    k = _k(np.r_[np.full(5, 100.0), np.linspace(100, 85, 60)])
    t = P.trades_coin(k, [k.index[2] + pd.Timedelta(seconds=20)])
    assert len(t) == 1 and t[0]["ein_zeit"] == k.index[3] and t[0]["art"] == "ziel"
    assert abs(t[0]["roh"] - 0.10) < 1e-9


def test_stop_und_luecke_ueber_stop():
    k = _k(np.r_[np.full(5, 100.0), np.linspace(100, 109, 3000)])
    t = P.trades_coin(k, [k.index[0]])
    assert t[0]["art"] == "stop" and abs(t[0]["roh"] + 0.08) < 1e-9
    sprung = _k(np.r_[np.full(5, 100.0), 120.0, 120.0])
    t = P.trades_coin(sprung, [sprung.index[0]])
    assert t[0]["art"] == "stop" and abs(t[0]["roh"] + 0.20) < 1e-9      # Eröffnung jenseits des Stops gilt


def test_beides_in_einer_minute_zaehlt_als_stop():
    k = _k(np.full(10, 100.0))
    k.iloc[4, k.columns.get_loc("high")] = 110.0
    k.iloc[4, k.columns.get_loc("low")] = 88.0
    assert P.trades_coin(k, [k.index[0]])[0]["art"] == "stop"


def test_nur_eine_position_je_coin_und_zeitausstieg():
    k = _k(np.full(72 * 60 + 200, 100.0))
    sig = [k.index[0], k.index[100], k.index[72 * 60 + 50]]
    t = P.trades_coin(k, sig)
    assert len(t) == 2 and t[0]["art"] == "zeit" and abs(t[0]["roh"]) < 1e-12
    assert t[0]["aus_zeit"] == t[0]["ein_zeit"] + pd.Timedelta(hours=72)


def test_kosten_und_funding():
    t = pd.DataFrame({"ein": [100.0, 100.0], "aus": [90.0, 108.0], "art": ["ziel", "stop"],
                      "ein_zeit": pd.to_datetime(["2026-09-01 01:00", "2026-11-05 01:00"]),
                      "aus_zeit": pd.to_datetime(["2026-09-01 20:00", "2026-11-06 01:00"])})
    k = P.kosten(t, 0.001)
    assert abs(k[0] - (0.00012 + 0.001 + 0.00006 * 0.9)) < 1e-12
    assert abs(k[1] - (0.00012 + 0.001 + (0.00012 + 0.001) * 1.08)) < 1e-12
    raten = pd.Series([0.001, 0.002, 0.003], index=pd.to_datetime(["2026-09-01 00:00", "2026-09-01 08:00", "2026-09-01 16:00"]))
    f = P.funding(t, raten, pd.Series([0.0, -0.0005]), pd.Timestamp("2026-11-01"))
    assert abs(f[0] - 0.005) < 1e-12 and abs(f[1] - 3 * -0.0005) < 1e-12


def test_ziel_und_stop_je_signal():
    k = _k(np.r_[np.full(5, 100.0), np.linspace(100, 97, 600), np.full(5, 97.0), np.linspace(97, 99.5, 600)])
    t = P.trades_coin(k, [k.index[0], k.index[612]], tp=np.array([0.025, 0.05]), sl=np.array([0.02, 0.02]))
    assert [x["art"] for x in t] == ["ziel", "stop"]
    assert abs(t[0]["roh"] - 0.025) < 1e-9 and abs(t[1]["roh"] + 0.02) < 1e-9


def _pfad(punkte, schritte=400):
    teile = [np.linspace(a, b, schritte) for a, b in zip(punkte[:-1], punkte[1:])]
    return _k(np.r_[np.full(3, punkte[0]), np.concatenate(teile)])


def test_trail_stufen():
    # fällt auf 91 (−9 %): Stufe 1, Stop bei 97; steigt wieder -> Ausstieg bei 97 = +3 %
    t = P.trades_coin_trail(_pfad([100, 91, 99]), [pd.Timestamp("2026-09-01")])
    assert t[0]["art"] == "trail" and t[0]["stufen"] == 1 and abs(t[0]["roh"] - 0.03) < 1e-9
    # fällt auf 81 (−19 %): Stufen bei 8, 13, 18 % -> Stop bei 87 = +13 %
    t = P.trades_coin_trail(_pfad([100, 81, 95]), [pd.Timestamp("2026-09-01")])
    assert t[0]["stufen"] == 3 and abs(t[0]["roh"] - 0.13) < 1e-9
    # nie 8 % Gewinn: ursprünglicher Stop
    t = P.trades_coin_trail(_pfad([100, 93, 110]), [pd.Timestamp("2026-09-01")])
    assert t[0]["art"] == "stop" and abs(t[0]["roh"] + 0.08) < 1e-9


def test_trail_kerze_schliesst_ueber_neuem_stop():
    k = _k(np.full(10, 100.0))
    k.iloc[4, k.columns.get_loc("low")] = 91.0            # Docht nach unten, Schluss wieder bei 100
    t = P.trades_coin_trail(k, [k.index[0]])
    assert t[0]["art"] == "trail" and abs(t[0]["roh"] - 0.03) < 1e-9 and t[0]["aus_zeit"] == k.index[4]
