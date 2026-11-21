"""Tests zu E24 aus der unabhängigen Gegenprüfung (21.11.2026): Vergleich aller Bausteine mit einer einfachen zweiten
Rechnung, Zeitversatz des Bitcoin-Signals gegen die US-Eröffnung, Datenzuschnitt, Hürden."""
import json, sys
from pathlib import Path
import numpy as np, pandas as pd, pytest
ROOT = str(Path(__file__).resolve().parents[1])
sys.path.insert(0, ROOT + '/forschung'); sys.path.insert(0, str(Path(__file__).parent))
pytest.importorskip("numba")
from experimente import e23_marktstruktur as E
from experimente import e24_einstieg_und_pool as X
import e24_referenz as N

REGELN = ['B0'] + [k for k, _, _ in X.kandidaten_a()] + [f'z_{i}' for i in range(5)] + [f'alter_{i}' for i in range(5)]


def synth(seed, n):
    rng = np.random.default_rng(seed)
    drift = np.repeat(rng.normal(0, 0.00035, n // 2880 + 1), 2880)[:n]             # Abschnitte mit Trend, damit z alle Stufen erreicht
    c = 100 * np.exp(np.cumsum(rng.normal(0, 0.003, n) + drift))
    o = np.concatenate([[100.0], c[:-1]]) * np.exp(rng.normal(0, 0.0003, n))
    h = np.maximum(o, c) * (1 + np.abs(rng.normal(0, 0.0005, n))); l = np.minimum(o, c) * (1 - np.abs(rng.normal(0, 0.0005, n)))
    g = np.ones(n, bool)
    for a in rng.integers(12 * 800, n - 500, 6):
        g[a:a + rng.integers(1, 300)] = False
    last = c[0]
    for j in range(n):
        if g[j]: last = c[j]
        else: o[j] = h[j] = l[j] = c[j] = last
    fs = np.where(np.arange(n) % 96 == 0, rng.normal(0, 1e-4, n), 0.0)
    return [o, h, l, c, g, fs, 1.5]


def rechne(monkeypatch, coins, i_ende, n):
    monkeypatch.setattr(X.D, 'COINS', list(coins)); monkeypatch.setattr(X.D, 'N', n)
    namen = list(coins)
    monkeypatch.setattr(E, 'coin_daten', lambda ci, ie: tuple(x[:ie] if isinstance(x, np.ndarray) else x for x in coins[namen[ci]]))
    return X.rechne_a(i_ende, mit_orders=60000)


N5 = 12 * 24 * 150


def test_alle_17_regeln_gegen_einfachen_nachbau_mit_luecken(monkeypatch):
    coins = {'AAA': synth(11, N5), 'BBB': synth(12, N5)}
    erg, orders = rechne(monkeypatch, coins, N5, N5)
    assert list(erg) == REGELN
    anzahl = {}
    for name, (o, h, l, c, g, fs, slip) in coins.items():
        r, d, z, alt = N.richtungen(c)
        assert np.allclose(X.ausdehnung(c), z, rtol=1e-9, equal_nan=True) and np.array_equal(np.isnan(X.ausdehnung(c)), np.isnan(z))
        for ken in REGELN:
            soll = N.orders_naiv(o, g, r[ken], N5)
            anzahl[ken] = anzahl.get(ken, 0) + len(soll)
            assert np.array_equal(orders[ken][name], soll), ken
    print('SYNTH Orders je Regel', anzahl)
    assert min(anzahl.values()) >= 8
    # Zeit im Markt: die Stufen zerlegen B0 vollstaendig (ab Stunde 721), der Ertrag vor Orderkosten addiert sich NICHT genau
    tag0 = 31
    assert all(np.isfinite(N.z_naiv(x[3])[721:]).all() for x in coins.values())
    for fam in ('z', 'alter'):
        ms = sum(erg[f'{fam}_{i}']['markt'][:, tag0:].sum() for i in range(5))
        assert ms == erg['B0']['markt'][:, tag0:].sum()
    bs = sum(erg[f'z_{i}']['brut'][:, :, tag0:].sum() for i in range(5))
    print('SYNTH Summe brut der z-Stufen', bs, 'gegen B0', erg['B0']['brut'][:, :, tag0:].sum())


@pytest.mark.parametrize('p', [12 * 1000, 12 * 1000 + 1, 12 * 1000 + 11, 12 * 1313 + 5, 288 * 60, 288 * 75 - 1])
def test_kein_blick_in_die_zukunft_alle_regeln(monkeypatch, p):
    coins = {'AAA': synth(21, N5)}
    erg, orders = rechne(monkeypatch, coins, N5, N5)
    rng = np.random.default_rng(p)
    c2 = [x.copy() if isinstance(x, np.ndarray) else x for x in coins['AAA']]
    f = np.exp(np.cumsum(rng.normal(0.0005, 0.01, N5 - p)))
    for i in range(4): c2[i][p:] = c2[i][p:] * f * 1.2
    c2[5][p:] = c2[5][p:] * -3 + 1e-4
    erg2, orders2 = rechne(monkeypatch, {'AAA': c2}, N5, N5)
    erg3, orders3 = rechne(monkeypatch, coins, p, N5)                 # nur bis p geladen
    aenderung = 0
    for ken in REGELN:
        a, b, k3 = orders[ken]['AAA'], orders2[ken]['AAA'], orders3[ken]['AAA']
        assert np.array_equal(a[a[:, 0] < p], b[b[:, 0] < p]), ken
        assert np.array_equal(a[a[:, 0] == p][:, :3], b[b[:, 0] == p][:, :3]), ken
        assert np.array_equal(a[a[:, 0] < p], k3), ken
        tg = p // 288
        for feld in ('brut', 'nord', 'slipb'):
            assert np.array_equal(erg[ken][feld][:, :, :tg], erg2[ken][feld][:, :, :tg]), (ken, feld)
            assert np.array_equal(erg[ken][feld][:, :, :tg], erg3[ken][feld][:, :, :tg]), (ken, feld)
        assert np.array_equal(erg[ken]['markt'][:, :tg], erg2[ken]['markt'][:, :tg])
        aenderung += not np.array_equal(a[a[:, 0] > p][:, :3], b[b[:, 0] > p][:, :3])
    assert aenderung >= 10                                           # die Stoerung wirkt danach wirklich


def test_min_filter_im_kern_und_richtung_bei_unbestimmtem_z():
    d = np.array([1, -1, 1, -1], np.int8); z = np.array([np.nan, np.inf, 1.0, 0.25])
    assert X.richtung_gefiltert(d, z, 'max', 1.0).tolist() == [0, 0, 1, -1]
    assert X.richtung_gefiltert(d, z, 'min', 1.0).tolist() == [0, -1, 1, 0]
    assert X.richtung_gefiltert(d, z, 'min', 0.25).tolist() == [0, -1, 1, -1]


# ------------------------------------------------------------------------------------------------ Teil C
def speicher(seed, n=320000):
    rng = np.random.default_rng(seed)
    c = np.empty((10, n)); c[:] = 100 * np.exp(np.cumsum(rng.normal(0, 0.002, n)))
    return c


def boersentage(a='2020-01-02', b='2024-06-28', seed=0):
    idx = pd.bdate_range(a, b)
    rng = np.random.default_rng(seed)
    weg = set(rng.choice(len(idx), 45, replace=False).tolist())      # Feiertage, auch montags und freitags
    return idx[[i for i in range(len(idx)) if i not in weg]]


def tageskurse(idx, seed):
    rng = np.random.default_rng(seed); n = len(idx)
    c = 100 * np.exp(np.cumsum(rng.normal(0.0002, 0.015, n)))
    return pd.DataFrame({'open': np.concatenate([[100.0], c[:-1]]) * (1 + rng.normal(0, 0.004, n)), 'close': c}, index=idx.astype('datetime64[us]'))


def test_btc_signal_tagesschluss_schnitt_und_stoerung(monkeypatch):
    c = speicher(1)
    monkeypatch.setattr(X.D, 'laden', lambda name: c)
    s = X.btc_signal()
    assert len(s) == 1096 and s.index[0] == pd.Timestamp('2021-07-01') and s.index[-1] == pd.Timestamp('2024-06-30')
    assert s.equals(N.btc_sig_naiv(c[0], s.index))
    c2 = c.copy(); c2[:, 315648:] = -7.0                              # nach dem Schnitt Unsinn
    monkeypatch.setattr(X.D, 'laden', lambda name: c2)
    assert s.equals(X.btc_signal())
    kurz = X.btc_signal(pd.Timestamp('2023-01-10'))
    assert kurz.index[-1] == pd.Timestamp('2023-01-10') and kurz.equals(s.iloc[:len(kurz)])
    k = 500                                                          # Tag D mit Index 500
    for kerze, erwartet in ((288 * k - 1, {k, k + 14}), (288 * k - 2, set()), (288 * k, set()), (288 * k + 287, {k + 1, k + 15})):
        c3 = c.copy(); c3[0, kerze] = 1e9
        monkeypatch.setattr(X.D, 'laden', lambda name: c3)
        s3 = X.btc_signal()
        anders = set(np.nonzero((s3 != s).to_numpy())[0].tolist())
        assert anders <= erwartet and (not erwartet or anders), (kerze, anders)
    c4 = c.copy(); c4[0, 288 * k:] *= np.exp(np.cumsum(np.random.default_rng(5).normal(0, 0.01, c.shape[1] - 288 * k)))
    monkeypatch.setattr(X.D, 'laden', lambda name: c4)
    s4 = X.btc_signal()
    assert s4.iloc[:k + 1].equals(s.iloc[:k + 1]) and not s4.iloc[k + 1:].equals(s.iloc[k + 1:])


def qqq(monkeypatch, c, d, art='btc', stress=False):
    monkeypatch.setattr(X.D, 'laden', lambda name: c)
    monkeypatch.setattr(X.pd, 'read_parquet', lambda pfad: d.copy())
    return X.baustein_qqq(art, stress=stress)


def test_qqq_nach_btc_gegen_nachbau_wochenende_feiertag_und_stoerung(monkeypatch):
    c = speicher(2); idx = boersentage(); d = tageskurse(idx, 3)
    slip = max(0.00005, json.loads(open(ROOT + '/reports/runde14_kosten.json').read())['QQQ']['spanne_bp'] / 1e4)
    sig = N.btc_sig_naiv(c[0], X.KAL)
    for stress in (False, True):
        f = 2.0 if stress else 1.0
        ref = N.tagesrechnung(d, X.KAL, 1.0, f * slip, f * 0.0008, 0.10 if stress else 0.0, sig=sig)
        got = qqq(monkeypatch, c, d, 'btc', stress)
        assert np.allclose(got.to_numpy(), ref.to_numpy(), atol=1e-13) and np.abs(ref).sum() > 1
        ref = N.tagesrechnung(d, X.KAL, 1.0, f * slip, f * 0.0008, 0.10 if stress else 0.0)
        assert np.allclose(qqq(monkeypatch, c, d, 'eigen', stress).to_numpy(), ref.to_numpy(), atol=1e-13)
        ref = N.tagesrechnung(d, X.KAL, 1.0, f * slip, f * 0.0008, 0.10 if stress else 0.0, sig=pd.Series(1.0, index=X.KAL))
        assert np.allclose(qqq(monkeypatch, c, d, 'halten', stress).to_numpy(), ref.to_numpy(), atol=1e-13)
    basis = qqq(monkeypatch, c, d)
    t0 = pd.Timestamp('2021-07-01')
    tage = set(idx)
    montage = [x for x in X.KAL[40:-40] if x in tage and x.dayofweek == 0 and (x - pd.Timedelta(days=3)) in tage]
    nach_feiertag = [x for x in X.KAL[40:-40] if x in tage and x.dayofweek in (2, 3) and (x - pd.Timedelta(days=1)) not in tage]
    mitte = [x for x in X.KAL[40:-40] if x in tage and x.dayofweek == 2 and (x - pd.Timedelta(days=1)) in tage]
    assert len(nach_feiertag) >= 3

    def kippen(tag_utc):                                             # Schluss des UTC-Tages so setzen, dass das Signal des Folgetags kippt
        k = (tag_utc - t0).days + 1
        c2 = c.copy(); alt = c[0, 288 * (k - 14) - 1]
        c2[0, 288 * k - 1] = alt * (0.5 if c[0, 288 * k - 1] > alt else 2.0)
        return c2

    for D_ in montage[:6] + nach_feiertag[:3] + mitte[:6]:
        neu = qqq(monkeypatch, kippen(D_ - pd.Timedelta(days=1)), d)   # BTC-Schluss des Vortags (Sonntag bzw. Feiertag) gekippt
        assert np.array_equal(neu[:D_ - pd.Timedelta(days=1)].to_numpy(), basis[:D_ - pd.Timedelta(days=1)].to_numpy())
        assert neu[D_] != basis[D_], D_                              # wirkt am Boersentag D selbst (kein zusaetzlicher Tag Verzug)
        neu = qqq(monkeypatch, kippen(D_), d)                        # BTC-Schluss des Tages D selbst gekippt
        assert np.array_equal(neu[:D_].to_numpy(), basis[:D_].to_numpy()), D_   # Tag D bleibt unberuehrt (kein Blick voraus)
    for D_ in montage[:6]:                                           # Freitag- und Samstag-Schluss gehen nur in Signale fuer Sa/So ein und in D+14
        for zurueck in (2, 3):
            neu = qqq(monkeypatch, kippen(D_ - pd.Timedelta(days=zurueck)), d)
            assert np.array_equal(neu[:D_ + pd.Timedelta(days=9)].to_numpy(), basis[:D_ + pd.Timedelta(days=9)].to_numpy())
    D_ = mitte[10]; k = (D_ - t0).days
    c2 = c.copy(); c2[:, 288 * k:] *= np.exp(np.cumsum(np.random.default_rng(8).normal(0, 0.01, c.shape[1] - 288 * k)))
    d2 = d.copy(); d2.loc[d2.index > D_, ['open', 'close']] *= 1.7; d2.loc[D_, 'close'] *= 1.1
    neu = qqq(monkeypatch, c2, d2)
    assert np.array_equal(neu[:D_ - pd.Timedelta(days=1)].to_numpy(), basis[:D_ - pd.Timedelta(days=1)].to_numpy())
    d3 = d.copy(); d3 = pd.concat([d3, tageskurse(pd.bdate_range('2024-07-01', '2024-12-31'), 99) * 50])   # Zeilen nach dem Schnitt
    c3 = c.copy(); c3[:, 315648:] *= 9
    assert np.array_equal(qqq(monkeypatch, c3, d3).to_numpy(), basis.to_numpy())
    for art in ('eigen', 'halten'):
        assert np.array_equal(qqq(monkeypatch, c3, d3, art).to_numpy(), qqq(monkeypatch, c, d, art).to_numpy())


# ------------------------------------------------------------------------------------------------ Teil B
def test_tagestrend_gegen_nachbau_und_ohne_blick_voraus():
    idx = boersentage(seed=4)
    for seed, start in ((1, '2020-01-02'), (2, '2022-03-10'), (3, '2021-08-02')):
        d = tageskurse(idx[idx >= start], seed)
        for stress in (False, True):
            f = 2.0 if stress else 1.0
            t = X.T.lauf_markt(d, X.KAL, 1 / 134, f * 0.0005, f * X.TAKER, 0.10 if stress else 0.0)
            got = t['brutto'] - (1 - X.REBATE) * t['gebuehr'] + t['funding']
            ref = N.tagesrechnung(d, X.KAL, 1 / 134, f * 0.0005, f * 0.0008, 0.10 if stress else 0.0)
            assert np.allclose(got.to_numpy(), ref.to_numpy(), atol=1e-15) and np.abs(ref).sum() > 0.005
        t = X.T.lauf_markt(d, X.KAL, 1 / 134, 0.0005, X.TAKER)
        for D_ in d.index[d.index >= '2022-09-01'][[0, 1, 2, 3, 4, 100]]:
            d2 = d.copy(); d2.loc[d2.index >= D_, 'close'] *= 1.5; d2.loc[d2.index > D_, 'open'] *= 1.5
            t2 = X.T.lauf_markt(d2, X.KAL, 1 / 134, 0.0005, X.TAKER)
            vor = t.index < D_
            assert np.array_equal(t[vor].to_numpy(), t2[vor].to_numpy())
            assert t.loc[D_, 'umsatz'] == t2.loc[D_, 'umsatz'] and t.loc[D_, 'gebuehr'] == t2.loc[D_, 'gebuehr']   # Handel zur Eroeffnung D kennt den Schluss D nicht


def test_aktien_laden_und_baustein(monkeypatch, tmp_path):
    (tmp_path / 'reports').mkdir(); (tmp_path / 'data/candles/aktien_1d').mkdir(parents=True)
    idx = boersentage('2020-01-02', '2024-12-31', seed=6)
    info = {'AAA': {'ok': True, 'spanne_bp': None}, 'BBB': {'ok': True, 'spanne_bp': 0.2}, 'CCC': {'ok': True, 'spanne_bp': 4.0},
            'DDD': {'ok': True, 'spanne_bp': 10.0}, 'EEE': {'ok': False, 'grund': 'x'}, 'NEU': {'ok': True, 'spanne_bp': 30.0},
            'SPAET': {'ok': True, 'spanne_bp': 7.0}}
    start = {'AAA': '2020-01-02', 'BBB': '2020-01-02', 'CCC': '2022-05-05', 'DDD': '2020-01-02', 'NEU': '2024-08-01', 'SPAET': '2024-06-28'}
    for k, a in start.items():
        tageskurse(idx[idx >= a], sum(map(ord, k))).to_parquet(tmp_path / f'data/candles/aktien_1d/{k}.parquet')
    (tmp_path / 'reports/runde17_aktien.json').write_text(json.dumps(info))
    monkeypatch.setattr(X, 'ROOT', tmp_path)
    kurse, slip, inf = X.aktien_laden()
    assert sorted(kurse) == ['AAA', 'BBB', 'CCC', 'DDD', 'NEU', 'SPAET'] and inf['anzahl'] == 6 and inf['ohne_messwert'] == 1
    assert all(d.index.max() <= pd.Timestamp('2024-06-30') for d in kurse.values() if len(d)) and len(kurse['NEU']) == 0 and len(kurse['SPAET']) == 1
    assert slip['AAA'] == pytest.approx(7.0 / 1e4) and slip['BBB'] == pytest.approx(0.00005) and slip['CCC'] == pytest.approx(0.0004)   # Median der gemessenen (0,2 4 7 10 30) = 7
    for stress in (False, True):
        f = 2.0 if stress else 1.0
        ref = sum(N.tagesrechnung(kurse[k], X.KAL, 1 / 6, f * slip[k], f * 0.0008, 0.10 if stress else 0.0) for k in ('AAA', 'BBB', 'CCC', 'DDD'))
        got = X.baustein_aktien(kurse, slip, stress=stress)
        assert np.allclose(got.to_numpy(), ref.to_numpy(), atol=1e-14) and np.abs(ref).sum() > 0.5
    lang = {k: pd.read_parquet(tmp_path / f'data/candles/aktien_1d/{k}.parquet') for k in kurse}   # ungeschnitten uebergeben: der Baustein schneidet selbst
    assert np.array_equal(X.baustein_aktien(lang, slip).to_numpy(), X.baustein_aktien(kurse, slip).to_numpy())


# ------------------------------------------------------------------------------------------- Urteil
def test_baustein_urteil_huerden_einzeln(monkeypatch):
    rng = np.random.default_rng(4); kal = X.KAL
    b0 = {'T': rng.normal(0.0005, 0.03, 685), 'V1': rng.normal(0.0005, 0.03, 366)}
    gut = pd.Series(rng.normal(0.004, 0.01, len(kal)), index=kal)
    u = X.baustein_urteil(gut, gut - 0.01, b0)
    assert u['huerden'] == {'1_netto_positiv': True, '2_stress_positiv': False, '3_mischung_besser': True} and not u['besteht_T_und_V1']
    null = pd.Series(0.0, index=kal)
    u = X.baustein_urteil(null, null, b0)                            # flacher Baustein: Mischung = halbe Basis, Sharpe-Zahl gleich, nicht hoeher
    assert not u['huerden']['3_mischung_besser'] and not u['huerden']['1_netto_positiv']
    assert u['T']['mischung_sharpe'] == u['T']['basis_sharpe'] and E.sharpe(0.5 * b0['T']) == E.sharpe(b0['T'])
    nurT = gut.copy(); nurT[kal >= '2023-07-01'] = -0.001
    u = X.baustein_urteil(nurT, nurT, b0)
    assert u['T']['h1'] and not u['V1']['h1'] and not u['huerden']['1_netto_positiv'] and u['T']['h3'] and not u['huerden']['3_mischung_besser']
    for p, erw in ((0.025, (True, True)), (0.0252, (False, True)), (0.16, (False, True)), (0.1602, (False, False))):
        monkeypatch.setattr(E, 'stichprobe', lambda a, b, p=p: p)
        u = X.baustein_urteil(gut, gut, b0)
        assert (u['T']['h3'], u['V1']['h3']) == erw, p
    monkeypatch.undo()
    mix = 0.5 * b0['V1'] + 0.5 * gut[kal >= '2023-07-01'].to_numpy()
    u = X.baustein_urteil(gut, gut, b0)
    assert u['V1']['mischung_sharpe'] == round(E.sharpe(mix), 3) and u['V1']['anteil_ohne_vorteil'] == round(E.stichprobe(mix, b0['V1']), 4)
    with pytest.raises(SystemExit):
        X.baustein_urteil(gut.iloc[:-1], gut.iloc[:-1], b0)
    kaputt = gut.copy(); kaputt.iloc[5] = np.nan
    with pytest.raises(SystemExit):
        X.baustein_urteil(kaputt, gut, b0)


def test_urteil_a_nur_naechstliegende_schwelle(monkeypatch):
    rng = np.random.default_rng(4)
    b0 = {'T': rng.normal(0.0005, 0.03, 685), 'V1': rng.normal(0.0005, 0.03, 366)}

    def lage(besser, nur_T=()):
        r = {('B0', zr): x for zr, x in b0.items()}
        for ken, _, _ in X.kandidaten_a():
            for zr in ('T', 'V1'):
                r[(ken, zr)] = b0[zr] + (0.006 if (ken in besser or (ken in nur_T and zr == 'T')) else -0.006)
        return X.urteil_a(r)
    u = lage({'A1_z_bis_1.0', 'A1_z_bis_2.0', 'A2_z_ab_0.25', 'A2_z_ab_1.0'})
    for ken in ('A1_z_bis_1.0', 'A1_z_bis_2.0', 'A2_z_ab_0.25', 'A2_z_ab_1.0'):   # der einzige Nachbar ist die mittlere Schwelle, die liegt nicht ueber B0
        assert u[ken]['urteil']['1_T'] and u[ken]['urteil']['2_V1'] and u[ken]['urteil']['3_netto_positiv'] and not u[ken]['urteil']['4_nachbar']
        assert not u[ken]['urteil']['besteht_T_und_V1']
    assert u['A1_z_bis_1.5']['urteil']['4_nachbar'] and u['A2_z_ab_0.5']['urteil']['4_nachbar']       # die mittlere hat beide Nachbarn
    u = lage({'A1_z_bis_1.5', 'A1_z_bis_1.0', 'A2_z_ab_0.25', 'A2_z_ab_0.5', 'A2_z_ab_1.0'}, nur_T={'A1_z_bis_2.0'})
    assert u['A1_z_bis_1.5']['urteil']['besteht_T_und_V1'] and u['A1_z_bis_1.0']['urteil']['besteht_T_und_V1']
    u = lage({'A1_z_bis_2.0'}, nur_T={'A1_z_bis_1.5'})              # Nachbar nur in T ueber B0 reicht nicht
    assert not u['A1_z_bis_2.0']['urteil']['4_nachbar']
    u = lage({'A1_z_bis_2.0', 'A2_z_ab_0.25', 'A2_z_ab_0.5', 'A2_z_ab_1.0'})   # die andere Familie zaehlt nicht als Nachbar
    assert not u['A1_z_bis_2.0']['urteil']['4_nachbar']
