"""Inventur der Kursdaten im Labor-Cache: Quelle, Symbol, Intervall, Zeitraum, Zeilen."""
import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT / "data/raw/labor-daten/trading-labor/trading-labor/cache"

z = []
for p in sorted(CACHE.rglob("*.parquet")):
    meta = p.with_suffix(".parquet.json")
    m = json.loads(meta.read_text()) if meta.exists() else {}
    df = pd.read_parquet(p)
    idx = df.index if isinstance(df.index, pd.DatetimeIndex) else pd.to_datetime(df.iloc[:, 0], errors="coerce")
    schritt = pd.Series(idx).diff().median() if len(df) > 1 else None
    z.append({"quelle": p.parent.name, "datei": p.name[:10], "zeilen": len(df), "von": idx.min(), "bis": idx.max(),
              "schritt": schritt, "spalten": ",".join(map(str, df.columns))[:60], "meta": json.dumps(m)[:160]})
t = pd.DataFrame(z)
t.to_csv(ROOT / "data/processed/cache_inventur.csv", index=False)
pd.set_option("display.width", 300, "display.max_rows", 400, "display.max_colwidth", 170)
print(t.head(6).to_string())
print(t.groupby(["quelle", "schritt"]).agg(n=("zeilen", "size"), zeilen=("zeilen", "sum"), von=("von", "min"), bis=("bis", "max")))
