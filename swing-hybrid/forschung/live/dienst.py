"""Live-Dienst für einen Papier-Test: läuft dauerhaft auf einem eigenen Server (siehe live/install.sh). Nur Simulation, keine Orders.

Alle fünf Minuten: (1) Binance-Kerzen des laufenden Tages holen, (2) den eingefrorenen Test neu rechnen, (3) bei einem neuen
Einstieg am Yubit-Orderbuch messen, was er gekostet hätte, (4) den Stand verschlüsselt für das Trading Board bereitstellen.
Einmal täglich: Kontrolle gegen den Schattentest aus den Archivdaten.

  python -m forschung.live.dienst L-dc1d27a3            Dauerbetrieb
  python -m forschung.live.dienst L-dc1d27a3 --einmal   ein Durchlauf (Probe)
"""
import datetime as dt
import json
import os
import subprocess
import sys
import time
import traceback
from pathlib import Path

F = Path(__file__).resolve().parents[1]
W = F.parent
sys.path.insert(0, str(W))
from forschung.live import daten as LD, yubit as Y
from forschung.papier import board as B, runner as R

UTC = dt.timezone.utc
DATEN = Path(os.environ.get("ODINGATE_DATEN", W / "data/live"))
CACHE_LIVE, CACHE_ARCHIV, ZWEIG_ORDNER = DATEN / "cache_live", DATEN / "cache_archiv", DATEN / "zweig"
SCHLUESSEL = Path(os.environ.get("ODINGATE_SCHLUESSEL", "/schluessel/deploy"))
ZIEL_REPO = os.environ.get("ODINGATE_ZIEL", "git@github.com:julienbaltrocco-bit/OdinGate-Botv134.git")
ZIEL_ZWEIG = "odingate-live"
TAKT = 300


def log(*teile):
    print(time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime()), *teile, flush=True)


class Quelle:
    """Wie der Papier-Runner, aber: gestern und heute kommen nur aus den live geschriebenen Dateien, ältere Tage aus dem Archiv."""

    def __init__(self, sperrtag):
        self.sperrtag = str(sperrtag)

    def __getattr__(self, name):
        return getattr(R, name)

    def holen(self, url, cache):
        if cache.exists():
            return cache.read_bytes()
        if cache.stem.split("-", 1)[1] >= self.sperrtag:
            return None
        return R.holen(url, CACHE_ARCHIV / cache.relative_to(CACHE_LIVE))


def schritt(test_id: str, PF, zustand: dict) -> dict:
    jetzt_ms = int(time.time() * 1000)
    heute = dt.datetime.fromtimestamp(jetzt_ms / 1000, UTC).date()
    ordner = R.HIER / test_id
    cfg = json.loads((ordner / "konfiguration.json").read_text())
    steuer = json.loads((ordner / "steuerung.json").read_text())
    symbole = sorted({c + "USDT" for c in cfg["coins"]} | {"BTCUSDT", "ETHUSDT"})
    LD.aktualisieren(symbole, "minuten" in cfg["daten"], CACHE_LIVE, jetzt_ms)
    stunde = jetzt_ms // 3_600_000
    if zustand.get("funding_stunde") != stunde:
        try:
            LD.funding_schreiben(symbole, CACHE_LIVE, jetzt_ms); zustand["funding_stunde"] = stunde
        except Exception as e:                                        # Funding fehlt dann vorerst und wird als ausstehend geführt
            log("Funding nicht geholt:", e)
    basis = {"id": cfg["id"], "name": cfg["name"], "version": cfg["version"], "art": cfg["art"],
             "lauf_id": time.strftime("%Y%m%dT%H%M%SZ", time.gmtime()) + "-" + os.urandom(3).hex(),
             "letzter_lauf": time.strftime("%Y-%m-%d %H:%M UTC", time.gmtime()), "aktualisiert": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
             "takt_stunden": round(TAKT / 3600, 3), "start": cfg["start"], "kapital": cfg["kapital_usd"], "hebel": cfg["hebel"], "maerkte": cfg["coins"],
             "regel": cfg["regel"], "validierung": cfg["validierung"], "eingefroren": cfg["eingefroren"]}
    doc = PF.lauf(ordner, cfg, steuer, basis, heute + dt.timedelta(days=2), CACHE_LIVE, True, Quelle(heute - dt.timedelta(days=1)))
    doc.update(live=True, ersetzt=cfg.get("ersetzt"), beobachtung=bool(cfg.get("beobachtung")))
    if (ordner / "board.json").exists():
        doc.update(json.loads((ordner / "board.json").read_text()))
    # Neuer Einstieg in dieser Kerze: Kosten am Yubit-Orderbuch messen (Vergleich mit dem Kostenmodell)
    for p in doc.get("offene_positionen", []):
        marke = f"{p['coin']}|{p['seit']}"
        if marke in zustand["gemessen"] or p["seit"][:16] != (doc.get("daten_bis") or "")[:16]:
            continue
        zustand["gemessen"].append(marke)
        try:
            m = Y.messen(p["coin"], doc["positionsgroesse_usd"], p["richtung"] == "Long")
            m.update(einstieg=p["seit"], modell_bp=round(cfg["kosten"]["slippage_bp_je_order"][p["coin"]], 2))
            zustand["messungen"].append(m)
            log("Yubit-Messung", m)
        except Exception as e:
            log("Yubit-Messung gescheitert:", p["coin"], e)
    ms = zustand["messungen"]
    if ms:
        doc["yubit"] = {"anzahl": len(ms), "mittel_bp": round(sum(m["kosten_bp"] for m in ms) / len(ms), 2),
                        "modell_bp": round(sum(m["modell_bp"] for m in ms) / len(ms), 2), "letzte": ms[-20:][::-1]}
    if zustand.get("kontrolle"):
        doc["kontrolle"] = zustand["kontrolle"]
    (R.HIER / "ausgabe" / f"{test_id}.json").write_text(json.dumps(doc, ensure_ascii=False, indent=1))
    return doc


def kontrolle(doc: dict, zustand: dict) -> None:
    """Einmal täglich: den Schattentest (Archivdaten) rechnen und mit dem Live-Stand vergleichen."""
    quelle, heute = doc.get("ersetzt"), time.strftime("%Y-%m-%d", time.gmtime())
    if not quelle or zustand.get("kontrolle_tag") == heute or time.gmtime().tm_hour < 9 or (time.gmtime().tm_hour == 9 and time.gmtime().tm_min < 40):
        return
    zustand["kontrolle_tag"] = heute
    try:
        if not (R.HIER / ".cache").exists():
            CACHE_ARCHIV.mkdir(parents=True, exist_ok=True); (R.HIER / ".cache").symlink_to(CACHE_ARCHIV, target_is_directory=True)
        subprocess.run([sys.executable, "-m", "forschung.papier.runner", quelle], cwd=W, check=False, capture_output=True, timeout=1800)
        b = json.loads((R.HIER / "ausgabe" / f"{quelle}.json").read_text())
        bis = (b.get("daten_bis") or "")[:16]
        archiv = {(t["coin"], t["ein"]): t for t in b.get("letzte_trades", [])}
        live = {(t["coin"], t["ein"]): t for t in doc.get("letzte_trades", []) if t["aus"] <= bis}
        gleich = [k for k in archiv if k in live]
        diff = max((abs(archiv[k]["netto_bp"] - live[k]["netto_bp"]) for k in gleich), default=0.0)
        ok = set(archiv) == set(live) and diff < 10 and b.get("status") != "Fehler"
        zustand["kontrolle"] = {"geprueft": time.strftime("%Y-%m-%d %H:%M UTC", time.gmtime()), "stand": bis, "archiv": len(archiv), "live": len(live), "gleich": len(gleich),
                                "groesste_abweichung_bp": round(diff, 1), "ok": ok,
                                "text": (f"Kontrolle gegen Archivdaten bis {bis}: {len(gleich)} von {len(archiv)} Trades gleich" + ("" if ok else " (ABWEICHUNG, Live-Stand prüfen)"))}
        log(zustand["kontrolle"]["text"])
    except Exception as e:
        log("Kontrolle gescheitert:", e)


def _git(*a, check=True):
    env = dict(os.environ, GIT_SSH_COMMAND=f"ssh -i {SCHLUESSEL} -o IdentitiesOnly=yes -o StrictHostKeyChecking=accept-new -o UserKnownHostsFile={DATEN / 'known_hosts'} -o ConnectTimeout=15")
    return subprocess.run(["git", "-C", str(ZWEIG_ORDNER), *a], check=check, capture_output=True, text=True, env=env, timeout=90)


def veroeffentlichen(docs: list, zustand: dict) -> None:
    """Stand verschlüsselt in einen eigenen Daten-Zweig schreiben (ein einziger Commit, der jeweils ersetzt wird). Das Board liest ihn von dort."""
    bild = json.dumps([(d["id"], d.get("status"), d.get("trades"), len(d.get("offene_positionen", [])), (d.get("yubit") or {}).get("anzahl"),
                        (d.get("kontrolle") or {}).get("geprueft"), d.get("fehler")) for d in docs], ensure_ascii=False)
    if bild == zustand.get("bild") and time.time() - zustand.get("gesendet", 0) < 1500:      # ohne Änderung alle 25 Minuten ein Lebenszeichen
        return
    if not SCHLUESSEL.exists():
        log("Kein Schlüssel für GitHub vorhanden: Stand wird nicht veröffentlicht."); return
    if not (ZWEIG_ORDNER / ".git").exists():
        ZWEIG_ORDNER.mkdir(parents=True, exist_ok=True)
        _git("init", "-q"); _git("checkout", "-q", "--orphan", ZIEL_ZWEIG); _git("remote", "add", "origin", ZIEL_REPO)
        _git("config", "user.name", "OdinGate Live"); _git("config", "user.email", "noreply@anthropic.com")
    paket = B.verschluesseln(json.dumps({"geschrieben": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "tests": docs}, ensure_ascii=False).encode(), B.HIER / "board_pub.pem")
    (ZWEIG_ORDNER / "live.enc.json").write_text(json.dumps(paket, separators=(",", ":")))
    _git("add", "live.enc.json")
    text = "Live-Papierhandel: Stand " + time.strftime("%Y-%m-%d %H:%M", time.gmtime()) + " UTC (verschlüsselt, wird laufend ersetzt)"
    _git("commit", "-q", "--amend", "-m", text) if _git("rev-parse", "-q", "--verify", "HEAD", check=False).returncode == 0 else _git("commit", "-q", "-m", text)
    r = _git("push", "-q", "--force", "origin", f"HEAD:{ZIEL_ZWEIG}", check=False)
    if r.returncode == 0:
        zustand["bild"], zustand["gesendet"] = bild, time.time()
        log("Stand veröffentlicht")
    else:
        log("Veröffentlichen gescheitert (ist der Schlüssel bei GitHub eingetragen, mit Schreibrecht?):", (r.stderr or "").strip().splitlines()[-1:] or "")


def haupt(test_id: str, einmal: bool = False) -> int:
    for o in (CACHE_LIVE, CACHE_ARCHIV, R.HIER / "zustand", R.HIER / "ausgabe"):
        o.mkdir(parents=True, exist_ok=True)
    zdatei = DATEN / f"zustand_{test_id}.json"
    zustand = json.loads(zdatei.read_text()) if zdatei.exists() else {}
    zustand.setdefault("gemessen", []); zustand.setdefault("messungen", [])
    sys.path.insert(0, str(R.HIER / test_id / "code"))
    import papier_fabrik as PF                                        # eingefrorener Code dieses Tests
    log(f"Live-Dienst {test_id} gestartet (nur Simulation, keine Orders). Erster Durchlauf lädt rund 40 Tage Archivdaten und dauert einige Minuten.")
    while True:
        beginn = time.time()
        try:
            doc = schritt(test_id, PF, zustand)
            kontrolle(doc, zustand)
            log(f"{test_id}: Status={doc['status']} Daten bis {doc.get('daten_bis')} Trades={doc.get('trades')} offen={len(doc.get('offene_positionen', []))} "
                f"Konto={doc.get('kontostand')} Fehler={len(doc.get('fehler', []))} ({time.time() - beginn:.0f} s)")
            veroeffentlichen([doc], zustand)
        except Exception as e:
            log("FEHLER im Durchlauf:", type(e).__name__, e)
            traceback.print_exc()
        zdatei.write_text(json.dumps(zustand, ensure_ascii=False))
        if einmal:
            return 0
        time.sleep(max(5.0, TAKT - (time.time() - 12) % TAKT))        # nächster Lauf zwölf Sekunden nach der vollen Fünf-Minuten-Marke


if __name__ == "__main__":
    sys.exit(haupt(sys.argv[1], "--einmal" in sys.argv))
