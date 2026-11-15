# Betrieb der OdinGate Research Engine

Stand 15.11.2026. Dieses Blatt sagt, was wie läuft, was ohne KI weiterläuft und wo die Grenzen liegen.

## Bausteine

| Baustein | Ort | Läuft ohne KI? |
|---|---|---|
| Papier-Runner (alle Tests, täglich) | `papier/tag.sh`, `papier/runner.py` | ja, braucht nur python3 und git |
| Spiegel von Test 1 und Test 2 (nur lesend) | `papier/spiegel.py` | ja |
| Experiment-Warteschlange (festgelegte Rechnungen) | `engine/warteschlange.py` | ja |
| Automatische Zusammenfassung je zehn Experimente | `engine/zusammenfassung.py` | ja |
| Experiment-Buch, Hypothesenliste, Register | `engine/experimente.json`, `engine/hypothesen.json`, `register/` | Dateien im Repository |
| Neue Ideen entwickeln, Ergebnisse beurteilen | `engine/AUFTRAG.md` | **nein**, braucht eine KI-Sitzung |
| Zentrale Übersicht | private Seite mit eigener Datenbank | Anzeige ja; das Eintragen des Stands derzeit über die KI-Sitzung |

## Wie der Dauerbetrieb heute gelöst ist

- **Zeitgeber:** zwei geplante Aufgaben im Claude-Konto. Die tägliche Aufgabe „Papier-Lauf“ führt `papier/tag.sh` aus
  und trägt den Stand in die Übersicht ein. Die Aufgabe „Forschungszyklus“ startet eine frische Forschungssitzung,
  die nach `engine/AUFTRAG.md` arbeitet. Beide verbrauchen Kontingent des Claude-Abos, keine zusätzliche bezahlte
  Schnittstelle. Beide lassen sich in der Claude-App unter den geplanten Aufgaben pausieren oder löschen.
- **Zustand der Papier-Tests:** Jeder Lauf rechnet den Test vollständig aus den öffentlichen Archivdaten neu. Ein
  ausgefallener oder doppelter Lauf kann deshalb nichts verlieren und nichts verdoppeln. Innerhalb eines Laufs wird
  in eine lokale SQLite-Datenbank geschrieben (eine Transaktion je Lauf, eindeutige Trade-Kennung, Sperre gegen
  Doppelläufe). Dauerhaft liegt der Stand in der Datenbank der Übersicht, nicht im öffentlichen Git.
- **Git** enthält nur Code, eingefrorene Konfigurationen, Protokolle und Forschungsergebnisse.

## Grenzen, ehrlich benannt

1. **Kein dauerhaft laufender Prozess.** Die Umgebung ist ein Wegwerf-Container. „Dauerbetrieb“ heißt hier: ein
   Zeitplan startet kurze Läufe. Fällt der Zeitplan aus (Abo-Grenze, Störung), läuft nichts, bis er wieder läuft;
   verloren geht dabei nichts.
2. **Schattentest statt Live-Papierhandel.** Die Orderbuch-Tiefe von Binance ist von hier nur über das Archiv mit
   einem Tag Verzug erreichbar. Der Test bucht zu Binance-Kursen mit Kostenmodell und misst keine Füllungen bei Yubit.
3. **Forschung braucht KI.** Ohne KI-Sitzung laufen nur festgelegte Rechnungen und die Papier-Tests weiter.
4. **Frische Sitzungen haben keine Marktdaten.** Sie laden, was sie brauchen, jedes Mal neu (einige Minuten).

## Unabhängig von Claude betreiben (vorbereitet, nicht aktiviert)

`papier/tag.sh` läuft auf jedem Rechner mit python3 und git, also auch als geplanter GitHub-Actions-Lauf oder auf
einem kleinen Server (cron). Dafür fehlen zwei Entscheidungen des Auftraggebers:
- GitHub führt Zeitpläne nur aus dem Standard-Zweig aus. Die Vorlage `betrieb/github_actions_vorlage.yml` müsste
  dorthin (Pull Request oder Standard-Zweig ändern).
- Ohne KI-Sitzung kann der Stand nicht in die private Übersicht geschrieben werden. Er müsste dann verschlüsselt
  abgelegt werden (wie beim bestehenden Board) oder auf einem eigenen Server liegen.

## Test pausieren, beenden, prüfen

- Pausieren: in `papier/<ID>/steuerung.json` den Status auf `pausiert` setzen und pushen.
- Beenden: Status `beendet` und `ende` (Zeit in UTC). Der Test bleibt mit allen Ergebnissen in der Übersicht.
- Alles anhalten: die beiden geplanten Aufgaben in der Claude-App pausieren.
- Von Hand prüfen: `bash swing-hybrid/forschung/papier/tag.sh` und `pytest swing-hybrid/forschung/tests`.
