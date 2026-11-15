# Papier-Test OS-1.1: Orderbuch-Stütze Version 1.1

Festgelegt am 15.11.2026, vor dem Start. Freigabe: automatisch nach Auftrag des Auftraggebers vom 15.11.2026
(nur Papierhandel). Kein echtes Geld, keine Orders an einer Börse.

1. **Ziel.** Prüfen, ob die Regel auf Daten nach ihrer Festlegung dieselbe Richtung und Größe zeigt wie in der
   Validierung (roh +8,3 bp, netto mit Rebate +4,4 bp je Trade). Der Test kann einen Vorteil in absehbarer Zeit nicht
   beweisen; bei rund 2,5 Trades am Tag bräuchte das mehr als zwei Jahre. Er kann ihn aber früh widerlegen.
2. **Art.** Schattentest: Signal aus den täglich veröffentlichten Binance-Archivdateien des Vortags, Buchung zu
   Binance-Eröffnungskursen mit dem eingefrorenen Kostenmodell (Taker 0,08 %, Rebate 85 % angenommen, Slippage wie in
   der Rückrechnung). Keine Füllungen bei Yubit; die Ausführbarkeit dort misst dieser Test nicht.
3. **Zeitraum.** Start 16.11.2026 00:00 UTC. Erste Zwischenwertung nach 200 Trades, Hauptwertung nach 400 Trades
   (rund fünf Monate), Ende spätestens nach 1.000 Trades.
4. **Erfolg (Hauptwertung).** Rohe Kursbewegung im Mittel positiv und netto mit Rebate positiv. Das gilt als
   „nicht widerlegt“, nicht als Beweis.
5. **Abbruch.** Kontostand unter 70 % des Startkapitals, Liquidation im Modell, oder nach 400 Trades rohe
   Kursbewegung im Mittel negativ. Der Runner setzt die ersten beiden selbst um.
6. **Parameter.** Ausschließlich die in `konfiguration.json` eingefrorenen. 5.000 $ Papier-Kapital, Hebel 3, feste
   Größe 5.000 $ je Position, BTC, ETH, SOL. Jede Änderung wäre eine neue Version mit eigenem Test.
7. **Technische Ausfälle.** Der Test wird bei jedem Lauf vollständig aus den Archivdaten neu berechnet; ein
   ausgefallener Lauf verliert nichts. Fehlen Archivdaten länger als drei Tage, zeigt die Übersicht eine Datenlücke.
8. **Datenqualität.** Lückenlose 5-Minuten-Kerzen; fehlende Orderbuch-Werte erzeugen kein Signal. Funding wird
   nachgebucht, sobald Binance die Monatsdatei veröffentlicht; bis dahin ist es als ausstehend gekennzeichnet.
9. **Pausieren und Beenden.** `steuerung.json`: `pausiert` hält den Test an, `beendet` mit Zeitpunkt schließt ihn ab.
