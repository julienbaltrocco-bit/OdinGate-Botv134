"""RSK 09: Gegenproben. (a) Drei Starttage der Start-Tag-Analyse direkt mit dem Rechenkern der Forschung nachgerechnet
(eigener Markt ab dem Starttag). (b) Wann fällt das Konto bei Hebel 3 nach diesen Starts unter 50 % / 25 % / 0 %.
(c) Häufigkeit großer Tagesverluste bei Hebel 3 je Zeitraum."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import numpy as np
import pandas as pd
from rsk_common import A, R, SCRATCH, kandidat, runner

d = np.load(SCRATCH / "starttage.npz")
start = pd.DatetimeIndex(d["start"]); mn = d["mn"]
print("(a)/(b) Gegenprobe einzelner Starttage mit dem Rechenkern (R.markt ab Starttag, 365 Tage, Hebel 1; Konto bei Hebel 3 = 1 + 3 x Ergebnis)")
for tag in ("2021-02-13", "2024-08-06", "2025-07-23", "2022-01-01", "2023-06-01", "2026-02-26"):
    a = pd.Timestamp(tag); b = min(a + pd.Timedelta(days=365), pd.Timestamp(R.ENDE))
    m = R.markt(A, start=str(a), ende=str(b), vor=True)
    l, _ = kandidat(m, 1.0)
    eq = l.equity(runner.MIT)[:-1]                              # ohne die Schlussabrechnung der letzten Kerze
    k3 = 1.0 + 3.0 * eq
    i = int(np.flatnonzero(start == a)[0])
    volle = len(m.index) >= 365 * 288
    ref = mn[i, 3] if volle else np.nan
    erst = lambda sw: (str(m.index[int(np.argmax(k3 < sw))])[:16] + f" (Tag {int(np.argmax(k3 < sw)) // 288})") if (k3 < sw).any() else "nie"
    ks = pd.Series(k3, index=m.index[:-1])
    tief_t, tief_h = ks.resample("1D").min(), ks.resample("1h").min()
    zaehl = "; ".join(f"unter {int(sw * 100)} %: {(tief_t < sw).sum()} Tage / {(tief_h < sw).sum()} Stunden" for sw in (0.5, 0.25, 0.0))
    print(f"  Start {tag}: [{zaehl}]")
    print(f"  Start {tag}: tiefstes Ergebnis Hebel 1 laut Rechenkern {eq.min():+.4f}" + (f", laut Start-Tag-Simulation {ref:+.4f} (Abweichung {abs(eq.min() - ref):.1e})" if volle else " (weniger als 365 Tage Daten)")
          + f"; Konto bei Hebel 3: tiefster Stand {k3.min():.0%}, unter 50 % ab {erst(0.5)}, unter 25 % ab {erst(0.25)}, unter 0 % ab {erst(0.0)}; Stand am Ende des Fensters ({len(k3) // 288} Tage) {k3[-1]:.0%}")

print("\n(c) Tage mit großem Verlust bei Hebel 3 (Tagesschluss zu Tagesschluss, in Punkten des Startkapitals)")
for name, fen in (("vor", {"Vorperiode": (None, None)}), ("haupt", {"Entwicklung": (None, R.SPLIT), "Pruefzeitraum": (R.SPLIT, None)})):
    tg = pd.read_pickle(SCRATCH / f"tage_{name}.pkl").sum(axis=1) * 3.0
    for fname, (a, b) in fen.items():
        x = tg
        if a is not None:
            x = x[x.index >= pd.Timestamp(a)]
        if b is not None:
            x = x[x.index < pd.Timestamp(b)]
        jahre = len(x) / 365.25
        print(f"  {fname:13s} ({len(x)} Tage): Verlust ab 10 %: {(x <= -0.10).sum()} Tage ({(x <= -0.10).sum() / jahre:.0f}/Jahr), ab 20 %: {(x <= -0.20).sum()} ({(x <= -0.20).sum() / jahre:.1f}/Jahr), "
              f"ab 33 %: {(x <= -1 / 3).sum()} ({(x <= -1 / 3).sum() / jahre:.1f}/Jahr), ab 50 %: {(x <= -0.5).sum()}; Gewinn ab 20 %: {(x >= 0.20).sum()}; Streuung {x.std():.1%} je Tag")
