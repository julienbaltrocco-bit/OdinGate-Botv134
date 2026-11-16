"""Schritt 7/8: Walk-Forward (70/30 + rollierend), Entscheidungsregeln, Kapital-Szenarien. Schreibt ergebnis.json."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
import pandas as pd
from hybrid import runner, walkforward as wf

ROOT = Path(__file__).resolve().parents[1]
pd.set_option("display.width", 250, "display.max_columns", 40, "display.max_rows", 100)
gesamt = {}
for strat in ("trail_beide", "momentum_vol_ls"):
    L = wf.laden(strat, 3.0)
    idx = L["baseline"].markt.index
    split = wf.split_datum(idx, runner.CFG["walk_forward"]["lern_anteil"])
    print(f"\n================ {strat}: Lernen {idx[0].date()} – {split.date()}, Prüfen {split.date()} – {idx[-1].date()}")
    p, lern = wf.waehlen(L, None, split)
    print(lern[["dip", "tp", "trail", "sharpe", "rendite_ohne", "dd_ohne", "order_zu_fill", "trades", "plateau"]].to_string())
    print("gewählt:", p)
    hyb = L[wf.name(p)]
    zeile = {}
    for n, l in (("baseline", L["baseline"]), ("swing_limit", L["swing_limit"]), ("hybrid", hyb)):
        zeile[n] = {"lernen": runner.kennzahlen(l, None, split), "pruefen": runner.kennzahlen(l, split, None),
                    "orders": runner.order_statistik(l)}
    u = wf.urteil(zeile["hybrid"]["pruefen"], zeile["baseline"]["pruefen"], zeile["hybrid"]["orders"])
    spalten = ["rendite_brutto", "rendite_ohne", "rendite_mit", "dd_ohne", "dd_mit", "trades", "trades_taktik",
               "haltedauer_h", "trefferquote", "volumen_tag", "maker_anteil", "rebate_tag", "orders_tag",
               "order_zu_fill", "anteil_coin", "anteil_monat", "funding"]
    for fenster in ("lernen", "pruefen"):
        print(f"--- {fenster}")
        print(pd.DataFrame({n: {s: zeile[n][fenster][s] for s in spalten} for n in zeile}).round(4).to_string())
    print("--- Urteil (Prüffenster, Hebel 3)")
    for r in u:
        print(f"  {'OK  ' if r['ok'] else 'NEIN'} {r['regel']}: {r['wert']}")
    print("  Orders Hybrid:", zeile["hybrid"]["orders"])
    roll = wf.rollierend(L, **runner.CFG["walk_forward"]["rollierend"])
    print("--- rollierend (12 Monate lernen, 3 Monate prüfen)")
    print(roll.round(4).to_string())
    print("Summe:", roll[["hybrid_ohne", "hybrid_mit", "hybrid_brutto", "baseline_ohne", "baseline_mit", "swing_limit_ohne"]].sum().round(4).to_dict(),
          "| Hybrid ≥ Baseline in", int((roll.hybrid_ohne >= roll.baseline_ohne).sum()), "von", len(roll), "Fenstern")
    # dieselbe Wahl mit Hebel 1 (nur zur Einordnung des Einbruchs)
    L1 = wf.laden(strat, 1.0)
    h1 = {n: runner.kennzahlen(L1[k], split, None) for n, k in (("baseline", "baseline"), ("swing_limit", "swing_limit"), ("hybrid", wf.name(p)))}
    print("--- Hebel 1, Prüffenster:", {n: (round(x["rendite_ohne"], 4), round(x["dd_ohne"], 4)) for n, x in h1.items()})
    alle = {n: runner.kennzahlen(L[n], split, None) for n in L}
    gesamt[strat] = {"split": str(split.date()), "start": str(idx[0].date()), "ende": str(idx[-1].date()), "gewaehlt": p,
                     "lerntabelle": lern.reset_index(names="name").to_dict("records"), "ergebnis": zeile, "urteil": u,
                     "rollierend": roll.to_dict("records"), "hebel1_pruefen": h1, "alle_pruefen": alle}
(ROOT / "data/processed").mkdir(exist_ok=True)
(ROOT / "reports/ergebnis.json").write_text(json.dumps(gesamt, indent=1, default=str))
