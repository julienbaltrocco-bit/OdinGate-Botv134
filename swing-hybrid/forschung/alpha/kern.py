"""Gemeinsames Werkzeug der Alpha-Forschung: Daten lesen (nur bis Ende Validierung), Trades bewerten, Kennzahlen.

Alle Größen je Trade in Basispunkten (bp) des Positionswerts. Kosten wie in forschung/protokoll.md, Abschnitt 4.
"""
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
from hybrid import research as R  # nur lesend: Kostenmessung und Coin-Gruppen

DATEN = ROOT / "data/candles"
ERG = ROOT / "forschung/ergebnisse"
COINS = list(R.GRUPPE_A)
E_VON, E_BIS = pd.Timestamp("2021-08-15"), pd.Timestamp("2023-07-01")      # Entwicklung (bis ausschließlich)
V_VON, V_BIS = pd.Timestamp("2023-07-01"), pd.Timestamp("2025-04-01")      # Validierung
SPERRE = pd.Timestamp("2025-04-01")                                         # ab hier wird in Runde 1 nichts gelesen
GEBUEHR = 8.0                                                               # Taker je Order in bp


def lesen(art: str, coin: str) -> pd.DataFrame:
    """Parquet aus data/candles/<art>/<coin>USDT.parquet, hart abgeschnitten vor dem gesperrten Prüfzeitraum."""
    d = pd.read_parquet(DATEN / art / f"{coin}USDT.parquet")
    return d[d.index < SPERRE]


def slippage_bp(coins) -> dict:
    """Slippage je Order in bp: 2 x gemessene halbe Yubit-Spanne, mindestens 0,5 bp (wie Runde 6)."""
    s, fehlt = R.yubit_kosten(list(coins))
    assert not fehlt, fehlt
    return {c: float(x) * 1e4 for c, x in zip(coins, s)}


def ohne_ueberlappung(ein: np.ndarray, aus: np.ndarray) -> np.ndarray:
    """Eine Position je Coin: Signale, die während einer offenen Position kämen, entfallen. Gibt Maske zurück."""
    ok = np.zeros(len(ein), bool)
    frei = -1
    for k in range(len(ein)):
        if ein[k] >= frei:
            ok[k] = True
            frei = aus[k]
    return ok


def trades(coin: str, kerzen: pd.DataFrame, ein: np.ndarray, aus: np.ndarray, richtung: np.ndarray, funding=None) -> pd.DataFrame:
    """Bewertet Trades: Einstieg zum Open der Kerze `ein`, Ausstieg zum Open der Kerze `aus` (Indizes in `kerzen`)."""
    o, zeit = kerzen["open"].to_numpy(), kerzen.index
    g = (ein < len(o)) & (aus < len(o)) & (aus > ein)
    ein, aus, richtung = ein[g], aus[g], richtung[g]
    roh = richtung * (o[aus] / o[ein] - 1) * 1e4
    t = pd.DataFrame({"coin": coin, "ein": zeit[ein], "aus": zeit[aus], "richtung": richtung, "roh": roh})
    t["funding"] = 0.0
    if funding is not None and len(t):
        ft, fr = funding.index.to_numpy(), funding["rate"].to_numpy() * 1e4
        kum = np.concatenate([[0.0], np.cumsum(fr)])
        a = np.searchsorted(ft, t["ein"].to_numpy(), side="right")     # Termine nach dem Einstieg ...
        b = np.searchsorted(ft, t["aus"].to_numpy(), side="right")     # ... bis einschließlich Ausstiegszeit
        t["funding"] = -richtung * (kum[b] - kum[a])                    # Long zahlt positive Rate
    return t


def netto(t: pd.DataFrame, slip: dict, faktor=1.0) -> pd.DataFrame:
    """Ergänzt Kosten und Nettospalten (bp je Trade)."""
    t = t.copy()
    t["slip"] = 2 * faktor * t["coin"].map(slip)
    t["g"] = t["roh"] - t["slip"] + t["funding"]                # nach Slippage und Funding, vor Gebühr
    t["n0"] = t["g"] - 2 * GEBUEHR                              # ohne Rebate
    t["n50"] = t["g"] - 2 * GEBUEHR * 0.50
    t["n85"] = t["g"] - 2 * GEBUEHR * 0.15
    return t


def t_tage(t: pd.DataFrame, spalte: str) -> float:
    """t-Wert des Mittels, nach Kalendertagen gebündelt (Trades eines Tages sind nicht unabhängig)."""
    tag = t.groupby(t["ein"].dt.floor("D"))[spalte].sum()
    return float(tag.mean() / (tag.std(ddof=1) / np.sqrt(len(tag)))) if len(tag) > 2 and tag.std() > 0 else float("nan")


def kennzahlen(t: pd.DataFrame, von=None, bis=None) -> dict:
    if von is not None:
        t = t[(t["ein"] >= von) & (t["ein"] < bis)]
    if not len(t):
        return {"trades": 0}
    tage = max(1.0, (t["ein"].max() - t["ein"].min()) / pd.Timedelta(days=1))
    gew, verl = t.loc[t["n85"] > 0, "n85"], t.loc[t["n85"] <= 0, "n85"]
    dauer = (t["aus"] - t["ein"]).dt.total_seconds() / 60
    return {"trades": int(len(t)), "trades_je_tag": round(len(t) / tage, 2), "haltedauer_min": round(float(dauer.mean()), 1),
            "roh": round(float(t["roh"].mean()), 2), "funding": round(float(t["funding"].mean()), 2),
            "slip": round(float(t["slip"].mean()), 2), "g": round(float(t["g"].mean()), 2),
            "n0": round(float(t["n0"].mean()), 2), "n50": round(float(t["n50"].mean()), 2), "n85": round(float(t["n85"].mean()), 2),
            "n85_median": round(float(t["n85"].median()), 2), "t_roh": round(t_tage(t, "roh"), 2), "t_n85": round(t_tage(t, "n85"), 2),
            "gewinnquote": round(float((t["n85"] > 0).mean()), 3),
            "profit_factor": round(float(gew.sum() / -verl.sum()), 3) if len(verl) and verl.sum() < 0 else None,
            "summe_n85_pct": round(float(t["n85"].sum()) / 100, 1), "summe_n0_pct": round(float(t["n0"].sum()) / 100, 1)}


def stufe0(t_roh: pd.DataFrame, slip: dict, e_von=E_VON, e_bis=E_BIS) -> dict:
    """Machbarkeit nach Protokoll: nur Entwicklungszeitraum."""
    t = netto(t_roh, slip)
    t = t[(t["ein"] >= e_von) & (t["ein"] < e_bis)]
    mitte = e_von + (e_bis - e_von) / 2
    k = kennzahlen(t)
    h1, h2 = kennzahlen(t, e_von, mitte), kennzahlen(t, mitte, e_bis)
    doppelt = kennzahlen(netto(t_roh, slip, 2.0), e_von, e_bis)
    ok = {"a_300_trades": k.get("trades", 0) >= 300,
          "b_n85_positiv_t2": bool(k.get("n85", -1) > 0 and k.get("t_n85", 0) >= 2),
          "c_roh_beide_haelften": bool(h1.get("roh", -1) > 0 and h2.get("roh", -1) > 0),
          "d_doppelte_slippage": bool(doppelt.get("n85", -1) > 0)}
    return {"gesamt": k, "haelfte1": h1, "haelfte2": h2, "doppelte_slippage_n85": doppelt.get("n85"),
            "huerden": ok, "bestanden": all(ok.values())}


def speichern(name: str, inhalt: dict, start: float):
    inhalt = {"experiment": name, "gerechnet": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
              "rechenzeit_s": round(time.time() - start, 1), **inhalt}
    ERG.mkdir(parents=True, exist_ok=True)
    (ERG / f"{name}.json").write_text(json.dumps(inhalt, indent=1, ensure_ascii=False, default=str))
    return inhalt


def zeile(name: str, k: dict) -> str:
    if not k.get("trades"):
        return f"{name:<34} keine Trades"
    return (f"{name:<34} n={k['trades']:>6} /Tag {k['trades_je_tag']:>5} halte {k['haltedauer_min']:>6}m | roh {k['roh']:>6} "
            f"fund {k['funding']:>5} slip {k['slip']:>5} | n0 {k['n0']:>7} n50 {k['n50']:>6} n85 {k['n85']:>6} | "
            f"t_roh {k['t_roh']:>5} t_n85 {k['t_n85']:>5} | Quote {k['gewinnquote']} PF {k['profit_factor']}")
