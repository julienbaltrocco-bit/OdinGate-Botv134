"""QD-Audit: Zahlen im Protokolltext (reports/suche_protokoll.md, Zeile angegeben) gegen die gespeicherten JSON/CSV-Dateien.
Nur lesend. Aufruf: .venv/bin/python -I reports/audit/evidence/QD/konsistenz_tabelle.py"""
import json
from pathlib import Path
import pandas as pd
R = Path(__file__).resolve().parents[3]
def j(n): return json.loads((R / n).read_text())
r3, k, r4, r5, g60 = j("suche_runde3.json"), j("kandidat.json"), j("suche_runde4.json"), j("suche_runde5.json"), j("gesamt_60.json")
r6, r7, r8, r9, r10, r11 = (j(f"suche_runde{i}.json") for i in (6, 7, 8, 9, 10, 11))
r13, r14, r15, r16, r17, r18, r19 = (j(f"suche_runde{i}.json") for i in (13, 14, 15, 16, 17, 18, 19))
r20a, r21, r22, r23, r24 = j("suche_runde20a.json"), j("suche_runde21.json"), j("suche_runde22.json"), j("suche_runde23.json"), j("suche_runde24.json")
s1 = pd.read_csv(R / "suche_stufe1.csv"); r2 = j("suche_runde2.json")
f3 = r3["finalisten"]["tsmom_L336_biasFalse"]["stufen"]
Z = [  # (Runde, Zeile im Protokoll, Aussage, Wert laut Protokoll, Wert aus Datei, Nachkommastellen)
 (1, 62, "Einstellungen, die Stufe 1 bestehen (von 30)", 3, int(s1["bestanden"].sum()), 0),
 (2, 98, "Einstellungen, die Stufe 1 bestehen", 1, sum(z["bestanden"] for z in r2["stufe1"]), 0),
 (3, 135, "Hebel des Kandidaten", 0.2, f3["5_hebel"]["hebel"], 2),
 (3, 136, "Pruefzeitraum netto mit Rebate, Hebel 0,2 (%)", 2.4, f3["5_hebel"]["Pruefung"]["N"] * 100, 1),
 (3, 136, "Zufallstest nur Pruefzeitraum (Perzentil)", 80, k["zufall_pruefung"]["perzentil"], -1),
 (4, 163, "Breites Portfolio Pruefzeitraum (%)", 5.5, r4["breit"]["Pruefung"]["N"] * 100, 1),
 (5, 205, "vol_beide schlechtere Haelfte (Sharpe)", 0.74, r5["entwicklung"]["vol_beide"]["score"], 2),
 (5, 205, "Basis schlechtere Haelfte (Sharpe)", 0.44, r5["entwicklung"]["basis"]["score"], 2),
 (5, 207, "Gruppe D Pruefzeitraum vol_beide (%)", -0.6, r5["D"]["vol_beide"]["Pruefung"]["N"] * 100, 1),
 (5, 211, "60 Coins Pruefzeitraum, Hebel 0,15 (%)", 2.7, g60["alle"]["Pruefung"]["N"] * 100, 1),
 (5, 211, "60 Coins gesamter Zeitraum (%)", 27.6, g60["alle"]["Gesamt"]["N"] * 100, 1),
 (6, 258, "Kandidat Yubit-Kosten Entwicklung, Hebel 0,2 (%)", 41.3, r6["teil1"]["A"]["Entwicklung"]["N"] * 100, 1),
 (6, 258, "Kandidat Yubit-Kosten Pruefzeitraum (%)", 5.2, r6["teil1"]["A"]["Pruefung"]["N"] * 100, 1),
 (6, 259, "dasselbe mit doppelten Kosten (%)", 1.2, r6["teil1"]["A"]["stress_2x"]["Pruefung"]["N"] * 100, 1),
 (6, 262, "Rangfolge Pruefzeitraum Gruppe A (%)", -5.5, r6["teil2"]["finalist"]["stufen"]["3_bestaetigung"]["A"]["Pruefung"]["N"] * 100, 1),
 (6, 265, "Kombination Pruefzeitraum (%)", 5.9, r6["teil3"]["kombination"]["Pruefung"]["N"] * 100, 1),
 (7, 322, "orderfluss Pruefzeitraum Gruppe A (%)", -18.2, r7["signale"]["orderfluss"]["stufen"]["3_bestaetigung"]["A"]["Pruefung"]["N"] * 100, 1),
 (8, 347, "23 guenstige Coins Pruefzeitraum (%)", 16.5, r8["guenstige_coins"]["Pruefung"]["N"] * 100, 1),
 (9, 372, "Top-20-Umsatz Entwicklung (%)", 22.4, r9["Entwicklung"]["N"] * 100, 1),
 (9, 372, "Top-20-Umsatz Pruefzeitraum (%)", 5.1, r9["Pruefung"]["N"] * 100, 1),
 (10, 461, "Listings Pruefzeitraum (%)", -107.7, r10["hebel1"]["Pruefung"]["N"] * 100, 1),
 (11, 506, "Zahl der Varianten", 602, r11["varianten"], 0),
 (11, 508, "Varianten, die Stufe 1 bestehen", 9, len(r11["stufe1"]), 0),
 (13, 639, "Niedrig-Risiko D2 vor Gebuehren (%)", -8.2, r13["stufen"]["1_entwicklung"]["D2"]["G"] * 100, 1),
 (14, 699, "Nicht-Krypto-Trend Entwicklung (%)", -66.4, r14["tradfi"]["Entwicklung"]["N"] * 100, 1),
 (14, 702, "Kandidat Sharpe Entwicklung (Einsatz 100 %)", 0.95, r14["kandidat"]["Entwicklung"]["sharpe"], 2),
 (14, 702, "Kandidat Sharpe Pruefzeitraum", 0.34, r14["kandidat"]["Pruefung"]["sharpe"], 2),
 (15, 736, "12-Monats-Trend Pruefzeitraum (%)", 18.7, r15["tradfi"]["Pruefung"]["N"] * 100, 1),
 (16, 790, "Kandidat Pruefzeitraum netto, Einsatz 100 % (%)", 25.8, r16["kandidat_A"]["Pruefung"]["N"] * 100, 1),
 (16, 790, "mit QQQ-Filter (%)", -22.4, r16["H2"]["A"]["Pruefung"]["N"] * 100, 1),
 (17, 838, "Aktien-Momentum Pruefzeitraum (%)", 33.5, r17["H2"]["netto"]["Pruefung"]["N"] * 100, 1),
 (18, 891, "Trades", 173, r18["alle"]["trades"], 0),
 (18, 893, "netto je Trade (%)", 0.92, r18["alle"]["netto_mittel"] * 100, 2),
 (19, 958, "fest5 Trades Entwicklung", 16064, r19["stufe1"]["fest5"]["Entwicklung"]["trades"], 0),
 (20, 996, "Teil A netto je Trade (%)", 0.14, r20a["alle"]["netto_mittel"] * 100, 2),
 (21, 1062, "Kandidat Sharpe D1", 0.56, r21["kandidat"]["D1"]["sharpe"], 2),
 (21, 1062, "Kandidat Sharpe D2", 1.32, r21["kandidat"]["D2"]["sharpe"], 2),
 (21, 1067, "Funding-Filter Vorsprung (Punkte/Jahr)", 10, r21["varianten"]["funding_filter"]["vorsprung_jahr"] * 100, 0),
 (21, 1068, "p-Wert der besten (%)", 84, r21["reality_check"]["p_beste"] * 100, 0),
 (21, 1068, "Schwelle (Punkte/Jahr)", 44, r21["reality_check"]["schwelle_95"] * 365 * 100, 0),
 (22, 1114, "Pruefzeitraum Sharpe Kandidat, 49 Coins", 0.38, r22["pruefzeitraum"]["kandidat"], 2),
 (22, 1115, "Vorperiode Sharpe mit Filter", 0.48, r22["vorperiode"]["variante"], 2),
 (23, 1208, "roh Trades", 4440, r23["varianten"]["roh"]["Entwicklung"]["trades"], 0),
 (24, 1270, "Kandidat Ertrag pro Jahr (%)", 59, r24["kandidat"]["Entwicklung"]["jahr"] * 100, 0),
 (24, 1271, "Kandidat Einbruch (%)", 24.6, r24["kandidat"]["Entwicklung"]["dd"] * 100, 1),
 (24, 1282, "sl5_tp15 Sharpe gesamt", 1.13, r24["varianten"]["sl5_tp15"]["Entwicklung"]["sharpe"], 2),
 (24, 1289, "p-Wert der besten (%)", 54, r24["reality_check"]["p_beste"] * 100, 0),
]
ok = 0; runden = set()
print(f"{'Runde':>5} {'Zeile':>5}  {'Aussage':52s} {'Protokoll':>10} {'Datei':>12}  Urteil")
for r, zeile, text, p, d, nd in Z:
    gleich = abs(round(float(d), max(nd, 0)) - float(p)) < 10 ** (-nd) * 0.5001 if nd >= 0 else abs(float(d) - float(p)) <= 1.0
    ok += gleich; runden.add(r)
    print(f"{r:5d} {zeile:5d}  {text:52s} {p:10} {float(d):12.4f}  {'stimmt' if gleich else 'WEICHT AB'}")
print(f"\n{ok} von {len(Z)} Stichproben stimmen, aus {len(runden)} Runden.")
