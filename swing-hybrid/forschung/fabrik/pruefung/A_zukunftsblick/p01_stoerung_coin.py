"""Störungstest auf dem ENDERGEBNIS von signale._coin (normierte Signale, 4 Filter, sigma).

Es läuft der echte Code S._coin; nur D.laden, D.SPEICHER, D.N, D.RASTER werden umgebogen:
  - gelesen wird ausschließlich der Bereich [:I_ENDE] der Speicher (V2 bleibt ungelesen),
  - geschrieben wird in ein eigenes Verzeichnis unter pruefung/A_zukunftsblick/tmp_speicher.
Prüfung A: Rechnung auf den bei I_ENDE abgeschnittenen Daten == gespeicherte Werte [:I_ENDE] (bitgleich).
           (Abschneiden ist die stärkste Störung: die gespeicherten Werte wurden mit den Daten bis 03/2025 gerechnet.)
Prüfung B: alle Rohreihen aller Coins ab Kerze T elementweise zufällig verfälscht -> Werte vor T bitgleich.
Gegenprobe: nach T müssen sich die Ergebnisse ändern.
"""
import shutil, sys, time
from pathlib import Path
sys.path.insert(0, 'forschung')
import numpy as np, pandas as pd
from fabrik import daten as D, signale as S, lauf as L

HIER = Path(__file__).resolve().parent
TMP = HIER / "tmp_speicher"
ORIG = D.SPEICHER
I_ENDE = L.I_ENDE
NC = len(D.COINS)
ROH = ("o", "h", "l", "c", "qv", "tq", "tqv", "frate", "fcum", "oi", "konten_ls", "profis_ls", "taker_log", "prem", "b1", "a1", "b3", "a3", "b5", "a5")
_cache = {}


def echt(name):
    if name not in _cache:
        _cache[name] = np.array(np.load(ORIG / f"{name}.npy", mmap_mode="r")[:, :I_ENDE])      # nie über I_ENDE hinaus
    return _cache[name]


def umbiegen():
    D.SPEICHER = TMP
    D.N = I_ENDE
    D.RASTER = D.RASTER[:I_ENDE]


def leere_ziele():
    if TMP.exists():
        shutil.rmtree(TMP)
    TMP.mkdir(parents=True)
    np.lib.format.open_memmap(TMP / "signale.npy", mode="w+", dtype=np.float32, shape=(len(S.NAMEN), NC, I_ENDE))
    np.lib.format.open_memmap(TMP / "filter.npy", mode="w+", dtype=np.int8, shape=(4, NC, I_ENDE))
    np.lib.format.open_memmap(TMP / "sigma.npy", mode="w+", dtype=np.float32, shape=(NC, I_ENDE))


def lauf_coin(j, laden):
    leere_ziele()
    D.laden = laden
    S._coin(j)
    return (np.array(np.load(TMP / "signale.npy", mmap_mode="r")[:, j]), np.array(np.load(TMP / "filter.npy", mmap_mode="r")[:, j]),
            np.array(np.load(TMP / "sigma.npy", mmap_mode="r")[j]))


def gleich(a, b):
    return (a == b) | (np.isnan(a) & np.isnan(b)) if a.dtype.kind == "f" else (a == b)


def verfaelscher(T, seed):
    rng = np.random.default_rng(seed)
    gest = {}

    def laden(name):
        if name not in gest:
            a = echt(name).astype(np.float64) if name in ROH else echt(name)
            if name in ROH:
                a = a.copy()
                n = a.shape[1] - T
                # elementweise: Faktor, Vorzeichenwechsel/Versatz, und ein Teil der Werte wird NaN bzw. NaN wird Zahl
                f = np.exp(rng.normal(0, 0.5, (a.shape[0], n)))
                add = rng.normal(0, 1, (a.shape[0], n)) * (np.nanstd(a[:, :T], axis=1, keepdims=True) + 1e-12)
                neu = a[:, T:] * f + add
                loch = rng.random(neu.shape) < 0.02
                neu = np.where(np.isnan(neu), add, neu)
                neu[loch] = np.nan
                a[:, T:] = neu
            gest[name] = a
        return gest[name]
    return laden


if __name__ == "__main__":
    umbiegen()
    coins = [int(x) for x in sys.argv[1].split(",")] if len(sys.argv) > 1 else [2, 0]
    Ts = [int(x) for x in sys.argv[2].split(",")] if len(sys.argv) > 2 else [200_000, 290_000]
    fehler = 0
    for j in coins:
        t0 = time.time()
        sigA, filA, sgmA = lauf_coin(j, echt)
        sp_sig = np.array(np.load(ORIG / "signale.npy", mmap_mode="r")[:, j, :I_ENDE])
        sp_fil = np.array(np.load(ORIG / "filter.npy", mmap_mode="r")[:, j, :I_ENDE])
        sp_sgm = np.array(np.load(ORIG / "sigma.npy", mmap_mode="r")[j, :I_ENDE])
        print(f"\n=== Coin {j} {D.COINS[j]} | Grundrechnung {time.time() - t0:.0f} s")
        # Prüfung A
        ungl = [(S.NAMEN[i], int((~gleich(sigA[i], sp_sig[i])).sum()), int(np.argmin(gleich(sigA[i], sp_sig[i])))) for i in range(len(S.NAMEN)) if not gleich(sigA[i], sp_sig[i]).all()]
        print("A: Signale abgeschnitten == gespeichert:", "JA, alle", len(S.NAMEN), "bitgleich" if not ungl else f"NEIN: {ungl}")
        print("A: Filter gleich:", [bool((filA[k] == sp_fil[k]).all()) for k in range(4)], "| sigma gleich:", bool(gleich(sgmA, sp_sgm).all()))
        fehler += len(ungl) + sum(not (filA[k] == sp_fil[k]).all() for k in range(4)) + (not gleich(sgmA, sp_sgm).all())
        print("   gültige Werte je Signal (Anteil endlich) min/median:", round(float(np.isfinite(sigA).mean(1).min()), 3), round(float(np.median(np.isfinite(sigA).mean(1))), 3))
        # Tageszeit-Filter direkt
        print("   Filter 2 (Tageszeit) == Stunde der Kerzen-Eröffnung // 8:", bool((filA[2] == (pd.DatetimeIndex(D.RASTER).hour.to_numpy() // 8)).all()))
        for T in Ts:
            t0 = time.time()
            sigB, filB, sgmB = lauf_coin(j, verfaelscher(T, 1000 + T + j))
            bad = []
            for i, name in enumerate(S.NAMEN):
                g = gleich(sigA[i, :T], sigB[i, :T])
                if not g.all():
                    bad.append((name, int((~g).sum()), int(np.argmin(g))))
            fb = [(k, int((filA[k, :T] != filB[k, :T]).sum()), int(np.argmax(filA[k, :T] != filB[k, :T]))) for k in range(4) if (filA[k, :T] != filB[k, :T]).any()]
            gs = gleich(sgmA[:T], sgmB[:T])
            geaendert = sum(not np.array_equal(sigA[i, T:T + 5000], sigB[i, T:T + 5000], equal_nan=True) for i in range(len(S.NAMEN)))
            nicht = [S.NAMEN[i] for i in range(len(S.NAMEN)) if np.array_equal(sigA[i, T:T + 5000], sigB[i, T:T + 5000], equal_nan=True)]
            fg = [bool((filA[k, T:T + 20000] != filB[k, T:T + 20000]).any()) for k in range(4)]
            print(f"B: T={T} ({D.RASTER[T]}) {time.time() - t0:.0f} s | Signale vor T verändert: {bad or 'keine'} | Filter vor T verändert: {fb or 'keine'} | sigma vor T verändert: {int((~gs).sum())}")
            print(f"   Gegenprobe nach T: {geaendert}/{len(S.NAMEN)} Signale geändert (unverändert: {nicht}); Filter geändert {fg}; sigma geändert {not np.array_equal(sgmA[T:T+5000], sgmB[T:T+5000], equal_nan=True)}")
            # erste veränderte Stelle je Signal: darf nicht vor T liegen
            erste = [int(np.argmin(gleich(sigA[i], sigB[i]))) for i in range(len(S.NAMEN)) if not gleich(sigA[i], sigB[i]).all()]
            print(f"   früheste veränderte Stelle über alle Signale: {min(erste)} (T={T}); Verteilung erste Stelle - T: min {min(erste) - T}, median {int(np.median(erste)) - T}, max {max(erste) - T}")
            fehler += len(bad) + len(fb) + int((~gs).sum() > 0)
    shutil.rmtree(TMP, ignore_errors=True)
    print("\nFEHLER GESAMT:", fehler)
