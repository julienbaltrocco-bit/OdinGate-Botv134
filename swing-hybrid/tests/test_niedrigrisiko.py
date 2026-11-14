import numpy as np
import pandas as pd

from hybrid import niedrigrisiko as N


def _betas(werte, stunden=400):
    idx = pd.date_range("2024-01-01", periods=stunden, freq="1h")
    return pd.DataFrame(np.tile(werte, (stunden, 1)), index=idx, columns=[f"C{i}" for i in range(len(werte))])


def test_seiten_und_beta_neutral():
    b = _betas([0.4, 0.5, 0.6, 0.9, 1.0, 1.1, 1.2, 1.4, 1.5, 1.6])
    w = N.gewichte(b).iloc[-1]
    assert (w[["C0", "C1", "C2"]] > 0).all() and (w[["C7", "C8", "C9"]] < 0).all()
    assert (w[["C3", "C4", "C5", "C6"]] == 0).all()
    assert abs((w * b.iloc[-1]).sum()) < 1e-9             # Beta hebt sich auf
    assert abs(w.abs().sum() / 3 - 2.0) < 1e-9            # Gewichte der Seiten summieren sich zu 2


def test_nur_woechentlich_und_ohne_blick_voraus():
    b = _betas([0.4, 0.5, 0.6, 0.9, 1.0, 1.1, 1.2, 1.4, 1.5, 1.6])
    b.iloc[200:, 0] = 2.0                                  # C0 wird später zum wildesten Coin
    w = N.gewichte(b)
    wechsel = (w.diff().abs().sum(axis=1) > 0)
    stunde = ((w.index - pd.Timestamp(0)) // pd.Timedelta(hours=1)).to_numpy() + 1
    assert (stunde[wechsel.to_numpy()] % N.TAKT == 0).all()
    assert w["C0"].iloc[200] > 0                           # bis zur nächsten Umschichtung bleibt die alte Position
    assert w["C0"].iloc[-1] < 0


def test_zu_wenig_coins_kein_handel():
    b = _betas([0.5, 1.0, 1.5, np.nan, np.nan, np.nan, np.nan])
    assert (N.gewichte(b) == 0).all().all()


def test_beta_rechnung():
    rng = np.random.default_rng(1)
    idx = pd.date_range("2024-01-01", periods=600, freq="1h")
    f = rng.normal(0, 0.01, 600)
    ladung = np.array([0.5, 1.0, 1.5, 0.8, 1.2, 1.0])
    r = np.outer(f, ladung) + rng.normal(0, 0.0005, (600, 6))
    kurs = pd.DataFrame(100 * np.cumprod(1 + r, axis=0), index=idx, columns=list("abcdef"))
    from types import SimpleNamespace
    m = SimpleNamespace(coins=list("abcdef"), h1={c: pd.DataFrame({"close": kurs[c]}) for c in kurs})
    b = N.beta(m, fenster=500).iloc[-1]
    assert np.allclose(b.to_numpy(), ladung / ladung.mean(), atol=0.05)
    assert N.beta(m, fenster=500).iloc[400].isna().all()   # ohne volle Historie kein Wert
