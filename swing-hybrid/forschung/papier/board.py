"""Stellt den Stand der Schattentests für das Trading Board (GitHub Pages) bereit.

Bündelt forschung/papier/ausgabe/<ID>.json aller Tests mit eigenem Ordner zu einer Datei und verschlüsselt sie mit dem
öffentlichen Schlüssel des Boards (board_pub.pem, derselbe wie für Test 1 und 2). Lesen kann sie nur, wer das Passwort
des Boards kennt. Ergebnis: forschung/papier/board/schattentests.enc.json. Nur Standardbibliothek plus `openssl`.

  python3 -m forschung.papier.board            (aus swing-hybrid/)
"""
import base64
import json
import os
import subprocess
import time
from pathlib import Path

HIER = Path(__file__).resolve().parent
b64 = lambda b: base64.b64encode(b).decode()


def verschluesseln(klartext: bytes, pub: Path) -> dict:
    """Wie vorwaertstest/board_verschluesseln.py: AES-256-CBC für die Daten, RSA-OAEP (SHA-256) für den AES-Schlüssel."""
    key, iv = os.urandom(32), os.urandom(16)
    huelle = subprocess.run(["openssl", "pkeyutl", "-encrypt", "-pubin", "-inkey", str(pub), "-pkeyopt", "rsa_padding_mode:oaep",
                             "-pkeyopt", "rsa_oaep_md:sha256", "-pkeyopt", "rsa_mgf1_md:sha256"], input=key, capture_output=True, check=True).stdout
    daten = subprocess.run(["openssl", "enc", "-aes-256-cbc", "-K", key.hex(), "-iv", iv.hex()], input=klartext, capture_output=True, check=True).stdout
    return {"v": 1, "k": b64(huelle), "iv": b64(iv), "d": b64(daten)}


def buendel() -> dict:
    tests = []
    for cfg in sorted(HIER.glob("*/konfiguration.json")):
        tid = cfg.parent.name
        aus = HIER / "ausgabe" / f"{tid}.json"
        if not aus.exists():                                       # vorbereitet, aber noch nie gelaufen
            continue
        d = json.loads(aus.read_text())
        extra = cfg.parent / "board.json"                          # Kurzname und Regel in Klartext für das Board (nicht Teil der eingefrorenen Regel)
        if extra.exists():
            d.update(json.loads(extra.read_text()))
        c = json.loads(cfg.read_text())
        d["beobachtung"] = bool(c.get("beobachtung"))
        tests.append(d)
    tests.sort(key=lambda d: (d.get("start", ""), d["id"]))
    return {"geschrieben": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "tests": tests}


def haupt() -> None:
    b = buendel()
    ziel = HIER / "board" / "schattentests.enc.json"
    ziel.parent.mkdir(exist_ok=True)
    ziel.write_text(json.dumps(verschluesseln(json.dumps(b, ensure_ascii=False).encode(), HIER / "board_pub.pem"), separators=(",", ":")))
    print(f"Board-Stand verschlüsselt: {len(b['tests'])} Tests ({', '.join(d['id'] for d in b['tests'])}), {ziel.stat().st_size // 1024} KB")


if __name__ == "__main__":
    haupt()
