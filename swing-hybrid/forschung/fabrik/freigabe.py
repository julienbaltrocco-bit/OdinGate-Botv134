"""Freigabe eines validierten Fabrik-Kandidaten als Papier-Test (Schattentest), automatisch und nachvollziehbar.

  .venv/bin/python -I forschung/fabrik/freigabe.py <Kennung> [Startdatum JJJJ-MM-TT]

Schritte: (1) Kandidat muss den Status "validiert" haben. (2) Risikoprüfung: jeder Kalendertag als Start über Training,
Auswahl- und Schlussprüfung; gewählt wird der höchste Hebel bis 3 ohne Liquidation und mit Kontostand über 50 %.
(3) Der Code der Fabrik wird in den Testordner kopiert und mit der Einstellung eingefroren (Prüfsumme). (4) Parität:
der Papier-Runner muss auf einem historischen Fenster dieselben Trades bilden wie die Rückrechnung. Erst dann wird der
Test registriert. Der tägliche Lauf (papier/tag.sh) führt ihn ab dem Folgetag automatisch mit.
"""
import datetime as dt
import json
import shutil
import sqlite3
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

F = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(F))
sys.path.insert(0, str(F.parent))
from fabrik import daten as D, generator as G, kern as FK, lauf as L, signale as S, trichter as T

PAPIER = F / "papier"
ARTEN = {"minuten": ("kaufdruck",), "aufschlag": ("aufschlag",), "positionen": ("oi_", "konten_ls", "profis_gegen_konten", "taker_4h"), "tiefe": ("tiefe_", "liq_entzug")}


def trades_voll(z, i0, i1):
    """Einzel-Trades des Kandidaten über die Kerzen [i0, i1) aus dem großen Datenspeicher (Referenz für die Parität und das Risiko)."""
    a = T.aufgabe_aus(z)
    halte, sl, tp, tr, ta, sx = T.ausstieg_aus(z)
    M = T.markt_von(z, a)
    alt, L.I_ENDE = L.I_ENDE, i1
    teile = []
    try:
        for j in M:
            ein, wert = L.einstieg(a, j)
            aus = np.zeros((200000, 6))
            n = FK.trades_liste(np.asarray(L._g["o"][j]), np.asarray(L._g["h"][j]), np.asarray(L._g["l"][j]), np.asarray(L._g["fcum"][j]), ein, wert,
                                np.asarray(L._g["sigma"][j]), i0, i1, halte, sl, tp, tr, ta, np.nan if sx is None else sx, L.slip_bewegt(j), aus)
            t = pd.DataFrame(aus[:n], columns=["a", "b", "richtung", "roh", "tief", "offen"])
            t["coin"] = D.COINS[j]
            t["ein"], t["aus"] = D.RASTER[t["a"].astype(int)], D.RASTER[t["b"].astype(int)]
            teile.append(t)
    finally:
        L.I_ENDE = alt
    return pd.concat(teile).sort_values("ein").reset_index(drop=True), M


def hebel_waehlen(t, n_coins):
    """Jeder Kalendertag als Start: tiefster Kontostand (gleichzeitige Trades alle zum ungünstigsten Kurs), je Hebel 3, 2, 1."""
    t = t.sort_values("aus")
    netto = (t["roh"] - L.KOSTEN85).to_numpy() / 1e4
    tief = (t["tief"] - L.KOSTEN85).to_numpy() / 1e4
    ein, aus = t["ein"].to_numpy(), t["aus"].to_numpy()
    bericht = {}
    for hebel in (3.0, 2.0, 1.0):
        f = hebel / n_coins
        real = np.cumsum(netto * f)
        vor = np.concatenate([[0.0], real[:-1]])
        gleichzeitig = np.array([tief[(ein <= e) & (aus > e)].sum() for e in ein]) * f      # pessimistisch: alle offenen Trades am Tiefpunkt
        niedrig = np.minimum(vor + np.minimum(gleichzeitig, tief * f), real)
        sufmin = np.minimum.accumulate(niedrig[::-1])[::-1]
        tage = pd.date_range(t["ein"].min().floor("D"), t["ein"].max().floor("D") - pd.Timedelta(days=30), freq="D")
        k = np.searchsorted(aus, tage.to_numpy())
        k = k[k < len(t)]
        tiefst = 1 + sufmin[k] - np.concatenate([[0.0], real])[k]
        bericht[hebel] = {"starttage": int(len(k)), "tiefster_kontostand": round(float(tiefst.min()), 3), "liquidationen": int((tiefst <= 0.01 * hebel).sum()),
                          "anteil_unter_70pct": round(float((tiefst < 0.7).mean()), 4)}
    wahl = next((h for h in (3.0, 2.0, 1.0) if bericht[h]["liquidationen"] == 0 and bericht[h]["tiefster_kontostand"] >= 0.5), None)
    return wahl, bericht


def freigeben(kennung: str, start: str = None, beobachtung: bool = False, name: str = None, begruendung: str = None, freigegeben: str = None, wertung=(100, 300)):
    """beobachtung=True: Der Kandidat ist NICHT validiert. Ohne `freigegeben` wird der Test nur vorbereitet (Regel eingefroren,
    Status "pausiert") und läuft erst, wenn der Auftraggeber ihn ausdrücklich freigibt. `freigegeben` = Datum und Wortlaut der
    Freigabe des Auftraggebers; dann startet der Test. `begruendung` ersetzt den Text zur Prüflage, `wertung` = Trades bis zur
    Zwischen- und Hauptwertung."""
    L._init()
    con = T.db()
    z = con.execute("SELECT * FROM kandidaten WHERE id = ?" + ("" if beobachtung else " AND status = 'validiert'"), (kennung,)).fetchone()
    if z is None:
        print("Kein validierter Kandidat mit dieser Kennung; keine Freigabe."); return 2
    tid = f"{'B' if beobachtung else 'F'}-{kennung[:8]}"
    ordner = PAPIER / tid
    if ordner.exists():
        print(tid, "existiert bereits; ein laufender Test wird nicht verändert."); return 0
    tiefe = bool(z["braucht"] == "t" or (z["best"] and ("tiefe" in z["best"] or "liq_entzug" in z["best"])))
    t, M = trades_voll(z, L.I_TIEFE if tiefe else L.I_T, D.N)
    hebel, risiko = hebel_waehlen(t, len(M))
    if hebel is None:
        print("Risikoprüfung nicht bestanden (Liquidation oder Kontostand unter 50 % auch bei Hebel 1):", risiko); return 3
    namen = [z["signal"]] + ([json.loads(z["best"])[0]] if z["best"] else [])
    arten = sorted(a for a, praefixe in ARTEN.items() if any(n.startswith(praefixe) for n in namen))
    slip = np.asarray(L._g["slip_bp"])
    start = start or str((dt.datetime.now(dt.timezone.utc) + dt.timedelta(days=1)).date())
    kd = {"signal": z["signal"], "th": z["th"], "r": z["r"], "f": z["f"], "k": z["k"], "ausstieg": list(T.ausstieg_aus(z)), "ausstieg_name": z["x"], "markt": z["m"],
          "best": json.loads(z["best"]) if z["best"] else None, "kennung": z["id"], "generation": z["gen"]}
    sp = json.loads((F / "fabrik/ergebnisse/schlusspruefung.json").read_text())
    v2 = next(e for e in sp["ergebnisse"] if e["id"] == z["id"] and e["gen"] == z["gen"])
    richt = "mit dem Signal" if z["r"] == 1 else "gegen das Signal"
    einfach = json.loads((F / "fabrik/ergebnisse/schlusspruefung_einfache_slippage.json").read_text()) if beobachtung else None
    cfg = {"id": tid, "name": name or (f"Beobachtung (nicht validiert): {z['signal']}, {z['f']}" if beobachtung else f"Fabrik {z['signal']} ({richt})"), "version": "1.0", "strategie": "fabrik", "art": "Schattentest (Binance-Archiv, ein Tag Verzug, keine Orders)",
           "coins": [D.COINS[j] for j in M], "coin_index": M, "daten": arten, "kandidat": kd,
           "regel": f"Signal {z['signal']}, Schwelle {z['th']}, {richt}, Filter {z['f']}, geprüft alle {z['k'] * 5} Minuten, Ausstieg {z['x']}"
                    + (f", Bestätigung durch {kd['best'][0]}" if kd["best"] else "") + ".",
           "start": f"{start}T00:00:00Z", "vorlauf_tage": 38, "kapital_usd": 5000, "hebel": hebel,
           "kosten": {"taker_bp": 8.0, "rebate": 0.85, "slippage_bp_je_order": {D.COINS[j]: float(slip[j]) for j in M}, "slippage_anteil_spanne": L.SPANNEN_ANTEIL},
           "risiko": {"mmr": 0.01, "abbruch_kontostand": 0.70},
           "validierung": (begruendung if begruendung else f"NICHT validiert. Bester von {sp['finalisten_gesamt']} Finalisten der Strategie-Fabrik (p = {v2['p_v2']}), besteht die Korrektur für die vielen "
                           f"gleichzeitig geprüften Regeln aber nur mit der ruhigen Kostenannahme, nicht mit der strengen. Schlussprüfung netto mit Rebate {v2['n85_v2']} bp je Trade, "
                           f"ohne Rebate {v2['n0_v2']} bp. Beobachtungstest: Nur neue Daten können klären, ob etwas daran ist." if beobachtung else
                           f"Strategie-Fabrik: alle fünf Stufen bestanden (einer von {sp['validiert']} validierten unter {sp['finalisten_gesamt']} Finalisten aus über 500.000 Kandidaten). "
                           f"Schlussprüfung netto mit Rebate {v2['n85_v2']} bp je Trade, ohne Rebate {v2['n0_v2']} bp. Validiert heißt nicht bewiesen."
                           ) + (" Schlussprüfung für Orderbuch-Signale nicht unberührt." if tiefe else ""),
           "rueckrechnung": {"n85_t": z["n85_t"], "n85_v1": z["n85_v"], "n85_v2": v2["n85_v2"], "n0_v2": v2["n0_v2"], "t85_v2": v2["t85_v2"], "trades_v2": v2["n_v2"],
                             "ertrag_jahr_pct_hebel1_v2": v2["ertrag_jahr_pct"], "haltedauer_min": z["dauer_min"], "risiko_starttage": {str(h): r for h, r in risiko.items()}},
           "eingefroren": time.strftime("%Y-%m-%d", time.gmtime()), "beobachtung": beobachtung,
           "freigabe": (f"Beobachtungstest, nicht validiert; {freigegeben} (nur Papierhandel)" if beobachtung and freigegeben else
                        "offen: Beobachtungstest, nicht validiert, wartet auf die ausdrückliche Freigabe des Auftraggebers (protokoll.md Abschnitt 22; nur Papierhandel)" if beobachtung else "automatisch nach Auftrag vom 15.11.2026 (nur Papierhandel)")}
    code = ordner / "code"
    (code / "fabrik").mkdir(parents=True)
    for name in ("__init__", "daten", "signale", "kern", "lauf", "generator"):
        shutil.copy(F / "fabrik" / f"{name}.py", code / "fabrik" / f"{name}.py")
    shutil.copy(F / "fabrik/papier_fabrik.py", code / "papier_fabrik.py")
    cfg["strategie_sha256"] = __import__("hashlib").sha256(b"".join(p.name.encode() + p.read_bytes() for p in sorted(code.rglob("*.py")))
                                                           + json.dumps(kd, sort_keys=True).encode()).hexdigest()
    (ordner / "konfiguration.json").write_text(json.dumps(cfg, ensure_ascii=False, indent=1))
    (ordner / "steuerung.json").write_text(json.dumps({"status": "pausiert" if beobachtung and not freigegeben else "laufend",
                                                       "hinweis": ("Wartet auf die Freigabe des Auftraggebers. Start: status 'laufend'. " if beobachtung and not freigegeben else "")
                                                       + "Pausieren: status 'pausiert'. Beenden: status 'beendet' und 'ende' (UTC)."}, ensure_ascii=False, indent=1))
    (ordner / "plan.md").write_text(f"""# Papier-Test {tid}: {cfg['name']}

Festgelegt am {cfg['eingefroren']}, vor dem Start. {f"**Nicht validiert.** Beobachtungstest, {freigegeben}." if beobachtung and freigegeben else "**Nicht validiert.** Der Test ist nur vorbereitet und läuft erst nach ausdrücklicher Freigabe des Auftraggebers. Die Regel ist ab heute eingefroren; gewertet wird ab dem Startdatum, auch wenn die Freigabe später kommt (jeder Lauf rechnet vollständig neu, es geht nichts verloren)." if beobachtung else "Freigabe automatisch nach Auftrag vom 15.11.2026."} Nur Papierhandel, keine Orders.

1. **Ziel.** Prüfen, ob die Regel nach ihrer Festlegung weiter verdient. Rückrechnung in der Schlussprüfung: netto mit Rebate
   {v2['n85_v2']} bp je Trade, ohne Rebate {v2['n0_v2']} bp, {v2['n_v2']} Trades in neun Monaten.
2. **Art.** Schattentest aus den täglichen Binance-Archivdateien (ein Tag Verzug), Buchung mit dem eingefrorenen Kostenmodell.
3. **Regel.** {cfg['regel']} Märkte: {', '.join(cfg['coins'])}. Hebel {hebel:g}, 5.000 $ Papier-Kapital, feste Größe je Coin.
4. **Zeitraum.** Start {start} 00:00 UTC. Zwischenwertung nach {wertung[0]} Trades, Hauptwertung nach {wertung[1]} Trades oder zwölf Monaten.
5. **Erfolg.** In der Hauptwertung netto mit Rebate im Mittel positiv. Das gilt als „nicht widerlegt“, nicht als Beweis.
6. **Abbruch.** Kontostand unter 70 % des Startkapitals oder Liquidation im Modell (setzt der Runner selbst um); in der
   Hauptwertung netto mit Rebate negativ.
7. **Unverändert.** Code und Einstellung sind im Ordner `code/` und in `konfiguration.json` eingefroren (Prüfsumme).
8. **Ausfälle.** Jeder Lauf rechnet den Test vollständig neu; ein ausgefallener Lauf verliert nichts.
""")
    print(tid, "vorbereitet, wartet auf Freigabe" if beobachtung and not freigegeben else "angelegt", "| Hebel", hebel, "| Daten:", arten, "| Risiko:", risiko[hebel])
    return 0




def auswahl_papier(max_neu: int = 5):
    """Aus den validierten Kandidaten bis zu `max_neu` möglichst verschiedene auswählen (kleinster p-Wert zuerst; Korrelation der
    Tagesergebnisse in T und V1 mit allen schon gewählten unter 0,5) und freigeben. Die übrigen bleiben als validiert im Register."""
    L._init()
    con = T.db()
    sp = json.loads((F / "fabrik/ergebnisse/schlusspruefung.json").read_text())
    val = [e for e in sp["ergebnisse"] if e["validiert"] and e.get("by_bestanden")]      # nur, wer auch die strengere Korrektur besteht
    reihen, gewaehlt, regeln = [], [], set()
    for e in val:
        z = con.execute("SELECT * FROM kandidaten WHERE id = ? AND gen = ?", (e["id"], e["gen"])).fetchone()
        r = np.asarray(np.load(L.AUS / f"tage_{z['gen']}.npy", mmap_mode="r")[z["zeile"]], dtype=np.float64)
        if e["regel"] not in regeln and all(abs(np.corrcoef(r, x)[0, 1]) < 0.5 for x in reihen):   # eine Einstiegsregel = eine Entdeckung
            reihen.append(r); gewaehlt.append(e["id"]); regeln.add(e["regel"])
        if len(gewaehlt) >= max_neu:
            break
    print(f"{len(val)} validiert, davon für Papier-Tests gewählt: {gewaehlt}")
    return gewaehlt


if __name__ == "__main__":
    if sys.argv[1] == "auswahl":
        for kennung in auswahl_papier(int(sys.argv[2]) if len(sys.argv) > 2 else 5):
            freigeben(kennung, sys.argv[3] if len(sys.argv) > 3 else None)
    elif sys.argv[1] == "beobachtung":
        sys.exit(freigeben(sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else None, beobachtung=True))
    else:
        sys.exit(freigeben(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None))
