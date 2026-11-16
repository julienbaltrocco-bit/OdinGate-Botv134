"""INF: Fehlerbehandlung des Yubit-Clients (vorwaertstest/yubit.py:77-86) gegen einen lokalen Testserver auf 127.0.0.1.

Kein Zugriff auf die Boerse, kein Netz nach aussen. Der echte Code-Pfad urllib.request -> Yubit._anfrage wird benutzt,
nur die Basisadresse zeigt auf den lokalen Server; das Zeitlimit wird fuer den Haenge-Fall auf 1 s verkuerzt.

Aufruf (aus swing-hybrid):  .venv/bin/python -I -B <dieses Skript>
"""
import socket
import struct
import sys
import tempfile
import threading
import time
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

sys.path.insert(0, "/home/user/OdinGate-Botv134/swing-hybrid")
from vorwaertstest import bot                                  # noqa: E402
from vorwaertstest.yubit import Yubit, YubitFehler            # noqa: E402

MODUS = {"m": "ok"}
GUT = b'{"code":0,"data":{"list":[{"bidPrice":"1","askPrice":"2","lastPrice":"1.5","markPrice":"1.5","fundingRate":"100","turnover24h":"5"}]}}'


class H(BaseHTTPRequestHandler):
    def do_GET(self):                                           # noqa: N802
        m = MODUS["m"]
        if m == "abbruch":                                      # Verbindung ohne Antwort schliessen
            self.close_connection = True
            return
        if m == "reset":                                        # TCP-Reset
            self.connection.setsockopt(socket.SOL_SOCKET, socket.SO_LINGER, struct.pack("ii", 1, 0))
            self.connection.close(); self.close_connection = True
            return
        if m == "haengt":
            time.sleep(3); self.close_connection = True
            return
        if m == "429":
            self.send_response(429); self.send_header("Content-Length", "9"); self.end_headers(); self.wfile.write(b"too many\n")
            return
        koerper = {"ok": GUT, "html": b"<html>Wartung</html>", "liste": b"[]", "leer": b'{"code":0,"data":{"list":[]}}',
                   "null": GUT.replace(b'"bidPrice":"1"', b'"bidPrice":null'), "fehlercode": b'{"code":10006,"message":"rate limit"}',
                   "teil": b'{"code":0,"da'}[m]
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(1000 if m == "teil" else len(koerper)))
        self.end_headers(); self.wfile.write(koerper); self.wfile.flush()
        if m == "teil":
            self.close_connection = True

    def log_message(self, *a):
        pass


srv = ThreadingHTTPServer(("127.0.0.1", 0), H)
threading.Thread(target=srv.serve_forever, daemon=True).start()
ohne_proxy = urllib.request.build_opener(urllib.request.ProxyHandler({}))
api = Yubit(basis=f"http://127.0.0.1:{srv.server_address[1]}", pause=0, oeffner=lambda req, timeout=20: ohne_proxy.open(req, timeout=1))

print("Antwort des Servers                         -> was Yubit.ticker() wirft")
gefangen = (YubitFehler, KeyError, ValueError, IndexError)     # genau die Liste aus bot.py:172
for m, text in (("ok", "gueltige Antwort"), ("429", "HTTP 429"), ("fehlercode", "code != 0"), ("html", "HTML statt JSON"),
                ("haengt", "keine Antwort (Zeitlimit)"), ("leer", "leere Liste"), ("abbruch", "Verbindung ohne Antwort geschlossen"),
                ("reset", "TCP-Reset"), ("teil", "Antwort bricht mitten im Text ab"), ("liste", "JSON-Liste statt Objekt"),
                ("null", "Feld bidPrice ist null")):
    MODUS["m"] = m
    try:
        api.ticker("BTCUSDT")
        aus = "kein Fehler"
    except Exception as e:                                      # noqa: BLE001
        art = "wird in bot.py:172 abgefangen (Coin wird uebersprungen)" if isinstance(e, gefangen) else "NICHT abgefangen: der ganze Lauf bricht ab"
        aus = f"{type(e).__module__}.{type(e).__name__}: {str(e)[:60]!r}  -> {art}"
    print(f"  {text:40s} -> {aus}")

print("\nGanzer Durchlauf bot.schritt mit zehn Coins, wenn EINE Verbindung ohne Antwort geschlossen wird:")
MODUS["m"] = "abbruch"
cfg = {"modus": "papier", "kapital_usd": 5000, "hebel": 3.0, "coins": ["BTC", "ETH", "SOL", "XRP", "DOT", "DOGE", "ADA", "LINK", "AVAX", "LTC"],
       "tagesverlust_limit": 1.0, "preisgrenze": 0.0005, "max_order_usd": 2000}
d = Path(tempfile.mkdtemp(prefix="inf_http_"))
try:
    bot.schritt(cfg, api, d, melden=lambda *_: None)
    print("  Lauf beendet")
except SystemExit as e:
    print("  SystemExit:", str(e)[:120])
except Exception as e:                                          # noqa: BLE001
    print(f"  Ausnahme verlaesst bot.schritt: {type(e).__name__}: {e}  | geschriebene Dateien: {sorted(p.name for p in d.iterdir())}")
print("\nZeitlimit je Abruf laut yubit.py:78: 20 s; Abrufe je Coin in bot.markt_lesen: 5 (bot.py:84,91,94,97,98); keine Wiederholung, kein Gesamtlimit.")
print("Rechnerische Obergrenze eines Laufs bei haengender Schnittstelle: 10 Coins x 5 Abrufe x 20 s = 1000 s je Konto, also bis 2000 s je stunde.sh-Lauf (Takt: rund 300 s).")
