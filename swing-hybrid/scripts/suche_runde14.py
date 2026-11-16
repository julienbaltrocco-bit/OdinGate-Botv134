"""Runde 14: der unveränderte 14-Tage-Trend auf 14 Nicht-Krypto-Märkten, allein und gemischt mit dem Kandidaten."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
import numpy as np
import pandas as pd
from hybrid import research as R, runner, tagestrend as T

ROOT = Path(__file__).resolve().parents[1]
pd.set_option("display.width", 220)
FEN = {"D1": (None, R.D1_ENDE), "D2": (R.D1_ENDE, R.SPLIT), "Entwicklung": (None, R.SPLIT), "Pruefung": (R.SPLIT, None),
       "Gesamt": (None, None)}
REBATE = runner.MIT.rebate
kosten = json.loads((ROOT / "reports/runde14_kosten.json").read_text())
namen = [n for n in kosten if not n.startswith("_")]
kurse = {n: pd.read_parquet(ROOT / f"data/candles/tradfi_1d/{n}.parquet") for n in namen}
slip = {n: max(0.00005, kosten[n]["spanne_bp"] / 1e4) for n in namen}
kal = pd.date_range(pd.Timestamp(R.START).normalize(), pd.Timestamp(R.ENDE).normalize() - pd.Timedelta(days=1), freq="D")


def fen(tag):
    return {k: T.kennzahlen(tag, *v) for k, v in FEN.items()}


def tab(d):
    return pd.DataFrame(d).T[["N", "jahr_N", "dd", "sharpe"]].round(3).to_string()


out = {"maerkte": namen, "slip": slip}
TAGE = int(sys.argv[1]) if len(sys.argv) > 1 else 14
AUS = "suche_runde14.json" if TAGE == 14 else "suche_runde15.json"
l = T.lauf(kurse, kal, slip, runner.TAKER, tage=TAGE)
nt = T.netto(l, REBATE)
tr = nt.sum(axis=1)
out["tradfi"] = fen(tr)
out["tradfi_brutto"] = fen(pd.DataFrame({n: t["brutto"] for n, t in l.items()}).sum(axis=1))
out["tradfi_ohne_rebate"] = fen(T.netto(l, 0.0).sum(axis=1))
out["umsatz_tag"] = float(sum(t["umsatz"].sum() for t in l.values()) / len(kal))
print("Nicht-Krypto-Trend allein, netto mit Rebate, Funding 0:"); print(tab(out["tradfi"]))
ok1 = all(out["tradfi"][f]["N"] > 0 for f in ("D1", "D2", "Pruefung"))
print("Hürde 1:", "bestanden" if ok1 else "DURCHGEFALLEN")

ls = T.lauf(kurse, kal, {n: 2 * s for n, s in slip.items()}, 2 * runner.TAKER, funding_jahr=0.10, tage=TAGE)
out["tradfi_stress"] = fen(T.netto(ls, REBATE).sum(axis=1))
print("Stress (doppelte Kosten, 10 % Funding pro Jahr gegen jede Position):"); print(tab(out["tradfi_stress"]))
ok2 = all(out["tradfi_stress"][f]["N"] > 0 for f in ("Entwicklung", "Pruefung"))
print("Hürde 2:", "bestanden" if ok2 else "DURCHGEFALLEN")

mA = R.markt(R.GRUPPE_A)
lk = R.lauf(mA, R.auf_raster(mA, R.variante(mA, "basis")), taker=True, slip=R.yubit_kosten(R.GRUPPE_A)[0], day_limit=9.0)
kr = lk.daily_pnl(runner.MIT).sum(axis=1).reindex(kal).fillna(0.0)
mix = 0.5 * kr + 0.5 * tr
out["kandidat"] = fen(kr)
out["mischung"] = fen(mix)
out["korrelation_tag"] = float(np.corrcoef(kr, tr)[0, 1])
m = pd.DataFrame({"k": kr, "t": tr}).resample("ME").sum()
out["korrelation_monat"] = float(m.corr().iloc[0, 1])
print("Kandidat (Krypto-Trend, Gruppe A, Einsatz 100 %):"); print(tab(out["kandidat"]))
print("Mischung je zur Hälfte, gleicher Gesamteinsatz:"); print(tab(out["mischung"]))
print("Korrelation Tag / Monat:", round(out["korrelation_tag"], 3), round(out["korrelation_monat"], 3))
ok3 = all(out["mischung"][f]["N"] > out["kandidat"][f]["N"] and out["mischung"][f]["sharpe"] > out["kandidat"][f]["sharpe"]
          for f in ("Entwicklung", "Pruefung"))
out["sharpe_hoeher"] = bool(all(out["mischung"][f]["sharpe"] > out["kandidat"][f]["sharpe"] for f in ("Entwicklung", "Pruefung")))
print("Hürde 3 (mehr Netto UND höherer Sharpe in beiden Zeiträumen):", "bestanden" if ok3 else "DURCHGEFALLEN",
      "| nur Sharpe höher:", out["sharpe_hoeher"])
out["huerden"] = {"1": bool(ok1), "2": bool(ok2), "3": bool(ok3)}
je = pd.DataFrame({f: {n: T.kennzahlen(nt[n], *FEN[f])["N"] for n in namen} for f in ("Entwicklung", "Pruefung")})
out["je_markt"] = je.to_dict()
print((je * 100).round(2).to_string())
j = pd.DataFrame({"krypto": kr, "tradfi": tr, "mischung": mix}); j = j.groupby(j.index.year).sum()
out["jahre"] = j.to_dict()
print((j * 100).round(1).to_string())
(ROOT / "reports" / AUS).write_text(json.dumps(out, indent=1, default=float))
