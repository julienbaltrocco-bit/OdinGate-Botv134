"""Welche Datei unter reports/ wird von welchem Skript geschrieben bzw. gelesen? Statische Textsuche, nur lesend."""
import re, sys, subprocess
from pathlib import Path
ROOT = Path(sys.argv[1])
tracked = subprocess.run(["git", "ls-files", "reports"], cwd=ROOT, capture_output=True, text=True).stdout.split()
tracked = [t for t in tracked if not t.startswith("reports/audit/")]
quellen = {p: p.read_text() for p in sorted(list((ROOT/"scripts").glob("*.py")) + list((ROOT/"src/hybrid").glob("*.py")) + list((ROOT/"vorwaertstest").glob("*.py")))}
ohne = []
for t in sorted(tracked):
    name = Path(t).name
    stem = Path(t).stem
    treffer = []
    for p, txt in quellen.items():
        if name in txt:
            schreibt = bool(re.search(r"(write_text|to_csv|open\([^)]*['\"]w)", txt)) and bool(re.search(re.escape(name) + r"['\"]?\)?\s*\)?\.?(write_text|to_csv)|to_csv\([^)]*" + re.escape(name) + r"|" + re.escape(name) + r"['\"]\)\.write_text", txt))
            treffer.append((p.name, "schreibt" if schreibt else "nennt"))
    if not treffer:
        ohne.append(t)
    print(f"{t:45s} {treffer if treffer else '!! kein Skript nennt diese Datei'}")
print()
print("Dateien in reports/ ohne nennendes Skript:", len(ohne))
for o in ohne: print("  ", o)
