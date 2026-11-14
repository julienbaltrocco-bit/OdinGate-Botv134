"""Runde 9: Kandidat auf den jeweils 20 umsatzstärksten Coins (Auswahl monatlich, nur aus damals bekannten Daten)."""
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
N_TOP = 20
G = json.loads((ROOT / "reports/suche_runde6.json").read_text())["gruppen"]
alle = G["A"] + G["B"] + G["C"] + G["D"]
m = R.markt(alle)
kosten = R.yubit_kosten(alle)[0]


def auswahl(m) -> pd.DataFrame:
    """1.0 für die 20 umsatzstärksten Coins der letzten 30 Tage, gewählt zu Monatsbeginn aus Daten bis zur Vorstunde."""
    umsatz = pd.DataFrame({c: m.h1[c]["quote_volume"] for c in m.coins}).rolling(720, min_periods=360).sum().shift(1)
    rang = umsatz.rank(axis=1, ascending=False)
    wahl = (rang <= N_TOP).astype(float)
    wahl[umsatz.isna()] = 0.0
    monatsbeginn = (wahl.index.day == 1) & (wahl.index.hour == 0)
    monatsbeginn[0] = True                                   # erste Wahl sofort, danach nur zu Monatsbeginn
    wahl[~monatsbeginn] = np.nan
    return wahl.ffill().fillna(0.0)


def fen(l):
    return {k: R.sicht(l, *FEN[k]) for k in FEN}


wahl = auswahl(m)
assert (wahl.sum(axis=1).iloc[800:] == N_TOP).all(), "es müssen immer genau 20 Coins gewählt sein"
w = R.auf_raster(m, R.variante(m, "basis") * wahl)
skala = len(alle) / N_TOP                                    # Positionsgröße je Coin = Hebel / 20
for h in HEBEL:
    l = R.lauf(m, w, hebel=h * skala, taker=True, slip=kosten)
    if R.sicht(l, *FEN["Entwicklung"])["dd_mit"] <= 0.10:
        break
j = {}
for nm, fees in (("G", runner.BRUTTO), ("ohne", runner.OHNE), ("N", runner.MIT)):
    tg = l.daily_pnl(fees).sum(axis=1)
    j[nm] = tg.groupby(tg.index.year).sum()
j = pd.DataFrame(j); j["R"] = j["N"] - j["ohne"]
haeufig = (wahl.mean().sort_values(ascending=False) * 100).round(0)
tg = l.daily_pnl(runner.MIT)
pruef = tg[tg.index >= pd.Timestamp(R.SPLIT)].sum().sort_values(ascending=False)
out = {"hebel": h, **fen(l), "stress_2x": fen(R.lauf(m, w, hebel=h * skala, taker=True, slip=2 * kosten)),
       "alt_5bp": fen(R.lauf(m, w, hebel=h * skala, taker=True, slip=0.0005)), "orders": runner.order_statistik(l),
       "jahre": {str(i): x for i, x in j.round(5).T.to_dict().items()},
       "anteil_gewaehlt_pct": haeufig.to_dict(), "wechsel_je_monat": float((wahl.diff().abs().sum(axis=1) / 2)[wahl.index.day == 1].mean()),
       "pruefung_je_coin_top": pruef.head(5).round(4).to_dict(), "pruefung_je_coin_flop": pruef.tail(5).round(4).to_dict(),
       "tage": {"Pruefung": (m.index[-1] - pd.Timestamp(R.SPLIT)).days + 1, "Gesamt": (m.index[-1] - m.index[0]).days + 1}}
r8 = json.loads((ROOT / "reports/suche_runde8.json").read_text())["A"]
out["besser"] = bool(out["Entwicklung"]["N"] > r8["Entwicklung"]["N"] and out["Pruefung"]["N"] > r8["Pruefung"]["N"]
                     and out["stress_2x"]["Pruefung"]["N"] > 0)
print(f"Hebel {h}; immer 20 von {len(alle)} Coins; im Mittel {out['wechsel_je_monat']:.1f} Wechsel je Monat")
print(pd.DataFrame({k: out[k] for k in FEN}).T[SP].round(3).to_string())
print("doppelte Kosten: Entwicklung N", round(out["stress_2x"]["Entwicklung"]["N"], 4), "Prüfung N", round(out["stress_2x"]["Pruefung"]["N"], 4),
      "| alt 0,05 %: Prüfung N", round(out["alt_5bp"]["Pruefung"]["N"], 4))
print(j.round(3).to_string())
print("Prüfzeitraum, größte Beiträge je Coin:", out["pruefung_je_coin_top"])
print("Prüfzeitraum, kleinste Beiträge je Coin:", out["pruefung_je_coin_flop"])
print("Am häufigsten gewählt (% der Zeit):", dict(list(haeufig.items())[:24]))
print(f"Maßstab Gruppe A: Entwicklung {r8['Entwicklung']['N']:.4f}, Prüfung {r8['Pruefung']['N']:.4f} | BESSER: {out['besser']}")
(ROOT / "reports/suche_runde9.json").write_text(json.dumps(out, indent=1, default=float))
