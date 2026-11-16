"""Spannen-Stichprobe bei Yubit: alle N Minuten Geld-/Briefkurs aller Kontrakte (ein einziger öffentlicher Abruf je Messung).

    .venv/bin/python -I scripts/yubit_spannen_sammeln.py <minuten> <abstand_minuten>

Schreibt data/processed/yubit_spannen_stichprobe.csv (zeit, symbol, geld, brief). Kein Konto, keine Orders.
"""
import csv
import json
import sys
import time
import urllib.request
from pathlib import Path

ZIEL = Path(__file__).resolve().parents[1] / "data/processed/yubit_spannen_stichprobe.csv"
URL = "https://openapi.yubit.com/oapi/contract/market/public/v1/tickers"
dauer, abstand = float(sys.argv[1]) * 60, float(sys.argv[2]) * 60
ende = time.time() + dauer
ZIEL.parent.mkdir(parents=True, exist_ok=True)
neu = not ZIEL.exists()
n = 0
while True:
    try:
        with urllib.request.urlopen(urllib.request.Request(URL, headers={"User-Agent": "vorwaertstest/1.0"}), timeout=30) as r:
            d = json.loads(r.read())
        zeit = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime())
        with open(ZIEL, "a", newline="") as f:
            w = csv.writer(f)
            if neu:
                w.writerow(["zeit", "symbol", "geld", "brief"]); neu = False
            for t in d["data"]["list"]:
                if t.get("bidPrice") and t.get("askPrice"):
                    w.writerow([zeit, t["symbol"], t["bidPrice"], t["askPrice"]])
        n += 1
        print(zeit, "Messung", n, flush=True)
    except Exception as e:  # eine fehlgeschlagene Messung überspringen, nicht abbrechen
        print("Fehler:", e, flush=True)
    if time.time() + abstand > ende:
        break
    time.sleep(abstand)
print("fertig:", n, "Messungen")
