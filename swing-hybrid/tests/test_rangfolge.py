import sys
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from hybrid import research as R


def markt(n_coins=10, stunden=400, seed=0):
    rng = np.random.default_rng(seed)
    idx = pd.date_range("2024-01-01", periods=stunden, freq="1h")
    coins = [f"C{i}" for i in range(n_coins)]
    h1 = {c: pd.DataFrame({"close": 100 * np.exp(np.cumsum(rng.normal(0, 0.01, stunden)))}, index=idx) for c in coins}
    return SimpleNamespace(coins=coins, h1=h1)


def test_rangfolge_ist_marktneutral_und_haelt_zwischen_den_terminen():
    m = markt()
    w = R.rangfolge(m, L=72, takt=4)
    aktiv = w.iloc[100:]
    assert (aktiv.sum(axis=1) == 0).all()                                 # gleich viele Long wie Short
    assert ((aktiv == 1).sum(axis=1) == 3).all() and ((aktiv == -1).sum(axis=1) == 3).all()
    stunde = ((w.index - pd.Timestamp(0)) // pd.Timedelta(hours=1)).to_numpy() + 1
    wechsel = (w.diff().abs().sum(axis=1) > 0).to_numpy()
    assert not wechsel[stunde % 4 != 0][1:].any()                         # Änderungen nur auf dem 4-Stunden-Raster


def test_rangfolge_nutzt_keine_zukunft():
    m = markt(seed=1)
    a = R.rangfolge(m, L=72, takt=4)
    for c in m.coins:                                                     # Kurse ab Stunde 300 verändern
        m.h1[c].iloc[300:, 0] *= np.linspace(1, 2, 100)
    b = R.rangfolge(m, L=72, takt=4)
    assert a.iloc[:300].equals(b.iloc[:300])


def test_rangfolge_nimmt_die_staerksten_long():
    m = markt(n_coins=10, stunden=200, seed=2)
    for i, c in enumerate(m.coins):                                       # eindeutige Reihenfolge: C9 am stärksten
        m.h1[c]["close"] = 100 * (1 + 0.001 * (i + 1)) ** np.arange(200)
    w = R.rangfolge(m, L=72, takt=1).iloc[-1]
    assert list(w[w == 1].index) == ["C7", "C8", "C9"] and list(w[w == -1].index) == ["C0", "C1", "C2"]
