"""Vorschau-Seite aus dem Register bauen: vorlage.html + register/register.json -> index.html (Daten eingebettet).

Die Seite liest ausschließlich das Register. Ein neuer Eintrag im Register erscheint ohne Änderung an der Seite.
Aufruf: python -I forschung/register/bauen.py && python -I forschung/dashboard_dev/bauen.py
"""
import json
from pathlib import Path

HIER = Path(__file__).parent
register = json.loads((HIER.parent / "register/register.json").read_text())
seite = (HIER / "vorlage.html").read_text().replace("/*REGISTER*/null", json.dumps(register, ensure_ascii=False).replace("</", "<\\/"))
(HIER / "index.html").write_text(seite)
print("gebaut:", len(seite) // 1024, "KB,", len(register["eintraege"]), "Einträge")
