"""Ein Durchlauf des Datensammlers. Aufruf alle fünf Minuten am Ende von vorwaertstest/stunde.sh:

    python3 -m sammler.lauf --daten /daten/sammler

Grundsätze:
- Nur öffentliche Marktdaten, kein Schlüssel, keine Orders. Nur Standardbibliothek und das Programm `git`.
- Der Sammler darf den Papier-Bot nie stören: Er läuft nach den Tests, schreibt nur in seinen eigenen Ordner (nie ins
  Repository des Bots), hält eine feste Zeitgrenze ein und endet auch bei Fehlern mit 0.
- Höflich abrufen: wenige gleichzeitige Abrufe mit Pause. Meldet eine Börse „zu viele Abrufe“ (HTTP 403, 418, 429 oder eine
  entsprechende Meldung), pausiert der Sammler für diese Börse eine Stunde. Scheitern fünf Orderbuch-Abrufe in Folge, endet die
  Runde für diesen Lauf; geschieht das in drei Läufen nacheinander, folgt ebenfalls eine Stunde Pause.
- Ablage in drei Schritten, jeder für sich wiederaufnehmbar:
    offen/<tabelle>_<tag>_<stunde>.csv          laufende Stunde, je Lauf werden Zeilen angehängt
    bereit/<monat>/<tabelle>/<tag>/<stunde>.csv.gz   abgeschlossene Stunde, gepackt, noch nicht veröffentlicht
    Daten-Zweig `<zweig>-JJJJ-MM` im Repository  veröffentlicht; danach wird die Datei aus bereit/ entfernt
  Was noch zu veröffentlichen ist, ergibt sich allein aus dem Ordner bereit/ (nicht aus einem Merkzettel).
- Der Arbeitsordner je Monat (zweig-JJJJ-MM) ist ersetzbar. Geht er verloren oder lehnt das Ziel den Push dauerhaft ab, beginnt
  der Sammler einen weiteren Zweig mit angehängter Nummer (`…-JJJJ-MM-2`); im Daten-Zweig wird nie etwas gelöscht oder überschrieben.
- Ausschalten: `"aktiv": false` in sammler/config.json (wirkt mit dem nächsten Lauf) oder die Datei <daten>/STOPP auf dem Server.
"""
import argparse
import concurrent.futures
import csv
import datetime as dt
import gzip
import io
import json
import os
import re
import shutil
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.request
from pathlib import Path

from . import kern

HIER = Path(__file__).resolve().parent
YUBIT = "https://openapi.yubit.com"
BINANCE = "https://fapi.binance.com"
P_TICKER = "/oapi/contract/market/public/v1/tickers"
P_BUCH = "/oapi/contract/market/public/v1/orderbooks"
UTC = dt.timezone.utc
PFLICHT = ("coins", "reihum", "baender_bp", "groessen_usd")
FEHLER_IN_FOLGE = 5          # so viele gescheiterte Orderbuch-Abrufe nacheinander beenden die Runde dieses Laufs
STOERLAEUFE = 3              # so viele solche Läufe nacheinander führen zur Stunden-Pause
FEHLVERSUCHE = 3             # so viele abgelehnte Pushes (bei erreichbarem Ziel) führen zu einem neuen Zweig
HOECHSTE_NUMMER = 20         # darüber wird kein weiterer Zweig begonnen (z. B. wenn dem Schlüssel das Schreibrecht fehlt)
IDENTITAET = {"GIT_AUTHOR_NAME": "OdinGate Sammler", "GIT_AUTHOR_EMAIL": "odingate-sammler@users.noreply.github.com",
              "GIT_COMMITTER_NAME": "OdinGate Sammler", "GIT_COMMITTER_EMAIL": "odingate-sammler@users.noreply.github.com"}


class Gebremst(RuntimeError):
    """Die Börse lehnt wegen zu vieler Abrufe ab."""


def holen(url: str, timeout: float = 8.0, hoechstens: float = 12.0):
    """Antwort als JSON. `timeout` gilt je Leseschritt, `hoechstens` für den ganzen Abruf (auch wenn die Antwort nur tröpfelt)."""
    beginn = time.monotonic()
    req = urllib.request.Request(url, headers={"User-Agent": "marktdaten/1.0", "Accept-Encoding": "gzip"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            teile = []
            while True:
                stueck = r.read(65536)
                if not stueck:
                    break
                teile.append(stueck)
                if time.monotonic() - beginn > hoechstens:
                    raise TimeoutError("Antwort zu langsam")
            roh = b"".join(teile)
            if r.headers.get("Content-Encoding") == "gzip":
                roh = gzip.decompress(roh)
    except urllib.error.HTTPError as e:
        if e.code in (403, 418, 429):
            raise Gebremst(f"HTTP {e.code}") from e
        raise RuntimeError(f"HTTP {e.code}") from e
    return json.loads(roh.decode())


def kurz(e: BaseException) -> str:
    return (type(e).__name__ + ": " + str(e))[:120]


def zeitteile(t: int) -> tuple:
    d = dt.datetime.fromtimestamp(t, UTC)
    return d.strftime("%Y-%m"), d.strftime("%Y-%m-%d"), d.strftime("%H")


def yubit(hole, pfad: str) -> dict:
    a = hole(YUBIT + pfad)
    if not isinstance(a, dict) or a.get("code") != 0:
        code = a.get("code") if isinstance(a, dict) else "?"
        text = str(a.get("message") if isinstance(a, dict) else a)[:60]
        if re.search(r"rate.?limit|too many|too frequent|frequency|busy", text, re.I):   # Drosselung, die nur im Antwortkörper gemeldet wird
            raise Gebremst(f"Yubit meldet {code} {text}")
        raise RuntimeError(f"Yubit meldet {code} {text}")
    return a


# ----------------------------------------------------------------------- Ablage ----
def anhaengen(daten: Path, art: str, t: int, spalten: list, zeilen: list) -> None:
    """Zeilen an die Stundendatei der Tabelle anhängen (ein Schreibvorgang; Kopfzeile, wenn die Datei neu ist).

    Endet die Datei nach einem Abbruch mitten in einer Zeile, wird diese mit einem Zeilenumbruch abgeschlossen (sie hat dann zu
    wenige Spalten und ist daran erkennbar). Passt die vorhandene Kopfzeile nicht zu den Spalten (Einstellung geändert oder
    Kopfzeile verstümmelt), wird die alte Datei beiseitegelegt und eine neue begonnen."""
    if not zeilen:
        return
    _, tag, stunde = zeitteile(t)
    datei = daten / "offen" / f"{art}_{tag}_{stunde}.csv"
    datei.parent.mkdir(parents=True, exist_ok=True)
    neu, flicken = True, False
    if datei.exists() and datei.stat().st_size > 0:
        with open(datei, "rb") as f:
            erste = f.readline().decode("utf-8", "replace").rstrip("\r\n")
            f.seek(-1, os.SEEK_END)
            letztes = f.read(1)
        if erste == ",".join(spalten):
            neu, flicken = False, letztes != b"\n"
        else:
            n = 1
            while (datei.parent / f"{art}-alt{n}_{tag}_{stunde}.csv").exists():
                n += 1
            datei.rename(datei.parent / f"{art}-alt{n}_{tag}_{stunde}.csv")
    puffer = io.StringIO()
    if flicken:
        puffer.write("\n")
    w = csv.DictWriter(puffer, fieldnames=spalten, lineterminator="\n")
    if neu:
        w.writeheader()
    for z in zeilen:
        w.writerow({k: z.get(k, "") for k in spalten})
    with open(datei, "a", newline="") as f:
        f.write(puffer.getvalue())


def packen(roh: bytes) -> bytes:
    puffer = io.BytesIO()
    with gzip.GzipFile(filename="", mode="wb", fileobj=puffer, compresslevel=9, mtime=0) as g:
        g.write(roh)
    return puffer.getvalue()


def _gepackt_lesen(datei: Path):
    """Inhalt einer bereitliegenden Datei; None, wenn es sie nicht gibt. Eine unlesbare Datei wird beiseitegelegt (gilt dann als nicht da)."""
    if not datei.exists():
        return None
    try:
        return gzip.decompress(datei.read_bytes())
    except Exception:
        datei.rename(datei.with_name(datei.name + ".kaputt"))
        return None


def veroeffentlicht(daten: Path, monat: str, rel: str) -> bool:
    """Steht diese Datei schon im Daten-Zweig des Monats (laut Arbeitsordner)? Dann darf ihr Name nicht noch einmal vergeben werden."""
    ordner = daten / f"zweig-{monat}"
    if not (ordner / ".git").exists():
        return False
    try:
        return git(ordner, "ls-files", "--error-unmatch", "--", rel, timeout=10).returncode == 0
    except Exception:
        return False


def stunden_abschliessen(daten: Path, t: int, belegt=veroeffentlicht) -> tuple:
    """Dateien abgeschlossener Stunden packen und nach bereit/<monat>/ legen. Gibt ({Monat: [Pfade]}, [Fehlertexte]) zurück."""
    jetzt = "_".join(zeitteile(t)[1:])
    neu, fehler = {}, []
    for datei in sorted((daten / "offen").glob("*_*_*.csv")):
        try:
            art, tag, stunde = datei.stem.rsplit("_", 2)
            if f"{tag}_{stunde}" >= jetzt:
                continue                                              # die laufende Stunde bleibt offen
            roh = datei.read_bytes()
            if not roh.strip():
                datei.unlink()
                continue
            monat, n = tag[:7], 0
            while True:                                               # ein freier Name: nichts überschreiben, was bereitliegt oder veröffentlicht ist
                rel = f"{art}/{tag}/{stunde}{'' if n == 0 else f'_nachtrag{n}'}.csv.gz"
                ziel = daten / "bereit" / monat / rel
                vorhanden = _gepackt_lesen(ziel)
                if vorhanden == roh or (vorhanden is None and not belegt(daten, monat, rel)):
                    break
                n += 1
            if vorhanden != roh:
                ziel.parent.mkdir(parents=True, exist_ok=True)
                tmp = ziel.with_name(ziel.name + ".teil")
                tmp.write_bytes(packen(roh))
                if gzip.decompress(tmp.read_bytes()) != roh:          # erst prüfen, dann die CSV löschen
                    raise OSError("gepackte Datei ist nicht lesbar")
                tmp.replace(ziel)
            datei.unlink()
            neu.setdefault(monat, []).append(rel)
        except Exception as e:
            fehler.append(f"packen {datei.name}: {kurz(e)}")
    return neu, fehler


def bereit_dateien(daten: Path, monat: str) -> list:
    wurzel = daten / "bereit" / monat
    return sorted(str(p.relative_to(wurzel)) for p in wurzel.rglob("*.csv.gz")) if wurzel.exists() else []


def monate_bereit(daten: Path) -> set:
    wurzel = daten / "bereit"
    return {p.name for p in wurzel.iterdir() if p.is_dir() and bereit_dateien(daten, p.name)} if wurzel.exists() else set()


def platz_mb(ordner: Path) -> float:
    summe = 0
    for wurzel, _, dateien in os.walk(ordner):
        for d in dateien:
            try:
                summe += os.lstat(os.path.join(wurzel, d)).st_size
            except OSError:
                pass
    return summe / 1_000_000


# --------------------------------------------------------------- Veröffentlichen ----
def git(ordner: Path, *a, timeout: float = 40.0) -> subprocess.CompletedProcess:
    env = dict(os.environ, GIT_TERMINAL_PROMPT="0", **IDENTITAET)       # eigene Identität, unabhängig von der Umgebung des Bots
    return subprocess.run(["git", "-C", str(ordner), *a], capture_output=True, text=True, timeout=max(1.0, timeout), env=env)


def fehlerzeile(r: subprocess.CompletedProcess) -> str:
    zeilen = [z.strip() for z in (r.stderr or "").splitlines() if z.strip()]
    wichtig = [z for z in zeilen if z.startswith(("fatal:", "error:")) or "! [" in z]
    return (wichtig or zeilen or ["ohne Meldung"])[0][:110]


def ziel_repo(cfg: dict) -> str:
    if cfg.get("ziel"):
        return cfg["ziel"]
    r = git(HIER, "remote", "get-url", "origin", timeout=10)            # dasselbe Repository, aus dem der Bot läuft
    if r.returncode != 0 or not r.stdout.strip():
        raise RuntimeError("Ziel-Repository unbekannt: " + fehlerzeile(r))
    return r.stdout.strip()


def zweigname(cfg: dict, monat: str, nr: int) -> str:
    return f"{cfg.get('zweig', 'odingate-marktdaten')}-{monat}" + ("" if nr <= 1 else f"-{nr}")


def repo_vorbereiten(ordner: Path, cfg: dict, monat: str, z: dict, rest) -> str:
    """Arbeitsordner des Monats-Zweigs bereitstellen und den Namen des Zweigs zurückgeben.

    Ist der Ordner vollständig eingerichtet (Marker), wird er weiterbenutzt. Sonst wird er neu angelegt, und zwar immer auf einem
    Zweig, den es beim Ziel noch nicht gibt: So muss nichts geholt werden, und es kann nichts überschrieben werden."""
    nr = int(z.setdefault("zweig_nr", {}).get(monat, 1))
    marker = ordner / ".git" / "eingerichtet"
    if marker.exists() and marker.read_text().strip() == zweigname(cfg, monat, nr):
        for sperre in (ordner / ".git").rglob("*.lock"):                # Rest eines abgebrochenen Laufs; es gibt immer nur einen Sammler
            sperre.unlink(missing_ok=True)
        return zweigname(cfg, monat, nr)
    shutil.rmtree(ordner, ignore_errors=True)                           # halb eingerichtet oder Zweig gewechselt: von vorn
    ordner.mkdir(parents=True)
    for a in (("init", "-q"), ("config", "gc.auto", "0"), ("remote", "add", "origin", ziel_repo(cfg))):
        r = git(ordner, *a, timeout=10)
        if r.returncode != 0:
            raise RuntimeError(f"git {a[0]}: {fehlerzeile(r)}")
    r = git(ordner, "ls-remote", "--heads", "origin", f"{zweigname(cfg, monat, 1)}*", timeout=rest())
    if r.returncode != 0:
        shutil.rmtree(ordner, ignore_errors=True)
        raise RuntimeError("Ziel nicht erreichbar: " + fehlerzeile(r))
    vorhanden = {zeile.split("refs/heads/", 1)[1] for zeile in r.stdout.splitlines() if "refs/heads/" in zeile}
    while zweigname(cfg, monat, nr) in vorhanden:
        nr += 1
    z["zweig_nr"][monat] = nr
    name = zweigname(cfg, monat, nr)
    r = git(ordner, "symbolic-ref", "HEAD", f"refs/heads/{name}", timeout=10)
    if r.returncode != 0:
        raise RuntimeError("git symbolic-ref: " + fehlerzeile(r))
    (ordner / ".git" / "info").mkdir(exist_ok=True)
    (ordner / ".git" / "info" / "exclude").write_text("*.teil\n*.kaputt\n")
    marker.write_text(name + "\n")                                      # erst jetzt gilt der Ordner als eingerichtet
    return name


def veroeffentlichen(daten: Path, cfg: dict, monat: str, z: dict, status: dict, rest) -> None:
    """Alles, was für den Monat bereitliegt, in den Daten-Zweig schreiben. Wirft bei Misserfolg; bereit/ bleibt dann unverändert."""
    ordner = daten / f"zweig-{monat}"
    dateien = bereit_dateien(daten, monat)
    name = repo_vorbereiten(ordner, cfg, monat, z, rest)
    for rel in dateien:
        ziel = ordner / rel
        ziel.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(daten / "bereit" / monat / rel, ziel)
    if dateien:
        (ordner / "status.json").write_text(json.dumps(dict(status, zweig=name), ensure_ascii=False, indent=1) + "\n")
    # Nur Neues aufnehmen, nie eine Löschung: Veröffentlichte Dateien liegen nicht mehr im Ordner und müssen im Zweig bleiben.
    r = git(ordner, "add", "--ignore-removal", "--", ".", timeout=rest())
    if r.returncode != 0:
        raise RuntimeError("git add: " + fehlerzeile(r))
    if git(ordner, "diff", "--cached", "--quiet", timeout=rest()).returncode != 0:
        r = git(ordner, "commit", "-q", "-m", f"Marktdaten bis {status.get('zeit', '')} UTC ({len(dateien)} Dateien, automatisch, ohne KI)", timeout=rest())
        if r.returncode != 0:
            raise RuntimeError("git commit: " + fehlerzeile(r))
    if git(ordner, "rev-parse", "-q", "--verify", "HEAD", timeout=10).returncode != 0:
        return                                                          # nichts bereit und noch nie etwas festgeschrieben
    offen = set(z.setdefault("ungesichert", []))
    offen.add(monat); z["ungesichert"] = sorted(offen)
    r = git(ordner, "push", "-q", "origin", f"HEAD:refs/heads/{name}", timeout=rest())
    if r.returncode != 0:
        grund = fehlerzeile(r)
        erreichbar = git(ordner, "ls-remote", "--heads", "origin", name, timeout=rest()).returncode == 0
        if erreichbar:                                                  # das Ziel antwortet, nimmt den Stand aber nicht an
            versuche = z.setdefault("fehlversuche", {})
            versuche[monat] = versuche.get(monat, 0) + 1
            if versuche[monat] >= FEHLVERSUCHE and int(z["zweig_nr"].get(monat, 1)) < HOECHSTE_NUMMER:   # neuer Zweig; was bereitliegt, geht beim nächsten Mal dorthin
                versuche[monat] = 0
                z["zweig_nr"][monat] = int(z["zweig_nr"].get(monat, 1)) + 1
                shutil.rmtree(ordner, ignore_errors=True)
                offen.discard(monat); z["ungesichert"] = sorted(offen)
                raise RuntimeError("git push dreimal abgelehnt, weiter auf neuem Zweig: " + grund)
        raise RuntimeError("git push: " + grund)
    z.setdefault("fehlversuche", {})[monat] = 0
    offen.discard(monat); z["ungesichert"] = sorted(offen)
    for rel in dateien:                                                 # veröffentlicht: lokal nicht mehr nötig
        (daten / "bereit" / monat / rel).unlink(missing_ok=True)
        (ordner / rel).unlink(missing_ok=True)


def alte_monate_entfernen(daten: Path, t: int, offen: set) -> None:
    """Arbeitsordner von Monaten, die älter als der Vormonat und vollständig veröffentlicht sind, vom Server nehmen."""
    d = dt.datetime.fromtimestamp(t, UTC)
    vormonat = (d.replace(day=1) - dt.timedelta(days=1)).strftime("%Y-%m")
    for ordner in list(daten.glob("zweig-????-??")) + list((daten / "bereit").glob("????-??")):
        monat = ordner.name[-7:]
        if monat < vormonat and monat not in offen:
            shutil.rmtree(ordner, ignore_errors=True)


# -------------------------------------------------------------------- Durchlauf ----
def zustand_laden(daten: Path) -> dict:
    try:
        z = json.loads((daten / "zustand.json").read_text())
        return z if isinstance(z, dict) else {}
    except (OSError, ValueError):
        return {}


def zustand_speichern(daten: Path, z: dict) -> None:
    tmp = daten / "zustand.json.tmp"
    tmp.write_text(json.dumps(z, ensure_ascii=False, indent=1, sort_keys=True))
    tmp.replace(daten / "zustand.json")


def lauf(daten: Path, cfg: dict, jetzt: float | None = None, hole=holen, melden=print, mit_git: bool = True) -> dict:
    beginn = time.monotonic()
    t = int(jetzt if jetzt is not None else time.time())
    monat, tag, _ = zeitteile(t)
    zeit = dt.datetime.fromtimestamp(t, UTC).strftime("%Y-%m-%d %H:%M")
    fehlend = [k for k in PFLICHT if not isinstance(cfg.get(k), list) or not cfg[k]]
    if fehlend:
        raise ValueError("Einstellung unvollständig: " + ", ".join(fehlend))
    daten.mkdir(parents=True, exist_ok=True)
    if not cfg.get("aktiv", True) or (daten / "STOPP").exists():
        melden("Sammler ist ausgeschaltet (config.json oder STOPP-Datei): kein Durchlauf.")
        return {"aus": True}
    z = zustand_laden(daten)
    lauf_nr = z["lauf_nr"] = int(z.get("lauf_nr", -1)) + 1               # eigener Zähler: unabhängig davon, wann genau der Lauf beginnt
    z["platz_mb"] = round(platz_mb(daten), 1)                            # in jedem Lauf neu messen: „voll“ löst sich von selbst
    z["voll"] = z["platz_mb"] > cfg.get("platz_mb", 1500)
    zustand_speichern(daten, z)                                          # zugleich Schreibprobe: ohne beschreibbaren Ordner kein Abruf
    frist = beginn + cfg.get("frist_s", 45)                              # danach keine neuen Abrufe mehr
    ende = beginn + cfg.get("frist_gesamt_s", 95)                        # danach kein neuer git-Schritt mehr
    pause = cfg.get("pause_nach_bremse_s", 3600)
    fehler = []
    stat = {"t": t, "lauf_nr": lauf_nr, "zeit": zeit, "ticker": 0, "tiefe_soll": 0, "tiefe_ist": 0, "binance": 0, "boersenzeit_ms": ""}
    coins, reihum = list(cfg["coins"]), list(cfg["reihum"])
    gruppe_a = set(coins) | set(reihum)
    voll = z["voll"]
    if voll:
        fehler.append(f"Platzgrenze erreicht ({z['platz_mb']} MB): es wird nichts Neues mitgeschrieben")

    def bremsen(wer: str, grund: str) -> None:
        z[f"{wer}_pause_bis"] = t + pause
        zustand_speichern(daten, z)                                      # sofort merken, auch wenn der Lauf später abbricht
        fehler.append(f"{'Yubit' if wer == 'yubit' else 'Binance'} bremst ({grund}): Pause für {pause // 60} Minuten")

    # 1. Yubit: alle Ticker in einem Abruf
    yubit_frei = not voll and z.get("yubit_pause_bis", 0) <= t
    if yubit_frei:
        try:
            a = yubit(hole, P_TICKER)
            zeilen = kern.ticker_zeilen(a["data"]["list"], t, gruppe_a, lauf_nr % max(1, cfg.get("alle_jede", 12)) == 0)
            anhaengen(daten, "ticker", t, kern.TICKER, zeilen)
            stat["ticker"], stat["boersenzeit_ms"] = len(zeilen), a.get("time", "")
        except Gebremst as e:
            yubit_frei = False
            bremsen("yubit", str(e))
        except Exception as e:
            fehler.append("ticker: " + kurz(e))
    elif not voll:
        fehler.append("Yubit-Pause nach Bremse")

    # 2. Yubit: Orderbücher (Coins immer, die übrigen reihum), wenige gleichzeitige Abrufe mit Pause
    if yubit_frei:
        auswahl = kern.tiefe_auswahl(coins, reihum, lauf_nr, cfg.get("tiefe_teile", 3))
        baender, groessen, ruhe = cfg["baender_bp"], cfg["groessen_usd"], cfg.get("pause_s", 0.3)
        stat["tiefe_soll"] = len(auswahl)
        halt, abbruch, schloss = threading.Event(), threading.Event(), threading.Lock()
        zeilen, pannen, folge, bremsgrund = [], [], [0], []

        def eins(sym):
            if halt.is_set() or abbruch.is_set() or time.monotonic() > frist:
                return
            try:
                d = yubit(hole, f"{P_BUCH}?depth=500&symbol={sym}")["data"]
                zeile = kern.buch_merkmale(d, t, baender, groessen)
                zeile["sym"] = sym
                with schloss:
                    zeilen.append(zeile); folge[0] = 0
            except Gebremst as e:
                halt.set(); bremsgrund.append(str(e))
            except Exception as e:
                with schloss:
                    pannen.append((sym, kurz(e))); folge[0] += 1
                    if folge[0] >= FEHLER_IN_FOLGE:
                        abbruch.set()
            time.sleep(ruhe)

        with concurrent.futures.ThreadPoolExecutor(max_workers=max(1, min(4, cfg.get("tiefe_threads", 2)))) as ex:
            list(ex.map(eins, auswahl))
        ordnung = {s: i for i, s in enumerate(auswahl)}
        zeilen.sort(key=lambda r: ordnung[r["sym"]])
        try:
            anhaengen(daten, "tiefe", t, kern.tiefe_spalten(baender, groessen), zeilen)
            stat["tiefe_ist"] = len(zeilen)
        except Exception as e:
            fehler.append("tiefe schreiben: " + kurz(e))
        if halt.is_set():
            bremsen("yubit", bremsgrund[0] if bremsgrund else "Orderbuch")
        if pannen:
            fehler.append(f"tiefe: {len(pannen)} Abrufe gescheitert, z. B. {pannen[0][0]} ({pannen[0][1]})")
        if abbruch.is_set():
            z["yubit_stoerlaeufe"] = z.get("yubit_stoerlaeufe", 0) + 1
            fehler.append(f"tiefe: nach {FEHLER_IN_FOLGE} Fehlern in Folge beendet")
            if z["yubit_stoerlaeufe"] >= STOERLAEUFE:
                z["yubit_stoerlaeufe"] = 0
                bremsen("yubit", f"{STOERLAEUFE} gestörte Läufe nacheinander")
        else:
            z["yubit_stoerlaeufe"] = 0
            if not halt.is_set() and len(zeilen) + len(pannen) < len(auswahl):
                fehler.append(f"tiefe: Zeitgrenze, {len(auswahl) - len(zeilen) - len(pannen)} Orderbücher ausgelassen")

    # 3. Binance: Spanne, Mark, Index, Funding derselben Kontrakte (zwei Abrufe für alle Symbole), nicht in jedem Lauf
    if (cfg.get("binance", True) and not voll and lauf_nr % max(1, cfg.get("binance_jede", 3)) == 0
            and z.get("binance_pause_bis", 0) <= t and time.monotonic() < frist):
        try:
            buecher = hole(BINANCE + "/fapi/v1/ticker/bookTicker")
            try:
                praemien = hole(BINANCE + "/fapi/v1/premiumIndex")
            except Gebremst:
                raise
            except Exception as e:
                praemien = []; fehler.append("binance premiumIndex: " + kurz(e))
            zeilen = kern.binance_zeilen(buecher, praemien, t, gruppe_a)
            anhaengen(daten, "binance", t, kern.BINANCE, zeilen)
            stat["binance"] = len(zeilen)
            if not zeilen:
                fehler.append("binance: keine Zeile für die gesuchten Kontrakte")
        except Gebremst as e:
            bremsen("binance", str(e))
        except Exception as e:
            fehler.append("binance: " + kurz(e))

    # 4. Abgeschlossene Stunden packen (nach bereit/), Laufzeile, Tageszähler; Zustand sichern, bevor git beginnt
    try:
        neu, packfehler = stunden_abschliessen(daten, t)
    except Exception as e:
        neu, packfehler = {}, ["packen: " + kurz(e)]
    fehler += packfehler
    stat["dauer_s"] = round(time.monotonic() - beginn, 1)
    stat["fehler"] = "; ".join(fehler)[:400]
    if not voll:
        try:
            anhaengen(daten, "laeufe", t, kern.LAEUFE, [stat])
        except Exception as e:
            fehler.append("laeufe schreiben: " + kurz(e))
    heute = z.get("heute") if (z.get("heute") or {}).get("tag") == tag else {"tag": tag, "laeufe": 0, "ticker": 0, "tiefe": 0, "binance": 0, "laeufe_mit_fehler": 0}
    heute["laeufe"] += 1; heute["ticker"] += stat["ticker"]; heute["tiefe"] += stat["tiefe_ist"]; heute["binance"] += stat["binance"]
    heute["laeufe_mit_fehler"] += 1 if fehler else 0
    z["heute"] = heute
    z["letzter_lauf"] = dict(stat)
    zustand_speichern(daten, z)

    # 5. Veröffentlichen: alles, was in bereit/ liegt, und Stände, deren Push noch aussteht
    offen = monate_bereit(daten) | set(z.get("ungesichert", []))
    if mit_git and offen:
        status = {"geschrieben": zeit, "zeit": zeit, "letzter_lauf": stat, "heute": heute, "platz_mb": z["platz_mb"], "voll": voll,
                  "einstellung": {k: cfg.get(k) for k in ("tiefe_teile", "tiefe_threads", "pause_s", "binance_jede", "alle_jede")},
                  "kontrakte": {"coins": len(coins), "reihum": len(reihum)}}
        rest = lambda: min(40.0, ende - time.monotonic())
        for m in sorted(offen):
            if rest() < 8:
                fehler.append("veröffentlichen: Zeitgrenze, wird im nächsten Lauf nachgeholt")
                break
            try:
                veroeffentlichen(daten, cfg, m, z, status, rest)
            except Exception as e:
                fehler.append(f"veröffentlichen {m}: {kurz(e)}")
            zustand_speichern(daten, z)
        offen = monate_bereit(daten) | set(z.get("ungesichert", []))
    if mit_git:
        try:
            alte_monate_entfernen(daten, t, offen)
        except Exception as e:
            fehler.append("aufräumen: " + kurz(e))
    z["letzter_lauf"] = dict(stat, fehler="; ".join(fehler)[:400])
    zustand_speichern(daten, z)
    melden(f"Sammler {zeit} UTC: {stat['ticker']} Ticker, {stat['tiefe_ist']}/{stat['tiefe_soll']} Orderbücher, {stat['binance']} Binance-Zeilen, "
           f"{time.monotonic() - beginn:.0f} s" + (f" | Hinweise: {'; '.join(fehler)[:300]}" if fehler else ""))
    return {"stat": stat, "fehler": fehler, "neu": neu, "push_offen": sorted(offen)}


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description="Datensammler: ein Durchlauf")
    p.add_argument("--daten", type=Path, required=True)
    p.add_argument("--config", type=Path, default=HIER / "config.json")
    p.add_argument("--ohne-git", action="store_true", help="nur mitschreiben und packen, nichts veröffentlichen (Probe)")
    a = p.parse_args(argv)
    try:
        lauf(a.daten, json.loads(a.config.read_text()), mit_git=not a.ohne_git)
    except BaseException as e:                                          # der Sammler meldet, bricht aber nie den Bot-Lauf ab
        if isinstance(e, KeyboardInterrupt):
            raise
        print("Sammler: unerwarteter Fehler:", kurz(e))
    return 0


if __name__ == "__main__":
    sys.exit(main())
