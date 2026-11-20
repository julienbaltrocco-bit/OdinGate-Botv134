# Offene Fragen an den Auftraggeber

## 16.11.2026 (Zyklus mit Generation 3 und 4)

1. **Ablauf in frischer Sitzung.** `trichter.py statistik` und `bericht.py` lesen nur die lokale Datenbank, die nach
   einem Neustart leer ist. Unverändert ausgeführt würden sie `statistik.json`, `kandidaten.parquet` und
   `zaehlung.json` mit dem Stand allein der neuen Generation überschreiben. In diesem Zyklus so gelöst: Statistik nicht
   neu gerechnet (sie wertet ohnehin nur Generation 1 aus); vor `bericht.py` das Archiv in die lokale Datenbank
   zurückgelesen. Frage: Soll das fest in den Auftrag (oder in die Programme), oder ist ein anderer Weg gewünscht?
2. **Kostenbasis.** Die Yubit-Spannen-Stichprobe vom 14.11.2026 (`data/processed/yubit_spannen_stichprobe.csv`) liegt
   nicht im Repository und lässt sich nicht neu erzeugen. Die daraus abgeleiteten Werte stehen jetzt in
   `fabrik/slippage_gemessen.json` (aus dem Prüfbeleg, drei Nachkommastellen). Frage: Soll die Stichprobe selbst ins
   Repository, oder sollen die Kosten künftig aus der wachsenden Messreihe des Papier-Bots (E16) neu bestimmt werden?
3. **Arbeitsumgebung.** Die Anleitung im Auftrag reicht nicht ganz: zusätzlich nötig waren das Paket `pyyaml`,
   `scripts/positionierung_laden.py` (zehn Coins) und die Orderbuch-Tiefe für alle zehn Coins, nicht nur BTC/ETH/SOL.

### Antworten (16.11.2026, Hauptsitzung, nach der Nachkontrolle des ersten Nachtlaufs)

Die drei Fragen betreffen den technischen Ablauf, nicht die Strategie; sie sind in den Programmen gelöst und brauchen
keine Entscheidung des Auftraggebers.

1. **Ablauf in frischer Sitzung: in den Programmen gelöst.** Das Archiv liegt jetzt in Teilen (`kandidaten.parquet`
   eingefroren für Generation 1 und 2, je spätere Generation eine eigene kleine Datei). `bericht.py` zählt immer über
   Archiv plus lokale Datenbank und bricht ab, wenn das eingefrorene Archiv verändert wurde. `trichter.py statistik`
   und `stufe3` lassen die Dateien im Repository unverändert, wenn es in der Sitzung nichts Neues zu prüfen gibt.
2. **Kostenbasis: eingefroren.** `fabrik/slippage_gemessen.json` enthält die Werte der Stichprobe vom 14.11.2026 in
   voller Genauigkeit und ist die einzige Quelle. Die Kosten werden nicht laufend aus der wachsenden Messreihe neu
   bestimmt, sonst wären Generationen untereinander nicht vergleichbar. Die Messreihe (E16) dient dazu, die Annahme
   zu prüfen; eine Änderung wäre eine eigene, vorab festgelegte Entscheidung.
3. **Arbeitsumgebung: Anleitung in `AUFTRAG.md` ergänzt** (`pyyaml`, Positionierungsdaten, Tiefe für alle zehn Coins).

## 17.11.2026 (Zyklus mit Generation 5)

1. **`trichter.py stufe3` ohne neue Finalisten.** Erreicht ein Kandidat Stufe 2, scheitert aber in Stufe 3, schreibt das
   Programm `finalisten.json` trotzdem neu: Kopfzeilen (Zahl aus Stufe 2, Gründe, „robust“) zeigen dann nur die neue
   Generation, und die Gruppengrößen der 1.199 früheren Finalisten stehen alle auf 1. Finalisten und Tagesreihen sind
   gleich. In diesem Zyklus von Hand auf den gesicherten Stand zurückgesetzt. Vorschlag: Datei nur schreiben, wenn es
   neue Finalisten gibt, oder die alten Angaben fortführen. (Technischer Ablauf, keine Strategie-Entscheidung.)
2. **Kostenmessung:** 31 von 200 nötigen Messpunkten über 100 bp nach zwei Tagen. Bei diesem Tempo dauert es rund zwei
   Wochen; ein bewegter Markttag kann das stark verkürzen.

### Antworten (17.11.2026, Hauptsitzung, nach der Nachkontrolle)

1. **`trichter.py stufe3`: im Programm gelöst.** Gibt es weder neue Finalisten noch neue Gruppenmitglieder, bleiben
   `finalisten.json` und `finalisten_reihen.npz` unverändert. Kommen welche dazu, behalten die früheren Finalisten ihre
   Gruppengröße, und die Kopfzahlen laufen über alle Chargen weiter (die Angaben nur zur letzten Charge stehen unter
   `letzte_charge`). Geprüft mit der nachgerechneten Generation 5: ein Kandidat aus Stufe 2, in Stufe 3 verworfen,
   Dateien unverändert.
2. **Kostenmessung:** zur Kenntnis; weiter nur die Zahl der Messpunkte notieren, bis 200 über 100 bp vorliegen.

## 18.11.2026 (Zyklus ohne neue Generation)

1. **Minuten-Simulator (Rest von H07):** Plan und Tests stehen im Protokoll, Abschnitt 36. Der nächste Zyklus beginnt mit
   dem Bau, wenn hier nichts anderes steht. Frage: Ist der Aufwand (rund zwei Sitzungen, Erfolg unsicher) gewünscht, oder
   soll die Forschung warten, bis die Kostenmessung (62 von 200 Messpunkten über 100 bp) oder die Papier-Tests Neues liefern?
2. **Protokoll:** Die Abschnittsnummer 34 ist doppelt vergeben (Festlegung Generation 5 und Nachkontrolle vom 17.11.).
   Nicht geändert, weil andere Unterlagen auf die Nummern verweisen können; dieser Zyklus zählt mit 36 weiter.

## 19.11.2026 (Zyklus ohne Rechnung)

1. Die Frage vom 18.11. (Minuten-Simulator bauen oder warten) blieb ohne Antwort; Baustein 1 ist wie angekündigt gebaut
   (Protokoll Abschnitt 37). Der nächste Zyklus würde die erste Minuten-Generation (nur Kaufdruck, als Paare) festlegen
   und rechnen. Soll das nicht geschehen, bitte hier vermerken.

## 20.11.2026 (Zyklus mit E22)

1. Die Frage vom 18. und 19.11. ist erledigt: E22 ist gerechnet und verworfen, H07 abgeschlossen (Protokoll Abschnitt 39).
2. **Wie weiter?** Im Baukasten ist keine offene Hypothese mehr, die als kleine Generation mit neuer Information taugt
   (Stand wie in Abschnitt 36). Ohne neue Vorgabe schreiben die nächsten Zyklen nur die Kostenmessung fort (93 von 200)
   und enden danach, wie im Auftrag unter „Was als Nächstes sinnvoll ist“, Punkt 4, vorgesehen. Neue Datenquellen
   (H13 Einzeltrades, H14 eigener Orderbuch-Sammler) oder neue Ideen brauchen eine Entscheidung des Auftraggebers.
