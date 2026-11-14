import numpy as np
import pandas as pd

from hybrid import tradfi_neutral as N


def _df(c):
    idx = pd.bdate_range("2023-01-02", periods=len(c))
    s = pd.Series(c, index=idx, dtype=float)
    return pd.DataFrame({"open": s.shift(1).fillna(s.iloc[0]), "close": s})


def test_paar_verdient_an_rueckkehr_und_ist_marktneutral():
    rng = np.random.default_rng(3)
    n = 300
    markt = 100 * np.exp(np.cumsum(rng.normal(0, 0.01, n)))
    abw = np.zeros(n)
    for i in range(1, n):
        abw[i] = 0.9 * abw[i - 1] + rng.normal(0, 0.01)
    a, b = _df(markt * np.exp(abw)), _df(markt)
    t = N.paar(a, b, 1.0, 0.0, 0.0, "2023-01-01")
    assert t["umsatz"].sum() > 2 and t["brutto"].sum() > 0.05
    assert abs(np.corrcoef(t["brutto"].iloc[1:], np.diff(np.log(markt)))[0, 1]) < 0.25


def test_paar_ohne_blick_voraus():
    rng = np.random.default_rng(4)
    x = 100 * np.exp(np.cumsum(rng.normal(0, 0.02, 200)))
    y = 100 * np.exp(np.cumsum(rng.normal(0, 0.02, 200)))
    t1 = N.paar(_df(x), _df(y), 1.0, 0.0, 0.0, "2023-01-01")
    x2 = x.copy(); x2[150:] *= 1.5
    t2 = N.paar(_df(x2), _df(y), 1.0, 0.0, 0.0, "2023-01-01")
    assert np.allclose(t1["umsatz"].iloc[:150], t2["umsatz"].iloc[:150])


def test_momentum_gewichte_und_gewinn():
    idx = pd.bdate_range("2021-01-01", periods=900)
    steig = np.linspace(-0.001, 0.001, 20)
    close = pd.DataFrame({f"S{i}": 100 * np.exp(steig[i] * np.arange(900)) for i in range(20)}, index=idx)
    w = N.momentum_gewichte(close)
    letzte = w.iloc[-1]
    assert abs(letzte.abs().sum() - 1.0) < 1e-9 and abs(letzte.sum()) < 1e-9
    assert (letzte[[f"S{i}" for i in range(14, 20)]] > 0).all() and (letzte[[f"S{i}" for i in range(6)]] < 0).all()
    assert (w.iloc[:12].abs().sum(axis=1) == 0).all()             # ohne 400 Tage Historie kein Handel
    t = N.momentum(close, pd.Series(0.0, index=close.columns), "2021-01-01")
    assert t["brutto"].sum() > 0.1
    teuer = N.netto(t.assign(slip=t["umsatz"] * 0.001), idx, 0.0008, 0.0, funding_jahr=0.1)
    assert teuer.sum() < t["brutto"].sum()


def test_momentum_neue_titel_erst_nach_wartezeit():
    idx = pd.bdate_range("2021-01-01", periods=700)
    close = pd.DataFrame({f"S{i}": 100.0 + i + np.arange(700) * 0.01 * (i - 6) for i in range(12)}, index=idx)
    close.iloc[:500, 0] = np.nan
    w = N.momentum_gewichte(close)
    assert (w["S0"] == 0).all()
