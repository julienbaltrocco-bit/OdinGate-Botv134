"""Binance-Daten in Echtzeit für den Live-Papierhandel: schreibt Tagesdateien im Format des Binance-Archivs.

Der Papier-Rechner liest danach dieselben Dateien wie im Schattentest, nur dass der laufende Tag schon vorliegt.
Nur öffentliche Marktdaten, kein Schlüssel, nur Standardbibliothek.
"""
import datetime as dt
import json
import time
import urllib.error
import urllib.request
import zipfile
from pathlib import Path

BINANCE = "https://fapi.binance.com"
UTC = dt.timezone.utc
TAG_MS = 86_400_000
ARTEN = {"kerzen": ("5m", 300_000), "minuten": ("1m", 60_000)}      # Ordner im Zwischenspeicher -> (Intervall, Kerzenlänge)


def abruf(pfad: str, **params):
    url = BINANCE + pfad + "?" + "&".join(f"{k}={v}" for k, v in params.items())
    fehler = None
    for versuch in range(3):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "papierhandel/1.0"})
            with urllib.request.urlopen(req, timeout=20) as r:
                return json.loads(r.read().decode())
        except urllib.error.HTTPError as e:
            fehler = f"HTTP {e.code}"
            if e.code in (418, 429):                                  # Abruflimit: nicht nachfassen
                break
        except Exception as e:
            fehler = f"{type(e).__name__}: {e}"
        time.sleep(1.5 * (versuch + 1))
    raise RuntimeError(f"Binance-Abruf gescheitert ({pfad} {params.get('symbol', '')}): {fehler}")


def _zip_schreiben(ziel: Path, name: str, zeilen: list) -> None:
    ziel.parent.mkdir(parents=True, exist_ok=True)
    tmp = ziel.with_suffix(".teil")
    with zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr(name, "\n".join(zeilen) + "\n")
    tmp.replace(ziel)                                                 # erst vollständig schreiben, dann umbenennen


def tag_schreiben(sym: str, art: str, tag: dt.date, cache: Path, jetzt_ms: int) -> int:
    """Alle abgeschlossenen Kerzen eines Tages holen und als Archiv-Datei ablegen. Gibt die Zahl der Kerzen zurück."""
    intervall, laenge = ARTEN[art]
    start = int(dt.datetime(tag.year, tag.month, tag.day, tzinfo=UTC).timestamp() * 1000)
    roh = abruf("/fapi/v1/klines", symbol=sym, interval=intervall, startTime=start, endTime=min(start + TAG_MS - 1, jetzt_ms), limit=1500)
    zeilen = [",".join(str(x) for x in k[:12]) for k in roh if start <= int(k[0]) < start + TAG_MS and int(k[6]) < jetzt_ms]   # nur abgeschlossene Kerzen
    ziel = cache / art / f"{sym}-{tag}.zip"
    marke = ziel.with_suffix(".offen")
    if zeilen:
        _zip_schreiben(ziel, f"{sym}-{intervall}-{tag}.csv", zeilen)
    if len(zeilen) < TAG_MS // laenge:
        marke.parent.mkdir(parents=True, exist_ok=True); marke.write_text(str(len(zeilen)))
    elif marke.exists():
        marke.unlink()
    return len(zeilen)


def aktualisieren(symbole: list, minuten: bool, cache: Path, jetzt_ms: int) -> dict:
    """Heute immer; gestern, solange die Datei fehlt oder unvollständig ist. Ältere Tage kommen aus dem Archiv."""
    heute = dt.datetime.fromtimestamp(jetzt_ms / 1000, UTC).date()
    zahl = {}
    for sym in symbole:
        for art in (("kerzen", "minuten") if minuten else ("kerzen",)):
            for tag in (heute - dt.timedelta(days=1), heute):
                ziel = cache / art / f"{sym}-{tag}.zip"
                if tag == heute or not ziel.exists() or ziel.with_suffix(".offen").exists():
                    zahl[(sym, art, str(tag))] = tag_schreiben(sym, art, tag, cache, jetzt_ms)
    return zahl


def funding_schreiben(symbole: list, cache: Path, jetzt_ms: int) -> None:
    """Funding-Sätze des laufenden Monats (und in den ersten drei Tagen auch des Vormonats) im Format der Monatsdatei des Archivs."""
    heute = dt.datetime.fromtimestamp(jetzt_ms / 1000, UTC).date()
    monate = [heute.replace(day=1)]
    if heute.day <= 3:
        monate.append((monate[0] - dt.timedelta(days=1)).replace(day=1))
    for erster in monate:
        naechster = (erster + dt.timedelta(days=32)).replace(day=1)
        a, b = (int(dt.datetime(m.year, m.month, 1, tzinfo=UTC).timestamp() * 1000) for m in (erster, naechster))
        for sym in symbole:
            roh = abruf("/fapi/v1/fundingRate", symbol=sym, startTime=a, endTime=min(b - 1, jetzt_ms), limit=1000)
            zeilen = [f"{int(r['fundingTime'])},8,{r['fundingRate']}" for r in roh if a <= int(r["fundingTime"]) < b]
            if zeilen:
                _zip_schreiben(cache / "funding" / f"{sym}-{erster:%Y-%m}.zip", f"{sym}-fundingRate-{erster:%Y-%m}.csv", zeilen)
