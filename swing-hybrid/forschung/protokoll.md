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
