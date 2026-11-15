"""Gemeinsame Bausteine der Risiko-Prüfung (RSK). Nur lesend auf Daten und Module; schreibt nichts ins Repo.

Aufruf der Skripte (aus swing-hybrid/, in dieser Reihenfolge; s01 legt Zwischenspeicher an, die s03, s04, s06, s07 lesen):
    export RSK_SCRATCH=/tmp/rsk_audit NUMBA_CACHE_DIR=/tmp/rsk_audit/numba
    for s in s01_laeufe s02_konto s03_gleichzeitig s04_korrelation s05_test2 s06_funding s07_liquidation s08_repro_hebel s09_gegenprobe; do
        .venv/bin/python -I -B reports/audit/evidence/RSK/$s.py > /tmp/rsk_audit/$s.txt; done
Zwischenspeicher (rund 400 MB) landen in RSK_SCRATCH (Standard: Temp-Verzeichnis), nie im Repo.
"""
import os
import sys
import tempfile
from pathlib import Path

ROOT = Path("/home/user/OdinGate-Botv134/swing-hybrid")
if not ROOT.exists():                                    # anderer Ablageort: relativ zu dieser Datei (reports/audit/evidence/RSK)
    ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "src"))
os.environ.setdefault("NUMBA_CACHE_DIR", str(Path(tempfile.gettempdir()) / "rsk_audit" / "numba"))

import numpy as np
import pandas as pd
from hybrid import mutationen as M, research as R, runner

SCRATCH = Path(os.environ.get("RSK_SCRATCH", str(Path(tempfile.gettempdir()) / "rsk_audit")))
SCRATCH.mkdir(parents=True, exist_ok=True)
A = list(R.GRUPPE_A)


def kandidat(m, hebel=1.0):
    """Kandidat genau wie in scripts/suche_runde21.py / suche_runde24.py (Funktion `tage`), nur mit wählbarem Hebel:
    sofortige Ausführung (Taker), Yubit-Slippage je Coin, kein Tagesverlust-Limit (day_limit=9.0 = 900 % des Kapitals)."""
    w = R.auf_raster(m, M.basis(m))
    l = R.lauf(m, w, hebel=hebel, taker=True, slip=R.yubit_kosten(m.coins)[0], day_limit=9.0)
    return l, w


def maerkte():
    """Vorperiode 02/2020-08/2021 und Hauptzeitraum 08/2021-10/2026 (Entwicklung + Prüfzeitraum), Gruppe A."""
    mv = R.markt(A, start=R.VOR_START, ende=R.VOR_ENDE, vor=True)
    mh = R.markt(A, vor=True)
    return mv, mh


from numba import njit


@njit
def _nachbau_coin(o, c, fr, wj, S, sl):
    T = len(c)
    pos = np.zeros(T); brutto = np.zeros(T); tv = np.zeros(T); fu = np.zeros(T)
    q = 0.0; cash = 0.0; vol = 0.0; f = 0.0; held = 0.0
    for t in range(T):
        ende = t == T - 1
        tgt = 0.0 if ende else wj[t]
        if ende and q != 0.0:                       # Schlussabrechnung zum Open, vor dem Funding (wie im Kern)
            d = 1.0 if q > 0 else -1.0
            px = o[t] * (1.0 - d * sl)
            cash += q * px; vol += abs(q) * px; q = 0.0; held = 0.0
        # Funding wird im Kern VOR dem Fill mit der bis dahin gehaltenen Position gebucht
        if fr[t] != 0.0 and q != 0.0:
            f -= q * o[t] * fr[t]
        if (not ende) and t > 0 and abs(tgt - held) > 1e-9:
            if held == 0.0:
                dq = tgt * S / o[t]
            elif tgt * held < 0.0:
                dq = -q + tgt * S / o[t]
            else:
                dq = -q * (1.0 - tgt / held)
            sq = 1.0 if dq > 0 else -1.0
            px = o[t] * (1.0 + sq * sl)
            cash -= dq * px; vol += abs(dq) * px; q += dq; held = tgt
            if abs(q) < 1e-15:
                q = 0.0
        pos[t] = q; brutto[t] = cash + q * c[t]; tv[t] = vol; fu[t] = f
    return pos, brutto, tv, fu


def nachbau(m, w, S, slip):
    """Unabhängiger Nachbau der Positionsführung des Rechenkerns im Taker-Modus, je Coin auf dem 5-Minuten-Raster.

    Regeln (aus engine2.simulate_target abgelesen): Zielgewicht gilt ab dem Open der Kerze t (t >= 1); bei Abweichung
    wird zum Open gefüllt, Stückzahl = Ziel * S / Open, Preis = Open * (1 +- slip). Letzte Kerze: alles schließen.
    Gibt je Coin (pos Stückzahl nach Kerze t, brutto kumulierter Gewinn vor Gebühren, tv kumuliertes Volumen,
    fu kumuliertes Funding) als Felder [N, T] zurück.
    """
    N, T = m.c.shape
    pos = np.zeros((N, T)); brutto = np.zeros((N, T)); tv = np.zeros((N, T)); fu = np.zeros((N, T))
    for j in range(N):
        pos[j], brutto[j], tv[j], fu[j] = _nachbau_coin(m.o[j], m.c[j], m.fund[j], np.ascontiguousarray(w[j], dtype=np.float64), S, float(slip[j]))
    return pos, brutto, tv, fu


def dd_stat(konto: np.ndarray, index: pd.DatetimeIndex) -> dict:
    """Größter Einbruch (relativ zum Höchststand und in Punkten des Startkapitals) und längste Zeit unter dem Höchststand.
    `konto` = Kontostand in Einheiten des Startkapitals (Start = 1)."""
    spitze = np.maximum.accumulate(np.maximum(konto, konto[0]))
    rel = (spitze - konto) / spitze
    absd = spitze - konto
    i = int(np.argmax(rel))
    # längste Phase unter dem Höchststand
    unter = konto < spitze - 1e-12
    laengste, start, best = 0, None, (None, None)
    for t in range(len(unter)):
        if unter[t]:
            if start is None:
                start = t
        elif start is not None:
            if t - start > laengste:
                laengste, best = t - start, (start, t)
            start = None
    offen = False
    if start is not None and len(unter) - start > laengste:
        laengste, best, offen = len(unter) - start, (start, len(unter) - 1), True
    ip = int(np.argmax(spitze[: i + 1] >= spitze[i] - 1e-15))
    return {"dd_rel": float(rel[i]), "dd_rel_tief": str(index[i]), "dd_rel_spitze": str(index[ip]),
            "dd_abs": float(absd.max()), "dd_abs_tief": str(index[int(np.argmax(absd))]),
            "unter_wasser_tage": laengste / 288.0, "unter_wasser_von": str(index[best[0]]) if best[0] is not None else None,
            "unter_wasser_bis": str(index[best[1]]) if best[1] is not None else None, "unter_wasser_offen_am_ende": offen}


def frisch(m, w, a, b, slip, fee):
    """Kontoverlauf (Hebel 1, Einheiten des Startkapitals) bei frischem Start an Kerze a bis Kerze b (exklusiv):
    alle Positionen werden neu in Standardgröße eröffnet, wie beim Start eines Papier-Tests. Gibt (eq, brutto_exposure) zurück,
    brutto_exposure = Summe |Stückzahl| x Schlusskurs in Einheiten des Startkapitals."""
    N = m.c.shape[0]
    eq = np.zeros(b - a); ex = np.zeros(b - a)
    for j in range(N):
        pos, brutto, tv, fu = _nachbau_coin(np.ascontiguousarray(m.o[j, a:b]), np.ascontiguousarray(m.c[j, a:b]),
                                            np.ascontiguousarray(m.fund[j, a:b]), np.ascontiguousarray(w[j, a:b], dtype=np.float64),
                                            1.0 / N, float(slip[j]))
        eq += brutto - fee * tv + fu
        ex += np.abs(pos) * m.c[j, a:b]
    return eq, ex


from numba import prange


@njit(parallel=True)
def starts_sim(o, c, fund, w, slip, fee, starts, n_h, checkpoints):
    """Frischer Start an jedem Index in `starts` (Hebel 1, S = 1/N je Coin, Regeln wie `_nachbau_coin`, ohne Schlussabrechnung).
    Gibt je Start und je Prüfpunkt (Anzahl Kerzen) das Minimum des Gewinns seit Start zurück (NaN, wenn die Daten nicht reichen)."""
    ns = len(starts); N = o.shape[0]; T = o.shape[1]
    out = np.full((ns, len(checkpoints)), np.nan)
    ende = np.full((ns, len(checkpoints)), np.nan)
    S = 1.0 / N
    for si in prange(ns):
        s = starts[si]
        n = min(n_h, T - s)
        path = np.zeros(n)
        for j in range(N):
            q = 0.0; cash = 0.0; vol = 0.0; f = 0.0; held = 0.0
            for k in range(n):
                t = s + k
                tgt = w[j, t]
                if fund[j, t] != 0.0 and q != 0.0:
                    f -= q * o[j, t] * fund[j, t]
                if k > 0 and abs(tgt - held) > 1e-9:
                    if held == 0.0:
                        dq = tgt * S / o[j, t]
                    elif tgt * held < 0.0:
                        dq = -q + tgt * S / o[j, t]
                    else:
                        dq = -q * (1.0 - tgt / held)
                    sq = 1.0 if dq > 0 else -1.0
                    px = o[j, t] * (1.0 + sq * slip[j])
                    cash -= dq * px; vol += abs(dq) * px; q += dq; held = tgt
                path[k] += cash + q * c[j, t] - fee * vol + f
        mn = 0.0
        ci = 0
        for k in range(n):
            if path[k] < mn:
                mn = path[k]
            while ci < len(checkpoints) and k == checkpoints[ci] - 1:
                out[si, ci] = mn; ende[si, ci] = path[k]
                ci += 1
    return out, ende
