"""V-QR-02 (d): nur lesend. Im Papier-Test gemessene Kosten je Order (Buch-Fill gegen Mitte) gegen die Annahme der Rueckrechnung.
Aufruf (aus swing-hybrid/): .venv/bin/python -I -B -W ignore <Skript>
"""
import sys
sys.path.insert(0, "src")
import numpy as np
import pandas as pd
from hybrid import research as R

kA = dict(zip(R.GRUPPE_A, R.yubit_kosten(R.GRUPPE_A)[0] * 1e4))
for lauf in ("lauf", "lauf_tpsl"):
    s = pd.read_csv(f"vorwaertstest/{lauf}/spannen.csv")
    p = pd.read_csv(f"vorwaertstest/{lauf}/protokoll.csv")
    z = pd.to_datetime(s["zeit"])
    g = s.groupby("coin").agg(n=("spanne_bp", "size"), halbe_spanne_bp=("spanne_bp", lambda x: x.mean() / 2),
                              kauf_bp=("kauf_bp", "mean"), verkauf_bp=("verkauf_bp", "mean"),
                              max_bp=("kauf_bp", "max")).reindex(R.GRUPPE_A)
    g["je_order_bp"] = (g["kauf_bp"] + g["verkauf_bp"]) / 2
    g["annahme_bp"] = pd.Series(kA)
    print(f"{lauf}: {len(s)} Messungen, {z.min()} bis {z.max()} ({z.min().day_name()}), Messzeitpunkte {z.nunique()}, Ordergroesse Median {s['volumen'].median():.0f} USDT")
    print(g.round(3).to_string())
    print(f"  Mittel je Order {g['je_order_bp'].mean():.3f} bp gegen Annahme {g['annahme_bp'].mean():.3f} bp | Papier-Orders: {len(p)}, Slippage Mittel {p['slippage_bp'].mean():.3f} bp, "
          f"Rebate/Gebuehr im Protokoll: {p['rebate'].sum() / p['gebuehr'].sum():.4f} (gerechnet, nicht gemessen), modus: {sorted(p['modus'].unique())}\n")
