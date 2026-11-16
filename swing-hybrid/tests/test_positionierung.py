import sys
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from hybrid import positionierung as P


def markt(n=10, stunden=1500, seed=0):
    rng = np.random.default_rng(seed)
    idx = pd.date_range("2024-01-01", periods=stunden, freq="1h")
    coins = [f"C{i}" for i in range(n)]
    h1 = {c: pd.DataFrame({"close": 100 * np.exp(np.cumsum(rng.normal(0, 0.01, stunden)))}, index=idx) for c in coins}
    met = {c: pd.DataFrame({"oi": 1000 * np.exp(np.cumsum(rng.normal(0, 0.01, stunden))),
                            "konten_ls": np.exp(rng.normal(0.5, 0.3, stunden)), "profis_ls": np.exp(rng.normal(0.2, 0.2, stunden)),
                            "taker_log": rng.normal(0, 0.1, stunden)}, index=idx) for c in coins}
    return SimpleNamespace(coins=coins, h1=h1, metrik=met)


@pytest.mark.parametrize("name", list(P.SIGNALE))
def test_kein_blick_in_die_zukunft(name):
    m = markt(seed=3)
    a = P.SIGNALE[name](m)
    for c in m.coins:                                           # alles ab Stunde 1200 verändern
        m.h1[c].iloc[1200:, 0] *= 1.5
        m.metrik[c].iloc[1200:] *= 2.0
    b = P.SIGNALE[name](m)
    assert a.iloc[:1200].equals(b.iloc[:1200])


@pytest.mark.parametrize("name", sorted(P.NEUTRAL))
def test_marktneutral_und_tagesraster(name):
    w = P.SIGNALE[name](markt(seed=4)).iloc[800:]
    assert (w.sum(axis=1) == 0).all() and ((w == 1).sum(axis=1) == 3).all()
    stunde = ((w.index - pd.Timestamp(0)) // pd.Timedelta(hours=1)).to_numpy() + 1
    wechsel = (w.diff().abs().sum(axis=1) > 0).to_numpy()
    assert not wechsel[stunde % 24 != 0][1:].any()


def test_richtung_der_signale():
    m = markt(seed=5)
    idx = m.h1["C0"].index
    rng = np.random.default_rng(9)
    for i, c in enumerate(m.coins):                                       # kleine Schwankung, damit „ungewöhnlich“ messbar ist
        m.metrik[c]["konten_ls"] = np.exp(rng.normal(0, 0.01, len(idx)))
        m.metrik[c]["profis_ls"] = np.exp(rng.normal(0, 0.01, len(idx)))
        m.metrik[c]["taker_log"] = 0.01 * (i - 4.5)                       # C9 mit dem stärksten Kaufüberhang
    m.metrik["C9"].loc[idx[1400:], "konten_ls"] = 5.0                     # in C9 plötzlich sehr viele Konten long
    m.metrik["C0"].loc[idx[1400:], "profis_ls"] = 5.0                     # in C0 die Profis plötzlich stark long
    assert P.gegen_die_menge(m).iloc[-1]["C9"] == -1.0                    # überfüllte Seite wird verkauft
    assert P.profis_gegen_menge(m).iloc[-1]["C0"] == 1.0                  # den Profis folgen
    assert P.profis_gegen_menge(m).iloc[-1]["C9"] == -1.0                 # Masse long, Profis nicht: verkaufen
    w = P.orderfluss(m).iloc[-1]
    assert w["C9"] == 1.0 and w["C0"] == -1.0


def test_trend_nur_mit_steigendem_open_interest():
    m = markt(seed=6)
    for c in m.coins:
        m.h1[c]["close"] = 100 * 1.001 ** np.arange(1500)                 # klarer Aufwärtstrend
        m.metrik[c]["oi"] = 1000.0 - np.arange(1500)                      # Open Interest fällt
    assert (P.trend_frisches_geld(m).iloc[600:] == 0).all().all()
    for c in m.coins:
        m.metrik[c]["oi"] = 1000.0 + np.arange(1500)
    assert (P.trend_frisches_geld(m).iloc[600:] == 1).all().all()
    m.metrik["C0"].iloc[-1, m.metrik["C0"].columns.get_loc("oi")] = np.nan
    m.metrik["C0"].iloc[-12:, m.metrik["C0"].columns.get_loc("oi")] = np.nan   # länger als 6 Stunden ohne Wert
    assert P.trend_frisches_geld(m).iloc[-1]["C0"] == 0.0
