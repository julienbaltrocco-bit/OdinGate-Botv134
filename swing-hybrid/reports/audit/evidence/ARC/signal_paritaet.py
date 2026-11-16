"""ARC: Paritaet der Signalregel zwischen Forschung (research.tsmom / mutationen.basis / research._trend) und
Papier-Bot (vorwaertstest.bot.markt_lesen + kern.richtung), gerechnet auf denselben Binance-Stundenkerzen.
Nur lesend; keine Zustaende des Bots, kein Netz. Aufruf aus swing-hybrid: .venv/bin/python -I <dieses skript>
"""
import sys
sys.path.insert(0, "src"); sys.path.insert(0, ".")
import numpy as np, pandas as pd
from hybrid import research as R, mutationen as M
from vorwaertstest import bot, kern
from vorwaertstest.yubit import YubitFehler

m = R.markt(R.GRUPPE_A)
a, b, c = R.tsmom(m, 336), R._trend(m), M.basis(m)
print("Forschung intern: tsmom(336) == _trend() :", bool(a.equals(b)), "| tsmom(336) == mutationen.basis():", bool(a.equals(c)))
close = R._close(m)
print("Stundenraster:", close.index[0], "bis", close.index[-1], "| Zeilen:", len(close))
erwartet = pd.date_range(close.index[0], close.index[-1], freq="1h")
print("Fehlende Stunden im gemeinsamen Raster (alle Coins ohne Kerze):", len(erwartet.difference(close.index)))
print("NaN-Stunden je Coin (Coin ohne Kerze, andere haben eine):", close.isna().sum().to_dict())
warm = a.iloc[336:]
print("Signal == 0 nach Vorlauf, je Coin:", (warm == 0).sum().to_dict())
gleich = (close == close.shift(336)).iloc[336:].sum().to_dict()
print("  davon echte Gleichstaende (Schluss == Schluss vor 336 h):", gleich)

H = kern.STUNDE_MS
class Api:
    """Stellt die Binance-Stundenkerzen so bereit, wie bot.markt_lesen sie von Yubit abruft."""
    def __init__(self):
        self.t = {coin: {int(ts.value // 1_000_000): float(v) for ts, v in m.h1[coin]["close"].items()} for coin in m.coins}
        self.aufrufe = 0
    def kerzen(self, sym, minuten=60, limit=3, start_ms=None, ende_ms=None):
        d = self.t[sym.removesuffix("USDT")]
        if start_ms is not None:
            return [{"start": start_ms, "close": d[start_ms]}] if start_ms in d else []
        letzte = self.jetzt - self.jetzt % H            # laufende Stunde
        return [{"start": s, "close": d[s]} for s in (letzte - 2 * H, letzte - H, letzte) if s in d]
    def kontrakt(self, sym): return {"status": "Trading", "min_menge": 1e-9, "schritt": 1e-9, "tick": 1e-9, "funding_minuten": 480}
    def ticker(self, sym): return {"mark": 1.0, "funding": 0.0}
    def buch(self, sym, tiefe=25): return {"geld": [(1.0, 1e9)], "brief": [(1.0, 1e9)]}

api = Api()
stunden = close.index[336:]                              # Signal der Kerze H gilt ab H+1 (auf_raster verschiebt um 1 h)
zaehler = {"gleich": 0, "abweichend": 0, "bot_fehler_forschung_0": 0, "bot_fehler_forschung_signal": 0, "bot_aeltere_kerze": 0}
beispiele = []
for ts in stunden:
    api.jetzt = int(ts.value // 1_000_000) + H + 5 * 60_000      # 5 Minuten nach Schluss der Kerze ts
    for coin in m.coins:
        f = float(a.at[ts, coin])
        try:
            r = bot.markt_lesen(api, coin, api.jetzt)
        except YubitFehler as e:
            k = "bot_fehler_forschung_0" if f == 0 else "bot_fehler_forschung_signal"
            zaehler[k] += 1
            if len(beispiele) < 12: beispiele.append((str(ts), coin, f, "Bot: " + str(e)))
            continue
        if r["kerze"] != int(ts.value // 1_000_000):
            zaehler["bot_aeltere_kerze"] += 1
            if len(beispiele) < 12: beispiele.append((str(ts), coin, f, f"Bot nutzt aeltere Kerze {bot.utc(r['kerze'])}, Richtung {r['richtung']}"))
            continue
        if r["richtung"] == f: zaehler["gleich"] += 1
        else:
            zaehler["abweichend"] += 1
            if len(beispiele) < 12: beispiele.append((str(ts), coin, f, f"Bot Richtung {r['richtung']}"))
n = len(stunden) * len(m.coins)
print("Vergleich Bot gegen Forschung:", n, "Coin-Stunden |", zaehler)
for x in beispiele: print("  ", x)
