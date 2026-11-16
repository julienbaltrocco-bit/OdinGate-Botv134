"""Runde 8: der unveränderte Kandidat auf den bei Yubit günstig handelbaren Coins. Eine Variante, keine Suche."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
import numpy as np
import pandas as pd
from hybrid import research as R, runner

ROOT = Path(__file__).resolve().parents[1]
pd.set_option("display.width", 260, "display.max_columns", 60)
FEN = {"Entwicklung": (None, R.SPLIT), "Pruefung": (R.SPLIT, None), "Gesamt": (None, None)}
SP = ["G", "F", "R", "handel", "N", "dd_mit", "vol_tag", "bp_je_umsatz", "trades", "halte_h", "sharpe", "jahr_N"]
HEBEL = (5, 4, 3, 2.5, 2, 1.5, 1, 0.75, 0.5, 0.4, 0.35, 0.3, 0.25, 0.2, 0.15, 0.1)
GRENZE = 0.0003
G = json.loads((ROOT / "reports/suche_runde6.json").read_text())["gruppen"]
alle = G["A"] + G["B"] + G["C"] + G["D"]
kosten = dict(zip(alle, R.yubit_kosten(alle)[0]))
guenstig = [c for c in alle if kosten[c] <= GRENZE]


def fen(l):
    return {k: R.sicht(l, *FEN[k]) for k in FEN}


def auswerten(coins):
    m = R.markt(coins)
    k = np.array([kosten[c] for c in coins])
    w = R.auf_raster(m, R.variante(m, "basis"))
    for h in HEBEL:
        l = R.lauf(m, w, hebel=h, taker=True, slip=k)
        if R.sicht(l, *FEN["Entwicklung"])["dd_mit"] <= 0.10:
            break
    j = {}
    for nm, fees in (("G", runner.BRUTTO), ("ohne", runner.OHNE), ("N", runner.MIT)):
        tg = l.daily_pnl(fees).sum(axis=1)
        j[nm] = tg.groupby(tg.index.year).sum()
    j = pd.DataFrame(j); j["R"] = j["N"] - j["ohne"]
    return {"coins": coins, "hebel": h, **fen(l), "stress_2x": fen(R.lauf(m, w, hebel=h, taker=True, slip=2 * k)),
            "alt_5bp": fen(R.lauf(m, w, hebel=h, taker=True, slip=0.0005)), "orders": runner.order_statistik(l),
            "kosten_mittel_bp": float(k.mean() * 1e4), "jahre": {str(i): x for i, x in j.round(5).T.to_dict().items()},
            "tage": {"Pruefung": (m.index[-1] - pd.Timestamp(R.SPLIT)).days + 1, "Gesamt": (m.index[-1] - m.index[0]).days + 1}}


out = {"grenze_bp": GRENZE * 1e4, "guenstig": guenstig, "kosten_bp": {c: round(kosten[c] * 1e4, 3) for c in alle},
       "A": auswerten(G["A"]), "guenstige_coins": auswerten(guenstig)}
print(f"Günstige Coins ({len(guenstig)}): {guenstig}")
for n in ("A", "guenstige_coins"):
    e = out[n]
    print(f"\n-- {n}: {len(e['coins'])} Coins, Hebel {e['hebel']}, Slippage-Annahme im Mittel {e['kosten_mittel_bp']:.2f} bp")
    print(pd.DataFrame({k: e[k] for k in FEN}).T[SP].round(3).to_string())
    print("   doppelte Kosten: Prüfung N", round(e["stress_2x"]["Pruefung"]["N"], 4), "| Entwicklung N", round(e["stress_2x"]["Entwicklung"]["N"], 4))
    print(pd.DataFrame(e["jahre"]).T.round(3).to_string())
a, g = out["A"], out["guenstige_coins"]
out["besser"] = bool(g["Entwicklung"]["N"] > a["Entwicklung"]["N"] and g["Pruefung"]["N"] > a["Pruefung"]["N"]
                     and g["stress_2x"]["Pruefung"]["N"] > 0)
print("\nBESSER als Gruppe A:", out["besser"])
(ROOT / "reports/suche_runde8.json").write_text(json.dumps(out, indent=1, default=float))
