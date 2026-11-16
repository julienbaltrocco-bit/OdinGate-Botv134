# Audit OdinGate: alle Befunde im Wortlaut

Automatisch aus `rohdaten/*.json` erzeugt (Stand 15.11.2026). Der Text stammt unverändert von den Prüfern. Die Einordnung und die Korrekturen der Gegenprüfer stehen in `zwischenbericht.md`. Wo ein Gegenprüfer einen Erstprüfer korrigiert hat, gilt die Gegenprüfung.

Umfang: 78 Befunde, 8 abgeschlossene Gegenprüfungen.

## Bereich QD: Quantitative Research

Die Rückrechnung des Kandidaten ist technisch sauber und vollständig reproduzierbar: +59 %/Jahr bei Sharpe 0,95 (Entwicklung) und +16,5 %/Jahr bei Sharpe 0,34 (Prüfzeitraum) habe ich mit den Projektmodulen exakt und mit einer eigenen, unabhängigen Rechnung nachvollzogen; ein Blick in die Zukunft fand sich in keiner von 34 geprüften Signalfunktionen und nicht im Rechenkern. Die Zahlen gehören zu Gruppe A, Einsatz 100 % (Hebel 1), ohne Tageslimit, Yubit-Slippage aus einer Ein-Stunden-Stichprobe und 85 % Rebate; mit der vorab festgelegten Annahme von 5 bp waren es im Prüfzeitraum nur +7,8 %/Jahr bei Sharpe 0,16. Statistisch ist der Vorteil nicht gesichert: Im Prüfzeitraum ist t = 0,42, und nach Korrektur für die Auswahl aus den zehn Einstellungen der Runde 3 ist auch die Entwicklung nicht signifikant (p 0,07 bis 0,19). Ohne Rebate hat der Kandidat im Prüfzeitraum 12,5 %/Jahr verloren. Die Bezeichnung „ungesehener Prüfzeitraum“ ist nicht haltbar: Der Zeitraum war vor der Suche für Trend-Strategien auf denselben Coins bekannt, diente in Runde 3 als Hürde und wurde seither in 22 Ergebnisdateien eingesehen. Die laufenden Papier-Tests fahren Hebel 3 ohne Tageslimit, was nie gerechnet wurde; in meiner Neustart-Simulation fällt das Konto von 47 % der Starttage aus binnen eines Jahres um mindestens die Hälfte und von 16 % aus auf null.

### Befunde

#### QD-01 (P0): Vorteil des Kandidaten ist statistisch nicht gesichert, nach Auswahl-Korrektur auch in der Entwicklung nicht

- **Sicherheit des Prüfers:** hoch
- **Stand:** **bestätigt** (eigene Gegenprüfung)
- **Evidenz:** evidence/QD/statistik_kandidat.txt: Prüfzeitraum 571 Tage, +16,5 %/Jahr, Sharpe 0,337, t = 0,42; 90-%-Band (stationärer Bootstrap, 10.000 Ziehungen) Sharpe −0,83 bis +1,43, Ertrag −38 % bis +73 %/Jahr; 31 % der Ziehungen mit Mittel ≤ 0. Entwicklung: t = 1,80, Band Sharpe 0,13 bis 1,73. Zufallstest des Projekts nur im Prüfzeitraum: Perzentil 80,5 bei eigener Hürde 90 (reports/kandidat.json zufall_pruefung.perzentil = 80.5; mit Yubit-Kosten nachgerechnet ebenfalls 80,5; reports/suche_bericht.md:100 nennt das selbst „statistisch nicht gesichert“). evidence/QD/reality_check_2.txt: Auswahl des Kandidaten als Bester von 10 Trend-Einstellungen (scripts/suche_runde3.py:54), Entwicklung: p ohne Korrektur 0,071 (5 bp) bzw. 0,042 (Yubit-Kosten); White's Reality Check über die 10 mit der Projektfunktion 0,123 bzw. 0,074; Hansen SPA 0,188 bzw. 0,126.
- **Auswirkung:** Eine Entscheidung für echtes Geld, die +16,5 %/Jahr und Sharpe 0,34 als belegten Vorteil behandelt, stützt sich auf eine Zahl, die von null nicht zu unterscheiden ist. Der wahre Ertrag je Risiko kann null oder negativ sein.
- **Empfehlung:** In allen Unterlagen (uebergabe_fuer_dritte.md, Board-Texte) als „nicht gesichert“ führen und das Band mit angeben. Keine Echtgeld-Entscheidung auf Basis der Rückrechnung; jede Positionsgröße so wählen, dass ein wahrer Sharpe von 0 verkraftbar ist. Auswahl-Korrektur (Reality Check oder SPA über die Auswahlrunde) als Pflichtteil jeder künftigen Kandidatenwahl im Protokoll festlegen.
- **Nachstellen:** cd /home/user/OdinGate-Botv134/swing-hybrid && .venv/bin/python -I reports/audit/evidence/QD/statistik.py && .venv/bin/python -I reports/audit/evidence/QD/reality2.py

#### QD-03 (P0): Der gesamte Ertrag im Prüfzeitraum stammt aus dem 85-%-Rebate; ohne Rebate Verlust

- **Sicherheit des Prüfers:** hoch
- **Stand:** **bestätigt** (eigene Gegenprüfung)
- **Evidenz:** evidence/QD/repro_kandidat.txt (Hebel 1, Yubit-Kosten, ohne Tageslimit): Prüfzeitraum netto +25,8 %, darin Rebate +45,4 %; ohne Rebate −19,6 % (−12,5 %/Jahr, Sharpe −0,25). Entwicklung ohne Rebate +113,8 % statt +215,6 %, Sharpe 0,50 statt 0,95 (t = 0,95). Mit der alten 5-bp-Annahme ohne Rebate: Prüfzeitraum −33,2 %. vorwaertstest/YUBIT_REGELN.md:19–27: Yubit verbietet Rebate-Arbitrage und kann Rebate abziehen; „Sein Gewinn stammt aber überwiegend aus dem Rebate“. reports/hybrid_report.md:207: Rebate als sofortige Gutschrift gerechnet, Bedingungen nicht berücksichtigt. vorwaertstest/bot.py:245: im Live-Modus „rebate = 0.0 … hier nicht sichtbar“, im Papier-Modus werden 85 % sofort gutgeschrieben.
- **Auswirkung:** Wird das Rebate gekürzt, verzögert oder einbehalten, hat die Strategie in den letzten 19 Monaten Geld verloren. Die Rentabilität hängt an einer Vertragsbedingung, die sich aus dem Repo nicht prüfen lässt.
- **Empfehlung:** Rebate-Vereinbarung schriftlich klären (Höhe, Gültigkeit für Taker-Volumen und Bot-Handel, Auszahlungsrhythmus, Verhältnis zur Rebate-Arbitrage-Klausel). Alle Kennzahlen und das Board immer zusätzlich ohne Rebate ausweisen. Live-Start nur mit bestätigtem Vertrag.
- **Nachstellen:** cd /home/user/OdinGate-Botv134/swing-hybrid && .venv/bin/python -I reports/audit/evidence/QD/repro1.py   # Spalten ohne_rebate_N und sharpe_ohne_rebate

#### QD-04 (P0): Papier-Tests laufen mit Hebel 3 ohne Tageslimit; diese Konfiguration wurde nie gerechnet und widerspricht der eigenen Hebel-Regel (0,2)

- **Sicherheit des Prüfers:** hoch
- **Stand:** **bestätigt** (eigene Gegenprüfung)
- **Evidenz:** vorwaertstest/config_lauf.json:4 „hebel": 3.0“, :17 „tagesverlust_limit": 1.0“ (ebenso config_lauf_tpsl.json). Forschung: regelkonformer Hebel 0,2 (scripts/suche_runde3.py:100–104, suche_runde3.json 5_hebel.hebel = 0.2); Hebel 3 nur mit 3-%-Tageslimit gerechnet (reports/diagnose_kapital.json: Entwicklung −101 %/Jahr). Eigene Rechnung, evidence/QD/statistik_kandidat.txt und hebel3_engagement_delisting.txt: Hebel 3 ohne Limit, Einbruch relativ zum Höchststand 38 % (Entwicklung) und 56 % (Prüfzeitraum); größter Rückgang 171 % bzw. 163 % des Startkapitals. Neustart-Simulation mit fester Positionsgröße wie im Bot (267 Starttage, 5-Minuten-Werte, evidence/QD/neustart_hebel3.csv): Kontotief binnen 365 Tagen ≤ −50 % bei 47 %, ≤ −75 % bei 32 %, ≤ −100 % bei 16 % der Starts; Starts im Prüfzeitraum (soweit Daten reichen) 45 % / 31 % / 13 %. vorwaertstest/dashboard_live.html:133 räumt ein, ein solcher Einbruch „hätte das Konto fast aufgebraucht“.
- **Auswirkung:** Mit echtem Geld wäre von etwa jedem sechsten Starttag aus binnen eines Jahres ein Totalverlust eingetreten (ohne Liquidationsregeln gerechnet, real also früher). Das Ergebnis der Papier-Tests wird vom Hebel bestimmt, nicht vom Signal.
- **Empfehlung:** Hebel vor jedem Echtgeld-Einsatz aus einer vorab festgelegten Verlustgrenze ableiten und mit Neustart-Simulation belegen. Papier-Test parallel auf den regelkonformen Hebel umrechnen (bei fester Positionsgröße linear möglich). Liquidations- und Margin-Logik der Börse in die Rückrechnung aufnehmen. Details gehören in den Bereich Risk Engineering.
- **Nachstellen:** cd /home/user/OdinGate-Botv134/swing-hybrid && .venv/bin/python -I reports/audit/evidence/QD/hebel3.py

#### QD-02 (P1): Bezeichnung „ungesehener/unabhängiger Prüfzeitraum“ ist für den Kandidaten nicht gerechtfertigt

- **Sicherheit des Prüfers:** hoch
- **Stand:** nicht gegengeprüft
- **Evidenz:** reports/uebergabe_fuer_dritte.md:25 „Ungesehener Prüfzeitraum 04/2025–10/2026 | +16,5 % | 0,34“, :47 „je Idee höchstens einmal“. (1) Vor der Suche bekannt: reports/hybrid_report.md:50 und :68 werten 19.04.2025 bzw. 14.07.2025 bis 23.10.2026 für zwei Trend-Strategien auf denselben 10 Coins aus (18 Einstellungen, :14), :181 „trail_beide hat seit April 2025 kaum verdient“; reports/suche_bericht.md:36 beschreibt den Kandidaten als „dein Tagestrend (momentum_vol_ls), nur stündlich nachgeführt und mit kürzerer Länge“. Commit 68db371 (14.11. 10:49) liegt vor dem Suchprotokoll 8682d30 (12:40). (2) In Runde 3 Hürde für zwei Finalisten (scripts/suche_runde3.py:54 und :80): tsmom_L96 fällt mit −112 % durch, tsmom_L336 besteht; das Ergebnis ist also auf Bestehen bedingt. (3) Danach: 22 JSON- und 3 CSV-Dateien in reports/ enthalten Prüfzeitraum-Zahlen (evidence/QD/pruefzeitraum_einsichten.txt); 16 der 127 gezählten Hypothesen, alle 602 Massentest-Varianten (suche_runde11_alle.csv: 2.408 Zeilen mit fenster = Pruefung, 602 Regeln) und 7 Rückblicke (diagnose_frequenz.csv) wurden dort gerechnet. Das Protokoll sagt es selbst: Zeile 164 „alle frischen Daten verbraucht“, 192 „nicht mehr ganz unberührt“, 1055 „Ich kenne den Verlauf des Kandidaten in allen Zeiträumen“.
- **Auswirkung:** Dritte lesen die Zahl als unabhängigen Beleg. Tatsächlich war der Zeitraum für die Strategiefamilie vorab bekannt, diente als Filter und wurde nachträglich mit geänderter Kostenannahme neu ausgewiesen (siehe QD-06).
- **Empfehlung:** Umbenennen in „Prüfzeitraum, in Runde 3 einmal als Hürde benutzt, seither vielfach eingesehen“. Als unabhängig nur Daten ab 24.10.2026 bzw. den Papier-Test ab 15.11.2026 werten. Keine weitere Auswahl oder Wertung auf 04/2025–10/2026; ein Register aller Einsichten in diesen Zeitraum führen.
- **Nachstellen:** cd /home/user/OdinGate-Botv134/swing-hybrid && .venv/bin/python -I reports/audit/evidence/QD/pruefzeitraum_einsichten.py; git log --format='%h %ad %s' --date=iso -- reports/hybrid_report.md reports/suche_protokoll.md | tail -8

#### QD-05 (P1): Kennzahl „größter Einbruch“ (25 % / 31 %) unterschätzt das Risiko eines frisch gestarteten Kontos; „Einsatz 100 %“ ist kein konstantes Engagement

- **Sicherheit des Prüfers:** hoch
- **Stand:** Kern über QR-01, ENG-02 bestätigt
- **Evidenz:** src/hybrid/runner.py:79–83 misst den Einbruch relativ zum Höchststand von 1 + kumuliertem Gewinn, während die Positionsgröße fest am Startkapital hängt (src/hybrid/engine2.py:88, S = hebel / Coins). evidence/QD/statistik_kandidat.txt, Hebel 1: Entwicklung 25,8 % relativ = 0,569 Einheiten des Startkapitals absolut; Prüfzeitraum 33,1 % = 0,543. Neustart bei Hebel 1 (aus neustart_hebel3.csv, Drittel): 32 % der Starts verlieren binnen 365 Tagen ≥ 25 %, 16 % ≥ 33 %, schlechtester Start −48 % (05.02.2023). evidence/QD/hebel3_engagement_delisting.txt (a): Brutto-Engagement im Mittel 1,02, 95-%-Wert 1,32, Maximum 2,18 × Startkapital (03.12.2024), weil die Stückzahl beim Einstieg fixiert wird; schlechtester Tag −29,7 % des Startkapitals am 09.12.2024 bei Engagement 2,10 und Kontostand 3,31. Drei Einbruch-Definitionen: 5-Minuten-Werte (runner.max_drawdown, Runden 3–9), Tageswerte mit Boden 1 (src/hybrid/tagestrend.py:67–69), Tageswerte ohne Boden (scripts/suche_runde24.py:49 und :62); daher 25,8 % gegen 24,6 % und 33,1 % gegen 31,3 %.
- **Auswirkung:** Wer Hebel oder Kapital nach „Einbruch 25 %“ bemisst, unterschätzt den möglichen Verlust eines neuen Kontos etwa um den Faktor zwei.
- **Empfehlung:** Zusätzlich ausweisen: größter Rückgang in Einheiten des Startkapitals, schlechtester Tag und schlechteste Woche, Verteilung der Tiefstände aus der Neustart-Simulation, Verlauf des Brutto-Engagements. Eine Einbruch-Definition (5-Minuten-Werte) festlegen und im Protokoll benennen.
- **Nachstellen:** cd /home/user/OdinGate-Botv134/swing-hybrid && .venv/bin/python -I reports/audit/evidence/QD/statistik.py && .venv/bin/python -I reports/audit/evidence/QD/hebel3.py

#### QD-06 (P1): Kopfzahl des Prüfzeitraums beruht auf einer nach Kenntnis des Ergebnisses geänderten Kostenannahme und reagiert stark auf Ausführungsdetails

- **Sicherheit des Prüfers:** hoch
- **Stand:** nicht gegengeprüft
- **Evidenz:** Vorab festgelegt (Runde 2/3, 5 bp): Prüfzeitraum Hebel 1 +7,8 %/Jahr, Sharpe 0,159 (evidence/QD/repro_kandidat.txt; suche_runde3.json sofort/A/Pruefung). Runde 6 (reports/suche_protokoll.md:217–229, nach Runden 3–5): Slippage je Coin = 2 × halbe Spanne aus 30 Messungen am Samstag, 14.11.2026, 15:40–16:39 UTC (suche_runde6.json stichprobe; src/hybrid/research.py:272–279), im Mittel 2,95 bp, BTC/ETH am Boden 0,5 bp; damit +16,5 %/Jahr, Sharpe 0,337. Doppelte Slippage: Sharpe 0,079. Verzögerte Ausführung um 5 / 15 / 30 / 60 Minuten (evidence/QD/gruppen_latenz.txt): Prüfzeitraum Sharpe 0,23 / 0,15 / −0,01 / 0,06, Entwicklung 0,92 / 0,84 / 0,90 / 0,98. Gegenprobe zugunsten der Annahme: Papier-Test 1 misst bisher 1,58 bp je Order bei 1.500 $ (635 Messungen, Sonntag 15.11., 13:21–18:58 UTC; evidence/QD/kosten_vorwaertstest_vs_annahme.txt).
- **Auswirkung:** Die veröffentlichte Zahl ist doppelt so hoch wie die vorab festgelegte. Unterschiede zwischen nahezu gleichen Umsetzungen (wenige Minuten Verzögerung) sind so groß wie der behauptete Vorteil.
- **Empfehlung:** Beide Zahlen nebeneinander berichten (5 bp vorab, Yubit-Messung nachträglich). Kosten aus dem Papier-Test über mindestens vier Wochen einschließlich Werktagen und unruhiger Phasen nachführen. Tatsächliche Verzögerung des 5-Minuten-Takts messen und als festen Stress in die Rückrechnung aufnehmen.
- **Nachstellen:** cd /home/user/OdinGate-Botv134/swing-hybrid && .venv/bin/python -I reports/audit/evidence/QD/repro1.py && .venv/bin/python -I reports/audit/evidence/QD/gruppen_latenz.py

#### QD-07 (P1): 336 Stunden ist im Entwicklungszeitraum eine Spitze, keine Hochebene; die behauptete Robustheit prüft nur denselben Rückblick

- **Sicherheit des Prüfers:** hoch
- **Stand:** nicht gegengeprüft
- **Evidenz:** evidence/QD/nachbarn_entwicklung.txt (ausschließlich Entwicklung bis 31.03.2025, Gruppe A, Hebel 1, Yubit-Kosten): Sharpe 168 h 0,57 · 192 h 0,52 · 240 h 0,74 · 288 h 0,74 · 336 h 0,95 · 384 h 0,55 · 432 h 0,20 · 504 h 0,28 · 672 h 0,48 · 1008 h 0,21 · 1440 h 0,52; in D1 liegt der Sharpe für 384 bis 1008 h zwischen −0,42 und +0,03. Die im Protokoll (reports/suche_protokoll.md:1129–1131) und in uebergabe_fuer_dritte.md:27 genannten „anderen Bauarten“ benutzen alle L = 336 (src/hybrid/mutationen.py:8). 336 h war der größte Einzelwert des Rasters und kam erst in Runde 2 dazu. Gespeichert in reports/diagnose_frequenz.csv (pruef_N_jahr): Im Prüfzeitraum sind alle sechs kürzeren Rückblicke negativ (168 h −4,9 %/Jahr), nur 336 h ist positiv.
- **Auswirkung:** Sharpe 0,95 ist das Maximum einer Familie, deren Mittel in der Entwicklung bei rund 0,5 liegt; die Kopfzahl ist durch die Auswahl nach oben verzerrt. Ein Rückblick von 18 statt 14 Tagen hätte 0,20 ergeben.
- **Empfehlung:** Keinen Parameter ändern (kein Nachjustieren). In den Unterlagen Familienmittel und Spanne neben dem Einzelwert ausweisen und für Planungen höchstens das Familienmittel ansetzen. Ein Mittel über mehrere Rückblicke wäre eine neue Hypothese und nur mit vorab festgelegtem Protokoll im Vorwärtstest prüfbar.
- **Nachstellen:** cd /home/user/OdinGate-Botv134/swing-hybrid && .venv/bin/python -I reports/audit/evidence/QD/nachbarn.py

#### QD-08 (P1): Vorwärtstest ohne vorab festgelegte Auswertung; er kann den Vorteil in absehbarer Zeit nicht belegen, und Test 2 entspricht nicht der gerechneten Variante

- **Sicherheit des Prüfers:** hoch
- **Stand:** nicht gegengeprüft; Takt-Teil von fünf Prüfern gefunden
- **Evidenz:** reports/uebergabe_fuer_dritte.md:71–72 führt die Auswertung als offene Frage. Rechnung: Für 80 % Trennschärfe bei 5 % einseitig braucht ein wahrer Sharpe von 0,95 rund 6,9 Jahre, 0,5 rund 25 Jahre, 0,34 rund 53 Jahre ((1,645 + 0,842) / Sharpe)². Test 2: vorwaertstest/config_lauf_tpsl.json:21–22 (tp 0,15, sl 0,05) ist sl5_tp15 aus Runde 24, dort Stufe 1 nicht bestanden (D2 0,83 gegen 1,32), gemeinsamer p-Wert 0,54 (reports/suche_runde24.json), Protokoll Zeile 1297–1298 „kein belegter Vorteil“; gewählt wurde die nach Gesamt-Sharpe beste von 11 Varianten derselben Stichprobe. Umsetzung weicht ab: vorwaertstest/bot.py:216–226 prüft Ziel und Stop bei jedem Durchlauf gegen Mittelkurs und Füllkurs (laut vorwaertstest/lauf_tpsl/stand.csv alle rund 5 Minuten), Runde 24 prüft am Stundenschluss (reports/suche_protokoll.md:1245; src/hybrid/tpsl.py:15–40). vorwaertstest/README.md:3 nennt noch Hebel 0,2.
- **Auswirkung:** Jeder Ausgang nach Wochen oder Monaten lässt sich als Bestätigung lesen. Der Vergleich Test 1 gegen Test 2 misst Rauschen, und für Test 2 gibt es keine passende Rückrechnung.
- **Empfehlung:** Schriftlich vorab festlegen: Zweck (Kosten, Füllungen, Funding, Abweichung zur parallel nachgerechneten Rückrechnung auf denselben Stunden), Laufzeit, Abbruchgrenzen. Gewinn oder Verlust ausdrücklich nicht als Beleg für den Vorteil werten. Test 2 an die Stundenschluss-Prüfung angleichen oder als eigene, ungeprüfte Variante kennzeichnen; README aktualisieren.
- **Nachstellen:** sed -n 216,226p /home/user/OdinGate-Botv134/swing-hybrid/vorwaertstest/bot.py; sed -n 14,40p /home/user/OdinGate-Botv134/swing-hybrid/src/hybrid/tpsl.py; tail -8 /home/user/OdinGate-Botv134/swing-hybrid/vorwaertstest/lauf_tpsl/stand.csv

#### QD-09 (P2): Alle Coin-Gruppen enthalten nur Überlebende; Gruppe A wurde im Rückblick festgelegt

- **Sicherheit des Prüfers:** mittel
- **Stand:** nicht gegengeprüft (nicht vorgesehen)
- **Evidenz:** Gruppe A: src/hybrid/research.py:16, laut reports/hybrid_report.md:206 und suche_bericht.md:392 „im Rückblick festgelegt“ (Labor des Betreibers). Gruppe B: research.py:17, im Protokoll (Zeile 23–24) ohne Kriterium. Gruppen C und D: Listen „aus dem Gedächtnis“ (Protokoll 143–147, 193–195) plus Filter auf lückenlose Monatsdateien bis 10/2026 (scripts/suche_runde4.py:23–38, scripts/suche_runde5.py:26–28 und :97). data/candles/download5.log: LRC, OCEAN, STORJ, ICX und DENT fielen wegen endender Funding-Historie heraus (Delisting zwischen 2025 und 08/2026; Kerzen danach flach mit Umsatz 0), das sind 5 von 25 geprüften Anwärtern für D. Ab Runde 6 zusätzlich nur heute bei Yubit gelistete Coins (C 19, D 10). Stichprobe zur Wirkung, evidence/QD/hebel3_engagement_delisting.txt (c): Kandidat auf den fünf ausgeschlossenen Coins (5 bp, Hebel 1) Entwicklung +224,6 %, Prüfzeitraum −3,2 %; Gruppe D +109,3 % und −0,1 %.
- **Auswirkung:** Die Bestätigungen auf „frischen“ Coins (Runden 4, 5, 22) laufen auf Überlebenden. Für eine Long/Short-Trendregel ist die Richtung der Verzerrung offen; die Stichprobe zeigt keine Schönung. Für Gruppe A ist sie nicht messbar.
- **Empfehlung:** Für künftige Prüfungen ein Universum nach damaligem Stand verwenden (alle zum jeweiligen Zeitpunkt gelisteten Binance-Perpetuals einschließlich später gestrichener, Auswahl nach damaligem Umsatz wie in Runde 9). Delisting über Umsatz 0 erkennen statt über fehlende Funding-Dateien.
- **Nachstellen:** grep -v 'fehlende Monate: keine' /home/user/OdinGate-Botv134/swing-hybrid/data/candles/download5.log; cd /home/user/OdinGate-Botv134/swing-hybrid && .venv/bin/python -I reports/audit/evidence/QD/hebel3.py   # Abschnitt (c)

#### QD-10 (P2): Reality Check ist richtig umgesetzt, wurde aber nie auf die Auswahl des Kandidaten angewendet und ist ohne Studentisierung für eng verwandte Varianten kaum trennscharf

- **Sicherheit des Prüfers:** hoch
- **Stand:** nicht gegengeprüft (nicht vorgesehen)
- **Evidenz:** src/hybrid/mutationen.py:165–183: stationärer Bootstrap, Zentrierung je Spalte, Maximum der Mittel; Größentest evidence/QD/reality_check_2.txt: Ablehnungsquote 5,7 % bei Soll 5 % (300 Wiederholungen, k = 14 und k = 11). Runden 21 und 24 exakt nachgerechnet (evidence/QD/reality_check.txt: p 0,8426 und 0,5400, Schwellen bis zur 10. Stelle gleich). Schwäche: Die Streuung der Tagesdifferenzen reicht in Runde 24 von 0,4 %/Jahr (sl15) bis 62 %/Jahr (tp10) bei einer gemeinsamen Schwelle von +61 Punkten/Jahr; eng korrelierte Varianten können sie nie erreichen. Studentisiert: p 0,71 (Runde 21) und 0,91 (Runde 24), Urteil unverändert. Skalierungsfaktor aus derselben Stichprobe (scripts/suche_runde21.py:46). Der Reality Check kommt erst ab Runde 21 vor, also nach der Auswahl des Kandidaten in Runde 1–3.
- **Auswirkung:** Die Schlüsse der Runden 21, 23 und 24 halten. Stufe 2 würde aber eine echte kleine Verbesserung einer eng verwandten Variante nicht erkennen, und die Auswahl des Kandidaten selbst blieb unkorrigiert (siehe QD-01).
- **Empfehlung:** Studentisierte Variante ergänzen (Hansen SPA oder Romano-Wolf) und mit Test absichern. Den Reality Check für die Auswahlrunde 3 im Protokoll nachtragen.
- **Nachstellen:** cd /home/user/OdinGate-Botv134/swing-hybrid && .venv/bin/python -I reports/audit/evidence/QD/reality.py && .venv/bin/python -I reports/audit/evidence/QD/reality2.py

#### QD-11 (P3): Zählung „127 Einzelhypothesen, 602 Varianten“ stimmt mit dem Protokoll, erfasst aber nicht alle Auswertungen auf denselben Daten

- **Sicherheit des Prüfers:** hoch
- **Stand:** nicht gegengeprüft (nicht vorgesehen)
- **Evidenz:** Summe je Runde laut Protokoll: 30+10+7+6+4+1+1+1+9+1+1+1+2+2+1+4+5+14+1+15+11 = 127; 43 Einstiege × 7 Ausstiege × 2 Bias-Längen = 602 (reports/suche_runde11.json varianten = 602). Enthalten sind 8 Wiederholungen derselben Signale in Runde 2 (nur andere Ausführung) sowie in Runde 5 „basis“ und das nie gerechnete „trend_carry“. Nicht gezählt: Neumessung der 10 Einstellungen in Runde 3, 7 Rückblicke der Diagnose (Protokoll 388–405), Kombination in Runde 6, 4 Fusionen in Runde 12 samt Nachrechnung, 6 Mischungen mit dem Kandidaten in den Runden 13–17, das Vorprojekt (18 Einstellungen × 2 Swing-Quellen, reports/hybrid_report.md:14) und das Labor des Betreibers (4.177 Einzelläufe, reports/datenbericht.md:14).
- **Auswirkung:** 127 zählt vorab festgelegte Hypothesen, nicht alle Auswertungen. Die Last des Mehrfachtestens ist höher, als die Zahl nahelegt.
- **Empfehlung:** Zusätzlich die Zahl aller Auswertungen und die Zahl der Einsichten in den Prüfzeitraum führen und berichten.
- **Nachstellen:** grep -n 'Gesamtzahl der Versuche' /home/user/OdinGate-Botv134/swing-hybrid/reports/suche_protokoll.md

#### QD-12 (P3): Rechenkonventionen stehen nicht im Protokoll; einzelne Unterlagen widersprechen dem Stand

- **Sicherheit des Prüfers:** hoch
- **Stand:** nicht gegengeprüft (nicht vorgesehen)
- **Evidenz:** „Ohne Zinseszins“ steht nur in reports/suche_bericht.md:45 und hybrid_report.md:44, nicht im Protokoll und nicht in uebergabe_fuer_dritte.md. Sharpe = Tagesmittel / Tagesstreuung × √365 ohne Zinsabzug (src/hybrid/research.py:185, runner.py:128, tagestrend.py:70) und Ertrag/Jahr = Summe / Tage × 365 (research.py:186) sind einheitlich, aber nirgends im Protokoll definiert. vorwaertstest/README.md:3 nennt Hebel 0,2, config_lauf.json:4 hat 3,0. reports/suche_runde6.json enthält „staerkerer_edge": true, das Protokoll (Zeile 268–270) wertet begründet dagegen. Korrelation 0,68 / 0,79 (uebergabe_fuer_dritte.md:28) ohne Rechengrundlage im Repo; eigene Rechnung 0,67–0,69 und 0,77–0,79 je nach Stunden- oder Tagesrenditen.
- **Auswirkung:** Leser können Kennzahlen aus verschiedenen Runden und Berichten nicht sicher vergleichen.
- **Empfehlung:** Kennzahlen-Glossar an den Anfang des Protokolls (Einsatz, Hebel, Tageslimit, Kosten, Rebate, Zinseszins, Annualisierung, Einbruch-Definition). README aktualisieren, JSON der Runde 6 um ein Feld mit der Wertung ergänzen, Rechenweg der Korrelation ablegen.
- **Nachstellen:** grep -n 'Zinseszins' /home/user/OdinGate-Botv134/swing-hybrid/reports/*.md; sed -n 3p /home/user/OdinGate-Botv134/swing-hybrid/vorwaertstest/README.md

### Nachgerechnete Aussagen

- **reproduziert**: Entwicklung +59 % pro Jahr, Sharpe 0,95 (Gruppe A, Einsatz 100 %, ohne Tageslimit, Yubit-Kosten mit 85 % Rebate). Mit den Projektmodulen 0,5940 und 0,9457 (identisch zu suche_runde24.json). Eigene Rechnung ohne engine2 und auf_raster: 0,5934 und 0,9438; die Abweichung von 0,24 Prozentpunkten Gesamtertrag kommt aus der Behandlung von fünf Lückentagen bei SOL, XRP und LTC (Projekt: ohne Position; eigene Rechnung: Signal gehalten). Befehl: `cd /home/user/OdinGate-Botv134/swing-hybrid && .venv/bin/python -I reports/audit/evidence/QD/repro1.py && .venv/bin/python -I reports/audit/evidence/QD/lookahead.py`
- **reproduziert**: Prüfzeitraum +16,5 % pro Jahr, Sharpe 0,34. 0,1652 und 0,3369, mit Projektmodulen und mit der eigenen Rechnung auf vier Stellen gleich. Gesamt +25,85 % in 571 Tagen. Befehl: `cd /home/user/OdinGate-Botv134/swing-hybrid && .venv/bin/python -I reports/audit/evidence/QD/repro1.py`
- **reproduziert**: Größter Einbruch 25 % (Entwicklung) und 31 % (Prüfzeitraum). Auf Tageswerten 24,6 % und 31,3 %. Auf 5-Minuten-Werten (runner.max_drawdown) 25,8 % und 33,1 %. In Einheiten des Startkapitals 0,569 und 0,543 (siehe QD-05). Befehl: `cd /home/user/OdinGate-Botv134/swing-hybrid && .venv/bin/python -I reports/audit/evidence/QD/repro1.py`
- **reproduziert**: Runde 3: Kandidat bei Hebel 0,2 mit 5 bp, Entwicklung +34,9 %, Prüfzeitraum +2,4 %; Hebel 1 ohne Limit Sharpe 0,80 und 0,16. 0,3486 und 0,0244; Sharpe 0,8033 und 0,1591. Identisch zu suche_runde3.json und kandidat.json. Befehl: `cd /home/user/OdinGate-Botv134/swing-hybrid && .venv/bin/python -I reports/audit/evidence/QD/repro1.py`
- **reproduziert**: Runde 6 Teil 1: Yubit-Kosten, Hebel 0,2, Entwicklung +41,3 %, Prüfzeitraum +5,2 %. 0,4133 und 0,0517. Doppelte Slippage bei Hebel 1: Sharpe 0,0791 wie im JSON. Befehl: `cd /home/user/OdinGate-Botv134/swing-hybrid && .venv/bin/python -I reports/audit/evidence/QD/repro1.py`
- **reproduziert**: Zufallstest nur im Prüfzeitraum: besser als rund 80 % der verschobenen Signale. Mit Yubit-Kosten Perzentil 80,5 (200 Verschiebungen, seed 11); kandidat.json nennt 80,5 mit 5 bp. Unter der eigenen 90-%-Hürde. Befehl: `cd /home/user/OdinGate-Botv134/swing-hybrid && .venv/bin/python -I reports/audit/evidence/QD/statistik.py`
- **reproduziert**: Runde 21: beste Variante käme zufällig in 84 % der Fälle so weit, Schwelle +44 Punkte; Runde 24: 54 %. p 0,8426 und 0,5400, Schwellen bis zur zehnten Stelle gleich; Sharpe und Skalierungsfaktoren aller 25 Varianten ohne Abweichung. Eigene Bootstrap-Umsetzung: p 0,83 und 0,56. Befehl: `cd /home/user/OdinGate-Botv134/swing-hybrid && .venv/bin/python -I reports/audit/evidence/QD/reality.py`
- **reproduziert**: Kandidat je Gruppe A bis D und Vorperiode (gesamt_60.json, suche_runde4.json, suche_runde22.json). Alle Werte auf vier Stellen gleich. Prüfzeitraum-Sharpe mit Yubit-Kosten: A 0,34, B 0,20, C 0,64, D −0,05; Vorperiode 40 Coins +181,8 %. Befehl: `cd /home/user/OdinGate-Botv134/swing-hybrid && .venv/bin/python -I reports/audit/evidence/QD/gruppen_latenz.py`
- **reproduziert**: 127 Einzelhypothesen und 602 Varianten. Die Summe der Runden ergibt 127, 43 × 7 × 2 ergibt 602. Die Zählung folgt der Definition des Protokolls und ist eine Untergrenze der Auswertungen (QD-11). Befehl: `grep -n 'Gesamtzahl der Versuche' /home/user/OdinGate-Botv134/swing-hybrid/reports/suche_protokoll.md`
- **reproduziert**: Zahlen im Protokolltext stimmen mit den gespeicherten JSON- und CSV-Dateien überein. 47 von 47 Stichproben aus 23 Runden stimmen auf die im Protokoll genannte Stellenzahl. Runde 12 zusätzlich von Hand geprüft. Befehl: `cd /home/user/OdinGate-Botv134/swing-hybrid && .venv/bin/python -I reports/audit/evidence/QD/konsistenz_tabelle.py`
- **reproduziert**: Hohe Korrelation der zehn Coins (0,68; seit 04/2025 0,79). Mittlere paarweise Korrelation in der Entwicklung 0,69 (Stundenrenditen) und 0,67 (Tagesrenditen), ab 04/2025 0,77 und 0,79. Alle zehn Positionen in 41 % der Stunden gleichgerichtet, mindestens acht in 74 %. Der Rechenweg für genau 0,68 liegt nicht im Repo. Befehl: `cd /home/user/OdinGate-Botv134/swing-hybrid && .venv/bin/python -I reports/audit/evidence/QD/statistik.py`
- **abweichend**: „Ungesehener Prüfzeitraum“, „je Idee höchstens einmal“ angesehen. 22 JSON- und 3 CSV-Dateien enthalten Prüfzeitraum-Zahlen; der Kandidat wurde dort in mindestens 12 Skripten und Konfigurationen gerechnet; der Zeitraum war vor der Suche für Trend-Strategien bekannt (QD-02). Befehl: `cd /home/user/OdinGate-Botv134/swing-hybrid && .venv/bin/python -I reports/audit/evidence/QD/pruefzeitraum_einsichten.py`
- **abweichend**: „Robust gegen die Bauart“, „Der Vorteil hängt nicht an einer Einstellung“. Gilt für andere Trend-Maße mit demselben Rückblick von 336 Stunden (Sharpe 0,78 bis 0,94, in suche_runde21.json bestätigt). Für benachbarte Rückblicke nicht: 288 h 0,74, 384 h 0,55, 432 h 0,20 (nur Entwicklung gerechnet). Befehl: `cd /home/user/OdinGate-Botv134/swing-hybrid && .venv/bin/python -I reports/audit/evidence/QD/nachbarn.py`
- **abweichend**: Hebel 3 ohne Tageslimit (Konfiguration der Papier-Tests) ist durch die Forschung gedeckt. In reports/ gibt es dazu keine Rechnung; diagnose_kapital.json rechnet Hebel 3 nur mit 3-%-Tageslimit. Eigene Rechnung siehe QD-04. Befehl: `cd /home/user/OdinGate-Botv134/swing-hybrid && .venv/bin/python -I reports/audit/evidence/QD/hebel3.py`

### Als richtig befunden

- Kein Blick in die Zukunft bei der Signalbildung: Störtest mit verfremdeten Kursen, Umsätzen und Funding ab 03.06.2024 13:00 lässt die Zielgewichte bis einschließlich dieser Kerze bei allen 34 geprüften Signalfunktionen unverändert (research.tsmom, ensemble, reversal, querschnitt, rangfolge, vol_beide, mischung, carry; alle 14 aus mutationen.VARIANTEN; alle 11 aus tpsl.VARIANTEN). Beleg: reports/audit/evidence/QD/lookahead_test.txt.
- src/hybrid/research.py:70–75 (auf_raster): Das Stundensignal mit Etikett Stundenbeginn wird um eine Stunde verschoben und gilt erst ab der ersten 5-Minuten-Kerze nach Stundenschluss.
- src/hybrid/research.py:39–67 (markt): ATR wird um eine Stunde verschoben (Zeile 60), Funding auf die 5-Minuten-Kerze des Abrechnungszeitpunkts gelegt (Zeile 63–64). ffill füllt Lücken mit dem letzten bekannten Kurs; bfill wirkt nur vor dem Handelsstart eines Coins, wo das Signal 0 ist und der Kurs stillsteht. ATR- und Funding-Feld im Störtest vor T0 unverändert.
- src/hybrid/engine2.py:84–94 und 124–159 (Taker-Pfad): Order und Fill in der Kerze nach dem Signal zum Eröffnungskurs × (1 ± Slippage); Funding (Zeile 99–102) wird auf die Position vor dem Fill gerechnet. Kontoverlauf im Störtest vor T0 bitgleich, auch im passiven Pfad. Die eigene Nachrechnung ohne diesen Kern trifft den Prüfzeitraum auf vier Stellen.
- Stichprobe weiterer Runden per Code-Durchsicht ohne Befund: Runde 7 (src/hybrid/positionierung.py:41, scripts/positionierung_laden.py Stundenwerte mit resample last/mean), Runde 9 (scripts/suche_runde9.py:25, Umsatz mit shift(1)), Runde 11 (src/hybrid/massentest.py:74–77, Einstieg zum Open der Folgekerze), Runde 13 (src/hybrid/niedrigrisiko.py:110–111), Runde 14 (src/hybrid/tagestrend.py:23, Signal mit shift(1)).
- src/hybrid/mutationen.py:165–183 (reality_check) ist eine korrekte Umsetzung von White's Reality Check: stationärer Bootstrap mit geometrischer Blocklänge und Ringschluss, gleiche Indizes für alle Spalten, Zentrierung je Spalte, Teststatistik Maximum der Mittel. Größentest: 5,7 % Ablehnungen bei Soll 5 %; ein deutlicher wahrer Vorsprung wird in 100 von 100 Fällen erkannt (reports/audit/evidence/QD/reality_check_2.txt).
- Anwendung in den Runden 21, 23 und 24 fachlich vertretbar: Maßstab Kandidat (21, 24) bzw. null (23), Varianten auf die Schwankung des Kandidaten gebracht, Blöcke 20 bzw. 5 Tage bei Autokorrelation der Tagesergebnisse nahe 0 (−0,02). Die Urteile bleiben mit studentisierter Statistik gleich (p 0,71 und 0,91).
- Annualisierung und Sharpe sind einheitlich: Tagesergebnis nach UTC-Tagen, Mittel / Streuung × √365, Ertrag pro Jahr = Summe / Tage × 365, nicht aufgezinst, feste Positionsgröße (src/hybrid/research.py:185–186, runner.py:127–128, tagestrend.py:69–70, scripts/suche_runde21.py:23–24). 365 Tage passen zum durchgehenden Handel.
- Positionsgröße im Papier-Bot folgt derselben Konvention wie die Rückrechnung: fester Nominalbetrag je Einstieg aus Startkapital × Hebel / Coins (vorwaertstest/bot.py:165; src/hybrid/engine2.py:88).
- Die Auswahl des Kandidaten in Runde 3 Stufe 1 benutzte nur den Entwicklungszeitraum (scripts/suche_runde3.py:35–54; suche_runde3.json stufe1: Score 0,421 gegen 0,047 des Zweiten). Die Runden 1 und 2 haben den Prüfzeitraum nicht angesehen (suche_ergebnis.json und suche_runde2.json enthalten nur Stufe 2).
- Vorab-Festlegung ist durch die Commit-Reihenfolge gestützt: Für die Runden 1 bis 7, 13, 21, 22 und 24 liegt der Commit des Protokolls jeweils vor dem Commit der Ergebnisdatei (z. B. Runde 5: 13:39 gegen 13:51; Runde 24: 17:39:54 gegen 17:40:34).
- Das Protokoll berichtet alle Runden einschließlich der durchgefallenen und benennt eigene Schwächen offen (Rückschau in Runde 8, zu weiches Kriterium in Runde 6, Vorwissen in den Runden 5, 13, 14, 16, 21).
- Kostenannahme der Rückrechnung ist nach den bisherigen Messungen des Papier-Tests eher vorsichtig: 1,58 bp je Order gemessen gegen 2,95 bp angenommen (635 Messungen bei 1.500 $ Ordergröße, nur Sonntag 15.11.; reports/audit/evidence/QD/kosten_vorwaertstest_vs_annahme.txt).
- Bestehende Tests der geprüften Module laufen grün: 38 bestanden (tests/test_mutationen.py, test_tpsl.py, test_engine2.py, test_rangfolge.py, test_tagestrend.py; mit -p no:cacheprovider ausgeführt).

### Ungeklärt

- Rebate: Höhe (85 %), Gültigkeit für Taker-Volumen eines Bots, Auszahlungsrhythmus und das Verhältnis zur Rebate-Arbitrage-Klausel von Yubit lassen sich aus dem Repo nicht prüfen. Davon hängt ab, ob der Kandidat im Prüfzeitraum überhaupt positiv war.
- Auswahl der Gruppen A und B: Zeitpunkt und Kriterium sind nicht dokumentiert (A stammt aus dem Labor des Betreibers, B ist eine fest eingetragene Liste). Die Größe der Rückschau-Verzerrung für Gruppe A lässt sich ohne Universum nach damaligem Stand nicht beziffern.
- Vorwissen aus dem Labor des Betreibers (4.177 Einzelläufe, 26 Strategien auf denselben 10 Coins bis 10/2026): Umfang und Einfluss auf die Wahl der Signal-Familien sind nicht rekonstruierbar.
- Ob jedes Protokoll tatsächlich vor der ersten Rechnung der Runde geschrieben wurde, belegt die Commit-Reihenfolge nur mittelbar; zwischen Protokoll- und Ergebnis-Commit liegen teils unter zwei Minuten.
- Übertragbarkeit von Binance auf Yubit: Kurse, Funding und Liquidität der Vergangenheit stammen von Binance; eine Yubit-Historie liegt nicht vor. Die Kostenmessungen decken nur ruhige Wochenendstunden ab (Samstag 14.11. eine Stunde, Sonntag 15.11. rund sechs Stunden).
- Verzögerte Ausführung: Im Prüfzeitraum fällt der Sharpe bei 30 Minuten Verzögerung auf null, in der Entwicklung nicht. Ob das ein echter Effekt oder Rauschen ist, lässt sich mit 19 Monaten nicht entscheiden.
- Rechenweg der im Übergabebericht genannten Korrelation 0,68 liegt nicht im Repo.
- Im Zweig liegt ein Commit 3dfd5b2 vom 15.11.2026 19:03 UTC („Audit: Zwischenstand der Evidenzdateien“), der unter anderem meine Evidenzdateien aufnimmt. Er stammt nicht von mir; ich habe keinen git-Schreibbefehl ausgeführt. Urheber und Push-Status habe ich nicht geprüft.
- Nicht nachgerechnet habe ich die Runden 10 bis 20 und 23 (andere Datensätze und Rechenkerne); dort wurden nur Protokoll und JSON verglichen.

### Evidenzdateien

- `/home/user/OdinGate-Botv134/swing-hybrid/reports/audit/evidence/QD/repro_kandidat.txt`
- `/home/user/OdinGate-Botv134/swing-hybrid/reports/audit/evidence/QD/repro_kandidat.json`
- `/home/user/OdinGate-Botv134/swing-hybrid/reports/audit/evidence/QD/repro1.py`
- `/home/user/OdinGate-Botv134/swing-hybrid/reports/audit/evidence/QD/lookahead_test.txt`
- `/home/user/OdinGate-Botv134/swing-hybrid/reports/audit/evidence/QD/lookahead.py`
- `/home/user/OdinGate-Botv134/swing-hybrid/reports/audit/evidence/QD/statistik_kandidat.txt`
- `/home/user/OdinGate-Botv134/swing-hybrid/reports/audit/evidence/QD/statistik_kandidat.json`
- `/home/user/OdinGate-Botv134/swing-hybrid/reports/audit/evidence/QD/statistik.py`
- `/home/user/OdinGate-Botv134/swing-hybrid/reports/audit/evidence/QD/reality_check.txt`
- `/home/user/OdinGate-Botv134/swing-hybrid/reports/audit/evidence/QD/reality_check.json`
- `/home/user/OdinGate-Botv134/swing-hybrid/reports/audit/evidence/QD/reality.py`
- `/home/user/OdinGate-Botv134/swing-hybrid/reports/audit/evidence/QD/reality_check_2.txt`
- `/home/user/OdinGate-Botv134/swing-hybrid/reports/audit/evidence/QD/reality_check_2.json`
- `/home/user/OdinGate-Botv134/swing-hybrid/reports/audit/evidence/QD/reality2.py`
- `/home/user/OdinGate-Botv134/swing-hybrid/reports/audit/evidence/QD/hebel3_engagement_delisting.txt`
- `/home/user/OdinGate-Botv134/swing-hybrid/reports/audit/evidence/QD/hebel3_engagement_delisting.json`
- `/home/user/OdinGate-Botv134/swing-hybrid/reports/audit/evidence/QD/neustart_hebel3.csv`
- `/home/user/OdinGate-Botv134/swing-hybrid/reports/audit/evidence/QD/hebel3.py`
- `/home/user/OdinGate-Botv134/swing-hybrid/reports/audit/evidence/QD/gruppen_latenz.txt`
- `/home/user/OdinGate-Botv134/swing-hybrid/reports/audit/evidence/QD/gruppen_latenz.json`
- `/home/user/OdinGate-Botv134/swing-hybrid/reports/audit/evidence/QD/gruppen_latenz.py`
- `/home/user/OdinGate-Botv134/swing-hybrid/reports/audit/evidence/QD/nachbarn_entwicklung.txt`
- `/home/user/OdinGate-Botv134/swing-hybrid/reports/audit/evidence/QD/nachbarn_entwicklung.json`
- `/home/user/OdinGate-Botv134/swing-hybrid/reports/audit/evidence/QD/nachbarn.py`
- `/home/user/OdinGate-Botv134/swing-hybrid/reports/audit/evidence/QD/konsistenz_tabelle.txt`
- `/home/user/OdinGate-Botv134/swing-hybrid/reports/audit/evidence/QD/konsistenz_tabelle.py`
- `/home/user/OdinGate-Botv134/swing-hybrid/reports/audit/evidence/QD/konsistenz_roh.txt`
- `/home/user/OdinGate-Botv134/swing-hybrid/reports/audit/evidence/QD/konsistenz.py`
- `/home/user/OdinGate-Botv134/swing-hybrid/reports/audit/evidence/QD/pruefzeitraum_einsichten.txt`
- `/home/user/OdinGate-Botv134/swing-hybrid/reports/audit/evidence/QD/pruefzeitraum_einsichten.py`
- `/home/user/OdinGate-Botv134/swing-hybrid/reports/audit/evidence/QD/kosten_vorwaertstest_vs_annahme.txt`

## Bereich QR: Unabhängige Nachrechnung

Die zentralen Zahlen sind auf zwei Wegen nachgerechnet und stimmen: mit den Modulen bitgenau zu den gespeicherten JSON-Dateien (Entwicklung +59,4 % pro Jahr, Sharpe 0,946, Einbruch 24,6 %; Prüfzeitraum +16,5 %, Sharpe 0,337, Einbruch 31,3 %), mit einer eigenen Minimal-Rechnung ohne src/hybrid auf höchstens 2 % genau (D1-Sharpe 0,535 statt 0,564, erklärt durch fünf fehlende Kerzentage bei SOL, XRP, LTC). Korrelation (0,675 / 0,785), Anteil gleichgerichteter Stunden (41,6 %), Runde 4, 6, 21 und 24 samt Reality Check sind ebenfalls reproduziert; ein Störungstest findet keinen Blick voraus. Die Rechnung ist also richtig, ihre Deutung trägt aber nicht: Der berichtete Einbruch gilt für feste Positionsgröße am Startkapital bei Hebel 1; bei Hebel 3 ohne Tageslimit (laufende Papier-Konfiguration) kostet der schlechteste Tag 89 % des Kontos, und 10 bis 13 % aller Starttage enden mit Konto null. Das Plus im Prüfzeitraum entsteht allein durch das 85-%-Rebate (ohne Rebate −19,6 %) und ist statistisch nicht von null zu unterscheiden (t = 0,42). Ein Reality Check über die 32 Einstellungen, aus denen der Kandidat gewählt wurde, wird nicht bestanden (p zwischen 0,09 und 0,48). Vor echtem Geld sind Hebel, Rebate-Nachweis und die Aussage „belegt“ zu korrigieren.

### Befunde

#### QR-01 (P0): Berichteter Einbruch (25 % / 31 %) und „Einsatz 100 %“ gelten nicht für die laufende Konfiguration mit Hebel 3; in der eigenen Historie wäre ein Hebel-3-Konto mehrfach ausgelöscht worden

- **Sicherheit des Prüfers:** hoch
- **Stand:** **bestätigt** (eigene Gegenprüfung)
- **Evidenz:** Messvorschrift: scripts/suche_runde24.py:62 misst den Einbruch als Rückgang von 1 + kumuliertem Tagesergebnis relativ zum Höchststand, bei fester Positionsgröße am STARTkapital (src/hybrid/engine2.py:88-92, dq = tgt*S/p). Das Rechenkonto wächst bis 3,28 (08.12.2024), der Prozentwert fällt dadurch klein aus. In Einheiten des Startkapitals bei Hebel 1 (evidence/QR/c_abweichung_risiko.txt): schlechtester Tag −29,7 % (09.12.2024), 7 Tage unter −10 % in der Entwicklung; größter absoluter Rückgang 0,51 (Entwicklung, Tagesbasis; 0,56 stündlich) und 0,50 (Prüfzeitraum; 0,54 stündlich). Feste Stückzahl bis zum Richtungswechsel lässt den Einsatz in Trends wachsen: Mittel 1,02x, 95-%-Wert 1,32x, Maximum 2,18x Startkapital (03.12.2024, XRP allein 0,54x); bei Hebel 3 sind das 6,5x, über hebel_max 5 (config.yaml:13). Hebel 3 ohne Tageslimit = vorwaertstest/config_lauf.json:4 und :17 (tagesverlust_limit 1.0): Start 01.04.2025 ergibt Konto-Tief 0,84 und Einbruch 55,8 % vom Höchststand (evidence/QR/d_module_zusatz.txt, Abschnitt 5). Start an jedem möglichen Tag: Konto <= 0 bei 12,5 % der Starttage in der Entwicklung und 10,5 % im Prüfzeitraum, Verlust >= 50 % bei 48 % bzw. 41 %. Mit Größe am laufenden Kontostand (Zinseszins): Einbruch 95 % / 92 %, CAGR −18 % / −44 % (evidence/QR/j_kosten_papier_zinseszins.txt). Die Forschung selbst hat den Kandidaten nur bei Hebel 0,2 mit Tageslimit 3 % bestanden (reports/suche_protokoll.md:135; reports/suche_bericht.md:23 „Das hält nur bei Hebel 0,2“; nachgerechnet: Hebel 0,25 -> Einbruch 10,6 %, Hebel 0,2 -> 8,8 %). vorwaertstest/README.md:3 nennt weiter Hebel 0,2. Zusatz: In der Stunde 10.10.2025 21:00 fielen DOT −74,5 %, AVAX −66 %, ADA/DOGE −62 % gegen den Vorstundenschluss; der Kandidat war zufällig in 8 von 10 Coins short, LTC long (−57,5 % innerhalb der Stunde). Die Rückrechnung kennt keine Liquidation (evidence/QR/i_crash_2025-10-10.txt).
- **Auswirkung:** Wer mit „Einbruch 25 %“ und Hebel 3 plant, unterschätzt das Verlustrisiko um ein Vielfaches. Ein Tag wie der 09.12.2024 kostet bei Hebel 3 rund 89 % des Kontos; Totalverlust bzw. Liquidation ist in den eigenen Daten mehrfach enthalten. Die Papier-Tests laufen mit dem 15-Fachen des Hebels, der in der Forschung bestanden hat.
- **Empfehlung:** Vor jedem Live-Handel: (1) Risiko in absoluten Größen je Startzeitpunkt berichten (schlechtester Tag, absoluter Rückgang, Anteil der Starttage mit Konto <= 50 % und <= 0) und den Hebel daraus ableiten. (2) Live höchstens mit dem bestandenen Hebel (0,2); die Hebel-3-Papierläufe nicht als Vorlage verwenden. (3) Positionswert je Coin und gesamt begrenzen (Obergrenze oder Nachführen), Margin- und Liquidationslogik der Börse in die Rückrechnung aufnehmen. (4) In allen Berichten „Einbruch“ und „Einsatz 100 %“ mit Messvorschrift kennzeichnen und README/Konfiguration in Einklang bringen.
- **Nachstellen:** cd /home/user/OdinGate-Botv134/swing-hybrid && E=reports/audit/evidence/QR && .venv/bin/python -I -B $E/c_abweichung_risiko.py $E/a_tagesreihe.csv /tmp/qr_c.json && NUMBA_CACHE_DIR=/tmp/qr_numba .venv/bin/python -I -B -W ignore $E/d_module_zusatz.py /tmp/qr_d.json && .venv/bin/python -I -B -W ignore $E/j_kosten_papier_zinseszins.py $E/a_tagesreihe.csv

#### QR-02 (P1): Das Plus im Prüfzeitraum entsteht allein durch das 85-%-Rebate und hängt an einer Kostenannahme aus einer 60-Minuten-Stichprobe

- **Sicherheit des Prüfers:** hoch
- **Stand:** **bestätigt** (eigene Gegenprüfung)
- **Evidenz:** Prüfzeitraum, Hebel 1 (evidence/QR/a_module.txt und d_module_zusatz.txt, Abschnitt 4): Ergebnis vor Gebühr inkl. Slippage und Funding +33,9 %; volle Taker-Gebühr 53,4 % des Kapitals (Umsatz 668x Kapital x 0,08 %); netto ohne Rebate −19,6 % (Sharpe −0,25); mit 85 % Rebate +25,9 % (0,34); mit 50 % Rebate +7,2 % (0,09). Slippage doppelt: +6,1 % (Sharpe 0,08); pauschal 0,05 %: +12,2 % (0,16); pauschal 0,10 %: −21,2 %. Unabhängige Rechnung bestätigt: ohne Rebate −19,5 % (evidence/QR/b_unabhaengig.txt). Gespeichert bei Hebel 0,2: reports/suche_runde6.json teil1.A.Pruefung handel = −0,039, rebate_anteil = 1,76. Kostenbasis: data/processed/yubit_spannen_stichprobe.csv, 30 Messungen am Samstag 14.11.2026 15:40–16:39 UTC, angewandt auf fünf Jahre (im Protokoll selbst als größte Unsicherheit genannt, suche_protokoll.md:248). vorwaertstest/bot.py:245 setzt im Live-Modus rebate = 0.0 („wird von Yubit getrennt gutgeschrieben, hier nicht sichtbar“); der tatsächliche Rebate-Zufluss wird nirgends gemessen. Zum Vergleich Entwicklung ohne Rebate: +113,8 % (Sharpe 0,50).
- **Auswirkung:** Ob die Strategie außerhalb der Entwicklungsdaten Geld verdient, entscheidet eine Zusage der Börse, nicht das Signal. Bei geringerem Rebate (Staffel, Deckel, Ausschluss von Taker-Volumen, verspätete Gutschrift) oder höherer Slippage ist das Ergebnis des Prüfzeitraums negativ.
- **Empfehlung:** Rebate-Bedingungen (Satz, Obergrenze, Auszahlungsrhythmus, Geltung für Taker-Orders und API-Handel) schriftlich belegen und im Repo ablegen. „Netto ohne Rebate“ in allen Berichten gleichrangig ausweisen. Im Vorwärtstest gemessene Slippage und (später live) Rebate-Gutschriften laufend gegen die Annahme abgleichen und ein Abbruchkriterium vorab festlegen.
- **Nachstellen:** cd /home/user/OdinGate-Botv134/swing-hybrid && NUMBA_CACHE_DIR=/tmp/qr_numba .venv/bin/python -I -B -W ignore reports/audit/evidence/QR/d_module_zusatz.py /tmp/qr_d.json   (Abschnitt 4 „Empfindlichkeit“ und „Zerlegung“)

#### QR-03 (P1): Vorteil des Kandidaten statistisch nicht gesichert: Reality Check über die eigene Auswahl nicht bestanden, Prüfzeitraum-Sharpe 0,34 nicht von null unterscheidbar

- **Sicherheit des Prüfers:** hoch
- **Stand:** **bestätigt** (eigene Gegenprüfung)
- **Evidenz:** evidence/QR/l_reality_check_kandidat.txt: White's Reality Check (mutationen.reality_check, Entwicklung, 1.325 Tage, Nullhypothese kein Ertrag) über die 32 Signal-Einstellungen der Runden 1–3, aus denen tsmom_L336 gewählt wurde (scripts/suche_stufe1.py:12-15, scripts/suche_runde2.py:14-15): p = 0,16 bei Slippage 0,05 % (Stand der Auswahl; auf gleiche Schwankung gebracht 0,48), p = 0,09 mit Yubit-Kosten (0,30). Nur die 14 Trend-Einstellungen: p = 0,15 / 0,21 bzw. 0,09 / 0,13. Als Einzelhypothese ohne Mehrfachvergleich: p = 0,07 bzw. 0,05. Der Kandidat ist die längste getestete Länge (Rand des Rasters). Bootstrap der Sharpe-Werte (evidence/QR/d_module_zusatz.txt, Abschnitt 6): Entwicklung 0,95, 90-%-Bereich 0,09 bis 1,71, t = 1,80; Prüfzeitraum 0,34, Bereich −0,87 bis +1,43, t = 0,42, 34 % der Ziehungen <= 0. Prüfzeitraum-Summe +25,9 %, ohne die fünf besten von 571 Tagen −25,4 %. Das Protokoll rechnet den Reality Check nur für Abwandlungen GEGEN den Kandidaten (Runden 21, 24), nie für den Kandidaten selbst; dessen „Zufallstest“ erreichte im Prüfzeitraum allein nur 80 % bzw. 85,5 % (suche_protokoll.md:136; reports/suche_runde4.json breit_zufall_pruefung).
- **Auswirkung:** Die Aussage „Ein einziger Baustein hält der Prüfung stand“ (reports/uebergabe_fuer_dritte.md:17) ist stärker als die Daten. Entscheidungen über echtes Geld und Hebel stützen sich auf einen Vorteil, der unter Berücksichtigung der Auswahl mit beträchtlicher Wahrscheinlichkeit Zufall ist.
- **Empfehlung:** Aussage auf „plausibel, nicht belegt“ herabstufen und Kennzahlen stets mit Unsicherheitsbereich nennen. Vorab festlegen, was der Vorwärtstest zeigen kann (Kosten, Ausführung, Betrieb) und was nicht: Bei einem wahren Sharpe von 0,5 braucht t = 2 rund 16 Jahre, bei 0,95 gut 4 Jahre. Kapital und Hebel so wählen, dass ein wahrer Vorteil von null tragbar bleibt.
- **Nachstellen:** cd /home/user/OdinGate-Botv134/swing-hybrid && NUMBA_CACHE_DIR=/tmp/qr_numba .venv/bin/python -I -B -W ignore reports/audit/evidence/QR/l_reality_check_kandidat.py /tmp/qr_l.json

#### QR-04 (P2): Rückrechnung unterstellt Ausführung exakt zur vollen Stunde; im Prüfzeitraum kosten schon fünf Minuten Verzögerung ein Drittel des Ergebnisses

- **Sicherheit des Prüfers:** mittel
- **Stand:** nicht gegengeprüft (nicht vorgesehen)
- **Evidenz:** src/hybrid/engine2.py:85 und :124-128 rechnen die Order zum Open der ersten 5-Minuten-Kerze nach Stundenschluss ab (keine Latenz). Gewichte um n Kerzen verschoben, sonst alles gleich (evidence/QR/d_module_zusatz.txt, Abschnitt 4): Prüfzeitraum netto +25,9 % (Sharpe 0,34) -> 5 min +17,5 % (0,23) -> 15 min +11,5 % (0,15) -> 60 min +4,4 % (0,06). Entwicklung dagegen kaum empfindlich: Sharpe 0,95 -> 0,92 -> 0,84 -> 0,98; der Effekt im Prüfzeitraum kann also teilweise Zufall sein. Tatsächlicher Takt des Papier-Bots laut vorwaertstest/lauf/stand.csv: erster Durchlauf je Stunde in Minute 5, 1, 4, 4, 4; größter Abstand zweier Durchläufe 13 Minuten (evidence/QR/j_kosten_papier_zinseszins.txt). Zusätzlich bildet der Bot das Signal aus Yubit-Stundenkerzen (vorwaertstest/bot.py:83-92), die Forschung aus Binance-Kerzen.
- **Auswirkung:** Der ohnehin dünne Ertrag außerhalb der Entwicklung wird durch die reale Auslösung (KI-Sitzung im Fünf-Minuten-Takt) weiter geschmälert; Vorwärtstest und Rückrechnung sind nicht deckungsgleich.
- **Empfehlung:** Bot deterministisch wenige Sekunden nach der vollen Stunde auslösen und die Latenz je Order protokollieren. Verzögerungs-Szenarien (5, 15, 60 Minuten) fest in die Referenzrechnung aufnehmen. Vorwärtstest gegen eine Rückrechnung mit denselben Zeitstempeln und derselben Kursquelle vergleichen.
- **Nachstellen:** cd /home/user/OdinGate-Botv134/swing-hybrid && NUMBA_CACHE_DIR=/tmp/qr_numba .venv/bin/python -I -B -W ignore reports/audit/evidence/QR/d_module_zusatz.py /tmp/qr_d.json   (Zeilen „verzoegerung_…“)

#### QR-05 (P2): Papier-Test 2 prüft Stop und Ziel bei jedem Durchlauf (etwa alle fünf Minuten), die Rückrechnung der Runde 24 nur am Stundenschluss: der Test misst eine andere Regel

- **Sicherheit des Prüfers:** hoch
- **Stand:** nicht gegengeprüft; von fünf Prüfern gefunden
- **Evidenz:** Rückrechnung: src/hybrid/tpsl.py:31-38 prüft das Ergebnis seit Einstieg auf Stundenschlüssen gegen den Stundenschluss beim Signal. Bot: vorwaertstest/bot.py:223-224 prüft bei JEDEM Aufruf von schritt den aktuellen Mittelkurs gegen den Füllkurs; es gibt keine Sperre auf eine Prüfung je Stunde, und vorwaertstest/lauf/stand.csv zeigt 60 Durchläufe in 5,3 Stunden. Eigene 5-Minuten-Rechnung nur im Entwicklungszeitraum (evidence/QR/k_tpsl_pruefintervall.txt): Prüfung je Stunde Sharpe 1,43 / 0,84 / 1,16 (D1 / D2 / gesamt), Ertrag 34,1 % pro Jahr, Einbruch 14,2 %, 236 Stops; Prüfung alle 5 Minuten 1,29 / 0,73 / 1,04, Ertrag 29,8 %, Einbruch 16,6 %, 373 Stops (+58 %).
- **Auswirkung:** Ergebnisse von Test 2 lassen sich nicht mit den Zahlen der Runde 24 vergleichen; in der Entwicklung ist die tatsächlich laufende Regel rund 10 bis 13 % schlechter als die berichtete. Runde 24 selbst hatte ohnehin „keinen belegten Vorteil“ ergeben.
- **Empfehlung:** Entweder den Bot auf eine Prüfung je abgeschlossener Stundenkerze beschränken oder die Rückrechnung auf den realen Prüftakt umstellen; die gewählte Lesart im Protokoll festhalten, bevor Test 2 ausgewertet wird.
- **Nachstellen:** cd /home/user/OdinGate-Botv134/swing-hybrid && .venv/bin/python -I -B -W ignore reports/audit/evidence/QR/k_tpsl_pruefintervall.py /tmp/qr_k.json

#### QR-06 (P2): Fünf fehlende Kerzentage bei 30 von 72 Coins (in Gruppe A: SOL, XRP, LTC) bleiben unbemerkt und verschieben das D1-Ergebnis

- **Sicherheit des Prüfers:** hoch
- **Stand:** nicht gegengeprüft (nicht vorgesehen)
- **Evidenz:** data/candles/5m: 26.–28.02.2022 und 01.–02.04.2022 fehlen je 1.440 Kerzen bei 29 Dateien, ICP fehlen 7.518 (evidence/QR/g_daten_luecken_funding.txt). Die Ladeprüfung meldet nur fehlende Monate (scripts/kerzen_laden.py:75-80; data/candles/download.log: „5m SOLUSDT: 559872 Zeilen … fehlende Monate: keine“ gegen 561312 bei BTC). src/hybrid/research.py:48-55 lässt den Kurs in der Lücke stillstehen und verwirft die Stunden; mutationen.py:24 macht daraus Signal 0 in der Lücke und noch einmal 336 Stunden später (720 Coin-Stunden glatt, ohne Meldung). Wirkung: Module D1 netto +63,1 %, Sharpe 0,564; unabhängige Rechnung mit fortgeschriebenem Kurs +60,0 %, Sharpe 0,535; mit nachgebauter Lückenbehandlung +63,5 %, Sharpe 0,568 (evidence/QR/c_abweichung_risiko.txt, Teil 1). Entwicklung gesamt: Sharpe 0,946 gegen 0,931. Betroffen sind auch Gruppe B (FIL, NEAR, TRX, XLM) und große Teile von C und D, also die Bestätigungsläufe.
- **Auswirkung:** Berichtete Kennzahlen hängen an einer stillen Annahme über fehlende Daten; für Gruppe A beträgt der Effekt rund 3 Prozentpunkte in D1 (Sharpe +5 %), für die Gruppen B bis D ist er nicht beziffert.
- **Empfehlung:** Fehlende Tage nachladen; Ladeprüfung auf lückenloses 5-Minuten-Raster erweitern; research.markt bei Lücken abbrechen oder sie ausweisen; Referenzzahlen danach neu rechnen und als Regressionstest festhalten.
- **Nachstellen:** cd /home/user/OdinGate-Botv134/swing-hybrid && .venv/bin/python -I -B -W ignore reports/audit/evidence/QR/g_daten_luecken_funding.py && .venv/bin/python -I -B reports/audit/evidence/QR/c_abweichung_risiko.py reports/audit/evidence/QR/a_tagesreihe.csv /tmp/qr_c.json

#### QR-07 (P2): „+59 % pro Jahr“ und „+16,5 % pro Jahr“ sind Summen ohne Zinseszins bei fester Größe am Startkapital; als Wachstumsrate gelesen sind sie zu hoch

- **Sicherheit des Prüfers:** hoch
- **Stand:** nicht gegengeprüft (nicht vorgesehen)
- **Evidenz:** scripts/suche_runde24.py:62: jahr = Tagesmittel x 365; src/hybrid/runner.py:52-57 liefert Tagesergebnisse in Einheiten des Startkapitals. Nachgerechnet (evidence/QR/j_kosten_papier_zinseszins.txt): Entwicklung 59,4 % arithmetisch gegen 48,7 % CAGR bei Größe am laufenden Kontostand, Einbruch dann 41,6 % statt 24,6 %; Prüfzeitraum 16,5 % gegen 4,7 % CAGR, Einbruch 45,7 % statt 31,3 %. Der Einbruch wird zudem auf Tagesschlüssen gemessen; auf dem 5-Minuten-Raster sind es 25,8 % und 33,1 % (evidence/QR/a_module.txt, Spalte dd_5m). reports/uebergabe_fuer_dritte.md:22-25 nennt „Ertrag pro Jahr“ und „Größter Einbruch“ ohne diese Angaben.
- **Auswirkung:** Leser rechnen die Werte als Rendite hoch (etwa mal Hebel oder mit Zinseszins) und erhalten ein zu günstiges Bild von Ertrag und Risiko.
- **Empfehlung:** In Berichten und im Board beide Sichten ausweisen (feste Größe und Größe am Kontostand), die Messvorschrift für den Einbruch nennen und den 5-Minuten-Wert als maßgeblich verwenden.
- **Nachstellen:** cd /home/user/OdinGate-Botv134/swing-hybrid && .venv/bin/python -I -B -W ignore reports/audit/evidence/QR/j_kosten_papier_zinseszins.py reports/audit/evidence/QR/a_tagesreihe.csv

#### QR-08 (P3): Regeltext „sonst Short“ stimmt nicht mit dem Code: bei Gleichstand und bei fehlenden Kursen ist die Position glatt

- **Sicherheit des Prüfers:** hoch
- **Stand:** nicht gegengeprüft (nicht vorgesehen)
- **Evidenz:** src/hybrid/mutationen.py:23-24 und research.py:190-192 benutzen np.sign(...).fillna(0.0); vorwaertstest/kern.py:14-19 gibt bei Gleichstand 0 zurück. Im Zeitraum gibt es 147 Coin-Stunden mit exakt gleichem Schlusskurs (evidence/QR/b_unabhaengig.txt) und in den Modulen 867 Coin-Stunden mit Signal 0 (evidence/QR/a_module.txt), die Differenz stammt aus den Datenlücken (QR-06). Jede solche Stunde erzeugt zwei zusätzliche Orders. reports/uebergabe_fuer_dritte.md:17-18 beschreibt „long, sonst short“. Rückrechnung und Bot sind untereinander gleich.
- **Auswirkung:** Kein Rechenfehler, aber eine ungenaue Spezifikation; ein Nachbau nach dem Text weicht leicht ab.
- **Empfehlung:** Regel im Text präzisieren („bei Gleichstand oder fehlendem Kurs keine Position“) oder bewusst entscheiden, bei Gleichstand die bisherige Richtung zu halten, und das als Test festschreiben.
- **Nachstellen:** cd /home/user/OdinGate-Botv134/swing-hybrid && .venv/bin/python -I -B reports/audit/evidence/QR/b_unabhaengig.py /tmp/qr_b.json /tmp/qr_b.csv   (Zeile „Signal==0 Coin-Stunden“)

### Nachgerechnete Aussagen

- **reproduziert**: Entwicklung 15.08.2021–31.03.2025: +59 % pro Jahr, Sharpe 0,95 (Einbruch 24,6 %). (a) Module: Summe +215,6 %, 59,40 % pro Jahr, Sharpe 0,9457, Einbruch 24,58 % (Tagesbasis; 25,79 % auf 5 Minuten); bitgenau gleich reports/suche_runde24.json. (b) unabhängig: 58,55 % pro Jahr, Sharpe 0,9308, Einbruch 24,95 % (25,88 % stündlich). Abweichung (b) gegen Behauptung: −0,8 % / −2,0 % / +1,5 %, alle unter 10 %; Ursache ist die Lückenbehandlung (QR-06). Befehl: `cd /home/user/OdinGate-Botv134/swing-hybrid && E=reports/audit/evidence/QR && NUMBA_CACHE_DIR=/tmp/qr_numba .venv/bin/python -I -B $E/a_module.py /tmp/qr_a.json /tmp/qr_a.csv && .venv/bin/python -I -B $E/b_unabhaengig.py /tmp/qr_b.json /tmp/qr_b.csv`
- **reproduziert**: Prüfzeitraum 01.04.2025–23.10.2026: +16,5 % pro Jahr, Sharpe 0,34 (Einbruch 31 %). (a) Module: Summe +25,85 % in 571 Tagen = 16,52 % pro Jahr, Sharpe 0,3369, Einbruch 31,30 % (33,10 % auf 5 Minuten). (b) unabhängig: +25,89 %, 16,55 % pro Jahr, Sharpe 0,3375, Einbruch 31,30 % (32,83 % stündlich). Abweichung unter 0,2 %. Tagesreihen (a) und (b) über den ganzen Zeitraum: Korrelation 0,99981, Unterschiede nur an 38 Tagen um die Datenlücken und am ersten Tag. Befehl: `wie oben (a_module.py, b_unabhaengig.py); Vergleich der Tagesreihen in evidence/QR/a_tagesreihe.csv und b_tagesreihe.csv`
- **reproduziert**: Kandidaten-Sharpe D1 0,56 und D2 1,32. (a) Module: 0,5640 und 1,3165 (gleich reports/suche_runde21.json). (b) unabhängig: 0,5348 (−5,2 %) und 1,3165 (auf vier Stellen gleich). Die D1-Abweichung ist vollständig durch fehlende Kerzen bei SOL, XRP, LTC erklärt: mit nachgebauter Lückenbehandlung der Module ergibt die unabhängige Rechnung 0,5675; Rest 0,0046 der Summe stammt vom ersten Handelstag (Einstieg 00:00 statt 00:05). Befehl: `cd /home/user/OdinGate-Botv134/swing-hybrid && .venv/bin/python -I -B reports/audit/evidence/QR/c_abweichung_risiko.py reports/audit/evidence/QR/a_tagesreihe.csv /tmp/qr_c.json`
- **reproduziert**: Mittlere Korrelation der Tagesrenditen der zehn Coins 0,68, seit 04/2025 0,79. Einfache Tagesrenditen (UTC-Tagesschluss), Mittel der 45 Paare: gesamter Zeitraum 0,675, seit 01.04.2025 0,785 (Entwicklung allein 0,648). Mit Log-Renditen 0,695 / 0,794; Stundenrenditen 0,698 / 0,771. Befehl: `cd /home/user/OdinGate-Botv134/swing-hybrid && .venv/bin/python -I -B reports/audit/evidence/QR/b_unabhaengig.py /tmp/qr_b.json /tmp/qr_b.csv   (Zeile „Korrelation“)`
- **reproduziert**: In 42 % der Stunden zeigen alle zehn Signale in dieselbe Richtung. Gesamter Zeitraum 41,6 % (19,0 % alle long, 22,6 % alle short); Entwicklung 38,9 %, Prüfzeitraum 47,8 %. Mindestens 8 von 10 gleich: 74,5 %. Mittlere Netto-Ausrichtung 0,71 von 1. Die Quelle der Behauptung wurde im Repo nicht gefunden; Fenster vermutlich gesamter Zeitraum. Befehl: `wie oben (b_unabhaengig.py, Tabelle „Gleiche Richtung“)`
- **reproduziert**: Runde 24, Variante sl5_tp15: Sharpe 1,39 / 0,83 / 1,13, Ertrag 33 % pro Jahr, Einbruch 14,6 %, Zeit im Markt 56 %. Module über hybrid.tpsl: 1,3870 / 0,8257 / 1,1345, 33,27 %, 14,56 %, 56,38 % (gleich suche_runde24.json); alle elf Varianten stimmen. Unabhängiger Nachbau nach dem Protokolltext: 1,4356 / 0,8257 / 1,1620, 34,2 %, 14,3 %, 56,6 %; größte Abweichung +3,5 % (D1). Befehl: `cd /home/user/OdinGate-Botv134/swing-hybrid && .venv/bin/python -I -B -W ignore reports/audit/evidence/QR/e_unabhaengig_tpsl_vorperiode.py /tmp/qr_e.json`
- **reproduziert**: Runde 24 und Runde 21: gemeinsame Zufallsprüfung (p = 0,54 bzw. 0,84; Schwelle +44 Punkte; Funding-Filter 0,66 / 1,59 / 1,11, Vorsprung +10 Punkte). Runde 24: p = 0,5400, Schwelle 0,0016628 je Tag, identisch zum gespeicherten Wert. Runde 21: alle 14 Varianten mit Sharpe-Abweichung 0,0 gegen suche_runde21.json; p = 0,8426; Schwelle 0,0012172 je Tag = 44,4 Punkte pro Jahr; Funding-Filter 0,658 / 1,591 / 1,110, Vorsprung +10,35 Punkte. Befehl: `cd /home/user/OdinGate-Botv134/swing-hybrid && E=reports/audit/evidence/QR && NUMBA_CACHE_DIR=/tmp/qr_numba .venv/bin/python -I -B $E/a_module.py /tmp/qr_a.json /tmp/qr_a.csv && NUMBA_CACHE_DIR=/tmp/qr_numba .venv/bin/python -I -B -W ignore $E/d_module_zusatz.py /tmp/qr_d.json`
- **reproduziert**: Runde 6 Teil 1: Kandidat bei Hebel 0,2 mit Tageslimit 3 %: Entwicklung +41,3 %, Prüfzeitraum +5,2 %, bei doppelten Kosten +1,2 %. Nachgerechnet +41,33 % / +5,17 % / +1,22 %; Einbruch 8,85 % (Entwicklung) und 9,62 % (Prüfzeitraum); drei Sperrtage. Mit altem Wert 0,05 %: +2,44 %. Hebelsuche bestätigt: bei 0,25 liegt der Einbruch mit 10,6 % über der 10-%-Grenze. Befehl: `wie oben (d_module_zusatz.py, Abschnitt 1)`
- **reproduziert**: Runde 4: Vorperiode 02/2020–08/2021, Gruppe A, positiv (gespeichert: +198 %, Sharpe 1,29). Module: N 1,9797, Sharpe 1,2890, 2.753 Trades, identisch zu suche_runde4.json. Unabhängige Rechnung aus 5m_vor + 5m mit pauschal 0,05 % Slippage: N 1,9810, Sharpe 1,2898. Bootstrap: 90-%-Bereich −0,04 bis 2,52. Befehl: `cd /home/user/OdinGate-Botv134/swing-hybrid && .venv/bin/python -I -B -W ignore reports/audit/evidence/QR/e_unabhaengig_tpsl_vorperiode.py /tmp/qr_e.json`
- **reproduziert**: Diagnose Frequenz, 336 Stunden: mittlere Haltedauer 42 Stunden, Umsatz 1,1x Einsatz pro Tag. Module: Haltedauer 42,4 Stunden (Entwicklung) und 41,1 (Prüfzeitraum), Umsatz 1,13 bzw. 1,17 pro Tag, 10.986 Orders. Unabhängig: 10.979 Orders, Umsatz 1,14 pro Tag. Befehl: `wie oben (a_module.py, b_unabhaengig.py)`
- **reproduziert**: Signal aus der letzten abgeschlossenen Stunde, wirksam ab der Folgestunde (kein Blick voraus). Störungstest: alle Kurse ab T mit 1,5 bzw. 0,5 multipliziert (T = 01.06.2022, 17.03.2023 13:00, 10.10.2025 21:00). Zielgewichte bis einschließlich Kerze T und Kontoverlauf vor T bleiben bitgenau gleich, danach verschieden. Geprüft für basis, sl5_tp15 und funding_filter. Befehl: `cd /home/user/OdinGate-Botv134/swing-hybrid && NUMBA_CACHE_DIR=/tmp/qr_numba .venv/bin/python -I -B -W ignore reports/audit/evidence/QR/h_kein_blick_voraus.py`
- **abweichend**: Regel: long, wenn der Stundenschluss über dem von vor 336 Stunden liegt, andernfalls short. Bei Gleichstand ist die Position glatt, nicht short (np.sign bzw. kern.richtung). 147 Coin-Stunden echter Gleichstand; in den Modulen zusätzlich 720 Coin-Stunden Signal 0 durch Datenlücken. Wirkung auf die Kennzahlen gering, siehe QR-08. Befehl: `wie oben (a_module.py: „Signal==0-Stunden: 867“; b_unabhaengig.py: 147)`
- **reproduziert**: Zwei Papier-Tests mit Hebel 3 seit 15.11.2026. Nur aus Dateien gelesen: config_lauf.json und config_lauf_tpsl.json mit hebel 3.0 und tagesverlust_limit 1.0; Test 1 Start 13:21 UTC, Test 2 Start 17:44 UTC, je zehn Short-Einstiege; Einsatz 14.928 USDT bei 5.000 USDT Kapital. Gemessene Orderkosten in Test 1 im Mittel 1,58 bp bei rund 1.500 USDT je Order gegen 2,95 bp Annahme der Rückrechnung (60 Durchläufe, 5,3 Stunden eines Sonntags). Befehl: `cd /home/user/OdinGate-Botv134/swing-hybrid && .venv/bin/python -I -B -W ignore reports/audit/evidence/QR/j_kosten_papier_zinseszins.py reports/audit/evidence/QR/a_tagesreihe.csv`
- **ungeklaert**: 127 Einzelhypothesen und 602 Varianten untersucht. Die laufende Zählung im Protokoll ist rechnerisch schlüssig (40, 47, 53, 57, 58, 59, 60, 69, 70, 72, 74, 76, 77, 81, 86, 100, 101, 116, 127; 602 = 43 x 7 x 2, suche_protokoll.md:506). Inhaltlich nachgezählt wurde nicht; die Zählweise ist Auslegungssache (Runde 3 misst zehn Einstellungen in einem dritten Aufbau, ohne sie zu zählen). Befehl: `grep -n -E "Gesamtzahl der Versuche|Einzelhypothesen" /home/user/OdinGate-Botv134/swing-hybrid/reports/suche_protokoll.md`
- **reproduziert**: Bestehende Tests: 105 grün. 105 passed in 14,9 s (ohne Cache- und Bytecode-Schreiben). Befehl: `cd /home/user/OdinGate-Botv134/swing-hybrid && NUMBA_CACHE_DIR=/tmp/qr_numba PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -B -m pytest -q -p no:cacheprovider tests`

### Als richtig befunden

- Rechenkern für den Kandidaten: src/hybrid/engine2.py:84-92 und :124-158 (Taker-Modus) liefert dieselbe Tagesreihe wie eine eigene Stundenrechnung ohne src/hybrid; D2 und Prüfzeitraum stimmen auf vier Nachkommastellen, Korrelation der Tagesreihen 0,99981 (evidence/QR/a_tagesreihe.csv, b_tagesreihe.csv).
- Zeitliche Zuordnung ohne Blick voraus: research.py:70-75 (auf_raster verschiebt um eine Stunde), engine2.py:85 (Abrechnung zum Open der Kerze); Störungstest bestanden (evidence/QR/h_kein_blick_voraus.txt).
- Gebühren und Rebate: runner.py:48-57 rechnet Taker 0,08 % x (1 − 0,85) auf das gehandelte Volumen; unabhängig nachgerechnet identisch (Prüfzeitraum ohne Rebate −19,56 % gegen −19,46 %).
- Funding: Vorzeichen richtig (Long zahlt positives Funding, engine2.py:99-102); Funding-Daten der Gruppe A lückenlos, 5.688 Ereignisse je Coin, SOL 5.763 mit zusätzlichen Terminen (evidence/QR/g_daten_luecken_funding.txt).
- Gespeicherte Ergebnisse sind deterministisch nachrechenbar: reports/suche_runde21.json (alle 14 Varianten, Reality Check), suche_runde24.json (alle 11 Varianten, Reality Check), suche_runde6.json teil1.A, suche_runde4.json vorperiode.A; jeweils ohne Abweichung.
- Der Schalter vor=True/False in research.markt ändert das Ergebnis des Kandidaten nicht (größte Abweichung der Tagesreihen 0,0; evidence/QR/a_module.txt).
- mutationen.reality_check (mutationen.py:165-183) ist ein korrekt gebauter stationärer Bootstrap mit zentrierten Differenzen und Maximum-Statistik, fester Seed; Ergebnisse reproduzierbar.
- Kursdaten Binance gegen lokal vorhandene OKX-Tageskerzen (ab 01/2022): mittlere Abweichung rund 5 bp, Korrelation der Tagesrenditen >= 0,9998, nur SOL 0,991 um den FTX-Zusammenbruch (evidence/QR/f_okx_abgleich.txt). Keine Kerzen mit high < low oder Kurs <= 0 in Gruppe A.
- Slippage-Annahme ist bei der jetzigen Ordergröße vorsichtig: im Papier-Test 1 gemessen im Mittel 1,58 bp gegen 2,95 bp Annahme, je Coin 24 bis 71 % der Annahme (vorwaertstest/lauf/spannen.csv, nur gelesen; evidence/QR/j_kosten_papier_zinseszins.txt). Die Stichprobe ist allerdings nur gut fünf Stunden lang.
- Bot und Rückrechnung behandeln Gleichstand gleich (vorwaertstest/kern.py:14-19 gegen mutationen.py:23-24) und bemessen die Position beide fest am Startkapital (bot.py:165 gegen research.py:150).
- Bestehende Testsuite: 105 Tests grün.

### Ungeklärt

- Ob Yubit das Rebate von 85 % tatsächlich in dieser Höhe, ohne Deckel und für Taker-Orders per API gewährt: im Repo findet sich kein Beleg, nur die Annahme in config.yaml:8 und kern.py:9.
- Wie stark Yubit-Stundenkerzen (Signalquelle des Bots) von Binance-Kerzen (Forschungsgrundlage) abweichen und wie oft dadurch Signale anders ausfallen: Es liegt keine Yubit-Kurshistorie vor.
- Ob die fehlenden Tage 26.–28.02.2022 und 01.–02.04.2022 schon im Binance-Archiv fehlen oder beim Laden verloren gingen (ohne Netz nicht prüfbar). Die Wirkung auf die Bestätigungsläufe der Gruppen B, C, D wurde nicht beziffert.
- Liquidations- und Margin-Regeln von Yubit (Wartungsmargin, Cross oder Isolated): Die Auswertung zu Hebel 3 verwendet „Konto <= 0“ als Ersatz; eine echte Liquidation käme früher. Kurse innerhalb der Stunde wurden nur für den 10.10.2025 und als Obergrenze betrachtet.
- Quelle und Zeitfenster der Angabe „42 % gleichgerichtet“; im Repo nicht auffindbar, der nachgerechnete Wert passt für den gesamten Zeitraum.
- Die Zählung „127 Einzelhypothesen“ wurde nur als laufende Summe im Protokoll geprüft, nicht inhaltlich nachgezählt.
- Ob die Empfindlichkeit gegen Ausführungsverzögerung im Prüfzeitraum (QR-04) ein echter Effekt ist: In der Entwicklung zeigt er sich kaum, statistisch trennen lässt es sich mit diesen Daten nicht.
- Art der OKX-Vergleichsdaten (Spot oder Swap) ist nicht dokumentiert; der Abgleich deckt erst die Zeit ab 01/2022 ab.
- Der Reality Check in QR-03 rechnet alle 32 Einstellungen mit sofortiger Ausführung; in Runde 1 wurden sie mit passiven Limits gemessen. Für die passive Ausführung wurde er nicht wiederholt.

### Evidenzdateien

- `/home/user/OdinGate-Botv134/swing-hybrid/reports/audit/evidence/QR/a_module.py`
- `/home/user/OdinGate-Botv134/swing-hybrid/reports/audit/evidence/QR/a_module.txt`
- `/home/user/OdinGate-Botv134/swing-hybrid/reports/audit/evidence/QR/a_module.json`
- `/home/user/OdinGate-Botv134/swing-hybrid/reports/audit/evidence/QR/a_tagesreihe.csv`
- `/home/user/OdinGate-Botv134/swing-hybrid/reports/audit/evidence/QR/b_unabhaengig.py`
- `/home/user/OdinGate-Botv134/swing-hybrid/reports/audit/evidence/QR/b_unabhaengig.txt`
- `/home/user/OdinGate-Botv134/swing-hybrid/reports/audit/evidence/QR/b_unabhaengig.json`
- `/home/user/OdinGate-Botv134/swing-hybrid/reports/audit/evidence/QR/b_tagesreihe.csv`
- `/home/user/OdinGate-Botv134/swing-hybrid/reports/audit/evidence/QR/c_abweichung_risiko.py`
- `/home/user/OdinGate-Botv134/swing-hybrid/reports/audit/evidence/QR/c_abweichung_risiko.txt`
- `/home/user/OdinGate-Botv134/swing-hybrid/reports/audit/evidence/QR/c_abweichung_risiko.json`
- `/home/user/OdinGate-Botv134/swing-hybrid/reports/audit/evidence/QR/d_module_zusatz.py`
- `/home/user/OdinGate-Botv134/swing-hybrid/reports/audit/evidence/QR/d_module_zusatz.txt`
- `/home/user/OdinGate-Botv134/swing-hybrid/reports/audit/evidence/QR/d_module_zusatz.json`
- `/home/user/OdinGate-Botv134/swing-hybrid/reports/audit/evidence/QR/d_module_zusatz_vorperiode_tage.csv`
- `/home/user/OdinGate-Botv134/swing-hybrid/reports/audit/evidence/QR/e_unabhaengig_tpsl_vorperiode.py`
- `/home/user/OdinGate-Botv134/swing-hybrid/reports/audit/evidence/QR/e_unabhaengig_tpsl_vorperiode.txt`
- `/home/user/OdinGate-Botv134/swing-hybrid/reports/audit/evidence/QR/e_unabhaengig_tpsl_vorperiode.json`
- `/home/user/OdinGate-Botv134/swing-hybrid/reports/audit/evidence/QR/f_okx_abgleich.py`
- `/home/user/OdinGate-Botv134/swing-hybrid/reports/audit/evidence/QR/f_okx_abgleich.txt`
- `/home/user/OdinGate-Botv134/swing-hybrid/reports/audit/evidence/QR/g_daten_luecken_funding.py`
- `/home/user/OdinGate-Botv134/swing-hybrid/reports/audit/evidence/QR/g_daten_luecken_funding.txt`
- `/home/user/OdinGate-Botv134/swing-hybrid/reports/audit/evidence/QR/h_kein_blick_voraus.py`
- `/home/user/OdinGate-Botv134/swing-hybrid/reports/audit/evidence/QR/h_kein_blick_voraus.txt`
- `/home/user/OdinGate-Botv134/swing-hybrid/reports/audit/evidence/QR/i_crash_2025-10-10.py`
- `/home/user/OdinGate-Botv134/swing-hybrid/reports/audit/evidence/QR/i_crash_2025-10-10.txt`
- `/home/user/OdinGate-Botv134/swing-hybrid/reports/audit/evidence/QR/j_kosten_papier_zinseszins.py`
- `/home/user/OdinGate-Botv134/swing-hybrid/reports/audit/evidence/QR/j_kosten_papier_zinseszins.txt`
- `/home/user/OdinGate-Botv134/swing-hybrid/reports/audit/evidence/QR/k_tpsl_pruefintervall.py`
- `/home/user/OdinGate-Botv134/swing-hybrid/reports/audit/evidence/QR/k_tpsl_pruefintervall.txt`
- `/home/user/OdinGate-Botv134/swing-hybrid/reports/audit/evidence/QR/k_tpsl_pruefintervall.json`
- `/home/user/OdinGate-Botv134/swing-hybrid/reports/audit/evidence/QR/l_reality_check_kandidat.py`
- `/home/user/OdinGate-Botv134/swing-hybrid/reports/audit/evidence/QR/l_reality_check_kandidat.txt`
- `/home/user/OdinGate-Botv134/swing-hybrid/reports/audit/evidence/QR/l_reality_check_kandidat.json`

## Bereich ENG: Trading Engine

Die Rechenkerne rechnen korrekt: engine2 stimmt im Taker-Modus auf den echten Daten mit einer unabhängigen Nachrechnung auf 3e-16 überein, und +59 % pro Jahr / Sharpe 0,95 (Entwicklung) sowie +16,5 % pro Jahr / Sharpe 0,34 (Prüfzeitraum) sind reproduziert. Signalregel, Gebühren- und Rebate-Arithmetik sowie alle Kontoidentitäten des Papier-Bots (Zustand = stand.csv = Orderprotokoll = dashboard.json = Browser-Formel) stimmen. Die schweren Befunde liegen in dem, was nicht modelliert ist: Weder Rückrechnung noch Bot kennen Margin oder Liquidation, das Tagesverlust-Limit steht in beiden Tests auf 1.0 (faktisch aus), und bei Hebel 3 mit fester Positionsgröße fällt ein frisch gestartetes Konto im Entwicklungszeitraum bei 8,4 % der Starttage binnen 365 Tagen auf null (ohne Rebate 44,9 %), während die gemeldete Einbruchskennzahl 38 % zeigt. Im Live-Pfad blockiert der Sicherheitsdeckel max_order_usd auch Schließ-Orders (P0, mit nachgestellter Börse belegt), und verspätete Füllungen lassen den Bot mit offener Position stehen. Test 2 prüft Stop und Ziel bei jedem Lauf (alle 5 Minuten) statt am Stundenschluss wie Runde 24: 58 % mehr Stops und rund 4 Prozentpunkte weniger Ertrag pro Jahr bei Hebel 1, also nicht mit der Rückrechnung vergleichbar. Der Prüfzeitraum ist nur durch die Rebate-Annahme positiv (ohne Rebate −19,6 %), der Bot bucht das Rebate aber als erzielten Ertrag; 18 Regressionstests zum Ausgangsverhalten und alle Belege liegen unter reports/audit/evidence/ENG.

### Befunde

#### ENG-01 (P0): Live-Modus: Sicherheitsdeckel max_order_usd blockiert auch Schließ-Orders

- **Sicherheit des Prüfers:** hoch
- **Stand:** **bestätigt** (eigene Gegenprüfung)
- **Evidenz:** vorwaertstest/bot.py:130-131: `if menge * preis > cfg["max_order_usd"]: raise YubitFehler(...)` gilt für jede Order, auch reduce_only; bot.py:254-256 fängt den Fehler nur als Hinweis ab. Experiment mit nachgestelltem Konto (reports/audit/evidence/ENG/d_bot_experimente.txt, Schlüssel D8_live): Short 1,0 Stück zu 100 USD, Deckel 150 USD. Kurs 160, Signal dreht: Warnung "Order über dem Sicherheitsdeckel (160 > 150 USDT)", Position an der Börse bleibt -1,0. Kurs 200 und ausgelöstes Tageslimit: wieder keine Schließ-Order für AAA, gesperrt_tag gesetzt. Abstand Deckel zu Sollbetrag: config.json:8 150 USD bei 100 USD (50 %), config_lauf.json:19 und config_lauf_tpsl.json:19 2000 USD bei 1500 USD (33 %). Im Entwicklungszeitraum gab es innerhalb eines Trades eine Gegenbewegung von 38,1 % (ADA-Short 24.02. bis 02.03.2025, g_hebel3_entwicklung.txt).
- **Auswirkung:** Steigt der Wert einer Short-Position über den Deckel, kann der Bot sie nicht mehr schließen: weder durch Umkehrsignal noch durch Stop noch durch das Tageslimit. Der Verlust läuft unbegrenzt weiter, gemeldet wird nur ein Hinweis auf der Standardausgabe. Betrifft nur den Live-Modus; der Papier-Modus prüft den Deckel nicht.
- **Empfehlung:** Deckel nur auf eröffnende Orders anwenden; reduce-only-Orders immer zulassen (bei Bedarf in Teilen unterhalb des Deckels). Scheitert eine Schließ-Order, Alarm auslösen statt nur Hinweis. Den Test test_ist_live_sicherheitsdeckel_blockiert_auch_das_schliessen nach der Korrektur umdrehen.
- **Nachstellen:** cd /home/user/OdinGate-Botv134/swing-hybrid && NUMBA_CACHE_DIR=$(mktemp -d) .venv/bin/python -I -B -m pytest -q -p no:cacheprovider --basetemp=$(mktemp -d) reports/audit/evidence/ENG/test_eng_ausgangsverhalten.py -k sicherheitsdeckel

#### ENG-02 (P0): Kein Margin- und Liquidationsmodell bei Hebel 3; Einbruchskennzahl unterschätzt den Verlust eines frisch gestarteten Kontos

- **Sicherheit des Prüfers:** hoch
- **Stand:** **bestätigt** (eigene Gegenprüfung)
- **Evidenz:** src/hybrid/engine2.py:161-170 und vorwaertstest/kern.py:83-88 rechnen ohne Untergrenze weiter; bot.py:165 hält die Größe fest auf kapital_usd x hebel / Anzahl Coins. Hebel oder Margin-Modus der Börse werden nirgends gelesen oder gesetzt (nur Anzeige dashboard_daten.py:66-67, aktuell 97,7 % des Kontos als Margin gebunden). reports/audit/evidence/ENG/g_hebel3_entwicklung.txt (nur Entwicklungszeitraum, Kandidat, Hebel 3, feste Größe, 5-Minuten-Basis): Konto <= 0 binnen 365 Tagen bei 8,4 % von 960 Starttagen, <= 50 % bei 46,6 %; binnen 90 Tagen <= 0 bei 5,7 %; ohne Rebate <= 0 bei 44,9 %. Größter Rückgang 170,7 % des Startkapitals, runner.max_drawdown (runner.py:79-83, relativ zum Höchststand) meldet dafür 38,4 %. Bei Hebel 1: 50,7 % des Startkapitals gegen gemeldete 24,6 % (a_engine_parity.txt). engine2 ist exakt linear im Hebel (f_gleichstand_hebel.txt: |e3 - 3*e1| <= 1,4e-14). Bot-Experiment D10: Konto rechnerisch bei -2.514 USD, Bot hält weiter 15.000 USD Short, gesperrt_tag leer.
- **Auswirkung:** Rückrechnung und Vorwärtstest weisen auch für Verläufe ein Ergebnis aus, in denen ein echtes Konto bei Hebel 3 liquidiert wäre. Die gemeldeten Einbrüche (24,6 % im Protokoll, einbruch_pct im Dashboard) beziehen sich auf den Höchststand samt aufgelaufener Gewinne bei nicht mitwachsender Position; für neu eingesetztes Geld sagen sie zu wenig. Bei echtem Geld ist ein Totalverlust möglich, ohne dass eine vorhandene Kennzahl davor warnt.
- **Empfehlung:** Liquidation in engine2 und im Bot abbilden (Konto unter Erhaltungsmargin: alles schließen, Lauf als Ausfall werten). Zusätzlich den Einbruch in Einheiten des Startkapitals und den Anteil der Starttage mit Kontoausfall berichten. Die Hebelwahl darauf stützen, ausschließlich mit Entwicklungsdaten. Im Live-Modus Hebel und Margin-Modus der Börse lesen und gegen die Konfiguration prüfen.
- **Nachstellen:** cd /home/user/OdinGate-Botv134/swing-hybrid && NUMBA_CACHE_DIR=$(mktemp -d) .venv/bin/python -I -B reports/audit/evidence/ENG/g_hebel3_entwicklung.py

#### ENG-03 (P1): Test 2 prüft Stop und Gewinnziel bei jedem Lauf statt am Stundenschluss und misst damit eine andere Regel als Runde 24

- **Sicherheit des Prüfers:** hoch
- **Stand:** Gegenprüfung abgebrochen; Zahlen beim Wiederholen identisch
- **Evidenz:** src/hybrid/tpsl.py:19-40: Prüfung je Stundenschluss, Einstiegsreferenz ist der Stundenschluss. vorwaertstest/bot.py:216-228: Prüfung bei jedem Lauf mit dem Mittelkurs gegen den Füllkurs (z["einstieg"]). Läufe im Median alle 5 Minuten (e_snapshot_identitaeten.txt, Punkt 6). reports/audit/evidence/ENG/c_tpsl_takt.txt (Entwicklungszeitraum, Hebel 1, tp 0,15 / sl 0,05 fest): hybrid.tpsl 33,3 % pro Jahr, Sharpe 1,135, Einbruch 14,6 %; Bot-Logik mit einem Lauf je Stunde 34,0 % / 1,159 / 14,2 % (236 Stops, 371 Ziele); Bot-Logik alle 5 Minuten 29,7 % / 1,035 / 16,6 % (373 Stops, 379 Ziele). Experiment D13: Bot stoppt 20 Minuten nach der vollen Stunde bei -5,5 %, tpsl._zustand bleibt bei den Stundenschlüssen 100 / 99 / 99,5 investiert.
- **Auswirkung:** 58 % mehr Stops und rund 4,3 Prozentpunkte weniger Ertrag pro Jahr bei Hebel 1 (linear etwa 13 bei Hebel 3) gegenüber der protokollierten Variante sl5_tp15. Die Ergebnisse von Test 2 lassen sich nicht mit Runde 24 vergleichen und hängen vom Lauf-Takt ab, also von einem Betriebsdetail.
- **Empfehlung:** Festlegen und im Protokoll dokumentieren, welche Regel gilt. Entweder prüft der Bot Stop und Ziel nur beim ersten Lauf nach Stundenschluss gegen den Stundenschluss (wie tpsl), oder die 5-Minuten-Prüfung wird als eigene, vorab protokollierte Variante im Entwicklungszeitraum nachgerechnet. Bis dahin Test 2 als nicht mit der Rückrechnung vergleichbar kennzeichnen; bestehende Daten nicht ändern.
- **Nachstellen:** cd /home/user/OdinGate-Botv134/swing-hybrid && NUMBA_CACHE_DIR=$(mktemp -d) .venv/bin/python -I -B reports/audit/evidence/ENG/c_tpsl_takt.py

#### ENG-04 (P1): Tagesverlust-Limit in beiden Tests faktisch aus; die dokumentierte Sicherung von 3 % ist bei Hebel 3 laut Rückrechnung nicht tragfähig

- **Sicherheit des Prüfers:** hoch
- **Stand:** „Limit faktisch aus“ über ENG-02, QD-04 bestätigt
- **Evidenz:** vorwaertstest/config_lauf.json:17 und config_lauf_tpsl.json:17: "tagesverlust_limit": 1.0; bot.py:196 löst damit erst bei einem Tagesverlust von 100 % des Kapitals aus; bot.konfig (bot.py:41-47) prüft den Wert nicht. README.md:47 nennt als Live-Sicherung "Tagesverlust-Limit 3 %", config.json:6 und config.yaml haben 0,03. Die Kandidaten-Kennzahlen sind ohne Limit gerechnet (scripts/suche_runde21.py:19 und suche_runde24.py:19, day_limit=9.0). reports/audit/evidence/ENG/g_hebel3_entwicklung.txt (Entwicklungszeitraum): Hebel 1 ohne Limit +59,4 % pro Jahr, mit 3 % +13,2 % (269 Sperrtage von 1325); Hebel 3 ohne Limit +178,1 %, mit 3 % -101,3 % (826 Sperrtage). Experiment D10b: bei Hebel 3 reicht eine Kursbewegung von 1,5 %, um das 3-%-Limit auszulösen.
- **Auswirkung:** Es gibt keinen wirksamen, getesteten Verlustbegrenzer. Die einzige eingebaute Sicherung würde bei Hebel 3 den gemessenen Vorteil in einen Verlust drehen, ohne sie besteht kein Schutz (siehe ENG-02). Die README beschreibt eine Sicherung, die in keinem der beiden laufenden Tests aktiv ist.
- **Empfehlung:** Verlustbegrenzung als Teil der Strategie vorab im Protokoll festlegen, in engine2 und Bot identisch rechnen und nur im Entwicklungszeitraum prüfen. bot.konfig soll Werte ab 1 ablehnen oder ausdrücklich als abgeschaltet kennzeichnen. README an den getesteten Stand anpassen.
- **Nachstellen:** cd /home/user/OdinGate-Botv134/swing-hybrid && NUMBA_CACHE_DIR=$(mktemp -d) .venv/bin/python -I -B reports/audit/evidence/ENG/g_hebel3_entwicklung.py   # letzte zwei Zeilen

#### ENG-05 (P1): Ergebnis hängt am angenommenen Rebate; der Bot bucht es als erzielten Ertrag und zeigt es als Kopfzahl

- **Sicherheit des Prüfers:** hoch
- **Stand:** Sachverhalt über QD-03, QR-02 bestätigt
- **Evidenz:** reports/audit/evidence/ENG/h_kostenzerlegung.txt (engine2, Gruppe A, Hebel 1): Entwicklung netto mit Rebate +215,6 %, davon Rebate 101,8 Punkte (47 %), ohne Rebate +31,4 % pro Jahr. Prüfzeitraum netto mit Rebate +25,9 % (16,5 % pro Jahr), Rebate 45,4 Punkte, ohne Rebate -19,6 % (-12,5 % pro Jahr). Gebühr vor Rebate rund 33 % des Kapitals pro Jahr bei Hebel 1. bot.py:252-253 bucht 85 % der Gebühr sofort als Rebate; bot.py:245 setzt im Live-Modus rebate = 0.0 ("wird von Yubit getrennt gutgeschrieben, hier nicht sichtbar"). Dashboard-Kopfzahl und Verlauf sind "mit Rebate" (docs/index.html:123, 227-228). vorwaertstest/YUBIT_REGELN.md Abschnitt 2: Yubit kann Rebates abziehen.
- **Auswirkung:** Der unabhängige Prüfzeitraum ist nur durch die Rebate-Annahme positiv. Der Vorwärtstest kann diese Annahme nicht prüfen (Papier rechnet sie fest ein, Live sieht sie nicht), weist sie aber als verdient aus. Entscheidungen auf Basis der Kopfzahl stützen sich auf einen nicht gemessenen Ertragsbestandteil.
- **Empfehlung:** Netto ohne Rebate als Kopfzahl oder gleichrangig zeigen und das Rebate als offene Forderung getrennt führen. Vor Live eine schriftliche Zusage von Yubit einholen und Gutschriften im Live-Modus mit dem Konto abgleichen. Jede Entscheidungsvorlage muss beide Sichten enthalten.
- **Nachstellen:** cd /home/user/OdinGate-Botv134/swing-hybrid && NUMBA_CACHE_DIR=$(mktemp -d) .venv/bin/python -I -B reports/audit/evidence/ENG/h_kostenzerlegung.py

#### ENG-06 (P1): Live-Ausführung: Füllungen werden einmal nach 1,5 Sekunden abgefragt; verspätete Füllungen führen zu Abbruch und unbeaufsichtigter Position

- **Sicherheit des Prüfers:** mittel
- **Stand:** nicht gegengeprüft
- **Evidenz:** vorwaertstest/bot.py:135-145: time.sleep(1.5), ein einziger Abruf der Fills, Storno-Fehler werden verschluckt. yubit.py:130-138: Limit-Order ohne timeInForce, die orderLinkId wird nicht gespeichert. bot.py:177-182: Abweichung zwischen Börse und Protokoll beendet den Lauf mit SystemExit. bot.py:276-281: Zustand und Protokoll werden erst nach allen Orders geschrieben. Experiment mit nachgestelltem Konto (d_bot_experimente.txt, D8_live.fills_spaet): Börse hält -1,0 / -2,0, Protokoll leer ("nichts gefüllt"), der nächste Lauf bricht ab mit "Position laut Börse -1.0 weicht vom Protokoll 0.0 ab. Kein Handel." README.md:52-53: der Live-Teil ist nie gegen ein echtes Konto gelaufen. Wie schnell Yubit Fills meldet, ist nicht bekannt, daher Vertrauen mittel.
- **Auswirkung:** Eine gewöhnliche Verzögerung der Börse genügt, damit der Bot dauerhaft stehen bleibt. Die offenen, gehebelten Positionen laufen dann ohne Signal, Stop und Tageslimit weiter; die Meldung erscheint nur auf der Standardausgabe. Stürzt der Prozess nach einer Order ab, fehlt sie im Zustand, mit derselben Folge.
- **Empfehlung:** Vor Live: Fills mit Wiederholung und Zeitlimit abholen, offene Orders und Positionen der Börse als maßgeblich übernehmen (Abgleich statt Abbruch), orderLinkId vor dem Senden speichern, sofort ausführbare Orderart nutzen, falls die API sie anbietet, und einen Alarmweg einrichten. Tests mit verzögerten und teilweisen Fills ergänzen.
- **Nachstellen:** cd /home/user/OdinGate-Botv134/swing-hybrid && .venv/bin/python -I -B reports/audit/evidence/ENG/d_bot_experimente.py $(mktemp -d)   # Schlüssel D8_live.fills_spaet

#### ENG-07 (P2): Funding im Bot: gebucht wird der Ticker-Satz nach dem Termin, multipliziert mit der Zahl verpasster Termine

- **Sicherheit des Prüfers:** mittel
- **Stand:** nicht gegengeprüft (nicht vorgesehen)
- **Evidenz:** vorwaertstest/bot.py:184-189 ("Näherung mit der aktuellen Rate"), kern.py:91-96, yubit.py:92. Die echte Ticker-Antwort in tests/fixtures/yubit_ticker.json führt fundingRate zusammen mit nextFundingTime (2026-11-14 16:00 UTC), der Satz gehört also zum kommenden Termin. Experiment D5 (d_bot_experimente.txt): Satz vor dem Termin +0,01 %, Ticker danach -0,03 %: gebucht +4,50 USD statt -1,50 USD auf 15.000 USD Long; drei Termine ohne Lauf: dreimal der aktuelle Satz (+13,50 USD). Realer Lauf Test 1: einziger Termin 16:00 UTC, gebucht um 16:04: -1,1503 USD = -0,00785 % auf 14.647 USD Short (e_snapshot_identitaeten.txt). Rückrechnung: Funding -23,2 Punkte im Entwicklungszeitraum, etwa -6,4 % pro Jahr bei Hebel 1 (h_kostenzerlegung.txt). Vorzeichen und Einheit sind in Ordnung (siehe correct).
- **Auswirkung:** Die Funding-Spalte des Vorwärtstests ist eine Näherung mit unbekanntem Fehler; bei Hebel 3 geht es in der Rückrechnung um rund 19 % des Kapitals pro Jahr. Auf Handelsentscheidungen wirkt das nicht, wohl aber auf den Vergleich Vorwärtstest gegen Rückrechnung. Im Live-Modus würde das Kontrollbuch vom echten Konto abweichen.
- **Empfehlung:** Den Satz des letzten Laufs vor dem Termin verwenden (beim 5-Minuten-Takt vorhanden) oder die Funding-Historie der Börse abrufen. Verpasste Termine in stand.csv kennzeichnen. Im Live-Modus die tatsächlichen Funding-Buchungen abgleichen.
- **Nachstellen:** cd /home/user/OdinGate-Botv134/swing-hybrid && NUMBA_CACHE_DIR=$(mktemp -d) .venv/bin/python -I -B -m pytest -q -p no:cacheprovider --basetemp=$(mktemp -d) reports/audit/evidence/ENG/test_eng_ausgangsverhalten.py -k funding

#### ENG-08 (P2): Teilausfall der Marktdaten: Coin wird übersprungen, Position bleibt, Bewertung mit altem Kurs ohne Kennzeichen

- **Sicherheit des Prüfers:** hoch
- **Stand:** nicht gegengeprüft (nicht vorgesehen)
- **Evidenz:** vorwaertstest/bot.py:168-173 überspringt einen Coin bei Datenfehler; bot.py:88 akzeptiert eine bis zu 2 Stunden alte Kerze ohne Hinweis; bot.py:272-279 schreibt stand.csv ohne Kennzeichen. Bereits eingetreten: Test 1, Lauf 2026-11-15 15:16 UTC, nur 5 von 10 Coins in spannen.csv (BTC, ETH, SOL, XRP, DOT), Zeile in stand.csv unauffällig (reports/audit/evidence/ENG/j_teilausfall.txt). Experiment D7: Referenzkerze fehlt, Kurs fällt von 100 auf 70; der Bot hält die Long-Position und meldet brutto -11,25 USD statt -2.261,25 USD. Experiment D6: Kerze 1 h 05 min nach Schluss wird ohne Warnung benutzt, ab 2 h 05 min Abbruch. Die Rückrechnung geht bei fehlenden Daten flach (Signal 0; SOL, XRP, LTC je 120 Stunden vom 26.02. bis 02.03.2022, b_signal_luecken.txt).
- **Auswirkung:** Bei Teilausfällen zeigt der Stand einen falschen Wert; Umkehr und Stop (Test 2) werden für den betroffenen Coin in diesem Lauf nicht ausgeführt. Im Live-Modus bliebe die Position so lange unbeaufsichtigt. Bisher ein belegter Fall in 64 Läufen.
- **Empfehlung:** In stand.csv je Lauf festhalten, wie viele Coins mit frischem Kurs bewertet wurden und welche fehlten. Nach N fehlgeschlagenen Läufen je Coin Alarm. Das Alter der verwendeten Kerze protokollieren und über einer Stunde warnen. Verhalten bei fehlenden Daten festlegen und in Rückrechnung und Bot gleich umsetzen.
- **Nachstellen:** cd /home/user/OdinGate-Botv134/swing-hybrid && T=$(mktemp -d) && cp -r vorwaertstest/lauf vorwaertstest/lauf_tpsl $T/ && .venv/bin/python -I -B reports/audit/evidence/ENG/j_teilausfall.py $T

#### ENG-09 (P2): Teilfüllungen werden nicht nachgeführt; Mengenrundung falsch bei Schrittweiten, die keine Zehnerpotenz sind

- **Sicherheit des Prüfers:** hoch
- **Stand:** nicht gegengeprüft (nicht vorgesehen)
- **Evidenz:** vorwaertstest/bot.py:229 vergleicht nur die Richtung (`if ziel == ist_richtung: continue`), bot.py:268-270 bricht nach einer Teilfüllung ab. Experiment D2: Soll 75,0 Stück, gefüllt 6,0; im nächsten Lauf mit vollem Buch keine Order, Position bleibt 6,0. kern.py:28-29 und 33-35 runden auf Dezimalstellen: Experiment D4: menge_runden(10, 13, 0.25, 0.25) = 0.8 statt 0.75 (kein Vielfaches der Schrittweite, über dem Zielbetrag), als_text(0.75, 0.25) = "0.8". Real: alle 10 Coins haben Zehnerpotenz-Schritte; BTC erreicht 96,4 % des Sollbetrags (Schritt 0,001 BTC, rund 65 USD), die Summe 99,5 % (e_snapshot_identitaeten.txt). 0 von 775 Messungen ohne volle Buchtiefe.
- **Auswirkung:** Derzeit ohne Wirkung auf die beiden Tests. Bei dünnerem Buch, kleinerem Kapital oder weiteren Coins bliebe eine Position bis zum nächsten Dreh zu klein, bzw. im Live-Modus ginge eine ungültige Ordermenge an die Börse. Im Live-Modus sind Teilfüllungen wegen der Preisgrenze von 0,05 % wahrscheinlicher als im Papier-Modus, der das ganze Buch füllt.
- **Empfehlung:** Zielmenge statt Zielrichtung vergleichen (Toleranz eine Schrittweite) und Reste nachführen. Auf Vielfache der Schrittweite mit Decimal runden. Die beiden test_ist-Tests nach der Korrektur umdrehen.
- **Nachstellen:** cd /home/user/OdinGate-Botv134/swing-hybrid && NUMBA_CACHE_DIR=$(mktemp -d) .venv/bin/python -I -B -m pytest -q -p no:cacheprovider --basetemp=$(mktemp -d) reports/audit/evidence/ENG/test_eng_ausgangsverhalten.py -k "teilfuellung or runden"

#### ENG-10 (P2): Vorwärtstest ist kein 1:1-Abbild der Rückrechnung: 23 semantische Unterschiede; Test 1 und Test 2 untereinander nicht direkt vergleichbar

- **Sicherheit des Prüfers:** hoch
- **Stand:** nicht gegengeprüft (nicht vorgesehen)
- **Evidenz:** Vollständige Liste mit Fundstellen und Bewertung: reports/audit/evidence/ENG/semantik_backtest_vs_bot.txt. Ergebniswirksam sind: Stop/Ziel-Takt (ENG-03), Hebel 3 ohne Liquidation gegen Kennzahlen bei Hebel 1 (ENG-02), Funding-Näherung (ENG-07), Kursquelle Yubit gegen Binance (nicht messbar, keine Yubit-Historie im Repo), Start mitten im Trend. Klein oder zugunsten der Rückrechnung: Verzug der Ausführung (5 Minuten später: 59,4 auf 57,8 % pro Jahr, Sharpe 0,946 auf 0,919, c_tpsl_takt.txt), Slippage (gemessen 1,58 bp im Mittel gegen 2,95 bp Annahme, e_snapshot_identitaeten.txt), Rundung der Stückzahl. Test 1 startete 13:21 UTC, Test 2 17:44 UTC, beide mit sofortigem Einstieg: Stand 18:58 UTC +264,57 USD gegen -10,45 USD, seit 17:46 aber -9,70 gegen -6,44 USD. Der Abstand von 5,5 % des Kapitals ist ein Startzeit-Effekt und keine Wirkung von Stop und Ziel.
- **Auswirkung:** Ohne diese Liste werden Abweichungen zwischen Vorwärtstest und Rückrechnung leicht der Strategie zugeschrieben, obwohl sie aus der Messanordnung stammen. Ein Vergleich der Kontostände von Test 1 und Test 2 führt derzeit zu einem falschen Schluss über Stop und Gewinnziel.
- **Empfehlung:** Yubit-Stundenkerzen je Lauf mitschreiben und den Vorwärtstest regelmäßig gegen eine Schatten-Rückrechnung derselben Stunden mit engine2 prüfen. Test 1 und Test 2 nur ab einem gemeinsamen Zeitpunkt bzw. je Coin ab dem ersten gemeinsamen Dreh vergleichen. Tagesschlüsse aus stand.csv bilden, bevor ein Sharpe berechnet wird.
- **Nachstellen:** cat /home/user/OdinGate-Botv134/swing-hybrid/reports/audit/evidence/ENG/semantik_backtest_vs_bot.txt

#### ENG-11 (P3): Kleinere Unstimmigkeiten in Beschriftung und Anzeige (Sammelbefund)

- **Sicherheit des Prüfers:** hoch
- **Stand:** nicht gegengeprüft (nicht vorgesehen)
- **Evidenz:** (a) Takt: README.md:10 und docs/index.html:135 sagen stündlich, dashboard_daten.py:12 TAKT_MINUTEN = 60, index.html:478 zählt auf Minute 4 herunter, bot.py:314 "zur vollen Stunde"; gemessen läuft der Bot im Median alle 5 Minuten, also sind auch die Spannen-Messungen 5-Minuten-Werte. (b) bot.py:318 vergleicht die gemessene Slippage mit festen 5 bp; der Kandidat wurde mit 0,5 bis 13,2 bp je Coin gerechnet, im Mittel 2,95 bp (research.py:272-279). (c) "brutto" enthält in runner.py:14, 50 das Funding, in kern.py:85-86 nicht. (d) docs/index.html:192-204 bewertet Yubit-Positionen live mit Binance-Kursen; mit Bot-Kursen weicht die Browser-Formel nur durch Rundung ab (höchstens 0,02 USD). (e) Die STOPP-Datei hält an, schließt aber keine Position (bot.py:151-153, Experiment D9); die README nennt sie Notbremse. (f) Zwei Läufe in derselben Minute erzeugen doppelte Zeilen in stand.csv und spannen.csv, aber keine doppelten Orders (Experiment D14). (g) Gleichstand bedeutet in Rückrechnung und Bot flach, nicht short; in den Binance-Daten 146 solche Phasen, 2026 bei DOT 15 Stunden (f_gleichstand_hebel.txt). Ein Gleichstand löst außerdem die Sperre nach Stop oder Ziel (Experiment D1b), in beiden Implementierungen gleich.
- **Auswirkung:** Keine Wirkung auf die Rechnung, aber Missverständnisse beim Lesen von Bericht und Dashboard und beim Vergleich von Spalten zwischen Rückrechnung und Vorwärtstest.
- **Empfehlung:** Texte und Konstanten an den tatsächlichen Takt anpassen oder den Takt auf stündlich zurückstellen. Slippage-Urteil gegen die Annahme je Coin rechnen. Spalten einheitlich benennen. In der README klarstellen, dass STOPP nicht schließt. Die Regelbeschreibung um den Gleichstand ergänzen.
- **Nachstellen:** cd /home/user/OdinGate-Botv134/swing-hybrid && .venv/bin/python -I -B reports/audit/evidence/ENG/d_bot_experimente.py $(mktemp -d)   # Schlüssel D1, D1b, D9, D14

### Nachgerechnete Aussagen

- **reproduziert**: Entwicklung: +59 % pro Jahr, Sharpe 0,95 (Kandidat, Gruppe A, Einsatz 100 %, Yubit-Kosten mit Rebate, ohne Tageslimit). engine2: 59,40 % pro Jahr, Sharpe 0,946, Einbruch 24,58 % (D1 0,564, D2 1,317). Unabhängige Nachrechnung ohne engine2 mit denselben Zielgewichten: größte Abweichung im Tagesergebnis je Coin 3,3e-16; mit eigenem, zeitbasiertem Signal 59,34 % und Sharpe 0,944 (Unterschied nur durch die 120-Stunden-Datenlücke bei SOL, XRP, LTC). Befehl: `cd /home/user/OdinGate-Botv134/swing-hybrid && NUMBA_CACHE_DIR=$(mktemp -d) .venv/bin/python -I -B reports/audit/evidence/ENG/a_engine_parity.py`
- **reproduziert**: Unabhängiger Prüfzeitraum: +16,5 % pro Jahr, Sharpe 0,34. engine2 und Nachrechnung: 16,52 % pro Jahr, Sharpe 0,337, netto +25,85 % über 571 Tage, Einbruch 31,3 %. Einschränkung: ohne Rebate -19,6 % (h_kostenzerlegung.txt). Befehl: `cd /home/user/OdinGate-Botv134/swing-hybrid && NUMBA_CACHE_DIR=$(mktemp -d) .venv/bin/python -I -B reports/audit/evidence/ENG/a_engine_parity.py`
- **abweichend**: Signal: long, wenn der Schlusskurs der letzten abgeschlossenen Stunde über dem von 336 Stunden zuvor liegt, andernfalls short. Rückrechnung (mutationen.py:22-23) und Bot (kern.py:14-19, bot.py:84-102) setzen dieselbe Regel um, aber bei exaktem Gleichstand gehen beide flach statt short. In den Binance-Daten 146 solche Phasen über zehn Coins. Der Vergleichskurs ist in beiden die Kerze genau 336 Stunden früher; der gemeinsame Stundenindex ist lückenlos (59.904 Stunden). Befehl: `cd /home/user/OdinGate-Botv134/swing-hybrid && NUMBA_CACHE_DIR=$(mktemp -d) .venv/bin/python -I -B reports/audit/evidence/ENG/b_signal_luecken.py`
- **abweichend**: Stündliche Signalprüfung. Das Signal ändert sich nur stündlich, der Bot läuft aber im Median alle 5 Minuten (Test 1: 64 Läufe in 5,6 Stunden, Abstand 1 bis 13 Minuten; erster Lauf nach voller Stunde in Minute 1 bis 5). Für Test 1 ohne Wirkung auf das Signal, für Test 2 wesentlich (ENG-03). Befehl: `cd /home/user/OdinGate-Botv134/swing-hybrid && T=$(mktemp -d) && cp -r vorwaertstest/lauf vorwaertstest/lauf_tpsl $T/ && NUMBA_CACHE_DIR=$(mktemp -d) .venv/bin/python -I -B reports/audit/evidence/ENG/e_snapshot_identitaeten.py $T`
- **reproduziert**: 10 Kryptowährungen, gleichgewichtet, zwei Papier-Tests mit Hebel 3 seit 15.11.2026. config_lauf.json und config_lauf_tpsl.json: 10 Coins, Hebel 3,0, Kapital 5.000 USD, Sollbetrag 1.500 USD je Coin. Test 1 Start 13:21 UTC, Test 2 Start 17:44 UTC. Effektiver Hebel 2,985 bzw. 2,992; BTC durch die Schrittweite 96,4 % des Sollbetrags, die übrigen 98,9 bis 100 %. Ein früherer Lauf mit Hebel 1 von 13:00 UTC liegt in lauf_hebel1_archiv. Befehl: `cd /home/user/OdinGate-Botv134/swing-hybrid && T=$(mktemp -d) && cp -r vorwaertstest/lauf vorwaertstest/lauf_tpsl $T/ && NUMBA_CACHE_DIR=$(mktemp -d) .venv/bin/python -I -B reports/audit/evidence/ENG/e_snapshot_identitaeten.py $T`
- **abweichend**: Test 2: zusätzlich Stop 5 % und Gewinnziel 15 % (Runde 24, Variante sl5_tp15: 33 % pro Jahr, Sharpe 1,13, Einbruch 14,6 %, 56 % der Zeit im Markt). Die Protokollzeile ist reproduziert (33,27 % / 1,135 / 14,56 % / 56,35 %). Der Bot setzt die Regel aber anders um (Prüfung alle 5 Minuten gegen den Füllkurs): 29,7 % / 1,035 / 16,6 %, 373 statt 236 Stops im Entwicklungszeitraum. Befehl: `cd /home/user/OdinGate-Botv134/swing-hybrid && NUMBA_CACHE_DIR=$(mktemp -d) .venv/bin/python -I -B reports/audit/evidence/ENG/c_tpsl_takt.py`
- **reproduziert**: Kontorechnung des Papier-Bots ist in sich stimmig (Zustand, stand.csv, Orderprotokoll, Dashboard, Browser). Beide Tests, Stand 18:58 UTC: kern.vermoegen(zustand) gleich der letzten Zeile von stand.csv (Abweichung unter 0,0001 USD), brutto aus protokoll.csv neu gerechnet identisch (267,5080 bzw. -8,6558), Gebühr genau 0,08 % des Volumens, Rebate genau 85 % der Gebühr, dashboard.json 264,57 / -10,45, Browser-Formel 264,5680 / -10,4558, Einbruch 1,820 / 1,247 % nachgerechnet gleich. Befehl: `cd /home/user/OdinGate-Botv134/swing-hybrid && T=$(mktemp -d) && cp -r vorwaertstest/lauf vorwaertstest/lauf_tpsl $T/ && NUMBA_CACHE_DIR=$(mktemp -d) .venv/bin/python -I -B reports/audit/evidence/ENG/e_snapshot_identitaeten.py $T`
- **reproduziert**: Bestehende Tests: 105 Tests grün. 105 passed in 13,5 s, ohne Schreibzugriffe im Repo (Cache und temporäre Verzeichnisse umgeleitet). Befehl: `cd /home/user/OdinGate-Botv134/swing-hybrid && NUMBA_CACHE_DIR=$(mktemp -d) .venv/bin/python -I -B -m pytest -q -p no:cacheprovider --basetemp=$(mktemp -d) tests`
- **reproduziert**: Börse Yubit: Funding-Einheit (yubit.ticker teilt fundingRate durch 1e6). Nur indirekt belegt: In der aufgezeichneten Ticker-Antwort steht price24hPcnt = -41317 bei lastPrice 66480,3 und prevPrice24h 69345,5, das sind -4,1318 %; die Prozentfelder haben also die Einheit 1e-6, fundingRate "100" entspricht 0,01 %. Im echten Lauf wurde Funding nur zum 8-Stunden-Termin 16:00 UTC gebucht (-0,00785 % auf 14.647 USD Short), eine plausible Größe. Ein direkter Abgleich mit einer Yubit-Abrechnung fehlt. Befehl: `cat /home/user/OdinGate-Botv134/swing-hybrid/tests/fixtures/yubit_ticker.json`

### Als richtig befunden

- engine2 im Taker-Modus (Stückzahl = hebel/N / Open, Dreh als eine Order, Slippage-Vorzeichen, Gebühr auf das Volumen, Funding-Vorzeichen, Schlussabrechnung): unabhängige Nachrechnung auf den echten 5-Minuten-Daten weicht um höchstens 3,3e-16 je Coin und Tag ab (src/hybrid/engine2.py:84-159; reports/audit/evidence/ENG/a_engine_parity.txt)
- Identität Summe der Tagesergebnisse = Endstand: 2,4148538757 auf beiden Seiten; G - F = netto ohne Rebate und netto ohne Rebate + R = N in allen Fenstern (runner.py:48-57; a_engine_parity.txt, h_kostenzerlegung.txt)
- engine2 skaliert exakt linear mit dem Hebel: |equity(Hebel 3) - 3 x equity(Hebel 1)| <= 1,4e-14 (f_gleichstand_hebel.txt)
- Kein Blick voraus bei der Zuordnung des Stundensignals: Signal der Stunde H gilt erst ab H+1:00 (research.py:70-75; Test test_stundensignal_gilt_erst_ab_stundenschluss)
- shift(336) der Rückrechnung ist faktisch zeitbasiert: der gemeinsame Stundenindex hat 59.904 Stunden ohne Lücke; Bot und Rückrechnung vergleichen dieselben zwei Kerzen (b_signal_luecken.txt; bot.py:84-91; kern.py:14-19)
- Hebel-Semantik identisch: Bot nominal = kapital_usd x hebel / Anzahl Coins (bot.py:165), Rückrechnung S = hebel / N (research.py:150); feste Größe bis zum Dreh, kein Zinseszins auf beiden Seiten
- Gebühr und Rebate im Bot: je Order |Gebühr - 0,0008 x Volumen| <= 5e-7 und |Rebate - 0,85 x Gebühr| <= 7e-7 in beiden echten Protokollen; gleiche Sätze wie runner.py / config.yaml (e_snapshot_identitaeten.txt)
- Füllung gegen das Orderbuch (kern.buch_fill, kern.py:38-51) und Dreh als zwei Orders: kumulativ durch dasselbe Buch, Volumen wie eine einzige Order (Experiment D12, 19.960,00 USD auf beiden Wegen)
- kern.vermoegen = stand.csv = Rekonstruktion aus protokoll.csv = dashboard.json = Browser-Formel konto() (docs/index.html:192-204) für beide laufenden Tests; Einbruch und Margin-Anzeige rechnerisch richtig nachvollzogen (e_snapshot_identitaeten.txt)
- Funding-Vorzeichen: Long zahlt bei positivem Satz, Short erhält (Bot: Experiment D5, -1,50 / +1,50 USD auf 15.000 USD; engine2: Test test_engine2_taker_stueckzahl_dreh_gebuehr_funding); Termin-Raster in Minuten korrekt (kern.py:91-96; im echten Lauf nur eine Buchung um 16:04 UTC)
- Sperre nach Stop oder Ziel bis das Signal die Richtung verlässt: Bot (bot.py:218-228) und hybrid.tpsl (tpsl.py:24-28) verhalten sich gleich; Stop- und Zielkurs im Dashboard (dashboard_daten.py:35-36) passen zur Bot-Formel
- Live-Schranken: modus live ohne YUBIT_LIVE=ja oder ohne Schlüssel bricht vor jeder Order ab; modus papier bleibt Papier auch mit Umgebungsvariable und Schlüssel; live nur mit allen dreien (bot.py:107-108, 156-158; Experiment D8, Test test_live_nur_mit_modus_umgebungsvariable_und_schluessel)
- STOPP-Datei: kein Lauf, Zustand unverändert, keine neue Zeile in stand.csv (bot.py:151-153; Experiment D9)
- Wiederholter Lauf in derselben Minute löst keine zweite Order aus, weil der Bot zustandsbasiert vergleicht (Experiment D14)
- Mengenrundung für die zehn gehandelten Coins (alle Schrittweiten sind Zehnerpotenzen): abgerundet auf die Schrittweite, unter der Mindestmenge kein Einstieg mit Hinweis (kern.py:22-30; bestehender Test test_unter_mindestgroesse_wird_ausgelassen)
- Slippage-Annahme der Rückrechnung ist gegenüber der bisherigen Messung vorsichtig: gemessen 1,58 bp im Mittel über die Coins gegen 2,95 bp Annahme (DOT 7,3 gegen 13,2 bp), 635 Messungen in 5,6 Stunden; in keiner Messung lag der Durchschnittskurs jenseits der Live-Preisgrenze (e_snapshot_identitaeten.txt, i_preisgrenze.txt)
- Verzug der Ausführung um 5 Minuten wirkt im Entwicklungszeitraum nur wenig: 59,4 auf 57,8 % pro Jahr (c_tpsl_takt.txt)
- Bestehende Testsuite: 105 Tests bestanden; zusätzlich 18 Regressionstests zum Ausgangsverhalten bestanden (reports/audit/evidence/ENG/test_eng_ausgangsverhalten.py)

### Ungeklärt

- Wie stark Yubit-Stundenschlüsse von Binance-Stundenschlüssen abweichen und wie oft das Signal dadurch zu einer anderen Stunde dreht: im Repo liegt keine Yubit-Kerzenhistorie, der Bot speichert die verwendeten Kerzen nicht.
- Bedeutung von fundingRate im Yubit-Ticker (Prognose für den kommenden Termin oder zuletzt abgerechneter Satz) und die Funding-Intervalle der neun Coins außer BTC: nur aus der Fixture (nextFundingTime neben fundingRate, fundingInterval 480 für BTC) erschlossen, ohne Netz nicht prüfbar. Die Einheit 1e-6 ist nur indirekt über price24hPcnt belegt.
- Ob Yubit das Rebate von 85 % und den Taker-Satz von 0,08 % für dieses Konto tatsächlich so abrechnet, wann es gutgeschrieben wird und ob es nach YUBIT_REGELN.md Abschnitt 2 gestrichen werden kann: keine Abrechnung im Repo.
- Hebel-Einstellung, Margin-Modus (cross oder isoliert), Hedge-Modus und Liquidationsregeln des Yubit-Kontos: Der Bot liest und setzt nichts davon; die Fixture nennt nur für BTC eine Erhaltungsmargin von 0,25 %. Ab welchem Kontostand real liquidiert würde, ist daher offen; die Auswertung in ENG-02 nimmt Kontostand <= 0 als Näherung.
- Verhalten der echten Yubit-API im Live-Pfad (Meldeverzug von Fills, Unterstützung einer sofort ausführbaren Orderart, Fehlercodes beim Storno): Der Live-Teil ist laut README nie gegen ein echtes Konto gelaufen; ENG-06 ist nur mit nachgestellter Börse belegt.
- Ursache der 120-Stunden-Lücke in den Binance-Daten von SOL, XRP und LTC (26.02. bis 02.03.2022): Download-Lücke oder echte Handelspause nicht geklärt; Wirkung auf das Kandidaten-Ergebnis 0,24 Punkte über den Gesamtzeitraum.
- Warum im Lauf vom 15.11.2026 15:16 UTC nur 5 von 10 Coins Marktdaten lieferten: Die Hinweise des Bots gehen nur auf die Standardausgabe und sind nicht gespeichert.
- Ob der 5-Minuten-Takt dauerhaft so bleibt: Er ist nur aus den Zeitstempeln in stand.csv abgelesen; das Ergebnis von Test 2 hängt davon ab.
- Die Auswertung der Kontoausfälle je Starttag in f_gleichstand_hebel.txt Teil (2) umfasst auch den Prüfzeitraum und ist rein beschreibend; für Befunde wurde nur g_hebel3_entwicklung.txt (ausschließlich Entwicklungszeitraum) herangezogen. Es wurden keine Parameter gewählt oder verändert.

### Evidenzdateien

- `/home/user/OdinGate-Botv134/swing-hybrid/reports/audit/evidence/ENG/semantik_backtest_vs_bot.txt`
- `/home/user/OdinGate-Botv134/swing-hybrid/reports/audit/evidence/ENG/test_eng_ausgangsverhalten.py`
- `/home/user/OdinGate-Botv134/swing-hybrid/reports/audit/evidence/ENG/test_eng_ausgangsverhalten.txt`
- `/home/user/OdinGate-Botv134/swing-hybrid/reports/audit/evidence/ENG/a_engine_parity.py`
- `/home/user/OdinGate-Botv134/swing-hybrid/reports/audit/evidence/ENG/a_engine_parity.txt`
- `/home/user/OdinGate-Botv134/swing-hybrid/reports/audit/evidence/ENG/b_signal_luecken.py`
- `/home/user/OdinGate-Botv134/swing-hybrid/reports/audit/evidence/ENG/b_signal_luecken.txt`
- `/home/user/OdinGate-Botv134/swing-hybrid/reports/audit/evidence/ENG/c_tpsl_takt.py`
- `/home/user/OdinGate-Botv134/swing-hybrid/reports/audit/evidence/ENG/c_tpsl_takt.txt`
- `/home/user/OdinGate-Botv134/swing-hybrid/reports/audit/evidence/ENG/d_bot_experimente.py`
- `/home/user/OdinGate-Botv134/swing-hybrid/reports/audit/evidence/ENG/d_bot_experimente.txt`
- `/home/user/OdinGate-Botv134/swing-hybrid/reports/audit/evidence/ENG/e_snapshot_identitaeten.py`
- `/home/user/OdinGate-Botv134/swing-hybrid/reports/audit/evidence/ENG/e_snapshot_identitaeten.txt`
- `/home/user/OdinGate-Botv134/swing-hybrid/reports/audit/evidence/ENG/f_gleichstand_hebel.py`
- `/home/user/OdinGate-Botv134/swing-hybrid/reports/audit/evidence/ENG/f_gleichstand_hebel.txt`
- `/home/user/OdinGate-Botv134/swing-hybrid/reports/audit/evidence/ENG/g_hebel3_entwicklung.py`
- `/home/user/OdinGate-Botv134/swing-hybrid/reports/audit/evidence/ENG/g_hebel3_entwicklung.txt`
- `/home/user/OdinGate-Botv134/swing-hybrid/reports/audit/evidence/ENG/h_kostenzerlegung.py`
- `/home/user/OdinGate-Botv134/swing-hybrid/reports/audit/evidence/ENG/h_kostenzerlegung.txt`
- `/home/user/OdinGate-Botv134/swing-hybrid/reports/audit/evidence/ENG/i_preisgrenze.py`
- `/home/user/OdinGate-Botv134/swing-hybrid/reports/audit/evidence/ENG/i_preisgrenze.txt`
- `/home/user/OdinGate-Botv134/swing-hybrid/reports/audit/evidence/ENG/j_teilausfall.py`
- `/home/user/OdinGate-Botv134/swing-hybrid/reports/audit/evidence/ENG/j_teilausfall.txt`

## Bereich RSK: Risk Engineering

Die Ausgangszahlen des Kandidaten sind exakt reproduziert (Entwicklung +59,4 % pro Jahr, Sharpe 0,95, Einbruch 24,6 %; Prüfzeitraum +16,5 % pro Jahr, Sharpe 0,34, Einbruch 31,3 %; jeweils Hebel 1), und ein unabhängiger Nachbau der Positionsführung stimmt mit dem Rechenkern auf null Abweichung überein. Bei Hebel 3 in der Bauart der Papier-Tests (feste Größe, kein wirksames Verlustlimit) schwankt das Konto je Tag um 8 bis 16 % des Startkapitals, der schlechteste Tag kostet 89 Punkte, die schlechteste Stunde 83 Punkte des Startkapitals; über alle 2.093 möglichen Starttage 02/2020 bis 10/2025 fällt das Konto binnen 365 Tagen in 51 % der Fälle unter die Hälfte und in 13 % unter null (unter der Annahme gemeinsamer Margin: Liquidation des ganzen Kontos in 14 bis 19 %). Das widerspricht dem eigenen Forschungsergebnis, das als regelkonformen Hebel 0,2 ermittelt und Hebel 3 selbst als Kontoverlust ausgewiesen hat. Weder Backtest noch Papier-Bot kennen Liquidation, Margin-Call oder eine Konto-Untergrenze (per Test belegt: der Bot führt ein Konto mit zehn offenen Positionen auf minus 50 %), und Margin-Modus, Börsenhebel und Erhaltungsmargin von Yubit sind im Repo nicht dokumentiert und werden vom Bot nicht gesetzt. Die zehn Positionen sind 1,2 bis 2,5 unabhängige Wetten, in 39 bis 48 % der Stunden stehen alle zehn in derselben Richtung (aktuell beide Tests 10 von 10 Short). Der Stop von Test 2 ist kein Börsen-Stop, Test 2 misst wegen des 5-Minuten-Takts nicht die erforschte Variante, und diese Variante hat in der Vorperiode 2020/21 das Konto bei Hebel 3 aufgebraucht.

### Befunde

#### RSK-01 (P0): Hebel 3 ohne wirksames Verlustlimit widerspricht dem eigenen Forschungsergebnis; historisch Totalverlust nach rund jedem achten Starttag binnen eines Jahres

- **Sicherheit des Prüfers:** hoch
- **Stand:** Gegenprüfung abgebrochen; Sachverhalt über QR-01, QD-04, ENG-02 bestätigt
- **Evidenz:** Konfiguration: vorwaertstest/config_lauf.json:4 und config_lauf_tpsl.json:4 "hebel": 3.0; Zeile 17 "tagesverlust_limit": 1.0 (= 100 % des Kapitals an einem Tag). Forschung: reports/suche_protokoll.md:135 ("besteht alle fünf Stufen, bei Hebel 0,2"), reports/suche_bericht.md:23 ("Das hält nur bei Hebel 0,2") und :318-331 (eigene Hebel-Tabelle mit Tageslimit: Hebel 3 Entwicklung −101,3 % pro Jahr, "Konto unter null"; "lässt sich also nicht durch Hebel zu einem guten Edge ... machen"). Diese Tabelle ist mit Abweichung 0 nachgerechnet (evidence/RSK/aus_s08_repro_hebel.txt). README.md des Vorwärtstests beschreibt weiter Hebel 0,2. Eigene Messung ohne Tageslimit, frischer Start, feste Größe (aus_s10_uebersicht.txt Tabelle 1 und 2, aus_s02_konto.txt): Hebel 3 Entwicklung: Einbruch 38,4 % vom Höchststand bzw. 170,7 Punkte des Startkapitals, schlechtester Tag −89,0 Punkte (09.12.2024), Woche −76,9, Monat −81,3, rollierend 1 h −83,0 und 24 h −121,4 Punkte, 1-%-Quantil Tag −23,0, 0,1-%-Quantil −39,2, 279 Tage unter Höchststand. Prüfzeitraum: Einbruch 55,6 % (162,8 Punkte), Tag −33,4, Monat −60,7, 240 Tage unter Höchststand (am Ende noch offen). Vorperiode: Einbruch 61,7 % (239,7 Punkte), Tag −63,1, Monat −97,3. Tagesstreuung 7,7 / 9,9 / 15,7 % des Startkapitals; Tage mit Verlust ab 10 %: 27 bis 48 pro Jahr (aus_s09_gegenprobe.txt Teil c). In den drei Standardfenstern fiel das Konto nie unter 50 % (tiefster Stand 81 bis 89 %), weil jedes Fenster mit Gewinnen beginnt. Start-Tag-Analyse (jeder Kalendertag als Start, exakt neu gerechnet, gegen den Rechenkern mit Abweichung <= 1e-16 geprüft): Hebel 3, 90 Tage: Konto < 50 % bei 33,6 %, < 25 % bei 15,5 %, < 0 % bei 5,4 % von 2.368 Starts; 365 Tage: 50,7 % / 31,4 % / 12,9 % von 2.093 Starts. Zum Vergleich Hebel 1: < 50 % bei 0,2 %, nie < 25 %; Hebel 0,2: tiefster Stand im schlechtesten Zwanzigstel 92 %. Beispiel Start 06.08.2024: unter 50 % nach 2 Tagen, unter 0 % nach 59 Tagen.
- **Auswirkung:** Mit echtem Geld wäre bei diesem Hebel ein Totalverlust kein Extremfall, sondern in der vorliegenden Historie für rund jeden achten Starttag binnen eines Jahres eingetreten, jeder dritte Start hätte binnen 90 Tagen die Hälfte verloren. Die Papier-Tests laufen in einer Einstellung, die die Forschung nie ohne Tageslimit gemessen und mit Tageslimit selbst als Kontoverlust ausgewiesen hat. Ein positiver Papier-Verlauf über Wochen sagt über dieses Risiko nichts.
- **Empfehlung:** Vor jedem Live-Handel schriftlich ein Risikobudget festlegen (höchster hinnehmbarer Kontoverlust, daraus der Hebel), abgeleitet nur aus Vorperiode und Entwicklung; die eigene Regel der Forschung (Einbruch <= 10 % Entwicklung, < 15 % Prüfzeitraum) ergibt 0,2. Die Hebel-3-Tests ausdrücklich als Kosten- und Ausführungsmessung kennzeichnen, nicht als Eignungsnachweis. Abbruchkriterien für die Papier-Tests vorab festlegen. Die Start-Tag-Analyse als feste Kennzahl in jeden Bericht aufnehmen. Kein neuer Hebelwert aus dem Prüfzeitraum ableiten.
- **Nachstellen:** cd /home/user/OdinGate-Botv134/swing-hybrid && export RSK_SCRATCH=/tmp/rsk_audit NUMBA_CACHE_DIR=/tmp/rsk_audit/numba && mkdir -p $RSK_SCRATCH && for s in s01_laeufe s02_konto s08_repro_hebel s09_gegenprobe; do .venv/bin/python -I -B reports/audit/evidence/RSK/$s.py; done

#### RSK-02 (P0): Liquidation, Margin-Call und negatives Konto sind weder im Backtest noch im Papier-Bot abgebildet; Margin-Modus, Börsenhebel und Erhaltungsmargin von Yubit sind unbekannt und werden vom Bot nicht gesetzt

- **Sicherheit des Prüfers:** hoch
- **Stand:** Sachverhalt über ENG-02 bestätigt
- **Evidenz:** Code: vorwaertstest/kern.py:83-88 (vermoegen ohne Untergrenze), bot.py:165 (Größe = kapital_usd x hebel / Coins, unabhängig vom Kontostand), bot.py:191-199 (einzige Verlustprüfung ist das Tageslimit), src/hybrid/engine2.py (kein Liquidationszweig; Konto = cash + pos x Kurs), vorwaertstest/yubit.py:19-31 (kein Endpunkt für Hebel oder Margin-Modus, order() Zeile 130-138 ohne Hebelangabe). Dokumente: YUBIT_REGELN.md, README.md und data/processed/yubit_coins.csv (Spalten gruppe, coin, gelistet, spanne_bp, min_order_usd, schritt_usd, umsatz24h_mio, funding_min) enthalten nichts zu Margin-Modus, Erhaltungsmargin, Mark-Preis oder Liquidation. Tests (evidence/RSK/test_rsk_risiko.py): test_papier_bot_kennt_weder_liquidation_noch_margin_call_noch_konto_untergrenze (zehn Shorts, Korb +30 %: Konto bei rund 10 %, keine Order, keine Warnung; +50 %: Konto −2.500 $ bei 5.000 $ Start, Positionen weiter offen, so in stand.csv geschrieben); test_rechenkern_hebel_ist_linear_und_konto_kann_negativ_werden (Konto unter −790 %, Position läuft bis zur Schlussabrechnung). Szenariorechnung unter ANNAHMEN (aus_s07_liquidation.txt, Tabellen 3 und 4 in aus_s10_uebersicht.txt): isoliert, Börsenhebel 3x: Liquidation bei 30,8 bis 32,8 % gegen den Einstieg (MMR 2,5 bis 0,5 %), Margin 500 $ je Position, alle zehn 5.000 $ = 100 % des Kontos (Test 2 aktuell: 4.989 $ von 4.990 $, frei 1 $). 5 bis 7 der 13.571 Haltephasen wären liquidiert worden (nur Schlusskurse: 4), z. B. LTC Long 03.-10.10.2025: Gegenbewegung 56,0 %, im Backtest mit −15,3 % gebucht. Bei 5x: 29 bis 47, bei 10x: 283 bis 470, bei 20x: 1.178 bis 2.639 Haltephasen. Gemeinsame Margin: Liquidation des ganzen Kontos, wenn der Korb bei gleichgerichteten Positionen um 30,1 bis 33,0 % dagegen läuft; aktuell Test 1 +32,6 bis +35,2 %, Test 2 +30,1 bis +32,7 %. Start-Tag-Analyse Hebel 3: Liquidation binnen 90 Tagen bei 6,2 bis 8,0 %, binnen 365 Tagen bei 14,4 bis 18,6 % der Starts; Hebel 1: nie. Das Dashboard rechnet "Gebundene Margin" als Positionswert / Hebel (dashboard_daten.py:66-67), eine Börsengröße, die nirgends festgelegt ist; dashboard_live.html:131 nennt nur "rund 33 % ... Konto aufgebraucht".
- **Auswirkung:** Die Ergebnisse von Backtest und Papier-Test enthalten Verläufe, die an einer echten Börse nicht möglich sind (Position überlebt eine Gegenbewegung von 56 %, Konto erholt sich aus dem Minus). Im Live-Betrieb bestimmt eine vom Bot nicht kontrollierte Kontoeinstellung bei Yubit, ob eine Position bei 4,5 %, 9,5 % oder 33 % Gegenbewegung zwangsweise geschlossen wird. Bei 3x Börsenhebel wäre die Margin vollständig gebunden; nach dem ersten Verlust fehlte Margin für Folgeorders (Annahme übliche Margin-Regeln).
- **Empfehlung:** Vor Live-Betrieb: Margin-Modus, Hebel je Symbol, Erhaltungsmargin-Stufen, Liquidationspreis-Basis (Mark-Preis) und Liquidationsgebühr von Yubit schriftlich einholen und im Repo ablegen; der Bot muss Hebel und Margin-Modus je Symbol setzen und prüfen. Im Rechenkern und im Papier-Bot eine Liquidationsprüfung und eine Konto-Untergrenze ergänzen (Margin-Quote je Lauf, Warnschwellen), erst nachdem das heutige Verhalten durch die vorhandenen Tests festgehalten ist. Dashboard: "Gebundene Margin" als Annahme kennzeichnen, Abstand zur Liquidation anzeigen.
- **Nachstellen:** cd /home/user/OdinGate-Botv134/swing-hybrid && .venv/bin/python -B -m pytest -q -p no:cacheprovider reports/audit/evidence/RSK/test_rsk_risiko.py -k "liquidation or negativ" ; export RSK_SCRATCH=/tmp/rsk_audit && .venv/bin/python -I -B reports/audit/evidence/RSK/s03_gleichzeitig.py && .venv/bin/python -I -B reports/audit/evidence/RSK/s07_liquidation.py (s01 muss vorher gelaufen sein)

#### RSK-03 (P1): Klumpenrisiko: zehn Positionen sind 1,2 bis 2,5 unabhängige Wetten; in 39 bis 48 % der Stunden stehen alle zehn in derselben Richtung

- **Sicherheit des Prüfers:** hoch
- **Stand:** nicht gegengeprüft; Korrelation von QR und QD nachgerechnet
- **Evidenz:** evidence/RSK/aus_s04_korrelation.txt und Tabellen 5, 6 in aus_s10_uebersicht.txt. Mittlere paarweise Korrelation der Tagesrenditen: Vorperiode 0,48, Entwicklung 0,65, Prüfzeitraum 0,79 (Stundenrenditen 0,57 / 0,68 / 0,77; kleinste Paar-Korrelation im Prüfzeitraum 0,65). Effektive Zahl unabhängiger Wetten der Coins (n/(1+(n-1)rho)): 1,87 / 1,46 / 1,24; der Tagesergebnisse der zehn Positionen: 3,55 / 2,52 / 1,95. Alle zehn gleichgerichtet in 36,2 / 39,0 / 48,0 % der Stunden, mindestens acht gleich in 63,5 / 73,7 / 76,6 %, längste Phase mit allen zehn gleich 25 Tage. Beta zum gleichgewichteten Korb an Tagen mit mindestens 9 Long +0,77 bis +1,46, mit mindestens 9 Short −0,69 bis −0,70; die reine Richtungswette (Netto-Richtung x Korbrendite) erklärt 58 / 76 / 67 % der Streuung des Tagesergebnisses. Gleichzeitige Verluste (aus_s03_gleichzeitig.txt): alle zehn im selben Stundenfenster im Verlust in 3,5 / 7,7 / 10,8 % der Stunden; 52 / 79 / 85 % aller Verluste entstehen in Stunden mit mindestens acht Verlierern. Größte Verluste mit allen zehn im Minus: 24 h ab 10.01.2021 −42,2 Punkte bei Hebel 1 (−126,5 bei Hebel 3), Tag 05.03.2024 −14,1 (−42,2), 24 h ab 23.07.2025 −14,9 (−44,8). Aktueller Stand beider Papier-Tests: 0 Long / 10 Short (vorwaertstest/lauf/zustand.json, lauf_tpsl/zustand.json). Der Betreiber nennt die Schwäche selbst (reports/uebergabe_fuer_dritte.md:28-29).
- **Auswirkung:** Die Gleichgewichtung über zehn Coins streut kaum. Bei Hebel 3 ist das Konto fast die Hälfte der Zeit eine einzige Richtungswette mit dem Dreifachen des Kapitals: 10 % Korbbewegung dagegen sind 30 % des Kontos. Größenregeln, die von zehn Positionen ausgehen, unterschätzen das Risiko um etwa den Faktor zwei bis drei in der Streuung.
- **Empfehlung:** Das Portfolio für die Risikosteuerung als eine Position behandeln: Netto-Richtung und Positionswert als Kennzahl führen und begrenzen (Grenzwert vorab im Protokoll festlegen, auf Entwicklungsdaten prüfen). Effektive Zahl der Wetten und Anteil gleichgerichteter Stunden in Bericht und Dashboard ausweisen. Unabhängige Bausteine sind laut Forschung bisher nicht belegt; bis dahin den Hebel an der Ein-Wetten-Sicht ausrichten.
- **Nachstellen:** cd /home/user/OdinGate-Botv134/swing-hybrid && export RSK_SCRATCH=/tmp/rsk_audit && .venv/bin/python -I -B reports/audit/evidence/RSK/s01_laeufe.py && .venv/bin/python -I -B reports/audit/evidence/RSK/s04_korrelation.py && .venv/bin/python -I -B reports/audit/evidence/RSK/s03_gleichzeitig.py

#### RSK-04 (P1): Feste Stückzahl ab Einstieg: Positionswert der Gewinner wächst bis zum 6,5- bis 7-Fachen des Startkapitals, und bei Verlusten wird nie abgebaut

- **Sicherheit des Prüfers:** hoch
- **Stand:** nicht gegengeprüft
- **Evidenz:** Code: engine2.py:88-92 (Stückzahl = Ziel x S / Kurs nur bei Einstieg oder Dreh), research.py:150 (S = hebel / Anzahl Coins, bezogen auf das Startkapital), kern.py:1-6 ("Größe wird beim Einstieg festgelegt und ... nicht angepasst"), bot.py:165. Messung (aus_s02_konto.txt, Zeilen "Positionswert / Startkapital"): bei Nennhebel 3 Maximum 6,53 (03.12.2024, Entwicklung), 7,05 (10.02.2021, Vorperiode), 4,39 (21.07.2025, Prüfzeitraum). Am 09.12.2024 20:00 UTC: XRP 4,51-fache, ADA 3,14-fache, DOT 2,28-fache Standardgröße, Summe 1,95 bei Hebel 1 = 5,84 x Startkapital bei Hebel 3; der Kurssturz 20:05 bis 21:05 (XRP −15 %, DOT −19 %, LTC −18 % auf 5-Minuten-Schluss) kostete 27,7 Punkte bei Hebel 1 und 83,0 bei Hebel 3, davon XRP 6,9 und ADA 5,4 Punkte (Ausgabe von s03b im Prüfprotokoll, Rohkerzen geprüft). DOGE am 08.02.2021 7,0-fache Standardgröße. Umgekehrt steigt der Hebel gegenüber dem laufenden Konto bei Verlusten, weil neue Positionen immer mit 1.500 $ eröffnet werden: nach −50 % Konto 6-fach, nach −75 % 12-fach. Tests: test_positionswert_waechst_mit_dem_kurs_groesse_wird_nicht_nachgefuehrt (Einsatz 30.000 $ = 6 x Kapital bei Nennhebel 3), test_rechenkern_groesse_fest_beim_einstieg_gewinner_wachsen.
- **Auswirkung:** Der Nennhebel 3 gilt nur im Moment des Einstiegs. Die größten Stunden- und Tagesverluste der Historie stammen aus aufgeblähten Gewinnerpositionen; nach Verlusten wächst der wirksame Hebel statt zu sinken, was den Weg zum Totalverlust beschleunigt (siehe RSK-01).
- **Empfehlung:** Als eigene, vorab protokollierte Runde prüfen (Strategieänderung, nicht stillschweigend): Obergrenze für den Positionswert je Coin und für die Summe, sowie Größenberechnung aus dem laufenden Kontostand statt aus dem Startkapital. Bis dahin Positionswert gegen laufendes Konto als Warnkennzahl je Lauf ausgeben. Die beiden Tests dokumentieren das heutige Verhalten.
- **Nachstellen:** cd /home/user/OdinGate-Botv134/swing-hybrid && .venv/bin/python -B -m pytest -q -p no:cacheprovider reports/audit/evidence/RSK/test_rsk_risiko.py -k "positionswert or gewinner"; grep -n "Positionswert / Startkapital" reports/audit/evidence/RSK/aus_s02_konto.txt

#### RSK-05 (P1): Test 2: Der Stop von 5 % ist kein Stop an der Börse; er wird nur beim Bot-Lauf mit dem Mittelkurs geprüft und hängt am Taktgeber, an Test 1 und am git push

- **Sicherheit des Prüfers:** hoch
- **Stand:** nicht gegengeprüft; Takt-Teil von fünf Prüfern gefunden
- **Evidenz:** Code: bot.py:216-228 (Prüfung r = (mitte / ein − 1) x Richtung nur innerhalb von schritt(), Ausführung als Taker gegen das Buch dieses Moments); bot.py:168-173 (Coin ohne Marktdaten wird übersprungen, auch die Stop-Prüfung); vorwaertstest/stunde.sh:3 (set -euo pipefail), :10-18 (Test 1 rechnen, verschlüsseln, committen, git push), :23 (Test 2 erst danach): scheitert Schritt oder push von Test 1, läuft Test 2 in diesem Durchgang nicht. Docstring bot.py:3 und README.md:10 nennen stündlichen Aufruf, dashboard_daten.py:12 TAKT_MINUTEN = 60, betrieben wird laut stand.csv alle 5 Minuten (Median 5 min, größter Abstand 13 min in 64 Läufen). Tests: test_stop_wird_nur_beim_lauf_geprueft_und_zum_dann_gueltigen_kurs_ausgefuehrt (Sprung zwischen zwei Läufen: Ausführung bei −20 %, 300 $ statt 75 $ je 1.500 $), test_bei_fehlenden_marktdaten_wird_der_stop_nicht_geprueft. Historische Nachstellung der Bot-Logik (aus_s05_test2.txt): bei 5-Minuten-Prüfung 754 Stops in 6,7 Jahren, Verlust am Stop im Mittel −5,54 %, schlechtestes 1 % ab −9,5 %, schlechtester −16,9 % (XRP 03.01.2024 = −5,1 % des Startkapitals aus einer Position bei Hebel 3); bis zu 8 Stops in einer Stunde (26.05.2022, zusammen −13,9 % des Startkapitals). Bei 24 Stunden ohne Lauf: Mittel −8,0 %, schlechtester −29,9 %, im Prüfzeitraum Konto bei Hebel 3 auf 0 %. Der Taktgeber ist laut Betreiber eine KI-Sitzung. docs/index.html:268, :390 zeigt "Stop bei" und eine SL-Linie wie einen festen Ausstiegskurs.
- **Auswirkung:** Der Stop begrenzt den Verlust einer Position nicht auf 5 %: bei Kurslücken, bei einem ausgefallenen Lauf, bei einem fehlgeschlagenen push von Test 1 oder bei einem Abfragefehler bleibt die Position ungeschützt. Im Live-Pfad (gleiche Logik) gäbe es keine Absicherung an der Börse, während der Taktgeber steht.
- **Empfehlung:** Für Live-Betrieb Stop als ruhende Reduce-only-Stop-Order an der Börse führen und im Papier-Bot entsprechend nachbilden (Ausführung zum ersten Kurs jenseits der Schwelle). Test 2 im Skript von Test 1 und vom push entkoppeln (eigener Aufruf, Fehler eines Tests bricht den anderen nicht ab). Ausgefallene Läufe erkennen und melden (Abstand zum letzten Lauf im Zustand). Im Board klarstellen, dass der Stop nur beim Lauf geprüft wird.
- **Nachstellen:** cd /home/user/OdinGate-Botv134/swing-hybrid && .venv/bin/python -B -m pytest -q -p no:cacheprovider reports/audit/evidence/RSK/test_rsk_risiko.py -k "stop"; export RSK_SCRATCH=/tmp/rsk_audit && .venv/bin/python -I -B reports/audit/evidence/RSK/s05_test2.py

#### RSK-06 (P1): Test 2 misst nicht die erforschte Variante, und die Variante selbst ist unbestätigt: in der Vorperiode 2020/21 ist das Konto bei Hebel 3 aufgebraucht

- **Sicherheit des Prüfers:** hoch
- **Stand:** nicht gegengeprüft; Takt-Teil von fünf Prüfern gefunden, Vorperioden-Zahl nur ein Prüfer
- **Evidenz:** Protokoll: reports/suche_protokoll.md:1243-1246 (geprüft wird am Stundenschluss), :1288-1289 ("keine Variante ist in beiden Hälften besser ... Stufe 3 nicht gerechnet"), :1298 ("Dashboard und Papier-Test bleiben unverändert"); Test 2 wurde 5 Minuten nach diesem Ergebnis gestartet (git 42c2168 17:40, b8795b3 17:45). Nachrechnung (aus_s05_test2.txt, Tabelle 7 in aus_s10_uebersicht.txt): die Forschungsvariante tpsl.VARIANTEN["sl5_tp15"] ist in der Entwicklung reproduziert (Sharpe 1,13, +362 Punkte bei Hebel 3 = 33 % pro Jahr bei Hebel 1). In der Vorperiode 02/2020-08/2021, die das Protokoll als Bestätigung vorsah, aber nie rechnete: −121,4 Punkte bei Hebel 3 (Hebel 1: −40,5 %), Sharpe −0,86, tiefster Kontostand −106 %; der Kandidat ohne Stop im selben Zeitraum +627,5 Punkte. Bot-Logik mit 5-Minuten-Prüfung statt Stundenschluss: Stops 373 statt 236 (Entwicklung), 264 statt 143 (Vorperiode), 117 statt 71 (Prüfzeitraum); Ergebnis im Prüfzeitraum bei Hebel 3 +129,7 gegen +66,0 Punkte, in der Entwicklung +324,5 gegen +371,4: das Ergebnis hängt vom Takt des Taktgebers ab, der nirgends festgelegt ist.
- **Auswirkung:** Aus Test 2 lässt sich weder die erforschte Variante bestätigen noch widerlegen, weil eine andere Regel läuft (Prüfung alle rund 5 Minuten am Mittelkurs, Bezug Füllkurs). Die Variante hat die eigene Hürde nicht bestanden und in der einzigen trendstarken Vergleichsphase bei Hebel 3 das Konto vernichtet. Ein günstiger Papier-Verlauf könnte fälschlich als Beleg gelesen werden.
- **Empfehlung:** Vor Auswertung von Test 2 schriftlich festlegen, welche Regel gemeint ist (Prüfabstand, Bezugskurs), und den Bot danach takten; die Abweichung zur Forschung im Bericht nennen. Test 2 als Ausführungsmessung führen, nicht als Strategietest. Offenlegung: Mit dieser Risikomessung ist der Prüfzeitraum ab 04/2025 für sl5_tp15 eingesehen und taugt für diese Variante nicht mehr als unabhängige Bestätigung; die Unterschiede zwischen den Prüfabständen dürfen nicht zur Auswahl benutzt werden.
- **Nachstellen:** cd /home/user/OdinGate-Botv134/swing-hybrid && export RSK_SCRATCH=/tmp/rsk_audit && .venv/bin/python -I -B reports/audit/evidence/RSK/s05_test2.py

#### RSK-07 (P2): Wiedereinstieg nach dem Stop: Das Signal dreht rund 200-mal je Coin und Jahr; der Stop begrenzt den Summenverlust nicht

- **Sicherheit des Prüfers:** mittel
- **Stand:** nicht gegengeprüft (nicht vorgesehen)
- **Evidenz:** aus_s05_test2.txt (Abschnitte "Wiedereinstieg" und "Signal-Drehs"), aus_s03_gleichzeitig.txt: 13.350 Signal-Drehs in 6,7 Jahren = 199 je Coin und Jahr; Abstand zum vorigen Dreh im Median 4 Stunden, genau 1 Stunde bei 30 %, bis 24 Stunden bei 79 %; Haltedauer im Mittel 42 Stunden, im Median 3 Stunden; bis zu 43 Drehs an einem Tag (26.05.2022), jeder Dreh handelt das Doppelte der Positionsgröße (3.000 $ bei 5.000 $ Konto). Nach den 754 Stops der 5-Minuten-Nachstellung: Gegenposition im Median nach 9 Stunden; dieselbe Richtung wie die gestoppte Position wieder offen binnen 6 Stunden bei 19 %, binnen 24 Stunden bei 44 %, binnen 72 Stunden bei 60 %; in 55 % der Fälle zu einem schlechteren Kurs als der Stop-Ausstieg. Schlechteste 30 Tage: 43 Stops, Summe −244 % der Positionsgröße = −73 % des Startkapitals bei Hebel 3 (bis 13.06.2021). Code: bot.py:219-220 (Sperre fällt, sobald das Signal ungleich der gesperrten Richtung ist, auch bei Richtung 0), :227-228. Test: test_nach_dem_stop_reicht_ein_hin_und_her_des_signals_fuer_den_wiedereinstieg.
- **Auswirkung:** Ein Stop von 5 % je Position wirkt wie eine Verlustgrenze, ist aber nur eine Pause bis zum nächsten Hin und Her des Signals. In Seitwärtsphasen reihen sich Stops und Wiedereinstiege; der Summenverlust ist nicht begrenzt, die Handelskosten steigen.
- **Empfehlung:** Im Protokoll festhalten, dass der Stop keine Kontogrenze ist. Zahl der Stops und Summe der Stop-Verluste je 30 Tage als Kennzahl in den Bericht von Test 2 aufnehmen. Eine Kontogrenze (siehe RSK-08) getrennt vom Positions-Stop behandeln. Die Sonderbedingung Richtung 0 in der Sperrlogik bewusst entscheiden und testen.
- **Nachstellen:** cd /home/user/OdinGate-Botv134/swing-hybrid && export RSK_SCRATCH=/tmp/rsk_audit && .venv/bin/python -I -B reports/audit/evidence/RSK/s05_test2.py; .venv/bin/python -B -m pytest -q -p no:cacheprovider reports/audit/evidence/RSK/test_rsk_risiko.py -k wiedereinstieg

#### RSK-08 (P2): Es gibt keinen geprüften Verlustbegrenzer auf Kontoebene: Tageslimit in den Tests faktisch aus, in der Forschung bei Hebel über 0,5 schädlich, im Bot mit Lücke über Nacht

- **Sicherheit des Prüfers:** hoch
- **Stand:** nicht gegengeprüft (nicht vorgesehen)
- **Evidenz:** config_lauf.json:17 und config_lauf_tpsl.json:17: tagesverlust_limit 1.0. Test test_tagesverlust_limit_100_prozent_greift_erst_nach_dem_totalverlust: bei −4.950 $ am Tag keine Reaktion, geschlossen wird erst bei −5.100 $ mit negativem Konto. bot.py:194-195: der Tagesanfang wird beim ersten Lauf des neuen Tages mit den dann gültigen Kursen gesetzt; Test test_verlust_ueber_nacht_zaehlt_fuer_kein_tageslimit: −60 % des Kapitals zwischen zwei Läufen über Mitternacht lösen ein 3-%-Limit nicht aus. bot.konfig (bot.py:41-47) prüft nur modus und Hebel <= 5, kein Limit (Test test_konfig_prueft_hebel_bis_5_aber_kein_verlustlimit: Hebel 5 und Limit 99 werden angenommen). Forschung: reports/suche_protokoll.md:102-105 (Limit bei Hebel 1 an 222 von 1.324 Tagen ausgelöst, verfälschte die Messung), suche_bericht.md:320-329 (Hebel 3 mit Limit: 1.178 Sperrtage, Konto unter null; nachgerechnet in aus_s08_repro_hebel.txt). Der Betreiber führt die Frage selbst als offen (uebergabe_fuer_dritte.md:65-66).
- **Auswirkung:** Für Hebel 3 existiert keine wirksame und keine getestete Begrenzung des Kontoverlusts. Das einzige vorhandene Mittel ist in den Tests abgeschaltet und hat sich in der Forschung bei höherem Hebel als kontraproduktiv erwiesen.
- **Empfehlung:** Kontoweite Begrenzung als eigene Runde entwerfen und vorab festlegen (z. B. Schwelle auf den Kontostand gegenüber dem Höchststand statt auf den Kalendertag), nur auf Entwicklungsdaten prüfen. Im Bot den Tagesanfang aus dem letzten Stand des Vortags nehmen statt aus dem ersten Lauf des neuen Tages. In bot.konfig Grenzen für das Limit prüfen (z. B. Wert über 0,5 nur mit ausdrücklichem Schalter).
- **Nachstellen:** cd /home/user/OdinGate-Botv134/swing-hybrid && .venv/bin/python -B -m pytest -q -p no:cacheprovider reports/audit/evidence/RSK/test_rsk_risiko.py -k "tagesverlust or ueber_nacht or konfig"

#### RSK-09 (P2): Funding trifft die Strategie einseitig: Long zahlt deutlich mehr, als Short erhält; in heißen Phasen bis 45 Punkte des Startkapitals in 30 Tagen bei Hebel 3

- **Sicherheit des Prüfers:** mittel
- **Stand:** nicht gegengeprüft (nicht vorgesehen)
- **Evidenz:** aus_s06_funding.txt und Tabelle 8 in aus_s10_uebersicht.txt (Binance-Sätze, Positionen des Kandidaten): Funding gesamt bei Hebel 1: Vorperiode −45,4 % des Startkapitals (−29,6 % pro Jahr, bei Hebel 3 −88,6 % pro Jahr), Entwicklung −6,4 % pro Jahr, Prüfzeitraum −2,2 % pro Jahr. Schlechteste 30 Tage: −14,95 Punkte bei Hebel 1 (−44,8 bei Hebel 3, bis 03.03.2021), Entwicklung −4,3 (−12,9, bis 15.03.2024). Position zahlt in 57 bis 62 % der Abrechnungen; mittlerer Satz, wenn Long: +0,0178 % je 8 Stunden, wenn Short: +0,0026 %; Summe Long −83,2, Summe Short +11,2 Punkte (Hebel 1, ganze Historie). Längste Phasen mit mindestens 0,03 % gegen die Position ohne Unterbrechung: XRP Long 28.03.-18.04.2021, 63 Abrechnungen (21 Tage), Summe 9,4 % der Positionsgröße; BTC Long 56 Abrechnungen (18,7 Tage). Extrem: SOL Short 08.-10.11.2022, 16 Abrechnungen im 2-Stunden-Abstand mit bis zu −2 %, Summe 22,3 % der Positionsgröße. Portfolio zahlte 127 Abrechnungen in Folge (05.02.-18.03.2024, −14,0 Punkte bei Hebel 3). Die Kosten wachsen zusätzlich mit aufgeblähten Gewinnern (DOGE 08.02.2021: 7-fache Standardgröße, Satz +0,378 %). Bot: bot.py:184-189 bucht Funding als Näherung mit dem aktuellen Ticker-Satz.
- **Auswirkung:** Trendfolge ist dann Long, wenn Funding hoch ist. In starken Aufwärtsphasen frisst Funding bei Hebel 3 einen zweistelligen Anteil des Kontos pro Monat; die historischen Yubit-Sätze sind nicht bekannt, die Zahlen stammen von Binance.
- **Empfehlung:** Funding im Papier-Test mit dem abgerechneten Satz buchen und je Coin mitschreiben, um Yubit gegen Binance zu vergleichen. Laufende Funding-Kosten der letzten 30 Tage als Kennzahl führen. Eine Funding-Regel wurde in Runde 21/22 bereits verworfen; keine neue Variante ohne vorab festgelegtes Protokoll.
- **Nachstellen:** cd /home/user/OdinGate-Botv134/swing-hybrid && export RSK_SCRATCH=/tmp/rsk_audit && .venv/bin/python -I -B reports/audit/evidence/RSK/s06_funding.py (s01 muss vorher gelaufen sein)

#### RSK-10 (P2): Einzelne Coins laufen binnen einer Stunde 25 bis 49 % gegen die Position; die Datenbasis (letzter Preis Binance) enthält Ausreißer, ein Mark-Preis fehlt

- **Sicherheit des Prüfers:** mittel
- **Stand:** nicht gegengeprüft (nicht vorgesehen)
- **Evidenz:** aus_s03_gleichzeitig.txt. Größte Bewegung gegen die gehaltene Richtung innerhalb einer Stunde, nur 5-Minuten-Schlusskurse: DOGE Short 48,6 % (28.01.2021), LTC Long 41,0 % (10.10.2025), LINK Short 38,1 % (13.03.2020), ADA Long 36,4 % (19.05.2021), ADA Short 33,6 % (02.03.2025), AVAX Short 33,1 % (11.05.2022); innerhalb 24 Stunden: SOL Short 86,0 % (09./10.11.2022), LINK Short 67,6 %, DOGE Long 65,2 %, LTC Long 46,4 %. Mit Hochs und Tiefs: LTC 57,5 % in einer Stunde (Rohkerze 10.10.2025 21:20: Tief 51,60 nach 122). Je Haltephase: größte Gegenbewegung 56,0 % (LTC Long), 47,7 % (DOGE Short 27./28.01.2021, im Backtest mit −45,2 % der Positionsgröße beendet = −13,6 % des Startkapitals bei Hebel 3), 41,7 % (XRP Short 04/2021, −36,1 %), 37,2 % (AVAX Short 10/2020, −35,5 %); 255 Haltephasen mit mindestens 10 %, 26 mit mindestens 20 %. Ausreißer in den Daten: ETHUSDT 13.03.2020 02:35 Hoch 323,00 bei Kursen um 103 bis 117 (237 % über dem Stundenanfang); mit Schlusskursen 23,7 %.
- **Auswirkung:** Ein einzelner Coin kann bei Hebel 3 in einer Stunde 10 bis 15 % des Kontos kosten, mit aufgeblähter Position mehr. Ob Yubit in solchen Momenten dieselben Kurse, Dochte und Buchtiefen hat, ist nicht bekannt; Liquidationen richten sich üblicherweise nach dem Mark-Preis, der in den Daten fehlt. Die Zahl der Liquidationsfälle in RSK-02 ist deshalb nur eine Größenordnung.
- **Empfehlung:** Mark-Preis- oder Index-Kerzen beschaffen und die Auswertung damit wiederholen. Im Papier-Test je Lauf Geld/Brief und Tiefe weiter mitschreiben und gezielt Stressphasen auswerten (bisher nur ruhige Stunden vom 14./15.11.2026). Offensichtliche Ausreißerkerzen in der Datenprüfung kennzeichnen, nicht stillschweigend entfernen.
- **Nachstellen:** cd /home/user/OdinGate-Botv134/swing-hybrid && export RSK_SCRATCH=/tmp/rsk_audit && .venv/bin/python -I -B reports/audit/evidence/RSK/s03_gleichzeitig.py (s01 muss vorher gelaufen sein)

#### RSK-11 (P2): Live-Pfad: Nach einer Zwangsschließung an der Börse stellt der Bot den Handel für alle Coins ein und lässt die übrigen Positionen ungeführt

- **Sicherheit des Prüfers:** mittel
- **Stand:** nicht gegengeprüft (nicht vorgesehen)
- **Evidenz:** bot.py:177-182: weicht die Position laut Börse bei irgendeinem Coin vom Protokoll ab, endet der Lauf mit SystemExit ("Kein Handel. Bitte prüfen"), vor Signal-, Stop- und Tageslimit-Prüfung aller Coins; das wiederholt sich bei jedem Lauf bis zum Eingriff von Hand. Eine Liquidation oder Teil-Liquidation einer Position erzeugt genau diese Abweichung. In stunde.sh:3 (set -e) bricht damit auch der Rest des Skripts ab. Nur am Code gelesen, bewusst nicht ausgeführt (kein Live-Pfad im Audit). Zusammenhang mit RSK-02: bei isolierter Margin und Börsenhebel 3x wären historisch 5 bis 7 Haltephasen liquidiert worden, bei höherem Börsenhebel Hunderte.
- **Auswirkung:** Gerade im Stressfall (eine Position wird liquidiert) bleiben die anderen neun Positionen mit dreifachem Hebel ohne Signalwechsel, ohne Stop und ohne Tageslimit im Markt, bis ein Mensch eingreift. Der Taktgeber ist eine KI-Sitzung ohne Bereitschaft.
- **Empfehlung:** Für den Live-Betrieb einen definierten Notfallablauf festlegen und testen: Abweichung bei einem Coin führt zu einer benannten Reaktion (z. B. betroffenen Coin sperren, übrige weiterführen oder alles geordnet schließen) und zu einer Meldung an den Betreiber. Das Verhalten mit nachgestellter Börse als Test festhalten, bevor ein Schlüssel eingesetzt wird.
- **Nachstellen:** sed -n 177,182p /home/user/OdinGate-Botv134/swing-hybrid/vorwaertstest/bot.py; sed -n 1,18p /home/user/OdinGate-Botv134/swing-hybrid/vorwaertstest/stunde.sh

### Nachgerechnete Aussagen

- **reproduziert**: Entwicklung: +59 % pro Jahr, Sharpe 0,95 (Kandidat, Hebel 1, Yubit-Kosten mit Rebate). N +2,1564 in 1.325 Tagen = +59,40 % pro Jahr, Sharpe 0,9457, Einbruch auf Tagesschluss 24,58 %; identisch mit reports/suche_runde24.json (kandidat.Entwicklung). D1 Sharpe 0,564, D2 1,3165. Auf dem 5-Minuten-Raster ist der Einbruch 25,8 %. Befehl: `cd /home/user/OdinGate-Botv134/swing-hybrid && RSK_SCRATCH=/tmp/rsk_audit .venv/bin/python -I -B reports/audit/evidence/RSK/s01_laeufe.py`
- **reproduziert**: Unabhängiger Prüfzeitraum: +16,5 % pro Jahr, Sharpe 0,34. N +0,2585 in 571 Tagen = +16,52 % pro Jahr, Sharpe 0,3369, Einbruch auf Tagesschluss 31,3 %. Mit frischem Start am 01.04.2025 statt durchlaufender Positionen: +16,7 % pro Jahr, Einbruch 33,0 %. Befehl: `wie oben; zusätzlich reports/audit/evidence/RSK/s02_konto.py`
- **reproduziert**: Hohe Korrelation der zehn Positionen (Betreiber: 0,68, seit 04/2025 0,79). Mittlere paarweise Korrelation der Stundenrenditen in der Entwicklung 0,68, der Tagesrenditen im Prüfzeitraum 0,79 (Stundenrenditen 0,77). Effektive Zahl unabhängiger Wetten 1,46 bzw. 1,24. Befehl: `RSK_SCRATCH=/tmp/rsk_audit .venv/bin/python -I -B reports/audit/evidence/RSK/s04_korrelation.py`
- **reproduziert**: Rechenkern engine2 (Taker-Modus): Positionsführung, Gebühr mit Rebate, Slippage, Funding. Eigener Nachbau in rsk_common.nachbau: größte Abweichung des Kontoverlaufs, des Volumens und des Fundings gegen den Rechenkern 0,0 in Vorperiode (2.753 Trades) und Hauptzeitraum (10.818 Trades). Hebel 3 ist exakt das Dreifache von Hebel 1 (Abweichung 1,4e-14); kein Tageslimit ausgelöst bei day_limit=9.0. Befehl: `RSK_SCRATCH=/tmp/rsk_audit .venv/bin/python -I -B reports/audit/evidence/RSK/s01_laeufe.py; pytest reports/audit/evidence/RSK/test_rsk_risiko.py -k nachbau`
- **reproduziert**: Hebel-Tabelle der Forschung (reports/diagnose_kapital.json, suche_bericht.md:320-326): Hebel 0,2 Einbruch 9 %, Hebel 3 mit Tageslimit −101,3 % pro Jahr und Konto unter null. Alle fünf Zeilen (Hebel 0,2 / 0,5 / 1 / 2 / 3) mit Abweichung 0 nachgerechnet, einschließlich 1.178 Sperrtagen bei Hebel 3. Befehl: `RSK_SCRATCH=/tmp/rsk_audit .venv/bin/python -I -B reports/audit/evidence/RSK/s08_repro_hebel.py`
- **reproduziert**: Runde 24: Variante sl5_tp15 in der Entwicklung Sharpe 1,13, Ertrag 33 % pro Jahr. Sharpe 1,13; +362,3 Punkte bei Hebel 3 = +120,8 % bei Hebel 1 in 3,63 Jahren = 33 % pro Jahr. Nicht in Runde 24 gerechnet und hier erstmals: Vorperiode Sharpe −0,86 und −40,5 % bei Hebel 1. Befehl: `RSK_SCRATCH=/tmp/rsk_audit .venv/bin/python -I -B reports/audit/evidence/RSK/s05_test2.py`
- **reproduziert**: Zwei Papier-Tests mit Hebel 3 seit 15.11.2026. config_lauf.json und config_lauf_tpsl.json: Hebel 3,0, Kapital 5.000 $, Tageslimit 1,0; Start laut zustand.json 13:21 und 17:44 UTC; je zehn Einstiegsorders zu rund 1.500 $; beide Konten am letzten lokalen Stand (18:58 UTC) 0 Long / 10 Short. Befehl: `pytest reports/audit/evidence/RSK/test_rsk_risiko.py -k ist_konfiguration; cat vorwaertstest/lauf/zustand.json`
- **reproduziert**: Start-Tag-Simulation (eigene Rechnung) stimmt mit dem Rechenkern der Forschung überein. Fünf Starttage mit eigenem Markt ab Starttag durch R.lauf gerechnet: tiefstes Ergebnis identisch bis 1e-16 (z. B. Start 06.08.2024: −0,5014 bei Hebel 1). Befehl: `RSK_SCRATCH=/tmp/rsk_audit .venv/bin/python -I -B reports/audit/evidence/RSK/s09_gegenprobe.py (nach s02)`
- **abweichend**: Dashboard: "fällt der Korb der Coins rund 33 % gegen die Positionen, ist das Konto aufgebraucht" (dashboard_live.html:131). Rechnerisch richtig nur für ein frisches Konto mit zehn gleichgerichteten Positionen in Standardgröße. Unter Annahme gemeinsamer Margin liegt die Liquidation bei 30,1 bis 33,0 % (MMR 2,5 bis 0,5 %), bei isolierter Margin hängt sie vom Börsenhebel ab (4,5 bis 32,8 %). Mit gewachsenen Gewinnern lag der Positionswert historisch bei bis zu 6,5 bis 7 x Startkapital statt 3 x. Befehl: `RSK_SCRATCH=/tmp/rsk_audit .venv/bin/python -I -B reports/audit/evidence/RSK/s07_liquidation.py`
- **reproduziert**: YUBIT_REGELN.md: Kandidat hält im Schnitt rund 42 Stunden. Mittel 42 Stunden über 13.571 Haltephasen; der Median liegt aber bei 3 Stunden, 30 % der Signal-Drehs folgen binnen einer Stunde auf den vorigen. Befehl: `RSK_SCRATCH=/tmp/rsk_audit .venv/bin/python -I -B reports/audit/evidence/RSK/s03_gleichzeitig.py`
- **reproduziert**: Bestehende Tests: 105 Tests grün. 105 passed in 13,8 s. Keiner dieser Tests deckt Hebel 3, Liquidation, Kurslücken am Stop oder das Tageslimit von 100 % ab; dafür 12 neue Tests in evidence/RSK/test_rsk_risiko.py (12 passed). Befehl: `cd /home/user/OdinGate-Botv134/swing-hybrid && .venv/bin/python -B -m pytest -q -p no:cacheprovider tests reports/audit/evidence/RSK/test_rsk_risiko.py`

### Als richtig befunden

- Hebel wirkt im Rechenkern rein linear auf das Ergebnis in Punkten des Startkapitals (research.py:150 S = hebel / Anzahl Coins; kein versteckter Zinseszins): Hebel 3 = 3 x Hebel 1 bis 1,4e-14 (aus_s01_laeufe.txt).
- Bauart der Forschungsläufe ab Runde 21 entspricht dem Papier-Test: Taker, Yubit-Slippage je Coin, day_limit=9.0 ohne eine einzige Auslösung (scripts/suche_runde21.py und suche_runde24.py Funktion tage; aus_s01_laeufe.txt: Sperrtage 0).
- Kostenansatz: Taker 0,08 % x (1 − 0,85) = 0,012 % je Seite (config.yaml:6-8, runner.py:11-13); Slippage je Coin aus der Yubit-Stichprobe (research.py:272-279), DOT 13,2 bp, BTC/ETH 0,5 bp Boden. Die im Papier-Test gemessene Slippage (lauf/spannen.csv, 635 Messungen) liegt in derselben Größenordnung (DOT 7,3 bp, ADA 3,3 bp, übrige unter 1,2 bp).
- Signal und Positionswechsel nur zur vollen Stunde, Signal aus abgeschlossener Stundenkerze (research.py:70-75 auf_raster verschiebt um eine Stunde); der eigene Nachbau mit Handel zum Open der Folgekerze stimmt exakt überein, die Risikozahlen enthalten also keinen Blick voraus.
- Positionsgröße im Papier-Bot: 5.000 $ x 3 / 10 = 1.500 $ je Coin, auf die Schrittweite abgerundet (bot.py:165, kern.py:22-30); größte Abweichung BTC 0,022 Stück = 1.446 $ (−3,6 %). Mindestgrößen laut yubit_coins.csv (BTC 66 $, ETH 19 $, SOL und AVAX rund 8 $, übrige unter 1 $) sind bei 1.500 $ nicht bindend.
- Buchführung des Papier-Bots (Kasse + Stück x Kurs − Gebühr + Funding + Rebate, kern.py:73-88) rechnet in den neuen Tests auf den Dollar wie erwartet (z. B. 20 % Verlust auf 1.500 $ = 300 $).
- Stop-, Ziel- und Sperrlogik von Test 2 arbeitet wie im Code beschrieben (bot.py:216-228): Auslösung bei r <= −5 % bzw. >= +15 % am Mittelkurs, Pause bis zum Dreh; durch bestehende und neue Tests belegt.
- bot.konfig lehnt Hebel über 5 ab (bot.py:45-46; Test mit 5,01).
- Taktgeber bis zum letzten lokal vorhandenen Lauf: Test 1 64 Läufe von 13:21 bis 18:58 UTC, Abstand im Median 5 Minuten, größter Abstand 13 Minuten, keiner über 15 Minuten; Test 2 14 Läufe, größter Abstand 9 Minuten (aus_s07_liquidation.txt).
- Die Aussage der Übergabe, zehn Positionen seien praktisch eine (uebergabe_fuer_dritte.md:28-29), ist durch die Messung gedeckt.
- Am Audit wurde nichts außerhalb von reports/audit/evidence/RSK geschrieben; git status zeigt keine Änderung an Code, Konfiguration, vorwaertstest/lauf*, docs/ oder gespeicherten Ergebnissen. Der Bot wurde nur in temporären Verzeichnissen gegen eine nachgestellte Börse ausgeführt.

### Ungeklärt

- Margin-Modus (isoliert oder gemeinsam), eingestellter Börsenhebel je Symbol, Erhaltungsmargin-Sätze und -Stufen, Liquidationsbasis (Mark-Preis oder letzter Preis), Liquidationsgebühr, Auto-Deleveraging und Positionsgrenzen bei Yubit: im Repo nicht dokumentiert (YUBIT_REGELN.md, README.md, yubit_coins.csv enthalten nichts dazu). Alle Liquidationszahlen sind Szenarien mit angenommener Erhaltungsmargin von 0,5 / 1 / 2,5 % und Formeln üblicher USDT-Perpetuals.
- Historische Yubit-Kurse, Yubit-Funding und Yubit-Buchtiefe in Stressphasen liegen nicht vor. Alle Risikozahlen beruhen auf Binance-Futures (letzter Preis, 5-Minuten-Kerzen). Ob Dochte wie LTC am 10.10.2025 (Tief 51,60 nach 122) bei Yubit kleiner oder größer ausfallen, ist offen.
- Mark-Preis-Daten fehlen. Ob der Ausreißer ETHUSDT 13.03.2020 02:35 (Hoch 323,00 bei Kursen um 110) ein echter Handel oder ein Datenfehler ist und ob er den Mark-Preis berührt hätte, ließ sich nicht klären.
- Ob Hebel 3 und das Tageslimit von 100 % eine bewusste Entscheidung des Betreibers mit Kenntnis der eigenen Hebel-Tabelle waren: Commit 4276791 (15.11.2026 13:21) und das Protokoll enthalten keine Begründung und keine Risikogrenze.
- Ob der Taktgeber nach 18:58 UTC weiterläuft: Der lokale Stand endet bei Commit 3dfd5b2 (19:03 UTC); ein Abgleich mit dem entfernten Zweig war nicht erlaubt. Um 19:35 UTC lag lokal kein neuerer Lauf vor.
- Die Start-Tag-Analyse zählt Häufigkeiten in einer einzigen Historie mit stark überlappenden Fenstern; sie ist keine unabhängige Wahrscheinlichkeit. In der Vorperiode handeln bis 10/2020 erst 5 bis 9 der zehn Coins, das Risiko ist dort eher zu niedrig ausgewiesen.
- Wie sich das Konto nach einer Liquidation einzelner Positionen bei isolierter Margin im Gesamtverlauf entwickelt hätte, ist nicht simuliert (nur gezählt); die in aus_s07_liquidation.txt genannte Schätzung, um wie viel der Backtest dadurch zu gut ist, ist grob und nicht belastbar.
- Die Nachstellung von Test 2 benutzt das Open der 5-Minuten-Kerze als Ersatz für den Mittelkurs des Bot-Laufs und unterstellt Ausführung zu diesem Kurs plus gemessener Slippage; die echte Ausführung in einem Kurssturz (dünnes Buch) ist unbekannt und vermutlich schlechter.
- Die Annahme, dass bei Börsenhebel 3x nach dem ersten Verlust Folgeorders mangels freier Margin abgelehnt würden, folgt aus üblichen Margin-Regeln und ist für Yubit nicht belegt.
- Mit der Risikomessung von Test 2 ist der Prüfzeitraum ab 04/2025 für die Variante sl5_tp15 erstmals eingesehen worden (laut Protokoll Runde 24 bis dahin unberührt). Es wurde nichts ausgewählt oder angepasst; für diese Variante steht der Prüfzeitraum aber nicht mehr als unabhängige Bestätigung zur Verfügung.

### Evidenzdateien

- `/home/user/OdinGate-Botv134/swing-hybrid/reports/audit/evidence/RSK/LIESMICH.txt`
- `/home/user/OdinGate-Botv134/swing-hybrid/reports/audit/evidence/RSK/test_rsk_risiko.py`
- `/home/user/OdinGate-Botv134/swing-hybrid/reports/audit/evidence/RSK/aus_s10_uebersicht.txt`
- `/home/user/OdinGate-Botv134/swing-hybrid/reports/audit/evidence/RSK/aus_s01_laeufe.txt`
- `/home/user/OdinGate-Botv134/swing-hybrid/reports/audit/evidence/RSK/aus_s02_konto.txt`
- `/home/user/OdinGate-Botv134/swing-hybrid/reports/audit/evidence/RSK/aus_s03_gleichzeitig.txt`
- `/home/user/OdinGate-Botv134/swing-hybrid/reports/audit/evidence/RSK/aus_s04_korrelation.txt`
- `/home/user/OdinGate-Botv134/swing-hybrid/reports/audit/evidence/RSK/aus_s05_test2.txt`
- `/home/user/OdinGate-Botv134/swing-hybrid/reports/audit/evidence/RSK/aus_s06_funding.txt`
- `/home/user/OdinGate-Botv134/swing-hybrid/reports/audit/evidence/RSK/aus_s07_liquidation.txt`
- `/home/user/OdinGate-Botv134/swing-hybrid/reports/audit/evidence/RSK/aus_s08_repro_hebel.txt`
- `/home/user/OdinGate-Botv134/swing-hybrid/reports/audit/evidence/RSK/aus_s09_gegenprobe.txt`
- `/home/user/OdinGate-Botv134/swing-hybrid/reports/audit/evidence/RSK/rsk_common.py`
- `/home/user/OdinGate-Botv134/swing-hybrid/reports/audit/evidence/RSK/s01_laeufe.py`
- `/home/user/OdinGate-Botv134/swing-hybrid/reports/audit/evidence/RSK/s02_konto.py`
- `/home/user/OdinGate-Botv134/swing-hybrid/reports/audit/evidence/RSK/s03_gleichzeitig.py`
- `/home/user/OdinGate-Botv134/swing-hybrid/reports/audit/evidence/RSK/s04_korrelation.py`
- `/home/user/OdinGate-Botv134/swing-hybrid/reports/audit/evidence/RSK/s05_test2.py`
- `/home/user/OdinGate-Botv134/swing-hybrid/reports/audit/evidence/RSK/s06_funding.py`
- `/home/user/OdinGate-Botv134/swing-hybrid/reports/audit/evidence/RSK/s07_liquidation.py`
- `/home/user/OdinGate-Botv134/swing-hybrid/reports/audit/evidence/RSK/s08_repro_hebel.py`
- `/home/user/OdinGate-Botv134/swing-hybrid/reports/audit/evidence/RSK/s09_gegenprobe.py`
- `/home/user/OdinGate-Botv134/swing-hybrid/reports/audit/evidence/RSK/s10_uebersicht.py`

## Bereich INF: Infrastructure

Der Papier-Bot rechnet im geprüften Stand sauber (Protokoll, Stand und Zustand beider Konten stimmen überein, die CSV-Dateien sind über 68 bzw. 14 Versionen nur gewachsen), aber der Betrieb drumherum ist für echtes Geld nicht tragfähig. Der Zeitgeber ist eine KI-Sitzung ohne Überwachung: gemessen rund alle 5 Minuten statt wie überall dokumentiert stündlich, Lücken bis 13 Minuten, kein Alarm; Stop und Signaldreh greifen nur, wenn ein Lauf stattfindet (nachgestellt: nach 10 Stunden Ausfall Ausstieg bei 20 % statt 5 %). Der Zustand liegt in einem Git-Zweig, auf den auch Entwickler- und Audit-Sitzungen pushen: Ein einziger fremder Push im Fenster von rund 51 Sekunden je Lauf (16 % des Zyklus) lässt den Runner dauerhaft abweichen, Konto 2 läuft dann gar nicht mehr und ein frischer Klon rechnet mit altem Zustand weiter (nachgestellt); heute lagen zehn fremde Commits zwischen 26 und 251 Sekunden neben einem solchen Fenster. Es gibt keine Sperre gegen Doppelläufe und der Zustand wird erst nach den CSV-Dateien und im Live-Pfad erst nach allen Orders gespeichert; ein Abbruch dazwischen verdoppelt Orders im Protokoll bzw. hinterlässt unbekannte Börsenpositionen (mit nachgestellter Börse gezeigt). Belegter Vorfall: 13:44 bis 15:00 UTC stand das Board 79 Minuten still (öffentlicher Schlüssel war durch .gitignore ausgeschlossen), und die Klartextdatei docs/stand.json wurde durch einen Selbstaustausch des Skripts während des Laufs wieder veröffentlicht und liegt bis heute dort. Die Veröffentlichung erzeugt 24 Pages-Builds pro Stunde und rund 12 MB Repo-Zuwachs pro Tag; Tests laufen nicht automatisch.

### Befunde

#### INF-01 (P0): Zeitgeber ist eine unbeaufsichtigte KI-Sitzung; tatsächlicher Takt weicht vom dokumentierten ab, Ausfälle werden weder erkannt noch nachgeholt

- **Sicherheit des Prüfers:** hoch
- **Stand:** direkt sichtbar (Commits rund alle 5 Minuten)
- **Evidenz:** Kein Zeitgeber für den realen Betrieb im Repo: vorwaertstest/stunde.sh:16-17 trägt nur die feste Sitzungsadresse im Commit-Text. Dokumentiert ist überall Stundentakt: README.md:10, server/installieren.sh:43 (OnCalendar=*:03), .github/workflows/vorwaertstest.yml:8 (cron 4 * * * *, inaktiv), dashboard_daten.py:12 (TAKT_MINUTEN = 60), docs/index.html:478 (Countdown auf Minute :04). Gemessen (evidence/INF/historie_takt_luecken.txt): Test 1 64 Läufe 13:21 bis 18:58 UTC, Abstand Median 5 min, min 1, max 13 (15:51 auf 16:04), vier Abstände über 7 min; nur 5 von 64 Läufen (8 %) waren der erste Lauf nach einer vollen Stunde (Minute :01 bis :05). Stop/Ziel werden nur während eines Laufs geprüft (bot.py:216-228), es gibt keine Lückenerkennung (letzte_kerze wird in bot.py:280 nur geschrieben, nie gelesen). Versuch V4 (evidence/INF/bot_versuche_ausgabe.txt): nach 10 h ohne Lauf Ausstieg mit Grund stop bei 20,2 % gegen die Position statt 5 %, Rückgabe warnungen == []. Ursache der Lücken laut Historie nicht feststellbar.
- **Auswirkung:** Bei echtem Geld und Hebel 3 bleiben Positionen ohne Stop und ohne Signaldreh, solange die Sitzung steht; niemand wird benachrichtigt. Schon im Papierbetrieb hängen die Ergebnisse von Test 2 (Stop/Ziel) und die Slippage-Messung vom zufälligen Takt ab: 92 % der als 'zur vollen Stunde' berichteten Messungen (bot.py:314) fanden nicht zur vollen Stunde statt, und Stop/Ziel werden rund zwölfmal so oft geprüft wie im dokumentierten Stundentakt.
- **Empfehlung:** Vor jedem Live-Handel: fester, überwachter Zeitgeber auf einem eigenen Rechner (systemd-Timer oder cron), Takt als Konfigurationswert festlegen und in stand.csv und Dashboard ausweisen; externer Totmannschalter (Signal nach jedem erfolgreichen Lauf, Alarm nach zwei ausgebliebenen Takten); Lückenerkennung im Bot (Abstand zum letzten Lauf größer als Soll führt zu dauerhaft gespeicherter Warnung); im Live-Betrieb Stops als Börsenorder hinterlegen statt nur im Bot prüfen. Für Test 2 schriftlich festlegen, welches Prüfintervall gilt (reine Festlegung, keine Optimierung).
- **Nachstellen:** cd /home/user/OdinGate-Botv134 && python3 -I swing-hybrid/reports/audit/evidence/INF/historie.py . ; cd swing-hybrid && .venv/bin/python -I -B reports/audit/evidence/INF/bot_versuche.py (Abschnitt V4)

#### INF-02 (P0): Git-Zweig als gemeinsamer Zustandsspeicher: ein fremder Push im Lauf-Fenster lässt den Runner dauerhaft und still abweichen

- **Sicherheit des Prüfers:** hoch
- **Stand:** nicht gegengeprüft
- **Evidenz:** stunde.sh:6 und :8 verschlucken Fehler von fetch und pull (|| true), :14-17 verschlucken Fehler von commit (|| true), :18 bricht bei abgelehntem push ab (set -e, Zeile 3), das zweite Konto folgt erst ab :23. Sandbox mit byte-gleicher Kopie von stunde.sh und eigenem Bare-Repo (evidence/INF/gitsim_ausgabe.txt): S1 nach einem fremden Push zwischen pull und push liefern Lauf 3, 4 und 5 Rückgabewert 1, der Runner ist 3 Commits voraus und 1 zurück, stand.csv Konto 1 lokal 5 Zeilen gegen 2 auf origin, Konto 2 bleibt bei 2 Zeilen stehen; ein frischer Klon startet mit Zustand lauf 2 statt lauf 5. S2 Push-Fehler: Konto 2 wird in diesem Lauf ausgelassen. S5 commit scheitert: Rückgabewert 0, Ausgabe 'gesichert', origin unverändert. Realer Betrieb: zehn Commits, die nicht vom Runner stammen, lagen zwischen 13:22 und 19:03 UTC auf dem Bot-Zweig; dieser Klon erzeugt sie per commit, pull --rebase, push (evidence/INF/reflog_entwicklerklon.txt, 0 Bot-Commits im reflog). Fenster je Lauf Median 51 s bei Zyklus 311 s, also 16 %; knappste Abstände zum Fenster 26 s (cf1f1cb), 39 s (b8795b3), 41 s (a6bf357) (historie_takt_luecken.txt, letzter Abschnitt). Zweig ungeschützt (GitHub-API: protected false). Ein solcher Vorfall ist in der Historie bis 3dfd5b2 nicht eingetreten: jede Zeile in stand.csv hat ihren eigenen Commit.
- **Auswirkung:** Nach einer Kollision rechnet der Runner nur noch lokal weiter, das Board und der Zweig frieren ein, Konto 2 wird gar nicht mehr berechnet. Geht der Runner-Klon verloren (neue Sitzung, neuer Container), startet der Bot ohne Hinweis mit dem veralteten Zustand des Zweigs: Positionen, Einstiegskurse und Sperren stimmen nicht mehr. Mit echtem Geld sind das falsche Orders oder ein Stillstand mit offenen Positionen.
- **Empfehlung:** Zustand aus dem gemeinsam genutzten Zweig herausnehmen: eigener Datenspeicher (Datei oder SQLite auf dem Runner mit Sicherung) oder ein Datenzweig, auf den nur der Runner schreibt (Branch-Schutz). Im Skript: nach dem Holen prüfen, dass der lokale Stand nicht hinter origin liegt, sonst abbrechen und alarmieren; abgelehnten Push mit pull --rebase einmal wiederholen; Rückgabewert von git commit auswerten; beide Konten unabhängig voneinander behandeln. Code-Auslieferung (geprüfter Stand) von den Laufdaten trennen.
- **Nachstellen:** S=$(mktemp -d /tmp/inf.XXXX); mkdir $S/stubs; E=/home/user/OdinGate-Botv134/swing-hybrid/reports/audit/evidence/INF; for f in bot dashboard_daten board_verschluesseln; do cp $E/gitsim_stellvertreter_$f.py $S/stubs/$f.py; done; bash $E/gitsim.sh /home/user/OdinGate-Botv134 $S/sim $S/stubs

#### INF-03 (P0): Keine Sperre gegen Doppelläufe und Zustand wird zuletzt gespeichert: Abbruch oder Überlappung verdoppelt Orders im Protokoll, im Live-Pfad bleiben unbekannte Börsenpositionen

- **Sicherheit des Prüfers:** hoch
- **Stand:** nicht gegengeprüft
- **Evidenz:** Kein Sperrmechanismus: grep nach flock, lockf, fcntl, .lock in vorwaertstest/*.py und *.sh liefert nichts. Reihenfolge in bot.py: Zustand laden :160, CSV anhängen :276-279, Zustand speichern :281; Live-Orders werden in der Coin-Schleife gesendet (:244), gespeichert wird erst danach. V2 (bot_versuche_ausgabe.txt): Abbruch vor :281, Neustart: protokoll.csv 4 Orders, zustand.orders 2; bericht.md meldet '4 Orders, Volumen 29.992 $, Gebühr gezahlt 23,99 $' bei tatsächlich 12,00 $; Dashboard orders 4. V3 zwei Instanzen: Position laut Protokoll AAA 150 / BBB -300 gegen Zustand 75 / -150. Live-Pfad mit nachgestellter Börse im Prozess (test_inf_betrieb.py, test_ist_inf03_live_absturz_...): Verbindungsabbruch beim Abholen der Fills nach der zweiten Order, zwei Orders stehen an der Börse, zustand.json und protokoll.csv existieren nicht, der nächste Lauf endet mit SystemExit 'weicht vom Protokoll ab' (bot.py:177-182). Laufzeit ohne Obergrenze: yubit.py:78 timeout=20 mal 5 Abrufe je Coin (bot.py:84, 91, 94, 97, 98) mal 10 Coins ergibt bis 1000 s je Konto bei rund 300 s Takt. Im tatsächlichen Verlauf keine doppelten Zeilen und keine Abweichung (konsistenz_zustand.txt).
- **Auswirkung:** Papier: Orderzahl, Volumen und Gebühren in Bericht und Board werden nach einem Abbruch doppelt gezählt, ohne dass es auffällt. Live: Positionen in doppelter Größe (zwei Instanzen) oder Positionen, die der Bot nicht kennt; danach verweigert er den Handel, die Positionen bleiben mit Hebel 3 unbetreut offen.
- **Empfehlung:** Sperrdatei um den gesamten Lauf (flock in stunde.sh und im Bot), Gesamtzeitlimit unter dem Takt. Schreibreihenfolge umdrehen: zuerst ein Journal mit eindeutiger Lauf-Nummer und Order-Kennung (Absicht, Ausführung, Bestätigung) dauerhaft schreiben, Zustand nach jeder einzelnen Ausführung speichern, CSV-Dateien aus dem Journal ableiten. Im Live-Pfad die orderLinkId aus Lauf-Nummer und Coin bilden, damit eine Wiederholung bereits gesendete Orders erkennt; nach einem Abbruch offene Orders abfragen und streichen.
- **Nachstellen:** cd /home/user/OdinGate-Botv134/swing-hybrid && .venv/bin/python -I -B -m pytest -q -p no:cacheprovider reports/audit/evidence/INF/test_inf_betrieb.py -k inf03 ; .venv/bin/python -I -B reports/audit/evidence/INF/bot_versuche.py (Abschnitte V2, V3)

#### INF-04 (P1): Belegter Vorfall 13:44 bis 15:00 UTC: Auslieferung ohne Prüfung, Skript tauscht sich während des eigenen Laufs aus, jeder Folgefehler bricht die ganze Kette ab

- **Sicherheit des Prüfers:** hoch
- **Stand:** nicht gegengeprüft
- **Evidenz:** 14 Commits von 13:50 bis 14:55 UTC mit dem Zusatz '(Verschlüsselungsschritt fehlgeschlagen, nur Lauf-Daten)' (git log -- swing-hybrid/vorwaertstest/lauf); docs/stand.enc.json blieb von 1695511 (13:41:56) bis cf1f1cb (15:00:40) unverändert, also 79 Minuten. Ursache laut cf1f1cb: .gitignore:25 (*.pem) schloss vorwaertstest/board_pub.pem aus, der Runner-Klon hatte die Datei nicht. S3 der Sandbox stellt das nach: Rückgabewert 1 in jedem Lauf, Laufdaten lokal geändert, aber vom Skript nie gesichert, Konto 2 läuft nie (stunde.sh:12 bricht unter set -e vor :13 ab); die Commits des Vorfalls tragen einen abweichenden Text, wurden also von Hand erzeugt. Zweiter Effekt: Commit 4dc3256 (13:44:41, Elternteil 1695511) legt docs/stand.json im Klartext wieder an, obwohl 1695511 die Datei gelöscht und stunde.sh auf Verschlüsselung umgestellt hatte. S4 stellt das mit den beiden historischen Fassungen nach: bash führt die alte Fassung zu Ende, während git pull (stunde.sh:8) die Datei ersetzt. Außerdem wurde bot.py um 17:45 UTC (b8795b3) während des laufenden Test 1 geändert und vom nächsten Lauf ohne Testlauf ausgeführt; in .github gibt es keinen pytest-Aufruf.
- **Auswirkung:** Jede Änderung auf dem Zweig wird binnen fünf Minuten ungeprüft im laufenden Bot wirksam; ein fehlendes Hilfsprogramm oder eine fehlende Datei stoppt Sicherung und Konto 2 vollständig. Die Fortsetzung des Tests hing im Vorfall an einer improvisierenden KI-Sitzung. Die als entfernt geltende Klartextdatei wurde wieder veröffentlicht.
- **Empfehlung:** Publikation (Dashboard, Verschlüsselung, Push) vom Handelsschritt entkoppeln: Laufdaten zuerst sichern, Folgefehler melden statt abbrechen. Startprüfung im Skript (Schlüsseldatei, openssl, Python-Version). Holen und Ausführen trennen (kleiner Starter holt den Stand und startet danach die neue Fassung per exec). Bot-Code nur aus einem getesteten, markierten Stand ausliefern; pytest bei jedem Push automatisch laufen lassen. In .gitignore eine ausdrückliche Ausnahme für board_pub.pem eintragen.
- **Nachstellen:** cd /home/user/OdinGate-Botv134 && git log --format='%h %cI %s' -- docs/stand.enc.json | tail -3 ; git show --stat 4dc3256 | head ; Sandbox wie bei INF-02 (Szenarien s3_schluessel_fehlt und s4_selbstaenderung)

#### INF-05 (P1): Fehlerbehandlung der Marktabfrage: gängige Verbindungsfehler beenden den ganzen Lauf, Teilausfälle werden still übergangen, keine Wiederholung

- **Sicherheit des Prüfers:** hoch
- **Stand:** nicht gegengeprüft
- **Evidenz:** yubit.py:80-83 fängt nur HTTPError, URLError, TimeoutError, JSONDecodeError; bot.py:172 fängt nur YubitFehler, KeyError, ValueError, IndexError. Lokaler Testserver auf 127.0.0.1 über den echten urllib-Pfad (evidence/INF/http_versuch_ausgabe.txt): Verbindung ohne Antwort geschlossen ergibt http.client.RemoteDisconnected, TCP-Reset ergibt ConnectionResetError, abgebrochene Antwort ergibt IncompleteRead, JSON-Liste ergibt AttributeError, Feld null ergibt TypeError: jeweils nicht abgefangen; ein einziger solcher Fehler bei einem von 50 Abrufen lässt bot.schritt mit Ausnahme enden, ohne dass etwas geschrieben wird. HTTP 429, Fehlercode, HTML und Zeitlimit werden korrekt zu YubitFehler. Keine Wiederholung, kein Gesamtlimit (yubit.py:71-78). V5: fehlt ein Coin genau im Lauf des Signaldrehs, gibt es 0 Orders, die Position wird mit dem alten Kurs bewertet (stand.csv brutto -11,25 statt -2411,25 USDT im Beispiel), der Hinweis steht nur in der Rückgabe. V6: eine Kerze, deren Schluss bis 120 Minuten alt ist, wird ohne Hinweis verwendet (bot.py:88). Realer Lauf 15:16 UTC: spannen.csv enthält nur BTC, ETH, SOL, XRP, DOT; Schritt bis Commit 78 s statt Median 29 s; die Ursache ist nirgends festgehalten.
- **Auswirkung:** Ein kurzer Netzfehler lässt über set -e beide Konten für diesen Takt ausfallen; im Stundentakt wäre das eine volle Stunde ohne Signal- und Stop-Prüfung. Bei Teilausfällen ist die Vermögenskurve unbemerkt falsch und ein Signaldreh wird verspätet gehandelt.
- **Empfehlung:** Im Client alle Transport- und Formatfehler (OSError, http.client.HTTPException, ValueError, TypeError, AttributeError) in YubitFehler überführen; zwei bis drei Wiederholungen mit Wartezeit, Gesamtzeitlimit je Lauf. Fehlende oder veraltete Coins je Lauf dauerhaft festhalten (Spalte in stand.csv und Logdatei) und im Board anzeigen. Frischegrenze der Kerze auf einen Takt senken. Plausibilitätsprüfungen ergänzen (Serverzeit gegen lokale Uhr, Buch nicht gekreuzt, Kurse größer null).
- **Nachstellen:** cd /home/user/OdinGate-Botv134/swing-hybrid && .venv/bin/python -I -B reports/audit/evidence/INF/http_versuch.py ; .venv/bin/python -I -B reports/audit/evidence/INF/bot_versuche.py (V5, V6)

#### INF-06 (P1): Keine Protokollierung, kein Alarm; das Board erkennt einen stehenden Bot nicht

- **Sicherheit des Prüfers:** hoch
- **Stand:** nicht gegengeprüft
- **Evidenz:** Der Bot schreibt Meldungen nur auf die Standardausgabe (bot.py:149 melden=print, :282-285); kein logging-Modul, stunde.sh schreibt keine Logdatei (grep). Das Board zeigt das Alter aus dem Feld geschrieben (docs/index.html:477), das dashboard_daten.py:73 aus der Wanduhr setzt; letzter_lauf und takt_minuten kommen in docs/index.html nicht vor (0 Treffer). Die Statuszeile 'Live · Kurse im Sekundentakt' hängt nur an Binance-Ticks (index.html:163, :475), der Countdown 'Nächste Signalprüfung' zielt fest auf Minute :04 (index.html:478). V8: mit STOPP-Datei liefert der Schritt nur gestoppt True, das Dashboard erhält trotzdem einen frischen Wert für geschrieben. Für den Teilausfall um 15:16 UTC und für die Lücken (bis 13 min) gibt es keinerlei Aufzeichnung.
- **Auswirkung:** Ein Stillstand wie in INF-02 oder ein dauerhaft scheiternder Lauf fällt nur auf, wenn jemand zufällig auf die Altersangabe schaut; die grüne Live-Anzeige bleibt dabei an. Ursachen vergangener Störungen lassen sich nicht nachvollziehen.
- **Empfehlung:** Je Lauf eine Zeile in einer dauerhaften Logdatei (Beginn, Ende, Dauer, Abrufe, Hinweise, Rückgabewert, Git-Stand). Alarm an den Betreiber bei Fehler, bei Lücke über zwei Takte und bei Abweichung zwischen lokalem und entferntem Stand. Im Board das Alter aus der letzten Zeile von stand.csv ableiten, ab zwei Takten deutlich warnen, die Live-Anzeige daran koppeln und Takt sowie nächsten Lauf aus der Konfiguration lesen.
- **Nachstellen:** cd /home/user/OdinGate-Botv134 && grep -c 'letzter_lauf\|takt_minuten' docs/index.html ; sed -n 475,479p docs/index.html ; cd swing-hybrid && .venv/bin/python -I -B -m pytest -q -p no:cacheprovider reports/audit/evidence/INF/test_inf_betrieb.py -k inf06

#### INF-07 (P1): Veröffentlichung über Git: zwei Pushes je Lauf, rund 24 Pages-Builds pro Stunde und etwa 12 MB Repo-Zuwachs pro Tag

- **Sicherheit des Prüfers:** mittel
- **Stand:** nicht gegengeprüft
- **Evidenz:** GitHub-API, nur lesend (evidence/INF/pages_builds_github.tsv): 92 Läufe von 'pages build and deployment' zwischen 13:46 und 19:34 UTC, 72 erfolgreich, 20 abgebrochen; in der Stunde ab 18:00 UTC 25 Builds (13 erfolgreich, 12 abgebrochen). Seit Konto 2 wird der Build des ersten Pushs jedes Laufs vom zweiten abgebrochen (stunde.sh:18 und :31). Repo (evidence/INF/repo_wachstum.txt): 76 von 144 Commits im lokalen Stand sind Bot-Commits, Pull Request 1 zählt 159 Commits; neue Objektdaten je Lauf mit zwei Konten Median 41 kB, das sind bei 288 Läufen 11,8 MB pro Tag und 355 MB pro Monat sowie 576 Commits pro Tag. Größter Posten sind die verschlüsselten Stände, die wegen neuem Schlüssel und IV je Lauf (board_verschluesseln.py:25) nicht delta-komprimierbar sind; Hochrechnung nach Erreichen von 400 Verlaufspunkten (dashboard_daten.py:68-71): rund 0,89 GB pro Monat. Die Grenze von 10 Builds pro Stunde für GitHub Pages stammt aus meiner Kenntnis der GitHub-Dokumentation; docs.github.com war aus dieser Umgebung nicht erreichbar, deshalb Vertrauen nur mittel.
- **Auswirkung:** Der Betrieb liegt beim Mehrfachen der mir bekannten weichen Grenze für Pages-Builds; GitHub kann solche Sites drosseln oder abschalten, dann steht das Board. Das Repo wächst in wenigen Monaten über die empfohlene Größe, die Historie ist für Code-Prüfungen kaum noch lesbar.
- **Empfehlung:** Ein Push je Lauf für beide Konten. Board-Daten nicht in die Historie des Arbeitszweigs schreiben: eigener Veröffentlichungszweig mit einem einzelnen, jeweils ersetzten Commit oder Auslieferung über einen Actions-Workflow mit Artefakt oder externer Ablage. Laufdaten gebündelt sichern (zum Beispiel einmal täglich) oder außerhalb von Git führen. Veröffentlichungstakt vom Rechentakt trennen.
- **Nachstellen:** gh api --paginate 'repos/julienbaltrocco-bit/OdinGate-Botv134/actions/runs?per_page=100' -q '.workflow_runs[] | [.run_number,.conclusion,.created_at] | @tsv' ; Auswertung und Hochrechnung siehe evidence/INF/repo_wachstum.txt

#### INF-08 (P2): Der Papierbetrieb prüft nicht den vorgesehenen Live-Betriebsweg: drei verschiedene Zeitgeber und Konfigurationen im Repo

- **Sicherheit des Prüfers:** hoch
- **Stand:** nicht gegengeprüft (nicht vorgesehen)
- **Evidenz:** Tatsächlich läuft nur stunde.sh (config_lauf.json und config_lauf_tpsl.json, Hebel 3, rund alle 5 Minuten, mit Dashboard, Verschlüsselung und Git). server/installieren.sh:36 startet 'bot schritt' ohne --config, also mit config.json (Hebel 0,2, Tagesverlust-Limit 3 %, Ordner daten), stündlich um :03 (:43), ohne Dashboard, ohne Sicherung, ohne OnFailure. .github/workflows/vorwaertstest.yml:36 ebenfalls ohne --config, stündlich um :04 (:8), Ziel-Zweig vorwaertstest-daten, der nicht existiert. Der Workflow ist inaktiv (GitHub-API: einziger registrierter Workflow ist pages-build-deployment; Standard-Zweig feature/content-engine-mvp). Pull Request 1 ist offen mit dem Bot-Zweig als Quelle und dem Standard-Zweig als Ziel: Ein Merge würde den stündlichen Zeitplan automatisch starten. Live verlangt laut README.md:36-38 eine feste, von Yubit freigegebene IP ('nicht bei GitHub'); die KI-Sitzung als Runner erfüllt das nicht.
- **Auswirkung:** Aus dem laufenden Papierbetrieb lassen sich keine Aussagen über Stabilität und Verhalten des späteren Live-Betriebs ableiten (anderer Takt, andere Konfiguration, anderer Datenweg, andere Maschine). Ein Merge des offenen Pull Requests startet unbeabsichtigt einen dritten Papier-Bot.
- **Empfehlung:** Einen einzigen Betriebsweg festlegen und genau diesen im Papiermodus mehrere Wochen betreiben (gleicher Rechner, gleicher Zeitgeber, gleiche Konfigurationsdatei wie später live). installieren.sh auf diesen Weg bringen (--config, Sperre, Zeitlimit, Fehlerbenachrichtigung). Den GitHub-Workflow entfernen oder vor einem Merge deaktivieren.
- **Nachstellen:** cd /home/user/OdinGate-Botv134 && sed -n 36p swing-hybrid/vorwaertstest/server/installieren.sh && sed -n 36p .github/workflows/vorwaertstest.yml && cat swing-hybrid/vorwaertstest/config.json ; gh api repos/julienbaltrocco-bit/OdinGate-Botv134/actions/workflows -q '.workflows[].name'

#### INF-09 (P2): Laufdateien ohne Lauf-Nummer, mit Minutenzeitstempeln und ohne Schutz gegen abgeschnittene Zeilen; fehlender Zustand führt zu stillem Neustart

- **Sicherheit des Prüfers:** hoch
- **Stand:** nicht gegengeprüft (nicht vorgesehen)
- **Evidenz:** bot.py:37-38 Zeitstempel in Minutenauflösung ohne Zeitzonenangabe; :50-59 Anhängen ohne fsync; :62-66 Lesen ohne Fehlertoleranz; :69-71 fehlt zustand.json, beginnt der Bot ohne Hinweis mit leerem Zustand und hängt an die vorhandenen CSV-Dateien an (V2: erneute Einstiege); kern.py:69 schreibt version 1, geprüft wird sie nirgends. V1: zwei Läufe in derselben Minute erzeugen zwei Zeilen mit identischem Zeitstempel und doppelte Messungen. V7: eine abgeschnittene letzte Zeile in protokoll.csv lässt bot.bericht und dashboard_daten.bauen mit TypeError abbrechen, der nächste Lauf klebt seine Zeile an die kaputte an; da bot.py:397 den Bericht nach jedem Schritt schreibt, scheitert danach jeder Lauf. Wachstum: spannen.csv 60,6 Bytes je Zeile, 10 Zeilen je Lauf, bei 5-Minuten-Takt 64 MB pro Jahr und Konto (50 MB nach 286 Tagen); alle drei Dateien werden in jedem Lauf vollständig neu gelesen (bot.py:303, dashboard_daten.py:16).
- **Auswirkung:** Doppelte oder beschädigte Zeilen lassen sich nachträglich nicht sicher erkennen oder zuordnen; ein einziger Schreibabbruch legt Bericht, Dashboard und über set -e die Sicherung dauerhaft lahm. Ein verlorener Zustand mischt zwei Testläufe in einer Datei.
- **Empfehlung:** Jede Zeile mit Lauf-Nummer und Zeitstempel in Sekunden mit Z-Kennung versehen; Schreiben über Zwischendatei und Umbenennen oder SQLite; unvollständige Zeilen beim Lesen überspringen und melden; fehlt zustand.json bei vorhandenen CSV-Dateien, abbrechen statt neu starten; Versionsfeld prüfen. Die Konsistenzprüfung aus evidence/INF/konsistenz.py täglich laufen lassen. spannen.csv monatsweise teilen.
- **Nachstellen:** cd /home/user/OdinGate-Botv134/swing-hybrid && .venv/bin/python -I -B -m pytest -q -p no:cacheprovider reports/audit/evidence/INF/test_inf_betrieb.py -k inf09

#### INF-10 (P2): Im veröffentlichten Ordner docs/ liegen ein veralteter Klartext-Stand und sechs fremde Dokumente; die Laufdaten stehen zusätzlich unverschlüsselt im öffentlichen Repo

- **Sicherheit des Prüfers:** mittel
- **Stand:** teilweise direkt nachgeprüft (docs/stand.json)
- **Evidenz:** git ls-tree HEAD docs/ und GitHub-API für den Zweigkopf: neben index.html, schluessel.json, stand.enc.json und stand_tpsl.enc.json liegen dort stand.json (5847 Bytes, Klartext, Feld geschrieben 2026-11-15T13:44:41Z, mit Positionen und Ergebnis von Test 1) sowie API.md, ARCHITECTURE.md, BLOCKERS.md, COMPLIANCE.md, ROADMAP.md und SETUP.md der Next.js-Anwendung; eine Datei .nojekyll fehlt. Herkunft von stand.json siehe INF-04 (Commit 4dc3256). Unabhängig davon liegen vorwaertstest/lauf/ und lauf_tpsl/ (dashboard.json, zustand.json, CSV-Dateien) im Klartext im Repo, das laut GitHub-API öffentlich ist. Ob GitHub Pages diese Dateien tatsächlich ausliefert, konnte ich nicht abrufen (github.io und die Pages-Einstellungen waren aus dieser Umgebung nicht erreichbar), deshalb Vertrauen mittel.
- **Auswirkung:** Die Passwortabfrage des Boards schützt die Handelsdaten nicht; interne Projektdokumente der anderen Anwendung werden mit veröffentlicht. Die Bewertung der Vertraulichkeit gehört in den Prüfbereich Security.
- **Empfehlung:** docs/stand.json löschen (bleibt in der Historie sichtbar), die sechs Dokumente aus dem Veröffentlichungsordner herausnehmen, einen eigenen Ordner oder Zweig nur für das Board verwenden und .nojekyll anlegen. Entscheiden, ob die Laufdaten vertraulich sein sollen; wenn ja, gehören sie nicht in ein öffentliches Repo.
- **Nachstellen:** cd /home/user/OdinGate-Botv134 && git ls-tree -l HEAD docs/ && python3 -I -c "import json;d=json.load(open('docs/stand.json'));print(d['geschrieben'],d['kennzahlen'][0]['mit_rebate_usd'])"

#### INF-11 (P2): Umgebung und Daten nur teilweise reproduzierbar: keine Sperrdatei für Abhängigkeiten, keine automatischen Tests, Marktdaten ohne Prüfsummen und teils nicht wiederbeschaffbar

- **Sicherheit des Prüfers:** hoch
- **Stand:** nicht gegengeprüft (nicht vorgesehen)
- **Evidenz:** swing-hybrid/requirements.txt nennt acht Pakete mit fester Version, aber ohne Hashes und ohne Festlegung der indirekten Abhängigkeiten (pip freeze der .venv zeigt weit mehr Pakete, zum Beispiel ccxt, aiohttp, cryptography). Python-Versionen uneinheitlich: pyproject.toml verlangt ab 3.12, die .venv ist 3.13.18, der Workflow nimmt 3.12, stunde.sh:10 das python3 des Systems. Die 105 Tests laufen lokal in 3,3 s grün, werden aber nirgends automatisch ausgeführt (kein pytest in .github). Marktdaten (9,7 GB) liegen nur lokal (swing-hybrid/.gitignore); scripts/kerzen_laden.py:21 lädt von data.binance.vision ohne Abgleich der dort angebotenen Prüfsummen (grep nach sha256 und checksum in scripts/*_laden.py: 0 Treffer); data/raw (3,6 GB) und data/download/trading-labor.zip (1,4 GB) haben keine öffentliche Quelle; Yubit-Spannen sind Momentaufnahmen (scripts/yubit_spannen_sammeln.py:15); Tageskurse kommen von einem inoffiziellen Yahoo-Endpunkt (scripts/aktien_laden.py:25, tageskurse_laden.py:18). Ein Verzeichnis der Dateien mit Hashwerten fehlt.
- **Auswirkung:** Geht die Cloud-Umgebung verloren, sind die Forschungsergebnisse nicht bitgenau nachrechenbar; stille Änderungen an Daten oder Bibliotheken bleiben unbemerkt. Fehler im Bot-Code erreichen den Runner ungetestet (siehe INF-04).
- **Empfehlung:** Sperrdatei mit Hashes erzeugen (pip-compile oder uv), eine Python-Version festlegen, pytest bei jedem Push automatisch ausführen. Ein Datenverzeichnis mit Datei, Größe, SHA-256, Quelle und Abrufdatum ins Repo legen, beim Laden die Prüfsummen von Binance abgleichen, Rohdaten ohne öffentliche Quelle extern sichern.
- **Nachstellen:** cd /home/user/OdinGate-Botv134/swing-hybrid && cat requirements.txt && .venv/bin/python -I -B -m pytest -q -p no:cacheprovider | tail -1 && grep -c 'sha256\|checksum' scripts/*_laden.py

#### INF-12 (P3): Live-Server lauscht ohne Zugriffsschutz auf allen Netzwerkschnittstellen und fragt die Börse alle 3 Sekunden ab

- **Sicherheit des Prüfers:** hoch
- **Stand:** nicht gegengeprüft (nicht vorgesehen)
- **Evidenz:** vorwaertstest/live_server.py:108 bindet ThreadingHTTPServer an 0.0.0.0, eine Anmeldung gibt es nicht; :19 TAKT_S = 3.0, das sind rund 28.800 Abrufe aller Ticker pro Tag (:64); Fehler werden nur im Speicher gehalten (:69-71), live_start.sh:6 schreibt das Log nach /tmp. In diesem Container läuft kein solcher Prozess (pgrep ohne Treffer, /tmp/vorwaertstest_live.log leer); ob er beim Betreiber läuft, ist offen.
- **Auswirkung:** Wo der Server läuft, ist der Kontostand für jeden im selben Netz lesbar; die Dauerabfrage kann Abruflimits der Börse berühren, die auch der Bot braucht.
- **Empfehlung:** An 127.0.0.1 binden oder ganz entfernen (das Board in docs/ ersetzt ihn), Abruftakt senken, Log an einen dauerhaften Ort schreiben.
- **Nachstellen:** cd /home/user/OdinGate-Botv134 && sed -n '19p;108p' swing-hybrid/vorwaertstest/live_server.py ; pgrep -af live_server

### Nachgerechnete Aussagen

- **reproduziert**: 105 bestehende Tests sind grün. 105 passed in 3.33s. Die Tests laufen nur von Hand, nicht automatisch. Befehl: `cd /home/user/OdinGate-Botv134/swing-hybrid && .venv/bin/python -I -B -m pytest -q -p no:cacheprovider`
- **reproduziert**: Eine KI-Sitzung führt etwa alle fünf Minuten stunde.sh aus. Test 1: 64 Läufe 13:21 bis 18:58 UTC, Abstand Median 5 min (min 1, max 13). Test 2: 14 Läufe 17:44 bis 18:58 UTC, Median 5 min (max 9). Jeder Lauf hat einen eigenen Commit. Wie die Sitzung den Takt erzeugt, steht nicht im Repo. Befehl: `cd /home/user/OdinGate-Botv134 && python3 -I swing-hybrid/reports/audit/evidence/INF/historie.py .`
- **abweichend**: Stündliche Signalprüfung. Geprüft wird rund alle 5 Minuten gegen die letzte abgeschlossene Stundenkerze; nur 5 von 64 Läufen (8 %) waren der erste Lauf nach einer vollen Stunde (Minute :01 bis :05). Stop und Ziel von Test 2 werden damit etwa zwölfmal so oft geprüft wie im dokumentierten Stundentakt. Befehl: `siehe evidence/INF/historie_takt_luecken.txt`
- **reproduziert**: Zwei Papier-Tests seit 15.11.2026 mit Hebel 3 (Test 2 mit Stop 5 % und Ziel 15 %). Beide Konfigurationen: hebel 3.0, kapital 5000, 10 Coins; Test 2 zusätzlich tp 0.15 und sl 0.05. Test 1 beginnt 13:21 UTC (Neustart, der vorige Lauf mit Hebel 1 wurde in Commit 4276791 archiviert), Test 2 beginnt 17:44 UTC. Befehl: `cd /home/user/OdinGate-Botv134/swing-hybrid/vorwaertstest && cat config_lauf.json config_lauf_tpsl.json && head -2 lauf/stand.csv lauf_tpsl/stand.csv`
- **reproduziert**: Protokoll, Stand und Zustand der beiden laufenden Tests sind untereinander konsistent. Stand 3dfd5b2: je 10 Orders in protokoll.csv, zustand.orders und stand.csv; Positionen und Kasse aus dem Protokoll gleich dem Zustand (Abweichung 0); Vermögen aus zustand.json gleich letzter Zeile von stand.csv; Zeitstempel streng aufsteigend, keine doppelten Zeilen, einheitliche Spaltenzahl. Befehl: `cd /home/user/OdinGate-Botv134 && python3 -I swing-hybrid/reports/audit/evidence/INF/konsistenz.py .`
- **reproduziert**: Vorfall mit fehlgeschlagenem Verschlüsselungsschritt. 14 Commits von 13:50 bis 14:55 UTC; docs/stand.enc.json 79 Minuten unverändert. Mechanismus in der Sandbox nachgestellt (Szenario s3_schluessel_fehlt in evidence/INF/gitsim_ausgabe.txt). Befehl: `cd /home/user/OdinGate-Botv134 && git log --format='%h %cI %s' -- swing-hybrid/vorwaertstest/lauf | grep -c fehlgeschlagen`
- **reproduziert**: Die Workflow-Datei liegt nicht im Standard-Zweig; das Repo ist öffentlich. default_branch feature/content-engine-mvp, visibility public, has_pages true; einziger registrierter Workflow ist pages-build-deployment, der Vorwärtstest-Workflow läuft also nicht. Befehl: `gh api repos/julienbaltrocco-bit/OdinGate-Botv134 -q '{default_branch, visibility, has_pages}' ; gh api repos/julienbaltrocco-bit/OdinGate-Botv134/actions/workflows -q '.workflows[].name'`
- **ungeklaert**: GitHub Pages veröffentlicht den Ordner /docs dieses Zweigs. Bestätigt: jeder Push auf diesen Zweig löst einen Pages-Build aus (92 Builds, alle mit head_branch claude/intelligent-sagan-2cviug). Nicht bestätigt: der eingestellte Quellordner und die tatsächlich ausgelieferten Dateien, weil die Pages-Einstellungen über den Proxy gesperrt sind (HTTP 403) und github.io nicht erreichbar war. Befehl: `gh api --paginate 'repos/julienbaltrocco-bit/OdinGate-Botv134/actions/runs?per_page=100' -q '.workflow_runs[] | [.head_branch,.conclusion] | @tsv' | sort | uniq -c`
- **reproduziert**: Der Bot läuft in einem anderen Klon als die Entwicklung und lief nach dem lokalen Stand weiter. Auf origin folgen nach 3dfd5b2 (19:03 UTC) weitere Bot-Commits bis 19:43 UTC, die lokal fehlen; im reflog dieses Klons gibt es 0 selbst erzeugte Bot-Commits. Der Audit-Commit 3dfd5b2 ist Elternteil des Bot-Commits 015b5b1, wurde also vom Runner per Fast-Forward übernommen. Befehl: `cat /home/user/OdinGate-Botv134/swing-hybrid/reports/audit/evidence/INF/origin_commits_nach_lokalem_stand.tsv ; git -C /home/user/OdinGate-Botv134 reflog | grep -c 'commit: Vorwärtstest'`

### Als richtig befunden

- zustand.json wird über eine Zwischendatei geschrieben und per Umbenennen ersetzt (bot.py:74-77); nach einem Lauf bleibt keine .tmp-Datei zurück (test_ok_zustand_wird_ueber_zwischendatei_ersetzt).
- Der Handel ist über den Zustand idempotent: ein zweiter Lauf zum selben Zeitpunkt erzeugt keine Orders (Versuch V1, test_ok_zweiter_lauf_zur_selben_zeit_handelt_nicht).
- Die CSV-Dateien beider Tests sind laut Historie nur gewachsen: 68 Versionen bei Test 1 und 14 bei Test 2, einzige nicht-anhängende Änderung ist der dokumentierte Neustart mit Hebel 3 in Commit 4276791 (evidence/INF/historie_takt_luecken.txt).
- Jede Zeile in stand.csv hat einen eigenen Commit; bis 3dfd5b2 ging kein Lauf verloren und es gab keine Abweichung zwischen Runner und origin, die mehrere Läufe in einem Commit hinterlassen hätte.
- Protokoll, Stand und Zustand stimmen für beide Tests überein; keine doppelten Zeitstempel, Zeit streng aufsteigend, einheitliche Spaltenzahl, keine CRLF-Zeilenenden (evidence/INF/konsistenz_zustand.txt).
- Zeitangaben sind durchgehend UTC: bot.py:37-38, Tageswechsel des Verlustlimits bot.py:192, Dashboard hängt Z an (dashboard_daten.py:20), Commit-Zeiten +00:00.
- Ein kurzer Ausfall von origin wird verkraftet: der lokale Commit bleibt erhalten und wird beim nächsten erfolgreichen Lauf mit gepusht (Sandbox s2_netzausfall); Einschränkung siehe INF-02 (Konto 2 fällt in diesem Lauf aus).
- Der Yubit-Client wandelt HTTP-Fehler, Fehlercodes, Zeitlimit und Nicht-JSON in YubitFehler um, der Bot überspringt dann nur den betroffenen Coin (evidence/INF/http_versuch_ausgabe.txt, erste sechs Zeilen).
- Fehlen alle Marktdaten, bricht der Bot ab, ohne etwas zu schreiben (bot.py:174-175, test_ok_ohne_marktdaten_wird_nichts_geschrieben); Kerzen mit einem Schluss älter als zwei Stunden werden abgelehnt (bot.py:88).
- Die STOPP-Datei wird beachtet (bot.py:151-153, Versuch V8).
- Der GitHub-Workflow hat eine Nebenläufigkeitsgruppe und ein Zeitlimit von 10 Minuten (.github/workflows/vorwaertstest.yml:14-16, :21); er ist allerdings nicht aktiv.
- Das Board lädt den Stand mit wechselndem Abfrageparameter und cache: no-store (docs/index.html:408), ein veralteter Zwischenspeicher verfälscht die Anzeige also nicht.
- Zwischen dem genannten Prüfstand 0e92022 und dem lokalen Stand 3dfd5b2 hat sich außerhalb von reports/audit nur der Datenbestand von vier Bot-Läufen geändert, kein Code (git diff --stat 0e92022 3dfd5b2).
- Während dieser Prüfung wurden die Papier-Daten nicht verändert: stunde.sh, Bot und dashboard_daten liefen nur in temporären Verzeichnissen bzw. in der Sandbox; git status zeigt außerhalb von reports/audit keine Änderung.

### Ungeklärt

- Wie die KI-Sitzung den Takt erzeugt, wie lange sie lebt und was bei ihrem Ende geschieht: im Repo gibt es dazu nichts; ob Läufe streng nacheinander gestartet werden oder ein Werkzeug-Zeitlimit einen Lauf mittendrin beenden kann, ließ sich nicht prüfen.
- Ursache des Teilausfalls im Lauf 15:16 UTC (nur 5 von 10 Coins gemessen, Lauf 78 s statt 29 s) und Ursache der Lücken bis 13 Minuten (15:51 auf 16:04, dazu 17:04, 17:56 und 18:04): es existiert kein Protokoll.
- Ob GitHub Pages docs/stand.json und die sechs Markdown-Dokumente tatsächlich ausliefert und welcher Quellordner eingestellt ist: github.io war nicht erreichbar, die Pages-Einstellungen sind über den Proxy gesperrt.
- Die Grenzen von GitHub Pages (10 Builds pro Stunde, Größenempfehlungen) stammen aus meiner Kenntnis der GitHub-Dokumentation; docs.github.com war nicht erreichbar, ob und wann GitHub hier eingreift, ist offen.
- Abruflimits von Yubit für öffentliche Endpunkte und die Frage, ob Yubits Regel zu Rechenzentrums-IPs (YUBIT_REGELN.md, Abschnitt 1) schon das Lesen von Kursdaten aus einer Cloud-Sitzung betrifft: aus dem Repo nicht zu klären.
- Der entfernte Stand nach 3dfd5b2 wurde nur über die GitHub-API gelesen (Commit-Liste, Ordnerliste, Builds); der Inhalt der Laufdateien nach 18:58 UTC wurde nicht geprüft, weil git fetch untersagt war.
- Der Commit 3dfd5b2 ('Audit: Zwischenstand der Evidenzdateien') wurde von einem früheren Audit-Lauf auf den Bot-Zweig gepusht, nicht von mir. Er ist selbst ein Beispiel für das Risiko aus INF-02; weitere Audit-Commits auf diesen Zweig sollten bis zur Behebung unterbleiben oder nur außerhalb des Lauf-Fensters erfolgen.
- Ob live_server.py beim Betreiber läuft und von außen erreichbar ist.
- Die Hochrechnungen zum Repo-Wachstum (0,89 GB pro Monat nach Erreichen von 400 Verlaufspunkten) sind Rechnungen unter den in evidence/INF/repo_wachstum.txt genannten Annahmen, keine Messungen.

### Evidenzdateien

- `/home/user/OdinGate-Botv134/swing-hybrid/reports/audit/evidence/INF/historie.py`
- `/home/user/OdinGate-Botv134/swing-hybrid/reports/audit/evidence/INF/historie_takt_luecken.txt`
- `/home/user/OdinGate-Botv134/swing-hybrid/reports/audit/evidence/INF/konsistenz.py`
- `/home/user/OdinGate-Botv134/swing-hybrid/reports/audit/evidence/INF/konsistenz_zustand.txt`
- `/home/user/OdinGate-Botv134/swing-hybrid/reports/audit/evidence/INF/gitsim.sh`
- `/home/user/OdinGate-Botv134/swing-hybrid/reports/audit/evidence/INF/gitsim_ausgabe.txt`
- `/home/user/OdinGate-Botv134/swing-hybrid/reports/audit/evidence/INF/gitsim_stellvertreter_bot.py`
- `/home/user/OdinGate-Botv134/swing-hybrid/reports/audit/evidence/INF/gitsim_stellvertreter_dashboard_daten.py`
- `/home/user/OdinGate-Botv134/swing-hybrid/reports/audit/evidence/INF/gitsim_stellvertreter_board_verschluesseln.py`
- `/home/user/OdinGate-Botv134/swing-hybrid/reports/audit/evidence/INF/bot_versuche.py`
- `/home/user/OdinGate-Botv134/swing-hybrid/reports/audit/evidence/INF/bot_versuche_ausgabe.txt`
- `/home/user/OdinGate-Botv134/swing-hybrid/reports/audit/evidence/INF/http_versuch.py`
- `/home/user/OdinGate-Botv134/swing-hybrid/reports/audit/evidence/INF/http_versuch_ausgabe.txt`
- `/home/user/OdinGate-Botv134/swing-hybrid/reports/audit/evidence/INF/test_inf_betrieb.py`
- `/home/user/OdinGate-Botv134/swing-hybrid/reports/audit/evidence/INF/pages_builds_github.tsv`
- `/home/user/OdinGate-Botv134/swing-hybrid/reports/audit/evidence/INF/origin_commits_nach_lokalem_stand.tsv`
- `/home/user/OdinGate-Botv134/swing-hybrid/reports/audit/evidence/INF/reflog_entwicklerklon.txt`
- `/home/user/OdinGate-Botv134/swing-hybrid/reports/audit/evidence/INF/repo_wachstum.txt`

## Bereich SEC: Security

Der Passwortschutz des Trading Boards schützt derzeit nichts: Der Stand, der für docs/stand*.enc.json verschlüsselt wird, liegt im selben Commit unverschlüsselt unter swing-hybrid/vorwaertstest/lauf*/ (88 von 88 geprüften Paaren längengleich), und docs/stand.json wird zusätzlich im Klartext mitveröffentlicht. Heute sind das nur Papierdaten, bei echtem Geld wären Positionen, Größen und Stop-Kurse öffentlich. Geheimnisse (API-Schlüssel, Tokens, private Schlüssel) wurden in 144 Commits und 922 Blobs nicht gefunden; Schlüssel werden nur aus Umgebungsvariablen gelesen und tauchen weder in Dateien noch in Fehlertexten auf. Die drei Schranken vor echten Orders (modus, YUBIT_LIVE=ja, Schlüssel) wirken in allen 28 getesteten Kombinationen; ein Pfad zu versehentlichem Live-Handel wurde nicht gefunden. Im Live-Pfad selbst blockiert der Sicherheitsdeckel max_order_usd aber auch das Schließen: Ein Short lässt sich bei den laufenden Einstellungen nach rund +33 % nicht mehr schließen (nachgestellt reproduziert). Die Stärke der Schlüsseldatei gegen Offline-Angriffe hängt allein am unbekannten Passwort; das Regelrisiko bei Yubit (Bot-Genehmigung, Rebate-Klausel) ist im Repo benannt, aber nicht ausgeräumt.

### Befunde

#### SEC-01 (P0): Passwortschutz des Boards ist wirkungslos: derselbe Stand liegt unverschlüsselt im selben öffentlichen Repo

- **Sicherheit des Prüfers:** hoch
- **Stand:** direkt nachgeprüft (Klartext-Stand liegt im Repo)
- **Evidenz:** swing-hybrid/vorwaertstest/stunde.sh:12-13 und 25-26: board_verschluesseln liest vorwaertstest/lauf/dashboard.json, danach `git add vorwaertstest/lauf ../docs/stand.enc.json` (Klartext und Chiffrat im selben Commit). `git ls-files` führt lauf/, lauf_tpsl/ und lauf_hebel1_archiv/ mit dashboard.json, zustand.json, protokoll.csv, stand.csv, spannen.csv, bericht.md. Längenvergleich ohne Entschlüsselung: in 88 von 88 Paaren über die ganze Historie ist bytes(Chiffrat) = (bytes(dashboard.json)//16+1)*16, z. B. Commit be1f4dd: 12896 zu 12890 und 7376 zu 7370 (evidence/SEC/chiffrat_vs_klartext_laengen.txt). Klartext Test 2 am HEAD: BTC Short, Einstieg 64599.2, Menge -0.023, stop_kurs 67829.16, ziel_kurs 54909.32. Historie: 68 Fassungen von lauf/dashboard.json, 65 von lauf/zustand.json (evidence/SEC/fassungen_in_historie.txt). Zusätzlich offen: config_lauf*.json (Kapital, Hebel, Stop/Ziel) und reports/ (Regel, alle Ergebnisse).
- **Auswirkung:** Wer das Repo liest, sieht ohne Passwort alle Positionen, Stückzahlen, Einstiege, Stop- und Zielkurse, jede Order und den Kontoverlauf, lückenlos seit Start. Die Passwortabfrage hält nur Besucher der Pages-Adresse ab, die das Repo nicht öffnen. Aktuell betrifft das Papierdaten (Schaden gering, aber falsches Sicherheitsgefühl). Mit derselben Kette und echtem Geld wäre es ein Vertraulichkeitsvorfall.
- **Empfehlung:** Entscheiden, ob die Daten vertraulich sein sollen. Wenn ja: Laufdaten (lauf*/) nicht mehr in ein öffentliches Repo schreiben, sondern in ein privates Daten-Repo oder auf einen Server; öffentlich nur index.html, schluessel.json und *.enc.json. Die bisherige Historie bleibt öffentlich lesbar; entweder so akzeptieren (Papierdaten) oder Repo privat stellen bzw. Historie bereinigen. Wenn nein: Passwortabfrage entfernen, damit kein Schutz vorgetäuscht wird. Vor Stufe live zwingend klären.
- **Nachstellen:** cd /home/user/OdinGate-Botv134 && python3 -I swing-hybrid/reports/audit/evidence/SEC/laengenvergleich.py . | tail -1 ; git show HEAD:swing-hybrid/vorwaertstest/lauf_tpsl/dashboard.json | head -c 600

#### SEC-02 (P0): Live-Pfad: Sicherheitsdeckel max_order_usd blockiert auch Schließ-Orders, Position bleibt offen

- **Sicherheit des Prüfers:** hoch
- **Stand:** Sachverhalt über ENG-01 bestätigt
- **Evidenz:** swing-hybrid/vorwaertstest/bot.py:130-131 prüft `menge * preis > cfg["max_order_usd"]` für jede Order; Schließ-Orders (bot.py:232-233, reduce_only) laufen über dieselbe Funktion (bot.py:244), ebenso das Schließen beim Tagesverlust-Limit und bei Stop/Ziel. Nachgestellt (Stufe live, nachgestellte Börse, temporäres Verzeichnis): Short 15 Stück zu 100 (1500 USDT), Kurs steigt auf 140, Signal dreht auf Long -> Warnung 'AAA: Order fehlgeschlagen (Order über dem Sicherheitsdeckel (2102 > 2000 USDT))', Position laut Buch danach weiter -15.0, keine Order gesendet (evidence/SEC/live_schranken.txt, Teil 2). Laufende Einstellungen: Zielbetrag 1500 USDT je Coin (5000 x 3 / 10), Deckel 2000 (config_lauf.json, config_lauf_tpsl.json) -> Schwelle rund +33 %; config.json: 100 zu 150 -> +50 %.
- **Auswirkung:** Betrifft nur Stufe live, die nicht aktiv ist. Dort ließe sich eine Position, deren Wert über den Deckel gewachsen ist, weder beim Umkehrsignal noch per Stop oder Tagesverlust-Limit schließen; der Bot wiederholt den Fehlversuch jede Stunde. Bei einem Short ist der Verlust dann nach oben offen, bis von Hand eingegriffen oder liquidiert wird. Die Sicherung wirkt genau im Ernstfall gegen den Betreiber.
- **Empfehlung:** Deckel nur auf eröffnende Orders anwenden; reduce-only-Orders immer zulassen (höchstens gegen die Positionsgröße laut Börse prüfen). Regressionstest aus evidence/SEC/live_schranken.py in tests/ übernehmen, bevor bot.py geändert wird. Vor jedem Live-Betrieb beheben. Überschneidung mit dem Prüfbereich Trading Engine möglich.
- **Nachstellen:** cd /home/user/OdinGate-Botv134/swing-hybrid && env -u YUBIT_LIVE -u YUBIT_API_KEY -u YUBIT_API_SECRET .venv/bin/python -I -B reports/audit/evidence/SEC/live_schranken.py . | tail -6

#### SEC-03 (P1): docs/stand.json: unverschlüsselter Stand liegt weiter im veröffentlichten Ordner

- **Sicherheit des Prüfers:** hoch
- **Stand:** direkt nachgeprüft (Datei liegt im Repo)
- **Evidenz:** `git ls-files docs/` enthält docs/stand.json. Verlauf: 360fa1b (13:32) angelegt, 1695511 (13:41:56, 'Stand nur noch verschlüsselt in docs/') gelöscht, 4dc3256 (13:44:41, automatischer Lauf 'Vorwärtstest (Papier)') wieder angelegt: Ein noch laufender Durchlauf mit der alten stunde.sh (`cp ... ../docs/stand.json; git add`) hat die Datei drei Minuten nach der Umstellung erneut eingecheckt. Inhalt am HEAD: geschrieben 2026-11-15T13:44:41Z, 10 Positionen mit Einstieg, Menge, Kasse, 10 Orders, Kapital 5000, Hebel 3.
- **Auswirkung:** Wenn GitHub Pages den Ordner /docs ausliefert, ist dieser Stand unter <Pages-Adresse>/stand.json ohne Passwort abrufbar, direkt neben dem geschützten Board. Die Commit-Nachricht von 1695511 behauptet das Gegenteil. Der Vorfall zeigt außerdem, dass Code-Umstellungen und der 5-Minuten-Lauf sich gegenseitig überschreiben können.
- **Empfehlung:** docs/stand.json per `git rm` entfernen (durch den Betreiber, nicht im Audit). Vor Änderungen an stunde.sh den Takt anhalten. Prüfschritt ergänzen, der fehlschlägt, wenn unter docs/ eine andere JSON-Datei als schluessel.json und *.enc.json liegt.
- **Nachstellen:** cd /home/user/OdinGate-Botv134 && git log --format='%h %ad %s' --date=format:'%H:%M:%S' --name-status -- docs/stand.json && git show HEAD:docs/stand.json | head -c 400

#### SEC-04 (P1): Schlüsseldatei des Boards: Schutz gegen Offline-Angriff hängt allein am Passwort, kein Schlüsselwechsel möglich

- **Sicherheit des Prüfers:** mittel
- **Stand:** nicht gegengeprüft
- **Evidenz:** docs/schluessel.json: PBKDF2-HMAC-SHA256, runden 600000, Salz 16 Byte, Chiffrat 1232 Byte (= AES-256-CBC über PKCS8 RSA-2048). docs/index.html:147-150 leitet 384 Bit ab (Schlüssel + IV), 154-156 entschlüsselt und importiert. Nachbau mit Wegwerf-Schlüssel und erfundenem Passwort (evidence/SEC/kdf_nachbau.txt): (1) Zum Prüfen eines Kandidaten genügt der erste PBKDF2-Block, der IV ist unnötig; der Angreifer zahlt 600.000 Runden, der Nutzer 1.200.000. (2) Der Klartext ist bekannt (fester PKCS8-Kopf 0d0101010500048204a8308204a40201, Modulus aus vorwaertstest/board_pub.pem), die Prüfung ist eindeutig. Gemessen: 0,105 s je Versuch auf einem CPU-Kern (9,5/s). Annahme für eine aktuelle Grafikkarte rund 14.800 Versuche/s (veröffentlichte hashcat-Werte, nicht hier gemessen): 6 Ziffern 1,1 Min., 10 Mio. häufige Passwörter 11 Min., 6 Kleinbuchstaben 5,8 Std., 8 Kleinbuchstaben 163 Tage (100 Karten: 1,6 Tage), 8 Zeichen Groß/Klein/Ziffern 467 Jahre, 5 Zufallswörter praktisch unerreichbar (evidence/SEC/transport_und_kdf.txt). Historie: schluessel.json 1 Fassung, 46 + 14 Fassungen der *.enc.json (evidence/SEC/fassungen_in_historie.txt). board_verschluesseln.py:20-28: AES-CBC ohne Integritätsschutz, keine Signatur der Pakete.
- **Auswirkung:** Die Parameter entsprechen dem üblichen Mindestwert für PBKDF2, das Verfahren ist aber auf Grafikkarten gut parallelisierbar. Ein kurzes oder gängiges Passwort fällt in Minuten bis Stunden, unbemerkt und ohne Zugriffsversuche auf die Seite. Schlüsseldatei und alle bisherigen Chiffrate bleiben in der öffentlichen git-Historie: Ein späterer Passwortwechsel schützt alte Stände nicht, und mit dem einen statischen RSA-Schlüssel sind alle künftigen Stände lesbar. Da der öffentliche Schlüssel im Repo liegt, kann jeder mit Schreibzugriff gültige Stand-Pakete erzeugen; das Board erkennt nicht, ob Daten vom Bot stammen. Solange SEC-01 besteht, ist der Angriff allerdings gar nicht nötig.
- **Empfehlung:** Passwort als lange Zufallsphrase wählen (mindestens 5 Zufallswörter oder 14 zufällige Zeichen) und nirgends sonst verwenden. Bei Neuaufsetzen: neues RSA-Schlüsselpaar, speicherhartes Verfahren (Argon2id oder scrypt) oder zumindest nur 256 Bit ableiten und IV zufällig beilegen; AES-GCM statt CBC; Pakete zusätzlich vom Bot signieren. Erzeugung der Schlüsseldatei als Skript ins Repo legen, damit sie prüfbar ist.
- **Nachstellen:** cd /home/user/OdinGate-Botv134/swing-hybrid && python3 -I reports/audit/evidence/SEC/kdf_nachbau.py && .venv/bin/python -I -B reports/audit/evidence/SEC/transport_und_kdf.py . | sed -n '8,30p'

#### SEC-05 (P1): Regelrisiko Yubit: Bot nur mit Genehmigung, Rebate-Klausel trifft den Kern des Ansatzes, kein Beleg einer Freigabe

- **Sicherheit des Prüfers:** mittel
- **Stand:** nicht gegengeprüft
- **Evidenz:** swing-hybrid/vorwaertstest/YUBIT_REGELN.md:8-10 (automatisierte Orders nur mit vorheriger Genehmigung; verboten sei das Verschleiern der Herkunft über VPN, Proxy oder Rechenzentrums-IPs), :19-24 (Rebate-Arbitrage untersagt, Maßnahmen: Rebate abziehen, Gewinne streichen, Konto sperren), :27 ('Sein Gewinn stammt aber überwiegend aus dem Rebate'), :30-33 (verbundene Konten). swing-hybrid/reports/suche_bericht.md:19-21: im Prüfzeitraum +9,1 % Rebate gegen +2,4 % Nettogewinn, ohne Rebate −6,6 %. Im Repo findet sich keine Bestätigung von Yubit (Suche nach genehmig/zusage/partner: nur Hinweise, selbst nachzufragen). Der Papier-Bot ruft die öffentlichen Kursdaten derzeit aus einer Cloud-Sitzung ab; die Workflow-Datei würde von GitHub-Servern abrufen.
- **Auswirkung:** Bei echtem Geld kann die Börse nach eigener Regel Rebate und Gewinne einziehen oder das Konto sperren. Das Ergebnis 'mit Rebate' steht damit unter einem Vorbehalt, den der Betreiber nicht selbst kontrolliert. Für den Papierbetrieb ohne Konto ist das Risiko auf eine IP-Sperre begrenzt.
- **Empfehlung:** Vor Stufe live schriftliche Bestätigung von Yubit einholen: stündlich laufendes Programm über die offizielle Schnittstelle, Rebate-Satz und -Weg, Zulässigkeit eines Partner-Kontos, IP-Freigabe. Bestätigung außerhalb des öffentlichen Repos ablegen. Entscheidungen auf der Kennzahl ohne Rebate aufbauen, solange keine Zusage vorliegt.
- **Nachstellen:** cd /home/user/OdinGate-Botv134/swing-hybrid && sed -n 6,33p vorwaertstest/YUBIT_REGELN.md && sed -n 19,21p reports/suche_bericht.md

#### SEC-06 (P2): Board lädt fremdes Skript ohne Integritätsprüfung vor der Passworteingabe; abgeleiteter Schlüssel dauerhaft in localStorage

- **Sicherheit des Prüfers:** hoch
- **Stand:** nicht gegengeprüft (nicht vorgesehen)
- **Evidenz:** docs/index.html:138 `<script src="https://unpkg.com/lightweight-charts@4.2.0/...">` ohne integrity/crossorigin, eingebunden vor dem Skript mit der Passwortabfrage. Keine Content-Security-Policy und keine Referrer-Vorgabe im Dokument (grep: 0 Treffer). docs/index.html:490-491 und 499: die 48 abgeleiteten Byte (AES-Schlüssel + IV zum privaten Schlüssel) werden als 'board-schluessel' unbefristet in localStorage abgelegt; 507 löscht sie nur bei 'Sperren'. Kein docs/CNAME: Die Seite liegt damit voraussichtlich unter <konto>.github.io, dessen Projektseiten sich einen Ursprung und damit denselben localStorage teilen. Verbindungen zu Dritten: unpkg.com, fapi.binance.com, fstream.binance.com (index.html:163, 369, 399, 438, 449, 463).
- **Auswirkung:** Wird die Auslieferung über unpkg manipuliert, läuft fremder Code mit vollem Zugriff auf Passwortfeld, gespeicherten Schlüssel und entschlüsselte Daten. Der gespeicherte Wert ersetzt das Passwort: Wer das Browserprofil oder eine andere Seite desselben github.io-Kontos kontrolliert, kann das Board öffnen. Binance und unpkg sehen IP-Adresse und Aufrufzeiten der Betrachter.
- **Empfehlung:** Bibliothek in docs/ selbst ablegen oder integrity-Hash (sha384) und crossorigin=anonymous setzen. Content-Security-Policy per meta-Element (script-src 'self' plus Hash des Inline-Skripts, connect-src nur die beiden Binance-Hosts). Schlüssel in sessionStorage statt localStorage oder als nicht exportierbaren CryptoKey in IndexedDB halten und befristen. Eigene Domain oder eigenes Pages-Konto für das Board.
- **Nachstellen:** cd /home/user/OdinGate-Botv134 && grep -n -E '<script src|integrity|Content-Security-Policy|localStorage' docs/index.html

#### SEC-07 (P2): Betriebsmodell: Code und Grenzwerte kommen bei jedem Lauf ungeprüft aus dem öffentlichen Zweig

- **Sicherheit des Prüfers:** mittel
- **Stand:** nicht gegengeprüft (nicht vorgesehen)
- **Evidenz:** swing-hybrid/vorwaertstest/stunde.sh:6-8 holt den Zweig (`git fetch`, `checkout`, `pull --ff-only`, Fehler werden mit `|| true` übergangen), 10-12 und 23-25 führen danach Python-Module aus diesem Stand aus, 18 und 31 pushen. bot.py:41-47 prüft in der Konfiguration nur `modus` und `0 < hebel <= 5`; kapital_usd, max_order_usd, coins, tagesverlust_limit (in config_lauf*.json auf 1.0, also 100 %) sind unbegrenzt. Alle drei Konfigurationsdateien sind eingecheckt. Der Lauf findet laut Betreiber in einer KI-Sitzung mit Push-Recht statt (uebergabe_fuer_dritte.md:57). Branch-Schutz und Schreibberechtigte sind aus dem Repo nicht ersichtlich.
- **Auswirkung:** Heute: Wer in den Zweig schreiben kann, bestimmt, welcher Code alle fünf Minuten in der Laufumgebung ausgeführt wird, und kann Papier-Ergebnisse und Board verändern. Würde dieselbe Kette mit Schlüsseln und YUBIT_LIVE=ja betrieben, hingen die verbleibende dritte Schranke (modus) und alle Größenbegrenzungen an Schreibrechten auf ein öffentliches Repo. Der dokumentierte Live-Weg (systemd, installieren.sh) zieht nicht automatisch nach, nutzt aber ebenfalls die eingecheckte config.json.
- **Empfehlung:** Für Stufe live: kein automatisches Nachziehen; festen, geprüften Commit ausrollen. Live-Konfiguration außerhalb des Repos (z. B. /etc) und harte Obergrenzen für Kapital, Ordergröße und Hebel im Code. Branch-Schutz mit Prüfpflicht. Laufdaten mit einem eigenen, eng begrenzten Schlüssel in ein getrenntes Daten-Repo schreiben statt mit den Rechten der KI-Sitzung.
- **Nachstellen:** cd /home/user/OdinGate-Botv134/swing-hybrid && sed -n 4,13p vorwaertstest/stunde.sh && sed -n 41,47p vorwaertstest/bot.py

#### SEC-08 (P2): live_server.py lauscht auf allen Schnittstellen ohne Anmeldung und ohne TLS

- **Sicherheit des Prüfers:** hoch
- **Stand:** nicht gegengeprüft (nicht vorgesehen)
- **Evidenz:** swing-hybrid/vorwaertstest/live_server.py:108 `ThreadingHTTPServer(("0.0.0.0", a.port), Handler)`; 86-95: /api/stand liefert Konto, Positionen, Einstiege, Ergebnis und die letzten 12 Orders an jeden Aufrufer, ohne Prüfung; 97-98 schaltet das Zugriffsprotokoll ab. live_start.sh:5-6 startet ihn im Hintergrund auf Port 8765 und schreibt nach /tmp/vorwaertstest_live.log (fester Name in /tmp). Auf dieser Maschine liegt eine solche Logdatei vom 15.11. 13:14 UTC; aktuell läuft kein Prozess und kein Port ist offen.
- **Auswirkung:** Auf einem Server mit öffentlicher Adresse oder in einem geteilten Netz ist der vollständige Kontostand für jeden lesbar, der Port 8765 erreicht; Zugriffe hinterlassen keine Spur. Nur lesend, kein Eingriff in den Bot möglich.
- **Empfehlung:** Standardbindung 127.0.0.1, Adresse als Parameter; Zugriff von außen nur über SSH-Tunnel oder vorgeschalteten Proxy mit Anmeldung und TLS. Logdatei in ein eigenes Verzeichnis mit engen Rechten. Zugriffsprotokoll einschalten.
- **Nachstellen:** cd /home/user/OdinGate-Botv134/swing-hybrid && grep -n -E '0\.0\.0\.0|api/stand|log_message' vorwaertstest/live_server.py && cat vorwaertstest/live_start.sh

#### SEC-09 (P2): Daten eines fremden Signal-Dienstes im öffentlichen Repo

- **Sicherheit des Prüfers:** mittel
- **Stand:** nicht gegengeprüft (nicht vorgesehen)
- **Evidenz:** swing-hybrid/reports/suche_runde18_trades.csv (173 Zeilen) und suche_runde20a_trades.csv (185 Zeilen): Spalte `signal` mit den Zeitstempeln des Dienstes auf Mikrosekunden (z. B. 2026-08-17 11:58:26.072946), 51 Coins, 17.08. bis 14.11.2026; erzeugt in scripts/suche_runde18.py:16-17 aus data/raw/plimaflow/historie.parquet mit Filter p_win >= 0,6. reports/suche_protokoll.md:853-859 nennt den Anbieter, den Abruf 'über die Lese-Schnittstelle' (254.696 Einträge) und dessen interne Statistik (617 echte Trades, 51,5 % Treffer, Rendite 0). Die Rohseiten tragen ein Feld meta.tier (abgestufter Zugang). Die Rohdaten selbst (rund 96 MB) sind nicht in git; ein Abrufskript fehlt im Repo.
- **Auswirkung:** Die qualifizierten Signale eines zugangsbeschränkten Dienstes samt dessen Leistungszahlen sind öffentlich nachlesbar. Je nach Nutzungsbedingungen kann das eine Vertragsverletzung sein und den Zugang kosten. Die Bedingungen liegen dem Audit nicht vor.
- **Empfehlung:** Nutzungsbedingungen des Dienstes prüfen. Bis zur Klärung die beiden CSV-Dateien und die Anbieter-Statistik aus dem öffentlichen Repo nehmen (nur aggregierte Kennzahlen behalten) oder das Repo privat stellen. Abrufweg dokumentieren, Zugangsdaten dabei außerhalb des Repos halten.
- **Nachstellen:** cd /home/user/OdinGate-Botv134/swing-hybrid && head -3 reports/suche_runde18_trades.csv && wc -l reports/suche_runde18_trades.csv reports/suche_runde20a_trades.csv && sed -n 853,859p reports/suche_protokoll.md

#### SEC-10 (P2): Lieferkette: nur 8 von 89 Paketen festgeschrieben, ungenutztes freqtrade bringt 70 Pakete mit

- **Sicherheit des Prüfers:** hoch
- **Stand:** nicht gegengeprüft (nicht vorgesehen)
- **Evidenz:** swing-hybrid/requirements.txt: 8 Zeilen mit ==, keine Hashes, keine Sperrdatei. .venv: 89 Pakete (evidence/SEC/venv_pakete.txt). Abhängigkeitsabschluss: ohne freqtrade 18 Pakete, 70 nur wegen freqtrade (ccxt, fastapi, uvicorn, aiohttp, python-telegram-bot, SQLAlchemy, cryptography u. a.; evidence/SEC/venv_abhaengigkeiten.txt). `grep freqtrade` in src, scripts, vorwaertstest, tests, labor_strategie: kein Import. .github/workflows/vorwaertstest.yml:23-24 bindet actions/checkout@v4 und setup-python@v5 per verschiebbarem Tag ein, bei `contents: write` (11-12). scripts/kerzen_laden.py:42-45 und die übrigen Ladeskripte prüfen die CHECKSUM-Dateien des Binance-Archivs nicht. src/hybrid/walkforward.py:28-29 lädt Pickle-Dateien aus data/processed/laeufe (eigene Zwischenergebnisse aus scripts/raster.py:29-30).
- **Auswirkung:** Indirekte Abhängigkeiten können sich bei jeder Neuinstallation ändern; Forschungsergebnisse sind dann nicht bitgenau wiederholbar, und ein kompromittiertes Paket liefe in der Umgebung, die auch den Bot startet. Der Bot selbst nutzt nur die Standardbibliothek, was die Angriffsfläche des Teils, der später Schlüssel hält, klein hält. Pickle führt beim Laden beliebigen Code aus, falls jemand die Dateien im als nicht vertrauenswürdig eingestuften data/-Ordner austauscht.
- **Empfehlung:** freqtrade aus requirements.txt streichen, sofern nicht gebraucht. Sperrdatei mit Hashes erzeugen (pip-compile --generate-hashes oder uv lock) und mit --require-hashes installieren. Bot und Forschung in getrennten Umgebungen halten. Actions auf Commit-SHA festlegen. Archiv-Prüfsummen prüfen. Zwischenergebnisse als Parquet/NPZ statt Pickle speichern. Regelmäßig pip-audit laufen lassen.
- **Nachstellen:** cd /home/user/OdinGate-Botv134/swing-hybrid && cat requirements.txt && .venv/bin/python -I -m pip list --format=freeze | wc -l && cat reports/audit/evidence/SEC/venv_abhaengigkeiten.txt

#### SEC-11 (P3): Yubit-Client folgt Weiterleitungen und reicht signierte Kopfzeilen an fremde Hosts weiter; Schema der Basisadresse ungeprüft

- **Sicherheit des Prüfers:** hoch
- **Stand:** nicht gegengeprüft (nicht vorgesehen)
- **Evidenz:** swing-hybrid/vorwaertstest/yubit.py:39-42 nimmt jede `basis` an (auch http://) und nutzt urllib.request.urlopen mit Standard-Weiterleitung; 76-78 sendet mit timeout=20. Lokaler Versuch mit zwei Testservern auf 127.0.0.1 und erfundenem Schlüssel: Nach einer 302-Weiterleitung auf einen anderen Hostnamen kommen dort Mf-Access-Api-Key, Mf-Access-Timestamp, Mf-Access-Recv-Window und Mf-Access-Sign an (evidence/SEC/transport_und_kdf.txt, Teil a). Die Zertifikats- und Hostnamenprüfung selbst ist nicht abgeschaltet (kein verify=False, kein eigener SSL-Kontext).
- **Auswirkung:** Gering: Ein Angriff setzt voraus, dass der Börsen-Host selbst eine Weiterleitung ausliefert. Dann gingen API-Schlüssel und eine für fünf Sekunden gültige Signatur an einen fremden Host, das Secret nicht. urllib erlaubt dabei auch den Wechsel von https auf http.
- **Empfehlung:** Eigenen Opener ohne Weiterleitungen verwenden (HTTPRedirectHandler, der abbricht) und im Konstruktor prüfen, dass `basis` mit https:// beginnt. Als Regressionstest den lokalen Versuch aus evidence/SEC/transport_und_kdf.py übernehmen.
- **Nachstellen:** cd /home/user/OdinGate-Botv134/swing-hybrid && .venv/bin/python -I -B reports/audit/evidence/SEC/transport_und_kdf.py . | sed -n 1,6p

#### SEC-12 (P3): Kleinere Punkte: Sitzungsadresse in Commit-Nachrichten, mitveröffentlichte Fremddokumente, Schlüssel auf der Kommandozeile, Entpacker, systemd

- **Sicherheit des Prüfers:** hoch
- **Stand:** nicht gegengeprüft (nicht vorgesehen)
- **Evidenz:** (a) 144 Commit-Nachrichten tragen 'Claude-Session: https://claude.ai/code/session_…' (drei verschiedene Sitzungen; stunde.sh:14-17 und 27-30 schreiben sie fest hinein). (b) docs/ enthält neben dem Board API.md, ARCHITECTURE.md, BLOCKERS.md, COMPLIANCE.md, ROADMAP.md, SETUP.md der Next.js-Anwendung; ohne .nojekyll werden sie mitveröffentlicht (Inhalt geprüft: keine Zugangsdaten). (c) board_verschluesseln.py:21 übergibt den AES-Schlüssel je Stand als Argument `-K <hex>` an openssl; er ist für die Laufzeit in der Prozessliste sichtbar. (d) scripts/intake.py:19-20 überspringt nur die Datei mit exakt dem Namen '.env' (nicht .env.local o. ä.) und begrenzt weder Größe noch Anzahl entpackter Dateien; der Parameter <name> wird nicht geprüft. (e) server/installieren.sh:28-37 erzeugt eine systemd-Einheit ohne Abschottung (kein NoNewPrivileges, ProtectSystem, PrivateTmp), ausgeführt aus einem vom Nutzer beschreibbaren Checkout. (f) docs/index.html:6 `noindex` gilt nur für die HTML-Seite, nicht für die JSON-Dateien.
- **Auswirkung:** Jeweils gering. (a) verrät Sitzungskennungen, die ohne Anmeldung des Besitzers nicht nutzbar sind. (c) betrifft nur Mehrbenutzer-Maschinen. (d) kann bei einem präparierten Archiv die Platte füllen oder eine Zugangsdatei mit anderem Namen entpacken. (e) vergrößert den Schaden, falls der Bot-Code kompromittiert wird.
- **Empfehlung:** (a) Sitzungszeile in automatischen Commits weglassen, sofern keine Vorgabe sie verlangt. (b) Board in einen eigenen Ordner oder ein eigenes Repo legen, das nur Board-Dateien enthält. (c) Schlüssel über eine Datei mit Modus 600 oder über die Standardeingabe übergeben, oder die Verschlüsselung mit der Bibliothek cryptography rechnen. (d) Muster '.env*', Schlüssel- und Zertifikatsendungen überspringen, Obergrenzen für Größe und Anzahl setzen. (e) Abschottungsoptionen ergänzen, Checkout für den Dienstnutzer nur lesbar machen.
- **Nachstellen:** cd /home/user/OdinGate-Botv134 && git log --format=%B | grep -o 'Claude-Session: [^ ]*' | sort | uniq -c ; ls docs ; sed -n 20,21p swing-hybrid/vorwaertstest/board_verschluesseln.py ; sed -n 19,36p swing-hybrid/scripts/intake.py

### Nachgerechnete Aussagen

- **abweichend**: Commit 1695511: 'Passwortabfrage, Stand nur noch verschlüsselt in docs/'; Übergabebericht: 'passwortgeschütztes Live-Board'. docs/stand.json liegt weiter unverschlüsselt im veröffentlichten Ordner (durch Commit 4dc3256 drei Minuten später wieder angelegt). Der verschlüsselte Inhalt liegt zudem in jedem Commit als Klartext unter vorwaertstest/lauf*/dashboard.json: 88 von 88 Paaren längengleich. Befehl: `cd /home/user/OdinGate-Botv134 && git ls-files docs/ && python3 -I swing-hybrid/reports/audit/evidence/SEC/laengenvergleich.py . | tail -1`
- **reproduziert**: README.md:44: Ohne YUBIT_LIVE=ja und modus live und Schlüssel wird nie geordert. 28 Kombinationen aus modus (papier, live), YUBIT_LIVE (nicht gesetzt, nein, JA, 'ja ', 1, true, ja) und Schlüssel (ja, nein) mit nachgestellter Börse: Private Aufrufe und Orders gibt es nur bei modus=live, YUBIT_LIVE exakt 'ja' und gesetztem Schlüssel (5 private Aufrufe, 2 Orders). modus=live ohne die beiden anderen Bedingungen bricht mit SystemExit ab. Befehl: `cd /home/user/OdinGate-Botv134/swing-hybrid && env -u YUBIT_LIVE .venv/bin/python -I -B reports/audit/evidence/SEC/live_schranken.py . | sed -n 1,30p`
- **reproduziert**: README.md:9: Stufe papier setzt keine Orders, braucht kein Konto und keinen Schlüssel. In allen 14 Papier-Kombinationen, auch mit gesetztem Schlüssel und YUBIT_LIVE=ja, 0 private Aufrufe. Alle drei eingecheckten Konfigurationen stehen auf modus papier. In dieser Sitzung sind keine YUBIT_*-Variablen gesetzt. Befehl: `cd /home/user/OdinGate-Botv134/swing-hybrid && env -u YUBIT_LIVE .venv/bin/python -I -B reports/audit/evidence/SEC/live_schranken.py . | grep '^papier'`
- **abweichend**: README.md:45: Jede Order ist gedeckelt (max_order_usd) als Sicherung im Live-Betrieb. Der Deckel greift, aber auch für Schließ-Orders: Short über 1500 USDT nach +40 % nicht mehr schließbar ('2102 > 2000 USDT'), Position bleibt offen (bot.py:130-131). Befehl: `cd /home/user/OdinGate-Botv134/swing-hybrid && env -u YUBIT_LIVE .venv/bin/python -I -B reports/audit/evidence/SEC/live_schranken.py . | tail -6`
- **reproduziert**: Commit 1695511: 'Passwort liegt nicht im Repo'; keine Schlüssel im Repo. 144 Commits, 922 Blobs aller Zweige nach 13 Mustern durchsucht (private Schlüssel, AWS, GitHub, Anthropic/OpenAI, Slack, Google, JWT, Telegram, YUBIT_API_*, Signaturen, Passwort-Zuweisungen): 0 echte Treffer, 2 Fehlalarme (Base64-Chiffrat, Testpasswort der Next.js-Tests). Im Repo liegt allerdings der passwortverschlüsselte private Schlüssel (docs/schluessel.json), siehe SEC-04. Befehl: `cat /home/user/OdinGate-Botv134/swing-hybrid/reports/audit/evidence/SEC/geheimnis_suche.txt`
- **reproduziert**: Bot-Schlüssel werden nur aus Umgebungsvariablen gelesen und nicht protokolliert. bot.py:394 liest YUBIT_API_KEY und YUBIT_API_SECRET. Live-Lauf mit erfundenen Schlüsseln und nachgestellter Börse: weder in zustand.json, protokoll.csv, stand.csv, spannen.csv, bericht.md noch in Meldungen oder Fehlertexten (HTTP 401) enthalten. Befehl: `cd /home/user/OdinGate-Botv134/swing-hybrid && env -u YUBIT_LIVE .venv/bin/python -I -B reports/audit/evidence/SEC/schluessel_leck.py .`
- **reproduziert**: yubit.py / README: Bot braucht nur die Standardbibliothek. Alle Importe in vorwaertstest/*.py stammen aus der Standardbibliothek; board_verschluesseln.py ruft zusätzlich das Programm openssl auf. Befehl: `cd /home/user/OdinGate-Botv134/swing-hybrid && grep -h -E '^(import|from) ' vorwaertstest/*.py | sort -u`
- **ungeklaert**: Signatur wie im offiziellen Yubit-Paket (HMAC-SHA256 über Zeitstempel + Schlüssel + Fenster + Nutzlast). Der Test test_signatur_wie_im_offiziellen_paket ist grün (11 von 11 Tests der Datei) und belegt, dass der Code die im Test beschriebene Formel rechnet. Ob diese Formel der echten Schnittstelle entspricht, ist ohne das offizielle Paket und ohne Konto nicht prüfbar; laut README.md:50-51 lief der Live-Teil noch nie gegen ein echtes Konto. Befehl: `cd /home/user/OdinGate-Botv134/swing-hybrid && .venv/bin/python -B -m pytest -q -p no:cacheprovider tests/test_vorwaertstest_bot.py`
- **ungeklaert**: Betreiber: Repo ist öffentlich, GitHub Pages veröffentlicht /docs dieses Zweigs, die Workflow-Datei liegt nicht im Standard-Zweig. Nicht über das Netz geprüft. Belege nur aus dem Repo: uebergabe_fuer_dritte.md:76 nennt das Repo öffentlich; der zweite bekannte Zweig origin/feature/content-engine-mvp enthält weder .github noch swing-hybrid; der Standard-Zweig ist lokal nicht bestimmbar (origin/HEAD fehlt); kein docs/CNAME.

### Als richtig befunden

- Keine API-Schlüssel, Tokens, Passwörter oder privaten Schlüssel in der git-Historie: 144 Commits, 922 Blobs, 13 Muster, 0 echte Treffer (swing-hybrid/reports/audit/evidence/SEC/geheimnis_suche.txt). Jemals eingecheckte einschlägige Dateinamen: nur .env.example (leer), docs/schluessel.json, board_pub.pem (öffentlicher Schlüssel), board_verschluesseln.py.
- Kein unverschlüsselter privater Schlüssel des Boards im Arbeitsverzeichnis sowie unter /tmp, /home, /root gefunden; git-Remote ohne eingebettete Zugangsdaten.
- .gitignore (Wurzel, Zeilen 25 und 34) schließt *.pem und .env* aus; swing-hybrid/.gitignore schließt data/raw, data/download, data/candles, data/processed und vorwaertstest/daten aus (mit git check-ignore geprüft).
- Drei unabhängige Schranken vor echten Orders (bot.py:107-108, 156-158): modus=live, YUBIT_LIVE exakt 'ja', Schlüssel und Secret gesetzt. In 28 Kombinationen geprüft; kein Pfad zu versehentlichem Live-Handel gefunden. Private Endpunkte werden nur in yubit.py angesprochen; live_server.py und die Skripte unter scripts/ nutzen nur öffentliche Kursdaten.
- Abweichung zwischen Börse und Protokoll führt zum Abbruch ohne Order (bot.py:177-182); die Datei STOPP hält den Lauf an (bot.py:151-153, Test in tests/test_vorwaertstest_bot.py:104-112).
- API-Schlüssel kommen ausschließlich aus Umgebungsvariablen (bot.py:394) und erscheinen weder in Laufdateien noch in Meldungen oder Fehlertexten (evidence/SEC/schluessel_leck.txt). yubit.py:80-85 gibt nur Pfad und Antworttext aus.
- Transport: BASIS ist https (yubit.py:18), urllib prüft Zertifikat und Hostnamen standardmäßig, nirgends abgeschaltet (grep nach verify=, CERT_NONE, _create_unverified: 0 Treffer in src, scripts, vorwaertstest); Zeitlimit 20 s (yubit.py:78); HMAC-SHA256 mit Zeitstempel und Empfangsfenster 5 s (yubit.py:47-51); Order-Kennung mit secrets.token_hex (yubit.py:132).
- Board: keine Stelle, an der Daten als HTML eingefügt werden (kein innerHTML, eval, document.write in docs/index.html); Anzeige nur über textContent und createElement (index.html:171, 181-189). Die einzige innerHTML-Stelle (vorwaertstest/live_seite.html:125) setzt nur selbst berechnete Zahlen ein.
- Board-Kryptografie in den Grundbausteinen stimmig: RSA-2048 mit OAEP/SHA-256 auf beiden Seiten gleich (board_verschluesseln.py:26-27, index.html:156 und 159), AES-256 mit Zufallsschlüssel und Zufalls-IV je Stand (board_verschluesseln.py:25), PBKDF2 mit 600.000 Runden und 16 Byte Zufallssalz, privater Schlüssel im Browser nicht exportierbar importiert (index.html:156).
- Falsches Passwort: Entschlüsselung bzw. Import schlägt fehl, Meldung 'Falsches Passwort.', nichts wird gespeichert oder angezeigt (index.html:492-506); ein ungültiger gespeicherter Schlüssel wird verworfen (index.html:511).
- installieren.sh: Schlüsseldatei /etc/vorwaertstest.env mit Modus 600, YUBIT_LIVE=nein voreingestellt, Hinweis auf Schlüssel ohne Auszahlungsrecht (Zeilen 12-22); README.md:36-39 verlangt Schlüssel ohne Auszahlung und 'nie in den Chat, nie ins Repo'.
- Workflow .github/workflows/vorwaertstest.yml: nur schedule und workflow_dispatch, keine Secrets, kein pull_request_target, concurrency-Gruppe, Papier-Lauf ohne Schlüssel; Schreibrecht nur für contents.
- scripts/intake.py:29-36 weist absolute Pfade und '..' ab und überspringt Symlinks; fremde Uploads werden nur als JSON, CSV und Parquet gelesen (src/hybrid/swing.py:25-41), kein Import fremden Codes; YAML mit safe_load (src/hybrid/config.py:11); pyarrow 26.0.1 liegt weit über den Versionen mit der bekannten Parquet-Deserialisierungslücke.
- Rohdaten des Signal-Dienstes (data/raw/plimaflow, rund 96 MB) sind nicht in git.
- Die 8 direkten Abhängigkeiten in requirements.txt sind exakt festgeschrieben und stimmen mit der installierten Umgebung überein; der Papier-Bot selbst kommt ohne Fremdpakete aus.

### Ungeklärt

- Länge und Qualität des Board-Passworts sind unbekannt (und wurden bewusst nicht geprüft). Die Widerstandskraft gegen einen Offline-Angriff lässt sich daher nur als Tabelle je Passwortklasse angeben (SEC-04). Die Rate je Grafikkarte ist eine Annahme aus veröffentlichten Benchmarks, hier nicht gemessen.
- Wie Schlüsselpaar und docs/schluessel.json erzeugt wurden, ist nicht nachvollziehbar (kein Skript im Repo). Ob Passwort oder privater Schlüssel in einem Chat-Verlauf, einer Shell-Historie oder einer anderen Sitzung im Klartext vorlagen oder vorliegen, ist nicht prüfbar.
- Ob das Repo tatsächlich öffentlich ist, ob GitHub Pages /docs dieses Zweigs ausliefert und ob <Pages-Adresse>/stand.json abrufbar ist, wurde nicht über das Netz geprüft (Angabe des Betreibers und uebergabe_fuer_dritte.md:76).
- Standard-Zweig, Branch-Schutz, Liste der Schreibberechtigten sowie Status von Secret Scanning und Dependabot auf GitHub sind aus dem lokalen Repo nicht ersichtlich.
- Ob Yubit dem Betreiber eine Genehmigung für ein automatisches Programm, den Rebate-Satz von 85 % oder ein Partner-Konto erteilt hat, ist nicht belegt. Die Regeln sind nur in der Wiedergabe von YUBIT_REGELN.md geprüft, nicht an der Originalquelle. Ob der Abruf öffentlicher Kurse aus Rechenzentrums-Adressen unter die Klausel fällt, ist offen.
- Ob Endpunkte und Signatur von yubit.py der echten Schnittstelle entsprechen: nicht prüfbar ohne Konto und ohne das offizielle Paket; der Live-Teil lief laut README noch nie gegen ein echtes Konto.
- Nutzungsbedingungen des Signal-Dienstes und die Art des Zugangs zur Lese-Schnittstelle (Zugangsdaten, Tarif) liegen nicht vor; ein Abrufskript fehlt im Repo.
- Bekannte Schwachstellen in den 89 installierten Paketen wurden nicht geprüft (kein pip-audit ohne Netz; die Versionen sind jünger als mein Wissensstand).
- Ob unter demselben github.io-Konto weitere Projektseiten liegen, die sich den localStorage mit dem Board teilen.
- Ob live_server.py in der Betriebsumgebung von außen erreichbar war: Auf dieser Maschine zeigt /tmp/vorwaertstest_live.log einen Start am 15.11. um 13:14 UTC; die Netzlage der Umgebung ist unbekannt.
- Die Laufumgebung der separaten KI-Sitzung (welche Rechte, Verbindungen und Zugangsdaten dort neben dem Push-Recht vorhanden sind) war nicht einsehbar.

### Evidenzdateien

- `/home/user/OdinGate-Botv134/swing-hybrid/reports/audit/evidence/SEC/chiffrat_vs_klartext_laengen.txt`
- `/home/user/OdinGate-Botv134/swing-hybrid/reports/audit/evidence/SEC/laengenvergleich.py`
- `/home/user/OdinGate-Botv134/swing-hybrid/reports/audit/evidence/SEC/fassungen_in_historie.txt`
- `/home/user/OdinGate-Botv134/swing-hybrid/reports/audit/evidence/SEC/geheimnis_suche.txt`
- `/home/user/OdinGate-Botv134/swing-hybrid/reports/audit/evidence/SEC/live_schranken.py`
- `/home/user/OdinGate-Botv134/swing-hybrid/reports/audit/evidence/SEC/live_schranken_boerse.py`
- `/home/user/OdinGate-Botv134/swing-hybrid/reports/audit/evidence/SEC/live_schranken.txt`
- `/home/user/OdinGate-Botv134/swing-hybrid/reports/audit/evidence/SEC/schluessel_leck.py`
- `/home/user/OdinGate-Botv134/swing-hybrid/reports/audit/evidence/SEC/schluessel_leck.txt`
- `/home/user/OdinGate-Botv134/swing-hybrid/reports/audit/evidence/SEC/kdf_nachbau.py`
- `/home/user/OdinGate-Botv134/swing-hybrid/reports/audit/evidence/SEC/kdf_nachbau.txt`
- `/home/user/OdinGate-Botv134/swing-hybrid/reports/audit/evidence/SEC/transport_und_kdf.py`
- `/home/user/OdinGate-Botv134/swing-hybrid/reports/audit/evidence/SEC/transport_und_kdf.txt`
- `/home/user/OdinGate-Botv134/swing-hybrid/reports/audit/evidence/SEC/venv_pakete.txt`
- `/home/user/OdinGate-Botv134/swing-hybrid/reports/audit/evidence/SEC/venv_abhaengigkeiten.txt`

## Bereich ARC: Architektur

Die Plattform besteht aus zwei getrennten Teilen ohne gemeinsamen Code: der Forschung (src/hybrid, zwei Rechenkerne plus sechs eigene Simulatoren) und dem Papier-Bot (vorwaertstest, nur Standardbibliothek). Die Modul- und Datenflusskarte liegt als Mermaid-Text in reports/audit/evidence/ARC/datenfluss.mmd, der Importgraph in importgraph.txt. Wichtigstes Ergebnis: Geprüft wurde der Kandidat mit Hebel 0,2 und Tageslimit 3 %, berichtet wird Hebel 1 ohne Limit (+59 % pro Jahr, Sharpe 0,95, von mir nachgerechnet), betrieben wird Hebel 3 mit abgeschaltetem Limit. Mit dem dokumentierten Limit von 3 % ergibt Hebel 3 im Entwicklungszeitraum −101 % pro Jahr. Die Signalregel selbst stimmt zwischen Forschung und Bot überein (463.680 von 464.400 Coin-Stunden, der Rest sind Datenlücken), aber kein Test sichert das ab. Der Live-Pfad im Bot wird von keinem der 105 grünen Tests ausgeführt, und sein Sicherheitsdeckel blockiert auch schließende Orders. Ein Margin- und Liquidationsmodell fehlt in Bot und Rechenkern. Code, Zustand und Board liegen im selben öffentlichen Arbeitszweig, in dem der Klartext-Stand neben dem verschlüsselten Board-Stand steht.

### Befunde

#### ARC-01 (P0): Drei verschiedene Strategie- und Risikostände: geprüft Hebel 0,2 mit Tageslimit 3 %, berichtet Hebel 1 ohne Limit, betrieben Hebel 3 ohne Limit

- **Sicherheit des Prüfers:** hoch
- **Stand:** Sachverhalt über QR-01, QD-04 bestätigt
- **Evidenz:** Geprüfter Kandidat: reports/kandidat.json ('hebel': 0.2; Entwicklung jahr_N 0,096; Prüfzeitraum jahr_N 0,0156, Sharpe 0,159) und reports/suche_protokoll.md:125,135 (Stufe 5 mit Tagesverlust-Limit 3 %, 'besteht alle fünf Stufen, bei Hebel 0,2'). Berichtete Kennzahl: scripts/suche_runde24.py:19 (R.lauf mit Hebel-Standard 1.0 und day_limit=9.0), reports/suche_runde24.json kandidat.Entwicklung (jahr 0,594, sharpe 0,946). Betrieb: vorwaertstest/config_lauf.json:4,17 und config_lauf_tpsl.json:4,17 ('hebel': 3.0, 'tagesverlust_limit': 1.0; Schwelle nach bot.py:196 = −5.000 $ = 100 % des Kapitals), eingeführt mit Commit 4276791. 'Hebel 3' kommt in suche_protokoll.md und suche_bericht.md nicht vor (grep -n -i 'hebel 3'). Dokumentierte Regel: config.yaml:15 (tagesverlust_limit 0.03), vorwaertstest/README.md:3,47 (Hebel 0,2; Tagesverlust-Limit 3 %). Stiller Standard: research.py:148-158 (day_limit=None nimmt den Wert aus config.yaml). Nachrechnung Entwicklungszeitraum, Gruppe A, Yubit-Kosten mit Rebate (reports/audit/evidence/ARC/experimente_forschung.txt): Hebel 1 ohne Limit +59,4 %/Jahr, Sharpe 0,946, 0 Sperrtage; Hebel 1 mit Standardaufruf +13,2 %/Jahr, Sharpe 0,248, 375 Sperrtage; Hebel 3 ohne Limit Sharpe 0,946; Hebel 3 mit Limit 3 % −101 %/Jahr, Sharpe −0,91, 1.178 Sperrtage.
- **Auswirkung:** Entscheidungen über Hebel und Echtgeldbetrieb stützen sich auf Kennzahlen, die zu keiner betriebenen Konfiguration gehören. Die als fest dokumentierte Risikoregel ist im Betrieb abgeschaltet und lässt sich beim betriebenen Hebel nicht einschalten, ohne das Ergebnis umzukehren. Ein vergessenes day_limit-Argument verändert Forschungsergebnisse um Größenordnungen, ohne dass der Aufruf auffällt.
- **Empfehlung:** Einen einzigen versionierten Parametersatz festlegen (Coins, Rückblick, Hebel, Risikoregeln, Kosten), den Forschung und Bot lesen. Hebel 3 erst weiter betreiben oder bewerten, nachdem er mit genau den betriebenen Risikoregeln in einer vorab festgelegten Runde gerechnet wurde. day_limit in research.lauf zum Pflichtargument machen. README und config.yaml auf den tatsächlichen Stand bringen. Keine Parameterwahl am Prüfzeitraum.
- **Nachstellen:** cd /home/user/OdinGate-Botv134/swing-hybrid && .venv/bin/python -I -B reports/audit/evidence/ARC/experimente_forschung.py

#### ARC-02 (P0): Live-Handelspfad im Papier-Bot ist ungetestet, weicht vom Papier-Ausführungsmodell ab, und der Sicherheitsdeckel blockiert auch schließende Orders

- **Sicherheit des Prüfers:** hoch
- **Stand:** Teil „Deckel“ über ENG-01 bestätigt, Rest nicht gegengeprüft
- **Evidenz:** Abdeckung der 105 Tests (reports/audit/evidence/ARC/abdeckung_zeilen.txt): bot.py:113-145 (live_positionen, live_order), 178-181, 244-245 sowie yubit.py storno, fills und die Rückgabe von positionen werden nie ausgeführt. vorwaertstest/README.md:50 sagt dagegen 'mit nachgestellter Börse getestet'. Deckel: bot.py:130-131 prüft max_order_usd ohne Rücksicht auf reduce_only; experimente_bot.txt E3: Schließen einer Short-Position von 1.500 $ nach +40 % Kurs ergibt 'Order über dem Sicherheitsdeckel (2102 > 2000 USDT)', danach bot.py:254-256 nur Hinweis und Abbruch für den Coin. Fill-Abfrage: bot.py:135-145 fragt genau einmal nach 1,5 s; experiment_live_attrappe.txt: meldet die Börse den Fill später, liefert live_order Menge 0, der Zustand bleibt unverändert und der nächste Lauf bricht bei bot.py:177-182 ab. Papier-Modell: bot.py:246-253 füllt ohne preisgrenze und ohne Deckel durch bis zu 25 Buchstufen; live ist es ein Limit mit 0,05 % Preisgrenze, Rest gestrichen. Rebate live = 0 (bot.py:245), Funding als Näherung (bot.py:184-189). Umschaltung: 'modus': 'live' plus YUBIT_LIVE=ja plus Schlüssel (bot.py:107-108); server/installieren.sh:12-22 legt die Datei dafür an.
- **Auswirkung:** Beim Umschalten auf live liefe Code mit echtem Geld, der nie ausgeführt wurde. Positionen lassen sich ab rund +33 % Kurswert gegenüber dem Einstieg nicht mehr schließen, bei Shorts also genau im Verlust. Nach einem verspätet gemeldeten Fill steht eine Position ohne Verwaltung an der Börse. Die Papier-Ergebnisse sagen nichts über das Live-Ausführungsverhalten aus.
- **Empfehlung:** Live-Pfad bis zu vollständigen Tests mit nachgestellter Börse (Teilfüllung, verspäteter Fill, Storno-Fehler, Positionsabgleich) aus dem Betriebsmodul herausnehmen oder hart sperren. Deckel nur auf eröffnende Orders anwenden. Papier-Füllung mit derselben Preisgrenze rechnen wie live. Fill-Abfrage mit Wiederholung und Abgleich über offene Orders. Aussage in der README berichtigen.
- **Nachstellen:** cd /home/user/OdinGate-Botv134/swing-hybrid && .venv/bin/python -I -B reports/audit/evidence/ARC/experimente_bot.py && .venv/bin/python -I -B reports/audit/evidence/ARC/experiment_live_attrappe.py && .venv/bin/python -I -B reports/audit/evidence/ARC/abdeckung_zeilen.py

#### ARC-03 (P0): Kein Margin- und Liquidationsmodell in Papier-Konto und Rechenkern; weitere Bausteine für einen Echtgeldbetrieb fehlen

- **Sicherheit des Prüfers:** hoch
- **Stand:** Sachverhalt über ENG-02 bestätigt
- **Evidenz:** kern.py:68-88 und bot.py:160-199: Das Papier-Konto kennt keine Margin und keine Liquidation; einzige Schwelle ist tagesverlust_limit (bot.py:196). experimente_bot.txt E4 (nachgestellte Börse, Hebel 3, Konfiguration wie config_lauf.json): nach −30 % Kurs netto −4.512 $ von 5.000 $, Positionen offen, keine Sperre; nach −50 % Konto rechnerisch −2.518 $, erst dann Sperre. engine2.py:161-170: Konto in Kapital-Einheiten bei fester Positionsgröße, kein Abbruch bei Konto ≤ 0 (experimente_forschung.txt: ein Lauf mit Einbruch 359 % des Höchststands wird zu Ende gerechnet). dashboard_daten.py:66-67: 'margin_usd' = Einsatz / Hebel, reine Anzeige. Warnungen nur auf der Konsole (bot.py:282-285), stunde.sh schreibt kein Laufprotokoll.
- **Auswirkung:** Papier- und Backtest-Ergebnisse bei Hebel 3 enthalten keine Zwangsliquidation. Ein Verlauf, bei dem ein echtes Konto liquidiert würde, läuft im Papier-Konto weiter und kann sich erholen. Die Überlebensfähigkeit der betriebenen Konfiguration wird dadurch überschätzt.
- **Empfehlung:** Vor Echtgeld fehlen (nur benannt, nichts gebaut): 1. Margin- und Liquidationsrechnung nach den Kontraktregeln der Börse in Papier-Konto und Rechenkern. 2. Von der Strategie unabhängige Risikogrenzen (Gesamtexposure, Verlustgrenze, Notaus). 3. Abgleich von Fills, Gebühren, Funding und Rebate mit der Börsenabrechnung. 4. Order-Idempotenz und definierter Wiederanlauf nach Abbruch. 5. Überwachung und Alarmierung mit dauerhaftem Laufprotokoll. 6. Schlüsselverwaltung und getrennte Umgebungen für Forschung, Papier und Live. 7. Freigabeprozess mit Versionsstand je Lauf. 8. Eigener, verlässlicher Taktgeber.
- **Nachstellen:** cd /home/user/OdinGate-Botv134/swing-hybrid && .venv/bin/python -I -B reports/audit/evidence/ARC/experimente_bot.py   (Abschnitt E4)

#### ARC-04 (P1): Handelsregel, Kontobewertung und Kennzahlen sind mehrfach getrennt implementiert, ohne gemeinsamen Code und ohne Paritätstest

- **Sicherheit des Prüfers:** hoch
- **Stand:** nicht gegengeprüft
- **Evidenz:** Signalregel 336 Stunden an sechs Stellen: research.py:89-93 (tsmom), research.py:190-192 (_trend), mutationen.py:23-24 (basis), labor_strategie/trend_14d/strategie.py:22, vorwaertstest/kern.py:11-19 mit bot.py:84-102, docs/index.html:438-440 (JavaScript, auf Binance-Kerzen statt Yubit). Importgraph (reports/audit/evidence/ARC/importgraph.txt): vorwaertstest importiert nichts aus src/hybrid. Kontobewertung viermal: kern.py:83-88, dashboard_daten.py:29-39, live_server.py:25-56, docs/index.html:192-198 (mit Binance-Kursen). Eigene Gewinn- und Kostenrechnung in engine.py:41, engine2.py:25, statarb.py:12, listings.py:12, massentest.py:69,86, pumpshort.py:11,73, tagestrend.py:19, tradfi_neutral.py:11,81. Sharpe-Formel neunmal (grep 'sqrt(365)'), Einbruch siebenmal in zwei Definitionen: runner.py:79-83 (5-Minuten-Werte, Höchststand mindestens 1,0) gegen suche_runde24.py:49,62 (Tageswerte ohne Boden); derselbe Lauf ergibt 24,6 % (suche_runde24.json) und 25,8 % (experimente_forschung.txt). Sichtbare Drift zwischen Kern 1 und Kern 2: runner.py:132-138 beschriftet Zähler 5 als 'verstoesse_beide_seiten', in engine2.py:40 ist das die Zahl der Stops (experimente_forschung.txt E6: ein Stop erscheint als 1 Verstoß); runner.py:113-114 liefert bei engine2-Läufen immer trades_kern = trades_taktik = 0; das Tageslimit schließt in Kern 1 nur die Taktik (engine.py Kopf), in Kern 2 alles (engine2.py:62-77), bei demselben Konfigurationsschlüssel.
- **Auswirkung:** Jede Änderung an einer Stelle (Rückblick, Gleichstandsregel, Kosten, Limit) lässt Forschung, Bot und Board unbemerkt auseinanderlaufen. Das Board kann ein anderes Signal und einen anderen Kontowert zeigen, als der Bot handelt und bucht, weil es eine andere Börse als Kursquelle nutzt. Zahlen aus verschiedenen Runden sind nur eingeschränkt vergleichbar.
- **Empfehlung:** Regel, Buchung und Kennzahlen in eine gemeinsame, abhängigkeitsarme Bibliothek legen, die Forschung und Bot nutzen. Mindestens einen Paritätstest als Pflichttest einführen (Bot mit nachgestellter Börse gegen engine2 auf denselben Kerzen). Das Board soll nur Signale und Werte anzeigen, die der Bot liefert. Eine einzige Kennzahlenfunktion für alle Runden.
- **Nachstellen:** cd /home/user/OdinGate-Botv134/swing-hybrid && .venv/bin/python -I -B reports/audit/evidence/ARC/signal_paritaet.py && .venv/bin/python -I -B reports/audit/evidence/ARC/experimente_forschung.py

#### ARC-05 (P1): Verhalten von Test 2 (Stop 5 % / Ziel 15 %) hängt vom Aufruftakt ab, der nicht Teil der Konfiguration ist; die Forschung hat eine andere Regel gerechnet

- **Sicherheit des Prüfers:** hoch
- **Stand:** nicht gegengeprüft; von fünf Prüfern gefunden
- **Evidenz:** bot.py:216-228 prüft Stop und Ziel bei jedem Aufruf am Mittelkurs. Runde 24 rechnet dieselbe Variante nur auf Stundenschlüssen (tpsl.py:14-40). Takt laut Code und Dokumentation stündlich: bot.py:3, vorwaertstest/README.md:10, dashboard_daten.py:12 (TAKT_MINUTEN = 60), .github/workflows/vorwaertstest.yml:8. Tatsächlich laut vorwaertstest/lauf/stand.csv 64 Läufe von 13:21 bis 18:58 UTC, Abstände 1 bis 13 Minuten, am häufigsten 5. Nachstellung (experimente_bot.txt E1): Kurs fällt innerhalb der Stunde auf −6 % und schließt bei −3 %; der Bot im 5-Minuten-Takt stoppt und sperrt die Richtung, tpsl._zustand und ein stündlicher Aufruf stoppen nicht. Zusätzlich: reports/suche_runde24.json ('finalisten': [], sl5_tp15 ok1 false, ok2 false) und suche_protokoll.md ab Zeile 1268 ('kein belegter Vorteil. Dashboard und Papier-Test bleiben unverändert'); Test 2 wurde fünf Minuten später mit Commit b8795b3 gestartet.
- **Auswirkung:** Das Ergebnis von Test 2 lässt sich weder mit Runde 24 vergleichen noch von einem Betrieb mit anderem Takt reproduzieren. Ein Wechsel des Taktgebers (etwa auf den stündlichen Workflow) ändert die gehandelte Regel, ohne dass eine Konfigurationsdatei sich ändert.
- **Empfehlung:** Prüfzeitpunkt für Stop und Ziel ausdrücklich festlegen (Stundenschluss oder fester Takt) und im Bot erzwingen, unabhängig vom Aufrufabstand. Den Takt in Konfiguration und Zustand festhalten. Vor der Auswertung von Test 2 schriftlich festlegen, mit welcher Rückrechnung er verglichen wird.
- **Nachstellen:** cd /home/user/OdinGate-Botv134/swing-hybrid && .venv/bin/python -I -B reports/audit/evidence/ARC/experimente_bot.py   (Abschnitt E1)

#### ARC-06 (P1): Kritische Rechenwege der Kennzahlenkette und des Bots haben keinen Test

- **Sicherheit des Prüfers:** hoch
- **Stand:** nicht gegengeprüft
- **Evidenz:** Testlauf: 105 passed. Zeilenabdeckung mit stdlib trace (reports/audit/evidence/ARC/abdeckung.txt, abdeckung_zeilen.txt). Signal: mutationen.basis geprüft (tests/test_mutationen.py:25-31), aber research.tsmom, research.auf_raster (Zeitversatz), research.markt (Raster, Lücken, Funding-Zuordnung), research.lauf, research.sicht, research.yubit_kosten werden nie ausgeführt (research.py 49 von 208 Zeilen); im Bot liefert die nachgestellte Börse für jede Startzeit denselben Altkurs (tests/test_vorwaertstest_bot.py:31-32), der 336-Stunden-Bezug wird also nicht geprüft. Gebühren und Rebate im Ergebnis: runner.py 0 von 112 Zeilen (equity, daily_pnl, kennzahlen, max_drawdown). Funding: alle engine2-Tests laufen mit Funding 0 (tests/test_engine2.py:18,91-93); bot.py:188 wird nie ausgeführt. Tageslimit in engine2: alle Tests mit day = 0 und day_limit = 9.0. Füllung: Teilfüllung und 'nichts gefüllt' im Bot (bot.py:254-259, 269-270) nie ausgeführt. Konfiguration: bot.konfig (bot.py:41-47) nie ausgeführt. Verschlüsselung: board_verschluesseln.py 0 von 26 Zeilen, kein Rundlauf gegen den Entschlüsselungsweg in docs/index.html. live_server.py 0 von 91 Zeilen, walkforward.py 0 von 80. Zustandsführung: kein Test für Abbruch, Neustart oder doppelte Ausführung. Eigene Stichproben auf diesen Wegen (luecken_pruefung.txt): 13 von 13 ohne Abweichung.
- **Auswirkung:** Die Kette, aus der die berichteten Kennzahlen stammen (Marktdaten, Signal, Zeitversatz, Kern 2, Gebühren und Rebate, Sharpe), ist nur im Füllpreis abgesichert. Ein Fehler beim Zeitversatz, beim Funding-Vorzeichen oder bei der Rebate-Rechnung fiele in den Tests nicht auf. Heute rechnen die Wege richtig, das ist aber nicht festgeschrieben.
- **Empfehlung:** Regressionstests in dieser Reihenfolge ergänzen: Zeitversatz research.auf_raster mit tsmom; Funding und Tageslimit in engine2; runner.Lauf mit Gebühr und Rebate; Parität Bot gegen Forschung; Funding-Buchung im Bot; Verschlüsselungs-Rundlauf; bot.konfig. Die Skripte unter reports/audit/evidence/ARC/ (luecken_pruefung.py, signal_paritaet.py) können als Vorlage dienen.
- **Nachstellen:** cd /home/user/OdinGate-Botv134/swing-hybrid && .venv/bin/python -I -B -m pytest -q -p no:cacheprovider tests && .venv/bin/python -I -B reports/audit/evidence/ARC/abdeckung.py /tmp/abdeckung.json && .venv/bin/python -I -B reports/audit/evidence/ARC/luecken_pruefung.py

#### ARC-07 (P1): Zustandsführung des Bots ist nicht transaktional und hat zwei Wahrheiten (CSV-Protokolle und zustand.json)

- **Sicherheit des Prüfers:** hoch
- **Stand:** nicht gegengeprüft
- **Evidenz:** bot.py:276-281: erst drei CSV-Anhänge (protokoll, spannen, stand), danach zustand.json. Nachstellung (experimente_bot.txt E2): Abbruch dazwischen, der nächste Lauf wiederholt die Orders: zustand.orders = 2, protokoll.csv 4 Zeilen, Gebührensumme im Protokoll 24,00 gegen 12,00 im Zustand, das Dashboard meldet 4 Orders und 30.000 $ Volumen statt 15.000 $. dashboard_daten.py:49-50,61 zählt Orders, Volumen und Slippage aus protokoll.csv, die Positionen aus zustand.json (Zeile 30). kern.py:69: die Felder version, kapital und letzte_kerze werden geschrieben, aber nirgends gelesen (grep in vorwaertstest/*.py). Kein Dateischloss gegen parallele Läufe. Übersprungene Coins und andere Warnungen werden nur ausgegeben (bot.py:172-173, 284-285), stand.csv enthält sie nicht. Kein Code-Stand im Zustand: bot.py und kern.py wurden um 17:45 UTC geändert (Commit b8795b3), während Test 1 seit 13:21 UTC lief.
- **Auswirkung:** Nach einem Abbruch zeigen Protokoll, Bericht und Board andere Orderzahlen, Volumina und Gebühren als das Konto. Ausgelassene Coins bleiben in den gespeicherten Daten unsichtbar. Ergebnisse eines Tests lassen sich keinem Code-Stand zuordnen. Im Live-Betrieb käme die Abweichung zur Börse hinzu.
- **Empfehlung:** Zustand und Protokoll in einem Schritt schreiben (ein Journal mit Laufnummer oder der Zustand zuerst und die Protokolle daraus ableitbar). Laufnummer, Kerzenzeit und Commit-Stand je Lauf festhalten. Warnungen dauerhaft mitschreiben. Dateischloss gegen parallele Läufe. Das Feld version beim Laden prüfen.
- **Nachstellen:** cd /home/user/OdinGate-Botv134/swing-hybrid && .venv/bin/python -I -B reports/audit/evidence/ARC/experimente_bot.py   (Abschnitt E2)

#### ARC-08 (P1): Code, Betriebszustand und Board liegen im selben Arbeitszweig; der Taktgeber liegt außerhalb des Repos; drei widersprüchliche Betriebswege sind definiert

- **Sicherheit des Prüfers:** mittel
- **Stand:** nicht gegengeprüft
- **Evidenz:** vorwaertstest/stunde.sh:4-8 (fester Zweigname, fetch, checkout und pull vor jedem Lauf, Fehler mit '|| true' verschluckt), :13-18 und :26-31 (Zustand und Board werden in denselben Zweig committet und gepusht), :3 mit :10-23 (set -e: scheitert Test 1 oder der erste Push, läuft Test 2 nicht). git log: 76 von 144 Commits sind Bot-Läufe aus 5,6 Stunden, zuletzt 25 je Stunde, hochgerechnet rund 210.000 pro Jahr. Je Zyklus rund 108 KB neu geschriebene Dateien (git diff-tree 3985cf0 und be1f4dd). spannen.csv wächst je Test um rund 2.900 Zeilen pro Tag und wird bei jedem Lauf vollständig eingelesen (dashboard_daten.py:16). git reflog zeigt Entwickler- und Audit-Commits, die per 'pull --rebase' zwischen die Bot-Commits geschoben werden. Taktgeber nicht im Repo (reports/uebergabe_fuer_dritte.md:57: 'Claude-Sitzung alle fünf Minuten'). Weitere, abweichende Betriebswege: .github/workflows/vorwaertstest.yml:2,8,36 (stündlich, Standard-config.json mit Hebel 0,2, eigener Zweig vorwaertstest-daten) und vorwaertstest/server/installieren.sh:36,43 (systemd stündlich, config.json, Ordner daten/).
- **Auswirkung:** Jeder Push auf den Zweig ändert binnen Minuten den laufenden Bot, ohne Freigabe und ohne Versionsvermerk. Die Code-Historie wird von Betriebs-Commits überdeckt. Der Betrieb hängt an einer KI-Sitzung ohne Verfügbarkeitszusage. Aus dem Code abgeleitet, nicht ausgeführt: Ein fremder Push zwischen pull und push lässt den Bot-Push scheitern, und wegen 'pull --ff-only || true' bleibt er danach dauerhaft hängen, während der Bot lokal weiterrechnet.
- **Empfehlung:** Betriebsdaten in einen eigenen Zweig oder Speicher auslagern. Den Bot von einem freigegebenen, festen Code-Stand starten statt vom Kopf des Arbeitszweigs. Einen einzigen Betriebsweg behalten und die beiden anderen entfernen oder angleichen. Die Tests voneinander entkoppeln. Verlauf verdichten statt jeden Lauf einzeln zu committen.
- **Nachstellen:** cd /home/user/OdinGate-Botv134 && git log --format=%s | grep -c '^Vorwärtstest (Papier' && git log --format='%ad' --date=format:'%Y-%m-%d %H' | sort | uniq -c | tail -5 && git reflog -8 --date=iso && cat -n swing-hybrid/vorwaertstest/stunde.sh

#### ARC-09 (P1): Der Klartext-Stand liegt im selben öffentlichen Zweig wie der verschlüsselte Board-Stand

- **Sicherheit des Prüfers:** hoch
- **Stand:** direkt nachgeprüft (Klartext-Stand liegt im Repo)
- **Evidenz:** vorwaertstest/stunde.sh:12-13 und :25-26: dashboard.json (Klartext) wird verschlüsselt nach docs/stand.enc.json geschrieben und zusammen mit dem Klartext-Ordner committet. git ls-files zeigt als versioniert: swing-hybrid/vorwaertstest/lauf/zustand.json, protokoll.csv, stand.csv, dashboard.json, dasselbe unter lauf_tpsl/ und lauf_hebel1_archiv/. Größenvergleich: dashboard.json 12.890 Bytes, stand.enc.json 17.593 Bytes (Base64 desselben Inhalts). Zusätzlich docs/stand.json: Klartext-Stand von 13:44 UTC (Commit 4dc3256), nach der Umstellung auf Verschlüsselung (Commit 1695511) nochmals geschrieben und weiter im veröffentlichten Ordner docs/. Dass das Repo öffentlich ist, steht in reports/uebergabe_fuer_dritte.md:76 und ist lokal nicht prüfbar.
- **Auswirkung:** Die Passwortabfrage des Boards schützt keine Information: Positionen, Orders, Einstiegskurse und Kontostand sind im selben Zweig im Klartext lesbar. Für Papierdaten ist der Schaden begrenzt; bei echtem Geld wären Positionen und Orders öffentlich. Die Bewertung der Kryptografie selbst gehört in den Bereich Security.
- **Empfehlung:** Entscheiden, ob der Stand vertraulich sein soll. Wenn ja: Zustand und Klartext-Dashboard nicht in einem öffentlichen Zweig ablegen, docs/stand.json entfernen und die Historie berücksichtigen. Wenn nein: Verschlüsselung und Passwortabfrage entfernen, damit kein falscher Eindruck von Schutz entsteht.
- **Nachstellen:** cd /home/user/OdinGate-Botv134 && git ls-files swing-hybrid/vorwaertstest docs | grep -E 'zustand.json|protokoll.csv|dashboard.json|stand' && git log --oneline -3 -- docs/stand.json

#### ARC-10 (P2): Konfiguration: ungenutzte Schlüssel, fest im Code stehende Werte, kaum Prüfung der Bot-Konfiguration

- **Sicherheit des Prüfers:** hoch
- **Stand:** nicht gegengeprüft (nicht vorgesehen)
- **Evidenz:** config.yaml:1 ('Alle Regeln aus dem Auftrag stehen hier, nicht verstreut im Code'). Ohne Leser im Code (grep je Schlüssel in src, scripts, vorwaertstest, tests): boerse, gebuehren.szenarien, ausfuehrung.einstieg, teilgewinn, stop, fill_regel, min_standzeit_minuten, beidseitige_orders, kapital_szenarien, walk_forward.test_anteil, entscheidung.netto_ohne_rebate_min; risiko.hebel_max wird nur in tests/test_fees.py:20 gelesen. Gebühr und Rebate zusätzlich fest im Code: vorwaertstest/kern.py:9, src/hybrid/listings.py:9, pumpshort.py:47, massentest.py:9-10, scripts/kandidat_pruefen.py:50, fusion_yubit.py:20, suche_runde12.py:71. Zeitgrenzen der Forschung fest in research.py:18-19 statt über walk_forward.lern_anteil. Bot: konfig (bot.py:41-47) prüft nur modus und hebel; tp und sl kommen über cfg.get mit Standard 0 (bot.py:216), falsch geschriebene Schlüssel bleiben unbemerkt; preisgrenze und max_order_usd wirken nur im Live-Pfad (bot.py:127-131) und im Papier-Modus nie; 'daten' wird durch --daten übersteuert (bot.py:393). Drei Bot-Konfigurationen mit unterschiedlichem Stand (experimente_bot.txt E4): config.json Hebel 0,2, Limit 0,03, Deckel 150 $; config_lauf.json und config_lauf_tpsl.json Hebel 3, Limit 1,0, Deckel 2.000 $.
- **Auswirkung:** Die Konfigurationsdatei vermittelt Regeln, die der Code nicht durchsetzt (Mindeststandzeit, Hebelobergrenze in der Forschung, Order-Arten). Eine Änderung der Gebühr an einer Stelle erreicht die anderen nicht. Ein Tippfehler bei tp oder sl schaltet die Variante stillschweigend ab.
- **Empfehlung:** Ungenutzte Schlüssel entfernen oder durchsetzen. Gebühren, Rebate und Rückblick an einer Stelle definieren. Bot-Konfiguration gegen ein festes Schema prüfen (unbekannte Schlüssel ablehnen, Wertebereiche für tagesverlust_limit, tp, sl). Im Papier-Modus dieselben Grenzen anwenden wie live.
- **Nachstellen:** cd /home/user/OdinGate-Botv134/swing-hybrid && for k in szenarien teilgewinn fill_regel min_standzeit_minuten beidseitige_orders kapital_szenarien test_anteil netto_ohne_rebate_min hebel_max; do echo $k $(grep -rn "[\"']$k[\"']" src scripts vorwaertstest/*.py tests | grep -v __pycache__ | wc -l); done

#### ARC-11 (P2): Stille Annahmen bei Datenlücken und Fehlern; Forschung und Bot behandeln Lücken unterschiedlich

- **Sicherheit des Prüfers:** hoch
- **Stand:** nicht gegengeprüft (nicht vorgesehen)
- **Evidenz:** Forschung: research.py:48 (ffill().bfill(): vor dem ersten Kurs gilt der erste Kurs), :51-52 (in Lücken Open, Hoch und Tief = letzter Schluss, eine Taker-Füllung zu veraltetem Kurs ist möglich), :64 (fehlendes Funding = 0), :74 (fehlendes Signal = 0). Gemessene Wirkung (reports/audit/evidence/ARC/signal_paritaet.txt): SOL, XRP und LTC haben ab 26.02.2022 je 120 Stunden ohne Kerzen; die Forschung stellt deshalb je Coin 240 Stunden glatt (während der Lücke und 336 Stunden später), der Bot würde die Position halten (714 Fälle 'keine Kerze', 6 Fälle 'ältere Kerze'). Bot: bot.py:172-173 (Coin bei jedem Fehler übersprungen, nur Konsolenhinweis), bot.py:171 und kern.py:85 (alter Kurs bleibt stehen, fehlender Kurs zählt als 0), bot.py:88 (eine bis zu 2 Stunden alte Kerze gilt), yubit.py:86 ('data or {}' führt zu KeyError 'list' als Hinweistext), live_server.py:69 (except Exception), docs/index.html:401,419,441,466 (catch ohne Meldung), stunde.sh:6,8,17 ('|| true'), scripts/yubit_spannen_sammeln.py:35.
- **Auswirkung:** Lücken und Ausfälle verändern Ergebnisse, ohne in den Ausgaben zu erscheinen. Der Umfang ist im geprüften Zeitraum klein (720 von 464.400 Coin-Stunden), die Behandlung unterscheidet sich aber zwischen Rückrechnung und Betrieb. Im Betrieb kann ein Coin über längere Zeit ausfallen, ohne dass die gespeicherten Daten es zeigen.
- **Empfehlung:** Lücken ausdrücklich kennzeichnen und in Forschung und Bot gleich behandeln (Position halten oder schließen, aber einheitlich). Fehlende Funding-Werte zählen und ausgeben. Jeden übersprungenen Coin und jede abgefangene Ausnahme dauerhaft mitschreiben. Im Board Ladefehler anzeigen.
- **Nachstellen:** cd /home/user/OdinGate-Botv134/swing-hybrid && .venv/bin/python -I -B reports/audit/evidence/ARC/signal_paritaet.py

#### ARC-12 (P2): Repo-Hygiene, Dokumentation und Reproduzierbarkeit entsprechen nicht dem tatsächlichen Stand

- **Sicherheit des Prüfers:** hoch
- **Stand:** nicht gegengeprüft (nicht vorgesehen)
- **Evidenz:** Vermischung: Das Repo ist laut README.md:1-9 eine Next.js-Anwendung ('Content Engine'); die Trading-Plattform liegt als Unterordner in einem Arbeitszweig. docs/ enthält die App-Dokumentation (API.md, ARCHITECTURE.md und weitere) neben dem Board; Dockerfile:11 (COPY . .) mit .dockerignore nimmt swing-hybrid und docs in das App-Image; .gitignore:25 ('*.pem') der App schloss den Board-Schlüssel aus (Commit cf1f1cb). Dokumentation: vorwaertstest/README.md:3,10,18-21,47,55 beschreibt Hebel 0,2, stündlichen Lauf per Workflow, Tageslimit 3 % und nur config.json; stunde.sh, config_lauf*.json, Test 2, Board und Verschlüsselung fehlen. swing-hybrid/README.md:5-6,35-46 endet bei Runde 3 von 24. Verwaist: vorwaertstest/dashboard_seite.html und dashboard_live.html (von keinem Skript genutzt, grep), lauf_hebel1_archiv/, docs/stand.json. Abhängigkeiten: requirements.txt:1 pinnt freqtrade==2026.10, das nirgends importiert wird (grep). Reproduzierbarkeit: data/ (9,7 GB) liegt laut swing-hybrid/.gitignore:4-8 nur lokal, ohne Prüfsummen; die Kostenbasis der Kennzahlen (research.py:272-279) ist data/processed/yubit_spannen_stichprobe.csv mit 30 Messzeitpunkten aus einer Stunde am 14.11.2026 und lässt sich nicht neu erzeugen. Herkunft der Ergebnisdateien (reports_herkunft.txt): Runde 15, 20a und 20b entstehen über Aufrufargumente von suche_runde14.py, suche_runde18.py und suche_runde19.py; für swing_vergleich.json gibt es kein erzeugendes Skript.
- **Auswirkung:** Dritte können aus der Dokumentation weder den laufenden Betrieb noch die geltende Konfiguration ablesen. Die berichteten Kennzahlen lassen sich nur in der bestehenden Arbeitsumgebung nachrechnen; geht sie verloren, ist die Kostenbasis nicht wiederherstellbar.
- **Empfehlung:** Trading-Plattform in ein eigenes Repo oder mindestens einen eigenen Zweig mit eigener .gitignore und eigenem Veröffentlichungsordner legen. READMEs auf den Stand bringen (Betriebsweg, Konfigurationen, Tests 1 und 2). Verwaiste Dateien entfernen. Die kleine Kostenstichprobe und ein Datenverzeichnis mit Prüfsummen versionieren. Ungenutzte Abhängigkeiten streichen. Je Runde den genauen Aufruf festhalten.
- **Nachstellen:** cd /home/user/OdinGate-Botv134/swing-hybrid && .venv/bin/python -I reports/audit/evidence/ARC/outputs_map.py /home/user/OdinGate-Botv134/swing-hybrid; grep -rn 'freqtrade' --include=*.py src scripts vorwaertstest tests; grep -rn 'dashboard_seite\|dashboard_live' --include=*.py --include=*.sh vorwaertstest scripts

### Nachgerechnete Aussagen

- **reproduziert**: Bestehende Tests: 105 Tests grün. 105 passed in 16,6 s, verteilt auf 17 Testdateien. Der Arbeitsbaum blieb danach unverändert (git status). Befehl: `cd /home/user/OdinGate-Botv134/swing-hybrid && .venv/bin/python -I -B -m pytest -q -p no:cacheprovider tests`
- **reproduziert**: Regel: long, wenn der Schlusskurs der letzten abgeschlossenen Stunde über dem von 336 Stunden zuvor liegt, sonst short; 10 Coins gleichgewichtet. research.tsmom(336), research._trend und mutationen.basis sind identisch. Der Bot (bot.markt_lesen mit kern.richtung) liefert auf denselben Binance-Stundenkerzen in 463.680 von 464.400 Coin-Stunden dieselbe Richtung, in 0 Fällen eine widersprechende. Die 720 Abweichungen liegen alle in Datenlücken (SOL, XRP, LTC). Bei Gleichstand ist das Signal 0, also keine Position. Positionsgröße in beiden Teilen fest: Kapital × Hebel / Anzahl Coins (bot.py:165, research.py:150). Befehl: `cd /home/user/OdinGate-Botv134/swing-hybrid && .venv/bin/python -I -B reports/audit/evidence/ARC/signal_paritaet.py`
- **reproduziert**: Entwicklung +59 % pro Jahr, Sharpe 0,95. Gruppe A, bis 01.04.2025, sofortige Ausführung, Yubit-Kosten mit Rebate, Hebel 1, ohne Tageslimit: N +2,156, +59,4 % pro Jahr, Sharpe 0,946. Das deckt sich mit reports/suche_runde24.json. Die Zahl gilt nur für Hebel 1 ohne Tageslimit und ohne Zinseszins, nicht für die betriebene Konfiguration (siehe ARC-01). Befehl: `cd /home/user/OdinGate-Botv134/swing-hybrid && .venv/bin/python -I -B reports/audit/evidence/ARC/experimente_forschung.py`
- **reproduziert**: Zwei Papier-Tests mit Hebel 3 seit 15.11.2026 (Test 1 nur Umkehrsignal, Test 2 mit Stop 5 % und Ziel 15 %). Beide Konfigurationen: Hebel 3.0, Modus papier, Kapital 5.000 $. Test 1 startet laut zustand.json um 13:21 UTC, Test 2 um 17:44 UTC. Je 10 Short-Positionen, je 10 Orders. Die Zustände habe ich nur gelesen. Befehl: `cat swing-hybrid/vorwaertstest/config_lauf.json swing-hybrid/vorwaertstest/config_lauf_tpsl.json; head -2 swing-hybrid/vorwaertstest/lauf/stand.csv swing-hybrid/vorwaertstest/lauf_tpsl/stand.csv`
- **abweichend**: Stündliche Signalprüfung. Das Signal ändert sich nur mit der Stundenkerze, der Bot wird aber alle 1 bis 13 Minuten aufgerufen, am häufigsten alle 5 (64 Läufe in 5,6 Stunden). Für Test 1 ist das ohne Folgen für die Regel, für Test 2 ändert es die Stop- und Ziel-Prüfung (ARC-05). Befehl: `python3 -I -c "import csv,datetime as d,collections;r=list(csv.DictReader(open('/home/user/OdinGate-Botv134/swing-hybrid/vorwaertstest/lauf/stand.csv')));t=[d.datetime.fromisoformat(x['zeit']) for x in r];print(sorted(collections.Counter(int((b-a).total_seconds()/60) for a,b in zip(t,t[1:])).items()))"`
- **abweichend**: README: Tagesverlust-Limit 3 % als Sicherung im Betrieb. config.json und config.yaml nennen 0.03, die laufenden Konfigurationen config_lauf.json und config_lauf_tpsl.json 1.0. Das Limit greift damit erst bei 100 % Verlust des Kapitals an einem Tag. Befehl: `grep -n tagesverlust_limit swing-hybrid/vorwaertstest/config*.json swing-hybrid/config.yaml`
- **abweichend**: README: Der Live-Teil ist mit nachgestellter Börse getestet. Getestet sind nur die Signatur einer Order und die Sperre ohne Schlüssel. bot.live_order, bot.live_positionen, yubit.storno und yubit.fills werden von keinem Test ausgeführt. Befehl: `cd /home/user/OdinGate-Botv134/swing-hybrid && .venv/bin/python -I -B reports/audit/evidence/ARC/abdeckung_zeilen.py`
- **ungeklaert**: Die Workflow-Datei unter .github liegt nicht im Standard-Zweig. Die Datei existiert nur im Zweig claude/intelligent-sagan-2cviug, nicht in feature/content-engine-mvp. Welcher Zweig auf GitHub als Standard gesetzt ist, lässt sich lokal nicht feststellen. Befehl: `cd /home/user/OdinGate-Botv134 && git ls-tree -r origin/feature/content-engine-mvp --name-only | grep -c workflows`
- **ungeklaert**: Unabhängiger Prüfzeitraum +16,5 % pro Jahr, Sharpe 0,34. In diesem Prüfbereich nicht nachgerechnet; ich habe nur im Entwicklungszeitraum gerechnet. Die Nachrechnung gehört in den Bereich Quantitative Research.

### Als richtig befunden

- Signalregel stimmt zwischen Forschung und Bot überein: 463.680 von 464.400 Coin-Stunden gleich, 0 widersprechend, Rest Datenlücken (reports/audit/evidence/ARC/signal_paritaet.txt; research.py:89-93, kern.py:14-19, bot.py:84-102).
- Kein Blick voraus beim Zeitversatz: Das Signal der Stunde H wirkt im 5-Minuten-Raster erst ab H+1:00, spätere Kurse ändern nichts Früheres (research.py:70-75; luecken_pruefung.txt, Abschnitt 4).
- Kern 2 rechnet Funding mit richtigem Vorzeichen und Betrag (Long zahlt bei positiver Rate, Nominal × Rate) und nicht in der Einstiegskerze; das Tageslimit schließt alles, sperrt bis zum nächsten UTC-Tag und lässt danach den Wiedereinstieg zu (engine2.py:45-79, 99-102; luecken_pruefung.txt, Abschnitte 1 und 2).
- Gebühr und Rebate im Ergebnis: netto ohne Rebate = brutto − 0,08 % × Taker-Volumen, mit Rebate = brutto − 0,012 % × Taker-Volumen; die Summe der Tagesgewinne entspricht dem Endstand; in sicht() gilt N = G − F + R (runner.py:48-57, research.py:170-186; luecken_pruefung.txt, Abschnitt 3).
- Funding-Buchung im Bot: über einen 8-Stunden-Termin genau einmal gebucht, Betrag = Position × Mark-Kurs × Rate (bot.py:185-189, kern.py:91-96; luecken_pruefung.txt, Abschnitt 5).
- zustand.json wird über eine temporäre Datei und replace geschrieben, also nie halb (bot.py:74-77).
- Im Papier-Modus kann der Bot keine Order senden: live nur bei 'modus': 'live' und YUBIT_LIVE=ja und Schlüssel (bot.py:107-108, 156-158); private Endpunkte brechen ohne Schlüssel ab (yubit.py:55-56); beide laufenden Konfigurationen stehen auf 'papier'; Test dazu: tests/test_vorwaertstest_bot.py:104-112.
- Der Papier-Bot braucht nur die Standardbibliothek und importiert nichts aus src/hybrid; src/hybrid hat keine zyklischen Importe (reports/audit/evidence/ARC/importgraph.txt).
- Gebühren und Rebate sind derzeit an allen Stellen gleich: config.yaml:6-8 (0,04 %, 0,08 %, 85 %), kern.py:9, listings.py:9, pumpshort.py:47.
- Positionsgröße ist in Forschung und Bot gleich definiert: fester Nominalwert je Coin beim Einstieg, ohne Zinseszins (research.py:150, engine2.py:88; bot.py:165, 204).
- Alle Bot-Tests schreiben nur in temporäre Verzeichnisse (tmp_path); der Testlauf verändert weder vorwaertstest/lauf noch docs oder reports.
- Die Forschungsskripte schreiben nur nach reports/; bis auf fünf Dateien lässt sich jede Ergebnisdatei einem Skript zuordnen (reports/audit/evidence/ARC/reports_herkunft.txt).

### Ungeklärt

- GitHub-Einstellungen sind lokal nicht prüfbar: Sichtbarkeit des Repos, Standard-Zweig, Quelle von GitHub Pages (Ordner /docs dieses Zweigs).
- Der Taktgeber (KI-Sitzung) liegt nicht im Repo. Sein Takt ist nur aus stand.csv abgeleitet. Ob der Bot nach 18:58 UTC weiterlief, ist lokal nicht feststellbar: Der lokale Stand endet mit dem Abruf von 19:03 UTC, und ein fetch war nicht erlaubt.
- Ob der Live-Pfad gegen die echte Yubit-Schnittstelle funktioniert, ist ungeklärt; er ist nie gelaufen und wurde auftragsgemäß nicht gegen die Börse geprüft. Die Aussagen zu ARC-02 stammen aus Code und Attrappen.
- Ob die Preisgrenze von 0,05 % bei den beobachteten Orderbüchern live gebunden hätte, ist ungeklärt: In 93 von 635 Messungen von Test 1 reichte die beste Buchstufe nicht für eine Order in Standardgröße, wegen der Tick-Rundung (bei DOT entspricht ein Tick rund 13,7 Basispunkten) lässt sich daraus aber keine Teilfüllung ableiten.
- Die Bedeutung der Yubit-Felder (fundingRate / 1e6, fundingInterval) ist nur durch die vier gespeicherten Antwortbeispiele in tests/fixtures belegt, nicht durch eine Abrechnung.
- Der in ARC-08 beschriebene Dauerfehler nach einem fremden Push (Push abgelehnt, danach 'pull --ff-only || true') ist aus stunde.sh abgeleitet und wurde nicht ausgeführt, weil schreibende git-Befehle untersagt waren.
- Ob die Rohdaten unter data/ vollständig und unverändert sind, ist ungeklärt: Es gibt keine Prüfsummen und kein versioniertes Verzeichnis; die Nachrechnung auf einer frischen Maschine wurde nicht versucht.
- Die Reihenfolge 'Protokoll vor Ergebnis' lässt sich aus git allein nicht beweisen: Protokoll- und Ergebnis-Commits liegen oft nur ein bis zwei Minuten auseinander (zum Beispiel 30443cd um 17:39 und 42c2168 um 17:40).

### Evidenzdateien

- `/home/user/OdinGate-Botv134/swing-hybrid/reports/audit/evidence/ARC/datenfluss.mmd`
- `/home/user/OdinGate-Botv134/swing-hybrid/reports/audit/evidence/ARC/importgraph.txt`
- `/home/user/OdinGate-Botv134/swing-hybrid/reports/audit/evidence/ARC/importgraph.py`
- `/home/user/OdinGate-Botv134/swing-hybrid/reports/audit/evidence/ARC/signal_paritaet.txt`
- `/home/user/OdinGate-Botv134/swing-hybrid/reports/audit/evidence/ARC/signal_paritaet.py`
- `/home/user/OdinGate-Botv134/swing-hybrid/reports/audit/evidence/ARC/abdeckung.txt`
- `/home/user/OdinGate-Botv134/swing-hybrid/reports/audit/evidence/ARC/abdeckung.py`
- `/home/user/OdinGate-Botv134/swing-hybrid/reports/audit/evidence/ARC/abdeckung_zeilen.txt`
- `/home/user/OdinGate-Botv134/swing-hybrid/reports/audit/evidence/ARC/abdeckung_zeilen.py`
- `/home/user/OdinGate-Botv134/swing-hybrid/reports/audit/evidence/ARC/experimente_bot.txt`
- `/home/user/OdinGate-Botv134/swing-hybrid/reports/audit/evidence/ARC/experimente_bot.py`
- `/home/user/OdinGate-Botv134/swing-hybrid/reports/audit/evidence/ARC/experimente_forschung.txt`
- `/home/user/OdinGate-Botv134/swing-hybrid/reports/audit/evidence/ARC/experimente_forschung.py`
- `/home/user/OdinGate-Botv134/swing-hybrid/reports/audit/evidence/ARC/experiment_live_attrappe.txt`
- `/home/user/OdinGate-Botv134/swing-hybrid/reports/audit/evidence/ARC/experiment_live_attrappe.py`
- `/home/user/OdinGate-Botv134/swing-hybrid/reports/audit/evidence/ARC/luecken_pruefung.txt`
- `/home/user/OdinGate-Botv134/swing-hybrid/reports/audit/evidence/ARC/luecken_pruefung.py`
- `/home/user/OdinGate-Botv134/swing-hybrid/reports/audit/evidence/ARC/reports_herkunft.txt`
- `/home/user/OdinGate-Botv134/swing-hybrid/reports/audit/evidence/ARC/outputs_map.py`

## Gegenprüfungen im Wortlaut

### Gegenprüfung ENG-01: bestaetigt, Stufe P0

Der Befund ENG-01 ist nicht widerlegbar; ich habe ihn am Code und mit einer eigenen Nachstellung bestätigt. Er ist eher zu eng gefasst.

**Mechanismus (bestätigt)**
- `vorwaertstest/bot.py:130-131` prüft `menge * preis > cfg["max_order_usd"]` für jede Live-Order, auch für `reduce_only`.
- Geschlossen wird immer die ganze Position in einer Order (`bot.py:233`), ohne Aufteilung.
- `bot.py:254-256` fängt den Fehler als Warnung ab und bricht ab. Der Lauf endet normal, gemeldet wird nur "Hinweis: ..." auf der Standardausgabe.
- Der Abgleich Börse gegen Protokoll (`bot.py:177-182`) schlägt nicht an, weil beide Seiten die Position unverändert führen. Der Bot wiederholt den Fehlschlag also bei jedem Lauf.
- `max_order_usd` wird nur in `bot.py:130-131` ausgewertet. Der Papier-Modus prüft den Deckel nicht, die laufenden Papier-Tests können den Fehler daher nie zeigen.
- Die bestehenden Tests unter `tests/` decken `live_order` gar nicht ab.

**Das Szenario ist realistisch**
- Bei Deckel/Betrag 2000/1500 wie in `config_lauf*.json` reicht ein Kursanstieg von rund 33 % gegen einen Short.
- ADA-Short am 02.03.2025 (Entwicklungszeitraum): Der Ausstieg war um 16:00 UTC fällig, bei Kursverhältnis 1,273 zum Einstieg. Um 16:05 stand es bei 1,340, das Hoch der 16:00-Kerze bei 1,381. Ein Lauf wenige Minuten nach der vollen Stunde wäre am Deckel gescheitert. Der Kurs blieb bis 03.03. 18:35 über der Schwelle, in der Spitze bei 1,73.
- Vorperiode 2020 bis 08/2021: drei Short-Ausstiege über der Schwelle. Bei DOGE (28.01.2021, Verhältnis 1,453) fiel der Kurs danach nie wieder unter 1,34 und stieg bis auf das 91,7-Fache des Einstiegs.
- Bei Deckel/Betrag 150/100 wie in `config.json` gab es auf Stundenschlüssen vor 04/2025 keinen Short-Fall.

**Was der Erstprüfer nicht nennt: Long-Positionen sind ebenfalls betroffen, und viel häufiger**
- Ein Long, dessen Wert über dem Deckel liegt, lässt sich ebenso wenig schließen (eigene Nachstellung, Fall F).
- Im Entwicklungszeitraum (08/2021 bis 03/2025) betrifft das 46 von 7467 Ausstiegen bei 2000/1500 und 27 bei 150/100.
- Folge: Die gewinnstärksten Trades können nicht wie im Backtest glattgestellt werden. Der Bot bleibt gegen das Signal long, bis der Kurs unter die Schwelle zurückfällt.

**Präzisierungen zur behaupteten Auswirkung**
- "Unbegrenzt" gilt aus Sicht des Bots. Praktisch begrenzt die Zwangsliquidation der Börse den Verlust auf Margin oder Konto. Der Bot bildet sie nicht ab.
- Die Blockade endet von selbst, sobald der Positionswert wieder unter den Deckel fällt (Nachstellung Fall A, letzter Schritt).
- Der Fehler ist latent: Alle drei Konfigurationen stehen auf "papier", und laut `README.md:50` lief der Live-Teil noch nie gegen ein echtes Konto. Aktuell ist kein Geld gefährdet.

**Priorität**
P0 ist angemessen im Sinne von "vor jedem Live-Handel beheben". Eine als Schutz dokumentierte Schranke (`README.md:45`) verhindert genau den Risikoabbau durch Umkehrsignal, Stop und Tageslimit, und es gibt keinen Alarm. Bei Hebel 3 droht damit der Kontoverlust.

Nicht geprüft habe ich das Verhalten der echten Yubit-Schnittstelle bei `reduceOnly`; das ist für den Befund unerheblich, weil die Order die Börse gar nicht erreicht.

**Evidenz:**

Alle Belege liegen in `/home/user/OdinGate-Botv134/swing-hybrid/reports/audit/evidence/V-ENG-01/`; die Aufrufe stehen in `BEFEHLE.txt`. Am Repo wurde nichts geändert (git status zeigt nur `reports/audit/evidence`), es gab kein Netz, keine Schlüssel und keinen Zugriff auf `vorwaertstest/lauf*` oder `docs/`.

**1. Code gelesen**
- `vorwaertstest/bot.py:122-145` (`live_order`), `:229-270` (Auftragsschleife), `:177-182` (Positionsabgleich).
- Konfigurationen: `config.json:8` (150 bei 5000 × 0,2 / 10 = 100 USD), `config_lauf.json:19` und `config_lauf_tpsl.json:19` (2000 bei 5000 × 3 / 10 = 1500 USD); alle mit `"modus": "papier"`.
- Eine Suche nach `max_order_usd` in `vorwaertstest/`, `src/`, `scripts/`, `tests/` und `.github` findet die Auswertung nur in `bot.py:130-131`.
- In `tests/` gibt es keinen Test, der `live_order` ausführt.

**2. Eigene Nachstellung** (`repro_deckel.py`, Ausgabe `repro_deckel.txt`)
Eigene Konto-Attrappe mit Hedge-Positionen und reduceOnly-Prüfung, Läufe in temporären Verzeichnissen. Betrag 100 USD, Deckel 150 USD, sofern nicht anders genannt.

| Fall | Ablauf | Ergebnis |
|---|---|---|
| A | Short 1,0 zu 100; Kurs 160, Signal +1 | Warnung "Order über dem Sicherheitsdeckel (160 > 150 USDT)", keine Order an der Börse, Position bleibt −1,0 |
| A, Folgestunden | Kurs 200 / 300 / 500 | jeweils derselbe Fehlschlag; Ergebnis −100 / −200 / −400 USD; kein Abbruch |
| A, Rückfall | Kurs 149 | Schließen und Dreh gehen durch |
| B (Kontrolle) | wie A, Deckel 100000 | Schließen und Dreh funktionieren |
| C (Kontrolle) | Kurs 140 | funktioniert |
| D | Tageslimit löst aus, Signal bleibt Short | `gesperrt_tag` gesetzt, keine Schließ-Order; in der Folgestunde erneut blockiert |
| E | Stop 5 %, Kurssprung auf 152 | Stop-Order blockiert, Position bleibt |
| F | Long 1,0 zu 100; Kurs 160, Signal −1 | Verkauf (reduceOnly) blockiert, Position bleibt +1,0; bei Kurs 149 geht er durch |
| G | Werte aus `config_lauf.json` im Live-Modus, 15 Stück zu 100 | Kurs 133,0 schließt; Kurs 133,3 blockiert ("2001 > 2000"); Kurs 134,0 blockiert |
| H | Zahlen wie A im Papier-Modus | schließt und dreht ohne Warnung |

**3. Test des Erstprüfers ausgeführt**
`NUMBA_CACHE_DIR=$(mktemp -d) .venv/bin/python -I -B -m pytest -q -p no:cacheprovider --basetemp=$(mktemp -d) reports/audit/evidence/ENG/test_eng_ausgangsverhalten.py -k sicherheitsdeckel` ergibt "1 passed, 17 deselected".

**4. Zählung auf Binance-Stundenschlüssen vor 2025-04-01** (`historie_deckel.py`, `historie_detail.py`)
Signal wie `mutationen.basis`, nur Zählung, keine Parameterwahl, kein Prüfzeitraum. Ein- und Ausstieg zum Stundenschluss sind eine Näherung.

| Zeitraum | Trades | Deckel/Betrag 1,333: abgelehnte Schließ-Orders | Deckel/Betrag 1,5 |
|---|---|---|---|
| Entwicklung 15.08.2021 bis 31.03.2025 | 7467 | 46 (0 Short, 46 Long) | 27 (0 Short, 27 Long) |
| Vorperiode bis 14.08.2021 | 2755 | 37 (3 Short, 34 Long) | 25 (0 Short, 25 Long) |

- Größtes Short-Kursverhältnis bei fälligem Ausstieg im Entwicklungszeitraum: 1,273.
- Die drei Short-Fälle der Vorperiode: AVAX 12.10.2020 (1,355), XRP 30.04.2021 (1,360), DOGE 28.01.2021 (1,453). DOGE lag danach bis 03/2025 nie unter dem 1,34-Fachen des Einstiegs, Höchststand das 91,7-Fache.
- Die Spalten "stunden_blockiert" und "hoechstes_verh_solange_blockiert" in `historie_deckel.txt` sind eine Vereinfachung; belastbar ist die Anzahl der beim ersten Versuch abgelehnten Orders.

**5. ADA-Short in 5-Minuten-Auflösung** (`historie_ada.py`, Ausgabe `historie_ada.txt`)
- Einstieg 24.02.2025 23:00 zu 0,6792; das Signal dreht mit dem Schluss der 15:00-Kerze am 02.03.2025.
- 16:00 Eröffnung 0,8648 (1,273), Hoch 0,9381 (1,381); das bestätigt die 38,1 % des Erstprüfers.
- 16:05 Eröffnung 0,9103 (1,340), also über der Schwelle 1,3327.
- Erstmals wieder unter der Schwelle am 03.03.2025 18:35; Hoch dazwischen 1,1753 (1,730).
- Der ADA-Aufruf in `historie_detail.py` liegt wegen des Kerzen-Etiketts eine Stunde zu spät; maßgeblich ist `historie_ada.txt`.

### Gegenprüfung ENG-02: bestaetigt, Stufe P0

Der Befund hält der Gegenprüfung stand. Widerlegen ließ er sich nicht, drei Aussagen brauchen aber eine Einschränkung.

**Bestätigt**

- **Kein Margin- oder Liquidationsmodell.** `engine2.py:161-170` und `kern.py:83-88` summieren Kasse plus Bestand mal Kurs ohne Untergrenze. `bot.py:165` hält die Größe fest auf `kapital_usd` x `hebel` / Anzahl Coins. `yubit.py` hat keinen Endpunkt für Hebel oder Margin-Modus; `dashboard_daten.py:66-67` rechnet die Margin nur zur Anzeige (Test 1 aktuell 97,7 %, Test 2 99,8 %).
- **Tagesverlust-Limit faktisch aus.** Beide Lauf-Konfigurationen setzen `tagesverlust_limit` auf 1.0. Es greift erst, wenn an einem UTC-Tag mehr als das ganze Kapital verloren ist.
- **Zahlen des Prüfers.** Sein Skript liefert bei mir eine identische Ausgabe. Eine eigene Stundenrechnung ohne `engine2` trifft den Kontoverlauf des Kerns auf 6e-15.
- **Frisches Konto, Hebel 3, feste Größe, Entwicklungszeitraum.** Ich habe den Kern für jeden Starttag echt neu gestartet, statt die Abkürzung des Prüfers zu verwenden:

| Horizont | Konto <= 0, mit Rebate | Konto <= 0, ohne Rebate | Wert des Prüfers (mit / ohne) |
|---|---|---|---|
| 365 Tage (960 Starttage) | 8,4 % | 46,5 % | 8,4 % / 44,9 % |
| 90 Tage (1.235 Starttage) | 4,9 % | 9,8 % | 5,7 % / 10,0 % |

- **Einbruchskennzahl.** Größter Rückgang bei Hebel 3: 1,707 Startkapital, `runner.max_drawdown` meldet 0,384. Bei Hebel 1 auf Tagesbasis: 24,6 % relativ zur Spitze (Formel aus Runde 24) gegen 50,7 % des Startkapitals; auf 5-Minuten-Basis 56,9 %.
- **Bot-Experiment.** Mit der Konfiguration aus `config_lauf.json` und zehn Shorts steht das Konto nach +40 % bei -1.076 USD und nach +60 % bei -4.003 USD. Der Bot stellt keine Order, `gesperrt_tag` bleibt leer.

**Zusätzlich gefunden (verschärft den Befund)**

- Am 09.12.2024 um 21:00 UTC verliert das Portfolio in einer einzigen 5-Minuten-Kerze 0,53 Startkapital, in rund einer Stunde 0,83, am Kalendertag 0,89.
- Die feste Stückzahl lässt den Positionswert mit dem Kurs wachsen: an diesem Tag 5,8-faches Startkapital, im Maximum 6,5-faches. Der Bot prüft nur stündlich und hätte nicht reagieren können.

**Einschränkungen**

- **Die 8,4 % sind keine Wahrscheinlichkeit.** Die 81 Starttage überlappen und gehen auf etwa drei Episoden zurück (Konto erstmals <= 0 in 04–06/2023 und 10–11/2024, dazu je ein Starttag 03/2022 und 01/2024). Bis dahin vergehen im Median 132 Tage, mindestens 35. Der durchgehende Lauf ab 15.08.2021 fällt nie unter 0,887.
- **`einbruch_pct` im Dashboard unterschätzt nur nach aufgelaufenen Gewinnen.** Dann zeigt es für 100 % des Startkapitals 50 %. Bei einem frisch gestarteten Konto wie den beiden laufenden Tests zeigt es den Verlust korrekt (121 % in meinem Szenario).
- **„Keine Kennzahl warnt" gilt für Code und Dashboard, nicht für die Projektdokumente.** `suche_bericht.md:318-331` weist für Hebel 2 und 3 „Konto unter null" aus, allerdings mit 3-%-Tageslimit. `uebergabe_fuer_dritte.md:65-66` nennt das Ruin-Risiko bei Hebel 3 als offene Frage.

**Ungeklärt**

- Erhaltungsmargin, Cross- oder Isoliert-Modus und Standardhebel bei Yubit sind im Repo nicht belegt; der genaue Liquidationspunkt bleibt offen.
- Mit angenommener Erhaltungsmargin von 0,5 bis 2 % steigt der Anteil von 8,4 auf 9,2 bis 11,4 %.
- Bei isolierter Margin wären je nach an der Börse eingestelltem Hebel 1 Trade (Hebel 3), 8 (Hebel 5) oder 121 (Hebel 10) von 7.483 liquidiert worden.

**Priorität**

P0 ist angemessen. Derzeit läuft nur Papierhandel, es ist kein Geld gefährdet. Der Live-Pfad würde dieselbe Konfiguration aber annehmen: 1.500 USD je Coin liegen unter `max_order_usd` 2.000, und `konfig()` erlaubt Hebel bis 5. Ein Totalverlust bei Hebel 3 ist historisch belegt, und weder Rückrechnung noch Bot bilden ihn ab.

**Evidenz:**

Alle Läufe mit `-I -B` und eigenem `NUMBA_CACHE_DIR`, nur Entwicklungszeitraum bis 31.03.2025, keine Parameterwahl. Nichts außerhalb von `reports/audit` wurde geändert (`git status` geprüft); `stunde.sh` und der Bot liefen nicht gegen `lauf`, `lauf_tpsl` oder `docs`.

**Gelesen**

- `src/hybrid/engine2.py`, `runner.py:79-83`, `research.py:148-167`
- `vorwaertstest/kern.py`, `bot.py`, `yubit.py`, `dashboard_daten.py:52-67`
- `vorwaertstest/config_lauf.json`, `config_lauf_tpsl.json`, `config.json`
- `scripts/suche_runde24.py` (Formel des Einbruchs), `scripts/diagnose_kapital.py`
- `reports/suche_bericht.md:316-331`, `reports/uebergabe_fuer_dritte.md:54-66`, `reports/diagnose_kapital.json`
- `vorwaertstest/lauf/dashboard.json` und `lauf_tpsl/dashboard.json`, nur lesend

**Ausgeführt** (Skripte und Ausgaben liegen in `/home/user/OdinGate-Botv134/swing-hybrid/reports/audit/evidence/V-ENG-02/`)

1. **Skript des Prüfers nachgelaufen.** `reports/audit/evidence/ENG/g_hebel3_entwicklung.py`; `diff` gegen seine gespeicherte Ausgabe ohne Unterschied. Ausgabe: `g_hebel3_entwicklung_nachlauf.txt`.

2. **`v1_backtest.py`** (Ausgabe `v1_backtest.txt`, Laufzeit rund 6 Minuten)
   - A: `engine2` direkt aufgerufen. Hebel 1 +0,594 pro Jahr, Hebel 3 +1,781 pro Jahr; größte Abweichung |e3 − 3·e1| 8,9e-15.
   - B: eigene Stundenrechnung ohne `engine2`. Signal deckungsgleich mit der Forschung (0 abweichende Stunden), Kontoverlauf weicht höchstens 6,2e-15 ab.
   - C: alle 960 und 1.235 Starttage echt neu gestartet: 8,4 % und 4,9 % mit Rebate, 46,5 % und 9,8 % ohne. Schlechtester Starttag 04.02.2023: erstmals <= 0 am 25.04.2023, Tiefststand −0,46, nach 365 Tagen +1,19.
   - D: 81 Starttage mit Konto <= 0, nach Monat des ersten Unterschreitens: 2023-04 28, 2023-06 21, 2024-10 25, 2024-11 5, 2022-03 1, 2024-01 1.
   - E: angenommene Erhaltungsmargin 0,5 / 1 / 2 % ergibt 9,2 / 10,0 / 11,4 % (365 Tage, mit Rebate).
   - F: Hebel 1: 0,569 Startkapital auf 5-Minuten-Basis; Tagesbasis 0,2458 relativ zur Spitze gegen 0,5066 in Startkapital. Hebel 3: 1,707 gegen 0,384.
   - H: schlechteste Stunde −0,830, schlechtester Kalendertag −0,890 (09.12.2024); 7 von 1.325 Tagen mit Verlust >= 30 % des Startkapitals.
   - I: größte Gegenbewegung je Trade 38,1 %; >= 33 %: 1 Trade, >= 20 %: 8, >= 10 %: 121, >= 5 %: 507 von 7.483.

3. **`v2_einsatz.py`** (Ausgabe `v2_einsatz.txt`): Positionswert bei fester Stückzahl im Median 3,02, im 99-%-Quantil 5,43, maximal 6,53 Startkapital; am 09.12.2024 um 20:00 UTC 5,83. In 38,6 % der Stunden haben alle zehn Coins dieselbe Richtung.

4. **`v3_stunde.py`** (Ausgabe `v3_stunde.txt`): Kerze 09.12.2024 21:00 UTC −0,531 Startkapital; die Altcoins fallen in diesen fünf Minuten um 9 bis 13 %.

5. **`v4_bot.py`** (Ausgabe `v4_bot.txt`): `bot.schritt` mit nachgestellter Börse in einem Scratch-Verzeichnis, Werte aus `config_lauf.json`.
   - Szenario 1: Kontostand −1.076 USD bei +40,5 %, −4.003 USD bei +60 %; 0 Orders, zehn Shorts bleiben, `gesperrt_tag` leer; `margin_pct` 140,5 und 160,0.
   - Szenario 2: Rückgang um 100,2 % des Startkapitals, `einbruch_pct` zeigt 50,06.
   - Szenario 3: das Tageslimit 1.0 schließt erst bei −5.130 USD, also nach Kontostand −106 USD.

**Nicht geprüft:** der Live-Pfad gegen eine echte Börse (Ablehnung wegen fehlender Margin, Liquidation durch Yubit) und der Prüfzeitraum ab 04/2025.

### Gegenprüfung QD-01: bestaetigt, Stufe P0

Der Befund hält der Gegenprüfung stand. Alle genannten Zahlen habe ich mit eigenen Skripten nachvollzogen, und kein Widerlegungsversuch hat die Kernaussage gekippt. Die Überschrift ist nur für die Gesamthistorie etwas zu absolut (siehe Punkt 3).

**1. Reproduktion der Zahlen**
- **Prüfzeitraum:** 571 Tage, +16,5 %/Jahr, Sharpe 0,337, t = 0,42 (mit Newey-West-Korrektur 0,45).
- **Unsicherheit im Prüfzeitraum:** 90-%-Band Sharpe −0,84 bis +1,43, Ertrag −38,5 % bis +73,1 %/Jahr; 32 % der Ziehungen mit Mittel ≤ 0 (Prüfer: 31 %).
- **Entwicklung:** t = 1,80, Band Sharpe 0,10 bis 1,74.
- **Zufallstest nur Prüfzeitraum:** Perzentil 80,5, exakt wie in `reports/kandidat.json` gespeichert; mit Yubit-Kosten ebenfalls 80,5.
- **Auswahl-Korrektur über die 10 Trend-Einstellungen (Projektfunktion):** p allein 0,0710 (5 bp) und 0,0416 (Yubit-Kosten); White 0,1232 und 0,0744. Das stimmt exakt mit dem Prüfer überein.

**2. Widerlegungsversuche ohne Erfolg**
- **Rechenkern:** Eine eigene Nachrechnung der Tagesreihe ohne `engine2` weicht höchstens 5e-16 ab. Die Reihe ist kein Artefakt des Kerns.
- **Bootstrap-Varianten:** Blocklänge 5 und 40, Kreisblock, ohne Blöcke und die Näherungsformel liefern im Prüfzeitraum 30–34 % der Ziehungen ≤ 0.
- **Zufallstest:** Mit anderem Zufallsstart und 600 Verschiebungen um ganze Stunden liegt das Perzentil bei 79,2.
- **Eigene Auswahl-Korrektur:** White 0,133 (5 bp) und 0,081 (Yubit-Kosten); studentisiert bzw. Hansen SPA 0,20 und 0,136; Maximum der Sharpe-Werte 0,16 und 0,098. Über die Blocklängen 5 bis 40 bleibt alles zwischen 0,07 und 0,22, also nie unter 0,05.
- **Größerer Suchraum:** Über alle 32 bis Runde 3 getesteten Signal-Einstellungen wird es schwächer (White 0,17 / 0,09, SPA 0,33 / 0,27). Die Korrektur über 10 ist also eher milde.

**3. Gegenevidenz, die der Befund nicht nennt**
- **Vorperiode 02/2020–08/2021** (nicht zur Auswahl benutzt): Sharpe 1,36, t = 1,69.
- **Vorperiode plus Prüfzeitraum:** t = 1,70; 4,3 % der Ziehungen ≤ 0.
- **Gesamte Historie 2020–2026:** t = 2,47 ohne Korrektur für die Suche.
- **Zufallstest in der Entwicklung:** Perzentil 100 (bei 600 Verschiebungen 99,8).

Ein historischer Vorteil ist damit schwach bis mäßig belegt, aber nur aus den Jahren 2020–2024. Der Ertrag fällt monoton: +136 %, dann +59 %, dann +16,5 % pro Jahr; in den letzten 365 Tagen +5 % (Sharpe 0,12). Für die Zahl, auf die sich eine Entscheidung stützen würde, gilt der Befund uneingeschränkt.

**4. Einordnung der Prüfzeitraum-Zahl**
- Sie ist auch vom Entwicklungswert nicht zu unterscheiden (Differenz t = 0,84). Der Prüfzeitraum ist also nichtssagend, nicht widerlegend.
- Ohne Rebate ist die Punktschätzung negativ: −12,5 %/Jahr.
- Die +16,5 % / 0,34 beruhen auf der Yubit-Kostenannahme, die erst nach dem ersten Blick auf den Prüfzeitraum eingeführt wurde. Bei der Auswahl (5 bp) waren es +7,8 %/Jahr und Sharpe 0,159 (`reports/suche_runde3.json`).
- Die Yubit-Spannen stammen aus einer einzigen Stunde am 14.11.2026 (30 Zeitpunkte).

**5. Kleine Ungenauigkeit des Prüfers**
Die Hürde 90 war im Protokoll für den ganzen Zeitraum festgelegt und wurde dort bestanden (Perzentil 100). Die Variante nur für den Prüfzeitraum ist eine nachträgliche Diagnose. Der Projektbericht legt die 90-%-Marke aber selbst daran an (`reports/suche_bericht.md:98-100`).

**6. Szenario und Priorität**
- Das Szenario ist real: `reports/uebergabe_fuer_dritte.md:16-25` führt +16,5 % / Sharpe 0,34 unter „Was belegt ist“ als „Ungesehener Prüfzeitraum“, ohne Unsicherheitsangabe.
- Die Papier-Tests laufen mit Hebel 3. Das 90-%-Band des Jahresertrags liegt dort bei −115 % bis +219 % des Kapitals.
- Ein Vorwärtstest kann die Frage praktisch nicht klären: Bei wahrem Sharpe 0,34 bräuchte t = 1,645 rund 24 Jahre.
- P0 ist angemessen, als Entscheidungssperre vor echtem Geld und nicht als Code-Fehler. Solange nur Papierhandel läuft, entsteht kein unmittelbarer Schaden. Das Projekt verschweigt die Schwäche auch nicht (`reports/suche_bericht.md:100`, `reports/suche_protokoll.md:136`).

**Evidenz:**

**Vorgehen**
- Gelesen: `src/hybrid/research.py` (`tsmom`, `auf_raster`, `lauf`, `sicht`, `yubit_kosten`), `engine2.py`, `runner.py`, `mutationen.py:165-183` (`reality_check`), `scripts/suche_runde3.py` (Auswahl Zeile 54, Zufallstest 86-96), `scripts/kandidat_pruefen.py:60-67`, `reports/kandidat.json`, `reports/suche_runde3.json`, `reports/suche_bericht.md:98-100`, `reports/suche_protokoll.md` (Runden 1–4, 6, 8), `reports/uebergabe_fuer_dritte.md:16-25`.
- Die Skripte des Prüfers habe ich nicht gestartet, weil sie JSON nach `evidence/QD` schreiben. Stattdessen zwei eigene Skripte, die nur nach stdout schreiben.
- `git status` zeigt nach den Läufen außerhalb von `reports/audit/` keine Änderung.

**Nachvollziehen**
```
cd /home/user/OdinGate-Botv134/swing-hybrid
.venv/bin/python -I reports/audit/evidence/V-QD-01/v_stat.py   # ca. 4 min
.venv/bin/python -I reports/audit/evidence/V-QD-01/v_rc.py     # ca. 1,5 min
```
Ein zweiter Lauf von `v_rc.py` gab identische Ausgabe.

**Auszüge aus `v_stat.txt`**
- Eigene Nachrechnung gegen `engine2`: größte Abweichung 4,79e-16 (mit Rebate) und 5,20e-16 (ohne Rebate).
- Yubit, mit Rebate, Prüfzeitraum: Tage 571, Ertrag/Jahr +0,165, Sharpe +0,337, t +0,42, t(HAC) +0,45. Stationärer Bootstrap (Block 20, 10.000 Ziehungen): Ertrag [−0,385, +0,731], Sharpe [−0,84, +1,43], Anteil Mittel ≤ 0: 0,322.
- Yubit, mit Rebate, Entwicklung: Tage 1325, +0,594, Sharpe +0,946, t +1,80; Sharpe [+0,10, +1,74]; Anteil ≤ 0: 0,033.
- Yubit, ohne Rebate, Prüfzeitraum: −0,125, Sharpe −0,254.
- 5 bp, mit Rebate, Prüfzeitraum: +0,078, Sharpe +0,159, t +0,20.
- Unterschied Entwicklung minus Prüfzeitraum: t = 0,84.
- Zufallstest wie `kandidat_pruefen.py` (5 bp, seed 11, 200): Perzentil 80,5, echt 0,1222, Median −0,296784; Abweichung gegen gespeichert +0,00 / 7e-17.
- Zufallstest Yubit, seed 11: Prüfzeitraum 80,5, Entwicklung 100,0. Anderer seed, 600 ganze Stunden: Prüfzeitraum 79,17, Entwicklung 99,83.
- Vorperiode mit Rebate: Tage 561, +1,361, Sharpe +1,363, t +1,69.
- Vorperiode + Prüfzeitraum: t +1,70, Anteil ≤ 0: 0,0428.
- Vorperiode + Entwicklung + Prüfzeitraum: t +2,47, Anteil ≤ 0: 0,0076.
- Letzte 365 Tage: +0,051, Sharpe +0,115.

**Auszüge aus `v_rc.txt`**
- Abgleich mit `reports/suche_runde3_stufe1.csv`: größte Abweichung 4,44e-16. Finalisten nach gespeicherter Regel: `tsmom_L336_biasFalse`, `tsmom_L96_biasFalse`.

| Aufbau (10 Einstellungen, Entwicklung) | p allein (Projekt) | White (Projekt, seed 3 / 21) | White eigen | White studentisiert | SPA | Sharpe-Maximum |
|---|---|---|---|---|---|---|
| 5 bp, mit Vorlauf | 0,0710 | 0,1232 / 0,1242 | 0,1351 | 0,2039 | 0,1990 | 0,1603 |
| Yubit-Kosten | 0,0416 | 0,0744 / 0,0772 | 0,0811 | 0,1359 | 0,1359 | 0,0981 |

- Blocklänge 5 und 40: White 0,07–0,15, SPA 0,11–0,22.
- 32 Einstellungen: White 0,1674 (5 bp) und 0,0902 (Yubit); SPA 0,3258 und 0,2674.

**Gespeicherte Projektwerte**
- `reports/kandidat.json`, `zufall_pruefung.perzentil` = 80.5.
- `reports/suche_runde3.json`, Stufe `4_zufall` (ganzer Zeitraum): Perzentil 100.0. Prüfzeitraum sofort, Gruppe A (5 bp, Hebel 1): N 0,1222, Sharpe 0,1591, `jahr_N` 0,0781.
- `data/processed/yubit_spannen_stichprobe.csv`: 30 Zeitpunkte, 2026-11-14 15:40 bis 16:39.

**Dateien**
- /home/user/OdinGate-Botv134/swing-hybrid/reports/audit/evidence/V-QD-01/v_stat.py
- /home/user/OdinGate-Botv134/swing-hybrid/reports/audit/evidence/V-QD-01/v_stat.txt
- /home/user/OdinGate-Botv134/swing-hybrid/reports/audit/evidence/V-QD-01/v_rc.py
- /home/user/OdinGate-Botv134/swing-hybrid/reports/audit/evidence/V-QD-01/v_rc.txt

### Gegenprüfung QD-03: bestaetigt, Stufe P0

Widerlegung nicht gelungen. Alle Zahlen des Befunds habe ich auf zwei Wegen nachgerechnet: mit den Repo-Modulen und mit einer eigenen Schleife, die engine2, research und runner nicht benutzt. Im Prüfzeitraum stimmen beide Wege auf vier Nachkommastellen überein.

**Nachgerechnet (Hebel 1, Yubit-Kosten, ohne Tageslimit, Prüfzeitraum 01.04.2025–23.10.2026, 571 Tage):**
- Vor Gebühren +33,9 % (darin Funding −3,5 %), Gebühr 53,4 %, Rebate 45,4 %.
- Netto mit Rebate +25,8 % (+16,5 %/Jahr, Sharpe 0,34).
- Netto ohne Rebate −19,6 % (−12,5 %/Jahr, Sharpe −0,25).
- Mit 5 bp Slippage ohne Rebate −33,2 %.
- Entwicklung ohne Rebate +113,8 % statt +215,6 %, Sharpe 0,50 statt 0,95, t = 0,95.

**Der Befund hält auch unter günstigeren Annahmen:**
- Selbst mit null Slippage bleibt der Prüfzeitraum ohne Rebate bei +0,2 %.
- Ohne Rebate sind 6 von 10 Coins und 5 von 7 Quartalen negativ; es hängt nicht an einem Ausreißer.
- Bei Hebel 3 wie im Papier-Test sind es ohne Rebate −58,7 % des festen Startkapitals in 19 Monaten (−37,5 %/Jahr).
- Das Rebate beträgt bei Hebel 1 rund 29 % des Kapitals pro Jahr und ist damit größer als der gesamte Nettoertrag von 16,5 %/Jahr.

**Code-Aussagen bestätigt:**
- Im Papier-Modus wird das Rebate sofort mit 85 % der Gebühr gutgeschrieben (eigener Lauf im temporären Ordner mit nachgestellter Börse).
- Im Live-Zweig steht fest `rebate = 0.0` (bot.py:245), und yubit.py fragt kein Rebate ab. Ein ausbleibendes Rebate wäre im Live-Betrieb also nicht zu erkennen.
- YUBIT_REGELN.md:19–28 und hybrid_report.md:207 sind korrekt zitiert.

**Präzisierungen, die in den Bericht gehören:**
1. Der Handel war vor Gebühren positiv; die Gebühr frisst ihn auf. Die Verlustschwelle im Prüfzeitraum liegt bei einem Rebate-Satz von 36,6 % (bei 5 bp Slippage 62,1 %). Eine Kürzung führt erst darunter zum Verlust.
2. Eine reine Verzögerung erzeugt keinen Verlust, sondern Vorfinanzierung: bei Hebel 3 im Mittel 7,2 % des Kapitals je 30 Tage, maximal 14,5 %.
3. Statistisch ist weder −19,6 % ohne Rebate (t = −0,32; Block-Bootstrap 33 % positiv) noch +25,8 % mit Rebate (t = 0,42; 65,5 % positiv) von null unterscheidbar. Über den Gesamtzeitraum ist die Strategie ohne Rebate positiv (+94 %, Sharpe 0,31, t = 0,70), getragen von D2. Sicher ist nur die Größe des Rebate-Beitrags.
4. Die Abhängigkeit ist kein versteckter Fehler. Sie war Suchziel (suche_protokoll.md:7–13) und steht im Bericht des Entwicklers (suche_bericht.md:376–378). Die Kennzahlen des Betreibers (+59 % / +16,5 %) sind aber alle mit Rebate gerechnet.

**Ungeklärt, aus dem Repo nicht prüfbar:** tatsächlicher Rebate-Satz, Auszahlungsrhythmus und Bedingungen sowie die Taker-Gebühr von 0,08 %; beides steht nur in config.yaml.

**Priorität:** P0 ist als Freigabebedingung vor Live-Handel angemessen, weil die Rentabilität an einer unbelegten Vertragsbedingung hängt, die Yubit laut eigenen Regeln streichen darf. Für den laufenden Papier-Betrieb entsteht kein Schaden.

**Nebenbeobachtung:** In D1 weicht meine eigene Rechnung leicht ab (netto mit Rebate 0,608 statt 0,631). Ursache sind 5 fehlende Tage bei SOL, XRP und LTC (26.02.–02.04.2022), in denen das Repo das Signal auf 0 setzt. Der Prüfzeitraum ist davon nicht berührt.

**Evidenz:**

Alle Läufe mit `cd /home/user/OdinGate-Botv134/swing-hybrid && .venv/bin/python -I <skript>`. Skripte und Ausgaben liegen in /home/user/OdinGate-Botv134/swing-hybrid/reports/audit/evidence/V-QD-03/. Die Skripte schreiben nur auf stdout; papier_rebate.py legt zusätzlich einen temporären Ordner neben sich an und löscht ihn wieder. Das Skript des Prüfers (evidence/QD/repro1.py) habe ich gelesen, aber nicht ausgeführt, weil es eine Datei im Ordner des Prüfers überschreibt.

**1. repo_module.py → repo_module.txt** (Repo-Module research.markt / tsmom / lauf; eigene Zerlegung aus eq_gross, TV, FU)
- Prüfung, Yubit-Kosten: G 0,3386, Funding −0,0348, F 0,5343, R 0,4541, N_mit 0,2585, N_ohne −0,1956, jahr_ohne −0,1251, sharpe_ohne −0,2537, t_ohne −0,3174, Satz für Null 0,3662.
- Entwicklung: N_mit 2,1564, N_ohne 1,1383, Sharpe 0,9457 / 0,4970, t_ohne 0,9469.
- 5 bp: Prüfung N_ohne −0,3319, Satz für Null 0,6213.
- Null Slippage: Prüfung N_ohne +0,0020.
- Hebel 3: Prüfung N_ohne −0,5869 (jahr −0,3752), N_mit +0,7755.
- Je Coin ohne Rebate: BTC −0,020, ETH +0,097, SOL +0,001, XRP −0,074, DOT −0,133, DOGE +0,065, ADA −0,109, LINK +0,043, AVAX −0,037, LTC −0,028.
- Je Quartal ohne Rebate: +0,174 / −0,043 / −0,172 / +0,154 / −0,093 / −0,198 / −0,018.

**2. unabhaengig.py → unabhaengig.txt** (eigene Rechnung nur aus data/candles/5m, data/candles/funding und yubit_spannen_stichprobe.csv, ohne engine2 / research / runner)
- Prüfung: G 0,3386, F 0,5343, R 0,4541, N_mit 0,2585, N_ohne −0,1956, Sharpe 0,3369 / −0,2537. Identisch mit dem Repo.
- D2 identisch (N_ohne 1,0168).
- D1 abweichend: N_mit 0,6080 statt 0,6312.
- Staffel Rebate-Satz im Prüfzeitraum: 0 % → −0,1956; 30 % → −0,0354; 36,6 % → −0,0001; 50 % → +0,0715; 85 % → +0,2585.
- Vorfinanzierung bei Hebel 1: 85 % der Gebühr je 30 Tage im Mittel 0,0240, maximal 0,0483.
- Block-Bootstrap (20-Tage-Blöcke, 5000 Züge, Seed 20261115): ohne Rebate 5 % / 50 % / 95 % = −1,131 / −0,242 / +0,738, Anteil > 0 33,4 %; mit Rebate Anteil > 0 65,5 %.

**3. luecken.py → luecken.txt**
- SOL, XRP und LTC fehlen je 1440 5-Minuten-Kerzen zwischen 26.02.2022 und 02.04.2022.
- research.tsmom liefert in diesen Stunden Signal 0. Das erklärt die D1-Abweichung.

**4. papier_rebate.py → papier_rebate.txt** (bot.schritt mit der nachgestellten Börse aus tests/test_vorwaertstest_bot.py)
- Modus papier, 4 Orders, Gebühr 22,787052, Rebate 19,368994, Verhältnis 0,85.
- netto_mit_rebate − netto_ohne_rebate = 19,368994, also sofort im Stand.
- Live-Zweig nur gelesen: /home/user/OdinGate-Botv134/swing-hybrid/vorwaertstest/bot.py:243–245 setzt `rebate = 0.0`; in yubit.py kommt „rebate“ nicht vor.

**5. Nur gelesen**
- /home/user/OdinGate-Botv134/swing-hybrid/vorwaertstest/YUBIT_REGELN.md:19–28: Verbot der Rebate-Arbitrage, Abzug von Rebate, Streichen von Gewinnen; „Sein Gewinn stammt aber überwiegend aus dem Rebate“.
- /home/user/OdinGate-Botv134/swing-hybrid/reports/hybrid_report.md:207–208 und reports/suche_bericht.md:391: Rebate als sofortige Gutschrift gerechnet, Bedingungen nicht berücksichtigt.
- reports/suche_bericht.md:376–378: „Der Gewinn kommt hier wirklich aus dem Rebate … Wird das Rebate gekürzt oder gestrichen, trägt die Strategie nach heutigem Stand nicht mehr.“
- reports/suche_protokoll.md:7–13: Suchziel R > N − R.
- /home/user/OdinGate-Botv134/swing-hybrid/config.yaml: taker 0.0008, rebate_anteil 0.85.
- vorwaertstest/lauf/protokoll.csv: je Order Rebate = 0,85 × Gebühr, Summen 10,1495 / 11,9405.
- src/hybrid/runner.py:48–57 und :97–107: Rebate wirkt als Faktor (1 − rebate) auf die Gebühr, also zeitgleich mit ihr.

Am Ende zeigte `git status --short` außerhalb von swing-hybrid/reports/audit keine Änderung.

### Gegenprüfung QD-04: bestaetigt, Stufe P0

Der Befund hält im Kern; widerlegen ließ er sich nicht. Vier Punkte sind aber zu präzisieren.

**Was bestätigt ist**
- **Konfiguration:** Beide Tests laufen mit `hebel` 3.0 und `tagesverlust_limit` 1.0. Im laufenden Zustand halten beide Konten zehn gleichgerichtete Short-Positionen von je rund 1.500 $ auf 5.000 $ Kapital.
- **Mechanismus im Bot:** Die Positionsgröße kommt fest aus dem Startkapital (`bot.py:165`) und schrumpft bei Verlusten nicht. Das Limit greift erst bei 5.000 $ Verlust an einem UTC-Tag (`bot.py:196`). Ein Liquidations- oder Margin-Modell gibt es nicht.
- **Widerspruch zur eigenen Regel:** Der regelkonforme Hebel der Forschung ist 0,2. Für den Kandidaten ist Hebel 3 nur mit 3-%-Limit gespeichert (−101 %/Jahr, nachgerechnet). Ohne Limit findet sich im Repo keine Rechnung; Runde 24 (Stop/Ziel) lief nur mit Hebel 1.
- **Zahlen:** Mein eigener Rechenkern ohne `src/hybrid` liefert Kontotief ≤ −50 / −75 / −100 % bei 47,2 / 31,8 / 16,1 % der 267 Starts, im Prüfzeitraum 45,5 / 31,2 / 13,0 %. Alle 267 Starts werden gleich eingestuft wie beim Prüfer. Einbruch 38 % / 56 % und Rückgang 171 % / 163 % stimmen ebenfalls.
- **Szenario tritt im echten Code ein:** Der unveränderte Bot, gegen historische Kurse nachgespielt, fällt ab Start 20.07.2025 nach 75 Tagen auf Konto ≤ 0 (Tief −123 %). Er eröffnet danach weitere 516 Positionen in voller Größe; das Limit meldet sich nie.

**Präzisierungen**
1. **„Jeder sechste Starttag“ ist rasterabhängig.** Wöchentliche Starts ergeben 16,1 %, tägliche 13,5 %, Ausführung um hh:05 rund 20 %. Die Fälle überlappen stark und gehen auf etwa fünf bis sechs Episoden zurück (03/2022, 12/2022, 04–06/2023, 10–11/2024, 10–12/2025, 05–08/2026). Das ist eine historische Häufigkeit, keine belastbare Wahrscheinlichkeit. Ein durchgehender Lauf ab 08/2021 wäre nicht ruiniert worden.
2. **Die Quote gilt nur für Test 1.** Test 2 (Stop 5 % / Ziel 15 %) erreicht ≤ −100 % bei 3–4 % aller Starts, im Prüfzeitraum bei 8–14 %. Totalverlust kommt auch dort vor: Im Replay ab 08.02.2026 fallen beide Tests unter null (−126 % und −128 %).
3. **„Ohne Tageslimit“ ist faktisch richtig.** Das Limit 1,0 hätte historisch genau einmal ausgelöst (09.12.2024) und keinen Totalverlust verhindert.
4. **„Vom Hebel bestimmt, nicht vom Signal“ ist überspitzt.** Der Sharpe bleibt 0,95 / 0,34, der Hebel skaliert nur. Richtig ist: Das Überleben hängt am Hebel. Das schlechteste Kontotief liegt bei Hebel 2 bei −96 %, bei Hebel 1 bei −48 %, bei Hebel 0,2 bei −9,6 %.

**Folgen für die Bewertung**
- Papier-Ergebnisse nach einem Kontostand ≤ 0 sind real nicht erzielbar. Beispiel Start 23.06.2024: Tief −128 %, danach Papier-Endstand +163 %.
- Das 3-%-Limit wieder einzuschalten ist keine Lösung (−101 %/Jahr bei Hebel 3).
- Der Betreiber kennt das Risiko qualitativ (`dashboard_live.html:131–133`, `uebergabe_fuer_dritte.md:65`), unterschätzt es aber: „fast aufgebraucht“ steht dort, tatsächlich sind es bis 163 % des Startkapitals.

**Priorität**
P0 ist angemessen im Sinne von „vor jedem Live-Handel zu beheben“. Akut ist kein echtes Geld betroffen: Der Bot läuft im Papier-Modus, Live braucht `modus` live, `YUBIT_LIVE=ja` und Schlüssel. `konfig()` lässt aber Hebel bis 5 zu, und dieselben Felder gelten für Live.

**Ungeklärt**
- Margin- und Liquidationsregeln von Yubit: Der reale Ausfallzeitpunkt läge eher früher.
- Eine Datenlücke bei SOL, XRP und LTC (26.–28.02. und 01.–02.04.2022) kann die Episode 03/2022 berühren, das ist 1 von 43 Fällen.

**Evidenz:**

Alle Belege liegen in `/home/user/OdinGate-Botv134/swing-hybrid/reports/audit/evidence/V-QD-04/`; die Befehle zum Nachrechnen stehen in `nachvollziehen.txt`. Bestehende Dateien wurden nicht verändert, `stunde.sh` und der Bot liefen nie gegen `lauf/`, `lauf_tpsl/` oder `docs/`.

**1. Code und Konfiguration gelesen**
- `vorwaertstest/config_lauf.json:4,17` und `config_lauf_tpsl.json:4,17,21–22`.
- `vorwaertstest/bot.py:45` (Hebel bis 5 erlaubt), `:165` (feste Größe), `:196` (Limit), `:216–228` (Stop/Ziel).
- `vorwaertstest/config.json` (Vorlage mit Hebel 0,2 und Limit 0,03) und `README.md:3,61–63`.
- Commit 4276791: Hebel von 1 auf 3 gesetzt, Limit 1,0.
- `lauf/zustand.json` und `lauf_tpsl/zustand.json`, nur gelesen: je zehn Short-Positionen, zusammen rund 14.660 $ bzw. 14.970 $.
- `scripts/suche_runde3.py:100–113` und `reports/suche_runde3.json` (`finalisten/tsmom_L336_biasFalse/stufen/5_hebel`, Hebel 0,2).
- `scripts/diagnose_kapital.py:23–24` und `reports/diagnose_kapital.json`: einzige gespeicherte Rechnung mit Hebel ≥ 2, mit 3-%-Limit.
- `scripts/suche_runde24.py:19`: Hebel 1, Limit aus.
- `vorwaertstest/dashboard_live.html:131–133`, `reports/uebergabe_fuer_dritte.md:65`.

**2. Skript des Prüfers nachgerechnet**
- `evidence/QD/hebel3.py` als Kopie mit umgeleiteten Ausgabepfaden ausgeführt.
- Ausgabe identisch, die Ergebnis-CSV stimmt mit `evidence/QD/neustart_hebel3.csv` exakt überein (`repro_pruefer_skript_hebel3.txt`).

**3. Eigener Rechenkern ohne `src/hybrid`** (`unabhaengig.py`, `unabhaengig.txt`)
- Hebel 1: Entwicklung +59,5 %/Jahr, Sharpe 0,947; Prüfzeitraum +16,6 %/Jahr, Sharpe 0,338.
- Hebel 3: Einbruch 0,382 / 0,558, Rückgang 1,707 / 1,628.
- Neustart, 7-Tage-Raster: 0,472 / 0,318 / 0,161; Prüfzeitraum 0,455 / 0,312 / 0,130.
- Neustart, täglich (1.866 Starts): 0,472 / 0,303 / 0,135.
- Abgleich mit dem Prüfer: 267 von 267 Starts gleich eingestuft, größte Abweichung im Kontotief 0,010.
- Ereignis-Cluster und Vergleich für Hebel 0,2, 1 und 2 stehen in derselben Ausgabe; Tabellen in `neustart_hebel3_unabhaengig.csv` und `neustart_hebel3_taeglich.csv`.

**4. Nachbau der Bot-Logik für Test 1 und Test 2** (`bot_nachbau.py`, `bot_nachbau.txt`)

Mit Limit 1,0 und beiden Takten gerechnet:

| Variante | Anteil der Starts mit Kontotief ≤ −100 % |
|---|---|
| Test 1, Ausführung um hh:05 | 20,2–20,6 % |
| Test 1, alle 5 Minuten | 13,5–16,1 % |
| Test 2, alle Starts | 2,8–4,3 % |
| Test 2, Starts im Prüfzeitraum | 7,8–13,7 % |

- Das Limit 1,0 löst in 48 von 267 Pfaden einmal aus; die Quoten bleiben unverändert.
- Der Nachbau trifft die 5-Minuten-Latenz-Zeile des Prüfers (+57,8 % / Sharpe 0,92; +11,2 % / 0,23).

**5. Unveränderter Bot-Code im Replay** (`bot_replay.py`, `bot_replay_*.txt`)

`bot.schritt` lief mit den Werten der beiden Konfigurationsdateien gegen eine nachgestellte Börse mit historischen Kursen, in einem temporären Ordner.

| Start | Takt | Test 1 | Test 2 |
|---|---|---|---|
| 20.07.2025 | stündlich | Konto ≤ 0 am 02.10.2025, Tief −123 % | Tief −69 % |
| 08.02.2026 | stündlich | Tief −126 % | Tief −128 % |
| 08.02.2026 | 5 Minuten | Tief −113 % | Tief −116 % |
| 23.06.2024 | stündlich | Tief −128 %, Endstand +163 % | Tief −37 % |

- Start 20.07.2025, Test 1: 1.032 Orders nach Konto ≤ 0, davon 516 Einstiege; mittlerer Positionswert dabei 14.267 $; keine Limit-Meldung.
- Die Replay-Werte weichen von meinem Nachbau um höchstens rund einen Prozentpunkt ab.
- Die Starttage sind keine Stichprobe, sondern Fälle, die die Neustart-Rechnung bereits als Totalverlust ausweist.

**6. Gegenprobe mit dem Rechenkern des Projekts** (`engine_gegenprobe.py`, `engine_gegenprobe.txt`)
- Hebel 3 mit 3-%-Limit: −101,3 %/Jahr, Einbruch 3,589, 1.178 Sperrtage. Das entspricht der gespeicherten Zeile.
- Hebel 3 mit Limit 1,0: ein Sperrtag, Einbruch 0,384 / 0,558, tiefster Kontostand im durchgehenden Lauf +0,887.

**Nicht geprüft**
- Echtes Margin- und Liquidationsverhalten von Yubit.
- Nebenbeobachtung außerhalb des Befunds, nur am Code gelesen (`bot.py:130–131`): `max_order_usd` 2.000 würde im Live-Modus auch Schließ-Orders für Positionen blockieren, deren Wert über 2.000 $ gewachsen ist.

### Gegenprüfung QR-01: bestaetigt, Stufe P0

Der Kern des Befunds hält meinem Widerlegungsversuch stand: Der berichtete Einbruch (24,6 % / 31,3 %) gilt nur für Hebel 1 und ist am gewachsenen Rechenkonto gemessen. Mit der laufenden Konfiguration (Hebel 3, kein wirksames Tageslimit) enthält die eigene Historie mehrere Totalverluste. Drei Teilaussagen des Prüfers sind überzeichnet und sollten im Bericht korrigiert werden.

**Was bestätigt ist**

- **Messvorschrift:** `scripts/suche_runde24.py:62` misst den Einbruch als Rückgang von 1 + kumuliertem Tagesergebnis gegen den Höchststand. Die Größe ist fest am Startkapital (`engine2.py:88-92`).
- **Verlust in Startkapital-Einheiten bei Hebel 1:** größter absoluter Rückgang 0,51 / 0,50 auf Tagesbasis und 0,57 / 0,54 auf 5-Minuten-Basis. Mal 3 sind das 1,5 bis 1,7 Startkapital.
- **Der Papier-Bot rechnet genauso:** `bot.py:165` setzt je Coin Kapital × Hebel / 10 an, also 1.500 $, unabhängig vom Kontostand. `config_lauf.json` hat Hebel 3,0 und `tagesverlust_limit` 1,0; das Limit greift erst bei 100 % Tagesverlust (`bot.py:196`). Eine Liquidation oder Margin-Prüfung gibt es im Bot und im Rechenkern nicht.
- **Totalverlust bei frischem Start:** Ich habe jeden Kalendertag als Starttag einzeln durchgerechnet, statt wie der Prüfer die Tagesreihe des Dauerlaufs zu verdreifachen.

| Fenster | Starttage | Konto ≤ 0 | Konto ≤ 0,5 | Näherung des Prüfers (≤ 0) |
|---|---|---|---|---|
| Entwicklung, Hebel 3 | 1.325 | 14,6 % (194 Tage) | 49,1 % | 12,5 % |
| Prüfzeitraum, Hebel 3 | 571 | 10,7 % (61 Tage) | 42,2 % | 10,5 % |
| Entwicklung, Hebel 2 | 1.325 | 0,1 % | 32,0 % | – |
| Prüfzeitraum, Hebel 2 | 571 | 0,0 % | 27,0 % | – |
| beide, Hebel 1 | – | 0 % | 0,1 % / 0,0 % | – |

- **Mehrere getrennte Episoden:** 03/2022, 12/2022, 04–06/2023, 10–11/2024, 10–12/2025 und 05–08/2026. Die Näherung des Prüfers ist also eher vorsichtig.
- **Hebel in der Forschung:** Mit Tageslimit 3 % ergibt Hebel 0,2 einen Einbruch von 8,85 %, Hebel 0,25 schon 10,58 %. Bestanden hat der Kandidat nur bei 0,2 (`suche_protokoll.md:135`, `suche_bericht.md:23`). `vorwaertstest/README.md:3` nennt weiter Hebel 0,2. Der Wechsel auf Hebel 3 (Commit 4276791) enthält keine Risikobegründung.
- **Kurssturz 10.10.2025, 21:00 UTC:** Die Zahlen stimmen (DOT −74,5 %, AVAX −66,3 %, ADA −61,8 %, DOGE −61,7 %, LTC −57,5 % im Tief; 8 Short, BTC und LTC Long).

**Was zu korrigieren ist**

1. **„Der 09.12.2024 kostet bei Hebel 3 rund 89 % des Kontos“ ist überzeichnet.** Es sind 0,89 Startkapital. Gemessen am Konto des Vorabends sind es −11,2 % (Start 2021) bis −36,3 % (Start kurz davor), im Tagestief bis −51 %. An diesem Tag wird kein Konto ausgelöscht.
2. **Die Totalverluste sind kein Ein-Tages-Ereignis.** Sie entstehen über Wochen in Seitwärtsphasen: vom Start bis Konto ≤ 0 vergehen im Median 113 Tage (Entwicklung) bzw. 141 Tage (Prüfzeitraum), mindestens 38.
3. **„Einsatz 6,5x über hebel_max 5“ gilt nur gegen das Startkapital.** Im Dauerlauf stand das Konto dabei auf 8,09, das Verhältnis Einsatz zu Konto war 0,81. Gefährlich ist das Gegenteil: Bei Verlusten bleibt die Größe am Startkapital, und der wirksame Hebel wächst unbegrenzt.
4. **Die Zinseszins-Zahlen (95 % / 92 %, CAGR −18 % / −44 %) sind eine Näherung.** Echte Läufe bei Hebel 3:

| Schema | Einbruch Entw. / Prüf. | CAGR Entw. / Prüf. |
|---|---|---|
| Größe beim Einstieg = Konto × Hebel / 10 | 84,4 % / 85,6 % | +49,8 % / −13,4 % |
| zusätzlich täglich zurückgestellt | 98,2 % / 91,4 % | −24,7 % / −49,0 % |

Belastbar ist nur „Einbruch über 84 %“. Das Vorzeichen der CAGR in der Entwicklung hängt vom Schema ab. Der Papier-Bot rechnet ohnehin ohne Zinseszins.

**Test 2 (Stop 5 % / Ziel 15 %)**

Als Näherung mit den Gewichten des Dauerlaufs und Hebel 3: in der Entwicklung 0,0 % der Starttage mit Konto ≤ 0 (19,7 % mit ≤ 0,5), im Prüfzeitraum 9,3 % (63,7 % mit ≤ 0,5). Der Befund trifft damit auch Test 2.

**Ungeklärt**

- Margin-Modus und Liquidationsregeln von Yubit stehen nicht im Repo. Eine echte Liquidation käme vor Konto 0.
- Für die Zeit seit dem Start der Papier-Tests (15.11.2026) gibt es keine Historie.

**Priorität**

P0 ist angemessen. Live-Stufe und Hebel bis 5 sind im Bot vorgesehen (`bot.py:45`, `bot.py:106-145`), und es gibt keine Bremse. Wer mit „Einbruch 25 %“ und Hebel 3 plant, unterschätzt das Risiko um ein Vielfaches. Solange nur Papier läuft, entsteht kein Geldschaden.

**Evidenz:**

Alles in temporären Verzeichnissen gerechnet; keine bestehende Datei geändert, `stunde.sh` und der Bot nie gegen `lauf/`, `lauf_tpsl/` oder `docs/` gestartet. `git status` zeigt außerhalb von `reports/audit/` keine Änderung.

Belege liegen in `/home/user/OdinGate-Botv134/swing-hybrid/reports/audit/evidence/V-QR-01/`.

**Code gelesen**
- `/home/user/OdinGate-Botv134/swing-hybrid/scripts/suche_runde24.py:62` (Einbruch)
- `/home/user/OdinGate-Botv134/swing-hybrid/src/hybrid/engine2.py:84-92` (Größe fest an S) und `:168` (Tageslimit)
- `/home/user/OdinGate-Botv134/swing-hybrid/src/hybrid/research.py:148-158`
- `/home/user/OdinGate-Botv134/swing-hybrid/vorwaertstest/bot.py:45`, `:165`, `:196`
- `/home/user/OdinGate-Botv134/swing-hybrid/vorwaertstest/config_lauf.json` und `config_lauf_tpsl.json` (Hebel 3,0, `tagesverlust_limit` 1,0)
- `/home/user/OdinGate-Botv134/swing-hybrid/config.yaml:13`
- `/home/user/OdinGate-Botv134/swing-hybrid/reports/suche_protokoll.md:135`, `:1270-1271`
- `/home/user/OdinGate-Botv134/swing-hybrid/reports/suche_bericht.md:23`
- `/home/user/OdinGate-Botv134/swing-hybrid/vorwaertstest/README.md:3`
- Suche nach „liquid“ und „margin“ in `vorwaertstest/*.py`, `engine2.py` und `research.py`: nur eine Anzeigezeile in `dashboard_daten.py:66-67`.
- Laufender Zustand, nur gelesen: `vorwaertstest/lauf/stand.csv` zeigt 14.658 $ Einsatz bei 5.000 $ Kapital, 10 Shorts.

**Eigene Läufe** (aus `swing-hybrid/`, mit `.venv/bin/python -I -B -W ignore`, `NUMBA_CACHE_DIR` und Ausgabeverzeichnis im Scratch)

1. `v1_module.py <scratch>` → `v1_ausgabe.txt`: Modul-Lauf.
   - Entwicklung: Ertrag 0,594 pro Jahr, Sharpe 0,9457, Einbruch 0,2458 (identisch mit `suche_runde24.json`), absoluter Rückgang 0,5066, schlechtester Tag −0,2968 am 09.12.2024, 7 Tage unter −10 %.
   - Prüfzeitraum: Einbruch 0,3130, absoluter Rückgang 0,5014.
   - Mit Tageslimit 3 %: Hebel 0,2 → 0,0885; Hebel 0,25 → 0,1058.
   - Hebel 3 ohne Limit ist exakt linear (Abweichung 1,4e-14). Start am Fensterbeginn 01.04.2025: Konto-Tief 0,8432, Einbruch 0,5578.
2. `v2_frischstart.py <scratch>` (nach v1) → `v2_ausgabe.txt`, `v2_frischstart_hebel3_entw.csv`, `v2_frischstart_hebel3_pruef.csv`.
   - Eigener 5-Minuten-Kern stimmt mit engine2 auf 3,6e-15 überein.
   - Einsatz bei Hebel 1: Mittel 1,02, 95-%-Wert 1,32, Maximum 2,178 am 03.12.2024.
   - Frischer Start an jedem Tag: die Anteile aus der Tabelle oben, dazu die Ereignistage je Episode.
3. `v3_zusatz.py` → `v3_ausgabe.txt`: absoluter Rückgang auf 5-Minuten-Basis (0,5691 / 0,5425), Tabelle zum 09.12.2024 je Starttag, beide Zinseszins-Läufe, Test 2 (sl5_tp15), Kurssturz 10.10.2025.
4. `v4_unabhaengig.py` → `v4_ausgabe.txt`: reines pandas aus den Rohkerzen, ohne `src/hybrid`, ohne Slippage. Konto ≤ 0 bei Start 05.08.2024 (am 15.10.2024), 01.02.2023 (27.04.2023), 20.07.2025 (13.10.2025) und 25.02.2026 (03.08.2026). Kein Totalverlust bei Start 15.08.2021 und 01.04.2025.
5. `v5_bot_ohne_bremse.py <scratch>/botlauf` → `v5_ausgabe.txt`: echter Bot-Code mit `config_lauf.json` gegen eine nachgestellte Börse. Zehn Shorts, Kurse steigen dreimal 12 % pro Tag. Das Konto geht über 1.059 $ auf −76,68 $ und −2.557,75 $; keine Order, kein Limit, `gesperrt_tag` bleibt leer.

**Skripte des Prüfers nachgefahren**
- `c_abweichung_risiko.py`: Ausgabe identisch mit der gespeicherten Evidenz.
- `j_kosten_papier_zinseszins.py`: Teil 2 identisch; Teil 1 weicht nur ab, weil der Papier-Test inzwischen weitergelaufen ist.
- `a_tagesreihe.csv` stimmt mit meiner Modul-Tagesreihe exakt überein (Abweichung 0,0).
- `d_module_zusatz.py` habe ich nicht erneut ausgeführt; die relevanten Teile (Hebelsuche, Hebel 3) sind in v1 nachgerechnet.

### Gegenprüfung QR-02: bestaetigt, Stufe P1

Der Befund hält der Gegenprüfung stand. Alle genannten Zahlen habe ich auf drei Wegen nachvollzogen: mit dem Befehl des Prüfers, mit einem eigenen Skript über die Module aus src/hybrid und mit einer eigenen Rechnung direkt aus den Rohkerzen ohne engine2, runner oder research.

**Kernaussage (Prüfzeitraum 01.04.2025–23.10.2026, Gruppe A, Hebel 1):**
- Ergebnis vor Gebühr, inklusive Slippage und Funding: +33,9 %.
- Volle Taker-Gebühr: 53,4 % des Kapitals (Umsatz 667,8-fach × 0,08 %).
- Netto ohne Rebate: −19,6 % (Sharpe −0,25). Mit 85 % Rebate: +25,9 % (Sharpe 0,34, entspricht +16,5 % pro Jahr). Mit 50 % Rebate: +7,2 %.
- Das Rebate muss mindestens 36,6 % betragen, damit der Prüfzeitraum nicht negativ wird. Bei doppelter Slippage steigt diese Schwelle auf 73,6 %, bei pauschal 0,05 % auf 62,1 %.
- Selbst bei Slippage null bleibt ohne Rebate nur +0,2 %. Das Signal deckt im Prüfzeitraum also gerade die volle Gebühr.
- Je Kalenderjahr ist das Ergebnis ohne Rebate 2021–2024 positiv, 2025 (−7,9 %) und 2026 (−15,5 %) negativ. In 5 von 7 Quartalen des Prüfzeitraums ist es negativ.

**Kostenannahme:**
- Die Stichprobe umfasst genau 30 Messzeitpunkte am Samstag, 14.11.2026, 15:40:22–16:39:02 UTC.
- `yubit_kosten` macht daraus einen festen Wert je Coin (Mittel 2,95 bp) für den gesamten Zeitraum 2021–2026.
- Mit 85 % Rebate wird der Prüfzeitraum bei pauschal etwa 6,8 bp Slippage null (interpoliert). Bei doppelter Annahme bleiben +6,1 %, bei dreifacher −13,7 %.

**Rebate im Bot:**
- `vorwaertstest/bot.py:245` setzt im Live-Modus `rebate = 0.0`.
- `yubit.py` kennt keinen Endpunkt für Rebate-Gutschriften.
- Im Papier-Modus ist das Rebate rechnerisch 0,85 × Gebühr (bot.py:253). Das Protokoll zeigt deshalb zwangsläufig genau 85 %; der Papier-Test kann die Zusage nicht prüfen.
- Im Repo liegt kein Beleg für die 85-%-Vereinbarung.

**Kann das Szenario eintreten?** Ja. `vorwaertstest/YUBIT_REGELN.md:19-28` hält fest, dass Yubit bei „Rebate-Arbitrage“ Rebates abziehen, Gewinne streichen und Konten sperren kann, und dass der Gewinn des Kandidaten „überwiegend aus dem Rebate“ stammt. Den Originaltext bei Yubit habe ich nicht geprüft (kein Netz). Wie wahrscheinlich das ist, bleibt ungeklärt.

**Einschränkungen, die den Befund präzisieren, aber nicht widerlegen:**
1. Die Auswirkung ist zu allgemein formuliert. In der Vorperiode 02/2020–08/2021, ebenfalls außerhalb der Entwicklung, ist der Handel auch ohne Rebate klar positiv (+160 % bei 5 bp, +171 % mit Yubit-Kosten). Die Rebate-Abhängigkeit gilt für den Prüfzeitraum ab 04/2025, also die jüngsten 19 Monate.
2. Die Kostenannahme ist weniger fragil als der Titel nahelegt. Sie enthält einen Faktor 2 als Sicherheit. Die Orderbuch-Messungen der Papier-Tests vom Sonntag, 15.11.2026 (635 Messungen, Orders um 1.500 USDT) ergeben 1,58 bp je Order gegen 2,95 bp Annahme. Beide Messungen stammen aber von einem Wochenende, enthalten keine Stressphase und keine Verzögerung zwischen Stundenschluss und Ausführung. Ob sie für fünf Jahre repräsentativ sind, bleibt ungeklärt.
3. Die Abhängigkeit ist nicht verborgen. `suche_bericht.md:21` und `:234` sowie `suche_protokoll.md:7` und `:248` nennen sie; Rebate als größerer Gewinnanteil ist das erklärte Suchziel.
4. Nebenbeobachtung: Meine Rohdaten-Rechnung weicht in der Entwicklung leicht ab (+218,0 % statt +215,6 % mit Rebate), im Prüfzeitraum ist sie auf vier Nachkommastellen identisch. Die Ursache habe ich nicht untersucht.

**Priorität: P1 ist angemessen.** Der Befund verändert die Aussage des Prüfzeitraums wesentlich, ist aber kein stiller Rechen- oder Codefehler. Im Live-Modus bucht der Bot das Rebate mit 0, und das Tagesverlust-Limit rechnet mit dem Ergebnis ohne Rebate (bot.py:195-196); beides ist vorsichtig. Derzeit läuft nur Papierhandel.

Vor echtem Geld sollte der Befund dennoch als Freigabebedingung gelten: schriftliche Rebate-Bedingungen von Yubit, Messung der tatsächlichen Gutschrift und eine längere Kostenmessung. Bei Hebel 3 entspräche der Prüfzeitraum ohne Rebate rechnerisch etwa −59 % des Kapitals.

**Evidenz:**

Alles lief aus /home/user/OdinGate-Botv134/swing-hybrid mit `.venv/bin/python -I -B`, Ausgaben nur ins Scratch-Verzeichnis und nach reports/audit/evidence/V-QR-02/. `git status` ist außerhalb von reports/audit unverändert; es gab keinen Bot-Lauf, kein Netz und keine Schlüssel. Die Belege liegen unter /home/user/OdinGate-Botv134/swing-hybrid/reports/audit/evidence/V-QR-02/.

**1. Befehl des Prüfers ausgeführt** (Ausgabe-JSON ins Scratch umgeleitet): `NUMBA_CACHE_DIR=<scratch>/numba .venv/bin/python -I -B -W ignore reports/audit/evidence/QR/d_module_zusatz.py <scratch>/qr_d.json`
- Abschnitt 4 ist identisch mit dem Befund: slip_echt mit Rebate 85/50/0 ergibt im Prüfzeitraum N = 0,2585 / 0,0715 / −0,1956 (Sharpe 0,3369 / 0,0930 / −0,2537).
- slip_2x mit 85 %: 0,0609 (0,0791). slip_5bp mit 85 %: 0,1222 (0,1591). slip_10bp mit 85 %: −0,2117.
- Zerlegung Prüfzeitraum: Umsatz 667,8274, Gebühr 0,5343, Rebate 0,4541, vor Gebühr 0,3386, Funding −0,0348.
- Entwicklung ohne Rebate: 1,1383 (Sharpe 0,4970).
- Datei: e_befehl_des_pruefers_ausgabe.txt

**2. Eigenes Modul-Skript** (a_module.py / a_module.txt)
- `R.tsmom(336)` ist identisch mit `mutationen.basis`.
- Slippage je Coin: BTC und ETH 0,5 bp (Boden), DOT 13,2 bp, ADA 6,4 bp, Mittel 2,951 bp; kein Coin fehlt.
- Identität geprüft: G − F = −0,195631 = netto_ohne.
- Rebate für ein Null-Ergebnis im Prüfzeitraum: 36,62 % (slip_echt), 73,61 % (2x), 62,13 % (5 bp), über 100 % bei 3x und 10 bp.
- slip_0 ohne Rebate: +0,0020.
- Pauschale Slippage mit Null-Ergebnis bei 85 %: 6,83 bp (interpoliert).

**3. Unabhängige Rechnung aus den Rohdaten** (b_unabhaengig.py / b_unabhaengig.txt), nur data/candles/5m, funding und die Stichprobe
- Prüfzeitraum: G = +0,3386, Umsatz 667,83, F = 0,5343.
- Rebate 0 %: N = −0,1956 (Sharpe −0,254). 50 %: +0,0715. 85 %: +0,2585 (Sharpe 0,337). Rebate für Null: 36,6 %.
- Entwicklung mit 85 %: +2,1796 (Module: 2,1564).

**4. Jahre, Quartale, Vorperiode** (c_jahre.py / c_jahre.txt)
- Ohne Rebate je Jahr: 2021 +0,314, 2022 +0,048, 2023 +0,284, 2024 +0,530, 2025 −0,079, 2026 −0,155.
- Prüfzeitraum: 5 von 7 Quartalen ohne Rebate negativ.
- Vorperiode A ohne Rebate: +1,6023 (5 bp, gleich reports/suche_runde4.json) und +1,7143 mit Yubit-Kosten.

**5. Stichprobe** data/processed/yubit_spannen_stichprobe.csv
- 16.680 Zeilen, 556 Symbole, 30 Messzeitpunkte, 2026-11-14 15:40:22 bis 16:39:02 UTC, Samstag, Abstand rund 121 s.

**6. Gespeicherte Werte** reports/suche_runde6.json, teil1.A.Pruefung
- handel = −0,0391, rebate_anteil = 1,7568, N = 0,0517, Hebel 0,2.
- Mit doppelten Kosten: handel = −0,0787.

**7. Code und Dokumente gelesen**
- src/hybrid/research.py:272-279 (`yubit_kosten`: fester Wert je Coin), :148-167 (`lauf`).
- src/hybrid/engine2.py:84-94 und 124-135 (Taker-Fill zum Open plus Slippage; Drehen zählt Schließen und Öffnen als Umsatz).
- src/hybrid/runner.py:48-57 (Gebühr × (1 − Rebate)).
- vorwaertstest/bot.py:243-253 (live: rebate = 0.0; Papier: kern.REBATE × Gebühr), :195-196 (Tageslimit auf netto_ohne_rebate).
- vorwaertstest/kern.py:9 (TAKER, REBATE = 0.0008, 0.85).
- vorwaertstest/yubit.py:19-30 (kein Rebate-Endpunkt).
- scripts/vorwaertstest_auswerten.py:13 und :36 (die Rebate-Spalte wird nur aus dem Protokoll gelesen).
- vorwaertstest/YUBIT_REGELN.md:19-33; reports/suche_protokoll.md:7-13, 226-227, 248-249; reports/suche_bericht.md:21 und :234.

**8. Papier-Daten, nur lesend** (d_papier_spannen.py / d_papier_spannen.txt)
- lauf/spannen.csv: 635 Messungen am 15.11.2026 13:21–18:58 (Sonntag), Mittel je Order 1,577 bp gegen 2,951 bp Annahme.
- protokoll.csv beider Tests: je 10 Orders, Modus papier, Rebate/Gebühr = 0,8500 (gerechnet).

**Nicht geprüft:** Yubits tatsächliche Gebührensätze und Rebate-Bedingungen (kein Netz, keine privaten Endpunkte), der Originaltext der Yubit-Regeln sowie historische Yubit-Spannen vor dem 14.11.2026.

### Gegenprüfung QR-03: bestaetigt, Stufe P1

Der Befund hält der Gegenprüfung stand; ich konnte ihn nicht widerlegen. Alle Zahlen des Prüfers sind reproduziert, und sie bleiben unter anderer Umsetzung, anderen Blocklängen, anderem Testverfahren und der tatsächlichen Auswahlregel bestehen.

**Reality Check über die Auswahl (Entwicklung, 1.325 Tage, eigene Umsetzung)**

| Menge | 0,05 % Slippage: roh / gleiche Schwankung | Yubit-Kosten: roh / gleiche Schwankung |
|---|---|---|
| 32 Einstellungen (Runden 1–3) | 0,164 / 0,471 | 0,088 / 0,296 |
| 14 Trend-Einstellungen | 0,148 / 0,207 | 0,083 / 0,126 |
| 10 Einstellungen der Runde 3 | 0,130 / 0,177 | 0,076 / 0,113 |
| Kandidat allein | 0,071 | 0,044 |

- **Robustheit:** Über Blocklängen 5 bis 60 Tage und drei Startwerte liegt der rohe p-Wert für 32 Einstellungen bei 0,11–0,21 (0,05 %) bzw. 0,056–0,113 (Yubit). Er fällt nie unter 0,05.
- **Hansens SPA-Test:** Er bestraft die offensichtlich schlechten Gegenbewegungs-Einstellungen nicht mit und ergibt trotzdem p = 0,34 bzw. 0,26.
- **Tatsächliche Auswahlregel der Runde 3** (schlechtester von vier Halbzeit-Sharpe, `scripts/suche_runde3.py:36-49`): Die beste von 10 wirkungslosen Einstellungen erreicht den Wert des Kandidaten (0,421) in 20–23 % der Ziehungen.
- **Sharpe-Unsicherheit:** Entwicklung 0,95, 90-%-Bereich 0,12 bis 1,74, t = 1,80. Prüfzeitraum 0,34, Bereich −0,81 bis +1,43, t = 0,42, 31 % der Ziehungen ≤ 0.
- **Prüfzeitraum:** Summe +25,85 %, ohne die fünf besten von 571 Tagen −25,4 %.
- **Protokoll:** Der Reality Check kommt nur in den Runden 21, 23 und 24 vor, nie für die Auswahl des Kandidaten. Die Zufallstests nur im Prüfzeitraum (80,5 % und 85,5 %) stehen so in `reports/kandidat.json` und `reports/suche_runde4.json`.

**Was den Befund abschwächt, aber nicht kippt**

- **Vorperiode fehlt im Befund:** Die bei der Auswahl unbenutzte Vorperiode 02/2020–08/2021 hat t = 1,69. Mit dem Prüfzeitraum zusammengelegt ergibt das t = 1,70 (einseitig p = 0,045) bei Yubit-Kosten und t = 1,52 (p = 0,064) bei 0,05 %. Gleich gewichtet nach Stouffer: p = 0,068 bzw. 0,10. Das ist grenzwertig und hängt am Bullenmarkt 2020/21.
- **Alle 2.457 Tage zusammen:** t = 2,47, enthält aber den Auswahlzeitraum.
- **Fünf-Tage-Argument ist einseitig:** Ohne die fünf schlechtesten Tage wären es +68 %.
- **Formulierung „mit beträchtlicher Wahrscheinlichkeit Zufall“:** Ein p-Wert ist keine Zufallswahrscheinlichkeit. Korrekt ist: Kein Vorteil lässt sich nach Berücksichtigung der Auswahl nicht auf dem 5-%-Niveau ausschließen.

**Was den Befund zusätzlich stützt**

- **Zwei Finalisten im Prüfzeitraum:** Runde 3 hat den Prüfzeitraum für `tsmom_L336` und `tsmom_L96` angesehen. L96 verlor dort −112 % (Sharpe −1,32) und schied aus. Der Kandidat ist also der Überlebende von zwei.
- **L = 336 ist eine Einzelspitze:** In der Entwicklung liegen die Nachbarn bei 0,78 (312 h), 0,65 (360 h), 0,55 (384 h) und 0,20 (432 h) gegen 0,95.

**Priorität P1 ist angemessen.** Es ist kein Rechenfehler und es fließt kein echtes Geld, und die Berichte legen die Schwäche teilweise selbst offen (`reports/suche_bericht.md:98-100`, `reports/suche_protokoll.md:136`). Deshalb nicht P0. Der Befund betrifft aber die zentrale Aussage `reports/uebergabe_fuer_dritte.md:17`, auf die sich eine Entscheidung über Hebel 3 und echtes Geld stützen würde. Deshalb nicht P2.

**Evidenz:**

Alles in temporären Verzeichnissen gerechnet; kein bestehender Code, keine Papier-Daten und keine gespeicherten Ergebnisse geändert (`git status` außerhalb von `reports/audit` leer). Belege liegen in `/home/user/OdinGate-Botv134/swing-hybrid/reports/audit/evidence/V-QR-03/`.

1. **Befehl des Prüfers selbst ausgeführt.** `reports/audit/evidence/QR/l_reality_check_kandidat.py` mit Ausgabe in mein Scratch-Verzeichnis: Ergebnis-JSON feldweise identisch mit `evidence/QR/l_reality_check_kandidat.json`. Ausgabe: `v0_befehl_des_pruefers_ausgabe.txt`.

2. **Code gelesen.**
   - `src/hybrid/mutationen.py:164-183`: `reality_check` ist ein korrekt zentrierter stationärer Bootstrap.
   - `src/hybrid/research.py`: `tsmom`, `auf_raster`, `lauf`.
   - `src/hybrid/engine2.py`.
   - `scripts/suche_stufe1.py:12-15` und `scripts/suche_runde2.py:14-15`: 30 + 10 Einstellungen, davon 32 verschieden; neu in Runde 2 sind nur `tsmom_L336` mit und ohne Filter.
   - `scripts/suche_runde3.py:36-49`: Auswahlregel.

3. **Tagesreihen erzeugt** (`v1_reihen.py`, `v1_reihen.txt`): 32 Einstellungen bei 0,05 % und Yubit-Kosten, 10 Einstellungen passiv, Vorperiode. Dazu der Kandidat ohne `engine2` mit eigener Schleife nachgerechnet:
   - Korrelation der Tagesreihen 0,9993.
   - Sharpe Entwicklung 0,935 gegen 0,946, Prüfzeitraum 0,337 gegen 0,337.
   - Die Abweichung an 22 Tagen stammt aus der Datenlücke ab 26.02.2022 (120 Stunden bei SOL, XRP, LTC), siehe `v4_abgleich_luecken.txt`.

4. **Eigene Statistik ohne Projektmodule** (`v2_statistik.py`, Ausgabe `v2_statistik.txt` und `v2_statistik.json`):
   - Reality Check mit stationärem und kreisförmigem Block-Bootstrap, Blöcke 5/10/20/40/60, drei Startwerte.
   - Hansens SPA-Test.
   - Auswahlregel der Runde 3 unter der Nullhypothese: p = 0,231 / 0,207 / 0,197 für Blöcke 10 / 20 / 40.
   - Bootstrap der Sharpe-Werte mit t-Werten (einfach und HAC mit 20 Verzögerungen): Entwicklung t = 1,80 (HAC 1,70), Prüfzeitraum 0,42, Vorperiode 1,69, Vorperiode + Prüfzeitraum 1,70, alles 2,47.
   - Prüfzeitraum ohne die k besten Tage: k = 1: +14,4 %, k = 3: −6,8 %, k = 5: −25,4 %. Ohne die fünf schlechtesten: +68,3 %.
   - Sharpe je Trendlänge in der Entwicklung bei Yubit-Kosten: L12 −1,78, L24 −1,43, L48 0,02, L96 0,52, L168 0,57, L336 0,95.

5. **Nachbar-Längen, nur Entwicklungszeitraum** (`v3_nachbarn.py`, `v3_nachbarn.txt`): Sharpe 0,57 (168 h), 0,74 (240 h), 0,74 (288 h), 0,78 (312 h), 0,95 (336 h), 0,65 (360 h), 0,55 (384 h), 0,20 (432 h), 0,28 (504 h), 0,48 (672 h).

6. **Gespeicherte Ergebnisse gelesen.**
   - `reports/suche_runde3.json`: Finalist `tsmom_L96_biasFalse` in Stufe 3 durchgefallen, Prüfzeitraum sofortige Ausführung N = −1,122, Sharpe −1,324.
   - `reports/kandidat.json`: `zufall_pruefung.perzentil` = 80,5.
   - `reports/suche_runde4.json`: `breit_zufall_pruefung.perzentil` = 85,5.
   - `reports/suche_protokoll.md`: Zeile 136; Reality Check nur in den Zeilen 1017, 1047, 1066 (Runde 21), 1179 (Runde 23) und 1258–1288 (Runde 24).
   - `reports/uebergabe_fuer_dritte.md:17`.

**Nachvollziehen** (aus `/home/user/OdinGate-Botv134/swing-hybrid`, `<scratch>` = beliebiges leeres Verzeichnis):
- `NUMBA_CACHE_DIR=<scratch>/numba .venv/bin/python -I -B -W ignore reports/audit/evidence/V-QR-03/v1_reihen.py <scratch>`
- `.venv/bin/python -I -B -W ignore reports/audit/evidence/V-QR-03/v2_statistik.py <scratch> <scratch>/aus.json`
- `NUMBA_CACHE_DIR=<scratch>/numba .venv/bin/python -I -B -W ignore reports/audit/evidence/V-QR-03/v3_nachbarn.py`

**Nicht geprüft:** Die Reihen mit passiver Ausführung hängen an der Füllannahme des Modells; ich habe sie nur für die Auswahlregel in Punkt 4 benutzt und nicht eigenständig validiert.
