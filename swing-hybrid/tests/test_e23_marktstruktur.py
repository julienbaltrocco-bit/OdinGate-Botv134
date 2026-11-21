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


# ------------------------------------------------------------------ aus der unabhängigen Gegenprüfung (21.11.2026)
sys.path.insert(0, str(Path(__file__).resolve().parent))
import e23_referenz as G  # noqa: E402

NAME = {E.B0: "B0", E.V1: "V1", E.V2: "V2", E.V3: "V3", E.K1: "K1", E.K2: "K2", E.K3: "K3"}


def kunst(seed, tage=70, tick=0.5, luecken=True):
    """Grobe Kursstufen (Gleichstände, d = 0), zufällige Datenlücken auch an 4-Stunden-Grenzen, Funding."""
    rng = np.random.default_rng(seed)
    n = 288 * tage
    c = np.round(100 * np.exp(np.cumsum(rng.normal(0, 0.004, n))) / tick) * tick
    o = np.round(np.concatenate([[100.0], c[:-1]]) * (1 + rng.normal(0, 0.0005, n)) / tick) * tick
    h = np.maximum(o, c) + tick * rng.integers(0, 3, n)
    l = np.minimum(o, c) - tick * rng.integers(0, 3, n)
    g = np.ones(n, bool)
    if luecken:
        for _ in range(12):
            a = int(rng.integers(288 * 15, n - 400)); ln = int(rng.choice([1, 2, 11, 12, 13, 47, 48, 49, 300]))
            if rng.random() < 0.5:
                a = (a // 48) * 48 + int(rng.choice([-1, 0, 1]))
            g[a:a + ln] = False
        last = c[0]
        for i in range(n):
            if g[i]:
                last = c[i]
            else:
                o[i] = h[i] = l[i] = c[i] = last
    fs = rng.normal(0, 1e-4, n) * (np.arange(n) % 96 == 0)
    return o, h, l, c, g, fs


@pytest.mark.parametrize("art,tf,k", ALLE)
@pytest.mark.parametrize("seed", [0, 1, 2])
def test_orders_und_tagesbuchung_wie_die_zweite_rechnung(art, tf, k, seed):
    md = kunst(seed); n = len(md[3])
    r = laufen(md, art, tf, k)
    zweite = G.sim(md + (1.0,), NAME[art], tf, k, n)
    assert [(int(x[0]), int(x[1]), E.GRUND[int(x[2])], float(x[3])) for x in r["orders"]] == zweite and len(zweite) > 4
    b, no, s, m = G.buchung(md + (1.0,), zweite, n)
    assert np.abs(b - r["brut"]).max() < 1e-12 and np.array_equal(no, r["nord"]) and np.abs(s - r["slipb"]).max() < 1e-9 and np.array_equal(m, r["markt"])
    x = r["orders"][:, 0].astype(int)
    assert md[4][x].all() and md[4][x - 1].all()                  # keine Order ohne gültige Prüf- und Ausführungskerze


@pytest.mark.parametrize("art,tf,k", ALLE)
def test_kein_blick_in_die_zukunft_an_beliebigen_kerzen(art, tf, k):
    md = kunst(5, luecken=False); n = len(md[3])
    r1 = laufen(md, art, tf, k)
    for stich in np.random.default_rng(1).integers(288 * 16, n - 3, 60):
        stich = int(stich)                                        # nicht an Stunden-, 4-Stunden- oder Tagesgrenzen ausgerichtet
        o, h, l, c, g, fs = (x.copy() for x in md)
        rng = np.random.default_rng(stich)
        c[stich:] = c[stich - 1] * np.exp(np.cumsum(rng.normal(0.001, 0.01, n - stich)))
        o[stich:] = np.concatenate([[c[stich - 1]], c[stich:-1]])
        h[stich:], l[stich:] = np.maximum(o[stich:], c[stich:]) * 1.004, np.minimum(o[stich:], c[stich:]) * 0.996
        a, b = r1["orders"], laufen((o, h, l, c, g, fs), art, tf, k)["orders"]
        a, b = a[a[:, 0] <= stich], b[b[:, 0] <= stich]
        assert a.shape == b.shape and (a[:, :3] == b[:, :3]).all()


def test_luecke_verschiebt_eine_faellige_order():
    md = kunst(3, luecken=False)
    od = laufen(md, E.B0, 1, 3)["orders"]
    kerzen, anz = np.unique(od[:, 0].astype(int), return_counts=True)
    x = int(kerzen[anz == 2][len(kerzen[anz == 2]) // 2])          # eine Drehung der Basis (zwei Orders zur selben Eröffnung)
    assert x % 12 == 1
    o, h, l, c, g, fs = (y.copy() for y in md)
    g[x - 3:x + 8] = False                                        # die fällige Prüfung fällt aus; die nächste mögliche ist x+8
    od2 = laufen((o, h, l, c, g, fs), E.B0, 1, 3)["orders"]
    assert not ((od2[:, 0] >= x - 3) & (od2[:, 0] <= x + 8)).any()
    a, b = od[od[:, 0] == x], od2[od2[:, 0] == x + 9]
    assert len(b) == 2 and (a[:, 1:3] == b[:, 1:3]).all() and (b[:, 3] == o[x + 9]).all()


@pytest.mark.parametrize("tf,k", E.EINSTELLUNGEN)
def test_stop_niveau_loest_genau_jenseits_des_erwarteten_kurses_aus(tf, k):
    md = kunst(8, luecken=False); o, h, l, c, g, fs = md; n = len(c)
    dh, st = E.richtung_stunden(c), E.struktur(*E.tf_kerzen(h, l, c, 12 * tf), k)
    for name, art in (("V1", E.V1), ("V2", E.V2)):
        log = []
        G.sim(md + (1.0,), name, tf, k, n, log=log)
        ein = [x for x in log if x[0] == "einstieg"]
        assert any(x[3] != x[4] for x in ein) and any(x[3] == x[4] for x in ein)    # Zwischenniveau und Ersatz-Stop kommen beide vor
        geprueft = 0
        for _, je, soll, stop, lv, cj, _ in ein[:60]:
            p = je + 1                                            # Einstiegskerze: ihr Schluss ist die erste Stop-Prüfung
            if p + 2 >= n or p % 12 == 0:
                continue
            alt, feuert = (c[p], h[p], l[p]), []
            for kurs in (stop, np.nextafter(stop, np.inf if soll < 0 else -np.inf)):
                c[p], h[p], l[p] = kurs, max(alt[1], kurs), min(alt[2], kurs)
                od = np.zeros((6000, 4)); nt = n // E.TAG + 1
                no = E.lauf(o, h, l, c, g, fs, 1.0, dh, 12 * tf, k, *st, art, p + 2, np.zeros((2, nt)), np.zeros((2, nt)), np.zeros((2, nt)),
                            np.zeros(nt), np.zeros(7), od)
                feuert.append(bool(no and od[no - 1, 0] == p + 1 and od[no - 1, 2] == 3))
            c[p], h[p], l[p] = alt
            assert feuert == [False, True]
            geprueft += 1
        assert geprueft > 10


def test_zeitraeume_kosten_und_kennzahlen():
    t0 = np.datetime64("2021-07-01")
    for zr, (a, b, n) in {"T": ("2021-08-15", "2023-06-30", 685), "V1": ("2023-07-01", "2024-06-30", 366), "V2": ("2024-07-01", "2025-03-31", 274)}.items():
        sl = E.tage(zr)
        assert t0 + np.timedelta64(sl.start, "D") == np.datetime64(a) and t0 + np.timedelta64(sl.stop - 1, "D") == np.datetime64(b) and sl.stop - sl.start == n
    assert E.ENDE_V1 == E.tage("V2").start * E.TAG and E.D.N == 1370 * E.TAG
    rng = np.random.default_rng(2)
    nt = E.D.N // E.TAG
    r = {"brut": rng.normal(0, 0.01, (10, 2, nt)), "nord": rng.integers(0, 3, (10, 2, nt)).astype(float), "slipb": rng.uniform(1, 9, (10, 2, nt)),
         "markt": rng.integers(0, 289, (10, nt)).astype(float), "slip_coin": rng.uniform(0.5, 13, 10)}
    assert np.allclose(E.netto(r), r["brut"] - (r["slipb"] + r["nord"] * 1.2) / 1e4)
    assert np.allclose(E.netto(r, rebate=False), r["brut"] - (r["slipb"] + r["nord"] * 8.0) / 1e4)
    assert np.allclose(E.netto(r, bewegt=False), r["brut"] - (r["nord"] * r["slip_coin"][:, None, None] + r["nord"] * 1.2) / 1e4)
    k, konto = E.kennzahlen(r, "V1")
    sl = E.tage("V1")
    erwartet = E.netto(r)[:, :, sl].sum(1).mean(0)
    assert np.allclose(konto, erwartet) and k["sharpe"] == round(float(erwartet.mean() / erwartet.std(ddof=1) * np.sqrt(365)), 3)
    assert k["summe_pct"] == round(float(erwartet.sum() * 100), 2) and k["long_pct"] + k["short_pct"] == pytest.approx(k["summe_pct"], abs=0.02)
    assert sum(k["je_jahr_pct"].values()) == pytest.approx(k["summe_pct"], abs=0.02) and set(k["je_jahr_pct"]) == {"2023", "2024"}
    assert E.einbruch(np.array([0.1, -0.2, -0.1, 0.4, -0.05])) == pytest.approx(0.3) and E.sharpe(np.zeros(5)) == 0.0


def test_stichprobe_wie_einfache_schleife_und_urteil_auf_ungerundeten_werten():
    rng = np.random.default_rng(7)
    a, b = rng.normal(0.0008, 0.012, 300), rng.normal(0.0002, 0.011, 300)
    g, ohne = np.random.default_rng(23), 0
    for _ in range(400):                                          # Präzisierungen 10 und 14, als einfache Schleife
        tage_ = []
        for s0 in g.integers(0, 300, 15):
            tage_ += [(int(s0) + q) % 300 for q in range(20)]
        tage_ = tage_[:300]
        ohne += not (E.sharpe(a[tage_]) > E.sharpe(b[tage_]))
    assert E.stichprobe(a, b, zuege=400) == ohne / 400 and E.stichprobe(b, a, zuege=400) == pytest.approx(1 - ohne / 400, abs=0.01)

    basis = {"T": rng.normal(0.0003, 0.01, 685), "V1": rng.normal(0.0003, 0.01, 366)}
    reihen = {("B0", zr): x for zr, x in basis.items()}
    for ken in [f"{v}_{tf}h_k{k}" for v in ("V1", "V2", "V3") for tf, k in E.EINSTELLUNGEN]:
        for zr in ("T", "V1"):
            reihen[(ken, zr)] = basis[zr] * 0.5 - 0.001           # klar schlechter als die Basis
    for zr in ("T", "V1"):
        reihen[("V1_1h_k3", zr)] = basis[zr] + 0.004              # klar besser, aber ohne besseren Nachbarn
        reihen[("V2_1h_k3", zr)] = basis[zr] + 0.004              # klar besser, mit Nachbar knapp über der Basis
        reihen[("V2_1h_k5", zr)] = basis[zr] + 5e-8               # Vorteil weit unter der Rundung des Berichts
    u = E.urteil(reihen)
    assert u["V1_1h_k3"]["urteil"] == {"1_T": True, "2_V1": True, "3_netto_positiv": True, "4_nachbar": False, "besteht_T_und_V1": False}
    assert u["V2_1h_k3"]["urteil"]["besteht_T_und_V1"] and u["V2_1h_k3"]["urteil"]["4_nachbar"]
    assert u["V3_4h_k5"]["urteil"] == {"1_T": False, "2_V1": False, "3_netto_positiv": False, "4_nachbar": False, "besteht_T_und_V1": False}
    assert u["V2_1h_k5"]["T"]["differenz"] > 0 and round(u["V2_1h_k5"]["T"]["differenz"], 3) == 0
    reihen[("V1_4h_k3", "T")] = np.full(685, np.nan)
    with pytest.raises(SystemExit):
        E.urteil(reihen)


def test_schlusspruefung_nur_einmal_und_nur_fuer_die_besteher(tmp_path, monkeypatch):
    import json
    monkeypatch.setattr(E, "ERGEBNIS", tmp_path / "e23.json")
    nt = E.D.N // E.TAG
    rng = np.random.default_rng(3)

    def falsch_rechne(i_ende, nur=None, mit_orders=0):
        assert i_ende == E.D.N and nur == {"B0", "V2_1h_k3"}
        mach = lambda plus: {"brut": rng.normal(plus, 0.01, (10, 2, nt)), "nord": np.zeros((10, 2, nt)), "slipb": np.zeros((10, 2, nt)),
                             "markt": np.zeros((10, nt)), "slip_coin": np.ones(10), "zahl": np.zeros((10, 7))}
        return {"B0": mach(0.0), "V2_1h_k3": mach(0.002)}
    monkeypatch.setattr(E, "rechne", falsch_rechne)
    E.ERGEBNIS.write_text(json.dumps({"besteher_T_und_V1": ["V2_1h_k3"], "einstufung": "offen"}))
    for falsch in ([], ["V1_1h_k3"], ["V2_1h_k3", "V3_1h_k3"]):
        with pytest.raises(SystemExit):
            E.schlusspruefung(falsch)
    assert "V2" not in json.loads(E.ERGEBNIS.read_text())
    aus = E.schlusspruefung(["V2_1h_k3"])
    assert aus["V2"]["V2_1h_k3"]["besteht"] and aus["einstufung"].startswith("C") and "V2" in json.loads(E.ERGEBNIS.read_text())
    with pytest.raises(SystemExit):
        E.schlusspruefung(["V2_1h_k3"])                           # zweites Öffnen verweigert
    with pytest.raises(SystemExit):
        E.hauptlauf()                                             # und der Hauptlauf überschreibt das Ergebnis nicht mehr
