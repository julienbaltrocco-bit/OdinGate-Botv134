"""ENG-H: Zerlegung des Kandidaten-Ergebnisses (engine2, Gruppe A, Einsatz 100 %, Yubit-Kosten, ohne Tageslimit) in
Handel vor Gebuehren, Gebuehr, Rebate, Funding je Zeitfenster. Nur lesend, keine Parameterwahl."""
import sys
sys.path.insert(0, "src")
import numpy as np, pandas as pd
from hybrid import research as R, runner, mutationen as M
m = R.markt(R.GRUPPE_A, vor=True)
l = R.lauf(m, R.auf_raster(m, M.basis(m)), taker=True, slip=R.yubit_kosten(m.coins)[0], day_limit=9.0)
print("Fenster        Tage  vor_Geb(G)  Gebuehr(F)  Funding  netto_ohne_Rebate  Rebate(R)  netto_mit(N)  N/Jahr  ohne_Rebate/Jahr  Rebate-Anteil an N")
for name, (a, b) in {"Entwicklung": (None, R.SPLIT), "Pruefung": (R.SPLIT, None), "Gesamt": (None, None)}.items():
    k = runner.kennzahlen(l, a, b); s = R.sicht(l, a, b)
    print(f"{name:12s} {k['tage']:6.0f} {s['G']:10.4f} {s['F']:11.4f} {k['funding']:8.4f} {s['handel']:18.4f} {s['R']:10.4f} {s['N']:13.4f} "
          f"{s['jahr_N']:7.4f} {s['handel'] / k['tage'] * 365:17.4f} {s['R'] / s['N']:10.2f}")
    assert abs(s["G"] - s["F"] - s["handel"]) < 1e-9 and abs(s["handel"] + s["R"] - s["N"]) < 1e-9   # G enthaelt das Funding bereits (runner.BRUTTO)
print("Identitaeten G - F = netto_ohne_Rebate und netto_ohne_Rebate + R = N: erfuellt. Achtung: G (runner \"brutto\") ENTHAELT das Funding; im Bot ist \"brutto\" OHNE Funding.")
print("Umsatz je Tag (x Kapital):", round(R.sicht(l)["vol_tag"], 4), "| Gebuehrensatz effektiv mit Rebate:", runner.TAKER * (1 - runner.MIT.rebate))
