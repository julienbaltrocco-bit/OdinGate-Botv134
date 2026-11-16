"""Runde 21: 14 Mutationen des Kandidaten, gemeinsame Zufallsprüfung, Bestätigung auf frischen Gruppen."""
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
import numpy as np
import pandas as pd
from hybrid import mutationen as M, research as R, runner, tagestrend as T

ROOT = Path(__file__).resolve().parents[1]
pd.set_option("display.width", 220)
G = json.loads((ROOT / "reports/suche_runde6.json").read_text())["gruppen"]
t0 = time.time()


def tage(m, fn):
    l = R.lauf(m, R.auf_raster(m, fn(m)), taker=True, slip=R.yubit_kosten(m.coins)[0], day_limit=9.0)
    return l.daily_pnl(runner.MIT).sum(axis=1)


def sharpe(x):
    return float(x.mean() / x.std() * np.sqrt(365)) if x.std() > 0 else 0.0


def teil(x, von=None, bis=None):
    if von is not None:
        x = x[x.index >= pd.Timestamp(von)]
    if bis is not None:
        x = x[x.index < pd.Timestamp(bis)]
    return x


out = {"varianten": {}}
mA = R.markt(G["A"], vor=True)
basis = tage(mA, M.basis)
reihen = {n: tage(mA, fn) for n, fn in M.VARIANTEN.items()}
print(f"Läufe Gruppe A fertig nach {time.time() - t0:.0f} s")
FEN = {"D1": (None, R.D1_ENDE), "D2": (R.D1_ENDE, R.SPLIT), "Entwicklung": (None, R.SPLIT)}
out["kandidat"] = {f: {"sharpe": sharpe(teil(basis, *v)), "N": float(teil(basis, *v).sum())} for f, v in FEN.items()}
bd = teil(basis, None, R.SPLIT)
diffs, namen, faktor = [], [], {}
for n, x in reihen.items():
    xd = teil(x, None, R.SPLIT)
    faktor[n] = float(bd.std() / xd.std())
    e = {f: {"sharpe": sharpe(teil(x, *v)), "N": float(teil(x, *v).sum())} for f, v in FEN.items()}
    e["faktor"] = faktor[n]
    e["korrelation"] = float(np.corrcoef(bd, xd)[0, 1])
    e["ok1"] = bool(e["D1"]["sharpe"] > out["kandidat"]["D1"]["sharpe"] and e["D2"]["sharpe"] > out["kandidat"]["D2"]["sharpe"])
    out["varianten"][n] = e
    diffs.append((faktor[n] * xd - bd).to_numpy()); namen.append(n)
mittel, schwelle, p = M.reality_check(np.column_stack(diffs))
out["reality_check"] = {"schwelle_95": schwelle, "p_beste": p, "tage": int(len(bd))}
for n, mw in zip(namen, mittel):
    out["varianten"][n]["vorsprung_jahr"] = float(mw * 365)
    out["varianten"][n]["ok2"] = bool(mw > schwelle)
t = pd.DataFrame({n: {"S_D1": e["D1"]["sharpe"], "S_D2": e["D2"]["sharpe"], "S_Entw": e["Entwicklung"]["sharpe"], "Korr": e["korrelation"],
                      "Vorsprung/Jahr": e["vorsprung_jahr"], "Stufe1": e["ok1"], "Stufe2": e["ok2"]} for n, e in out["varianten"].items()}).T
print("Kandidat:", {f: round(v["sharpe"], 3) for f, v in out["kandidat"].items()})
print(t.to_string()); print("Reality Check:", {k: round(v, 5) for k, v in out["reality_check"].items()}, "Schwelle/Jahr", round(schwelle * 365, 4))
final = [n for n in namen if out["varianten"][n]["ok1"] and out["varianten"][n]["ok2"]]
out["finalisten"] = final
print("Finalisten:", final)
if final:
    out["stufe3"] = {}
    proben = {"A_Pruefung": (mA, R.SPLIT, None, basis)}
    for g in ("B", "C", "D"):
        mg = R.markt(G[g], vor=True)
        proben[g] = (mg, None, None, tage(mg, M.basis))
    mv = R.markt(G["A"], start=R.VOR_START, ende=R.VOR_ENDE, vor=True)
    proben["A_Vorperiode"] = (mv, None, None, tage(mv, M.basis))
    for n in final:
        e = out["stufe3"][n] = {}
        for pn, (m, von, bis, bs) in proben.items():
            x = reihen[n] if pn == "A_Pruefung" else tage(m, M.VARIANTEN[n])
            e[pn] = {"kandidat": sharpe(teil(bs, von, bis)), "variante": sharpe(teil(x, von, bis)),
                     "N_kandidat": float(teil(bs, von, bis).sum()), "N_variante_skaliert": float(teil(x, von, bis).sum() * faktor[n])}
            e[pn]["ok"] = bool(e[pn]["variante"] > e[pn]["kandidat"])
        e["ok3"] = bool(all(v["ok"] for v in e.values()))
        print(n, "Stufe 3:", e["ok3"]); print(pd.DataFrame({k: v for k, v in e.items() if k != "ok3"}).T.round(3).to_string())
    out["ausbau"] = [n for n in final if out["stufe3"][n]["ok3"]]
else:
    out["ausbau"] = []
print("\nAUSBAU DES VORTEILS:", out["ausbau"])
(ROOT / "reports/suche_runde21.json").write_text(json.dumps(out, indent=1, default=float))
print(f"fertig in {time.time() - t0:.0f} s")
