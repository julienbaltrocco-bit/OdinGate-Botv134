# Audit OdinGate: konsolidierter Zwischenbericht

Stand: 15.11.2026, 21:00 UTC. Der Audit-Lauf wurde auf Wunsch des Auftraggebers vorzeitig und kontrolliert gestoppt.
Dieser Bericht fasst alles zusammen, was bis dahin vorlag. Er ist ohne weitere Agenten aus den gespeicherten
Rohergebnissen geschrieben. Geprüft wurde der Stand des Zweigs `claude/intelligent-sagan-2cviug` (Commit `0e92022`).

Alles hier betrifft Rückrechnung und Papierhandel. Es ist kein echtes Geld im Spiel. Keine Anlageberatung.

## Kurzfassung

1. **Die Rechnung stimmt.** Vier Prüfer und die Gegenprüfer haben die Kernzahlen des 14-Tage-Trends auf eigenen
   Wegen nachgerechnet (Entwicklung +59,4 % pro Jahr, Sharpe 0,95; Prüfzeitraum +16,5 %, Sharpe 0,34). Ein Blick in
   die Zukunft wurde nicht gefunden. Die Buchführung des Papier-Bots ist in sich stimmig.
2. **Die Deutung war zu stark.** Der Vorteil ist statistisch nicht gesichert. Im Prüfzeitraum stammt das gesamte
   Plus aus dem angenommenen Rebate von 85 %; ohne Rebate steht dort ein Verlust von 19,6 %. Die Bezeichnungen
   „belegt“ und „ungesehener Prüfzeitraum“ sind so nicht haltbar.
3. **Die laufenden Papier-Tests fahren eine Einstellung, die nie gerechnet wurde.** Hebel 3 ohne wirksames
   Verlustlimit. In der eigenen Historie wäre ein so gestartetes Konto je nach Zählweise von 8 bis 16 % der Starttage
   aus auf null gefallen. Der Bot kennt weder Margin noch Liquidation und würde nach einem Kontostand unter null
   einfach weiterrechnen.
4. **Akut entsteht kein Schaden.** Es läuft nur Papierhandel, die Schranken vor echten Orders wirken, im Repo liegen
   keine Zugangsdaten.
5. **Weitere Prüfläufe mit Agenten sind nicht nötig.** Die verbleibenden zwingenden Punkte sind eine Anfrage bei
   Yubit und Entscheidungen des Auftraggebers (Abschnitt 5).

## 1. Untersuchte Bereiche

Sieben Prüfer haben je einen Bereich vollständig bearbeitet. Danach sollte jeder schwere Befund (P0, P1) von einem
zweiten, unabhängigen Prüfer mit eigenem Code widerlegt werden; geplant waren bis zu drei je Bereich. Beim Stopp
waren 8 dieser Gegenprüfungen fertig, 2 liefen gerade, 11 waren noch nicht begonnen.

| Bereich | Inhalt | Befunde (P0 / P1 / P2 / P3) | Gegenprüfung |
|---|---|---|---|
| QD Quantitative Research | Daten, Statistik, Überanpassung, Protokoll | 12 (3 / 5 / 2 / 2) | 3 von 3 fertig, alle bestätigt |
| QR Unabhängige Nachrechnung | Kernzahlen ohne Projektcode neu gerechnet | 8 (1 / 2 / 4 / 1) | 3 von 3 fertig, alle bestätigt |
| ENG Trading Engine | Rechenkern, Papier-Bot, Live-Pfad | 11 (2 / 4 / 4 / 1) | 2 bestätigt, 1 abgebrochen |
| RSK Risk Engineering | Hebel, Verlustgrenzen, Klumpenrisiko, Stop | 11 (2 / 4 / 5 / 0) | 1 abgebrochen, 2 nicht begonnen |
| INF Infrastructure | Taktgeber, Git als Speicher, Ausfälle | 12 (3 / 4 / 4 / 1) | nicht begonnen |
| SEC Security | Board-Schutz, Geheimnisse, Live-Schranken | 12 (2 / 3 / 5 / 2) | nicht begonnen |
| ARC Architektur | Aufbau, Doppelungen, Testabdeckung | 12 (3 / 6 / 3 / 0) | nicht begonnen |
| **Summe** | | **78 (16 / 28 / 27 / 7)** | **8 bestätigt, 0 widerlegt** |

Nicht untersucht: die Next.js-Anwendung im Wurzelverzeichnis des Repos (gehört nicht zur Handelsplattform), die
echte Yubit-Schnittstelle (auftragsgemäß keine Orders, kein Konto) und bekannte Schwachstellen der installierten
Pakete.

Nicht mehr erstellt wurden die drei geplanten Testautoren, die sechs Einzelberichte, die Roadmap und die
Vollständigkeitsprüfung. Dieser Bericht ersetzt sie (siehe Abschnitt 4).

## 2. Gefundene Probleme nach Kritikalität

Bedeutung der Stufen: **P0** heißt, vor jedem Einsatz von echtem Geld zu beheben, oder eine Aussage ist in ihrer
jetzigen Form nicht haltbar. **P1** heißt, das Ergebnis oder der Betrieb wird spürbar verfälscht. **P2** und **P3**
sind Mängel ohne Einfluss auf die Kernaussage. Kein Befund gefährdet heute Geld.

Die 16 P0-Befunde beschreiben neun verschiedene Sachverhalte, weil mehrere Prüfer unabhängig auf dasselbe stießen.

### P0: neun Sachverhalte

| Nr. | Sachverhalt | Befunde | Stand |
|---|---|---|---|
| A | **Hebel 3 ohne wirksames Verlustlimit wurde nie gerechnet; die Historie enthält Totalverluste.** Geprüft wurde in der Forschung Hebel 0,2 mit Tageslimit 3 %, berichtet wird Hebel 1 ohne Limit, betrieben wird Hebel 3 mit Limit 100 % (also faktisch aus). | QR-01, QD-04, RSK-01, ARC-01 | bestätigt |
| B | **Kein Margin- und Liquidationsmodell** in Rückrechnung und Papier-Bot. Das Papier-Konto kann unter null fallen und eröffnet danach weiter Positionen in voller Größe. Margin-Regeln von Yubit sind unbekannt. | ENG-02, RSK-02, ARC-03 | bestätigt |
| C | **Der Vorteil ist statistisch nicht gesichert**, auch nicht in der Entwicklung, sobald man berücksichtigt, dass der Kandidat aus mehreren Einstellungen ausgewählt wurde. | QD-01 (dazu QR-03) | bestätigt |
| D | **Das gesamte Plus im Prüfzeitraum stammt aus dem Rebate von 85 %.** Ohne Rebate Verlust. Ein Nachweis des Rebates fehlt. | QD-03 (dazu QR-02, ENG-05) | bestätigt |
| E | **Live-Pfad: Der Sicherheitsdeckel je Order blockiert auch das Schließen.** Ist eine Position über den Deckel gewachsen, kann der Bot sie nicht mehr schließen. Der Live-Pfad ist insgesamt ungetestet. Schlummernder Fehler, der Papier-Modus ist nicht betroffen. | ENG-01, SEC-02, ARC-02 | bestätigt |
| F | **Der Taktgeber ist eine unbeaufsichtigte KI-Sitzung.** Sie läuft rund alle 5 Minuten statt wie dokumentiert stündlich. Ausfälle werden weder erkannt noch nachgeholt. | INF-01 | direkt sichtbar |
| G | **Der Git-Zweig dient als gemeinsamer Speicher.** Ein fremder Push während eines Bot-Laufs (Fenster rund 51 Sekunden) lässt den Bot dauerhaft und still abweichen; Test 2 läuft dann nicht mehr. | INF-02 | nicht gegengeprüft, aus dem Skript ablesbar |
| H | **Keine Sperre gegen Doppelläufe, Zustand wird zuletzt gespeichert.** Ein Abbruch an der falschen Stelle verdoppelt Orders im Protokoll. | INF-03 | nicht gegengeprüft |
| I | **Der Passwortschutz des Boards schützt nichts.** Derselbe Stand liegt unverschlüsselt im selben öffentlichen Repo, zusätzlich liegt eine alte Klartextdatei `docs/stand.json` im veröffentlichten Ordner. | SEC-01 (dazu SEC-03, ARC-09) | direkt nachgeprüft |

Die wichtigsten Zahlen dazu stehen in Abschnitt 3.

### P1: die wichtigsten Punkte

- **Prüfzeitraum nicht „ungesehen“ (QD-02).** Er war vor der Suche für Trend-Strategien auf denselben Coins bekannt,
  diente in Runde 3 als Hürde und steht seither in 22 Ergebnisdateien.
- **Kopfzahl hängt an einer nachträglich geänderten Kostenannahme (QD-06).** Mit der vorab festgelegten Annahme
  (0,05 % je Order) ergibt der Prüfzeitraum +7,8 % pro Jahr bei Sharpe 0,16. Die +16,5 % entstehen erst mit den
  später gemessenen Yubit-Spannen (30 Messungen in einer Samstagsstunde). Gegenprobe zugunsten der Annahme: Test 1
  misst bisher noch niedrigere Kosten.
- **336 Stunden ist eine Spitze, keine Hochebene (QD-07).** Sharpe in der Entwicklung für benachbarte Rückblicke:
  288 h 0,74, 336 h 0,95, 384 h 0,55, 432 h 0,20. Die behauptete Robustheit galt nur für andere Bauarten mit
  demselben Rückblick.
- **Der Vorwärtstest hat keine vorab festgelegte Auswertung und kann den Vorteil in absehbarer Zeit nicht belegen
  (QD-08).** Bei einem wahren Sharpe von 0,95 bräuchte ein statistischer Beleg rund 7 Jahre.
- **Test 2 misst eine andere Regel als die gerechnete (ENG-03, QR-05, ARC-05, RSK-05, RSK-06).** Die Rückrechnung
  prüfte Stop und Ziel am Stundenschluss, der Bot prüft bei jedem Lauf, also rund alle 5 Minuten. In der Entwicklung
  ergibt das 373 statt 236 Stops, 29,7 % statt 33,3 % pro Jahr und Sharpe 1,04 statt 1,13. Der Stop ist außerdem
  kein Stop an der Börse: Er greift nur, wenn ein Bot-Lauf stattfindet.
- **Die Stop-Variante selbst ist unbestätigt (RSK-06).** Ein Prüfer hat sie erstmals für die Vorperiode 2020/21
  gerechnet: −40,5 % bei Hebel 1, Sharpe −0,86. Diese Zahl ist nicht gegengeprüft.
- **Der berichtete Einbruch unterschätzt das Risiko (QD-05).** 25 % und 31 % gelten für Hebel 1 und sind am
  gewachsenen Konto gemessen. Gemessen am Startkapital sind es 50 bis 57 %, bei Hebel 3 das Dreifache.
- **Klumpenrisiko (RSK-03).** Zehn Positionen entsprechen 1,2 bis 2,5 unabhängigen Wetten.
- **Feste Stückzahl (RSK-04).** Nach Verlusten wird nie verkleinert; neue Positionen kommen immer in voller Größe.
- **Architektur (ARC-04, ARC-06, ARC-07).** Die Handelsregel ist in Forschung und Bot getrennt geschrieben, ohne
  Test, der beide vergleicht. Kritische Rechenwege des Bots haben keinen Test.
- **Betrieb (INF-04 bis INF-07).** Kein Protokoll, kein Alarm, das Board erkennt einen stehenden Bot nicht. Jeder
  Lauf erzeugt zwei Pushes; das sind rund 24 Seiten-Builds pro Stunde und etwa 12 MB Repo-Zuwachs pro Tag.
- **Regelrisiko bei Yubit (SEC-05).** Laut den im Repo wiedergegebenen Regeln braucht ein Bot eine Genehmigung, und
  Yubit darf Rebates streichen. Eine Freigabe liegt nicht vor.

### Alle 78 Befunde

Sortiert nach Stufe. „Sicherheit“ ist die Selbsteinschätzung des Erstprüfers. Evidenz, Auswirkung, Empfehlung und der
Befehl zum Nachstellen stehen je Befund in `befunde_vollstaendig.md`.

| ID | Stufe | Sicherheit | Befund | Stand |
|---|---|---|---|---|
| ARC-01 | P0 | hoch | Drei verschiedene Strategie- und Risikostände: geprüft Hebel 0,2 mit Tageslimit 3 %, berichtet Hebel 1 ohne Limit, betrieben Hebel 3 ohne Limit | Sachverhalt über QR-01, QD-04 bestätigt |
| ARC-02 | P0 | hoch | Live-Handelspfad im Papier-Bot ist ungetestet, weicht vom Papier-Ausführungsmodell ab, und der Sicherheitsdeckel blockiert auch schließende Orders | Teil „Deckel“ über ENG-01 bestätigt, Rest nicht gegengeprüft |
| ARC-03 | P0 | hoch | Kein Margin- und Liquidationsmodell in Papier-Konto und Rechenkern; weitere Bausteine für einen Echtgeldbetrieb fehlen | Sachverhalt über ENG-02 bestätigt |
| ENG-01 | P0 | hoch | Live-Modus: Sicherheitsdeckel max_order_usd blockiert auch Schließ-Orders | **bestätigt** (eigene Gegenprüfung) |
| ENG-02 | P0 | hoch | Kein Margin- und Liquidationsmodell bei Hebel 3; Einbruchskennzahl unterschätzt den Verlust eines frisch gestarteten Kontos | **bestätigt** (eigene Gegenprüfung) |
| INF-01 | P0 | hoch | Zeitgeber ist eine unbeaufsichtigte KI-Sitzung; tatsächlicher Takt weicht vom dokumentierten ab, Ausfälle werden weder erkannt noch nachgeholt | direkt sichtbar (Commits rund alle 5 Minuten) |
| INF-02 | P0 | hoch | Git-Zweig als gemeinsamer Zustandsspeicher: ein fremder Push im Lauf-Fenster lässt den Runner dauerhaft und still abweichen | nicht gegengeprüft |
| INF-03 | P0 | hoch | Keine Sperre gegen Doppelläufe und Zustand wird zuletzt gespeichert: Abbruch oder Überlappung verdoppelt Orders im Protokoll, im Live-Pfad bleiben unbekannte Börsenpositionen | nicht gegengeprüft |
| QD-01 | P0 | hoch | Vorteil des Kandidaten ist statistisch nicht gesichert, nach Auswahl-Korrektur auch in der Entwicklung nicht | **bestätigt** (eigene Gegenprüfung) |
| QD-03 | P0 | hoch | Der gesamte Ertrag im Prüfzeitraum stammt aus dem 85-%-Rebate; ohne Rebate Verlust | **bestätigt** (eigene Gegenprüfung) |
| QD-04 | P0 | hoch | Papier-Tests laufen mit Hebel 3 ohne Tageslimit; diese Konfiguration wurde nie gerechnet und widerspricht der eigenen Hebel-Regel (0,2) | **bestätigt** (eigene Gegenprüfung) |
| QR-01 | P0 | hoch | Berichteter Einbruch (25 % / 31 %) und „Einsatz 100 %“ gelten nicht für die laufende Konfiguration mit Hebel 3; in der eigenen Historie wäre ein Hebel-3-Konto mehrfach ausgelöscht worden | **bestätigt** (eigene Gegenprüfung) |
| RSK-01 | P0 | hoch | Hebel 3 ohne wirksames Verlustlimit widerspricht dem eigenen Forschungsergebnis; historisch Totalverlust nach rund jedem achten Starttag binnen eines Jahres | Gegenprüfung abgebrochen; Sachverhalt über QR-01, QD-04, ENG-02 bestätigt |
| RSK-02 | P0 | hoch | Liquidation, Margin-Call und negatives Konto sind weder im Backtest noch im Papier-Bot abgebildet; Margin-Modus, Börsenhebel und Erhaltungsmargin von Yubit sind unbekannt und werden vom Bot nicht gesetzt | Sachverhalt über ENG-02 bestätigt |
| SEC-01 | P0 | hoch | Passwortschutz des Boards ist wirkungslos: derselbe Stand liegt unverschlüsselt im selben öffentlichen Repo | direkt nachgeprüft (Klartext-Stand liegt im Repo) |
| SEC-02 | P0 | hoch | Live-Pfad: Sicherheitsdeckel max_order_usd blockiert auch Schließ-Orders, Position bleibt offen | Sachverhalt über ENG-01 bestätigt |
| ARC-04 | P1 | hoch | Handelsregel, Kontobewertung und Kennzahlen sind mehrfach getrennt implementiert, ohne gemeinsamen Code und ohne Paritätstest | nicht gegengeprüft |
| ARC-05 | P1 | hoch | Verhalten von Test 2 (Stop 5 % / Ziel 15 %) hängt vom Aufruftakt ab, der nicht Teil der Konfiguration ist; die Forschung hat eine andere Regel gerechnet | nicht gegengeprüft; von fünf Prüfern gefunden |
| ARC-06 | P1 | hoch | Kritische Rechenwege der Kennzahlenkette und des Bots haben keinen Test | nicht gegengeprüft |
| ARC-07 | P1 | hoch | Zustandsführung des Bots ist nicht transaktional und hat zwei Wahrheiten (CSV-Protokolle und zustand.json) | nicht gegengeprüft |
| ARC-08 | P1 | mittel | Code, Betriebszustand und Board liegen im selben Arbeitszweig; der Taktgeber liegt außerhalb des Repos; drei widersprüchliche Betriebswege sind definiert | nicht gegengeprüft |
| ARC-09 | P1 | hoch | Der Klartext-Stand liegt im selben öffentlichen Zweig wie der verschlüsselte Board-Stand | direkt nachgeprüft (Klartext-Stand liegt im Repo) |
| ENG-03 | P1 | hoch | Test 2 prüft Stop und Gewinnziel bei jedem Lauf statt am Stundenschluss und misst damit eine andere Regel als Runde 24 | Gegenprüfung abgebrochen; Zahlen beim Wiederholen identisch |
| ENG-04 | P1 | hoch | Tagesverlust-Limit in beiden Tests faktisch aus; die dokumentierte Sicherung von 3 % ist bei Hebel 3 laut Rückrechnung nicht tragfähig | „Limit faktisch aus“ über ENG-02, QD-04 bestätigt |
| ENG-05 | P1 | hoch | Ergebnis hängt am angenommenen Rebate; der Bot bucht es als erzielten Ertrag und zeigt es als Kopfzahl | Sachverhalt über QD-03, QR-02 bestätigt |
| ENG-06 | P1 | mittel | Live-Ausführung: Füllungen werden einmal nach 1,5 Sekunden abgefragt; verspätete Füllungen führen zu Abbruch und unbeaufsichtigter Position | nicht gegengeprüft |
| INF-04 | P1 | hoch | Belegter Vorfall 13:44 bis 15:00 UTC: Auslieferung ohne Prüfung, Skript tauscht sich während des eigenen Laufs aus, jeder Folgefehler bricht die ganze Kette ab | nicht gegengeprüft |
| INF-05 | P1 | hoch | Fehlerbehandlung der Marktabfrage: gängige Verbindungsfehler beenden den ganzen Lauf, Teilausfälle werden still übergangen, keine Wiederholung | nicht gegengeprüft |
| INF-06 | P1 | hoch | Keine Protokollierung, kein Alarm; das Board erkennt einen stehenden Bot nicht | nicht gegengeprüft |
| INF-07 | P1 | mittel | Veröffentlichung über Git: zwei Pushes je Lauf, rund 24 Pages-Builds pro Stunde und etwa 12 MB Repo-Zuwachs pro Tag | nicht gegengeprüft |
| QD-02 | P1 | hoch | Bezeichnung „ungesehener/unabhängiger Prüfzeitraum“ ist für den Kandidaten nicht gerechtfertigt | nicht gegengeprüft |
| QD-05 | P1 | hoch | Kennzahl „größter Einbruch“ (25 % / 31 %) unterschätzt das Risiko eines frisch gestarteten Kontos; „Einsatz 100 %“ ist kein konstantes Engagement | Kern über QR-01, ENG-02 bestätigt |
| QD-06 | P1 | hoch | Kopfzahl des Prüfzeitraums beruht auf einer nach Kenntnis des Ergebnisses geänderten Kostenannahme und reagiert stark auf Ausführungsdetails | nicht gegengeprüft |
| QD-07 | P1 | hoch | 336 Stunden ist im Entwicklungszeitraum eine Spitze, keine Hochebene; die behauptete Robustheit prüft nur denselben Rückblick | nicht gegengeprüft |
| QD-08 | P1 | hoch | Vorwärtstest ohne vorab festgelegte Auswertung; er kann den Vorteil in absehbarer Zeit nicht belegen, und Test 2 entspricht nicht der gerechneten Variante | nicht gegengeprüft; Takt-Teil von fünf Prüfern gefunden |
| QR-02 | P1 | hoch | Das Plus im Prüfzeitraum entsteht allein durch das 85-%-Rebate und hängt an einer Kostenannahme aus einer 60-Minuten-Stichprobe | **bestätigt** (eigene Gegenprüfung) |
| QR-03 | P1 | hoch | Vorteil des Kandidaten statistisch nicht gesichert: Reality Check über die eigene Auswahl nicht bestanden, Prüfzeitraum-Sharpe 0,34 nicht von null unterscheidbar | **bestätigt** (eigene Gegenprüfung) |
| RSK-03 | P1 | hoch | Klumpenrisiko: zehn Positionen sind 1,2 bis 2,5 unabhängige Wetten; in 39 bis 48 % der Stunden stehen alle zehn in derselben Richtung | nicht gegengeprüft; Korrelation von QR und QD nachgerechnet |
| RSK-04 | P1 | hoch | Feste Stückzahl ab Einstieg: Positionswert der Gewinner wächst bis zum 6,5- bis 7-Fachen des Startkapitals, und bei Verlusten wird nie abgebaut | nicht gegengeprüft |
| RSK-05 | P1 | hoch | Test 2: Der Stop von 5 % ist kein Stop an der Börse; er wird nur beim Bot-Lauf mit dem Mittelkurs geprüft und hängt am Taktgeber, an Test 1 und am git push | nicht gegengeprüft; Takt-Teil von fünf Prüfern gefunden |
| RSK-06 | P1 | hoch | Test 2 misst nicht die erforschte Variante, und die Variante selbst ist unbestätigt: in der Vorperiode 2020/21 ist das Konto bei Hebel 3 aufgebraucht | nicht gegengeprüft; Takt-Teil von fünf Prüfern gefunden, Vorperioden-Zahl nur ein Prüfer |
| SEC-03 | P1 | hoch | docs/stand.json: unverschlüsselter Stand liegt weiter im veröffentlichten Ordner | direkt nachgeprüft (Datei liegt im Repo) |
| SEC-04 | P1 | mittel | Schlüsseldatei des Boards: Schutz gegen Offline-Angriff hängt allein am Passwort, kein Schlüsselwechsel möglich | nicht gegengeprüft |
| SEC-05 | P1 | mittel | Regelrisiko Yubit: Bot nur mit Genehmigung, Rebate-Klausel trifft den Kern des Ansatzes, kein Beleg einer Freigabe | nicht gegengeprüft |
| ARC-10 | P2 | hoch | Konfiguration: ungenutzte Schlüssel, fest im Code stehende Werte, kaum Prüfung der Bot-Konfiguration | nicht gegengeprüft (nicht vorgesehen) |
| ARC-11 | P2 | hoch | Stille Annahmen bei Datenlücken und Fehlern; Forschung und Bot behandeln Lücken unterschiedlich | nicht gegengeprüft (nicht vorgesehen) |
| ARC-12 | P2 | hoch | Repo-Hygiene, Dokumentation und Reproduzierbarkeit entsprechen nicht dem tatsächlichen Stand | nicht gegengeprüft (nicht vorgesehen) |
| ENG-07 | P2 | mittel | Funding im Bot: gebucht wird der Ticker-Satz nach dem Termin, multipliziert mit der Zahl verpasster Termine | nicht gegengeprüft (nicht vorgesehen) |
| ENG-08 | P2 | hoch | Teilausfall der Marktdaten: Coin wird übersprungen, Position bleibt, Bewertung mit altem Kurs ohne Kennzeichen | nicht gegengeprüft (nicht vorgesehen) |
| ENG-09 | P2 | hoch | Teilfüllungen werden nicht nachgeführt; Mengenrundung falsch bei Schrittweiten, die keine Zehnerpotenz sind | nicht gegengeprüft (nicht vorgesehen) |
| ENG-10 | P2 | hoch | Vorwärtstest ist kein 1:1-Abbild der Rückrechnung: 23 semantische Unterschiede; Test 1 und Test 2 untereinander nicht direkt vergleichbar | nicht gegengeprüft (nicht vorgesehen) |
| INF-08 | P2 | hoch | Der Papierbetrieb prüft nicht den vorgesehenen Live-Betriebsweg: drei verschiedene Zeitgeber und Konfigurationen im Repo | nicht gegengeprüft (nicht vorgesehen) |
| INF-09 | P2 | hoch | Laufdateien ohne Lauf-Nummer, mit Minutenzeitstempeln und ohne Schutz gegen abgeschnittene Zeilen; fehlender Zustand führt zu stillem Neustart | nicht gegengeprüft (nicht vorgesehen) |
| INF-10 | P2 | mittel | Im veröffentlichten Ordner docs/ liegen ein veralteter Klartext-Stand und sechs fremde Dokumente; die Laufdaten stehen zusätzlich unverschlüsselt im öffentlichen Repo | teilweise direkt nachgeprüft (docs/stand.json) |
| INF-11 | P2 | hoch | Umgebung und Daten nur teilweise reproduzierbar: keine Sperrdatei für Abhängigkeiten, keine automatischen Tests, Marktdaten ohne Prüfsummen und teils nicht wiederbeschaffbar | nicht gegengeprüft (nicht vorgesehen) |
| QD-09 | P2 | mittel | Alle Coin-Gruppen enthalten nur Überlebende; Gruppe A wurde im Rückblick festgelegt | nicht gegengeprüft (nicht vorgesehen) |
| QD-10 | P2 | hoch | Reality Check ist richtig umgesetzt, wurde aber nie auf die Auswahl des Kandidaten angewendet und ist ohne Studentisierung für eng verwandte Varianten kaum trennscharf | nicht gegengeprüft (nicht vorgesehen) |
| QR-04 | P2 | mittel | Rückrechnung unterstellt Ausführung exakt zur vollen Stunde; im Prüfzeitraum kosten schon fünf Minuten Verzögerung ein Drittel des Ergebnisses | nicht gegengeprüft (nicht vorgesehen) |
| QR-05 | P2 | hoch | Papier-Test 2 prüft Stop und Ziel bei jedem Durchlauf (etwa alle fünf Minuten), die Rückrechnung der Runde 24 nur am Stundenschluss: der Test misst eine andere Regel | nicht gegengeprüft; von fünf Prüfern gefunden |
| QR-06 | P2 | hoch | Fünf fehlende Kerzentage bei 30 von 72 Coins (in Gruppe A: SOL, XRP, LTC) bleiben unbemerkt und verschieben das D1-Ergebnis | nicht gegengeprüft (nicht vorgesehen) |
| QR-07 | P2 | hoch | „+59 % pro Jahr“ und „+16,5 % pro Jahr“ sind Summen ohne Zinseszins bei fester Größe am Startkapital; als Wachstumsrate gelesen sind sie zu hoch | nicht gegengeprüft (nicht vorgesehen) |
| RSK-07 | P2 | mittel | Wiedereinstieg nach dem Stop: Das Signal dreht rund 200-mal je Coin und Jahr; der Stop begrenzt den Summenverlust nicht | nicht gegengeprüft (nicht vorgesehen) |
| RSK-08 | P2 | hoch | Es gibt keinen geprüften Verlustbegrenzer auf Kontoebene: Tageslimit in den Tests faktisch aus, in der Forschung bei Hebel über 0,5 schädlich, im Bot mit Lücke über Nacht | nicht gegengeprüft (nicht vorgesehen) |
| RSK-09 | P2 | mittel | Funding trifft die Strategie einseitig: Long zahlt deutlich mehr, als Short erhält; in heißen Phasen bis 45 Punkte des Startkapitals in 30 Tagen bei Hebel 3 | nicht gegengeprüft (nicht vorgesehen) |
| RSK-10 | P2 | mittel | Einzelne Coins laufen binnen einer Stunde 25 bis 49 % gegen die Position; die Datenbasis (letzter Preis Binance) enthält Ausreißer, ein Mark-Preis fehlt | nicht gegengeprüft (nicht vorgesehen) |
| RSK-11 | P2 | mittel | Live-Pfad: Nach einer Zwangsschließung an der Börse stellt der Bot den Handel für alle Coins ein und lässt die übrigen Positionen ungeführt | nicht gegengeprüft (nicht vorgesehen) |
| SEC-06 | P2 | hoch | Board lädt fremdes Skript ohne Integritätsprüfung vor der Passworteingabe; abgeleiteter Schlüssel dauerhaft in localStorage | nicht gegengeprüft (nicht vorgesehen) |
| SEC-07 | P2 | mittel | Betriebsmodell: Code und Grenzwerte kommen bei jedem Lauf ungeprüft aus dem öffentlichen Zweig | nicht gegengeprüft (nicht vorgesehen) |
| SEC-08 | P2 | hoch | live_server.py lauscht auf allen Schnittstellen ohne Anmeldung und ohne TLS | nicht gegengeprüft (nicht vorgesehen) |
| SEC-09 | P2 | mittel | Daten eines fremden Signal-Dienstes im öffentlichen Repo | nicht gegengeprüft (nicht vorgesehen) |
| SEC-10 | P2 | hoch | Lieferkette: nur 8 von 89 Paketen festgeschrieben, ungenutztes freqtrade bringt 70 Pakete mit | nicht gegengeprüft (nicht vorgesehen) |
| ENG-11 | P3 | hoch | Kleinere Unstimmigkeiten in Beschriftung und Anzeige (Sammelbefund) | nicht gegengeprüft (nicht vorgesehen) |
| INF-12 | P3 | hoch | Live-Server lauscht ohne Zugriffsschutz auf allen Netzwerkschnittstellen und fragt die Börse alle 3 Sekunden ab | nicht gegengeprüft (nicht vorgesehen) |
| QD-11 | P3 | hoch | Zählung „127 Einzelhypothesen, 602 Varianten“ stimmt mit dem Protokoll, erfasst aber nicht alle Auswertungen auf denselben Daten | nicht gegengeprüft (nicht vorgesehen) |
| QD-12 | P3 | hoch | Rechenkonventionen stehen nicht im Protokoll; einzelne Unterlagen widersprechen dem Stand | nicht gegengeprüft (nicht vorgesehen) |
| QR-08 | P3 | hoch | Regeltext „sonst Short“ stimmt nicht mit dem Code: bei Gleichstand und bei fehlenden Kursen ist die Position glatt | nicht gegengeprüft (nicht vorgesehen) |
| SEC-11 | P3 | hoch | Yubit-Client folgt Weiterleitungen und reicht signierte Kopfzeilen an fremde Hosts weiter; Schema der Basisadresse ungeprüft | nicht gegengeprüft (nicht vorgesehen) |
| SEC-12 | P3 | hoch | Kleinere Punkte: Sitzungsadresse in Commit-Nachrichten, mitveröffentlichte Fremddokumente, Schlüssel auf der Kommandozeile, Entpacker, systemd | nicht gegengeprüft (nicht vorgesehen) |

## 3. Unabhängig bestätigte Probleme

### Mit eigener Gegenprüfung bestätigt (8 von 8, keiner widerlegt)

Jeder Gegenprüfer hatte den Auftrag, den Befund zu widerlegen, und rechnete mit eigenem Code. Wo der Erstprüfer
überzeichnet hatte, steht die Korrektur dabei.

| Befund | Bestätigte Kernzahlen | Korrektur des Gegenprüfers |
|---|---|---|
| **QR-01** Einbruch gilt nicht für Hebel 3 | Jeder Kalendertag einzeln als Start gerechnet, Hebel 3: Konto fällt auf null bei 14,6 % der Starttage (Entwicklung) und 10,7 % (Prüfzeitraum). Bei Hebel 2: 0,1 %. Bei Hebel 1: nie. | Die Totalverluste entstehen über Wochen (im Median 113 bis 141 Tage), nicht an einem Tag. „89 % Verlust an einem Tag“ meint 0,89 Startkapital, nicht 89 % des damaligen Kontos. |
| **QD-04** Hebel 3 ohne Limit nie gerechnet | Wöchentliche Starts: Konto mindestens halbiert bei 47 %, auf null bei 16 %. Der unveränderte Bot, gegen alte Kurse nachgespielt, fällt ab Start 20.07.2025 nach 75 Tagen unter null und eröffnet danach 516 weitere Positionen. | Das sind Häufigkeiten aus fünf bis sechs Episoden einer einzigen Historie, keine Wahrscheinlichkeit. Ein durchgehender Lauf ab 08/2021 wäre nicht ruiniert worden. Das Limit von 3 % wieder einzuschalten löst nichts (bei Hebel 3: −101 % pro Jahr). Test 2 fällt seltener auf null (3 bis 4 % der Starts), aber auch. |
| **ENG-02** Kein Margin-Modell | Horizont 365 Tage, Hebel 3: Konto auf null bei 8,4 % der Starttage mit Rebate, 46,5 % ohne. Bot-Versuch: zehn Shorts, Kurse +40 %, Konto bei −1.076 $, der Bot handelt weiter. | Die Einbruchs-Anzeige im Board ist für ein frisch gestartetes Konto korrekt; sie unterschätzt nur nach aufgelaufenen Gewinnen. |
| **QD-01** Vorteil nicht gesichert | Prüfzeitraum: t = 0,42; in 32 % der Zufallsziehungen kein Gewinn. Entwicklung: t = 1,80. Nach Korrektur für die Auswahl liegt der p-Wert zwischen 0,07 und 0,22 und nie unter 0,05. | keine |
| **QR-03** Auswahl-Prüfung nicht bestanden | Über die 32 Einstellungen, aus denen der Kandidat stammt: p = 0,09 bis 0,47. Ohne die fünf besten von 571 Tagen wäre der Prüfzeitraum bei −25,4 %. | keine |
| **QD-03** Plus stammt aus dem Rebate | Prüfzeitraum, Hebel 1: vor Gebühr +33,9 %, Gebühr 53,4 %, Rebate 45,4 %. Netto mit Rebate +25,8 %, ohne −19,6 %. | Die Abhängigkeit ist kein versteckter Fehler; sie war Suchziel und steht im Entwicklerbericht. Über die gesamte Historie ist die Regel auch ohne Rebate positiv (+94 %, Sharpe 0,31), aber nicht gesichert. |
| **QR-02** Kostenannahme aus einer Stunde | Das Rebate muss mindestens 36,6 % betragen, damit der Prüfzeitraum nicht negativ wird; bei pauschal 0,05 % Kosten 62,1 %. Im Live-Zweig bucht der Bot kein Rebate und kann es nicht abfragen. | keine |
| **ENG-01** Deckel blockiert Schließen | Bei Deckel 2.000 $ und Position 1.500 $ genügt ein Kursanstieg von rund 33 %. | Betroffen sind auch Long-Positionen im Gewinn, und zwar häufiger: 46 von 7.467 Ausstiegen in der Entwicklung. |

### Ohne Agent direkt nachgeprüft (beim Schreiben dieses Berichts)

- `docs/stand.json` liegt im veröffentlichten Ordner (SEC-03). Die Datei wurde am 15.11. um 13:41 UTC gelöscht und
  drei Minuten später von einem noch laufenden Bot-Durchlauf mit dem alten Skript wieder angelegt. Sie zeigt den
  Papier-Stand von 13:44 UTC. Ob GitHub Pages sie tatsächlich ausliefert, wurde nicht über das Netz geprüft.
- Der unverschlüsselte Stand `dashboard.json` liegt unter `vorwaertstest/lauf/` und `lauf_tpsl/` im selben Repo
  (SEC-01).
- Der Bot läuft rund alle 5 Minuten (INF-01): Commits um 20:38, 20:43, 20:49 und 20:53 UTC.
- Die 46 Tests, die drei Prüfer hinterlassen haben, laufen grün (Abschnitt 6).

### Von mehreren Prüfern unabhängig gefunden, aber ohne eigene Gegenprüfung

- Takt-Abweichung von Test 2: fünf Prüfer (ENG, QR, ARC, RSK, QD). Die abgebrochene Gegenprüfung hatte die Tabelle
  des Erstprüfers bereits mit identischen Zahlen wiederholt, ein eigenes Urteil fehlt.
- Klartext-Stand im öffentlichen Repo: drei Prüfer (SEC, ARC, INF).
- Fehlendes Margin-Modell und Hebel 3: vier Prüfer (ENG, RSK, ARC, QD), über ENG-02 und QD-04 bestätigt.

### Was die Prüfung als richtig bestätigt hat

- Die Kernzahlen stimmen mit den Projektmodulen auf die letzte Stelle und mit unabhängigen Rechnungen auf unter 2 %.
  Nur die erste Halbzeit weicht um 5 % ab; das erklären fünf fehlende Kerzentage bei drei Coins.
- Kein Blick in die Zukunft in 34 geprüften Signalfunktionen und im Rechenkern (Störungstest).
- Forschung und Bot setzen dieselbe Signalregel um: gleiche Richtung in 463.680 von 464.400 Coin-Stunden, der Rest
  sind Datenlücken.
- Kontorechnung des Papier-Bots: Zustand, Protokoll, Verlauf, Dashboard-Daten und Browser-Formel stimmen überein.
- Die Zahlen im Protokolltext stimmen mit den gespeicherten Ergebnisdateien überein (47 von 47 Stichproben).
- Keine Zugangsdaten in 144 Commits und 922 Dateiständen.
- Die drei Schranken vor echten Orders wirken in allen 28 getesteten Kombinationen. Ein Weg zu versehentlichem
  Echtgeld-Handel wurde nicht gefunden.
- Die 105 bestehenden Tests sind grün.

### Nicht reproduziert oder ungeklärt

- Die Runden 10 bis 20 und 23 wurden nicht nachgerechnet; dort wurden nur Protokoll und Ergebnisdateien verglichen.
- Rebate-Satz, Taker-Gebühr, Bot-Genehmigung, Margin-Modus und Liquidationsregeln von Yubit: im Repo kein Beleg.
- Wie stark Yubit-Kurse von den Binance-Kursen der Forschung abweichen: keine Yubit-Historie vorhanden.
- Ob jedes Protokoll vor der ersten Rechnung geschrieben wurde: aus Git allein nicht beweisbar, die Commits liegen
  teils unter zwei Minuten auseinander.
- Ursache von fünf fehlenden Kerzentagen bei SOL, XRP und LTC im Februar und April 2022 (QR-06, Wirkung klein).
- Verhalten des Live-Pfads gegen die echte Yubit-Schnittstelle: nie gelaufen, nur mit nachgestellter Börse geprüft.

## 4. Offene Prüfungen und ihre Bedeutung

| Offene Prüfung | Stand | Bedeutung |
|---|---|---|
| Gegenprüfung ENG-03 (Takt von Test 2) | abgebrochen | gering. Der Sachverhalt steht im Code, fünf Prüfer fanden ihn, die Zahlen wurden wiederholt. |
| Gegenprüfung RSK-01 (Hebel 3) | abgebrochen | gering. Derselbe Sachverhalt ist über QR-01, QD-04 und ENG-02 dreifach bestätigt. |
| Gegenprüfung RSK-02, RSK-03 | nicht begonnen | gering. RSK-02 deckt sich mit ENG-02; die Korrelationszahlen zu RSK-03 haben QR und QD nachgerechnet. |
| Gegenprüfung ARC-01 bis ARC-03 | nicht begonnen | gering. Inhaltlich Dopplungen von A, B und E. |
| Gegenprüfung SEC-01 bis SEC-03 | nicht begonnen | gering. SEC-01 und SEC-03 sind direkt nachgeprüft, SEC-02 deckt sich mit ENG-01. |
| Gegenprüfung INF-02, INF-03 | nicht begonnen | mittel. Nur vom Erstprüfer in einer Sandbox nachgestellt. Betrifft die Verlässlichkeit der laufenden Papier-Daten, kein Geld. |
| Gegenprüfung der übrigen P1-Befunde | nicht vorgesehen oder nicht begonnen | gering bis mittel. Am wichtigsten wäre RSK-06 (Stop-Variante in der Vorperiode −40,5 %): eine neue Zahl von nur einem Prüfer. |
| Eigene Regressionstests (drei Testautoren) | nicht begonnen | gering. Drei Prüfer haben bereits 46 lauffähige Tests zum Ausgangsverhalten geschrieben. Weitere Tests sind erst nötig, wenn kritischer Code geändert wird. |
| Sechs Einzelberichte und Roadmap | nicht erstellt | keine inhaltliche. Alle Inhalte liegen in den Rohdaten und in diesem Bericht. |
| Vollständigkeitsprüfung | nicht begonnen | gering. Lücken sind in diesem Abschnitt von Hand benannt. |

## 5. Was zwingend erforderlich ist und was entfallen kann

### Zwingend, aber ohne Agenten zu erledigen

1. **Anfrage bei Yubit, schriftlich** (vor jedem Echtgeld-Schritt). Gilt das Rebate von 85 % für Taker-Umsatz eines
   Bots, wie und wann wird es gutgeschrieben, ist ein stündlich laufendes Programm erlaubt, welcher Margin-Modus und
   welche Liquidationsregeln gelten? Ohne diese Antwort sind alle Kennzahlen „mit Rebate“ keine
   Entscheidungsgrundlage. Kosten: eine Nachricht.
2. **Entscheidung des Auftraggebers zum Hebel der Papier-Tests.** Hebel 3 ist nie gerechnet worden, und die Historie
   enthält Totalverluste. Die Tests laufen unverändert weiter, bis der Auftraggeber entscheidet. Ohne Eingriff
   möglich: vorab festhalten, dass ein Test als gescheitert gilt, sobald das Papier-Konto null erreicht, weil alles
   danach an einer echten Börse nicht erzielbar wäre.
3. **Auswertung des Vorwärtstests vorab festlegen** (eine Seite): Zweck, Laufzeit, Abbruchgrenzen. Realistischer
   Zweck ist das Messen von Kosten, Füllungen, Funding und der Abweichung zur Rückrechnung, nicht der Beweis des
   Vorteils. Gewinn oder Verlust einiger Wochen belegt nichts.
4. **Entscheidung zu Test 2.** Entweder als das führen, was er ist (Prüfung alle 5 Minuten, eigene ungeprüfte
   Variante), oder den Takt angleichen. Das Angleichen ändert einen laufenden Test und geschieht nur auf
   ausdrücklichen Wunsch.
5. **Nur falls Echtgeld geplant wird:** Live-Pfad reparieren und testen (Schließen trotz Deckel, Füllungen,
   Speicherreihenfolge), Margin- und Liquidationsmodell ergänzen, überwachten Zeitgeber einrichten. Bis dahin kann
   das vollständig ruhen.

### Kann entfallen

- **Die restlichen Gegenprüfungen.** Sie betreffen fast nur Dopplungen bereits bestätigter Sachverhalte oder Dinge,
  die direkt im Repo sichtbar sind. Erwarteter Erkenntnisgewinn klein.
- **Die sechs Einzelberichte, die Roadmap und die Vollständigkeitsprüfung.** Sie würden ein Mehrfaches dieses
  Berichts kosten und keine neue Tatsache liefern.
- **Weitere Statistik auf der vorhandenen Historie.** Sie kann das Ergebnis nicht mehr ändern. Neue Evidenz kommt
  nur aus neuen Daten: dem Vorwärtstest und der Antwort von Yubit.
- **Weitere Testautoren.** Erst sinnvoll zusammen mit einer konkreten Code-Änderung.
- **Schwachstellen-Prüfung der Pakete, Next.js-Anwendung.** Für die Papier-Phase ohne Belang.

### Günstig und sinnvoll, aber nur auf ausdrücklichen Wunsch

Jeder dieser Punkte berührt das Dashboard oder die laufenden Tests und wurde deshalb nicht angefasst.

- `docs/stand.json` aus dem veröffentlichten Ordner entfernen (ein Befehl; betrifft nur die alte Klartextdatei,
  nicht das Board).
- Den Bot auf stündlichen Takt bringen, wie dokumentiert. Das senkt Kosten und Repo-Wachstum, ändert aber, was Test 2
  misst.
- Den Bot aus der KI-Sitzung auf einen festen Zeitplan umziehen.

## 6. Korrekturen an früheren Aussagen

Diese Formulierungen aus `reports/uebergabe_fuer_dritte.md` und aus früheren Kurzmeldungen sind nach dem Audit zu
stark. Dort steht jetzt ein Hinweis auf diesen Bericht.

| Bisherige Aussage | Zutreffend ist |
|---|---|
| „Ein einziger Baustein hält der Prüfung stand“, „belegt“ | In der Entwicklung positiv und richtig gerechnet, aber statistisch nicht gesichert. |
| „Ungesehener Prüfzeitraum“ | In Runde 3 einmal als Hürde benutzt, davor bekannt, seither vielfach eingesehen. Unabhängig sind nur Daten ab 24.10.2026 und der Papier-Test. |
| „+16,5 % pro Jahr“ im Prüfzeitraum | Gilt mit 85 % Rebate und nachträglich gemessenen Kosten. Mit der vorab festgelegten Kostenannahme +7,8 %, ohne Rebate −12,5 % pro Jahr. |
| „+59 % pro Jahr“ | Summe ohne Zinseszins bei fester Größe am Startkapital, Hebel 1. Als Wachstumsrate gelesen zu hoch. |
| „Größter Einbruch 25 % / 31 %“ | Gilt für Hebel 1, gemessen am gewachsenen Konto. Am Startkapital gemessen 50 bis 57 %, bei Hebel 3 das Dreifache. |
| „Robust gegen die Bauart“ | Nur für andere Trend-Maße mit demselben Rückblick von 336 Stunden. Benachbarte Rückblicke sind deutlich schwächer. |
| Test 2 entspricht der Variante mit Sharpe 1,13 aus Runde 24 | Der Bot prüft alle 5 Minuten statt am Stundenschluss. Das ist eine andere, nicht gerechnete Regel. |
| Die alte Klartextdatei im Board-Ordner sei entfernt | Sie wurde drei Minuten später vom Bot wieder angelegt und liegt noch dort. |

## 7. Offenlegung zum Audit selbst

- **Prüfzeitraum für die Stop-Variante eingesehen.** Der Risiko-Prüfer und zwei Gegenprüfer haben Test 2 (Stop 5 %,
  Ziel 15 %) auch im Prüfzeitraum ab 04/2025 gerechnet, um das Risiko zu messen. Laut Protokoll war dieser Zeitraum
  für diese Variante bis dahin unberührt. Es wurde nichts ausgewählt oder angepasst, aber der Zeitraum taugt für
  diese Variante nicht mehr als unabhängige Bestätigung.
- **Nichts wurde verändert.** Handelsregel, Konfigurationen, Daten der laufenden Tests, Bot-Code und Dashboard sind
  unberührt. Das Audit hat nur unter `swing-hybrid/reports/audit/` geschrieben, dazu den Hinweis im Übergabebericht.
- **Audit-Commits liegen auf dem Zweig des Bots.** Das ist genau das Risiko aus Sachverhalt G. Dieser Bericht wurde
  deshalb unmittelbar nach einem abgeschlossenen Bot-Lauf gepusht, nicht während eines Laufs.
- **Aufwand.** 17 Agenten liefen (7 Bereichsprüfer, 8 fertige und 2 abgebrochene Gegenprüfer), gut zwei Stunden.

## 8. Ablage

Alles liegt unter `swing-hybrid/reports/audit/`.

| Pfad | Inhalt |
|---|---|
| `zwischenbericht.md` | dieser Bericht |
| `befunde_vollstaendig.md` | alle 78 Befunde mit Evidenz, Auswirkung, Empfehlung und Befehl zum Nachstellen; je Bereich die nachgerechneten Aussagen und offenen Punkte; alle acht Gegenprüfungen im Wortlaut |
| `rohdaten/bereich_*.json`, `rohdaten/pruefung_*.json` | unveränderte Ergebnisse der 7 Bereichsprüfer und 8 Gegenprüfer |
| `evidence/<Bereich>/` | Skripte und Ausgaben der Prüfer, 163 Dateien |
| `evidence/V-*/` | Skripte und Ausgaben der Gegenprüfer, 97 Dateien |
| `evidence/V-ENG-03_abgebrochen/`, `evidence/V-RSK-01_abgebrochen/` | Teilergebnisse der beiden abgebrochenen Gegenprüfungen, ohne Urteil |

Die 46 Tests zum Ausgangsverhalten (18 Trading Engine, 12 Risiko, 16 Betrieb) laufen so:

```
cd swing-hybrid
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest -q -p no:cacheprovider \
  reports/audit/evidence/ENG/test_eng_ausgangsverhalten.py \
  reports/audit/evidence/RSK/test_rsk_risiko.py \
  reports/audit/evidence/INF/test_inf_betrieb.py
```

Stand 15.11.2026: 46 bestanden. Sie schreiben nicht in die Daten der laufenden Tests.
