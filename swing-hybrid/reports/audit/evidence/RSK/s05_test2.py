"""RSK 05: Test 2 (Stop 5 % / Gewinnziel 15 %). Die Logik aus vorwaertstest/bot.py (Zeilen 216-228) wird auf den
historischen 5-Minuten-Kerzen nachgestellt, mit dem Prüfabstand als einziger Stellgröße des BETRIEBS (nicht der Strategie):
5 Minuten (so läuft der Taktgeber laut Betreiber und stand.csv), 60 Minuten (so ist die Variante erforscht und beschrieben),
6 Stunden und 24 Stunden (Ausfall des Taktgebers: in dieser Zeit prüft der Bot weder Stop noch Signal).
Stop und Ziel bleiben unverändert bei 5 % und 15 %. Keine Auswahl, keine Optimierung.

OFFENLEGUNG: Diese Risikomessung zeigt die Variante sl5_tp15 auch im Prüfzeitraum ab 04/2025. Laut Protokoll (Runde 24)
war der Prüfzeitraum für diese Variante bis dahin unberührt. Er ist damit für sl5_tp15 eingesehen und taugt nicht mehr als
unabhängige Bestätigung dieser Variante. Die Unterschiede zwischen den Prüfabständen sind KEINE Grundlage für eine Auswahl."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import numpy as np
import pandas as pd
from numba import njit
from rsk_common import A, M, R, SCRATCH, dd_stat, runner
from hybrid import tpsl

OUT = {}
TP, SL = 0.15, 0.05
FEE = runner.TAKER * (1 - runner.MIT.rebate)
SLIP = R.yubit_kosten(A)[0]


@njit
def bot_logik(o, sig, takt, tp, sl, slip):
    """Zustandsmaschine wie bot.schritt mit tp/sl, für einen Coin. Der Bot handelt nur an Kerzen t mit t % takt == 0
    (sein Lauf), zum Open dieser Kerze (Mittelkurs ~ Open). Gibt Zielgewichte je Kerze und die Ereignisliste zurück:
    Ereignis = (Kerze, Art 1 Stop / 2 Ziel / 3 Dreh, Richtung der geschlossenen Position, Ergebnis seit Einstieg am Prüfkurs)."""
    T = len(o)
    w = np.zeros(T)
    ev = np.zeros((T // 2 + 2, 4)); k = 0
    ist = 0.0; ein = 0.0; sperre = 0.0
    for t in range(T):
        if t > 0 and t % takt == 0:
            s = sig[t]
            mitte = o[t]
            if sperre != 0.0 and sperre != s:
                sperre = 0.0
            ziel = s
            anlass = 0.0
            if ist != 0.0 and ist == s and ein > 0.0:
                r = (mitte / ein - 1.0) * ist
                if tp > 0 and r >= tp:
                    anlass = 2.0
                elif sl > 0 and r <= -sl:
                    anlass = 1.0
                if anlass != 0.0:
                    sperre = ist
            if s != 0.0 and sperre == s:
                ziel = 0.0
            if ziel != ist:
                if ist != 0.0:
                    ev[k, 0] = t; ev[k, 1] = anlass if anlass != 0.0 else 3.0; ev[k, 2] = ist; ev[k, 3] = (mitte / ein - 1.0) * ist
                    k += 1
                if ziel != 0.0:
                    ein = mitte * (1.0 + ziel * slip)          # Einstieg zum Brief-/Geldkurs (Kern rechnet Open x (1 +- slip))
                ist = ziel
        w[t] = ist
    return w, ev[:k]


def konto_stat(eq1, ix, hebel=3.0):
    konto = 1.0 + hebel * eq1
    s = pd.Series(konto, index=ix)
    schluss = s.resample("1D").last(); tag = schluss.diff(); tag.iloc[0] = schluss.iloc[0] - 1.0
    k = dd_stat(konto, ix)
    return {"ergebnis": float(konto[-1] - 1), "sharpe": float(tag.mean() / tag.std() * np.sqrt(365)), "dd_rel": k["dd_rel"], "dd_abs": k["dd_abs"],
            "schlechtester_tag": float(tag.min()), "konto_min": float(konto.min()), "q01_tag": float(tag.quantile(0.01))}


print("OFFENLEGUNG: Die Variante sl5_tp15 wird hier auch im Prüfzeitraum ab 04/2025 gezeigt (bisher laut Protokoll unberührt). Reine Risikomessung;")
print("die Unterschiede zwischen den Prüfabständen sind keine Grundlage für eine Auswahl von Einstellungen.")
mv = R.markt(A, start=R.VOR_START, ende=R.VOR_ENDE, vor=True)
mh = R.markt(A, vor=True)
TAKTE = {"5 Minuten (Betrieb)": 1, "60 Minuten (Forschung/README)": 12, "6 Stunden (Ausfall)": 72, "24 Stunden (Ausfall)": 288}
alle_ev = {}
for mname, m in (("vor", mv), ("haupt", mh)):
    sig = R.auf_raster(m, M.basis(m))
    fen = {"Vorperiode": (0, len(m.index))} if mname == "vor" else {"Entwicklung": (0, int(m.index.searchsorted(pd.Timestamp(R.SPLIT)))),
                                                                    "Pruefzeitraum": (int(m.index.searchsorted(pd.Timestamp(R.SPLIT))), len(m.index))}
    # Referenz: Kandidat ohne Stop und die erforschte Variante sl5_tp15 (hybrid/tpsl.py), beide durch den Rechenkern
    lk = R.lauf(m, sig, taker=True, slip=SLIP, day_limit=9.0)
    lr = R.lauf(m, R.auf_raster(m, tpsl.VARIANTEN["sl5_tp15"](m)), taker=True, slip=SLIP, day_limit=9.0)
    laeufe = {"Kandidat ohne Stop (Test 1)": (lk, None), "Forschung sl5_tp15 (tpsl.py, Stundenschluss)": (lr, None)}
    for tname, takt in TAKTE.items():
        w2 = np.zeros_like(sig); evs = []
        for j in range(len(A)):
            w2[j], ev = bot_logik(m.o[j], np.ascontiguousarray(sig[j]), takt, TP, SL, float(SLIP[j]))
            e = pd.DataFrame(ev, columns=["kerze", "art", "richtung", "r"]); e["coin"] = A[j]; evs.append(e)
        ev = pd.concat(evs, ignore_index=True)
        ev["zeit"] = m.index[ev["kerze"].astype(int)]
        l2 = R.lauf(m, np.ascontiguousarray(w2), taker=True, slip=SLIP, day_limit=9.0)
        laeufe[f"Bot-Logik Test 2, Prüfabstand {tname}"] = (l2, ev)
        alle_ev.setdefault(tname, []).append(ev)
    for fname, (a, b) in fen.items():
        print(f"\n=== {fname} ({m.index[a]} bis {m.index[b - 1]}) ===  [Hebel 3, Konto = 1 am Fensterbeginn, durchlaufende Positionen]")
        OUT[fname] = {}
        for lname, (l, ev) in laeufe.items():
            eq = l.equity(runner.MIT)
            basis = eq[a - 1] if a > 0 else 0.0
            k = konto_stat(eq[a:b] - basis, m.index[a:b])
            im_markt = None
            txt = ""
            if ev is not None:
                e = ev[(ev["kerze"] >= a) & (ev["kerze"] < b)]
                st = e[e["art"] == 1]["r"]; zi = e[e["art"] == 2]["r"]
                k.update({"stops": int(len(st)), "ziele": int(len(zi)), "drehs": int((e["art"] == 3).sum()),
                          "stop_mittel": float(st.mean()) if len(st) else None, "stop_p01": float(st.quantile(0.01)) if len(st) else None,
                          "stop_schlechtester": float(st.min()) if len(st) else None,
                          "stops_schlechter_7.5": int((st <= -0.075).sum()), "stops_schlechter_10": int((st <= -0.10).sum()), "stops_schlechter_20": int((st <= -0.20).sum())})
                jahre = (b - a) / 288 / 365.25
                txt = (f" | {len(st)} Stops ({len(st) / jahre:.0f}/Jahr), {len(zi)} Ziele, {int((e['art'] == 3).sum())} Drehs; Verlust am Stop: Mittel {st.mean():.2%}, "
                       f"schlechtestes 1 % ab {st.quantile(0.01):.1%}, schlechtester {st.min():.1%}; Stops schlechter als −7,5 %: {(st <= -0.075).sum()}, −10 %: {(st <= -0.10).sum()}, −20 %: {(st <= -0.20).sum()}")
            OUT[fname][lname] = k
            print(f"  {lname:52s}: Ergebnis {k['ergebnis']:+7.1%}, Sharpe {k['sharpe']:.2f}, Einbruch {k['dd_rel']:.1%} (in Punkten {k['dd_abs']:.0%}), schlechtester Tag {k['schlechtester_tag']:+.1%}, tiefster Stand {k['konto_min']:.0%}{txt}")

# ---------------------------------------------------- Ereignis-Auswertung für den Betrieb (5 Minuten) ----
print("\n=== Stops im Betrieb mit 5-Minuten-Prüfung, alle Zeiträume zusammen ===")
ev5 = pd.concat(alle_ev["5 Minuten (Betrieb)"], ignore_index=True)
st = ev5[ev5["art"] == 1].copy()
print(f"  {len(st)} Stops; Verlust am Prüfkurs: Median {st['r'].median():.2%}, Mittel {st['r'].mean():.2%}, schlechteste 1 % ab {st['r'].quantile(0.01):.1%}, schlechtester {st['r'].min():.1%}")
print("  Die zehn schlechtesten Stop-Ausführungen (Kurslücke zwischen zwei Läufen):")
for _, r in st.sort_values("r").head(10).iterrows():
    print(f"      {r['coin']:5s} {'Long ' if r['richtung'] > 0 else 'Short'} {str(r['zeit'])[:16]}: {r['r']:+.1%} statt −5 % -> bei Hebel 3 {0.3 * r['r']:+.1%} des Startkapitals aus EINER Position")
OUT["stops_5min"] = {"n": int(len(st)), "median": float(st["r"].median()), "mittel": float(st["r"].mean()), "p01": float(st["r"].quantile(0.01)), "schlechtester": float(st["r"].min())}
# gleichzeitige Stops
st["stunde"] = st["zeit"].dt.floor("1h"); st["tag"] = st["zeit"].dt.floor("1D")
je_h = st.groupby("stunde").agg(n=("r", "size"), summe=("r", "sum")); je_t = st.groupby("tag").agg(n=("r", "size"), summe=("r", "sum"))
print(f"  Gleichzeitige Stops: höchstens {je_h['n'].max()} in einer Stunde (Summe {je_h['summe'].min():+.1%} der Positionsgröße = {0.3 * je_h['summe'].min():+.1%} des Startkapitals bei Hebel 3, am {je_h['summe'].idxmin()}); "
      f"höchstens {je_t['n'].max()} an einem Tag (Summe {je_t['summe'].min():+.1%} = {0.3 * je_t['summe'].min():+.1%} des Startkapitals, am {je_t['summe'].idxmin().date()})")
print(f"  Stunden mit mindestens 5 Stops: {(je_h['n'] >= 5).sum()}, Tage mit mindestens 8 Stops: {(je_t['n'] >= 8).sum()}")
OUT["gleichzeitig"] = {"max_je_stunde": int(je_h["n"].max()), "summe_schlechteste_stunde": float(je_h["summe"].min()), "max_je_tag": int(je_t["n"].max()),
                       "summe_schlechtester_tag": float(je_t["summe"].min()), "stunden_ab_5": int((je_h["n"] >= 5).sum()), "tage_ab_8": int((je_t["n"] >= 8).sum())}
# Stops in rollierenden 30 Tagen (Summe der realisierten Stop-Verluste)
tage = je_t["summe"].resample("1D").sum()
r30 = tage.rolling(30).sum(); n30 = je_t["n"].resample("1D").sum().rolling(30).sum()
print(f"  Schlechteste 30 Tage: {int(n30[r30.idxmin()])} Stops, Summe {r30.min():+.0%} der Positionsgröße = {0.3 * r30.min():+.0%} des Startkapitals bei Hebel 3 (bis {r30.idxmin().date()})")
OUT["stops_30_tage"] = {"n": int(n30[r30.idxmin()]), "summe": float(r30.min()), "bis": str(r30.idxmin().date())}

# ---------------------------------------------------- Wiedereinstieg nach dem Stop ----
print("\n=== Wiedereinstieg nach einem Stop (5-Minuten-Prüfung) ===")
wieder = []
for mname, m in (("vor", mv), ("haupt", mh)):
    sig = R.auf_raster(m, M.basis(m))
    for j, coin in enumerate(A):
        w2, ev = bot_logik(m.o[j], np.ascontiguousarray(sig[j]), 1, TP, SL, float(SLIP[j]))
        T = len(w2)
        for row in ev[ev[:, 1] == 1.0]:
            t, d = int(row[0]), row[2]
            # nächster Einstieg überhaupt und nächster Einstieg in DERSELBEN Richtung wie die gestoppte Position
            n1 = n2 = -1
            for u in range(t + 1, min(T, t + 288 * 60)):
                if w2[u] != 0.0 and w2[u - 1] != w2[u]:
                    if n1 < 0:
                        n1 = u
                    if w2[u] == d:
                        n2 = u
                        break
            px = m.o[j, t]
            wieder.append({"coin": coin, "zeit": m.index[t], "richtung": d, "bis_einstieg_h": (n1 - t) / 12 if n1 > 0 else np.nan,
                           "bis_gleiche_richtung_h": (n2 - t) / 12 if n2 > 0 else np.nan,
                           "kurs_bei_wiedereinstieg_gegen_stop": d * (m.o[j, n2] / px - 1) if n2 > 0 else np.nan})
wd = pd.DataFrame(wieder)
g = wd["bis_gleiche_richtung_h"]
k = {"stops": int(len(wd)), "median_h_bis_gegenposition": float(wd["bis_einstieg_h"].median()), "median_h_bis_gleiche_richtung": float(g.median()),
     "anteil_gleiche_richtung_binnen_6h": float((g <= 6).mean()), "anteil_gleiche_richtung_binnen_24h": float((g <= 24).mean()),
     "anteil_gleiche_richtung_binnen_72h": float((g <= 72).mean()),
     "anteil_wiedereinstieg_schlechter_als_stopkurs": float((wd["kurs_bei_wiedereinstieg_gegen_stop"] > 0).mean())}
OUT["wiedereinstieg"] = k
print(f"  Nach {k['stops']} Stops: Gegenposition (Dreh) im Median nach {k['median_h_bis_gegenposition']:.0f} h; dieselbe Richtung wie die gestoppte Position wieder offen im Median nach {k['median_h_bis_gleiche_richtung']:.0f} h; "
      f"binnen 6 h bei {k['anteil_gleiche_richtung_binnen_6h']:.0%}, binnen 24 h bei {k['anteil_gleiche_richtung_binnen_24h']:.0%}, binnen 72 h bei {k['anteil_gleiche_richtung_binnen_72h']:.0%} der Stops")
print(f"  In {k['anteil_wiedereinstieg_schlechter_als_stopkurs']:.0%} dieser Fälle liegt der Wiedereinstieg in dieselbe Richtung zu einem schlechteren Kurs als der Stop-Ausstieg (teurer zurückgekauft bzw. tiefer wieder verkauft).")
# Dreh-Häufigkeit des Signals selbst
dreh = []
for mname, m in (("vor", mv), ("haupt", mh)):
    sig = R.auf_raster(m, M.basis(m))
    for j, coin in enumerate(A):
        s = sig[j]
        t = np.flatnonzero((s[1:] != s[:-1]) & (s[1:] != 0) & (s[:-1] != 0)) + 1
        dreh.append(pd.DataFrame({"coin": coin, "zeit": m.index[t]}))
dr = pd.concat(dreh, ignore_index=True).sort_values(["coin", "zeit"])
dr["abstand_h"] = dr.groupby("coin")["zeit"].diff().dt.total_seconds() / 3600
jahre = (mh.index[-1] - mv.index[0]).days / 365.25
k = {"drehs": int(len(dr)), "je_coin_und_jahr": float(len(dr) / len(A) / jahre), "abstand_median_h": float(dr["abstand_h"].median()),
     "anteil_abstand_1h": float((dr["abstand_h"] <= 1).mean()), "anteil_abstand_bis_3h": float((dr["abstand_h"] <= 3).mean()), "anteil_abstand_bis_24h": float((dr["abstand_h"] <= 24).mean())}
OUT["drehs"] = k
print(f"\n  Signal-Drehs: {k['drehs']} in {jahre:.1f} Jahren = {k['je_coin_und_jahr']:.0f} je Coin und Jahr; Abstand zum vorigen Dreh: Median {k['abstand_median_h']:.0f} h, "
      f"genau 1 h bei {k['anteil_abstand_1h']:.0%}, bis 3 h bei {k['anteil_abstand_bis_3h']:.0%}, bis 24 h bei {k['anteil_abstand_bis_24h']:.0%}")
dr["tag"] = dr["zeit"].dt.floor("1D")
jt = dr.groupby("tag").size()
print(f"  Meiste Drehs an einem Tag über alle zehn Coins: {jt.max()} (am {jt.idxmax().date()}); jeder Dreh handelt 2 x Positionsgröße (bei Hebel 3: 3.000 $ je Dreh bei 5.000 $ Konto)")
OUT["drehs"]["max_je_tag"] = int(jt.max())
(SCRATCH / "s05.json").write_text(json.dumps(OUT, indent=1, default=str))
