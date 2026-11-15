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

---

# Runde 6: Echte Yubit-Kosten und marktneutrale Rangfolge (festgelegt vor dem ersten Ergebnis)

**Neue Information, keine neue Laune:** Am 14.11.2026 wurde an Yubits öffentlichem Orderbuch gemessen, dass die
Slippage für kleine Orders bei den großen Coins um 0,01 % liegt, nicht bei den bisher angenommenen 0,05 %.
Damit ändern sich zwei Dinge: (1) der bestehende Kandidat ist mit echten Kosten neu zu bewerten, (2) Strategien mit
mehr Umsatz, die an 0,05 % gescheitert sind, können tragen. Am wertvollsten wäre eine **marktneutrale** Strategie:
Sie hat weniger Einbruch je eingesetztem Dollar, erlaubt also mehr Hebel und damit mehr Umsatz und Rebate.
In Runde 1 war die Rangfolge über 72 Stunden die Einstellung mit den gleichmäßigsten Hälften, sie scheiterte dort
an einem falsch gebauten Füll-Stress und später an 0,05 % Slippage.

**Kostenmodell (fest, bevor Ergebnisse vorliegen):**
- Slippage je Coin = 2 × mittlere halbe Spanne Geld/Brief aus einer 60-Minuten-Stichprobe bei Yubit
  (alle 2 Minuten, 14.11.2026), mindestens 0,005 %. Der Faktor 2 ist ein Sicherheitsaufschlag.
- Sofortige Ausführung (Taker 0,08 %, mit Rebate effektiv 0,012 %). Nur Coins, die Yubit führt.
- Stress: doppelte Kosten (4 × halbe Spanne). Zusätzlich wird der alte Wert 0,05 % mitberichtet.

**Teil 1 (keine Auswahl):** der bestehende Kandidat (14-Tage-Trend) mit echten Kosten, Gruppe A und A+B.

**Teil 2 (Suche, 6 Einstellungen):** Rangfolge marktneutral. Die stärksten 30 % der Coins über L Stunden long, die
schwächsten 30 % short, umgeschichtet alle T Stunden. L = 72 / 168 / 336, T = 4 / 24.
1. Entwicklung nur Gruppe A: G > 0 und N > 0 in D1 **und** D2. Ein Finalist: bester schlechterer Halbzeit-Sharpe.
2. Stress in der Entwicklung (doppelte Kosten): N > 0 in D1 und D2.
3. Bestätigung, für diese Familie alles frisch: Prüfzeitraum Gruppe A mit G > 0 und N > 0; Gruppe B **und**
   Gruppe C (soweit bei Yubit gelistet) jeweils N > 0 in Entwicklung und Prüfzeitraum. Gruppe D wird berichtet.
4. Zufallstest (Gruppe A, ganzer Zeitraum): besser als 90 % von 200 verschobenen Signalen.
5. Hebel wie bisher: Einbruch in der Entwicklung ≤ 10 % mit Tageslimit 3 %, höchstens 5; im Prüfzeitraum < 15 %.

**Teil 3 (keine Suche):** Kombination aus Kandidat und Finalist je zur Hälfte auf A+B (20 Coins).

**„Stärkerer Edge gefunden“ heißt:** Der Finalist besteht alle fünf Stufen, **oder** die Kombination bringt beim
regelkonformen Hebel in Entwicklung **und** Prüfzeitraum mehr Netto mit Rebate als der Kandidat allein
(beides mit echten Kosten, 20 Coins). Sonst lautet das Ergebnis „kein stärkerer Edge“.

Gesamtzahl der Versuche danach: 53. Die Spannen-Stichprobe ist eine Stunde eines einzigen Tages; das bleibt die
größte Unsicherheit und wird im Bericht so benannt.

---

# Runde 6: Ergebnis (14.11.2026)

Stichprobe: 30 Messungen, 15:40–16:39 UTC. Slippage-Annahme (2 × halbe Spanne): Gruppe A im Mittel 0,030 %
(Median 0,014 %, DOT 0,132 %, ADA 0,064 %), Gruppe B 0,033 %, Gruppe C 0,053 %, Gruppe D 0,078 %.

**Teil 1, Kandidat mit echten Kosten (Hebel 0,2):** Gruppe A: Entwicklung +41,3 %, Prüfzeitraum +5,2 % netto mit
Rebate (mit dem alten Wert 0,05 % waren es +2,4 %; mit doppelten Kosten +1,2 %). A+B: +30,5 % / +3,9 %.

**Teil 2, Rangfolge:** Alle 6 Einstellungen bestehen die Entwicklung auf Gruppe A. Finalist `rang_L168_T24`
(7 Tage, tägliche Umschichtung) besteht den Kosten-Stress. **Stufe 3: durchgefallen.** Prüfzeitraum Gruppe A −5,5 %,
Gruppe C in der Entwicklung −66,6 %, Gruppe D in beiden Zeiträumen negativ. Die Rangfolge ist nicht robust.

**Teil 3, Kombination auf A+B:** Hebel 0,35; Entwicklung +31,7 % (Kandidat allein +30,5 %), Prüfzeitraum +5,9 %
(Kandidat allein +3,9 %). Das erfüllt das vorab festgelegte Kriterium „stärker“ dem Wortlaut nach.

**Bewertung:** Ich werte das **nicht** als stärkeren Edge. Der Vorsprung in der Entwicklung ist winzig, und der
zugemischte Baustein hat seine eigene Robustheitsprüfung nicht bestanden. Das Kriterium war zu weich formuliert:
Es hätte verlangen müssen, dass der neue Baustein selbst besteht. Das wird in Runde 7 so festgelegt.
Belastbar ist aus Runde 6 nur Teil 1: Mit echten Yubit-Kosten ist der Kandidat besser als bisher gerechnet.

---

# Runde 7: Positionierungsdaten als neue Informationsquelle (festgelegt vor dem ersten Ergebnis)

**Begründung:** Aus Kursen allein kam in 53 Versuchen nur der Trend heraus. Neue Stärke kann nur aus neuer
Information kommen. Binance veröffentlicht für jeden Kontrakt alle 5 Minuten: offene Positionen (Open Interest),
das Long/Short-Verhältnis aller Konten, das Long/Short-Verhältnis der größten Händler und das Verhältnis von
Kauf- zu Verkaufs-Marktorders. Diese Daten kamen in der Suche bisher nicht vor.

**Vier Hypothesen, je genau eine Einstellung (keine Raster, keine Auswahl unter Varianten):**

| # | Name | Idee | Bauart |
|---|---|---|---|
| S1 | profis_gegen_menge | Coins kaufen, in denen die großen Händler stärker long sind als die Masse; die umgekehrten verkaufen | marktneutral |
| S2 | gegen_die_menge | Coins verkaufen, in denen ungewöhnlich viele Konten long sind; die mit den wenigsten kaufen | marktneutral |
| S3 | trend_frisches_geld | der Kandidat (14-Tage-Trend), aber nur solange das Open Interest höher ist als vor 7 Tagen | gerichtet |
| S4 | orderfluss | Coins kaufen, in denen 7 Tage lang die Kauf-Marktorders überwogen; die umgekehrten verkaufen | marktneutral |

Feste Bauteile: Abweichung vom eigenen 30-Tage-Mittel in Standardabweichungen (S1, S2), 7-Tage-Fenster (S3, S4),
stärkste 30 % gegen schwächste 30 %, Umschichtung alle 24 Stunden, Signal erst nach Stundenschluss wirksam.
Kosten wie in Runde 6 (2 × gemessene halbe Yubit-Spanne je Coin, Taker mit Rebate).

**Hürden je Hypothese (jede steht für sich):**
1. Entwicklung Gruppe A: G > 0 und N > 0 in D1 und D2.
2. Doppelte Kosten: N > 0 in D1 und D2.
3. Bestätigung: Prüfzeitraum Gruppe A mit G > 0 und N > 0; Gruppe B und Gruppe C (bei Yubit gelistet) jeweils
   N > 0 in Entwicklung und Prüfzeitraum.
4. Zufallstest (Gruppe A, ganzer Zeitraum): besser als 90 % von 200 verschobenen Signalen.
5. Hebel: Einbruch in der Entwicklung ≤ 10 % mit Tageslimit, im Prüfzeitraum < 15 %, dort G > 0 und N > 0.

**„Stärkerer Edge“ (strenger als in Runde 6):** Die Hypothese besteht **selbst** alle fünf Hürden **und** bringt
auf A+B beim regelkonformen Hebel in Entwicklung und Prüfzeitraum mehr Netto mit Rebate als der Kandidat allein:
S3 für sich, S1/S2/S4 als Mischung je zur Hälfte mit dem Kandidaten.

Gesamtzahl der Versuche danach: 57. Einschränkung für den Betrieb: Die Signale kämen live von Binance, gehandelt
würde bei Yubit.

---

# Runde 7: Ergebnis (14.11.2026)

Positionierungsdaten für 49 Coins geladen (ab 01.12.2021, BTC ab 07/2021). Kandidat als Maßstab auf A+B: Hebel 0,2,
Entwicklung +30,5 %, Prüfzeitraum +3,9 %.

| Hypothese | Ergebnis |
|---|---|
| S1 profis_gegen_menge | Stufe 1 durchgefallen (erste Hälfte −8,7 %) |
| S2 gegen_die_menge | Stufe 1 bestanden, Stufe 2 durchgefallen (erste Hälfte bei doppelten Kosten −1,8 %) |
| S3 trend_frisches_geld | Stufe 1 durchgefallen (erste Hälfte −15,1 %); schlechter als der Trend ohne Filter |
| S4 orderfluss | Stufen 1 und 2 bestanden, Stufe 3 durchgefallen (Prüfzeitraum Gruppe A −18,2 %, Gruppe C Entwicklung −23,3 %) |

**Runde 7: kein stärkerer Edge.**

# Runde 8: Kandidat nur auf günstig handelbaren Coins (festgelegt vor dem ersten Ergebnis)

**Keine Suche, eine einzige Variante.** Die Auswahl der Coins hängt nur an den gemessenen Yubit-Kosten, nicht an
Ergebnissen: alle bei Yubit gelisteten Coins der vier Gruppen, deren Slippage-Annahme (2 × halbe Spanne) höchstens
0,03 % beträgt („günstige Coins“). Darauf läuft der unveränderte Kandidat mit echten Kosten und regelkonformem Hebel.

**Besser** heißt: mehr Netto mit Rebate als der Kandidat auf Gruppe A, in Entwicklung **und** Prüfzeitraum, und im
Prüfzeitraum auch bei doppelten Kosten positiv. Sonst bleibt Gruppe A die Empfehlung.
Hinweis zur Einordnung: Ich kenne aus früheren Runden die Ergebnisse je Gruppe, aber nicht je Coin.
Gesamtzahl der Versuche danach: 58.

---

# Runde 8: Ergebnis (14.11.2026)

23 günstige Coins (Slippage-Annahme ≤ 0,03 %): BTC, ETH, SOL, XRP, DOGE, LINK, AVAX, LTC, BNB, TRX, BCH, ETC, UNI, XLM,
AAVE, XMR, ZEC, DASH, 1INCH, MANA, AXS, RUNE, HBAR. Hebel 0,2.

| | Gruppe A (10 Coins) | 23 günstige Coins |
|---|---|---|
| Entwicklung, netto mit Rebate | +41,3 % | +39,8 % |
| Prüfzeitraum, netto mit Rebate | +5,2 % | +16,5 % |
| Prüfzeitraum bei doppelten Kosten | +1,2 % | +14,7 % |

**Nach der Regel: nicht besser** (in der Entwicklung knapp darunter).
**Wichtiger Vorbehalt zum Prüfzeitraum:** Die Auswahl nach heutiger Spanne enthält Rückschau. Coins, die heute eng
gehandelt werden, sind oft solche, die zuletzt stark gelaufen sind und deshalb viel Umsatz haben. Genau an solchen
Coins verdient Trendfolge. Die +16,5 % sind deshalb nach oben verzerrt und kein Beleg.

# Runde 9: Auswahl nach damals bekanntem Umsatz (festgelegt vor dem ersten Ergebnis)

**Eine Variante, keine Suche.** Sie prüft dieselbe Idee ohne Rückschau: zu jedem Monatsbeginn die 20 Coins mit dem
höchsten Binance-Umsatz der vorangegangenen 30 Tage wählen (aus allen bei Yubit gelisteten Test-Coins), einen Monat
lang nur diese handeln, dann neu wählen. Signal, Kosten (heutige Yubit-Spannen) und Hebelregel unverändert.

**Besser** heißt wie in Runde 8: mehr Netto mit Rebate als der Kandidat auf Gruppe A in Entwicklung **und**
Prüfzeitraum, und im Prüfzeitraum auch bei doppelten Kosten positiv.
Verbleibende Einschränkung: Die Liste der 59 Coins selbst enthält nur solche, die bis 2026 überlebt haben.
Gesamtzahl der Versuche danach: 59.

---

# Runde 9: Ergebnis (14.11.2026)

Berichtigung zum Protokolltext oben: Es sind 49 bei Yubit gelistete Test-Coins, nicht 59.

Immer die 20 umsatzstärksten von 49 Coins, Hebel 0,15: Entwicklung +22,4 %, Prüfzeitraum +5,1 % netto mit Rebate
(Gruppe A: +41,3 % / +5,2 %). **Nicht besser.** Damit ist der Vorbehalt aus Runde 8 bestätigt: Der dortige Vorsprung
im Prüfzeitraum kam aus der Rückschau in der Coin-Auswahl, nicht aus einem stärkeren Edge.

# Stand nach 9 Runden und 59 Versuchen

- **Kein stärkerer Edge gefunden.** Marktneutrale Rangfolge, vier Hypothesen aus Positionierungsdaten und zwei
  Arten der Coin-Auswahl bestehen die vorab festgelegten Hürden nicht.
- **Belastbar besser geworden ist nur die Kostenrechnung:** Mit den an Yubit gemessenen Spannen bringt der
  unveränderte Kandidat (Gruppe A, Hebel 0,2) in der Entwicklung +41,3 % und im Prüfzeitraum +5,2 % netto mit Rebate,
  bei doppelten Kosten +1,2 %.
- Zwei Stellen, an denen ich mich korrigiert habe: Das Kriterium „stärker“ in Runde 6 war zu weich (in Runde 7
  verschärft), und die Coin-Auswahl in Runde 8 enthielt Rückschau (in Runde 9 sauber nachgeprüft).

---

# Diagnose: dasselbe Trend-Signal in sieben Geschwindigkeiten (14.11.2026)

Keine Kandidatensuche, sondern die Antwort auf die Frage „geht das auch schnell?“. Gruppe A, Hebel 1, echte
Yubit-Kosten (Slippage 2 × halbe Spanne, rund 0,029 % je Order, plus 0,012 % Gebühr nach Rebate). Zahlen in
`diagnose_frequenz.csv`.

| Rückblick | Ø Haltedauer | Umsatz/Tag (× Einsatz) | Signalwert je Dollar, Entwicklung / Prüfzeitraum | Netto je Dollar, Entwicklung / Prüfzeitraum |
|---|---|---|---|---|
| 6 h | 5 h | 9,7 | −0,005 % / +0,008 % | −0,046 % / −0,033 % |
| 12 h | 7 h | 6,8 | −0,002 % / +0,018 % | −0,043 % / −0,023 % |
| 24 h | 10 h | 4,6 | −0,009 % / −0,019 % | −0,050 % / −0,060 % |
| 48 h | 15 h | 3,2 | +0,041 % / +0,021 % | +0,001 % / −0,020 % |
| 96 h | 21 h | 2,2 | +0,076 % / −0,022 % | +0,035 % / −0,063 % |
| 168 h | 29 h | 1,6 | +0,097 % / +0,032 % | +0,056 % / −0,008 % |
| 336 h (Kandidat) | 42 h | 1,1 | +0,185 % / +0,080 % | +0,144 % / +0,039 % |

Ergebnis: Je schneller, desto kleiner der Signalwert je umgesetztem Dollar. Unter zwei Tagen Rückblick ist er schon
ohne Kosten null oder negativ. Die Kosten je Dollar bleiben gleich (rund 0,041 %).

---

# Runde 10: Neue Listings gegen BTC (festgelegt vor dem ersten Ergebnis)

**Begründung:** Kursmuster, Funding und Positionierung sind durchsucht. Ein wirklich guter Edge muss aus einer
anderen Ertragsquelle kommen. Neu gelistete Token stehen oft monatelang unter Verkaufsdruck: Freigaben gesperrter
Token, Verkäufe früher Investoren, nachlassende Aufmerksamkeit. Das ist ein struktureller Grund, kein Kursmuster.
Die Strategie handelt selten und in kleinen Stückgrößen, braucht also wenig Kapital.

**Eine Hypothese, eine Einstellung, keine Raster:**

- **Neu** ist ein Kontrakt, dessen erster Handelstag bei Binance-Futures am oder nach dem 01.09.2021 liegt.
  Betrachtet werden nur Kontrakte, die Yubit heute führt und für die Binance Daten hat. Aktien-, Rohstoff- und
  Index-Kontrakte werden anhand des Namens ausgeschlossen, bevor Ergebnisse vorliegen.
- **Einstieg:** Tagesschluss 7 Tage nach dem ersten Handelstag. Coin short, gleich großer Betrag BTC long.
- **Ausstieg:** Tagesschluss 90 Tage nach dem Einstieg, oder früher, wenn das Paar 100 % seines Einsatzes verloren
  hat (Stop), oder wenn die Daten enden.
- **Größe:** jedes Paar ein Zwanzigstel einer Einheit je Seite, fest ab Einstieg. Die Einheit wird über den Hebel
  skaliert.
- **Kosten:** Taker-Gebühr 0,08 % mit 85 % Rebate; Slippage je Order beim Coin 0,15 %, bei BTC 0,005 %;
  echtes Binance-Funding für beide Seiten (der Short erhält positives Funding und zahlt negatives).
- Das Tagesverlust-Limit entfällt hier (Tagesdaten, zwei Orders je Paar in 90 Tagen); maßgeblich ist die Einbruch-Regel.

**Hürden:**
1. Entwicklung: Ergebnis vor Gebühren und netto mit Rebate positiv in D1 (bis 30.06.2023) **und** D2 (bis 31.03.2025).
2. Stress: Slippage beim Coin 0,5 % je Order. Netto in D1 und D2 positiv.
3. Prüfzeitraum (ab 01.04.2025): vor Gebühren und netto positiv; die dort eröffneten Paare im Mittel im Plus,
   mit t-Wert mindestens 2.
4. Placebo: dieselben Termine, aber statt des neuen Coins ein zufällig gewählter alter Coin. Die echte Strategie
   muss besser sein als 90 % von 200 Placebo-Läufen. Das prüft, ob wirklich die Neuheit zählt.
5. Hebel: Einbruch in der Entwicklung ≤ 10 %, Gesamteinsatz höchstens das Fünffache; im Prüfzeitraum < 15 %.

**„Wirklich gut“** heißt: alle fünf Hürden bestanden **und** im Prüfzeitraum beim regelkonformen Hebel mindestens
10 % netto pro Jahr (der Trend-Kandidat liegt dort bei rund 3 %).

**Bekannte Verzerrungen, vorab benannt:** Es fehlen Coins, die Yubit oder Binance wieder gestrichen haben. Das sind
meist die schwächsten, ihr Fehlen macht einen Short eher schlechter als besser. Ob Yubit einen Coin zum
Einstiegstag schon führte, ist nicht bekannt. Gesamtzahl der Versuche danach: 60.

**Nachtrag zu Runde 10, vor dem ersten Ergebnis (Ausschlussregel):** Von 554 Yubit-Kontrakten haben 529
Binance-Daten, 474 davon mit erstem Handelstag ab 01.09.2021. Viele davon sind Aktien-, ETF- und Rohstoff-Kontrakte
aus dem Jahr 2026. Statt nach Namen wird objektiv getrennt: Ausgeschlossen ist jeder Kontrakt, dessen typische
Tagesbewegung am Wochenende unter 55 % der Wochentags-Bewegung liegt (der zugrunde liegende Markt ist dann am
Wochenende geschlossen). Die Verteilung ist klar zweigipflig (194 Kontrakte unter 45 %, 3 dazwischen, 276 darüber).
Zusätzlich nach Namen ausgeschlossen: ANTHROPIC (Unternehmensanteil, kein Token). Die Liste steht in
`scripts/listings_ausschluss.txt`. Es bleiben 275 neue Krypto-Listings
(2021: 6, 2022: 10, 2023: 43, 2024: 61, 2025: 127, 2026: 28).
Die frühen Jahrgänge sind dünn besetzt, weil nur Coins enthalten sind, die Yubit heute noch führt.

---

# Runde 10: Ergebnis (14.11.2026)

275 Paare, Portfolio bei Hebel 1. Entwicklung netto +57,4 % (D1 +22,0 %, D2 +35,4 %), Stress bestanden.
**Prüfzeitraum: −107,7 %.** Die dort eröffneten 133 Paare verlieren im Mittel 17,1 % (t = −2,1), obwohl 61 % von
ihnen gewinnen und der Median bei +17,6 % liegt: 33 Stops durch Coins, die sich gegen BTC verdoppelt haben, und
negatives Funding von im Mittel 4,4 % je Paar. Placebo: schlechter als 98 % der Zufallsläufe mit alten Coins.

**Runde 10: durchgefallen (Stufen 3, 4 und 5).** Die Hürden haben getan, wofür sie da sind: Nach der Entwicklung
allein hätte die Idee überzeugend ausgesehen. Hinzu kommt, dass die Auswahl „heute bei Yubit gelistet“ gerade die
Coins enthält, die überlebt haben und beliebt sind; das schadet einem Short stärker als vorab angenommen.
Gesamtzahl der Versuche: 60.

---

# Runde 11: Massentest „kleine Trades in Swing-Richtung, die ihre Gebühr verdienen“ (festgelegt vor dem ersten Ergebnis)

**Vorgabe des Users (präzisiert):** viele kleine, echte Trades in Richtung des Swing-Bias. Jeder Trade soll seine
eigene Gebühr mindestens wieder einspielen („2 € Gebühr, 2,20 € verdient“), das Rebate ist dann Gewinn obendrauf.
Erlaubt sind neue Indikatoren und abgewandelte Regeln. Nicht gebaut werden Trades, deren Zweck nur Volumen ist.

**Messlatte je Trade:** Deckung = Ertrag des Trades nach Slippage ÷ gezahlte Gebühr (0,16 % für Ein- und Ausstieg
als Taker). Deckung 1,0 heißt: Gebühr genau verdient. Die Vorgabe „2,20 € bei 2 €“ entspricht Deckung 1,1.
Slippage je Order wie in Runde 6 (2 × gemessene halbe Yubit-Spanne je Coin). Zusätzlich wird die Deckung für
Maker-Ausführung berichtet (0,08 % Gebühr, ohne Slippage) als optimistische Obergrenze.

**Regelraum (systematisch, rund 600 Varianten), Stundenkerzen:**
- Swing-Bias: Vorzeichen der 60-Tage-Rendite (wie momentum_vol_ls) oder der 14-Tage-Rendite (Kandidat).
- Einstieg nur in Bias-Richtung, eine Position je Coin, Einstieg zum Open der Folgekerze:
  Rücksetzer nach RSI (3 Längen × 3 Schwellen) · Rücksetzer nach Bollinger (2 × 3) · Ausbruch über das N-Stunden-Hoch
  (5) · Impuls in Bias-Richtung (3 × 2) · Rücksetzer-Impuls gegen die Richtung (3 × 2) · Volumenspitze mit oder gegen
  die Richtung (2 × 2) · feste Tageszeit (6) · „immer sofort wieder einsteigen“ als Vergleich (1).
- Ausstieg: feste Haltedauer 1 / 2 / 4 / 8 / 24 Stunden, oder Gewinnziel und Stop im Abstand von 1 bzw. 2
  Stunden-ATR mit Zeitlimit 24 Stunden (trifft eine Kerze beide, zählt der Stop).

**Hürden:**
1. Entwicklung Gruppe A: Deckung ≥ 1,0 in D1 **und** D2, mit jeweils mindestens 200 Trades.
2. Bestätigung für jede Regel, die Stufe 1 besteht: Deckung ≥ 1,0 im Prüfzeitraum Gruppe A, und in Gruppe B und
   Gruppe C jeweils in Entwicklung und Prüfzeitraum.
3. Wer das besteht, wird im vollen Rechenkern nachgerechnet (Funding, Tageslimit, Einbruch, Hebel).

**Erwartung vorab, damit das Ergebnis einzuordnen ist:** Bei rund 600 Varianten bestehen einige Stufe 1 rein
zufällig. Entscheidend ist Stufe 2 mit sechs unabhängigen Gegenproben. Berichtet wird außerdem, wie die beste und
die mittlere Deckung von der Haltedauer abhängt. Gesamtzahl der Versuche: 60 Einzelhypothesen plus dieser Massentest.

---

# Runde 11: Ergebnis (14.11.2026)

602 Regel-Varianten (43 Einstiege × 7 Ausstiege × 2 Bias-Längen), Stundenkerzen, 49 Coins.

- **Stufe 1** (Entwicklung Gruppe A, Deckung ≥ 1,0 in beiden Hälften, je ≥ 200 Trades): **9 Varianten.** Bei 580
  Varianten mit genug Trades ist das die Größenordnung, die der Zufall erwarten lässt.
- **Stufe 2** (Prüfzeitraum Gruppe A, Gruppe B und C je Entwicklung und Prüfzeitraum): **0 Varianten.**
  Die beste aus Stufe 1 (`b14_volumen_mit_z3.0_halte24`) fällt im Prüfzeitraum auf Deckung 0,69, in Gruppe C auf 0,19.

Deckung nach Haltedauer (Median über alle Regeln, Gruppe A): 1 Stunde −0,31 · 2 Stunden −0,25 · 4 Stunden −0,08 ·
8 Stunden +0,09 · 24 Stunden +0,46 in der Entwicklung; im Prüfzeitraum durchweg negativ (−0,28 bis −0,53).
Gewinnziel mit Stop: −0,53 (1 ATR) und −0,50 (2 ATR).
Selbst die optimistische Maker-Rechnung (halbe Gebühr, keine Slippage, jede Order gefüllt) kommt im Prüfzeitraum im
Median nur auf 0,16 bei 24 Stunden Haltedauer und liegt bei kürzeren Haltedauern um null.

**Runde 11: keine Regel gefunden, deren Trades ihre Gebühr verlässlich verdienen.** Der Befund ist kein Zufall der
Regelauswahl, sondern Rechnung: Die Gebühr je Trade ist fest (0,16 % hin und zurück), der erzielbare Vorteil wächst
mit der Haltedauer. Gebühr plus Slippage betragen im Mittel 0,22 % je Trade, die typische Stundenbewegung eines Coins
0,38 % (`diagnose_huerde.json`). Ein Stunden-Trade müsste im Schnitt mehr als die Hälfte davon richtig erwischen.

---

# Runde 12: Statistical Arbitrage (Paare, Z-Score) und Fusion mit dem Swing (festgelegt vor dem ersten Ergebnis)

**Auftrag des Users:** unabhängig von Yubit ein Stat-Arb-System bauen, das Korrelationen zwischen Coins modelliert,
über einen Z-Score long/short geht, und es mit der Swing-Strategie verbinden.

**Das Stat-Arb-System (Stundenkerzen, Binance-Futures):**
- Für jedes Coin-Paar laufend über ein Fenster W: Korrelation der Stundenrenditen, Hedge-Verhältnis β (Regression
  der logarithmierten Kurse), daraus der Spread und sein Z-Score (Abweichung vom Fenster-Mittel in Standardabweichungen).
- Einstieg: Korrelation ≥ 0,7, β zwischen 0,5 und 2, |Z| ≥ z_ein. Teurer Coin short, billiger long, nach β gewichtet.
  β bleibt bis zum Ausstieg fest. Ausführung zum Open der Folgekerze.
- Ausstieg: |Z| ≤ 0,5 oder Vorzeichenwechsel (Ziel erreicht), |Z| ≥ 4 (Stop, Paar danach W/4 gesperrt),
  oder nach W/2 Stunden (Zeitlimit).
- Höchstens 10 Paare gleichzeitig, jeder Coin in höchstens 3 Paaren, stärkste Signale zuerst.
  Einsatz: Long- und Short-Seite zusammen höchstens 100 % des Topfes.
- Kosten wie im Labor des Users: 0,05 % Gebühr + 0,05 % Slippage je Order. Echtes Funding für beide Seiten.

**Raster (9 Einstellungen):** W = 7 / 14 / 30 Tage, z_ein = 1,5 / 2,0 / 2,5.

**Hürden für das Stat-Arb-System allein:**
1. Entwicklung Gruppe A: vor Kosten und netto positiv in D1 und D2. Ein Finalist: bester schlechterer Halbzeit-Sharpe.
2. Doppelte Kosten: netto positiv in D1 und D2.
3. Bestätigung: Prüfzeitraum Gruppe A netto positiv; Gruppe B und C jeweils netto positiv in Entwicklung und Prüfzeitraum.

**Fusion mit dem Swing (beide Labor-Strategien getrennt: trail_beide 4H und momentum_vol_ls 1D, je Hebel 1,
gleiche Kosten):**
- F1 „zwei Töpfe“: je 50 % Swing und Stat-Arb.
- F2 „Swing als Filter“: Stat-Arb nimmt ein Paar nur, wenn keine der beiden Seiten gegen die Swing-Richtung des
  jeweiligen Coins läuft; dazu wieder 50 % Swing.
**Fusion ist besser**, wenn sie gegenüber dem Swing allein in Entwicklung **und** Prüfzeitraum einen höheren Sharpe
und einen kleineren Einbruch hat. Berichtet wird in jedem Fall alles, auch wenn das Stat-Arb-System allein durchfällt.

Vorwissen, offen benannt: Gegenbewegungs-Regeln (Runde 1) und die marktneutrale Rangfolge (Runde 6) sind
durchgefallen. Paar-Handel über Kointegration ist verwandt, aber nicht dasselbe. Gesamtzahl der Versuche danach:
69 Einzelhypothesen plus Massentest.

---

# Runde 12: Ergebnis (14.11.2026)

**Stat-Arb allein:** Keine der 9 Einstellungen ist in beiden Entwicklungshälften netto positiv (Stufe 1 nicht
bestanden). Vor Kosten ist der Effekt auf Gruppe A vorhanden (30 Tage / Z 2,0: +28,3 % in der Entwicklung, +4,8 % im
Prüfzeitraum), nach Labor-Kosten −2,8 % und −11,5 %. Gruppe B ist schon vor Kosten negativ, Gruppe C vor Kosten
positiv und netto +9,0 % / −7,7 %. Ein Paar-Trade verdient im Mittel 0,13 % seines Einsatzes und kostet 0,20 %.

**Fusion:** Die Tagesgewinne von Swing und Stat-Arb korrelieren mit −0,14. Der Einbruch sinkt in allen vier
Kombinationen deutlich, der Sharpe ist in der Entwicklung in drei von vier Fällen höher, im Prüfzeitraum in allen
vier Fällen niedriger als beim Swing allein. **Nach der vorab festgelegten Regel ist keine Fusion besser.**
Details in `statarb_bericht.md`.

---

# Nachrechnung zu Runde 12: Fusion mit Yubit-Kosten und 85 % Rebate (14.11.2026)

Auf Wunsch des Users, nach Kenntnis der Ergebnisse mit Labor-Kosten, also **keine** vorab festgelegte Prüfung.
Gleiche Stat-Arb-Einstellung (30 Tage, Z 2,0), Kosten je Order 0,012 % plus 2 × gemessene halbe Yubit-Spanne.
Zahlen in `fusion_yubit.json`.

- trail_beide: „Swing als Filter“ erfüllt die Regel aus Runde 12 formal (Sharpe Entwicklung 1,27 gegen 1,13,
  Prüfzeitraum 0,46 gegen 0,43; Einbruch 9 % gegen 16 % und 13 % gegen 20 %). Der Vorsprung im Prüfzeitraum ist
  minimal, der Ertrag pro Jahr niedriger (4,9 % gegen 8,3 %). „Zwei Töpfe“ erfüllt sie nicht.
- momentum_vol_ls: keine der beiden Fusionen erfüllt sie (Sharpe im Prüfzeitraum 0,48 und 0,50 gegen 0,53).
- Stat-Arb allein bleibt im Prüfzeitraum negativ (−1,1 % pro Jahr).

Wertung: kein belastbarer Vorteil. Ein formaler Treffer aus vier Kombinationen, nachträglich gerechnet und mit
einem Vorsprung, der im Rauschen liegt.

---

# Runde 13: Niedrig-Risiko-Baustein auf breiter Coin-Auswahl (festgelegt vor dem ersten Ergebnis)

**Anlass (Frage des Users):** Der Sharpe fällt nach März 2025 von 1,27 auf 0,46. Ein zweiter Ertragsbringer, der
nicht vom Trend abhängt, könnte schwache Trend-Phasen glätten. Der Prüfzeitraum wird dafür nicht nachjustiert:
eine Idee, eine Einstellung, eine Rechnung.

**Idee:** In vielen Märkten sind riskante Titel dauerhaft zu teuer, weil Händler ohne viel Kapital lieber stark
schwankende Titel kaufen als Hebel zu nehmen. Ruhige Titel bringen deshalb je Risiko mehr („Betting against Beta“).
Diese Quelle kam in der Suche bisher nicht vor und hängt nicht von der Marktrichtung ab.

**Eine Hypothese, eine Einstellung, kein Raster:**
- Beta jedes Coins: Stundenrenditen der letzten 60 Tage (1.440 Stunden, volle Historie nötig) gegen den
  gleichgewichteten Korb aller Coins der jeweiligen Auswahl.
- Einmal pro Woche (alle 168 Stunden, Raster ab 00:00 UTC): die 30 % mit dem niedrigsten Beta long, die 30 % mit
  dem höchsten Beta short. Dazwischen wird gehalten.
- Beide Seiten werden so gewichtet, dass ihr Beta sich aufhebt (Gewicht ∝ 1 / mittleres Beta der Seite, Summe der
  beiden Gewichte 2, je Seite auf 0,5 bis 1,5 begrenzt). Marktneutral nach Beta, nicht nach Betrag.
- Signal erst nach Stundenschluss wirksam. Kosten wie in Runde 6 (2 × gemessene halbe Yubit-Spanne je Coin, Taker
  mit 85 % Rebate), echtes Funding.

**Breite (Punkt 2):** Entwickelt wird auf A+B (20 Coins), weil 30 % von 10 Coins zu wenige sind. Bestätigt wird
auf C (19 Coins) und D (10 Coins), die für diese Idee frisch sind.

**Hürden (wie Runde 7, auf die breitere Auswahl übertragen):**
1. Entwicklung A+B: G > 0 und N > 0 in D1 und D2.
2. Doppelte Kosten: N > 0 in D1 und D2.
3. Bestätigung: Prüfzeitraum A+B mit G > 0 und N > 0; Gruppe C und Gruppe D jeweils N > 0 in Entwicklung und
   Prüfzeitraum.
4. Zufallstest (A+B, ganzer Zeitraum): besser als 90 % von 200 zeitlich verschobenen Signalen.
5. Hebel: Einbruch in der Entwicklung ≤ 10 % mit Tageslimit, im Prüfzeitraum < 15 %, dort G > 0 und N > 0.
6. **Antwort auf die Frage:** Mischung je zur Hälfte mit dem Kandidaten (14-Tage-Trend) auf A+B, beim Hebel mit
   Einbruch ≤ 10 % in der Entwicklung. „Besser“ nur, wenn die Mischung in Entwicklung **und** Prüfzeitraum mehr
   Netto mit Rebate **und** einen höheren Sharpe hat als der Kandidat allein.

Wer an einer Hürde scheitert, scheidet aus; die späteren Stufen werden dann nicht gerechnet. Der Prüfzeitraum wird
erst in Stufe 3 angesehen. Unabhängig vom Ausgang wird alles berichtet.

Vorwissen, offen benannt: Der Prüfzeitraum ist für Trend und Paar-Handel bekannt, für diese Idee nicht. Ich weiß,
dass Coins im Prüfzeitraum überwiegend gefallen sind; die Beta-Neutralität soll verhindern, dass der Baustein nur
davon lebt. Gesamtzahl der Versuche danach: 70 Einzelhypothesen plus Massentest.

# Runde 13: Ergebnis (14.11.2026)

Zahlen in `suche_runde13.json`.

- **Stufe 1 durchgefallen.** Entwicklung A+B, vor Gebühren: D1 +10,3 %, D2 −8,2 %, zusammen +2,1 % in gut
  dreieinhalb Jahren bei einem Einbruch von 51 %. Netto mit Rebate: D1 +10,2 %, D2 −8,3 %.
- Die späteren Stufen wurden nicht gerechnet. **Der Prüfzeitraum und die Gruppen C und D wurden nicht angesehen.**
- Gegenrechnung ohne Rechenkern (Gewichte stündlich auf den Sollwert zurückgesetzt, ohne Kosten und Funding):
  D1 −0,2 %, D2 +12,1 %, Sharpe −0,01 und 0,55. Auch so besteht eine Hälfte nicht. Die beiden Rechnungen
  unterscheiden sich, weil der Rechenkern die Stückzahl bis zur nächsten Gewichtsänderung hält und die Positionen
  dazwischen auseinanderlaufen. In keiner der beiden Bauarten ist der Baustein in beiden Hälften positiv.
- Der Baustein hält fast durchgehend BTC, BNB und TRX long und NEAR, AAVE, AVAX short. Das ist eher eine Dauerwette
  auf wenige Coins als eine breit gestreute Quelle.

**Runde 13: kein zweiter Ertragsbringer.** Keine Nachbesserung der Einstellung. Stand: 70 Einzelhypothesen plus
Massentest, weiterhin nur der Trend.

---

# Runde 14: Derselbe Trend auf Nicht-Krypto-Märkten bei Yubit (festgelegt vor dem ersten Ergebnis, noch nicht gerechnet)

**Begründung:** Trendfolge wird in der Praxis vor allem durch Märkte stärker, die nicht gemeinsam laufen. Die zehn
Coins laufen fast als ein Markt. Yubit führt aber auch Kontrakte auf Aktien-Indizes, Metalle und Energie.

**Keine neue Regel, keine neue Einstellung:** der Kandidat unverändert (Schlusskurs gegen den vor 14 Tagen, long
oder short, jeder Markt gleich groß), auf Tageskursen.

**Märkte (festgelegt, bevor ein Kurs geladen ist):** SPY, QQQ, IWM, EWJ, EWY, Gold, Silber, Platin, Palladium,
Kupfer, WTI-Öl, Brent-Öl, Erdgas, TBT. Keine Einzelaktien, keine gehebelten oder Branchen-ETFs.

**Kosten:** Taker 0,08 % mit 85 % Rebate plus 2 × halbe Yubit-Spanne je Kontrakt (wird vor der Rechnung gemessen).
Funding: aktueller Yubit-Satz je Kontrakt als Dauerwert, weil es keine Historie gibt.

**Hürden:**
1. Nicht-Krypto-Trend allein: N > 0 in D1, D2 und im Prüfzeitraum.
2. Doppelte Kosten: N > 0 in Entwicklung und Prüfzeitraum.
3. Mischung je zur Hälfte mit dem Kandidaten auf Gruppe A, gleicher Gesamteinsatz: mehr Netto mit Rebate **und**
   höherer Sharpe als der Kandidat allein, in Entwicklung **und** Prüfzeitraum.

Einschränkung, vorab benannt: Die Kurse wären die der Basiswerte (Börsentage), gehandelt würden Yubit-Kontrakte, die
erst seit 2026 existieren. Abweichungen zwischen beiden sind ungeprüft.

**Stand 14.11.2026:** Nicht gerechnet. Für diese Märkte fehlen Kurse vor 2026 (Binance-Historie nur wenige Monate).
Der Abruf bei stooq.com scheiterte technisch, der Abruf bei Yahoo Finance wurde von der Sicherheitsprüfung der
Umgebung nicht zugelassen.

**Nachtrag zu Runde 14, vor dem ersten Ergebnis (14.11.2026):**
- Tageskurse von Yahoo Finance geladen (User hat den Abruf ausdrücklich angewiesen): 14 Märkte, 2020 bis 10/2026.
  Rohstoffe sind die jeweils nächstfälligen Futures ohne Bereinigung der Kontraktwechsel.
- Yubit-Spannen gemessen (`runde14_kosten.json`), an einem Samstag. Slippage je Order = gemessene Spanne
  (2 × halbe Spanne), mindestens 0,005 %, wie in Runde 6.
- **Funding:** Der Momentanwert ist unbrauchbar (Wochenende: meist 0, Silber −0,15 % je 4 Stunden). Die
  Festlegung „aktueller Satz als Dauerwert“ wird deshalb ersetzt, bevor ein Ergebnis vorliegt: Hauptrechnung mit
  Funding 0; zusätzlich Pflicht-Stress, in dem **jede** Position 10 % pro Jahr Funding zahlt. Hürde 2 (doppelte
  Kosten) gilt mit diesem Stress zusammen.
- Ausführung: Signal nach Tagesschluss, Handel zur Eröffnung des nächsten Börsentags plus Slippage. Größe wird beim
  Einstieg festgelegt und bis zum Richtungswechsel gehalten (wie beim Kandidaten). „Vor 14 Tagen“ = letzter
  Schlusskurs, der mindestens 14 Kalendertage alt ist.
- Zeitraum und Teilung wie bisher (ab 15.08.2021, D1 bis 30.06.2023, D2 bis 31.03.2025, danach Prüfzeitraum).

# Runde 14: Ergebnis (14.11.2026)

Zahlen in `suche_runde14.json`.

- **Hürde 1 durchgefallen.** Der 14-Tage-Trend verliert auf den 14 Märkten: Entwicklung −66,4 % (D1 −27,9 %,
  D2 −38,5 %), Prüfzeitraum −2,9 %, schon vor Gebühren negativ (−63,2 % und −1,5 %). 11 von 14 Märkten sind in der
  Entwicklung negativ.
- Hürde 2 (Stress) und Hürde 3 (Mischung) ebenfalls verfehlt. Mischung: Sharpe 0,62 und 0,28 gegen 0,95 und 0,34
  des Kandidaten allein (Gruppe A, Einsatz 100 %, ohne Tageslimit).
- Kontrolle der Rechnung: Eine unabhängige Vektor-Rechnung (Schluss zu Schluss) liefert für Gold, SPY und Öl
  dieselben Größenordnungen. Kein Rechenfehler; auf diesen Märkten kehren 14-Tage-Bewegungen eher um.
- **Vorwissen aus dieser Kontrolle, offen benannt:** Dabei habe ich für Gold, SPY und Öl auch längere Rückblicke
  über den ganzen Zeitraum gesehen (60/200 Börsentage, 90/280 Kalendertage). Gold war damit deutlich positiv, SPY
  positiv, Öl um null bis negativ. Der Prüfzeitraum ist für längere Rückblicke auf diesen drei Märkten damit nicht
  mehr unberührt.

**Runde 14: keine Verbesserung.** Der Krypto-Trend lässt sich nicht einfach auf andere Märkte übertragen.

---

# Runde 15: 12-Monats-Trend auf denselben 14 Märkten (festgelegt vor dem ersten Ergebnis)

**Begründung:** Für Aktien-Indizes, Metalle und Energie ist nicht der 14-Tage-, sondern der 12-Monats-Trend der
seit Jahrzehnten belegte Standard (Moskowitz, Ooi, Pedersen 2012: „Time Series Momentum“). Die Einstellung kommt
aus dieser Literatur und nicht aus einem Raster.

**Eine Einstellung:** Schluss gegen den Schluss vor 365 Kalendertagen, sonst alles wie in Runde 14 (Märkte, Kosten,
Ausführung, Stress, Zeiträume). Die Kurse reichen bis 01/2020 zurück, das erste Signal liegt also vor dem Start.

**Hürden:** dieselben drei wie in Runde 14.

**Einschränkung, vorab:** siehe Vorwissen oben. Ein Bestehen wäre deshalb nur ein Hinweis; als Beleg zählt es erst
nach einem Vorwärtstest. Gesamtzahl der Versuche danach: 72 Einzelhypothesen plus Massentest.

# Runde 15: Ergebnis (14.11.2026)

Zahlen in `suche_runde15.json`. Korrektur vor der Wertung: Die Tagesrechnung schnitt die Kurse 60 Tage vor dem
Start ab, das 12-Monats-Signal begann dadurch erst Mitte 2022. Behoben (Vorlauf = Rückblick + 46 Tage), wie im
Protokoll vorgesehen; Runde 14 ist davon nicht betroffen.

- **Hürde 1 durchgefallen.** 12-Monats-Trend allein, netto mit Rebate: D1 −7,2 %, D2 +1,9 %, Entwicklung −5,3 %,
  Prüfzeitraum +18,7 % (Sharpe 0,34). Über alles +13,3 % in gut fünf Jahren bei 29 % Einbruch.
- **Hürde 2 durchgefallen.** Mit doppelten Kosten und 10 % Funding pro Jahr in beiden Zeiträumen negativ.
- **Hürde 3 durchgefallen.** Mischung je zur Hälfte: Sharpe 0,90 gegen 0,95 in der Entwicklung, 0,47 gegen 0,34
  im Prüfzeitraum; Netto in beiden Zeiträumen niedriger. Der Einbruch sinkt (19 % gegen 25 %, 22 % gegen 31 %).
- Die Tagesergebnisse beider Bausteine hängen nicht zusammen (Korrelation 0,01). Die Streuung wirkt also, aber der
  zweite Baustein verdient im Entwicklungszeitraum nichts.

**Runde 15: keine Verbesserung nach den festgelegten Regeln.** Stand: 72 Einzelhypothesen plus Massentest.

---

# Runde 16: Zwei Ideen aus den neuen Aktien-Daten (festgelegt vor dem ersten Ergebnis)

Auf Wunsch des Users weitere Ideen. Beide nutzen Information, die in der Suche bisher fehlte (US-Aktienmarkt), und
haben je genau eine Einstellung.

**H1 „Übernacht-Effekt“.** Seit Jahrzehnten belegt: US-Aktienindizes verdienen ihre Rendite fast ganz zwischen
Börsenschluss und nächster Eröffnung, tagsüber fast nichts. Yubit-Kontrakte auf SPY, QQQ und IWM handeln rund um
die Uhr. Regel: zum US-Börsenschluss long, zur nächsten US-Eröffnung glatt, jeden Börsentag, drei Märkte gleich groß,
Einsatz 100 %. Nur diese drei: EWJ und EWY bilden Märkte ab, die in der US-Nacht selbst handeln.
- Rechnung: Eröffnung gegen Vortagesschluss (Yahoo, nicht dividendenbereinigt, das ist für Long vorsichtig).
  Je Tag zwei Orders: Slippage wie Runde 14, Taker 0,08 % mit 85 % Rebate.
- Hürden: (1) N > 0 in D1, D2 und Prüfzeitraum. (2) Stress: doppelte Slippage und 10 % Funding pro Jahr auf die
  gehaltene Zeit, N > 0 in Entwicklung und Prüfzeitraum. (3) Mischung je zur Hälfte mit dem Kandidaten: höherer
  Sharpe in Entwicklung und Prüfzeitraum.
- Zusätzlich berichtet: Ergebnis ohne Rebate.

**H2 „Risiko-Filter“.** Krypto läuft seit Jahren mit Technologie-Aktien. Regel: der Kandidat unverändert, aber eine
Position nur, wenn der 14-Tage-Trend von QQQ in dieselbe Richtung zeigt; sonst glatt. QQQ-Signal nach US-Schluss,
gültig ab dem nächsten UTC-Tag. Kein neuer Parameter (dieselben 14 Tage).
- Hürden: (1) N > 0 und höherer Sharpe als der Kandidat in D1, D2 und Prüfzeitraum (Gruppe A, Yubit-Kosten,
  Einsatz 100 %, ohne Tageslimit). (2) Zufallstest: Sharpe über den ganzen Zeitraum besser als 90 % von 200 Läufen
  mit zeitlich verschobenem QQQ-Signal. (3) Gruppe B: höherer Sharpe als der Kandidat in Entwicklung und Prüfzeitraum.

**Änderung an Hürde 3 gegenüber Runde 13–15, offen benannt:** Verlangt wird nur noch der höhere Sharpe, nicht mehr
zusätzlich mehr Netto bei gleichem Einsatz. Grund: Der Einsatz lässt sich frei wählen, der Sharpe ist das Maß, um
das es dem User geht. Die Runden 13 bis 15 hätten auch so nicht bestanden (alle an Hürde 1 gescheitert).

Vorwissen: Der Übernacht-Effekt ist aus der Literatur bekannt, ebenso, dass er nach Kosten knapp ist. Für H2 kenne
ich den Krypto-Prüfzeitraum (schwach für Trend). Einschränkungen wie in Runde 14 (Kurse der Basiswerte, Spannen an
einem Samstag gemessen, Funding unbekannt). Gesamtzahl der Versuche danach: 74 Einzelhypothesen plus Massentest.

# Runde 16: Ergebnis (14.11.2026)

Zahlen in `suche_runde16.json`.

**H1 Übernacht-Effekt: durchgefallen (alle drei Hürden).**
- Vor Kosten ist der Effekt da: Entwicklung +22,2 %, Prüfzeitraum +19,4 % (Sharpe 0,53 und 0,99), allerdings
  D1 −9,9 % (Bärenmarkt 2022).
- Zwei Orders an jedem Börsentag kosten mehr, als der Effekt bringt: netto mit Rebate −28,2 % und −2,5 %, ohne
  Rebate −152 % und −56 %. Im Stress überall negativ.
- Mischung mit dem Kandidaten: Sharpe 0,81 gegen 0,95 und 0,29 gegen 0,34.

**H2 Risiko-Filter: durchgefallen (Hürde 1).** Sharpe mit Filter 0,78 / 0,89 / −0,32 (D1 / D2 / Prüfzeitraum) gegen
0,56 / 1,32 / 0,34 ohne. Im Prüfzeitraum macht der Filter aus +25,8 % ein Minus von 22,4 %. Zufallstest und
Gruppe B wurden deshalb nicht gerechnet.

**Runde 16: keine Verbesserung.** Stand: 74 Einzelhypothesen plus Massentest, weiterhin nur der Krypto-Trend.

---

# Runde 17: Zwei marktneutrale Ideen auf Nicht-Krypto-Kontrakten (festgelegt vor dem ersten Ergebnis)

**H1 „Verwandte Paare“.** Der Paar-Handel aus Runde 12 scheiterte an Coins, die nur lose zusammenhängen. Bei eng
verwandten klassischen Märkten ist der Zusammenhang wirtschaftlich begründet. Paare (vorab fest): Gold/Silber,
Platin/Palladium, SPY/QQQ, SPY/IWM. Öl (WTI/Brent) bleibt draußen, weil die unbereinigten Kontraktwechsel dort
Scheingewinne erzeugen würden.
- Einstellung wie Runde 12, nichts Neues: Z-Wert des Preisverhältnisses (Logarithmus) über 30 Tage, Einstieg ab
  |Z| ≥ 2,0 gegen die Abweichung (ein Markt long, der andere short, gleicher Betrag), Ausstieg bei |Z| ≤ 0,5,
  Notausstieg bei |Z| ≥ 4,0. Je Paar ein Viertel des Einsatzes. Signal nach Tagesschluss, Handel zur nächsten
  Eröffnung.

**H2 „Aktien-Momentum“.** Der am besten belegte Effekt bei Aktien (Jegadeesh/Titman 1993): Gewinner der letzten
12 Monate schlagen Verlierer. Yubit führt rund 150 Aktien-Kontrakte.
- Einstellung aus der Literatur: Rendite von vor 12 Monaten bis vor 1 Monat; am Monatsende die besten 30 % long,
  die schwächsten 30 % short, gleich gewichtet, Summe der Beträge = Einsatz 100 %; einen Monat halten. Signal am
  letzten Börsentag des Monats, Handel am nächsten Börsentag zum Schluss.
- Auswahl: alle Yubit-Kontrakte der Ausschlussliste aus Runde 10, die bei Binance erst ab 2026 gelistet sind und
  bei Yahoo unter demselben Kürzel als Aktie geführt werden; je Stichtag nur Titel mit mindestens 400 Tagen Kursen.
- **Bekannte Verzerrung:** Die Liste stammt von 2026 und enthält bevorzugt Titel, die bis dahin groß geworden sind.
  Long gegen Short innerhalb der Liste mildert das, hebt es aber nicht auf.

**Kosten für beide:** Taker 0,08 % mit 85 % Rebate, Slippage = gemessene Yubit-Spanne je Kontrakt (mindestens
0,005 %; ohne Messwert der Median der gemessenen). Funding 0 in der Hauptrechnung.

**Hürden je Idee (wie Runde 16):** (1) N > 0 in D1, D2 und Prüfzeitraum. (2) Stress: doppelte Slippage und 10 %
Funding pro Jahr auf alle gehaltenen Beträge, N > 0 in Entwicklung und Prüfzeitraum. (3) Mischung je zur Hälfte
mit dem Kandidaten: höherer Sharpe in Entwicklung und Prüfzeitraum.

Vorwissen: Aus Runde 14/15 kenne ich Trend-Ergebnisse je Markt für Gold, Silber, Platin, Palladium, SPY, QQQ, IWM,
nicht aber deren Verhältnisse. Einschränkungen wie in Runde 14. Gesamtzahl der Versuche danach: 76 plus Massentest.

# Runde 17: Ergebnis (14.11.2026)

Zahlen in `suche_runde17.json`. 134 Aktien geladen (ETFs, Rohstoffe und nicht auffindbare Kürzel ausgelassen),
für alle eine Yubit-Spanne gemessen (Median 0,055 %).

**H1 Verwandte Paare: durchgefallen (alle drei Hürden).** Netto mit Rebate: D1 +2,9 %, D2 +4,8 %, Prüfzeitraum
−3,0 %. Im Stress überall negativ. Mischung: Sharpe 0,98 gegen 0,95 in der Entwicklung, aber 0,29 gegen 0,34 im
Prüfzeitraum. Der Verlust im Prüfzeitraum kommt aus Gold/Silber (−3,6 %).

**H2 Aktien-Momentum: durchgefallen (alle drei Hürden), aber knapper als alles bisher.**
- Netto mit Rebate: D1 −5,5 %, D2 +10,8 %, Prüfzeitraum +33,5 % (Sharpe 1,00). Hürde 1 scheitert an D1.
- Stress: Entwicklung −32,8 %, Prüfzeitraum +16,5 %. Der Baustein hält dauerhaft 100 % Einsatz, 10 % Funding pro
  Jahr fressen den Ertrag der Entwicklung auf.
- Mischung: Sharpe 0,93 gegen 0,95 in der Entwicklung (knapp darunter), 0,72 gegen 0,34 im Prüfzeitraum.
  Einbruch 18 % und 16 % gegen 25 % und 31 %. Korrelation der Tagesergebnisse 0,01.
- **Warum das kein Treffer ist:** Die Aktienliste stammt von 2026. Sie enthält Titel, die gerade wegen ihres Laufs
  2025/26 aufgenommen wurden. Das begünstigt genau den Prüfzeitraum. Das gute Ergebnis dort ist deshalb verzerrt,
  und in der Entwicklung verdient der Baustein kaum etwas (+5,3 % in dreieinhalb Jahren).

**Runde 17: keine Verbesserung nach den festgelegten Regeln.** Stand: 76 Einzelhypothesen plus Massentest.

---

# Runde 18: Fremde Signale „Short nach Pump“ (Plimaflow) nachrechnen (festgelegt vor dem ersten Ergebnis)

**Anlass:** Der User hat Zugriff auf einen Signal-Dienst und will wissen, ob in den Signalen ein Vorteil steckt.
Abgerufen über die Lese-Schnittstelle: 254.696 Scanner-Einträge, 17.08.–15.11.2026, 503 Coins. Die Einträge
enthalten nur „größter Rückgang danach“ und „−5 % / −10 % erreicht“, keinen Stop. Deshalb eigene Rechnung auf
Minutenkursen.

**Vorwissen, offen benannt:** Die Statistik des Anbieters kenne ich (617 echte Trades, 51,5 % Treffer, Rendite 0,
4 von 10 Monaten im Plus; −10 % erreicht bei 32 % aller und 42 % der qualifizierten Signale). Von den Signalen
selbst kenne ich Anzahl und Coins, keine Kursverläufe.

**Regel (eine Einstellung, aus der Beschreibung des Dienstes):**
- Signal: Eintrag mit Score (p_win) ≥ 0,60, die Schwelle des Live-Streams. Das sind 1.758 Einträge auf 54 Coins.
- Je Coin höchstens eine Position. Einstieg short zur Eröffnung der ersten Minutenkerze nach dem Signal. Der Dienst
  nennt „Limit am Sweep-Hoch“; das ist nicht nachbildbar, weil die Definition fehlt.
- Ziel 10 % unter dem Einstieg (Limit), Stop 8 % über dem Einstieg (Market). Liegen beide in derselben Minute, zählt
  der Stop. Eröffnet eine Kerze jenseits des Stops, gilt deren Eröffnung. Spätestens nach 72 Stunden glatt (Market).
  Nach dem Ausstieg ist der Coin für neue Signale wieder frei.
- Kurse: Binance-USD-M-Futures, Minutenkerzen. Coins ohne Binance-Kontrakt fallen weg und werden gezählt.
- Kosten: Einstieg, Stop und Zeitausstieg Taker 0,08 % plus Slippage (2 × halbe Yubit-Spanne des Coins, mindestens
  0,005 %; ohne Yubit-Wert der Median der Signal-Coins mit Wert); Ziel Maker 0,04 % ohne Slippage. Rebate 85 %.
  Funding: echte Binance-Sätze, soweit im Archiv (bis 10/2026), danach der Satz aus dem Signal alle 8 Stunden.
- Größe: jeder Trade 10 % des Kontos. Berichtet wird das Ergebnis je Trade und die Summe.

**Hürden:**
1. Netto mit Rebate > 0 in beiden Hälften des Zeitraums (Teilung am 01.10.2026) und mindestens 100 Trades.
2. Doppelte Slippage: netto > 0 über den ganzen Zeitraum.
3. Zufallstest: Mittelwert je Trade > 0 in mindestens 95 % von 2.000 Ziehungen, gezogen werden ganze Kalendertage
   (Trades eines Tages hängen zusammen).
4. Kein Coin trägt mehr als 50 % des Gewinns.

Zusätzlich berichtet, ohne Hürde: nur Coins, die bei Yubit gelistet sind; Ergebnis ohne Rebate; Anteil Ziel / Stop
/ Zeit. Einschränkung: 90 Tage sind kurz, und die Kurse sind von Binance, nicht von der Börse des Dienstes.
Gesamtzahl der Versuche danach: 77 plus Massentest.

# Runde 18: Ergebnis (15.11.2026)

Zahlen in `suche_runde18.json`, alle Trades in `suche_runde18_trades.csv`. 51 von 54 Coins mit Binance-Kursen
(ohne HNT, CNPY, BEAM). Die 24-Stunden-Veränderung laut Dienst passt zu Binance (Korrelation 0,95).

- **173 Trades in 90 Tagen**, im Median 1,7 Stunden gehalten, höchstens 3 gleichzeitig. Ziel erreicht 51,4 %,
  Stop 46,8 %, Zeitausstieg 1,7 %.
- Je Trade: vor Kosten +1,40 %, Funding −0,31 %, Kosten 0,17 %, **netto mit Rebate +0,92 %** (ohne Rebate +0,80 %).
  Bei 10 % Einsatz je Trade: Konto +15,9 % in 90 Tagen, größter Einbruch 4,0 %.
- Hürde 1 bestanden (Hälften +12,8 % und +3,0 %, 173 Trades). Hürde 2 bestanden (doppelte Slippage +13,3 %).
  Hürde 4 bestanden (größter Coin 26 % des Gewinns).
- **Hürde 3 nicht bestanden:** In 92,9 % der Ziehungen ganzer Tage ist der Mittelwert positiv, verlangt waren 95 %.
- Nach Monaten fällt der Ertrag je Trade: +1,4 %, +1,8 %, +0,4 %, +0,1 % (August bis November).
- Nur Yubit-Coins (85 Trades): erste Hälfte +13,7 %, zweite Hälfte −4,1 %.

**Offene Punkte, die das Ergebnis entwerten können:**
- Die Historie trägt für alle Einträge die Modell-Version „v4.5“, der Live-Scanner zeigt „v5.7“ mit anderen Scores
  für denselben Coin. Ob der Score in der Historie zum damaligen Zeitpunkt vergeben oder später nachgerechnet wurde,
  ist nicht prüfbar. Ein nachgerechneter Score wäre ein Blick in die Zukunft.
- Eigene Statistik des Dienstes für echten Handel: Rendite 0, 4 von 10 Monaten im Plus.
- 90 Tage, 64 Handelstage. Der Einstieg weicht von der Regel des Dienstes ab (sofort statt Limit am Hoch).

**Runde 18: nach den festgelegten Regeln nicht bestanden (3 von 4 Hürden), aber der bisher stärkste Hinweis.**
Kein Nachjustieren. Sinnvoll sind: der lange Export des Users als frische Daten und das Mitschreiben des
Live-Streams ab jetzt.

---

# Runde 19: „Short nach Pump“ auf unseren zehn Coins, im Maßstab angepasst (festgelegt vor dem ersten Ergebnis)

**Auftrag des Users:** Die Idee des Signal-Dienstes auf die großen Coins übertragen. 20 % in 24 Stunden kommen dort
kaum vor; die Schwelle soll dem entsprechen, was bei großen Coins als großer Anstieg gilt (Vorschlag des Users: 5 %).

**Übertragung:** Der Dienst nimmt 20 % Anstieg, 10 % Ziel, 8 % Stop. Ziel und Stop sind also das 0,5- und
0,4-Fache der Schwelle. Dieses Verhältnis bleibt fest. Variiert wird nur die Schwelle:

| Name | Schwelle für den 24-Stunden-Anstieg | Ziel / Stop |
|---|---|---|
| fest5 | 5 % (Vorschlag des Users) | 2,5 % / 2,0 % |
| sigma2 | 2,0 × übliche Tagesschwankung des Coins | 0,5 × / 0,4 × Schwelle |
| sigma25 | 2,5 × übliche Tagesschwankung | wie oben |
| sigma3 | 3,0 × übliche Tagesschwankung | wie oben |

Übliche Tagesschwankung = Standardabweichung der Tagesrenditen der letzten 90 abgeschlossenen UTC-Tage.

**Feste Bauteile (wie Runde 18):** Signal, sobald der Schlusskurs einer 5-Minuten-Kerze mindestens um die Schwelle
über dem von vor 24 Stunden liegt; Short zur Eröffnung der nächsten Kerze; je Coin eine Position; Ziel als Limit,
Stop als Market; beide in einer Kerze = Stop; nach 72 Stunden glatt; danach wieder frei. Gruppe A, 5-Minuten-Kerzen
von Binance, echtes Funding. Kosten: Taker 0,08 % / Maker 0,04 % mit 85 % Rebate, Slippage = 2 × halbe
Yubit-Spanne. Je Trade 10 % des Kontos.

**Ablauf:**
1. Entwicklung (bis 31.03.2025), Gruppe A: netto mit Rebate > 0 in D1 und D2 und mindestens 100 Trades. Unter den
   Einstellungen, die das schaffen, kommt genau eine weiter: die mit dem besseren schlechteren Halbzeit-Ertrag je Trade.
2. Doppelte Slippage: netto > 0 in D1 und D2.
3. Bestätigung, je einmal: Prüfzeitraum Gruppe A vor Kosten > 0 und netto > 0; Gruppe B netto > 0 in Entwicklung und
   Prüfzeitraum.
4. Zufallstest über den ganzen Zeitraum: Mittelwert je Trade > 0 in mindestens 95 % von 2.000 Ziehungen ganzer Tage.
5. Zusammen mit dem Kandidaten (Trend): Tagesergebnisse auf gleiche Schwankung gebracht und je zur Hälfte gemischt;
   höherer Sharpe als der Kandidat allein in Entwicklung und Prüfzeitraum.

Vorwissen: Gegenbewegungs-Regeln auf Gruppe A sind in Runde 1 gescheitert (andere Bauart, ohne festes Ziel/Stop).
Der Kandidat ist ein Trendfolger; ein Short nach starkem Anstieg handelt gegen ihn. Aus Runde 18 kenne ich das
Ergebnis für kleine Coins. Gesamtzahl der Versuche danach: 81 plus Massentest.

# Runde 19: Ergebnis (15.11.2026)

Zahlen in `suche_runde19.json`. **Stufe 1: keine der vier Einstellungen besteht.** Prüfzeitraum und Gruppe B
wurden nicht angesehen.

| Einstellung | Trades (Entwicklung) | Ziel erreicht | Konto D1 | Konto D2 | vor Kosten je Trade |
|---|---|---|---|---|---|
| fest5 (5 %) | 16.064 | 44,8 % | −25,3 % | −43,5 % | +0,02 % |
| sigma2 (im Mittel 7,9 %) | 3.806 | 43,1 % | +19,8 % | −32,0 % | +0,04 % |
| sigma25 (9,7 %) | 2.043 | 42,1 % | +12,6 % | −21,5 % | +0,03 % |
| sigma3 (11,5 %) | 1.179 | 41,7 % | +8,8 % | −5,5 % | +0,10 % |

Bei Ziel 0,5 × und Stop 0,4 × Schwelle braucht es vor Kosten 44,4 % Treffer. Die großen Coins liegen mit 42–45 %
genau an dieser Grenze: Nach einem starken Anstieg fällt der Kurs dort nicht häufiger, als der Zufall erwarten
lässt. D1 (bis Mitte 2023) war bei den Sigma-Einstellungen positiv, D2 durchweg negativ.

**Runde 19: durchgefallen.** Der Effekt aus Runde 18 hängt an kleinen, dünn gehandelten Coins und überträgt sich
nicht auf die zehn großen. Stand: 81 Einzelhypothesen plus Massentest.

---

# Runde 20: Dasselbe mit nachgezogenem Stop statt festem Ziel (festgelegt vor dem ersten Ergebnis)

**Anlass:** Laut User schließt der Dienst nicht bei 10 %, sondern zieht ab 8 % Gewinn den Stop in 5-%-Schritten
nach. Regel, vom User bestätigt: Stop 8 % über dem Einstieg; bei 8 % Gewinn Stop auf 3 % gesicherten Gewinn; bei
13 %, 18 %, 23 % … jeweils 5 % weiter; kein festes Ziel.

**Teil A, Plimaflow-Signale:** alles wie Runde 18 (Score ≥ 0,60, Minutenkerzen, Kosten, 72 Stunden, vier Hürden),
nur der Ausstieg ist ersetzt. Ausstieg über den nachgezogenen Stop zählt als Market-Order (Taker plus Slippage).
**Teil B, Gruppe A:** alles wie Runde 19 (vier Schwellen, Ablauf in fünf Stufen), Ausstieg im selben Verhältnis
zur Schwelle: Stop 0,4 ×, Nachziehen ab 0,4 × Gewinn, Schritte 0,25 ×.

**Reihenfolge innerhalb einer Kerze (vorsichtig):** Zuerst wird der bisherige Stop geprüft. Danach werden neue
Stufen aus dem Tief der Kerze gesetzt. Schließt die Kerze über dem neuen Stop, gilt er als in dieser Kerze
ausgelöst.

**Einordnung, vorab:** Für Teil A ist das der zweite Blick auf dieselben 90 Tage, für Teil B der zweite auf die
Entwicklung von Gruppe A (Prüfzeitraum dort weiter unberührt). Ein Bestehen zählt deshalb weniger als in Runde 18/19.
Gesamtzahl der Versuche danach: 86 plus Massentest.

# Runde 20: Ergebnis (15.11.2026)

Zahlen in `suche_runde20a.json` (Plimaflow-Signale) und `suche_runde20b.json` (Gruppe A).

**Teil A, Plimaflow-Signale mit nachgezogenem Stop: alle vier Hürden verfehlt.**
- 185 Trades. Netto je Trade +0,14 % (festes Ziel: +0,92 %). Konto +2,5 % in 90 Tagen (festes Ziel: +15,9 %),
  ohne Rebate ±0, mit doppelter Slippage −1,2 %. Hälften +3,7 % und −1,1 %. Zufallstest 59 %.
- Monate schwanken stark: −0,2 %, +1,0 %, −0,9 %, +1,6 % je Trade.
- Grund: Viele Trades, die bei 10 % sauber geschlossen worden wären, laufen zurück und enden bei +3 % oder +8 %.
  Die wenigen großen Abstürze gleichen das in diesen 90 Tagen nicht aus.

**Teil B, Gruppe A mit nachgezogenem Stop: Stufe 1 von keiner Einstellung bestanden.** Alle vier sind in D1 und D2
netto negativ und, anders als mit festem Ziel, drei davon schon vor Kosten. Prüfzeitraum und Gruppe B nicht angesehen.

**Runde 20: durchgefallen.** In beiden Datensätzen ist das Nachziehen schlechter als das feste Ziel.
Stand: 86 Einzelhypothesen plus Massentest.

---

# Runde 21: Mutations-Batterie für den Kandidaten mit gemeinsamer Zufallsprüfung (festgelegt vor dem ersten Ergebnis)

**Auftrag des Users:** Zusätze und Abwandlungen der vorhandenen Strategie recherchieren und ausprobieren; melden,
sobald der vorhandene Vorteil ausgebaut ist, ohne dass es ein Zufallstreffer ist.

**Das Problem:** Nach 86 Versuchen findet sich unter vielen Varianten fast immer eine, die zufällig besser aussieht.
Deshalb werden alle Varianten dieser Runde **gemeinsam** geprüft: Die beste muss besser sein, als es die beste von
gleich vielen wirkungslosen Varianten zufällig wäre (White's Reality Check, 2000). Danach folgen frische Coins.

**Maßstab:** der Kandidat unverändert (Schluss gegen den vor 336 Stunden, long/short, stündlich, Gruppe A, sofortige
Ausführung, Yubit-Kosten mit Rebate, Einsatz 100 %, ohne Tageslimit).

**14 Varianten, je genau eine Einstellung** (aus Literatur und Praxis; Recherche: Man Group „In Crypto We Trend“,
Zarattini/Pagani/Barbon 2025, Han/Kang/Ryu, AdaptiveTrend 2026, Turtle-Regeln, Kaufman):

| # | Name | Änderung gegenüber dem Kandidaten |
|---|---|---|
| 1 | nur_long | Shorts entfallen |
| 2 | asym_70_30 | Longs × 1,4, Shorts × 0,6 |
| 3 | band | Richtung wechselt erst, wenn die 14-Tage-Rendite 0,5 übliche Schwankungen (90 Tage) jenseits von null liegt |
| 4 | ema_kreuz | Vorzeichen von EMA(84 h) − EMA(336 h) statt Punkt-zu-Punkt |
| 5 | donchian | long beim 336-h-Hoch, short beim 336-h-Tief; Ausstieg am 168-h-Gegenextrem |
| 6 | stetig | Größe = 14-Tage-Rendite / übliche Schwankung, begrenzt auf ±1, in Stufen von 0,25 |
| 7 | ohne_letzten_tag | Rendite von vor 336 h bis vor 24 h |
| 8 | breite | Position nur, wenn mindestens 7 von 10 Coins dieselbe Richtung haben |
| 9 | btc_regime | Longs nur, wenn BTC über seinem 200-Tage-Mittel liegt, Shorts nur darunter |
| 10 | effizienz | Position nur, wenn Kaufmans Effizienz (336 h) über ihrem Median der letzten 180 Tage liegt |
| 11 | volumen | Position nur, wenn der 14-Tage-Umsatz über dem 90-Tage-Umsatz liegt |
| 12 | funding_filter | keine Position, die im 3-Tage-Mittel mehr als 0,03 % je 8 Stunden Funding zahlt |
| 13 | markt_trend | alle Coins folgen dem 14-Tage-Trend des gleichgewichteten Korbs |
| 14 | relativ_staerke | stärkere Hälfte der Trends (|Rendite| / Schwankung) × 1,5, schwächere × 0,5 |

**Vergleichsgröße:** Tagesergebnis netto mit Rebate, jede Variante auf dieselbe Schwankung wie der Kandidat gebracht
(Faktor aus der Entwicklung). Damit zählt nur Ertrag je Risiko.

**Stufen:**
1. Entwicklung, Gruppe A: höherer Sharpe als der Kandidat in D1 **und** D2.
2. Gemeinsame Zufallsprüfung in der Entwicklung über **alle 14**: Stationärer Bootstrap (mittlere Blocklänge
   20 Tage, 5.000 Ziehungen) der Tagesdifferenzen zum Kandidaten. Eine Variante besteht, wenn ihr mittlerer
   Vorsprung über dem 95-%-Wert des jeweils größten Zufalls-Vorsprungs aller 14 liegt.
3. Bestätigung, je einmal: Prüfzeitraum Gruppe A, Gruppen B, C und D je über den ganzen Zeitraum, Vorperiode
   02/2020–08/2021 (Gruppe A). Überall höherer Sharpe als der Kandidat.

Nur eine Variante, die alle drei Stufen besteht, gilt als Ausbau des Vorteils. Berichtet wird alles.

**Vorwissen, offen benannt:** Ich kenne den Verlauf des Kandidaten in allen Zeiträumen und Gruppen (Prüfzeitraum
schwach, vermutlich Seitwärtsphasen). Die Liste ist davon gefärbt (mehrere Filter gegen Fehlsignale). Runde 5
(Größe nach Schwankung, Mischung von Rückblicken, Carry) und Runde 16 (QQQ-Filter) sind schon gescheitert und
deshalb nicht dabei. Gesamtzahl der Versuche danach: 100 plus Massentest.

# Runde 21: Ergebnis (15.11.2026)

Zahlen in `suche_runde21.json`. Kandidat in der Entwicklung: Sharpe 0,56 (D1), 1,32 (D2), 0,95 (gesamt).

- **Stufe 1:** 13 von 14 Varianten sind in mindestens einer Hälfte schlechter als der Kandidat. Nur der
  **Funding-Filter** ist in beiden besser (0,66 / 1,59 / 1,11).
- **Stufe 2 (gemeinsame Zufallsprüfung): keine Variante besteht.** Der Vorsprung des Funding-Filters entspricht
  +10 Prozentpunkten pro Jahr bei gleicher Schwankung; die beste von 14 wirkungslosen Varianten käme zufällig in
  84 % der Fälle mindestens so weit. Die Schwelle läge bei +44 Punkten.
- Stufe 3 wurde nicht gerechnet. Der Prüfzeitraum blieb für alle 14 unberührt.

**Was das bedeutet:** Mit dreieinhalb Jahren Entwicklung lässt sich ein realistischer Vorsprung (einige Zehntel
Sharpe) innerhalb derselben Daten nicht von Zufall trennen. Die Prüfung ist nicht zu streng, die Daten sind zu kurz.
Unterscheiden können das nur Daten, die bei der Auswahl keine Rolle gespielt haben.

**Runde 21: kein Ausbau.** Auffällig: Nur-Long, Bänder, Filter und andere Trend-Maße sind fast alle schlechter als
die einfache Regel. Stand: 100 Einzelhypothesen plus Massentest.

---

# Runde 22: Funding-Filter auf zeitlich unabhängigen Daten (festgelegt vor dem ersten Ergebnis)

**Begründung:** Der Funding-Filter ist die einzige Variante aus Runde 21, die in beiden Hälften besser war, und
er hat einen sachlichen Grund: Er vermeidet Positionen, die laufend hohe Finanzierungskosten zahlen. Innerhalb
der Entwicklung ist das nicht von Zufall zu trennen. Geprüft wird deshalb genau diese eine Variante, unverändert
(Grenze 0,03 % je 8 Stunden im 3-Tage-Mittel), auf Daten, die bei ihrer Auswahl keine Rolle spielten.

**Offen benannt:** Das weicht vom Ablauf der Runde 21 ab (dort wäre nach Stufe 2 Schluss). Es ist eine neue,
eigene Prüfung mit genau einer Hypothese. Gruppen B, C, D im Entwicklungszeitraum zählen **nicht** als unabhängig,
weil hohe Funding-Phasen alle Coins gleichzeitig treffen; sie werden nicht gewertet.

**Unabhängige Daten:** (a) Prüfzeitraum 04/2025–10/2026, alle 49 Coins (Gruppen A, B, C, D);
(b) Vorperiode 02/2020–08/2021, alle Coins mit Kursen.

**Rechnung:** je Gruppe Kandidat und Variante, Tagesergebnis netto mit Rebate, Variante auf die Schwankung des
Kandidaten gebracht (Faktor aus der Entwicklung der jeweiligen Gruppe); Gruppen nach Coin-Zahl gewichtet zu einem
Portfolio zusammengefasst.

**Hürden (alle nötig):**
1. Portfolio-Sharpe der Variante höher als der des Kandidaten im Prüfzeitraum **und** in der Vorperiode.
2. Im Prüfzeitraum in mindestens 3 der 4 Gruppen höherer Sharpe.
3. Zufallstest auf den zusammengelegten unabhängigen Tagen (Vorperiode + Prüfzeitraum): mittlerer Tagesvorsprung
   > 0 in mindestens 95 % von 5.000 Ziehungen (stationärer Bootstrap, Blöcke im Mittel 20 Tage).
4. Doppelte Kosten: Hürde 1 gilt auch dann.

Besteht die Variante, gilt sie als belegter kleiner Ausbau und geht in den Vorwärtstest. Gesamtzahl der Versuche
danach: 101 plus Massentest.

# Runde 22: Ergebnis (15.11.2026)

Zahlen in `suche_runde22.json`. **Nicht bestanden (Hürden 1, 3 und 4 verfehlt).**

| Unabhängige Daten | Sharpe Kandidat | Sharpe mit Funding-Filter |
|---|---|---|
| Prüfzeitraum 04/2025–10/2026, 49 Coins | 0,38 | 0,44 |
| Vorperiode 02/2020–08/2021, 44 Coins | 1,31 | 0,48 |

- Im Prüfzeitraum ist der Filter in allen vier Gruppen etwas besser (Hürde 2 bestanden).
- In der Vorperiode ist er in allen vier Gruppen deutlich schlechter: Im Bullenmarkt 2020/21 war das Funding
  gerade in den stärksten Trends hoch, der Filter nimmt genau diese Positionen heraus.
- Zufallstest: Vorsprung nur in 8 % der Ziehungen positiv, im Mittel −40 Punkte pro Jahr bei gleicher Schwankung.
- Mit doppelten Kosten dasselbe Bild.

**Runde 22: kein Ausbau.** Der Vorsprung aus der Entwicklung war ein Zufallstreffer bzw. hängt an der Marktphase;
die gemeinsame Zufallsprüfung in Runde 21 hatte das richtig angezeigt.

# Stand nach 22 Runden und 101 Versuchen

- Der einfache 14-Tage-Trend bleibt der einzige belegte Baustein. 14 Abwandlungen haben ihn nicht verbessert.
- Positiv für die Belastbarkeit: Fünf andere Bauarten desselben Gedankens (EMA-Kreuz, Donchian, stetige Größe,
  ohne letzten Tag, 70/30) erreichen in der Entwicklung Sharpe 0,78 bis 0,94 gegen 0,95. Der Vorteil hängt also
  nicht an einer Einstellung.
- Weitere Varianten auf denselben Daten zu testen, bis eine besteht, würde bei einer 5-%-Hürde im Schnitt nach
  etwa 20 Versuchen einen Zufallstreffer liefern. Neue Belege können nur aus neuen Daten kommen: Vorwärtstest,
  langer Export des Signal-Dienstes.

---

# Runde 23: „Short nach Pump“ mit eigenem Signal auf vielen kleinen Coins (festgelegt vor dem ersten Ergebnis)

**Begründung:** Auf den zehn großen Coins ist nach 101 Versuchen nichts mehr von Zufall zu trennen, weil eine
einzige Zeitreihe von dreieinhalb Jahren zu wenig Belege liefert. Ein Ansatz mit **tausenden voneinander
weitgehend unabhängigen Einzelereignissen** hat diese Schwäche nicht. Der stärkste Hinweis der ganzen Suche
(Runde 18: +0,92 % je Trade) stammt aus genau so einem Ansatz, hing dort aber am undurchsichtigen Score eines
Anbieters und an 90 Tagen. Hier wird die Idee mit eigenen, offenen Regeln auf mehreren Jahren geprüft.

**Daten:** alle Krypto-Kontrakte, die bei Yubit gelistet sind und Binance-Historie haben, ohne die 49 großen Coins
der Gruppen A–D und ohne Nicht-Krypto-Kontrakte: 281 Coins. 5-Minuten-Kerzen und Funding von Binance für jeden
Monat ab 01/2023, in dem der Coin laut Tageskerzen einen Sprung von rund 15–18 % hatte (plus Nachbarmonate).
Entwicklung 01/2023–03/2025, Prüfzeitraum 04/2025–10/2026.

**Grundregel (wie Runde 18, ohne Score):** Signal, sobald der Schluss einer 5-Minuten-Kerze mindestens 20 % über dem
von vor 24 Stunden liegt. Short zur nächsten Eröffnung, Ziel 10 % (Limit), Stop 8 % (Market), beide in einer Kerze
= Stop, nach 72 Stunden glatt, je Coin eine Position. Kosten: Taker 0,08 % / Maker 0,04 % mit 85 % Rebate, Slippage
2 × halbe Yubit-Spanne des Coins, echtes Binance-Funding. Je Trade 10 % des Kontos.

**15 Varianten, je eine Einstellung.** Die Merkmale sind an die Feldnamen des Dienstes angelehnt (Tempo, Funding,
Volumen, Trend, Liquidität), die Schwellen sind runde Werte ohne Raster:

| # | Name | Zusatzbedingung beim Signal |
|---|---|---|
| 0 | roh | keine |
| 1 | ab30 | Anstieg ≥ 30 % |
| 2 | ab50 | Anstieg ≥ 50 % |
| 3 | schnell | mindestens die Hälfte des Anstiegs in den letzten 4 Stunden |
| 4 | langsam | weniger als die Hälfte in den letzten 4 Stunden |
| 5 | funding_plus | letzter Funding-Satz > 0 (Longs zahlen) |
| 6 | funding_hoch | letzter Funding-Satz ≥ 0,03 % |
| 7 | funding_minus | letzter Funding-Satz < 0 (Shorts zahlen schon) |
| 8 | gedreht | Kurs liegt schon ≥ 5 % unter dem 24-Stunden-Hoch |
| 9 | am_hoch | Kurs liegt höchstens 2 % unter dem 24-Stunden-Hoch |
| 10 | volumen_fällt | Umsatz der letzten Stunde unter dem Stundenmittel der 24 Stunden davor |
| 11 | aus_dem_tief | 7-Tage-Rendite vor dem Anstieg (bis 24 h zuvor) < 0 |
| 12 | im_lauf | 7-Tage-Rendite vor dem Anstieg ≥ +20 % |
| 13 | liquide | 24-Stunden-Umsatz ≥ 20 Mio. $ |
| 14 | dünn | 24-Stunden-Umsatz < 5 Mio. $ |

**Stufen:**
1. Entwicklung: mindestens 300 Trades, netto mit Rebate > 0 in beiden Hälften (Teilung 01.03.2024).
2. Gemeinsame Zufallsprüfung über alle 15 in der Entwicklung (White's Reality Check, Tagesergebnisse, stationärer
   Bootstrap mit Blöcken von im Mittel 5 Tagen, 5.000 Ziehungen): Tagesmittel über dem 95-%-Wert des größten
   Zufallswerts. Nullhypothese: kein Ertrag.
3. Doppelte Slippage: netto > 0 in der Entwicklung.
4. Prüfzeitraum, je Variante einmal: netto > 0, vor Kosten > 0, mindestens 100 Trades, und Mittelwert je Trade > 0
   in mindestens 95 % von 2.000 Ziehungen ganzer Tage.
5. Kein Coin über 25 % des Gewinns im Prüfzeitraum; größter Konto-Einbruch über alles < 15 %.

**Vorwissen und Schwächen, vorab benannt:**
- Aus Runde 18 kenne ich das Ergebnis für 51 Coins von 08–11/2026 mit dem Score des Dienstes; dessen Statistik
  sagt, dass alle Signale zusammen nur in 32 % der Fälle −10 % erreichen. Die Roh-Regel erwarte ich daher schwach.
- Auswahl der Coins von heute: Coins, die inzwischen von der Börse genommen wurden, fehlen. Das sind oft Coins, die
  nach einem Pump zusammenbrachen (für Shorts günstig); die Verzerrung wirkt eher gegen die Strategie.
- Kurse von Binance, Handel wäre bei Yubit; Spannen aus einer Stichprobe; in dünnen Coins ist der Stop bei Yubit
  womöglich teurer. Yubit verlangt für Bots eine Freigabe.
Gesamtzahl der Versuche danach: 116 plus Massentest.

**Nachtrag zu Runde 23, vor dem ersten Ergebnis:** (1) Es sind 280 Coins, nicht 281. (2) Höchstens 10 Positionen
gleichzeitig (10 × 10 % = Einsatz 100 %), weitere Signale verfallen; ohne diese Grenze könnten in einer
Altcoin-Rallye beliebig viele Shorts offen sein. (3) Trades, deren Kursdaten vor dem Ausstieg abreißen (Coin-Monat
nicht im Archiv), werden verworfen und gezählt.

# Runde 23: Ergebnis (15.11.2026)

Zahlen in `suche_runde23.json`. 280 Coins, Entwicklung 01/2023–03/2025. **Keine der 15 Varianten besteht Stufe 1.**
Der Prüfzeitraum wurde nicht angesehen.

| Variante | Trades | Ziel erreicht | vor Kosten je Trade | netto je Trade | Konto H1 | Konto H2 |
|---|---|---|---|---|---|---|
| roh (≥ 20 %) | 4.440 | 40,8 % | −0,35 % | −0,57 % | −170 % | −82 % |
| ab30 | 2.399 | 43,4 % | −0,19 % | −0,41 % | −101 % | +4 % |
| ab50 | 811 | 44,0 % | −0,27 % | −0,48 % | −30 % | −9 % |
| schnell | 2.019 | 43,4 % | +0,03 % | −0,18 % | −35 % | −2 % |
| langsam | 3.785 | 40,4 % | −0,35 % | −0,57 % | −171 % | −45 % |
| funding_plus | 3.554 | 41,7 % | −0,05 % | −0,26 % | −97 % | +5 % |
| funding_hoch | 1.187 | 43,6 % | +0,14 % | −0,04 % | −26 % | +21 % |
| funding_minus | 1.412 | 39,6 % | −0,80 % | −1,03 % | −115 % | −30 % |
| gedreht | 2.762 | 42,0 % | −0,31 % | −0,53 % | −100 % | −47 % |
| am_hoch | 3.188 | 40,9 % | −0,20 % | −0,42 % | −105 % | −28 % |
| volumen_fällt | 2.162 | 41,2 % | −0,13 % | −0,34 % | −80 % | +6 % |
| aus_dem_tief | 1.715 | 40,4 % | −0,22 % | −0,45 % | −39 % | −37 % |
| im_lauf | 1.597 | 43,1 % | −0,10 % | −0,28 % | −66 % | +22 % |
| liquide | 4.431 | 40,8 % | −0,35 % | −0,57 % | −171 % | −82 % |
| dünn | 0 | – | – | – | – | – |

- Nötig wären vor Kosten 44,4 % Treffer. Die Roh-Regel liegt bei 40,8 %, die beste Variante bei 44,0 %. Das deckt
  sich mit der eigenen Statistik des Signal-Dienstes (32–42 %).
- Wer in einen Pump hinein shortet, ohne mehr zu wissen, verliert. Am teuersten ist es, wenn die Shorts schon
  Funding zahlen (funding_minus: −1,0 % je Trade), also wenn viele andere dieselbe Idee haben.
- Die erste Hälfte (2023 bis Anfang 2024) ist bei allen Varianten negativ, die zweite bei einigen leicht positiv.
- „Dünn“ hat keinen Fall: Während eines Pumps liegt der Tagesumsatz bei Binance praktisch immer über 5 Mio. $.

**Runde 23: durchgefallen.** Mit einfachen, offenen Regeln steckt in „Short nach Pump“ kein Vorteil. Falls die
Signale des Dienstes einen haben, steckt er in dessen Score, und das ist nur mit dem langen Export oder live
prüfbar. Stand: 116 Einzelhypothesen plus Massentest.
