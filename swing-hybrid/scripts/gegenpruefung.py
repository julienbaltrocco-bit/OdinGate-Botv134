"""Gegenprüfungen zum Ergebnis (keine Optimierung, nur: hält das Urteil?)."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
import numpy as np
import pandas as pd
from hybrid import data, runner, swing, walkforward as wf

ROOT = Path(__file__).resolve().parents[1]
erg = json.loads((ROOT / "reports/ergebnis.json").read_text())
out = {}
for strat in ("trail_beide", "momentum_vol_ls"):
    e = erg[strat]
    split = pd.Timestamp(e["split"])
    print(f"\n===== {strat}")
    # (a) Baseline gegen die Kontoverläufe des Labors, gleiches Fenster, ohne Hebel
    q = swing.QUELLEN[strat]
    d = json.loads((swing.LABOR / "berichte" / q["reihe"] / "ergebnis.json").read_text())
    lab = []
    for coin in swing.COINS:
        pfad = d["strategien"][strat]["laeufe"]["1x"][f"{coin}-USDT"].replace("\\", "/")
        eq = pd.read_csv(swing.LABOR / pfad / "artifacts/equity.csv", index_col=0, parse_dates=True)["equity"]
        a = eq[eq.index >= split]
        lab.append(a.iloc[-1] / a.iloc[0] - 1)
    L1 = wf.laden(strat, 1.0)
    mein = runner.kennzahlen(L1["baseline"], split, "2026-10-01")
    print(f"(a) {split.date()} – 2026-10-01 ohne Hebel: Labor Ø je Coin {np.mean(lab):+.1%} | meine Baseline {mein['rendite_ohne']:+.1%} "
          f"(brutto {mein['rendite_brutto']:+.1%})")
    out[strat] = {"labor_fenster": float(np.mean(lab)), "baseline_fenster": mein["rendite_ohne"]}
    # (b) alle 18 Varianten im Prüffenster: schlägt irgendeine die Baseline?
    alle = e["alle_pruefen"]
    base = alle["baseline"]["rendite_ohne"]
    t = pd.DataFrame({n: {"ohne": k["rendite_ohne"], "brutto": k["rendite_brutto"], "dd": k["dd_ohne"], "of": k["order_zu_fill"],
                          "vol": k["volumen_tag"]} for n, k in alle.items()}).T.sort_values("ohne", ascending=False)
    print("(b) Prüffenster, alle Varianten (netto ohne Rebate):")
    print(t.round(3).to_string())
    hyb = t[t.index.str.startswith("hybrid")]
    out[strat]["varianten_besser_als_baseline"] = int((hyb["ohne"] >= base).sum())
    out[strat]["varianten_besser_und_of_ok"] = int(((hyb["ohne"] >= base) & (hyb["of"] <= 5)).sum())
    out[strat]["beste_variante_ohne"] = float(hyb["ohne"].max())
    # (c) mildere Füllannahme: jede Berührung über den Preis hinaus zählt (eps = 0)
    m = data.laden(strat)
    alt = runner.EPS
    runner.EPS = 0.0
    p = e["gewaehlt"]
    h = runner.kennzahlen(runner.lauf(m, 3.0, **runner.hybrid(**p)), split, None)
    s = runner.kennzahlen(runner.lauf(m, 3.0, **runner.VARIANTEN["swing_limit"]), split, None)
    runner.EPS = alt
    print(f"(c) mildere Füllung (eps=0): Hybrid {h['rendite_ohne']:+.1%}, Swing-mit-Limit {s['rendite_ohne']:+.1%}, Baseline {base:+.1%}")
    out[strat]["mild_hybrid"] = h["rendite_ohne"]
    out[strat]["mild_swing_limit"] = s["rendite_ohne"]
    # Monatsgewinne der Baseline im Prüffenster (für das Klumpenrisiko)
    L3 = wf.laden(strat, 3.0)
    tg = L3["baseline"].daily_pnl(runner.OHNE).sum(axis=1)
    mon = tg[tg.index >= split].groupby(tg[tg.index >= split].index.to_period("M")).sum()
    print("Baseline Monatsgewinne (Hebel 3, ohne Rebate):", mon.round(3).to_dict())
    out[strat]["baseline_monate"] = {str(k): float(v) for k, v in mon.items()}
    tgh = L3[wf.name(p)].daily_pnl(runner.OHNE).sum(axis=1)
    monh = tgh[tgh.index >= split].groupby(tgh[tgh.index >= split].index.to_period("M")).sum()
    out[strat]["hybrid_monate"] = {str(k): float(v) for k, v in monh.items()}
    tr = L3[wf.name(p)].trades
    tr = tr[tr["aus_zeit"] >= split]
    netto = tr["brutto"] - runner.MAKER * tr["maker_vol"] - runner.TAKER * tr["taker_vol"]
    g = pd.DataFrame({"art": tr["art"], "brutto": tr["brutto"], "netto": netto}).groupby("art").agg(["sum", "count", "mean"])
    print("Hybrid-Trades im Prüffenster nach Art (ohne Funding):"); print(g.round(5).to_string())
    out[strat]["taktik_brutto"] = float(tr.loc[tr["art"] == "taktik", "brutto"].sum())
    out[strat]["taktik_netto"] = float(netto[tr["art"] == "taktik"].sum())
    out[strat]["kern_netto"] = float(netto[tr["art"] == "kern"].sum())
(ROOT / "reports/gegenpruefung.json").write_text(json.dumps(out, indent=1))
