import numpy as np
import pandas as pd

from hybrid import pumpmerkmale as F


def _k(n=3000, seed=0, sprung=None):
    rng = np.random.default_rng(seed)
    idx = pd.date_range("2024-03-01", periods=n, freq="5min")
    c = 10 * np.exp(np.cumsum(rng.normal(0, 0.002, n)))
    if sprung is not None:
        c[sprung:] *= 1.4
    return pd.DataFrame({"open": c, "high": c * 1.002, "low": c * 0.998, "close": c,
                         "quote_volume": np.abs(rng.normal(1e5, 2e4, n))}, index=idx)


def test_merkmale_ohne_blick_voraus():
    a, b = _k(), _k(sprung=2500)
    f = pd.Series([0.0001, -0.0002, 0.0005], index=pd.to_datetime(["2024-03-01", "2024-03-03", "2024-03-09"]))
    ma, mb = F.merkmale(a, f), F.merkmale(b, f)
    pd.testing.assert_frame_equal(ma.iloc[:2500], mb.iloc[:2500])
    assert mb["r24"].iloc[2500:2700].max() > 0.3
    assert ma["funding"].iloc[1000] == -0.0002                     # 4.3.: der Satz vom 3.3. gilt


def test_luecke_gibt_kein_signal():
    k = _k()
    k = pd.concat([k.iloc[:1000], k.iloc[2000:]])                   # 1000 Kerzen fehlen
    m = F.merkmale(k, None)
    assert m["r24"].iloc[1000:1250].isna().all()                    # 24 Stunden nach der Lücke kein Wert
    assert m["funding"].isna().all()
    assert not F.VARIANTEN["funding_plus"](m).any()


def test_varianten_sind_teilmengen_von_roh():
    m = F.merkmale(_k(sprung=1500), pd.Series([0.0004], index=pd.to_datetime(["2024-03-01"])))
    roh = F.VARIANTEN["roh"](m)
    assert roh.sum() > 0
    for n, fn in F.VARIANTEN.items():
        assert not (fn(m) & ~roh).any(), n
    assert (F.VARIANTEN["schnell"](m) | F.VARIANTEN["langsam"](m)).sum() == roh.sum()


def test_begrenzen():
    z = pd.Timestamp("2024-01-01")
    t = pd.DataFrame({"ein_zeit": [z + pd.Timedelta(minutes=i) for i in range(5)],
                      "aus_zeit": [z + pd.Timedelta(hours=1)] * 4 + [z + pd.Timedelta(hours=3)]})
    assert len(F.begrenzen(t, 2)) == 2
    t.loc[4, "ein_zeit"] = z + pd.Timedelta(hours=2)
    assert len(F.begrenzen(t, 2)) == 3
