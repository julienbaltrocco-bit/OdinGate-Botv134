"""Runde 4: Bestätigung des Kandidaten auf frischen Daten (Gruppe C, Vorperiode) und breites Portfolio. Keine Auswahl."""
import json
import re
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
import numpy as np
import pandas as pd
from hybrid import research as R, runner
from hybrid.config import DATA

ROOT = Path(__file__).resolve().parents[1]
pd.set_option("display.width", 260, "display.max_columns", 60)
L, AUS = 336, 9.0
LISTE_C = ("XMR ZEC DASH ALGO VET THETA EGLD SUSHI COMP SNX CRV 1INCH GRT SAND MANA AXS CHZ ENJ KSM ZIL IOTA NEO ONT QTUM "
           "XTZ RUNE KAVA BAT ZRX YFI HBAR ICP").split()
SP = ["G", "F", "R", "handel", "N", "dd_mit", "vol_tag", "bp_je_umsatz", "trades", "sharpe", "jahr_N"]
FEN = {"Entwicklung": (None, R.SPLIT), "Pruefung": (R.SPLIT, None), "Gesamt": (None, None)}


def vollstaendig(coin):
    log = (DATA / "candles/download3.log").read_text()
    return all(re.search(rf"^{art} {coin}USDT: .*fehlende Monate: keine$", log, re.M) for art in ("5m", "funding"))


def tab(d):
    return pd.DataFrame(d).T[SP].round(3).to_string()


def drei(l):
    return {k: R.sicht(l, *FEN[k]) for k in FEN}


t0 = time.time()
ok_c = [c for c in LISTE_C if vollstaendig(c)]
C = ok_c[:20]
out = {"gruppe_c": C, "nicht_vollstaendig": [c for c in LISTE_C if c not in ok_c]}
print("Gruppe C:", C, "| unvollständig:", out["nicht_vollstaendig"])

# ---- 1) Gruppe C, Hauptzeitraum
mC = R.markt(C)
wC = R.auf_raster(mC, R.tsmom(mC, L))
c_sofort = drei(R.lauf(mC, wC, taker=True, day_limit=AUS))
c_passiv = drei(R.lauf(mC, wC, day_limit=AUS))
out["C_sofort"], out["C_passiv"] = c_sofort, c_passiv
print("Gruppe C, sofortige Ausführung (Hebel 1, ohne Tageslimit):"); print(tab(c_sofort))
print("Gruppe C, passiv:"); print(tab(c_passiv))

# ---- 2) Vorperiode
vor = {}
alle = R.GRUPPE_A + R.GRUPPE_B + C
for nm, coins in (("A", R.GRUPPE_A), ("B", R.GRUPPE_B), ("C", C), ("alle", alle)):
    coins = [c for c in coins if (DATA / "candles/5m_vor" / f"{c}USDT.parquet").exists()]
    m = R.markt(coins, R.VOR_START, R.VOR_ENDE, vor=True)
    w = R.auf_raster(m, R.tsmom(m, L))
    vor[nm] = {"coins": len(coins), **R.sicht(R.lauf(m, w, taker=True, day_limit=AUS), None, None)}
out["vorperiode"] = vor
print("Vorperiode 02/2020–08/2021 (Hebel 1, ohne Tageslimit):")
print(pd.DataFrame(vor).T[["coins"] + SP].round(3).to_string())
best = c_sofort["Entwicklung"]["N"] > 0 and c_sofort["Pruefung"]["N"] > 0 and vor["alle"]["N"] > 0
out["bestaetigt"] = bool(best)
print("BESTÄTIGT:", best)

# ---- 3) Breites Portfolio
mX = R.markt(alle)
wX = R.auf_raster(mX, R.tsmom(mX, L))
x1 = drei(R.lauf(mX, wX, taker=True, day_limit=AUS))
out["breit_hebel1"] = x1
print(f"Breites Portfolio ({len(alle)} Coins), Hebel 1 ohne Tageslimit:"); print(tab(x1))
gew, lh = None, None
for h in (5, 4, 3, 2.5, 2, 1.5, 1, 0.75, 0.5, 0.4, 0.3, 0.25, 0.2, 0.15, 0.1):
    l = R.lauf(mX, wX, hebel=h, taker=True)
    if R.sicht(l, *FEN["Entwicklung"])["dd_mit"] <= 0.10:
        gew, lh = h, l
        break
out["breit_hebel"] = gew
if gew is not None:
    xh = drei(lh)
    out["breit"] = xh
    out["breit_orders"] = runner.order_statistik(lh)
    print(f"Breites Portfolio, Hebel {gew} mit Tageslimit 3 %:"); print(tab(xh)); print("  ", out["breit_orders"])
    jahre = {}
    for nm, fees in (("G", runner.BRUTTO), ("ohne", runner.OHNE), ("N", runner.MIT)):
        tg = lh.daily_pnl(fees).sum(axis=1)
        jahre[nm] = tg.groupby(tg.index.year).sum()
    j = pd.DataFrame(jahre); j["R"] = j["N"] - j["ohne"]
    out["breit_jahre"] = {str(k): v for k, v in j.round(5).T.to_dict().items()}
    print(j.round(3).to_string())
    out["breit_slippage"] = {}
    for bp in (0, 2.5, 5, 7.5, 10):
        s = R.sicht(R.lauf(mX, wX, hebel=gew, taker=True, slip=bp / 1e4), *FEN["Pruefung"])
        out["breit_slippage"][str(bp)] = {"G": s["G"], "N": s["N"]}
    print("Slippage Prüfzeitraum:", {k: round(v["N"], 3) for k, v in out["breit_slippage"].items()})
    out["tage"] = {"Pruefung": (mX.index[-1] - pd.Timestamp(R.SPLIT)).days + 1, "Gesamt": (mX.index[-1] - mX.index[0]).days + 1}
# Zufallstest nur im Prüfzeitraum, breites Portfolio
rng = np.random.default_rng(13)
echt = x1["Pruefung"]["N"]
T = wX.shape[1]
z = [R.sicht(R.lauf(mX, np.ascontiguousarray(np.roll(wX, int(rng.integers(288 * 30, T - 288 * 30)), axis=1)), taker=True, day_limit=AUS),
             R.SPLIT, None)["N"] for _ in range(200)]
out["breit_zufall_pruefung"] = {"perzentil": float((np.array(z) < echt).mean() * 100), "echt": echt, "median": float(np.median(z)),
                                "p90": float(np.percentile(z, 90))}
print("Zufallstest Prüfzeitraum, breites Portfolio:", out["breit_zufall_pruefung"])
(ROOT / "reports/suche_runde4.json").write_text(json.dumps(out, indent=1, default=float))
print(f"fertig in {time.time() - t0:.0f} s")
