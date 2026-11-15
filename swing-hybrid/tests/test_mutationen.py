from types import SimpleNamespace

import numpy as np
import pandas as pd
import pytest

from hybrid import mutationen as M


def _markt(seed=0, stunden=9000, n=10, aendern_ab=None):
    rng = np.random.default_rng(seed)
    idx = pd.date_range("2023-01-01", periods=stunden, freq="1h")
    r = rng.normal(0.0002, 0.01, (stunden, n)) + rng.normal(0, 0.006, (stunden, 1))
    kurs = 100 * np.exp(np.cumsum(r, axis=0))
    vol = np.abs(rng.normal(1e6, 3e5, (stunden, n)))
    fund = rng.normal(0.0001, 0.0004, (stunden // 8, n))
    if aendern_ab is not None:
        kurs[aendern_ab:] *= 1.3; vol[aendern_ab:] *= 3; fund[aendern_ab // 8:] += 0.002
    coins = [f"C{i}" for i in range(n)]
    h1 = {c: pd.DataFrame({"close": kurs[:, i], "quote_volume": vol[:, i]}, index=idx) for i, c in enumerate(coins)}
    return SimpleNamespace(coins=coins, h1=h1, btc_close=pd.Series(kurs[:, 0], index=idx),
                           fund_h={c: pd.Series(fund[:, i], index=idx[::8]) for i, c in enumerate(coins)})


@pytest.mark.parametrize("name", list(M.VARIANTEN) + ["basis"])
def test_kein_blick_voraus_und_wertebereich(name):
    fn = M.VARIANTEN.get(name, M.basis)
    a, b = fn(_markt()), fn(_markt(aendern_ab=8000))
    assert np.allclose(a.iloc[:8000].to_numpy(), b.iloc[:8000].to_numpy())     # spätere Daten ändern nichts Früheres
    assert a.abs().max().max() <= 1.5 + 1e-9 and a.abs().sum().sum() > 0
    assert not a.isna().any().any()


def test_einzelne_regeln():
    m = _markt()
    b = M.basis(m)
    assert (M.nur_long(m) >= 0).all().all() and (M.nur_long(m).to_numpy()[b.to_numpy() > 0] == 1).all()
    asym = M.asym_70_30(m)
    assert set(np.round(np.unique(asym.to_numpy()), 2)) <= {-0.6, 0.0, 1.4}
    br = M.breite(m)
    zeile = br.iloc[-1]
    assert (zeile == 0).all() or (zeile >= 0).all() or (zeile <= 0).all()
    mt = M.markt_trend(m).iloc[-1]
    assert mt.nunique() == 1
    assert (M.band(m).diff().abs() > 0).sum().sum() < (b.diff().abs() > 0).sum().sum()      # das Band wechselt seltener


def test_reality_check():
    rng = np.random.default_rng(5)
    null = rng.normal(0, 0.01, (1500, 14))
    _, schwelle, p = M.reality_check(null, ziehungen=500)
    assert p > 0.05 and schwelle > 0
    echt = null.copy(); echt[:, 3] += 0.002
    mittel, schwelle, p = M.reality_check(echt, ziehungen=500)
    assert p < 0.05 and mittel[3] > schwelle and (np.delete(mittel, 3) < schwelle).all()
