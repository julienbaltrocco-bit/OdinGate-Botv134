# Alpha-Forschung Runde 1: Protokoll

Begonnen am 15.11.2026. Alles in dieser Datei wird **vor** der jeweiligen Rechnung festgelegt und als eigener Commit
gesichert; Ergebnisse folgen in späteren Commits darunter. Historische Simulation, kein echtes Geld, keine
Anlageberatung.

## 1. Ausgangslage (aus bisheriger Forschung und Audit)

- 127 Einzelhypothesen und ein Massentest mit 602 Varianten sind gerechnet. Übrig blieb nur der 14-Tage-Trend, und
  auch der ist statistisch nicht gesichert (Audit QD-01, QR-03).
- Für kurze Haltedauern liegen bereits klare negative Befunde vor:
  - Trend-Signale mit 6 bis 24 Stunden Rückblick haben schon vor Kosten keinen Wert (Diagnose Frequenz).
  - Gegenbewegung zum 24- und 72-Stunden-Mittel verliert vor Gebühren (Runde 1).
  - 43 Einstiegsarten auf Stundenkerzen (RSI, Bollinger, Ausbruch, Impuls, Volumenspitze, feste Tageszeit) mal
    7 Ausstiege: nichts besteht (Runde 11).
  - Passive Limit-Orders lassen sich mit 5-Minuten-Kerzen nicht belastbar simulieren (Runde 1, Stufe 2).
- Folgerung: Weitere Regeln, die nur aus dem Kursverlauf eines Coins bestehen, sind keine neue Forschung. Neue
  Chancen kann es nur durch **neue Information** oder einen **benennbaren Mechanismus** geben.

## 2. Forschungslücken (Schritt 2)

Bewertung: Plausibilität (wirtschaftlicher Mechanismus), Daten, Aufwand. „Neu“ heißt: in den 127 Hypothesen nicht
enthalten.

| Nr. | Richtung | Mechanismus | Daten | Aufwand | Plausibilität |
|---|---|---|---|---|---|
| L1 | Ungleichgewicht der Orderbuch-Tiefe | Kurs bewegt sich zur dünneren Seite; große Kauf- oder Verkaufswände zeigen Absichten | Binance-Archiv bookDepth ab 01/2023 (neu) | mittel | mittel bis hoch |
| L2 | Aufschlag des Kontrakts auf den Index (Premium) | Der Aufschlag wird durch Arbitrage zurückgeführt; extreme Werte zeigen einseitigen Hebel-Druck | Binance-Archiv premiumIndexKlines (neu) | gering | mittel |
| L3 | Funding-Termin | Wer Funding zahlen müsste, baut vor dem Termin ab; planbarer Zeitpunkt, dreimal täglich | vorhanden plus L2 | gering | mittel |
| L4 | Nachlauf der Altcoins hinter BTC | Preisfindung zuerst in BTC; Altcoins reagieren Minuten später | 1-Minuten-Kerzen (neu) | mittel | mittel, Kosten kritisch |
| L5 | Zwangsliquidationen (Kurssturz mit fallendem Open Interest) | Erzwungene Verkäufe drücken den Kurs kurz unter den fairen Wert | vorhanden (Open Interest stündlich) | gering | mittel |
| L6 | Wiederkehrende Tageszeit-Muster (gleiche Uhrzeit an Vortagen) | Wiederkehrende Orderströme großer Marktteilnehmer | vorhanden | gering | gering bis mittel |
| L7 | Eröffnungsspanne der Handelssitzungen (Asien, Europa, USA) | Neue Information zu Sitzungsbeginn | vorhanden | gering | gering (Ausbrüche in Runde 11 gescheitert) |
| L8 | Große Einzelaufträge und Kauf-/Verkaufsdruck je Minute | Informierte Händler handeln groß und aggressiv | Minutenkerzen mit Kaufanteil (neu); Einzeltrades 0,8 GB je Coin-Monat | mittel bis hoch | mittel |
| L9 | Lücke der CME-Futures am Wochenende | Rückkehr zum Freitagsschluss | vorhanden | gering | gering (rund 190 Ereignisse) |
| L10 | Passive Limit-Orders als Liquiditätsgeber | Entlohnung für das Stellen von Liquidität; Maker-Gebühr nach Rebate 0,006 % | echtes Yubit-Orderbuch, nur durch eigene Sammlung ab heute | hoch | hoch, aber historisch nicht prüfbar |
| L11 | Optionsdaten (Schwankungserwartung, Schiefe) | Absicherungsströme | nicht erreichbar aus dieser Umgebung | hoch | mittel |
| L12 | Termine mit Nachrichten (US-Inflation, Notenbank) | Planbare Schwankungssprünge | Terminkalender fehlt | mittel | mittel |
| L13 | Marktphasen-Umschaltung zwischen Trend und Gegenbewegung | Autokorrelation hängt von Schwankung und Volumen ab | vorhanden | mittel | gering (beide Bausteine einzeln ohne Wert) |

## 3. Auswahl (Schritt 3)

Gewählt werden die fünf Richtungen mit benennbarem Mechanismus, verfügbaren Daten und geringem bis mittlerem Aufwand:
**L1, L2, L3, L4, L5.** L1, L2 und L4 bringen neue Daten, L3 und L5 neue Mechanismen auf vorhandenen Daten.

Nicht gewählt: L6, L7, L9, L13 (reine Kursmuster, niedrige Erfolgserwartung nach Runde 11), L8 (als Mutation
vorgemerkt, falls L4 oder L1 trägt), L10 (nur mit eigener Datensammlung prüfbar, siehe Abschnitt Datensammler),
L11 und L12 (Daten fehlen).

## 4. Gemeinsame Regeln für alle Experimente

**Zeiträume.** Entwicklung E: 15.08.2021 bis 30.06.2023. Validierung V: 01.07.2023 bis 31.03.2025; V wird je
Experiment genau einmal angesehen, und nur für die vorab benannte Haupteinstellung. Für die Orderbuch-Tiefe (Daten
erst ab 2023): E 01.01.2023 bis 31.03.2024, V 01.04.2024 bis 31.03.2025. **Der Zeitraum ab 01.04.2025 wird in dieser
Runde nicht geladen und nicht angesehen.** Er ist laut Audit für Trend-Regeln nicht mehr unberührt; für die neuen
Signale bleibt er als letzte Prüfung reserviert.

**Coins.** Gruppe A (BTC, ETH, SOL, XRP, DOT, DOGE, ADA, LINK, AVAX, LTC), bei der Orderbuch-Tiefe BTC, ETH, SOL.

**Ausführung.** Signal aus abgeschlossenen Kerzen; Einstieg zum Eröffnungskurs der folgenden Kerze, Ausstieg zum
Eröffnungskurs der Kerze nach Ablauf. Stress: eine Kerze später. Alle Orders als Taker (sofort ausführbares Limit).
Maker-Ausführung wird nicht unterstellt.

**Kosten je Trade (Ein- und Ausstieg zusammen).**
- Gebühr 2 × 0,08 % = 16 Basispunkte (bp). Mit 85 % Rebate bleiben 2,4 bp, mit 50 % Rebate 8 bp.
- Slippage je Order: 2 × gemessene halbe Yubit-Spanne je Coin, mindestens 0,5 bp (wie Runde 6). Stress: doppelt.
- Funding, wenn der Trade einen Funding-Termin überspannt.
- Berichtet wird je Trade in bp: roh (reine Kursbewegung), nach Slippage und Funding (G), netto ohne Rebate,
  netto mit 50 % und mit 85 % Rebate (N85).
- Das Rebate ist eine unbestätigte Annahme. Jede Aussage „profitabel“ nennt deshalb auch das Ergebnis ohne Rebate.

**Stufe 0, Machbarkeit (nur E).** Eine Haupteinstellung je Hypothese, vorab benannt. Bestanden, wenn
(a) mindestens 300 Trades, (b) Mittel N85 > 0 mit t ≥ 2 (Tagesmittel, also nach Tagen gebündelt),
(c) Mittel roh > 0 in beiden Hälften von E, (d) N85 > 0 auch bei doppelter Slippage.
Nebeneinstellungen werden nur berichtet, nicht zur Auswahl benutzt. Wer Stufe 0 nicht besteht, ist verworfen (A).
Erlaubt ist höchstens eine begründete Mutation als neues, vorab festgelegtes Experiment.

**Stufe 1, Vollprüfung (E, dann einmal V).** Für Bestandene: Positionsführung mit Ausstiegsregeln, Kapitalverlauf,
Margin und Liquidation (Annahme: gemeinsame Margin, Erhaltungsmargin 1 % des Positionswerts, ausdrücklich nicht von
Yubit bestätigt), Startzeitpunkte, Abhängigkeit von Einzeltagen. Bestanden, wenn N85 > 0 in E und in V, t ≥ 2 über
E und V zusammen, kein Tag mehr als 20 % des Gesamtgewinns trägt und kein Starttag zur Liquidation führt.

**Einstufung.** A verworfen · B interessant, unbestätigt · C vorläufig vielversprechend (Stufe 1 in E bestanden) ·
D bereit für unabhängigen Vorwärtstest (Stufe 1 in E und V bestanden).

**Zählung.** Jedes Experiment zählt, auch gescheiterte. Jede Einstellung, deren Ergebnis ich sehe, zählt als Variante.
Obergrenze dieser Runde: 15 Experimente.

## 5. Experimente E01 bis E05, festgelegt vor der ersten Rechnung

### E01 Orderbuch-Tiefe (L1)
- **Frage:** Sagt das Verhältnis von Kauf- zu Verkaufsaufträgen nahe am Kurs die Richtung der nächsten Stunde vorher?
- **Signal:** U = (K − V) / (K + V), K und V = Auftragswert bis 1 % unter bzw. über dem Kurs, gemittelt über die
  letzten 5 Minuten. z = Abweichung von U vom eigenen 24-Stunden-Mittel in Standardabweichungen.
- **Regel (Haupteinstellung):** z ≥ +2 → Long, z ≤ −2 → Short, Haltedauer 60 Minuten, eine Position je Coin.
- **Nebeneinstellungen (nur Bericht):** Haltedauer 15 und 240 Minuten; Tiefe bis 5 % statt 1 %.
- **Erwartete Richtung vorab:** Übergewicht der Kaufaufträge → steigender Kurs.

### E02 Aufschlag des Kontrakts (L2)
- **Frage:** Kehrt der Kontraktkurs nach einem extremen Aufschlag auf den Index kurzfristig zurück?
- **Signal:** d = Aufschlag (Schluss der 5-Minuten-Kerze) minus eigenes 24-Stunden-Mittel, in Standardabweichungen.
- **Regel (Haupteinstellung):** d ≥ +2,5 → Short, d ≤ −2,5 → Long; Ausstieg, wenn d die Null kreuzt, spätestens nach
  60 Minuten.
- **Nebeneinstellungen:** Schwelle 2 und 3; Zeitlimit 15 und 240 Minuten.
- **Erwartete Richtung vorab:** hoher Aufschlag → Kontrakt fällt relativ zurück (Gegenposition).

### E03 Funding-Termin (L3)
- **Frage:** Gibt es vor oder nach dem Funding-Termin eine planbare Kursbewegung, wenn das Funding ungewöhnlich hoch ist?
- **Signal:** erwartete Funding-Rate, 65 Minuten vor dem Termin geschätzt aus dem bis dahin gemittelten Aufschlag
  (Formel der Börse: Mittel des Aufschlags plus Zinsanteil 0,01 %, begrenzt auf ±0,05 % Abstand). Kein Blick auf die
  später festgestellte Rate.
- **Regel a (Haupteinstellung):** erwartete Rate ≥ +0,03 % → Short von 60 Minuten vor bis 5 Minuten nach dem Termin
  (erhält das Funding); ≤ −0,03 % → Long.
- **Regel b:** nach dem Termin die Gegenrichtung für 60 Minuten (Erholung).
- **Nebeneinstellungen:** Schwelle 0,02 % und 0,05 %.
- Kursanteil und Funding-Anteil werden getrennt ausgewiesen. Die tatsächlich gezahlte Rate wird gebucht.

### E04 Nachlauf hinter BTC (L4)
- **Frage:** Holen Altcoins eine starke BTC-Bewegung der letzten Minuten in den folgenden Minuten nach?
- **Daten:** 1-Minuten-Kerzen. **Signal:** BTC-Rendite der letzten 5 Minuten mit Betrag ≥ 3 Standardabweichungen
  (eigene 24 Stunden). Erwartete Altcoin-Bewegung = Beta (7 Tage, 5-Minuten-Renditen) × BTC-Rendite.
- **Regel (Haupteinstellung):** Hat der Altcoin weniger als die Hälfte der erwarteten Bewegung vollzogen, Einstieg in
  BTC-Richtung, Haltedauer 15 Minuten. Neun Altcoins. Einstieg zur Eröffnung der nächsten Minute.
- **Nebeneinstellungen:** Haltedauer 5 und 60 Minuten; Schwelle 2 und 4.

### E05 Zwangsliquidationen (L5)
- **Frage:** Erholt sich der Kurs nach einem Sturz, der von einem Abbau offener Positionen begleitet ist?
- **Daten:** Stundenkerzen, Open Interest stündlich (ab 12/2021).
- **Signal:** Stundenrendite ≤ −2 Standardabweichungen (30 Tage) **und** Änderung des Open Interest in derselben
  Stunde ≤ −1,5 Standardabweichungen.
- **Regel (Haupteinstellung):** Long für 4 Stunden, Einstieg 5 Minuten nach Stundenschluss. Spiegelbildlich Short
  nach einem Anstieg mit fallendem Open Interest (Short-Squeeze).
- **Kontrolle des Mechanismus:** dieselben Kursbewegungen mit steigendem Open Interest (keine Erholung erwartet).
- **Nebeneinstellungen:** Haltedauer 1 und 12 Stunden.

## 6. Ressourcenprotokoll

Wird am Ende jedes Blocks fortgeschrieben (Abschnitt „Ressourcen“ im Bericht). Vorgabe: ein Hauptagent, keine
Subagenten, Rechnungen lokal in Python.

---

## 7. Ergebnisse E01 bis E05 (Stufe 0, nur Entwicklung, 15.11.2026)

Alle Zahlen in Basispunkten (bp) je Trade, Mittel über alle Trades. „roh“ = reine Kursbewegung, N85 = netto mit
85 % Rebate, N0 = netto ohne Rebate. t-Werte nach Tagen gebündelt. Vollständige Zahlen in `ergebnisse/e0*.json`.

| Exp. | Haupteinstellung | Trades (je Tag) | roh | N0 | N85 | t(roh) | t(N85) | Stufe 0 |
|---|---|---|---|---|---|---|---|---|
| E01 | Orderbuch-Tiefe 1 %, z ≥ 2, 60 min | 6.451 (14,2) | +0,86 | −16,8 | −3,2 | 0,8 | −3,0 | nicht bestanden |
| E02 | Aufschlag z ≥ 2,5, bis 60 min | 25.572 (37,4) | +0,25 | −21,1 | −7,5 | 0,3 | −7,3 | nicht bestanden |
| E03a | Funding-Termin, 60 min davor | 1.675 (2,5) | +2,4 (plus Funding 6,6) | −14,1 | −0,5 | 0,3 | −0,1 | nicht bestanden |
| E03b | Funding-Termin, 60 min danach | 1.681 (2,5) | −0,3 | −23,4 | −9,8 | 0,0 | −1,1 | nicht bestanden |
| E04 | Nachlauf hinter BTC, 3 σ, 15 min | 10.889 (15,9) | +1,5 | −21,0 | −7,4 | 1,0 | −4,9 | nicht bestanden |
| E05 | Sturz mit fallendem Open Interest, 4 h | 1.352 (2,5) | +9,2 | −12,3 | +1,3 | 0,6 | 0,1 | nicht bestanden |

Gesehene Einstellungen: E01 4, E02 5, E03 6, E04 5, E05 4, zusammen 24.

**Einordnung.**
- **E02 und E04: verworfen (A).** Die reine Kursbewegung nach dem Signal ist praktisch null. Der Aufschlag sagt die
  Richtung nicht vorher, und Altcoins haben eine BTC-Bewegung nach fünf Minuten bereits vollzogen.
- **E05: verworfen (A).** Die Richtung passt zur Idee (Erholung nach Sturz mit fallendem Open Interest +9 bp,
  Fortsetzung bei steigendem Open Interest −15 bp in der Kontrolle), aber beides ist nicht von Zufall zu trennen
  (t 0,6 und −1,0), und nach Kosten bleibt nichts.
- **E03: verworfen (A) in der festgelegten Form.** Beobachtung: Das eingenommene Funding (6,6 bp je Ereignis) ist
  sicher, die Kursbewegung über 65 Minuten (Streuung rund 60 bp) überdeckt es völlig. Das begründet eine Mutation mit
  kurzer Haltedauer (E06).
- **E01: Haupteinstellung verworfen, aber erster statistisch erkennbarer Effekt dieser Runde.** Nebeneinstellungen:
  Tiefe 1 % über 15 Minuten roh +1,9 bp bei t = 4,2; Tiefe 5 % über 60 Minuten roh +5,7 bp bei t = 4,7 und N85 +1,7
  (t = 1,4). Das Orderbuch enthält also Information, sie ist aber kaum größer als die Kosten. Das rechtfertigt eine
  Ursachenanalyse (E07), keine Erfolgsmeldung.

## 8. Festlegung E06 und E07 (vor der Rechnung)

### E06 Funding-Abgriff mit kurzer Haltedauer (Mutation von E03)
- **Begründung:** In E03 trägt das Funding, nicht der Kurs. Kürzere Haltedauer senkt das Kursrisiko, das Funding
  bleibt gleich. Offen ist, ob der Kurs am Termin um das Funding nachgibt.
- **Regel:** erwartete Rate (geschätzt 10 Minuten vor dem Termin aus dem bis dahin gemittelten Aufschlag) ≥ +0,03 %
  → Short, ≤ −0,03 % → Long. Einstieg 5 Minuten vor dem Termin, Ausstieg 5 Minuten danach (10 Minuten Haltedauer).
- **Coins:** nur die acht mit Slippage je Trade bis 5 bp (ohne DOT und ADA; Kostengrund, vorab bekannt).
- **Nebeneinstellungen:** Schwelle 0,02 % und 0,05 %. Hürden wie Stufe 0.
- **Einschränkung:** Gerechnet wird mit Binance-Funding. Yubit setzt eigene Raten; die Übertragbarkeit ist offen.

### E07 Ursachenanalyse Orderbuch-Tiefe (nur Entwicklung 01/2023 bis 03/2024, BTC, ETH, SOL)
Zweck: verstehen, woher der Effekt kommt, und daraus genau eine Regel für die Vollprüfung ableiten.
1. Raster: Tiefe 1, 2, 3, 4, 5 % × Haltedauer 15, 60, 240 Minuten bei z ≥ 2 (15 Einstellungen, 4 schon bekannt).
2. Schwelle z ≥ 1 und z ≥ 3 für die beste Tiefe bei 60 Minuten (2 Einstellungen).
3. Kontrolle „verkleideter Kursverlauf“: Trades getrennt nach Vorzeichen der Kursrendite der letzten 1 und 24 Stunden.
4. Stabilität: je Quartal, je Coin, Long und Short getrennt.
5. Gemeinsame Zufallsprüfung über alle 17 Einstellungen (White's Reality Check auf Tagesergebnissen N85).

**Entscheidungsregel vorab:** In die Vollprüfung (E08) geht die Einstellung mit dem höchsten t(N85), deren rohe
Kursbewegung in beiden Hälften positiv ist. Liegt der gemeinsame p-Wert über 0,10, gibt es keinen Kandidaten; das
Signal bleibt dann „interessant, unbestätigt“ (B). Die Validierung V bleibt bis E08 ungeöffnet.

---

## 9. Ergebnisse E06 und E07 (nur Entwicklung, 15.11.2026)

**E06 Funding-Abgriff kurz: verworfen (A).** 1.229 Trades, Funding +7,8 bp, aber Kurs −2,8 bp gegen die Position
(auf der Long-Seite −14 bp), N85 −0,1 bp, t = 0,0. Der Kurs gibt das Funding am Termin im Mittel zurück. Damit ist
auch die Idee „Funding kurz abgreifen“ erledigt. Gesehene Einstellungen: 3.

**E07 Orderbuch-Tiefe, Ursachenanalyse.** 17 Einstellungen, BTC/ETH/SOL, 01/2023 bis 03/2024.

| Tiefe | 15 min: roh / t | 60 min: roh / t / N85 | 240 min: roh / t / N85 |
|---|---|---|---|
| 1 % | +1,9 / 4,2 | +0,9 / 0,8 / −3,2 | −0,2 / −0,1 / −4,3 |
| 2 % | +1,8 / 4,5 | +4,0 / 3,4 / +0,1 | +6,4 / 2,1 / +2,4 |
| 3 % | +2,3 / 5,9 | +5,2 / 4,0 / +1,2 | +10,8 / 3,5 / +6,7 |
| 4 % | +2,4 / 6,5 | +4,9 / 4,1 / +0,9 | +11,0 / 3,5 / +6,9 |
| 5 % | +2,4 / 6,7 | +5,7 / 4,7 / +1,7 | +9,5 / 3,0 / +5,4 |
| 5 %, z ≥ 1 | | +2,6 / 4,3 / −1,4 | |
| 5 %, z ≥ 3 | | +9,8 / 3,8 / **+5,9** (t 2,3) | |

- Die **rohe Vorhersagekraft ist statistisch deutlich** und in beiden Hälften positiv: je tiefer das Orderbuch
  betrachtet wird und je länger die Haltedauer, desto größer. Sie wächst mit der Schwelle (z ≥ 1: 2,6 bp, z ≥ 3: 9,8 bp).
- **Nach Kosten bleibt nur mit Rebate etwas übrig**, und nur bei strenger Schwelle oder langer Haltedauer. Ohne Rebate
  ist jede Einstellung negativ (beste: −6,7 bp je Trade).
- Gemeinsame Zufallsprüfung über alle 17 Einstellungen (N85): p = 0,090; bei gleicher Schwankung gerechnet 0,106.
  Das liegt **knapp** an der vorab gesetzten Grenze von 0,10. Nach der festgelegten Regel (White, p ≤ 0,10) geht ein
  Kandidat in die Vollprüfung; das Ergebnis ist ausdrücklich grenzwertig.
- **Wahl nach Regel:** Tiefe 5 %, z ≥ 3, 60 Minuten. 1.508 Trades (3,3 je Tag über drei Coins), roh +9,8 bp, N85
  +5,9 bp, N50 +0,3 bp, N0 −7,7 bp, Gewinnquote 57 %, Profit Factor 1,24.
- Zerlegung der Wahl: SOL +17,9 bp, ETH +3,7 bp, BTC −1,2 bp (N85). Long +8,8, Short +3,1. Drei von fünf Quartalen
  positiv. 77 % der Trades laufen gegen die Kursbewegung der letzten Stunde (roh +10,7 bp), 23 % mit ihr (+6,5 bp).
  Bester Tag: 16 % des Gesamtgewinns.

Gesehene Einstellungen in E07: 17 (davon 4 aus E01). Stand: 7 Experimente, 44 Einstellungen.

## 10. Festlegung E08 und E09 (vor der Rechnung, Validierung bisher ungeöffnet)

### E08 Vollprüfung „Orderbuch-Stütze“ Version 1.0 (Stufe 1)
- **Regel, eingefroren:** U5 = (K − V) / (K + V) mit Auftragswert bis 5 % unter und über dem Kurs, 5-Minuten-Mittel;
  z gegen die eigenen 24 Stunden. z ≥ +3 → Long, z ≤ −3 → Short. Haltedauer 60 Minuten, kein Stop, eine Position je
  Coin. BTC, ETH, SOL. Einstieg zur Eröffnung der nächsten 5-Minuten-Kerze, alle Orders Taker.
- **Zeiträume:** E 02.01.2023 bis 31.03.2024, V 01.04.2024 bis 31.03.2025 (wird hier zum ersten und einzigen Mal für
  diese Regel geöffnet).
- **Bericht:** Kennzahlen je Zeitraum und Coin; doppelte Slippage; eine Kerze Verzögerung; Tagesreihe (Sharpe,
  größter Rückgang, Anteil des besten Tages, längste Verlustserie); Hebel 1, 3 und 5 mit fester Größe je Coin
  (Kapital × Hebel / 3) und Liquidation bei gemeinsamer Margin, Erhaltungsmargin 1 % (Annahme), geprüft gegen Hoch
  und Tief jeder 5-Minuten-Kerze; jeder Kalendertag als Starttag.
- **Kontrolle:** „Gegenbewegung ohne Orderbuch“: auf denselben Coins gegen die Stundenbewegung handeln, Schwelle so
  gewählt, dass in E gleich viele Trades entstehen (nicht nach Ergebnis). Zeigt, ob das Orderbuch mehr weiß als der Kurs.
- **Hürden (Abschnitt 4):** N85 > 0 in E und in V; t ≥ 2 über E und V zusammen; kein Tag über 20 % des Gewinns; kein
  Starttag mit Liquidation beim gewählten Hebel. Bestanden → D, sonst B oder A.
- Unabhängig vom Ausgang wird N0 genannt. Ist N0 negativ, trägt die Regel den Zusatz „nur mit Rebate“.

### E09 Bestätigung auf Coins, die nicht zur Auswahl dienten
- Dieselbe eingefrorene Regel auf XRP, DOGE, LINK, AVAX, LTC, ADA, DOT (Orderbuch-Tiefe wird dafür neu geladen),
  E und V.
- **Hürde:** rohe Kursbewegung > 0 mit t ≥ 2 über beide Zeiträume zusammen. N85 wird für alle sieben Coins berichtet
  und zusätzlich für die fünf mit Slippage je Trade bis 5 bp (ohne ADA und DOT), weil nur diese handelbar wären.

---

## 11. Ergebnis E08: Vollprüfung „Orderbuch-Stütze“ 1.0 (15.11.2026)

Die Validierung V wurde hier zum ersten und einzigen Mal für diese Regel geöffnet. Zahlen je Trade in bp.

| Zeitraum | Trades (je Tag) | roh | t(roh) | N0 ohne Rebate | N50 | N85 | t(N85) | Gewinnquote | Profit Factor |
|---|---|---|---|---|---|---|---|---|---|
| E 01/2023–03/2024 | 1.509 (3,3) | +9,8 | 3,8 | −7,7 | +0,3 | **+5,9** | 2,3 | 57 % | 1,24 |
| V 04/2024–03/2025 | 1.239 (3,4) | +6,8 | 2,6 | −10,7 | −2,7 | **+2,9** | 1,1 | 52 % | 1,10 |
| E und V | 2.748 (3,4) | +8,5 | 4,6 | −9,0 | −1,0 | **+4,6** | 2,5 | 55 % | 1,17 |

- **In V sind alle drei Coins positiv** (BTC +2,6, ETH +3,6, SOL +2,6 bp N85), Long und Short etwa gleich. Der hohe
  SOL-Wert aus E (+18 bp) hat sich nicht wiederholt; der Effekt in V ist etwa halb so groß wie in E.
- **Für sich allein ist V nicht gesichert** (t = 1,1 für N85). Gesichert ist die rohe Kursbewegung (t = 2,6 in V,
  4,6 über beide Zeiträume).
- **Ohne Rebate verliert die Regel** (−9,0 bp je Trade, rund −37 % pro Jahr bei Hebel 1). Sie braucht ein Rebate von
  etwa 57 %, um die Kosten zu decken.
- Stress in V: doppelte Slippage +1,4 bp, eine Kerze später +1,4 bp. Positiv, aber dünn.
- Quartale (N85): +5,8 · +8,8 · −2,7 · +20,6 · −1,3 · −6,1 · −5,6 · +11,6 · +14,1. Drei Verlustquartale in Folge 2024.
- Konto bei Hebel 1 (feste Größe, je Coin ein Drittel): E +23,7 % pro Jahr, Sharpe 2,0, größter Rückgang 6,6 %;
  V +12,1 %, Sharpe 1,1, Rückgang 13,9 %; zusammen +18,6 %, Sharpe 1,6, Rückgang 16,8 %. Längste Verlustserie 9 Trades.
- Starttage (jeder Kalendertag als Start): tiefster Kontostand bei Hebel 1 85 %, bei Hebel 3 56 %, bei Hebel 5 27 %
  des Startkapitals. Keine Liquidation in keinem Fall. Bei Hebel 5 fällt in V jeder achte Start unter die Hälfte.
  Größte Bewegung gegen einen einzelnen Trade: 12,5 %.
- **Kontrolle:** dieselbe Zahl Trades nur gegen die Stundenbewegung, ohne Orderbuch: roh +4,0 bp (t 1,0) in E und
  +4,5 bp (t 0,9) in V, N85 rund null. Etwa die Hälfte der rohen Bewegung ließe sich also auch mit einer einfachen
  Gegenbewegung erklären, die für sich nicht gesichert ist; das Orderbuch fügt den Rest hinzu.

**Hürden:** N85 > 0 in E und V: ja · t ≥ 2 über E und V: ja (2,5) · kein Tag über 20 % des Gewinns: ja (11 %) ·
keine Liquidation bei Hebel 3: ja. **Formal bestanden, Einstufung D mit Zusatz „nur mit Rebate“.**

Was das **nicht** bedeutet: kein Beweis eines dauerhaften Vorteils. Die Auswahl lag knapp an der Zufallsgrenze
(p = 0,09), V allein trägt nicht, und das Signal stammt aus dem Binance-Orderbuch, gehandelt würde bei Yubit.

## 12. Ergebnis E09: Bestätigung auf sieben Coins, die nicht zur Auswahl dienten (15.11.2026)

| Gruppe | Zeitraum | Trades | roh | t(roh) | N0 | N85 | t(N85) |
|---|---|---|---|---|---|---|---|
| alle sieben | E | 3.363 | +5,3 | 3,0 | −18,7 | −5,1 | −2,9 |
| alle sieben | V | 3.036 | +1,7 | 0,6 | −22,2 | −8,6 | −2,8 |
| alle sieben | E und V | 6.399 | +3,6 | 2,1 | −20,4 | −6,8 | −3,9 |
| fünf handelbare (ohne ADA, DOT) | E | 2.369 | +7,6 | 3,3 | −11,4 | +2,2 | 1,0 |
| fünf handelbare | V | 2.177 | +2,2 | 0,7 | −16,8 | −3,2 | −1,1 |
| fünf handelbare | E und V | 4.546 | +5,0 | 2,7 | −14,0 | −0,4 | −0,2 |

- **Vorab gesetzte Hürde (roh > 0, t ≥ 2 über beide Zeiträume): knapp bestanden** (t = 2,1). Die rohe Kursbewegung
  geht also auch auf fremden Coins in die erwartete Richtung, ist aber nur etwa halb so groß wie auf BTC, ETH, SOL.
- **Nach Kosten bleibt auf den frischen Coins nichts**, auch nicht mit 85 % Rebate (fünf handelbare: −0,4 bp).
  In V allein ist der Effekt dort praktisch null (+2,2 bp roh, t 0,7). Je Coin in V: XRP +7,6, DOGE +2,5,
  LINK +14,8, AVAX −9,3, LTC −4,6, ADA +3,5, DOT −2,5 bp roh.
- **Folgerung:** Die Information im Orderbuch ist echt, aber klein. Handelbar wäre sie höchstens auf den drei
  liquidesten Coins mit den niedrigsten Kosten, und auch dort nur mit Rebate. Die schwächere Bestätigung senkt das
  Vertrauen in E08. Stand: 9 Experimente, 44 Einstellungen plus die eingefrorene Regel.

## 13. Festlegung E10 bis E12 (vor der Rechnung)

### E10 Ausstiegs-Engine (nur Entwicklung, BTC/ETH/SOL, Einstiege unverändert wie Version 1.0)
σ = Schwankung der 60-Minuten-Rendite über die letzten 24 Stunden, bekannt beim Einstieg.

| Variante | Ausstieg |
|---|---|
| X0 | Basis: nach 60 Minuten |
| X1, X2 | nach 120 bzw. 240 Minuten |
| X3 | Signal-Ausstieg: sobald z unter 1 fällt, spätestens nach 240 Minuten |
| X4 | fester Stop bei 2 σ gegen die Position, sonst 240 Minuten |
| X5 | nachgezogener Stop mit Abstand 1,5 σ vom besten Kurs, sonst 240 Minuten |
| X6 | nachgezogenes Gewinnziel: ab 1 σ Gewinn Stop 0,5 σ hinter dem besten Kurs, sonst 240 Minuten |
| X7 | Break-even: ab 1 σ Gewinn Stop auf den Einstiegskurs, sonst 240 Minuten |

Stops sind Market-Orders: geprüft gegen Hoch und Tief jeder 5-Minuten-Kerze, Ausführung zum Stopkurs, bei Kurslücke
zum schlechteren Eröffnungskurs, zuzüglich Slippage. Der nachgezogene Stop kennt nur frühere Kerzen.
**Entscheidungsregel:** Eine Variante ersetzt die Basis nur, wenn ihr Vorsprung in der Tagesreihe N85 die gemeinsame
Zufallsprüfung über alle sieben Varianten besteht (p ≤ 0,10) und beide Hälften positiv sind. Nur dann wird sie
einmal in V gegen die Basis geprüft. Sonst bleibt X0.

### E11 Kombination mit dem bisherigen 14-Tage-Trend (beschreibend, 01/2023 bis 03/2025)
Korrelation der Tagesergebnisse, Kennzahlen einzeln und als Mischung mit gleichem Risiko, mit und ohne Rebate.
Keine Auswahl, keine Hürde. Der Trend wird mit dem vorhandenen Rechenkern unverändert gerechnet.

### E12 Marktphasen (beschreibend, nur Entwicklung)
Trades der Version 1.0 getrennt nach Schwankung der letzten 24 Stunden (Drittel, eingeordnet nur in vergangene
90 Tage), nach Richtung des 14-Tage-Trends und nach Tageszeit. Keine Auswahl; ein Filter wäre eine neue Regel für
eine spätere Runde.

---

## 14. Ergebnisse E10 bis E12 (15.11.2026)

### E10 Ausstiegs-Engine (nur Entwicklung)

| Variante | Trades | Haltedauer | roh | N0 | N85 | t(N85) | Gewinnquote | pro Jahr (Hebel 1) | Sharpe | Rückgang | Anteil Stops |
|---|---|---|---|---|---|---|---|---|---|---|---|
| X0 Basis 60 min | 1.508 | 60 min | +9,8 | −7,7 | +5,9 | 2,3 | 57 % | 23,7 % | 2,0 | 6,6 % | – |
| X1 120 min | 1.166 | 120 min | +12,2 | −5,3 | +8,3 | 2,0 | 56 % | 25,8 % | 1,9 | 10,2 % | – |
| X2 240 min | 968 | 240 min | +8,6 | −9,0 | +4,6 | 0,8 | 56 % | 12,0 % | 0,7 | 16,1 % | – |
| **X3 Signal-Ausstieg** | 1.112 | 128 min | **+19,2** | **+1,7** | **+15,3** | 3,7 | 64 % | 45,5 % | 3,3 | 7,8 % | – |
| X4 fester Stop 2 σ | 1.227 | 177 min | +17,2 | −0,4 | +13,2 | 3,3 | 50 % | 43,4 % | 3,2 | 8,5 % | 43 % |
| X5 nachgezogener Stop | 1.876 | 75 min | +7,4 | −10,1 | +3,5 | 1,6 | 40 % | 17,6 % | 1,4 | 9,4 % | 91 % |
| X6 nachgezogenes Gewinnziel | 1.303 | 107 min | +9,3 | −8,2 | +5,4 | 1,5 | 74 % | 18,9 % | 1,4 | 11,3 % | 73 % |
| X7 Break-even | 1.178 | 171 min | +8,4 | −9,1 | +4,5 | 1,0 | 32 % | 14,0 % | 0,9 | 12,7 % | 45 % |

- **Nachgezogene Stops und Gewinnziele (X5, X6, X7) verschlechtern das Ergebnis.** Sie erhöhen die Gewinnquote (X6:
  74 %) oder senken sie stark (X7: 32 %), aber nicht den Ertrag. Das ist dieselbe Erfahrung wie in Runde 20 und 24.
- **Zwei Varianten sind in der Entwicklung klar besser:** der Signal-Ausstieg (X3: halten, solange das Übergewicht
  im Orderbuch besteht) und der feste Stop (X4). Beide begrenzen die Verlierer, die bei reiner Zeitsteuerung
  weiterlaufen.
- Zufallsprüfung über die sieben Varianten gegen die Basis: beste X3, Vorsprung 21,8 Punkte pro Jahr,
  Zufallsschwelle 22,2, **p = 0,053**. Nach der vorab gesetzten Regel (p ≤ 0,10, beide Hälften positiv: +14,6 und
  +16,1 bp) geht X3 einmal in die Validierung (E13). Auch das ist knapp.

### E12 Marktphasen (nur Entwicklung, beschreibend)
- Nach Schwankung: niedrig +1,2 bp N85 · mittel +3,6 · **hoch +12,9** (t 2,5).
- Nach 14-Tage-Trend: mit dem Trend +6,0, gegen den Trend +5,9. Kein Unterschied.
- Nach Tageszeit (UTC): **0–8 Uhr +14,5** (t 3,6) · 8–16 Uhr −1,0 · 16–24 Uhr +6,5.
- Keine Auswahl daraus. Ein Filter auf hohe Schwankung wäre eine neue, eigens festzulegende Regel.

### E11 Kombination mit dem 14-Tage-Trend (01/2023 bis 03/2025, beschreibend)
- Korrelation der Tagesergebnisse: **−0,03**. Die beiden Regeln verdienen und verlieren unabhängig voneinander.
- Mit Rebate, Hebel 1: Orderbuch-Regel Sharpe 1,6 · Trend Sharpe 1,0 (größter Rückgang 51 % des Startkapitals) ·
  Mischung mit gleichem Risiko Sharpe 1,9. Dafür müsste die Orderbuch-Regel aber mit Hebel 5,5 laufen, mehr als die
  Obergrenze von 5.
- Ohne Rebate: Orderbuch-Regel −37 % pro Jahr, die Mischung negativ. Die Ergänzung funktioniert nur mit Rebate.

Stand: 12 Experimente, 52 Einstellungen.

## 15. Festlegung E13 (vor der Rechnung): Version 1.1 in der Validierung

- **Version 1.1, eingefroren:** Einstieg wie 1.0 (z ≥ 3 bzw. ≤ −3). Ausstieg, sobald z unter 1 fällt (Long) bzw.
  über −1 steigt (Short), geprüft am Schluss jeder 5-Minuten-Kerze, spätestens nach 240 Minuten. Kein Stop.
- **Einmalige Prüfung in V** (01.04.2024 bis 31.03.2025) auf BTC, ETH, SOL, im Vergleich mit Version 1.0.
- **Hürden:** N85 > 0 in V · N85 je Tag in V höher als bei Version 1.0 · N85 > 0 bei doppelter Slippage und bei
  einer Kerze Verzögerung · kein Starttag mit Liquidation bei Hebel 3.
- Besteht 1.1, ersetzt sie 1.0 als Kandidat. Besteht sie nicht, bleibt 1.0, und 1.1 gilt als Überanpassung.
- Zusätzlich berichtet (ohne Hürde): dieselbe Version auf den fünf handelbaren frischen Coins in E und V.
- Danach endet die Runde (13 Experimente). Der Zeitraum ab 04/2025 bleibt ungeöffnet.

---

## 16. Ergebnis E13: Version 1.1 in der Validierung (15.11.2026)

| Version | Zeitraum | Trades (je Tag) | Haltedauer | roh | N0 | N50 | N85 | t(N85) | pro Jahr, Hebel 1 | Sharpe | Rückgang |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1.1 | E | 1.113 (2,5) | 128 min | +19,2 | +1,7 | +9,7 | +15,3 | 3,7 | 45,5 % | 3,3 | 7,8 % |
| 1.1 | **V** | 919 (2,5) | 128 min | +8,3 | −9,2 | −1,2 | **+4,4** | 1,1 | 13,6 % | 1,1 | 13,6 % |
| 1.0 | E | 1.509 (3,3) | 60 min | +9,8 | −7,7 | +0,3 | +5,9 | 2,3 | 23,7 % | 2,0 | 6,6 % |
| 1.0 | **V** | 1.239 (3,4) | 60 min | +6,8 | −10,7 | −2,7 | **+2,9** | 1,1 | 12,1 % | 1,1 | 13,9 % |

- **Hürden formal bestanden:** N85 in V positiv (+4,4 bp), je Tag etwas besser als 1.0 (13,6 gegen 12,1 % pro Jahr),
  positiv bei doppelter Slippage (+2,9 bp) und bei einer Kerze Verzögerung (+0,9 bp), keine Liquidation bei Hebel 3.
- **Der große Vorsprung aus der Entwicklung hat sich nicht bestätigt.** In E war 1.1 fast dreimal so gut wie 1.0
  (15,3 gegen 5,9 bp), in V kaum besser (4,4 gegen 2,9 bp). Der Mehrwert des Signal-Ausstiegs war also überwiegend
  Anpassung an die Entwicklungsdaten. Ohne Rebate ist auch 1.1 in V klar negativ (−9,2 bp).
- **Empfindlich gegen Verzögerung:** fünf Minuten später handeln kostet in V rund 40 % der rohen Bewegung
  (8,3 → 4,8 bp). Das Signal verfällt schnell.
- In V je Coin: BTC +5,3, ETH +0,9, SOL +7,7 bp N85. Quartale: sechs positiv, drei negativ (2023 Q3, 2024 Q2, Q3).
- Starttage: tiefster Kontostand bei Hebel 1 86 %, Hebel 3 59 %, Hebel 5 31 % des Startkapitals; keine Liquidation.
  Größte Bewegung gegen einen Trade 13,2 %.
- Fünf frische Coins mit Version 1.1: roh +4,2 bp (t 1,7), N85 −1,2 bp. Nicht handelbar.

**Einstufung nach den vorab gesetzten Regeln:** Version 1.1 ersetzt 1.0 als Kandidat, Kategorie **D (bereit für
einen unabhängigen Vorwärtstest), Zusatz „nur mit Rebate“**. Eigene Einschätzung dazu im Bericht: Das Vertrauen ist
gering bis mittel. Gesichert ist die Vorhersagekraft des Orderbuchs vor Kosten, nicht ein Gewinn nach Kosten.

## 17. Abschluss der Runde

13 Experimente (Obergrenze 15), danach Stopp wie festgelegt. Der Zeitraum ab 01.04.2025 wurde nicht geladen und
nicht angesehen. Bericht: `bericht_runde1.md`. Register aller Strategien: `register/register.json`.

---

## 18. Übergang in den Dauerbetrieb (15.11.2026, Direktive „Continuous Autonomous Alpha Research Engine“)

- Die Obergrenze von 15 Experimenten entfällt. Die Forschung läuft in Zyklen weiter (`engine/AUFTRAG.md`).
- Der Auftraggeber hat die automatische Einrichtung rein simulierter Papier-Tests freigegeben und verlangt,
  unberührte Daten zu bewahren. Die zuvor vorgeschlagene Einmalprüfung auf 04/2025 bis 10/2026 findet deshalb nicht
  statt; dieser Zeitraum bleibt ungeöffnet.
- **Erster Durchlauf der Kette Forschung → Papier-Test: OS-1.1 „Orderbuch-Stütze“ 1.1.**
  Geprüfte Bedingungen: Regel dokumentiert und eingefroren (Prüfsumme in `papier/OS-1.1/konfiguration.json`) ·
  Mechanismus benannt · Rückrechnung reproduzierbar (E07 bis E13) · vorab gesetzte Hürden formal bestanden ·
  kein Blick in die Zukunft (Signal nur aus abgeschlossenen Kerzen; Paritätstest Runner gegen Rückrechnung auf
  echten Archivdaten grün) · Kosten mit und ohne Rebate · Margin und Liquidation im Modell · aktuelle Datenquelle
  vorhanden (Binance-Archiv, ein Tag Verzug) · 13 neue Softwaretests grün.
- **Kennzeichnung:** formal bestanden, schwach belegt, nur mit Rebate positiv. Art: Schattentest, keine Füllungen
  bei Yubit. Start 16.11.2026 00:00 UTC, 5.000 $ Papier-Kapital, Hebel 3. Plan mit Erfolgs- und Abbruchkriterien:
  `papier/OS-1.1/plan.md`.

---

## 19. Strategie-Fabrik: Festlegung vor der ersten Massenrechnung (15.11.2026)

Auftrag vom 15.11.2026 („Massive Parallel Alpha Discovery Engine“): sehr viele Strategiekandidaten automatisch
erzeugen, zurückrechnen, aussieben. Bei Zehntausenden Kandidaten entstehen zwangsläufig Zufallsgewinner; die Regeln
unten stehen deshalb fest, bevor die erste Zahl vorliegt.

**Aufbau eines Kandidaten.** Signal (Familie, Länge) · Schwelle · Richtung (mit oder gegen das Signal) · Filter
(Marktphase) · Takt (alle 5, 15 oder 60 Minuten geprüft) · Ausstieg (Haltedauer, Stop, Ziel, Nachziehen oder
Signal-Ausstieg) · Markt (BTC/ETH/SOL, alle zehn Coins, sieben Altcoins). Der Hebel ist kein eigener Kandidat: er
skaliert nur und wird erst in der Risikoprüfung bestimmt. Jeder Kandidat hat eine Kennung aus dem Hash seiner
Einstellung; gleiche Einstellungen werden nur einmal gerechnet.

**Zeiträume.**
| | Kurs-, Volumen-, Derivate-Signale | Orderbuch- und Orderfluss-Signale mit Tiefe (Daten ab 2023) |
|---|---|---|
| Training T | 15.08.2021 – 30.06.2023 | 01.01.2023 – 31.12.2023 |
| Auswahlprüfung V1 | 01.07.2023 – 30.06.2024 | 01.01.2024 – 30.06.2024 |
| Schlussprüfung V2 | 01.07.2024 – 31.03.2025 | 01.07.2024 – 31.03.2025 |
| Tresor | ab 01.04.2025: wird nicht geladen | ebenso |

T und V1 wurden in früheren Runden für andere Regeln schon gesehen. V2 ist für Orderbuch-Regeln durch E08 und E13
teilweise gesehen; Orderbuch-Kandidaten tragen deshalb den Vermerk „Schlussprüfung nicht unberührt“.
Die Massenrechnung liest nur T und V1. V2 wird erst für die eingefrorene Auswahl geöffnet, einmal.

**Ausführung und Kosten.** Signal am Schluss einer 5-Minuten-Kerze, Einstieg zur Eröffnung der nächsten, alle Orders
Taker. Gebühr 16 bp je Trade, mit 85 % Rebate 2,4 bp. Slippage 2 × gemessene halbe Yubit-Spanne je Coin und Order.
Funding gebucht. Stops gegen Hoch und Tief jeder Kerze, bei Lücke der schlechtere Eröffnungskurs. Eine Position je
Coin. Maker-Einstiege werden nicht unterstellt (höchstens als gekennzeichnete Nebenrechnung für die Auswahl).

**Trichter.**
1. **Stufe 1, Schnellsieb (T):** mindestens 200 Trades; Kursbewegung nach Slippage und Funding, vor Gebühr, im
   Mittel positiv mit t ≥ 2 (nach Tagen gebündelt). Sonst verworfen, mit Grund.
2. **Stufe 2, volle Kosten (T):** netto mit Rebate positiv mit t ≥ 2; in beiden Hälften von T positiv; auch bei
   doppelter Slippage positiv.
3. **Stufe 3, Robustheit:** in V1 netto mit Rebate positiv mit t ≥ 1; eine Kerze Verzögerung in T und V1 zusammen
   weiter positiv; mindestens die Hälfte der Nachbar-Einstellungen (gleiches Signal, benachbarte Länge oder
   Schwelle) in T positiv. Danach werden stark gleichlaufende Kandidaten (Korrelation der Tagesergebnisse über 0,8)
   zu Gruppen zusammengefasst; je Gruppe geht nur der beste nach V1 weiter.
4. **Stufe 4, Schlussprüfung (V2, einmal, Regel eingefroren):** einseitiger p-Wert der Tagesergebnisse netto mit
   Rebate; über alle Finalisten gemeinsam korrigiert (Benjamini-Hochberg, Fehlentdeckungsrate 10 %); zusätzlich
   positiv bei doppelter Slippage. Wer besteht, heißt „validiert“, nicht „bewiesen“.
5. **Stufe 5, Papier-Test:** validierte Kandidaten, höchstens einer je Gruppe, ohne Liquidation über alle Starttage
   beim gewählten Hebel (höchstens 3). Automatischer Start als Schattentest.

**Zusätzliche Prüfgrößen (Bericht, ohne eigene Hürde):** Anteil der Kandidaten, die Stufe 1 bestehen, gegen die
Zufallserwartung (rund 2,3 %); White's Reality Check auf dem besten Kandidaten über alle gerechneten; Deflated
Sharpe Ratio mit der Zahl aller Versuche; Wahrscheinlichkeit der Überanpassung (PBO) über Zeitblöcke.

**Evolution.** Neue Varianten entstehen nur aus Kandidaten, die Stufe 2 bestanden haben (also allein aus T):
Nachbar-Längen und -Schwellen, andere Ausstiege, andere Filter, zwei Signale als gemeinsame Bedingung. V1 dient nur
als Prüfung, V2 nie zur Steuerung. Jede Variante trägt die Kennung ihrer Eltern.

**Zählung.** Erzeugt, gerechnet, verworfen (mit Grund), bestanden je Stufe werden gespeichert. Als „getestet“ gilt
ein Kandidat erst, wenn seine Rechnung abgeschlossen und gespeichert ist.
