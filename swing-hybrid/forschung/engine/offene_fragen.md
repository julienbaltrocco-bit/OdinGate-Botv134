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
