# Stat-Arb mit Z-Score, fusioniert mit dem Swing

Stand 14.11.2026. Historische Simulation auf Binance-Futures, keine Anlageberatung. Yubit spielt hier keine Rolle;
gerechnet wird mit den Kosten deines Labors (0,05 % Gebühr + 0,05 % Slippage je Order).

## Ergebnis

**Das Stat-Arb-System ist gebaut und funktioniert technisch. Es verdient vor Kosten, nach Kosten aber nicht.
Die Fusion mit dem Swing senkt den Einbruch deutlich, ist aber im Prüfzeitraum nicht besser als der Swing allein.**

- Stat-Arb allein, Gruppe A: vor Kosten +28,3 % in der Entwicklung, netto −2,8 %; im Prüfzeitraum netto −11,5 %.
- Keine der 9 Einstellungen ist in beiden Entwicklungshälften netto positiv.
- Ein Paar-Trade verdient im Mittel 0,13 % seines Einsatzes und kostet 0,20 % (vier Orders).

## Was gebaut wurde

- **Paare finden:** Für jedes Coin-Paar wird laufend über ein Fenster gemessen, wie stark die Kurse zusammenlaufen
  (Korrelation mindestens 0,7) und in welchem Verhältnis (Hedge-Verhältnis aus einer Regression).
- **Z-Score:** Der Abstand der beiden Kurse voneinander wird mit seinem eigenen Mittel und seiner Schwankung
  verglichen. Z = 2 heißt: zwei Standardabweichungen auseinander.
- **Handeln:** Ab der Z-Schwelle den teuren Coin short, den billigen long. Raus, wenn der Abstand zurück am Mittel
  ist, bei Z = 4 (Stop) oder nach der halben Fensterlänge.
- **Grenzen:** höchstens 10 Paare gleichzeitig, jeder Coin in höchstens 3 Paaren, Long und Short zusammen höchstens
  100 % des Topfes. Signale am Kerzenschluss, Ausführung zum Open der nächsten Stundenkerze, echtes Funding.

Getestet sind: verdient an künstlichen Paaren, die zum Mittel zurückkehren; ignoriert unkorrelierte Coins; hält die
Obergrenzen ein; kein Blick in die Zukunft.

## Stat-Arb allein

Alle 9 Einstellungen, Gruppe A (10 Coins), Entwicklungszeitraum:

| Fenster | Z-Schwelle | Vor Kosten | Netto | Trades |
|---|---|---|---|---|
| 7 Tage | 1,5 | −2,2 % | −141,7 % | 6980 |
| 7 Tage | 2,0 | +0,9 % | −111,5 % | 5621 |
| 7 Tage | 2,5 | −1,4 % | −87,8 % | 4323 |
| 14 Tage | 1,5 | +12,8 % | −62,8 % | 3782 |
| 14 Tage | 2,0 | +29,6 % | −30,6 % | 3013 |
| 14 Tage | 2,5 | +30,5 % | −17,3 % | 2391 |
| 30 Tage | 1,5 | +30,7 % | −8,4 % | 1956 |
| 30 Tage | 2,0 | +28,3 % | −2,8 % | 1552 |
| 30 Tage | 2,5 | +21,7 % | −2,2 % | 1193 |

Je kürzer das Fenster, desto mehr Trades und desto mehr fressen die Kosten. Weitergerechnet wurde mit der
Einstellung, die dem Bestehen am nächsten kam (30 Tage, Z-Schwelle 2,0):

| Gruppe | Zeitraum | Vor Kosten | Kosten | Netto | Größter Einbruch |
|---|---|---|---|---|---|
| A | Entwicklung | +28,3 % | −31,1 % | **−2,8 %** | 17 % |
| A | Prüfzeitraum | +4,8 % | −16,3 % | **−11,5 %** | 19 % |
| B | Entwicklung | −0,3 % | −22,6 % | **−23,0 %** | 37 % |
| B | Prüfzeitraum | −19,7 % | −7,8 % | **−27,5 %** | 29 % |
| C | Entwicklung | +64,3 % | −55,3 % | **+9,0 %** | 22 % |
| C | Prüfzeitraum | +11,8 % | −19,5 % | **−7,7 %** | 12 % |

- **Trefferquote vor Kosten:** 61 %, mittlere Haltedauer 5,0 Tage, 2366 Trades über den ganzen Zeitraum.
- **Woran es hängt:** 1495 Trades enden am Ziel und bringen zusammen +329 % des Topfes. 589 enden im Stop
  (−177 %) und 282 im Zeitlimit (−122 %). Paare, die auseinanderlaufen und nicht
  zurückkommen, nehmen fast alles wieder weg.
- **Mit sehr niedrigen Kosten** (Yubit nach Rebate): Entwicklung +14,0 %, Prüfzeitraum −1,8 %.
  Selbst ganz ohne Kosten bleiben im Prüfzeitraum nur +4,8 %.

## Fusion mit dem Swing

Zwei Arten, jeweils mit beiden Swing-Strategien aus deinem Labor (Hebel 1, gleiche Kosten):

- **Fusion 1, zwei Töpfe:** die Hälfte des Kapitals im Swing, die Hälfte im Stat-Arb.
- **Fusion 2, Swing als Filter:** Das Stat-Arb nimmt ein Paar nur, wenn keine Seite gegen die Swing-Richtung des
  jeweiligen Coins läuft. Dazu wieder die Hälfte im Swing.

### trail_beide (4H)

| | Netto pro Jahr, Entwicklung | Einbruch | Sharpe | Netto pro Jahr, Prüfzeitraum | Einbruch | Sharpe |
|---|---|---|---|---|---|---|
| Swing allein | +26,6 % | 17 % | 1,03 | +5,8 % | 22 % | 0,30 |
| Stat-Arb allein | −0,7 % | 17 % | −0,06 | −7,4 % | 19 % | −0,79 |
| Fusion 1: zwei Töpfe | +13,0 % | 12 % | 0,97 | −0,8 % | 17 % | −0,08 |
| Fusion 2: Swing als Filter | +14,4 % | 11 % | 1,04 | +1,4 % | 17 % | 0,13 |

### momentum_vol_ls (1D)

| | Netto pro Jahr, Entwicklung | Einbruch | Sharpe | Netto pro Jahr, Prüfzeitraum | Einbruch | Sharpe |
|---|---|---|---|---|---|---|
| Swing allein | +7,3 % | 43 % | 0,29 | +11,9 % | 24 % | 0,45 |
| Stat-Arb allein | +2,1 % | 16 % | 0,19 | −7,4 % | 19 % | −0,79 |
| Fusion 1: zwei Töpfe | +4,7 % | 20 % | 0,36 | +2,3 % | 15 % | 0,17 |
| Fusion 2: Swing als Filter | +3,9 % | 22 % | 0,31 | +5,3 % | 13 % | 0,40 |

- **Der Einbruch sinkt deutlich.** Das liegt vor allem daran, dass nur noch die Hälfte im Swing steckt.
- **Swing und Stat-Arb laufen leicht gegeneinander** (Korrelation der Tagesgewinne −0,14). Das ist echte
  Streuung und der Grund, warum die Fusion in der Entwicklung in drei von vier Fällen einen besseren Sharpe hat.
- **Im Prüfzeitraum ist der Sharpe in allen vier Fällen niedriger als beim Swing allein.** Der Stat-Arb-Topf
  verdient netto nichts und verdünnt den Swing nur.
- **Der Filter hilft dem Stat-Arb** (bei trail_beide im Prüfzeitraum −4,9 % statt −11,5 %), macht es aber nicht profitabel.

Vorab festgelegt war: Die Fusion gilt als besser, wenn sie in Entwicklung **und** Prüfzeitraum einen höheren Sharpe
und einen kleineren Einbruch hat. Das erfüllt keine der vier Kombinationen.

## Einordnung

- Der Effekt ist da, aber klein: Paare kehren vor Kosten tatsächlich öfter zurück als nicht. Er reicht nicht für
  vier Orders je Trade.
- Er ist nicht stabil über Coin-Gruppen: Gruppe B ist schon vor Kosten negativ (−0,3 % / −19,7 %),
  Gruppe C vor Kosten klar positiv (+64,3 % / +11,8 %).
- Das passt zu den früheren Runden: Gegenbewegungs-Regeln und die marktneutrale Rangfolge sind ebenfalls an Kosten
  und fehlender Stabilität gescheitert.

## Dateien

- `src/hybrid/statarb.py`: das Stat-Arb-System
- `scripts/suche_runde12.py`: Raster, Gegenproben und Fusion; `tests/test_statarb.py`: Tests
- `reports/suche_runde12.json`, `reports/suche_runde12_stufe1.csv`: alle Zahlen
- `reports/suche_protokoll.md`: die vorab festgelegten Regeln (Runde 12)
