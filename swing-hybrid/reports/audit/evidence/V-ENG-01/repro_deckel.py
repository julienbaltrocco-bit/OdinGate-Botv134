"""V-ENG-01: unabhaengige Gegenpruefung von ENG-01 (Sicherheitsdeckel max_order_usd blockiert Schliess-Orders im Live-Modus).

Eigene nachgestellte Boerse (kein Netz, kein echter Schluessel, kein Zugriff auf vorwaertstest/lauf*). Jeder Lauf schreibt
ausschliesslich in ein temporaeres Verzeichnis. YUBIT_LIVE wird nur in diesem Prozess gesetzt.
"""
import json
import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, "/home/user/OdinGate-Botv134/swing-hybrid")
from vorwaertstest import bot, kern            # noqa: E402
from vorwaertstest.yubit import YubitFehler    # noqa: E402

bot.time.sleep = lambda *_: None               # die 1,5 s Wartezeit nach der Order ueberspringen
H = kern.STUNDE_MS
T0 = 1_800_000_000_000 - (1_800_000_000_000 % (24 * H)) + 5 * 60_000     # 00:05 UTC eines Tages
STILL = lambda *_: None


class KontoAttrappe:
    """Nachgestelltes Yubit-Konto im Hedge-Modus. Fuellt eine Limit-Order sofort und vollstaendig zum besten Gegenkurs,
    wenn das Limit den Markt kreuzt. reduceOnly darf die Position nur verkleinern."""
    key, secret = "attrappe", "attrappe"       # keine echten Zugangsdaten, das Objekt hat keinen Netzzugang

    def __init__(self, kurse, alt, schritt=0.1, tick=0.01, spanne=0.10):
        self.kurse, self.alt, self.schritt, self.tick, self.spanne = dict(kurse), dict(alt), schritt, tick, spanne
        self.jetzt = T0
        self.long, self.short = {}, {}         # Stueck je Symbol
        self.orders, self._fills, self.aufrufe = [], {}, 0

    def kerzen(self, sym, minuten=60, limit=3, start_ms=None, ende_ms=None):
        c = sym.removesuffix("USDT")
        if start_ms is not None:
            return [{"start": start_ms, "open": 0, "high": 0, "low": 0, "close": self.alt[c]}]
        letzte = self.jetzt - self.jetzt % H - H
        return [{"start": letzte, "open": 0, "high": 0, "low": 0, "close": self.kurse[c]},
                {"start": letzte + H, "open": 0, "high": 0, "low": 0, "close": self.kurse[c]}]

    def kontrakt(self, sym):
        return {"status": "Trading", "min_menge": self.schritt, "schritt": self.schritt, "tick": self.tick, "funding_minuten": 480}

    def ticker(self, sym):
        p = self.kurse[sym.removesuffix("USDT")]
        return {"geld": p - self.spanne / 2, "brief": p + self.spanne / 2, "letzter": p, "mark": p, "funding": 0.0, "umsatz24h": 1e9}

    def buch(self, sym, tiefe=25):
        p = self.kurse[sym.removesuffix("USDT")]
        return {"geld": [(p - self.spanne / 2, 1e9)], "brief": [(p + self.spanne / 2, 1e9)]}

    def positionen(self, settle="USDT"):
        out = []
        for sym, q in self.long.items():
            out.append({"symbol": sym, "size": str(q), "positionIdx": 1})
        for sym, q in self.short.items():
            out.append({"symbol": sym, "size": str(q), "positionIdx": 2})
        return out

    def order(self, symbol, seite, menge, preis, position_idx, reduce_only):
        oid = str(len(self.orders) + 1)
        q, limit = float(menge), float(preis)
        b = self.buch(symbol)
        kauf = seite == "Buy"
        gegen = b["brief"][0][0] if kauf else b["geld"][0][0]
        kreuzt = limit >= gegen if kauf else limit <= gegen
        buchseite = self.long if position_idx == 1 else self.short
        oeffnet = (kauf and position_idx == 1) or (not kauf and position_idx == 2)
        if reduce_only and (oeffnet or buchseite.get(symbol, 0.0) < q - 1e-12):
            raise YubitFehler("reduceOnly wuerde die Position vergroessern")
        self.orders.append({"zeit": self.jetzt, "sym": symbol, "seite": seite, "menge": q, "preis": limit, "idx": position_idx,
                            "reduce": reduce_only, "gefuellt": kreuzt})
        if kreuzt:
            buchseite[symbol] = round(buchseite.get(symbol, 0.0) + (q if oeffnet else -q), 10)
            self._fills[oid] = [{"execQty": str(q), "execPrice": str(gegen), "execFee": str(q * gegen * kern.TAKER)}]
        return {"order_id": oid, "link_id": "x"}

    def fills(self, symbol, order_id):
        return self._fills.get(order_id, [])

    def storno(self, symbol, order_id):
        return {}

    def netto(self, coin):
        return self.long.get(coin + "USDT", 0.0) - self.short.get(coin + "USDT", 0.0)


def lauf(cfg, api, daten, stunde, sammeln=None):
    api.jetzt = T0 + stunde * H
    zeilen = []
    r = bot.schritt(cfg, api, daten, api.jetzt, melden=zeilen.append)
    if sammeln is not None:
        sammeln.extend(zeilen)
    return r


def zst(d):
    return json.loads((Path(d) / "zustand.json").read_text())


def frisch():
    return Path(tempfile.mkdtemp(prefix="v_eng_01_"))


os.environ["YUBIT_LIVE"] = "ja"
BASIS = {"modus": "live", "kapital_usd": 2500, "hebel": 0.04, "coins": ["AAA"], "tagesverlust_limit": 1.0,
         "preisgrenze": 0.0005, "max_order_usd": 150, "daten": "x"}            # 100 USD je Coin, Deckel 150 USD (wie config.json)
E = {}


def neue_orders(api, n):
    return [(o["sym"], o["seite"], o["menge"], o["preis"], o["reduce"]) for o in api.orders[n:]]


# --- A: Short, Kurs +60 %, Signal dreht auf Long -> Schliess-Order wird vom Deckel abgelehnt ---------------------------------
d = frisch(); api = KontoAttrappe({"AAA": 100.0}, {"AAA": 110.0})
r0 = lauf(BASIS, api, d, 0)
a = {"einstieg_modus": r0["modus"], "einstieg_orders": neue_orders(api, 0), "pos_boerse": api.netto("AAA")}
api.kurse["AAA"] = 160.0; api.alt["AAA"] = 110.0
n = len(api.orders); aus = []
r = lauf(BASIS, api, d, 1, aus)
a["nach_dreh"] = {"signal": kern.richtung(160.0, 110.0), "warnungen": r["warnungen"], "orders_an_boerse": neue_orders(api, n),
                  "pos_boerse": api.netto("AAA"), "pos_protokoll": zst(d)["pos"], "protokoll_zeilen": len(bot.lesen(d / "protokoll.csv")),
                  "netto_ohne_rebate": round(r["vermoegen"]["netto_ohne_rebate"], 2), "ausgabe": aus}
# weiter steigende Kurse: jede Stunde derselbe Fehlschlag, Verlust waechst, kein Abbruch
verlauf = []
for i, kurs in enumerate((200.0, 300.0, 500.0), start=2):
    api.kurse["AAA"] = kurs; n = len(api.orders)
    r = lauf(BASIS, api, d, i)
    verlauf.append({"kurs": kurs, "orders": neue_orders(api, n), "pos_boerse": api.netto("AAA"), "warnungen": r["warnungen"],
                    "netto_ohne_rebate": round(r["vermoegen"]["netto_ohne_rebate"], 2)})
a["folgestunden"] = verlauf
# erst wenn der Kurs wieder unter den Deckel faellt (und das Signal noch Long ist), geht die Order durch
api.kurse["AAA"] = 149.0; n = len(api.orders)
r = lauf(BASIS, api, d, 5)
a["kurs_zurueck_unter_deckel_149"] = {"orders": neue_orders(api, n), "pos_boerse": api.netto("AAA"), "warnungen": r["warnungen"]}
E["A_short_dreh_blockiert"] = a

# --- B: Kontrolle, identischer Ablauf mit hohem Deckel -> Schliessen und Dreh funktionieren -----------------------------------
d = frisch(); api = KontoAttrappe({"AAA": 100.0}, {"AAA": 110.0}); cfgB = {**BASIS, "max_order_usd": 100000}
lauf(cfgB, api, d, 0); api.kurse["AAA"] = 160.0; n = len(api.orders)
r = lauf(cfgB, api, d, 1)
E["B_kontrolle_hoher_deckel"] = {"orders": neue_orders(api, n), "pos_boerse": api.netto("AAA"), "warnungen": r["warnungen"]}

# --- C: Kontrolle, Deckel 150 aber Kurs nur +40 % -> Schliessen funktioniert ---------------------------------------------------
d = frisch(); api = KontoAttrappe({"AAA": 100.0}, {"AAA": 110.0})
lauf(BASIS, api, d, 0); api.kurse["AAA"] = 140.0; n = len(api.orders)
r = lauf(BASIS, api, d, 1)
E["C_kontrolle_unter_deckel"] = {"orders": neue_orders(api, n), "pos_boerse": api.netto("AAA"), "warnungen": r["warnungen"]}

# --- D: Tagesverlust-Limit loest aus, Signal bleibt Short -> "alles schliessen" scheitert ebenfalls ----------------------------
d = frisch(); api = KontoAttrappe({"AAA": 100.0}, {"AAA": 300.0}); cfgD = {**BASIS, "tagesverlust_limit": 0.01}   # 25 USD
lauf(cfgD, api, d, 0); api.kurse["AAA"] = 160.0; n = len(api.orders); aus = []
r = lauf(cfgD, api, d, 1, aus)
r2 = lauf(cfgD, api, d, 2)
E["D_tageslimit_blockiert"] = {"signal": kern.richtung(160.0, 300.0), "gesperrt_tag": zst(d)["gesperrt_tag"], "orders": neue_orders(api, n),
                               "pos_boerse": api.netto("AAA"), "warnungen": r["warnungen"], "ausgabe": aus,
                               "folgestunde_warnungen": r2["warnungen"]}

# --- E: Variante mit Stop 5 %: Kurssprung zwischen zwei Laeufen ueber den Deckel -> Stop-Order scheitert -----------------------
d = frisch(); api = KontoAttrappe({"AAA": 100.0}, {"AAA": 300.0}); cfgE = {**BASIS, "tp": 0.15, "sl": 0.05}
lauf(cfgE, api, d, 0); api.kurse["AAA"] = 152.0; n = len(api.orders)
r = lauf(cfgE, api, d, 1)
E["E_stop_blockiert"] = {"orders": neue_orders(api, n), "pos_boerse": api.netto("AAA"), "warnungen": r["warnungen"],
                         "sperre": zst(d).get("sperre")}

# --- F: Long-Seite: Long mit +60 % Gewinn, Signal dreht auf Short -> Verkauf (reduceOnly) wird ebenfalls abgelehnt -------------
d = frisch(); api = KontoAttrappe({"AAA": 100.0}, {"AAA": 90.0})
lauf(BASIS, api, d, 0); api.kurse["AAA"] = 160.0; api.alt["AAA"] = 170.0; n = len(api.orders)
r = lauf(BASIS, api, d, 1)
f = {"pos_nach_einstieg": 1.0, "signal": kern.richtung(160.0, 170.0), "orders": neue_orders(api, n), "pos_boerse": api.netto("AAA"),
     "warnungen": r["warnungen"]}
api.kurse["AAA"] = 149.0; api.alt["AAA"] = 170.0; n = len(api.orders)
r = lauf(BASIS, api, d, 2)
f["kurs_faellt_auf_149"] = {"orders": neue_orders(api, n), "pos_boerse": api.netto("AAA"), "warnungen": r["warnungen"]}
E["F_long_gewinn_blockiert"] = f

# --- G: Zahlen der laufenden Konfigurationen (Hebel 3, 1500 USD je Coin, Deckel 2000 USD), im Live-Modus nachgestellt ----------
lauf_cfg = json.loads(Path("/home/user/OdinGate-Botv134/swing-hybrid/vorwaertstest/config_lauf.json").read_text())
cfgG = {**lauf_cfg, "modus": "live", "coins": ["AAA"], "kapital_usd": lauf_cfg["kapital_usd"] / 10}   # ein Coin, gleicher Betrag je Coin
g = {"nominal_je_coin": cfgG["kapital_usd"] * cfgG["hebel"], "deckel": cfgG["max_order_usd"]}
for kurs in (133.0, 133.3, 134.0):
    d = frisch(); api = KontoAttrappe({"AAA": 100.0}, {"AAA": 110.0})
    lauf(cfgG, api, d, 0); menge = -api.netto("AAA")
    api.kurse["AAA"] = kurs; n = len(api.orders)
    r = lauf(cfgG, api, d, 1)
    g[f"kurs_{kurs}"] = {"menge": menge, "orders": neue_orders(api, n), "pos_boerse": api.netto("AAA"), "warnungen": r["warnungen"]}
E["G_config_lauf_im_live_modus"] = g

# --- H: Papier-Modus mit denselben Zahlen wie A: Deckel wird nicht geprueft ---------------------------------------------------
d = frisch(); api = KontoAttrappe({"AAA": 100.0}, {"AAA": 110.0}); cfgH = {**BASIS, "modus": "papier"}
lauf(cfgH, api, d, 0); api.kurse["AAA"] = 160.0
r = lauf(cfgH, api, d, 1)
E["H_papier_gleiche_zahlen"] = {"modus": r["modus"], "pos_protokoll": zst(d)["pos"], "warnungen": r["warnungen"],
                                "gruende": [z["grund"] for z in bot.lesen(d / "protokoll.csv")], "orders_an_boerse": len(api.orders)}

print(json.dumps(E, indent=1, ensure_ascii=False))
