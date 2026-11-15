"""Runde 23: 5-Minuten-Kerzen und Funding für die Coin-Monate mit großen Sprüngen laden (data/processed/pump_monate.csv)."""
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import kerzen_laden as K

ROOT = Path(__file__).resolve().parents[1]
ZK, ZF = ROOT / "data/candles/pump_5m", ROOT / "data/candles/pump_5m_funding"
ZK.mkdir(parents=True, exist_ok=True); ZF.mkdir(parents=True, exist_ok=True)
plan = pd.read_csv(ROOT / "data/processed/pump_monate.csv").groupby("symbol")["monat"].apply(list)


def coin(args):
    sym, monate = args
    if (ZK / f"{sym}.parquet").exists():
        return sym, -1, -1
    ks, fs = [], []
    for m in monate:
        c = K.holen(f"{K.BASIS}/klines/{sym}/5m/{sym}-5m-{m}.zip")
        if c is not None:
            df = K.csv_aus_zip(c)
            df.columns = K.SPALTEN[: len(df.columns)]
            df.index = pd.to_datetime(df["open_time"].astype("int64"), unit="ms")
            ks.append(df[["open", "high", "low", "close", "quote_volume"]].astype("float64"))
        c = K.holen(f"{K.BASIS}/fundingRate/{sym}/{sym}-fundingRate-{m}.zip")
        if c is not None:
            x = K.csv_aus_zip(c)
            fs.append(pd.Series(x.iloc[:, -1].astype(float).to_numpy(), index=pd.to_datetime(x.iloc[:, 0].astype("int64"), unit="ms")))
    if ks:
        d = pd.concat(ks).sort_index()
        d[~d.index.duplicated()].to_parquet(ZK / f"{sym}.parquet")
    if fs:
        f = pd.concat(fs).sort_index()
        pd.DataFrame({"rate": f[~f.index.duplicated()]}).to_parquet(ZF / f"{sym}.parquet")
    return sym, len(ks), len(fs)


with ThreadPoolExecutor(8) as ex:
    n = 0
    for sym, k, f in ex.map(coin, list(plan.items())):
        n += 1
        if n % 20 == 0 or k == 0:
            print(n, sym, k, f, flush=True)
print("fertig", n)
