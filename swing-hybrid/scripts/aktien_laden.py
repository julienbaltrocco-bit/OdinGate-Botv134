"""Runde 17: Tageskurse der Aktien hinter den Yubit-Kontrakten (Yahoo Finance) und Yubit-Spannen dazu."""
import json
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "vorwaertstest"))
import kern
import yubit

ZIEL = ROOT / "data/candles/aktien_1d"
ZIEL.mkdir(parents=True, exist_ok=True)
y = yubit.Yubit()
info = {}
for s in [x.strip() for x in open(ROOT / "scripts/listings_ausschluss.txt") if x.strip()]:
    p = ROOT / f"data/candles/1d/{s}.parquet"
    if not p.exists() or pd.read_parquet(p).index[0] < pd.Timestamp("2026-01-01"):
        continue
    k = s[:-4]
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{urllib.parse.quote(k)}?period1=1577836800&period2=1793000000&interval=1d"
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "research-client/1.0"}), timeout=30) as r:
            res = json.loads(r.read().decode())["chart"]["result"][0]
    except Exception as e:                                  # noqa: BLE001
        info[k] = {"ok": False, "grund": str(e)[:80]}
        time.sleep(1.5)
        continue
    art = res["meta"].get("instrumentType")
    if art != "EQUITY" or "timestamp" not in res:
        info[k] = {"ok": False, "grund": f"Typ {art}"}
        time.sleep(1.5)
        continue
    q = res["indicators"]["quote"][0]
    d = pd.DataFrame({c: q[c] for c in ("open", "close")}, index=pd.to_datetime(res["timestamp"], unit="s").normalize()).dropna()
    d = d[~d.index.duplicated(keep="last")].sort_index()
    d.to_parquet(ZIEL / f"{k}.parquet")
    try:
        sp = sum(kern.spanne_bp(y.buch(s, 5)) for _ in range(2)) / 2
    except Exception:                                       # noqa: BLE001
        sp = None
    info[k] = {"ok": True, "von": str(d.index[0])[:10], "tage": len(d), "spanne_bp": sp, "boerse": res["meta"].get("exchangeName")}
    time.sleep(1.5)
(ROOT / "reports/runde17_aktien.json").write_text(json.dumps(info, indent=1))
ok = [k for k, v in info.items() if v["ok"]]
print(len(info), "geprüft,", len(ok), "Aktien geladen;", "ausgelassen:", {k: v["grund"] for k, v in info.items() if not v["ok"]})
