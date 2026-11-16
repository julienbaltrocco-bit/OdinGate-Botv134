# Papier-Test B-dc1d27a3: Beobachtung (nicht validiert): Gegen einseitigen Kaufdruck, Altcoins

Festgelegt am 2026-11-16, vor dem Start. **Nicht validiert.** Beobachtungstest, vom Auftraggeber am 16.11.2026 freigegeben (protokoll.md Abschnitt 28). Nur Papierhandel, keine Orders.

1. **Ziel.** Prüfen, ob die Regel nach ihrer Festlegung weiter verdient. Rückrechnung in der Schlussprüfung: netto mit Rebate
   181.84 bp je Trade, ohne Rebate 168.24 bp, 50 Trades in neun Monaten.
2. **Art.** Schattentest aus den täglichen Binance-Archivdateien (ein Tag Verzug), Buchung mit dem eingefrorenen Kostenmodell.
3. **Regel.** Signal kaufdruck_48, Schwelle 3.5, gegen das Signal, Filter vol_hoch, geprüft alle 5 Minuten, Ausstieg h720_zielnachzug, Bestätigung durch volspitze_1. Märkte: XRP, DOT, DOGE, ADA, LINK, AVAX, LTC. Hebel 3, 5.000 $ Papier-Kapital, feste Größe je Coin.
4. **Zeitraum.** Start 2026-11-17 00:00 UTC. Zwischenwertung nach 50 Trades, Hauptwertung nach 150 Trades oder zwölf Monaten.
5. **Erfolg.** In der Hauptwertung netto mit Rebate im Mittel positiv. Das gilt als „nicht widerlegt“, nicht als Beweis.
6. **Abbruch.** Kontostand unter 70 % des Startkapitals oder Liquidation im Modell (setzt der Runner selbst um); in der
   Hauptwertung netto mit Rebate negativ.
7. **Unverändert.** Code und Einstellung sind im Ordner `code/` und in `konfiguration.json` eingefroren (Prüfsumme).
8. **Ausfälle.** Jeder Lauf rechnet den Test vollständig neu; ein ausgefallener Lauf verliert nichts.
