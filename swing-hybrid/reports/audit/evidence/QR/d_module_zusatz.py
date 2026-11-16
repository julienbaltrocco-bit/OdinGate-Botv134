"""QR (d): weitere Protokollzahlen und Empfindlichkeiten, gerechnet mit den Modulen aus src/hybrid.

Aufruf (aus swing-hybrid/):
  NUMBA_CACHE_DIR=<scratch>/numba .venv/bin/python -I -B <dieses Skript> <ausgabe.json>
Keine Auswahl, keine Optimierung: es werden nur bereits berichtete Zahlen nachgerechnet und die Annahmen
(Kosten, Rebate, Verzoegerung, Hebel) variiert, um ihre Tragweite zu zeigen.
"""
import json
import sys

sys.path.insert(0, "src")
import numpy as np
import pandas as pd
from hybrid import mutationen as M, research as R, runner
from hybrid.fees import Fees

AUS_JSON = sys.argv[1]
FEN = {"D1": (None, R.D1_ENDE), "D2": (R.D1_ENDE, R.SPLIT), "Entwicklung": (None, R.SPLIT), "Pruefung": (R.SPLIT, None)}
out = {}


def teil(x, von=None, bis=None):
    if von is not None:
        x = x[x.index >= pd.Timestamp(von)]
    if bis is not None:
        x = x[x.index < pd.Timestamp(bis)]
    return x


def sharpe(x):
    return float(x.mean() / x.std() * np.sqrt(365)) if x.std() > 0 else 0.0


def dd(x):
    k = 1.0 + x.cumsum()
    return float(((k.cummax() - k) / k.cummax()).max())


def kenn(x):
    return {"N": float(x.sum()), "jahr": float(x.mean() * 365), "sharpe": sharpe(x), "dd_tag": dd(x)}


mA = R.markt(R.GRUPPE_A, vor=True)
sig = M.basis(mA)
wA = R.auf_raster(mA, sig)
kA = R.yubit_kosten(R.GRUPPE_A)[0]
l1 = R.lauf(mA, wA, taker=True, slip=kA, day_limit=9.0)
basis = l1.daily_pnl(runner.MIT).sum(axis=1)

# ---- 1) Runde 6 Teil 1: Hebel 0,2 mit Tageslimit 3 % (Standard aus config.yaml) ----
r6 = {}
for name, slip in (("echt", kA), ("stress_2x", 2 * kA), ("alt_5bp", 0.0005)):
    l = R.lauf(mA, wA, hebel=0.2, taker=True, slip=slip)
    r6[name] = {f: {k: R.sicht(l, *v)[k] for k in ("N", "handel", "G", "dd_mit", "sharpe")} for f, v in FEN.items() if f in ("Entwicklung", "Pruefung")}
    r6[name]["sperrtage"] = int(l.st[4])
g6 = json.load(open("reports/suche_runde6.json"))["teil1"]["A"]
out["runde6_teil1_hebel02"] = {"nachgerechnet": r6, "gespeichert": {
    "hebel": g6["hebel"], "echt": {f: {k: g6[f][k] for k in ("N", "handel", "G", "dd_mit", "sharpe")} for f in ("Entwicklung", "Pruefung")},
    "stress_2x": {f: {k: g6["stress_2x"][f][k] for k in ("N", "handel", "G", "dd_mit", "sharpe")} for f in ("Entwicklung", "Pruefung")},
    "alt_5bp": {f: {k: g6["alt_5bp"][f][k] for k in ("N", "handel", "G", "dd_mit", "sharpe")} for f in ("Entwicklung", "Pruefung")}}}
# Hebelsuche wie im Skript: groesster Hebel aus der Liste mit Einbruch <= 10 % in der Entwicklung (mit Tageslimit)
hs = {}
for h in (3, 2, 1, 0.5, 0.3, 0.25, 0.2):
    l = R.lauf(mA, wA, hebel=h, taker=True, slip=kA)
    hs[str(h)] = {"dd_entwicklung_mit_tageslimit": R.sicht(l, *FEN["Entwicklung"])["dd_mit"], "sperrtage": int(l.st[4]),
                  "N_entwicklung": R.sicht(l, *FEN["Entwicklung"])["N"], "N_pruefung": R.sicht(l, *FEN["Pruefung"])["N"],
                  "dd_pruefung": R.sicht(l, *FEN["Pruefung"])["dd_mit"]}
out["hebelsuche_mit_tageslimit_3pct"] = hs

# ---- 2) Runde 21 vollstaendig: 14 Mutationen und gemeinsame Zufallspruefung ----
def tage(m, fn):
    l = R.lauf(m, R.auf_raster(m, fn(m)), taker=True, slip=R.yubit_kosten(m.coins)[0], day_limit=9.0)
    return l.daily_pnl(runner.MIT).sum(axis=1)


bd = teil(basis, None, R.SPLIT)
r21, diffs = {}, []
for n, fn in M.VARIANTEN.items():
    x = tage(mA, fn); xd = teil(x, None, R.SPLIT)
    fak = float(bd.std() / xd.std())
    r21[n] = {"D1": sharpe(teil(x, None, R.D1_ENDE)), "D2": sharpe(teil(x, R.D1_ENDE, R.SPLIT)), "Entwicklung": sharpe(xd),
              "vorsprung_jahr": float((fak * xd - bd).mean() * 365)}
    diffs.append((fak * xd - bd).to_numpy())
mittel, schwelle, p = M.reality_check(np.column_stack(diffs))
g21 = json.load(open("reports/suche_runde21.json"))
abw = max(abs(r21[n][f] - g21["varianten"][n][f]["sharpe"]) for n in r21 for f in ("D1", "D2", "Entwicklung"))
out["runde21"] = {"varianten": r21, "reality_check": {"schwelle_95": schwelle, "p_beste": p}, "gespeichert_rc": g21["reality_check"],
                  "max_abweichung_sharpe_gegen_gespeichert": abw}

# ---- 3) Runde 4: Vorperiode Gruppe A (02/2020-08/2021), Slippage 0,05 %, Hebel 1, ohne Tageslimit ----
mv = R.markt(R.GRUPPE_A, R.VOR_START, R.VOR_ENDE, vor=True)
lv = R.lauf(mv, R.auf_raster(mv, R.tsmom(mv, 336)), taker=True, day_limit=9.0)
sv = R.sicht(lv, None, None)
tv = lv.daily_pnl(runner.MIT).sum(axis=1)
tv.to_csv(AUS_JSON.replace(".json", "_vorperiode_tage.csv"), float_format="%.10f")
g4 = json.load(open("reports/suche_runde4.json"))["vorperiode"]["A"]
out["runde4_vorperiode_A"] = {"nachgerechnet": {k: sv[k] for k in ("N", "G", "handel", "dd_mit", "sharpe", "jahr_N", "trades")},
                              "gespeichert": {k: g4[k] for k in ("N", "G", "handel", "dd_mit", "sharpe", "jahr_N", "trades")},
                              "kenn_tag": kenn(tv)}

# ---- 4) Empfindlichkeit: Rebate, Slippage, Ausfuehrungsverzoegerung (Hebel 1, ohne Tageslimit) ----
emp = {}
for name, slip in (("slip_echt", kA), ("slip_2x", 2 * kA), ("slip_5bp", 0.0005), ("slip_10bp", 0.001)):
    l = R.lauf(mA, wA, taker=True, slip=slip, day_limit=9.0)
    for rb in (0.85, 0.5, 0.0):
        x = l.daily_pnl(Fees(runner.MAKER, runner.TAKER, rb)).sum(axis=1)
        emp[f"{name}|rebate_{int(rb * 100)}"] = {f: kenn(teil(x, *v)) for f, v in FEN.items()}
for bars in (1, 3, 12):
    w2 = np.ascontiguousarray(np.concatenate([np.zeros((wA.shape[0], bars)), wA[:, :-bars]], axis=1))
    l = R.lauf(mA, w2, taker=True, slip=kA, day_limit=9.0)
    x = l.daily_pnl(runner.MIT).sum(axis=1)
    emp[f"verzoegerung_{bars * 5}min|slip_echt|rebate_85"] = {f: kenn(teil(x, *v)) for f, v in FEN.items()}
out["empfindlichkeit"] = emp
# Zerlegung im Pruefzeitraum (Hebel 1, echte Slippage)
k = runner.kennzahlen(l1, R.SPLIT, None)
V = k["volumen_tag"] * k["tage"]
out["zerlegung_pruefung"] = {"umsatz": V, "gebuehr_voll": runner.TAKER * V, "rebate": runner.TAKER * V * 0.85,
                             "vor_gebuehr_inkl_slip_funding": k["rendite_brutto"], "funding": k["funding"],
                             "slippage_summe": float((np.diff(np.concatenate([[0], l1.daily[:, :, 2]], axis=1) if False else l1.daily[:, :, 2], axis=1, prepend=0)[:, -int(k["tage"]):].sum(axis=1) * kA).sum()),
                             "netto_ohne_rebate": k["rendite_ohne"], "netto_mit_rebate": k["rendite_mit"]}
k = runner.kennzahlen(l1, None, R.SPLIT)
V = k["volumen_tag"] * k["tage"]
out["zerlegung_entwicklung"] = {"umsatz": V, "gebuehr_voll": runner.TAKER * V, "rebate": runner.TAKER * V * 0.85,
                                "vor_gebuehr_inkl_slip_funding": k["rendite_brutto"], "funding": k["funding"],
                                "netto_ohne_rebate": k["rendite_ohne"], "netto_mit_rebate": k["rendite_mit"]}

# ---- 5) Hebel 3 ohne Tageslimit (Konfiguration der Papier-Tests), feste Groesse am Startkapital ----
eq = l1.equity(runner.MIT)
idx = mA.index
h3 = {}
for f, (von, bis) in FEN.items():
    a = 0 if von is None else int(idx.searchsorted(pd.Timestamp(von)))
    b = len(idx) if bis is None else int(idx.searchsorted(pd.Timestamp(bis)))
    e = 3.0 * (eq[a:b] - (eq[a - 1] if a > 0 else 0.0))
    konto = 1.0 + e
    spitze = np.maximum.accumulate(np.maximum(konto, 1.0))
    i_tief = int(np.argmin(konto))
    erst = np.argmax(konto <= 0.0) if (konto <= 0.0).any() else -1
    h3[f] = {"konto_tief": float(konto.min()), "zeit_tief": str(idx[a + i_tief]), "konto_ende": float(konto[-1]),
             "einbruch_rel_spitze": float(((spitze - konto) / spitze).max()),
             "erstes_konto_null": (str(idx[a + int(erst)]) if erst >= 0 else None)}
out["hebel3_ohne_tageslimit_start_fensterbeginn"] = h3
l3 = R.lauf(mA, wA, hebel=3.0, taker=True, slip=kA, day_limit=9.0)
out["hebel3_linear"] = float(np.abs(l3.equity(runner.MIT) - 3.0 * eq).max())

# ---- 6) Unsicherheit der Sharpe-Werte: stationaerer Bootstrap (Bloecke im Mittel 20 Tage, 5000 Ziehungen, Seed 7) ----
def boot_sharpe(x, ziehungen=5000, block=20, seed=7):
    rng = np.random.default_rng(seed)
    v = x.to_numpy(); n = len(v)
    neu = rng.random((ziehungen, n)) < 1.0 / block
    neu[:, 0] = True
    start = rng.integers(0, n, (ziehungen, n))
    idx_ = np.empty((ziehungen, n), dtype=np.int64)
    pos = start[:, 0]
    for i in range(n):
        pos = np.where(neu[:, i], start[:, i], (pos + 1) % n)
        idx_[:, i] = pos
    s = v[idx_]
    sh = s.mean(axis=1) / s.std(axis=1, ddof=1) * np.sqrt(365)
    return {"sharpe": sharpe(x), "p05": float(np.percentile(sh, 5)), "p50": float(np.percentile(sh, 50)), "p95": float(np.percentile(sh, 95)),
            "anteil_sharpe_le_0": float((sh <= 0).mean()), "t_wert_mittel": float(x.mean() / (x.std() / np.sqrt(len(x)))), "tage": int(len(x))}


out["bootstrap_sharpe"] = {f: boot_sharpe(teil(basis, *v)) for f, v in FEN.items()}
out["bootstrap_sharpe"]["Vorperiode_A_5bp"] = boot_sharpe(tv)
json.dump(out, open(AUS_JSON, "w"), indent=1, default=float)

print("1) Runde 6 Teil 1, Hebel 0,2 mit Tageslimit 3 %:")
for name in r6:
    print("  ", name, {f: {k: round(v, 4) for k, v in r6[name][f].items()} for f in ("Entwicklung", "Pruefung")}, "Sperrtage", r6[name]["sperrtage"])
print("   gespeichert:", {f: {k: round(v, 4) for k, v in out["runde6_teil1_hebel02"]["gespeichert"]["echt"][f].items()} for f in ("Entwicklung", "Pruefung")})
print("   Hebelsuche:"); print(pd.DataFrame(hs).T.round(4).to_string())
print("2) Runde 21:"); print(pd.DataFrame(r21).T.round(4).to_string())
print("   Reality Check:", out["runde21"]["reality_check"], "gespeichert:", g21["reality_check"], "max. Sharpe-Abweichung:", abw)
print("3) Vorperiode A:", {k: round(v, 4) for k, v in out["runde4_vorperiode_A"]["nachgerechnet"].items()}, "gespeichert:", {k: round(v, 4) for k, v in out["runde4_vorperiode_A"]["gespeichert"].items()})
print("4) Empfindlichkeit (N / Sharpe je Fenster):")
print(pd.DataFrame({n: {f"{f}_{k}": e[f][k] for f in ("Entwicklung", "Pruefung") for k in ("N", "sharpe", "dd_tag")} for n, e in emp.items()}).T.round(4).to_string())
print("   Zerlegung Pruefzeitraum:", {k: round(v, 4) for k, v in out["zerlegung_pruefung"].items()})
print("   Zerlegung Entwicklung:", {k: round(v, 4) for k, v in out["zerlegung_entwicklung"].items()})
print("5) Hebel 3 ohne Tageslimit:"); print(pd.DataFrame(h3).T.to_string()); print("   Linearitaet |eq(h=3) - 3*eq(h=1)| max:", out["hebel3_linear"])
print("6) Bootstrap Sharpe:"); print(pd.DataFrame(out["bootstrap_sharpe"]).T.round(3).to_string())
