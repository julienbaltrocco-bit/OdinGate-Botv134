"""Störungstest: Kein Signal und kein Filter der Fabrik darf sich ändern, wenn nur spätere Daten verändert werden.

Alle Rohreihen aller Coins werden ab einer Kerze T verfälscht; die Signale bis T-1 müssen bitgleich bleiben.
Braucht den lokalen Datenspeicher (data/fabrik); ohne ihn wird der Test übersprungen.
"""
import sys
from pathlib import Path

import numpy as np
import pytest

F = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(F))
from fabrik import daten as D

VORHANDEN = (D.SPEICHER / "c.npy").exists()


@pytest.mark.skipif(not VORHANDEN, reason="Datenspeicher der Fabrik fehlt")
@pytest.mark.parametrize("coin,T", [(2, 300_000), (0, 250_000), (7, 345_000)])
def test_kein_blick_in_die_zukunft(coin, T, monkeypatch):
    from fabrik import signale as S
    vorher = S._roh(coin)
    echt = D.laden
    rng = np.random.default_rng(1)

    def verfaelscht(name):
        a = np.array(echt(name))
        if a.ndim == 2 and a.shape[1] == D.N and a.dtype != bool:
            a[:, T:] = a[:, T:] * (1.0 + rng.uniform(0.2, 0.8)) + (0.37 if name in ("frate", "prem", "taker_log", "fcum") else 0.0)
        return a

    monkeypatch.setattr(D, "laden", verfaelscht)
    nachher = S._roh(coin)
    for name in S.NAMEN:
        a, b = vorher[name].to_numpy()[:T], nachher[name].to_numpy()[:T]
        gleich = (a == b) | (np.isnan(a) & np.isnan(b))
        assert gleich.all(), f"{name}: {int((~gleich).sum())} Werte vor T hängen von späteren Daten ab (erste Stelle {int(np.argmin(gleich))})"
        spaeter = vorher[name].to_numpy()[T + 300: T + 3000], nachher[name].to_numpy()[T + 300: T + 3000]
    # Gegenprobe: nach T müssen sich die meisten Signale tatsächlich ändern (der Test greift)
    geaendert = sum(not np.array_equal(vorher[n].to_numpy()[T:T + 5000], nachher[n].to_numpy()[T:T + 5000], equal_nan=True) for n in S.NAMEN)
    assert geaendert >= len(S.NAMEN) * 0.8
