"""Zentrales Testregister bauen: forschung/register/register.json aus den Ergebnisdateien und den Stammdaten unten.

Ein neuer Test wird registriert, indem unten ein Eintrag ergänzt (Backtests, Kandidaten) oder ein Ordner unter
forschung/papier/<id>/ mit konfiguration.json und stand.json angelegt wird (freigegebene Vorwärtstests). Die
Dashboard-Seite liest nur dieses Register; für einen neuen Test muss keine Oberfläche programmiert werden.

Kategorien (nie vermischt): backtest · kandidat · vorbereitet · laufend · abgeschlossen
Aufruf: python -I forschung/register/bauen.py
"""
import json
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ERG = ROOT / "forschung/ergebnisse"
KOSTEN = "Taker 0,08 % je Order, Rebate 85 % angenommen (unbestätigt); Slippage 2 x gemessene halbe Yubit-Spanne"


def lade(name):
    return json.loads((ERG / f"{name}.json").read_text())


def stufe0(exp, schluessel, **meta):
    k = lade(exp)["ergebnis"][schluessel]["gesamt"]
    return {"kategorie": "backtest", "einstufung": "A", "status": "verworfen", "validierung": "Stufe 0 (Entwicklung) nicht bestanden",
            "vertrauen": "hoch (negativer Befund)", "gebuehren": KOSTEN, "ergebnisdateien": [f"forschung/ergebnisse/{exp}.json"],
            "kennzahlen": {"zeitraum": "Entwicklung", "trades_je_tag": k["trades_je_tag"], "haltedauer_min": k["haltedauer_min"], "roh_bp": k["roh"],
                           "n85_bp": k["n85"], "n0_bp": k["n0"], "t_n85": k["t_n85"], "gewinnquote": k["gewinnquote"], "profit_factor": k["profit_factor"]}, **meta}


def kandidat(exp, name, zeitraum, **meta):
    d = lade(exp)
    blk = d[f"{name} {zeitraum}"] if name else None
    k = blk["trades"] if blk else d[zeitraum]
    kt = blk["konto_hebel1"] if blk else d[f"konto_{zeitraum}_n85"]
    k0 = blk["konto_n0"] if blk else d[f"konto_{zeitraum}_n0"]
    return {"zeitraum": zeitraum, "trades_je_tag": k["trades_je_tag"], "haltedauer_min": k["haltedauer_min"], "roh_bp": k["roh"], "n85_bp": k["n85"],
            "n50_bp": k["n50"], "n0_bp": k["n0"], "t_n85": k["t_n85"], "gewinnquote": k["gewinnquote"], "profit_factor": k["profit_factor"],
            "ertrag_jahr_pct_hebel1": kt["ertrag_jahr_pct"], "ertrag_jahr_ohne_rebate_pct": k0["ertrag_jahr_pct"], "sharpe": kt["sharpe"],
            "rueckgang_pct": kt["rueckgang_pct_startkapital"], **meta}


def papier(ordner, **meta):
    k = json.loads((ROOT / "vorwaertstest" / ordner / "dashboard.json").read_text())["kennzahlen"][0]
    return {"kategorie": "laufend", "status": "läuft", "einstufung": "–", "startkapital": k["kapital"], "hebel": k["hebel"], "beginn": k["start"] + " UTC",
            "gebuehren": KOSTEN, "ergebnisdateien": [f"swing-hybrid/vorwaertstest/{ordner}/"],
            "kennzahlen": {"stand": k["letzter_lauf"] + " UTC", "kapital": round(k["kapital"] + k["mit_rebate_usd"], 2), "mit_rebate_pct": round(k["mit_rebate_pct"], 2),
                           "ohne_rebate_pct": round(k["ohne_rebate_pct"], 2), "orders": k["orders"], "volumen_usd": k["volumen_usd"], "gebuehr_usd": k["gebuehr_usd"],
                           "rebate_usd": k["rebate_usd"], "funding_usd": k["funding_usd"], "einbruch_pct": round(k["einbruch_pct"], 2), "margin_pct": k["margin_pct"],
                           "laeufe": k["laeufe"]}, **meta}


e8, e9, e13, e11 = lade("e08_vollpruefung"), lade("e09_frische_coins"), lade("e13_version11"), lade("e11_kombination")["ergebnis"]
A = "BTC, ETH, SOL, XRP, DOT, DOGE, ADA, LINK, AVAX, LTC"
eintraege = [
    papier("lauf", id="T1", name="Test 1 – 14-Tage-Trend, nur Umkehrsignal", version="1.0", familie="Trend", richtung="Long und Short", maerkte=A,
           daten="Yubit-Stundenkerzen und Orderbuch (live)", algorithmus="Schluss der letzten vollen Stunde gegen den Schluss vor 336 Stunden; Ausstieg nur beim Umkehrsignal",
           risiko="kein Stop, Tageslimit faktisch aus (Audit: Hebel 3 nie gerechnet)", validierung="Vorwärtstest läuft, ohne vorab festgelegte Auswertung (Audit QD-08)",
           vertrauen="offen"),
    papier("lauf_tpsl", id="T2", name="Test 2 – 14-Tage-Trend mit Stop 5 % / Ziel 15 %", version="1.0", familie="Trend", richtung="Long und Short", maerkte=A,
           daten="Yubit-Stundenkerzen und Orderbuch (live)", algorithmus="wie Test 1, zusätzlich Stop 5 % und Gewinnziel 15 % je Position, geprüft bei jedem Bot-Lauf",
           risiko="Stop nur lokal beim Bot-Lauf, kein Börsen-Stop", validierung="Vorwärtstest läuft; misst nicht die gerechnete Variante (Audit ENG-03)", vertrauen="offen"),
    {"id": "B0", "name": "14-Tage-Trend (Vergleichsbasis)", "version": "Kandidat der Runden 3–24", "familie": "Trend", "kategorie": "backtest", "einstufung": "B",
     "status": "Vergleichsbasis", "richtung": "Long und Short", "maerkte": A, "daten": "Binance-Futures 5-Minuten-Kerzen, Funding", "gebuehren": KOSTEN,
     "algorithmus": "Schluss gegen Schluss vor 336 Stunden, stündlich, zehn Coins gleich groß", "validierung": "statistisch nicht gesichert (Audit QD-01, QR-03)",
     "vertrauen": "gering bis mittel", "ergebnisdateien": ["swing-hybrid/reports/suche_runde24.json", "forschung/ergebnisse/e11_kombination.json"],
     "kennzahlen": {"zeitraum": "01/2023–03/2025 (gleicher Zeitraum wie die Orderbuch-Regel)", "trades_je_tag": 5.7, "haltedauer_min": 2520,
                    "ertrag_jahr_pct_hebel1": e11["mit 85 % Rebate"]["trend"]["ertrag_jahr_pct"], "ertrag_jahr_ohne_rebate_pct": e11["ohne Rebate"]["trend"]["ertrag_jahr_pct"],
                    "sharpe": e11["mit 85 % Rebate"]["trend"]["sharpe"], "rueckgang_pct": e11["mit 85 % Rebate"]["trend"]["rueckgang_pct_startkapital"],
                    "hinweis": "Entwicklung 08/2021–03/2025: +59 % pro Jahr, Sharpe 0,95; 04/2025–10/2026: +16,5 %, Sharpe 0,34, ohne Rebate −12,5 %"}},
    {"id": "OS-1.1", "name": "Orderbuch-Stütze", "version": "1.1", "familie": "Orderbuch / Liquidität", "kategorie": "laufend", "einstufung": "D", "status": "Papier-Test (Schattentest) seit 16.11.2026",
     "richtung": "Long und Short", "maerkte": "BTC, ETH, SOL", "daten": "Binance-Orderbuch-Tiefe bis 5 % (bookDepth), 5-Minuten-Kerzen, Funding", "gebuehren": KOSTEN,
     "hypothese": "Ein ungewöhnliches Übergewicht der Kauf- oder Verkaufsaufträge im tiefen Orderbuch zeigt, wohin sich der Kurs in den nächsten ein bis zwei Stunden bewegt.",
     "algorithmus": "z = Abweichung des Auftrags-Übergewichts (bis 5 % um den Kurs, 5-Minuten-Mittel) vom eigenen 24-Stunden-Mittel. Einstieg bei z ≥ 3 (Long) bzw. ≤ −3 (Short); Ausstieg, sobald z unter 1 fällt, spätestens nach 240 Minuten.",
     "parameter": e13["parameter"], "risiko": "eine Position je Coin, je Coin ein Drittel von Kapital x Hebel, kein Stop; Liquidationsmodell: gemeinsame Margin, Erhaltungsmargin 1 % (Annahme)",
     "hebel": "1 bis 3 geprüft ohne Liquidation; bei Hebel 5 tiefster Kontostand 31 %", "validierung": "Entwicklung und Validierung (einmalig) formal bestanden; Validierung allein nicht gesichert (t 1,1); 04/2025–10/2026 ungeöffnet",
     "vertrauen": "gering bis mittel; nur mit Rebate positiv", "ergebnisdateien": ["forschung/ergebnisse/e13_version11.json", "forschung/ergebnisse/e13_version11_trades.csv"],
     "kennzahlen": kandidat("e13_version11", "Version 1.1", "V", liquidationen=0, tiefster_kontostand_hebel3=e13["starttage_V_hebel3"]["tiefster_kontostand"]),
     "kennzahlen_entwicklung": kandidat("e13_version11", "Version 1.1", "E")},
    {"id": "OS-1.0", "name": "Orderbuch-Stütze", "version": "1.0", "familie": "Orderbuch / Liquidität", "kategorie": "backtest", "einstufung": "D", "status": "durch 1.1 ersetzt",
     "richtung": "Long und Short", "maerkte": "BTC, ETH, SOL", "daten": "Binance-Orderbuch-Tiefe bis 5 %, 5-Minuten-Kerzen", "gebuehren": KOSTEN,
     "algorithmus": "Einstieg wie 1.1, Ausstieg fest nach 60 Minuten.", "parameter": e8["parameter"], "validierung": "Entwicklung und Validierung formal bestanden; auf sieben frischen Coins nach Kosten negativ",
     "vertrauen": "gering bis mittel; nur mit Rebate positiv", "ergebnisdateien": ["forschung/ergebnisse/e08_vollpruefung.json", "forschung/ergebnisse/e09_frische_coins.json"],
     "kennzahlen": kandidat("e08_vollpruefung", None, "V", liquidationen=0), "kennzahlen_entwicklung": kandidat("e08_vollpruefung", None, "E")},
    stufe0("e01_orderbuch_tiefe", "haupt_1pct_z2_60m", id="E01", name="Orderbuch-Tiefe nahe am Kurs (1 %)", version="0.1", familie="Orderbuch / Liquidität", richtung="Long und Short",
           maerkte="BTC, ETH, SOL", daten="Binance bookDepth", algorithmus="Übergewicht bis 1 % um den Kurs, z ≥ 2, 60 Minuten"),
    stufe0("e02_aufschlag", "haupt_z2.5_60m", id="E02", name="Aufschlag des Kontrakts (Gegenposition)", version="0.1", familie="Mean Reversion", richtung="Long und Short", maerkte=A,
           daten="Binance premiumIndexKlines", algorithmus="Gegenposition bei Aufschlag ≥ 2,5 Standardabweichungen, bis 60 Minuten"),
    stufe0("e03_funding_termin", "a_vor_haupt_0.03", id="E03", name="Funding-Termin, 60 Minuten davor", version="0.1", familie="Funding", richtung="Long und Short", maerkte=A,
           daten="Funding, Aufschlag", algorithmus="Position, die das Funding erhält, 60 Minuten vor bis 5 Minuten nach dem Termin"),
    stufe0("e04_btc_nachlauf", "haupt_3s_15m", id="E04", name="Nachlauf der Altcoins hinter BTC", version="0.1", familie="Intraday Momentum / Cross-Market", richtung="Long und Short",
           maerkte="neun Altcoins", daten="1-Minuten-Kerzen", algorithmus="starke BTC-Bewegung (3 σ in 5 Minuten), Altcoin noch nicht gefolgt, 15 Minuten halten"),
    stufe0("e05_zwangsliquidation", "haupt_4h", id="E05", name="Erholung nach Zwangsliquidationen", version="0.1", familie="Positionierung", richtung="Long und Short", maerkte=A,
           daten="Stundenkerzen, Open Interest", algorithmus="Gegenposition nach 2-σ-Stundenbewegung mit fallendem Open Interest, 4 Stunden"),
    stufe0("e06_funding_kurz", "haupt_0.03", id="E06", name="Funding-Abgriff, 10 Minuten", version="0.2", familie="Funding", richtung="Long und Short", maerkte="acht günstige Coins",
           daten="Funding, Aufschlag", algorithmus="5 Minuten vor bis 5 Minuten nach dem Funding-Termin"),
]
# Papier-Tests aus der Strategie-Fabrik: jeder Ordner papier/F-*/ erscheint automatisch
for pfad in sorted((ROOT / "forschung/papier").glob("*/konfiguration.json")):
    c = json.loads(pfad.read_text())
    if c.get("strategie") != "fabrik":
        continue
    r = c["rueckrechnung"]
    beob = bool(c.get("beobachtung"))
    wartet = json.loads((pfad.parent / "steuerung.json").read_text())["status"] == "pausiert"
    eintraege.insert(3, {"id": c["id"], "name": c["name"], "version": c["version"], "familie": "Strategie-Fabrik", "kategorie": "vorbereitet" if wartet else "laufend",
                         "einstufung": "B" if beob else "D",
                         "status": (f"Beobachtungstest vorbereitet, nicht validiert, wartet auf Freigabe" if beob and wartet else
                                    f"{'Beobachtungstest, nicht validiert' if beob else 'Papier-Test'} (Schattentest) {'pausiert' if wartet else 'seit ' + c['start'][:10]}"), "richtung": "Long und Short", "maerkte": ", ".join(c["coins"]),
                         "daten": "Binance-Archiv: Kerzen" + (", " + ", ".join(c["daten"]) if c["daten"] else ""), "gebuehren": KOSTEN + "; in bewegtem Markt mindestens 5 % der Spanne der letzten Kerze je Order",
                         "algorithmus": c["regel"], "parameter": c["kandidat"], "hebel": c["hebel"], "validierung": c["validierung"],
                         "vertrauen": "gering: nicht validiert, bestes von 1.199 Ergebnissen" if beob else "gering bis mittel; Kosten in bewegtem Markt nur als Annahme",
                         "ergebnisdateien": [f"forschung/papier/{c['id']}/", "forschung/fabrik/ergebnisse/schlusspruefung.json"],
                         "kennzahlen": {"zeitraum": "Schlussprüfung 07/2024–03/2025", "n85_bp": r["n85_v2"], "n0_bp": r["n0_v2"], "t_n85": r["t85_v2"], "haltedauer_min": r["haltedauer_min"],
                                        "ertrag_jahr_pct_hebel1": r["ertrag_jahr_pct_hebel1_v2"]}})
fz = ROOT / "forschung/fabrik/ergebnisse/zaehlung.json"
if fz.exists():
    z = json.loads(fz.read_text())
    eintraege.append({"id": "FAB", "name": "Strategie-Fabrik (Massensuche)", "version": "Generationen 1–2", "familie": "alle Familien", "kategorie": "backtest", "einstufung": "–",
                      "status": f"{z['berechnet']:,} Kandidaten gerechnet".replace(",", "."), "validierung": f"{z['validiert']} validiert nach fünf Stufen; siehe Übersicht „Forschungsdurchsatz“",
                      "vertrauen": "–", "ergebnisdateien": ["forschung/fabrik/ergebnisse/zaehlung.json", "forschung/fabrik/ergebnisse/kandidaten.parquet", "forschung/fabrik/ergebnisse/schlusspruefung.json"]})
for exp, name in (("E07", "Ursachenanalyse Orderbuch-Tiefe (17 Einstellungen)"), ("E09", "Bestätigung auf sieben frischen Coins"), ("E10", "Ausstiegs-Engine (8 Varianten)"),
                  ("E11", "Kombination mit dem 14-Tage-Trend"), ("E12", "Marktphasen")):
    eintraege.append({"id": exp, "name": name, "version": "–", "familie": "Orderbuch / Liquidität", "kategorie": "backtest", "einstufung": "–", "status": "Analyse abgeschlossen",
                      "ergebnisdateien": [str(p.relative_to(ROOT)) for p in sorted(ERG.glob(exp.lower() + "_*.json"))], "validierung": "siehe Protokoll", "vertrauen": "–"})
register = {"stand": time.strftime("%Y-%m-%d %H:%M UTC", time.gmtime()), "runde": 1, "experimente": len(json.loads((ROOT / "forschung/engine/experimente.json").read_text())),
            "kategorien": {"backtest": "Historische Rückrechnung, kein laufender Test", "kandidat": "Neue Strategie, für einen Vorwärtstest vorbereitet, nicht gestartet",
                           "vorbereitet": "Vorwärtstest eingerichtet, wartet auf Freigabe", "laufend": "Papier-Vorwärtstest läuft", "abgeschlossen": "Vorwärtstest beendet oder gescheitert"},
            "einstufungen": {"A": "verworfen", "B": "interessant, unbestätigt", "C": "vorläufig vielversprechend", "D": "bereit für unabhängigen Vorwärtstest"},
            "eintraege": eintraege}
(Path(__file__).parent / "register.json").write_text(json.dumps(register, indent=1, ensure_ascii=False))
print(len(eintraege), "Einträge;", {k: sum(1 for e in eintraege if e["kategorie"] == k) for k in register["kategorien"]})
