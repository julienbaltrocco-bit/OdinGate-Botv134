"""Verschlüsselt den Stand für das Trading Board (docs/stand.enc.json). Braucht kein Passwort:

Die Daten werden mit einem zufälligen AES-Schlüssel verschlüsselt, dieser mit dem öffentlichen RSA-Schlüssel
(vorwaertstest/board_pub.pem). Entschlüsseln kann nur, wer das Passwort des Boards kennt: Der private Schlüssel
liegt passwortgeschützt in docs/schluessel.json. Nur Standardbibliothek plus das Programm `openssl`.

    python3 -m vorwaertstest.board_verschluesseln --quelle vorwaertstest/lauf/dashboard.json --ziel ../docs/stand.enc.json
"""
import argparse
import base64
import json
import os
import subprocess
from pathlib import Path

HIER = Path(__file__).resolve().parent
b64 = lambda b: base64.b64encode(b).decode()


def aes_cbc(daten: bytes, key: bytes, iv: bytes) -> bytes:
    return subprocess.run(["openssl", "enc", "-aes-256-cbc", "-K", key.hex(), "-iv", iv.hex()], input=daten, capture_output=True, check=True).stdout


def verschluesseln(klartext: bytes, pub: Path) -> dict:
    key, iv = os.urandom(32), os.urandom(16)
    huelle = subprocess.run(["openssl", "pkeyutl", "-encrypt", "-pubin", "-inkey", str(pub), "-pkeyopt", "rsa_padding_mode:oaep",
                             "-pkeyopt", "rsa_oaep_md:sha256", "-pkeyopt", "rsa_mgf1_md:sha256"], input=key, capture_output=True, check=True).stdout
    return {"v": 1, "k": b64(huelle), "iv": b64(iv), "d": b64(aes_cbc(klartext, key, iv))}


def main(argv=None) -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--quelle", type=Path, required=True); p.add_argument("--ziel", type=Path, required=True)
    p.add_argument("--pub", type=Path, default=HIER / "board_pub.pem")
    a = p.parse_args(argv)
    a.ziel.parent.mkdir(parents=True, exist_ok=True)
    a.ziel.write_text(json.dumps(verschluesseln(a.quelle.read_bytes(), a.pub), separators=(",", ":")))
    print("Board-Stand verschlüsselt:", a.ziel.name)


if __name__ == "__main__":
    main()
