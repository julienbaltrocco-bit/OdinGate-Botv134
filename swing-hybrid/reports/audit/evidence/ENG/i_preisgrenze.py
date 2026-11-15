"""ENG-I: Papier fuellt das ganze Buch (25 Stufen) ohne Preisgrenze; live gilt ein Limit 0,05 % durch den Markt (bot.live_order).
Untere Schranke aus der Kopie von lauf/spannen.csv: Messungen, bei denen schon der DURCHSCHNITTSKURS der Standardorder jenseits
des Live-Limits lag (dann waere live sicher nur ein Teil gefuellt worden). Nur lesend."""
import csv, math, sys
from collections import defaultdict
sp = list(csv.DictReader(open(sys.argv[1], newline="")))
tick = {}
for r in sp:                                             # Tickgroesse aus den Nachkommastellen der Kurse (grobe, aber konservative Naeherung)
    for k in ("geld", "brief"):
        s = r[k]; n = len(s.split(".")[1]) if "." in s else 0
        tick[r["coin"]] = min(tick.get(r["coin"], 1.0), 10.0 ** -n)
z = defaultdict(lambda: [0, 0, 0])
for r in sp:
    if r["kauf_bp"] == "" or r["verkauf_bp"] == "":
        continue
    g, b = float(r["geld"]), float(r["brief"]); m = (g + b) / 2; t = tick[r["coin"]]
    kauf_vwap = m * (1 + float(r["kauf_bp"]) / 1e4); verk_vwap = m * (1 - float(r["verkauf_bp"]) / 1e4)
    lim_k = math.ceil(b * 1.0005 / t - 1e-9) * t; lim_v = math.floor(g * 0.9995 / t + 1e-9) * t
    e = z[r["coin"]]; e[0] += 1; e[1] += kauf_vwap > lim_k * (1 + 1e-9); e[2] += verk_vwap < lim_v * (1 - 1e-9)
print("Coin   Tick      Messungen  Kauf sicher nur teilgefuellt  Verkauf sicher nur teilgefuellt")
for c, (n, k, v) in z.items():
    print(f"{c:5s} {tick[c]:<9g} {n:6d} {k:14d} ({k / n * 100:4.1f} %) {v:18d} ({v / n * 100:4.1f} %)")
