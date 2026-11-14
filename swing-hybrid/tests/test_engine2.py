"""Rechenkern 2 (Zielposition per Limit nachführen) an kleinen Beispielen."""
import numpy as np
import pytest

from hybrid import engine2

SLIP, EPS = 0.0005, 0.0001


def sim(close, w, high=None, low=None, open_=None, **kw):
    c = np.array([close], dtype=float)
    T = c.shape[1]
    o = np.array([open_], dtype=float) if open_ is not None else np.concatenate([c[:, :1], c[:, :-1]], axis=1)
    h = np.array([high], dtype=float) if high is not None else np.maximum(o, c)
    l = np.array([low], dtype=float) if low is not None else np.minimum(o, c)
    p = dict(S=1.0, ttl=3, eps=EPS, slip=SLIP, adverse=0.0, delay=0, stop_atr=0.0, day_limit=9.0, taker=False)
    p.update(kw)
    return engine2.simulate_target(o, h, l, c, np.array([w], dtype=float), np.ones((1, T)), np.zeros((1, T)),
                                   np.zeros(T, dtype=np.int64), p["S"], p["ttl"], p["eps"], p["slip"], p["adverse"],
                                   p["delay"], p["stop_atr"], 0.0004, 0.0008, p["day_limit"], 1000, p["taker"])


def test_einstieg_und_ausstieg_per_limit():
    # Kauf-Limit 100 (Schluss Kerze 0) füllt in Kerze 1 (Tief 99,9). Verkaufs-Limit 104 (Schluss Kerze 3) füllt in Kerze 4.
    close = [100, 102, 103, 104, 105, 105, 105]
    low = [100, 99.9, 102, 103, 104, 105, 105]
    high = [100, 102, 103, 104, 105.5, 105, 105]
    eq, MV, TV, *_ = sim(close, [0, 1, 1, 1, 0, 0, 0], low=low, high=high)
    assert eq[-1] == pytest.approx(4 / 100) and TV[-1] == 0.0      # alles Maker, Gewinn 4 %
    assert MV[-1] == pytest.approx(1.0 + 1.04)


def test_beruehren_reicht_nicht():
    close = [100, 101, 101, 101, 101]
    eq, MV, *_ = sim(close, [0, 1, 1, 1, 1], low=[100, 100, 100, 101, 101])
    assert MV[2] == 0.0


def test_drehen_in_einer_order():
    close = [100, 100, 100, 100, 100, 100]
    low = [100, 99.9, 100, 100, 100, 100]
    high = [100, 100, 100, 100.1, 100, 100]
    eq, MV, TV, FU, daily, tr, st, nt, *_ = sim(close, [0, 1, 1, -1, -1, -1], low=low, high=high)
    assert MV[3] == pytest.approx(3.0)             # 1 gekauft, dann 2 verkauft (schließen + Gegenseite)
    assert nt == 2                                  # Long-Trade und Short-Trade (Schlussabrechnung)


def test_stop_sperrt_die_richtung():
    close = [100, 100, 96, 96, 97, 97, 97]
    low = [100, 99.9, 95, 96, 96, 97, 97]
    eq, MV, TV, FU, daily, tr, st, nt, *_ = sim(close, [0, 1, 1, 1, 1, 1, 1], low=low, stop_atr=2.0)
    assert st[5] == 1 and TV[-1] > 0                # Stop bei 98 ausgelöst (Einstieg 100, ATR 1)
    assert MV[-1] == pytest.approx(1.0)             # kein Wiedereinstieg, solange das Ziel Long bleibt


def test_stress_schalter_machen_es_nur_schlechter():
    rng = np.random.default_rng(3)
    c = 100 * np.exp(np.cumsum(rng.normal(0, 0.003, 600)))
    o = np.concatenate([c[:1], c[:-1]]); h = np.maximum(o, c) * 1.001; l = np.minimum(o, c) * 0.999
    w = np.sign(np.sin(np.arange(600) / 15.0))
    basis = sim(c, w, high=h, low=l, open_=o)[0][-1]
    assert sim(c, w, high=h, low=l, open_=o, adverse=0.0005)[0][-1] < basis


def test_kein_blick_in_die_zukunft():
    rng = np.random.default_rng(2)
    c = 100 * np.exp(np.cumsum(rng.normal(0, 0.004, 400)))
    o = np.concatenate([c[:1], c[:-1]]); h = np.maximum(o, c) * 1.002; l = np.minimum(o, c) * 0.998
    w = np.sign(np.sin(np.arange(400) / 10.0))
    a = sim(c, w, high=h, low=l, open_=o, stop_atr=3.0)
    c2, h2, l2, o2 = c.copy(), h.copy(), l.copy(), o.copy()
    c2[200:] *= 1.3; h2[200:] *= 1.3; l2[200:] *= 1.3; o2[201:] *= 1.3
    b = sim(c2, w, high=h2, low=l2, open_=o2, stop_atr=3.0)
    assert np.allclose(a[0][:200], b[0][:200]) and np.allclose(a[1][:200], b[1][:200])


def test_taker_sofort_zum_open_mit_slippage():
    # Ziel ab Kerze 1 Long, ab Kerze 3 flat. Kauf zum Open 100 + Slippage, Verkauf zum Open 110 - Slippage.
    eq, MV, TV, FU, daily, tr, st, nt, *_ = sim([100, 105, 110, 108, 108], [0, 1, 1, 0, 0], taker=True)
    kauf, verkauf = 100 * (1 + SLIP), 110 * (1 - SLIP)
    assert eq[-1] == pytest.approx((verkauf - kauf) / 100)       # Stückzahl nach dem Open bemessen (1/100)
    assert MV[-1] == 0.0 and TV[-1] == pytest.approx((kauf + verkauf) / 100)
    assert st[0] == st[1] == 2 and nt == 1
