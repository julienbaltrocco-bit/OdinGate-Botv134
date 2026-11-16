"""Parität des Papier-Runners für Fabrik-Kandidaten: auf einem historischen Fenster (10. bis 20.06.2024, Auswahlprüfung)
muss der Runner aus den Archivdateien dieselben Trades bilden wie die Rückrechnung auf dem großen Datenspeicher.

  .venv/bin/python -I forschung/fabrik/paritaet_papier.py <Kennung> [<Kennung> ...]      Rückgabe 0 = gleich
"""
import datetime as dt
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

F = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(F)); sys.path.insert(0, str(F.parent))
from fabrik import daten as D, freigabe as FG, lauf as L, trichter as T
from forschung.papier import runner as R

START, HEUTE = "2024-06-10", dt.date(2024, 6, 21)
ORIGINAL = (D.SPEICHER, D.RASTER, D.N, L.I_ENDE)


def pruefe(kennung: str, code_ordner=None) -> bool:
    D.SPEICHER, D.RASTER, D.N, L.I_ENDE = ORIGINAL                # der Papier-Lauf stellt diese Größen auf sein Datenfenster um
    L._g.clear(); L._init()
    con = T.db()
    z = con.execute("SELECT * FROM kandidaten WHERE id = ?", (kennung,)).fetchone()
    i0, i1 = L.idx(START), L.idx("2024-06-21")
    ref, M = FG.trades_voll(z, i0 - 1, i1)
    ref = ref[(ref["ein"] >= START) & (ref["offen"] == 0)]
    namen = [z["signal"]] + ([json.loads(z["best"])[0]] if z["best"] else [])
    slip = np.asarray(L._g["slip_bp"])
    cfg = {"id": "PARI", "name": "Parität", "version": "0", "strategie": "fabrik", "art": "Paritätstest", "coins": [D.COINS[j] for j in M], "coin_index": M,
           "daten": sorted(a for a, pr in FG.ARTEN.items() if any(n.startswith(pr) for n in namen)), "regel": "", "validierung": "", "eingefroren": "",
           "kandidat": {"signal": z["signal"], "th": z["th"], "r": z["r"], "f": z["f"], "k": z["k"], "ausstieg": list(T.ausstieg_aus(z)), "best": json.loads(z["best"]) if z["best"] else None},
           "start": f"{START}T00:00:00Z", "vorlauf_tage": 38, "kapital_usd": 5000, "hebel": 1.0, "anzahl_letzte_trades": 5000,
           "kosten": {"taker_bp": 8.0, "rebate": 0.85, "slippage_bp_je_order": {D.COINS[j]: float(slip[j]) for j in M}, "slippage_anteil_spanne": L.SPANNEN_ANTEIL}, "risiko": {"mmr": 0.01, "abbruch_kontostand": 0.0}}
    sys.path.insert(0, str(code_ordner or F / 'fabrik'))
    import papier_fabrik as PF
    cfg["strategie_sha256"] = PF.pruefsumme(cfg)
    basis = {"id": "PARI", "name": "", "version": "", "art": "", "lauf_id": "p", "letzter_lauf": "", "aktualisiert": "", "takt_stunden": 24, "start": cfg["start"],
             "kapital": 5000, "hebel": 1.0, "maerkte": cfg["coins"], "regel": "", "validierung": "", "eingefroren": ""}
    d = PF.lauf(None, cfg, {"status": "laufend"}, basis, HEUTE, R.HIER / ".cache_paritaet", False, R)
    ist = {(t["coin"], t["ein"]): t for t in d["letzte_trades"]}
    soll = {(r.coin, str(r.ein)[:16]): r for r in ref.itertuples()}
    fehl, zus = set(soll) - set(ist), set(ist) - set(soll)
    kosten = {c: 2 * cfg["kosten"]["slippage_bp_je_order"][c] + 2.4 for c in cfg["coins"]}
    abw = max((abs(ist[k]["netto_bp"] - (soll[k].roh - 2.4)) for k in set(soll) & set(ist)), default=0.0)
    ok = len(fehl) + len(zus) <= max(1, len(soll) // 50) and abw < 0.2 and len(soll) > 0
    print(f"{kennung} {z['signal']} {z['m']} {z['x']}: Rückrechnung {len(soll)} Trades, Runner {len(ist)}, fehlend {len(fehl)}, zusätzlich {len(zus)}, größte Abweichung {abw:.3f} bp ->", "GLEICH" if ok else "ABWEICHUNG")
    if not ok:
        print("   fehlend:", sorted(fehl)[:5], "zusätzlich:", sorted(zus)[:5])
    return ok


if __name__ == "__main__":
    sys.exit(0 if all([pruefe(k) for k in sys.argv[1:]]) else 1)
