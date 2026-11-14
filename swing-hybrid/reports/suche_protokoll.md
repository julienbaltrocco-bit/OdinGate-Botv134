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
