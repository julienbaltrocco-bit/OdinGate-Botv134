# Übergabe für Dritte: Stand des Projekts und offene Fragen

Stand: 15.11.2026. Zweck: Außenstehende (Menschen oder andere KI-Assistenten) sollen den Stand prüfen und daraus
nächste Arbeitsschritte vorschlagen können. Alles hier ist Rückrechnung oder Papierhandel, kein echtes Geld.

> **Nachtrag 15.11.2026, unabhängiges Audit (Zwischenstand):** Mehrere Aussagen dieses Berichts sind zu stark
> formuliert, vor allem „belegt“, „ungesehener Prüfzeitraum“ sowie die Kennzahlen ohne Hinweis auf Rebate und Hebel.
> Die Rechnung selbst wurde bestätigt. Maßgeblich ist `swing-hybrid/reports/audit/zwischenbericht.md`, dort
> Abschnitt 6 „Korrekturen an früheren Aussagen“. Der Text unten ist unverändert.

## 1. Ziel und Rahmen

- Gesucht: eine regelbasierte Futures-Strategie für die Börse Yubit, die nach Gebühren profitabel ist und Umsatz
  erzeugt. Taker-Gebühr 0,08 %, Maker 0,04 %, davon kommen 85 % als Rebate zurück.
- Feste Regeln des Auftraggebers: kein Hochfrequenzhandel, keine Arbitrage zwischen Börsen, kein Handel gegen sich
  selbst, Hebel höchstens 5.
- Daten: Binance-USD-M-Futures (5-Minuten-Kerzen, Funding, Positionierungsdaten) 2020 bis 10/2026, Yubit-Spannen aus
  eigenen Messungen, Tageskurse klassischer Märkte von Yahoo Finance.

## 2. Was belegt ist

**Ein einziger Baustein hält der Prüfung stand: der 14-Tage-Trend.** Regel: Liegt der Schlusskurs der letzten vollen
Stunde über dem von vor 336 Stunden, long, sonst short. Zehn Coins (BTC, ETH, SOL, XRP, DOT, DOGE, ADA, LINK, AVAX,
LTC), jeder gleich groß, stündlich geprüft, sofortige Ausführung. Kein Gewinnziel, kein Stop; Ausstieg nur beim
Umkehrsignal.

| Zeitraum (Einsatz 100 %, ohne Hebel, Yubit-Kosten mit Rebate) | Ertrag pro Jahr | Sharpe | Größter Einbruch |
|---|---|---|---|
| Entwicklung 08/2021–03/2025 | +59 % | 0,95 | 25 % |
| Ungesehener Prüfzeitraum 04/2025–10/2026 | +16,5 % | 0,34 | 31 % |

- Robust gegen die Bauart: EMA-Kreuz, Donchian, stufenlose Größe und ähnliche Varianten erreichen Sharpe 0,78–0,94.
- Schwäche: Die zehn Coins laufen fast als ein Markt (mittlere Korrelation 0,68, seit 04/2025 0,79). Zehn Positionen
  sind praktisch eine.

## 3. Was getestet und verworfen wurde (127 Einzelhypothesen plus ein Massentest mit 602 Varianten)

- Dip-Käufe in Trendrichtung, Gegenbewegungs-Regeln, Rangfolge-Momentum zwischen Coins, Funding-Carry.
- Signale aus Positionierungsdaten (Open Interest, Long/Short-Verhältnisse, Orderfluss), neue Listings.
- Paar-Handel mit Z-Wert zwischen Coins und zwischen klassischen Märkten; Niedrig-Risiko-Baustein.
- Trend auf Gold, Öl, Indizes (14 Tage und 12 Monate), Übernacht-Effekt bei Aktien, Risiko-Filter über QQQ.
- Aktien-Momentum 12-1: im Prüfzeitraum stark (+33,5 %), in der Entwicklung schwach, Aktienliste rückblickend gewählt.
- „Short nach Pump“: Signale eines externen Dienstes (Plimaflow) zeigten 173 Trades mit +0,92 % je Trade über
  90 Tage, bestanden 3 von 4 Hürden; unklar, ob der Score nachträglich berechnet ist. Eigene Regeln auf 280 kleinen
  Coins: alle 15 Varianten negativ.
- 14 Abwandlungen des Trends (nur Long, Bänder, Filter) und 11 Varianten mit Gewinnziel/Stop: keine besteht.
  Gewinnziele halbieren den Ertrag und senken den Einbruch; besser nur in trendarmen Phasen.

## 4. Methode (wichtig für neue Vorschläge)

- Jede Runde wird vor dem ersten Ergebnis schriftlich festgelegt: Regel, Einstellungen, Hürden. Kein Nachjustieren.
- Entwicklung in zwei Hälften (bis 06/2023, bis 03/2025), Prüfzeitraum ab 04/2025 je Idee höchstens einmal.
- Bei mehreren Varianten gemeinsame Zufallsprüfung (White's Reality Check), danach Bestätigung auf frischen Coins.
- Befund: Mit dreieinhalb Jahren einer einzigen Zeitreihe lassen sich Verbesserungen von einigen Zehnteln Sharpe
  nicht von Zufall trennen. Weitere Varianten auf denselben Daten liefern vor allem Zufallstreffer.

## 5. Was gerade läuft

- **Test 1** (seit 15.11.2026, 13:21 UTC): 14-Tage-Trend, nur Umkehrsignal, Papier-Konto 5.000 $, Hebel 3.
- **Test 2** (seit 15.11.2026, 17:44 UTC): dieselbe Regel mit Stop 5 % und Gewinnziel 15 % je Position, eigenes Konto.
- Der Papier-Bot rechnet gegen das echte Yubit-Orderbuch, sichert den Stand im Repo und speist ein
  passwortgeschütztes Live-Board (GitHub Pages). Den Takt gibt derzeit eine Claude-Sitzung alle fünf Minuten.

## 6. Offene Fragen, zu denen Vorschläge gesucht sind

1. **Neue Informationsquellen**, die nicht aus Kursen, Funding und Positionierung bestehen (Orderbuch-Tiefe,
   Optionsdaten, On-Chain-Daten, Nachrichten). Welche sind realistisch beschaffbar und testbar?
2. **Unabhängige Märkte**: Yubit führt Kontrakte auf Metalle, Energie, Indizes und Aktien. Gibt es dort einen
   belegten Baustein, der mit dem Krypto-Trend nicht zusammenläuft und die Kosten trägt?
3. **Risikosteuerung bei Hebel 3**: Zehn gleichgerichtete Positionen ohne Tagesverlust-Limit. Welche Begrenzung
   senkt das Ruin-Risiko, ohne den Trend abzuschneiden?
4. **„Short nach Pump“ mit Score**: Wie lässt sich prüfen, ob der Score des Dienstes live vergeben wurde? Lohnt ein
   eigenes Modell auf mehreren Jahren kleiner Coins, sauber getrennt in Training und Prüfung?
5. **Betrieb ohne KI-Kosten**: Der Bot braucht nur Python und einen Zeitplan. Günstigster Weg: GitHub Actions,
   ein kleiner Server oder etwas anderes?
6. **Auswertung des Vorwärtstests**: Ab welcher Laufzeit und nach welchen Kennzahlen gilt er als bestanden oder
   gescheitert? Das sollte vorab festgelegt werden.

## 7. Wo alles liegt

- Repo (öffentlich): https://github.com/julienbaltrocco-bit/OdinGate-Botv134, Zweig `claude/intelligent-sagan-2cviug`.
- Vollständiges Protokoll aller Runden: `swing-hybrid/reports/suche_protokoll.md`.
- Zahlen je Runde: `swing-hybrid/reports/suche_runde*.json`. Code: `swing-hybrid/src/hybrid/`, `swing-hybrid/scripts/`.
- Papier-Bot und Stand: `swing-hybrid/vorwaertstest/` (`lauf/` für Test 1, `lauf_tpsl/` für Test 2). Board: `docs/index.html`.

Keine Anlageberatung.
