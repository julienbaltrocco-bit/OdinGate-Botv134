"""Aus der Gegenprüfung: sichert die Verdrahtung des Datenschnitts: teil1() lädt genau die 137 Krypto-Kontrakte bis 30.06.2024, teil2() lädt nur
Kontrakte mit erstem Handelstag ab 01.07.2024. `laden` ist ersetzt: es wird kein Kurs gelesen und nichts Echtes gerechnet."""
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

FORSCHUNG = Path(os.environ.get("E25_FORSCHUNG", str(Path(__file__).resolve().parents[1] / "forschung")))
sys.path.insert(0, str(FORSCHUNG))
pytest.importorskip("numba")
from experimente import e25_breites_universum as X  # noqa: E402


class Stopp(Exception):
    pass


def test_teil1_laedt_nur_bis_zum_30_06_2024(monkeypatch):
    rufe = []

    def falle(syms, bis):
        rufe.append((list(syms), bis))
        raise Stopp

    monkeypatch.setattr(X, "laden", falle)
    with pytest.raises(Stopp):
        X.teil1()
    syms, bis = rufe[0]
    assert bis == pd.Timestamp("2024-06-30") and len(syms) == 137 and syms == sorted(syms) and set(X.BASIS_SYM) <= set(syms)


def test_teil2_laedt_nur_kontrakte_ab_dem_01_07_2024(monkeypatch):
    inv = X.symbole().set_index("symbol")
    rufe = []

    def kunst(syms, bis):                                           # künstliche Kurse, damit beide Gruppen durchlaufen
        rufe.append((list(syms), bis))
        kal = pd.date_range(X.START, bis, freq="D")
        rng = np.random.default_rng(len(rufe))
        c = 100 * np.exp(np.cumsum(rng.normal(0, 0.03, (len(syms), len(kal))), axis=1))
        for i, s in enumerate(syms):
            c[i, :(inv.loc[s, "erster_tag"] - X.START).days] = np.nan
        return kal, c.copy(), c, np.where(np.isfinite(c), 1e6, np.nan), np.where(np.isfinite(c), 1e-4, np.nan)

    monkeypatch.setattr(X, "laden", kunst)
    out = X.teil2()
    assert len(rufe) == 2 and all(bis == pd.Timestamp("2026-10-31") for _, bis in rufe)
    geladen = [s for syms, _ in rufe for s in syms]
    assert len(geladen) == len(set(geladen)) == 392 and inv.loc[geladen, "erster_tag"].min() >= pd.Timestamp("2024-07-01")
    assert not set(geladen) & set(X.BASIS_SYM) and not inv.loc[rufe[0][0], "tradfi"].any() and inv.loc[rufe[1][0], "tradfi"].all()
    assert set(out) == {"krypto_neu", "aktien_index_rohstoff"} and "urteil" not in out
