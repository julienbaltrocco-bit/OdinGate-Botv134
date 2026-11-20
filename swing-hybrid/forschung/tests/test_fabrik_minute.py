"""Tests für das Minutenraster (protokoll.md Abschnitt 36): Parität mit dem 5-Minuten-Simulator, Stops und Ziele,
kein Blick in die Zukunft, Datenlücken. Braucht die lokalen Datenspeicher; ohne sie werden die Datentests übersprungen."""
import sys
from pathlib import Path

import numpy as np
import pytest

F = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(F))
from fabrik import daten as D, generator as G, lauf as L, minute as M, signale as S

VORHANDEN = (M.SPEICHER / "o.npy").exists() and (D.SPEICHER / "signale.npy").exists()
FAELLE = [(0, "2022-03-01", "2022-04-01"), (2, "2023-05-01", "2023-06-01"), (1, "2024-02-01", "2024-03-01")]   # BTC, SOL, ETH


def _fall(j, von, bis, signal="mom_12", th=2.0):
    """Reihen eines Coins auf beiden Rastern; Signal nur am Schluss der 5-Minuten-Kerzen."""
    i0, i1 = L.idx(von), L.idx(bis)
    r5 = {x: np.asarray(D.laden(x)[j], dtype=np.float64) for x in ("o", "h", "l", "c", "fcum")}
    sigma5 = np.asarray(D.laden("sigma")[j])
    w5 = np.asarray(D.laden("signale")[S.NAMEN.index(signal), j], dtype=np.float64)
    ein5 = np.where(w5 >= th, 1, np.where(w5 <= -th, -1, 0)).astype(np.int8)
    slip5 = np.maximum(float(D.laden("slip_bp")[j]), 0.05 * (r5["h"] - r5["l"]) / r5["c"] * 1e4)      # Kosten in bewegtem Markt
    einm, wertm = M.nur_kerzenschluss(ein5, w5)
    m = {x: np.asarray(M.laden(x)[j], dtype=np.float64) for x in ("o", "h", "l")}
    return dict(i0=i0, i1=i1, r5=r5, sigma5=sigma5, w5=w5, ein5=ein5, slip5=slip5, m=m, einm=einm, wertm=wertm,
                sigmam=M.auf_minuten(sigma5).astype(np.float32), fcumm=M.fcum_minuten(r5["fcum"]), slipm=M.slip_minuten(slip5))


def _beide(f, ausstieg, m=None):
    m = m or f["m"]
    t5 = M.trades(f["r5"]["o"], f["r5"]["h"], f["r5"]["l"], f["r5"]["fcum"], f["ein5"], f["w5"], f["sigma5"], f["slip5"], f["i0"], f["i1"], ausstieg)
    tm = M.trades(m["o"], m["h"], m["l"], f["fcumm"], f["einm"], f["wertm"], f["sigmam"], f["slipm"], 5 * f["i0"], 5 * f["i1"], ausstieg, je_kerze=5)
    return t5, tm


@pytest.mark.skipif(not VORHANDEN, reason="Datenspeicher fehlt")
@pytest.mark.parametrize("j,von,bis", FAELLE)
@pytest.mark.parametrize("ausstieg", ["h15", "h60", "h240", "signal_h720"])
def test_paritaet_ohne_stops(j, von, bis, ausstieg):
    """Signal nur am Kerzenschluss, keine Stops: dieselben Trades und Ergebnisse wie auf dem 5-Minuten-Raster."""
    t5, tm = _beide(_fall(j, von, bis), G.AUSSTIEGE[ausstieg])
    assert len(t5) == len(tm) and len(t5) >= 20
    assert np.array_equal(tm[:, 0], 5 * t5[:, 0]) and np.array_equal(tm[:, 2], t5[:, 2]) and np.array_equal(tm[:, 5], t5[:, 5])
    zu = t5[:, 5] == 0                                              # ein am Fensterende noch offener Trade endet je Raster an dessen letzter Kerze
    assert zu.sum() >= len(t5) - 1 and np.array_equal(tm[zu, 1], 5 * t5[zu, 1])
    assert np.abs(tm[zu, 3] - t5[zu, 3]).max() < 1e-6               # Ergebnis je Trade in bp


@pytest.mark.skipif(not VORHANDEN, reason="Datenspeicher fehlt")
@pytest.mark.parametrize("j,von,bis", FAELLE)
@pytest.mark.parametrize("ausstieg", ["h240_stop2", "h240_stop1.5_ziel3", "h60_stop1.5_ziel1.5"])
def test_stops_und_ziele(j, von, bis, ausstieg):
    """Mit Stop und Ziel: Solange beide Raster gleich verlaufen, gleiche Einstiege; der Ausstieg liegt in derselben 5-Minuten-Kerze.
    Abweichen darf das Ergebnis nur, wo die Minuten mehr wissen: Kurslücke zwischen zwei Minuten (schlechter als der Stop)
    oder Stop und Ziel in derselben Kerze (auf 5 Minuten zählt der Stop, auf Minuten die tatsächliche Reihenfolge)."""
    f = _fall(j, von, bis)
    halte, sl, tp, *_ = G.AUSSTIEGE[ausstieg]
    t5, tm = _beide(f, G.AUSSTIEGE[ausstieg])
    n, gleich, geprueft = min(len(t5), len(tm)), 0, 0
    assert n >= 20
    for a, b in zip(t5[:n], tm[:n]):
        if b[0] != 5 * a[0]:
            break                                                  # ab hier laufen die Raster wegen eines früheren, begründeten Unterschieds auseinander
        geprueft += 1
        assert b[2] == a[2]
        ka, d = int(a[1]), a[2]
        e = f["r5"]["o"][int(a[0])]
        s = float(f["sigma5"][int(a[0]) - 1])
        stop, ziel = e * (1 - d * sl * s), (e * (1 + d * tp * s) if tp > 0 else np.nan)
        hk, lk = f["r5"]["h"][ka], f["r5"]["l"][ka]
        stop_drin = lk <= stop if d > 0 else hk >= stop
        ziel_drin = tp > 0 and (hk >= ziel if d > 0 else lk <= ziel)
        if a[5] or b[5]:
            continue                                               # am Fensterende noch offen
        if abs(b[3] - a[3]) < 1e-6 and int(b[1]) // 5 == ka:       # Stop oder Ziel in derselben Kerze, gleiches Ergebnis
            gleich += 1
            continue
        assert int(b[1]) // 5 == ka, "Ausstieg in einer anderen 5-Minuten-Kerze"
        assert (stop_drin and ziel_drin) or (stop_drin and b[3] < a[3]), "Abweichung ohne zulässigen Grund"
    assert geprueft >= 20 and gleich >= 0.8 * geprueft


@pytest.mark.skipif(not VORHANDEN, reason="Datenspeicher fehlt")
@pytest.mark.parametrize("ausstieg", ["h60", "h240_stop1.5_ziel3", "signal_h720"])
def test_kein_blick_in_die_zukunft(ausstieg):
    """Minutendaten ab Minute T verfälscht: alle Trades, die vor T enden, bleiben unverändert."""
    f = _fall(2, "2023-05-01", "2023-06-01")
    T = 5 * f["i0"] + 20 * 1440
    _, vorher = _beide(f, G.AUSSTIEGE[ausstieg])
    rng = np.random.default_rng(3)
    falsch = {x: a.copy() for x, a in f["m"].items()}
    for a in falsch.values():
        a[T:] *= 1.0 + rng.uniform(0.2, 0.8)
    _, nachher = _beide(f, G.AUSSTIEGE[ausstieg], falsch)
    alt = vorher[vorher[:, 1] < T]
    assert len(alt) >= 10 and np.array_equal(alt, nachher[:len(alt)])
    assert not np.array_equal(vorher, nachher)                     # Gegenprobe: danach ändert sich etwas


def test_datenluecke():
    g = np.ones(12, bool)
    g[5] = False
    ok = M.handelbar(g)
    assert not ok[4] and not ok[5] and not ok[6]                   # kein Einstieg in der fehlenden Minute (Signal 4) und in der folgenden (Signal 5); Signal 6 sähe die Lücke
    assert ok[3] and ok[7] and not ok[0] and not ok[11]


def test_ausrichtung():
    x5 = np.arange(4.0)
    m = M.auf_minuten(x5)
    assert np.isnan(m[:4]).all() and m[4] == 0 and m[8] == 0 and m[9] == 1 and m[19] == 3      # Kerze i ist erst am Schluss von Minute 5i+4 bekannt
    ein, wert = M.nur_kerzenschluss(np.array([1, 0, -1], np.int8), np.array([2.0, 0.1, -3.0]))
    assert ein.tolist() == [0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, -1] and wert[4] == 2.0 and np.isnan(wert[5])
    assert M.fcum_minuten(np.array([0.0, 1.0])).tolist() == [0.0] * 5 + [1.0] * 5


@pytest.mark.skipif(not VORHANDEN, reason="Datenspeicher fehlt")
@pytest.mark.parametrize("L", [1, 12, 48])
def test_kaufdruck_minute(L):
    """Minuten-Kaufdruck: kein Blick in die Zukunft, und am Kerzenschluss gleich dem Fabrik-Signal."""
    a, b = 5 * L_IDX0, 5 * L_IDX0 + 60 * 1440                       # 60 Tage SOL ab 01.03.2023, davor 30 Tage Vorlauf
    tq, qv = (np.array(M.laden(x)[2, a - 30 * 1440:b], dtype=np.float64) for x in ("tq", "qv"))
    vorher = M.kaufdruck_minute(tq, qv, L)
    T = len(tq) - 20 * 1440
    tq2, qv2 = tq.copy(), qv.copy()
    tq2[T:] *= 1.7; qv2[T:] *= 1.3
    nachher = M.kaufdruck_minute(tq2, qv2, L)
    assert np.array_equal(vorher[:T], nachher[:T], equal_nan=True) and not np.array_equal(vorher[T:], nachher[T:], equal_nan=True)
    fabrik = np.asarray(D.laden("signale")[S.NAMEN.index(f"kaufdruck_{L}"), 2, (a - 30 * 1440) // 5:b // 5], dtype=np.float64)
    schluss = vorher[4::5]
    ok = np.isfinite(fabrik) & np.isfinite(schluss)
    ok[:2 * 2016] = False                                          # die 7-Tage-Schwankung braucht hier erst Vorlauf (im Speicher läuft sie seit 2021)
    assert ok.sum() > 10_000 and np.corrcoef(fabrik[ok], schluss[ok])[0, 1] > 0.999


L_IDX0 = L.idx("2023-03-01")
