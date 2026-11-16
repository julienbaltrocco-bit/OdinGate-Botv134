"""Der Rechenkern an kleinen, von Hand nachrechenbaren Kursverläufen."""
import numpy as np
import pytest

from hybrid import engine

FEE_M, FEE_T, SLIP, EPS = 0.0004, 0.0008, 0.0005, 0.0001


def sim(close, w, high=None, low=None, open_=None, atr=1.0, **kw):
    c = np.array([close], dtype=float)
    T = c.shape[1]
    o = np.array([open_], dtype=float) if open_ is not None else np.concatenate([c[:, :1], c[:, :-1]], axis=1)
    h = np.array([high], dtype=float) if high is not None else np.maximum(o, c)
    l = np.array([low], dtype=float) if low is not None else np.minimum(o, c)
    p = dict(S=1.0, core_frac=1.0, core_market=True, n_tr=0, dip=0.0, tp=0.0, trail=False, ttl=3, eps=EPS, slip=SLIP,
             fee_m=FEE_M, fee_t=FEE_T, day_limit=9.0, max_trades=1000)
    p.update(kw)
    hour = p.pop("hour_start", np.ones(T, dtype=np.bool_))
    return engine.simulate(o, h, l, c, np.array([w], dtype=float), np.full((1, T), atr), np.zeros((1, T)),
                           np.zeros(T, dtype=np.int64), hour, p["S"], p["core_frac"], p["core_market"], p["n_tr"],
                           p["dip"], p["tp"], p["trail"], p["ttl"], p["eps"], p["slip"], p["fee_m"], p["fee_t"],
                           p["day_limit"], p["max_trades"])


def test_baseline_market_zum_open_mit_slippage():
    # Signal gilt ab Kerze 1, endet ab Kerze 3. Open = Vorkerzen-Schluss: Kauf 100, Verkauf 110.
    eq, MV, TV, FU, daily, tr, st, nt, *_ = sim([100, 105, 110, 108, 108], [0, 1, 1, 0, 0])
    kauf, verkauf = 100 * (1 + SLIP), 110 * (1 - SLIP)
    assert eq[-1] == pytest.approx((verkauf - kauf) / kauf)
    assert TV[-1] == pytest.approx(1.0 + verkauf / kauf) and MV[-1] == 0
    assert nt == 1 and st[0] == st[1] == 2


def test_short_verdient_bei_fallendem_kurs():
    eq, *_ = sim([100, 95, 90, 90, 90], [0, -1, -1, 0, 0])
    assert eq[-1] == pytest.approx((100 * (1 - SLIP) - 90 * (1 + SLIP)) / (100 * (1 - SLIP)))


def test_limit_nur_bei_durchhandeln_gefuellt():
    # Kern-Limit zum letzten Schluss (100). Kerze 1 berührt 100 nur -> kein Fill. Kerze 2 handelt durch -> Fill zu 100.
    close = [100, 101, 101, 103, 103, 103]
    low = [100, 100.0, 99.9, 101, 103, 103]
    eq, MV, TV, FU, daily, tr, st, nt, *_ = sim(close, [0, 1, 1, 1, 1, 0], low=low, core_market=False, ttl=10)
    assert MV[1] == 0.0                      # berührt, nicht durchgehandelt
    assert MV[2] == pytest.approx(1.0)       # zu 100 gefüllt, nicht besser
    raus = 103 * (1 - SLIP)
    assert eq[-1] == pytest.approx((raus - 100) / 100)


def test_limit_verfaellt_nach_ttl_und_wird_neu_eingestellt():
    # Kurs läuft weg: Order zu 100 wird nie gefüllt, nach 3 Kerzen gestrichen und zum neuen Kurs neu eingestellt.
    close = [100, 102, 104, 106, 108, 107, 109, 109]
    low = [100, 101, 102, 104, 106, 105.9, 107, 109]
    eq, MV, TV, FU, daily, tr, st, nt, *_ = sim(close, [0, 1, 1, 1, 1, 1, 1, 0], low=low, core_market=False, ttl=3)
    assert st[2] == 1 and st[3] == 3         # ein Storno, Standzeit genau 3 Kerzen
    assert MV[4] == 0 and MV[5] > 0          # neue Order zu 106 (Schluss Kerze 3) füllt in Kerze 5 (Tief 105,9)
    assert st[0] == 3 and st[1] == 2         # 2 Limits + 1 Market-Ausstieg, 2 Fills


def test_dip_kauf_und_teilgewinn_nicht_in_derselben_kerze():
    # Hybrid: Kern 50 %, 1 Tranche. Dip-Limit = Schluss - 1 x ATR. TP = Einstieg + 1 x ATR.
    close = [100, 100, 99, 100.5, 100.5, 100.5]
    low = [100, 99.95, 98.5, 99, 100.5, 100.5]
    high = [100, 100.1, 100.6, 100.6, 100.5, 100.5]   # Kerze 2 hätte TP schon erreicht: darf nicht zählen
    eq, MV, TV, FU, daily, tr, st, nt, *_ = sim(close, [0, 1, 1, 1, 1, 0], low=low, high=high, core_market=False,
                                           core_frac=0.5, n_tr=1, dip=1.0, tp=1.0, ttl=10, atr=1.0)
    taktik = tr[tr[:, 1] == 1]
    assert len(taktik) == 1
    ein, aus = int(taktik[0, 3]), int(taktik[0, 4])
    assert ein == 2 and aus == 3              # Einstieg Kerze 2 (99 durchgehandelt), TP erst in Kerze 3
    assert taktik[0, 5] == pytest.approx(0.5 * 1.0 / 99.0)   # 50 % x (100 - 99) / 99, Einstieg 99, TP 100


def test_swing_ende_schliesst_alles_und_streicht_orders():
    close = [100, 100, 99, 98, 98, 98]
    low = [100, 99.95, 98.5, 98, 98, 98]
    eq, MV, TV, FU, daily, tr, st, nt, *_ = sim(close, [0, 1, 1, 0, 0, 0], low=low, core_market=False,
                                           core_frac=0.5, n_tr=1, dip=1.0, tp=5.0, ttl=10, atr=1.0)
    assert nt == 2                            # Kern und Tranche beide geschlossen
    assert MV[-1] + TV[-1] == pytest.approx(MV[3] + TV[3])   # danach kein Handel mehr
    assert st[5] == 0


def test_kein_blick_in_die_zukunft():
    # Ändert man Kurse NACH Kerze 3, darf sich bis einschließlich Kerze 3 nichts ändern.
    rng = np.random.default_rng(1)
    c = 100 * np.exp(np.cumsum(rng.normal(0, 0.004, 400)))
    o = np.concatenate([c[:1], c[:-1]])
    h, l = np.maximum(o, c) * 1.002, np.minimum(o, c) * 0.998
    w = np.where((np.arange(400) // 50) % 2 == 1, 1.0, 0.0)
    kw = dict(core_market=False, core_frac=0.5, n_tr=3, dip=0.5, tp=0.5, trail=True, ttl=4, atr=0.5)
    a = sim(c, w, high=h, low=l, open_=o, **kw)
    c2, h2, l2, o2 = c.copy(), h.copy(), l.copy(), o.copy()
    c2[200:] *= 1.5; h2[200:] *= 1.5; l2[200:] *= 1.5; o2[201:] *= 1.5
    b = sim(c2, w, high=h2, low=l2, open_=o2, **kw)
    assert np.allclose(a[0][:200], b[0][:200]) and np.allclose(a[1][:200], b[1][:200])
    assert a[6][5] == 0                       # keine Order, die gegen eine eigene laufen könnte
