"""Runde 16: H1 Übernacht-Effekt auf SPY/QQQ/IWM, H2 Kandidat mit QQQ-Risiko-Filter. Hürden laut Protokoll."""
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
REBATE, TAKER = runner.MIT.rebate, runner.TAKER
kosten = json.loads((ROOT / "reports/runde14_kosten.json").read_text())
kal = pd.date_range(pd.Timestamp(R.START).normalize(), pd.Timestamp(R.ENDE).normalize() - pd.Timedelta(days=1), freq="D")
lesen = lambda n: pd.read_parquet(ROOT / f"data/candles/tradfi_1d/{n}.parquet")


def fen(tag):
    return {k: T.kennzahlen(tag, *v) for k, v in FEN.items()}


def tab(d):
    return pd.DataFrame(d).T[["N", "jahr_N", "dd", "sharpe"]].round(3).to_string()


def uebernacht(slip_faktor=1.0, rebate=REBATE, funding_jahr=0.0):
    teile = {}
    for n in ("SPY", "QQQ", "IWM"):
        d = lesen(n)
        slip = slip_faktor * max(0.00005, kosten[n]["spanne_bp"] / 1e4)
        roh = d["open"] / d["close"].shift(1) - 1
        naechte = pd.Series(np.diff(d.index.to_numpy(), prepend=d.index.to_numpy()[:1]).astype("timedelta64[D]").astype(float), index=d.index)
        halte_tage = naechte - 6.5 / 24                      # Kalendertage von Schluss bis Eröffnung
        netto = roh - 2 * slip - 2 * TAKER * (1 - rebate) - funding_jahr / 365 * halte_tage
        teile[n] = pd.DataFrame({"roh": roh, "netto": netto}).iloc[1:]
    roh = pd.DataFrame({n: t["roh"] for n, t in teile.items()}).reindex(kal).fillna(0.0).mean(axis=1)
    netto = pd.DataFrame({n: t["netto"] for n, t in teile.items()}).reindex(kal).fillna(0.0).mean(axis=1)
    return roh, netto


out = {"H1": {}, "H2": {}}
# ---------------------------------------------------------------- Kandidat als Maßstab ----
def kandidat_lauf(coins, filt=None):
    m = R.markt(coins)
    sig = R.variante(m, "basis")
    if filt is not None:
        q = filt.reindex(sig.index.normalize()).to_numpy()
        sig = sig.where(np.sign(sig).to_numpy() == q[:, None], 0.0)
    l = R.lauf(m, R.auf_raster(m, sig), taker=True, slip=R.yubit_kosten(coins)[0], day_limit=9.0)
    return l.daily_pnl(runner.MIT).sum(axis=1).reindex(kal).fillna(0.0)


krA = kandidat_lauf(R.GRUPPE_A)
out["kandidat_A"] = fen(krA)
print("Kandidat Gruppe A:"); print(tab(out["kandidat_A"]))

# ------------------------------------------------------------------------------- H1 ----
roh, n1 = uebernacht()
h = out["H1"]
h["vor_kosten"] = fen(roh); h["netto"] = fen(n1); h["ohne_rebate"] = fen(uebernacht(rebate=0.0)[1])
h["stress"] = fen(uebernacht(slip_faktor=2.0, funding_jahr=0.10)[1])
mix = 0.5 * krA + 0.5 * n1
h["mischung"] = fen(mix)
h["korrelation_tag"] = float(np.corrcoef(krA, n1)[0, 1])
h["ok1"] = bool(all(h["netto"][f]["N"] > 0 for f in ("D1", "D2", "Pruefung")))
h["ok2"] = bool(all(h["stress"][f]["N"] > 0 for f in ("Entwicklung", "Pruefung")))
h["ok3"] = bool(all(h["mischung"][f]["sharpe"] > out["kandidat_A"][f]["sharpe"] for f in ("Entwicklung", "Pruefung")))
for k, t in (("vor Kosten", "vor_kosten"), ("netto mit Rebate", "netto"), ("ohne Rebate", "ohne_rebate"), ("Stress", "stress"),
             ("Mischung mit Kandidat", "mischung")):
    print(f"\nH1 Übernacht, {k}:"); print(tab(h[t]))
print("H1 Hürden 1/2/3:", h["ok1"], h["ok2"], h["ok3"], "| Korrelation:", round(h["korrelation_tag"], 3))

# ------------------------------------------------------------------------------- H2 ----
q = T.signal(lesen("QQQ")["close"])
q.index = q.index + pd.Timedelta(days=1)                      # nach US-Schluss bekannt, gilt ab dem nächsten UTC-Tag
voll = pd.date_range(q.index[0], kal[-1], freq="D")
qd = q.reindex(voll).ffill()
g = out["H2"]
fA = kandidat_lauf(R.GRUPPE_A, qd)
g["A"] = fen(fA)
print("\nH2 Kandidat mit QQQ-Filter, Gruppe A:"); print(tab(g["A"]))
g["ok1"] = bool(all(g["A"][f]["N"] > 0 and g["A"][f]["sharpe"] > out["kandidat_A"][f]["sharpe"] for f in ("D1", "D2", "Pruefung")))
print("H2 Hürde 1:", g["ok1"])
if g["ok1"]:
    rng = np.random.default_rng(16)
    echt = g["A"]["Gesamt"]["sharpe"]
    werte = qd.to_numpy()
    z = []
    for _ in range(200):
        s = pd.Series(np.roll(werte, int(rng.integers(30, len(werte) - 30))), index=voll)
        z.append(T.kennzahlen(kandidat_lauf(R.GRUPPE_A, s))["sharpe"])
    g["zufall"] = {"perzentil": float((np.array(z) < echt).mean() * 100), "echt": echt, "median": float(np.median(z))}
    g["ok2"] = g["zufall"]["perzentil"] >= 90
    print("H2 Hürde 2 Zufallstest:", g["zufall"], g["ok2"])
    if g["ok2"]:
        krB = kandidat_lauf(R.GRUPPE_B); fB = kandidat_lauf(R.GRUPPE_B, qd)
        g["kandidat_B"] = fen(krB); g["B"] = fen(fB)
        g["ok3"] = bool(all(g["B"][f]["sharpe"] > g["kandidat_B"][f]["sharpe"] for f in ("Entwicklung", "Pruefung")))
        print("Gruppe B Kandidat:"); print(tab(g["kandidat_B"])); print("Gruppe B mit Filter:"); print(tab(g["B"]))
        print("H2 Hürde 3:", g["ok3"])
(ROOT / "reports/suche_runde16.json").write_text(json.dumps(out, indent=1, default=float))
