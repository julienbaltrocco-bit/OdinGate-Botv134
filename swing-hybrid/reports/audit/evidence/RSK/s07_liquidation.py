"""RSK 07: Liquidationsrechnung unter klar benannten ANNAHMEN (das Repo enthält weder Margin-Modus noch
Erhaltungsmargin von Yubit; alles hier ist deshalb eine Szenariorechnung, kein Yubit-Fakt).

Annahmen (übliche Formeln linearer USDT-Perpetuals, z. B. Bybit-Bauart, an die die Yubit-Schnittstelle erinnert):
- Isolierte Margin, Börsenhebel L je Position: Margin = Positionswert / L. Liquidation, wenn der Kurs um (1/L - MMR) gegen
  den Einstieg läuft (Long: Einstieg x (1 - 1/L + MMR), Short: Einstieg x (1 + 1/L - MMR)). Verlust = die Margin der Position.
- Gemeinsame Margin (Cross): Liquidation des ganzen Kontos, wenn Kontostand <= MMR x Summe der Positionswerte.
- MMR (Erhaltungsmargin) unbekannt: gerechnet mit 0,5 %, 1 % und 2,5 %.
- Kurse: Binance-Futures letzter Preis (5-Minuten-Kerzen). Yubit liquidiert vermutlich nach Mark-Preis; der ist nicht vorhanden.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import numpy as np
import pandas as pd
from numba import njit, prange
from rsk_common import A, M, R, ROOT, SCRATCH, runner

OUT = {}
FEE = runner.TAKER * (1 - runner.MIT.rebate)
SLIP = R.yubit_kosten(A)[0]
MMRS = (0.005, 0.01, 0.025)

print("=== 1. Entfernung bis zur Liquidation, reine Formel ===")
print("  Isolierte Margin, je Position (Bewegung gegen den Einstieg bis zur Liquidation):")
OUT["isoliert_distanz"] = {}
for L in (3, 5, 10, 20):
    z = {str(m): 1.0 / L - m for m in MMRS}
    OUT["isoliert_distanz"][str(L)] = z
    print(f"    Börsenhebel {L:2d}x: " + ", ".join(f"MMR {m:.1%}: {1.0 / L - m:.1%}" for m in MMRS) + f"; Margin je Position bei 1.500 $ Positionswert: {1500 / L:.0f} $ ({1500 / L / 5000:.0%} des Kontos), alle zehn: {15000 / L:.0f} $")
print("  Gemeinsame Margin, Konto 5.000 $, zehn Positionen je 1.500 $, alle in derselben Richtung (wie beide Papier-Tests am 15.11.2026):")
OUT["cross_distanz"] = {}
for m in MMRS:
    xs = (1 / 3 - m) / (1 + m); xl = (1 / 3 - m) / (1 - m)
    OUT["cross_distanz"][str(m)] = {"alle_short": xs, "alle_long": xl}
    print(f"    MMR {m:.1%}: Liquidation, wenn der Korb um {xs:.1%} steigt (alle Short) bzw. um {xl:.1%} fällt (alle Long); Erhaltungsmargin am Start {m * 15000:.0f} $")

# aktueller Stand der Papier-Tests (nur lesen)
print("\n=== 2. Aktueller Stand der beiden Papier-Tests (gelesen, nicht verändert) ===")
OUT["papier"] = {}
for name, ordner in (("Test 1", "lauf"), ("Test 2", "lauf_tpsl")):
    z = json.loads(((ROOT / "vorwaertstest") / ordner / "zustand.json").read_text())
    st = pd.read_csv((ROOT / "vorwaertstest") / ordner / "stand.csv")
    wert = {c: z["pos"][c] * z["kurs"][c] for c in z["pos"]}
    brutto = sum(abs(v) for v in wert.values())
    netto = float(st["netto_mit_rebate"].iloc[-1])
    konto = z["kapital"] + netto
    nl, ns = sum(v > 0 for v in wert.values()), sum(v < 0 for v in wert.values())
    e = {"letzter_lauf": st["zeit"].iloc[-1], "long": nl, "short": ns, "positionswert": brutto, "konto": konto, "eff_hebel": brutto / konto,
         "margin_bei_3x": brutto / 3, "freie_margin_bei_3x": konto - brutto / 3}
    for m in MMRS:
        # alle Short: Konto - brutto*x = m*brutto*(1+x)
        e[f"cross_distanz_mmr_{m}"] = (konto / brutto - m) / (1 + m) if ns == len(wert) else None
    OUT["papier"][name] = e
    t = pd.to_datetime(st["zeit"]); lue = t.diff().dt.total_seconds().div(60)
    e["laeufe"] = int(len(st)); e["abstand_median_min"] = float(lue.median()); e["abstand_max_min"] = float(lue.max()); e["abstand_max_ende"] = str(t[lue.idxmax()])
    e["luecken_ueber_15_min"] = int((lue > 15).sum())
    print(f"  {name}: letzter Lauf {e['letzter_lauf']}, {nl} Long / {ns} Short, Positionswert {brutto:,.0f} $, Konto (Start + Ergebnis mit Rebate) {konto:,.0f} $, Positionswert/Konto {brutto / konto:.2f}; "
          f"bei Börsenhebel 3x wären {brutto / 3:,.0f} $ Margin gebunden, frei {konto - brutto / 3:,.0f} $")
    print(f"      Cross-Liquidation (alle Short, gleichmäßiger Anstieg aller zehn Kurse): " + ", ".join(f"MMR {m:.1%}: +{e[f'cross_distanz_mmr_{m}']:.1%}" for m in MMRS))
    print(f"      Taktgeber laut stand.csv: {len(st)} Läufe, Abstand Median {lue.median():.0f} min, größter Abstand {lue.max():.0f} min (bis {t[lue.idxmax()]}), Abstände über 15 min: {(lue > 15).sum()}")
    grosse = st.assign(abstand=lue)[lue > 15][["zeit", "abstand"]]
    if len(grosse):
        print("      Lücken über 15 min: " + "; ".join(f"bis {r.zeit}: {r.abstand:.0f} min" for r in grosse.itertuples()))


# ---------------------------------------------- 3. Cross-Margin in der Start-Tag-Analyse ----
@njit(parallel=True)
def starts_cross(o, c, fund, w, slip, fee, starts, n_h, checkpoints, hebel):
    """Wie rsk_common.starts_sim, zusätzlich Minimum der Margin-Quote Kontostand / Positionswert bei gegebenem Hebel.
    Gibt je Start und Prüfpunkt die kleinste Quote zurück (<= MMR heißt: Cross-Liquidation unter der Annahme)."""
    ns = len(starts); N = o.shape[0]; T = o.shape[1]
    out = np.full((ns, len(checkpoints)), np.nan)
    S = 1.0 / N
    for si in prange(ns):
        s = starts[si]
        n = min(n_h, T - s)
        path = np.zeros(n); ex = np.zeros(n)
        for j in range(N):
            q = 0.0; cash = 0.0; vol = 0.0; f = 0.0; held = 0.0
            for k in range(n):
                t = s + k
                tgt = w[j, t]
                if fund[j, t] != 0.0 and q != 0.0:
                    f -= q * o[j, t] * fund[j, t]
                if k > 0 and abs(tgt - held) > 1e-9:
                    if held == 0.0:
                        dq = tgt * S / o[j, t]
                    elif tgt * held < 0.0:
                        dq = -q + tgt * S / o[j, t]
                    else:
                        dq = -q * (1.0 - tgt / held)
                    sq = 1.0 if dq > 0 else -1.0
                    px = o[j, t] * (1.0 + sq * slip[j])
                    cash -= dq * px; vol += abs(dq) * px; q += dq; held = tgt
                path[k] += cash + q * c[j, t] - fee * vol + f
                ex[k] += abs(q) * c[j, t]
        mn = 1e9; ci = 0
        for k in range(n):
            if ex[k] > 0.0:
                quote = (1.0 + hebel * path[k]) / (hebel * ex[k])
                if quote < mn:
                    mn = quote
            while ci < len(checkpoints) and k == checkpoints[ci] - 1:
                out[si, ci] = mn
                ci += 1
    return out


mg = R.markt(A, start=R.VOR_START, ende=R.ENDE, vor=True)
wg = np.ascontiguousarray(R.auf_raster(mg, M.basis(mg)), dtype=np.float64)
tagstart = np.arange(0, len(mg.index), 288, dtype=np.int64)
HOR = {"30 Tage": 30, "90 Tage": 90, "180 Tage": 180, "365 Tage": 365}
cp = np.array([t * 288 for t in HOR.values()], dtype=np.int64)
tage_idx = mg.index[tagstart]
gruppen = {"Vorperiode": (pd.Timestamp(R.VOR_START), pd.Timestamp(R.VOR_ENDE)), "Entwicklung": (pd.Timestamp(R.START), pd.Timestamp(R.SPLIT)),
           "Pruefzeitraum": (pd.Timestamp(R.SPLIT), pd.Timestamp(R.ENDE)), "alle": (pd.Timestamp(R.VOR_START), pd.Timestamp(R.ENDE))}
print("\n=== 3. Gemeinsame Margin: Anteil der Starttage mit Liquidation des ganzen Kontos (Kontostand <= MMR x Positionswert) ===")
print("  Jeder Kalendertag als Start eines neuen Kontos mit frischen Positionen (wie s02), 5-Minuten-Schlusskurse.")
OUT["cross_starttage"] = {}
for h in (1.0, 3.0):
    q = starts_cross(mg.o, mg.c, mg.fund, wg, np.ascontiguousarray(SLIP), FEE, tagstart, int(cp[-1]), cp, h)
    print(f"  Hebel {h:.0f}:")
    for ci, hname in enumerate(HOR):
        for gname, (ga, gb) in gruppen.items():
            sel = (tage_idx >= ga) & (tage_idx < gb) & ~np.isnan(q[:, ci])
            if not sel.any():
                continue
            e = {"starttage": int(sel.sum()), **{f"mmr_{m}": float((q[sel, ci] <= m).mean()) for m in MMRS}}
            OUT["cross_starttage"][f"H{h}|{hname}|{gname}"] = e
            print(f"    {hname:8s} Starts {gname:13s} ({e['starttage']:4d}): Liquidation bei " + ", ".join(f"MMR {m:.1%}: {e[f'mmr_{m}']:5.1%}" for m in MMRS))

# ---------------------------------------------- 4. Isolierte Margin: Trades mit Gegenbewegung über der Distanz ----
t = pd.read_pickle(SCRATCH / "trades_mae.pkl")
jahre = (t["aus"].max() - t["ein"].min()).days / 365.25
print(f"\n=== 4. Isolierte Margin: Zahl der Haltephasen des Kandidaten, die liquidiert worden wären ({len(t)} Trades in {jahre:.1f} Jahren, Vorperiode bis Prüfzeitraum) ===")
print("  Basis: 5-Minuten-Hochs/-Tiefs des letzten Preises (in Klammern: nur 5-Minuten-Schlusskurse). Verlust je Liquidation = Margin der Position = 30 % / L des Kontos bei Hebel 3.")
OUT["isoliert_trades"] = {}
for L in (3, 5, 10, 20):
    for m in MMRS:
        d = 1.0 / L - m
        liq = t[t["mae"] >= d]; liqc = t[t["mae_schluss"] >= d]
        # Unterschied zum Backtest: der Backtest bucht das Ergebnis beim Dreh, die Börse hätte die Margin eingezogen
        diff = (-(1.0 / L) - liq["ergebnis"]).sum() * 0.3            # in Anteilen des Startkapitals bei Hebel 3 (Positionsgröße 0,3)
        e = {"distanz": d, "trades": int(len(liq)), "pro_jahr": float(len(liq) / jahre), "trades_schluss": int(len(liqc)),
             "je_fenster": liq["fenster"].value_counts().to_dict(), "backtest_zu_gut_um_h3": float(-diff),
             "davon_im_backtest_mit_gewinn_beendet": int((liq["ergebnis"] > 0).sum())}
        OUT["isoliert_trades"][f"L{L}|mmr{m}"] = e
        print(f"    Börsenhebel {L:2d}x, MMR {m:.1%} (Distanz {d:.1%}): {len(liq)} Trades ({len(liq) / jahre:.1f} pro Jahr; nur Schlusskurse {len(liqc)}); je Fenster {e['je_fenster']}; "
              f"davon im Backtest mit Gewinn beendet {e['davon_im_backtest_mit_gewinn_beendet']}; Backtest-Ergebnis dadurch zu gut um {e['backtest_zu_gut_um_h3']:+.1%} des Startkapitals (Hebel 3, ganze Historie)")
(SCRATCH / "s07.json").write_text(json.dumps(OUT, indent=1, default=str))
