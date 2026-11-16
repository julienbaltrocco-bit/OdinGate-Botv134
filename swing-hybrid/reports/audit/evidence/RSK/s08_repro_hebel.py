"""RSK 08: Die Hebel-Tabelle der Forschung (reports/diagnose_kapital.json, suche_bericht.md Zeilen 318-331) unabhängig
nachrechnen: Kandidat, Gruppe A, Yubit-Kosten, MIT Tageslimit 3 %. Schreibt nichts ins Repo."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import numpy as np
import pandas as pd
from rsk_common import A, R, ROOT, runner

alt = {z["hebel"]: z for z in json.loads((ROOT / "reports/diagnose_kapital.json").read_text())["hebel"]}
m = R.markt(A)
K = R.yubit_kosten(A)[0]
w = R.auf_raster(m, R.variante(m, "basis"))
tage_p = (m.index[-1] - pd.Timestamp(R.SPLIT)).days + 1
tage_e = (pd.Timestamp(R.SPLIT) - m.index[0]).days
print("Hebel | Entwicklung N/Jahr (neu / gespeichert) | Einbruch Entw. (neu / gesp.) | Prüfzeitraum N/Jahr (neu / gesp.) | Einbruch Prüf. (neu / gesp.) | Sperrtage (neu / gesp.) | größte Abweichung")
for h in (0.2, 0.5, 1.0, 2.0, 3.0):
    l = R.lauf(m, w, hebel=h, taker=True, slip=K)                    # Tageslimit aus config.yaml (3 %)
    e, p = R.sicht(l, None, R.SPLIT), R.sicht(l, R.SPLIT, None)
    neu = {"entw_N_jahr": e["N"] / tage_e * 365, "entw_einbruch": e["dd_mit"], "pruef_N_jahr": p["N"] / tage_p * 365, "pruef_einbruch": p["dd_mit"], "sperrtage": int(l.st[4])}
    a = alt[h]
    abw = max(abs(neu[k] - a[k]) for k in neu)
    print(f"{h:5.1f} | {neu['entw_N_jahr']:+8.1%} / {a['entw_N_jahr']:+8.1%} | {neu['entw_einbruch']:7.1%} / {a['entw_einbruch']:7.1%} | {neu['pruef_N_jahr']:+8.1%} / {a['pruef_N_jahr']:+8.1%} | "
          f"{neu['pruef_einbruch']:7.1%} / {a['pruef_einbruch']:7.1%} | {neu['sperrtage']:5d} / {a['sperrtage']:5d} | {abw:.2e}")
print(f"Tageslimit laut config.yaml: {runner.CFG['risiko']['tagesverlust_limit']}, hebel_standard {runner.CFG['risiko']['hebel_standard']}, hebel_max {runner.CFG['risiko']['hebel_max']}")
