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

### Nachtrag zu Abschnitt 19, festgelegt nach der ersten Generation und vor Stufe 3 und vor Öffnung von V2 (15.11.2026)

Beobachtung aus Generation 1 (nur T und V1): Viele Überlebende sind Regeln mit langer Haltedauer und Trendfiltern.
Solche Regeln können in steigenden Märkten allein dadurch verdienen, dass sie überwiegend long sind. Deshalb kommt
in Stufe 3 eine **strengere** Bedingung hinzu (eine Verschärfung vor der Schlussprüfung, keine Lockerung):

- **Marktbereinigung:** Das Tagesergebnis des Kandidaten wird auf die Tagesrendite seines Marktes (gleichgewichtetes
  Mittel seiner Coins) bezogen. Der verbleibende Ertrag (Alpha) muss über T und V1 zusammen positiv sein mit t ≥ 2.
- Zusätzlich berichtet (ohne Hürde): bei der Überanpassungsprüfung der Anteil der Aufteilungen, in denen der im
  einen Teil beste Kandidat im anderen Teil verliert. Die reine PBO-Zahl ist hier wenig aussagekräftig, weil die
  meisten Kandidaten schon an den Kosten scheitern und „besser als der mittlere Kandidat“ deshalb leicht ist.
- **Auslegung der Nachbar-Regel für Varianten mit Bestätigungssignal (vor Stufe 3 festgelegt):** Solche Varianten
  haben keine Geschwister mit anderer Länge oder Schwelle. Als Nachbarn gelten deshalb ihre Eltern-Regel ohne
  Bestätigung und deren Nachbarn.

### Zweiter Nachtrag zu Abschnitt 19 (16.11.2026): Befunde der unabhängigen Gegenprüfung, festgelegt vor Öffnung von V2

Drei unabhängige Prüfer haben Simulator, Buchung und Statistik mit eigenem Code nachgerechnet (Belege unter
`fabrik/pruefung/`). Kein Blick in die Zukunft gefunden; 656 Kandidaten und 16 Einzelfälle stimmen mit der eigenen
Nachrechnung überein. Gefunden und vor der Schlussprüfung behoben:

1. **Verzögerungstest (Fehler):** Beim Stress „eine Kerze später“ kam der Signal-Ausstieg zwei Kerzen später. 148
   Urteile der Stufe 3 wären gekippt. Behoben, Test ergänzt.
2. **Kosten in bewegtem Markt (ernster Einwand, kein Rechenfehler):** Die Finalisten des ersten Laufs handeln
   überwiegend direkt nach heftigen Kerzen (mittlere Spanne der Signalkerze 128 bp; 82 % des Ergebnisses nach Kerzen
   mit über 100 bp Spanne). Die angesetzte Slippage stammt aus einer ruhigen Stichprobe und beträgt dort nur rund
   2 % der Spanne. **Verschärfung, festgelegt vor V2:** Als Kosten in bewegtem Markt gilt je Order das Größere aus
   der gemessenen Yubit-Slippage und **5 % der Spanne (Hoch minus Tief) der letzten Kerze vor der Order**. Das ist
   eine Annahme, bis Yubit-Spannen in bewegten Phasen gemessen sind.
   - Stufe 3 zusätzlich: netto mit Rebate unter diesen Kosten in T **und** in V1 positiv.
   - Stufe 4: p-Wert und „validiert“ werden mit diesen Kosten gerechnet; der Stress ist das Doppelte (10 %). Das
     Ergebnis mit der einfachen Slippage wird nur zusätzlich berichtet.
3. **Datenlücken:** Bei SOL, XRP und LTC fehlen fünf Tage (02/2022, 04/2022). Jetzt: kein Einstieg, wenn die
   Einstiegskerze fehlt oder in den letzten sieben Tagen Kerzen fehlten.
4. **Teiler bei BTC als Leitmarkt:** Nutzt auch das Bestätigungssignal BTC als Leitmarkt, zählt BTC nicht mehr als
   gehandelter Coin.
5. **Marktbereinigung:** richtig gerechnet, aber fast wirkungslos (4 von 4.269 verworfen, mittleres Beta −0,02).
   Sie bleibt als Bedingung, ist aber keine wirksame Verschärfung.

Wegen 1, 3 und 4 werden beide Generationen vollständig neu gerechnet (rund acht Minuten Rechenzeit). Der erste Lauf
(„Lauf A“: 522.360 Kandidaten, 11.029 nach Stufe 2, 4.265 robust, 1.327 Finalisten) wird nicht weiterverwendet;
V2 wurde für ihn nicht geöffnet.

### Dritter Nachtrag zu Abschnitt 19 (16.11.2026): Befunde des Statistik-Prüfers, festgelegt vor Öffnung von V2

1. **Zufallsprüfung (Reality Check) war falsch gebildet:** beobachtete Größe und Bootstrap-Größe nutzten verschiedene
   Streuungen; die zuvor genannten p-Werte (0,39 und 0,17) gelten nicht. Behoben (Streuung derselben Stichprobe). Die
   Prüfung läuft jetzt nur über Generation 1, die ohne Auswahl erzeugte Grundmenge.
2. **„Anteil über Zufall“:** wird nur noch für Generation 1 ausgewiesen. Generation 2 stammt von Gewinnern des
   Trainings ab und wird auf demselben Training gemessen; ihr Anteil ist kein Beleg.
3. **Die Stufen 1 bis 3 begrenzen Zufallstreffer kaum.** Rein zufällig wären allein aus Generation 1 je nach Annahme
   rund 50 bis 1.000 „robuste“ Kandidaten zu erwarten. Die Zahl der Finalisten ist deshalb kein Beleg. Gegen Zufall
   schützt allein die Schlussprüfung. Die Finalisten sind zudem wenige verschiedene Einstiegsregeln in vielen
   Spielarten; falsche Treffer kämen gebündelt. **Verschärfung:** In der Schlussprüfung wird zusätzlich die strengere
   Korrektur nach Benjamini-Yekutieli gerechnet (gilt bei beliebig abhängigen Kandidaten). Validierte Kandidaten
   zählen je Einstiegsregel als eine Entdeckung. **Papier-Tests gibt es nur für Kandidaten, die auch die strengere
   Korrektur bestehen, höchstens einen je Einstiegsregel.**
4. **Stress im Kostenmodell für bewegten Markt:** war nicht das Doppelte. Jetzt das Doppelte der vollen Slippage.
5. **Marktbereinigung:** nimmt jetzt auch die Marktrendite des Folgetags auf (Trades laufen bis zwölf Stunden).
6. **Deflated Sharpe Ratio:** war angekündigt, aber nicht gerechnet. Jetzt in der Statistik enthalten.
7. **Mehrere Zyklen:** Sperre der Schlussprüfung nach Kennung statt nach Kennung und Generation; frühere Finalisten
   bleiben Vertreter ihrer Gruppen; schon gerechnete Einstellungen werden nicht doppelt gespeichert.

Wegen 5 wird Stufe 3 noch einmal gerechnet (V2 bleibt bis dahin geschlossen).

---

## 20. Ergebnis der Strategie-Fabrik, Generationen 1 und 2 (16.11.2026)

**Gerechnet.** Lauf A (vor den Korrekturen der Gegenprüfung, verworfen): 522.360 Kandidaten. Lauf B (maßgeblich):
522.660 Kandidaten, davon Generation 1 mit 340.200 (63 Signale × 3 Schwellen × 2 Richtungen × 10 Filter × 3 Takte ×
10 Ausstiege × 3 Märkte) und Generation 2 mit 182.460 (Evolution aus den 300 besten Einstiegsregeln des Trainings).
Durchsatz: rund 64.000 Kandidaten je Minute auf vier Kernen, das sind rund 3.500 Coin-Rückrechnungen je Sekunde.

**Trichter (Lauf B).**

| Stufe | übrig | verworfen, häufigster Grund |
|---|---|---|
| erzeugt und gerechnet | 522.660 | |
| mindestens 200 Trades im Training | 419.508 | 103.152 mit zu wenigen Trades |
| Stufe 1: Vorteil vor Gebühr | 18.392 | 401.116 ohne Brutto-Vorteil |
| Stufe 2: nach vollen Kosten | 10.856 | 7.536 (netto nicht gesichert, eine Hälfte negativ, doppelte Slippage) |
| Stufe 3: robust | 3.662 | 6.102 in V1 nicht positiv genug · 784 Verzögerung · 220 Kosten in bewegtem Markt · 84 Nachbarn · 4 Markt |
| Finalisten (eine je Gruppe) | 1.199 | |
| Stufe 4: Schlussprüfung V2 | **0** | |

**Zufallsprüfungen im Training (nur Generation 1).** Anteil mit Vorteil vor Gebühr: 1,2 % (Kurs-Signale) und 1,8 %
(Orderbuch-Tiefe); zufällig wären je nach Annahme 0,5 bis 2,8 % zu erwarten. Bester t-Wert 4,6 bzw. 3,7; der
Reality Check ergibt p = 0,98 bzw. 0,82, die Deflated Sharpe Ratio 0,00. Im Training hebt sich also nichts vom
Zufall ab.

**Schlussprüfung V2 (01.07.2024 bis 31.03.2025, einmal geöffnet am 16.11.2026, 00:48 UTC).**
- Von 1.199 Finalisten sind 521 (43 %) netto mit Rebate positiv. Median je Trade: Training +28,9 bp, Auswahlprüfung
  +24,9 bp, **Schlussprüfung −2,5 bp**.
- p-Wert unter 5 %: **60**. Rein zufällig zu erwarten: **60**.
- Kleinster p-Wert 0,0003 (Orderbuch-Tiefe 3 %, hohe Schwankung, Signal-Ausstieg, BTC/ETH/SOL); nötig wären unter
  0,00008. **Benjamini-Hochberg besteht keiner, validiert ist keiner.**
- Ohne Rebate positiv: 240 von 1.199. Mit der einfachen (ruhigen) Slippage wären 696 positiv; die Annahme zu den
  Kosten in bewegtem Markt entscheidet also über einen großen Teil.
- Nach Familie (Finalisten / positiv / p unter 5 %): Momentum 524 / 44 % / 28 · Mean Reversion 294 / 49 % / 14 ·
  Cross-Asset 163 / 29 % / 1 · Mikrostruktur 152 / 49 % / 15 · Derivate 37 / 59 % / 2 · Volatilität 29 / 0 % / 0.

**Folgen.**
- Kein Kandidat erfüllt die Bedingungen für einen Papier-Test. Es wurde **kein neuer Papier-Test gestartet**.
- V2 ist für diese 1.199 Regeln verbraucht. Der Tresor ab 04/2025 ist weiterhin ungeöffnet.
- Auffällig bleibt allein die Orderbuch-Tiefe: Sie stellt den besten Finalisten und 15 der 60 kleinsten p-Werte bei
  nur 13 % der Finalisten. Das reicht nicht für eine Validierung, deckt sich aber mit E07 bis E13. Diese Idee läuft
  bereits als Papier-Test OS-1.1.
- Lehre für die nächsten Zyklen: Mehr Kandidaten machen die Suche nicht besser, sondern die Schlussprüfung
  schwerer. Neue Generationen sollen klein sein und neue Information bringen (siehe `engine/hypothesen.json`, H15 bis H17).

---

## 21. Festlegung E16 (vor der Rechnung): Yubit-Kosten in bewegten Minuten (H15)

- **Frage:** Wie hängen die tatsächlich gemessenen Yubit-Kosten einer Order von der Bewegung der letzten 5-Minuten-Kerze
  ab? Trägt die Annahme „5 % der Kerzenspanne je Order“, ist sie zu streng oder zu milde?
- **Daten:** Messungen des bestehenden Papier-Bots (Test 1, nur gelesen): je Lauf und Coin die Kosten für einen Kauf
  und einen Verkauf über 1.500 $ gegen die Mitte des Orderbuchs. Dazu Yubit-5-Minuten-Kerzen derselben Zeit.
- **Auswertung:** je Messung die Spanne (Hoch minus Tief) der letzten abgeschlossenen Yubit-Kerze; Kosten je Order
  nach Fünfteln dieser Spanne; Anteil der Messungen, in denen die Kosten über 5 % der Spanne liegen.
- **Einschränkung vorab:** Die Messreihe ist erst wenige Stunden alt und stammt von einem ruhigen Sonntag. Sie kann
  die Annahme für heftige Kerzen (über 100 bp Spanne) voraussichtlich noch nicht prüfen; berichtet wird, wie viele
  solche Kerzen überhaupt vorkommen. Keine Hürde, keine Auswahl.

---

## 22. Ergebnis E16 und Zusatzangabe zur Schlussprüfung (16.11.2026)

**E16 Yubit-Kosten in bewegten Minuten.** 1.264 Messungen des Papier-Bots (15.11. 13:21 bis 16.11. 00:47 UTC, zehn
Coins, Order über 1.500 $), bezogen auf die Spanne der letzten abgeschlossenen Yubit-5-Minuten-Kerze.
- Kosten je Order nach Fünfteln der Kerzenspanne (Mittel 15 / 23 / 28 / 37 / 55 bp): 1,1 / 1,0 / 2,4 / 1,9 / 1,3 bp.
  Die Kosten steigen mit der Spanne nicht erkennbar (Korrelation 0,05).
- Im bewegtesten Fünftel betragen sie 2,4 % der Spanne. Die Annahme von 5 % wäre dort zu streng.
- **Grenze der Aussage:** nur zwei Kerzen über 100 bp, größte 110 bp, ein ruhiger Sonntag. Für die heftigen Kerzen,
  nach denen die Finalisten handeln, gibt es noch keine Messung. Die Reihe wächst täglich.

**Zusatzangabe: Schlussprüfung mit der einfachen Slippage** (im zweiten Nachtrag als reine Zusatzangabe vorgesehen;
ändert keinen Status; `fabrik/ergebnisse/schlusspruefung_einfache_slippage.json`).
- 696 von 1.199 positiv; p unter 5 %: 123 bei 60 zufällig erwarteten.
- Benjamini-Hochberg besteht **ein** Kandidat (`24332e4d3769`, Orderbuch-Tiefe 3 %, hohe Schwankung, stündlich
  geprüft, Signal-Ausstieg, BTC/ETH/SOL; p = 0,00004). Die strengere Korrektur besteht auch er nicht.
- Das negative Ergebnis der Schlussprüfung hängt also teilweise an der Kostenannahme für bewegte Märkte. Mit der
  strengen Annahme (vorab als maßgeblich festgelegt) ist nichts validiert; mit der milden gäbe es einen Treffer und
  doppelt so viele kleine p-Werte wie zufällig.

**Entscheidung, offen als Abweichung von der eigenen Regel benannt.** Nach dem dritten Nachtrag gibt es Papier-Tests
nur für Kandidaten, die die strenge Korrektur bestehen. Das tut keiner. Der Kandidat `24332e4d3769` ist aber in
beiden Kostenmodellen der beste von 1.199, stammt aus der einzigen Familie mit wiederholten Hinweisen (E07 bis E13),
und nur neue Daten können klären, ob etwas daran ist. Er wird deshalb als **Beobachtungstest** gestartet, mit dem
Vermerk „nicht validiert“ im Namen, in der Übersicht und im Register. Das ist keine Validierung und kein Erfolg der
Fabrik; es ist die Messung, die als einzige noch unabhängige Evidenz liefern kann. Weitere Beobachtungstests aus
dieser Charge gibt es nicht.

**Korrektur am selben Tag, vor dem ersten Lauf:** Der Beobachtungstest wird **nicht** selbstständig gestartet. Die
Freigabe des Auftraggebers für automatische Papier-Tests gilt für Kandidaten, die die vorab festgelegten Kriterien
erfüllen; dieser erfüllt sie nicht. Ein Start aus eigener Entscheidung wäre eine nachträgliche Lockerung der eigenen
Regel. Der Test `B-24332e4d` ist deshalb nur vorbereitet: Regel und Code eingefroren am 16.11.2026 (Prüfsumme),
Wertung ab 17.11.2026 00:00 UTC, Status „pausiert“. Er läuft erst, wenn der Auftraggeber ihn ausdrücklich freigibt
(`steuerung.json` auf „laufend“). Weil jeder Lauf vollständig neu rechnet und die Regel vor dem Startdatum im
Repository festgeschrieben ist, geht durch eine spätere Freigabe nichts verloren und nichts wird nachträglich
angepasst. Risiko in der Rückrechnung bei Hebel 3: tiefster Kontostand 62 %, an 6 % der Starttage unter der
Abbruchgrenze von 70 %, keine Liquidation.

---

## 23. Festlegung Generation 3 (vor der Rechnung, 16.11.2026): wiederkehrende Tageszeit-Muster (H10)

- **Mechanismus:** Große Teilnehmer handeln in festen Zeitfenstern (Fonds-Umschichtungen, Absicherung zu festen
  Terminen, zeitgesteuerte Ausführungsprogramme). Ein Coin, der zu einer bestimmten Uhrzeit an den Vortagen im Mittel
  gestiegen ist, könnte im selben Zeitfenster heute wieder steigen. Für Aktien und Kryptowährungen in der Literatur
  beschrieben; in der Fabrik bisher nicht geprüft (kein bisheriges Signal kennt die Uhrzeit der Vortage).
- **Neue Signale (sechs, ans Ende von `fabrik/signale.py`, Familie „Saisonalität“):**
  `tagzeit_L_N` = mittlere Rendite des jetzt beginnenden Zeitfensters (die nächsten L Kerzen: 15 oder 60 Minuten) an den
  letzten N Vortagen (7 oder 28), jeweils geteilt durch die damalige Schwankung. `tagzeitrel_L_28` = derselbe Wert
  abzüglich des Durchschnitts der zehn Coins (Muster des einzelnen Coins, nicht des Gesamtmarkts).
  Jeder Wert nutzt nur Kurse, die mindestens 23 Stunden alt sind.
- **Kandidaten (108, bewusst wenige):** 6 Signale × Schwellen 1,5 / 2,5 / 3,5 × mit oder gegen das Signal × kein Filter ×
  3 Märkte. Takt und Ausstieg folgen dem Zeitfenster und sind keine freie Wahl: 15-Minuten-Fenster wird alle
  15 Minuten geprüft und 15 Minuten gehalten, 60-Minuten-Fenster stündlich geprüft und 60 Minuten gehalten.
- **Prüfung:** Trichter, Zeiträume, Kosten und Hürden aus Abschnitt 19 samt Nachträgen unverändert. Neue Finalisten
  gehen einmal in die Schlussprüfung; die Korrektur rechnet über alle 1.199 bisherigen plus die neuen Finalisten.
- **Erwartung vorab:** Solche Effekte sind klein (wenige bp je Fenster), die Kosten je Trade liegen bei rund 5 bp.
  Wahrscheinlich scheitert die Generation an Stufe 1 oder 2. Kein Nachbessern mit weiteren Filtern oder Haltedauern.
- **Hinweis zum Ablauf in frischer Sitzung:** Die lokale Datenbank enthält nur die neue Generation. `trichter.py
  statistik` wertet allein Generation 1 aus und wird deshalb nicht neu gerechnet (`statistik.json` bleibt unverändert).
  Vor `bericht.py` werden die früheren Kandidaten aus `kandidaten.parquet` in die lokale Datenbank zurückgelesen,
  damit Zählung und Archiv vollständig bleiben.

---

## 24. Ergebnis Generation 3: wiederkehrende Tageszeit-Muster (16.11.2026)

**Gerechnet:** 108 Kandidaten (36 Einstiegsregeln × 3 Märkte), eine Sekunde Rechenzeit. Vorher Kontrolle der frischen
Umgebung: 960 Kandidaten der Generation 1 nachgerechnet, deckungsgleich mit dem Archiv (Abweichung nur Rundung).

| Stufe | übrig |
|---|---|
| erzeugt und gerechnet | 108 |
| mindestens 200 Trades im Training | 98 |
| Stufe 1: Vorteil vor Gebühr (t ≥ 2) | **0** |

- Nur 12 von 98 Kandidaten sind im Training vor Gebühr überhaupt positiv; der beste erreicht t = 1,7 (60-Minuten-Fenster,
  7 Vortage, BTC/ETH/SOL: +7,0 bp vor Gebühr im Training, −2,6 bp in der Auswahlprüfung). Median über alle: −5,4 bp je
  Trade im Training, −5,6 bp in der Auswahlprüfung.
- Beide Richtungen verlieren (mit dem Muster und dagegen). Es gibt also keinen Effekt, der nur das falsche Vorzeichen
  hätte; übrig bleibt im Wesentlichen die Slippage. Die Variante gegen den Durchschnitt der zehn Coins ist nicht besser.
- **Einstufung A (verworfen).** Keine Finalisten, keine Schlussprüfung, kein Papier-Test. H10 ist damit erledigt.

**Zum Ablauf:** Da kein Kandidat Stufe 2 erreicht hat, wurde `trichter.py stufe3` nicht ausgeführt (es hätte nur die
Zählfelder in `finalisten.json` mit Nullen überschrieben). `statistik.json` bleibt wie festgelegt unverändert.
Die Slippage je Coin kommt in frischen Sitzungen aus `fabrik/slippage_gemessen.json` (dieselben Werte wie bisher; die
Stichprobe vom 14.11.2026 liegt nicht im Repository). Siehe `engine/offene_fragen.md`.

---

## 25. Festlegung Generation 4 (vor der Rechnung, 16.11.2026): Orderbuch-Tiefe aus dem letzten Schnappschuss (H16, H07)

- **Mechanismus:** Das Tiefe-Signal verfällt schnell (frühere Messung, siehe H07: fünf Minuten Verzug kosten rund 40 %). Bisher geht das
  Mittel aller 30-Sekunden-Schnappschüsse einer 5-Minuten-Kerze ein; es ist beim Einstieg im Schnitt 2,5 Minuten alt.
  Der letzte Schnappschuss vor Kerzenschluss ist höchstens 30 Sekunden alt und enthält die jüngste Verschiebung des
  Orderbuchs. Das ist neue Information aus derselben Quelle, keine weitere Einstellung der alten Signale.
- **Neue Signale (zwei, Familie „Mikrostruktur“):** `tiefe_letzt_1` = Übergewicht der Kauf- gegenüber der Verkaufsseite
  innerhalb 1 % um den Kurs im letzten Schnappschuss, gemessen an den letzten 24 Stunden (wie `tiefe_1`, nur frischer).
  `tiefe_frisch_1` = dieses Übergewicht im letzten Schnappschuss minus Kerzenmittel (Verschiebung in den letzten Minuten).
- **Kandidaten (288):** 2 Signale × Schwellen 1,5 / 2,5 / 3,5 × mit oder gegen das Signal × Filter (keiner, hohe
  Schwankung; nach E12) × Takt (5 Minuten, 60 Minuten) × Ausstiege (60 Minuten, 240 Minuten, Signal-Ausstieg) ×
  Märkte (BTC/ETH/SOL, alle zehn Coins).
- **Prüfung:** unverändert nach Abschnitt 19 (Training 2023, Auswahlprüfung 01–06/2024). Neue Finalisten gehen einmal in
  die Schlussprüfung, Korrektur über alle bisherigen und neuen Finalisten. Vermerk wie bisher: Die Schlussprüfung ist
  für Orderbuch-Regeln nicht unberührt; ein Treffer wäre „formal bestanden“, nicht „belegt“.
- **Vergleichsgröße (nur Bericht, keine Hürde):** dieselben 144 Einstellungen mit dem alten Signal `tiefe_1` aus dem
  Archiv der Generation 1, soweit dort gerechnet. Ist das frische Signal im Training nicht besser als das alte, gilt
  die Idee als nicht bestätigt, auch wenn einzelne Kandidaten weiterkommen.

---

## 26. Ergebnis Generation 4: Orderbuch-Tiefe aus dem letzten Schnappschuss (16.11.2026)

**Gerechnet:** 288 Kandidaten (48 Einstiegsregeln × 3 Ausstiege × 2 Märkte), eine Sekunde Rechenzeit. Störungstest grün.

| Stufe | übrig |
|---|---|
| erzeugt und gerechnet | 288 |
| mindestens 200 Trades im Training | 240 |
| Stufe 1: Vorteil vor Gebühr (t ≥ 2) | **0** |

- 42 von 240 Kandidaten sind im Training vor Gebühr positiv, der beste erreicht t = 1,4. Median vor Gebühr:
  `tiefe_letzt_1` mit dem Signal −1,9 bp, dagegen −6,7 bp; `tiefe_frisch_1` in beiden Richtungen rund −4,5 bp.
- **Vergleich mit dem alten Signal (`tiefe_1`, Kerzenmittel, 102 gleiche Einstellungen aus Generation 1):** Das frische
  Signal ist im Median 0,05 bp schlechter und nur in 48 % der Paare besser. Die beiden Signale laufen zu 85 bis 95 %
  gleich. Der letzte Schnappschuss bringt also keine zusätzliche Information; die Vermutung, ein früherer Einstieg
  über frischere Daten rette den schnell verfallenden Effekt, ist auf 5-Minuten-Raster nicht bestätigt.
- Die Richtung „mit dem Signal“ auf BTC/ETH/SOL bleibt wie in allen früheren Prüfungen leicht vorn (Median vor Gebühr
  0,0 bp im Training, +5,2 bp in der Auswahlprüfung), aber weit unter den Kosten. Das ist die bekannte Spur, die als
  Papier-Test OS-1.1 bereits läuft, kein neuer Befund.
- **Einstufung A (verworfen).** Keine Finalisten, keine Schlussprüfung, kein Papier-Test. `trichter.py stufe3` wie
  bei Generation 3 nicht ausgeführt (kein Kandidat aus Stufe 2).

**Stand der Fabrik:** 523.056 Kandidaten gerechnet, 1.199 Finalisten, 0 validiert (unverändert). Die Zählung führt die
drei Größen „im Training netto positiv“ als alten Stand plus neue Generationen fort, weil das Archiv auf zwei
Nachkommastellen gerundet ist und eine Neuzählung daraus 17 Grenzfälle verlöre. `auswahl.json` ist unverändert.

**Folgerung für die nächsten Zyklen:** H07 und H16 sind in der Form „frischere Daten auf 5-Minuten-Raster“ erledigt.
Offen bleibt nur die echte 1-Minuten- oder 30-Sekunden-Ausführung (Einstieg innerhalb der Kerze); sie braucht einen
Simulator auf Minutenraster und passt nicht in den Baukasten. Ohne die Antworten in `engine/offene_fragen.md` und ohne
Messung der Yubit-Kosten in heftigen Kerzen (E16 wächst täglich) ist das die sinnvollste verbleibende Arbeit.

---

## 27. Nachkontrolle des ersten Nachtlaufs (16.11.2026, Hauptsitzung)

Der erste geplante Forschungszyklus lief von 01:43 bis 02:02 UTC ohne Fehler: ein Durchgang, keine Subagenten, nur
Dateien unter `forschung/`, keine Änderung an Papier-Tests, Tresor ungeöffnet. Beide Festlegungen (Abschnitte 23 und
25) wurden vor der jeweiligen Rechnung gesichert (Commits 01:45 und 01:58 UTC, Rechnungen 01:57 und 01:59 UTC).

**Unabhängige Nachrechnung.** Datenspeicher und Signale in der Hauptsitzung neu gebaut, die 84 Aufgaben aus dem Archiv
rekonstruiert (`fabrik/ergebnisse/aufgaben_gen3.json`, `aufgaben_gen4.json`) und alle 396 Kandidaten neu gerechnet:
gleiche Kennungen, gleicher Status bei allen 396, Kennzahlen bis auf Rundung gleich (größte Abweichung 0,03 bp). Die
gemeldeten Zahlen stimmen: Generation 3 hat 98 gültige Kandidaten, 12 vor Gebühr positiv, bester t-Wert 1,72;
Generation 4 hat 240 gültige, 42 positiv, bester t-Wert 1,40. Die 522.660 früheren Kandidaten im Archiv sind
unverändert. Tests grün (21), darunter der Störungstest über die acht neuen Signale.

**Ergänzung zum Ergebnis der Generation 4.** Zwei Kandidaten scheitern nur an der Mindestzahl von 200 Trades und
wären sonst im Training auffällig (`tiefe_frisch_1`, Schwelle 3,5, gegen das Signal, stündlich, BTC/ETH/SOL: 185 und
197 Trades, vor Gebühr +39,6 und +16,9 bp, t = 2,9 und 2,7). In der Auswahlprüfung sind beide klar negativ (−11,7 und
−12,0 bp vor Gebühr). Es ist also keine übersehene Spur; die Hürde bleibt, wie sie ist.

**Kleine Abweichung, ohne Folgen.** Der Nachtlauf rechnete mit auf drei Stellen gerundeter Slippage (die Stichprobe
lag in der frischen Sitzung nicht vor). Der Unterschied beträgt höchstens 0,0004 bp je Order. Ab jetzt steht die
Kostenbasis in voller Genauigkeit in `fabrik/slippage_gemessen.json` und ist die einzige Quelle.

**Änderungen an den Programmen (kein Einfluss auf bisherige Ergebnisse).**
- Das Archiv liegt in Teilen: `kandidaten.parquet` (Generation 1 und 2) ist eingefroren und wird nie neu geschrieben
  (Prüfsumme in `archiv_basis.json`); jede spätere Generation steht in einer eigenen kleinen Datei. Vorher hätte jede
  neue Generation die 18 MB große Datei neu ins Repository geschrieben, und in einer frischen Sitzung hätte ein
  unbedachter Aufruf das Archiv durch den Stand allein der neuen Generation ersetzt. Der Nachtlauf hat das erkannt
  und von Hand umgangen; jetzt verhindern es die Programme.
- `bericht.py` zählt immer über Archiv plus lokale Datenbank; `trichter.py statistik` und `stufe3` überschreiben in
  einer frischen Sitzung nichts mehr. Geprüft in drei Lagen (nur neue Generationen in der Datenbank, nur alte, gar
  keine Datenbank): jeweils dieselbe Zählung, 523.056 Kandidaten.
- `engine/AUFTRAG.md`: Anleitung zur Arbeitsumgebung ergänzt, Aufgabenliste wird künftig mit der Festlegung
  gesichert, Reihenfolge der nächsten sinnvollen Schritte. Die drei Fragen in `engine/offene_fragen.md` sind beantwortet.

---

## 28. Zwei Beobachtungstests, vom Auftraggeber freigegeben (16.11.2026, vor dem Anlegen festgelegt)

**Anlass.** Eine Aufschlüsselung der 1.199 Finalisten nach Signalart (nach der Schlussprüfung, also nur beschreibend)
zeigt zwei Gruppen, die sich vom Zufall abheben:
- Orderbuch-Tiefe, mit dem Signal, BTC/ETH/SOL: 97 Finalisten, 66 % in der Schlussprüfung positiv, 15 mit p unter
  5 % bei 4,9 zufällig erwarteten; gegen das Signal nur 9 % positiv. Median vor Gebühr rund +6 bp je Trade.
- `kaufdruck_48`, gegen das Signal, hohe Schwankung (nach vier Stunden einseitiger Marktorders dagegen handeln):
  acht Finalisten, Varianten einer Regel, alle in Training, Auswahl- und Schlussprüfung positiv (Schlussprüfung +6 bis
  +200 bp je Trade mit Rebate), aber nur 50 bis 120 Trades in neun Monaten bei sieben der acht; p zwischen 5 und 33 %.

**Einordnung.** Die Gruppen wurden nach Kenntnis der Ergebnisse gebildet; bei der Orderbuch-Tiefe überschneidet sich
die Schlussprüfung mit Daten der ersten Runde. Beides ist ein Hinweis, kein Beleg. Kein Kandidat ist validiert, und
aus der Schlussprüfung werden keine neuen Regeln abgeleitet. Unabhängige Evidenz liefern nur neue Daten.

**Entscheidung des Auftraggebers (16.11.2026):** Beide Muster kommen als Beobachtungstests in den Papierhandel.
Reiner Schattentest, keine Orders, eigene Konten, klar als „nicht validiert“ geführt. Tests 1 und 2 sowie OS-1.1
bleiben unverändert und werden nicht vermischt.

**Welche Regeln, festgelegt ohne Blick auf die Schlussprüfung:**
1. `B-24332e4d` (Orderbuch-Tiefe 3 %, hohe Schwankung, stündlich, Signal-Ausstieg, BTC/ETH/SOL): wie in Abschnitt 22
   vorbereitet, Regel seit 16.11. eingefroren. Er war der beste Finalist nach p-Wert; diese Wahl stammt aus der
   Schlussprüfung und ist deshalb vermerkt.
2. Kaufdruck: Unter den Finalisten mit `kaufdruck_48` wird derjenige genommen, der in der **Auswahlprüfung** das
   beste Sharpe-Verhältnis hatte (dasselbe Kriterium, nach dem die Fabrik Gruppenvertreter wählt): `dc1d27a31f5f`.
   Die Ergebnisse der Schlussprüfung spielen für diese Wahl keine Rolle. Nur dieser eine; keine weiteren Varianten.

**Bedingungen vor dem Start (sonst kein Test):** Risikoprüfung über alle Starttage ohne Liquidation und mit
Kontostand über 50 % beim gewählten Hebel (höchstens 3); der Papier-Runner muss auf einem historischen Fenster
dieselben Trades bilden wie die Rückrechnung.

**Wertung.** Start beider Tests 17.11.2026 00:00 UTC. Orderbuch-Tiefe: Zwischenwertung nach 100, Hauptwertung nach
300 Trades oder zwölf Monaten. Kaufdruck (seltene Trades, rund zehn im Monat): Zwischenwertung nach 50, Hauptwertung
nach 150 Trades oder zwölf Monaten. Erfolg heißt jeweils: netto mit Rebate im Mittel positiv; das gilt als „nicht
widerlegt“, nicht als Beweis. Abbruch bei Kontostand unter 70 % oder Liquidation im Modell. Ergebnisse dieser Tests
steuern keine Auswahl neuer Fabrik-Kandidaten.

**Nachtrag zu Abschnitt 28: Bedingungen geprüft, beide Tests angelegt (16.11.2026, 12:15 UTC).**
- `B-24332e4d` (Orderbuch-Tiefe): Parität 12 von 12 Trades gleich (Fenster 10. bis 20.06.2024); Risiko bei Hebel 3
  wie in Abschnitt 22 (tiefster Kontostand 62 %, keine Liquidation). Status „laufend“.
- `B-dc1d27a3` (Kaufdruck, Kennung `dc1d27a31f5f`, mit Bestätigung durch eine Volumenspitze, sieben Altcoins,
  alle 5 Minuten geprüft, Ausstieg nach spätestens 12 Stunden mit Ziel und Nachzug, kein Stop): Parität 19 von 19
  Trades gleich (Fenster 01.11. bis 20.12.2023; im Standardfenster lag nur ein Trade). Risiko über 1.271 Starttage
  bei Hebel 3: tiefster Kontostand 54 %, an 8,8 % der Starttage unter der Abbruchgrenze von 70 %, keine Liquidation;
  schlechtester Einzeltrade −18 %. Rund sieben Trades im Monat, in Schüben. Status „laufend“.
- Der Papier-Rechner (`fabrik/papier_fabrik.py`) kannte die zwei Datenreihen der Generation 4 nicht; ergänzt, bevor
  der zweite Test angelegt wurde. Der eingefrorene Code von `B-24332e4d` ist davon unberührt (Prüfsumme gültig).
- Voller täglicher Ablauf (`papier/tag.sh`) einmal durchgelaufen: fünf Tests, kein Fehler. Erste Trades frühestens
  am 18.11., weil die Archivdaten einen Tag Verzug haben.

---

## 29. Schattentests auf dem Trading Board (16.11.2026, auf Wunsch des Auftraggebers)

Der Auftraggeber möchte die neuen Papier-Tests auf derselben GitHub-Seite sehen wie Test 1 und 2.
- **Daten:** `papier/board.py` bündelt den Stand aller Schattentests (`OS-1.1`, `B-24332e4d`, `B-dc1d27a3` und künftige)
  und verschlüsselt ihn mit dem öffentlichen Schlüssel des Boards (`papier/board_pub.pem`, derselbe wie für Test 1
  und 2; das Passwort liegt nicht im Repository). Ergebnis: `papier/board/schattentests.enc.json`, einmal täglich nach
  dem Papier-Lauf gesichert (`papier/veroeffentlichen.sh`).
- **Seite:** Das Board liest diese eine Datei direkt aus dem Forschungszweig. In den Zweig des Bots wird dafür täglich
  nichts geschrieben; der Bot für Test 1 und 2 bleibt unberührt. Am Board selbst kommen Tabs und eine eigene Ansicht
  für Schattentests hinzu; Rechnung und Anzeige von Test 1 und 2 sind unverändert (im Browser geprüft: Anmeldung,
  Umschalten zwischen allen Tests und zurück, Handy-Breite, keine Fehler).
- **Kennzeichnung:** Beobachtungstests tragen auf dem Board die Marke „nicht validiert“.

---

## 30. Live-Fassung des Kaufdruck-Tests auf dem Server des Auftraggebers (16.11.2026, auf dessen Wunsch)

Der Auftraggeber stellt einen eigenen Server bereit (Standort Nürnberg; Binance dort live erreichbar, geprüft mit
`betrieb/server_check.sh`). Damit entfällt für Regeln, die nur Kerzen und Marktorder-Volumen brauchen, der Tag Verzug.

- **Test `L-dc1d27a3`:** Live-Fassung von `B-dc1d27a3`. Dieselbe eingefrorene Regel, derselbe Start (17.11.2026),
  dasselbe Kontomodell. Signale, Simulator und Massenlauf-Kern sind Datei für Datei identisch mit dem Schattentest;
  nur der Papier-Rechner hat einen Live-Modus (Fenster endet an der letzten vollständigen Kerze).
- **Geprüft vor der Installation:** (a) Live-Modus gegen Archiv-Modus auf 01.11. bis 21.12.2023: 19 von 19 Trades
  gleich, Abweichung 0. (b) Tag bricht mittendrin ab: alle bis dahin abgeschlossenen Trades gleich, keine Einstiege
  aus der Zukunft, ein Einstieg erscheint in der Kerze, in der er geschieht. (c) Ganzer Dienst mit nachgestellter
  Echtzeit-Schnittstelle: Abruf, Rechnung (rund 3 s je Lauf, rund 280 MB), Kontrolle, Veröffentlichung.
  Nicht hier prüfbar: der echte Binance-Abruf (aus der Forschungsumgebung gesperrt); das zeigt erst der Server.
- **Yubit-Kosten:** Bei jedem neuen Einstieg misst der Dienst am öffentlichen Yubit-Orderbuch, was die Order gekostet
  hätte (`live/yubit.py`). Der Kontostand rechnet weiter mit dem eingefrorenen Kostenmodell; die Messung steht daneben.
- **Kontrolle:** Einmal täglich rechnet der Server den Schattentest aus den Archivdaten und vergleicht die Trades.
  Maßgeblich bleibt der Schattentest; bei Abweichung gilt die Live-Fassung als fehlerhaft, bis die Ursache geklärt ist.
- **Veröffentlichung:** verschlüsselt (Schlüssel des Boards) in einen eigenen Daten-Zweig `odingate-live`, ein einziger
  Commit, der laufend ersetzt wird. Das Board zeigt die Live-Fassung im Tab des Schattentests, solange sie den
  neueren Datenstand hat; fällt der Server aus, erscheint wieder der tägliche Stand.
- **Nicht live möglich:** die beiden Orderbuch-Tests. Binance liefert das Orderbuch live nur bis ±0,22 % um den Kurs
  (gemessen auf dem Server), die Regeln brauchen ±3 % bzw. ±5 %; diese Tiefe gibt es nur im Archiv.
- **Betrieb:** ein Docker-Container mit Obergrenzen (0,6 Kerne, 800 MB), alles unter `/opt/odingate`, keine
  Handelsschlüssel, keine Orders. Einrichten `live/install.sh`, ansehen `live/status.sh`, entfernen `live/entfernen.sh`.

---

## 31. Zwei neue Ideen des Auftraggebers: Trend-Scalping und Cross-Exchange-Hedge (16.11.2026)

**Die Ideen (H18, H19).** (1) Zur bestehenden Swing-Position zusätzliche, kurz gehaltene Positionen in Trendrichtung
eröffnen, wenn der Kurs kurzfristig gegen den Trend läuft, mit engen Stops und Gewinnzielen und hohem Hebel (15 bis
20). (2) Gleichzeitig Long auf Börse A und Short auf Börse B eröffnen, die verlierende Seite früh schließen, die
gewinnende bis zum Ziel laufen lassen (Chance zu Risiko 2:1), bei hoher Handelsfrequenz.

**Einordnung vor jeder Rechnung.**
- Idee 1 ist im Kern schon gerechnet: Der Filter `trend_mit` der Fabrik ist derselbe 14-Tage-Trend wie in Test 1.
  „Rücksetzer in Trendrichtung handeln“ sind die Kandidaten mit diesem Filter, die gegen eine kurze Bewegung
  einsteigen; „Fortsetzung handeln“ die, die mit ihr einsteigen. Das wird aus dem Archiv ausgezählt (E20). Diese
  Auszählung ist beschreibend; sie enthält Ergebnisse der Schlussprüfung und steuert keine neue Generation.
- Hebel ist kein Ertragsfaktor: Er vervielfacht Ertrag und Verlust je Trade gleichermaßen. Ob eine Regel verdient,
  entscheidet sich bei Hebel 1. Die Obergrenze des Auftraggebers (Hebel höchstens 5) gilt weiter.
- Idee 2 ist rechnerisch ein Ausbruchshandel mit doppelten Kosten: Wer gleichzeitig Long und Short eröffnet und die
  Verliererseite beim Stop schließt, steht danach genau so da, als wäre er erst beim Ausbruch in dessen Richtung
  eingestiegen, hat aber zwei Positionen bezahlt. Ohne Vorhersagekraft ist der Erwartungswert vor Kosten null.
  Zusätzlich berührt sie drei Regeln des Auftraggebers (keine gegenläufigen Positionen, keine Cross-Exchange-Konstrukte,
  kein Handelsvolumen ohne eigenen Handelsgrund) und üblicherweise die Rebate-Bedingungen der Börsen.

**E19, festgelegt vor der Rechnung: der Kern von Idee 2 an echten Kursen.** BTC, ETH, SOL, Minutenkerzen,
15.08.2021 bis 30.06.2024 (Training und Auswahlprüfung; Schlussprüfung und Tresor bleiben zu). Alle vier Stunden wird
ein Paar eröffnet (Long und Short zum selben Kurs). Stop-Abstand s = 0,2 %, 0,5 % oder 1,0 %; Ziel 2 s. Die Seite, die
zuerst s verliert, wird geschlossen; die andere läuft bis +2 s, zurück bis −s oder höchstens 24 Stunden. Berühren Hoch
und Tief einer Minute beide Grenzen, gilt die ungünstige. Kosten: vier Orders je Paar, Taker 0,08 %, Rebate 85 %,
Slippage je Order wie im Kostenmodell der Fabrik. Berichtet werden je Paar: Ergebnis vor Kosten, mit und ohne Rebate
(in bp des Werts einer Seite), Trefferquote der Gewinnerseite. Erwartung: vor Kosten nahe null, nach Kosten negativ
in Höhe der Kosten. Kein Nachbessern mit Filtern; neun Zahlen (drei Coins, drei Abstände), keine Auswahl.

---

## 32. Ergebnisse E19 und E20 (16.11.2026)

**E19: gleichzeitig Long und Short, Verlierer früh schließen** (`ergebnisse/e19_gegenlaeufiges_paar.json`; je Coin
rund 6.300 Paare, 08/2021 bis 06/2024; alle Zahlen in bp des Werts einer Seite je Paar).

| Coin | Stop | vor Kosten | mit Rebate | ohne Rebate | Gewinnerseite erreicht Ziel |
|---|---|---|---|---|---|
| BTC | 0,2 % | −2,7 | −9,5 | −36,7 | 62 % |
| BTC | 0,5 % | −4,2 | −11,0 | −38,2 | 61 % |
| BTC | 1,0 % | −3,1 | −9,9 | −37,1 | 52 % |
| ETH | 0,2 % | −2,4 | −9,2 | −36,4 | 63 % |
| ETH | 0,5 % | −3,6 | −10,4 | −37,6 | 63 % |
| ETH | 1,0 % | −3,3 | −10,1 | −37,3 | 58 % |
| SOL | 0,2 % | −2,5 | −12,8 | −40,0 | 63 % |
| SOL | 0,5 % | −4,6 | −14,9 | −42,1 | 64 % |
| SOL | 1,0 % | −0,0 | −10,3 | −37,5 | 66 % |

- Vor Kosten null bis leicht negativ, wie erwartet: Damit das Paar bei Chance zu Risiko 2:1 aufgeht, müsste die
  Gewinnerseite in zwei von drei Fällen (66,7 %) ihr Ziel erreichen; gemessen sind 52 bis 66 %. Die Kursbewegung setzt
  sich nach dem ersten Ausschlag also nicht öfter fort, als der Zufall erwarten lässt.
- Nach Kosten verliert jedes Paar rund 9 bis 15 bp mit Rebate und 36 bis 42 bp ohne. Bei engem Stop (0,2 %) ist das
  rund die Hälfte des Stop-Abstands je Versuch.
- Das Rebate ist kein Ertrag: Es erstattet 85 % der selbst gezahlten Gebühr. Mehr Handelsfrequenz vervielfacht den
  Verlust, nicht den Gewinn. **Einstufung A (verworfen).** Unabhängig davon stünde die Struktur gegen drei Regeln
  des Auftraggebers (Abschnitt 31).

**E20: Idee 1 im Archiv der Fabrik** (Auszählung der schon gerechneten Kandidaten mit Filter `trend_mit`, also
Einstieg nur in Richtung des 14-Tage-Trends; bp je Trade im Training, Median über die gültigen Kandidaten).

| Einstieg in Trendrichtung | gerechnet | vor Gebühr positiv | Median vor Gebühr | mit Rebate | Stufe 1 | Finalisten |
|---|---|---|---|---|---|---|
| nach kurzer Gegenbewegung (Rücksetzer), alle Ausstiege | 5.430 | 23 % | −4,2 | −6,6 | 29 | 1 |
| Rücksetzer, nur mit Stop, Ziel oder Nachzug | 2.706 | 12 % | −5,7 | −8,1 | 3 | 0 |
| mit der kurzen Bewegung (Fortsetzung), alle Ausstiege | 15.600 | 36 % | −3,8 | −6,2 | 550 | 61 |
| Fortsetzung, nur mit Stop, Ziel oder Nachzug | 7.656 | 38 % | −3,2 | −5,6 | 390 | 36 |
| Scalping-nah (alle 5 Minuten geprüft, höchstens 60 Minuten gehalten) | 2.358 | 19 % | −5,0 | −7,4 | 27 | 1 |

- **Rücksetzer in Trendrichtung handeln** (der Kern der Idee) hat schon vor Gebühren einen negativen Erwartungswert;
  enge Stops und Ziele verschlechtern ihn. Von 5.430 Varianten erreicht eine die Schlussprüfung und ist dort negativ.
- **Besser ist das Gegenteil:** in Trendrichtung einsteigen, wenn der Kurs gerade stark in Trendrichtung gelaufen
  ist. Von den 61 Finalisten dieser Art sind in der Schlussprüfung 75 % positiv (Median +7,4 bp mit Rebate), fünf mit
  p unter 5 % bei 3,1 zufällig erwarteten; keiner validiert. Vorn liegt ein langsames Muster, kein Scalping:
  12-Stunden-Momentum (`mom_144`), stündlich geprüft, Ausstieg über nachgezogenes Ziel, alle zehn Coins. Bester:
  `4628c5a0dc9b` mit +23 / +18 / +36 bp je Trade mit Rebate (Training / Auswahl- / Schlussprüfung), +23 bp ohne Rebate
  in der Schlussprüfung, 250 Trades in neun Monaten, p = 0,005. Drei der sechs kleinsten p-Werte aller 1.199
  Finalisten gehören zu diesem Muster. Wie bei den beiden anderen Mustern (Abschnitt 28) gilt: nachträglich gebildete
  Gruppe, Hinweis und kein Beleg.
- **Hebel 15 bis 20:** ändert den Erwartungswert je Trade nicht. Test 1 bindet bei Hebel 3 schon rund 97 % der Margin;
  zusätzliche Positionen mit hohem Hebel im selben Konto erhöhen vor allem das Liquidationsrisiko des Ganzen.
- **Einstufung:** Rücksetzer-Scalping A (verworfen). Fortsetzung in Trendrichtung B (interessant, unbestätigt); als
  dritter Beobachtungstest möglich, wenn der Auftraggeber das will. Eine neue Generation wird dafür nicht gerechnet:
  Die Bausteine sind dieselben, weitere Varianten erhöhten nur die Hürde für alle späteren Prüfungen.

---

## 33. Umzug des Papier-Bots für Test 1 und 2 auf den Server des Auftraggebers (16.11.2026, auf dessen Wunsch)

**Anlass.** Der Bot lief in einer Claude-Sitzung und war der größte laufende Verbraucher von KI-Kontingent (nach
Listenpreis rund 2,40 $ je Stunde), weil die lange Sitzung bei jedem Lauf neu eingelesen wurde. Auf dem Server
braucht er keine KI.

**Was sich geändert hat und was nicht.** Regeln, Einstellungen, Stand und Daten von Test 1 und 2 sind unverändert;
die Bot-Schritte in `vorwaertstest/stunde.sh` sind Zeile für Zeile dieselben. Neu ist nur der Rahmen:
- **Staffelstab** (`vorwaertstest/betrieb.json` im Bot-Zweig): Es rechnet immer nur die Stelle, die dort steht
  („claude“ oder „server“). Geprüft wird am Anfang jedes Laufs und noch einmal, wenn sich der Zweig während des Laufs
  bewegt hat; ein Lauf, der in einen Wechsel fällt, wird verworfen.
- **Der Stand im Repository gilt:** Ein nicht gesicherter Lauf wird beim nächsten Mal neu gerechnet, statt den Bot
  zu blockieren (frühere Schwachstelle INF-02 aus dem Audit). Ist das Repository nicht erreichbar, wird nicht gerechnet.
- **Takt:** exakt alle fünf Minuten (Minute 4, 9, 14, …) statt im Mittel alle 5,6 Minuten. Stop und Ziel von Test 2
  werden dadurch regelmäßiger geprüft; die Regel ist dieselbe.
- **Notbremse:** Datei `STOPP` im Ordner `lauf` bzw. `lauf_tpsl` auf dem Server; sie bleibt lokal.

**Unabhängige Gegenprüfung vor dem Hochladen** (drei Prüfer: Skript und Git, Übergabe, Server). Kein Datenrisiko
gefunden; drei wesentliche Lücken geschlossen und nachgetestet: (1) Ein Lauf, der beim Umlegen des Staffelstabs
rechnete, hätte noch gesichert werden können. (2) Der Klon des Bots auf dem Server wäre unbegrenzt gewachsen (rund
50 MB am Tag), weil Aufräumarbeiten im Kurzzeit-Container abgebrochen werden. (3) Die Hilfsskripte auf dem Server
waren veraltet. Dazu kleinere Punkte (sichtbare Fehler beim Sichern, strengere Selbstprüfung der Installation,
Aufräumen nach abgebrochenen Läufen). Simulation mit lokalem Test-Repository: Wechsel in beide Richtungen, auch
mitten in einem Lauf, Konflikt beim Sichern, Notbremse, nicht erreichbares Repository; alle Prüfungen bestanden.

**Ablauf der Übergabe (alle Zeiten UTC).**
- 14:39:33 neues Laufskript im Bot-Zweig (Staffelstab bei „claude“); danach zwei vollständige Läufe der
  Claude-Sitzung damit (14:44, 14:49) und unveränderter Betrieb bis 18:17.
- 18:15 Installation auf dem Server durch den Auftraggeber: Yubit für alle zehn Coins lesbar, Schreibzugriff geprüft,
  Probelauf im Wartemodus („Der Bot läuft bei: claude“).
- 18:17:40 Staffelstab auf „server“, sechs Sekunden nach dem letzten Lauf der Claude-Sitzung.
- 18:19:21 und 18:19:34 erster vollständiger Lauf des Servers (Test 1 und Test 2), 18:24 der zweite.
- Vergleich vor und nach dem Wechsel: Start, Zahl der Orders (je 10), Positionen und alle bisherigen Zeilen von
  Stand und Order-Protokoll unverändert; geändert haben sich nur Kurse und Funding-Zeitstempel des neuen Laufs.
- 18:20 geplante Aufgaben der Claude-Sitzung des Bots abgestellt (nicht gelöscht).

**Zurück zur Claude-Sitzung** (falls der Server ausfällt): `betrieb.json` im Bot-Zweig auf „claude“ setzen und die
geplante Aufgabe „Vorwärtstest-Bot stündlich“ wieder einschalten. Der Server wartet dann von selbst.
**Nicht mehr aktualisiert:** die ältere private Seite „Vorwärtstest Trend-Strategie“ (sie wurde von der Claude-Sitzung
beschrieben). Das Trading Board liest weiter aus dem Bot-Zweig und ist nicht betroffen.

---

## 34. Zyklus vom 17.11.2026: Stand der Kostenmessung und Festlegung Generation 5 (vor der Rechnung)

**Kostenmessung (H15, nur Stand):** `e16_yubit_kosten_bewegung.py` erneut gelaufen. 4.044 Messungen (15.11. 13:21 bis
17.11. 01:39 UTC), davon **31 mit Kerzenspanne über 100 bp** (größte 184 bp), 461 über 50 bp. Die Schwelle von 200
Messpunkten über 100 bp ist nicht erreicht; kein neues Experiment, die Ergebnisdatei von E16 bleibt unverändert.

**Generation 5: Ausbruch aus der Eröffnungsspanne der Handelssitzungen (H11).**
- **Mechanismus:** Zu Sitzungsbeginn kommen neue Teilnehmer und neue Information in den Markt. Die Spanne der ersten
  Stunde gilt als Orientierung; ein Schlusskurs außerhalb zeigt, dass eine Seite sich durchgesetzt hat (Fortsetzung),
  oder er lockt Nachzügler in eine Bewegung, die zurückläuft (Gegenrichtung). Die bisherigen Ausbruch-Signale der
  Fabrik nutzen gleitende Fenster ohne Bezug zur Uhrzeit; der Sitzungsbezug ist neu.
- **Neue Signale (vier, Familie „Sitzung“):** Sitzungsbeginn 00:00 (Asien), 08:00 (Europa) und 13:30 UTC (USA: Börsenbeginn
  in der Sommerzeit, Zeitpunkt der US-Konjunkturdaten in der Winterzeit). Spanne = Hoch und Tief der ersten 60 Minuten.
  In den folgenden drei Stunden misst das Signal, wie weit der Schlusskurs über (positiv) oder unter (negativ) der Spanne
  liegt, bezogen auf die Schwankung; sonst ist es null. `sitzung_asien`, `sitzung_europa`, `sitzung_usa` und
  `sitzung_alle` (alle drei zusammen). Störungstest grün.
- **Kandidaten (216):** 4 Signale × Schwellen 1,5 / 2,5 / 3,5 × mit oder gegen den Ausbruch × kein Filter × alle
  5 Minuten geprüft × Ausstiege (60 Minuten, 240 Minuten, 240 Minuten mit Stop 1,5 und Ziel 3) × 3 Märkte.
  Aufgabenliste: `fabrik/ergebnisse/aufgaben_gen5.json`.
- **Prüfung:** unverändert nach Abschnitt 19 samt Nachträgen. Neue Finalisten gehen einmal in die Schlussprüfung;
  die Korrektur rechnet über alle bisherigen und neuen Finalisten.
- **Erwartung vorab:** Ausbrüche über gleitende Fenster sind in Generation 1 überwiegend an den Kosten gescheitert;
  wahrscheinlich gilt das auch hier. Kein Nachbessern mit anderen Uhrzeiten, Filtern oder Haltedauern.

---

## 35. Ergebnis Generation 5: Eröffnungsspanne der Handelssitzungen (17.11.2026)

**Gerechnet:** 216 Kandidaten (24 Einstiegsregeln × 3 Ausstiege × 3 Märkte), zwei Sekunden Rechenzeit.

| Stufe | übrig | verworfen |
|---|---|---|
| erzeugt und gerechnet | 216 | |
| mindestens 200 Trades im Training | 216 | 0 |
| Stufe 1: Vorteil vor Gebühr (t ≥ 2) | 6 | 210 |
| Stufe 2: nach vollen Kosten | 1 | 5 (netto nicht gesichert) |
| Stufe 3: robust | **0** | 1 (Auswahlprüfung nicht positiv genug) |

- 40 von 216 Kandidaten sind im Training vor Gebühr positiv; Median −6,3 bp je Trade im Training, −5,2 bp in der
  Auswahlprüfung. Asien und Europa verlieren in beiden Richtungen.
- Einzige Spur: Ausbruch nach oben oder unten aus der Spanne nach 13:30 UTC, **mit** dem Ausbruch, BTC/ETH/SOL, vier
  Stunden gehalten. Alle sechs Kandidaten der Stufe 1 gehören dazu (fünf davon US-Sitzung). Der beste
  (`adb192d9fb23`, Schwelle 3,5) hat im Training +21,5 bp je Trade mit Rebate (t = 2,1), in der Auswahlprüfung +9,3 bp
  bei t = 0,8; verlangt ist t ≥ 1. Die zweite Hälfte des Trainings ist schon deutlich schwächer als die erste
  (+12,5 gegen +29,8 bp). Auf den sieben Altcoins und mit allen zehn Coins zeigt sich nichts.
- Sechs Treffer in Stufe 1 bei 216 Kandidaten sind 2,8 %; rein zufällig wären 0,5 bis 2,8 % zu erwarten.
- **Einstufung A (verworfen).** Keine neuen Finalisten, keine Schlussprüfung, kein Papier-Test. Kein Kandidat scheitert
  allein an der Mindestzahl von 200 Trades.
- **Was dagegen sprechen könnte:** Der US-Ausbruch ist in Training und Auswahlprüfung positiv und verfehlt die Hürde
  der Auswahlprüfung nur knapp. Als Einzelfall unter 216 ist das mit Zufall vereinbar; die Hürde bleibt, und weitere
  Uhrzeiten oder Haltedauern werden nicht nachgeschoben (so festgelegt).

**Zum Ablauf:** `trichter.py stufe3` hat mit einem Kandidaten aus Stufe 2, aber ohne neuen Finalisten, die Kopfzeilen
und Gruppengrößen in `finalisten.json` überschrieben (Finalisten und Tagesreihen selbst gleich). Beide Dateien wurden
auf den gesicherten Stand zurückgesetzt; siehe `engine/offene_fragen.md`. Stand der Fabrik: 523.272 Kandidaten,
1.199 Finalisten, 0 validiert.

---

## 34. Nachkontrolle am 17.11.2026 (Hauptsitzung)

- **Bot für Test 1 und 2 auf dem Server:** seit der Übergabe (16.11. 18:19 UTC) 190 vollständige Läufe bis 10:04 UTC,
  größter Abstand 5,1 Minuten, keine Lücke; nur der Server schreibt in den Bot-Zweig.
- **Live-Test `L-dc1d27a3`:** Status „läuft“ seit 17.11. 00:00 UTC, Daten in Echtzeit, keine Fehler oder Datenlücken,
  noch kein Signal. Erste tägliche Kontrolle gegen die Archivdaten um 09:40 UTC ohne Abweichung (noch ohne Trades).
- **Täglicher Papier-Lauf:** lief um 09:17 UTC fehlerfrei, kam aber vor den Binance-Archivdateien des Vortags
  (Kerzen am 17.11. erst um 10:03 UTC veröffentlicht, am 16.11. um 07:35 UTC). Der Lauf ist deshalb auf 11:17 UTC
  verlegt. Es geht nichts verloren: Jeder Lauf rechnet vollständig neu.
- **Versehen der Hauptsitzung:** Ein von Hand ausgelöster Zusatzlauf startete eine neue Sitzung ohne Repository statt
  der vorgesehenen. Nach 15 Sekunden angehalten und archiviert; sie hat nichts geschrieben. Geplante Läufe sind davon
  nicht betroffen. Zusatzläufe werden künftig nicht mehr auf diesem Weg ausgelöst.
- **Nachtlauf (Generation 5, Eröffnungsspanne der Handelssitzungen, H11):** vor der Rechnung festgelegt, 216
  Kandidaten, keiner Finalist. Unabhängig nachgerechnet: gleiche Kennungen, Kennzahlen bis auf Rundung gleich, der
  eine Kandidat aus Stufe 2 scheitert an der Auswahlprüfung (t = 0,80 statt 1). Grenzen eingehalten; Papier-Tests,
  Live-Dienst und das eingefrorene Archiv unberührt. Die gemeldete Schwäche in `trichter.py stufe3` ist behoben
  (siehe `engine/offene_fragen.md`).

---

## 36. Zyklus vom 18.11.2026: Stand der Kostenmessung, keine neue Generation, Plan für den Minuten-Simulator

**Kostenmessung (H15, nur Stand):** 6.924 Messungen (15.11. 13:21 bis 18.11. 01:39 UTC), davon **62 mit Kerzenspanne über
100 bp** (größte 184 bp), 763 über 50 bp. Die Schwelle von 200 ist nicht erreicht; kein neues Experiment, die
Ergebnisdatei von E16 bleibt unverändert.

**Keine neue Generation in diesem Zyklus.** Die im Auftrag genannte kleine Generation (H11) ist gerechnet und verworfen.
Von den offenen Hypothesen passt keine als kleine Generation mit neuer Information in den Baukasten: H08 (Kaufdruck als
Bestätigung) war Teil der Generation 2; H09 braucht unberührte Daten und läuft der Sache nach als Papier-Test; H12 hat zu
wenige Trades; H13 braucht Einzeltrade-Daten (rund 0,8 GB je Coin-Monat); H14 braucht die Freigabe des Auftraggebers.
Eine Generation nur aus weiteren Einstellungen würde die Hürde für alle späteren Prüfungen erhöhen, ohne etwas zu lernen.

**Plan: Einstieg innerhalb der Kerze (Rest von H07), noch nichts gebaut und nichts gerechnet.**
- **Frage:** Verdient ein Signal mehr, wenn es jede Minute geprüft und zur nächsten Minute gehandelt wird, statt erst
  am Schluss der 5-Minuten-Kerze? Betroffen sind nur Signale, die es minütlich gibt: Kaufdruck (Minutenkerzen mit
  Kauf-Marktorders, vorhanden) und Orderbuch-Tiefe (30-Sekunden-Schnappschüsse; dafür müssten die Tagesdateien neu
  geladen und je Minute statt je fünf Minuten verdichtet werden, rund 8.200 Dateien).
- **Baustein 1, Simulator `fabrik/kern_minute.py`:** dieselbe Regel wie `fabrik/kern.py` (eine Position je Coin, Stop und
  Ziel gegen Hoch und Tief, bei Lücke der schlechtere Eröffnungskurs, Funding, Slippage je Order aus der Spanne der
  letzten fünf Minuten), nur auf Minutenraster. Kosten und Hürden bleiben unverändert.
- **Tests, die vor jeder Rechnung grün sein müssen:**
  1. Parität: Wird das Signal nur an Minuten geprüft, die eine 5-Minuten-Kerze schließen, und sind Stops und Ziele
     aus, liefert der Minuten-Simulator dieselben Trades und Ergebnisse wie `kern.py` (Abweichung null, drei Coins,
     je ein Monat aus 2022, 2023 und 2024).
  2. Mit Stops und Zielen: gleiche Einstiege; Ausstiege dürfen nur früher oder gleich liegen, nie zu einem besseren
     Kurs als Stop oder Ziel.
  3. Störungstest wie bei den Signalen: Daten ab Minute T verfälscht, alle Trades mit Ausstieg vor T unverändert.
  4. Datenlücken: fehlt eine Minute, kein Einstieg in dieser und der folgenden Minute.
- **Baustein 2, erste Generation damit (erst festlegen, wenn Baustein 1 steht):** wenige Kandidaten, nur Kaufdruck,
  jeweils als Paar „minütlich“ gegen „am Kerzenschluss“ bei sonst gleicher Einstellung. Maßgeblich ist der Unterschied
  im Paar, nicht der beste Einzelwert. Die Orderbuch-Tiefe folgt nur, wenn sich beim Kaufdruck ein Unterschied zeigt.
- **Einschätzung vorab:** Generation 4 hat gezeigt, dass frischere Tiefe-Daten auf 5-Minuten-Raster nichts bringen.
  Der Minuten-Simulator ist deshalb kein sicherer Gewinn; er klärt die letzte offene Seite von H07. Aufwand rund zwei
  Sitzungen. Soll er nicht gebaut werden, genügt ein Vermerk in `engine/offene_fragen.md`.

---

## 37. Zyklus vom 19.11.2026: Stand der Kostenmessung, Baustein 1 des Minuten-Simulators gebaut (keine Rechnung)

**Kostenmessung (H15, nur Stand):** 9.814 Messungen (15.11. 13:21 bis 19.11. 01:44 UTC), davon **73 mit Kerzenspanne über
100 bp**, 999 über 50 bp. Schwelle von 200 nicht erreicht; kein neues Experiment.

**Baustein 1 (Abschnitt 36) ist gebaut: `fabrik/minute.py` und `tests/test_fabrik_minute.py`.** Die offene Frage vom
18.11. blieb ohne Antwort; wie dort angekündigt wurde gebaut. Es wurde kein Kandidat gerechnet und nichts ausgewertet.
- **Bauweise:** Der vorhandene Simulator `fabrik/kern.py` kennt kein Raster, nur Kerzen. Er wird deshalb unverändert
  wiederverwendet und bekommt Minutenkerzen, Haltedauern in Minuten und alle 5-Minuten-Größen (Schwankung, Slippage,
  Funding) so, wie sie am Schluss der jeweiligen Minute bekannt sind. Es gibt also keinen zweiten Simulator, der vom
  ersten abweichen könnte. Neu ist nur der Datenspeicher auf Minutenraster (`data/fabrik_minute`, rund 0,8 GB, zehn
  Coins, bis 31.03.2025; SOL, XRP und LTC mit denselben fünf fehlenden Tagen wie im 5-Minuten-Speicher).
- **Tests (26, alle grün; mit den übrigen zusammen 47):**
  1. Parität ohne Stops: Signal nur am Kerzenschluss, vier Ausstiege, BTC 03/2022, SOL 05/2023, ETH 02/2024:
     1.386 Trades, Einstieg, Ausstieg und Ergebnis gleich (Abweichung unter 0,000001 bp). Einziger Unterschied: Ein am
     Fensterende noch offener Trade endet je Raster an dessen letzter Kerze.
  2. Mit Stop und Ziel (drei Ausstiege, dieselben Monate): 954 Trades verglichen, 952 gleich, 2 weichen ab, beide aus
     zulässigem Grund (Kurslücke zwischen zwei Minuten oder Stop und Ziel in derselben 5-Minuten-Kerze). Kein
     Ausstieg in einer anderen 5-Minuten-Kerze, keine Reihe läuft auseinander.
  3. Kein Blick in die Zukunft: Minutendaten ab Tag 20 verfälscht, alle vorher beendeten Trades unverändert.
  4. Datenlücke: Fehlt eine Minute, gibt es in ihr und in der folgenden keinen Einstieg.
- **Abweichung vom Plan:** Der Plan nannte eine eigene Datei `kern_minute.py`. Weil der vorhandene Kern wiederverwendet
  wird, gibt es sie nicht; die Hilfen stehen in `minute.py`. Der nachgezogene Stop ist in der Parität nicht geprüft:
  Er wird je Minute statt je fünf Minuten nachgezogen und liefert auf Minutenraster absichtlich andere Ausstiege.
- **Noch offen (Baustein 2, nächster Zyklus, erst festlegen, dann rechnen):** Kaufdruck je Minute als Signal
  (Störungstest), Anbindung an Massenlauf und Trichter mit Tagesergebnissen wie bisher, dann die kleine
  Paar-Generation „minütlich gegen Kerzenschluss“. Bis dahin ist der Baustein Werkzeug ohne Ergebnis.

---

## 38. Zyklus vom 20.11.2026: Stand der Kostenmessung und Festlegung E22 (vor der Rechnung)

**Kostenmessung (H15, nur Stand):** 12.694 Messungen (15.11. 13:21 bis 20.11. 01:44 UTC), davon **93 mit Kerzenspanne über
100 bp**, 1.246 über 50 bp. Schwelle von 200 nicht erreicht; kein neues Experiment.

**E22: Kaufdruck minütlich geprüft gegen Prüfung am Kerzenschluss (Rest von H07, Baustein 2 aus Abschnitt 36).**
- **Frage:** Bringt es etwas, ein Signal jede Minute zu prüfen und zur nächsten Minute zu handeln, statt nur am Schluss
  der 5-Minuten-Kerze? Geprüft am Kaufdruck, weil es ihn minütlich gibt. Das ist ein Vergleich von Paaren, keine
  Suche nach Kandidaten: Es entsteht kein Finalist, die Schlussprüfung wird nicht geöffnet, kein Papier-Test.
- **Signal:** Kaufdruck wie in der Fabrik (Überhang der Kauf-Marktorders am Umsatz) über die letzten 5, 15, 60 oder
  240 Minuten, an jeder Minute neu gerechnet, geteilt durch dieselbe 7-Tage-Schwankung wie im 5-Minuten-Signal. An
  Minuten, die eine 5-Minuten-Kerze schließen, ist der Wert derselbe wie das Fabrik-Signal (wird geprüft, ebenso der
  Störungstest).
- **Paare (216):** 4 Fensterlängen × Schwellen 1,5 / 2,5 / 3,5 × mit oder gegen das Signal × Haltedauer 15, 60 oder
  240 Minuten (ohne Stop, Ziel, Nachzug) × 3 Märkte, kein Filter. Je Paar zwei Arme mit sonst gleicher Einstellung:
  „Kerzenschluss“ (Signal nur an der schließenden Minute) und „minütlich“. Beide laufen durch denselben Simulator
  auf Minutenraster, mit derselben Lückenregel.
- **Zeiträume und Kosten:** Training 15.08.2021 bis 30.06.2023, Auswahlprüfung 01.07.2023 bis 30.06.2024; nichts
  danach. Kosten wie in Abschnitt 19 (gemessene Slippage, Gebühr mit Rebate 2,4 bp je Trade); zusätzlich berichtet mit
  den Kosten in bewegtem Markt (5 % der Spanne der letzten 5-Minuten-Kerze je Order).
- **Maß:** je Arm Ergebnis je Trade netto mit Rebate und Ertrag je Tag (Summe je Coin, gemittelt über den Markt),
  jeweils in Training und Auswahlprüfung. Je Paar die Differenz minütlich minus Kerzenschluss.
- **Urteil, vorab festgelegt:** Die Idee gilt als **interessant (B)**, wenn in Training **und** Auswahlprüfung
  mindestens 60 % der Paare im Ertrag je Tag minütlich besser sind **und** die mittlere Differenz je Trade über
  +1 bp liegt. Sonst **verworfen (A)**; damit wäre H07 erledigt. Zusätzlich nur berichtet: wie viele Arme im
  Training netto positiv mit t ≥ 2 und in der Auswahlprüfung positiv sind (bei 432 Armen sind einzelne zufällig zu
  erwarten; daraus folgt kein Status).
- **Kontrolle der Rechnung:** Der Arm „Kerzenschluss“ wird für eine Stichprobe mit dem Archiv der Generation 1
  verglichen (gleiche Regel, 5-Minuten-Raster); kleine Abweichungen durch die Lückenregel sind erlaubt und werden genannt.

---

## 39. Ergebnis E22: Kaufdruck minütlich gegen Kerzenschluss (20.11.2026)

**Gerechnet:** 216 Paare (432 Arme), zehn Coins, Minutenraster, 28 Sekunden (`ergebnisse/e22_minute_kaufdruck.json`,
alle Paare in `e22_minute_kaufdruck_paare.csv`). Kontrollen: Das Minuten-Signal ist am Kerzenschluss gleich dem
Fabrik-Signal (Abweichung 0); der Arm „Kerzenschluss“ trifft das Archiv der Generation 1 (216 gleiche Regeln,
Korrelation 0,999, mittlere Abweichung 0,07 bp je Trade, 0,7 % andere Trade-Zahl wegen der strengeren Lückenregel).

| gemessene Kosten | Training | Auswahlprüfung | verlangt |
|---|---|---|---|
| Paare, in denen „minütlich“ je Tag besser ist | 12 % | 13 % | mindestens 60 % |
| mittlere Differenz je Trade (minütlich minus Kerzenschluss) | +0,08 bp | +0,01 bp | über +1 bp |
| Median netto je Trade, Kerzenschluss / minütlich | −8,2 / −8,1 bp | −7,8 / −8,3 bp | |

- Minütliches Prüfen macht den einzelnen Trade nicht besser, aber rund 30 % mehr Trades. Weil der Kaufdruck nach
  Kosten in fast allen Einstellungen verliert, heißt mehr handeln hier mehr verlieren.
- Mit den Kosten in bewegtem Markt ist der einzelne Trade minütlich etwas besser (+0,7 bp im Training, +0,5 bp in der
  Auswahlprüfung, in rund zwei Dritteln der Paare), bleibt aber unter der Schwelle von +1 bp, und je Tag ist
  „minütlich“ auch dort nur in 18 % bzw. 16 % der Paare besser.
- Nach Richtung: Mit dem Signal gewinnt der frühere Einstieg im Training +1,1 bp je Trade, gegen das Signal verliert
  er 1,0 bp. Das passt zu einem Signal, das kurz nachwirkt; der Betrag ist ein Bruchteil der Kosten.
- Kein einziger der 432 Arme ist im Training netto positiv mit t ≥ 2 (bei beiden Kostenannahmen).
- **Einstufung A (verworfen).** Beide vorab festgelegten Bedingungen sind klar verfehlt. Kein Finalist, keine
  Schlussprüfung, kein Papier-Test. **H07 ist damit erledigt:** Weder frischere Orderbuch-Daten (E18) noch ein
  Einstieg innerhalb der Kerze (E22) retten die kurzfristigen Signale. Die Orderbuch-Tiefe auf Minutenraster wird
  nicht nachgeschoben (so in Abschnitt 36 festgelegt: nur, wenn sich beim Kaufdruck ein Unterschied zeigt).
- **Was dagegen sprechen könnte:** Geprüft wurde nur der Kaufdruck. Für die Orderbuch-Tiefe gilt der Schluss nur
  mittelbar (über E18). Der Kaufdruck-Beobachtungstest `B-dc1d27a3` nutzt ein langes Fenster mit Bestätigung und
  seltenen Trades; über ihn sagt dieses Ergebnis nichts.

Das Minutenraster (`fabrik/minute.py`) bleibt als geprüftes Werkzeug bestehen (jetzt 29 Tests, insgesamt 50 grün).

---

## 35. Test 3, festgelegt vor jeder Rechnung (20.11.2026, auf Wunsch des Auftraggebers): Trendregel mit nachgezogenem Stop

**Anlass.** Test 1 nimmt Gewinne erst bei der Trendumkehr mit; die Umkehr-Schwelle liegt nach dem Kursrückgang weit
über dem Einstieg (Stand 20.11.: 14 bis 24 % darüber, bei Hebel 3 im ungünstigsten Fall −57 % des Kontos). Der
Auftraggeber möchte dieselbe Regel mit nachgezogenem Stop sehen, mit den Einstiegen von Test 1.

**Regel (ab jetzt eingefroren).**
- Alles wie Test 1: 14-Tage-Trend auf Stundenschluss, zehn Coins, 5.000 $ Papier-Kapital, Hebel 3, feste Größe je Coin,
  Umkehrsignal schließt und dreht die Position.
- Zusätzlich: Für jede offene Position merkt sich der Bot den günstigsten Yubit-Mittelkurs seit dem Einstieg (geprüft
  bei jedem Lauf, alle fünf Minuten). Läuft der Kurs von dort **5 % gegen die Position**, wird sie geschlossen
  (Anlass „nachzug“). Am Anfang liegt der Stop damit 5 % vom Einstieg entfernt. Kein Gewinnziel.
- Nach einem solchen Ausstieg pausiert der Coin, bis sein 14-Tage-Signal dreht (wie in Test 2).
- **Warum 5 %:** derselbe Abstand wie der Stop in Test 2, damit sich die drei Tests in genau einer Sache
  unterscheiden (Test 1 ohne Stop, Test 2 fester Stop 5 % und Ziel 15 %, Test 3 nachgezogener Stop 5 %). Der Wert ist
  vor jeder Nachrechnung gewählt; ein anderer Abstand wird nicht ausprobiert und wäre ein eigener Test.

**Start mit den Einstiegen von Test 1.** Test 3 beginnt mit den tatsächlichen Füllungen von Test 1 vom 15.11.2026,
13:21 UTC (gleiche Kurse, Mengen, Gebühren).

**Nachgerechneter Abschnitt (15.11. bis zur Inbetriebnahme).** Für jeden Lauf von Test 1 liegen die damals
beobachteten Yubit-Werte vor (bester Geld- und Briefkurs je Coin und die gemessenen Kosten einer Order in
Standardgröße). Test 3 wird mit dem echten Bot-Code auf genau diesen Beobachtungen nachgerechnet; eine Order wird zum
Mittelkurs zuzüglich der in diesem Lauf gemessenen Kosten gefüllt. Funding in diesem Abschnitt: anteilig aus dem bei
Test 1 gebuchten Funding (Näherung, Größenordnung Cent bis wenige Dollar).
Dieser Abschnitt ist **kein Vorwärtstest**: Die Regel wurde festgelegt, nachdem diese Tage vergangen waren. Er wird
überall als „nachgerechnet“ gekennzeichnet. Vorwärts gewertet wird erst ab der Inbetriebnahme.

**Prüfungen vor der Inbetriebnahme (sonst kein Start).**
1. Die Nachrechnung muss Test 2 aus dessen eigenen Aufzeichnungen wiedergeben: dieselben Ausstiege (SOL 17.11.,
   XRP 18.11.) zur selben Zeit, Füllkurse bis auf wenige Basispunkte gleich.
2. Der geänderte Bot-Code muss für Test 1 und Test 2 exakt dieselben Ergebnisse liefern wie der bisherige
   (gleicher Stand, gleiche Orders) und darf deren Dateien nicht anders schreiben.
3. Bestehende Tests des Bots grün; neue Tests für den nachgezogenen Stop.

**Betrieb.** Dritter Durchgang im selben Lauf auf dem Server (nach Test 1 und Test 2), eigener Datenordner
`vorwaertstest/lauf_trail`, eigener Tab auf dem Board. Test 1 und Test 2 bleiben unverändert.
**Wertung.** Vergleich der drei Tests über dieselbe Zeit; aussagekräftig erst nach mindestens einem vollen
Trendwechsel. Keine Änderung der Regel während des Tests.

---

## 40. Test 2 auf die Einstiege von Test 1 umgestellt, festgelegt vor der Rechnung (20.11.2026, ausdrücklicher Wunsch des Auftraggebers)

**Anlass.** Test 1 stieg am 15.11.2026 um 13:21 UTC ein, Test 2 erst um 17:44 UTC, nach gut vier Stunden Kursrückgang
und damit zu tieferen Kursen. Der Auftraggeber möchte, dass alle drei Tests exakt dieselben Einstiege haben, damit sie
sich nur im Ausstieg unterscheiden. Wortlaut: „Die trades aus Test 2&3 soll bitte exakt die selben Entrys haben wie
die aus Test 1. […] alle sollten die selben Entrys haben.“ Für Test 3 ist das schon so festgelegt (Abschnitt
„Test 3“ oben); dieser Abschnitt betrifft Test 2.

**Was geschieht (ab jetzt eingefroren, vor jeder Rechnung).**
- Die Regel von Test 2 bleibt, wie sie ist: fester Stop 5 %, Gewinnziel 15 % (beides auf die Kursbewegung des Coins),
  danach Pause bis zum Signalwechsel. Die Einstellung ändert sich nicht, sie erhält nur den Vermerk `nachgerechnet_bis`.
- Test 2 beginnt mit den tatsächlichen Füllungen von Test 1 vom 15.11.2026, 13:21 UTC (gleiche Kurse, Mengen,
  Gebühren). Der Abschnitt bis zur Umstellung wird wie bei Test 3 mit dem echten Bot-Code aus den Aufzeichnungen von
  Test 1 nachgerechnet (`vorwaertstest/nachrechnen.py`; dasselbe Werkzeug gibt den bisherigen Test 2 aus dessen eigenen
  Aufzeichnungen auf den Cent wieder).
- Der bisherige Test 2 (eigene Einstiege 17:44 UTC, vorwärts geführt bis zur Umstellung) bleibt vollständig und
  unverändert erhalten: im Ordner `vorwaertstest/archiv/lauf_tpsl_eigene_einstiege/` und in der Git-Historie. Er wird
  nicht weitergeführt.

**Einordnung.** Der bisherige Test 2 war ab 17:44 UTC ein echter Vorwärtstest; der neue Test 2 ist bis zur Umstellung
eine Nachrechnung und wird so gekennzeichnet. Der gemeinsame Einstieg ist der tatsächliche Einstieg von Test 1, also
nicht nachträglich ausgesucht. Die Entscheidung, ihn für Test 2 und Test 3 zu übernehmen, fiel aber in Kenntnis des
Kursverlaufs danach (ein großer Rückgang, in dem alle zehn Shorts im Gewinn liegen).
- Zulässige Aussage: Vergleich der drei Ausstiegsregeln bei gleichen Einstiegen.
- Keine zulässige Aussage: die Höhe des Ergebnisses von Test 2 oder Test 3 bis zur Umstellung als Beleg für einen
  Vorteil. Vorwärts gewertet wird bei beiden erst ab der Umstellung.

**Was sich rechnerisch ändert (ohne Blick ins Ergebnis).** Mit den früheren Einstiegen liegen Stop und Ziel je Coin
höher, zum Beispiel SOL Stop 76,74 statt 74,85, XRP Stop 1,0247 statt 0,9972, ETH Ziel 1.562,39 statt 1.537,38. Ob die
beiden Stops des bisherigen Test 2 (SOL 17.11., XRP 18.11.) auch so ausgelöst hätten und ob ein Ziel erreicht wurde,
ergibt die Nachrechnung; daran wird nichts gesteuert.

**Prüfungen vor der Umstellung (sonst keine Umstellung).**
1. Die ersten zehn Orders des neuen Test 2 sind dieselben wie bei Test 1 (Zeit, Füllkurs, Menge, Gebühr).
2. Eine unabhängige Kontrollrechnung der Ausstiege direkt aus den aufgezeichneten Mittelkursen (ohne den Bot-Code)
   findet dieselben Ausstiege: gleicher Coin, gleicher Lauf, gleicher Anlass.
3. Der Archivordner ist byte-gleich mit dem letzten Stand des bisherigen Test 2.
4. Test 1 bleibt unberührt (kein Byte anders).

**Board.** Der Tab von Test 2 erhält denselben Hinweis wie Test 3: „bis … nachgerechnet, seitdem live“.

---

## 41. Test 3 in Betrieb, Test 2 auf die Einstiege von Test 1 umgestellt (20.11.2026, Ergebnis zu den Abschnitten „Test 3“ und 40)

**Stand.** Seit dem Lauf von 22:39 UTC rechnet der Server des Auftraggebers alle fünf Minuten drei Papier-Konten
nacheinander: Test 1 (unverändert), Test 2 (Stop 5 %, Ziel 15 %) und Test 3 (nachgezogener Stop 5 %). Alle drei haben
dieselben Einstiege: die tatsächlichen Füllungen von Test 1 vom 15.11.2026, 13:21 UTC.

| | Test 1 | Test 2 (neu) | Test 3 | Test 2 bisher (Archiv) |
|---|---|---|---|---|
| Einstieg | 15.11. 13:21 | wie Test 1 | wie Test 1 | 15.11. 17:44 |
| nachgerechnet bis | (ganz vorwärts) | 20.11. 22:29 | 20.11. 22:34 | (ganz vorwärts, beendet 22:29) |
| Ausstiege bis dahin | keine | keine | SOL 17.11. 12:44, XRP 18.11. 07:09 | SOL 17.11. 23:09, XRP 18.11. 07:49 |
| netto mit Rebate am Ende der Nachrechnung | +1.334,01 $ (22:29) | +1.334,01 $ | +1.127,69 $ | +824,78 $ |

- **Test 2 mit den Einstiegen von Test 1 hat bisher weder Stop noch Ziel ausgelöst** und ist deshalb bis zur
  Umstellung deckungsgleich mit Test 1. Schlechtester Stand gegen den Einstieg: SOL −3,15 %, XRP −3,10 % (Stop bei
  −5 %); bester: ETH +13,55 % (Ziel bei +15 %). Die beiden Stops des bisherigen Test 2 kamen allein vom späteren,
  tieferen Einstieg. Der Rückstand des bisherigen Test 2 auf Test 1 (rund 510 $) war also zum größeren Teil der
  spätere Einstieg und die zwei Stops, kein Unterschied der Regel in diesem Zeitraum.
- **Test 3** hat SOL (−0,9 % gegen den Einstieg) und XRP (−1,5 %) ausgestoppt und hält acht Shorts mit nachgezogenem
  Stop. Rückstand auf Test 1 rund 206 $: Die beiden Coins liefen nach dem Stop weiter in Richtung der Position.
- Das alles sind **Nachrechnungen über fünf Tage in einem einzigen Abwärtstrend** und kein Beleg für oder gegen eine
  der drei Ausstiegsregeln. Aussagekräftig wird der Vergleich erst nach mindestens einem vollen Trendwechsel.

**Prüfungen vor der Umstellung (alle bestanden).**
1. Die Nachrechnung gibt den bisherigen Test 2 aus dessen eigenen Aufzeichnungen wieder: dieselben zwölf Orders zur
   selben Minute, netto auf den Cent gleich (841,30 $ nach 1.465 Läufen).
2. Alter und neuer Bot-Code schreiben für Test 1 (1.515 Läufe) und Test 2 (1.465 Läufe) byte-gleiche Dateien.
3. Zwei unabhängige Prüfer (Bot-Logik und Nachrechnung; Inbetriebnahme und Board): kein Fehler in der Regel, nichts,
   das Test 1 oder Test 2 berührt. Unter anderem 240 Zufallsverläufe mit je 120 Läufen ohne Abweichung zwischen altem
   und neuem Code; der nachgezogene Stop gegen ein eigenes Vergleichsmodell (461 Ausstiege, 290 Drehungen) ohne
   Abweichung. Ihre Hinweise sind eingearbeitet: Nur die Einstiege des ersten Laufs werden aus der Quelle
   übernommen; zwei Läufe der Quelle in einer Minute werden abgelehnt; Bericht, Verlauf, Orderliste und Regeltext auf
   dem Board nennen den nachgerechneten Abschnitt; das Board zeigt daneben das Ergebnis seit dem Live-Start.
4. Kontrollrechnung der Ausstiege ohne Bot-Code, direkt aus den aufgezeichneten Mittelkursen: Test 2 keine, Test 3
   SOL und XRP zu denselben Läufen wie gebucht. Die ersten zehn Orders beider Tests sind die von Test 1.
5. Archiv des bisherigen Test 2 byte-gleich mit dessen letztem Stand; Test 1 unberührt.
6. Trockenübung der ganzen Umstellung gegen eine lokale Kopie mit dem echten Lauf-Skript (zweimal; die erste deckte
   einen Fehler im Umstell-Skript auf, nicht im Bot).

**Ablauf der Umstellung (UTC).** 22:30:31 Code, beide Nachrechnungen und Archiv in den Bot-Zweig (`00773b25`);
22:34 Lauf des Servers mit Test 1 und Test 2 (das schon laufende Skript kennt den dritten Durchgang noch nicht);
22:35:00 Nachrechnung von Test 3 um diesen Lauf fortgeschrieben (`7e905716`); 22:39 erster Lauf mit allen drei Tests.
Kein Lauf fehlt: Test 1 hat keine Lücke, Test 2 und Test 3 haben für jeden Lauf von Test 1 eine Zeile.

**Grenzen der Nachrechnung.** Orders werden zum Mittelkurs zuzüglich der damals gemessenen Kosten gefüllt, nicht gegen
das volle Orderbuch; Funding ist anteilig aus Test 1 übernommen; die Regel von Test 3 und die Übernahme der Einstiege
wurden festgelegt, nachdem diese Tage vergangen waren. Vorwärts gewertet wird bei Test 2 ab 20.11. 22:29 UTC und bei
Test 3 ab 22:34 UTC.

**Wo was liegt (Bot-Zweig).** `vorwaertstest/lauf_trail` (Test 3), `vorwaertstest/lauf_tpsl` (Test 2 neu),
`vorwaertstest/archiv/lauf_tpsl_eigene_einstiege` (Test 2 bisher, abgeschlossen), `vorwaertstest/nachrechnen.py`.
