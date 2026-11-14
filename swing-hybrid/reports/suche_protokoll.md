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
