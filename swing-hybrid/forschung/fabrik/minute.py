"""Minutenraster der Fabrik (Baustein 1 aus protokoll.md Abschnitt 36): Datenspeicher und Hilfen für den Einstieg innerhalb der Kerze.

Der Simulator selbst ist `fabrik/kern.py`: er kennt kein Raster, nur Kerzen. Auf Minutenraster bekommt er Minutenkerzen,
Haltedauern in Minuten und alle 5-Minuten-Größen so, wie sie am Schluss der jeweiligen Minute bekannt sind. Wird das
Signal nur an Minuten gesetzt, die eine 5-Minuten-Kerze schließen, entstehen dieselben Trades wie auf dem 5-Minuten-Raster
(Paritätstest `tests/test_fabrik_minute.py`). Liest nur über alpha.kern.lesen, also nie über den 31.03.2025 hinaus.

  .venv/bin/python -I forschung/fabrik/minute.py        (aus swing-hybrid/, einmalig, rund zwei Minuten, rund 1,5 GB)
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

F = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(F))
from fabrik import daten as D, kern as FK

SPEICHER = F.parent / "data/fabrik_minute"
RASTER = pd.date_range(D.RASTER[0], D.RASTER[-1] + pd.Timedelta(minutes=4), freq="1min")
N = len(RASTER)                                                   # genau 5 Minuten je 5-Minuten-Kerze
assert N == 5 * D.N


def bauen():
    from alpha import kern as K
    SPEICHER.mkdir(parents=True, exist_ok=True)
    f64 = {k: np.lib.format.open_memmap(SPEICHER / f"{k}.npy", mode="w+", dtype=np.float64, shape=(len(D.COINS), N)) for k in ("o", "h", "l", "c")}
    f32 = {k: np.lib.format.open_memmap(SPEICHER / f"{k}.npy", mode="w+", dtype=np.float32, shape=(len(D.COINS), N)) for k in ("tq", "qv")}
    gueltig = np.zeros((len(D.COINS), N), bool)
    for j, coin in enumerate(D.COINS):
        m = K.lesen("1m", coin).reindex(RASTER)
        g = np.isfinite(m["close"].to_numpy())
        c = m["close"].ffill().to_numpy()                          # Lücke: letzter Schluss, als ungültig markiert (wie im 5-Minuten-Speicher)
        for x, sp in (("o", "open"), ("h", "high"), ("l", "low"), ("c", "close")):
            f64[x][j] = np.where(g, m[sp].to_numpy(), c)
        f32["tq"][j], f32["qv"][j] = m["taker_quote"].to_numpy(), m["quote_volume"].to_numpy()
        gueltig[j] = g
        print(coin, "Minuten gültig:", int(g.sum()), "fehlend seit erster Minute:", int((~g[np.argmax(g):]).sum()), flush=True)
    for a in list(f64.values()) + list(f32.values()):
        a.flush()
    np.save(SPEICHER / "gueltig.npy", gueltig)
    print("gespeichert:", SPEICHER, f"{N} Minuten x {len(D.COINS)} Coins")


def laden(name: str) -> np.ndarray:
    return np.load(SPEICHER / f"{name}.npy", mmap_mode="r")


def auf_minuten(x5: np.ndarray) -> np.ndarray:
    """Größe des 5-Minuten-Rasters auf Minuten: an Minute m steht der Wert der letzten bis dahin abgeschlossenen 5-Minuten-Kerze.
    Kerze i umfasst die Minuten 5i bis 5i+4 und ist am Schluss von Minute 5i+4 bekannt."""
    i = (np.arange(5 * len(x5)) + 1) // 5 - 1
    aus = np.asarray(x5)[np.maximum(i, 0)].astype(np.float64)
    aus[i < 0] = np.nan
    return aus


def nur_kerzenschluss(ein5: np.ndarray, wert5: np.ndarray):
    """Einstiegsreihe und Signalwert des 5-Minuten-Rasters auf Minuten, gesetzt nur an der Minute, die die Kerze schließt.
    Dazwischen: kein Einstieg (0) und kein Signal-Ausstieg (nan)."""
    ein = np.zeros(5 * len(ein5), np.int8)
    wert = np.full(5 * len(wert5), np.nan)
    ein[4::5], wert[4::5] = ein5, wert5
    return ein, wert


def fcum_minuten(fcum5: np.ndarray) -> np.ndarray:
    """Aufgelaufenes Funding: fällt an der Minute an, mit der die betreffende 5-Minuten-Kerze öffnet."""
    return np.repeat(np.asarray(fcum5, dtype=np.float64), 5)


def slip_minuten(slip5: np.ndarray) -> np.ndarray:
    """Slippage je Order, die nach dem Schluss von Minute m gestellt wird: aus der letzten abgeschlossenen 5-Minuten-Kerze.
    Vor dem Schluss der ersten Kerze gilt deren Wert (dort wird nie gehandelt)."""
    s = auf_minuten(slip5)
    s[:4] = slip5[0]
    return s


def handelbar(gueltig_m: np.ndarray) -> np.ndarray:
    """Signal am Schluss von Minute m darf handeln, wenn m-1, m und die Einstiegsminute m+1 vorhanden sind:
    fehlt eine Minute, gibt es in ihr und in der folgenden Minute keinen Einstieg."""
    g = np.asarray(gueltig_m, bool)
    vor = np.concatenate([[False], g[:-1]])
    nach = np.concatenate([g[1:], [False]])
    return g & vor & nach


def kaufdruck_minute(tq: np.ndarray, qv: np.ndarray, L: int) -> np.ndarray:
    """Kaufdruck über die letzten 5*L Minuten, an jeder Minute neu, geteilt durch die 7-Tage-Schwankung des 5-Minuten-Signals
    (gerechnet aus den Werten an den schließenden Minuten bis zur vorletzten abgeschlossenen Kerze, wie in fabrik/signale.py).
    An Minuten, die eine 5-Minuten-Kerze schließen, entspricht der Wert dem Fabrik-Signal kaufdruck_L."""
    tq, qv = pd.Series(np.asarray(tq, dtype=np.float64)), pd.Series(np.asarray(qv, dtype=np.float64))
    roh = ((2 * tq - qv).rolling(5 * L).sum() / qv.rolling(5 * L).sum()).replace([np.inf, -np.inf], np.nan)
    sd5 = pd.Series(roh.to_numpy()[4::5]).rolling(S_W7, min_periods=576).std().shift(1).to_numpy()
    sd = np.repeat(sd5, 5)                                         # an Minute m gilt die Schwankung der Kerze m // 5 (kennt nur frühere Kerzen)
    return np.where(sd > 0, roh.to_numpy() / np.where(sd > 0, sd, 1.0), np.nan)


S_W7 = 2016                                                       # 7 Tage in 5-Minuten-Kerzen (wie signale.W7)


def trades(o, h, l, fcum, ein, wert, sigma, slip, i0, i1, ausstieg, je_kerze=1, max_trades=200_000):
    """Einzel-Trades über die Kerzen [i0, i1). `ausstieg` wie in generator.AUSSTIEGE (Haltedauer in 5-Minuten-Kerzen);
    je_kerze = 5 rechnet die Haltedauer auf Minuten um. Rückgabe: Feld [n, 6] wie kern.trades_liste."""
    halte, sl, tp, tr, ta, sx = ausstieg
    aus = np.zeros((max_trades, 6))
    n = FK.trades_liste(o, h, l, fcum, ein, wert, sigma, i0, i1, halte * je_kerze, float(sl), float(tp), float(tr), float(ta),
                        np.nan if sx is None else float(sx), slip, aus)
    return aus[:n]


if __name__ == "__main__":
    bauen()
