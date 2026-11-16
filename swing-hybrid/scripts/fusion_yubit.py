"""Nachrechnung der Fusion (Runde 12) mit Yubit-Kosten und 85 % Rebate. Gleiche Stat-Arb-Einstellung wie im Bericht.

Kosten je Order und Coin: 0,08 % Taker-Gebühr, davon 85 % zurück (netto 0,012 %), plus 2 x gemessene halbe Yubit-Spanne.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
import numpy as np
import pandas as pd
from hybrid import data, research as R, runner, statarb as S, swing

ROOT = Path(__file__).resolve().parents[1]
pd.set_option("display.width", 220)
r12 = json.loads((ROOT / "reports/suche_runde12.json").read_text())
W, z = r12["statarb"]["W"], r12["statarb"]["z_ein"]
A = json.loads((ROOT / "reports/suche_runde6.json").read_text())["gruppen"]["A"]
slip = R.yubit_kosten(A)[0]
kY = 0.0008 * 0.15 + slip
D1, SPLIT = R.D1_ENDE, R.SPLIT


def drei(tag):
    return {"Entwicklung": S.kennzahlen(tag, None, SPLIT), "Pruefung": S.kennzahlen(tag, SPLIT, None), "Gesamt": S.kennzahlen(tag)}


m = R.markt(A)
_, _, _, hidx = S.stundenfelder(m)
sa_frei, _ = S.lauf(m, W, z, kY)
out = {}
for strat in ("trail_beide", "momentum_vol_ls"):
    md = data.laden(strat, A)
    alt = runner.SLIP
    runner.SLIP = 0.0                                   # Slippage wird unten je Coin nach Umsatz abgezogen
    ls = runner.lauf(md, 1.0, **runner.VARIANTEN["baseline"])
    runner.SLIP = alt
    d = ls.daily                                        # [Coin, Tag, (Kurswert, Maker-Umsatz, Taker-Umsatz, Funding)] kumuliert
    umsatz = d[:, :, 1] + d[:, :, 2]
    kum_netto = (d[:, :, 0] + d[:, :, 3] - kY[:, None] * umsatz).sum(axis=0)
    kum_brutto = (d[:, :, 0] + d[:, :, 3] - slip[:, None] * umsatz).sum(axis=0)
    sw_tag = pd.DataFrame({"netto": np.diff(np.concatenate([[0.0], kum_netto])), "brutto": np.diff(np.concatenate([[0.0], kum_brutto]))}, index=md.days)
    sw_tag["kosten"] = sw_tag["brutto"] - sw_tag["netto"]
    for k in ("funding", "umsatz", "einsatz"):
        sw_tag[k] = 0.0
    def gewicht(c):
        s = swing.ziel_ab(c, strat)
        s.index = s.index.astype("datetime64[ns]")
        return s.reindex(hidx.union(s.index)).ffill().reindex(hidx).fillna(0.0).to_numpy()
    sw = np.column_stack([gewicht(c) for c in A])
    sa_filter, _ = S.lauf(m, W, z, kY, sw=sw, filter_swing=True)
    idx = sw_tag.index.intersection(sa_frei.index)
    def kombi(x):
        k = 0.5 * sw_tag.loc[idx, ["netto", "brutto", "kosten"]] + 0.5 * x.loc[idx, ["netto", "brutto", "kosten"]]
        for s_ in ("funding", "umsatz", "einsatz"):
            k[s_] = 0.0
        return k
    f = {"swing_allein": drei(sw_tag.loc[idx]), "statarb_allein": drei(sa_frei.loc[idx]), "statarb_gefiltert": drei(sa_filter.loc[idx]),
         "F1_zwei_toepfe": drei(kombi(sa_frei)), "F2_swing_als_filter": drei(kombi(sa_filter))}
    for k in ("F1_zwei_toepfe", "F2_swing_als_filter"):
        f[k + "_besser"] = bool(all(f[k][w]["sharpe"] > f["swing_allein"][w]["sharpe"] and f[k][w]["dd"] < f["swing_allein"][w]["dd"]
                                    for w in ("Entwicklung", "Pruefung")))
    out[strat] = f
    print(f"\n===== {strat}, Yubit-Kosten mit 85 % Rebate, {idx[0].date()} – {idx[-1].date()}")
    t = pd.DataFrame({k: {f"{w[:4]}_{x}": f[k][w][x] for w in ("Entwicklung", "Pruefung") for x in ("jahr_N", "dd", "sharpe")}
                      for k in ("swing_allein", "statarb_allein", "statarb_gefiltert", "F1_zwei_toepfe", "F2_swing_als_filter")}).T
    print(t.round(3).to_string())
    print("F1 besser:", f["F1_zwei_toepfe_besser"], "| F2 besser:", f["F2_swing_als_filter_besser"])
(ROOT / "reports/fusion_yubit.json").write_text(json.dumps(out, indent=1, default=float))
