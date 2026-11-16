"""Übersicht aller Testreihen im hochgeladenen Labor: je Reihe/Strategie die Prüfzeitraum-Kennzahlen."""
import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
LABOR = ROOT / "data/raw/labor-daten/trading-labor/trading-labor"


def tabelle() -> pd.DataFrame:
    z = []
    for f in sorted((LABOR / "berichte").glob("*/ergebnis.json")):
        d = json.loads(f.read_text())
        s = d["serie"]
        vw = f.parent / "vorwaerts.json"
        v = json.loads(vw.read_text()) if vw.exists() else {}
        for name, x in d["strategien"].items():
            p = x.get("pruefzeitraum", {})
            z.append({
                "reihe": s["name"], "quelle": s["quelle"], "iv": s["intervall"], "n_sym": len(s["symbole"]),
                "start": s["start"], "split": s["split"], "ende": s["ende"], "strategie": name,
                "ampel": x["urteil"]["ampel"], "rendite": p.get("rendite"), "bh": p.get("bh_rendite"),
                "max_dd": p.get("max_dd"), "trades": p.get("trades"), "treffer": p.get("trefferquote"),
                "pf2x": p.get("pf_2x"), "halte_bars": p.get("haltedauer_bars"), "zufall": p.get("zufall_perzentil"),
                "params": json.dumps(x.get("params")),
            })
    return pd.DataFrame(z)


if __name__ == "__main__":
    t = tabelle()
    out = ROOT / "data/processed"
    out.mkdir(parents=True, exist_ok=True)
    t.to_csv(out / "reihen_uebersicht.csv", index=False)
    pd.set_option("display.width", 250, "display.max_rows", 300, "display.max_colwidth", 60)
    print(t.drop(columns=["params"]).round(3).to_string())
