"""STELLVERTRETER fuer vorwaertstest.dashboard_daten (Git-Versuch des Audits)."""
import argparse, json
from pathlib import Path
p = argparse.ArgumentParser(); p.add_argument("--config"); p.add_argument("--daten", type=Path)
a = p.parse_args()
(a.daten / "dashboard.json").write_text(json.dumps({"laeufe": json.loads((a.daten / "zustand.json").read_text())["lauf"]}))
