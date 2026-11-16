# Zusammenfassung 2: Experimente 11 bis 20

Automatisch erzeugt aus `engine/experimente.json`. Rückrechnungen, kein echtes Geld, keine Anlageberatung.

## Experimente

| Nr. | ID | Idee | Einstufung | Ergebnis |
|---|---|---|---|---|
| 11 | E11 | Kombination mit dem 14-Tage-Trend | – (Analyse) | Korrelation −0,03 |
| 12 | E12 | Marktphasen | – (Analyse) | Wirkung vor allem bei hoher Schwankung |
| 13 | E13 | Orderbuch-Stütze 1.1 in der Validierung | D (Prüfung formal bestanden) | N85 +4,4 bp (t 1,1), ohne Rebate −9,2 bp |
| 14 | E14 | Strategie-Fabrik, Generation 1: 340.200 Kandidaten aus 63 Signalen in sechs Familien | A (verworfen) | 1.622 bestehen die Kostenstufe im Training; bester t-Wert 4,6 liegt im Zufallsbereich (Reality Check p 0,98) |
| 15 | E15 | Strategie-Fabrik, Generation 2 (Evolution, 182.460 Kandidaten) und Schlussprüfung der 1.199 Finalisten | A (verworfen) | Schlussprüfung: 60 mit p unter 5 % bei 60 zufällig erwarteten; keiner validiert; Median netto −2,5 bp je Trade |
| 16 | E16 | Yubit-Kosten in bewegten Minuten (Messung, 1.264 Punkte) und Zusatzrechnung der Schlussprüfung mit milder Kostenannahme | B (interessant, unbestätigt) | Kosten je Order 1–2,4 bp, kein Anstieg bis 100 bp Kerzenspanne (heftige Kerzen fehlen noch); mit milden Kosten 123 statt 60 p-Werte unter 5 %, ein Kandidat besteht die übliche, keiner die strenge Korrektur; kein Status geändert |
| 17 | E17 | Strategie-Fabrik, Generation 3: wiederkehrende Tageszeit-Muster (H10), 108 Kandidaten | A (verworfen) | kein Kandidat mit Vorteil vor Gebühr (bester t 1,7); beide Richtungen verlieren, Median −5,4 bp je Trade im Training; keine Finalisten |
| 18 | E18 | Strategie-Fabrik, Generation 4: Orderbuch-Tiefe aus dem letzten 30-Sekunden-Schnappschuss (H16, H07), 288 Kandidaten | A (verworfen) | kein Kandidat mit Vorteil vor Gebühr (bester t 1,4); frisches Signal nicht besser als das Kerzenmittel (Median −0,05 bp, in 48 % der Paare besser); keine Finalisten |
| 19 | E19 | Idee des Auftraggebers: gleichzeitig Long und Short (zwei Börsen), Verlierer früh schließen, Ziel 2:1 | A (verworfen) | vor Kosten null bis leicht negativ (Gewinnerseite erreicht Ziel in 52–66 % statt der nötigen 67 %); nach Kosten −9 bis −15 bp je Paar mit Rebate, −36 bis −42 bp ohne |
| 20 | E20 | Idee des Auftraggebers: Scalping in Richtung des 14-Tage-Trends (Auszählung von 21.030 schon gerechneten Kandidaten) | B (interessant, unbestätigt) | Rücksetzer handeln: vor Gebühr negativ (Median −4,2 bp, 1 Finalist); Fortsetzung handeln: 61 Finalisten, 75 % in der Schlussprüfung positiv, bestes Muster 12-Stunden-Momentum mit Nachzug, nicht validiert |

Verteilung: 5 × verworfen, 2 × interessant, unbestätigt, 1 × Prüfung formal bestanden, 2 × Analyse.

## Papier-Tests

- **B-24332e4d Beobachtung (nicht validiert): Orderbuch-Tiefe 3 % bei hoher Schwankung 1.0** (Start 2026-11-17, Hebel 3): Status wartet auf Daten, Trades 0, Kontostand 5000 $, mit Rebate 0.0 %, ohne Rebate 0.0 %. NICHT validiert. Bester von 1199 Finalisten der Strategie-Fabrik (p = 0.000312), besteht die Korrektur für die vielen gleichzeitig geprüften Regeln aber nur mit der ruhigen Kostenannahme, nicht mit der strengen. Schlussprüfung netto mit Rebate 21.58 bp je Trade, ohne Rebate 7.98 bp. Beobachtungstest: Nur neue Daten können klären, ob etwas daran ist. Schlussprüfung für Orderbuch-Signale nicht unberührt.
- **B-dc1d27a3 Beobachtung (nicht validiert): Gegen einseitigen Kaufdruck, Altcoins 1.0** (Start 2026-11-17, Hebel 3): Status wartet auf Daten, Trades 0, Kontostand 5000 $, mit Rebate 0.0 %, ohne Rebate 0.0 %. NICHT validiert. Regel der Strategie-Fabrik, in Training, Auswahl- und Schlussprüfung positiv (Schlussprüfung netto mit Rebate +181,8 bp je Trade, ohne Rebate +168,2 bp), aber nur 50 Trades in neun Monaten: nicht von Glück zu unterscheiden (p = 0,07) und nach Korrektur für die vielen gleichzeitig geprüften Regeln nicht bestanden. Ausgewählt nach dem besten Ergebnis in der Auswahlprüfung, nicht nach der Schlussprüfung. Beobachtungstest: Nur neue Daten können klären, ob etwas daran ist. Die Regel handelt selten (rund sieben Trades im Monat) und ohne Stop.
- **L-dc1d27a3 Live-Beobachtung (nicht validiert): Gegen einseitigen Kaufdruck, Altcoins 1.0** (Start 2026-11-17, Hebel 3): Status noch kein Lauf, Trades 0, Kontostand 5000 $, mit Rebate 0 %, ohne Rebate 0 %. NICHT validiert. Regel der Strategie-Fabrik, in Training, Auswahl- und Schlussprüfung positiv (Schlussprüfung netto mit Rebate +181,8 bp je Trade, ohne Rebate +168,2 bp), aber nur 50 Trades in neun Monaten: nicht von Glück zu unterscheiden (p = 0,07) und nach Korrektur für die vielen gleichzeitig geprüften Regeln nicht bestanden. Ausgewählt nach dem besten Ergebnis in der Auswahlprüfung, nicht nach der Schlussprüfung. Beobachtungstest: Nur neue Daten können klären, ob etwas daran ist. Die Regel handelt selten (rund sieben Trades im Monat) und ohne Stop.
- **OS-1.1 Orderbuch-Stütze 1.1** (Start 2026-11-16, Hebel 3): Status wartet auf Daten, Trades 0, Kontostand 5000 $, mit Rebate 0.0 %, ohne Rebate 0.0 %. Rückrechnung formal bestanden (Entwicklung und Validierung), schwach belegt, nur mit Rebate positiv. Vorwärtstest ohne Beweiskraft vor rund 400 Trades.
- **Test 1 – 14-Tage-Trend, nur Umkehrsignal**: Status läuft, Kontostand 5365.26 $, mit Rebate 7.305 %, Stand 2026-11-16 13:08 UTC.
- **Test 2 – 14-Tage-Trend mit Stop 5 % / Ziel 15 %**: Status läuft, Kontostand 5108.8 $, mit Rebate 2.176 %, Stand 2026-11-16 13:08 UTC.

## Offene Forschungsfragen

- H08 Kauf- und Verkaufsdruck je Minute als zweite Bestätigung: Aggressive Marktorders in Signalrichtung zeigen, dass die Stütze im Orderbuch tatsächlich angenommen wird.
- H09 Orderbuch-Stütze nur bei hoher Schwankung: E12: Wirkung fast nur im oberen Drittel der Schwankung. Eigene Regel, eigene Version.
- H11 Eröffnungsspanne der Handelssitzungen: Neue Information zu Sitzungsbeginn; Ausbrüche in Runde 11 nur in Trendrichtung getestet.
- H12 Lücke der CME-Futures am Wochenende: Rückkehr zum Freitagsschluss.
- H13 Große Einzelaufträge (Einzeltrade-Daten): Informierte Händler handeln groß und aggressiv.
- H14 Eigener Sammler für das Yubit-Orderbuch: Ausführbarkeit bei Yubit messen: Spanne und Tiefe zur Signalzeit; Grundlage für passive Orders.
- H15 Yubit-Spannen in bewegten Phasen messen: Fast alle Finalisten der Fabrik handeln direkt nach heftigen Kerzen. Ob dort bei Yubit überhaupt zu vertretbaren Kosten gehandelt werden kann, entscheidet über die ganze Familie.
- H17 Weniger Kandidaten, schärfere Vorauswahl: Lehre aus Generation 1 und 2: Die Stufen 1 bis 3 halten Zufallstreffer kaum auf; 1.199 Finalisten machen die Schlussprüfung fast unbestehbar. Künftige Generationen sollten klein sein (höchstens einige hundert Kandidaten aus einer begründeten Idee).

## Risiken

- Rebate von 85 % unbestätigt; ohne Rebate ist bisher keine kurzfristige Regel positiv.
- Signale stammen aus Binance-Daten, gehandelt würde bei Yubit.
- Margin- und Liquidationsregeln von Yubit sind unbekannt; gerechnet wird mit Annahmen.
