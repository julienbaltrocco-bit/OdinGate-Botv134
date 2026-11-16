"""STELLVERTRETER fuer vorwaertstest.bot (nur fuer den Git-Versuch des Audits): zaehlt Laeufe statt zu handeln."""
import argparse, json, os, subprocess, sys
from pathlib import Path
p = argparse.ArgumentParser(); p.add_argument("befehl"); p.add_argument("--config"); p.add_argument("--daten", type=Path)
a = p.parse_args()
a.daten.mkdir(parents=True, exist_ok=True)
zp = a.daten / "zustand.json"
z = json.loads(zp.read_text()) if zp.exists() else {"lauf": 0}
z["lauf"] += 1
with open(a.daten / "stand.csv", "a") as f:
    f.write(f"lauf {z['lauf']} von {os.environ.get('INF_WER', '?')}\n")
zp.write_text(json.dumps(z))
print(f"[Stellvertreter-Bot] {a.daten.name}: Lauf {z['lauf']}")
# Einmaliger Eingriff "waehrend des Laufs" (nach dem pull, vor dem push), nur im ersten Konto
haken, marke = os.environ.get("INF_HAKEN"), os.environ.get("INF_MARKE")
if haken and marke and a.daten.name == "lauf" and os.path.exists(marke):
    os.remove(marke)
    subprocess.run(["bash", haken], check=True)
