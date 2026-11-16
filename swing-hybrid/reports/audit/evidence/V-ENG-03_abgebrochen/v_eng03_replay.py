"""V-ENG-03, Teil A: unabhaengige Gegenpruefung mit dem ECHTEN Bot-Code (vorwaertstest.bot.schritt).

Eine nachgestellte Boerse spielt die Binance-5-Minuten-Historie des ENTWICKLUNGSZEITRAUMS (bis 2025-04-01) ab.
Der unveraenderte Bot (Konfiguration wie config_lauf_tpsl.json: tp 0.15, sl 0.05, Tageslimit 1.0; nur kapital_usd
und hebel fuer die Vergleichbarkeit auf 1.000.000 / 1.0 gesetzt) laeuft darauf einmal je Stunde und einmal alle
5 Minuten. Keine Parameterwahl, keine Daten des Pruefzeitraums. Schreibt nur in ein temporaeres Verzeichnis.

Aufruf:  .venv/bin/python -I -B v_eng03_replay.py <ausgabe.json> [tage]
"""
import json
import sys
import tempfile
import time
from pathlib import Path

WURZEL = "/home/user/OdinGate-Botv134/swing-hybrid"
sys.path.insert(0, WURZEL + "/src")
sys.path.insert(0, WURZEL)
import numpy as np
import pandas as pd
from hybrid import research as R
from vorwaertstest import bot, kern

H = kern.STUNDE_MS
BAR = 300_000


class Historie:
    """Nachgestellte Boerse: Mittelkurs = Open des laufenden 5-Minuten-Bars, Buch = Open -/+ Slippage je Coin
    (dieselbe Annahme wie research.yubit_kosten), Stundenkerzen = Stundenschluesse aus denselben 5-Minuten-Kerzen."""
    key = secret = ""

    def __init__(self, m, slip, takt_min):
        self.m, self.slip, self.takt_min, self.aufrufe, self.t = m, slip, takt_min, 0, 0
        self.ix = {c: j for j, c in enumerate(m.coins)}
        self.t0_ms = int(m.index[0].value // 1_000_000)
        h0 = min(s.index[0] for s in m.h1.values())
        h1 = max(s.index[-1] for s in m.h1.values())
        hidx = pd.date_range(h0, h1, freq="1h")
        self.h0_ms = int(h0.value // 1_000_000)
        self.hc = np.vstack([m.h1[c]["close"].reindex(hidx).to_numpy(dtype=np.float64) for c in m.coins])
        self.nh = self.hc.shape[1]

    def jetzt_ms(self):
        return self.t0_ms + self.t * BAR

    def _schluss(self, j, start_ms):
        d = start_ms - self.h0_ms
        if d % H != 0:
            return None
        k = d // H
        if 0 <= k < self.nh and np.isfinite(self.hc[j, k]):
            return float(self.hc[j, k])
        return None

    def kerzen(self, sym, minuten=60, limit=3, start_ms=None, ende_ms=None):
        j = self.ix[sym[:-4]]
        if start_ms is not None:
            c = self._schluss(j, start_ms)
            return [] if c is None else [{"start": start_ms, "open": 0, "high": 0, "low": 0, "close": c}]
        jetzt = self.jetzt_ms()
        lauf = jetzt - jetzt % H
        out = []
        for s in (lauf - 2 * H, lauf - H):
            c = self._schluss(j, s)
            if c is not None:
                out.append({"start": s, "open": 0, "high": 0, "low": 0, "close": c})
        out.append({"start": lauf, "open": 0, "high": 0, "low": 0, "close": float(self.m.o[j, self.t])})   # laeuft noch
        return out

    def kontrakt(self, sym):
        # funding_minuten = Lauf-Takt: so bucht der Bot das Funding genau wie engine2 (Satz des Bars x Open x Position)
        return {"status": "Trading", "min_menge": 1e-9, "schritt": 1e-9, "tick": 1e-8, "funding_minuten": self.takt_min}

    def ticker(self, sym):
        j = self.ix[sym[:-4]]
        p = float(self.m.o[j, self.t])
        a = max(0, self.t - self.takt_min // 5 + 1)                        # alle seit dem vorigen Lauf faelligen Saetze
        return {"geld": p, "brief": p, "letzter": p, "mark": p, "funding": float(self.m.fund[j, a:self.t + 1].sum()), "umsatz24h": 1e9}

    def buch(self, sym, tiefe=25):
        j = self.ix[sym[:-4]]
        p = float(self.m.o[j, self.t])
        s = float(self.slip[j])
        return {"geld": [(p * (1 - s), 1e18)], "brief": [(p * (1 + s), 1e18)]}


def replay(m, slip, cfg, takt_bars, versatz_bars, t_ende):
    api = Historie(m, slip, takt_bars * 5)
    prot, stand = [], []

    def fangen(datei, spalten, zeilen):
        if datei.name == "protokoll.csv":
            prot.extend(zeilen)
        elif datei.name == "stand.csv":
            stand.extend(zeilen)

    alt = bot.anhaengen
    bot.anhaengen = fangen            # nur das CSV-Schreiben wird abgefangen (Speicher statt Platte); Logik unveraendert
    warn = 0
    wtext = {}
    try:
        with tempfile.TemporaryDirectory(prefix="v_eng03_") as d:
            d = Path(d)
            for t in range(versatz_bars, t_ende, takt_bars):
                api.t = t
                r = bot.schritt(cfg, api, d, api.jetzt_ms(), melden=lambda *_: None)
                warn += len(r["warnungen"])
                for w in r["warnungen"]:
                    w = w.split("(")[0][:60]
                    wtext[w] = wtext.get(w, 0) + 1
            z = json.loads((d / "zustand.json").read_text())
    finally:
        bot.anhaengen = alt
    K = cfg["kapital_usd"]
    s = pd.DataFrame(stand)
    s["tag"] = pd.to_datetime(s["zeit"]).dt.normalize()
    tagesend = s.groupby("tag")["netto_mit_rebate"].last() / K
    x = tagesend.diff().fillna(tagesend.iloc[0])
    k = 1.0 + x.cumsum()
    gr = pd.Series([p["grund"] for p in prot]).value_counts().to_dict()
    return {"laeufe": len(stand), "tage": int(len(x)), "jahr": round(float(x.mean() * 365), 4),
            "sharpe": round(float(x.mean() / x.std() * np.sqrt(365)), 3),
            "einbruch": round(float(((k.cummax() - k) / k.cummax()).max()), 4),
            "orders": len(prot), "stops": int(gr.get("stop", 0)), "ziele": int(gr.get("ziel", 0)),
            "einstiege": int(gr.get("einstieg", 0)), "schliessen_signal": int(gr.get("schliessen", 0)),
            "umsatz_tag": round(sum(float(p["volumen"]) for p in prot) / K / len(x), 4),
            "funding": round(z["funding"] / K, 5), "warnungen": warn, "warnungen_arten": wtext}, x, prot


if __name__ == "__main__":
    ziel = sys.argv[1]
    t0 = time.time()
    m = R.markt(R.GRUPPE_A, vor=True)
    slip = R.yubit_kosten(m.coins)[0]
    ende = int(m.index.searchsorted(pd.Timestamp(R.SPLIT)))
    if len(sys.argv) > 2:
        ende = min(ende, int(sys.argv[2]) * 288)
    cfg = json.loads(Path(WURZEL + "/vorwaertstest/config_lauf_tpsl.json").read_text())
    assert cfg["tp"] == 0.15 and cfg["sl"] == 0.05 and cfg["tagesverlust_limit"] == 1.0
    cfg.update(kapital_usd=1_000_000, hebel=1.0)
    erg, reihen = {}, {}
    for name, takt, versatz in (("echter Bot, Lauf 1x je Stunde (hh:00)", 12, 0), ("echter Bot, Lauf alle 5 Minuten", 1, 0),
                                ("echter Bot, Lauf 1x je Stunde (hh:05)", 12, 1)):
        t1 = time.time()
        e, x, prot = replay(m, slip, cfg, takt, versatz, ende)
        e["sekunden"] = round(time.time() - t1)
        erg[name] = e
        reihen[name] = x
        print(name, e, flush=True)
    d = reihen["echter Bot, Lauf alle 5 Minuten"] - reihen["echter Bot, Lauf 1x je Stunde (hh:00)"]
    erg["differenz_5min_minus_stuendlich"] = {"jahr": round(float(d.mean() * 365), 4), "t": round(float(d.mean() / d.std() * np.sqrt(len(d))), 2)}
    print("Differenz 5 Minuten minus stuendlich:", erg["differenz_5min_minus_stuendlich"])
    Path(ziel).write_text(json.dumps({"bis": str(m.index[ende - 1]), "ergebnis": erg}, indent=1))
    pd.DataFrame(reihen).to_csv(Path(ziel).with_suffix(".tage.csv"))
    print(f"fertig nach {time.time() - t0:.0f} s")
