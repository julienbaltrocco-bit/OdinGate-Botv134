# Papier-Test B-24332e4d: Beobachtung (nicht validiert): tiefe_3, vol_hoch

Festgelegt am 2026-11-16, vor dem Start. **Nicht validiert.** Der Test ist nur vorbereitet und läuft erst nach ausdrücklicher Freigabe des Auftraggebers. Die Regel ist ab heute eingefroren; gewertet wird ab dem Startdatum, auch wenn die Freigabe später kommt (jeder Lauf rechnet vollständig neu, es geht nichts verloren). Nur Papierhandel, keine Orders.

1. **Ziel.** Prüfen, ob die Regel nach ihrer Festlegung weiter verdient. Rückrechnung in der Schlussprüfung: netto mit Rebate
   21.58 bp je Trade, ohne Rebate 7.98 bp, 524 Trades in neun Monaten.
2. **Art.** Schattentest aus den täglichen Binance-Archivdateien (ein Tag Verzug), Buchung mit dem eingefrorenen Kostenmodell.
3. **Regel.** Signal tiefe_3, Schwelle 1.5, mit dem Signal, Filter vol_hoch, geprüft alle 60 Minuten, Ausstieg signal_h720. Märkte: BTC, ETH, SOL. Hebel 3, 5.000 $ Papier-Kapital, feste Größe je Coin.
4. **Zeitraum.** Start 2026-11-17 00:00 UTC. Zwischenwertung nach 100 Trades, Hauptwertung nach 300 Trades oder zwölf Monaten.
5. **Erfolg.** In der Hauptwertung netto mit Rebate im Mittel positiv. Das gilt als „nicht widerlegt“, nicht als Beweis.
6. **Abbruch.** Kontostand unter 70 % des Startkapitals oder Liquidation im Modell (setzt der Runner selbst um); in der
   Hauptwertung netto mit Rebate negativ.
7. **Unverändert.** Code und Einstellung sind im Ordner `code/` und in `konfiguration.json` eingefroren (Prüfsumme).
8. **Ausfälle.** Jeder Lauf rechnet den Test vollständig neu; ein ausgefallener Lauf verliert nichts.
