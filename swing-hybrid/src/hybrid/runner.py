"""Läufe starten und auswerten: Baseline, Swing-mit-Limit, Hybrid. Kennzahlen für beliebige Zeitfenster."""
from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from . import config, data, engine
from .fees import Fees

CFG = config.load()
MAKER, TAKER = CFG["gebuehren"]["maker"], CFG["gebuehren"]["taker"]
OHNE = Fees(MAKER, TAKER, 0.0)
MIT = Fees(MAKER, TAKER, CFG["gebuehren"]["rebate_anteil"])
BRUTTO = Fees(0.0, 0.0, 0.0)
SLIP = 0.0005          # Slippage je Market-Order (wie im Labor)
EPS = 0.0001           # Limit gilt erst als gefüllt, wenn der Kurs 0,01 % DURCH den Preis handelt
TTL = CFG["ausfuehrung"]["order_ttl_minuten"] // 5
N_TR = 3               # Taktik-Tranchen je Coin (fest, nicht optimiert)
KERN = 0.5             # Kernanteil (fest, nicht optimiert)

VARIANTEN = {
    "baseline": dict(core_frac=1.0, core_market=True, n_tr=0, dip=0.0, tp=0.0, trail=False),
    "swing_limit": dict(core_frac=1.0, core_market=False, n_tr=0, dip=0.0, tp=0.0, trail=False),
}
RASTER = [dict(dip=d, tp=t, trail=tr) for d in (0.5, 1.0, 1.5) for t in (0.5, 1.0, 2.0) for tr in (False, True)]


def hybrid(dip, tp, trail):
    return dict(core_frac=KERN, core_market=False, n_tr=N_TR, dip=dip, tp=tp, trail=trail)


@dataclass
class Lauf:
    markt: data.Markt
    hebel: float
    params: dict
    eq_gross: np.ndarray
    MV: np.ndarray
    TV: np.ndarray
    FU: np.ndarray
    daily: np.ndarray
    trades: pd.DataFrame
    st: np.ndarray
    ORD: np.ndarray = None
    FIL: np.ndarray = None
    _cache: dict = field(default_factory=dict)

    def equity(self, fees: Fees) -> np.ndarray:
        """Kontoverlauf (Gewinn in Einheiten des Startkapitals) je 5-Minuten-Kerze."""
        return self.eq_gross - fees.maker * (1 - fees.rebate) * self.MV - fees.taker * (1 - fees.rebate) * self.TV + self.FU

    def daily_pnl(self, fees: Fees) -> pd.DataFrame:
        """Tagesgewinn je Coin (Zeilen = Tage, Spalten = Coins)."""
        d = self.daily
        kum = d[:, :, 0] - fees.maker * (1 - fees.rebate) * d[:, :, 1] - fees.taker * (1 - fees.rebate) * d[:, :, 2] + d[:, :, 3]
        kum = np.concatenate([np.zeros((kum.shape[0], 1)), kum], axis=1)
        return pd.DataFrame(np.diff(kum, axis=1).T, index=self.markt.days, columns=self.markt.coins)


def lauf(markt: data.Markt, hebel: float = None, **params) -> Lauf:
    hebel = hebel or CFG["risiko"]["hebel_standard"]
    S = hebel / len(markt.coins) * CFG["risiko"]["max_position_pro_paar"]
    p = dict(params)
    eq, MV, TV, FU, daily, tr, st, nt, ORD, FIL = engine.simulate(
        markt.o, markt.h, markt.l, markt.c, markt.w, markt.atr, markt.fund, markt.day, markt.hour_start, S,
        p["core_frac"], p["core_market"], p["n_tr"], p["dip"], p["tp"], p["trail"], TTL, EPS, SLIP, MAKER, TAKER,
        CFG["risiko"]["tagesverlust_limit"], 3_000_000)
    if nt > len(tr):
        raise RuntimeError("Trade-Speicher zu klein")
    t = pd.DataFrame(tr, columns=["coin", "art", "richtung", "ein", "aus", "brutto", "maker_vol", "taker_vol"])
    t["coin"] = [markt.coins[int(i)] for i in t["coin"]]
    t["art"] = np.where(t["art"] == 0, "kern", "taktik")
    t["ein_zeit"] = markt.index[t["ein"].astype(int)]
    t["aus_zeit"] = markt.index[t["aus"].astype(int)]
    t["stunden"] = (t["aus"] - t["ein"]) * 5 / 60
    return Lauf(markt, hebel, p, eq, MV, TV, FU, daily, t, st, ORD, FIL)


def max_drawdown(eq: np.ndarray) -> float:
    """Größter Rückgang vom Höchststand, bezogen auf den Kontostand am Höchststand (Startkapital = 1)."""
    konto = 1.0 + eq
    spitze = np.maximum.accumulate(np.maximum(konto, 1.0))
    return float(((spitze - konto) / spitze).max())


def kennzahlen(l: Lauf, von=None, bis=None) -> dict:
    """Kennzahlen im Zeitfenster [von, bis). Kapital = 1, also sind Gewinne direkt Renditen."""
    idx = l.markt.index
    a = 0 if von is None else int(idx.searchsorted(pd.Timestamp(von)))
    b = len(idx) if bis is None else int(idx.searchsorted(pd.Timestamp(bis)))
    tage = (b - a) / 288
    out = {"von": idx[a], "bis": idx[b - 1], "tage": tage}

    def delta(x):
        return float(x[b - 1] - (x[a - 1] if a > 0 else 0.0))

    for name, fees in (("brutto", BRUTTO), ("ohne", OHNE), ("mit", MIT)):
        eq = l.equity(fees)
        basis = eq[a - 1] if a > 0 else 0.0
        out[f"rendite_{name}"] = delta(eq)
        out[f"dd_{name}"] = max_drawdown(eq[a:b] - basis)
    mv, tv = delta(l.MV), delta(l.TV)
    out["volumen_tag"] = (mv + tv) / tage
    out["maker_anteil"] = mv / (mv + tv) if mv + tv > 0 else float("nan")
    out["gebuehr_tag"] = (MAKER * mv + TAKER * tv) / tage
    out["rebate_tag"] = out["gebuehr_tag"] * MIT.rebate
    out["funding"] = delta(l.FU)
    orders, fills = delta(l.ORD), delta(l.FIL)
    out["orders_tag"] = orders / tage
    out["order_zu_fill"] = orders / fills if fills else float("nan")
    t = l.trades[(l.trades["aus"] >= a) & (l.trades["aus"] < b)]
    out["trades"] = int(len(t))
    out["trades_kern"] = int((t["art"] == "kern").sum())
    out["trades_taktik"] = int((t["art"] == "taktik").sum())
    out["haltedauer_h"] = float(t["stunden"].mean()) if len(t) else float("nan")
    netto = t["brutto"] - MAKER * t["maker_vol"] - TAKER * t["taker_vol"]
    out["trefferquote"] = float((netto > 0).mean()) if len(t) else float("nan")
    # Klumpenrisiko: Anteil des größten Coins / Monats am Gewinn (netto ohne Rebate)
    d = l.daily_pnl(OHNE)
    d = d[(d.index >= idx[a].normalize()) & (d.index <= idx[b - 1].normalize())]
    gesamt = float(d.to_numpy().sum())
    out["anteil_coin"] = float(d.sum().max() / gesamt) if gesamt > 0 else float("nan")
    out["top_coin"] = str(d.sum().idxmax())
    monat = d.sum(axis=1).groupby(d.index.to_period("M")).sum()
    out["anteil_monat"] = float(monat.max() / gesamt) if gesamt > 0 else float("nan")
    out["top_monat"] = str(monat.idxmax())
    tg = d.sum(axis=1)
    out["sharpe_ohne"] = float(tg.mean() / tg.std() * np.sqrt(365)) if tg.std() > 0 else 0.0
    return out


def order_statistik(l: Lauf) -> dict:
    s = l.st
    return {"orders": int(s[0]), "fills": int(s[1]), "stornos": int(s[2]),
            "order_zu_fill": float(s[0] / s[1]) if s[1] else float("nan"),
            "min_standzeit_min": float(s[3] * 5) if s[3] < 1e8 else float("nan"),
            "sperrtage": int(s[4]), "verstoesse_beide_seiten": int(s[5]),
            "max_position_anteil": float(s[6]), "market_orders": int(s[7])}
