"""Stufe 1: alle 30 Einstellungen im ENTWICKLUNGSZEITRAUM (Gruppe A, Hebel 1). Der Prüfzeitraum wird nicht ausgegeben."""
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
import pandas as pd
from hybrid import research as R

ROOT = Path(__file__).resolve().parents[1]
KONFIG = ([("tsmom", dict(L=L, bias=b)) for L in (12, 24, 48, 96, 168) for b in (False, True)]
          + [("ensemble", dict(bias=b)) for b in (False, True)]
          + [("reversal", dict(n=n, k=k, bias=b)) for n in (24, 72) for k in (1.5, 2.0, 2.5) for b in (False, True)]
          + [("querschnitt", dict(L=L, modus=mo)) for L in (4, 24, 72) for mo in ("mom", "rev")])


def name(fam, p):
    return fam + "_" + "_".join(f"{k}{v}" for k, v in p.items())


if __name__ == "__main__":
    t0 = time.time()
    m = R.markt(R.GRUPPE_A)
    print(f"Markt geladen in {time.time() - t0:.0f} s, {len(m.index)} Kerzen")
    zeilen = []
    for fam, p in KONFIG:
        w = R.auf_raster(m, R.FAMILIEN[fam](m, **p))
        l = R.lauf(m, w)
        d1, d2 = R.sicht(l, None, R.D1_ENDE), R.sicht(l, R.D1_ENDE, R.SPLIT)
        ok = all(x["G"] > 0 and x["N"] > 0 and x["of"] <= 5 for x in (d1, d2))
        zeilen.append({"name": name(fam, p), "familie": fam, "params": json.dumps(p), "bestanden": ok,
                       "score": min(d1["sharpe"], d2["sharpe"]),
                       **{f"D1_{k}": v for k, v in d1.items()}, **{f"D2_{k}": v for k, v in d2.items()}})
    t = pd.DataFrame(zeilen)
    t.to_csv(ROOT / "reports/suche_stufe1.csv", index=False)
    pd.set_option("display.width", 260, "display.max_columns", 60, "display.max_rows", 100)
    sp = ["name", "bestanden", "score", "D1_G", "D1_F", "D1_N", "D2_G", "D2_F", "D2_N", "D1_bp_je_umsatz", "D2_bp_je_umsatz",
          "D2_vol_tag", "D2_maker", "D2_of", "D2_dd_mit", "D2_rebate_anteil", "D2_halte_h"]
    print(t[sp].round(3).to_string())
    fin = (t[t["bestanden"]].sort_values("score", ascending=False).groupby("familie").head(1)
           .sort_values("score", ascending=False).head(3))
    print("\nFinalisten:", list(fin["name"]))
    (ROOT / "reports/suche_finalisten.json").write_text(json.dumps(
        [{"name": r["name"], "familie": r["familie"], "params": json.loads(r["params"])} for _, r in fin.iterrows()], indent=1))
    print(f"fertig in {time.time() - t0:.0f} s")
