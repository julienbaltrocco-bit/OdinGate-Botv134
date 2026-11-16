# OdinGate Strategie-Fabrik: Bericht nach den ersten zwei Generationen

Stand: 16.11.2026, 01:05 UTC. Zweig `claude/alpha-forschung-r1`, Ordner `swing-hybrid/forschung/fabrik/`. Alles ist
Rückrechnung auf historischen Daten. Kein echtes Geld, keine Orders, keine Anlageberatung. Die bestehenden Tests 1
und 2, der Papier-Test OS-1.1 und das bisherige Board sind unverändert.

## Kurzfassung

1. **Die Fabrik läuft.** Ein Generator erzeugt Kandidaten aus Signal, Schwelle, Richtung, Filter, Takt, Ausstieg und
   Markt; ein schneller Simulator rechnet rund 64.000 Kandidaten je Minute auf vier Kernen.
2. **Gerechnet wurden 522.660 Kandidaten** (dazu 522.360 in einem ersten Lauf, der nach der Gegenprüfung verworfen
   und wiederholt wurde).
3. **Ergebnis: kein einziger Kandidat besteht die Schlussprüfung.** Von 1.199 Finalisten haben 60 einen p-Wert unter
   5 %, genau so viele, wie reiner Zufall erwarten lässt. Im Mittel kippt das Ergebnis von +29 Basispunkten je Trade
   im Training auf −2,5 in der Schlussprüfung.
4. **Deshalb wurde kein neuer Papier-Test gestartet.** Die Bedingung dafür war vorab festgelegt und ist nicht erfüllt.
5. **Einzige Auffälligkeit bleibt die Orderbuch-Tiefe.** Sie stellt den besten Finalisten und ein Viertel der
   kleinsten p-Werte, besteht aber die Korrektur für die vielen Versuche nicht. Diese Idee läuft bereits als
   Papier-Test OS-1.1.
6. **Das negative Ergebnis hängt teilweise an einer Kostenannahme.** Mit der milderen Annahme (Kosten wie im ruhigen
   Markt) hätten 123 statt 60 Finalisten einen p-Wert unter 5 %, und einer bestünde die übliche Korrektur, aber nicht
   die strenge. Eine erste Messung bei Yubit (1.264 Messpunkte, ein ruhiger Tag) spricht eher für die mildere
   Annahme, reicht für heftige Kerzen aber noch nicht aus. Siehe Abschnitt „Nachtrag: die Kostenfrage“.
7. **Ein Beobachtungstest ist vorbereitet, aber nicht gestartet.** Der beste Finalist ist nicht validiert. Seine
   Regel ist eingefroren (`papier/B-24332e4d/`); er läuft nur, wenn der Auftraggeber das ausdrücklich freigibt.

Ein Basispunkt (bp) ist ein Hundertstel Prozent. „p-Wert“ ist die Wahrscheinlichkeit, ein so gutes Ergebnis rein
zufällig zu sehen.

## Die zwölf Fragen

| Nr. | Frage | Antwort |
|---|---|---|
| 1 | Wie viele Kandidaten wurden erzeugt? | 522.660 eindeutige (Generation 1: 340.200, Generation 2: 182.460) |
| 2 | Wie viele wurden tatsächlich gerechnet? | alle 522.660; jeder mit gespeichertem Ergebnis. Dazu Lauf A mit 522.360, verworfen |
| 3 | Wie viele wurden aussortiert? | alle. 103.152 hatten zu wenige Trades, 401.116 keinen Vorteil vor Gebühr, 7.536 scheiterten an den Kosten, 7.194 an der Robustheit; die übrigen 3.662 bilden 1.199 Gruppen, deren Vertreter alle an der Schlussprüfung scheiterten |
| 4 | Wie viele sind nach Kosten positiv? | im Training 103.913 mit Rebate (29.341 ohne). Das ist die Zahl vor jeder Prüfung und sagt wenig. In der Schlussprüfung sind 521 der 1.199 Finalisten positiv (43 %) |
| 5 | Wie viele überstehen die robusten Prüfungen? | 3.662 bestehen Stufe 3 (in 1.199 Gruppen). Die Schlussprüfung besteht keiner |
| 6 | Wie viele gingen ins Paper Trading? | 0 neue. Es laufen weiter Test 1, Test 2 und OS-1.1. Ein Beobachtungstest (nicht validiert) ist vorbereitet und wartet auf Freigabe |
| 7 | Welche Familien zeigen mögliche Vorteile? | belegt keine. Auffällig, aber nicht gesichert: Orderbuch-Tiefe bei hoher Schwankung |
| 8 | Welche brauchen das Rebate? | praktisch alle. Ohne Rebate sind in der Schlussprüfung nur 240 der 1.199 Finalisten positiv, keiner davon gesichert |
| 9 | Welche funktionieren ohne Rebate? | keine nachweislich |
| 10 | Wie viele Experimente je Minute? | rund 64.000 Kandidaten je Minute, das sind rund 3.500 Coin-Rückrechnungen je Sekunde |
| 11 | Welche Prozesse laufen gerade? | siehe Abschnitt „Was tatsächlich läuft“ |
| 12 | Was lässt sich nach einer Unterbrechung fortsetzen? | siehe Abschnitt „Wiederaufnahme“ |

## Was gebaut wurde

- **Datenspeicher** (`daten.py`): zehn Coins auf einem gemeinsamen 5-Minuten-Raster von 07/2021 bis 03/2025, mit
  Kerzen, Volumen, Kauf-Marktorders, Funding, Open Interest, Long/Short-Verhältnissen, Aufschlag des Kontrakts und
  Orderbuch-Tiefe (ab 2023). Der Zeitraum ab 04/2025 ist gesperrt und wurde nicht geladen.
- **63 Signale in sechs Familien** (`signale.py`): Momentum (19), Mean Reversion (10), Volatilität (4), Cross-Asset
  (9), Derivate (11), Mikrostruktur (10); dazu zehn Marktphasen-Filter.
- **Generator** (`generator.py`): jede Einstellung genau einmal, Kennung aus dem Hash der Einstellung.
- **Simulator** (`kern.py`): Einstieg zur nächsten Eröffnung, Zeit-, Stop-, Ziel-, Nachzug- und Signal-Ausstieg,
  Stops gegen Hoch und Tief, Kurslücken, Funding, Slippage je Kerze.
- **Massenlauf** (`lauf.py`): vier Rechenkerne, Ergebnisse in einer Datenbank, wiederaufnehmbar je Aufgabe.
- **Trichter und Statistik** (`trichter.py`): fünf Stufen, Reality Check, Deflated Sharpe Ratio, Überanpassungsprüfung,
  Korrektur für viele Versuche (Benjamini-Hochberg und Benjamini-Yekutieli).
- **Evolution** (`evolution.py`): neue Varianten nur aus Gewinnern des Trainings.
- **Papier-Tests für Fabrik-Kandidaten** (`freigabe.py`, `papier_fabrik.py`): Risikoprüfung, eingefrorene Kopie des
  Codes je Test, eigener Ordner und eigenes Konto. Gebaut und getestet, aber mangels validierter Kandidaten nicht benutzt.

## Der Trichter in Zahlen

| Stufe | übrig |
|---|---|
| erzeugt und gerechnet | 522.660 |
| mindestens 200 Trades im Training | 419.508 |
| Stufe 1: Vorteil vor Gebühr | 18.392 |
| Stufe 2: nach vollen Kosten | 10.856 |
| Stufe 3: robust (Auswahlprüfung, Verzögerung, Kosten in bewegtem Markt, Nachbarn, Markt) | 3.662 |
| Finalisten (eine je Gruppe gleichlaufender Regeln) | 1.199 |
| Stufe 4: Schlussprüfung auf ungelesenen Daten | **0** |

Zeiträume: Training 08/2021 bis 06/2023, Auswahlprüfung 07/2023 bis 06/2024, Schlussprüfung 07/2024 bis 03/2025
(für Orderbuch-Signale Training 2023 und Auswahlprüfung 01 bis 06/2024). Die Schlussprüfung wurde genau einmal
geöffnet, für die zuvor eingefrorene Liste.

## Was die Schlussprüfung zeigt

| | Training | Auswahlprüfung | Schlussprüfung |
|---|---|---|---|
| Median netto je Trade der 1.199 Finalisten (mit Rebate) | +28,9 bp | +24,9 bp | **−2,5 bp** |

- 521 von 1.199 Finalisten sind in der Schlussprüfung positiv, also weniger als die Hälfte.
- 60 haben einen p-Wert unter 5 %. Zufällig zu erwarten: 60.
- Der beste (Orderbuch-Tiefe 3 %, hohe Schwankung, BTC/ETH/SOL) erreicht p = 0,0003. Für 1.199 gleichzeitig
  geprüfte Regeln läge die Grenze bei 0,00008.
- Nach Familie (Finalisten, davon positiv, davon p unter 5 %): Momentum 524, 44 %, 28 · Mean Reversion 294, 49 %,
  14 · Cross-Asset 163, 29 %, 1 · Mikrostruktur 152, 49 %, 15 · Derivate 37, 59 %, 2 · Volatilität 29, 0 %, 0.

Auch im Training selbst hob sich nichts vom Zufall ab: Der beste von 275.596 Kurs-Kandidaten hat einen t-Wert von
4,6; unter so vielen Versuchen ist das gewöhnlich (Reality Check p = 0,98, Deflated Sharpe Ratio 0,00).

## Nachtrag: die Kostenfrage

Maßgeblich für „validiert“ war, vorab festgelegt, die strenge Kostenannahme (je Order mindestens 5 % der Spanne der
letzten Kerze). Die folgenden zwei Punkte sind Zusatzangaben und ändern keinen Status.

| Schlussprüfung der 1.199 Finalisten | strenge Annahme (maßgeblich) | milde Annahme (Zusatz) |
|---|---|---|
| positiv | 521 | 696 |
| p-Wert unter 5 % (zufällig erwartet: 60) | 60 | 123 |
| besteht die übliche Korrektur (Benjamini-Hochberg) | 0 | 1 |
| besteht die strenge Korrektur (Benjamini-Yekutieli) | 0 | 0 |

- Der eine Kandidat ist in beiden Rechnungen derselbe und der beste: Orderbuch-Tiefe 3 %, hohe Schwankung,
  stündlich geprüft, BTC/ETH/SOL (Kennung `24332e4d3769`). Schlussprüfung: 524 Trades, mit Rebate +21,6 bp je Trade
  (strenge Kosten) bzw. +25,4 bp (milde Kosten), ohne Rebate +8,0 bp.
- **Messung E16 bei Yubit:** 1.264 Messpunkte des Papier-Bots (15.11. mittags bis 16.11. nachts, zehn Coins, Order
  über 1.500 $). Die Kosten je Order liegen bei 1 bis 2,4 bp und steigen mit der Kerzenspanne nicht erkennbar an;
  im bewegtesten Fünftel sind es 2,4 % der Spanne, nicht 5 %. Grenze: nur zwei Kerzen über 100 bp, ein ruhiger
  Sonntag. Für heftige Kerzen gibt es noch keine Messung; die Reihe wächst täglich.
- **Was das heißt:** Wer die milde Annahme für richtig hält, sieht doppelt so viele kleine p-Werte wie zufällig und
  einen knappen Treffer. Wer die strenge für richtig hält, sieht nichts. Entscheiden können das nur mehr Messungen
  in bewegtem Markt und neue Daten. Ein Beleg für eine profitable Strategie ist beides nicht.
- **Beobachtungstest B-24332e4d:** Für diesen einen Kandidaten ist ein Schattentest vorbereitet (Regel und Code
  eingefroren am 16.11.2026, Wertung ab 17.11.2026, Hebel 3, 5.000 $ Papier-Kapital). Er erfüllt die vorab
  festgelegte Bedingung für einen automatischen Papier-Test nicht und startet deshalb nur nach ausdrücklicher
  Freigabe. In der Rückrechnung wäre er bei Hebel 3 an 6 % der Starttage unter die Abbruchgrenze von 70 % gefallen,
  ohne Liquidation.

## Unabhängige Gegenprüfung

Drei Prüfer haben Signale, Buchung und Statistik mit eigenem Code nachgerechnet, bevor die Schlussprüfung geöffnet
wurde. Belege unter `fabrik/pruefung/`.

- **Kein Blick in die Zukunft gefunden.** Störungstests über alle 63 Signale, Filter und zehn Coins; 656 Kandidaten
  und 16 Einzelfälle stimmen mit der unabhängigen Nachrechnung überein.
- **Gefundene Fehler, vor der Schlussprüfung behoben:** der Verzögerungstest rechnete beim Signal-Ausstieg zwei
  Kerzen statt einer; die Zufallsprüfung war falsch gebildet (die anfangs genannten p-Werte 0,39 und 0,17 galten
  nicht); der Kosten-Stress war nicht das Doppelte; kleinere Punkte zu Datenlücken und zum Teiler bei BTC.
- **Wichtigster Einwand, kein Rechenfehler:** Die meisten Finalisten handeln direkt nach heftigen Kerzen. Die
  Slippage stammt aus einer ruhigen Messung und beträgt dort nur rund 2 % der Kerzenspanne. Deshalb gilt in Stufe 3
  und 4 ein strengeres Kostenmodell: je Order mindestens 5 % der Spanne der letzten Kerze. Das ist eine Annahme.
  Mit der einfachen Slippage wären in der Schlussprüfung 696 statt 521 Finalisten positiv (nachgerechnet, siehe
  „Nachtrag: die Kostenfrage“).
- **Einordnung des Prüfers:** Die Stufen 1 bis 3 halten Zufallstreffer kaum auf; allein aus Generation 1 wären je
  nach Annahme 50 bis 1.000 „robuste“ Zufallstreffer zu erwarten. Die Zahl der Finalisten ist daher kein Beleg.

## Was tatsächlich läuft

- **Massenrechnungen:** gerade keine. Beide Generationen, Statistik, Stufe 3 und Stufe 4 sind abgeschlossen.
- **Geplante Aufgabe „OdinGate Papier-Lauf“** (täglich 09:17 UTC): rechnet alle Papier-Tests und trägt den Stand in
  die Übersicht ein. Einmal erfolgreich gelaufen (15.11., rund 25 Sekunden).
- **Geplante Aufgabe „OdinGate Forschungszyklus“** (täglich 01:43 UTC): startet eine Forschungssitzung, die nach
  `engine/AUFTRAG.md` die Fabrik weiterführt. Eingerichtet, aber noch nicht gelaufen; ob sie in einer frischen
  Umgebung sauber durchläuft, zeigt erst der erste Lauf.
- **Bestehender Bot für Test 1 und 2:** unverändert, eigene Sitzung.
- **Kein dauerhafter Hintergrundprozess.** Die Umgebung ist ein Wegwerf-Container; Dauerbetrieb heißt hier: ein
  Zeitplan startet Läufe. Beide geplanten Aufgaben verbrauchen Kontingent des Claude-Abos.

## Wiederaufnahme

- **Innerhalb eines Laufs:** Der Massenlauf merkt sich jede erledigte Aufgabe in der Datenbank und setzt nach einem
  Abbruch bei der nächsten offenen fort.
- **Über Sitzungen hinweg:** Im Repository liegen alle Kandidaten mit Kennzahlen (`kandidaten.parquet`), die
  Finalisten mit Tagesreihen, die Schlussprüfung, das Protokoll und die Hypothesenliste. Eine neue Sitzung baut den
  Datenspeicher aus den öffentlichen Archiven neu (einige Minuten) und rechnet schon bekannte Kennungen nicht noch
  einmal in die Zählung.
- **Papier-Tests:** werden bei jedem Lauf vollständig neu berechnet; ein ausgefallener Lauf verliert nichts.
- **Nicht fortsetzbar ohne KI:** das Entwickeln neuer Ideen. Die Programme selbst laufen ohne KI.

## Wie es weitergeht

1. **Nicht mehr Varianten, sondern neue Information.** 1.199 gleichzeitig geprüfte Regeln machen die Schlussprüfung
   fast unbestehbar. Die nächsten Generationen sollen klein sein und eine begründete neue Idee prüfen.
2. **Kosten in bewegtem Markt weiter messen** (H15, erste Messung E16 liegt vor): Der bestehende Papier-Bot misst
   die Yubit-Spanne alle fünf Minuten. Sobald genug heftige Kerzen dabei sind, lässt sich entscheiden, ob 5 % der
   Kerzenspanne zu streng ist. Davon hängt die ganze Familie „Handeln nach heftigen Kerzen“ ab.
3. **Orderbuch-Tiefe vertiefen** (H16): mehr Information aus der einzigen Quelle, die immer wieder vorn liegt, mit
   wenigen vorab festgelegten Kandidaten.
4. **OS-1.1 laufen lassen.** Der Papier-Test prüft genau diese Idee auf neuen Daten.
5. **Unverändert offen:** die schriftliche Bestätigung von Yubit zu Rebate, Bot-Erlaubnis und Margin-Regeln.

## Ablage

| Pfad unter `swing-hybrid/forschung/` | Inhalt |
|---|---|
| `protokoll.md`, Abschnitte 19 bis 22 | Regeln vor der Rechnung, drei Nachträge vor der Schlussprüfung, Ergebnis, Kostenmessung und Zusatzangabe |
| `fabrik/` | Programme der Fabrik |
| `fabrik/ergebnisse/kandidaten.parquet` | alle 522.660 Kandidaten mit Kennzahlen und Verwerfungsgrund |
| `fabrik/ergebnisse/zaehlung.json`, `statistik.json` | Zählung, Durchsatz, Zufallsprüfungen |
| `fabrik/ergebnisse/finalisten.json`, `finalisten_reihen.npz`, `schlusspruefung.json` | eingefrorene Finalisten und Ergebnis der Schlussprüfung |
| `fabrik/ergebnisse/schlusspruefung_einfache_slippage.json`, `ergebnisse/e16_yubit_kosten_bewegung.json` | Zusatzrechnung mit milder Kostenannahme; Yubit-Kostenmessung |
| `papier/B-24332e4d/` | vorbereiteter Beobachtungstest (nicht validiert, wartet auf Freigabe) |
| `fabrik/pruefung/` | Skripte, Ausgaben und Urteile der drei unabhängigen Prüfer |
| `tests/test_fabrik_*.py` | Simulator gegen Referenzrechnung, Störungstest, Verzögerungstest |
| `engine/AUFTRAG.md`, `engine/hypothesen.json` | Dauerauftrag und Ideenliste für die nächsten Zyklen |
