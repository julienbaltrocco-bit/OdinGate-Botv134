"""Funding: Rohdatei (nur Zeilen vor 2024-07-01 gelesen) gegen fcum im Datenspeicher. Welche Kerze trägt den Termin?"""
import sys
import numpy as np, pandas as pd
import pyarrow.parquet as pq, pyarrow.dataset as ds, pyarrow as pa
sys.path.insert(0, 'forschung')
from fabrik import daten as D, lauf as L
ENDE = pd.Timestamp('2024-07-01')
fc = D.laden('fcum')
for j, coin in enumerate(D.COINS):
    pfad = f'data/candles/funding/{coin}USDT.parquet'
    schema = pq.read_schema(pfad)
    idxname = [n for n in schema.names if n not in ('rate',)][-1] if j == 0 else idxname
    if j == 0:
        print('Schema:', schema.names, [str(t) for t in schema.types], '| Indexspalte:', idxname)
    feld = ds.field(idxname)
    typ = schema.field(idxname).type
    tab = ds.dataset(pfad).to_table(filter=feld < pa.scalar(ENDE.to_datetime64(), type=typ) if pa.types.is_timestamp(typ) else None)
    d = tab.to_pandas()
    if idxname in d.columns:
        d = d.set_index(idxname)
    d = d[d.index < ENDE]
    assert d.index.max() < ENDE
    zeit = pd.DatetimeIndex(d.index).tz_localize(None) if getattr(d.index, 'tz', None) is not None else pd.DatetimeIndex(d.index)
    rate = d['rate'].to_numpy()
    # eigene Zuordnung: Termin t -> Kerze, die t enthält (floor 5 min)
    k = ((zeit - D.RASTER[0]) // pd.Timedelta('5min')).to_numpy()
    ok = (k >= 0) & (k < L.I_ENDE)
    eig = np.zeros(L.I_ENDE)
    np.add.at(eig, k[ok], rate[ok])
    eigc = np.cumsum(eig)
    f = np.asarray(fc[j, :L.I_ENDE])
    dup = pd.Series(k[ok]).duplicated().sum()
    versatz = (zeit - zeit.floor('5min')).total_seconds()
    std = pd.Series(zeit.hour).value_counts().sort_index().to_dict()
    print(f"{coin:<5} Termine {ok.sum():>5}  max|fcum-eigen| {np.abs(f - eigc).max():.3e}  doppelte Kerzen {dup}  Versatz zur Kerzenöffnung max {versatz.max():.3f}s  "
          f"Summe Rate T+V1 {rate[ok & (k >= L.I_T)].sum()*1e4:8.1f} bp  Stunden {std}")
