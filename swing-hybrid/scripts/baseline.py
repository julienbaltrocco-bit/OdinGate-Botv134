"""Schritt 3: reine Swing-Strategie mit Yubit-Gebühren nachrechnen (ganzer Zeitraum und Labor-Prüfzeitraum)."""
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
import pandas as pd
from hybrid import data, runner

LABOR_SPLIT = {"trail_beide": "2024-10-01", "momentum_vol_ls": "2025-01-01"}
zeilen = []
for strat in ("trail_beide", "momentum_vol_ls"):
    t0 = time.time()
    m = data.laden(strat)
    print(f"{strat}: {len(m.index)} Kerzen x {len(m.coins)} Coins geladen in {time.time() - t0:.0f} s")
    for hebel in (1.0, 3.0):
        t0 = time.time()
        l = runner.lauf(m, hebel, **runner.VARIANTEN["baseline"])
        for name, von, bis in (("gesamt", None, None), ("labor-pruefzeitraum", LABOR_SPLIT[strat], "2026-10-01")):
            k = runner.kennzahlen(l, von, bis)
            zeilen.append({"swing": strat, "hebel": hebel, "fenster": name, **k})
        print(f"  Hebel {hebel:g}: {time.time() - t0:.1f} s, {runner.order_statistik(l)}")
t = pd.DataFrame(zeilen)
out = Path(__file__).resolve().parents[1] / "data/processed/baseline.csv"
t.to_csv(out, index=False)
pd.set_option("display.width", 250, "display.max_columns", 40)
print(t[["swing", "hebel", "fenster", "tage", "rendite_brutto", "rendite_ohne", "rendite_mit", "dd_ohne", "trades",
         "haltedauer_h", "trefferquote", "volumen_tag", "rebate_tag", "funding", "anteil_coin", "anteil_monat",
         "sharpe_ohne"]].round(4).to_string())
