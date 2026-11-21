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
| netto mit Rebate | +1.334,01 $ (22:29), +1.343,72 $ (22:34) | +1.334,01 $ (22:29) | +1.127,69 $ (22:34) | +824,78 $ (22:29) |

- **Test 2 mit den Einstiegen von Test 1 hat bisher weder Stop noch Ziel ausgelöst** und ist deshalb bis zur
  Umstellung deckungsgleich mit Test 1. Schlechtester Stand gegen den Einstieg: SOL −3,15 %, XRP −3,10 % (Stop bei
  −5 %); bester: ETH +13,55 % (Ziel bei +15 %). Die beiden Stops des bisherigen Test 2 kamen allein vom späteren,
  tieferen Einstieg. Der Rückstand des bisherigen Test 2 auf Test 1 (rund 510 $) kam also vom späteren Einstieg und
  den dadurch ausgelösten zwei Stops, nicht von einem Unterschied der Regel in diesem Zeitraum.
- **Test 3** hat SOL (−0,9 % gegen den Einstieg) und XRP (−1,5 %) ausgestoppt und hält acht Shorts mit nachgezogenem
  Stop. Rückstand auf Test 1 rund 216 $ (Stand 22:34): Die beiden Coins liefen nach dem Stop weiter in Richtung der
  Position.
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

---

## 42. Zyklus vom 21.11.2026: nur Stand der Kostenmessung

**Kostenmessung (H15, nur Stand):** 15.564 Messungen (15.11. 13:21 bis 21.11. 01:39 UTC), davon **190 mit Kerzenspanne
über 100 bp** (größte 257 bp), 1.984 über 50 bp. Die Schwelle von 200 ist knapp nicht erreicht; kein neues Experiment,
die Ergebnisdatei von E16 bleibt unverändert. Der 20.11. war ein bewegter Tag (97 neue Messpunkte über 100 bp); im
nächsten Zyklus ist die Schwelle voraussichtlich erreicht. Dann wird die Auswertung als eigenes Experiment
festgelegt (vor dem Blick auf die Kosten in den heftigen Kerzen) und gerechnet.

**Keine Generation, kein Experiment.** Auftrag unverändert, keine neue Vorgabe in `engine/offene_fragen.md`; es gilt
Punkt 4 unter „Was als Nächstes sinnvoll ist“. Fabrik unverändert: 523.272 Kandidaten, 1.199 Finalisten, 0 validiert.

---

## 43. Festlegung E23 (vor der Rechnung, 21.11.2026, Idee des Auftraggebers): Marktstruktur als Zusatz zur Trendregel (H20)

**Anlass.** Der Auftraggeber fragt, ob Strukturbrüche („Break of Structure“, „Change of Character“) als Zusatz zur
Trendregel von Test 1 bis 3 taugen: für Stops, für neue Einstiege und als Trendfilter. Er hat die Prüfung an den
historischen Daten freigegeben („Ja, leg das so fest und rechne das so“); nur was besteht, wird ein Papier-Test.
Test 1 bis 3 bleiben unverändert. Bis hierher ist nichts davon gerechnet.

**Frage.** Verbessert einer von drei Struktur-Zusätzen die Trendregel nach Kosten, und zwar im Training **und** in der
Auswahlprüfung, gemessen am Ertrag je Risiko?

**Daten und Zeiträume.** Speicher der Fabrik (zehn Coins, 5-Minuten-Kerzen, Funding, bis 31.03.2025; der Tresor ab
01.04.2025 wird nicht geladen). Training T 15.08.2021 – 30.06.2023, Auswahlprüfung V1 01.07.2023 – 30.06.2024,
Schlussprüfung V2 01.07.2024 – 31.03.2025. Gerechnet werden zunächst **nur T und V1**. V2 wird nur für Kandidaten
geöffnet, die unten alle Bedingungen erfüllen, einmal.

**Ablauf wie beim Papier-Bot.** Geprüft wird am Schluss jeder 5-Minuten-Kerze, ausgeführt zur Eröffnung der nächsten
(Market-Order). Stunden- und 4-Stunden-Kerzen werden aus den 5-Minuten-Kerzen gebildet (4 Stunden ab 00:00 UTC) und
erst **eine 5-Minuten-Kerze nach ihrem Schluss** verwendet (der Bot läuft um hh:04). In Datenlücken wird nicht
gehandelt. Reihenfolge je Prüfung wie im Bot: erst Signalwechsel, dann Stop oder Ausstieg, dann Wiedereinstieg.

**Basis B0 (die Regel von Test 1, eingefroren).** Richtung d = Vorzeichen von (Stundenschluss jetzt − Stundenschluss
vor 336 Stunden). Je Coin immer eine Position in Richtung d, gleich groß, Größe beim Einstieg fest. Wechselt d, wird
gedreht.

**Struktur (je Coin, auf Kerzen der Länge TF, Stärke k).**
- Zwischenhoch: eine Kerze, deren Hoch höher ist als die Hochs der k Kerzen davor und mindestens so hoch wie die Hochs
  der k Kerzen danach. Es gilt erst als bekannt, wenn die k-te Kerze danach geschlossen hat. Zwischentief
  spiegelbildlich.
- Gültiges Niveau: das zuletzt bekannt gewordene Zwischenhoch bzw. Zwischentief.
- Strukturbruch nach oben: ein Kerzenschluss über dem gültigen, noch nicht gebrochenen Zwischenhoch (jedes Niveau
  bricht höchstens einmal); nach unten spiegelbildlich. Strukturrichtung s = Richtung des letzten Bruchs.
  (Bruch in Strukturrichtung heißt üblich „Break of Structure“, der erste Bruch dagegen „Change of Character“.)

**Drei Zusätze (Kandidaten).**
- **V1 Struktur-Stop.** Einstiege wie B0. Stop eines Shorts: das gültige, ungebrochene Zwischenhoch, wenn es über dem
  Kurs liegt; sonst das höchste Hoch der letzten (2k+1) Kerzenlängen. Wird später ein Zwischenhoch bekannt, das tiefer
  liegt als der Stop und über dem Kurs, rückt der Stop dorthin nach (nie zurück). Schließt eine 5-Minuten-Kerze über
  dem Stop, wird geschlossen; danach Pause bis zum Wechsel von d (wie Test 2 und 3). Long spiegelbildlich.
- **V2 Struktur-Stop mit Wiedereinstieg.** Wie V1; in der Pause wird wieder in Richtung d eingestiegen, sobald ein
  Strukturbruch in Richtung d geschieht (neuer Stop nach derselben Regel). Beliebig oft.
- **V3 Struktur-Filter.** Position in Richtung d nur, solange die Strukturrichtung s gleich d ist; sonst flach. Kein
  Stop.

**Einstellungen:** TF 1 Stunde oder 4 Stunden, k 3 oder 5. Das sind 3 × 4 = **12 Kandidaten**. Kein Puffer, keine
weiteren Stellschrauben. Andere Werte werden nicht nachgeschoben.

**Vergleichsregeln (nur zur Einordnung, ohne Urteil):** K1 fester Stop 5 % mit Pause; K2 Stop 5 % und Ziel 15 % mit
Pause (Regel von Test 2); K3 nachgezogener Stop 5 % mit Pause (Regel von Test 3). Geprüft am 5-Minuten-Schluss.

**Kosten.** Alle Orders Taker: Gebühr 8 bp je Order, mit 85 % Rebate 1,2 bp. Slippage je Order: das Größere aus der
gemessenen Yubit-Slippage des Coins (eingefrorene Kostenbasis) und 5 % der Spanne der letzten 5-Minuten-Kerze vor der
Order (Kosten in bewegtem Markt, Abschnitt 19, zweiter Nachtrag). Das ist hier die Hauptrechnung, weil Stops in
bewegtem Markt auslösen. Funding gebucht. Zusätzlich berichtet: mit ruhigen Kosten und ohne Rebate.

**Buchung.** Je Coin Einsatz 1 beim Einstieg; Tagesergebnis je Coin (UTC-Tag) aus Kursänderung der offenen Position,
Kosten am Tag der Order und Funding. Tagesergebnis des Kontos: Mittel über die zehn Coins (Einsatz 1 × Konto; die
Papier-Tests laufen mit 3 ×).

**Maß und Urteil (vorab festgelegt).** Hauptmaß ist der Ertrag je Risiko (Sharpe-Zahl der Tagesergebnisse netto mit
Rebate, aufs Jahr gerechnet) im Vergleich zu B0. Ein Kandidat **besteht**, wenn alles gilt:
1. T: Sharpe-Zahl höher als bei B0, und der Unterschied ist gegen Zufall gesichert (gepaarte Block-Stichprobe der Tage,
   Blöcke von 20 Tagen, 5.000 Ziehungen, Startwert 23; höchstens 2,5 % der Ziehungen ohne Vorteil).
2. V1: Sharpe-Zahl höher als bei B0; höchstens 16 % der Ziehungen ohne Vorteil.
3. Netto mit Rebate in T und in V1 positiv.
4. Mindestens eine Nachbar-Einstellung desselben Zusatzes (anderes k bei gleichem TF oder anderes TF bei gleichem k)
   liegt in T und V1 ebenfalls über B0.
Wer besteht, geht einmal in V2 und braucht dort eine höhere Sharpe-Zahl als B0 und ein positives Netto-Ergebnis.
- **A (verworfen):** kein Kandidat besteht T und V1. V2 bleibt dann geschlossen.
- **B (interessant):** besteht T und V1, aber nicht V2. Kein Papier-Test.
- **C (Kandidat für Test 4 auf Papier):** besteht alle drei. Der Start von Test 4 bleibt Entscheidung des Auftraggebers.
Bei zwölf Kandidaten ist rein zufällig mit rund 0,05 Bestehern zu rechnen.

**Zusätzlich berichtet (ohne Hürde):** Ertrag pro Jahr, größter Einbruch, Zahl der Orders, Umsatz, Zeit im Markt, Zahl
der Stops und Wiedereinstiege, Ergebnis je Jahr, long und short getrennt.

**Prüfungen der Rechnung (vor dem Urteil, sonst kein Ergebnis).**
1. Tests an handgebauten Kursreihen: Zwischenhochs und -tiefs, Brüche, Stop-Niveau, Pause, Wiedereinstieg.
2. Kein Blick in die Zukunft: Daten ab einem Stichtag verfälscht, alle Orders davor unverändert.
3. Unabhängige Nachrechnung durch einen zweiten Programmierer nur nach diesem Text, mit eigenem Code, für zwei Coins
   und zwei Einstellungen: gleiche Orders (Zeit, Seite, Anlass), Ergebnis bis auf Rundung gleich.
4. Gegenlesen des Codes gegen diese Festlegung.

**Was vorab dagegen spricht.** Die Basis selbst war in der früheren Prüfung nach Kosten nur schwach positiv
(Sharpe-Zahl rund 0,4 bis 0,6 im damaligen Prüfzeitraum). Verwandte Regeln (Ausbrüche, Rücksetzer im Trend) lagen in
der Fabrik nach Kosten fast durchweg im Minus. Stops und Filter senken oft Risiko **und** Ertrag gleichermaßen; dann
ändert sich am Ertrag je Risiko nichts. T und V1 wurden für andere Regeln schon gesehen.

### Präzisierungen zu Abschnitt 43 (21.11.2026, vor der Rechnung; damit zwei Programmierer dasselbe bauen)

Keine Regel ändert sich; festgelegt wird nur, was der Text oben offen ließ. Bezeichnungen: 5-Minuten-Kerze i mit
Eröffnung o, Hoch h, Tief l, Schluss c; „Prüfung i“ ist der Schluss der Kerze i, ausgeführt wird zu o der Kerze i+1.

1. **Raster.** Kerze 0 beginnt am 01.07.2021 00:00 UTC. Stunde = 12 Kerzen, 4 Stunden = 48 Kerzen, jeweils ab Kerze 0.
   Eine TF-Kerze hat Eröffnung der ersten, Hoch und Tief über alle, Schluss der letzten ihrer 5-Minuten-Kerzen.
2. **Wissen bei Prüfung i.** Bekannt sind alle TF-Kerzen, deren letzte 5-Minuten-Kerze höchstens i−1 ist (eine Kerze
   Verzug). Eine TF-Kerze wird also zum ersten Mal bei der Prüfung der ersten 5-Minuten-Kerze nach ihr verwendet.
3. **Richtung d** bei Prüfung i: Vorzeichen von (Schluss der letzten bekannten Stundenkerze − Schluss der Stundenkerze
   336 Stunden davor). Solange noch keine 337 Stundenkerzen bekannt sind: d = 0. d = 0 heißt flach.
4. **Struktur, Reihenfolge am Schluss einer TF-Kerze t:** zuerst werden die Zwischenhochs und -tiefs gültig, die mit
   dieser Kerze bekannt werden (Kerze t−k), und ersetzen das bisherige Niveau (ungebrochen); danach wird der Bruch
   geprüft: Schluss von t strikt über dem gültigen, ungebrochenen Zwischenhoch = Bruch nach oben (Niveau gilt dann als
   gebrochen, s = +1); strikt unter dem Zwischentief = Bruch nach unten (s = −1). Vor dem ersten Bruch ist s = 0.
5. **Prüfung findet nur statt,** wenn die Kerzen i und i+1 beide gültig sind (keine Datenlücke). In Lücken stehen
   im Speicher flache Kerzen zum letzten Schluss; sie gehen unverändert in Stunden- und Strukturkerzen ein.
6. **Reihenfolge je Prüfung und Coin** (wie im Bot): (a) Pause endet, wenn d nicht mehr die Richtung der gestoppten
   Position ist. (b) Hat die Position die Richtung d: Stop bzw. Ausstieg prüfen. (c) Sollrichtung bestimmen: B0 und
   V1, V2, K1 bis K3: d, außer in der Pause (dann flach); V3: d, wenn s = d, sonst flach. (d) Weicht die Position von
   der Sollrichtung ab: schließen und, wenn die Sollrichtung nicht flach ist, neu eröffnen (zwei Orders, zur selben
   Eröffnung). Ein Wiedereinstieg (V2) verlangt, dass die Pause schon vor dieser Prüfung bestand und dass der
   Strukturbruch in Richtung d genau bei dieser Prüfung erstmals bekannt ist.
7. **Stop-Niveau V1 und V2** (Short; Long gespiegelt), bestimmt bei der Prüfung, die den Einstieg auslöst: das
   gültige, ungebrochene Zwischenhoch, wenn es strikt über c der Prüfkerze liegt; sonst das höchste h der letzten
   (2k+1) TF-Längen an 5-Minuten-Kerzen bis einschließlich der Prüfkerze. Nachrücken: Wird bei einer Prüfung ein
   Zwischenhoch erstmals bekannt, das strikt unter dem Stop und strikt über c der Prüfkerze liegt, ist es der neue
   Stop. Auslösung: c strikt über dem Stop, frühestens bei der Prüfung nach der Einstiegskerze.
8. **Vergleichsregeln.** Einstiegskurs = o der Einstiegskerze. K1: c mindestens 5 % gegen die Position. K2: wie K1,
   dazu c mindestens 15 % für die Position (Ziel). K3: bester c seit dem Einstieg (Start beim Einstiegskurs), c
   mindestens 5 % davon zurück. Danach jeweils Pause wie in Punkt 6.
9. **Buchung.** Ergebnis in Anteilen des Einsatzes beim Einstieg: d × (Kurs / Einstiegskurs − 1). Jede Order kostet
   Gebühr und Slippage auf den Einsatz, gebucht am Tag ihrer Ausführungskerze. Slippage in bp: das Größere aus dem
   Wert des Coins und 5 % × (h − l) / c × 10.000 der Kerze vor der Ausführungskerze. Funding wie in der Fabrik: Eine
   Position von o der Kerze a bis o der Kerze b zahlt d × (Summe der Funding-Sätze der Kerzen a+1 bis b), gebucht am
   Tag der jeweiligen Kerze. Tagesschluss = c der letzten Kerze des UTC-Tages.
10. **Sharpe-Zahl:** Mittel durch Streuung (Stichprobe) der Tagesergebnisse des Kontos, mal Wurzel aus 365.
    **Block-Stichprobe:** n Tage; je Ziehung ⌈n/20⌉ Startpunkte gleichverteilt aus 0 bis n−1, ab jedem 20
    aufeinanderfolgende Tage (am Ende zum Anfang umlaufend), auf n Tage gekürzt, für Kandidat und B0 dieselben Tage;
    gezählt wird der Anteil der Ziehungen, in denen die Sharpe-Zahl des Kandidaten nicht über der von B0 liegt.
11. **Start.** Gerechnet wird ab Kerze 0; gewertet werden die Tage des jeweiligen Zeitraums. Positionen, die über
    eine Zeitraumgrenze laufen, werden täglich bewertet und zählen in jedem Zeitraum mit ihren Tagen.
12. **Zu Punkt 4:** Ein Zwischenhoch oder -tief braucht k vollständige Kerzen auf beiden Seiten (am Anfang der Daten
    gibt es also keines).
13. **Zu Punkt 7 und 8:** Die erste Prüfung des Stops ist der Schluss der Einstiegskerze selbst. Bei K2 wird zuerst
    das Ziel geprüft, dann der Stop. Bei K3 wird erst der beste Schluss fortgeschrieben, dann geprüft.
14. **Zu Punkt 10:** Zufallszahlen aus `numpy.random.default_rng(23)`; je Ziehung genau ein Aufruf
    `integers(0, n, ⌈n/20⌉)`; die Blöcke in der gezogenen Reihenfolge aneinandergehängt.
15. **Programm:** `forschung/experimente/e23_marktstruktur.py`, Tests `tests/test_e23_marktstruktur.py` (40 Tests grün).
    Bis hierher sind nur Orderlisten einzelner Coins für die Kontrolle erzeugt worden; kein Ergebnis wurde angesehen.

### Unabhängige Gegenprüfung von E23 und weitere Präzisierungen (21.11.2026, vor der Rechnung des Ergebnisses)

Drei unabhängige Prüfer haben geprüft, ohne das Ergebnis zu rechnen oder zu sehen:
- **Nachbau nur nach dem Text** (zweiter Programmierer, eigener Code): Für SOL und ETH und zehn Regeln stimmen alle
  20 Orderlisten überein (Kerze, Seite, Kurs; 667 bis 2.080 Orders je Liste), ebenso die Summen (Abweichung unter
  2 × 10⁻¹⁴) und die Block-Stichprobe (0,0514 auf beiden Seiten). Zusätzlich alle 16 Regeln direkt am Kern und 384
  künstliche Verläufe mit Lücken und Gleichständen: keine Abweichung.
- **Simulator:** kein Blick in die Zukunft (736 Störungsfälle an echten Daten, 0 Verstöße), keine Abweichung vom
  Text, Buchung richtig. 48 Stops, 24 Wiedereinstiege und 60 Filter-Wechsel von Hand aus den Rohkerzen nachvollzogen.
- **Auswertung:** Zeiträume, Kosten, Kennzahlen, Stichprobe und Urteil stimmen mit einer eigenen Rechnung überein.

**Behoben vor der Rechnung:** (1) Das Urteil verglich gerundete Zahlen; es rechnet jetzt auf den ungerundeten
Tagesreihen (Rundung hätte nur ein knappes Bestehen verhindern können, nie eines erzeugen). (2) Die einmalige Öffnung
von V2 war durch einen späteren Hauptlauf überschreibbar; jetzt gesperrt, die Sperre steht vor der ersten V2-Zahl.
(3) Der Hauptlauf lädt die Daten ab 01.07.2024 gar nicht mehr. (4) Die Tests waren an drei Stellen blind (Datenlücken,
Tagesbuchung je Richtung, 4-Stunden-Kerzen); die zweite Rechnung des Prüfers ist jetzt Teil der Tests
(`tests/e23_referenz.py`), dazu Tests für Stop-Niveau, Auswertung, Urteil und Sperre: 112 Tests grün. Die 20
Orderlisten sind nach den Korrekturen unverändert.

**Weitere Präzisierungen (der Text ließ sie offen; der Code war schon so, keine Regel ändert sich):**
16. **Benennung der Orders:** Schließen bei Wechsel von d oder bei d = 0: „signalwechsel“; die Eröffnung danach und
    jede Eröffnung aus flach: „einstieg“; Wiedereinstieg in V2: „wiedereinstieg“; V3 schließt bei unverändertem d:
    „filter“; dazu „stop“, „ziel“, „nachzug“.
17. **Datenlücken:** Alles geschieht nur in Prüfungen, die stattfinden: Ende der Pause, Nachrücken des Stops,
    Wiedereinstieg, Fortschreiben des besten Schlusses. Fällt die Prüfung, bei der ein Ereignis erstmals bekannt wäre,
    in eine Lücke, entfällt es. Wechselt d nur innerhalb einer Lücke hin und zurück, endet die Pause nicht.
18. **Schwellen** werden so gerechnet: Richtung × (c / Einstiegskurs − 1) ≥ 0,15 bzw. ≤ −0,05; beim Nachzug
    Richtung × (c / bester Schluss − 1) ≤ −0,05.
19. **Zu Punkt 7:** „frühestens bei der Prüfung nach der Einstiegskerze“ meint den Schluss der Einstiegskerze (Punkt 13).
20. **Stichprobe und Urteil:** Der Zufallsgenerator wird für jeden Vergleich neu mit dem Startwert 23 angelegt (alle
    Kandidaten eines Zeitraums sehen dieselben Ziehungen). Bedingung 4 meint: derselbe Nachbar hat in T und in V1 eine
    höhere Sharpe-Zahl als B0 (ohne Absicherung gegen Zufall, ohne Netto-Bedingung). Eine Reihe ohne Streuung hat
    die Sharpe-Zahl 0. Verglichen werden ungerundete Werte.

**Hinweise der Prüfer zur Auslegung des Urteils (die Regeln bleiben, wie sie sind):**
- Der Vergleich der Sharpe-Zahl ist nicht neutral dagegen, wie lange eine Regel im Markt ist. Ist die Sharpe-Zahl
  von B0 in einem Zeitraum negativ, sieht eine Regel, die zeitweise flach ist, allein dadurch besser aus; ist sie
  positiv, eher schlechter. Der Bericht nennt deshalb das Vorzeichen von B0 je Zeitraum.
- Die Stichprobe ist etwas zu großzügig (rund 3 % statt 2,5 % in T, 17 % statt 16 % in V1). Zufällige Besteher bei
  zwölf Kandidaten: rund 0,06 bis 0,12 statt 0,05. Ergebnisse nahe an der Schwelle gelten als grenzwertig.
- In V2 gibt es keinen Schutz gegen Zufall mehr (nur „besser als B0 und positiv“); ein zufälliger Besteher käme dort
  mit 30 bis 50 % durch.

---

## 44. Ergebnis E23: Marktstruktur als Zusatz zur Trendregel (21.11.2026)

**Gerechnet:** Basis, drei Vergleichsregeln und zwölf Kandidaten auf zehn Coins, nur T und V1 (5 Sekunden;
`ergebnisse/e23_marktstruktur.json`, Tagesreihen in `e23_marktstruktur_tage.npz`). Kosten wie festgelegt (bewegter
Markt, mit Rebate). Einsatz 1 × Konto.

| Regel | T: Sharpe | T: Summe | T: größter Einbruch | V1: Sharpe | V1: Summe | V1: größter Einbruch | Zeit im Markt | Orders je Tag |
|---|---|---|---|---|---|---|---|---|
| **B0 Basis (Regel von Test 1)** | **0,53** | +63 % | 60 % | **1,31** | +73 % | 33 % | 100 % | 10,9 |
| V1 Struktur-Stop, 1 h, k 3 | −1,21 | −40 % | 41 % | −1,44 | −23 % | 30 % | 19 % | 10,9 |
| V1 Struktur-Stop, 1 h, k 5 | −0,85 | −33 % | 44 % | −0,78 | −14 % | 26 % | 25 % | 10,9 |
| V1 Struktur-Stop, 4 h, k 3 | 0,02 | +1 % | 35 % | −0,08 | −2 % | 36 % | 45 % | 10,9 |
| V1 Struktur-Stop, 4 h, k 5 | −0,33 | −23 % | 38 % | 0,32 | +11 % | 42 % | 55 % | 10,9 |
| V2 mit Wiedereinstieg, 1 h, k 3 | −0,57 | −48 % | 82 % | −0,49 | −17 % | 38 % | 55 % | 18,5 |
| V2 mit Wiedereinstieg, 1 h, k 5 | −0,65 | −56 % | 75 % | −0,56 | −20 % | 41 % | 60 % | 15,7 |
| V2 mit Wiedereinstieg, 4 h, k 3 | −0,19 | −17 % | 55 % | 0,58 | +24 % | 22 % | 68 % | 12,4 |
| V2 mit Wiedereinstieg, 4 h, k 5 | −0,17 | −16 % | 68 % | 0,80 | +37 % | 23 % | 74 % | 11,8 |
| V3 Struktur-Filter, 1 h, k 3 | −0,26 | −23 % | 67 % | −0,26 | −10 % | 37 % | 56 % | 13,6 |
| V3 Struktur-Filter, 1 h, k 5 | −0,46 | −41 % | 70 % | −0,23 | −9 % | 39 % | 59 % | 11,0 |
| V3 Struktur-Filter, 4 h, k 3 | −0,14 | −13 % | 50 % | 0,85 | +35 % | 25 % | 65 % | 7,5 |
| V3 Struktur-Filter, 4 h, k 5 | −0,26 | −25 % | 75 % | 0,91 | +43 % | 24 % | 69 % | 6,9 |
| K1 fester Stop 5 % (Vergleich) | 0,36 | +40 % | 57 % | 1,11 | +59 % | 35 % | 90 % | 10,9 |
| K2 Stop 5 %, Ziel 15 % (Regel von Test 2) | 1,05 | +61 % | 30 % | 0,10 | +3 % | 32 % | 53 % | 10,9 |
| K3 nachgezogener Stop 5 % (Regel von Test 3) | −0,07 | −3 % | 28 % | −0,14 | −3 % | 20 % | 33 % | 10,9 |

- **Kein Kandidat besteht; keiner liegt in T oder in V1 auch nur über der Basis** (0 von 12 in T, 0 von 12 in V1).
  Anteil der Ziehungen ohne Vorteil: 78 bis 100 % in T, 89 bis 100 % in V1. Elf von zwölf sind in T netto negativ.
- **Warum:** Die Trendregel verdient an wenigen großen Bewegungen. Struktur-Stops werfen die Position sehr oft hinaus
  (bei 1 h, k 3 enden 2.166 von 6.072 Einstiegen am Stop; nur noch 19 % der Zeit im Markt) und verpassen dann genau
  diese Bewegungen. Der Wiedereinstieg holt das nicht zurück, er verdoppelt bei 1 h fast die Orders (bis 18,5 je Tag)
  und damit die Kosten. Der Filter auf 4 Stunden kommt der Basis in V1 am nächsten (0,91 gegen 1,31), verliert aber
  in T.
- Die Sharpe-Zahl der Basis ist in beiden Zeiträumen positiv; der von den Prüfern genannte mechanische Effekt
  (Abschnitt 43) spräche hier leicht gegen Regeln, die zeitweise flach sind, erklärt den Abstand aber nicht: Die
  meisten Kandidaten verlieren absolut.
- **Einstufung A (verworfen).** V2 bleibt geschlossen, kein Test 4. Andere Kerzenlängen, Stärken oder Puffer werden
  nicht nachgeschoben (so festgelegt). H20 ist für diese Bauart erledigt.

**Vergleichsregeln (nur Einordnung, kein Urteil).** Der feste Stop 5 % (K1) ist in beiden Zeiträumen etwas schlechter
als die Basis. Die Regel von Test 2 (K2) ist in T deutlich besser (halber Einbruch bei gleichem Ertrag), in V1
deutlich schlechter (+3 % gegen +73 %): Das Ziel bei 15 % nimmt in einem langen Trend zu früh Gewinn mit. Die Regel
von Test 3 (K3) verdient in beiden Zeiträumen nichts (1.062 Nachzug-Stops, 33 % der Zeit im Markt). Das spricht gegen
die Erwartung, dass engere Stops diese Trendregel verbessern; die laufenden Papier-Tests bleiben, wie sie sind.

**Nebenbefund zum Risiko der Basis (wichtig für Test 1 bis 3).**
- Größter Einbruch bei Einsatz 1: **60 % des Kontos**, vom 04.02. bis 29.06.2023 (145 Tage); schlechtester Tag −13 %.
- Die Papier-Tests laufen mit Hebel 3 und festem Einsatz. Rückgerechnet (Tagesschlusswerte, ohne Nachschuss): Bei
  einem Start am ungünstigsten Tag wäre das Konto aufgebraucht gewesen (Verlust 180 % des Startkapitals), ebenso bei
  Hebel 2 (120 %). Bei Hebel 3 hätte das für **173 von 1.051 Starttagen (16 %)** gegolten. Innerhalb eines Tages
  wäre es früher eingetreten.
- Ohne Rebate bleibt von der Basis wenig übrig (Sharpe 0,10 in T, 0,76 in V1): Bei 10,9 Orders je Tag kostet die
  Gebühr ohne Rebate rund 32 % des Kontos pro Jahr, mit Rebate rund 5 %. Das Rebate von 85 % ist weiter unbestätigt.

**Was dagegen sprechen könnte.** Geprüft ist eine Bauart von Marktstruktur (Zwischenhochs und -tiefs nach
Schlusskursen, 1 und 4 Stunden, Stärke 3 und 5) als Zusatz zu genau dieser Trendregel. Über Struktur auf Tageskerzen,
mit Docht statt Schluss oder als eigene Strategie sagt das Ergebnis nichts; das wären neue, vorab festzulegende
Experimente. T und V1 wurden für andere Regeln schon gesehen. Der Risikobefund hängt an der Annahme „fester Einsatz,
kein Nachschuss, Bewertung zum Tagesschluss“.

---

## 45. Festlegung E24 (vor der Rechnung, 21.11.2026, Idee des Auftraggebers): bessere Einstiege und ein breiterer Pool (H21 bis H23)

**Anlass.** Der Auftraggeber möchte (1) nicht „stumpf“ in einen Trend einsteigen, der schon weit gelaufen ist („nicht mehr
viel Luft“), (2) weitere bei Yubit handelbare Märkte außer Krypto einbeziehen (Nasdaq, Aktien, Indizes), die nur lose
mit Krypto zusammenhängen, und (3) nutzen, dass ein Markt dem anderen nachziehen könnte (Beispiel: Krypto fällt
zuerst, der Nasdaq folgt). Er will erst die Auswertung sehen; an den Papier-Tests wird vorher nichts geändert.

**Datenlage (gesichtet, ohne Ergebnisse).**
- Trading-Labor: Tageskurse von zehn US-ETFs (SPY, QQQ, DIA, IWM, EEM, EFA, XLE, XLF, XLK, XLV), 2016 bis 10/2026.
  Keine Intraday-Kurse, kein DAX, keine CFDs.
- Eigene Abrufe aus den Runden 14 bis 17 (`reports/suche_protokoll.md`): Tageskurse von 14 Märkten (SPY, QQQ, IWM, EWJ,
  EWY, Gold, Silber, Platin, Palladium, Kupfer, WTI, Brent, Erdgas, TBT) und von 134 Aktien, die Yubit als Kontrakt
  führt, jeweils 2020 bis 10/2026.
- Yubit führt Kontrakte auf QQQ, Nasdaq 100, S&P 500, SPY, DIA, IWM, Japan, Korea, Gold, Silber, Kupfer, Erdgas und
  rund 150 Aktien. **Kein DAX-Kontrakt** in der Symbolliste vom 14.11.2026. Die Kontrakte selbst gibt es erst seit
  2026 (wenige Monate Historie); gerechnet werden kann nur auf den Tageskursen der Basiswerte.

**Schon geprüft (Runden 14 bis 17, alle durchgefallen):** der 14-Tage-Trend auf den 14 Märkten (verliert, 11 von 14
negativ; dort kehren 14-Tage-Bewegungen eher um), der 12-Monats-Trend auf denselben Märkten, der Nasdaq-Trend als
Filter für Krypto (macht es schlechter), verwandte Paare, Aktien-Momentum über 12 Monate (am knappsten, aber durch
die Auswahl der Aktienliste verzerrt). Das wird nicht wiederholt. Neu sind die drei Teile unten.

### Teil A: „Luft“ beim Einstieg (H21), Krypto

Daten, Zeiträume (T, V1; V2 nur für Besteher), Kosten, Buchung und Rechenkern wie E23 (Abschnitt 43). Basis B0.
- **Ausdehnung z** je Coin an der Stundenkerze t: |ln(C_t / C_{t−336})| geteilt durch (σ_t × √336); σ_t = Streuung
  (Stichprobe) der letzten 720 Stunden-Renditen ln(C_u / C_{u−1}), u = t−719 bis t. z misst, wie weit der Kurs in
  14 Tagen schon gelaufen ist, gemessen an seiner üblichen Schwankung. Vor t = 720 ist z nicht bestimmt.
- **Kandidaten** (Position wie B0, aber Richtung 0 = flach, wenn die Bedingung nicht gilt; geprüft wie d):
  - A1 „nicht überdehnt“: nur solange z ≤ 1,0 / 1,5 / 2,0 (die Idee des Auftraggebers).
  - A2 „nur mit Kraft“ (Gegenprobe): nur solange z ≥ 0,25 / 0,5 / 1,0.
  Ist z nicht bestimmt, ist die Richtung 0. Sechs Kandidaten.
- **Urteil** wie E23: die vier Bedingungen gegen B0 (Sharpe-Zahl höher und gegen Zufall gesichert in T mit 2,5 % und
  in V1 mit 16 %, netto positiv, ein Nachbar ebenfalls über B0). Nachbar ist die nächstliegende Schwelle derselben
  Art (bei der mittleren beide).
- **Zusätzlich berichtet (ohne Urteil):** Ergebnis von B0 vor Orderkosten, zerlegt nach z (unter 0,5 / 0,5–1 / 1–1,5 /
  1,5–2 / über 2) und nach Alter des Trends (Stunden seit dem letzten Wechsel von d: unter 24 / 24–72 / 72–168 /
  168–336 / ab 336): Anteil der Zeit und Ertrag je 100 Tage Haltezeit, in T und V1.

### Teil B: dieselbe Trendregel auf Aktien (H22)

- 134 Aktien mit Yubit-Kontrakt (Liste und Tageskurse aus Runde 17). Regel und Rechnung exakt wie Runde 14
  (`src/hybrid/tagestrend.py`): Schluss gegen den Schluss vor 14 Kalendertagen, long oder short, Handel zur nächsten
  Eröffnung, Größe beim Einstieg fest, Einsatz 1 gleich verteilt auf alle 134 (noch nicht notierte bleiben leer).
- Kosten: Taker 0,08 % mit 85 % Rebate; Slippage = gemessene Yubit-Spanne je Aktie (ohne Messwert der Median,
  mindestens 0,5 bp), wie Runde 17. Funding 0. Stress: doppelte Slippage, doppelte Gebühr, 10 % Funding pro Jahr.
- Zeiträume T und V1 (Kalendertage). **Hürden:** (B1) netto mit Rebate in T und V1 positiv; (B2) auch im Stress;
  (B3) Mischung je zur Hälfte mit B0 (Tagesreihe aus E23): Sharpe-Zahl höher als B0 allein, gegen Zufall gesichert
  wie in E23 (T 2,5 %, V1 16 %).
- Besteht der Baustein, wird er allein auf 01.07.2024 bis 23.10.2026 nachgeprüft (netto positiv). Die Mischung
  lässt sich dort nicht prüfen, ohne die Krypto-Schlussprüfung zu öffnen; das bliebe einem Papier-Test überlassen.
- **Bekannte Verzerrung:** Die Aktienliste stammt von 2026 und enthält bevorzugt Titel, die bis dahin stark gestiegen
  sind. Das begünstigt Long-Positionen. Ein Bestehen wäre deshalb nur ein Hinweis.

### Teil C: „Der Nasdaq zieht Krypto nach“ (H23)

- Ein Markt: QQQ (Tageskurse und Spanne aus Runde 14). Position in QQQ nach dem 14-Tage-Trend von **Bitcoin**:
  Vorzeichen von (BTC-Schluss des UTC-Tages D−1 − BTC-Schluss des UTC-Tages D−15), gehandelt zur Eröffnung des
  US-Börsentags D (mindestens 13 Stunden später), Größe beim Einstieg fest, Einsatz 1. BTC-Tagesschluss = Schluss
  der letzten 5-Minuten-Kerze des UTC-Tages aus dem Speicher der Fabrik.
- Kosten und Stress wie Teil B. **Hürden:** (C1) netto in T und V1 positiv; (C2) auch im Stress; (C3) Mischung je
  zur Hälfte mit B0 mit höherer Sharpe-Zahl, gesichert wie oben. Zur Einordnung berichtet: QQQ nach dem eigenen
  14-Tage-Trend und QQQ gekauft und gehalten.
- Die umgekehrte Richtung (Nasdaq-Trend als Filter für Krypto) ist in Runde 16 gescheitert und wird nicht wiederholt.

### Gemeinsam

- **Einstufung je Teil:** A (verworfen), B (interessant: besteht T und V1, aber nicht die Nachprüfung), C (Kandidat
  für einen Papier-Test). Über einen Papier-Test entscheidet der Auftraggeber.
- **Prüfungen der Rechnung vor dem Urteil:** Tests für z (kein Blick in die Zukunft, Vergleich mit einer einfachen
  Schleife), Gleichlauf der Tagesrechnung mit `tagestrend`, Zeitversatz BTC-Signal gegen QQQ-Eröffnung; unabhängige
  Nachrechnung durch einen zweiten Programmierer nur nach diesem Text.
- **Was vorab dagegen spricht:** Runde 14 (derselbe Trend verliert auf Indizes, Metallen, Energie). In der
  Trendforschung laufen starke Bewegungen eher weiter, als dass sie enden; die Gegenprobe A2 prüft genau das. T und
  V1 sind für andere Regeln schon gesehen. Zehn Kandidaten und Bausteine insgesamt.

### Unabhängige Gegenprüfung von E24 und Präzisierungen (21.11.2026, vor der Rechnung des Ergebnisses)

Zwei unabhängige Prüfer, ohne das Ergebnis zu rechnen oder zu sehen:
- **Nachbau nur nach dem Text:** Teil A für SOL und ETH: Richtung, Ausdehnung z (Abweichung unter 4 × 10⁻¹⁴), Alter des
  Trends, alle sechs gefilterten Richtungen und alle 34 Orderlisten (58 bis 2.128 Orders) identisch. Teil C: Signal
  an allen 1.051 Tagen identisch, kein zusätzlicher Tag Verzug und kein Blick voraus. Teil B und C, Tagesreihen:
  identisch, sobald die Buchungsregeln von `tagestrend.py` gelten (der Text nannte sie nur durch den Verweis).
- **Gegenlesen:** kein Blick in die Zukunft (Störungen an Stunden-, Tages- und Zwischenkerzen, Wochenenden und
  Feiertagen), nichts nach dem 30.06.2024 kann eine Zahl beeinflussen, Urteil und Hürden entsprechen dem Text.
- **Schwäche der Tests, behoben:** Die sechs Tests hätten 19 absichtlich eingebaute Fehler nicht bemerkt (darunter ein
  Bitcoin-Signal einen Tag zu früh). Die 14 Tests des Prüfers mit seiner zweiten Rechnung (`tests/e24_referenz.py`,
  `tests/test_e24_gegenpruefung.py`) sind übernommen; zusammen mit E23 sind 132 Tests grün.

**Präzisierungen (der Code war schon so; keine Regel ändert sich):**
1. **Teil B und C, Buchung wie `tagestrend.py`:** Slippage als Aufschlag auf den Eröffnungskurs; Stückzahl = Einsatz
   geteilt durch diesen Kurs; Gebühr auf den gehandelten Betrag, 85 % Rebate auch im Stress (dort 0,16 %); vor dem
   15.08.2021 flach, erster Einstieg zur ersten Eröffnung im Fenster; am letzten Börsentag des Fensters (28.06.2024)
   werden alle Positionen zur Eröffnung geschlossen; Stress-Funding auf den Positionswert zum Vortagesschluss, je
   Kalendertag, gebucht am Börsentag. Liegt eine Summe in V1 näher als 0,2 % an null, gilt die Hürde als grenzwertig.
2. **Nachprüfung:** Teil A: V2 wird für Besteher einmal geöffnet, Bedingungen wie E23. Teil B: wie festgelegt. Teil C:
   keine Nachprüfung auf alten Daten (sie bräuchte Bitcoin-Kurse aus dem geschlossenen Zeitraum); ein Bestehen von T
   und V1 heißt B (interessant), C erst nach einem Papier-Test.
3. **Zerlegung in Teil A:** Jede Stufe von z und Alter ist eine eigene Regel (Position nur in dieser Stufe, Einsatz 1
   bei jedem Eintritt); untere Grenze eingeschlossen, obere ausgeschlossen. Die Erträge addieren sich nicht genau zu B0.
4. **Zahl der Urteile:** sechs Kandidaten (Teil A) und zwei Bausteine (Teil B, Teil C), zusammen acht, nicht zehn.

**Hinweise der Prüfer für die Auslegung:**
- Hürde 3 (Mischung besser, gegen Zufall gesichert) ist streng: Ein Baustein braucht dafür grob eine eigene
  Sharpe-Zahl ab 1,5. Ein Scheitern dort sagt wenig über einen mäßig guten Baustein; berichtet wird deshalb auch
  das Ergebnis des Bausteins allein.
- A1 ist 5 bis 32 % der Zeit flach und stellt 15 bis 54 % mehr Orders als die Basis; A1 und A2 mit Schwelle 1,0
  ergänzen sich genau.
- Aktienliste: 14 der 134 Titel haben im Fenster keine Kurse, 14 weitere beginnen erst im Fenster; Kurse ohne
  Dividenden. Die Auswahl von 2026 begünstigt die Regel eher. Acht Dateien zeigen Tagessprünge über 80 %
  (teils echte Ereignisse, nicht alle geprüft); das wird nachgesehen, falls das Aktien-Ergebnis nahe null liegt.

---

## 46. Ergebnis E24: bessere Einstiege und breiterer Pool (21.11.2026)

Gerechnet nur T und V1 (`ergebnisse/e24_einstieg_und_pool.json`, Tagesreihen in `e24_einstieg_und_pool_tage.npz`).
Einsatz 1 × Konto, Kosten wie festgelegt. **Alle drei Teile: Einstufung A (verworfen).** Keine Nachprüfung geöffnet,
kein Papier-Test, an den laufenden Tests ändert sich nichts.

### Teil A: „Luft“ beim Einstieg (Krypto)

| Regel | T: Sharpe | T: Summe | V1: Sharpe | V1: Summe | Ziehungen ohne Vorteil T / V1 | Zeit im Markt | Orders je Tag |
|---|---|---|---|---|---|---|---|
| **B0 Basis** | **0,53** | +63 % | **1,31** | +73 % | | 100 % | 10,9 |
| A1 nur bis z 1,0 | −0,42 | −30 % | 0,67 | +20 % | 96 % / 84 % | 71 % | 16,6 |
| A1 nur bis z 1,5 | 0,12 | +12 % | 1,12 | +45 % | 81 % / 65 % | 88 % | 14,2 |
| A1 nur bis z 2,0 | 0,29 | +31 % | 1,41 | +64 % | 73 % / 29 % | 96 % | 12,4 |
| A2 nur ab z 0,25 | 0,53 | +60 % | 1,44 | +74 % | 51 % / 24 % | 78 % | 10,0 |
| A2 nur ab z 0,5 | 0,29 | +30 % | 1,42 | +66 % | 84 % / 36 % | 59 % | 9,5 |
| A2 nur ab z 1,0 | 0,61 | +47 % | 0,66 | +22 % | 43 % / 92 % | 29 % | 5,7 |

- **Kein Kandidat besteht.** Keiner ist in T gegen Zufall besser; die Idee „nur einsteigen, solange noch Luft ist“
  (A1) ist in T bei allen drei Schwellen schlechter als die Basis, bei den engeren Schwellen deutlich.
- **Zerlegung der Basis (vor Orderkosten, Ertrag je 100 Tage Haltezeit, T / V1; Basis im Mittel 14,8 / 25,4):**

| Ausdehnung z | Anteil der Zeit | Ertrag | | Alter des Trends | Anteil der Zeit | Ertrag |
|---|---|---|---|---|---|---|
| unter 0,5 | 41 % / 44 % | +15 / +5 | | unter 1 Tag | 19 % / 21 % | +18 / −3 |
| 0,5 bis 1 | 30 % / 29 % | −7 / +41 | | 1 bis 3 Tage | 17 % / 16 % | +31 / +34 |
| 1 bis 1,5 | 17 % / 14 % | +35 / +35 | | 3 bis 7 Tage | 22 % / 19 % | +10 / +4 |
| 1,5 bis 2 | 8 % / 8 % | +26 / +37 | | 7 bis 14 Tage | 23 % / 22 % | −8 / +33 |
| über 2 | 4 % / 5 % | −26 / −43 | | über 14 Tage | 19 % / 23 % | +22 / +37 |

- **Lesart:** Ein alter Trend ist kein schlechterer Einstieg: Trends, die schon über 14 Tage laufen, verdienten in
  beiden Zeiträumen überdurchschnittlich. Der meiste Ertrag fällt an, wenn der Kurs schon deutlich gelaufen ist (z
  zwischen 1 und 2). Nur die äußerste Zone (z über 2, rund 4 bis 5 % der Zeit) verlor in beiden Zeiträumen. Dort
  auszusetzen (A1 bis 2,0) hat das Gesamtergebnis trotzdem nicht verbessert: in T deutlich weniger (+31 % gegen
  +63 %), in V1 etwas mehr je Risiko, nicht gesichert. Gründe: mehr Orders, und nach dem Aussetzen steigt die Regel
  mit neuer Größe zu neuem Kurs wieder ein, während die Basis ihre Stückzahl seit dem ersten Einstieg behält.
- Die Zerlegung ist eine Beschreibung aus zwei Zeiträumen, kein Urteil; die Stufen addieren sich nicht genau zur Basis.

### Teil B: dieselbe Trendregel auf 134 Aktien

| | T | V1 |
|---|---|---|
| Baustein allein, netto mit Rebate | +3,8 % (Sharpe 0,12) | +9,1 % (Sharpe 0,75) |
| im Stress (doppelte Kosten, 10 % Funding) | −22,8 % | −5,7 % |
| Mischung je zur Hälfte mit der Basis: Sharpe | 0,51 gegen 0,53 | 1,36 gegen 1,31 (56 % bzw. 40 % der Ziehungen ohne Vorteil) |
| Gleichlauf der Tagesergebnisse mit der Basis | 0,31 | 0,27 |

- Hürde 1 bestanden, Hürden 2 und 3 nicht: **verworfen.** Der Baustein verdient allein wenig, übersteht keine
  Funding-Kosten und macht die Mischung nicht verlässlich besser. Der halbierte Einbruch der Mischung (32 % gegen
  60 %, 16 % gegen 33 %) kommt fast nur daher, dass die Hälfte des Einsatzes in einem ruhigen Baustein liegt; das
  leistet ein kleinerer Einsatz genauso.
- Vorbehalte: Die Aktienliste von 2026 begünstigt die Regel eher. Das Ergebnis in T (+3,8 %) liegt in der
  Größenordnung dessen, was die acht ungeprüften Tagessprünge ausmachen könnten; am Urteil ändert das nichts, weil
  die Hürden 2 und 3 unabhängig davon scheitern.

### Teil C: QQQ nach dem 14-Tage-Trend von Bitcoin

- Netto mit Rebate −4,9 % (T) und +3,2 % (V1); im Stress −27 % und −9 %; Mischung schlechter als die Basis (Sharpe 0,41
  gegen 0,53; 1,28 gegen 1,31). **Alle drei Hürden verfehlt: verworfen.** Der Bitcoin-Trend sagt den Nasdaq nicht voraus.
- Zur Einordnung: QQQ nach dem eigenen 14-Tage-Trend +20,1 % und +6,5 %; QQQ gekauft und gehalten +0,5 % und +30,7 %.

### Zusammen mit den Runden 14 bis 17

Indizes, Metalle, Energie (14-Tage- und 12-Monats-Trend), Nasdaq als Filter für Krypto, Bitcoin als Signal für den
Nasdaq, Aktien-Momentum und jetzt der 14-Tage-Trend auf Aktien: keiner dieser Bausteine besteht. Für einen breiteren
Pool fehlt weiter die Grundlage. Was fehlt, sind echte Daten der Yubit-Kontrakte selbst (Kurse rund um die Uhr,
Spannen, Funding), die es erst seit 2026 gibt; ohne sie bleibt jede Rechnung auf den Basiswerten eine Näherung.

**Was dagegen sprechen könnte.** Teil A prüft eine Messgröße für „Luft“ (14-Tage-Bewegung gegen die übliche
Schwankung) und einfache Schwellen; andere Messgrößen wären neue Experimente. Teil B und C rechnen auf Tageskursen der
Basiswerte mit angenommenen Kosten. Hürde 3 ist streng (siehe Hinweise der Prüfer). T und V1 sind schon oft gesehen.

---

## 47. Festlegung E25 (vor der Rechnung, 21.11.2026, Auftrag des Auftraggebers): die Trendregel über alle Kontrakte (H24 bis H26)

**Auftrag.** „Such bitte weiter nach Edge in den ganzen Daten, die wir haben, mit den gleichen Strategien. In den ganzen
Assets.“ Wo Yubit einen Kontrakt noch nicht lange führt, soll ersatzweise die Historie einer anderen Börse dienen,
auch mit aktuellen Daten; Unterschiede zwischen den Orderbüchern seien vernachlässigbar.

**Datenlage.** OKX ist aus der Rechenumgebung nicht erreichbar. Als Ersatz-Historie liegen Binance-Tageskurse mit
Funding für **529 Kontrakte** vor, die Yubit führt (01.07.2021 bis 31.10.2026, keine fehlenden Monate), dazu je
Kontrakt eine gemessene Yubit-Spanne (Stichprobe vom 14.11.2026, 30 Messungen je Symbol). Erster Handelstag:

| | vor 08/2021 | 08/2021–06/2023 | 07/2023–06/2024 | 07/2024–03/2025 | 04–12/2025 | ab 2026 |
|---|---|---|---|---|---|---|
| Krypto | 54 | 29 | 52 | 64 | 102 | 28 |
| Aktien, Indizes, Rohstoffe (Liste aus Runde 10) | 1 | 1 | 0 | 1 | 2 | 195 |

**Schon geprüft:** der unveränderte Kandidat auf 60 alten Coins in vier Gruppen (Runden 3 bis 5: überall ähnlich,
Prüfzeitraum schwach) und die Tageskurse der Basiswerte (Runde 14, E24). **Neu** sind: alle übrigen Coins, eine
Auswahl der Coins nach Regeln, die nur die Vergangenheit kennen, und die echten Kontrakte auf Aktien, Indizes und
Rohstoffe seit ihrer Einführung.

**Tagesregel (die Trendregel auf Tageskursen, sonst unverändert).** Je Kontrakt Richtung d = Vorzeichen von
(Tagesschluss − Tagesschluss 14 Tage davor), bekannt am Schluss des UTC-Tages, gehandelt zur Eröffnung des nächsten
Tages. Immer eine Position in Richtung d, Stückzahl beim Einstieg fest (Einsatz 1 zum Einstiegskurs), bei Wechsel
drehen (zwei Orders). Ergebnis in Anteilen des Einsatzes: Richtung × (Kurs / Einstiegskurs − 1), täglich bewertet.
Ein Kontrakt ist ab dem 61. Tag nach seinem ersten Handelstag dabei.
- **Kosten:** je Order Gebühr 8 bp mit 85 % Rebate (1,2 bp) plus Slippage = gemessene Yubit-Spanne des Kontrakts
  (Median der 30 Messungen, mindestens 0,5 bp). Stress: doppelte Slippage. Funding: Eine am Tag t gehaltene Position
  zahlt Richtung × Funding-Summe des Tages t.
- Die Stops von Test 2 und Test 3 lassen sich auf Tageskursen nicht sauber nachbilden; geprüft wird nur die Regel von
  Test 1. (Auf den zehn Coins mit feinen Daten: E23, Vergleichsregeln.)

### Teil 1: Krypto breit, mit Urteil (nur T und V1; nichts nach dem 30.06.2024 wird geladen)

Körbe, jeder mit Einsatz 1, gleich verteilt auf seine Mitglieder; die Mitglieder stehen je Kalendermonat fest und
werden nur aus Daten bis zum letzten Tag des Vormonats bestimmt. Verlässt ein Kontrakt den Korb, wird er zur ersten
Eröffnung des Monats geschlossen (Kosten wie jede Order). Das Gewicht je Mitglied ist 1 / Zahl der Mitglieder des Monats.
- **BASIS:** die zehn Coins der Papier-Tests (Vergleichsmaß, mit derselben Tagesregel).
- **ALLE:** alle Krypto-Kontrakte, die dabei sind.
- **LIQ30:** die 30 mit dem höchsten mittleren Tagesumsatz der letzten 30 Tage.
- **KLEIN:** alle außer diesen 30.
- **GUT:** das Drittel, bei dem die Tagesregel selbst in den letzten 180 Tagen netto am meisten gebracht hat
  (nur Kontrakte mit mindestens 180 Tagen Zugehörigkeit); **SCHLECHT:** das schwächste Drittel (Gegenprobe).

**Urteil** für ALLE, LIQ30, KLEIN, GUT gegen BASIS: (1) T: Sharpe-Zahl höher und gegen Zufall gesichert (Block-
Stichprobe wie E23, höchstens 2,5 % der Ziehungen ohne Vorteil); (2) V1: höher, höchstens 16 %; (3) netto in T und V1
positiv; (4) auch mit doppelter Slippage in T und V1 positiv; (5) nur GUT: in T und V1 auch höher als SCHLECHT.
Besteher gehen einmal in V2 (01.07.2024 – 31.03.2025; höhere Sharpe-Zahl als BASIS und netto positiv). A, B, C wie bisher.
Zusätzlich berichtet: Mischung je zur Hälfte mit BASIS, Zahl der Mitglieder, Orders, Ergebnis je Jahr; zur Einordnung
die Tagesregel gegen die Stundenregel (B0 aus E23) auf den zehn Coins.

### Teil 2: neue Kontrakte, nur Bericht (auf ausdrücklichen Wunsch mit aktuellen Daten)

Kontrakte mit erstem Handelstag ab 01.07.2024 haben keine Historie in T und V1. Für sie, und nur für sie, wird die
Tagesregel vom 61. Tag bis 31.10.2026 gerechnet, getrennt nach (a) Krypto und (b) Aktien, Indizes, Rohstoffe: Zahl der
Kontrakte und Tage, Ergebnis eines gleichgewichteten Korbs (netto, im Stress, vor Kosten), Anteil der Kontrakte im
Plus, Ergebnis je Quartal. **Kein Urteil:** ein einziger Marktabschnitt, bei den Aktien-Kontrakten höchstens acht
Monate. Der Tresor (ab 04/2025) wird damit nur für diese neuen Kontrakte angesehen; für die zehn Coins der Papier-Tests
und alle älteren Kontrakte bleibt er zu. Ein auffälliges Ergebnis wäre ein Anlass für einen Papier-Test oder eine
spätere Prüfung, kein Beleg.

### Prüfungen der Rechnung vor dem Urteil

Tests an handgebauten Reihen (Richtung, Verzug, Drehung, Funding, Kosten, Monatswechsel, Auswahl nur aus der
Vergangenheit); Störungstest; unabhängige Nachrechnung durch einen zweiten Programmierer nur nach diesem Text.

**Was vorab dagegen spricht.** Die 60 alten Coins zeigten im Prüfzeitraum wenig. Die Liste enthält nur Kontrakte, die
Yubit heute führt (verschwundene fehlen). Spannen stammen aus einer Stunde an einem Samstag. Die Tagesregel handelt
seltener als die Stundenregel und ist nicht dieselbe Regel. Fünf Körbe gegen eine Basis; T und V1 sind oft gesehen.

### Präzisierungen zu Abschnitt 47 (21.11.2026, vor der Rechnung)

1. **Kalender:** Tag 0 ist der 01.07.2021 (Beginn der Dateien). „Ab dem 61. Tag“ heißt: dabei an Tagen mit Index ≥
   erster Handelstag + 60. Kontrakte, deren Daten am 01.07.2021 beginnen (also schon vorher gelistet waren), sind von
   Anfang an dabei.
2. **Mitglieder eines Monats:** wer am ersten Tag des Monats dabei ist (ALLE; BASIS: die zehn Coins). LIQ30: die 30
   mit dem höchsten mittleren Tagesumsatz der 30 Tage davor, KLEIN der Rest. GUT und SCHLECHT: unter den Kontrakten,
   die seit mindestens 180 Tagen dabei sind, das beste und das schwächste Drittel (abgerundet) nach der Netto-Summe
   der 180 Tage davor aus der Einzelrechnung des Kontrakts (Tagesregel mit Einsatz 1, seit er dabei ist). Bei
   Gleichstand entscheidet die alphabetische Reihenfolge der Symbole.
3. **Sollrichtung** am Tag t: d des Vortags, wenn der Kontrakt am Tag t Mitglied ist, sonst 0; ausgeführt zur
   Eröffnung von t. Offene Positionen laufen am Ende des Fensters weiter (bewertet zum letzten Schluss).
4. **Gewichte:** Tagesergebnis des Korbs = Summe der Ergebnisse seiner Mitglieder (je Einsatz 1) geteilt durch die Zahl
   der Mitglieder des Monats. Die Schlussorder eines ausscheidenden Kontrakts zählt mit dem Gewicht des Vormonats.
   Ändert sich die Zahl der Mitglieder, wird das Gewicht der übrigen ohne Kosten angepasst.
5. **GUT in T:** Wegen der 180 Tage Vorlauf hat GUT erst ab 01.01.2022 Mitglieder. Für die Bedingungen werden GUT und
   BASIS (und SCHLECHT) nur über die Tage ab dem ersten Tag mit Mitgliedern verglichen.
6. **Teil 2:** ein Korb je Gruppe, gebildet wie ALLE.
7. **Einteilung der Kontrakte:** Die Liste aus Runde 10 ging nach Namen und enthält zwei Krypto-Kontrakte (BTCUSDT, dort
   als Gegenstück ausgenommen, und MDTUSDT wegen Namensgleichheit mit einer Aktie). Als Aktien, Indizes, Rohstoffe
   gelten deshalb nur Einträge der Liste mit erstem Handelstag ab 01.01.2025 (198 Kontrakte, darunter der Gold-Token
   PAXG); alle anderen sind Krypto (331). Bemerkt beim Laden der Symbole, bevor ein Ergebnis gerechnet war.
8. **Fehlende Tageskurse** (in Teil 1 zusammen 136 Kontrakt-Tage): An einem Tag ohne Kurs geschieht nichts (keine Order,
   keine Bewertung, kein Funding); d ist an diesem Tag und 14 Tage später 0, die Position wird dann zur nächsten
   Eröffnung geschlossen und nach der Regel neu eröffnet.

### Unabhängige Gegenprüfung von E25 und weitere Präzisierungen (21.11.2026, vor der Rechnung des Ergebnisses)

Zwei unabhängige Prüfer, ohne das Ergebnis zu rechnen oder zu sehen:
- **Nachbau nur nach dem Text:** Symbollisten, erster Teilnahmetag, Richtung, Slippage, Einzelreihen aller 137
  Kontrakte und die Mitglieder von BASIS, ALLE, GUT, SCHLECHT identisch; ebenso alle Korbreihen bis auf einen Tag
  (KLEIN am 03.04.2022, siehe Punkt 11) und den ersten Monat von LIQ30 und KLEIN (Punkt 12). Teil 2 identisch.
- **Gegenlesen:** kein Blick in die Zukunft (Störungen an 13 Grenztagen), Datenzuschnitt hält, Kosten und Urteil
  entsprechen dem Text. Die vier Tests hätten 17 absichtlich eingebaute Fehler nicht bemerkt; die 31 Tests des Prüfers
  mit eigener zweiter Rechnung und zwei Tests zum Datenzuschnitt sind übernommen (38 Tests grün).

**Präzisierungen und Korrekturen (alle vor der Rechnung):**
9. **Einteilung:** ESPORTSUSDT (erster Handelstag 29.07.2025, Kurs unter 1 USDT, Tagesbewegungen über 100 %) steht
   nach Namen auf der Liste, ist aber ein kleiner Krypto-Token: zählt als Krypto. Damit 197 Aktien-, Index- und
   Rohstoff-Kontrakte und 332 Krypto.
10. **PUMPUSDT** hat zwei Kursreihen unter einem Symbol (bis 13.06.2025 und ab 10.07.2025, dazwischen ausgesetzt);
    gewertet wird die zweite, erster Handelstag 10.07.2025.
11. **Gewicht der Schlussorder (Fehler im Programm, behoben):** Sie zählt mit dem Gewicht des letzten Mitgliedstags,
    auch wenn sie wegen fehlender Kurse erst Tage später ausgeführt wird.
12. **LIQ30 und KLEIN** haben im Juli 2021 keine Mitglieder (es gibt noch keine 30 Tage Umsatz); ihre Positionen
    beginnen am 01.08.2021. Der mittlere Umsatz wird über die Tage mit Kurs gebildet. Bei Gleichstand gilt der
    alphabetisch frühere Kontrakt als der bessere.
13. **Ausgesetzte Kontrakte:** In Teil 1 gibt es 843 Kontrakt-Tage mit eingefrorenem Kurs und Umsatz null (CVC, CTK,
    ICP, CVX, MDT). Neu: Ein Kontrakt ist in einem Monat kein Mitglied, wenn sein letzter bekannter Tagesumsatz vor
    dem Monatsanfang null war. Das nutzt nur Vergangenes und gilt für alle Körbe und für Teil 2.
14. **Teil 2:** berichtet wird je Gruppe ab dem ersten Tag mit mindestens zehn Mitgliedern (bei den Aktien-Kontrakten
    gab es davor nur Gold-Token); der Anteil der Kontrakte im Plus zählt die Kontrakte im Korb an ihren
    Mitgliedstagen; dazu Mitglieder je Quartalsende und die größten Einzeltage.
15. **Zusätzlich berichtet (ohne Urteil):** Ergebnis je Jahr; und zur Einordnung 500 Körbe aus je zehn zufällig
    gezogenen Kontrakten, die von Anfang an dabei sind (fest über das ganze Fenster): Wo steht BASIS unter ihnen?

**Bekannte Schwächen der Daten (bleiben, werden im Ergebnis genannt):** An fünf Tagen (26.–28.02. und 01.–02.04.2022)
fehlen bei 22 Kontrakten die Kurse, darunter SOL, XRP und LTC; nach Punkt 8 wird dort je viermal geschlossen und neu
eröffnet. ICP hat bis 08/2022 kein Funding (zählt als null). Die Liste enthält nur Kontrakte, die Yubit heute führt.

**Hinweis der Prüfer zur Auslegung (wichtig):** Ein Korb mit mehr Mitgliedern hat schon rechnerisch eine höhere
Sharpe-Zahl als zehn Coins, auch ohne besseres Signal (bei mäßigem Gleichlauf der Einzelergebnisse grob 5 bis 30 %
mehr). Ein „höher als BASIS“ wäre deshalb zu erwarten, sobald die Regel überhaupt verdient, und kein Beleg für bessere
Märkte. Dafür dient der Vergleich mit den Zufalls-Zehn (Punkt 15).

---

## 48. Ergebnis E25: die Trendregel über alle Kontrakte (21.11.2026)

Gerechnet wie festgelegt (`ergebnisse/e25_breites_universum.json`, Tagesreihen in `e25_breites_universum_tage.npz`).
Tagesregel, Einsatz 1 × Konto, Binance-Tageskurse als Ersatz-Historie (OKX nicht erreichbar), Yubit-Spannen.

### Teil 1: Krypto breit (137 Kontrakte, T und V1): Einstufung A (verworfen)

| Korb | Mitglieder | T: Sharpe | T: Summe | T: Einbruch | V1: Sharpe | V1: Summe | V1: Einbruch | Ziehungen ohne Vorteil T / V1 |
|---|---|---|---|---|---|---|---|---|
| **BASIS (unsere zehn Coins)** | 10 | **0,54** | +67 % | 54 % | **1,66** | +89 % | 25 % | |
| ALLE | 55 bis 126 | 0,58 | +70 % | 52 % | 1,60 | +83 % | 36 % | 44 % / 54 % |
| LIQ30 (umsatzstärkste) | 30 | 0,42 | +51 % | 74 % | 1,48 | +71 % | 27 % | 57 % / 68 % |
| KLEIN (alle übrigen) | 25 bis 96 | 0,57 | +74 % | 46 % | 1,49 | +79 % | 36 % | 46 % / 60 % |
| GUT (bestes Drittel, ab 2022) | 19 bis 31 | 0,33 (BASIS ab 2022: 0,04) | +34 % | 67 % | 1,91 | +108 % | 34 % | 24 % / 36 % |
| SCHLECHT (schwächstes Drittel) | 19 bis 31 | 0,70 (ab 2022) | +65 % | 49 % | 2,19 | +110 % | 23 % | (Gegenprobe) |

- **Kein Korb besteht.** Alle sind netto und im Stress positiv, aber keiner ist gegen Zufall besser als die zehn Coins;
  ALLE und KLEIN liegen gleichauf, die 30 umsatzstärksten etwas darunter.
- **Auswahl nach vergangener Leistung trägt nicht:** Das Drittel, bei dem die Regel zuletzt am besten lief, ist in
  beiden Zeiträumen schlechter als das schwächste Drittel (0,33 gegen 0,70; 1,91 gegen 2,19). Wo die Regel zuletzt gut
  war, sagt nichts über die nächsten Monate.
- **Unsere zehn Coins sind eine gewöhnliche, eher gute Wahl:** Unter 500 Körben aus zehn zufällig gezogenen alten
  Kontrakten liegt BASIS vor 61 % (T) und 69 % (V1); Median der Zufallskörbe 0,46 und 1,40.
- Je Jahr (BASIS / ALLE): 2021 ab 15.08. +63 % / +28 %, 2022 +18 % / +36 %, 2023 +56 % / +29 %, 2024 bis 30.06.
  +20 % / +61 %. Die Mischung je zur Hälfte bringt 0,59 und 1,71 (Gleichlauf der Tagesergebnisse 0,85 und 0,81):
  kaum Streuungsgewinn, weil die Coins fast als ein Markt laufen.

### Teil 2: neue Kontrakte (nur Bericht, kein Urteil)

- **Aktien, Indizes, Rohstoffe (142 Kontrakte im Korb, 01.05. bis 31.10.2026, 184 Tage):** netto −10,8 % (vor Kosten
  −8,3 %, im Stress −12,7 %), größter Einbruch 20 %; Q2 −5,8 %, Q3 −10,4 %, Oktober +5,3 %. Ein halbes Jahr, ein
  Marktabschnitt: kein Urteil. Es passt aber zu Runde 14 und E24: Auf diesen Märkten verliert die 14-Tage-Regel eher.
- **Neue Krypto-Kontrakte (192 im Korb, 01.12.2024 bis 31.10.2026):** netto +60,8 % bei 63 % Einbruch, 48 % der
  Kontrakte im Plus. Das Ergebnis hängt an wenigen Fällen: Ohne die fünf besten Kontrakte bleiben +1,9 %; ein
  einzelner Tag (RAVE, 18.04.2026, Kurs −87 %) kostete das 71-Fache des Einsatzes dieser Position, die zuvor das
  80-Fache gewonnen hatte. Nicht belastbar.

### Nebenbefund (nachträglich gesehen, nicht vorab festgelegt): Tagesregel gegen Stundenregel

Zur Einordnung war der Vergleich auf den zehn Coins vorgesehen; die Zahlen ohne Rebate habe ich danach dazugerechnet.
Ruhige Kosten in beiden Rechnungen:

| | Stundenregel (Test 1) | Tagesregel |
|---|---|---|
| Orders je Tag (zehn Coins) | 10,9 bis 12,2 | 2,3 bis 2,4 |
| T mit Rebate | +71 % (Sharpe 0,60) | +67 % (0,54) |
| T ohne Rebate | +20 % (0,17) | +56 % (0,45) |
| V1 mit Rebate | +75 % (1,35) | +89 % (1,66) |
| V1 ohne Rebate | +45 % (0,80) | +84 % (1,55) |

Die Tagesregel entscheidet einmal am Tag statt jede Stunde, braucht ein Fünftel der Orders und verdient mit Rebate
etwa gleich, ohne Rebate deutlich mehr. Gleichlauf der Tagesergebnisse 0,94 und 0,96: Es ist im Kern dieselbe
Strategie. **Das ist eine Beobachtung, kein Urteil** (nachträglich gesehen, ein Vergleich, T und V1 oft gesehen). Sie
wäre mit eigener Festlegung zu prüfen; die Schlussprüfung V2 der zehn Coins ist dafür noch ungeöffnet.

### Einordnung

- Über alle bisherigen Prüfungen: Die Trendregel verdient auf Krypto breit ähnlich wie auf den zehn Coins; es gibt
  keinen Hinweis, dass andere Coins besser wären oder dass sich bessere vorab erkennen lassen. Auf Aktien, Indizes und
  Rohstoffen (Basiswerte und jetzt die echten Kontrakte) verliert sie eher.
- **Schwächen:** Tageskurse von Binance statt Yubit; nur Kontrakte, die Yubit heute führt; Spannen aus einer Stunde am
  Samstag, 14.11.2026; an fünf Tagen fehlen Kurse bei 22 Kontrakten; mehr Mitglieder heben die Sharpe-Zahl schon
  rechnerisch etwas (deshalb der Vergleich mit den Zufallskörben). Für Teil 2 wurden auf Wunsch des Auftraggebers
  Daten ab 04/2025 angesehen, nur für Kontrakte ohne frühere Historie; für die zehn Coins bleibt der Tresor zu.

---

## 49. Festlegung E26 (vor der Rechnung, 21.11.2026, Nachfrage des Auftraggebers): die Regel auf jedem einzelnen Markt

**Anlass.** Der Auftraggeber zweifelt, dass außerhalb der zehn Coins nichts zu finden ist, und fragt, ob wirklich alle
Paare aus dem Labor geprüft wurden. **Antwort vorab: nein.** Das Labor enthält 11 Coins (die zehn und BNB; OKX 1D und
4H, BTC/ETH/SOL auch 1H; Binance-Perpetuals 1D) und zehn US-ETFs (DIA, EEM, EFA, IWM, QQQ, SPY, XLE, XLF, XLK, XLV,
Tageskurse 04.01.2016 bis 16.10.2026). Mit der Trendregel gerechnet waren bisher die Coins, von den ETFs aber nur SPY,
QQQ und IWM (Runde 14, eigene Kurse ab 2020). Sieben ETFs und die Labor-Historie 2016 bis 2021 fehlten. Außerdem
wurden Nicht-Krypto-Märkte bisher nur als Summe über alle berichtet, nicht je Markt.

**Was gerechnet wird.** Die unveränderte Tagesregel (14 Tage) auf jedem einzelnen Markt, für den Tageskurse vorliegen:
- (a) die zehn Labor-ETFs mit den Labor-Kursen ab 2016;
- (b) die elf übrigen Märkte aus Runde 14 (EWJ, EWY, Gold, Silber, Platin, Palladium, Kupfer, WTI, Brent, Erdgas, TBT), ab 2020;
- (c) die 134 Aktien mit Yubit-Kontrakt, ab 2020;
- (d) jeder der 137 Krypto-Kontrakte einzeln (aus E25), nur T und V1.
Rechnung für (a) bis (c) wie Runde 14 (`tagestrend.py`: Signal nach Tagesschluss, Handel zur nächsten Eröffnung, Größe
beim Einstieg fest, Einsatz 1 je Markt), jeder Markt einmal über seine ganze Historie. Kosten: Taker 0,08 % mit 85 %
Rebate; Slippage = gemessene Yubit-Spanne des Kontrakts, mindestens 0,5 bp; für ETFs ohne Yubit-Kontrakt (EEM, EFA,
XLF, XLK, XLV) der Median der gemessenen ETF-Kontrakte. Funding 0; Stress: doppelte Slippage und Gebühr, 10 % Funding
pro Jahr.

**Zeiträume:** P0 vor dem 15.08.2021 (soweit Daten vorliegen), T, V1, V2 (01.07.2024 – 31.03.2025), P3 (ab 01.04.2025 bis
Datenende). Für Nicht-Krypto alle fünf; die späteren Zeiträume wurden für diese Märkte schon in den Runden 14 bis 17
angesehen. Für Krypto-Kontrakte nur T und V1 (V2 und Tresor bleiben für Krypto zu). Ein Zeitraum zählt für einen
Markt nur mit mindestens 60 Börsentagen.

**Bericht:** eine Zeile je Markt (netto mit Rebate je Zeitraum, Summe, Sharpe-Zahl über alles, Ergebnis im Stress), dazu
je Gruppe ein gleichgewichteter Korb.

**Wann ein Markt als auffällig gilt (vorab festgelegt, damit nicht nachträglich die Gewinner herausgesucht werden):**
(1) netto in jedem seiner Zeiträume positiv, bei mindestens vier Zeiträumen; (2) über alles auch im Stress positiv;
(3) t-Wert der Tagesergebnisse über die ganze Historie mindestens 2. Für Krypto-Kontrakte (zwei Zeiträume): in T und
V1 positiv und t mindestens 2.
- **Zufallserwartung:** Bei rund 155 Nicht-Krypto-Märkten ohne jeden Vorteil wären allein durch Zufall etwa zehn in
  vier Zeiträumen positiv und zwei bis vier nach allen drei Bedingungen auffällig. Erst deutlich mehr wäre ein Hinweis.
- Ein auffälliger Markt ist ein **Hinweis für einen Papier-Test, kein Beleg**: Für diese Märkte gibt es keinen
  unberührten Zeitraum mehr.

**Nicht Teil dieser Rechnung:** andere Rückblicke als 14 Tage (der 12-Monats-Trend scheiterte in Runde 15), die Stops
von Test 2 und 3 (auf Tageskursen nicht sauber nachzubilden), die echten Yubit-Kontrakte auf Aktien (zu kurz, E25).

**Prüfungen der Rechnung:** Tests für Laden, Zeiträume und Kriterium; unabhängige Nachrechnung einzelner Märkte; dazu
prüft ein unabhängiger Prüfer die Vollständigkeit: jede Datenquelle und jedes Paar im Labor und im Datenordner gegen
die Liste dessen, was gerechnet wurde.

### Unabhängige Gegenprüfung von E26: Korrekturen und Präzisierungen (21.11.2026, vor der Rechnung des Ergebnisses)

Zwei unabhängige Prüfer, ohne das Ergebnis zu rechnen: Der eine hat eine eigene Inventur aller Daten gemacht und acht
Märkte nachgerechnet (alle identisch), der andere das Programm gegengelesen. Kein Blick in die Zukunft, die Rechnung
stimmt; aber sie fanden **Fehler in den Daten und in meiner Festlegung**, alle vor der Rechnung behoben:

1. **DIAUSDT bei Yubit ist ein Krypto-Token** (Kurs 0,12 USDT), kein Kontrakt auf den Dow-ETF. DIA gilt als ETF ohne
   Kontrakt und bekommt wie EEM, EFA, XLF, XLK, XLV den Median der sechs ETF-Kontrakte SPY, QQQ, IWM, EWJ, EWY, XLE
   (1,76 bp) statt 8,5 bp.
2. **Zwei der 134 „Aktien“ waren falsche Basiswerte:** Unter CL und BZ hatte Runde 17 Colgate-Palmolive und Kanzhun
   geladen; die Yubit-Kontrakte CLUSDT und BZUSDT sind WTI und Brent (stehen schon in Gruppe b). Beide entfallen: 132
   Aktien. Das betrifft auch E24 Teil B (2 von 134 Titeln, je 0,7 % Gewicht; am Urteil dort ändert es nichts).
3. **WTI hatte am 20. und 21.04.2020 negative Kurse**, die ein Kontrakt nicht abbilden kann. WTI wird erst ab
   22.04.2020 gerechnet; das Programm bricht ab, wenn irgendein Kurs nicht größer als null ist.
4. **Zufallserwartung berichtigt** (meine Angabe war etwa doppelt zu hoch): Von den 153 Nicht-Krypto-Märkten haben
   rund 133 mindestens vier Zeiträume. Ohne jeden Vorteil wären etwa drei bis fünf in allen Zeiträumen positiv und
   **etwa einer auffällig**; null bis drei auffällige Märkte passen also vollständig zu „kein Vorteil“. Weil die Märkte
   gleichlaufen und die Aktienliste 2026 ausgesucht wurde, wären selbst fünf bis acht auffällige Aktien kein Beleg;
   maßgeblich sind die Körbe je Gruppe.
5. **Krypto-Kontrakte:** E25 hat gezeigt, dass der Korb aller Kontrakte in T und V1 klar verdient und dass sich gute
   Coins nicht vorab erkennen lassen. Ein gemeinsamer Markt-Effekt macht deshalb viele Kontrakte gleichzeitig
   „auffällig“. Als **eigenständig auffällig** gilt ein Kontrakt nur, wenn auch sein Ergebnis abzüglich des Korbs ALLE
   in T und V1 positiv ist und einen t-Wert von mindestens 2 hat (Zufallserwartung bei 77 Kontrakten mit beiden
   Zeiträumen: unter einem).
6. **Kein Paar fehlt stillschweigend:** Alle 137 alten Krypto-Kontrakte bekommen eine Zeile (14 mit „zu kurz“, 46 nur
   mit V1). Die 195 neuen Krypto-Kontrakte und die 199 Kontrakte auf Aktien, ETFs, Indizes, Rohstoffe (XLEUSDT und
   EWZUSDT gehören dazu) bekommen je eine Zeile „nur Bericht“ seit ihrer Einführung, ohne Einstufung. 25
   Yubit-Symbole ohne jede Kursdatei werden namentlich aufgeführt.
7. **Sonst festgehalten:** Positionen werden zur Eröffnung des letzten Börsentags jedes Marktes geschlossen; Summe,
   Stress, Sharpe-Zahl und t-Wert gehen nur über gezählte Zeiträume; entschieden wird auf ungerundeten Werten; die
   Labor-ETF-Kurse sind um Dividenden bereinigt (begünstigt die Regel leicht), die übrigen nicht; 13 Aktien-Dateien
   haben Tagessprünge über 80 % (der größte Tag steht in jeder Zeile); im Labor liegen 11 Coins als OKX-Spot und 20
   als Binance-Perpetual (alle unter den 137).
8. **Tests:** Die vier Tests hätten 28 von 35 eingebauten Fehlern nicht bemerkt; die 20 Testfälle des Prüfers sind
   übernommen und an die Korrekturen angepasst, dazu zwei eigene (26 Tests grün).

**Was nicht gerechnet werden kann (bleibt offen):** 49 Yubit-Kontrakte auf ETFs, gehebelte ETFs, asiatische Aktien und
Ähnliches haben keine Kurshistorie des Basiswerts im Projekt (nur die kurze Kontrakt-Reihe, Zeile „nur Bericht“);
25 Yubit-Symbole haben gar keine Kurse (darunter der Nasdaq-100-Kontrakt NDX100). Zehn Coins mit feinen Daten sind bei
Yubit nicht gelistet (CHR, DENT, HOT, ICX, IOST, LRC, MTL, OCEAN, RVN, STORJ) und bleiben außen vor. Krypto vor
08/2021 wurde nur als Gruppe gerechnet (Runden 4 und 22), nicht je Coin.

---

## 50. Ergebnis E26: die Trendregel auf jedem einzelnen Markt (21.11.2026)

Alle Zeilen in `ergebnisse/e26_jeder_markt.csv` (682 Zeilen: 153 Nicht-Krypto-Märkte, 137 alte und 392 neue Kontrakte)
und `e26_jeder_markt.json`. Tagesregel, Einsatz 1 je Markt, netto mit Rebate. P0 = vor 15.08.2021, T, V1, V2 =
07/2024–03/2025, P3 = ab 04/2025.

### Die zehn Labor-ETFs (ab 2016) und die elf weiteren Märkte (ab 2020), Ergebnis in % des Einsatzes

| Markt | P0 | T | V1 | V2 | P3 | Summe | im Stress |
|---|---|---|---|---|---|---|---|
| DIA (Dow) | +45 | −12 | +10 | +8 | −9 | +42 | −87 |
| SPY (S&P 500) | +5 | +8 | +13 | −7 | +7 | +27 | −98 |
| QQQ (Nasdaq) | −14 | +19 | +6 | −22 | +7 | −3 | −130 |
| XLK (Technologie) | −16 | +9 | +7 | −32 | +19 | −13 | −144 |
| XLE (Energie) | +35 | −11 | +21 | −25 | −33 | −14 | −158 |
| EFA (Industrieländer) | −23 | +18 | −1 | +3 | −13 | −15 | −146 |
| EEM (Schwellenländer) | −29 | −3 | −1 | −3 | +4 | −32 | −162 |
| XLF (Finanzen) | −56 | +1 | +15 | +7 | −25 | −58 | −190 |
| IWM (Nebenwerte) | −57 | −7 | −9 | −15 | +9 | −79 | −215 |
| XLV (Gesundheit) | −22 | −13 | −11 | −2 | −37 | −84 | −216 |
| EWY (Korea) | +35 | +8 | +15 | −19 | +74 | +113 | +35 |
| Silber | +36 | −34 | −26 | −5 | +91 | +62 | −46 |
| Brent-Öl | +94 | −90 | −2 | −7 | −35 | −40 | −120 |
| Gold | −23 | −10 | −15 | +9 | −16 | −55 | −133 |
| Kupfer | +24 | −33 | +1 | −10 | −45 | −63 | −147 |
| EWJ (Japan) | +6 | −15 | −10 | −24 | −42 | −85 | −237 |
| TBT (US-Anleihen short) | −32 | +16 | −20 | −41 | −32 | −110 | −275 |
| WTI-Öl (ab 22.04.2020) | +43 | −86 | −13 | −30 | −31 | −117 | −205 |
| Platin | −24 | −74 | −60 | −24 | +50 | −133 | −212 |
| Palladium | −26 | −69 | −101 | −23 | −0 | −219 | −310 |
| Erdgas | −54 | −25 | −66 | −34 | −67 | −245 | −358 |

- **Kein einziger dieser 21 Märkte ist in allen Zeiträumen positiv.** Vier sind in der Summe im Plus (DIA, SPY, Korea,
  Silber), 17 im Minus; mit Funding und doppelten Kosten bleibt nur Korea positiv. Korb der zehn ETFs über 10,8 Jahre
  −23 %, Korb der elf weiteren Märkte −80 %.

### Die 132 Aktien (ab 2020)

- 67 im Plus, 65 im Minus, Median +2,7 %. Korb aller Aktien +39 % in 6,8 Jahren (Sharpe 0,25; je Zeitraum +2, +5, +10,
  −1, +22). Von 112 Aktien mit mindestens vier Zeiträumen sind 4 in allen positiv (AAOI, CRDO, CYPH, ONDS) und **eine
  auffällig** (AAOI, t = 2,13). Erwartet ohne jeden Vorteil: drei bis fünf und etwa eine. Das ist genau Zufall, und
  die Aktienliste begünstigt die Regel dabei noch. Einzelne Tage machen bis zum Dreifachen des Einsatzes aus.

### Krypto: jeder der 137 alten Kontrakte

- Von 77 Kontrakten mit beiden Zeiträumen sind 52 in T positiv (68 %), 54 in V1 (70 %), 38 in beiden (49 %; ohne Vorteil
  wären es 25 %). Summe positiv bei 81 von 123. **Kein einzelner Kontrakt** erreicht für sich einen t-Wert von 2
  (höchster 1,93), keiner ist eigenständig auffällig: Der Vorteil zeigt sich in der Breite, nicht an einzelnen Coins.
- Die elf Labor-Coins (T / V1): BTC +44 / +75, ETH +41 / +19, SOL +245 / +289, XRP +92 / +99, DOT +78 / +55,
  DOGE +96 / +48, ADA +28 / +157, AVAX +234 / +179, BNB +0 / +110, LINK −141 / +42, LTC −51 / −69.

### Neue Kontrakte (nur Bericht) und was nicht prüfbar ist

- Neue Krypto-Kontrakte: 92 von 189 im Plus (Median −8 %). Kontrakte auf Aktien, ETFs, Indizes, Rohstoffe: 63 von 117
  im Plus (Median +1 %). Beides Münzwurf über kurze Zeit.
- **Ohne jede Kursdatei (25 Yubit-Symbole):** AMKR, ASX, BTC500, ETH500, FUTU, GE, GFS, GIGADEVICE, INDA, INFQ, JD,
  KIOXIA, KWEB, MINIMAXHKD, NDX100, OUST, PROS, QBTS, QNTSTOCK, QUBT, SIMO, SITM, STXSTOCK, XIAOMI, ZHIPUHKD.

### Einordnung

Die 14-Tage-Trendregel ist ein Krypto-Befund, kein Befund der zehn Coins: Auf Krypto verdient sie in der Breite, auf
ETFs, Indizes und Rohstoffen verliert sie über zehn Jahre, bei Aktien liegt sie genau auf Zufall. Geprüft ist damit
jede vorhandene Kursreihe mit **dieser** Regel. Nicht geprüft sind andere Rückblicke für Nicht-Krypto (außer 12 Monate,
Runde 15), andere Strategien und die oben genannten Märkte ohne Daten.

---

## 51. Festlegung E27 (vor der Rechnung, 21.11.2026, vom Auftraggeber freigegeben): Tagesvariante der Trendregel (H27)

**Anlass.** Nebenbefund aus E25 (nachträglich gesehen, Abschnitt 48): Entscheidet die Trendregel nur einmal am Tag
statt jede Stunde, braucht sie rund ein Fünftel der Orders, verdient mit Rebate etwa gleich und ohne Rebate deutlich
mehr. Der Auftraggeber hat die saubere Prüfung freigegeben („Okay, dann prüf die Tagesvariante sauber“).

**Die beiden Regeln, im selben Rechenkern (E23, zehn Coins, 5-Minuten-Kerzen, Abschnitt 43).**
- **B0 (Stundenregel, Test 1):** Richtung d = Vorzeichen von (Stundenschluss − Stundenschluss vor 336 Stunden), an jeder
  Stunde neu.
- **TAG (Tagesvariante):** dieselbe Richtung d, aber nur einmal am Tag übernommen: maßgeblich ist d der Stunde, die um
  00:00 UTC schließt; dieser Wert gilt bis zum nächsten Tag. Vor dem ersten solchen Zeitpunkt ist die Richtung 0.
  Ausführung wie immer eine 5-Minuten-Kerze später (00:05 UTC). Sonst ist alles gleich: zehn Coins, gleiche Größe,
  drehen bei Wechsel, Kosten und Buchung wie E23 (Hauptrechnung: Slippage in bewegtem Markt, Gebühr mit 85 % Rebate).
- TAG ist damit genau die Regel von Test 1, nur seltener abgefragt, und ließe sich im Papier-Bot als Test 4 einrichten.

**Zeiträume.** T und V1 (für beide Regeln schon gesehen). **V2 (01.07.2024 – 31.03.2025) wird einmal geöffnet**, für B0,
TAG und fünf weitere Tageszeiten (unten). Einordnung: In dieser Forschung war V2 für diese Regeln bisher nicht
gerechnet; die frühere Suche (Runden 1 bis 24) kannte für die Stundenregel nur ein Gesamtergebnis über 07/2023 bis
03/2025, das V2 einschließt. Für die Tagesvariante ist V2 neu. Der Tresor ab 04/2025 bleibt zu.

**Bedingungen (je Zeitraum, auf ungerundeten Tagesreihen des Kontos):**
- **A ohne Rebate besser:** Summe und Sharpe-Zahl von TAG ohne Rebate höher als bei B0.
- **B mit Rebate nicht schlechter:** Ist B0 mit Rebate positiv, muss TAG positiv sein und mindestens zwei Drittel der
  Summe von B0 erreichen; ist B0 nicht positiv, genügt TAG ≥ B0.
- **C weniger Orders:** TAG braucht höchstens ein Drittel der Orders von B0.
- **D nicht nur eine glückliche Uhrzeit:** Dieselbe Tagesvariante mit Entscheidung um 04, 08, 12, 16 und 20 Uhr UTC
  wird mitgerechnet; von den sechs Uhrzeiten müssen mindestens vier die Bedingung A erfüllen.

**Urteil.**
- **A (verworfen):** Die Bedingungen A bis D gelten in diesem Rechenkern schon in T oder V1 nicht. V2 bleibt dann zu.
- **B (interessant):** A bis D gelten in T und V1, aber nicht in V2. Kein Papier-Test.
- **C (Kandidat für Test 4 auf Papier):** A bis D gelten in T, V1 und V2. Über den Start entscheidet der Auftraggeber.
Ein Bestehen ist kein Beweis: V2 ist ein einziger Zeitraum von neun Monaten, und T und V1 waren für den Befund schon
gesehen. Für eine Variante, die dieselbe Regel nur seltener abfragt, ist es aber ein vertretbarer Schritt zum
Papier-Test.

**Zusätzlich berichtet (ohne Urteil):** für beide Regeln und alle Zeiträume Summe, Sharpe-Zahl, größter Einbruch,
Orders je Tag, jeweils mit und ohne Rebate, mit bewegten und ruhigen Kosten; der Anteil der Ziehungen ohne Vorteil
(Block-Stichprobe wie E23) für den Unterschied ohne Rebate; in T und V1 außerdem die Abfrage alle 4 und alle 12
Stunden (nur zur Einordnung, nicht in V2).

**Prüfungen der Rechnung vor dem Öffnen von V2:** Tests für die Tagesrichtung (kein Blick in die Zukunft, Ausführung
um 00:05 UTC, Vergleich mit einer einfachen Schleife), für die Bedingungen und für die Sperre (V2 nur einmal, nichts ab
04/2025); unabhängige Nachrechnung der Orders zweier Coins in T und V1; Gegenlesen.

### Unabhängige Gegenprüfung von E27 und Präzisierungen (21.11.2026, vor Stufe 1 und vor der Öffnung von V2)

Zwei unabhängige Prüfer, ohne V2 zu öffnen und ohne ein Kontoergebnis zu rechnen:
- **Nachbau nur nach dem Text** (SOL und ETH, bis 30.06.2024): Stundenrichtung, die geltende Richtung aller neun Regeln
  und alle 18 Orderlisten identisch; die Tagesfelder stimmen bis auf Rundung (unter 10⁻¹⁴). Jede Order der
  Tagesvariante liegt auf 00:05 UTC; an Tagen ohne Richtungswechsel um Mitternacht gibt es keine Order.
- **Gegenlesen:** kein Blick in die Zukunft (über 700 Störungsfälle), Bedingungen A bis D und die Einstufung wie im Text.

**Vor der Öffnung behoben:**
1. **Sperre:** Die Prüfungen, die V2 nicht brauchen, laufen jetzt vor der Sperre: Stufe 1 wird wiederholt und muss
   bitgleich herauskommen und bestehen; erst dann wird die Öffnung in die Ergebnisdatei geschrieben, erst danach wird
   über den 30.06.2024 hinaus gerechnet. Das Rechenprogramm verweigert jede Rechnung nach dem 30.06.2024, solange die
   Öffnung nicht in der Datei steht. Steht dort „geöffnet, Rechnung läuft“ und fehlt das Ergebnis, ist die Rechnung
   nach der Öffnung abgebrochen; ein zweiter Lauf wäre nur zulässig, wenn nachweislich keine Zahl aus V2 entstanden
   ist, und würde hier vermerkt.
2. **Tests:** Die acht Tests hätten 32 von 52 eingebauten Fehlern nicht bemerkt; die 42 Tests des Prüfers sind
   übernommen und an die Korrektur angepasst (50 Tests grün, keiner liest den Datenspeicher).
3. **Bericht ergänzt (ohne Einfluss auf das Urteil):** je Regel das Ergebnis vor Kosten, Slippage und Gebühr getrennt,
   und der Unterschied zur Stundenregel zerlegt in Zeitpunkt, gesparte Slippage und gesparte Gebühr. Nach der
   einmaligen Öffnung ließe sich das nicht mehr nachholen.

**Präzisierung:** Fällt die Prüfung um 00:05 UTC in eine Datenlücke, wird die Übernahme bei der nächsten Prüfung
nachgeholt, die stattfindet, mit dem Wert der Mitternachtsstunde (dieselbe Mechanik wie bei der Stundenregel). Bis
30.06.2024 betrifft das nur SOL, XRP und LTC an den bekannten fünf Tagen. Ein Papier-Bot, der nur einmal am Tag läuft
und nichts nachholt, würde sich an solchen Tagen anders verhalten.

**Hinweis der Prüfer zur Lesart (die Regeln bleiben):** Die Bedingungen A, C und D begünstigen das Bestehen schon durch
die Kostenrechnung: Wer ein Fünftel der Orders stellt, spart ohne Rebate rund 20 Punkte Gebühr in neun Monaten; die
sechs Uhrzeiten sind sechs Abfragen desselben Signals, keine sechs unabhängigen Bestätigungen. Ein Bestehen heißt
deshalb **„bei einem Fünftel der Orders nicht erkennbar schlechter“**, nicht „besser“. Berichtet wird für beide Regeln
das Vorzeichen je Zeitraum mit und ohne Rebate und die Zerlegung.

---

## 52. Ergebnis E27: Tagesvariante gegen Stundenregel, V2 einmal geöffnet (21.11.2026)

Stufe 1 (T, V1): Bedingungen A bis D erfüllt. Die Wiederholung vor der Öffnung kam bitgleich heraus; danach wurde V2
(01.07.2024 – 31.03.2025) um 11:12 UTC einmal geöffnet. **Einstufung C: Kandidat für Test 4 auf Papier.**
Zehn Coins, Einsatz 1 × Konto, bewegte Kosten (`ergebnisse/e27_tagesvariante.json`).

| | T (08/2021–06/2023) | V1 (07/2023–06/2024) | **V2 (07/2024–03/2025, neu)** |
|---|---|---|---|
| Orders je Tag: Stunde / Tag | 10,9 / 2,3 | 12,2 / 2,4 | 10,9 / 2,3 |
| **mit Rebate:** Stundenregel | +63 % (Sharpe 0,53) | +73 % (1,31) | **+83 % (1,42)** |
| mit Rebate: Tagesvariante | +61 % (0,49) | +91 % (1,68) | **+84 % (1,35)** |
| **ohne Rebate:** Stundenregel | +12 % (0,10) | +42 % (0,76) | **+63 % (1,07)** |
| ohne Rebate: Tagesvariante | +50 % (0,40) | +85 % (1,57) | **+79 % (1,28)** |
| größter Einbruch mit Rebate: Stunde / Tag | 60 % / 54 % | 33 % / 25 % | 48 % / 41 % |
| Uhrzeiten, die ohne Rebate vor der Stundenregel liegen | 6 von 6 | 6 von 6 | 6 von 6 |

**Woher der Unterschied kommt (Punkte des Kontos, Tagesvariante minus Stundenregel):**

| | T | V1 | V2 |
|---|---|---|---|
| Zeitpunkt (Ergebnis vor Kosten) | −31,8 | +2,3 | −11,7 |
| gesparte Slippage | +22,0 | +11,7 | +8,9 |
| gesparte Gebühr mit Rebate / ohne Rebate | +7,1 / +47,1 | +4,3 / +28,8 | +2,8 / +18,8 |

- **Lesart:** Die Stundenregel hat vor Kosten den etwas besseren Zeitpunkt (in zwei von drei Zeiträumen), zahlt dafür
  aber fast fünfmal so viele Orders. Mit dem angenommenen Rebate von 85 % heben sich beide auf (V2: +83,4 % gegen
  +83,5 %); ohne Rebate liegt die Tagesvariante in jedem Zeitraum klar vorn. In V2 liegt der Gleichstand bei 1,2 bp
  Gebühr je Order, also genau beim angenommenen Rebate: Fällt das Rebate niedriger aus, ist die Tagesvariante besser.
- Der Unterschied ohne Rebate ist in V2 allein nicht gegen Zufall gesichert (28 % der Ziehungen ohne Vorteil; in T
  11 %, in V1 unter 1 %). Wie von den Prüfern vorab festgehalten heißt das Urteil: **bei einem Fünftel der Orders
  nicht erkennbar schlechter, und weit weniger vom Rebate abhängig**, nicht „bessere Strategie“.
- Alle sechs Uhrzeiten bestehen in allen drei Zeiträumen; 00:00 UTC ist keine Glücks-Uhrzeit (in V2 liegt sie im
  Mittelfeld: ohne Rebate +79 % bei einer Spanne von +70 % bis +85 %).
- Zur Einordnung in T und V1: Abfrage alle 12 Stunden +80 % / +101 % mit Rebate bei 3,2 Orders je Tag, alle 4 Stunden
  +71 % / +94 % bei 5,3 bis 5,9. Seltener abfragen kostet in diesen Daten nichts.
- **Risiko unverändert:** Auch die Tagesvariante hatte in neun Monaten einen Einbruch von 41 % bei Einsatz 1.

**Verbraucht:** V2 ist für die Stundenregel und die Tagesvariante auf den zehn Coins jetzt angesehen. Der Tresor ab
04/2025 bleibt zu. Ein weiterer Beleg kann nur noch aus einem Papier-Test kommen.

---

## 53. Test 4, festgelegt vor jeder Rechnung (21.11.2026, vom Auftraggeber freigegeben): Tagesvariante der Trendregel auf Papier

**Anlass.** E27 (Abschnitte 51 und 52): Die Tagesvariante besteht in T, V1 und im einmal geöffneten V2 und ist damit
Kandidat für einen Papier-Test. Der Auftraggeber hat den Start am 21.11.2026 freigegeben („Ja, mach Test 4 mit der
Tagesvariante auf Papier“). Die Historie ist für diese Regel verbraucht; ein weiterer Beleg kann nur vorwärts kommen.

**Regel (ab jetzt eingefroren).**
- Alles wie Test 1: 14-Tage-Trend (Schluss einer Stundenkerze gegen den Schluss 336 Stunden davor), zehn Coins,
  5.000 $ Papier-Kapital, Hebel 3, feste Größe je Coin beim Einstieg, kein Stop, kein Gewinnziel, Umkehr schließt und
  dreht die Position. Füllung im Papier gegen das echte Yubit-Orderbuch des Laufs, Gebühr 0,08 %, Rebate 85 % gerechnet.
- **Einziger Unterschied:** Die Richtung wird je Coin nur **einmal am Tag** übernommen. Maßgeblich ist die Stundenkerze,
  die um 00:00 UTC schließt (Beginn 23:00 UTC des Vortags). Gehandelt wird im ersten Lauf danach (planmäßig 00:04 UTC).
  Bis zur nächsten Übernahme bleibt die Position stehen, egal was das Stundensignal dazwischen zeigt.
- **Aufholen:** Fällt der erste Lauf des Tages aus oder liefert Yubit eine der beiden Kerzen nicht, übernimmt der
  nächste Lauf, der sie bekommt, die Richtung **der 00:00-Kerze dieses Tages** (nicht die der dann laufenden Stunde).
  Solange für den laufenden Tag keine Richtung vorliegt, wird für diesen Coin nicht gehandelt. So war es in E27
  festgelegt (Übernahme wird beim nächsten stattfindenden Lauf nachgeholt).
- Gleichstand der beiden Schlusskurse: keine Position (wie Test 1). Tagesverlust-Limit wie Test 1.
- Die Uhrzeit 00:00 UTC ist die in E27 geprüfte; andere Uhrzeiten oder Abstände werden nicht ausprobiert und wären
  ein eigener Test.

**Start mit den Einstiegen von Test 1** (ausdrücklicher Wunsch des Auftraggebers vom 20.11.: alle Tests haben dieselben
Einstiege). Test 4 beginnt mit den tatsächlichen Füllungen von Test 1 vom 15.11.2026, 13:21 UTC. Das ist nur dann
zugleich die Tagesregel, wenn die Tagesrichtung vom 15.11. 00:00 UTC für alle zehn Coins der Richtung von Test 1
entspricht (Short). **Bedingung für die Inbetriebnahme:** Das wird vor dem Start an den Yubit-Kerzen geprüft; weicht
ein Coin ab, wird nicht gestartet, sondern neu festgelegt.

**Nachgerechneter Abschnitt (15.11. bis zur Inbetriebnahme).** Wie bei Test 2 und 3 mit `vorwaertstest/nachrechnen.py`
und dem echten Bot-Schritt aus den Aufzeichnungen von Test 1, gekennzeichnet über `nachgerechnet_bis`. Test 1 hat seit
dem Einstieg keine weitere Order (Stand 21.11. 11:34 UTC: zehn Orders, zehn Shorts); damit stand das Stundensignal zu
jeder vollen Stunde auf Short, also auch um 00:00 UTC jedes Tages. **Erwartung, vor der Rechnung festgehalten:** Der
nachgerechnete Abschnitt von Test 4 ist mit Test 1 identisch (dieselben zehn Orders, derselbe Kontostand in jeder
Zeile). **Prüfung vor dem Start:** Orders und Kontoverlauf werden Zeile für Zeile mit Test 1 verglichen; bei einer
Abweichung wird nicht gestartet. Ein Unterschied zwischen Test 4 und Test 1 kann also erst nach der Inbetriebnahme
entstehen, und zwar erst beim ersten Signalwechsel.

**Betrieb.** Vierter Durchgang in `stunde.sh` nach Test 3 (scheitert er, sind Test 1 bis 3 schon gesichert). Eigener
Datenordner `vorwaertstest/lauf_tag`, eigene Einstellung `config_lauf_tag.json` (Schalter `tagesregel`), eigene
Board-Datei `docs/stand_tag.enc.json`, eigener Reiter „Test 4“ auf dem Board, eigene Notbremse `lauf_tag/STOPP`. Der
Bot merkt sich die übernommene Tagesrichtung je Coin im Zustand (`tagesrichtung`: Tag, Richtung, beide Schlusskurse),
damit jede Entscheidung nachprüfbar ist.

**Test 1 bis 3 bleiben unberührt.** Ohne den Schalter `tagesregel` läuft der Bot-Schritt wie bisher. Belegt wird das
vor dem Start doppelt: durch Tests (Zustand und Ausgaben ohne neue Felder) und dadurch, dass der neue Code die
vorhandenen Aufzeichnungen von Test 1, 2 und 3 Byte für Byte gleich nachrechnet wie der alte.

**Was Test 4 zeigen kann, und was nicht.**
- Erwartung aus E27: über längere Zeit etwa ein Fünftel der Orders von Test 1, mit Rebate ein ähnliches Ergebnis, ohne
  Rebate ein besseres. Verglichen wird gepaart mit Test 1 ab demselben Start: Zahl der Orders, Gebühr, Ergebnis vor
  Kosten, netto ohne und mit Rebate.
- Solange kein Signal dreht, sind beide Tests gleich. Aussagekräftig wird der Vergleich erst nach etlichen Wechseln,
  also eher nach Monaten als nach Wochen. Es gibt keine vorab festgelegte Schwelle für „bestanden“; Test 4 ist eine
  Beobachtung, keine Freigabe für Echtgeld.
- **Unterschiede zur Rechnung in E27:** dort Einsatz 1 × Konto und Kostenmodell, hier Hebel 3 wie Test 1 und Füllung
  am echten Orderbuch um 00:04 UTC; dort Ausführung zur Eröffnung der 00:05-Kerze. Das Risiko aus Abschnitt 44 gilt
  unverändert (Hebel 3 hätte im Backtest in 16 % der Starttage das Konto aufgebraucht).

**Kein Nachjustieren.** Die Regel wird nach dem Start nicht verändert; jede Änderung wäre ein neuer Test.

**Präzisierungen zu Abschnitt 53 (21.11.2026, vor der Nachrechnung von Test 4).**
1. *Vergleich mit Test 1, genaue Fassung.* Orders: Zeit, Coin, Seite, Füllkurs, Menge und Gebühr müssen exakt gleich
   sein. Kontoverlauf: gleiche Zeilenzahl und gleiche Zeiten; `long`, `short` und `orders` exakt gleich; alle
   Geldspalten (`brutto`, `gebuehr`, `rebate`, `funding`, beide Netto-Spalten, `einsatz`) dürfen je Zeile um höchstens
   0,001 $ abweichen. Grund: Die Nachrechnung übernimmt das Funding und die Füllkurse aus den gerundeten
   Aufzeichnungen (vier bzw. zehn Nachkommastellen); größere Abweichungen wären ein Fehler und verhindern den Start.
2. *Werkzeug.* `nachrechnen.py` lädt einen Tag mehr Stundenkerzen, weil die Tagesregel die Kerze zum Tageswechsel mit
   der von 336 Stunden davor vergleicht. Für Test 2 und 3 ändert das nichts (wird mit der Byte-Gleichheit geprüft).
3. *Tagesverlust-Limit.* Es wirkt wie in Test 1 auch dann, wenn für den laufenden Tag noch keine Tagesrichtung
   übernommen werden konnte (dann wird geschlossen). In Test 4 steht es wie in Test 1 auf 100 % des Kapitals.
4. *Board.* Der Reiter „Test 4“ zeigt als gelbe Linie den Kurs, an dem die Richtung beim nächsten Stundenschluss um
   00:00 UTC dreht (Schluss 336 Stunden davor), nicht die Schwelle der laufenden Stunde. Die Reiter von Test 1 bis 3
   bleiben unverändert.

**Gegenprüfung von Test 4 (21.11.2026, drei unabhängige Prüfer, vor der Inbetriebnahme) und weitere Präzisierungen.**
Kein Blocker, kein Fehler in der Regel. (a) Ein Nachbau allein aus dem Wortlaut stimmt in 300 Zufallsszenarien (305.962
Läufe, auch mit Ausfällen über Mitternacht, fehlenden Kerzen und Gleichstand) nach jedem Lauf mit dem Bot überein, für
die Tagesregel und für die Stundenregel; 14 absichtlich eingebaute Fehler findet der Vergleich alle. (b) Gegenlesen von
Code, Lauf-Skript, Board und Inbetriebnahme: fünf kleine Punkte, alle unten aufgenommen. (c) Mutationsprüfung: Von 88
einzeln eingebauten Fehlern fanden meine Tests 57; 25 waren echte Lücken in den Tests (nicht im Code), 6 gleichwertig.
13 Zusatztests der Prüfer schließen alle 25 Lücken. Referenz, Vergleich und Zusatztests sind übernommen
(`tests/tagesregel_gegenpruefung`, `tests/test_vorwaertstest_tagesregel_zusatz.py`).

5. *Eine Minute Abstand zum Tageswechsel (neu, vor dem Start).* Übernommen wird frühestens 60 Sekunden nach 00:00 UTC.
   Grund: Der vierte Durchgang des Laufs von 23:59 beginnt wenige Sekunden vor Mitternacht; rutscht er darüber, würde er
   Sekunden nach dem Kerzenschluss entscheiden, und Yubit kennzeichnet nicht, ob ein Schlusskurs endgültig ist.
   Planmäßig übernimmt weiter der Lauf um 00:04 UTC. Die Referenz der Prüfer wurde um genau diese Bedingung ergänzt;
   ohne die Ergänzung meldet ihr Vergleich die Änderung, mit ihr stimmen wieder alle 300 Szenarien.
6. *Übernahme nur mit Marktdaten.* In einem Lauf wird nur für Coins übernommen, für die auch die Marktdaten des Laufs
   vorliegen (wie in Test 1 nötig, um zu handeln: letzte Stundenkerze, deren Gegenstück, Kontrakt, Ticker, Orderbuch).
   Fehlen sie, wartet die Übernahme auf den nächsten Lauf; betroffen ist nur das Aufholen, nicht der Lauf um 00:04.
7. *Ziel für den ganzen Tag.* Gelingt die Order im Lauf der Übernahme nicht, versucht es jeder weitere Lauf des Tages
   erneut (wie Test 1). Nach einer Schließung durch das Tagesverlust-Limit wird erst mit der Übernahme des nächsten
   Tages wieder eingestiegen.
8. *Nicht festgelegt und nicht benutzt:* die Tagesregel zusammen mit Gewinnziel, Stop oder nachgezogenem Stop.
9. *Betrieb.* Der vierte Durchgang rechnet nur, wenn der nachgerechnete Stand vorhanden ist (sonst begänne ein neues
   Konto mit Einstiegen von jetzt). Dauerhaft anhalten lässt sich Test 4 über die Datei `lauf_tag/ANGEHALTEN` im
   Repository; eine STOPP-Datei auf dem Server wirkt sofort, übersteht aber das Erneuern des Klons dort nicht (das gilt
   schon für Test 3). Auf dem Reiter „Test 4“ zählt die Kopfzeile bis 00:04 UTC.
10. *Genauer Umfang des Belegs „Test 1 bis 3 unberührt“.* Nachgerechnet werden mit altem und neuem Code die
   Aufzeichnungen von Test 1 mit den Einstellungen von Test 1, 2 und 3 und zusätzlich die eigenen Aufzeichnungen von
   Test 2 und Test 3; dazu kommen die Zufallsvergleiche der Prüfer (180 und 150 Durchgänge ohne Unterschied).
11. *Prüfung vor dem Start geschärft.* Der Vergleich mit Test 1 bricht ab, wenn nicht für jeden der zehn Coins die
   Tagesrichtung des letzten Lauftags im Zustand steht und zur Position passt (sonst wäre die Nachrechnung nur eine
   Kopie von Test 1).
- **Offen, nicht Teil dieser Inbetriebnahme:** Bericht und Board-Daten laden bei jedem Lauf die ganze `spannen.csv`.
  Nach Rechnung eines Prüfers stößt das bei etwa 116 Tagen Laufzeit (ungefähr März 2027) an die 300 MB des Containers
  und beträfe dann alle Tests. Das muss vorher behoben werden (eigener Arbeitspunkt).

---

## 54. Datensammler auf dem Server, festgelegt vor der Inbetriebnahme (21.11.2026, Auftrag des Auftraggebers)

**Auftrag.** Frische Daten auf dem Server sammeln: Yubit-Orderbücher, Aktien- und Indexkontrakte; wo Yubit zu wenig
hergibt, dürfen ähnliche Orderbücher anderer Börsen dazukommen. Kein Experiment, sondern Betrieb: Hier steht, was
gesammelt wird, warum so, und was für die spätere Auswertung gilt.

**Erkundung (gemessen am Samstag, 21.11.2026, 11:44 bis 12:02 UTC; zwei unabhängige Erkunder, nur lesend).**
- **Yubit:** Ein Abruf liefert die Ticker aller 561 Kontrakte (Geld, Brief, Mark, Index, offene Kontrakte,
  Funding-Vorschau; keine Mengen). Orderbuch bis 500 Stufen je Seite; bei Aktien-Kontrakten ist das das ganze Buch
  (61 bis 117 Stufen). Minuten-, Stunden- und Tageskerzen sowie der Funding-Verlauf reichen bis zum ersten Handelstag
  zurück (NVDAUSDT: 18.03.2026) und lassen sich jederzeit nachladen. **Nicht nachladbar** sind Orderbuch (Spanne,
  Tiefe), offene Kontrakte und Index. Ein Abruflimit ist nicht dokumentiert und steht in keiner Antwort; 30 Abrufe
  nacheinander und 20 mit vier gleichzeitigen blieben ohne Drosselung. Es gibt kein Feld, das Aktien, Indizes und
  Rohstoffe kennzeichnet: Die Zuordnung läuft über eine eigene Liste (196 der 197 Kontrakte aus Runde 10, ANTHROPICUSDT
  ist nicht mehr gelistet; dazu 26 weitere nach Name und Merkmalen, darunter NDX100USDT und SP500USDT).
- **Aktien-Kontrakte handeln rund um die Uhr,** auch am Wochenende (NVDAUSDT: 1.000 Trades in 36 Minuten am
  Samstagmittag; Spanne über 196 Kontrakte im Median 5,8 bp, 90 % unter 20,5 bp; Wochenend-Umsatz etwa ein Sechstel
  bis die Hälfte eines Werktags).
- **Binance** führt dieselben Kontrakte. Das öffentliche Archiv hat für alle 197 Symbole Kerzen (ab 1 Minute), Tiefe
  alle 30 Sekunden in Bändern von ±0,2 bis ±5 %, offene Kontrakte alle 5 Minuten, Trades und Funding, jeweils ab dem
  Listungstag (meist Mai bis September 2026) und rund 7 bis 10 Stunden nach Tagesende. **Es fehlt die Spanne**
  (bester Geld-/Briefkurs): die gibt es nur live.
- Andere Börsen (Bybit, Bitget, OKX, Gate, MEXC, Hyperliquid, Kraken) führen laut eigenen Angaben ähnliche Kontrakte.
  Von hier nicht erreichbar, Abdeckung und Archive ungeklärt; sie werden nicht verwendet.

**Was der Sammler mitschreibt** (alle fünf Minuten, als letzter Schritt des Server-Laufs):
1. *Yubit-Ticker:* Geld, Brief, Mark, Index, offene Kontrakte, Funding-Vorschau. Gruppe A (zehn Coins und 222
   Aktien-, Index- und Rohstoff-Kontrakte) in jedem Lauf, alle übrigen Kontrakte einmal je Stunde.
2. *Yubit-Orderbuch,* verdichtet: bester Geld-/Briefkurs mit Menge, Zahl der Stufen, Volumen je Seite gesamt und in
   Bändern von 5 bis 500 Basispunkten um die Mitte, Kosten einer Marktorder über 1.500, 5.000 und 25.000 USDT. Die
   zehn Coins in jedem Lauf, die 222 Kontrakte reihum (jeder alle 15 Minuten), rund 84 Abrufe je Lauf mit zwei
   gleichzeitigen Abrufen und Pause.
3. *Binance:* bester Geld-/Briefkurs mit Menge, Mark, Index und Funding der Gruppe A alle 15 Minuten (zwei Abrufe).
- **Nicht** mitgeschrieben wird, was sich nachladen lässt: Kurse und abgerechnetes Funding bei Yubit; Tiefe, Kerzen
  und offene Kontrakte bei Binance (Archiv).

**Ablage.** Je Tabelle und Stunde eine CSV-Datei auf dem Server; nach Ablauf der Stunde gepackt in einen eigenen
Daten-Zweig je Monat (`odingate-marktdaten-JJJJ-MM`), getrennt vom Bot-Zweig. Nur öffentliche Marktdaten, keine
Handelsdaten. Erwartet werden 2 bis 3,5 MB je Tag; der Wert wird nach den ersten Tagen gemessen und berichtet, danach
kann der Takt über die Einstellung angepasst werden. Auf dem Server gilt eine Obergrenze von 1,5 GB.

**Schutz der Tests.** Der Sammler läuft erst, wenn Test 1 bis 4 gesichert sind; eigene Zeitgrenze (120 Sekunden),
eigener Ordner außerhalb des Bot-Repositorys, endet auch bei Fehlern ohne Fehlercode. Meldet eine Börse „zu viele
Abrufe“, pausiert er für diese Börse eine Stunde. Ausschalten über `sammler/config.json` (`aktiv`) oder eine
STOPP-Datei auf dem Server.

**Grenzen.** Fünf-Minuten-Schnappschüsse, keine lückenlosen Orderbuch- oder Trade-Daten. Tiefe ist angezeigte Tiefe,
nicht geprüfte Ausführbarkeit. Das tatsächliche Abruflimit von Yubit ist unbekannt. Der Binance-Teil ließ sich von
hier nicht ausprobieren (Schnittstelle in dieser Umgebung gesperrt, vom Server aus erreichbar); ob er liefert, zeigen
die ersten Daten. Gleicher Symbolname bei Yubit und Binance ist noch nicht als gleicher Basiswert geprüft.

**Regeln für die spätere Auswertung.**
- Technische Kontrollen (Vollständigkeit, Plausibilität, Größe) sind jederzeit erlaubt.
- Jede Suche nach Handelsregeln in diesen Daten oder im Binance-Archiv der Aktien-Kontrakte braucht vorher eine
  eigene Festlegung mit Trennung in Entwicklungs- und Prüfzeitraum. Vom Binance-Archiv dieser Kontrakte sind bisher
  nur die Tageskurse bis 31.10.2026 benutzt (E25, E26); zur Erkundung des Formats wurden je zwei Tagesdateien von
  NVDAUSDT (14.11. und 19.11.2026) geöffnet sowie Stundenumsätze und Funding von NVDAUSDT bei Yubit angesehen.
- Was der Sammler ab jetzt bei Yubit mitschreibt, ist vorwärts erhoben.

**Gegenprüfung des Datensammlers (21.11.2026, drei unabhängige Prüfer, vor der Inbetriebnahme) und Änderungen danach.**
Kein Weg gefunden, auf dem der Sammler die Tests oder den Bot-Klon stört (Ende-Code, Arbeitsbaum, Abbruch durch die
Zeitgrenze selbst nachgestellt). Die Tabelleninhalte sind richtig gerechnet (54 echte Orderbücher und 6.000 künstliche
gegen einen unabhängigen Nachbau; Handrechnung an fünf Büchern). Die Mutationsprüfung fand 65 Lücken in meinen Tests
(211 eingebaute Fehler, 142 gefunden); 26 der 42 Zusatztests der Prüfer gelten unverändert und sind übernommen, der
Gegenstand der übrigen 16 wird nach dem Umbau in `tests/test_sammler.py` neu geprüft (zusammen 63 Tests).
Vor dem Start geändert:
1. *Veröffentlichen wiederaufnehmbar.* Gepackte Stunden liegen in `bereit/<Monat>/`, bis sie im Daten-Zweig sind; was
   aussteht, ergibt sich allein aus diesem Ordner. Vorher stand es nur im Gedächtnis des Laufs: Ein Abbruch am
   Monatswechsel hätte die letzte Stunde des Monats still verloren.
2. *Arbeitsordner ersetzbar.* Ist er unvollständig eingerichtet, verloren oder lehnt das Ziel dreimal ab, beginnt der
   Sammler einen weiteren Zweig mit Nummer (`odingate-marktdaten-JJJJ-MM-2`). Es wird nichts geholt, überschrieben oder
   gelöscht. Vorher konnte ein solcher Zustand jeden weiteren Push dauerhaft verhindern.
3. *Zeit.* Eine Gesamtfrist (95 s) für den ganzen Durchlauf, jeder Abruf höchstens 12 s auch bei tröpfelnder Antwort,
   der Zustand wird vor jedem git-Schritt gesichert. Das Lauf-Skript gibt dem Sammler höchstens 120 s und nur, wenn
   vom ganzen Lauf noch genug übrig ist (`timeout -k 10`); sonst wird er in diesem Lauf ausgelassen.
4. *Störungen der Börse.* Neben HTTP 403/418/429 gilt auch eine Drossel-Meldung im Antwortkörper als Bremse. Fünf
   gescheiterte Orderbuch-Abrufe in Folge beenden die Runde, drei solche Läufe nacheinander führen zur Stunden-Pause.
   Die Pause wird sofort gespeichert. Höchstens zwei gleichzeitige Abrufe mit 0,3 s Pause.
5. *Daten.* Eigener Laufzähler statt Uhrzeit (der Sammler beginnt nur Sekunden nach einer Fünf-Minuten-Grenze; die
   Runde wäre sonst gesprungen). Binance-Zeilen tragen die Zeit des Kurses laut Binance (`zeit_ms`). Bester Kurs und
   Menge kommen aus denselben Stufen wie die Rechnung. Bandgrenzen gehören zum Band. Halbe Zeilen nach einem Abbruch
   werden abgeschlossen; bei geänderten Spalten beginnt eine neue Datei. Die Platzgrenze wird in jedem Lauf neu
   gemessen. Commits im Daten-Zweig tragen die Identität „OdinGate Sammler“.
- **Bekannte Folgen der Bauart (kein Fehler):** Der Sammler läuft nur, wenn alle vier Tests durchgelaufen sind und der
  Server am Zug ist; fällt ein Lauf aus, fehlen diese fünf Minuten (erkennbar in der Tabelle `laeufe`). Der Binance-Teil
  ist von hier weiterhin nicht ausprobiert. Der Daten-Zweig wächst geschätzt um rund 100 MB je Monat; nach den ersten
  Tagen wird gemessen.

---

## 55. Test 4 in Betrieb (21.11.2026, Ergebnis zu Abschnitt 53)

- **Bedingungen vor dem Start erfüllt.** Die Nachrechnung von Test 4 aus den Aufzeichnungen von Test 1 stimmt mit Test 1
  überein: zehn Orders exakt, Kontoverlauf in allen 1.702 Zeilen (größter Abstand einer Geldspalte 0,0001 $); für
  alle zehn Coins steht die Tagesrichtung vom 21.11. (Short) im Zustand. Damit war auch die Tagesrichtung vom 15.11.
  00:00 UTC für alle zehn Coins Short (sonst wären die Einstiege abgewichen).
- **Test 1 bis 3 unberührt.** Alter und neuer Code liefern in fünf Nachrechnungen (Aufzeichnungen von Test 1 mit den
  Einstellungen von Test 1, 2 und 3; eigene Aufzeichnungen von Test 2 und Test 3; je 1.697 Läufe) byte-gleiche Dateien
  (30 Dateien). Die Inbetriebnahme hat an den Ordnern, Einstellungen und Board-Dateien von Test 1 bis 3 nichts geändert
  (vor jedem Push geprüft).
- **Ablauf.** Schritt A (Code und Nachrechnung bis 13:34 UTC) um 13:35:21 UTC, direkt nach einem Lauf des Servers. Der
  Lauf von 13:39 UTC lief wie erwartet noch mit dem alten Skripttext (drei Durchgänge). Schritt B (Nachrechnung bis
  13:39 UTC) um 13:40:24 UTC. Der Lauf von 13:44 UTC rechnete alle vier Tests; der Commit von Test 4 stammt vom Server
  (13:45:30 UTC). Kein Lauf von Test 1 bis 3 ging verloren oder wurde doppelt gebucht (je 1.704 Zeilen, wie Test 4).
  Zwei Trockenübungen gegen ein lokales Übungs-Repository gingen voraus (die zweite mit dem endgültigen Code ohne
  Fehlschlag), einschließlich Fehler im vierten Durchgang und Notbremse.
- **Stand beim Start:** Test 4 hält dieselben zehn Shorts wie Test 1 (netto mit Rebate +1.193 $ um 13:45 UTC).
  `nachgerechnet_bis` = 21.11.2026 13:39 UTC; vorwärts gewertet wird ab dem Lauf von 13:44 UTC. Die erste eigene
  Entscheidung fällt am 22.11. um 00:04 UTC.
- **Zum Lesen der Zahlen:** Test 4 rechnet im selben Lauf rund eine Minute nach Test 1 und damit zu etwas anderen
  Kursen; sein Zeitstempel kann um eine Minute neben dem von Test 1 liegen. Kleine Unterschiede im Kontostand sind
  deshalb kein Regel-Unterschied. Der kommt erst mit dem ersten Signalwechsel.

---

## 56. Festlegung E28 (vor der Rechnung, 21.11.2026, Einwand des Auftraggebers „wir haben mehr als Krypto“): Orderbuch-Regel und Wochenende auf Aktien-, Index- und Rohstoff-Kontrakten (H28, H29)

**Anlass.** Auf Nicht-Krypto ist bisher nur auf Tageskursen geprüft worden (Trend in mehreren Längen, Übernacht-Effekt,
Paare, Momentum, Nasdaq nach Bitcoin; alles verworfen). Seit der Erkundung vom 21.11. (Abschnitt 54) ist bekannt: Die
Kontrakte handeln rund um die Uhr, und es gibt für sie feine Daten seit dem Listungstag. Damit sind zwei Dinge
prüfbar, die es bisher nicht waren. Beide werden einmal gerechnet, ohne Einstellungen zu suchen.

**Berichtigung zu meiner Ankündigung an den Auftraggeber:** Von den drei Regeln der Schattentests lässt sich nur die
Orderbuch-Stütze (OS-1.1) unverändert übertragen. Die beiden Beobachtungsregeln aus der Strategie-Fabrik hängen am
Rechenrahmen der zehn Coins (feste Coin-Liste, eigene Kosten- und Filterfelder); sie zu übertragen hieße, sie
umzubauen. Das geschieht hier nicht.

### Teil 1 (H28): Orderbuch-Stütze OS-1.1, unverändert, auf 30 Kontrakten

- **Regel:** `forschung/papier/strategien/orderbuch_stuetze.py` mit den eingefrorenen Parametern von OS-1.1
  (Tiefe bis 5 %, Fenster 288, mindestens 200 Werte, Einstieg |z| ≥ 3, Ausstieg z < 1, höchstens 48 Kerzen). Die
  Prüfsumme der Regel wird vor der Rechnung gegen die Freigabe von OS-1.1 geprüft.
- **Kontrakte (Regel, aus schon bekannten Angaben, nicht aus Ergebnissen):** Aktien-, Index- und Rohstoff-Kontrakte der
  Liste aus E25, erster Handelstag bei Binance spätestens 31.07.2026, gemessene Yubit-Spanne (Stichprobe vom
  14.11.2026) höchstens 10 bp; davon die 30 mit dem höchsten Werktagsumsatz bei Binance (Median bis 31.10.2026).
- **Daten:** Binance-Archiv je Kontrakt vom ersten Tag bis 20.11.2026: Orderbuch-Tiefe (Bänder ±5 %), 5-Minuten-Kerzen,
  Funding. Signal und Kurse von Binance als Stellvertreter für Yubit, wie in den Schattentests.
- **Abrechnung wie im Papier-Runner:** Ein- und Ausstieg zur Eröffnung der nächsten 5-Minuten-Kerze; je Order 8 bp
  Gebühr und als Slippage die gemessene Yubit-Spanne des Kontrakts (Median der Stichprobe, mindestens 0,5 bp);
  Funding laut Binance. Je Trade in Basispunkten: netto mit 85 % Rebate (n85) und ohne Rebate (n0). Gewertet werden
  Einstiege ab dem dritten Handelstag des Kontrakts (zwei Tage Vorlauf).
- **Hauptzahl:** Mittel von n85 über alle Trades aller 30 Kontrakte. Zufallsprüfung: Kalendertage mit Zurücklegen
  ziehen (5.000 Ziehungen, Startwert 28; alle Trades eines Einstiegstags bleiben zusammen), einseitig „Mittel > 0“.
- **Einstufung:** **C** (Kandidat für einen Papier-Beobachtungstest), wenn mindestens 300 Trades vorliegen, das Mittel
  von n85 positiv ist mit p < 2,5 %, und es in beiden Hälften positiv ist (Einstiege bis 31.08.2026 / ab 01.09.2026).
  **B** (schwacher Hinweis, kein Test), wenn das Mittel positiv ist, aber eine Bedingung fehlt. Sonst **A** (verworfen).
- **Nur Bericht:** Mittel vor Kosten (ob das Signal überhaupt etwas weiß), n0, je Gruppe (Index/ETF, Einzelaktie,
  Rohstoff), Einstiege am Wochenende gegen Werktage, Tabelle je Kontrakt. Kein Vergleichslauf auf den zehn Coins: Für
  sie bleibt der Tresor ab 04/2025 zu.

### Teil 2 (H29): Was am Wochenende geschieht, wenn die Börsen geschlossen sind

- **Frage:** Setzt sich die Bewegung eines Kontrakts über das Wochenende am Montag fort, oder kehrt sie um? Zweiseitig,
  ohne Vorfestlegung der Richtung (für beides gibt es Gründe: dünner Markt übertreibt, oder der dünne Markt preist
  Nachrichten nur teilweise ein).
- **Kontrakte:** alle der Liste aus E25 mit gemessener Yubit-Spanne höchstens 10 bp. **Daten:** Stundenkerzen von Yubit
  (echte Kurse des Handelsplatzes) vom ersten Tag bis einschließlich Montag, 16.11.2026.
- **Festlegung (UTC, Eröffnung der Stundenkerze):** a = Samstag 01:00 (alle US-Handelsplätze geschlossen),
  b = Sonntag 23:00 (vor Öffnung der asiatischen Börsen), c = Montag 21:00 (nach US-Börsenschluss in Sommer- und
  Winterzeit). Wochenend-Bewegung W = Kurs(b)/Kurs(a) − 1, Montags-Bewegung M = Kurs(c)/Kurs(b) − 1. Ein Wochenende
  zählt, wenn mindestens 30 Kontrakte alle drei Kurse haben.
- **Hauptzahl:** Je Wochenende die Steigung von M auf W über die Kontrakte (beide um das Mittel des Wochenendes
  bereinigt, je Wochenende bei 1 % und 99 % gestutzt). Geprüft wird, ob das Mittel dieser Steigungen über die
  Wochenenden von null abweicht (t-Test, zweiseitig, p < 2,5 %).
- **Falls ja, die Handelsfassung in der gefundenen Richtung:** am Sonntag 23:00 UTC gegen (Umkehr) oder mit
  (Fortsetzung) der Wochenend-Bewegung, gewichtet nach deren Abstand vom Mittel, Summe der Beträge = 1 × Konto, ohne
  Netto-Richtung; Ausstieg Montag 21:00 UTC. Kosten je Kontrakt: zwei Orders zu 8 bp (mit und ohne Rebate) plus
  gemessene Spanne. Ergebnis je Wochenende, Mittel, t-Wert, erste und zweite Hälfte der Wochenenden.
- **Einstufung:** **C** (Kandidat für eine Papier-Beobachtung), wenn die Steigung gesichert ist und die Handelsfassung
  mit Rebate im Mittel positiv ist mit t > 2 und in beiden Hälften positiv. **B**, wenn nur die Steigung gesichert
  ist. Sonst **A**. Weil die Richtung aus denselben Daten stammt, ist auch C nur ein Kandidat, kein Beleg.
- **Nur Bericht:** Bewegung des ganzen Korbs am Wochenende gegen Montag, je Gruppe, Zahl der Wochenenden und Kontrakte.

**Gemeinsames.**
- Zwei Hauptprüfungen, deshalb je 2,5 % statt 5 %.
- **Grenzen, vorab:** Die Historie ist kurz (die meisten Kontrakte seit Mai bis Juli 2026, rund 20 bis 25
  Wochenenden). Signale und Kurse in Teil 1 stammen von Binance, nicht von Yubit. Die Spannen stammen aus einer
  Stunde an einem Samstag. Mehr als ein Kandidat für einen Papier-Beobachtungstest kann nicht herauskommen.
- **Verbraucht:** Mit dieser Rechnung ist die Historie der Kontrakte bis 20.11.2026 für diese beiden Fragen angesehen.
  Ein Prüfzeitraum wird nicht zurückgehalten; Bestätigung gibt es nur vorwärts (Sammler, Papier-Test).
- Kein Nachjustieren: keine anderen Schwellen, Zeitpunkte oder Kontraktlisten nach dem ersten Ergebnis.

**Präzisierungen zu Abschnitt 56 (21.11.2026, vor der Rechnung; Daten sind geladen, aber nicht ausgewertet).**
1. *Teil 1, Kontrakte nach der Regel:* SNDK, XAU, SOXL, SKHYNIX, SPCX, XAG, CL, MU, SKHY, BZ, SOXS, SAMSUNG, DRAM, CRCL, QQQ,
   INTC, MRVL, NVDA, PAXG, EWY, MUU, MSTR, TSLA, NBIS, LITE, AMD, AAOI, CBRS, GOOGL, ZHIPU (je …USDT). Größte Spanne der
   Auswahl 6,7 bp, kleinster Werktagsumsatz rund 40 Mio. USDT. KORU und SNXX fallen wegen ihrer Spanne heraus.
2. *Teil 1, Abrechnung:* Die Reihe eines Kontrakts wird wie im Papier-Runner als Ganzes gerechnet (fehlt das Übergewicht
   einer Kerze, gibt es dort keinen Einstieg). Trades, die am Datenende noch offen sind, zählen nicht. Tag eines Trades
   ist der UTC-Tag des Einstiegs. Zufallsprüfung: aus den Tagen mit mindestens einem Einstieg so viele Tage mit
   Zurücklegen ziehen, wie es solche Tage gibt; Kennzahl ist das Mittel über alle Trades der gezogenen Tage; p ist der
   Anteil der Ziehungen mit Mittel ≤ 0.
3. *Teil 1, Gruppen (nur Bericht):* Rohstoff = XAU, XAG, CL, BZ, PAXG; Fonds = SOXL, SOXS, QQQ, EWY, DRAM, MUU; alle
   übrigen Einzelwerte.
4. *Teil 2, Daten:* Stundenkerzen von Yubit liegen für 133 der 134 Kontrakte vor (ANTHROPICUSDT ist nicht mehr gelistet).
   Ein Kurs zählt nur, wenn es die Stundenkerze mit genau diesem Beginn gibt (kein Auffüllen).
5. *Teil 2, Rechnung:* Je Wochenende erst stutzen (W und M je bei ihrem 1 %- und 99 %-Punkt über die Kontrakte), dann das
   Mittel abziehen. Steigung = Summe(W·M) / Summe(W²). Geprüft wird das Mittel der Steigungen gegen null (t-Test über
   die Wochenenden). Handelsfassung: Gewichte aus dem gestutzten, bereinigten W, geteilt durch die Summe der Beträge
   (Umkehr: Gewicht = −W, Fortsetzung: +W); Ertrag mit dem unveränderten M; Kosten je Kontrakt = Betrag des Gewichts ×
   2 × (Gebühr 8 bp, mit Rebate 1,2 bp, plus gemessene Spanne, mindestens 0,5 bp). Hälften: die erste Hälfte der
   Wochenenden (bei ungerader Zahl eines mehr) gegen den Rest.

**Unabhängige Gegenprüfung von E28 und weitere Präzisierungen (21.11.2026, vor der Rechnung; es ist weiterhin kein Ergebnis gerechnet).**
Zwei Prüfer ohne Kenntnis voneinander: einer hat die Rechnung aus der Festlegung nachgebaut und auf künstlichen Reihen
verglichen (3.421 Trades, 2.373 Wochenenden, 416 Zufallsprüfungen: keine Abweichung, auch nach den Änderungen unten), der
andere hat gegengelesen und Fehler absichtlich eingebaut. Kein Befund, der die Rechnung verhindert. Was sich daraus ändert:

6. *Teil 1, Funding im November:* Das Archiv hat für November 2026 noch keine Funding-Datei (alle 30 Kontrakte, geprüft
   21.11.). Ein Trade, der in einem Monat ohne Funding-Angabe beginnt oder endet, wird mit Funding 0 gebucht und
   gekennzeichnet. Die Hauptzahl bleibt wie festgelegt das Mittel über alle Trades. Nur Bericht: Zahl dieser Trades und
   die Kennzahlen ohne sie.
7. *Teil 1, Vorlauf:* „Ab dem dritten Handelstag“ heißt: Einstiege ab erster Kerze + 48 Stunden (so rechnet auch der
   Papier-Runner).
8. *Teil 2, „je Gruppe“ entfällt:* Eine Gruppenliste gibt es nur für die 30 Kontrakte aus Teil 1. Für die 133 Kontrakte
   gibt es keine vorab feste Einteilung; eine jetzt gebaute wäre bei mehreren Kürzeln unsicher. Es wird nichts
   ersatzweise aufgeteilt.
9. *Teil 2, Sonderfälle:* Ein Wochenende, an dem sich W über die Kontrakte nicht unterscheidet (Steigung nicht
   bestimmbar), zählt nicht und wird unter „ausgelassen“ ausgewiesen. Bei weniger als drei zählenden Wochenenden gibt es
   keinen Test und die Einstufung ist A.
10. *Ablage:* Neben den Kennzahlen werden abgelegt: jeder Trade (`ergebnisse/e28_trades.csv`), je Kontrakt die fehlenden
    Archivdateien und Monate ohne Funding, der Stand des Programms, und in der Handelsfassung von Teil 2 jedes Wochenende
    vor Kosten, mit und ohne Rebate. Schon bekannt (aus dem Laden, keine Ergebnisse): Die Tiefe-Dateien vom 07. bis
    09.10.2026 fehlen im Archiv für alle Kontrakte (an diesen Tagen kein Signal), bei XAU, XAG und PAXG zusätzlich der
    14.01.2026. In Teil 2 erfüllen 34 Wochenenden die 30-Kontrakte-Regel (ab 28.03.2026, von 32 auf 133 Kontrakte wachsend).
11. *Tests:* Die Prüfer-Tests sind übernommen (`tests/test_e28_zusatz.py`), dazu Tests für den Hauptlauf auf
    künstlichen Dateien, die Funding-Kennzeichnung und das Laden; zusammen 33. Das Laden schreibt eine Datei jetzt erst
    vollständig und benennt sie dann um.

*Grenzen, die die Prüfer zusätzlich nennen und die im Bericht stehen müssen:* (a) In Teil 2 steckt der Kurs von Sonntag
23:00 in W und in M; ein ungenauer Kurs in dieser dünnen Stunde erzeugt von selbst einen Anschein von Umkehr. (b) Bei
weniger als 100 Kontrakten greift das Stutzen bei 1 % und 99 % kaum; ein einzelnes ruhiges Wochenende kann das Mittel
der Steigungen stark bewegen. (c) An zwei Montagen (25.05. und 07.09.2026) war die US-Börse geschlossen; sie bleiben
wie festgelegt in der Rechnung. (d) Die Spanne je Kontrakt stammt aus einer Samstagsstunde und wird je Order voll
angesetzt (eher vorsichtig).

## 57. Ergebnis E28 (21.11.2026): Orderbuch-Regel auf Nicht-Krypto verworfen, Wochenend-Umkehr schwacher Hinweis (H28: A, H29: B)

Einmal gerechnet mit dem Programmstand `1bf224de` (nach Festlegung und Präzisierungen 1 bis 11), ohne Nachjustieren.
Ablage: `forschung/ergebnisse/e28_nichtkrypto.json`, `forschung/ergebnisse/e28_trades.csv`. **Gegenrechnung:** Die
unabhängige Referenz des Prüfers auf denselben echten Daten ergibt in beiden Teilen dieselben Zahlen (Trades, Mittel,
Hälften, Steigungen je Wochenende, t, p, Handelsfassung, Einstufung; p der Zufallsprüfung 0,765 gegen 0,763 bei anderem
Startwert).

### Teil 1 (H28): OS-1.1 unverändert auf 30 Aktien-, Fonds- und Rohstoff-Kontrakten: **A (verworfen)**

| | Trades | vor Kosten | mit Rebate (n85) | ohne Rebate (n0) |
|---|---|---|---|---|
| alle 30 Kontrakte | 6.945 | +5,4 bp | **−1,2 bp** | −14,8 bp |
| Einstiege bis 31.08.2026 | 4.533 | +7,0 bp | +0,6 bp | −13,0 bp |
| Einstiege ab 01.09.2026 | 2.412 | +2,5 bp | −4,6 bp | −18,2 bp |
| Einzelwerte | 4.198 | +6,7 bp | +0,3 bp | −13,3 bp |
| Fonds | 1.134 | +6,8 bp | −0,5 bp | −14,1 bp |
| Rohstoffe | 1.613 | +1,1 bp | −5,7 bp | −19,3 bp |
| Einstieg am Wochenende | 1.666 | +1,4 bp | −5,1 bp | −18,7 bp |
| Einstieg an Werktagen | 5.279 | +6,7 bp | +0,0 bp | −13,6 bp |

- Zufallsprüfung (481 Tage mit Einstieg, 5.000 Ziehungen): p = 0,76, also kein positives Mittel. Trefferquote 46 %.
- Kosten je Trade: zweimal die gemessene Spanne = 4,3 bp, Gebühr 2,4 bp mit Rebate (16 bp ohne), Funding +0,07 bp.
- 13 von 30 Kontrakten sind mit Rebate positiv (am besten SOXL +24,9 bp bei 188 Trades, SPCX, MU, AAOI je rund +11;
  am schlechtesten XAG −12,9, MUU −11,8, SOXS −11,0, CL −9,9). Das ist nachträglich angesehen und keine Auswahlregel.
- Funding für November fehlt bei 688 Trades (mit 0 gebucht); ohne sie −1,7 bp bei 6.257 Trades. Am Urteil ändert es nichts.
- **Lesart:** Das Orderbuch weiß auch hier etwas (vor Kosten +5,4 bp je Trade), aber Spanne und Gebühr sind größer.
  Selbst mit vollem Rebate bleibt nichts, ohne Rebate ist es klar negativ. In der zweiten Hälfte ist auch das
  Roh-Signal schwächer. Kein Papier-Test.

### Teil 2 (H29): Wochenende gegen Montag auf 133 Kontrakten: **B (schwacher Hinweis, kein Test)**

- 34 Wochenenden (28.03. bis 14.11.2026), je 32 bis 133 Kontrakte (Median 94). Zwölf frühere Wochenenden hatten weniger
  als 30 Kontrakte; keines fiel wegen fehlender Streuung aus.
- **Steigung von Montag auf Wochenende:** Mittel −0,47, Median −0,31, t = −2,82, **p = 0,008** (Grenze 2,5 %): gesichert,
  Richtung **Umkehr**. 22 von 34 Wochenenden negativ. Der Korb als Ganzes zeigt nichts (Korrelation +0,03).
- **Handelsfassung (gegen die Wochenend-Bewegung, Sonntag 23:00 bis Montag 21:00 UTC), je Wochenende in % des Kontos:**
  vor Kosten +0,62 %, mit Rebate **+0,53 %**, ohne Rebate +0,39 %. t = 1,79 (verlangt > 2), erste Hälfte +0,23 %, zweite
  Hälfte +0,83 %, 20 von 34 Wochenenden positiv, schlechtestes −2,5 %, bestes +5,7 %, Streuung 1,7 %.
- **Einstufung B:** Die Steigung ist gesichert, die Handelsfassung nicht (t unter 2). Nachträglich angesehen: Ohne die
  zwei besten Wochenenden läge das Mittel bei +0,27 % statt +0,53 %; das Ergebnis hängt also an wenigen Wochenenden.
- **Lesart:** Es gibt einen plausiblen Grund (am Wochenende handelt der Kontrakt ohne die echte Börse; was dort nur
  Rauschen war, holt der Montag zurück), und die Messung zeigt in diese Richtung. Belegt ist es nicht: 34 Wochenenden,
  Richtung aus denselben Daten gewählt, und die Grenzen (a) bis (d) aus Abschnitt 56. Vor allem (a) kann das Ergebnis
  ganz oder teilweise erzeugen: Der Kurs von Sonntag 23:00 steckt im Signal und im Ertrag.

### Nachträgliche Diagnose zu Grenze (a), festgelegt vor ihrer Rechnung (kein Urteil, die Einstufung B bleibt)

Eine einzige Zusatzrechnung, um den Messfehler aus dem gemeinsamen Kurs zu prüfen: Das Signal wird eine Stunde früher
gemessen, W′ = Kurs(Sonntag 22:00) / Kurs(Samstag 01:00) − 1; der Ertrag bleibt M = Kurs(Montag 21:00) /
Kurs(Sonntag 23:00) − 1. Damit teilen Signal und Ertrag keinen Kurs mehr. Sonst alles wie in Teil 2 (dieselben
Wochenenden und Regeln; ein Kontrakt zählt, wenn er alle vier Kurse hat; Richtung der Handelsfassung fest: Umkehr).
Zum Vergleich wird die Hauptfassung auf genau denselben Kontrakten daneben gestellt. Berichtet werden Mittel und t der
Steigungen und das Mittel der Handelsfassung mit Rebate. **Lesart vorab:** Bleibt die Steigung ähnlich negativ, erklärt
der gemeinsame Kurs den Befund nicht. Fällt sie deutlich gegen null, war der Befund überwiegend ein Messfehler, und
die Vorwärts-Messung unten lohnt nicht. Mehr Varianten werden nicht gerechnet.

**Ergebnis der Diagnose (21.11.2026, `forschung/ergebnisse/e28_diagnose.json`, Programm `e28_diagnose.py`).** Alle 34
Wochenenden, alle Kontrakte haben auch den Kurs von Sonntag 22:00.

| | Steigung Mittel | Median | t | Handelsfassung mit Rebate | t |
|---|---|---|---|---|---|
| Hauptfassung (Signal bis Sonntag 23:00) | −0,47 | −0,31 | −2,82 | +0,53 % je Wochenende | 1,79 |
| Signal eine Stunde früher (bis 22:00) | −0,51 | −0,38 | −2,95 | +0,71 % je Wochenende | 2,44 |

Die Steigung bleibt gleich negativ, wenn Signal und Ertrag keinen Kurs teilen. **Der gemeinsame Kurs erklärt den Befund
also nicht.** Das ist eine nachträgliche Rechnung auf angesehenen Daten: Die Einstufung bleibt **B**, und das t von
2,44 ist kein Bestehen der vorab festgelegten Prüfung. Offen bleiben die kurze Historie, die Abhängigkeit von wenigen
Wochenenden und die Frage, ob man am Sonntagabend zu diesen Kursen wirklich handeln kann (Stundenkurse sind keine
Geld- und Briefkurse). Beantworten kann das nur eine Messung vorwärts mit echten Geld- und Briefkursen; die liefert
der Datensammler (Abschnitt 54). Deren Festlegung folgt als eigener Abschnitt, sobald der Sammler nachweislich liefert.
