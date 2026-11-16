"""V-QD-04: Der UNVERAENDERTE Papier-Bot (vorwaertstest/bot.py, schritt) gegen eine nachgestellte Boerse mit historischen
Binance-Kursen, mit den Werten aus config_lauf.json bzw. config_lauf_tpsl.json (nur gelesen).

Zweck: zeigen, ob das Szenario des Befunds mit dem echten Bot-Code eintritt (Konto <= -100 % des Startkapitals, ohne dass
das Tageslimit oder sonst eine Sicherung eingreift), und die eigenen Nachbauten gegen den echten Code abgleichen.
Zustand und Protokolle des Bots landen ausschliesslich in einem neuen Unterordner des uebergebenen Scratch-Verzeichnisses;
vorwaertstest/lauf, vorwaertstest/lauf_tpsl und docs/ werden nicht beruehrt. Kein Netz, keine Schluessel.

Aufruf: bot_replay.py <scratch> <start JJJJ-MM-TT> <tage> <takt_minuten: 60 oder 5>
"""
import json
import shutil
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path("/home/user/OdinGate-Botv134/swing-hybrid")
sys.path.append(str(ROOT))                     # hinten angehaengt: Standardbibliothek hat Vorrang
from vorwaertstest import bot, kern            # noqa: E402

AUS, START_TAG, TAGE, TAKT = Path(sys.argv[1]), sys.argv[2], int(sys.argv[3]), int(sys.argv[4])
A = ["BTC", "ETH", "SOL", "XRP", "DOT", "DOGE", "ADA", "LINK", "AVAX", "LTC"]
H = kern.STUNDE_MS
t0 = time.time()
idx = pd.date_range(pd.Timestamp(START_TAG) - pd.Timedelta(days=16), pd.Timestamp(START_TAG) + pd.Timedelta(days=TAGE + 1), freq="5min", inclusive="left")
T0_MS = int(idx[0].value // 1_000_000)
sp = pd.read_csv(ROOT / "data/processed/yubit_spannen_stichprobe.csv")
sp["halb"] = (sp["brief"] - sp["geld"]) / (sp["brief"] + sp["geld"])
halb = sp.groupby("symbol")["halb"].mean()
yc = pd.read_csv(ROOT / "data/processed/yubit_coins.csv").set_index("coin")
O, C, FR, SCHRITT, SPANNE = {}, {}, {}, {}, {}
for coin in A:
    d = pd.read_parquet(ROOT / "data/candles/5m" / f"{coin}USDT.parquet")
    d.index = d.index.astype("datetime64[ns]")
    k = d.reindex(idx)
    cl = k["close"].ffill().bfill()
    O[coin] = k["open"].where(k["close"].notna(), cl).to_numpy(); C[coin] = cl.to_numpy()
    fr = pd.read_parquet(ROOT / "data/candles/funding" / f"{coin}USDT.parquet")["rate"]
    fr.index = fr.index.astype("datetime64[ns]").floor("5min")
    FR[coin] = fr[~fr.index.duplicated()].reindex(idx).ffill().fillna(0.0).to_numpy()     # zuletzt abgerechneter Satz
    SCHRITT[coin] = 10.0 ** round(np.log10(float(yc.loc[coin, "schritt_usd"]) / float(d["close"].iloc[-1])))
    SPANNE[coin] = max(0.00005, 2.0 * float(halb[coin + "USDT"]))                       # wie die Kostenannahme der Forschung
print("Schrittweiten (Stueck):", SCHRITT)


class HistBoerse:
    """Nachgestellte Boerse: gleiche Schnittstelle wie vorwaertstest.yubit.Yubit (oeffentlicher Teil), Kurse aus der Historie."""
    key = secret = ""

    def __init__(self):
        self.jetzt, self.aufrufe = 0, 0

    def _i(self, ms):
        return int((ms - T0_MS) // 300_000)

    def kerzen(self, sym, minuten=60, limit=3, start_ms=None, ende_ms=None):
        self.aufrufe += 1
        c = sym.removesuffix("USDT")
        if start_ms is not None:
            return [{"start": start_ms, "open": 0, "high": 0, "low": 0, "close": float(C[c][self._i(start_ms) + 11])}]
        lauf = self.jetzt - self.jetzt % H
        return [{"start": lauf - 2 * H, "open": 0, "high": 0, "low": 0, "close": float(C[c][self._i(lauf - 2 * H) + 11])},
                {"start": lauf - H, "open": 0, "high": 0, "low": 0, "close": float(C[c][self._i(lauf - H) + 11])},
                {"start": lauf, "open": 0, "high": 0, "low": 0, "close": float(O[c][self._i(self.jetzt)])}]      # laeuft noch

    def kontrakt(self, sym):
        self.aufrufe += 1
        s = SCHRITT[sym.removesuffix("USDT")]
        return {"status": "Trading", "min_menge": s, "schritt": s, "tick": 1e-6, "funding_minuten": 480}

    def _mitte(self, c):
        return float(O[c][self._i(self.jetzt)])

    def ticker(self, sym):
        self.aufrufe += 1
        c = sym.removesuffix("USDT")
        p = self._mitte(c)
        return {"geld": p * (1 - SPANNE[c]), "brief": p * (1 + SPANNE[c]), "letzter": p, "mark": p,
                "funding": float(FR[c][self._i(self.jetzt)]), "umsatz24h": 1e9}

    def buch(self, sym, tiefe=25):
        self.aufrufe += 1
        c = sym.removesuffix("USDT")
        p = self._mitte(c)
        return {"geld": [(p * (1 - SPANNE[c]), 1e15)], "brief": [(p * (1 + SPANNE[c]), 1e15)]}


def replay(name, config):
    cfg = bot.konfig(ROOT / "vorwaertstest" / config)                 # nur lesen
    daten = AUS / f"replay_{name}_{START_TAG}_{TAKT}min"
    if daten.exists():
        shutil.rmtree(daten)                                           # nur der eigene Scratch-Ordner
    api = HistBoerse()
    start_ms = int(pd.Timestamp(START_TAG).value // 1_000_000)
    schritt_ms = TAKT * 60_000
    versatz = 5 * 60_000 if TAKT == 60 else 0
    meldungen = []
    n = TAGE * 24 * 60 // TAKT
    for i in range(n):
        jetzt = start_ms + versatz + i * schritt_ms
        api.jetzt = jetzt
        r = bot.schritt(cfg, api, daten, jetzt, melden=meldungen.append)
        if r.get("warnungen"):
            raise RuntimeError(str(r["warnungen"]))
    st = pd.read_csv(daten / "stand.csv", parse_dates=["zeit"]).set_index("zeit")
    pr = pd.read_csv(daten / "protokoll.csv", parse_dates=["zeit"])
    z = json.loads((daten / "zustand.json").read_text())
    K = cfg["kapital_usd"]
    konto = K + st["netto_mit_rebate"]
    unter0 = konto[konto <= 0]
    e = {"config": config, "hebel": cfg["hebel"], "tagesverlust_limit": cfg["tagesverlust_limit"], "tp": cfg.get("tp", 0), "sl": cfg.get("sl", 0),
         "durchlaeufe": int(len(st)), "orders": int(len(pr)), "gruende": pr["grund"].value_counts().to_dict(),
         "konto_tief_usd": float(konto.min()), "konto_tief_zeit": str(konto.idxmin()), "tief_anteil": float(st["netto_mit_rebate"].min() / K),
         "konto_ende_usd": float(konto.iloc[-1]),
         "erstes_konto_le_0": str(unter0.index[0]) if len(unter0) else None,
         "tage_bis_konto_le_0": float((unter0.index[0] - pd.Timestamp(START_TAG)).total_seconds() / 86400) if len(unter0) else None,
         "durchlaeufe_mit_konto_le_0": int(len(unter0)),
         "orders_nach_konto_le_0": int((pr["zeit"] >= unter0.index[0]).sum()) if len(unter0) else 0,
         "einstiege_nach_konto_le_0": int(((pr["zeit"] >= unter0.index[0]) & (pr["grund"] == "einstieg")).sum()) if len(unter0) else 0,
         "mittlerer_positionswert_bei_konto_le_0_usd": float(st.loc[unter0.index, "einsatz"].mean()) if len(unter0) else None,
         "max_positionswert_usd": float(st["einsatz"].max()), "gesperrt_tag_im_zustand": z["gesperrt_tag"],
         "tageslimit_meldungen": int(sum("Tagesverlust-Limit" in m for m in meldungen)),
         "groesster_verlust_ein_utc_tag_usd": float((st["netto_ohne_rebate"] - st["netto_ohne_rebate"].groupby(st.index.normalize()).transform("first")).min())}
    print(f"\n--- {name} ({config}): Hebel {e['hebel']}, tagesverlust_limit {e['tagesverlust_limit']}, tp {e['tp']}, sl {e['sl']}; Start {START_TAG}, {TAGE} Tage, Takt {TAKT} min")
    for k, v in e.items():
        if k not in ("config", "hebel", "tagesverlust_limit", "tp", "sl"):
            print(f"   {k}: {v}")
    (st["netto_mit_rebate"] / K).resample("1D").last().round(4).to_csv(AUS / f"replay_{name}_{START_TAG}_{TAKT}min_tagesstand.csv")
    shutil.rmtree(daten)                                               # Rohprotokolle des Replays nicht aufbewahren
    return e


out = {"start": START_TAG, "tage": TAGE, "takt_min": TAKT,
       "test1": replay("test1", "config_lauf.json"), "test2": replay("test2", "config_lauf_tpsl.json")}
json.dump(out, open(AUS / f"bot_replay_{START_TAG}_{TAKT}min.json", "w"), indent=1, default=str)
print(f"\nfertig nach {time.time() - t0:.0f} s")
