import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from hybrid import massentest as M


def kerzen(n=3000, seed=0):
    rng = np.random.default_rng(seed)
    c = 100 * np.exp(np.cumsum(rng.normal(0.0002, 0.01, n)))
    o = np.concatenate([c[:1], c[:-1]])
    idx = pd.date_range("2024-01-01", periods=n, freq="1h")
    return pd.DataFrame({"open": o, "high": np.maximum(o, c) * 1.002, "low": np.minimum(o, c) * 0.998, "close": c,
                         "quote_volume": rng.uniform(1, 3, n)}, index=idx)


def test_feste_haltedauer_von_hand():
    o = np.array([10.0, 10, 11, 12, 13, 14, 15, 16]); c = o + 0.5
    sig = np.array([True, False, False, True, False, False, False, False]); r = np.ones(8)
    ein, ret = M.trades_fest(o, c, sig, r, 2)
    assert list(ein) == [1, 4]                                   # Signal bei 0 -> Einstieg Open 1; Signal bei 3 -> Open 4
    assert ret[0] == pytest.approx(c[2] / o[1] - 1) and ret[1] == pytest.approx(c[5] / o[4] - 1)
    ein, ret = M.trades_fest(o, c, np.ones(8, np.bool_), -r, 2)   # Short, keine Überlappung
    assert list(ein) == [1, 3, 5] and ret[0] == pytest.approx(-(c[2] / o[1] - 1))


def test_ziel_und_stop():
    o = np.full(40, 100.0); c = o.copy(); h = o + 0.1; l = o - 0.1
    a = np.full(40, 1.0); sig = np.zeros(40, np.bool_); sig[0] = True; r = np.ones(40)
    h[5] = 101.5                                                  # Ziel 101 in Kerze 5 erreicht
    ein, ret = M.trades_ziel(o, h, l, c, sig, r, a, 1.0, 24)
    assert ret[0] == pytest.approx(0.01)
    l[3] = 98.0                                                   # vorher Stop 99 in Kerze 3
    assert M.trades_ziel(o, h, l, c, sig, r, a, 1.0, 24)[1][0] == pytest.approx(-0.01)
    h[3] = 102.0                                                  # dieselbe Kerze trifft beide: Stop zählt
    assert M.trades_ziel(o, h, l, c, sig, r, a, 1.0, 24)[1][0] == pytest.approx(-0.01)


def test_kein_blick_in_die_zukunft():
    df = kerzen(seed=3)
    a = M.coin_trades(df, 14)
    df2 = df.copy()
    df2.iloc[2500:, :4] *= 1.3
    b = M.coin_trades(df2, 14)
    for name in a:
        za, ra = a[name]; zb, rb = b[name]
        # Trades, die vor der Änderung vollständig abgeschlossen waren, dürfen sich nicht ändern
        alt = za < df.index[2470]
        assert (za[alt] == zb[: alt.sum()]).all() and np.allclose(ra[alt], rb[: alt.sum()]), name


def test_einstiege_nur_in_bias_richtung():
    df = kerzen(seed=4)
    b = M.bias(df["close"], 14)
    for name, s in M.einstiege(df, b).items():
        assert not s[(b == 0).to_numpy()].any(), name
    assert len(M.coin_trades(df, 14)) == 43 * 7
