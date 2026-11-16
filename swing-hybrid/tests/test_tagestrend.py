import numpy as np
import pandas as pd

from hybrid import tagestrend as T


def _markt(schluss, start="2024-01-01"):
    idx = pd.bdate_range(start, periods=len(schluss))
    c = pd.Series(schluss, index=idx, dtype=float)
    return pd.DataFrame({"open": c.shift(1).fillna(c.iloc[0]), "close": c})


def test_signal_ohne_blick_voraus_und_kalendertage():
    c = _markt(np.r_[np.full(15, 100.0), np.linspace(101, 130, 30)])["close"]
    s = T.signal(c)
    assert (s.iloc[:10] == 0).all()                       # noch kein Schluss, der 14 Tage alt ist
    assert s.iloc[15] == 1 and (s.iloc[15:] == 1).all()
    c2 = c.copy(); c2.iloc[-1] = 1.0                      # spätere Kurse ändern frühere Signale nicht
    assert (T.signal(c2).iloc[:-1] == s.iloc[:-1]).all()


def test_gewinn_im_aufwaertstrend_und_kostenabzug():
    d = _markt(np.r_[np.full(15, 100.0), np.linspace(101, 160, 60)])
    kal = pd.date_range(d.index[0], d.index[-1], freq="D")
    frei = T.lauf_markt(d, kal, 1.0, 0.0, 0.0)
    teuer = T.lauf_markt(d, kal, 1.0, 0.001, 0.0008, funding_jahr=0.10)
    assert frei["brutto"].sum() > 0.3
    assert frei["umsatz"].sum() > 1.9                     # Einstieg und Schlussabrechnung
    n_frei = frei["brutto"].sum()
    n_teuer = (teuer["brutto"] - teuer["gebuehr"] + teuer["funding"]).sum()
    assert n_teuer < n_frei and teuer["funding"].sum() < 0 and teuer["gebuehr"].sum() > 0.0015


def test_einstieg_erst_am_folgetag_zur_eroeffnung():
    d = _markt(np.r_[np.full(15, 100.0), 110.0, 120.0, 130.0, 140.0])
    kal = pd.date_range(d.index[0], d.index[-1], freq="D")
    t = T.lauf_markt(d, kal, 1.0, 0.0, 0.0)
    erster = t.index[t["umsatz"] > 0][0]
    assert erster == d.index[16]                          # Signal am Tag 15 (Schluss 110), Handel am Tag 16 zur Eröffnung 110
    assert abs(t.loc[erster, "brutto"] - (120 - 110) / 110) < 1e-9


def test_short_im_abwaertstrend():
    d = _markt(np.r_[np.full(15, 100.0), np.linspace(99, 60, 40)])
    kal = pd.date_range(d.index[0], d.index[-1], freq="D")
    assert T.lauf_markt(d, kal, 1.0, 0.0, 0.0)["brutto"].sum() > 0.2


def test_kennzahlen():
    x = pd.Series([0.01, -0.02, 0.01, 0.03], index=pd.date_range("2024-01-01", periods=4))
    k = T.kennzahlen(x)
    assert abs(k["N"] - 0.03) < 1e-12 and abs(k["dd"] - 0.02 / 1.01) < 1e-9
