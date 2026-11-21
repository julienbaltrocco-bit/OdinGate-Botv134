"""Tests zu E23 (Marktstruktur als Zusatz zur Trendregel), Festlegung in forschung/protokoll.md Abschnitt 43."""
import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "forschung"))
pytest.importorskip("numba")
from experimente import e23_marktstruktur as E  # noqa: E402


def test_zwischenhoch_wird_erst_k_kerzen_spaeter_bekannt_und_bricht_nur_einmal():
    #            0   1   2   3   4   5   6   7   8   9  10
    H = np.array([10, 11, 12, 15, 13, 12, 11, 12, 14, 16, 17.0])
    L = H - 2
    C = np.array([9, 10, 11, 14, 12, 11, 10, 11, 13, 15.5, 16.5])
    sh, sl, shn, sln, br, s = E.struktur(H, L, C, 2)
    assert np.isnan(shn[:5]).all() and shn[5] == 15              # Hoch der Kerze 3 ist mit dem Schluss der Kerze 5 bekannt
    assert sh[5] == 15 and sh[8] == 15 and br[:9].tolist() == [0] * 9
    assert br[9] == 1 and s[9] == 1 and np.isnan(sh[9])           # Schluss 15,5 über 15: Bruch nach oben, Niveau verbraucht
    assert br[10] == 0 and s[10] == 1                             # dasselbe Niveau bricht nicht noch einmal


def test_gleiches_hoch_rechts_zaehlt_links_nicht_und_tief_spiegelbildlich():
    H = np.array([5, 6, 9, 9, 6, 5, 4.0, 4, 4])
    sh, sl, shn, sln, br, s = E.struktur(H, H - 1, H - 0.5, 2)
    assert shn[4] == 9 and np.isnan(shn[5])                       # das erste der beiden gleichen Hochs gilt, das zweite nicht
    L = np.array([9, 8, 5, 5, 8, 9, 10.0, 10, 10])
    sh, sl, shn, sln, br, s = E.struktur(L + 1, L, L + 0.5, 2)
    assert sln[4] == 5 and np.isnan(sln[5])


def test_neues_niveau_gilt_vor_der_bruchpruefung_derselben_kerze():
    # Zwischenhoch 20 (Kerze 2) bekannt bei Kerze 4. Höheres Zwischenhoch 30 (Kerze 6) wird bei Kerze 8 bekannt;
    # dieselbe Kerze 8 schließt bei 25, also über dem alten und unter dem neuen Niveau: kein Bruch.
    H = np.array([10, 12, 20, 13, 12, 15, 30, 26, 27.0])
    C = np.array([9, 11, 15, 12, 11, 14, 19, 19.5, 25.0])
    sh, sl, shn, sln, br, s = E.struktur(H, C - 5, C, 2)
    assert sh[4] == 20 and br[5] == 0 and br[6] == 0 and br[7] == 0
    assert shn[8] == 30 and br[8] == 0 and sh[8] == 30


def markt(n, seed, drift=0.0):
    rng = np.random.default_rng(seed)
    c = 100 * np.exp(np.cumsum(rng.normal(drift, 0.004, n)))
    o = np.concatenate([[100.0], c[:-1]])
    h = np.maximum(o, c) * (1 + np.abs(rng.normal(0, 0.001, n)))
    l = np.minimum(o, c) * (1 - np.abs(rng.normal(0, 0.001, n)))
    return o, h, l, c, np.ones(n, bool), rng.normal(0, 1e-5, n) * (np.arange(n) % 96 == 0)


def laufen(md, art, tf=1, k=3, i_ende=None, slip=1.0):
    o, h, l, c, g, fs = md
    n = len(c)
    nt = n // E.TAG + 1
    brut, nord, slipb = np.zeros((2, nt)), np.zeros((2, nt)), np.zeros((2, nt))
    markt_, zahl, orders = np.zeros(nt), np.zeros(7), np.zeros((20000, 4))
    st = E.struktur(*E.tf_kerzen(h, l, c, 12 * tf), k)
    no = E.lauf(o, h, l, c, g, fs, slip, E.richtung_stunden(c), 12 * tf, k, *st, art, i_ende or n, brut, nord, slipb, markt_, zahl, orders)
    return dict(brut=brut, nord=nord, slipb=slipb, markt=markt_, zahl=zahl, orders=orders[:no], st=st)


ALLE = [(E.B0, 1, 3), (E.K1, 1, 3), (E.K2, 1, 3), (E.K3, 1, 3)] + [(v, tf, k) for v in (E.V1, E.V2, E.V3) for tf, k in E.EINSTELLUNGEN]


def test_basis_folgt_dem_vorzeichen_mit_einer_kerze_verzug():
    md = markt(12 * 24 * 40, 1)
    o, h, l, c, g, fs = md
    r = laufen(md, E.B0)
    dh = E.richtung_stunden(c)
    wechsel = [t for t in range(1, len(dh)) if dh[t] != dh[t - 1]]
    # Stundenkerze t endet mit Kerze 12t+11, ist bei Prüfung 12(t+1) bekannt, ausgeführt wird zur Eröffnung von 12(t+1)+1
    erwartet = sorted({12 * (t + 1) + 1 for t in wechsel if 12 * (t + 1) + 1 < len(c)})
    assert sorted(set(r["orders"][:, 0].astype(int))) == erwartet
    assert (r["orders"][:, 3] == o[r["orders"][:, 0].astype(int)]).all()
    assert r["zahl"][2:].sum() == 0                               # die Basis kennt keine Stops, Ziele, Wiedereinstiege


@pytest.mark.parametrize("art,tf,k", ALLE)
def test_buchung_stimmt_mit_den_einzelnen_trades_ueberein(art, tf, k):
    md = markt(12 * 24 * 60, 7)
    o, h, l, c, g, fs = md
    r = laufen(md, art, tf, k)
    od = r["orders"]
    assert len(od) > 4
    summe, pos, e, a = 0.0, 0, 0.0, 0
    for kerze, seite, anlass, kurs in od:                         # Seite und Anlass passen zusammen; nie zwei Positionen
        kerze = int(kerze)
        if anlass in (1, 6):
            assert pos == 0
            pos, e, a = int(seite), kurs, kerze
        else:
            assert pos != 0 and seite == -pos
            summe += pos * (kurs / e - 1) - pos * fs[a + 1:kerze + 1].sum()
            pos = 0
    if pos != 0:
        summe += pos * (c[-1] / e - 1) - pos * fs[a + 1:len(c)].sum()
    assert r["brut"].sum() == pytest.approx(summe, abs=1e-9)
    assert r["nord"].sum() == len(od)
    davor = od[:, 0].astype(int) - 1
    assert r["slipb"].sum() == pytest.approx(np.maximum(1.0, 500 * (h[davor] - l[davor]) / c[davor]).sum())


@pytest.mark.parametrize("art,tf,k", ALLE)
def test_kein_blick_in_die_zukunft(art, tf, k):
    md = markt(12 * 24 * 60, 11)
    stich = 12 * 24 * 45
    r1 = laufen(md, art, tf, k)
    o, h, l, c, g, fs = (x.copy() for x in md)
    rng = np.random.default_rng(5)
    c[stich:] = c[stich - 1] * np.exp(np.cumsum(rng.normal(0.001, 0.01, len(c) - stich)))
    o[stich:] = np.concatenate([[c[stich - 1]], c[stich:-1]])
    h[stich:], l[stich:] = np.maximum(o[stich:], c[stich:]) * 1.002, np.minimum(o[stich:], c[stich:]) * 0.998
    r2 = laufen((o, h, l, c, g, fs), art, tf, k)
    a = r1["orders"][r1["orders"][:, 0] <= stich]                 # Orders bis einschließlich der Eröffnung der Stichkerze
    b = r2["orders"][r2["orders"][:, 0] <= stich]
    assert len(a) > 2 and a.shape == b.shape and (a[:, :3] == b[:, :3]).all() and (a[a[:, 0] < stich] == b[b[:, 0] < stich]).all()


def test_struktur_stop_niveau_pause_und_wiedereinstieg():
    md = markt(12 * 24 * 60, 3, drift=-0.00005)
    o, h, l, c, g, fs = md
    for art in (E.V1, E.V2):
        r = laufen(md, art, 1, 3)
        od = r["orders"]
        sh, sl, shn, sln, br, s = r["st"]
        dh = E.richtung_stunden(c)
        stops = od[od[:, 2] == 3]
        assert len(stops) > 3
        for kerze, seite, _, _ in stops:                          # ein Stop schließt genau dann, wenn der Schluss davor jenseits des Niveaus lag
            j = int(kerze) - 1
            ein = od[(od[:, 0] < kerze) & np.isin(od[:, 2], (1, 6))][-1]
            je, pos = int(ein[0]) - 1, int(ein[1])                # Prüfkerze des Einstiegs
            t = je // 12 - 1
            lvl = (sh if pos < 0 else sl)[t]
            if pos < 0:
                stop = lvl if (lvl == lvl and lvl > c[je]) else h[max(0, je - 7 * 12 + 1):je + 1].max()
            else:
                stop = lvl if (lvl == lvl and lvl < c[je]) else l[max(0, je - 7 * 12 + 1):je + 1].min()
            for q in range(je + 1, j + 1):                        # Nachrücken nur zu Niveaus zwischen Kurs und Stop
                if q % 12 == 0:
                    neu = (shn if pos < 0 else sln)[q // 12 - 1]
                    if neu == neu and ((pos < 0 and c[q] < neu < stop) or (pos > 0 and c[q] > neu > stop)):
                        stop = neu
                if q < j:
                    assert not ((pos < 0 and c[q] > stop) or (pos > 0 and c[q] < stop))
            assert (pos < 0 and c[j] > stop) or (pos > 0 and c[j] < stop)
        wieder = od[od[:, 2] == 6]
        if art == E.V1:
            assert len(wieder) == 0
            for kerze, seite, _, _ in stops:                      # nach einem Stop bleibt V1 flach, bis d wechselt
                danach = od[od[:, 0] > kerze]
                if len(danach):
                    jn = int(danach[0, 0]) - 1
                    assert dh[jn // 12 - 1] == danach[0, 1] and dh[jn // 12 - 1] != -seite
        else:
            assert len(wieder) > 0
            for kerze, seite, _, _ in wieder:                     # Wiedereinstieg nur bei frisch bekanntem Bruch in Richtung d
                j = int(kerze) - 1
                assert j % 12 == 0 and br[j // 12 - 1] == seite and dh[j // 12 - 1] == seite


def test_struktur_filter_haelt_nur_wenn_struktur_und_trend_gleich_laufen():
    md = markt(12 * 24 * 60, 9)
    o, h, l, c, g, fs = md
    r = laufen(md, E.V3, 1, 3)
    dh, s = E.richtung_stunden(c), r["st"][5]
    pos = np.zeros(len(c), int)
    for kerze, seite, anlass, _ in r["orders"]:
        pos[int(kerze):] = int(seite) if anlass in (1, 6) else 0
    for j in range(12 * 400, len(c) - 1):                         # Position ab Kerze j+1 = Soll bei Prüfung j
        d, st = dh[j // 12 - 1], s[j // 12 - 1]
        assert pos[j + 1] == (d if (d != 0 and st == d) else 0)


def test_vergleichsregeln_stop_ziel_nachzug():
    md = markt(12 * 24 * 90, 21)
    o, h, l, c, g, fs = md
    for art, anlass in ((E.K1, 3), (E.K2, 3), (E.K2, 4), (E.K3, 5)):
        od = laufen(md, art)["orders"]
        raus = od[od[:, 2] == anlass]
        if anlass != 4:
            assert len(raus) > 0
        for kerze, seite, _, _ in raus:
            ein = od[(od[:, 0] < kerze) & (od[:, 2] == 1)][-1]
            a, pos, e = int(ein[0]), int(ein[1]), ein[3]
            j = int(kerze) - 1
            if anlass == 3:
                assert (c[j] / e - 1) * pos <= -0.05 and ((c[a:j] / e - 1) * pos > -0.05).all()
            elif anlass == 4:
                assert (c[j] / e - 1) * pos >= 0.15
            else:
                best = np.maximum.accumulate(np.concatenate([[e], c[a:j + 1]])) if pos > 0 else np.minimum.accumulate(np.concatenate([[e], c[a:j + 1]]))
                assert (c[j] / best[-1] - 1) * pos <= -0.05 and ((c[a:j] / best[1:-1] - 1) * pos > -0.05).all()


def test_datenluecke_keine_order_und_stichprobe_fest():
    md = markt(12 * 24 * 40, 4)
    o, h, l, c, g, fs = md
    g = g.copy(); g[12 * 24 * 20:12 * 24 * 22] = False
    od = laufen((o, h, l, c, g, fs), E.K3)["orders"]
    assert not ((od[:, 0] >= 12 * 24 * 20) & (od[:, 0] <= 12 * 24 * 22)).any()
    rng = np.random.default_rng(1)
    a, b = rng.normal(0.001, 0.01, 400), rng.normal(0.0, 0.01, 400)
    p = E.stichprobe(a, b, zuege=500)
    assert p == E.stichprobe(a, b, zuege=500) and 0 <= p <= 1 and E.stichprobe(a, a, zuege=50) == 1.0
    assert E.nachbarn("V2_4h_k3") == ["V2_1h_k3", "V2_4h_k5"]
