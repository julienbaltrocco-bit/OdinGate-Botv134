"""Runde 23: Merkmale zum Zeitpunkt eines Pump-Signals und die 15 Varianten. Alles nur aus Daten bis zum
Schluss der Signal-Kerze. Die 5-Minuten-Reihen dürfen Lücken haben (nicht geladene Monate)."""
import numpy as np
import pandas as pd


def _vor(s: pd.Series, delta: str) -> np.ndarray:
    """Wert der Reihe genau `delta` früher (NaN, wenn es die Kerze nicht gibt)."""
    return s.reindex(s.index - pd.Timedelta(delta)).to_numpy()


def merkmale(k: pd.DataFrame, funding: pd.Series | None) -> pd.DataFrame:
    c = k["close"]
    m = pd.DataFrame(index=k.index)
    c24 = _vor(c, "24h")
    m["r24"] = c.to_numpy() / c24 - 1
    m["r4"] = c.to_numpy() / _vor(c, "4h") - 1
    m["r7_davor"] = c24 / _vor(c, "8D") - 1
    hoch = k["high"].rolling("24h").max()
    m["unter_hoch"] = 1 - c / hoch
    v1 = k["quote_volume"].rolling("1h").sum()
    v25 = k["quote_volume"].rolling("25h").sum()
    m["vol_1h"] = v1
    m["vol_std_davor"] = (v25 - v1) / 24
    m["vol_24h"] = k["quote_volume"].rolling("24h").sum()
    voll = k["close"].rolling("24h").count() >= 280            # 24 Stunden fast lückenlos vorhanden
    m.loc[~voll, "r24"] = np.nan
    if funding is not None and len(funding):
        f = funding[~funding.index.duplicated(keep="last")].sort_index()
        m["funding"] = f.reindex(m.index.union(f.index)).ffill().reindex(m.index).to_numpy()
    else:
        m["funding"] = np.nan
    return m


VARIANTEN = {
    "roh": lambda m: m.r24 >= 0.20,
    "ab30": lambda m: m.r24 >= 0.30,
    "ab50": lambda m: m.r24 >= 0.50,
    "schnell": lambda m: (m.r24 >= 0.20) & (m.r4 >= 0.5 * m.r24),
    "langsam": lambda m: (m.r24 >= 0.20) & (m.r4 < 0.5 * m.r24),
    "funding_plus": lambda m: (m.r24 >= 0.20) & (m.funding > 0),
    "funding_hoch": lambda m: (m.r24 >= 0.20) & (m.funding >= 0.0003),
    "funding_minus": lambda m: (m.r24 >= 0.20) & (m.funding < 0),
    "gedreht": lambda m: (m.r24 >= 0.20) & (m.unter_hoch >= 0.05),
    "am_hoch": lambda m: (m.r24 >= 0.20) & (m.unter_hoch <= 0.02),
    "volumen_faellt": lambda m: (m.r24 >= 0.20) & (m.vol_1h < m.vol_std_davor),
    "aus_dem_tief": lambda m: (m.r24 >= 0.20) & (m.r7_davor < 0),
    "im_lauf": lambda m: (m.r24 >= 0.20) & (m.r7_davor >= 0.20),
    "liquide": lambda m: (m.r24 >= 0.20) & (m.vol_24h >= 20e6),
    "duenn": lambda m: (m.r24 >= 0.20) & (m.vol_24h < 5e6),
}


def begrenzen(t: pd.DataFrame, max_offen: int = 10) -> pd.DataFrame:
    """Höchstens `max_offen` Positionen gleichzeitig; spätere Signale verfallen. t nach ein_zeit sortiert."""
    t = t.sort_values("ein_zeit").reset_index(drop=True)
    offen, behalten = [], np.zeros(len(t), dtype=bool)
    ein, aus = t["ein_zeit"].to_numpy(), t["aus_zeit"].to_numpy()
    for i in range(len(t)):
        offen = [a for a in offen if a > ein[i]]
        if len(offen) < max_offen:
            behalten[i] = True
            offen.append(aus[i])
    return t[behalten].reset_index(drop=True)
