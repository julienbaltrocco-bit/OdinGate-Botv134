"""E28, nur Daten (keine Ergebnisse): Kontraktlisten nach der Festlegung (Protokoll Abschnitt 56) und das Laden.

Teil 1: Binance-Archiv je Kontrakt (5-Minuten-Kerzen, Orderbuch-Tiefe als Übergewicht U je Kerze, Funding), geladen mit den
        Funktionen des Papier-Runners (kerzen_tag, tiefe_tag, funding_monat), damit das Signal genau so entsteht wie bei OS-1.1.
        Die großen Tiefe-Dateien werden nach dem Verdichten nicht aufbewahrt.
Teil 2: Stundenkerzen von Yubit (öffentliche Schnittstelle) je Kontrakt.

    python -m forschung.experimente.e28_daten teil1|teil2        (aus swing-hybrid/)
"""
import concurrent.futures
import datetime as dt
import json
import sys
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from forschung.experimente import e25_breites_universum as E25
from forschung.papier import runner as R

ZIEL = ROOT / "data/raw/e28"
ENDE_TEIL1 = dt.date(2026, 11, 20)                 # letzter Tag der Archivdaten
ERSTER_SPAETESTENS = pd.Timestamp("2026-07-31")
UMSATZ_BIS = pd.Timestamp("2026-10-31")
SPANNE_HOECHSTENS_BP = 10.0
ANZAHL_TEIL1 = 30
TIEFE_PCT = 5                                       # OS-1.1: Aufträge bis 5 % um den Kurs
YUBIT_VON = dt.datetime(2026, 1, 1, tzinfo=dt.timezone.utc)
YUBIT_BIS = dt.datetime(2026, 11, 17, tzinfo=dt.timezone.utc)   # bis einschließlich Montag, 16.11.2026


def kandidaten() -> pd.DataFrame:
    """Aktien-, Index- und Rohstoff-Kontrakte der Liste aus E25 mit erstem Tag, Werktagsumsatz (Median bis 31.10.2026) und Yubit-Spanne."""
    s = E25.symbole()
    s = s[s.tradfi].copy()
    spanne = E25.spannen()
    umsatz = []
    for sym in s.symbol:
        d = pd.read_parquet(ROOT / f"data/candles/1d/{sym}.parquet", columns=["quote_volume"])
        d = d[d.index <= UMSATZ_BIS]
        w = d[d.index.day_of_week < 5]["quote_volume"]
        umsatz.append(float(w.median()) if len(w) else 0.0)
    s["umsatz"] = umsatz
    s["spanne_bp"] = [spanne.get(x, float("nan")) for x in s.symbol]
    return s.reset_index(drop=True)


def universum_teil1() -> pd.DataFrame:
    k = kandidaten()
    k = k[(k.erster_tag <= ERSTER_SPAETESTENS) & (k.spanne_bp <= SPANNE_HOECHSTENS_BP)]
    return k.sort_values(["umsatz", "symbol"], ascending=[False, True]).head(ANZAHL_TEIL1).reset_index(drop=True)


def universum_teil2() -> pd.DataFrame:
    k = kandidaten()
    return k[k.spanne_bp <= SPANNE_HOECHSTENS_BP].sort_values("symbol").reset_index(drop=True)


def tage(erster: dt.date, letzter: dt.date) -> list:
    return [erster + dt.timedelta(days=i) for i in range((letzter - erster).days + 1)]


def laden_teil1(sym: str, erster: dt.date) -> dict:
    """Kerzen und Übergewicht U eines Kontrakts über alle Tage; schreibt <ZIEL>/teil1/<sym>.npz. Gibt eine kurze Zählung zurück."""
    ziel = ZIEL / "teil1" / f"{sym}.npz"
    if ziel.exists():
        return {"sym": sym, "schon_da": True}
    cache = ZIEL / "cache"
    kz, u, fehlend = [], {}, []
    for tag in tage(erster, ENDE_TEIL1):
        k = R.kerzen_tag(sym, tag, cache)
        with tempfile.TemporaryDirectory(dir=ZIEL) as tmp:           # Tiefe-Datei (rund 0,5 MB) nur zum Verdichten holen
            t = R.tiefe_tag(sym, tag, TIEFE_PCT, Path(tmp))
        if k is None or t is None:
            fehlend.append((str(tag), "kerzen" if k is None else "tiefe"))
        if k is not None:
            kz += k
        if t is not None:
            u.update(t)
    kz = sorted({x[0]: x for x in kz}.values())
    zeit = np.array([x[0] for x in kz], dtype=np.int64)
    ohlc = np.array([x[1:] for x in kz], dtype=float).reshape(-1, 4)
    ueber = np.array([u.get(int(z), np.nan) for z in zeit], dtype=float)
    monate = sorted({str(tag)[:7] for tag in tage(erster, ENDE_TEIL1)})
    fund = {}
    for m in monate:
        f = R.funding_monat(sym, m, cache)
        if f:
            fund.update(f)
    ziel.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(ziel, zeit=zeit, ohlc=ohlc, u=ueber, fund_zeit=np.array(sorted(fund), dtype=np.int64),
                        fund_rate=np.array([fund[z] for z in sorted(fund)], dtype=float), fehlend=np.array(json.dumps(fehlend)))
    return {"sym": sym, "kerzen": len(zeit), "u_vorhanden": int(np.isfinite(ueber).sum()), "funding": len(fund), "fehlende_dateien": len(fehlend)}


def laden_teil2(sym: str) -> dict:
    """Stundenkerzen von Yubit; schreibt <ZIEL>/teil2/<sym>.npz."""
    from vorwaertstest.yubit import Yubit
    ziel = ZIEL / "teil2" / f"{sym}.npz"
    if ziel.exists():
        return {"sym": sym, "schon_da": True}
    api, H = Yubit(pause=0.25), 3_600_000
    a, ende, alle = int(YUBIT_VON.timestamp() * 1000), int(YUBIT_BIS.timestamp() * 1000), {}
    while a < ende:
        b = min(a + 999 * H, ende)
        for k in api.kerzen(sym, 60, 1000, a, b):
            if k["start"] < ende:
                alle[k["start"]] = (k["open"], k["high"], k["low"], k["close"])
        a = b + H
    zeit = np.array(sorted(alle), dtype=np.int64)
    ziel.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(ziel, zeit=zeit, ohlc=np.array([alle[z] for z in zeit], dtype=float).reshape(-1, 4))
    return {"sym": sym, "stunden": len(zeit), "von": str(pd.Timestamp(zeit[0], unit="ms")) if len(zeit) else "", "abrufe": api.aufrufe}


def main(teil: str) -> None:
    if teil == "teil1":
        u = universum_teil1()
        print("Teil 1:", len(u), "Kontrakte:", " ".join(u.symbol), flush=True)
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as ex:
            for r in ex.map(lambda z: laden_teil1(z.symbol, z.erster_tag.date()), list(u.itertuples())):
                print(r, flush=True)
    else:
        u = universum_teil2()
        print("Teil 2:", len(u), "Kontrakte", flush=True)
        for z in u.itertuples():                                       # nacheinander, höflich gegenüber der Börse
            try:
                print(laden_teil2(z.symbol), flush=True)
            except Exception as e:
                print({"sym": z.symbol, "fehler": str(e)[:120]}, flush=True)
    print("fertig", teil, flush=True)


if __name__ == "__main__":
    main(sys.argv[1])
