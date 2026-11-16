"""Runde 10: neue Listings short gegen BTC long (Tagesdaten).

Jedes Paar: Coin short und BTC long mit gleichem Betrag, fest ab Einstieg. Alle Größen in Einheiten des Einsatzes
je Seite (1 = ein Paar mit vollem Einsatz). Die Skalierung auf das Konto (Zwanzigstel, Hebel) passiert in `portfolio`.
"""
import numpy as np
import pandas as pd

TAKER, REBATE = 0.0008, 0.85


def paar(coin: pd.Series, btc: pd.Series, f_coin: pd.Series, f_btc: pd.Series, einstieg: pd.Timestamp, haltetage: int,
         slip_coin: float, slip_btc: float, stop: float = 1.0) -> dict | None:
    """Tagesverlauf eines Paares. `coin`/`btc`: Tagesschlusskurse; `f_*`: Summe der Funding-Raten je Tag.

    Gibt None zurück, wenn am Einstiegstag kein Kurs vorliegt. Sonst je Tag: Kursgewinn, Funding, Slippage,
    gehandeltes Volumen (für die Gebühr), jeweils je Einheit Einsatz.
    """
    if einstieg not in coin.index or einstieg not in btc.index:
        return None
    ende = einstieg + pd.Timedelta(days=haltetage)
    tage = coin.index[(coin.index > einstieg) & (coin.index <= ende)]
    tage = tage[tage.isin(btc.index)]
    pc0, pb0 = coin[einstieg], btc[einstieg]
    kurs = pd.Series(0.0, index=tage); fund = pd.Series(0.0, index=tage)
    slip = pd.Series(0.0, index=tage); vol = pd.Series(0.0, index=tage)
    pc_alt, pb_alt, kum, grund, letzter = pc0, pb0, 0.0, "zeit", einstieg
    einstiegs_slip, einstiegs_vol = slip_coin + slip_btc, 2.0          # beide Seiten zum Einstieg
    for t in tage:
        pc, pb = coin[t], btc[t]
        kurs[t] = -(pc - pc_alt) / pc0 + (pb - pb_alt) / pb0             # Coin short, BTC long
        fund[t] = f_coin.get(t, 0.0) * pc_alt / pc0 - f_btc.get(t, 0.0) * pb_alt / pb0
        kum += kurs[t] + fund[t]
        pc_alt, pb_alt, letzter = pc, pb, t
        if kum <= -stop:
            grund = "stop"
            break
    if letzter == einstieg:
        return None                                                      # kein einziger Folgetag
    if grund == "zeit" and letzter < ende:
        grund = "datenende"
    tage = tage[tage <= letzter]
    kurs, fund, slip, vol = kurs[tage], fund[tage], slip[tage], vol[tage]
    slip.iloc[0] += einstiegs_slip
    vol.iloc[0] += einstiegs_vol
    slip.iloc[-1] += slip_coin * pc_alt / pc0 + slip_btc * pb_alt / pb0  # Ausstieg zum letzten Kurs
    vol.iloc[-1] += pc_alt / pc0 + pb_alt / pb0
    return {"einstieg": einstieg, "ausstieg": letzter, "grund": grund, "kurs": kurs, "funding": fund, "slippage": slip,
            "volumen": vol, "coin_rendite": pc_alt / pc0 - 1, "btc_rendite": pb_alt / pb0 - 1,
            "ergebnis": float(kurs.sum() + fund.sum() - slip.sum() - TAKER * (1 - REBATE) * vol.sum())}


def portfolio(paare: dict, index: pd.DatetimeIndex, anteil: float = 0.05) -> pd.DataFrame:
    """Tagesreihen des Portfolios je Einheit Kapital bei Hebel 1: jedes Paar mit `anteil` je Seite."""
    out = pd.DataFrame(0.0, index=index, columns=["kurs", "funding", "slippage", "volumen", "offen", "einsatz"])
    for p in paare.values():
        for k in ("kurs", "funding", "slippage", "volumen"):
            out[k] = out[k].add(p[k] * anteil, fill_value=0.0)
        aktiv = (index > p["einstieg"]) & (index <= p["ausstieg"])
        out.loc[aktiv, "offen"] += 1
        out.loc[aktiv, "einsatz"] += 2 * anteil
    out["brutto"] = out["kurs"] + out["funding"] - out["slippage"]          # vor Gebühren
    out["gebuehr"] = TAKER * out["volumen"]
    out["rebate"] = REBATE * out["gebuehr"]
    out["netto_ohne"] = out["brutto"] - out["gebuehr"]
    out["netto_mit"] = out["netto_ohne"] + out["rebate"]
    return out


def einbruch(tagesgewinn: pd.Series) -> float:
    konto = 1.0 + tagesgewinn.cumsum()
    spitze = np.maximum.accumulate(np.maximum(konto.to_numpy(), 1.0))
    return float(((spitze - konto.to_numpy()) / spitze).max()) if len(konto) else 0.0


def fenster(p: pd.DataFrame, von=None, bis=None, hebel: float = 1.0) -> dict:
    x = p
    if von is not None:
        x = x[x.index >= pd.Timestamp(von)]
    if bis is not None:
        x = x[x.index < pd.Timestamp(bis)]
    tage = max(len(x), 1)
    n = x["netto_mit"] * hebel
    return {"G": float(x["brutto"].sum() * hebel), "F": float(x["gebuehr"].sum() * hebel), "R": float(x["rebate"].sum() * hebel),
            "funding": float(x["funding"].sum() * hebel), "handel": float(x["netto_ohne"].sum() * hebel), "N": float(n.sum()),
            "dd_mit": einbruch(n), "jahr_N": float(n.sum() / tage * 365), "vol_tag": float(x["volumen"].mean() * hebel),
            "offen_mittel": float(x["offen"].mean()), "offen_max": float(x["offen"].max()),
            "einsatz_max": float(x["einsatz"].max() * hebel),
            "sharpe": float(n.mean() / n.std() * np.sqrt(365)) if n.std() > 0 else 0.0, "tage": int(len(x))}
