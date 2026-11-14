"""Runde 10: neue Listings short gegen BTC long. Eine Hypothese, eine Einstellung. Hürden laut Protokoll."""
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
import numpy as np
import pandas as pd
from hybrid import listings as L
from hybrid.config import DATA

ROOT = Path(__file__).resolve().parents[1]
pd.set_option("display.width", 250, "display.max_columns", 40, "display.max_rows", 80)
NEU_AB, WARTEN, HALTEN = pd.Timestamp("2021-09-01"), 7, 90
D1_ENDE, SPLIT, ENDE = "2023-07-01", "2025-04-01", pd.Timestamp("2026-10-24")
SLIP_COIN, SLIP_BTC = 0.0015, 0.00005
HEBEL = (5, 4, 3, 2.5, 2, 1.5, 1, 0.75, 0.5, 0.4, 0.35, 0.3, 0.25, 0.2, 0.15, 0.1)
AUSSCHLUSS = set((ROOT / "scripts/listings_ausschluss.txt").read_text().split())   # Aktien, Rohstoffe, Indizes (nur nach Namen)
SP = ["G", "funding", "F", "R", "handel", "N", "dd_mit", "jahr_N", "sharpe", "offen_mittel", "offen_max", "einsatz_max"]


def lade(sym):
    k = pd.read_parquet(DATA / "candles/1d" / f"{sym}.parquet")["close"]
    k = k[k.index < ENDE]
    p = DATA / "candles/funding_1d" / f"{sym}.parquet"
    f = pd.read_parquet(p)["rate"] if p.exists() else pd.Series(dtype=float)
    return k, f


def laufe(paare_def, slip_coin=SLIP_COIN):
    """paare_def: Liste (name, kursreihe, fundingreihe, einstieg)."""
    out = {}
    for name, k, f, e in paare_def:
        p = L.paar(k, BTC, f, FBTC, e, HALTEN, slip_coin, SLIP_BTC)
        if p is not None:
            out[name] = p
    return out


def drei(pf, h=1.0):
    return {"D1": L.fenster(pf, None, D1_ENDE, h), "D2": L.fenster(pf, D1_ENDE, SPLIT, h),
            "Entwicklung": L.fenster(pf, None, SPLIT, h), "Pruefung": L.fenster(pf, SPLIT, None, h), "Gesamt": L.fenster(pf, None, None, h)}


def tab(d):
    return pd.DataFrame(d).T[SP].round(3).to_string()


t0 = time.time()
inv = pd.read_csv(DATA / "processed/listings_inventur.csv", parse_dates=["erster_tag", "letzter_tag"])
inv = inv[~inv["symbol"].isin(AUSSCHLUSS)]
BTC, FBTC = lade("BTCUSDT")
INDEX = BTC.index[BTC.index >= NEU_AB]
neu = inv[(inv["erster_tag"] >= NEU_AB) & (inv["symbol"] != "BTCUSDT")].sort_values("erster_tag")
alt = inv[(inv["erster_tag"] < NEU_AB) & (inv["symbol"] != "BTCUSDT")]
DATEN = {s: lade(s) for s in list(neu["symbol"]) + list(alt["symbol"])}
defs = [(s, *DATEN[s], e + pd.Timedelta(days=WARTEN)) for s, e in zip(neu["symbol"], neu["erster_tag"])]
print(f"{len(neu)} neue Listings seit {NEU_AB.date()} (je Jahr: {neu['erster_tag'].dt.year.value_counts().sort_index().to_dict()}), "
      f"{len(alt)} alte Coins für das Placebo")

paare = laufe(defs)
pf = L.portfolio(paare, INDEX)
basis = drei(pf)
out = {"neu": int(len(neu)), "alt": int(len(alt)), "paare": int(len(paare)), "hebel1": basis}
print(f"{len(paare)} Paare gerechnet. Portfolio bei Hebel 1 (je Paar 5 % je Seite):"); print(tab(basis))

# Paar-Statistik
pt = pd.DataFrame([{"symbol": n, "einstieg": p["einstieg"], "ausstieg": p["ausstieg"], "grund": p["grund"], "ergebnis": p["ergebnis"],
                    "coin": p["coin_rendite"], "btc": p["btc_rendite"], "funding": float(p["funding"].sum())} for n, p in paare.items()])
pt.to_csv(ROOT / "reports/suche_runde10_paare.csv", index=False)
def stat(x):
    n = len(x)
    return {"paare": n, "mittel": float(x["ergebnis"].mean()), "median": float(x["ergebnis"].median()),
            "gewinner": float((x["ergebnis"] > 0).mean()), "t": float(x["ergebnis"].mean() / x["ergebnis"].std() * np.sqrt(n)) if n > 2 else float("nan"),
            "stops": int((x["grund"] == "stop").sum()), "coin_mittel": float(x["coin"].mean()), "btc_mittel": float(x["btc"].mean()),
            "funding_mittel": float(x["funding"].mean())}
out["paar_statistik"] = {"alle": stat(pt), "entwicklung": stat(pt[pt["einstieg"] < SPLIT]), "pruefung": stat(pt[pt["einstieg"] >= SPLIT]),
                         "je_jahr": {str(j): stat(g) for j, g in pt.groupby(pt["einstieg"].dt.year)}}
print("Paare:", json.dumps({k: {a: round(b, 3) for a, b in v.items()} for k, v in out["paar_statistik"].items() if k != "je_jahr"}))
print(pd.DataFrame(out["paar_statistik"]["je_jahr"]).T.round(3).to_string())

# ---- Hürden
ok1 = all(basis[f]["G"] > 0 and basis[f]["N"] > 0 for f in ("D1", "D2"))
stress = drei(L.portfolio(laufe(defs, 0.005), INDEX))
ok2 = all(stress[f]["N"] > 0 for f in ("D1", "D2"))
sp = out["paar_statistik"]["pruefung"]
ok3 = basis["Pruefung"]["G"] > 0 and basis["Pruefung"]["N"] > 0 and sp["mittel"] > 0 and sp["t"] >= 2
rng = np.random.default_rng(7)
alte = list(alt["symbol"])
echt = basis["Gesamt"]["N"]
plac = []
for _ in range(200):
    d = [(f"{n}_{i}", *DATEN[alte[int(rng.integers(len(alte)))]], e) for i, (n, _, _, e) in enumerate(defs)]
    plac.append(L.fenster(L.portfolio(laufe(d), INDEX))["N"])
pct = float((np.array(plac) < echt).mean() * 100)
ok4 = pct >= 90
dd1 = basis["Entwicklung"]["dd_mit"]
h = next((x for x in HEBEL if dd1 * x <= 0.10 and basis["Gesamt"]["einsatz_max"] * x <= 5), None)
mit_h = drei(pf, h) if h else None
ok5 = bool(h) and mit_h["Pruefung"]["dd_mit"] < 0.15
gut = bool(ok1 and ok2 and ok3 and ok4 and ok5 and mit_h["Pruefung"]["jahr_N"] >= 0.10)
print(f"\nStufe 1 Entwicklung: {'bestanden' if ok1 else 'DURCHGEFALLEN'}")
print(f"Stufe 2 Slippage 0,5 %: {'bestanden' if ok2 else 'DURCHGEFALLEN'} (D1 N {stress['D1']['N']:.3f}, D2 N {stress['D2']['N']:.3f}, Prüfung N {stress['Pruefung']['N']:.3f})")
print(f"Stufe 3 Prüfzeitraum: {'bestanden' if ok3 else 'DURCHGEFALLEN'} (G {basis['Pruefung']['G']:.3f}, N {basis['Pruefung']['N']:.3f}, Paare {sp['paare']}, Mittel {sp['mittel']:.3f}, t {sp['t']:.2f})")
print(f"Stufe 4 Placebo: Perzentil {pct:.1f} ({'bestanden' if ok4 else 'DURCHGEFALLEN'}); echt {echt:.3f}, Placebo Median {np.median(plac):.3f}, 90 % {np.percentile(plac, 90):.3f}, Max {np.max(plac):.3f}")
print(f"Stufe 5 Hebel {h}: {'bestanden' if ok5 else 'DURCHGEFALLEN'}")
if h:
    print(tab(mit_h))
    j = (pf[["brutto", "funding", "gebuehr", "rebate", "netto_ohne", "netto_mit"]] * h).groupby(pf.index.year).sum()
    print(j.round(3).to_string())
    out["jahre"] = {str(i): x for i, x in j.round(5).T.to_dict().items()}
out.update({"stufen": {"1": ok1, "2": ok2, "3": ok3, "4": ok4, "5": ok5}, "stress": stress, "placebo": {"perzentil": pct, "echt": echt,
            "median": float(np.median(plac)), "p90": float(np.percentile(plac, 90)), "max": float(np.max(plac))},
            "hebel": h, "mit_hebel": mit_h, "wirklich_gut": gut})
print("\nWIRKLICH GUT (alle Hürden und mindestens 10 % pro Jahr im Prüfzeitraum):", gut)
(ROOT / "reports/suche_runde10.json").write_text(json.dumps(out, indent=1, default=float))
print(f"fertig in {time.time() - t0:.0f} s")
