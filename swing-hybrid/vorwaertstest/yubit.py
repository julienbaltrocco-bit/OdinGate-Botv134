"""Schlanker Client für die offizielle Yubit-OpenAPI (https://openapi.yubit.com).

Endpunkte, Parameter und Signatur stammen aus dem offiziellen Paket `@yubit/exchange-skill` (Version 1.0.6).
Kursdaten brauchen keinen Schlüssel. Kontodaten und Orders brauchen einen API-Schlüssel, und Yubit verlangt dafür
eine vorherige Freigabe der IP-Adresse durch den Kundendienst.

Nur Standardbibliothek, damit der Bot überall ohne Installation läuft.
"""
import hashlib
import hmac
import json
import secrets
import time
import urllib.error
import urllib.parse
import urllib.request

BASIS = "https://openapi.yubit.com"
P = {
    "ticker": "/oapi/contract/market/public/v1/tickers",
    "buch": "/oapi/contract/market/public/v1/orderbooks",
    "kerzen": "/oapi/contract/instrument/public/v1/klines",
    "kontrakte": "/oapi/contract/instrument/public/v1/instruments",
    "guthaben": "/oapi/contract/trade/private/v1/wallet-balances",
    "gebuehren": "/oapi/contract/trade/private/v1/fee-rates",
    "positionen": "/oapi/contract/trade/private/v1/positions",
    "orders": "/oapi/contract/trade/private/v1/orders",
    "storno": "/oapi/contract/trade/private/v1/orders/cancel",
    "offene_orders": "/oapi/contract/trade/private/v1/open-orders",
    "fills": "/oapi/contract/trade/private/v1/executions",
}


class YubitFehler(RuntimeError):
    pass


class Yubit:
    def __init__(self, api_key: str = "", api_secret: str = "", basis: str = BASIS, pause: float = 0.15,
                 recv_window: str = "5000", oeffner=None):
        self.key, self.secret, self.basis, self.pause, self.recv = api_key, api_secret, basis.rstrip("/"), pause, recv_window
        self._oeffner = oeffner or urllib.request.urlopen   # in Tests austauschbar
        self._naechster = 0.0
        self.aufrufe = 0

    # ------------------------------------------------------------------ Transport ----
    def _signatur(self, payload: str) -> dict:
        ts = str(int(time.time() * 1000))
        sig = hmac.new(self.secret.encode(), (ts + self.key + self.recv + payload).encode(), hashlib.sha256).hexdigest()
        return {"MF-ACCESS-API-KEY": self.key, "MF-ACCESS-TIMESTAMP": ts, "MF-ACCESS-RECV-WINDOW": self.recv,
                "MF-ACCESS-SIGN": sig}

    def _anfrage(self, methode: str, pfad: str, params: dict | None = None, privat: bool = False):
        params = {k: v for k, v in (params or {}).items() if v is not None}
        if privat and not (self.key and self.secret):
            raise YubitFehler("Für diesen Aufruf fehlt der API-Schlüssel")
        kopf = {"Content-Type": "application/json", "User-Agent": "vorwaertstest/1.0"}
        url, daten = self.basis + pfad, None
        if methode == "GET":
            query = "&".join(f"{urllib.parse.quote(str(k), safe='')}={urllib.parse.quote(str(params[k]), safe='')}"
                             for k in sorted(params))
            if query:
                url += "?" + query
            if privat:
                kopf.update(self._signatur(query))
        else:
            body = json.dumps(params, separators=(",", ":"))
            daten = body.encode()
            if privat:
                kopf.update(self._signatur(body))
        warten = self._naechster - time.time()
        if warten > 0:
            time.sleep(warten)
        self._naechster = time.time() + self.pause
        self.aufrufe += 1
        req = urllib.request.Request(url, data=daten, headers=kopf, method=methode)
        try:
            with self._oeffner(req, timeout=20) as r:
                roh = json.loads(r.read().decode())
        except urllib.error.HTTPError as e:
            raise YubitFehler(f"HTTP {e.code} bei {pfad}: {e.read()[:200]!r}") from e
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as e:
            raise YubitFehler(f"Keine brauchbare Antwort von {pfad}: {e}") from e
        if roh.get("code") != 0:
            raise YubitFehler(f"Yubit meldet Fehler bei {pfad}: {roh.get('code')} {roh.get('message')}")
        return roh.get("data") or {}

    # ------------------------------------------------------- öffentliche Kursdaten ----
    def ticker(self, symbol: str) -> dict:
        t = self._anfrage("GET", P["ticker"], {"symbol": symbol})["list"][0]
        return {"geld": float(t["bidPrice"]), "brief": float(t["askPrice"]), "letzter": float(t["lastPrice"]),
                "mark": float(t["markPrice"]), "funding": float(t["fundingRate"]) / 1e6,   # "100" = 0,01 %
                "umsatz24h": float(t["turnover24h"])}

    def buch(self, symbol: str, tiefe: int = 25) -> dict:
        d = self._anfrage("GET", P["buch"], {"symbol": symbol, "depth": str(tiefe)})
        geld = sorted(((float(p), float(q)) for p, q in d["b"]), reverse=True)   # bester Geldkurs zuerst
        brief = sorted((float(p), float(q)) for p, q in d["a"])                  # bester Briefkurs zuerst
        return {"geld": geld, "brief": brief}

    def kerzen(self, symbol: str, minuten: int = 60, limit: int = 3, start_ms: int | None = None,
               ende_ms: int | None = None) -> list[dict]:
        """Kerzen aufsteigend nach Zeit. Die letzte Kerze kann noch laufen."""
        d = self._anfrage("GET", P["kerzen"], {"symbol": symbol, "interval": str(minuten), "limit": str(limit),
                                               "start": start_ms, "end": ende_ms})
        k = [{"start": int(x[0]), "open": float(x[1]), "high": float(x[2]), "low": float(x[3]), "close": float(x[4])}
             for x in d.get("list", [])]
        return sorted(k, key=lambda x: x["start"])

    def kontrakt(self, symbol: str) -> dict:
        liste = self._anfrage("GET", P["kontrakte"], {"symbol": symbol}).get("list", [])
        if not liste:
            raise YubitFehler(f"{symbol} ist bei Yubit nicht gelistet")
        i = liste[0]
        return {"status": i["status"], "min_menge": float(i["lotSizeFilter"]["minTradingQty"]),
                "schritt": float(i["lotSizeFilter"]["qtyStep"]), "tick": float(i["priceFilter"]["tickSize"]),
                "funding_minuten": int(i.get("fundingInterval") or 480)}

    # ---------------------------------------------------- Konto (nur Stufe „live“) ----
    def positionen(self, settle: str = "USDT") -> list[dict]:
        d = self._anfrage("GET", P["positionen"], {"settleCoin": settle}, privat=True)
        return list(d.get("list") or []) + list(d.get("separateList") or [])

    def guthaben_roh(self) -> dict:
        return self._anfrage("GET", P["guthaben"], {}, privat=True)

    def gebuehren_roh(self, symbol: str) -> dict:
        return self._anfrage("GET", P["gebuehren"], {"symbol": symbol}, privat=True)

    def order(self, symbol: str, seite: str, menge: str, preis: str, position_idx: int, reduce_only: bool) -> dict:
        """Limit-Order mit Preisgrenze. seite: 'Buy' oder 'Sell'. position_idx: 1 = Long-Seite, 2 = Short-Seite."""
        link = f"vt_{int(time.time() * 1000)}_{secrets.token_hex(3)}"
        body = {"symbol": symbol, "side": seite, "orderType": "Limit", "qty": menge, "orderLinkId": link,
                "positionIdx": position_idx, "price": preis}
        if reduce_only:
            body["reduceOnly"] = True
        d = self._anfrage("POST", P["orders"], body, privat=True)
        return {"order_id": d.get("orderId"), "link_id": link}

    def storno(self, symbol: str, order_id: str) -> dict:
        return self._anfrage("POST", P["storno"], {"symbol": symbol, "orderId": order_id}, privat=True)

    def offene_orders(self, symbol: str) -> list[dict]:
        return list(self._anfrage("GET", P["offene_orders"], {"symbol": symbol}, privat=True).get("list") or [])

    def fills(self, symbol: str, order_id: str) -> list[dict]:
        d = self._anfrage("GET", P["fills"], {"symbol": symbol, "orderId": order_id, "limit": "50"}, privat=True)
        return list(d.get("list") or [])
