"""Live-Ansicht des Papier-Vorwärtstests: holt alle paar Sekunden die Yubit-Kurse und bewertet das Papier-Konto neu.

    python3 -m vorwaertstest.live_server --daten vorwaertstest/lauf --config vorwaertstest/config_lauf.json --port 8765

Nur lesend: setzt keine Orders und ändert den Zustand des Bots nicht. Nur Standardbibliothek.
"""
import argparse
import collections
import datetime as dt
import json
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from . import bot, kern
from .yubit import P, Yubit

TAKT_S = 3.0
STAND = {"ok": False, "fehler": "noch kein Abruf"}
VERLAUF = collections.deque(maxlen=1200)          # rund eine Stunde bei 3 Sekunden
SCHLOSS = threading.Lock()


def bewerten(cfg: dict, daten: Path, ticker: dict) -> dict:
    z = json.loads((daten / "zustand.json").read_text())
    pr = bot.lesen(daten / "protokoll.csv")
    einstieg = {r["coin"]: (float(r["fuellkurs"]), r["zeit"]) for r in pr if r["grund"] == "einstieg"}
    kap = cfg["kapital_usd"]
    kurse, zeilen = {}, []
    for coin in cfg["coins"]:
        t = ticker.get(coin + "USDT")
        if not t:
            kurse[coin] = z.get("kurs", {}).get(coin, 0.0)
            continue
        geld, brief = float(t["bidPrice"]), float(t["askPrice"])
        kurse[coin] = (geld + brief) / 2
    for coin in cfg["coins"]:
        q, k = z["pos"].get(coin, 0.0), kurse[coin]
        ein, seit = einstieg.get(coin, (0.0, ""))
        t = ticker.get(coin + "USDT", {})
        zeilen.append({"coin": coin, "richtung": "Long" if q > 0 else "Short" if q < 0 else "keine", "seit": seit,
                       "einstieg": ein if q else None, "kurs": k, "betrag": abs(q) * k,
                       "ergebnis": q * (k - ein) if q else 0.0,
                       "ergebnis_pct": (k / ein - 1) * (1 if q > 0 else -1) * 100 if q and ein else 0.0,
                       "tag_pct": float(t.get("price24hPcnt", 0) or 0) / 1e4})
    v = kern.vermoegen(z, kurse)
    return {"ok": True, "zeit": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"), "kapital": kap,
            "start": z.get("start", ""), "orders": z.get("orders", 0),
            "mit_rebate_usd": v["netto_mit_rebate"], "mit_rebate_pct": v["netto_mit_rebate"] / kap * 100,
            "ohne_rebate_usd": v["netto_ohne_rebate"], "ohne_rebate_pct": v["netto_ohne_rebate"] / kap * 100,
            "vor_gebuehren_usd": v["brutto"], "gebuehr_usd": v["gebuehr"], "rebate_usd": v["rebate"], "funding_usd": v["funding"],
            "konto_usd": kap + v["netto_mit_rebate"], "offen_usd": sum(r["ergebnis"] for r in zeilen),
            "einsatz_usd": sum(r["betrag"] for r in zeilen), "positionen": zeilen,
            "letzte_orders": [{"zeit": r["zeit"], "coin": r["coin"], "seite": "Kauf" if r["seite"] == "kauf" else "Verkauf",
                               "kurs": float(r["fuellkurs"]), "volumen": float(r["volumen"])} for r in pr[-12:]][::-1]}


def schleife(cfg: dict, daten: Path) -> None:
    api = Yubit(pause=0.0)
    while True:
        beginn = time.time()
        try:
            liste = api._anfrage("GET", P["ticker"], {}).get("list", [])
            s = bewerten(cfg, daten, {t["symbol"]: t for t in liste})
            with SCHLOSS:
                STAND.clear(); STAND.update(s)
                VERLAUF.append([int(beginn * 1000), round(s["mit_rebate_usd"], 4)])
        except Exception as e:                                   # noqa: BLE001  (weiterlaufen, Fehler anzeigen)
            with SCHLOSS:
                STAND["ok"] = False; STAND["fehler"] = str(e)[:200]
        time.sleep(max(0.5, TAKT_S - (time.time() - beginn)))


class Handler(BaseHTTPRequestHandler):
    seite = b""

    def _senden(self, code: int, typ: str, daten: bytes) -> None:
        self.send_response(code)
        self.send_header("Content-Type", typ)
        self.send_header("Content-Length", str(len(daten)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(daten)

    def do_GET(self):                                            # noqa: N802
        pfad = self.path.split("?")[0]
        if pfad.endswith("/api/stand"):
            with SCHLOSS:
                d = dict(STAND); d["verlauf"] = list(VERLAUF)
            self._senden(200, "application/json", json.dumps(d, separators=(",", ":")).encode())
        elif pfad.endswith("/api/gesund"):
            self._senden(200, "text/plain", b"ok")
        else:
            self._senden(200, "text/html; charset=utf-8", (Path(__file__).parent / "live_seite.html").read_bytes())

    def log_message(self, *a):                                   # still
        pass


def main(argv=None) -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--config", type=Path); p.add_argument("--daten", type=Path, required=True)
    p.add_argument("--port", type=int, default=8765)
    a = p.parse_args(argv)
    cfg = bot.konfig(a.config)
    threading.Thread(target=schleife, args=(cfg, a.daten), daemon=True).start()
    ThreadingHTTPServer(("0.0.0.0", a.port), Handler).serve_forever()


if __name__ == "__main__":
    main()
