"""Datenspeicher der Fabrik: alle Rohreihen der zehn Coins auf einem gemeinsamen 5-Minuten-Raster als .npy-Dateien.

Liest nur über alpha.kern.lesen, also nie über den 31.03.2025 hinaus (Tresor). Jede Reihe ist so ausgerichtet, dass
ihr Wert an der Kerze i am Schluss dieser Kerze bekannt ist.

  .venv/bin/python -I forschung/fabrik/daten.py        (aus swing-hybrid/, einmalig, rund eine Minute)
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

F = Path(__file__).resolve().parents[1]
SPEICHER = F.parent / "data/fabrik"
COINS = ["BTC", "ETH", "SOL", "XRP", "DOT", "DOGE", "ADA", "LINK", "AVAX", "LTC"]
RASTER = pd.date_range("2021-07-01", "2025-03-31 23:55", freq="5min")
N = len(RASTER)


def _auf_raster(s: pd.Series) -> np.ndarray:
    return s.reindex(RASTER).to_numpy()


def bauen():
    sys.path.insert(0, str(F))
    from alpha import kern as K                                         # nur für den Aufbau aus den Rohdaten nötig (mit Tresor-Sperre)
    assert COINS == list(K.COINS)
    SPEICHER.mkdir(parents=True, exist_ok=True)
    felder = {k: np.full((len(COINS), N), np.nan, np.float64) for k in ("o", "h", "l", "c")}
    f32 = {k: np.full((len(COINS), N), np.nan, np.float32) for k in
           ("qv", "tq", "tqv", "frate", "oi", "konten_ls", "profis_ls", "taker_log", "prem", "b1", "a1", "b3", "a3", "b5", "a5", "b1l", "a1l")}
    fcum = np.zeros((len(COINS), N), np.float64)
    gueltig = np.zeros((len(COINS), N), bool)
    try:
        slip = K.slippage_bp(COINS)
    except FileNotFoundError:                                            # frische Sitzung: die Stichprobe vom 14.11.2026 liegt nicht im Repository
        import json
        slip = json.loads((F / "fabrik/slippage_gemessen.json").read_text())["slippage_bp_je_order"]
        print("Slippage aus fabrik/slippage_gemessen.json (dieselben Werte wie in Generation 1 und 2)", flush=True)
    for j, coin in enumerate(COINS):
        k = K.lesen("5m", coin)
        for x, sp in (("o", "open"), ("h", "high"), ("l", "low"), ("c", "close")):
            felder[x][j] = _auf_raster(k[sp])
        gueltig[j] = np.isfinite(felder["c"][j])
        c = pd.Series(felder["c"][j]).ffill().to_numpy()                 # Lücken: letzter Schluss, aber als ungültig markiert
        for x in ("o", "h", "l", "c"):
            felder[x][j] = np.where(gueltig[j], felder[x][j], c)
        f32["qv"][j] = _auf_raster(k["quote_volume"])
        m1 = K.lesen("1m", coin)                                         # Kauf-Marktorders je 5 Minuten aus den Minutenkerzen
        g = m1[["taker_quote", "quote_volume"]].resample("5min").sum(min_count=1)             # Lücke bleibt Lücke, nicht 0
        f32["tq"][j], f32["tqv"][j] = _auf_raster(g["taker_quote"]), _auf_raster(g["quote_volume"])
        fu = K.lesen("funding", coin)["rate"]
        fu.index = fu.index.floor("5min")
        fu = fu[~fu.index.duplicated()]
        r = fu.reindex(RASTER)
        fcum[j] = r.fillna(0.0).cumsum().to_numpy()                      # Funding fällt an der Kerze an, die zum Termin öffnet
        f32["frate"][j] = r.ffill().shift(1).to_numpy()                  # zuletzt festgestellte Rate, bekannt nach dem Termin
        m = K.lesen("metrics", coin)                                     # Stundenwerte: Stand am Ende der Stunde, nutzbar ab der Folgestunde
        for sp in ("oi", "konten_ls", "profis_ls", "taker_log"):
            s = m[sp].copy(); s.index = s.index + pd.Timedelta(hours=1)
            f32[sp][j] = s.reindex(RASTER, method="ffill", limit=12).to_numpy()
        f32["prem"][j] = _auf_raster(K.lesen("premium_5m", coin)["close"])
        t = K.lesen("tiefe_5m", coin)
        for st in (1, 3, 5):
            f32[f"b{st}"][j], f32[f"a{st}"][j] = _auf_raster(t[f"w-{st}"]), _auf_raster(t[f"w+{st}"])
        f32["b1l"][j], f32["a1l"][j] = _auf_raster(t["letzt_w-1"]), _auf_raster(t["letzt_w+1"])     # letzter 30-Sekunden-Schnappschuss der Kerze (Generation 4)
        print(coin, "Kerzen gültig:", int(gueltig[j].sum()), "Tiefe ab:", t.index.min().date(), flush=True)
    for k2, a in {**felder, **f32, "fcum": fcum, "gueltig": gueltig}.items():
        np.save(SPEICHER / f"{k2}.npy", a)
    np.save(SPEICHER / "slip_bp.npy", np.array([slip[c] for c in COINS]))
    print("gespeichert:", SPEICHER, f"{N} Kerzen x {len(COINS)} Coins")


def laden(name: str) -> np.ndarray:
    return np.load(SPEICHER / f"{name}.npy", mmap_mode="r")


if __name__ == "__main__":
    bauen()
