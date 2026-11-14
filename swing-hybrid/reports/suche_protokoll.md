# Suchprotokoll: Strategie mit hohem Umsatz und Rebate als größerem Gewinnanteil

Festgelegt am 14.11.2026, **bevor** ein Ergebnis dieser Suche vorlag. Historische Simulation, keine Anlageberatung.

## Ziel (Vorgabe des Users)

Eine Strategie, die im Handel profitabel ist und bei der das Rebate der größere Teil des Gewinns ist.
Rechnerisch: G = Ergebnis vor Gebühren, F = gezahlte Gebühr, R = 0,85 × F, N = G − F + R (netto mit Rebate).

Eine Lösung muss erfüllen:
1. G > 0 (Handel vor Gebühren profitabel). Zusätzlich wird berichtet, ob G − F ≥ 0 (auch nach voller Gebühr).
2. N > 0.
3. R > N − R (Rebate ist der größere Anteil am Nettogewinn).
4. Alle harten Regeln: kein HFT, nie Orders gegeneinander, Hebel ≤ 5, Limit für alle planbaren Orders,
   Market nur für Stop / Tagesverlust-Limit, Order-zu-Fill ≤ 5:1, Standzeit ≥ 15 Minuten, Obergrenze je Coin,
   Tagesverlust-Limit 3 %.
5. Größter Einbruch < 15 % beim gewählten Hebel.

## Schutz vor Selbsttäuschung

- **Zeit:** Entwicklung nur 15.08.2021 – 31.03.2025 (70 %), geteilt in D1 (bis 30.06.2023) und D2.
  Prüfzeitraum 01.04.2025 – 23.10.2026 wird je Finalist genau einmal angesehen.
- **Coins:** Gruppe A (die 10 Labor-Coins) für die Auswahl. Gruppe B (BNB, TRX, ATOM, BCH, ETC, FIL, UNI, NEAR, XLM,
  AAVE) nur als Gegenprobe, nie zur Auswahl.
- **Umfang:** 4 Familien, zusammen 30 Einstellungen. Alles wird berichtet, auch was durchfällt.

| Familie | Idee | Einstellungen |
|---|---|---|
| tsmom | Trend über L Stunden: gestiegen → Long, gefallen → Short | L = 12/24/48/96/168, mit/ohne Tagestrend-Filter |
| ensemble | Mittel aus 6 Trendlängen (12 h bis 14 Tage) | mit/ohne Tagestrend-Filter |
| reversal | Kurs k Standardabweichungen vom n-Stunden-Mittel entfernt → Gegenposition bis zurück am Mittel | n = 24/72, k = 1,5/2,0/2,5, mit/ohne Filter |
| querschnitt | alle 4 h: stärkste 3 Coins gegen schwächste 3 (oder umgekehrt) | L = 4/24/72, Trend/Gegentrend |

Tagestrend-Filter = der ursprüngliche „Swing-Bias“: nur in Richtung der 60-Tage-Rendite handeln.

## Ablauf und Hürden

1. **Stufe 1 (Entwicklung, Gruppe A, Hebel 1):** bestanden, wenn in D1 **und** D2 jeweils G > 0, N > 0, Order-zu-Fill ≤ 5.
   Je Familie höchstens ein Finalist: die Einstellung mit dem besten schlechteren Halbzeit-Sharpe (netto mit Rebate).
   Höchstens 3 Finalisten.
2. **Stufe 2 (Füll-Stress, Entwicklung):** jeder Limit-Fill 0,01 % schlechter und erst eine Kerze später möglich.
   N muss in D1 und D2 positiv bleiben.
3. **Stufe 3 (einmalig):** Prüfzeitraum Gruppe A und Gruppe B über alles. Bestanden, wenn G > 0 und N > 0 im
   Prüfzeitraum (A) und N > 0 für Gruppe B in Entwicklung und Prüfzeitraum.
4. **Stufe 4 (Zufallstest):** dasselbe Signal 200-mal zeitlich verschoben. Die echte Strategie muss besser sein als 90 %.
5. **Stufe 5 (Hebel):** Hebel so, dass der Einbruch in der Entwicklung ≤ 10 % ist (höchstens 5). Im Prüfzeitraum
   muss er unter 15 % bleiben.

Besteht kein Finalist alle Stufen, lautet das Ergebnis „keine Lösung gefunden“. Es wird nicht nachgebessert,
bis es passt; eine zweite Runde ist nur mit neuen, begründeten Ideen und neuem Protokoll zulässig, und die
Gesamtzahl der Versuche wird mitgezählt.

## Füllmodell

5-Minuten-Kerzen der Binance-Futures. Limit zum letzten Schlusskurs, gefüllt nur, wenn eine Kerze den Preis um mehr
als 0,01 % durchhandelt, zum Limitpreis. Nach 15 Minuten ungefüllt: streichen, neu einstellen. Eine Order je Coin.

---

# Runde 1: Ergebnis (14.11.2026)

- Stufe 1: 3 von 30 Einstellungen bestehen beide Entwicklungshälften. Alle Gegenbewegungs-Strategien (reversal,
  querschnitt „rev“) verlieren schon vor Gebühren. Finalisten: `querschnitt_L72_mom`, `tsmom_L168` mit Tagestrend-Filter.
- **Stufe 2: beide Finalisten fallen durch.** Unter Füll-Stress kippt das Ergebnis von +29 % auf −82 %.
- Diagnose (`fuellmodell_diagnose.json`, nur Entwicklungszeitraum): Das Signal ist zu Eröffnungskursen etwas wert
  (5 bzw. 11 Basispunkte je umgesetztem Dollar). Was davon bei **passiven** Limit-Orders übrig bleibt, hängt fast
  vollständig an der Füllannahme und lässt sich mit 5-Minuten-Kerzen nicht belastbar bestimmen.

**Runde 1: keine Lösung.** Der Prüfzeitraum und Gruppe B wurden für keine Einstellung angesehen.

# Runde 2: Protokoll (festgelegt vor dem ersten Ergebnis dieser Runde)

**Neue, begründete Idee:** nicht das Signal ändern, sondern die unsichere Annahme entfernen. Statt passiver Limits
eine Limit-Order mit Preisgrenze durch den Markt („marktfähiges Limit“): sofort gefüllt, zählt als Taker
(0,08 %, mit Rebate effektiv 0,012 %). Abrechnung: Eröffnungskurs der Kerze plus 0,05 % Slippage.
Das braucht keine Annahme über Warteschlangen. Die Order ist dem Typ nach ein Limit (Preisschutz), verdient aber kein
Maker-Rebate; das ist eine Auslegung der Regel „Limit für Einstiege“ und wird im Bericht so benannt.
Order-zu-Fill ist dabei 1:1, es gibt keine Stornos.

**Umfang:** nur die Trend-Familie, 10 Einstellungen: tsmom L = 48/96/168/336 Stunden mit/ohne Tagestrend-Filter,
ensemble mit/ohne Filter. Gegenbewegung und Rangfolge werden nicht erneut getestet.
Gesamtzahl der Versuche dieser Suche damit: 40.

**Hürden:**
1. Stufe 1 (Entwicklung, Gruppe A, Hebel 1): in D1 und D2 jeweils G > 0 und N > 0. Höchstens 2 Finalisten nach dem
   besseren schlechteren Halbzeit-Sharpe.
2. Stufe 2 (Stress): doppelte Slippage (0,10 %). N muss in D1 und D2 positiv bleiben.
3. Stufe 3 (einmalig): Prüfzeitraum Gruppe A: G > 0 und N > 0. Gruppe B: N > 0 in Entwicklung und Prüfzeitraum.
4. Stufe 4: Zufallstest, besser als 90 % von 200 zeitlich verschobenen Signalen.
5. Stufe 5: Hebel so, dass der Einbruch in der Entwicklung ≤ 10 % ist (höchstens 5); im Prüfzeitraum < 15 %.

Lösung nur, wenn alle Stufen bestanden sind und im Prüfzeitraum G > 0, N > 0 und R > N − R gilt.

---

# Runde 2: Ergebnis (14.11.2026)

- Stufe 1: nur `tsmom_L336` mit Tagestrend-Filter besteht beide Entwicklungshälften.
- **Stufe 2: durchgefallen** (doppelte Slippage: N in beiden Hälften negativ).
- **Runde 2: keine Lösung.** Prüfzeitraum und Gruppe B wurden nicht angesehen.

Diagnose (nur Entwicklungszeitraum): Das Tagesverlust-Limit von 3 % wurde bei Hebel 1 an 222 von 1.324 Tagen ausgelöst.
Jede Auslösung schließt alles per Market und setzt den Rest des Tages aus. Bei `tsmom_L168` mit Filter sinkt das
Ergebnis vor Gebühren dadurch von +91 % auf +31 %. Stufe 1 hat also nicht das Signal gemessen, sondern vor allem das
Limit. Der Fehler liegt im Testaufbau: Das Limit gehört zum tatsächlich gewählten Hebel (Stufe 5), nicht zur
Messung bei vollem Einsatz. Zweiter Mangel aus Runde 1: Der Füll-Stress „eine Kerze später“ ließ die Order fünf
Minuten mit altem Preis liegen, ohne dass sie im Buch war. Das bildet keinen realen Ablauf ab.

# Runde 3: Protokoll (festgelegt vor dem ersten Ergebnis dieser Runde)

**Keine neuen Signale.** Dieselben 10 Trend-Einstellungen wie in Runde 2. Geändert wird nur die Messung:

- Stufen 1–4 messen bei Hebel 1 **ohne** Tagesverlust-Limit. Das Limit (3 %) gilt in Stufe 5 beim gewählten Hebel.
- Statt eines künstlichen Füll-Stresses muss ein Kandidat unter **zwei unabhängigen Ausführungsarten** bestehen:
  passiv (Limit zum letzten Schluss, 0,01 % Durchhandeln) **und** sofort (marktfähiges Limit, Taker, 0,05 % Slippage).
  Die zweite Art kommt ohne Füllannahme aus.

**Hürden:**
1. Stufe 1 (Entwicklung, Gruppe A): G > 0 und N > 0 in D1 **und** D2, in **beiden** Ausführungsarten. Höchstens
   2 Finalisten nach dem schlechtesten der vier Halbzeit-Sharpe-Werte.
2. Stufe 2: passiv mit 0,01 % schlechterem Füllpreis: N > 0 in D1 und D2.
3. Stufe 3 (einmalig): Prüfzeitraum Gruppe A: G > 0 und N > 0 in beiden Ausführungsarten. Gruppe B: N > 0 in
   Entwicklung und Prüfzeitraum, in beiden Ausführungsarten.
4. Stufe 4: Zufallstest (sofortige Ausführung, ganzer Zeitraum): besser als 90 % von 200 verschobenen Signalen.
5. Stufe 5: sofortige Ausführung mit Tagesverlust-Limit 3 %. Hebel so, dass der Einbruch in der Entwicklung ≤ 10 %
   ist (höchstens 5, mindestens 0,1). Im Prüfzeitraum: Einbruch < 15 %, G > 0, N > 0, R > N − R.

Gesamtzahl der Versuche: weiterhin 40 Signal-Einstellungen, jetzt im dritten Messaufbau. Das wird im Bericht genannt.
Danach ist Schluss: Besteht nichts, lautet das Ergebnis „keine Lösung innerhalb der Regeln“.

---

# Runde 3: Ergebnis (14.11.2026)

`tsmom_L336` ohne Filter (14-Tage-Trend, stündlich, sofortige Ausführung) besteht alle fünf Stufen, bei Hebel 0,2.
Im Prüfzeitraum dünn: netto mit Rebate +2,4 %, Zufallstest nur im Prüfzeitraum 80 %. Details in `suche_bericht.md`.

# Runde 4: Bestätigung auf frischen Daten (festgelegt vor dem ersten Ergebnis)

**Keine Suche, keine Auswahl, keine Parameter.** Der Kandidat wird exakt so getestet, wie er ist
(L = 336 Stunden, gleiche Größe je Coin, sofortige Ausführung, 0,05 % Slippage), auf Daten, die bisher nie benutzt wurden:

1. **Gruppe C:** die ersten 20 Coins dieser festen Liste, für die das Binance-Archiv von 07/2021 bis 10/2026
   lückenlose Monatsdateien hat: XMR, ZEC, DASH, ALGO, VET, THETA, EGLD, SUSHI, COMP, SNX, CRV, 1INCH, GRT, SAND,
   MANA, AXS, CHZ, ENJ, KSM, ZIL, IOTA, NEO, ONT, QTUM, XTZ, RUNE, KAVA, BAT, ZRX, YFI, HBAR, ICP.
   Die Liste stammt aus dem Gedächtnis (Perpetuals, die Mitte 2021 schon handelbar waren), nicht aus Ergebnissen.
   Einschränkung: Nur Coins mit vollständiger Historie bis 2026, das schönt etwas (Überlebende).
2. **Vorperiode:** 01.02.2020 – 14.08.2021 für alle Coins, die dort schon handelbar waren.

**Bestätigt** heißt: Gruppe C netto mit Rebate > 0 in Entwicklung **und** Prüfzeitraum, und die Vorperiode über alle
Coins zusammen netto mit Rebate > 0. Jeweils Hebel 1, ohne Tageslimit.

3. **Breites Portfolio (nur Bericht, keine Hürde):** alle Gruppen zusammen. Hebel wie in Stufe 5 (Einbruch in der
   Entwicklung ≤ 10 %, mit Tageslimit 3 %). Frage: Senkt die breitere Streuung den Einbruch so weit, dass mehr Hebel
   und damit mehr Rebate möglich wird?

---

# Runde 4: Ergebnis (14.11.2026)

**Bestätigt.** Gruppe C (20 frische Coins) netto mit Rebate positiv in Entwicklung und Prüfzeitraum, Vorperiode
02/2020–08/2021 über alle 40 Coins positiv. ICP schied wegen unvollständiger Funding-Historie aus.
Breites Portfolio: zulässiger Hebel bleibt 0,2; Prüfzeitraum netto mit Rebate +5,5 %.
Damit sind alle frischen Daten verbraucht. Weitere Erkenntnis nur noch aus dem Vorwärtstest.

---

# Runde 5: Mehr aus dem Trend holen (festgelegt vor dem ersten Ergebnis)

**Begründung:** Rebate = Umsatz × Satz, Umsatz = Einsatz × Umschlag, und den Einsatz begrenzt die 15-%-Grenze.
Mehr Rebate und mehr Gewinn gibt es also nur über ein besseres Verhältnis von Ertrag zu Einbruch.
Dafür gibt es drei in der Trendfolge übliche Hebel und eine zweite, unabhängige Ertragsquelle.

**Varianten (7, alle auf 40 Coins = Gruppen A+B+C, sofortige Ausführung, 0,05 % Slippage):**

| # | Name | Idee |
|---|---|---|
| 0 | basis | der Kandidat: 14-Tage-Trend, alle Coins gleich groß |
| 1 | vol_coin | ruhige Coins größer, wilde kleiner (Größe ∝ 1/Schwankung der letzten 20 Tage, Stufen von 25 %, 0,25- bis 2-fach) |
| 2 | vol_markt | in wilden Marktphasen alles kleiner (Marktschwankung gegen ihren bisherigen Median, 0,5- bis 1,5-fach) |
| 3 | vol_beide | 1 und 2 zusammen |
| 4 | mischung | Mittel aus vier Trendlängen: 7, 14, 28 und 60 Tage |
| 5 | carry | neue Quelle: Coins mit dem höchsten Funding der letzten 3 Tage short, die mit dem niedrigsten long (je ein Viertel), marktneutral |
| 6 | trend_carry | beste Trend-Variante und carry je zur Hälfte, nur falls carry allein besteht |

**Auswahl (nur Entwicklungszeitraum):** Eine Variante ersetzt die Basis nur, wenn sie in D1 und D2 vor Gebühren und
netto positiv ist **und** ihr schlechterer Halbzeit-Sharpe den der Basis um mindestens 0,10 übertrifft.
Gewinnt keine, bleibt es bei der Basis („kein Mehrwert“).

**Prüfung der Gewinnerin:**
1. Hebel wie bisher (Einbruch in der Entwicklung ≤ 10 %, Tageslimit 3 %), dann Prüfzeitraum. Der Prüfzeitraum ist
   für Trend-Signale nicht mehr ganz unberührt: Ich weiß aus Runde 3 und 4, dass er für Trend schwach war.
2. **Gruppe D (frisch):** 20 Coins, die bisher nirgends vorkamen: die 11 unbenutzten der Liste aus Runde 4 (IOTA, NEO,
   ONT, QTUM, XTZ, RUNE, KAVA, BAT, ZRX, YFI, HBAR), aufgefüllt mit den ersten vollständigen aus LRC, OCEAN, ONE, STORJ,
   ANKR, RLC, BAND, KNC, ZEN, CELR, COTI, SKL, IOST, ICX, RVN, TRB, MTL, CHR, HOT, DENT.
   **Bestätigt** nur, wenn die Gewinnerin auf Gruppe D netto positiv ist (Entwicklung und Prüfzeitraum) **und** dort
   über den ganzen Zeitraum mehr Netto je Prozent Einbruch bringt als die Basis.

Gesamtzahl der Versuche danach: 47.

---

# Runde 5: Ergebnis (14.11.2026)

- Auswahlregel: `vol_beide` gewinnt in der Entwicklung (schlechtere Hälfte 0,74 gegen 0,44 der Basis).
- Beim zulässigen Hebel (0,15 statt 0,20) bringt sie im Prüfzeitraum weniger als die Basis (+3,9 % gegen +5,5 %).
- **Gruppe D: nicht bestätigt.** Im Prüfzeitraum netto −0,6 % (Hebel 1). Auch die Basis liegt dort bei −0,1 %.
- Funding-Carry und Trend-Mischung bestehen die Entwicklung nicht.

**Runde 5: kein Mehrwert.** Gesamtschätzung für den unveränderten Kandidaten über alle 60 Coins in `gesamt_60.json`:
Hebel 0,15, Prüfzeitraum netto mit Rebate +2,7 %, gesamter Zeitraum +27,6 %.
