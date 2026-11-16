# Hybrid-Bericht: Swing-Bias + Intraday-Dip-Ausführung

Stand 14.11.2026. Historische Simulation, keine Anlageberatung. Vergangene Ergebnisse sagen nichts Sicheres über die Zukunft.

## Ergebnis

**Nicht weiterbauen. Die Hybrid-Variante fällt durch, bei beiden Swing-Strategien und deutlich.**

- Sie verdient im Prüfzeitraum nach Gebühren weniger als die reine Swing-Strategie:
  −11,8 % gegen +15,4 % bei trail_beide, +39,7 % gegen +101,4 % bei momentum_vol_ls.
- Das Dip-Kaufen selbst bringt vor Gebühren praktisch nichts und kostet nach Gebühren Geld.
- Das Mehr an Volumen ist real (Faktor 2,0 bzw. 4,3),
  bringt bei 1.000 $ Kapital aber nur etwa 0,05 $ bis 0,29 $ mehr Rebate pro Tag.
- Keine der 18 getesteten Einstellungen schlägt im Prüfzeitraum die reine Swing-Strategie, bei keiner der beiden Swing-Quellen. Nachjustieren würde also nichts retten.

Drei Nebenbefunde sind für dich wichtiger als das Hauptergebnis (Abschnitt „Was stattdessen auffällt“).

## Was in den Daten steckt

Deine ZIP ist das komplette Labor: 4.177 Einzel-Backtests, 23 Testreihen, 26 Strategien, Kerzen in 4H (ab 08/2021)
und 1D (ab 01/2022) für 10 Coins. Details in `datenbericht.md`. Als Swing-Bias dienen die zwei Strategien, die dein
Signalbot an Telegram meldet: **trail_beide (4H)** und **momentum_vol_ls (1D)**. Ihre Signale habe ich nachgerechnet;
im Prüfzeitraum deines Labors stimmen sie an jeder einzelnen Kerze mit den dort gespeicherten Werten überein.

Feine Kurse fehlten. Nachgeladen: 5-Minuten-Kerzen und Funding-Raten der Binance-Futures, 07/2021 bis 10/2026,
für alle 10 Coins. Bei SOL, XRP und LTC fehlen im Binance-Archiv 5 Tage (26.–28.02.2022 und 01.–02.04.2022);
an diesen Tagen wird für diese Coins kein Handel simuliert. Sie liegen im Lernzeitraum, nicht im Prüfzeitraum.

## Wie getestet wurde

- **Reine Swing (Baseline):** wie im Labor, Market-Order zum Open der nächsten Kerze. Yubit-Taker-Gebühr 0,08 %,
  dazu 0,05 % Slippage je Market-Order (wie im Labor).
- **Hybrid:** 50 % der Position folgt dem Swing-Signal (Einstieg per Limit). Die anderen 50 % in 3 Tranchen:
  jede volle Stunde ein Limit unter dem Kurs (bei Short darüber), nach Füllung ein Limit-Teilgewinn.
  Endet das Swing-Signal, wird alles per Market geschlossen.
- **Füllung streng:** Ein Limit zählt nur, wenn eine spätere 5-Minuten-Kerze den Preis um mehr als 0,01 % durchhandelt.
  Füllpreis ist der Limitpreis. Ungefüllte Orders werden nach 60 Minuten verworfen.
- **Deine Regeln sind eingebaut:** Hebel 3, nur Limits für Einstiege und Teilgewinne, Stops als Market, nie Orders
  gegeneinander, Obergrenze je Coin, Tagesverlust-Limit 3 % (schließt den Dip-Teil und sperrt ihn bis zum nächsten Tag).
- **Walk-Forward:** Einstellungen nur in den ersten 70 % der Zeit gewählt (aus 18 Kombinationen, stabilster Bereich
  statt Spitzenwert), die letzten 30 % unverändert gemessen. Dazu rollierende Fenster (12 Monate lernen, 3 Monate prüfen).
- **Immer drei Rechnungen:** vor Gebühren, ohne Rebate, mit 85 % Rebate. Die Trades sind in allen dreien dieselben.

Alle Prozentzahlen beziehen sich auf das Startkapital bei Hebel 3, ohne Zinseszins.

## Baseline gegen Hybrid

### trail_beide (4H)

Prüfzeitraum 19.04.2025 bis 23.10.2026. Gewählte Einstellung: Dip 1,0 × Stunden-ATR, Teilgewinn 0,5 × ATR, ohne Trailing.

| | Reine Swing | Swing, Einstieg per Limit | Hybrid |
|---|---|---|---|
| Ergebnis vor Gebühren | +30,6 % | +33,8 % | +6,5 % |
| **Netto ohne Rebate** | **+15,4 %** | **+23,0 %** | **−11,8 %** |
| Netto mit 85 % Rebate | +28,3 % | +32,2 % | +3,8 % |
| Größter Einbruch (ohne Rebate) | 55,1 % | 52,1 % | 48,8 % |
| Anzahl Trades | 316 | 316 | 3927 |
| Ø Haltedauer | 4,4 Tage | 4,4 Tage | 12 Std. |
| Gewinn-Trades | 46 % | 46 % | 77 % |
| Volumen pro Tag (× Kapital) | 0,34 | 0,34 | 0,70 |
| Anteil Maker-Volumen | 0 % | 57 % | 82 % |
| Orders pro Tag | 1 | 1 | 63 |
| Order-zu-Fill | 1,0:1 | 1,0:1 | 4,3:1 |

### momentum_vol_ls (1D)

Prüfzeitraum 14.07.2025 bis 23.10.2026. Gewählte Einstellung: Dip 1,0 × Stunden-ATR, Teilgewinn 2,0 × ATR, ohne Trailing.

| | Reine Swing | Swing, Einstieg per Limit | Hybrid |
|---|---|---|---|
| Ergebnis vor Gebühren | +111,3 % | +113,8 % | +65,6 % |
| **Netto ohne Rebate** | **+101,4 %** | **+106,9 %** | **+39,7 %** |
| Netto mit 85 % Rebate | +109,8 % | +112,7 % | +61,7 % |
| Größter Einbruch (ohne Rebate) | 26,5 % | 26,2 % | 21,3 % |
| Anzahl Trades | 237 | 237 | 8527 |
| Ø Haltedauer | 20,9 Tage | 20,9 Tage | 30 Std. |
| Gewinn-Trades | 39 % | 40 % | 62 % |
| Volumen pro Tag (× Kapital) | 0,26 | 0,26 | 1,13 |
| Anteil Maker-Volumen | 0 % | 60 % | 78 % |
| Orders pro Tag | 2 | 2 | 183 |
| Order-zu-Fill | 1,0:1 | 1,0:1 | 4,9:1 |

## Entscheidungsregeln

### trail_beide (4H)

| Regel | Bestanden | Messwert |
|---|---|---|
| Netto ohne Rebate ≥ reine Swing-Baseline | **NEIN** | −11,8 % gegen +15,4 % |
| Ergebnis vor Gebühren ≥ 0 | ja | +6,5 % |
| Max. Drawdown < 15 % | **NEIN** | 48,8 % |
| ≥ 300 Trades | ja | 3927 |
| Kein Paar > 50 % des Gewinns | **NEIN** | kein Gewinn |
| Kein Monat > 50 % des Gewinns | **NEIN** | kein Gewinn |
| Order-zu-Fill ≤ 5:1 | ja | 4,34:1 |
| Nie Orders, die gegeneinander laufen | ja | 0 Fälle (1 Order vorsorglich nicht eingestellt) |
| Mindest-Standzeit ≥ 5 Minuten | ja | 5 Minuten |

### momentum_vol_ls (1D)

| Regel | Bestanden | Messwert |
|---|---|---|
| Netto ohne Rebate ≥ reine Swing-Baseline | **NEIN** | +39,7 % gegen +101,4 % |
| Ergebnis vor Gebühren ≥ 0 | ja | +65,6 % |
| Max. Drawdown < 15 % | **NEIN** | 21,3 % |
| ≥ 300 Trades | ja | 8527 |
| Kein Paar > 50 % des Gewinns | ja | 29 % (ADA) |
| Kein Monat > 50 % des Gewinns | **NEIN** | 61 % (11/2025) |
| Order-zu-Fill ≤ 5:1 | ja | 4,92:1 |
| Nie Orders, die gegeneinander laufen | ja | 0 Fälle (0 Order vorsorglich nicht eingestellt) |
| Mindest-Standzeit ≥ 5 Minuten | ja | 5 Minuten |

Rollierende Fenster bestätigen das:
- trail_beide: 15 Fenster, Summe netto ohne Rebate: Hybrid +83,5 %, reine Swing +242,8 %. Hybrid war in 5 von 15 Fenstern mindestens so gut.
- momentum_vol_ls: 12 Fenster, Summe netto ohne Rebate: Hybrid +40,2 %, reine Swing +148,9 %. Hybrid war in 4 von 12 Fenstern mindestens so gut.

In den Fenstern, in denen Hybrid vorn liegt, verliert die Swing-Strategie. Hybrid verliert dann weniger, weil
weniger Kapital im Markt ist, nicht weil das Dip-Kaufen verdient.

## Volumen- und Rebate-Rechnung

Prüfzeitraum, Hebel 3. Alle Beträge skalieren genau mit dem Kapital.

### trail_beide (4H)

| Kapital | Variante | Volumen/Tag | Rebate/Tag | Netto/Tag ohne Rebate | Netto/Tag mit Rebate | Größter Einbruch (ohne / mit Rebate) |
|---|---|---|---|---|---|---|
| 500 $ | Reine Swing | 172 $ | 0,12 $ | 0,14 $ | 0,26 $ | 55 % / 50 % |
| 500 $ | Hybrid | 351 $ | 0,14 $ | −0,11 $ | 0,03 $ | 49 % / 41 % |
| 1.000 $ | Reine Swing | 343 $ | 0,23 $ | 0,28 $ | 0,51 $ | 55 % / 50 % |
| 1.000 $ | Hybrid | 701 $ | 0,28 $ | −0,21 $ | 0,07 $ | 49 % / 41 % |
| 5.000 $ | Reine Swing | 1.716 $ | 1,17 $ | 1,39 $ | 2,56 $ | 55 % / 50 % |
| 5.000 $ | Hybrid | 3.506 $ | 1,41 $ | −1,07 $ | 0,34 $ | 49 % / 41 % |

### momentum_vol_ls (1D)

| Kapital | Variante | Volumen/Tag | Rebate/Tag | Netto/Tag ohne Rebate | Netto/Tag mit Rebate | Größter Einbruch (ohne / mit Rebate) |
|---|---|---|---|---|---|---|
| 500 $ | Reine Swing | 132 $ | 0,09 $ | 1,09 $ | 1,18 $ | 26 % / 26 % |
| 500 $ | Hybrid | 566 $ | 0,24 $ | 0,42 $ | 0,66 $ | 21 % / 19 % |
| 1.000 $ | Reine Swing | 265 $ | 0,18 $ | 2,17 $ | 2,35 $ | 26 % / 26 % |
| 1.000 $ | Hybrid | 1.131 $ | 0,47 $ | 0,85 $ | 1,32 $ | 21 % / 19 % |
| 5.000 $ | Reine Swing | 1.323 $ | 0,90 $ | 10,86 $ | 11,76 $ | 26 % / 26 % |
| 5.000 $ | Hybrid | 5.657 $ | 2,35 $ | 4,25 $ | 6,60 $ | 21 % / 19 % |

Warum mehr Volumen wenig mehr Rebate bringt: Die reine Swing zahlt auf jedes Volumen die teure Taker-Gebühr (0,08 %),
Hybrid handelt zu rund 80 % als Maker (0,04 %). Mehr Volumen zum halben Satz ergibt nur wenig mehr Gebühr und
damit wenig mehr Rebate. Der Einbruch ist in Prozent für jedes Kapital gleich.

## Warum es nicht funktioniert

Zerlegung der Hybrid-Trades im Prüfzeitraum (ohne Funding):

| | Kern (Swing-Hälfte) | Dip-Teil vor Gebühren | Dip-Teil nach Gebühren |
|---|---|---|---|
| trail_beide | +13,9 % | −10,2 % | −23,1 % |
| momentum_vol_ls | +54,4 % | +8,2 % | −14,2 % |

1. **Der Dip-Teil hat keinen eigenen Vorteil.** 77 % bzw. 62 % der Trades gewinnen,
   aber die Gewinne sind klein (fester Teilgewinn) und die Verlierer groß: Sie laufen, bis das Swing-Signal endet.
2. **Er verdrängt die Hälfte der Swing-Position.** Hybrid hält nur den halben Swing-Anteil. Der Dip-Teil müsste
   also die andere Hälfte des Swing-Gewinns ersetzen. Das schafft er in keinem der beiden Fälle.
3. **Gebühren fressen den Rest.** 3927 bzw. 8527 Trades mit winzigem Ertrag pro Trade.

## Was stattdessen auffällt

**1. Derselbe Swing, aber Einstieg per Limit statt Market, war besser als die Baseline.**
Im Prüfzeitraum +23,0 % statt +15,4 % (trail_beide) und +106,9 % statt +101,4 %
(momentum_vol_ls), jeweils ohne Rebate. Der Grund ist schlicht: halbe Gebühr und keine Slippage beim Einstieg.
Mehr Volumen entsteht dadurch nicht. Der Vorteil hängt an der Füllannahme und ist klein gegenüber den Schwankungen.

**2. Hebel 3 ist für diese Swing-Strategien zu viel, auch ohne Hybrid.**
Die reine Swing hat im Prüfzeitraum einen Einbruch von 55 % (trail_beide) bzw. 26 % (momentum_vol_ls).
Über den ganzen Zeitraum (ab 07/2022) wäre das Konto mit momentum_vol_ls bei Hebel 3 zwischenzeitlich unter null
gefallen (Einbruch 126 % vom Höchststand), in der Praxis also vorher liquidiert worden.
Mit Hebel 1 liegen die Einbrüche im Prüfzeitraum bei 25 % bzw. 12 %.
Deine 15-%-Grenze hält bei Hebel 3 keine Variante. Bei Hebel 1 hält sie trail_beide auch nicht, und momentum_vol_ls
nur im Prüfzeitraum: über den ganzen Zeitraum sind es dort 45 %.

**3. trail_beide hat seit April 2025 kaum verdient.**
Ohne Hebel +5,1 % in 18 Monaten bei 25 % Einbruch.
Der gute Labor-Wert (+62 % im Labor-Prüfzeitraum ab 10/2024) stammt überwiegend aus November 2024 bis Januar 2025:
Allein diese drei Monate brachten ohne Hebel +54,9 %.

## Empfehlung

- **Hybrid mit Dip-Nachkauf: nein.** Nicht weiterbauen, nicht nachjustieren.
- **Wenn du etwas mitnehmen willst:** Swing-Einstiege per Limit statt Market (Befund 1) und Hebel deutlich unter 3
  (Befund 2). Beides ist keine neue Strategie, sondern sauberere Ausführung der bestehenden.
- **Rebate als Einnahme lohnt bei diesem Kapital nicht.** Selbst die volumenstärkste Hybrid-Rechnung bringt bei 5.000 $
  nur 2,35 $ Rebate pro Tag.

## Risiken und Annahmen

- **Yubit selbst ist nicht getestet.** Kurse und Funding stammen von Binance-Futures. Liquidität, Spreads, Funding und
  Mindestordergrößen bei Yubit können abweichen. Bei 500 $ ist eine Dip-Tranche nur 25 $ groß.
- **Füllmodell:** 5-Minuten-Kerzen zeigen nicht, wo man in der Warteschlange steht. Eine mildere Annahme (jedes
  Durchhandeln zählt) ändert das Urteil nicht: Hybrid −9,6 % bzw. +43,4 %.
- **Positionsgröße:** festes Kapital ohne Zinseszins, Hebel 3 gleichmäßig auf 10 Coins. Das Labor rechnet je Coin
  mit Zinseszins; im selben Fenster ohne Hebel weichen beide Rechnungen wenig ab
  (trail_beide: Labor +7,6 %, hier +8,7 %; momentum_vol_ls: Labor +48,3 %, hier +41,9 %).
- **Tagesverlust-Limit:** Den Wert 3 % habe ich gesetzt, bevor Ergebnisse vorlagen. Er wirkt nur auf den Dip-Teil.
  Der Kern folgt weiter dem Swing-Signal.
- **Die Swing-Strategien selbst sind nicht gesichert profitabel.** Im Labor erreichte keine Futures-Strategie GRÜN,
  und sie wurden aus 17 Versuchen ausgewählt. Die 10 Coins wurden im Rückblick festgelegt.
- **Rebate:** gerechnet als sofortige Gutschrift von 85 % der gezahlten Gebühr. Auszahlungstermine und Bedingungen
  des Partners sind nicht berücksichtigt.
- **Ein Datenstand:** Die Auswertung endet am 23.10.2026. Der Prüfzeitraum umfasst nur 15 bis 18 Monate.

## Nachrechnen

```bash
cd swing-hybrid
.venv/bin/python -m pytest -q                 # 10 Tests, u. a. Füllregel und „kein Blick in die Zukunft“
.venv/bin/python -I scripts/raster.py         # alle Varianten rechnen
.venv/bin/python -I scripts/walkforward.py    # Auswahl, Urteil, rollierende Fenster
.venv/bin/python -I scripts/gegenpruefung.py  # Gegenprüfungen
.venv/bin/python -I scripts/bericht.py        # diesen Bericht erzeugen
```
