# Zusammenfassung 1: Experimente 1 bis 10

Automatisch erzeugt aus `engine/experimente.json`. Rückrechnungen, kein echtes Geld, keine Anlageberatung.

## Experimente

| Nr. | ID | Idee | Einstufung | Ergebnis |
|---|---|---|---|---|
| 1 | E01 | Orderbuch-Tiefe nahe am Kurs (1 %) | A (verworfen) | roh +0,9 bp, N85 −3,2 bp |
| 2 | E02 | Gegenposition bei extremem Aufschlag | A (verworfen) | roh +0,3 bp, N85 −7,5 bp |
| 3 | E03 | Funding-Termin, 60 Minuten davor und danach | A (verworfen) | Funding +6,6 bp, N85 −0,5 bp |
| 4 | E04 | Nachlauf der Altcoins hinter BTC | A (verworfen) | roh +1,5 bp, N85 −7,4 bp |
| 5 | E05 | Erholung nach Zwangsliquidationen | A (verworfen) | roh +9,2 bp (t 0,6), N85 +1,3 bp |
| 6 | E06 | Funding-Abgriff in 10 Minuten | A (verworfen) | Kurs gibt das Funding zurück, N85 −0,1 bp |
| 7 | E07 | Ursachenanalyse Orderbuch-Tiefe, 17 Einstellungen | B (interessant, unbestätigt) | roh bis t 6,7; Zufallsprüfung p 0,09 |
| 8 | E08 | Vollprüfung Orderbuch-Stütze 1.0 | D (Prüfung formal bestanden) | Validierung N85 +2,9 bp, ohne Rebate −10,7 bp |
| 9 | E09 | Bestätigung auf sieben frischen Coins | B (interessant, unbestätigt) | roh +3,6 bp (t 2,1), nach Kosten negativ |
| 10 | E10 | Ausstiegs-Engine, 8 Varianten | B (interessant, unbestätigt) | Signal-Ausstieg vorn (p 0,05); Trailing schadet |

Verteilung: 6 × verworfen, 3 × interessant, unbestätigt, 1 × Prüfung formal bestanden.

## Papier-Tests

- **OS-1.1 Orderbuch-Stütze 1.1** (Start 2026-11-16, Hebel 3): Status wartet auf Daten, Trades 0, Kontostand 5000 $, mit Rebate 0.0 %, ohne Rebate 0.0 %. Rückrechnung formal bestanden (Entwicklung und Validierung), schwach belegt, nur mit Rebate positiv. Vorwärtstest ohne Beweiskraft vor rund 400 Trades.
- **Test 1 – 14-Tage-Trend, nur Umkehrsignal**: Status läuft, Kontostand 5093.09 $, mit Rebate 1.862 %, Stand 2026-11-15 22:17 UTC.
- **Test 2 – 14-Tage-Trend mit Stop 5 % / Ziel 15 %**: Status läuft, Kontostand 4828.57 $, mit Rebate -3.429 %, Stand 2026-11-15 22:18 UTC.

## Offene Forschungsfragen

- H07 Orderbuch-Signal in 1-Minuten-Auflösung: Das Signal verfällt schnell (5 Minuten Verzug kosten 40 %). Feinere Auflösung könnte früher einsteigen.
- H08 Kauf- und Verkaufsdruck je Minute als zweite Bestätigung: Aggressive Marktorders in Signalrichtung zeigen, dass die Stütze im Orderbuch tatsächlich angenommen wird.
- H09 Orderbuch-Stütze nur bei hoher Schwankung: E12: Wirkung fast nur im oberen Drittel der Schwankung. Eigene Regel, eigene Version.
- H10 Wiederkehrende Tageszeit-Muster (gleiche Uhrzeit an Vortagen): Wiederkehrende Orderströme großer Teilnehmer.
- H11 Eröffnungsspanne der Handelssitzungen: Neue Information zu Sitzungsbeginn; Ausbrüche in Runde 11 nur in Trendrichtung getestet.
- H12 Lücke der CME-Futures am Wochenende: Rückkehr zum Freitagsschluss.
- H13 Große Einzelaufträge (Einzeltrade-Daten): Informierte Händler handeln groß und aggressiv.
- H14 Eigener Sammler für das Yubit-Orderbuch: Ausführbarkeit bei Yubit messen: Spanne und Tiefe zur Signalzeit; Grundlage für passive Orders.

## Risiken

- Rebate von 85 % unbestätigt; ohne Rebate ist bisher keine kurzfristige Regel positiv.
- Signale stammen aus Binance-Daten, gehandelt würde bei Yubit.
- Margin- und Liquidationsregeln von Yubit sind unbekannt; gerechnet wird mit Annahmen.
