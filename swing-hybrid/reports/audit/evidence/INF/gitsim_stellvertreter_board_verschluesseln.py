"""STELLVERTRETER fuer vorwaertstest.board_verschluesseln (Git-Versuch des Audits): kopiert nur; scheitert ohne Schluesseldatei wie das Original."""
import argparse, shutil, sys
from pathlib import Path
p = argparse.ArgumentParser(); p.add_argument("--quelle", type=Path); p.add_argument("--ziel", type=Path)
a = p.parse_args()
if not (Path(__file__).parent / "board_pub.pem").exists():
    sys.exit("openssl: oeffentlicher Schluessel board_pub.pem fehlt")
a.ziel.parent.mkdir(parents=True, exist_ok=True)
shutil.copy(a.quelle, a.ziel)
