"""Runde 11: Massentest. Rund 600 Regel-Varianten in Swing-Richtung gegen die Messlatte „Trade verdient seine Gebühr“."""
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
import numpy as np
import pandas as pd
from hybrid import massentest as M, research as R

ROOT = Path(__file__).resolve().parents[1]
pd.set_option("display.width", 250, "display.max_columns", 40, "display.max_rows", 120)
G = json.loads((ROOT / "reports/suche_runde6.json").read_text())["gruppen"]
D1, SPLIT, START, ENDE = pd.Timestamp(R.D1_ENDE), pd.Timestamp(R.SPLIT), pd.Timestamp(R.START), pd.Timestamp(R.ENDE)
FEN = {"D1": (START, D1), "D2": (D1, SPLIT), "Pruefung": (SPLIT, ENDE)}
TAGE = {f: (b - a).days for f, (a, b) in FEN.items()}
t0 = time.time()
zeilen = {}
for g, coins in G.items():
    m = R.markt(coins)
    slip = dict(zip(coins, R.yubit_kosten(coins)[0]))
    for coin in coins:
        df = m.h1[coin]
        df = df[(df.index >= START - pd.Timedelta(days=75)) & (df.index < ENDE)]
        for bt in (60, 14):
            for name, (zeit, ret) in M.coin_trades(df, bt).items():
                for f, (a, b) in FEN.items():
                    x = ret[(zeit >= a) & (zeit < b)]
                    z = zeilen.setdefault((name, g, f), [0, 0.0, 0.0, 0.0])
                    netto = x - 2 * slip[coin]
                    z[0] += len(x); z[1] += float(netto.sum()); z[2] += float((netto ** 2).sum()); z[3] += float(x.sum())
    print(f"Gruppe {g}: {len(coins)} Coins gerechnet ({time.time() - t0:.0f} s)", flush=True)

t = pd.DataFrame([{"regel": k[0], "gruppe": k[1], "fenster": k[2], "n": v[0], "summe": v[1], "sq": v[2], "summe_roh": v[3]}
                  for k, v in zeilen.items()])
t["mittel"] = t["summe"] / t["n"].where(t["n"] > 0)
t["deckung"] = t["mittel"] / M.GEBUEHR_TAKER                       # Ertrag nach Slippage / volle Taker-Gebühr
t["deckung_maker"] = (t["summe_roh"] / t["n"].where(t["n"] > 0)) / M.GEBUEHR_MAKER   # ohne Slippage, halbe Gebühr
t.to_csv(ROOT / "reports/suche_runde11_alle.csv", index=False)


def pool(gruppe, fenster):
    """Deckung je Regel, über die genannten Fenster zusammengefasst."""
    x = t[(t["gruppe"] == gruppe) & (t["fenster"].isin(fenster))].groupby("regel")[["n", "summe", "summe_roh"]].sum()
    return pd.DataFrame({"n": x["n"], "deckung": x["summe"] / x["n"] / M.GEBUEHR_TAKER,
                         "deckung_maker": x["summe_roh"] / x["n"] / M.GEBUEHR_MAKER})


def eins(gruppe, fenster):
    return t[(t["gruppe"] == gruppe) & (t["fenster"] == fenster)].set_index("regel")


a1, a2 = eins("A", "D1"), eins("A", "D2")
uebersicht = pd.DataFrame({"A_D1": a1["deckung"], "A_D2": a2["deckung"], "n_D1": a1["n"], "n_D2": a2["n"],
                           "A_Pruef": eins("A", "Pruefung")["deckung"], "n_Pruef": eins("A", "Pruefung")["n"],
                           "B_Entw": pool("B", ["D1", "D2"])["deckung"], "B_Pruef": eins("B", "Pruefung")["deckung"],
                           "C_Entw": pool("C", ["D1", "D2"])["deckung"], "C_Pruef": eins("C", "Pruefung")["deckung"],
                           "D_Entw": pool("D", ["D1", "D2"])["deckung"], "D_Pruef": eins("D", "Pruefung")["deckung"],
                           "maker_A_Entw": pool("A", ["D1", "D2"])["deckung_maker"], "maker_A_Pruef": eins("A", "Pruefung")["deckung_maker"]})
uebersicht["min_haelfte"] = uebersicht[["A_D1", "A_D2"]].min(axis=1)
uebersicht["ausstieg"] = [r.rsplit("_", 1)[1] for r in uebersicht.index]
uebersicht["trades_tag_je_coin"] = (uebersicht["n_D1"] + uebersicht["n_D2"]) / (TAGE["D1"] + TAGE["D2"]) / len(G["A"])
uebersicht.to_csv(ROOT / "reports/suche_runde11_uebersicht.csv")

stufe1 = uebersicht[(uebersicht["A_D1"] >= 1) & (uebersicht["A_D2"] >= 1) & (uebersicht["n_D1"] >= 200) & (uebersicht["n_D2"] >= 200)]
gegen = ["A_Pruef", "B_Entw", "B_Pruef", "C_Entw", "C_Pruef"]
stufe2 = stufe1[(stufe1[gegen] >= 1).all(axis=1)]
print(f"\n{len(uebersicht)} Regel-Varianten. Stufe 1 (Deckung >= 1 in D1 und D2, je >= 200 Trades): {len(stufe1)}")
print(f"Davon Stufe 2 (alle fünf Gegenproben >= 1): {len(stufe2)}")
print(f"Zum Vergleich: genug Trades haben {int(((uebersicht.n_D1 >= 200) & (uebersicht.n_D2 >= 200)).sum())} Varianten; "
      f"Deckung >= 1 in genau einer Hälfte: {int(((uebersicht.A_D1 >= 1) ^ (uebersicht.A_D2 >= 1)).sum())}")
sp = ["A_D1", "A_D2", "n_D1", "n_D2", "A_Pruef", "B_Entw", "B_Pruef", "C_Entw", "C_Pruef", "D_Entw", "D_Pruef", "trades_tag_je_coin"]
print("\nDie 20 besten nach schlechterer Entwicklungshälfte (mit Gegenproben):")
print(uebersicht[(uebersicht.n_D1 >= 200) & (uebersicht.n_D2 >= 200)].sort_values("min_haelfte", ascending=False).head(20)[sp].round(2).to_string())
print("\nDeckung nach Ausstiegsart (Median / bestes Zehntel / beste Regel), Gruppe A:")
grenze = uebersicht[(uebersicht.n_D1 >= 200) & (uebersicht.n_D2 >= 200)].copy()
grenze["A_Entw"] = pool("A", ["D1", "D2"])["deckung"]
fr = grenze.groupby("ausstieg").agg(regeln=("A_Entw", "size"), entw_median=("A_Entw", "median"), entw_p90=("A_Entw", lambda x: x.quantile(0.9)),
                                    entw_max=("A_Entw", "max"), pruef_median=("A_Pruef", "median"), pruef_p90=("A_Pruef", lambda x: x.quantile(0.9)),
                                    pruef_max=("A_Pruef", "max"), maker_entw_median=("maker_A_Entw", "median"), maker_pruef_median=("maker_A_Pruef", "median"),
                                    maker_pruef_max=("maker_A_Pruef", "max"))
fr = fr.loc[[a for a, _ in M.AUSSTIEGE]]
print(fr.round(2).to_string())
out = {"varianten": int(len(uebersicht)), "stufe1": list(stufe1.index), "stufe2": list(stufe2.index),
       "frontier": {k: {kk: float(vv) for kk, vv in v.items()} for k, v in fr.T.to_dict().items()},
       "stufe1_tabelle": stufe1[sp].round(4).T.to_dict(), "tage": TAGE}
(ROOT / "reports/suche_runde11.json").write_text(json.dumps(out, indent=1, default=float))
print(f"\nfertig in {time.time() - t0:.0f} s")
