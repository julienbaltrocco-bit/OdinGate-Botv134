# Suchbericht: Strategie mit Rebate als größerem Gewinnanteil

Stand 14.11.2026. Historische Simulation, keine Anlageberatung. Vergangene Ergebnisse sagen nichts Sicheres über die Zukunft.

## Ergebnis

**Der Kandidat (14-Tage-Trend) bleibt das Beste, was die Daten hergeben. Fünf weitere Runden mit 13 neuen
Versuchen haben keinen stärkeren Edge gefunden. Deutlich besser geworden ist aber die Kostenrechnung: An Yubit
gemessen ist die Slippage viel niedriger als bisher angenommen.**

Mit echten Yubit-Kosten (10 Coins, Hebel 0,2): Entwicklung +41,3 %, Prüfzeitraum +5,2 % netto mit Rebate
in 19 Monaten, davon +9,1 % Rebate. Bei doppelten Kosten bleiben im Prüfzeitraum +1,2 %.
Der Vorteil ist weiterhin klein und im Prüfzeitraum statistisch nicht gesichert.

Die folgenden Punkte und die Abschnitte bis Runde 5 rechnen noch mit der alten, vorsichtigen Annahme von 0,05 %
Slippage. Über alle 60 getesteten Coins waren es damit +2,7 % im Prüfzeitraum (Hebel 0,15).

- **Vor Gebühren profitabel:** ja, in jedem Kalenderjahr seit 2021.
- **Netto mit Rebate profitabel:** ja, in jedem Kalenderjahr. Im Prüfzeitraum aber nur +2,4 % in 19 Monaten.
- **Rebate ist der größere Anteil:** ja. Im Prüfzeitraum +9,1 % Rebate gegen +2,4 % Nettogewinn.
  Ohne Rebate hätte der Handel dort −6,6 % gebracht, also verloren.
- **Größter Einbruch:** 11 % im Prüfzeitraum, 10 % in der Entwicklung (Grenze 15 %).
- **Der Haken:** Das hält nur bei Hebel 0,2, also wenn nur ein Fünftel des Kontos im Markt ist. Bei 5.000 $ sind
  das etwa 0,80 $ Rebate und 0,21 $ Nettogewinn pro Tag.
- **Breiter gestreut wird es etwas besser:** Über 40 Coins bringt derselbe Kandidat im Prüfzeitraum +5,5 % statt +2,4 %,
  bei 9 % Einbruch. Mehr Hebel erlaubt die Streuung aber nicht.

Meine Empfehlung: den gebauten Vorwärtstest (`../vorwaertstest/`) laufen lassen, zuerst auf Papier gegen das echte
Yubit-Orderbuch. Die Kostenmessung beruht bisher auf einer Stunde eines einzigen Tages. Nicht hochfahren, bevor
der Dauerwert vorliegt.

## Der Kandidat in einfachen Worten

- **Markt:** dieselben 10 Coins wie in deinem Labor, als Futures.
- **Signal, jede volle Stunde:** Steht der Kurs höher als vor 14 Tagen, dann Long. Steht er tiefer, dann Short.
  Das ist dein Tagestrend (momentum_vol_ls), nur stündlich nachgeführt und mit kürzerer Länge.
- **Größe:** jeder Coin gleich groß, zusammen höchstens 20 % des Kontos (Hebel 0,2).
- **Order:** Limit mit Preisgrenze knapp durch den Markt. Sie wird sofort gefüllt und zählt als Taker.
- **Schutz:** Tagesverlust-Limit 3 % (in 1896 Tagen 3-mal ausgelöst), Obergrenze je Coin.
- **Aktivität:** rund 6 Orders pro Tag über alle Coins, Ø Haltedauer 42 Stunden,
  Order-zu-Fill 1:1, keine Stornos, nie zwei Orders gleichzeitig je Coin.

## Zahlen

Gruppe A (10 Labor-Coins), Hebel 0,2, 0,05 % Slippage je Order. Prozent vom Startkapital, ohne Zinseszins.

| | Entwicklung (08/2021–03/2025) | Prüfzeitraum (04/2025–10/2026) | Gesamt |
|---|---|---|---|
| Handel vor Gebühren | +38,5 % | +4,0 % | +42,5 % |
| Gezahlte Gebühr | 24,0 % | 10,7 % | 34,7 % |
| Rebate (85 %) | +20,4 % | +9,1 % | +29,5 % |
| Handel nach voller Gebühr (ohne Rebate) | +14,4 % | −6,6 % | +7,8 % |
| **Netto mit Rebate** | +34,9 % | +2,4 % | +37,3 % |
| Größter Einbruch | 10 % | 11 % | 10 % |
| Volumen pro Tag (× Kapital) | 0,23 | 0,23 | 0,23 |

### Jahr für Jahr

| Jahr | Handel vor Gebühren | Rebate | Handel nach voller Gebühr | Netto mit Rebate |
|---|---|---|---|---|
| 2021 (ab 15.08.) | +7,8 % | +1,8 % | +5,6 % | +7,5 % |
| 2022 | +5,8 % | +5,5 % | −0,7 % | +4,8 % |
| 2023 | +10,6 % | +5,8 % | +3,8 % | +9,5 % |
| 2024 | +13,8 % | +5,8 % | +6,9 % | +12,8 % |
| 2025 | +3,0 % | +5,5 % | −3,4 % | +2,0 % |
| 2026 (bis 23.10.) | +1,6 % | +5,1 % | −4,4 % | +0,7 % |

Das Rebate ist jedes Jahr fast gleich groß (rund 5,8 % des Kapitals), weil der Umsatz gleich bleibt.
Der Handel selbst schwankt stark und ist 2025 und 2026 deutlich schwächer als davor.
56 % der 63 Monate schließen im Plus, 28 % der Trades gewinnen (typisch für Trendfolge:
viele kleine Verluste, wenige große Gewinne).

## Kapital-Szenarien

| Kapital | Position je Coin | Volumen/Tag | Rebate/Tag | Netto/Tag (Prüfzeitraum) | Netto/Tag (gesamter Zeitraum) | Größter Einbruch |
|---|---|---|---|---|---|---|
| 500 $ | 10 $ | 117 $ | 0,08 $ | 0,02 $ | 0,10 $ | 11 % (≈ 56 $) |
| 1.000 $ | 20 $ | 234 $ | 0,16 $ | 0,04 $ | 0,20 $ | 11 % (≈ 111 $) |
| 5.000 $ | 100 $ | 1.170 $ | 0,80 $ | 0,21 $ | 0,98 $ | 11 % (≈ 556 $) |

Bei 500 $ ist eine Position nur 10 $ groß. Ob Yubit so kleine Orders annimmt, weiß ich nicht.

## Wie belastbar ist das?

**Slippage entscheidet.** Der Kandidat verträgt im Prüfzeitraum bis knapp 0,07 % je Order, darüber verliert er:

| Slippage je Order | Netto mit Rebate, Entwicklung | Netto mit Rebate, Prüfzeitraum |
|---|---|---|
| 0,000 % | +49,9 % | +9,1 % |
| 0,025 % | +42,4 % | +5,8 % |
| 0,050 % | +34,9 % | +2,4 % |
| 0,075 % | +27,4 % | −0,9 % |
| 0,100 % | +19,9 % | −4,2 % |

**Zweite Coin-Gruppe (nie zur Auswahl benutzt):** BNB, TRX, ATOM, BCH, ETC, FIL, UNI, NEAR, XLM, AAVE.
Entwicklung +18,3 %, Prüfzeitraum +0,5 %. Positiv, im Prüfzeitraum aber praktisch null.

**Zufallstest:** Über den ganzen Zeitraum schlägt der Kandidat alle 200 Zufallsvarianten (dasselbe Signal, zeitlich
verschoben). Nur im Prüfzeitraum betrachtet ist er besser als 80 % davon. Das liegt unter der 90-%-Marke
deines Labors: In den letzten 19 Monaten ist der Vorteil statistisch nicht gesichert.

**Passive Ausführung statt sofortiger:** Mit Limit zum letzten Kurs (Maker) rechnet das Modell im Prüfzeitraum
+5,7 % netto, und der Handel wäre dort sogar nach voller Gebühr im Plus (+1,1 %).
Dieser Wert hängt an der Füllannahme, die sich mit Kerzen nicht absichern lässt. Die sofortige Ausführung ist die
vorsichtige Untergrenze.

## Bestätigung auf frischen Daten (Runde 4)

Der Kandidat wurde unverändert auf Daten getestet, die in der Suche nie vorkamen. Vorab festgelegt war: bestätigt
nur, wenn Gruppe C in Entwicklung und Prüfzeitraum und die Vorperiode netto positiv sind. **Ergebnis: bestätigt.**
Runde 5 relativiert das: Eine weitere frische Gruppe (D) liegt im Prüfzeitraum bei null.
Alle Werte auf Hebel 0,2 umgerechnet, ohne Tageslimit.

| Gruppe C (20 neue Coins) | Entwicklung | Prüfzeitraum |
|---|---|---|
| Handel vor Gebühren | +39,7 % | +11,1 % |
| Handel nach voller Gebühr (ohne Rebate) | +16,0 % | +0,5 % |
| **Netto mit Rebate** | +36,1 % | +9,5 % |

| Vorperiode 02/2020–08/2021 | Coins | Handel vor Gebühren | Netto mit Rebate |
|---|---|---|---|
| Gruppe A | 10 | +40,9 % | +39,6 % |
| Gruppe B | 10 | +16,8 % | +15,5 % |
| Gruppe C | 20 | +46,3 % | +45,2 % |
| alle zusammen | 40 | +37,6 % | +36,4 % |

Gruppe C: XMR, ZEC, DASH, ALGO, VET, THETA, EGLD, SUSHI, COMP, SNX, CRV, 1INCH, GRT, SAND, MANA, AXS, CHZ, ENJ, KSM, ZIL. Die Vorperiode war ein starker Aufwärtsmarkt, in dem Trendfolge leichtes
Spiel hatte; sie zählt deshalb weniger als Gruppe C. Nur Coins mit vollständiger Historie bis 2026 sind dabei, das
schönt etwas.

### Breites Portfolio: alle 40 Coins zusammen

| Breites Portfolio (40 Coins), Hebel 0,2 | Entwicklung | Prüfzeitraum | Gesamt |
|---|---|---|---|
| Handel vor Gebühren | +37,8 % | +7,0 % | +44,8 % |
| Rebate (85 %) | +20,2 % | +8,8 % | +29,0 % |
| Handel nach voller Gebühr (ohne Rebate) | +14,0 % | −3,4 % | +10,7 % |
| **Netto mit Rebate** | +34,2 % | +5,5 % | +39,7 % |
| Größter Einbruch | 10 % | 9 % | 10 % |

| Jahr | Handel vor Gebühren | Rebate | Netto mit Rebate |
|---|---|---|---|
| 2021 (ab 15.08.) | −0,1 % | +2,2 % | −0,5 % |
| 2022 | +11,4 % | +5,0 % | +10,6 % |
| 2023 | +4,9 % | +6,1 % | +3,8 % |
| 2024 | +20,1 % | +5,3 % | +19,2 % |
| 2025 | +4,5 % | +5,6 % | +3,5 % |
| 2026 (bis 23.10.) | +4,1 % | +4,8 % | +3,2 % |

- **Streuung senkt den Einbruch nicht genug für mehr Hebel.** Die Coins fallen und steigen zu sehr gemeinsam.
  Der zulässige Hebel bleibt 0,2, das Rebate damit bei rund 5,6 % des Kapitals pro Jahr.
- **Slippage im Prüfzeitraum** (netto mit Rebate): 0,000 % → +12,0 %, 0,025 % → +8,7 %, 0,050 % → +5,5 %, 0,075 % → +2,2 %, 0,100 % → −1,0 %. Die Schmerzgrenze liegt hier bei knapp 0,09 %.
- **Zufallstest nur im Prüfzeitraum:** besser als 86 % der Zufallsvarianten, weiter unter der 90-%-Marke.

| Kapital | Position je Coin | Volumen/Tag | Rebate/Tag | Netto/Tag (Prüfzeitraum) | Netto/Tag (gesamter Zeitraum) |
|---|---|---|---|---|---|
| 500 $ | 2,50 $ | 114 $ | 0,08 $ | 0,05 $ | 0,10 $ |
| 1.000 $ | 5,00 $ | 228 $ | 0,15 $ | 0,10 $ | 0,21 $ |
| 5.000 $ | 25,00 $ | 1.138 $ | 0,77 $ | 0,48 $ | 1,05 $ |

Bei 40 Coins werden die Einzelpositionen sehr klein. Unter etwa 5.000 $ Kapital ist das breite Portfolio kaum
handelbar, und ob Yubit alle diese Coins führt, weiß ich nicht.

## Tiefer gegraben (Runde 5)

Frage: Lässt sich aus dem Trend mehr holen, ohne den Einbruch zu erhöhen? Getestet wurden drei Arten der
Risikosteuerung, eine Mischung aus vier Trendlängen und eine neue Ertragsquelle (Funding-Carry), auf 40 Coins.

| Variante | Besteht beide Hälften | Schlechtere Hälfte (Sharpe) | Netto, Entwicklung (Hebel 1) | Einbruch (Hebel 1) |
|---|---|---|---|---|
| Basis (der Kandidat) | ja | 0,44 | +162,4 % | 35 % |
| Ruhige Coins größer | ja | 0,45 | +141,6 % | 35 % |
| In wilden Phasen kleiner | ja | 0,73 | +199,4 % | 41 % |
| Beides zusammen | ja | 0,74 | +176,8 % | 41 % |
| Mischung aus 4 Trendlängen | nein | −0,01 | +76,6 % | 42 % |
| Funding-Carry | nein | −0,13 | +16,6 % | 10 % |

- **Risikosteuerung sieht in der Entwicklung besser aus, hilft aber nicht.** Sie macht die beiden Hälften
  gleichmäßiger, erhöht aber den Einbruch. Beim zulässigen Hebel (0,15 statt 0,20) bringt sie im Prüfzeitraum
  +3,9 % statt +5,5 %. Auf der frischen Gruppe D ist sie nicht bestätigt.
- **Funding-Carry fällt durch:** in der ersten Hälfte positiv, in der zweiten nicht mehr.
- **Die Mischung aus Trendlängen fällt durch:** in der ersten Hälfte netto negativ.

### Gegenprobe über alle vier Coin-Gruppen

Der unveränderte Kandidat, auf Hebel 0,2 umgerechnet:

| Gruppe | Coins | Handel vor Gebühren, Prüfzeitraum | Netto mit Rebate, Prüfzeitraum | Netto mit Rebate, Entwicklung |
|---|---|---|---|---|
| A | 10 | +4,0 % | +2,4 % | +36,7 % |
| B | 10 | +2,0 % | +0,5 % | +21,0 % |
| C (frisch in Runde 4) | 20 | +11,1 % | +9,5 % | +36,1 % |
| D (frisch in Runde 5) | 20 | +1,6 % | −0,0 % | +21,9 % |

Vor Gebühren ist der Handel in allen vier Gruppen und beiden Zeiträumen positiv. Netto mit Rebate bleibt im
Prüfzeitraum aber nur in einer Gruppe (C) deutlich etwas übrig. Gruppe D: IOTA, NEO, ONT, QTUM, XTZ, RUNE, KAVA, BAT, ZRX, YFI, HBAR, ONE, ANKR, RLC, BAND, KNC, ZEN, CELR, COTI, SKL.

| Alle 60 Coins, Hebel 0,15 | Entwicklung | Prüfzeitraum | Gesamt |
|---|---|---|---|
| Handel vor Gebühren | +27,5 % | +3,9 % | +31,4 % |
| Rebate (85 %) | +15,1 % | +6,8 % | +21,9 % |
| Handel nach voller Gebühr (ohne Rebate) | +9,7 % | −4,0 % | +5,7 % |
| **Netto mit Rebate** | +24,8 % | +2,7 % | +27,6 % |
| Größter Einbruch | 9 % | 8 % | 9 % |

- **Jahr für Jahr netto:** 2021: −2,8 %, 2022: +7,8 %, 2023: +2,6 %, 2024: +15,8 %, 2025: +1,1 %, 2026: +3,1 %.
- **Slippage im Prüfzeitraum:** 0,000 % → +7,7 %, 0,025 % → +5,2 %, 0,050 % → +2,7 %, 0,075 % → +0,3 %, 0,100 % → −2,2 %.
- **Zufallstest nur im Prüfzeitraum:** besser als 86 % der Zufallsvarianten.
- **In Dollar bei 5.000 $:** etwa 0,59 $ Rebate und 0,24 $ netto pro Tag im Prüfzeitraum,
  0,73 $ netto pro Tag über den ganzen Zeitraum.

Über 60 Coins sinkt der zulässige Hebel auf 0,15.

## Runden 6 bis 10: echte Yubit-Kosten und die Suche nach mehr

### Was eine Order bei Yubit wirklich kostet

Gemessen an Yubits öffentlichem Orderbuch, 30 Messungen über eine Stunde am 14.11.2026
(Details in `yubit_erstmessung.md`). Angesetzt wird je Coin das Doppelte der gemessenen halben Spanne:
Gruppe A im Mittel 0,030 %, Gruppe B 0,033 %, Gruppe C 0,053 %, Gruppe D 0,078 %.
Bisher hatte ich pauschal 0,050 % gerechnet. Das Orderbuch ist tief genug, dass auch Orders über 10.000 $
bei den großen Coins kaum mehr kosten.

### Der Kandidat mit echten Kosten

Unverändert: 14-Tage-Trend, Gruppe A, Hebel 0,2, Tageslimit 3 %.

| Slippage-Annahme | Entwicklung, netto mit Rebate | Prüfzeitraum, netto mit Rebate |
|---|---|---|
| alt: 0,05 % pauschal | +34,9 % | +2,4 % |
| **gemessen: 2 × halbe Yubit-Spanne je Coin** | **+41,3 %** | **+5,2 %** |
| Stress: das Doppelte davon | +32,8 % | +1,2 % |

- **Im Prüfzeitraum:** Handel vor Gebühren +6,8 %, Rebate +9,1 %, nach voller Gebühr ohne Rebate −3,9 %,
  größter Einbruch 10 %.
- **Jahr für Jahr netto mit Rebate:** 2021: +8,1 %, 2022: +6,5 %, 2023: +11,5 %, 2024: +14,6 %, 2025: +3,9 %, 2026: +2,0 %.
- **In Dollar bei 5.000 $:** etwa 0,80 $ Rebate und 0,45 $ netto pro Tag im Prüfzeitraum.

### Was nicht stärker war

| Idee | Versuche | Ergebnis |
|---|---|---|
| Marktneutrale Rangfolge (starke Coins gegen schwache) | 6 | In der Entwicklung auf Gruppe A gut, dann nicht bestätigt: Prüfzeitraum Gruppe A −5,5 %, Gruppe C in der Entwicklung −66,6 % (Hebel 1) |
| Mischung Kandidat + Rangfolge | – | Formal knapp vorn (Entwicklung +31,7 % gegen +30,5 %, Prüfzeitraum +5,9 % gegen +3,9 %). Nicht gewertet, weil der zugemischte Baustein selbst durchfiel |
| Den großen Händlern folgen, gegen die Masse | 1 | Entwicklung, erste Hälfte −8,7 %: durchgefallen |
| Gegen überfüllte Long-Seiten | 1 | Besteht die Entwicklung, fällt bei doppelten Kosten durch (−1,8 % in der ersten Hälfte) |
| Trend nur bei steigendem Open Interest | 1 | Erste Hälfte −15,1 %: schlechter als der Trend ohne Filter |
| Orderfluss (Kauf- gegen Verkaufsdruck) | 1 | Besteht Entwicklung und Kosten-Stress, Prüfzeitraum Gruppe A −18,2 %: nicht bestätigt |
| Kandidat nur auf den 23 heute günstigen Coins | 1 | Prüfzeitraum +16,5 %, Entwicklung +39,8 %. Sieht stark aus, enthält aber Rückschau (siehe unten) |
| Kandidat auf den jeweils 20 umsatzstärksten Coins, ohne Rückschau | 1 | Prüfzeitraum +5,1 %, Entwicklung +22,4 % bei Hebel 0,15: nicht besser |
| Neue Listings short gegen BTC long (275 Paare) | 1 | Entwicklung +57,4 %, Prüfzeitraum −107,7 % (Hebel 1). Schlechter als 98 % der Placebo-Läufe: durchgefallen |

**Warum ich die +16,5 % nicht als Edge werte:** Die Auswahl „heute günstig handelbar“ bevorzugt Coins, die zuletzt
stark gelaufen sind und deshalb viel Umsatz haben. Genau an solchen Coins verdient Trendfolge im Rückblick.
Die Gegenprobe ohne Rückschau (Auswahl nur nach damals bekanntem Umsatz) bringt keinen Vorsprung.

**Zur Listing-Idee (Runde 10):** Sie nutzt eine andere Ertragsquelle als Kursmuster: den Verkaufsdruck auf neu
gelistete Token. In der Entwicklung sah sie überzeugend aus. Im Prüfzeitraum gewinnen zwar 61 % der Paare,
aber 33 von 133 laufen in den Stop (der Coin verdoppelt sich gegen BTC), und das Funding kostet im Mittel
4,4 % je Paar. Im Mittel verliert ein Paar 17,1 %.

### Wenig Kapital und Hebel

**Mindestgrößen.** Yubit verlangt bei BTC rund 66 $ je Order, bei ETH 19 $, bei SOL und AVAX 8 $, sonst unter 1 $.

| Kapital | Betrag je Coin bei Hebel 0,2 | Handelbare Coins |
|---|---|---|
| 100 $ | 2,00 $ | 6 von 10 (ohne BTC, ETH, SOL, AVAX) |
| 300 $ | 6,00 $ | 6 von 10 (ohne BTC, ETH, SOL, AVAX) |
| 500 $ | 10,00 $ | 8 von 10 (ohne BTC, ETH) |
| 1.000 $ | 20,00 $ | 9 von 10 (ohne BTC) |
| 3.000 $ | 60,00 $ | 9 von 10 (ohne BTC) |
| 5.000 $ | 100,00 $ | 10 von 10 |

Ohne BTC und ETH (8 Coins, Hebel 0,2) bringt der Kandidat in der Entwicklung +40,3 % und im Prüfzeitraum +1,9 %
statt +41,3 % und +5,2 %. Kleine Konten verlieren also einen Teil des Ergebnisses.

**Mehr Hebel.** Der unveränderte Kandidat mit echten Kosten und Tageslimit 3 %:

| Hebel | Netto pro Jahr, Entwicklung | Einbruch, Entwicklung | Netto pro Jahr, Prüfzeitraum | Einbruch, Prüfzeitraum | Tage mit Tageslimit |
|---|---|---|---|---|---|
| 0,2 | +11,4 % | 9 % | +3,3 % | 10 % | 3 |
| 0,5 | +22,8 % | 18 % | +10,6 % | 20 % | 64 |
| 1,0 | +13,2 % | 38 % | −16,9 % | 53 % | 375 |
| 2,0 | −25,7 % | 102 % | −11,2 % | 58 % | 885 |
| 3,0 | −101,3 % | 359 % | −39,9 % | 98 % | 1178 |

- Bei Hebel 0,5 steigt der Ertrag, der Einbruch liegt dann aber bei rund 20 % und damit über deiner 15-%-Grenze.
- Ab Hebel 1 kippt es: Das Tageslimit greift an Hunderten Tagen, schließt alles mit Verlust und verpasst die Erholung.
  Im Prüfzeitraum ist das Ergebnis dann negativ.
- Der Kandidat lässt sich also nicht durch Hebel zu einem guten Edge für kleines Kapital machen.

**Zwei Korrekturen an meiner eigenen Arbeit:** Das Kriterium „stärker“ in Runde 6 war zu weich formuliert und hätte
die Mischung durchgewinkt; ich habe sie nicht gewertet und das Kriterium für Runde 7 verschärft. Und die
Coin-Auswahl in Runde 8 enthielt die beschriebene Rückschau; Runde 9 hat das sauber nachgeprüft.

## Der Weg dorthin

Zehn Runden, 60 Versuche, alles vorab im Protokoll festgelegt (`suche_protokoll.md`).

1. **Runde 1 (30 Einstellungen, passive Limits):** 3 bestehen die Entwicklung, beide Finalisten fallen im Füll-Stress durch.
   Alle Gegenbewegungs-Ideen (Rücksetzer kaufen, schwache Coins kaufen) verlieren schon vor Gebühren.
2. **Runde 2 (10 Trend-Einstellungen, sofortige Ausführung):** durchgefallen. Die Diagnose zeigte einen Fehler in
   meinem Testaufbau: Das Tagesverlust-Limit von 3 % wurde bei vollem Einsatz an jedem sechsten Tag ausgelöst
   und hat das Ergebnis dominiert.
3. **Runde 3 (dieselben 10, Messfehler korrigiert):** 2 Finalisten. Einer fällt im Prüfzeitraum klar durch
   (4-Tage-Trend), der 14-Tage-Trend besteht alle fünf Stufen.

4. **Runde 4 (keine Suche):** der Kandidat unverändert auf 20 frischen Coins und der Vorperiode 2020–2021. Bestätigt.

5. **Runde 5 (7 Varianten, tiefer gegraben):** Risikosteuerung, Trend-Mischung, Funding-Carry. Kein Mehrwert.
   Eine vierte, frische Coin-Gruppe zeigt den Kandidaten im Prüfzeitraum bei netto null.

6. **Runde 6 (6 Einstellungen):** echte Yubit-Kosten gemessen; marktneutrale Rangfolge nicht robust.
7. **Runde 7 (4 Hypothesen):** Positionierungsdaten von Binance (Open Interest, Long/Short-Verhältnisse, Orderfluss).
   Keine besteht.
8. **Runde 8 (1 Variante):** nur heute günstige Coins. Im Prüfzeitraum stark, aber mit Rückschau in der Auswahl.
9. **Runde 9 (1 Variante):** dieselbe Idee ohne Rückschau. Kein Vorsprung.
10. **Runde 10 (1 Hypothese):** neue Listings short gegen BTC. In der Entwicklung gut, im Prüfzeitraum klar negativ.

Der Prüfzeitraum und die zweite Coin-Gruppe wurden erst in Runde 3 angesehen, und nur für diese zwei Finalisten.
Insgesamt sind es jetzt 60 Versuche. Der Kern des Befunds hat sich seit Runde 3 nicht mehr bewegt: ein kleiner
Trend-Vorteil vor Gebühren, der nach Kosten vor allem mit Rebate trägt.
Wichtig für die Einordnung: Bei 60 Versuchen ist ein einzelner Treffer weniger wert als ein Treffer beim ersten
Versuch. Deshalb habe ich knappe oder nur formale Treffer nicht als Erfolg gewertet.

## Was das für dein Ziel bedeutet

- **Rebate hängt am Umsatz, Umsatz hängt am Einsatz, und den Einsatz begrenzt deine 15-%-Grenze.**
  Diese Strategie schlägt den eingesetzten Betrag etwa 1,1-mal pro Tag um. Mit Hebel 0,2 ergibt das
  rund 5,8 % des Kapitals als Rebate pro Jahr.
- **Mehr Hebel bringt mehr Rebate, aber im selben Maß mehr Einbruch.** Bei Hebel 1 lag der Einbruch im
  Prüfzeitraum bei 39 %.
- **Der Gewinn kommt hier wirklich aus dem Rebate.** In den Jahren 2022, 2025 und 2026 hätte der Handel ohne Rebate
  verloren. Wird das Rebate gekürzt oder gestrichen, trägt die Strategie nach heutigem Stand nicht mehr.
  Das ist genau die Abhängigkeit, die du mit „kein Rebate-Farming“ ursprünglich ausschließen wolltest.
- **Mehr Rebate heißt hier nicht mehr Gewinn.** Deine reine Tages-Swing (momentum_vol_ls) hätte im selben
  Prüfzeitraum beim selben Hebel +4,1 % netto gebracht, also mehr als der Kandidat (+2,4 %),
  mit rund einem 13tel des Umsatzes. Der Kandidat tauscht Gewinn gegen Volumen.

## Risiken und Annahmen

- **Yubit ist nicht getestet.** Kurse, Funding und Slippage stammen von Binance-Futures. Die Slippage bei Yubit ist
  die eine Zahl, die über Gewinn oder Verlust entscheidet.
- **Regel-Auslegung:** Du hast „Limit-Orders für Einstiege“ verlangt. Der Kandidat nutzt Limits mit Preisgrenze,
  die sofort gefüllt werden. Dem Ordertyp nach ist das ein Limit, den Gebühren nach ein Taker.
- **Risikokontrolle der Börse:** Ein Konto, dessen Gewinn überwiegend aus Rebate stammt, kann dort auffallen.
  Prüf, ob die Freigabe deines Partners das ausdrücklich abdeckt.
- **Rebate:** gerechnet als sofortige Gutschrift von 85 % der Gebühr.
- **Die Coins wurden im Rückblick festgelegt,** und der Prüfzeitraum umfasst nur 19 Monate.
- **Keine Zinseszins-Rechnung,** feste Positionsgröße vom Startkapital.

## Dateien

- `suche_protokoll.md`: Regeln und Zwischenergebnisse aller drei Runden
- `suche_stufe1.csv`, `suche_runde2_stufe1.csv`, `suche_runde3_stufe1.csv`: alle 40 Einstellungen mit Zahlen
- `suche_runde3.json`, `suche_runde4.json`, `suche_runde5.json`, `gesamt_60.json`, `kandidat.json`, `fuellmodell_diagnose.json`: Rohwerte zu diesem Bericht
- `suche_runde6.json` bis `suche_runde10.json`, `yubit_erstmessung.md`: echte Kosten und die Runden 6 bis 10
- `diagnose_frequenz.csv`, `diagnose_kapital.json`: Geschwindigkeit, Hebel und Mindestkapital
- `../vorwaertstest/`: der Vorwärtstest für Yubit (Anleitung in `README.md`, Regeln in `YUBIT_REGELN.md`)
- `../labor_strategie/trend_14d/strategie.py`: der Kandidat im Format deines Labors
- `../scripts/vorwaertstest_auswerten.py`: wertet ein Protokoll echter Orders aus (Slippage gegen die Schmerzgrenze)
