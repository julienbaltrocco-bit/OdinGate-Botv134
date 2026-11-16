"""QD-Audit: Welche gespeicherten Ergebnisdateien enthalten Zahlen aus dem Pruefzeitraum (ab 01.04.2025)? Nur lesend.
Aufruf: .venv/bin/python -I reports/audit/evidence/QD/pruefzeitraum_einsichten.py"""
import json, re
from pathlib import Path
import pandas as pd
R = Path(__file__).resolve().parents[3]
MUSTER = re.compile(r"pruef|Pruef|haelfte_2|H2\b")
def pfade(x, pfad=""):
    if isinstance(x, dict):
        for k, v in x.items():
            p = f"{pfad}/{k}"
            if re.search(r"[Pp]ruef", str(k)):
                yield p
            else:
                yield from pfade(v, p)
    elif isinstance(x, list):
        for i, v in enumerate(x[:400]):
            yield from pfade(v, f"{pfad}[{i}]")
gesamt = 0
for f in sorted(R.glob("*.json")):
    try:
        d = json.loads(f.read_text())
    except Exception as e:
        print(f.name, "nicht lesbar", e); continue
    p = list(pfade(d))
    # Pfade verdichten: Listenindizes und Blattnamen zusammenfassen
    kurz = sorted({re.sub(r"\[\d+\]", "[]", x) for x in p})
    if kurz:
        gesamt += len(kurz)
        print(f"{f.name}: {len(kurz)} Stellen mit Pruefzeitraum-Zahlen")
        for x in kurz[:14]:
            print("     ", x)
        if len(kurz) > 14:
            print("      ... und", len(kurz) - 14, "weitere")
for f in sorted(R.glob("*.csv")):
    sp = [c for c in pd.read_csv(f, nrows=3).columns if re.search(r"[Pp]ruef", c)]
    inhalt = pd.read_csv(f)
    zus = ""
    if "fenster" in inhalt.columns:
        zus = f"; Zeilen mit fenster == 'Pruefung': {int((inhalt['fenster'] == 'Pruefung').sum())} (Regeln: {inhalt.loc[inhalt['fenster'] == 'Pruefung', 'regel'].nunique()})"
    if sp or zus:
        print(f"{f.name}: Spalten {sp}{zus}; Zeilen {len(inhalt)}")
print("\nJSON-Stellen insgesamt:", gesamt)
