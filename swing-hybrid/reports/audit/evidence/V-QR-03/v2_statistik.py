"""V-QR-03 Schritt 2: eigene Statistik auf den Tagesreihen aus Schritt 1 (keine Module aus src/hybrid, nur numpy/pandas).

Aufruf:  .venv/bin/python -I -B -W ignore <dieses Skript> <verzeichnis mit den CSV aus Schritt 1> <ausgabe.json>

Eigene Umsetzung von White's Reality Check (stationaerer und kreisfoermiger Block-Bootstrap), Hansens SPA-Test,
Bootstrap der Sharpe-Werte, HAC-t-Werte, Abhaengigkeit des Pruefzeitraums von wenigen Tagen, zusammengelegte
unabhaengige Zeitraeume. Nichts wird optimiert; es werden nur Pruefgroessen fuer feststehende Reihen gerechnet.
"""
import json
import sys
from math import erf, log, sqrt

import numpy as np
import pandas as pd

VERZ, AUS = sys.argv[1], sys.argv[2]
SPLIT, D1_ENDE = pd.Timestamp("2025-04-01"), pd.Timestamp("2023-07-01")
KAND = "tsmom_L336_biasFalse"
out = {}


def lade(n):
    return pd.read_csv(f"{VERZ}/{n}", index_col=0, parse_dates=True)


def idx_stationaer(n, B, block, rng):
    neu = rng.random((B, n)) < 1.0 / block
    neu[:, 0] = True
    start = rng.integers(0, n, (B, n))
    lauf = np.arange(n)
    letzt = np.maximum.accumulate(np.where(neu, lauf, 0), axis=1)
    return (np.take_along_axis(start, letzt, axis=1) + (lauf - letzt)) % n


def idx_kreis(n, B, block, rng):
    k = -(-n // block)
    start = rng.integers(0, n, (B, k))
    return ((start[:, :, None] + np.arange(block)[None, None, :]) % n).reshape(B, -1)[:, :n]


def boot_mittel(x, B=5000, block=20, seed=1, art="stationaer"):
    """Bootstrap-Mittelwerte (B x k) der Spalten von x."""
    rng = np.random.default_rng(seed)
    n = x.shape[0]
    teile = []
    for a in range(0, B, 250):
        b = min(250, B - a)
        idx = idx_stationaer(n, b, block, rng) if art == "stationaer" else idx_kreis(n, b, block, rng)
        teile.append(x[idx].mean(axis=1))
    return np.vstack(teile)


def reality_check(x, **kw):
    """White (2000): H0 max_k E[x_k] <= 0. p = Anteil der Ziehungen, in denen das groesste zentrierte Mittel >= beobachtetes Maximum."""
    m = x.mean(axis=0)
    bm = boot_mittel(x, **kw) - m
    mx = bm.max(axis=1)
    return float((mx >= m.max()).mean()), float(np.percentile(mx, 95))


def spa(x, **kw):
    """Hansen (2005) SPA: studentisiert, drei Zentrierungen (l = untere, c = konsistente, u = obere Schranke = studentisierter RC)."""
    n = x.shape[0]
    m = x.mean(axis=0)
    bm = boot_mittel(x, **kw)
    om = np.sqrt(n) * (bm - m).std(axis=0, ddof=1)
    t = max(float((np.sqrt(n) * m / om).max()), 0.0)
    erg = {"t_beobachtet": t}
    for nm, g in (("l", np.maximum(m, 0.0)), ("c", m * (np.sqrt(n) * m / om >= -np.sqrt(2 * np.log(np.log(n))))), ("u", m)):
        ts = np.maximum((np.sqrt(n) * (bm - g) / om).max(axis=1), 0.0)
        erg["p_" + nm] = float((ts > t).mean())
    return erg


def sharpe(v):
    return float(v.mean() / v.std(ddof=1) * np.sqrt(365))


def hac_t(v, lag):
    v = np.asarray(v, float)
    n = len(v)
    e = v - v.mean()
    s = float(e @ e) / n
    for k in range(1, lag + 1):
        s += 2 * (1 - k / (lag + 1)) * float(e[k:] @ e[:-k]) / n
    return float(v.mean() / np.sqrt(s / n))


def p_norm(t):
    return 0.5 * (1 - erf(t / sqrt(2)))


def boot_sharpe(v, B=5000, block=20, seed=1):
    rng = np.random.default_rng(seed)
    v = np.asarray(v, float)
    s = v[idx_stationaer(len(v), B, block, rng)]
    sh = s.mean(axis=1) / s.std(axis=1, ddof=1) * np.sqrt(365)
    return {"sharpe": sharpe(v), "p05": float(np.percentile(sh, 5)), "p50": float(np.percentile(sh, 50)), "p95": float(np.percentile(sh, 95)),
            "anteil_le_0": float((sh <= 0).mean()), "t_iid": float(v.mean() / (v.std(ddof=1) / np.sqrt(len(v)))), "t_hac20": hac_t(v, 20),
            "p_einseitig_iid": p_norm(float(v.mean() / (v.std(ddof=1) / np.sqrt(len(v))))), "tage": int(len(v)), "summe": float(v.sum()),
            "jahr": float(v.mean() * 365)}


# ------------------------------------------------------------------ A) Abgleich eigene Abrechnung gegen engine2
eig = lade("eigen_kandidat.csv")
print("A) Kandidat: eigene Abrechnung (ohne engine2) gegen Modul-Lauf")
out["A_abgleich"] = {}
for kosten in ("slip_5bp", "slip_yubit"):
    d = lade(f"reihen_{kosten}.csv")
    a, b = d[KAND], eig[kosten]
    out["A_abgleich"][kosten] = {"max_abw_tag": float((a - b).abs().max()), "korrelation": float(np.corrcoef(a, b)[0, 1]),
                                 "summe_modul": float(a.sum()), "summe_eigen": float(b.sum()),
                                 "sharpe_entw_modul": sharpe(a[a.index < SPLIT]), "sharpe_entw_eigen": sharpe(b[b.index < SPLIT]),
                                 "sharpe_pruef_modul": sharpe(a[a.index >= SPLIT]), "sharpe_pruef_eigen": sharpe(b[b.index >= SPLIT])}
    print("  ", kosten, {k: round(v, 6) for k, v in out["A_abgleich"][kosten].items()})

# ------------------------------------------------------------------ B) Reality Check ueber die Auswahl (Entwicklung)
print("B) Reality Check / SPA in der Entwicklung (H0: keine Einstellung hat positiven Ertrag)")
out["B_rc"] = {}
for kosten in ("slip_5bp", "slip_yubit"):
    d = lade(f"reihen_{kosten}.csv")
    d = d[d.index < SPLIT]
    sh = (d.mean() / d.std() * np.sqrt(365)).sort_values(ascending=False)
    trend = [c for c in d.columns if c.startswith(("tsmom", "ensemble"))]
    r3 = [c for c in trend if c.startswith("ensemble") or any(f"_L{L}_" in c for L in (48, 96, 168, 336))]
    mengen = {"alle_32": list(d.columns), "trend_14": trend, "runde3_10": r3, "kandidat_1": [KAND]}
    e = out["B_rc"][kosten] = {"tage": int(len(d)), "rang_kandidat": int(list(sh.index).index(KAND) + 1), "sharpe_kandidat": float(sh[KAND]),
                               "sharpe_zweitbeste": {sh.index[1]: float(sh.iloc[1])}, "anzahl_sharpe_positiv": int((sh > 0).sum())}
    for nm, sp in mengen.items():
        x = d[sp].to_numpy()
        xn = x / x.std(axis=0, ddof=1)
        z = e[nm] = {"k": len(sp), "beste_roh": sp[int(np.argmax(x.mean(axis=0)))]}
        p, s95 = reality_check(x, block=20, seed=1)
        z["rc_roh_p"], z["rc_roh_schwelle_jahr"], z["mittel_beste_jahr"] = p, s95 * 365, float(x.mean(axis=0).max() * 365)
        p, s95 = reality_check(xn, block=20, seed=1)
        z["rc_gleichvol_p"], z["rc_gleichvol_schwelle_sharpe"] = p, s95 * np.sqrt(365)
        z["spa"] = spa(x, block=20, seed=1)
        # Empfindlichkeit: Blocklaenge, Startwert, Bootstrap-Art
        emp = {}
        for block in (5, 10, 20, 40, 60):
            ps = [reality_check(x, block=block, seed=s)[0] for s in (1, 2, 3)]
            pn = [reality_check(xn, block=block, seed=s)[0] for s in (1, 2, 3)]
            emp[f"block_{block}"] = {"roh_p_min_max": [min(ps), max(ps)], "gleichvol_p_min_max": [min(pn), max(pn)]}
        emp["kreis_block_20"] = {"roh_p": reality_check(x, block=20, seed=1, art="kreis")[0], "gleichvol_p": reality_check(xn, block=20, seed=1, art="kreis")[0]}
        z["empfindlichkeit"] = emp
        print(f"   {kosten:10s} {nm:11s} k={len(sp):2d}  RC roh p={z['rc_roh_p']:.3f} (Schwelle {z['rc_roh_schwelle_jahr']:.3f}/Jahr, beste {z['mittel_beste_jahr']:.3f})"
              f"  RC gleiche Schwankung p={z['rc_gleichvol_p']:.3f}  SPA p_l/p_c/p_u={z['spa']['p_l']:.3f}/{z['spa']['p_c']:.3f}/{z['spa']['p_u']:.3f}"
              f"  | roh p ueber Bloecke 5..60: {min(v['roh_p_min_max'][0] for k, v in emp.items() if k.startswith('block'))}..{max(v['roh_p_min_max'][1] for k, v in emp.items() if k.startswith('block'))}")
    print("     ", kosten, "Rang Kandidat", e["rang_kandidat"], "Sharpe", round(e["sharpe_kandidat"], 3), "zweitbeste", {k: round(v, 3) for k, v in e["sharpe_zweitbeste"].items()},
          "| Sharpe > 0:", e["anzahl_sharpe_positiv"], "von", d.shape[1])

# ------------------------------------------------------------------ C) Auswahlregel der Runde 3 unter H0
# Regel (scripts/suche_runde3.py:36-49): Punktzahl = schlechtester der vier Halbzeit-Sharpe-Werte (passiv/sofort x D1/D2), beste gewinnt.
print("C) Auswahlregel der Runde 3 (schlechtester von vier Halbzeit-Sharpe) unter H0 'kein Ertrag'")
so = lade("reihen_slip_5bp.csv")
pa = lade("reihen_passiv_5bp.csv")
sp = list(pa.columns)
so = so.loc[so.index < SPLIT, sp]
pa = pa.loc[pa.index < SPLIT, sp]
h1 = (so.index < D1_ENDE)


def punkt(a_d1, a_d2, b_d1, b_d2):
    f = lambda v: v.mean(axis=-2) / v.std(axis=-2, ddof=1) * np.sqrt(365)
    return np.minimum(np.minimum(f(a_d1), f(a_d2)), np.minimum(f(b_d1), f(b_d2)))


beob = punkt(so[h1].to_numpy(), so[~h1].to_numpy(), pa[h1].to_numpy(), pa[~h1].to_numpy())
print("   beobachtete Punktzahlen:", dict(zip(sp, np.round(beob, 3))))
zs = {"D1": (so[h1].to_numpy() - so[h1].to_numpy().mean(0), pa[h1].to_numpy() - pa[h1].to_numpy().mean(0)),
      "D2": (so[~h1].to_numpy() - so[~h1].to_numpy().mean(0), pa[~h1].to_numpy() - pa[~h1].to_numpy().mean(0))}
out["C_auswahlregel"] = {"punktzahl_beobachtet": dict(zip(sp, map(float, beob)))}
for block in (10, 20, 40):
    rng = np.random.default_rng(11)
    mx, einzel = [], []
    for a in range(0, 5000, 250):
        i1 = idx_stationaer(len(zs["D1"][0]), 250, block, rng)
        i2 = idx_stationaer(len(zs["D2"][0]), 250, block, rng)
        p = punkt(zs["D1"][0][i1], zs["D2"][0][i2], zs["D1"][1][i1], zs["D2"][1][i2])          # 250 x 10
        mx.append(p.max(axis=1)); einzel.append(p[:, sp.index(KAND)])
    mx, einzel = np.concatenate(mx), np.concatenate(einzel)
    out["C_auswahlregel"][f"block_{block}"] = {"p_beste_von_10": float((mx >= beob.max()).mean()), "schwelle_95": float(np.percentile(mx, 95)),
                                               "p_nur_kandidat": float((einzel >= beob[sp.index(KAND)]).mean())}
    print(f"   Block {block}: P(beste von 10 wirkungslosen >= {beob.max():.3f}) = {(mx >= beob.max()).mean():.3f}; 95-%-Schwelle {np.percentile(mx, 95):.3f};"
          f" nur Kandidat allein: {(einzel >= beob[sp.index(KAND)]).mean():.3f}")

# ------------------------------------------------------------------ D) Unsicherheit der Sharpe-Werte des Kandidaten
print("D) Kandidat: Sharpe, Bootstrap-Bereich (Bloecke 20 Tage, 5000 Ziehungen), t-Werte")
out["D_sharpe"] = {}
vor = lade("vorperiode_kandidat.csv")
for kosten in ("slip_yubit", "slip_5bp"):
    x = lade(f"reihen_{kosten}.csv")[KAND]
    fen = {"D1": x[x.index < D1_ENDE], "D2": x[(x.index >= D1_ENDE) & (x.index < SPLIT)], "Entwicklung": x[x.index < SPLIT],
           "Pruefung": x[x.index >= SPLIT], "Vorperiode": vor[kosten],
           "unabhaengig_zusammen(Vorperiode+Pruefung)": pd.concat([vor[kosten], x[x.index >= SPLIT]]),
           "alles(Vor+Entw+Pruef)": pd.concat([vor[kosten], x])}
    e = out["D_sharpe"][kosten] = {}
    for nm, v in fen.items():
        e[nm] = boot_sharpe(v)
        e[nm]["bereich_ueber_bloecke_p05"] = [boot_sharpe(v, block=b, seed=2)["p05"] for b in (5, 10, 40)]
        z = e[nm]
        print(f"   {kosten:10s} {nm:42s} Tage {z['tage']:4d} Summe {z['summe']:+.3f} Sharpe {z['sharpe']:+.3f} [{z['p05']:+.2f}; {z['p95']:+.2f}]"
              f"  Anteil<=0 {z['anteil_le_0']:.3f}  t {z['t_iid']:.2f} (HAC20 {z['t_hac20']:.2f})  p einseitig {z['p_einseitig_iid']:.3f}")
    # Stouffer: gleich gewichtete Zusammenfassung der beiden unabhaengigen t-Werte
    st = (e["Vorperiode"]["t_iid"] + e["Pruefung"]["t_iid"]) / sqrt(2)
    e["stouffer_unabhaengig"] = {"z": st, "p_einseitig": p_norm(st)}
    print(f"   {kosten:10s} Stouffer (Vorperiode, Pruefung): z = {st:.2f}, p einseitig = {p_norm(st):.3f}")

# ------------------------------------------------------------------ E) Pruefzeitraum: Abhaengigkeit von wenigen Tagen
print("E) Pruefzeitraum (Yubit-Kosten): Abhaengigkeit von wenigen Tagen")
x = lade("reihen_slip_yubit.csv")[KAND]
p = x[x.index >= SPLIT].sort_values(ascending=False)
out["E_pruefzeitraum"] = {"tage": int(len(p)), "summe": float(p.sum()), "jahr": float(p.mean() * 365),
                          "ohne_beste": {str(k): float(p.iloc[k:].sum()) for k in (1, 2, 3, 5, 10)},
                          "ohne_schlechteste": {str(k): float(p.iloc[:-k].sum()) for k in (1, 2, 3, 5, 10)},
                          "beste_5": {str(i.date()): float(v) for i, v in p.head(5).items()},
                          "schlechteste_5": {str(i.date()): float(v) for i, v in p.tail(5).items()},
                          "anteil_positive_tage": float((p > 0).mean()), "schiefe": float(((p - p.mean()) ** 3).mean() / p.std(ddof=0) ** 3)}
z = out["E_pruefzeitraum"]
print("   Tage", z["tage"], "Summe", round(z["summe"], 4), "pro Jahr", round(z["jahr"], 4), "| ohne beste k Tage:", {k: round(v, 3) for k, v in z["ohne_beste"].items()},
      "| ohne schlechteste k Tage:", {k: round(v, 3) for k, v in z["ohne_schlechteste"].items()})
print("   beste 5:", {k: round(v, 4) for k, v in z["beste_5"].items()}, "| schlechteste 5:", {k: round(v, 4) for k, v in z["schlechteste_5"].items()},
      "| Schiefe", round(z["schiefe"], 2), "| Anteil positiver Tage", round(z["anteil_positive_tage"], 3))
# dieselbe Probe fuer die Entwicklung (Vergleichsmassstab)
q = x[x.index < SPLIT].sort_values(ascending=False)
out["E_entwicklung_vergleich"] = {"tage": int(len(q)), "summe": float(q.sum()), "ohne_beste": {str(k): float(q.iloc[k:].sum()) for k in (5, 12)},
                                  "ohne_schlechteste": {str(k): float(q.iloc[:-k].sum()) for k in (5, 12)}}
print("   Vergleich Entwicklung:", {k: (round(v, 3) if not isinstance(v, dict) else {a: round(b, 3) for a, b in v.items()}) for k, v in out["E_entwicklung_vergleich"].items()})

# ------------------------------------------------------------------ F) Lage im Raster und zweiter Finalist (nur Gespeichertes / Entwicklung)
print("F) Trendlaenge im Raster (Sharpe in der ENTWICKLUNG, ohne Filter) und zweiter Finalist der Runde 3")
out["F_raster"] = {}
for kosten in ("slip_5bp", "slip_yubit"):
    d = lade(f"reihen_{kosten}.csv")
    d = d[d.index < SPLIT]
    z = {f"L{L}": float(d[f"tsmom_L{L}_biasFalse"].mean() / d[f"tsmom_L{L}_biasFalse"].std(ddof=1) * np.sqrt(365)) for L in (12, 24, 48, 96, 168, 336)}
    out["F_raster"][kosten] = z
    print("  ", kosten, {k: round(v, 3) for k, v in z.items()}, "-> laengste getestete Laenge ist die beste; ein Maximum ist im Raster nicht eingeschlossen")
g = json.load(open("reports/suche_runde3.json"))["finalisten"]
out["F_finalisten_runde3_gespeichert"] = {}
for n, e in g.items():
    s3 = e["stufen"].get("3_pruefung", {})
    z = {"stufe3_ok": s3.get("ok"), "pruefung_sofort_N": s3.get("sofort", {}).get("A", {}).get("Pruefung", {}).get("N"),
         "pruefung_sofort_sharpe": s3.get("sofort", {}).get("A", {}).get("Pruefung", {}).get("sharpe"),
         "pruefung_passiv_N": s3.get("passiv", {}).get("A", {}).get("Pruefung", {}).get("N"),
         "zufall_perzentil_gesamt": e["stufen"].get("4_zufall", {}).get("perzentil")}
    out["F_finalisten_runde3_gespeichert"][n] = z
    print("   reports/suche_runde3.json", n, z)
k = json.load(open("reports/kandidat.json"))["zufall_pruefung"]
r4 = json.load(open("reports/suche_runde4.json"))["breit_zufall_pruefung"]
out["F_zufallstest_pruefung_gespeichert"] = {"kandidat.json": k, "suche_runde4.json": r4}
print("   Zufallstest nur Pruefzeitraum (gespeichert): Gruppe A", k["perzentil"], "% | breites Portfolio", r4["perzentil"], "%")

json.dump(out, open(AUS, "w"), indent=1, default=float)
print("fertig")
