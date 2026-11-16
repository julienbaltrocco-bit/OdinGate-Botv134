"""SEC: (a) Verhalten des Yubit-Clients bei Weiterleitungen, (b) Rechenaufwand der Schluesselableitung des Boards.

Aufruf:  .venv/bin/python -I -B <dieses Skript> <pfad-zu-swing-hybrid>
(a) laeuft nur gegen zwei lokale Testserver auf 127.0.0.1 mit einem ERFUNDENEN Schluessel ("testkey"/"testsecret").
(b) misst PBKDF2-HMAC-SHA256 mit ERFUNDENEM Passwort und ZUFAELLIGEM Salz. Die Datei docs/schluessel.json wird dafuer
    nicht gelesen, es wird kein Passwort geraten und nichts entschluesselt.
"""
import hashlib
import json
import os
import sys
import threading
import time
import urllib.request
from http.server import BaseHTTPRequestHandler, HTTPServer

sys.path.insert(0, sys.argv[1])
from vorwaertstest.yubit import Yubit  # noqa: E402

# ---------------------------------------------------------------- (a) Weiterleitung ----
gesehen = []


class Ziel(BaseHTTPRequestHandler):
    def do_GET(self):  # noqa: N802
        gesehen.append({k: v for k, v in self.headers.items() if k.upper().startswith("MF-")})
        body = b'{"code":0,"data":{"list":[]}}'
        self.send_response(200); self.send_header("Content-Length", str(len(body))); self.end_headers(); self.wfile.write(body)

    def log_message(self, *a):
        pass


class Umleiter(BaseHTTPRequestHandler):
    ziel = ""

    def do_GET(self):  # noqa: N802
        self.send_response(302); self.send_header("Location", self.ziel + self.path); self.send_header("Content-Length", "0"); self.end_headers()

    def log_message(self, *a):
        pass


s_ziel = HTTPServer(("127.0.0.1", 0), Ziel)
s_um = HTTPServer(("127.0.0.1", 0), Umleiter)
Umleiter.ziel = f"http://localhost:{s_ziel.server_port}"          # anderer Hostname und anderer Port als der Client anspricht
for s in (s_ziel, s_um):
    threading.Thread(target=s.serve_forever, daemon=True).start()
ohne_proxy = urllib.request.build_opener(urllib.request.ProxyHandler({}))     # Standard-Weiterleitungslogik, nur ohne Proxy
api = Yubit("testkey", "testsecret", basis=f"http://127.0.0.1:{s_um.server_port}", pause=0, oeffner=ohne_proxy.open)
api.positionen("USDT")
print("(a) Weiterleitung eines signierten GET auf einen anderen Host:")
print("    Client spricht an:  ", api.basis)
print("    Server leitet um auf:", Umleiter.ziel)
print("    Beim fremden Ziel angekommene Kopfzeilen:", json.dumps(gesehen[-1] if gesehen else {}, indent=None))
print("    => API-Schluessel und Signatur werden mitgeschickt:", bool(gesehen and "testkey" in gesehen[-1].values()))
print("    Hinweis: yubit.py akzeptiert jede 'basis' (auch http://), prueft das Schema nicht und begrenzt Weiterleitungen nicht.")
for s in (s_ziel, s_um):
    s.shutdown()

# ------------------------------------------------------------------------ (b) KDF ----
RUNDEN = 600_000
salz = os.urandom(16)
t = time.perf_counter(); hashlib.pbkdf2_hmac("sha256", b"erfundenes-passwort", salz, RUNDEN, 48); t48 = time.perf_counter() - t
t = time.perf_counter(); hashlib.pbkdf2_hmac("sha256", b"erfundenes-passwort", salz, RUNDEN, 32); t32 = time.perf_counter() - t
print()
print("(b) PBKDF2-HMAC-SHA256, 600.000 Runden, ein CPU-Kern dieser Maschine (hashlib/OpenSSL):")
print(f"    48 Byte (wie das Board ableitet: 2 Bloecke): {t48:.3f} s")
print(f"    32 Byte (reicht dem Angreifer: 1 Block)    : {t32:.3f} s  -> {1 / t32:.1f} Versuche/s je Kern")
RATE_GPU = 8.9e6 * 999 / RUNDEN      # ANNAHME: rund 8,9 Mio/s bei 999 Runden (veroeffentlichte hashcat-Werte, Modus 10900, eine RTX 4090)
print(f"    Annahme fuer eine aktuelle Grafikkarte: {RATE_GPU:,.0f} Versuche/s (nicht hier gemessen)")
print()
print(f"    {'Passwortraum':46s} {'Kandidaten':>10s}  {'1 CPU-Kern':>14s}  {'1 GPU (Annahme)':>16s}  {'100 GPUs':>12s}")


def dauer(sek):
    for name, s in (("Jahre", 31557600), ("Tage", 86400), ("Std.", 3600), ("Min.", 60)):
        if sek >= s:
            return f"{sek / s:,.1f} {name}"
    return f"{sek:.1f} s"


for name, n in (("4 Ziffern", 10 ** 4), ("6 Ziffern", 10 ** 6), ("Liste der 10 Mio. haeufigsten Passwoerter", 10 ** 7),
                ("6 Kleinbuchstaben", 26 ** 6), ("Woerterliste mit Regeln, 1 Mrd. Kandidaten", 10 ** 9),
                ("8 Kleinbuchstaben", 26 ** 8), ("8 Kleinbuchstaben+Ziffern", 36 ** 8), ("8 Gross/Klein+Ziffern", 62 ** 8),
                ("10 Gross/Klein+Ziffern", 62 ** 10), ("12 Gross/Klein+Ziffern", 62 ** 12), ("5 Zufallswoerter (Diceware, 7776^5)", 7776 ** 5)):
    print(f"    {name:46s} {n:10.1e}  {dauer(n * t32):>14s}  {dauer(n / RATE_GPU):>16s}  {dauer(n / RATE_GPU / 100):>12s}")
print("    (Zeit fuer den GESAMTEN Raum; im Mittel die Haelfte.)")
