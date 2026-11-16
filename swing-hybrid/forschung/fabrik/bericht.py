"""Auswertung der Fabrik: Zählung, Durchsatz, Tabellen für Bericht und Dashboard; sichert die Ergebnisse in kompakter Form im Repository.

  .venv/bin/python -I forschung/fabrik/bericht.py
Schreibt nach forschung/fabrik/ergebnisse/: kandidaten_<Generation>.parquet (je neue Generation eine kleine Datei), zaehlung.json, auswahl.json.

Das Archiv liegt in Teilen: kandidaten.parquet enthält die Generationen 1 und 2 und ist eingefroren (Prüfsumme in
archiv_basis.json); es wird nie neu geschrieben. Jede spätere Generation steht in einer eigenen Datei. Die Zählung
entsteht immer aus Archiv plus lokaler Datenbank, also auch in einer frischen Sitzung mit leerer Datenbank vollständig.
"""
import hashlib
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


BASIS = ERG / "kandidaten.parquet"
BASIS_INFO = ERG / "archiv_basis.json"


def kompakt(k: pd.DataFrame) -> pd.DataFrame:
    """Kompakte Form für das Archiv: Kategorien und auf zwei Stellen gerundete 32-Bit-Zahlen, ohne die Zeilennummer der Tagesreihen."""
    k = k[[c for c in k.columns if c != "zeile"]].copy()
    for c in k.columns:
        if k[c].dtype == object and c != "id":
            k[c] = k[c].astype("category")
        elif k[c].dtype == "float64":
            k[c] = k[c].round(2).astype("float32")
        elif k[c].dtype == "int64":
            k[c] = k[c].astype("int32")
    return k


def _lesbar(k: pd.DataFrame) -> pd.DataFrame:
    for c in k.columns:
        if isinstance(k[c].dtype, pd.CategoricalDtype):
            k[c] = k[c].astype(object)
    return k


def archiv_teile() -> list:
    return [BASIS] + sorted(ERG.glob("kandidaten_gen*.parquet"))


def basis_pruefen() -> dict:
    """Das eingefrorene Archiv der Generationen 1 und 2 muss unverändert sein; sonst wird nichts geschrieben."""
    info = json.loads(BASIS_INFO.read_text())
    if hashlib.sha256(BASIS.read_bytes()).hexdigest() != info["sha256"]:
        raise SystemExit("kandidaten.parquet weicht vom eingefrorenen Stand ab (archiv_basis.json). Nichts geschrieben. "
                         "Wiederherstellen: git checkout -- forschung/fabrik/ergebnisse/kandidaten.parquet")
    return info


def haupt():
    info = basis_pruefen()
    con = sqlite3.connect(f"file:{L.DB}?mode=ro", uri=True) if L.DB.exists() else None
    tabellen = {r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type = 'table'")} if con else set()
    k_db = pd.read_sql("SELECT * FROM kandidaten", con) if "kandidaten" in tabellen else pd.DataFrame(columns=["gen"])
    laeufe = pd.read_sql("SELECT * FROM laeufe", con) if "laeufe" in tabellen else pd.DataFrame(columns=["gen", "begonnen", "kandidaten", "sekunden"])
    ERG.mkdir(parents=True, exist_ok=True)
    for gen, g in k_db.groupby("gen"):                             # jede neue Generation in ihre eigene kleine Datei; das große Archiv bleibt unberührt
        if gen not in info["generationen"]:
            kompakt(g).to_parquet(ERG / f"kandidaten_{gen}.parquet", compression="zstd", compression_level=19, index=False)
    k = pd.concat([_lesbar(pd.read_parquet(t)) for t in archiv_teile()], ignore_index=True)       # Archiv = Gedächtnis; überall dieselbe Genauigkeit
    assert not k.duplicated(["id", "gen"]).any(), "doppelte Kandidaten im Archiv"
    neu = k[~k["gen"].isin(info["generationen"])]
    neu_g = neu[neu["n_t"] >= 200]
    alt_z = json.loads((ERG / "zaehlung.json").read_text()) if (ERG / "zaehlung.json").exists() else {}
    laeufe = pd.concat([pd.DataFrame(alt_z.get("laeufe", [])), laeufe], ignore_index=True)        # Läufe früherer Sitzungen bleiben in der Liste
    laeufe = laeufe.drop_duplicates(["gen", "begonnen"], keep="last").sort_values("begonnen").reset_index(drop=True)
    gueltig = k[k["n_t"] >= 200]
    nach_s2 = k[k["status"].isin(["stufe2", "verworfen_3", "stufe3", "final", "verworfen_4", "validiert"])]
    z = {"stand": time.strftime("%Y-%m-%d %H:%M UTC", time.gmtime()),
         "erzeugt": int(len(k)), "eindeutig": int(k["id"].nunique()), "berechnet": int(len(k)), "gueltig_mind_200_trades": int(len(gueltig)),
         "nach_status": {STUFEN.get(s, s): int(n) for s, n in k["status"].value_counts().items()},
         "stufe1_bestanden": int((~k["status"].isin(["ungültig", "verworfen_1"])).sum()), "stufe2_bestanden": int(len(nach_s2)),
         "stufe3_bestanden": int(k["status"].isin(["stufe3", "final", "verworfen_4", "validiert"]).sum()),
         "finalisten": int(k["status"].isin(["final", "verworfen_4", "validiert"]).sum()), "validiert": int((k["status"] == "validiert").sum()),
         # Generation 1 und 2: in voller Genauigkeit gezählt und in archiv_basis.json festgehalten; spätere Generationen aus ihren Archivdateien
         "training_netto_mit_rebate_positiv": info["training_netto_mit_rebate_positiv"] + int((neu_g["n85_t"] > 0).sum()),
         "training_netto_ohne_rebate_positiv": info["training_netto_ohne_rebate_positiv"] + int((neu_g["n0_t"] > 0).sum()),
         "training_und_v1_mit_rebate_positiv": info["training_und_v1_mit_rebate_positiv"] + int(((neu_g["n85_t"] > 0) & (neu_g["n85_v"] > 0)).sum()),
         "archiv": [t.name for t in archiv_teile()],
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
        z["einordnung"] = (f"Schlussprüfung auf bis dahin ungelesenen Daten: Von {sp['finalisten_gesamt']:,} Finalisten haben {sp['p_unter_5pct']} einen p-Wert unter 5 %; "
                           f"rein zufällig wären {sp['zufallserwartung_p_unter_5pct']:.0f} zu erwarten. Nach Korrektur für die vielen Versuche bestehen {sp['validiert']}. "
                           + ("Kein Kandidat ist validiert; es wurde kein neuer Papier-Test gestartet." if sp["validiert"] == 0 else f"{sp['validiert']} Kandidaten sind validiert.")).replace(",", ".")
        ze = ERG / "schlusspruefung_einfache_slippage.json"
        if ze.exists():                                             # reine Zusatzangabe, ändert keinen Status
            e = json.loads(ze.read_text())
            z["schlusspruefung"]["zusatz_einfache_slippage"] = {x: e[x] for x in e if x != "ergebnisse" and not isinstance(e[x], list)}
            z["einordnung"] += (f" Zusatzangabe: Mit der milderen Kostenannahme (ruhiger Markt) wären es {e['p_unter_5pct']} statt {sp['p_unter_5pct']}, und {e['bh_bestanden']} "
                                f"Kandidat bestünde die übliche Korrektur, {e['by_bestanden']} die strenge. Das Ergebnis hängt also teilweise an den Kosten in bewegtem Markt.")
    st = json.loads((ERG / "statistik.json").read_text()) if (ERG / "statistik.json").exists() else None
    if st:
        z["statistik"] = st["gruppen"]
    rang = {"validiert": 0, "verworfen_4": 1, "final": 1, "stufe3": 2}
    auswahl["rang"] = auswahl["status"].map(rang)
    auswahl = auswahl.sort_values(["rang", "p_v2" if sp else "sharpe_v", "sharpe_v"], ascending=[True, True, False])
    feld = [c for c in ["id", "gen", "signal", "familie", "th", "r", "f", "k", "x", "m", "best", "n_t", "n85_t", "n0_t", "t85_t", "n_v", "n85_v", "t85_v", "dauer_min", "status",
                        "n_v2", "n85_v2", "n0_v2", "t85_v2", "p_v2", "sharpe_v2", "ertrag_jahr_pct"] if c in auswahl.columns]
    (ERG / "auswahl.json").write_text(json.dumps({"stand": z["stand"], "gesamt": int(len(auswahl)), "kandidaten": json.loads(auswahl[feld].head(300).to_json(orient="records"))}, ensure_ascii=False))
    (ERG / "zaehlung.json").write_text(json.dumps(z, ensure_ascii=False, indent=1))
    print(json.dumps({x: z[x] for x in ("erzeugt", "gueltig_mind_200_trades", "stufe1_bestanden", "stufe2_bestanden", "stufe3_bestanden", "finalisten", "validiert",
                                         "training_netto_mit_rebate_positiv", "training_netto_ohne_rebate_positiv", "kandidaten_je_minute", "rueckrechnungen_je_sekunde")}, ensure_ascii=False))
    print("Archiv:", ", ".join(f"{t.name} {t.stat().st_size // 1024} KB" for t in archiv_teile()))


if __name__ == "__main__":
    haupt()
