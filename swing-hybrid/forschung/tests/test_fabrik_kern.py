"""Parität: Der schnelle Simulator der Fabrik muss dieselben Trades liefern wie die Referenzrechnung (E08 und E13).

Braucht die lokalen Marktdaten (data/candles); ohne sie wird der Test übersprungen.
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

F = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(F))
pytest.importorskip("numba")
from alpha import kern as K
from fabrik import kern as FK

DATEN = (K.DATEN / "tiefe_5m" / "BTCUSDT.parquet").exists() and (K.ERG / "e13_version11_trades.csv").exists()


def _lauf(coin, halte, sx):
    from alpha import orderbuch_stuetze as S
    k, z = S.z_wert(coin)
    o, h, l = (k[x].to_numpy(np.float64) for x in ("open", "high", "low"))
    fu = K.lesen("funding", coin)["rate"]
    fu.index = fu.index.floor("5min")
    fcum = fu[~fu.index.duplicated()].reindex(k.index).fillna(0.0).cumsum().to_numpy()
    ein = np.where(z >= 3.0, 1, np.where(z <= -3.0, -1, 0)).astype(np.int8)
    aus = np.zeros((20000, 6))
    n = FK.trades_liste(o, h, l, fcum, ein, z.astype(np.float64), np.ones(len(o), np.float32), 0, len(o), halte, 0.0, 0.0, 0.0, 0.0, sx, np.zeros(len(o)), aus)
    t = pd.DataFrame(aus[:n], columns=["a", "b", "richtung", "roh", "tief", "offen"])
    t["ein"], t["aus"] = k.index[t["a"].astype(int)], k.index[t["b"].astype(int)]
    return t


@pytest.mark.skipif(not DATEN, reason="lokale Marktdaten fehlen")
@pytest.mark.parametrize("datei,halte,sx", [("e08_vollpruefung_trades.csv", 12, np.nan), ("e13_version11_trades.csv", 48, 1.0)])
def test_kern_gleich_referenz(datei, halte, sx):
    ref = pd.read_csv(K.ERG / datei, parse_dates=["ein", "aus"])
    for coin in ("BTC", "ETH", "SOL"):
        r = ref[ref["coin"] == coin].set_index("ein")
        t = _lauf(coin, halte, sx).set_index("ein")
        t = t[(t.index >= r.index.min()) & (t.index <= r.index.max())]
        assert len(t) == len(r) and (t.index == r.index).all(), (coin, len(t), len(r))
        assert (t["aus"].to_numpy() == r["aus"].to_numpy()).all()
        assert np.abs(t["roh"].to_numpy() - (r["roh"] + r["funding"]).to_numpy()).max() < 1e-6
        assert (t["richtung"].to_numpy() == r["richtung"].to_numpy()).all()


def test_stop_ziel_und_luecke():
    n = 60
    o = np.full(n, 100.0); h = o + 0.1; l = o - 0.1
    o[10:] = 97.0; h[10:] = 97.1; l[10:] = 96.9                         # Kurslücke nach unten ab Kerze 10
    ein = np.zeros(n, np.int8); ein[4] = 1
    sig = np.full(n, 0.01, np.float32); f = np.zeros(n); w = np.zeros(n)
    aus = np.zeros((5, 6))
    assert FK.trades_liste(o, h, l, f, ein, w, sig, 0, n, 48, 2.0, 0.0, 0.0, 0.0, np.nan, np.zeros(n), aus) == 1
    assert aus[0, 0] == 5 and aus[0, 1] == 10 and abs(aus[0, 3] - (97.0 / 100.0 - 1) * 1e4) < 1e-6   # Stop bei 98, gefüllt zum schlechteren Open 97
    h2 = h.copy(); o2 = o.copy(); l2 = l.copy(); o2[10:] = 100.0; l2[10:] = 99.9; h2[10:] = 100.1; h2[8] = 103.5; l2[8] = 97.5
    FK.trades_liste(o2, h2, l2, f, ein, w, sig, 0, n, 48, 2.0, 3.0, 0.0, 0.0, np.nan, np.zeros(n), aus)
    assert aus[0, 1] == 8 and abs(aus[0, 3] - (-200.0)) < 1e-3          # Kerze trifft Stop und Ziel: der Stop zählt


def test_sim_gleich_trades_liste():
    rng = np.random.default_rng(3)
    n = 5000
    c = 100 * np.exp(np.cumsum(rng.normal(0, 0.002, n))); o = np.concatenate([[100.0], c[:-1]])
    h = np.maximum(o, c) * 1.001; l = np.minimum(o, c) * 0.999
    ein = rng.choice(np.array([-1, 0, 0, 0, 0, 0, 1], np.int8), n)
    w = rng.normal(0, 1, n); sig = np.full(n, 0.005, np.float32); f = np.cumsum(np.where(np.arange(n) % 96 == 0, 1e-4, 0.0))
    tag = (np.arange(n) // 288).astype(np.int32)
    for halte, sl, tp, tr, ta, sx in ((12, 0, 0, 0, 0, np.nan), (48, 2.0, 3.0, 0, 0, np.nan), (144, 0, 0, 1.0, 0.5, np.nan), (144, 0, 0, 0, 0, 0.5)):
        z = [np.zeros(20) for _ in range(6)]
        k = FK.sim(o, h, l, f, ein, w, sig, tag, 0, n, halte, sl, tp, tr, ta, sx, np.full(n, 0.5), 2.4, *z, 0)
        aus = np.zeros((n, 6))
        m = FK.trades_liste(o, h, l, f, ein, w, sig, 0, n, halte, sl, tp, tr, ta, sx, np.full(n, 0.5), aus)
        assert abs(k - m) <= 1 and abs(z[0].sum() - aus[:k, 3].sum()) < 1e-6


def test_verzoegerung_verschiebt_genau_eine_kerze():
    """Stress "eine Kerze später": Einstieg und Signal-Ausstieg je genau eine Kerze später (Befund der Gegenprüfung vom 16.11.2026)."""
    n = 60
    o = 100.0 + np.arange(n) * 0.1; h = o + 0.05; l = o - 0.05
    ein = np.zeros(n, np.int8); ein[10] = 1
    w = np.full(n, 2.0); w[20:] = 0.0                                   # Signal fällt am Schluss der Kerze 20 unter die Ausstiegsschwelle
    sig = np.ones(n, np.float32); f = np.zeros(n); tag = np.zeros(n, np.int32)
    erg = {}
    for verzug in (0, 1):
        z = [np.zeros(1) for _ in range(6)]
        FK.sim(o, h, l, f, ein, w, sig, tag, 0, n, 48, 0.0, 0.0, 0.0, 0.0, 0.5, np.zeros(n), 0.0, *z, verzug)
        erg[verzug] = z[0][0]
    assert abs(erg[0] - (o[21] / o[11] - 1) * 1e4) < 1e-9                # Einstieg Kerze 11, Ausstieg Kerze 21
    assert abs(erg[1] - (o[22] / o[12] - 1) * 1e4) < 1e-9                # mit Verzögerung: Einstieg 12, Ausstieg 22
