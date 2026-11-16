"""Dieselben Läufe, neue Zielgröße: Rebate zählt voll als Ertrag. Wo käme der Gewinn her?

Je Variante: Handelsergebnis vor Gebühren (G), gezahlte Gebühr (F), Rebate (R = 85 % von F),
Netto mit Rebate (N = G - F + R). "Rebate ist der größere Anteil" heißt: R > N - R.
Auswahl wie bisher nur im Lernfenster, diesmal nach Sharpe MIT Rebate.
"""
import json
import statistics
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
import numpy as np
import pandas as pd
from hybrid import runner, walkforward as wf

ROOT = Path(__file__).resolve().parents[1]
pd.set_option("display.width", 250, "display.max_columns", 40, "display.max_rows", 100)
out = {}
for strat in ("trail_beide", "momentum_vol_ls"):
    L = wf.laden(strat, 3.0)
    idx = L["baseline"].markt.index
    split = wf.split_datum(idx, 0.7)

    def zeile(l, von, bis):
        k = runner.kennzahlen(l, von, bis)
        F = k["gebuehr_tag"] * k["tage"]
        R = k["rebate_tag"] * k["tage"]
        tg = l.daily_pnl(runner.MIT).sum(axis=1)
        a = pd.Timestamp(von) if von is not None else tg.index[0]
        b = pd.Timestamp(bis) if bis is not None else tg.index[-1] + pd.Timedelta(days=1)
        tg = tg[(tg.index >= a) & (tg.index < b)]
        return {"G_vor_gebuehren": k["rendite_brutto"], "F_gebuehr": F, "R_rebate": R, "handel_nach_gebuehr": k["rendite_ohne"],
                "N_mit_rebate": k["rendite_mit"], "rebate_anteil": R / k["rendite_mit"] if k["rendite_mit"] > 0 else float("nan"),
                "dd_mit": k["dd_mit"], "vol_tag": k["volumen_tag"], "of": k["order_zu_fill"],
                "sharpe_mit": float(tg.mean() / tg.std() * np.sqrt(365)) if tg.std() > 0 else 0.0}

    lern = {n: zeile(l, None, split) for n, l in L.items()}
    pruef = {n: zeile(l, split, None) for n, l in L.items()}
    # Plateau-Wahl im Lernfenster nach Sharpe mit Rebate, O:F <= 5
    score = {wf.name(p): (lern[wf.name(p)]["sharpe_mit"] if lern[wf.name(p)]["of"] <= 5 else -9.0) for p in runner.RASTER}
    plateau = {wf.name(p): (statistics.median([score[wf.name(p)]] + [score[wf.name(q)] for q in wf.nachbarn(p)])
                            if score[wf.name(p)] > -9 else -9.0) for p in runner.RASTER}
    wahl = max(plateau, key=plateau.get)
    t = pd.DataFrame(pruef).T.sort_values("N_mit_rebate", ascending=False)
    print(f"\n===== {strat} | Prüffenster {split.date()} – {idx[-1].date()} | gewählt im Lernfenster (mit Rebate): {wahl}")
    print(t.round(3).to_string())
    b = pruef["baseline"]
    h = pruef[wahl]
    erfuellt = t[(t.index.str.startswith("hybrid")) & (t["G_vor_gebuehren"] >= 0) & (t["N_mit_rebate"] > 0)
                 & (t["R_rebate"] > t["N_mit_rebate"] - t["R_rebate"]) & (t["of"] <= 5)]
    print("Varianten, die im Prüffenster alle neuen Bedingungen erfüllen (vor Gebühren >= 0, netto mit Rebate > 0, Rebate > Handelsanteil, O:F <= 5):")
    print(erfuellt.round(3).to_string() if len(erfuellt) else "  keine")
    print("  davon besser als reine Swing mit Rebate:", int((erfuellt["N_mit_rebate"] >= b["N_mit_rebate"]).sum()))
    out[strat] = {"split": str(split.date()), "wahl": wahl, "lern": lern, "pruef": pruef,
                  "erfuellt": list(erfuellt.index)}
(ROOT / "reports/rebate_sicht.json").write_text(json.dumps(out, indent=1))
