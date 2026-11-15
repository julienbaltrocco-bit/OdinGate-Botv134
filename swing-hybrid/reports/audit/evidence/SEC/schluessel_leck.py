"""SEC: Tauchen API-Schluessel in Dateien, Meldungen oder Fehlertexten auf? Erfundene Schluessel, nachgestellte Boerse,
temporaeres Verzeichnis, kein Netz.   Aufruf: .venv/bin/python -I -B <skript> <pfad-zu-swing-hybrid>"""
import io, json, os, sys, tempfile, urllib.error
from pathlib import Path
sys.path.insert(0, sys.argv[1])
sys.path.insert(0, str(Path(__file__).resolve().parent))
from vorwaertstest import bot
from vorwaertstest.yubit import Yubit, YubitFehler
import live_schranken_boerse as lb

KEY, SECRET = "ERFUNDENER-KEY-0123456789", "ERFUNDENES-SECRET-9876543210"
meldungen = []
os.environ["YUBIT_LIVE"] = "ja"
bot.time.sleep = lambda s: None
api = lb.Boerse({"AAA": 100.0, "BBB": 50.0}, {"AAA": 110.0, "BBB": 40.0}, key=KEY, secret=SECRET)
cfg = {"modus": "live", "kapital_usd": 1000, "hebel": 3.0, "coins": ["AAA", "BBB"], "tagesverlust_limit": 1.0,
       "preisgrenze": 0.0005, "max_order_usd": 2000, "daten": "x"}
with tempfile.TemporaryDirectory() as d:
    api.jetzt = lb.JETZT
    bot.schritt(cfg, api, Path(d), lb.JETZT, melden=meldungen.append)
    meldungen.append(bot.bericht(cfg, Path(d)))
    inhalt = {p.name: p.read_text() for p in Path(d).iterdir()}
os.environ.pop("YUBIT_LIVE")
alles = "\n".join(meldungen) + "\n".join(inhalt.values())
print("Dateien des Laufs:", sorted(inhalt))
print("Schluessel oder Secret in Dateien/Meldungen:", KEY in alles or SECRET in alles)

def kaputt(req, timeout=20):
    raise urllib.error.HTTPError(req.full_url, 401, "Unauthorized", req.headers, io.BytesIO(b'{"code":10003,"message":"invalid api key"}'))
texte = []
for fn in (lambda a: a.positionen(), lambda a: a.order("AAAUSDT", "Buy", "1", "1", 1, False)):
    try:
        fn(Yubit(KEY, SECRET, pause=0, oeffner=kaputt))
    except YubitFehler as e:
        texte.append(str(e))
print("Fehlertexte:", texte)
print("Schluessel oder Secret in Fehlertexten:", any(KEY in t or SECRET in t for t in texte))
