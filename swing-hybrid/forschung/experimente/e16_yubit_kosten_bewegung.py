"""E16 Yubit-Kosten in bewegten Minuten: gemessene Orderkosten des Papier-Bots gegen die Spanne der letzten Yubit-5-Minuten-Kerze.

Liest die Messungen von Test 1 nur (git show aus dem Zweig des Bots) und Yubit-Kerzen über die öffentliche Schnittstelle.
Nur Standardbibliothek:  python3 forschung/experimente/e16_yubit_kosten_bewegung.py   (aus swing-hybrid/)
"""
import csv
import io
import json
import statistics as st
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from vorwaertstest import yubit

start = time.time()
roh = subprocess.run(["git", "show", "origin/claude/intelligent-sagan-2cviug:swing-hybrid/vorwaertstest/lauf/spannen.csv"], capture_output=True, text=True, check=True).stdout
mess = list(csv.DictReader(io.StringIO(roh)))
ms = lambda s: int(datetime.strptime(s, "%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc).timestamp() * 1000)
t0, t1 = min(ms(m["zeit"]) for m in mess), max(ms(m["zeit"]) for m in mess)
y = yubit.Yubit()
zeilen = []
for coin in sorted({m["coin"] for m in mess}):
    kerzen, von = {}, (t0 // 300_000 - 2) * 300_000
    while von <= t1:                                                # Kerzen in Paketen zu 200 holen (Beginn und Ende müssen beide genannt sein)
        for x in y.kerzen(coin + "USDT", minuten=5, limit=200, start_ms=von, ende_ms=von + 199 * 300_000):
            kerzen[x["start"]] = x
        von += 200 * 300_000
    for m in mess:
        if m["coin"] != coin or not m["kauf_bp"]:
            continue
        letzte = (ms(m["zeit"]) // 300_000 - 1) * 300_000           # letzte abgeschlossene Kerze vor der Messung
        k = kerzen.get(letzte)
        if k:
            zeilen.append({"coin": coin, "zeit": m["zeit"], "spanne_kerze_bp": (k["high"] - k["low"]) / k["close"] * 1e4,
                           "kosten_bp": (float(m["kauf_bp"]) + float(m["verkauf_bp"])) / 2, "halbe_spanne_bp": float(m["spanne_bp"]) / 2})
zeilen.sort(key=lambda z: z["spanne_kerze_bp"])
n = len(zeilen)
teile = [zeilen[i * n // 5:(i + 1) * n // 5] for i in range(5)]
erg = {"messungen": n, "zeitraum": [mess[0]["zeit"], mess[-1]["zeit"]], "kerzen_ueber_100bp": sum(1 for z in zeilen if z["spanne_kerze_bp"] > 100),
       "kerzen_ueber_50bp": sum(1 for z in zeilen if z["spanne_kerze_bp"] > 50), "groesste_spanne_bp": round(zeilen[-1]["spanne_kerze_bp"], 1) if n else None,
       "fuenftel": [{"spanne_kerze_bp_mittel": round(st.mean(z["spanne_kerze_bp"] for z in t), 1), "kosten_bp_mittel": round(st.mean(z["kosten_bp"] for z in t), 2),
                     "kosten_anteil_spanne": round(st.mean(z["kosten_bp"] for z in t) / max(1e-9, st.mean(z["spanne_kerze_bp"] for z in t)), 3), "n": len(t)} for t in teile if t],
       "anteil_kosten_ueber_5pct_der_spanne": round(sum(1 for z in zeilen if z["kosten_bp"] > 0.05 * z["spanne_kerze_bp"]) / n, 3) if n else None,
       "je_coin": {c: {"kosten_bp": round(st.mean(z["kosten_bp"] for z in zeilen if z["coin"] == c), 2), "spanne_kerze_bp": round(st.mean(z["spanne_kerze_bp"] for z in zeilen if z["coin"] == c), 1)}
                   for c in sorted({z["coin"] for z in zeilen})}}
x, yv = [z["spanne_kerze_bp"] for z in zeilen], [z["kosten_bp"] for z in zeilen]
if n > 10:
    mx, my = st.mean(x), st.mean(yv)
    erg["steigung_kosten_je_bp_spanne"] = round(sum((a - mx) * (b - my) for a, b in zip(x, yv)) / sum((a - mx) ** 2 for a in x), 4)
    erg["korrelation"] = round(st.correlation(x, yv), 3)
erg = {"experiment": "e16_yubit_kosten_bewegung", "gerechnet": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "rechenzeit_s": round(time.time() - start, 1), **erg}
(ROOT / "forschung/ergebnisse/e16_yubit_kosten_bewegung.json").write_text(json.dumps(erg, indent=1, ensure_ascii=False))
print(json.dumps(erg, ensure_ascii=False, indent=1))
