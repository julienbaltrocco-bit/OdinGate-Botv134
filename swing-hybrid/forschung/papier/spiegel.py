"""Bestehende Papier-Tests (Test 1, Test 2) nur lesend in die zentrale Übersicht spiegeln.

Liest den zuletzt gesicherten Stand aus dem Zweig des Bots per `git show` und schreibt forschung/papier/ausgabe/T1.json
und T2.json. An den Tests, ihrem Code und ihren Daten wird nichts verändert.
"""
import calendar
import json
import subprocess
import time
from pathlib import Path

HIER = Path(__file__).resolve().parent
ZWEIG = "origin/claude/intelligent-sagan-2cviug"
TESTS = {"T1": ("lauf", "Test 1 – 14-Tage-Trend, nur Umkehrsignal", "Schluss der letzten vollen Stunde gegen den Schluss vor 336 Stunden; Ausstieg nur beim Umkehrsignal."),
         "T2": ("lauf_tpsl", "Test 2 – 14-Tage-Trend mit Stop 5 % / Ziel 15 %", "Wie Test 1, zusätzlich Stop 5 % und Gewinnziel 15 % je Position, geprüft bei jedem Bot-Lauf.")}


def spiegeln():
    subprocess.run(["git", "fetch", "-q", "origin", ZWEIG.split("/", 1)[1]], check=False, timeout=120)
    (HIER / "ausgabe").mkdir(exist_ok=True)
    for tid, (ordner, name, regel) in TESTS.items():
        try:
            roh = subprocess.run(["git", "show", f"{ZWEIG}:swing-hybrid/vorwaertstest/{ordner}/dashboard.json"], capture_output=True, text=True, check=True, timeout=60).stdout
            d = json.loads(roh)
            k = d["kennzahlen"][0]
            alter_h = (time.time() - calendar.timegm(time.strptime(d["geschrieben"], "%Y-%m-%dT%H:%M:%SZ"))) / 3600
            v = d["verlauf"][:: max(1, len(d["verlauf"]) // 200)]
            doc = {"id": tid, "name": name, "version": "1.0", "art": "Papier-Bot gegen das Yubit-Orderbuch (bestehender Test, hier nur gespiegelt)",
                   "status": "läuft" if alter_h < 3 else "Bot steht", "letzter_lauf": k["letzter_lauf"] + " UTC", "aktualisiert": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                   "takt_stunden": 24, "start": k["start"] + " UTC", "kapital": k["kapital"], "hebel": k["hebel"], "maerkte": sorted({p["coin"] for p in d["positionen"]}),
                   "regel": regel, "validierung": "Vorwärtstest ohne vorab festgelegte Auswertung; Hebel 3 wurde nie zurückgerechnet (Audit).",
                   "laufzeit_tage": k["tage"], "kontostand": round(k["kapital"] + k["mit_rebate_usd"], 2), "rendite_mit_rebate_pct": round(k["mit_rebate_pct"], 3),
                   "rendite_ohne_rebate_pct": round(k["ohne_rebate_pct"], 3), "trades": k["orders"], "gebuehr_usd": k["gebuehr_usd"], "rebate_usd_angenommen": k["rebate_usd"],
                   "funding_usd": k["funding_usd"], "slippage_bp_je_order": k.get("slippage_orders_bp"), "volumen_usd": k["volumen_usd"], "rueckgang_max_pct": round(k["einbruch_pct"], 2),
                   "margin_pct": k.get("margin_pct"),
                   "offene_positionen": [{"coin": p["coin"], "richtung": p["richtung"], "seit": p["seit"], "einstieg": p["einstieg"], "ergebnis_usd": p["ergebnis"]} for p in d["positionen"] if p.get("menge")],
                   "verlauf": [{"tag": x["zeit"][:16].replace("T", " "), "kontostand": round(k["kapital"] * (1 + x["mit_rebate"] / 100), 2)} for x in v],
                   "datenluecken": [], "fehler": [] if alter_h < 3 else [f"Letzter gesicherter Bot-Lauf vor {alter_h:.0f} Stunden."]}
        except Exception as e:
            doc = {"id": tid, "name": name, "status": "Fehler", "fehler": [f"Spiegeln gescheitert: {type(e).__name__}: {e}"], "aktualisiert": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "takt_stunden": 24}
        (HIER / "ausgabe" / f"{tid}.json").write_text(json.dumps(doc, ensure_ascii=False, indent=1))
        print(tid, doc["status"], doc.get("kontostand"), doc.get("letzter_lauf"))


if __name__ == "__main__":
    spiegeln()
