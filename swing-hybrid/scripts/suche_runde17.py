"""Runde 17: H1 verwandte Paare (Z-Wert), H2 Aktien-Momentum 12-1. Hürden laut Protokoll."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
import numpy as np
import pandas as pd
from hybrid import research as R, runner, tagestrend as T, tradfi_neutral as N

ROOT = Path(__file__).resolve().parents[1]
pd.set_option("display.width", 220)
FEN = {"D1": (None, R.D1_ENDE), "D2": (R.D1_ENDE, R.SPLIT), "Entwicklung": (None, R.SPLIT), "Pruefung": (R.SPLIT, None),
       "Gesamt": (None, None)}
REBATE, TAKER = runner.MIT.rebate, runner.TAKER
START = pd.Timestamp(R.START).normalize()
kal = pd.date_range(START, pd.Timestamp(R.ENDE).normalize() - pd.Timedelta(days=1), freq="D")
k14 = json.loads((ROOT / "reports/runde14_kosten.json").read_text())
slip14 = lambda n: max(0.00005, k14[n]["spanne_bp"] / 1e4)
lesen = lambda n: pd.read_parquet(ROOT / f"data/candles/tradfi_1d/{n}.parquet")
fen = lambda tag: {k: T.kennzahlen(tag, *v) for k, v in FEN.items()}
tab = lambda d: pd.DataFrame(d).T[["N", "jahr_N", "dd", "sharpe"]].round(3).to_string()

mA = R.markt(R.GRUPPE_A)
kr = R.lauf(mA, R.auf_raster(mA, R.variante(mA, "basis")), taker=True, slip=R.yubit_kosten(R.GRUPPE_A)[0],
            day_limit=9.0).daily_pnl(runner.MIT).sum(axis=1).reindex(kal).fillna(0.0)
out = {"kandidat_A": fen(kr)}
print("Kandidat Gruppe A:"); print(tab(out["kandidat_A"]))


def werten(name, teile):
    """teile: Liste von Tages-Tabellen (brutto, slip, umsatz, gehalten)."""
    summe = lambda **kw: sum(N.netto(t, kal, TAKER, **kw) for t in teile)
    h = {"vor_kosten": fen(sum(t["brutto"].reindex(kal).fillna(0.0) for t in teile)),
         "netto": fen(summe(rebate=REBATE)), "ohne_rebate": fen(summe(rebate=0.0)),
         "stress": fen(summe(rebate=REBATE, slip_faktor=2.0, funding_jahr=0.10))}
    n = summe(rebate=REBATE)
    h["mischung"] = fen(0.5 * kr + 0.5 * n)
    h["korrelation_tag"] = float(np.corrcoef(kr, n)[0, 1])
    h["umsatz_tag"] = float(sum(t["umsatz"].sum() for t in teile) / len(kal))
    h["ok1"] = bool(all(h["netto"][f]["N"] > 0 for f in ("D1", "D2", "Pruefung")))
    h["ok2"] = bool(all(h["stress"][f]["N"] > 0 for f in ("Entwicklung", "Pruefung")))
    h["ok3"] = bool(all(h["mischung"][f]["sharpe"] > out["kandidat_A"][f]["sharpe"] for f in ("Entwicklung", "Pruefung")))
    for k, t in (("vor Kosten", "vor_kosten"), ("netto mit Rebate", "netto"), ("ohne Rebate", "ohne_rebate"), ("Stress", "stress"),
                 ("Mischung mit Kandidat", "mischung")):
        print(f"\n{name}, {k}:"); print(tab(h[t]))
    print(f"{name} Hürden 1/2/3:", h["ok1"], h["ok2"], h["ok3"], "| Korrelation:", round(h["korrelation_tag"], 3),
          "| Umsatz/Tag:", round(h["umsatz_tag"], 3))
    return h


PAARE = [("XAU", "XAG"), ("XPT", "XPD"), ("SPY", "QQQ"), ("SPY", "IWM")]
teile = [N.paar(lesen(a), lesen(b), 1.0 / len(PAARE), slip14(a), slip14(b), START) for a, b in PAARE]
out["H1"] = werten("H1 Paare", teile)
out["H1"]["je_paar"] = {f"{a}/{b}": {f: T.kennzahlen(N.netto(t, kal, TAKER, rebate=REBATE), *FEN[f])["N"] for f in ("Entwicklung", "Pruefung")}
                        for (a, b), t in zip(PAARE, teile)}
print(pd.DataFrame(out["H1"]["je_paar"]).T.round(4).to_string())

info = json.loads((ROOT / "reports/runde17_aktien.json").read_text())
titel = sorted(k for k, v in info.items() if v["ok"])
close = pd.DataFrame({k: pd.read_parquet(ROOT / f"data/candles/aktien_1d/{k}.parquet")["close"] for k in titel})
close = close[close.index <= kal[-1]]
gemessen = pd.Series({k: info[k]["spanne_bp"] for k in titel}, dtype=float)
slip = (gemessen.fillna(gemessen.median()) / 1e4).clip(lower=0.00005)
out["H2_titel"] = {"anzahl": len(titel), "spanne_median_bp": float(gemessen.median()), "ohne_messwert": int(gemessen.isna().sum())}
print("\nAktien:", out["H2_titel"])
out["H2"] = werten("H2 Aktien-Momentum", [N.momentum(close, slip, START)])
(ROOT / "reports/suche_runde17.json").write_text(json.dumps(out, indent=1, default=float))
