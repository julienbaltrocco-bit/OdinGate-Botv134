"""Parität: Der Runner (Standardbibliothek, Archivdateien) muss dieselben Trades bilden wie die Rückrechnung (pandas).

Braucht Netz (Binance-Archiv) und forschung/ergebnisse/e13_version11_trades.csv. Fenster: 20. bis 31.03.2025 (Validierung).
"""
import csv
import datetime as dt
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from forschung.papier import runner as R

CSV = ROOT / "forschung/ergebnisse/e13_version11_trades.csv"


@pytest.mark.skipif(not CSV.exists(), reason="Trade-Liste der Rückrechnung fehlt")
def test_runner_gleich_rueckrechnung(tmp_path):
    cfg = json.loads((Path(R.__file__).parent / "OS-1.1" / "konfiguration.json").read_text())
    cfg["start"] = "2025-03-20T00:00:00Z"
    cfg["anzahl_letzte_trades"] = 500
    cache = Path(R.__file__).parent / ".cache_paritaet"
    try:
        d = R.lauf("OS-1.1", dt.date(2025, 4, 1), cache, schreiben=False, cfg=cfg)
    except RuntimeError as e:
        pytest.skip(f"Archiv nicht erreichbar: {e}")
    von, bis = "2025-03-20 06:00", "2025-03-31 12:00"
    soll = {(z["coin"], z["ein"][:16]): z for z in csv.DictReader(open(CSV)) if von <= z["ein"][:16] < bis}
    ist = {(t["coin"], t["ein"]): t for t in d["letzte_trades"] if von <= t["ein"] < bis}
    assert len(soll) >= 20
    fehlend, zusaetzlich = set(soll) - set(ist), set(ist) - set(soll)
    assert len(fehlend) + len(zusaetzlich) <= 1, (sorted(fehlend), sorted(zusaetzlich))     # Rundung float32 gegen float64 an der Schwelle
    for key in set(soll) & set(ist):
        assert ist[key]["aus"] == soll[key]["aus"][:16]
        assert abs(ist[key]["netto_bp"] - float(soll[key]["n85"])) < 0.06
