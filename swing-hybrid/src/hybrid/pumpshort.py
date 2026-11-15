"""Runde 18: Short nach Signal mit festem Ziel und Stop auf Minutenkerzen.

Einstieg zur Eröffnung der ersten Minutenkerze nach dem Signal. Ziel (Limit) unter, Stop (Market) über dem Einstieg.
Beide in derselben Minute: Stop zählt. Kerze eröffnet jenseits des Stops: deren Eröffnung gilt. Zeitausstieg nach
`max_h` Stunden. Je Coin höchstens eine Position.
"""
import numpy as np
import pandas as pd


def trades_coin(k: pd.DataFrame, signale, tp=0.10, sl=0.08, max_h=72) -> list[dict]:
    """k: Minutenkerzen (open/high/low/close, Index = Kerzenbeginn). signale: aufsteigend sortierte Zeitpunkte."""
    zeit = k.index.to_numpy()
    o, h, l, c = (k[x].to_numpy() for x in ("open", "high", "low", "close"))
    out, frei_ab = [], 0
    for s in signale:
        i = int(np.searchsorted(zeit, np.datetime64(s), side="right"))    # erste Kerze, die nach dem Signal beginnt
        if i >= len(zeit) or i < frei_ab:
            continue
        if (zeit[i] - np.datetime64(s)) > np.timedelta64(10, "m"):       # Datenlücke: kein Einstieg
            continue
        ein = o[i]
        ziel, stop = ein * (1 - tp), ein * (1 + sl)
        ende = int(np.searchsorted(zeit, zeit[i] + np.timedelta64(max_h, "h"), side="left"))
        art, aus, j = "zeit", None, i
        for j in range(i, min(ende, len(zeit))):
            if o[j] >= stop and j > i:
                art, aus = "stop", o[j]; break
            if h[j] >= stop:
                art, aus = "stop", stop; break
            if l[j] <= ziel:
                art, aus = "ziel", ziel; break
        if aus is None:
            j = min(ende, len(zeit) - 1)
            aus = o[j] if j < len(zeit) and ende < len(zeit) else c[-1]
            if ende >= len(zeit):
                art = "ende"
        out.append({"signal": pd.Timestamp(s), "ein_zeit": pd.Timestamp(zeit[i]), "aus_zeit": pd.Timestamp(zeit[j]),
                    "ein": ein, "aus": aus, "art": art, "roh": (ein - aus) / ein})
        frei_ab = j + 1
    return out


def kosten(t: pd.DataFrame, slip: float, taker=0.0008, maker=0.0004, rebate=0.85, slip_faktor=1.0) -> pd.Series:
    """Kosten je Trade als Anteil am Einsatz: Einstieg Taker + Slippage; Ziel Maker ohne, sonst Taker + Slippage."""
    f = 1.0 - rebate
    aus_wert = t["aus"] / t["ein"]
    ein = taker * f + slip * slip_faktor
    aus = np.where(t["art"] == "ziel", maker * f, taker * f + slip * slip_faktor) * aus_wert
    return ein + aus


def funding(t: pd.DataFrame, raten: pd.Series | None, ersatz_rate: pd.Series, ersatz_ab) -> pd.Series:
    """Funding je Trade aus Sicht des Shorts (positiv = Einnahme). `raten`: echte Sätze mit Zeitstempel;
    ab `ersatz_ab` der Satz aus dem Signal alle 8 Stunden (00/08/16 UTC)."""
    werte = []
    for (_, r), ers in zip(t.iterrows(), ersatz_rate):
        summe = 0.0
        if raten is not None and len(raten):
            x = raten[(raten.index > r["ein_zeit"]) & (raten.index <= r["aus_zeit"]) & (raten.index < ersatz_ab)]
            summe += float(x.sum())
        a = max(r["ein_zeit"], pd.Timestamp(ersatz_ab))
        if r["aus_zeit"] > a:
            raster = pd.date_range(a.ceil("8h"), r["aus_zeit"], freq="8h")
            summe += float(ers) * len(raster)
        werte.append(summe)
    return pd.Series(werte, index=t.index)
