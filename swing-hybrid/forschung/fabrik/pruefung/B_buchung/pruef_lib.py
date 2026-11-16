"""Gemeinsame Hilfen der Prüfung B: eigener Nachbau eines Kandidaten (Trades, Tagesfelder, Kennzahlen) nur aus Kerzen < I_ENDE."""
import json, sys
import numpy as np
sys.path.insert(0, 'forschung'); sys.path.insert(0, 'forschung/fabrik/pruefung/B_buchung')
from fabrik import daten as D, lauf as L, generator as G, signale as S
import eigen as E

L._init()
I_ENDE = L.I_ENDE
o, h, l, c = (np.asarray(D.laden(x)[:, :I_ENDE]) for x in ("o", "h", "l", "c"))
fc = np.asarray(D.laden("fcum")[:, :I_ENDE])
frate = np.diff(fc, axis=1, prepend=0.0)
sigma = np.asarray(D.laden("sigma")[:, :I_ENDE])
gueltig = np.asarray(D.laden("gueltig")[:, :I_ENDE])
slip_bp = np.asarray(D.laden("slip_bp"))
AUSSTIEGE = dict(G.AUSSTIEGE)
try:
    AUSSTIEGE.update({k: tuple(v) for k, v in json.load(open('forschung/fabrik/ergebnisse/ausstiege.json')).items()})
except FileNotFoundError:
    pass
TAG_VON = int(np.searchsorted(D.RASTER.values, np.datetime64('2021-08-15')))
N_TAGE = (I_ENDE - TAG_VON) // 288
OHNE_BTC = ('btcfuehrt', 'relstaerke', 'korrbruch')
TIEFE = {s[0] for s in S.SIGNALE if s[3] == 't'}


def aufgabe(z):
    a = {"si": S.NAMEN.index(z['signal']), "signal": z['signal'], "familie": z['familie'], "braucht": z['braucht'], "th": z['th'], "r": z['r'], "f": z['f'], "k": z['k']}
    if z.get('best'):
        b = json.loads(z['best'])
        a["best"] = {"si": S.NAMEN.index(b[0]), "signal": b[0], "th": b[1], "r": b[2], "braucht": S.SIGNALE[S.NAMEN.index(b[0])][3]}
    return a


def segment(z):
    tief = z['signal'] in TIEFE or (z.get('best') and json.loads(z['best'])[0] in TIEFE)
    T0 = np.datetime64('2023-01-01') if tief else np.datetime64('2021-08-15')
    V0 = np.datetime64('2024-01-01') if tief else np.datetime64('2023-07-01')
    i_t0, i_v0 = int(np.searchsorted(D.RASTER.values, T0)), int(np.searchsorted(D.RASTER.values, V0))
    return i_t0, i_v0, (i_t0 - TAG_VON) // 288, (i_v0 - TAG_VON) // 288


def markt(z):
    m = list(G.MAERKTE[z['m']])
    if z['signal'].startswith(OHNE_BTC):
        m = [x for x in m if x != 0]
    return m


def nachbau(z, verzug=0, mit_trades=False, sx_doppelt=True):
    a = aufgabe(z)
    halte, sl, tp, tr, ta, sx = AUSSTIEGE[z['x']]
    i_t0, i_v0, d_t0, d_v0 = segment(z)
    M = markt(z)
    roh_tag, n_tag, alle = np.zeros((len(M), N_TAGE)), np.zeros((len(M), N_TAGE)), []
    for q, j in enumerate(M):
        ein, wert = L.einstieg(a, j)
        t = E.trades(o[j], h[j], l[j], frate[j], ein, wert, sigma[j], i_t0, I_ENDE, halte, sl, tp, tr, ta, sx, verzug, sx_doppelt)
        roh_tag[q], n_tag[q], roh = E.tagesfelder(t, 2 * slip_bp[j], TAG_VON, N_TAGE)
        if mit_trades:
            alle += [(j, *x, r) for x, r in zip(t, roh)]
    slip_rt = 2 * slip_bp[M]
    mitte = (d_t0 + d_v0) // 2
    K = {n: E.kennzahlen(roh_tag, n_tag, slip_rt, x, y) for n, (x, y) in (("T", (d_t0, d_v0)), ("H1", (d_t0, mitte)), ("H2", (mitte, d_v0)), ("V", (d_v0, N_TAGE)))}
    p85 = (roh_tag.sum(0) - 2.4 * n_tag.sum(0)) / len(M)
    T, H1, H2 = K["T"], K["H1"], K["H2"]
    if T["n"] < 200: st = "ungültig"
    elif not (T["roh"] > 0 and T["t_roh"] >= 2): st = "verworfen_1"
    elif not (T["n85"] > 0 and T["t85"] >= 2 and H1["n85"] > 0 and H2["n85"] > 0 and T["n85_2x"] > 0): st = "verworfen_2"
    else: st = "stufe2"
    return dict(p85=p85, K=K, status=st, M=M, roh_tag=roh_tag, n_tag=n_tag, trades=alle, seg=(i_t0, i_v0, d_t0, d_v0))


def vergleich(z, r):
    T, H1, H2, V = (r["K"][k] for k in ("T", "H1", "H2", "V"))
    paare = [("n_t", T["n"]), ("roh_t", T["roh"]), ("n85_t", T["n85"]), ("t_roh_t", T["t_roh"]), ("t85_t", T["t85"]), ("n85_h1", H1["n85"]), ("n85_h2", H2["n85"]),
             ("n85_2x_t", T["n85_2x"]), ("n_v", V["n"]), ("roh_v", V["roh"]), ("n85_v", V["n85"]), ("t85_v", V["t85"])]
    return {k: (float(v), z[k]) for k, v in paare if abs(v - z[k]) > 0.01}
