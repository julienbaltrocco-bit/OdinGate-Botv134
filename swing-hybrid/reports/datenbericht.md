# Datenbericht: Was in deiner ZIP steckt

Stand 14.11.2026. Historische Simulation, keine Anlageberatung.

## Kurz gesagt

Die ZIP ist dein komplettes „trading-labor“ samt aller Rechenergebnisse. Sie enthält genug, um die Swing-Strategien
exakt nachzurechnen. Es fehlen aber feine Intraday-Kurse; die habe ich von Binance nachgeladen.

## Inhalt

| Teil | Umfang | Was es ist |
|---|---|---|
| `runs/` | 3,3 GB, 4.177 Einzelläufe | Jeder Backtest einzeln: Einstellungen, Strategie-Code, Kerzen, Kontoverlauf, jede Ausführung |
| `cache/` | 47 MB, 254 Dateien | Die geladenen Kurse (siehe unten) |
| `berichte/` | 23 Testreihen | Ergebnis je Reihe mit Ampel |
| `strategien/` | 26 Strategien | Der Code jeder Strategie |
| `logs/` | | Versuchsprotokoll, Signalbot-Meldungen seit 18.10.2026 |
| `.venv`, `vendor`, `.python` | 0,9 GB | Programme, keine Daten. Nicht entpackt. |
| `.env` | | Zugangsdaten (Telegram). Bewusst nicht entpackt und nicht gelesen. |

## Kurse in der ZIP

| Quelle | Kerzen | Zeitraum | Märkte |
|---|---|---|---|
| OKX (Spot-Kurse) | 4H | 08/2021 – 24.10.2026 | 10 Coins |
| OKX (Spot-Kurse) | 1D | 01/2022 – 24.10.2026 | 10 Coins |
| OKX (Spot-Kurse) | 1H | 07/2025 – 10/2026 | nur BTC, ETH, SOL |
| Binance-Perpetuals | 1D, mit echtem Funding | 01/2022 – 24.10.2026 | 20 Coins |
| yfinance | 1D | 2016 – 10/2026 | 10 US-ETFs |

Die 10 Coins: BTC, ETH, SOL, XRP, DOT, DOGE, ADA, LINK, AVAX, LTC.

**Keine 5m- oder 15m-Kerzen.** Nachgeladen: Binance-USD-M-Futures, 5-Minuten-Kerzen und Funding-Raten,
07/2021 – 10/2026, dieselben 10 Coins.

## Die Strategien und wie sie abgeschnitten haben

Alle Zahlen: Prüfzeitraum (den die Parameterwahl nie gesehen hat), Durchschnitt über die Coins, ohne Hebel,
mit den Labor-Kosten (0,05 % Gebühr + 0,05 % Slippage je Seite).

| Strategie | Kerzen | Richtung | Rendite | Größter Einbruch | Trades | Ampel |
|---|---|---|---|---|---|---|
| **trail_beide** | 4H | Long + Short | +62 % | −39 % | 414 | GELB |
| breakout_trail | 4H | Long | +43 % | −37 % | 318 | GELB |
| momentum_breakout | 4H | Long | +48 % | −42 % | 326 | GELB |
| **momentum_vol_ls** | 1D | Long + Short | +41 % | −34 % | 349 | GELB |
| momentum_vol_ls (echte Binance-Perps) | 1D | Long + Short | +31 % | −38 % | 329 | GELB |
| momentum_dual_ls / regime_ls / ensemble_ls | 1D | Long + Short | +19 bis +25 % | −20 bis −24 % | ~350–390 | GELB |
| rsi2_reversion | 1D | Long | +3 % | −10 % | 42 | GELB |

Prüfzeitraum 4H: 01.10.2024 – 01.10.2026. Prüfzeitraum 1D: 01.01.2025 – 01.10.2026.
Der Markt (Kaufen und Halten) lag im selben Zeitraum bei etwa 0 % (4H-Reihen) bzw. −45 % (1D-Reihen).

Durchgefallen (ROT): Short-Ausbrüche, RSI(2) Long+Short, Funding-Kontra, Coin-Rangfolge, Supertrend,
alle 1H-Rücksetzer-Strategien.

## Was ich als „Swing-Bias“ nehme

Die zwei Strategien, die dein Signalbot aktuell an Telegram meldet und die genug Trades haben:

1. **trail_beide (4H)** – Long per Ausbruch, Short per Erschöpfung, 1/3 Gewinnmitnahme, dann Trailing-Stop.
2. **momentum_vol_ls (1D)** – Trendrichtung der letzten 60 Tage, Positionsgröße nach Schwankung.

## Drei Dinge, die du vor dem Ergebnis wissen solltest

1. **„Profitabel“ stimmt, aber mit Vorbehalt.** Keine Futures-Strategie hat GRÜN erreicht. Alle scheitern am
   Zufallstest (73–83 statt 90). Dein eigenes Versuchsprotokoll zählt 17 Varianten; je mehr man probiert, desto eher
   sieht eine zufällig gut aus.
2. **Die Einbrüche der Swing-Strategien sind groß:** −34 % bis −39 % je Coin ohne Hebel. Deine Regel für die
   Hybrid-Variante lautet „Einbruch unter 15 %“, mit Hebel 3. Das ist eine hohe Hürde. Über alle 10 Coins als ein
   Konto gerechnet ist der Einbruch kleiner als je Coin; das rechne ich in der Baseline aus.
3. **Die trail_beide-Short-Seite war im Lernzeitraum negativ** und hat erst im Prüfzeitraum Gewinn gebracht
   (steht so in deinem Protokoll). Der Vorteil könnte an der Abwärtsphase 2025/26 liegen.

## Unterschiede zwischen Labor und Yubit

| | Labor | Yubit (für diesen Test) |
|---|---|---|
| Kurse | OKX Spot | Binance-Futures als Stellvertreter (Yubit-Historie nicht verfügbar) |
| Gebühr je Seite | 0,05 % | 0,04 % Maker / 0,08 % Taker, mit und ohne 85 % Rebate |
| Slippage | 0,05 % | nur bei Market-Orders (Stops) |
| Funding | fest 0,01 % je 8 h | echte Binance-Raten |
| Ausführung | zum Open der nächsten Kerze | Limit-Orders auf 5-Minuten-Kerzen |
