"""E22 Kaufdruck minütlich geprüft gegen Prüfung am Kerzenschluss (Festlegung: protokoll.md Abschnitt 38).

216 Paare, je zwei Arme, beide über denselben Simulator auf Minutenraster. Liest nur Training und Auswahlprüfung (bis 30.06.2024).
  .venv/bin/python -I forschung/experimente/e22_minute_kaufdruck.py     (aus swing-hybrid/, braucht data/fabrik und data/fabrik_minute)
"""
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

F = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(F))
from fabrik import daten as D, generator as G, kern as FK, lauf as L, minute as M

start = time.time()
LAENGEN, SCHWELLEN, HALTE = (1, 3, 12, 48), (1.5, 2.5, 3.5), {"h15": 3, "h60": 12, "h240": 48}
I0, IV, I1 = 5 * L.I_T, 5 * L.I_V1, 5 * L.I_ENDE                  # Minuten: Beginn Training, Beginn Auswahlprüfung, Ende
N_TAGE, TAG_V = (I1 - I0) // 1440, (IV - I0) // 1440
tag = np.maximum((np.arange(M.N) - I0) // 1440, 0).astype(np.int32)
schliesst = (np.arange(M.N) % 5) == 4
nC = len(D.COINS)
# Ergebnis: [Kostenmodell, Länge, Schwelle, Richtung, Haltedauer, Arm, Coin, (roh, n), Tag]
R = np.zeros((2, len(LAENGEN), len(SCHWELLEN), 2, len(HALTE), 2, nC, 2, N_TAGE))
leer = [np.zeros(N_TAGE) for _ in range(4)]
abgleich = []
for j, coin in enumerate(D.COINS):
    o, h, l = (np.asarray(M.laden(x)[j, :I1], dtype=np.float64) for x in ("o", "h", "l"))
    tq, qv = (np.asarray(M.laden(x)[j, :I1]) for x in ("tq", "qv"))
    ok = M.handelbar(np.asarray(M.laden("gueltig")[j, :I1]))
    fcum = M.fcum_minuten(np.asarray(D.laden("fcum")[j, :L.I_ENDE]))
    h5, l5, c5 = (np.asarray(D.laden(x)[j, :L.I_ENDE], dtype=np.float64) for x in ("h", "l", "c"))
    basis = float(D.laden("slip_bp")[j])
    slips = (np.full(I1, basis), M.slip_minuten(np.maximum(basis, L.SPANNEN_ANTEIL * (h5 - l5) / c5 * 1e4)))
    sigma, wert = np.ones(I1, np.float32), np.zeros(I1)
    for a, Lg in enumerate(LAENGEN):
        w = M.kaufdruck_minute(tq, qv, Lg)
        fab = np.asarray(D.laden("signale")[L.S.NAMEN.index(f"kaufdruck_{Lg}"), j, :L.I_ENDE], dtype=np.float64)
        g = np.isfinite(fab) & np.isfinite(w[4::5]); g[:L.I_T] = False
        abgleich.append(float(np.abs(fab[g] - w[4::5][g]).max()))
        for b, th in enumerate(SCHWELLEN):
            d0 = np.where(ok, np.where(w >= th, 1, np.where(w <= -th, -1, 0)), 0).astype(np.int8)
            for r, vz in enumerate((1, -1)):
                for arm in (0, 1):                                 # 0 = nur am Kerzenschluss, 1 = jede Minute
                    ein = (d0 * vz if arm else np.where(schliesst[:I1], d0 * vz, 0)).astype(np.int8)
                    for x, halte in enumerate(HALTE.values()):
                        for km, slip in enumerate(slips):
                            z = R[km, a, b, r, x, arm, j]
                            for q in leer:
                                q[:] = 0
                            FK.sim(o, h, l, fcum, ein, wert, sigma, tag, I0, I1, 5 * halte, 0.0, 0.0, 0.0, 0.0, np.nan, slip, L.KOSTEN85, z[0], z[1], *leer, 0)
    print(coin, f"{time.time() - start:.0f} s", flush=True)

K = L.KOSTEN85


def kenn(z, d0, d1, m):
    """z: [Coin, (roh, n), Tag] -> Trades, netto je Trade, Ertrag je Tag (bp des Kapitals), t-Wert der Tage."""
    roh, n = z[m, 0, d0:d1], z[m, 1, d0:d1]
    nt = n.sum()
    p = (roh.sum(0) - n.sum(0) * K) / len(m)
    s = p.std(ddof=1)
    return int(nt), (roh.sum() / nt - K if nt else 0.0), float(p.mean()), (float(p.mean() / s * np.sqrt(len(p))) if s > 0 else 0.0)


zeilen = []
for km, kosten in enumerate(("gemessen", "bewegt")):
    for a, Lg in enumerate(LAENGEN):
        for b, th in enumerate(SCHWELLEN):
            for r, vz in enumerate((1, -1)):
                for x, xn in enumerate(HALTE):
                    for mn, m in G.MAERKTE.items():
                        m = np.array(m)
                        zeile = {"kosten": kosten, "signal": f"kaufdruck_{Lg}", "th": th, "r": vz, "x": xn, "m": mn}
                        for arm, an in enumerate(("schluss", "minute")):
                            z = R[km, a, b, r, x, arm]
                            for seg, (d0, d1) in (("t", (0, TAG_V)), ("v", (TAG_V, N_TAGE))):
                                n, n85, tagbp, t = kenn(z, d0, d1, m)
                                zeile |= {f"n_{seg}_{an}": n, f"n85_{seg}_{an}": round(n85, 3), f"tag_{seg}_{an}": round(tagbp, 4), f"t_{seg}_{an}": round(t, 3)}
                        zeilen.append(zeile)
df = pd.DataFrame(zeilen)
aus = {"experiment": "e22_minute_kaufdruck", "gerechnet": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "paare": int(len(df) // 2),
       "abgleich_signal_groesste_abweichung": round(max(abgleich), 5)}
for kosten, g in df.groupby("kosten"):
    e = {}
    for seg in ("t", "v"):
        beide = (g[f"n_{seg}_schluss"] >= 30) & (g[f"n_{seg}_minute"] >= 30)
        gg = g[beide]
        e[seg] = {"paare_mit_trades": int(beide.sum()), "anteil_minute_besser_je_tag": round(float((gg[f"tag_{seg}_minute"] > gg[f"tag_{seg}_schluss"]).mean()), 3),
                  "anteil_minute_besser_je_trade": round(float((gg[f"n85_{seg}_minute"] > gg[f"n85_{seg}_schluss"]).mean()), 3),
                  "differenz_je_trade_mittel": round(float((gg[f"n85_{seg}_minute"] - gg[f"n85_{seg}_schluss"]).mean()), 2),
                  "differenz_je_trade_median": round(float((gg[f"n85_{seg}_minute"] - gg[f"n85_{seg}_schluss"]).median()), 2),
                  "n85_median_schluss": round(float(gg[f"n85_{seg}_schluss"].median()), 2), "n85_median_minute": round(float(gg[f"n85_{seg}_minute"].median()), 2),
                  "trades_verhaeltnis_median": round(float((gg[f"n_{seg}_minute"] / gg[f"n_{seg}_schluss"]).median()), 2)}
    for an in ("schluss", "minute"):
        gut = g[(g[f"n_t_{an}"] >= 200) & (g[f"n85_t_{an}"] > 0) & (g[f"t_t_{an}"] >= 2)]
        e[f"arme_training_t2_{an}"] = int(len(gut))
        e[f"davon_auswahlpruefung_positiv_{an}"] = int((gut[f"n85_v_{an}"] > 0).sum())
        e[f"arme_gueltig_{an}"] = int((g[f"n_t_{an}"] >= 200).sum())
    e["nach_richtung_training"] = {str(vz): {"anteil_minute_besser_je_tag": round(float((x["tag_t_minute"] > x["tag_t_schluss"]).mean()), 3),
                                             "differenz_je_trade_mittel": round(float((x["n85_t_minute"] - x["n85_t_schluss"]).mean()), 2)} for vz, x in g.groupby("r")}
    aus[kosten] = e
# Kontrolle gegen das Archiv der Generation 1 (Arm Kerzenschluss, gemessene Kosten)
arch = pd.read_parquet(F / "fabrik/ergebnisse/kandidaten.parquet", columns=["gen", "signal", "th", "r", "f", "k", "x", "m", "n_t", "n85_t", "n_v", "n85_v"])
arch = arch[(arch.gen == "gen1") & (arch.f == "kein") & (arch.k == 1) & arch.signal.astype(str).str.startswith("kaufdruck") & arch.x.isin(list(HALTE))]
for c in ("signal", "x", "m"):
    arch[c] = arch[c].astype(str)
v = df[df.kosten == "gemessen"].merge(arch, on=["signal", "th", "r", "x", "m"])
aus["kontrolle_archiv"] = {"paare": int(len(v)), "trades_abweichung_median_pct": round(float(((v.n_t_schluss - v.n_t).abs() / v.n_t.clip(lower=1)).median() * 100), 2),
                           "n85_training_abweichung_median_bp": round(float((v.n85_t_schluss - v.n85_t).abs().median()), 3),
                           "n85_training_abweichung_groesste_bp": round(float((v.n85_t_schluss - v.n85_t).abs().max()), 3),
                           "n85_training_korrelation": round(float(np.corrcoef(v.n85_t_schluss, v.n85_t)[0, 1]), 4)}
aus["rechenzeit_s"] = round(time.time() - start, 1)
(F / "ergebnisse/e22_minute_kaufdruck.json").write_text(json.dumps(aus, ensure_ascii=False, indent=1))
df.to_csv(F / "ergebnisse/e22_minute_kaufdruck_paare.csv", index=False)
print(json.dumps(aus, ensure_ascii=False, indent=1))
