"""RSK 06: Funding als Risiko des Kandidaten. Binance-Funding (Forschungsgrundlage), Positionen aus dem Lauf in s01.
Vorzeichen: positive Rate = Long zahlt an Short. Kosten in Einheiten des Startkapitals bei Hebel 1 (Hebel 3 = dreifach)."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import numpy as np
import pandas as pd
from rsk_common import A, R, SCRATCH

OUT = {}
HOCH = 0.0003            # 0,03 % je Abrechnung = Dreifaches des Regelsatzes von 0,01 %; dieselbe Schwelle wie mutationen.funding_filter

alle = []
for name in ("vor", "haupt"):
    d = np.load(SCRATCH / f"lauf_{name}.npz")
    idx = pd.DatetimeIndex(d["index"])
    pos, o, fund, fu, nc = d["pos"], d["o"], d["fund"], d["fu_coin"], d["netto_coin"]
    fen = {"Vorperiode": (0, len(idx))} if name == "vor" else {"Entwicklung": (0, int(idx.searchsorted(pd.Timestamp(R.SPLIT)))),
                                                               "Pruefzeitraum": (int(idx.searchsorted(pd.Timestamp(R.SPLIT))), len(idx))}
    # Abrechnungen: Kerzen mit Rate != 0; Position VOR dem Handel dieser Kerze = pos[t-1]
    for j, coin in enumerate(A):
        t = np.flatnonzero(fund[j] != 0.0)
        t = t[t > 0]
        q = pos[j, t - 1]
        zahl = -q * o[j, t] * fund[j, t]                     # > 0 erhalten, < 0 gezahlt (Einheiten des Startkapitals, Hebel 1)
        alle.append(pd.DataFrame({"lauf": name, "coin": coin, "zeit": idx[t], "rate": fund[j, t], "richtung": np.sign(q), "zahlung": zahl,
                                  "groesse": np.abs(q) * o[j, t] / 0.1}))
    for fname, (a, b) in fen.items():
        e = OUT[fname] = {}
        jahre = (b - a) / 288 / 365.25
        f_ges = fu[:, b - 1].sum() - (fu[:, a - 1].sum() if a > 0 else 0.0)
        n_ges = nc[:, b - 1].sum() - (nc[:, a - 1].sum() if a > 0 else 0.0)
        port = pd.Series(fu.sum(axis=0)[a:b], index=idx[a:b]).resample("1D").last()
        port = port.diff().fillna(port.iloc[0] - (fu[:, a - 1].sum() if a > 0 else 0.0))
        r30, r90 = port.rolling(30).sum(), port.rolling(90).sum()
        e.update({"funding_gesamt_h1": float(f_ges), "funding_pro_jahr_h1": float(f_ges / jahre), "netto_gesamt_h1": float(n_ges),
                  "anteil_am_netto": float(f_ges / n_ges) if n_ges else None,
                  "schlechteste_30_tage_h1": float(r30.min()), "schlechteste_30_tage_bis": str(r30.idxmin().date()),
                  "schlechteste_90_tage_h1": float(r90.min()), "schlechteste_90_tage_bis": str(r90.idxmin().date()),
                  "schlechtester_tag_h1": float(port.min()), "schlechtester_tag": str(port.idxmin().date()),
                  "beste_30_tage_h1": float(r30.max())})
        print(f"\n=== {fname} ({idx[a].date()} bis {idx[b - 1].date()}) ===")
        print(f"  Funding gesamt bei Hebel 1: {f_ges:+.2%} des Startkapitals ({f_ges / jahre:+.2%} pro Jahr; Hebel 3: {3 * f_ges / jahre:+.1%} pro Jahr); Netto-Ergebnis im Fenster {n_ges:+.1%}")
        print(f"  Schlechteste 30 Tage: {r30.min():+.2%} (Hebel 3: {3 * r30.min():+.1%}) bis {r30.idxmin().date()}; schlechteste 90 Tage: {r90.min():+.2%} (Hebel 3: {3 * r90.min():+.1%}) bis {r90.idxmin().date()}; "
              f"schlechtester Tag {port.min():+.2%} (Hebel 3: {3 * port.min():+.1%}) am {port.idxmin().date()}; beste 30 Tage {r30.max():+.2%}")

z = pd.concat(alle, ignore_index=True)
z = z[z["richtung"] != 0].copy()
z["fenster"] = np.where(z["lauf"] == "vor", "Vorperiode", np.where(z["zeit"] < pd.Timestamp(R.SPLIT), "Entwicklung", "Pruefzeitraum"))
z["zahlt"] = z["zahlung"] < 0
z["hoch_gegen"] = z["zahlt"] & (z["rate"].abs() >= HOCH)
z["rate_gegen"] = -z["rate"] * z["richtung"]                # < 0: Position zahlt diesen Satz
print("\n=== Je Abrechnung (alle Coins) ===")
OUT["abrechnungen"] = {}
for fname, g in list(z.groupby("fenster", sort=False)) + [("alle", z)]:
    lg, sh = g[g["richtung"] > 0], g[g["richtung"] < 0]
    k = {"abrechnungen": int(len(g)), "anteil_position_zahlt": float(g["zahlt"].mean()), "anteil_hoch_gegen_position": float(g["hoch_gegen"].mean()),
         "mittlere_rate_long": float(lg["rate"].mean()), "mittlere_rate_short": float(sh["rate"].mean()),
         "anteil_long": float(len(lg) / len(g)), "summe_long_h1": float(lg["zahlung"].sum()), "summe_short_h1": float(sh["zahlung"].sum()),
         "groesste_einzelzahlung_satz": float(g["rate_gegen"].min()), "groesste_einzelzahlung_h1": float(g["zahlung"].min())}
    OUT["abrechnungen"][fname] = k
    i = g["zahlung"].idxmin()
    print(f"  {fname:13s}: {k['abrechnungen']} Abrechnungen mit Position; Position zahlt in {k['anteil_position_zahlt']:.0%}, zahlt mindestens 0,03 % in {k['anteil_hoch_gegen_position']:.1%}; "
          f"mittlerer Satz, wenn Long: {k['mittlere_rate_long']:+.4%} (Long zahlt), wenn Short: {k['mittlere_rate_short']:+.4%} (Short erhält); "
          f"Summe Long {k['summe_long_h1']:+.2%}, Summe Short {k['summe_short_h1']:+.2%} des Startkapitals (Hebel 1)")
    print(f"      größte Einzelzahlung: {g.loc[i, 'coin']} {'Long' if g.loc[i, 'richtung'] > 0 else 'Short'} am {str(g.loc[i, 'zeit'])[:16]}, Satz {g.loc[i, 'rate']:+.3%}, Position {g.loc[i, 'groesse']:.1f}x Standardgröße, "
          f"kostet {g.loc[i, 'zahlung']:+.3%} des Startkapitals (Hebel 1), {3 * g.loc[i, 'zahlung']:+.2%} bei Hebel 3")

print("\n=== Längste Phasen mit hohem Funding gegen die Position (mindestens 0,03 % je Abrechnung, Position zahlt, ohne Unterbrechung) ===")
phasen = []
for (lauf, coin), g in z.groupby(["lauf", "coin"], sort=False):
    g = g.sort_values("zeit")
    lauf_id = (g["hoch_gegen"] != g["hoch_gegen"].shift()).cumsum()
    for _, p in g[g["hoch_gegen"]].groupby(lauf_id):
        phasen.append({"coin": coin, "von": p["zeit"].iloc[0], "bis": p["zeit"].iloc[-1], "abrechnungen": len(p), "richtung": "Long" if p["richtung"].iloc[0] > 0 else "Short",
                       "tage": (p["zeit"].iloc[-1] - p["zeit"].iloc[0]).total_seconds() / 86400 + 1 / 3, "summe_satz": float(p["rate"].abs().sum()),
                       "kosten_h1": float(p["zahlung"].sum()), "max_satz": float(p["rate"].abs().max())})
ph = pd.DataFrame(phasen).sort_values("abrechnungen", ascending=False)
OUT["phasen_top"] = []
for _, r in ph.head(10).iterrows():
    OUT["phasen_top"].append({k: (str(v) if isinstance(v, pd.Timestamp) else v) for k, v in r.items()})
    print(f"  {r['coin']:5s} {r['richtung']:5s} {str(r['von'])[:10]} bis {str(r['bis'])[:10]}: {r['abrechnungen']} Abrechnungen in Folge ({r['tage']:.1f} Tage), Summe der Sätze {r['summe_satz']:.2%} der Positionsgröße "
          f"(höchster {r['max_satz']:.3%}), Kosten {r['kosten_h1']:+.3%} des Startkapitals (Hebel 1), {3 * r['kosten_h1']:+.2%} bei Hebel 3")
print("  Je Coin die längste Phase:")
for coin, g in ph.groupby("coin", sort=False):
    r = g.iloc[0]
    print(f"      {coin:5s}: {r['abrechnungen']} Abrechnungen ({r['tage']:.1f} Tage) ab {str(r['von'])[:10]}, {r['richtung']}, Summe {r['summe_satz']:.2%}")
teuer = ph.sort_values("kosten_h1").head(5)
print("  Die fünf teuersten Phasen:")
for _, r in teuer.iterrows():
    print(f"      {r['coin']:5s} {r['richtung']:5s} {str(r['von'])[:10]} bis {str(r['bis'])[:10]}: {r['abrechnungen']} Abrechnungen, Summe der Sätze {r['summe_satz']:.2%}, Kosten {r['kosten_h1']:+.3%} (Hebel 1), {3 * r['kosten_h1']:+.2%} (Hebel 3)")

# Phasen, in denen das GANZE Portfolio je Abrechnung zahlt (Summe über alle Coins negativ), ohne Unterbrechung
print("\n=== Portfolio: längste Folgen von Abrechnungszeitpunkten, an denen das Portfolio netto Funding zahlt ===")
OUT["portfolio_folgen"] = {}
for lauf, g in z.groupby("lauf", sort=False):
    p = g.groupby(g["zeit"].dt.floor("8h"))["zahlung"].sum()
    neg = p < 0
    lid = (neg != neg.shift()).cumsum()
    best = max(((len(x), x.index[0], x.index[-1], x.sum()) for _, x in p[neg].groupby(lid)), key=lambda x: x[0])
    teuer = min(((len(x), x.index[0], x.index[-1], x.sum()) for _, x in p[neg].groupby(lid)), key=lambda x: x[3])
    OUT["portfolio_folgen"][lauf] = {"laengste": [int(best[0]), str(best[1]), str(best[2]), float(best[3])], "teuerste": [int(teuer[0]), str(teuer[1]), str(teuer[2]), float(teuer[3])],
                                     "anteil_zeitpunkte_zahlt": float(neg.mean())}
    print(f"  {lauf}: Portfolio zahlt an {neg.mean():.0%} der Zeitpunkte; längste Folge {best[0]} Abrechnungen ({best[0] / 3:.0f} Tage) {str(best[1])[:10]} bis {str(best[2])[:10]}, Kosten {best[3]:+.2%} (Hebel 1) / {3 * best[3]:+.1%} (Hebel 3); "
          f"teuerste Folge {teuer[0]} Abrechnungen {str(teuer[1])[:10]} bis {str(teuer[2])[:10]}, Kosten {teuer[3]:+.2%} (Hebel 1) / {3 * teuer[3]:+.1%} (Hebel 3)")

# Rohdaten: Extremwerte der Binance-Raten je Coin und Abrechnungsabstand
print("\n=== Binance-Funding der zehn Coins: Extremwerte und Abstand der Abrechnungen ===")
OUT["raten"] = {}
for coin in A:
    fr = R._lesen("funding", coin, True)["rate"]
    ab = fr.index.to_series().diff().dt.total_seconds().div(3600).round().value_counts().head(3).to_dict()
    OUT["raten"][coin] = {"min": float(fr.min()), "max": float(fr.max()), "abstand_h": {str(k): int(v) for k, v in ab.items()}, "n": int(len(fr)),
                          "anteil_ueber_0.03": float((fr.abs() >= HOCH).mean())}
    print(f"  {coin:5s}: {len(fr)} Abrechnungen, Minimum {fr.min():+.3%} am {fr.idxmin().date()}, Maximum {fr.max():+.3%} am {fr.idxmax().date()}, Betrag ab 0,03 % in {(fr.abs() >= HOCH).mean():.1%}; Abstand in Stunden: {ab}")
(SCRATCH / "s06.json").write_text(json.dumps(OUT, indent=1, default=str))
