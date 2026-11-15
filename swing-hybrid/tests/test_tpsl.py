import numpy as np

from hybrid import tpsl as T


def test_ohne_regeln_gleich_signal():
    c = np.array([100.0, 101, 102, 103, 99, 98])
    sig = np.array([0.0, 1, 1, 1, -1, -1])
    assert np.array_equal(T._zustand(c, sig, 0.0, 0.0, 0.0), sig)


def test_ziel_dann_pause_bis_signal_dreht():
    c = np.array([100.0, 105, 111, 120, 125, 110, 105])
    sig = np.array([1.0, 1, 1, 1, 1, -1, -1])
    out = T._zustand(c, sig, 0.10, 0.0, 0.0)
    assert list(out) == [1, 1, 0, 0, 0, -1, -1]              # +11 % erreicht das Ziel, danach Pause, Short erst beim Dreh


def test_stop_und_short_seite():
    c = np.array([100.0, 103, 106, 90, 80])
    sig = np.array([-1.0, -1, -1, -1, -1])
    assert list(T._zustand(c, sig, 0.0, 0.05, 0.0)) == [-1, -1, 0, 0, 0]   # Short verliert 6 %
    assert list(T._zustand(c, sig, 0.15, 0.10, 0.0)) == [-1, -1, -1, -1, 0]  # Ziel erst bei −20 %


def test_nachgezogener_stop():
    c = np.array([100.0, 120, 130, 116, 140])
    sig = np.ones(5)
    assert list(T._zustand(c, sig, 0.0, 0.0, 0.10)) == [1, 1, 1, 0, 0]       # 130 -> 116 sind mehr als 10 % zurück


def test_luecke_ohne_position():
    c = np.array([np.nan, np.nan, 100.0, 101])
    sig = np.array([0.0, 0, 1, 1])
    assert list(T._zustand(c, sig, 0.1, 0.1, 0.0)) == [0, 0, 1, 1]
