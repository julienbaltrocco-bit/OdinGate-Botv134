"""Kapitalverlauf, Margin und Liquidation für Trade-Listen (feste Größe je Coin = Kapital x Hebel / Anzahl Coins).

Annahmen (nicht von Yubit bestätigt): gemeinsame Margin, Erhaltungsmargin 1 % des offenen Positionswerts,
Liquidation, sobald Kontostand zum ungünstigsten Kurs der Haltedauer unter die Erhaltungsmargin fällt.
"""
import numpy as np
import pandas as pd

MMR = 0.01


def tagesreihe(t: pd.DataFrame, spalte: str, von, bis, n_coins: int, hebel=1.0) -> pd.Series:
    """Tagesergebnis in Anteilen des Startkapitals (ohne Zinseszins, feste Größe)."""
    tage = pd.date_range(von, bis - pd.Timedelta(days=1), freq="D")
    x = t[(t["ein"] >= von) & (t["ein"] < bis)]
    return (x.groupby(x["aus"].dt.floor("D"))[spalte].sum() / 1e4 * hebel / n_coins).reindex(tage, fill_value=0.0)


def kennzahlen(tag: pd.Series) -> dict:
    kum = tag.cumsum()
    rueck = (kum.cummax() - kum).max()
    jahr = tag.mean() * 365
    neg = tag[tag < 0]
    return {"ertrag_jahr_pct": round(float(jahr) * 100, 1), "sharpe": round(float(tag.mean() / tag.std() * np.sqrt(365)), 2) if tag.std() > 0 else None,
            "sortino": round(float(tag.mean() / np.sqrt((neg ** 2).sum() / len(tag)) * np.sqrt(365)), 2) if len(neg) else None,
            "rueckgang_pct_startkapital": round(float(rueck) * 100, 1), "summe_pct": round(float(kum.iloc[-1]) * 100, 1),
            "anteil_bester_tag": round(float(tag.max() / tag.sum()), 3) if tag.sum() > 0 else None,
            "gewinntage": round(float((tag > 0).sum() / max(1, (tag != 0).sum())), 3), "tage": int(len(tag))}


def starttage(t: pd.DataFrame, spalte: str, von, bis, n_coins: int, hebel: float) -> dict:
    """Jeder Kalendertag als Start mit Kapital 1: tiefster Kontostand (zum ungünstigsten Kurs offener Trades)."""
    x = t[(t["ein"] >= von) & (t["ein"] < bis)].sort_values("aus")
    f = hebel / n_coins / 1e4
    real = (x[spalte] * f).cumsum().to_numpy()                       # realisiert nach jedem Trade
    vor = np.concatenate([[0.0], real[:-1]])                         # Stand vor dem Trade (andere offene Trades vernachlässigt ...)
    tief = vor + (x["schlimmst"].to_numpy() - 2 * 0.5) * f            # ... dafür ungünstigster Kurs des Trades voll angesetzt
    sufmin = np.minimum.accumulate(np.minimum(tief, real)[::-1])[::-1]
    aus = x["aus"].to_numpy()
    tage = pd.date_range(von, bis - pd.Timedelta(days=30), freq="D")
    k = np.searchsorted(aus, tage.to_numpy())
    k = k[k < len(x)]
    basis = np.concatenate([[0.0], real])[k]
    tiefst = 1 + sufmin[k] - basis
    return {"starttage": int(len(k)), "tiefster_kontostand": round(float(tiefst.min()), 3),
            "anteil_unter_0.5": round(float((tiefst < 0.5).mean()), 4), "liquidationen": int((tiefst <= MMR * hebel).sum())}


def verlustserie(t: pd.DataFrame, spalte: str) -> int:
    v = (t.sort_values("aus")[spalte] <= 0).to_numpy()
    best = lauf = 0
    for x in v:
        lauf = lauf + 1 if x else 0
        best = max(best, lauf)
    return int(best)
