"""Runde 14: Tageskurse der Nicht-Krypto-Märkte von Yahoo Finance laden (Basiswerte der Yubit-Kontrakte)."""
import json
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
ZIEL = ROOT / "data/candles/tradfi_1d"
MAERKTE = {"SPY": "SPY", "QQQ": "QQQ", "IWM": "IWM", "EWJ": "EWJ", "EWY": "EWY", "XAU": "GC=F", "XAG": "SI=F", "XPT": "PL=F",
           "XPD": "PA=F", "COPPER": "HG=F", "CL": "CL=F", "BZ": "BZ=F", "NATGAS": "NG=F", "TBT": "TBT"}

ZIEL.mkdir(parents=True, exist_ok=True)
for name, sym in MAERKTE.items():
    url = (f"https://query1.finance.yahoo.com/v8/finance/chart/{urllib.parse.quote(sym)}"
           "?period1=1577836800&period2=1793000000&interval=1d")
    req = urllib.request.Request(url, headers={"User-Agent": "research-client/1.0"})
    for versuch in range(4):
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                roh = json.loads(r.read().decode())
            break
        except Exception as e:                      # noqa: BLE001
            print(name, "Fehler", e, file=sys.stderr)
            time.sleep(5 * (versuch + 1))
    else:
        raise SystemExit(f"{name}: kein Abruf möglich")
    res = roh["chart"]["result"][0]
    q = res["indicators"]["quote"][0]
    d = pd.DataFrame({k: q[k] for k in ("open", "high", "low", "close", "volume")},
                     index=pd.to_datetime(res["timestamp"], unit="s").normalize())
    d = d.dropna(subset=["close"])
    d = d[~d.index.duplicated(keep="last")].sort_index()
    d.to_parquet(ZIEL / f"{name}.parquet")
    print(f"{name:7s} {sym:5s} {str(d.index[0])[:10]} bis {str(d.index[-1])[:10]}  {len(d)} Tage  letzter {d['close'].iloc[-1]:.2f}")
    time.sleep(2)
