import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from hybrid import statarb as S


def paar_daten(T=3000, seed=0, theta=0.05, sigma_s=0.004, mit_dritt=True):
    """Zwei Coins mit gemeinsamem Trend und einem Spread, der zum Mittel zurückkehrt (Ornstein-Uhlenbeck)."""
    rng = np.random.default_rng(seed)
    gemeinsam = np.cumsum(rng.normal(0, 0.008, T))
    s = np.zeros(T)
    for t in range(1, T):
        s[t] = s[t - 1] * (1 - theta) + rng.normal(0, sigma_s)
    a = 100 * np.exp(gemeinsam + s)
    b = 50 * np.exp(gemeinsam)
    spalten = [a, b]
    if mit_dritt:
        spalten.append(20 * np.exp(np.cumsum(rng.normal(0, 0.01, T))))       # unabhängiger dritter Coin
    c = np.column_stack(spalten)
    o = np.vstack([c[:1], c[:-1]])
    return o, c


def lauf(o, c, kosten=0.0, **kw):
    T, N = c.shape
    p = dict(W=200, z_ein=2.0, z_aus=0.5, z_stop=4.0, rho_min=0.7, max_halten=100, K=2, coin_max=3, filter_swing=False,
             sw=np.zeros((T, N)), fund=np.zeros((T, N)))
    p.update(kw)
    return S.simulate(o, c, p["fund"], p["sw"], p["W"], p["z_ein"], p["z_aus"], p["z_stop"], p["rho_min"], p["max_halten"],
                      p["K"], p["coin_max"], np.full(N, kosten), p["filter_swing"])


def test_verdient_an_rueckkehr_zum_mittel_und_ignoriert_unkorrelierte():
    o, c = paar_daten()
    kurs, kost, fu, einsatz, vol, tr, pi, pj = lauf(o, c)
    assert kurs[-1] > 0.02 and len(tr) > 10
    assert set(tr[:, 0].astype(int)) == {0}                 # nur das Paar (0, 1); Coin 2 ist unkorreliert
    assert einsatz.max() <= 0.5 * 1.3                       # ein Paar = die Hälfte des Topfes (K = 2), plus Kursdrift


def test_richtung_teurer_coin_short():
    o, c = paar_daten(seed=1)
    kurs, kost, fu, einsatz, vol, tr, pi, pj = lauf(o, c)
    assert (tr[:, 6] > 0.5).all() and (tr[:, 6] < 2.0).all()            # beta im erlaubten Bereich
    ziel = tr[tr[:, 4] == 1]
    assert len(ziel) > 5 and (ziel[:, 3] > 0).mean() > 0.8              # Ausstiege am Ziel sind fast immer Gewinne


def test_kosten_und_funding_wirken():
    o, c = paar_daten(seed=2)
    ohne = lauf(o, c)
    mit = lauf(o, c, kosten=0.001)
    assert mit[1][-1] > 0 and np.allclose(ohne[0], mit[0])               # Kosten getrennt geführt, Kursgewinn gleich
    assert mit[1][-1] == pytest.approx(0.001 * mit[4][-1])               # Kosten = Satz x Umsatz
    f = lauf(o, c, fund=np.full(c.shape, 0.0001))
    assert abs(f[2][-1]) < 0.02                                          # Long und Short heben sich beim Funding weitgehend auf


def test_kein_blick_in_die_zukunft():
    o, c = paar_daten(seed=3)
    a = lauf(o, c)
    c2, o2 = c.copy(), o.copy()
    c2[2000:] *= 1.5; o2[2001:] *= 1.5
    b = lauf(o2, c2)
    assert np.allclose(a[0][:2000], b[0][:2000]) and np.allclose(a[4][:2000], b[4][:2000])


def test_swing_filter_blockiert_gegenlaeufige_seiten():
    o, c = paar_daten(seed=4)
    T, N = c.shape
    sw = np.zeros((T, N)); sw[:, 0] = 1.0                    # Swing: Coin 0 nur long erlaubt
    kurs, kost, fu, einsatz, vol, tr, pi, pj = lauf(o, c, sw=sw, filter_swing=True)
    assert len(tr) > 0 and (tr[:, 5] < 0).all()              # nur Einstiege mit Z < 0 (Coin 0 billig, also long)
    frei = lauf(o, c)
    assert len(tr) < len(frei[5])


def test_obergrenzen():
    rng = np.random.default_rng(5)
    T = 2500
    gemeinsam = np.cumsum(rng.normal(0, 0.008, T))
    c = np.column_stack([100 * np.exp(gemeinsam + rng.normal(0, 0.002, T)) for _ in range(6)])   # 6 eng korrelierte Coins
    o = np.vstack([c[:1], c[:-1]])
    kurs, kost, fu, einsatz, vol, tr, pi, pj = lauf(o, c, K=4, coin_max=2, z_ein=1.5)
    assert einsatz.max() <= 1.0 * 1.2                        # nie mehr als der Topf (plus Kursdrift)
    assert len(tr) > 20
    # nie mehr als 4 Paare gleichzeitig und kein Coin in mehr als 2 Paaren
    ereignisse = sorted([(int(x[1]), 1, int(x[0])) for x in tr] + [(int(x[2]), 0, int(x[0])) for x in tr])
    offen, je_coin, maxi, maxc = set(), np.zeros(6, int), 0, 0
    for t, art, p in ereignisse:                             # Schließen (0) vor Öffnen (1) in derselben Kerze
        i, j = int(pi[p]), int(pj[p])
        if art == 0:
            offen.discard(p); je_coin[i] -= 1; je_coin[j] -= 1
        else:
            offen.add(p); je_coin[i] += 1; je_coin[j] += 1
        maxi, maxc = max(maxi, len(offen)), max(maxc, je_coin.max())
    assert maxi <= 4 and maxc <= 2
