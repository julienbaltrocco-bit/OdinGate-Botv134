"""Auswertung der Fabrik: Zählung, Durchsatz, Tabellen für Bericht und Dashboard; sichert die Ergebnisse in kompakter Form im Repository.

  .venv/bin/python -I forschung/fabrik/bericht.py
Schreibt nach forschung/fabrik/ergebnisse/: kandidaten.parquet (alle gerechneten Kandidaten), zaehlung.json, auswahl.json.
"""
import json
import os
import sqlite3
import sys
import time
from pathlib import Path

import pandas as pd

F = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(F))
from fabrik import daten as D, lauf as L

ERG = F / "fabrik/ergebnisse"
STUFEN = {"ungültig": "zu wenige Trades", "verworfen_1": "Stufe 1: kein Brutto-Vorteil", "verworfen_2": "Stufe 2: Kosten", "stufe2": "Stufe 2 bestanden",
          "verworfen_3": "Stufe 3: nicht robust", "stufe3": "Stufe 3 bestanden (in einer Gruppe vertreten)", "final": "Finalist", "verworfen_4": "Schlussprüfung nicht bestanden",
          "validiert": "validiert"}


def haupt():
    con = sqlite3.connect(f"file:{L.DB}?mode=ro", uri=True)
    k = pd.read_sql("SELECT * FROM kandidaten", con)
    laeufe = pd.read_sql("SELECT * FROM laeufe", con)
    ERG.mkdir(parents=True, exist_ok=True)
    spalten = [c for c in k.columns if c not in ("zeile",)]
    kompakt = k[spalten].copy()
    for c in kompakt.columns:                                      # kompakt speichern: Kategorien und gerundete 32-Bit-Zahlen
        if kompakt[c].dtype == object and c != "id":
            kompakt[c] = kompakt[c].astype("category")
        elif kompakt[c].dtype == "float64":
            kompakt[c] = kompakt[c].round(2).astype("float32")
        elif kompakt[c].dtype == "int64":
            kompakt[c] = kompakt[c].astype("int32")
    kompakt.to_parquet(ERG / "kandidaten.parquet", compression="zstd", compression_level=19, index=False)
    gueltig = k[k["n_t"] >= 200]
    nach_s2 = k[k["status"].isin(["stufe2", "verworfen_3", "stufe3", "final", "verworfen_4", "validiert"])]
    z = {"stand": time.strftime("%Y-%m-%d %H:%M UTC", time.gmtime()),
         "erzeugt": int(len(k)), "eindeutig": int(k["id"].nunique()), "berechnet": int(len(k)), "gueltig_mind_200_trades": int(len(gueltig)),
         "nach_status": {STUFEN.get(s, s): int(n) for s, n in k["status"].value_counts().items()},
         "stufe1_bestanden": int((~k["status"].isin(["ungültig", "verworfen_1"])).sum()), "stufe2_bestanden": int(len(nach_s2)),
         "stufe3_bestanden": int(k["status"].isin(["stufe3", "final", "verworfen_4", "validiert"]).sum()),
         "finalisten": int(k["status"].isin(["final", "verworfen_4", "validiert"]).sum()), "validiert": int((k["status"] == "validiert").sum()),
         "training_netto_mit_rebate_positiv": int((gueltig["n85_t"] > 0).sum()), "training_netto_ohne_rebate_positiv": int((gueltig["n0_t"] > 0).sum()),
         "training_und_v1_mit_rebate_positiv": int(((gueltig["n85_t"] > 0) & (gueltig["n85_v"] > 0)).sum()),
         "laeufe": laeufe.to_dict("records"),
         "kandidaten_je_minute": round(float(laeufe["kandidaten"].sum() / laeufe["sekunden"].sum() * 60), 0) if len(laeufe) else None,
         "rueckrechnungen_je_sekunde": round(float(laeufe["kandidaten"].sum() / 3 * 10 / laeufe["sekunden"].sum()), 0) if len(laeufe) else None,
         "rechenkerne": os.cpu_count(), "zeitraeume": {"training": "15.08.2021–30.06.2023 (Tiefe-Signale: 2023)", "auswahlpruefung": "01.07.2023–30.06.2024 (Tiefe: 01–06/2024)",
                                                    "schlusspruefung": "01.07.2024–31.03.2025", "tresor": "ab 01.04.2025, nicht geladen"},
         "je_familie": {f: {"gueltig": int(len(g)), "stufe1": int((~g["status"].isin(["verworfen_1"])).sum()),
                            "stufe2": int(g["status"].isin(["stufe2", "verworfen_3", "stufe3", "final", "verworfen_4", "validiert"]).sum()),
                            "stufe3": int(g["status"].isin(["stufe3", "final", "verworfen_4", "validiert"]).sum()), "validiert": int((g["status"] == "validiert").sum())}
                        for f, g in gueltig.groupby("familie")},
         "gruende": {g: int(n) for g, n in k.loc[k["status"].str.startswith("verworfen"), "grund"].str.replace(r"V2 netto.*", "Schlussprüfung", regex=True).value_counts().head(12).items()}}
    (ERG / "zaehlung.json").write_text(json.dumps(z, ensure_ascii=False, indent=1))
    # Auswahl für Bericht und Übersicht: Kandidaten ab Stufe 3, mit dem Ergebnis der Schlussprüfung (falls schon geöffnet)
    auswahl = k[k["status"].isin(["stufe3", "final", "verworfen_4", "validiert"])].copy()
    sp = json.loads((ERG / "schlusspruefung.json").read_text()) if (ERG / "schlusspruefung.json").exists() else None
    if sp:
        v2 = pd.DataFrame(sp["ergebnisse"])[["id", "gen", "n_v2", "n85_v2", "n0_v2", "n85_2x_v2", "t85_v2", "p_v2", "sharpe_v2", "ertrag_jahr_pct"]]
        auswahl = auswahl.merge(v2, on=["id", "gen"], how="left")
        z["schlusspruefung"] = {x: sp[x] for x in sp if x != "ergebnisse"}
    st = json.loads((ERG / "statistik.json").read_text()) if (ERG / "statistik.json").exists() else None
    if st:
        z["statistik"] = st["gruppen"]
    rang = {"validiert": 0, "verworfen_4": 1, "final": 1, "stufe3": 2}
    auswahl["rang"] = auswahl["status"].map(rang)
    auswahl = auswahl.sort_values(["rang", "p_v2" if sp else "sharpe_v", "sharpe_v"], ascending=[True, True, False])
    feld = [c for c in ["id", "gen", "signal", "familie", "th", "r", "f", "k", "x", "m", "best", "n_t", "n85_t", "n0_t", "t85_t", "n_v", "n85_v", "t85_v", "dauer_min", "status",
                        "n_v2", "n85_v2", "n0_v2", "t85_v2", "p_v2", "sharpe_v2", "ertrag_jahr_pct"] if c in auswahl.columns]
    (ERG / "auswahl.json").write_text(json.dumps({"stand": z["stand"], "gesamt": int(len(auswahl)), "kandidaten": json.loads(auswahl[feld].head(400).to_json(orient="records"))}, ensure_ascii=False))
    (ERG / "zaehlung.json").write_text(json.dumps(z, ensure_ascii=False, indent=1))
    print(json.dumps({x: z[x] for x in ("erzeugt", "gueltig_mind_200_trades", "stufe1_bestanden", "stufe2_bestanden", "stufe3_bestanden", "finalisten", "validiert",
                                         "training_netto_mit_rebate_positiv", "training_netto_ohne_rebate_positiv", "kandidaten_je_minute", "rueckrechnungen_je_sekunde")}, ensure_ascii=False))
    print("kandidaten.parquet:", (ERG / "kandidaten.parquet").stat().st_size // 1024, "KB")


if __name__ == "__main__":
    haupt()
