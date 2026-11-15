# OdinGate Alpha-Forschung: Bericht Runde 1

Stand: 15.11.2026. Zweig `claude/alpha-forschung-r1`, Ordner `swing-hybrid/forschung/`. Alles ist Rückrechnung auf
historischen Daten. Kein echtes Geld, keine Orders, keine Anlageberatung. Die laufenden Papier-Tests, ihr Code, ihre
Daten und das Dashboard wurden nicht angefasst.

## Kurzfassung

1. **Sechs neue Ideen für kurzfristigen Handel sind geprüft, fünf davon sind klar gescheitert.** Aufschlag des
   Kontrakts, Funding-Termin (zwei Formen), Nachlauf hinter BTC und Erholung nach Zwangsliquidationen verdienen ihre
   Kosten nicht, auch nicht mit 85 % Rebate.
2. **Eine neue Informationsquelle zeigt echte Vorhersagekraft: die Tiefe des Orderbuchs.** Ein ungewöhnliches
   Übergewicht der Kauf- oder Verkaufsaufträge bis 5 % um den Kurs sagt die Richtung der nächsten ein bis zwei
   Stunden vorher. Vor Kosten ist das statistisch deutlich (t = 4,9 über 27 Monate).
3. **Daraus entstand ein Kandidat, „Orderbuch-Stütze“ Version 1.1.** Er hat alle vorab festgelegten Hürden formal
   bestanden, auch im einmalig geöffneten Validierungsjahr. Dort bleiben nach allen Kosten **+4,4 Basispunkte je
   Trade**, bei 2,5 Trades am Tag und rund zwei Stunden Haltedauer. Das sind rund **+14 % pro Jahr ohne Hebel**.
4. **Der Kandidat ist schwach belegt und hängt vollständig am Rebate.** Ohne Rebate verliert er rund 28 % pro Jahr.
   Er braucht ein Rebate von mindestens etwa 57 %. Das Validierungsjahr allein ist nicht gesichert (t = 1,1), und
   auf sieben weiteren Coins bleibt nach Kosten nichts übrig.
5. **Empfehlung:** noch keinen Vorwärtstest starten. Zuerst die eingefrorene Regel einmal auf dem bisher ungeöffneten
   Zeitraum 04/2025 bis 10/2026 prüfen. Das kostet wenige Minuten Rechenzeit und ist aussagekräftiger als Monate
   Papierhandel.

Eine Zahl zur Einordnung: Ein Basispunkt (bp) ist ein Hundertstel Prozent. Ein Trade kostet mit 85 % Rebate rund
4 bis 5 bp (Gebühr 2,4 bp plus Spanne), ohne Rebate rund 18 bp.

## A. Was wurde untersucht?

**Vorgehen.** Zuerst die Lücken der bisherigen Forschung (13 Richtungen, `protokoll.md` Abschnitt 2), dann fünf
Hypothesen mit benennbarem Mechanismus. Jede Regel stand schriftlich fest und war als Commit gesichert, bevor sie
gerechnet wurde. Entwicklung und Validierung sind zeitlich getrennt; die Validierung wurde je Regel genau einmal
geöffnet. Der Zeitraum ab 04/2025 wurde weder geladen noch angesehen.

**Neue Daten** (Binance-Archiv, bis 03/2025):
- Orderbuch-Tiefe alle 30 Sekunden, ab 01/2023, zehn Coins (2,2 GB).
- Aufschlag des Kontrakts auf den Index, 5 Minuten, zehn Coins.
- 1-Minuten-Kerzen, zehn Coins.

**Experimente** (13 von höchstens 15, zusammen 52 angesehene Einstellungen):

| Nr. | Idee | Ergebnis |
|---|---|---|
| E01 | Orderbuch-Tiefe nahe am Kurs (1 %) | verworfen, aber erster erkennbarer Effekt |
| E02 | Gegenposition bei extremem Aufschlag des Kontrakts | verworfen |
| E03 | Position vor dem Funding-Termin, Gegenrichtung danach | verworfen |
| E04 | Altcoins laufen BTC hinterher (1-Minuten-Daten) | verworfen |
| E05 | Erholung nach Kurssturz mit fallendem Open Interest | verworfen |
| E06 | Funding in zehn Minuten um den Termin abgreifen | verworfen |
| E07 | Ursachenanalyse Orderbuch-Tiefe, 17 Einstellungen | Regel abgeleitet, Zufallsprüfung knapp (p = 0,09) |
| E08 | Vollprüfung Version 1.0 mit Validierung | formal bestanden |
| E09 | Dieselbe Regel auf sieben frischen Coins | roh knapp bestätigt, nach Kosten negativ |
| E10 | Acht Ausstiegsarten (Zeit, Signal, Stop, Trailing, Break-even) | Signal-Ausstieg vorn (p = 0,05) |
| E11 | Kombination mit dem 14-Tage-Trend | unabhängig voneinander (Korrelation −0,03) |
| E12 | Marktphasen | Wirkung vor allem bei hoher Schwankung |
| E13 | Version 1.1 in der Validierung | formal bestanden, Vorsprung geschrumpft |

## B. Was funktioniert?

**Die Orderbuch-Tiefe als Signal.** Rohe Kursbewegung in Signalrichtung, also vor allen Kosten:

| Coins | Zeitraum | Trades | roh je Trade | t-Wert |
|---|---|---|---|---|
| BTC, ETH, SOL (Version 1.0, 60 min) | Entwicklung 01/2023–03/2024 | 1.509 | +9,8 bp | 3,8 |
| BTC, ETH, SOL | Validierung 04/2024–03/2025 | 1.239 | +6,8 bp | 2,6 |
| sieben frische Coins | beide Zeiträume | 6.399 | +3,6 bp | 2,1 |

Der Effekt wächst, je tiefer man ins Orderbuch schaut und je strenger die Schwelle ist. Eine einfache Gegenbewegung
ohne Orderbuch bringt mit gleich vielen Trades nur etwa die Hälfte und ist nicht gesichert.

**Der Kandidat „Orderbuch-Stütze“ 1.1.** Regel: Einstieg, wenn das Übergewicht der Aufträge mindestens drei
Standardabweichungen über oder unter seinem 24-Stunden-Mittel liegt; Ausstieg, sobald es unter eine
Standardabweichung fällt, spätestens nach vier Stunden. BTC, ETH, SOL, alle Orders als Taker.

| Kennzahl (Hebel 1) | Entwicklung | Validierung |
|---|---|---|
| Trades je Tag, mittlere Haltedauer | 2,5 · 128 min | 2,5 · 128 min |
| Kursbewegung roh je Trade | +19,2 bp | +8,3 bp |
| **Netto mit 85 % Rebate** | +15,3 bp | **+4,4 bp** |
| Netto mit 50 % Rebate | +9,7 bp | −1,2 bp |
| **Netto ohne Rebate** | +1,7 bp | **−9,2 bp** |
| Gewinnquote, Profit Factor | 64 % · 1,49 | 57 % · 1,12 |
| Ertrag pro Jahr mit Rebate | 45,5 % | 13,6 % |
| Ertrag pro Jahr ohne Rebate | – | −28 % |
| Sharpe | 3,3 | 1,1 |
| Größter Rückgang | 7,8 % | 13,6 % |
| Tiefster Kontostand über alle Starttage, Hebel 1 / 3 / 5 | 92 / 75 / 59 % | 86 / 59 / 31 % |
| Liquidationen (Annahme: Erhaltungsmargin 1 %) | 0 | 0 |

Die Zahlen der Entwicklung sind geschönt, weil die Regel dort ausgewählt wurde. Maßgeblich ist die Validierung.

**Abhängigkeit vom Rebate.** Vollständig. In der Validierung deckt die Kursbewegung die volle Gebühr nicht. Die
Gewinnschwelle liegt bei einem Rebate von etwa 57 %.

## C. Was funktioniert nicht?

- **Aufschlag des Kontrakts (E02):** sagt die Richtung nicht vorher (roh +0,3 bp).
- **Funding-Termin (E03, E06):** Das Funding kommt herein (6 bis 8 bp), aber der Kurs gibt es um den Termin im
  Mittel wieder ab. Die Vorstellung, Funding ließe sich mit kurzer Haltedauer fast risikolos einsammeln, ist widerlegt.
- **Nachlauf hinter BTC (E04):** Nach fünf Minuten haben die Altcoins eine BTC-Bewegung bereits vollzogen.
- **Zwangsliquidationen (E05):** Richtung wie erwartet, aber nicht von Zufall zu trennen.
- **Nachgezogene Stops, nachgezogenes Gewinnziel, Break-even (E10):** Sie verändern die Gewinnquote (bis 74 %),
  verschlechtern aber den Ertrag. Das deckt sich mit den Runden 20 und 24.
- **Übertragung auf weitere Coins (E09):** Auf XRP, DOGE, LINK, AVAX, LTC bleibt nach Kosten nichts (−0,4 bp).
- **Der Signal-Ausstieg als großer Hebel (E13):** In der Entwicklung fast dreimal so gut wie der feste Ausstieg, in
  der Validierung kaum besser. Der Vorsprung war überwiegend Anpassung an die Entwicklungsdaten.

## D. Welche Strategie ist aktuell am interessantesten?

**„Orderbuch-Stütze“ 1.1**, weil sie als einzige neue Regel auf einer Information beruht, die nachweislich etwas
vorhersagt, und weil sie zum gewünschten Stil passt (mehrere Trades am Tag, Haltedauer rund zwei Stunden).

| Kriterium | Einschätzung |
|---|---|
| Profitabilität | klein: +4,4 bp je Trade, rund 14 % pro Jahr ohne Hebel, nur mit Rebate |
| Risiko | mäßig: Rückgang 14 %, keine Liquidation bis Hebel 3; bei Hebel 5 fällt jeder neunte Start unter die Hälfte |
| Handelsfrequenz | 2,5 Trades je Tag über drei Coins |
| Datenqualität | gut für die Rückrechnung (Binance-Archiv, 3 von 821 Tagen fehlen); für den Betrieb offen, siehe unten |
| Ausführbarkeit | kritisch: fünf Minuten Verzögerung kosten 40 % der Kursbewegung; Signal von Binance, Handel bei Yubit |
| Statistische Belastbarkeit | gering bis mittel: Signal vor Kosten gesichert, Gewinn nach Kosten nicht |

**Offene Punkte zur Ausführbarkeit.**
- Das Signal kommt aus dem **Binance**-Orderbuch. Yubit liefert über seine Schnittstelle höchstens 200 Preisstufen;
  bei BTC sind das nur ±0,04 % um den Kurs. Die Tiefe bis 5 % ist dort nicht abrufbar.
- Für einen Live-Betrieb bräuchte der Bot das volle Binance-Orderbuch in Echtzeit. Aus dieser Cloud-Umgebung ist
  die Binance-Schnittstelle nicht erreichbar; erreichbar ist nur das Archiv mit einem Tag Verzug.
- Maker-Ausführung wurde nicht unterstellt. Ob passive Orders die Kosten senken würden, ist mit Kerzendaten nicht
  prüfbar.

## E. Wie groß ist die tatsächliche Verbesserung?

Vergleich unter gleichen Bedingungen: gleicher Zeitraum 01/2023 bis 03/2025, Hebel 1, feste Größe, gleiche
Kostenannahmen.

| | 14-Tage-Trend (bisher) | Orderbuch-Stütze 1.0 | Mischung gleiches Risiko |
|---|---|---|---|
| Ertrag pro Jahr mit Rebate | 63,7 % | 18,6 % | – |
| Ertrag pro Jahr ohne Rebate | +34,6 % | −36,8 % | negativ |
| Sharpe mit Rebate | 1,0 | 1,6 | 1,9 |
| Größter Rückgang (Anteil am Startkapital) | 51 % | 17 % | – |
| Zeit im Markt | fast immer | rund 5 % | – |
| Korrelation der Tagesergebnisse | | −0,03 | |

- **Kein Ersatz für den Trend, höchstens eine Ergänzung.** Die neue Regel verdient weniger, schwankt aber viel
  weniger und läuft unabhängig vom Trend. Zusammen wäre das Verhältnis von Ertrag zu Risiko besser gewesen.
- **Zwei Einschränkungen.** Der Zeitraum war für den Trend ein guter (im späteren Prüfzeitraum Sharpe 0,34). Und
  ohne Rebate bleibt nur der Trend positiv; die neue Regel und die Mischung nicht.
- Die Audit-Befunde gelten weiter: Rebate unbestätigt, Margin-Regeln von Yubit unbekannt.

**Eingeordnet in die Erfolgskriterien:** Erfolg D (neue Informationsquelle mit nachvollziehbarer Vorhersagekraft)
ist erreicht. Erfolg A (neue profitable Strategie) ist nicht belegt. Für fünf Ideen liegt ein belastbarer negativer
Befund vor (Erfolg E).

## F. Wie geht es weiter?

**Empfehlung: weiterforschen, aber in genau einem Schritt, und noch keinen Vorwärtstest starten.**

1. **Einmalige Prüfung auf dem ungeöffneten Zeitraum 04/2025 bis 10/2026** (braucht deine Freigabe, weil damit die
   letzten unberührten Daten verbraucht werden). Regel 1.1 unverändert, BTC, ETH, SOL. Vorab festgelegt:
   bestanden, wenn die rohe Kursbewegung positiv ist mit t ≥ 2 **und** das Netto mit 85 % Rebate positiv ist.
   Erwartet werden rund 1.400 Trades. Fällt die Regel durch, wird sie verworfen. Aufwand: ein Download, eine Rechnung.
2. **Nur wenn das besteht:** Schattentest als Vorwärtstest. Täglich die Orderbuch-Datei des Vortags aus dem
   Binance-Archiv laden, die Trades des Vortags bilden und in einem eigenen Papier-Konto buchen; dazu die zur
   Signalzeit gemessene Yubit-Spanne. Zweck ist das Messen der Ausführung, nicht der Beweis des Vorteils: Bei
   2,5 Trades am Tag bräuchte ein statistischer Beleg mehr als zwei Jahre.
3. **Parallel und unabhängig davon: Yubit schriftlich fragen**, ob das Rebate von 85 % für Bot-Umsatz gilt. Unter
   etwa 57 % ist der Kandidat erledigt.
4. **Nicht empfohlen:** weitere Varianten der fünf gescheiterten Ideen; ein Filter auf hohe Schwankung oder
   Tageszeit ohne neue Daten (E12 ist nur ein Hinweis aus der Entwicklung); Hebel über 3.

Mögliche Runde 2, falls Schritt 1 besteht (Vorschlag, höchstens fünf Experimente): Orderbuch-Signal mit
1-Minuten-Auflösung statt 5 Minuten; Kauf- und Verkaufsdruck aus den Minutenkerzen als zweite Bestätigung; Filter
auf hohe Schwankung als eigene, vorab festgelegte Regel.

## Rangliste

Rendite, Risiko und Sicherheit stehen getrennt. Es gibt bewusst keine Gesamtpunktzahl. Netto je Trade in bp;
E01 bis E06 nur Entwicklung (Stufe 0), dort wurden Sharpe und Rückgang nicht berechnet.

| ID | Familie | Märkte | Haltedauer | Trades/Tag | roh | N85 | N0 | Profit Factor | Sharpe | Rückgang | Liquid. | Validierung | Vertrauen |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| OS-1.1 | Orderbuch | BTC, ETH, SOL | 128 min | 2,5 | +8,3 | +4,4 | −9,2 | 1,12 | 1,1 | 13,6 % | 0 | bestanden (formal), D | gering bis mittel |
| OS-1.0 | Orderbuch | BTC, ETH, SOL | 60 min | 3,4 | +6,8 | +2,9 | −10,7 | 1,10 | 1,1 | 13,9 % | 0 | bestanden (formal), durch 1.1 ersetzt | gering bis mittel |
| B0 | 14-Tage-Trend | zehn Coins | 42 h | 5,7 | – | – | – | – | 1,0 (später 0,34) | 51 % | Audit: bei Hebel 3 ja | nicht gesichert (Audit) | gering bis mittel |
| E05 | Positionierung | zehn Coins | 4 h | 2,5 | +9,2 | +1,3 | −12,3 | 1,01 | – | – | – | Stufe 0 nicht bestanden | A |
| E06 | Funding | acht Coins | 10 min | 1,8 | −2,8 | −0,1 | −13,7 | 1,00 | – | – | – | Stufe 0 nicht bestanden | A |
| E03 | Funding | zehn Coins | 65 min | 2,5 | +2,4 | −0,5 | −14,1 | 0,99 | – | – | – | Stufe 0 nicht bestanden | A |
| E01 | Orderbuch 1 % | BTC, ETH, SOL | 60 min | 14,2 | +0,9 | −3,2 | −16,8 | 0,88 | – | – | – | Stufe 0 nicht bestanden | A |
| E04 | BTC-Nachlauf | neun Altcoins | 15 min | 15,9 | +1,5 | −7,4 | −21,0 | 0,76 | – | – | – | Stufe 0 nicht bestanden | A |
| E02 | Aufschlag | zehn Coins | 21 min | 37,4 | +0,3 | −7,5 | −21,1 | 0,76 | – | – | – | Stufe 0 nicht bestanden | A |

Zeile OS: Werte der Validierung. Zeile B0: Zeitraum 01/2023 bis 03/2025.

## Dashboard und Register

- **Zentrales Register:** `register/register.json`, erzeugt von `register/bauen.py`. 16 Einträge: 2 laufende
  Papier-Tests, 1 vorbereiteter Kandidat, 13 Rückrechnungen. Jeder Eintrag trägt Kategorie, Version, Regel,
  Parameter, Daten, Kostenannahmen, Kennzahlen und Ergebnisdateien. Rückrechnungen und laufende Tests sind getrennte
  Kategorien und werden nie gemischt dargestellt.
- **Vorschau der erweiterten Oberfläche:** `dashboard_dev/index.html`, gebaut aus dem Register, als private Seite
  veröffentlicht unter https://claude.ai/artifact/QyTGdysnpzbaYD4xfwkoYA. Sie zeigt Testkarten,
  die Strategie-Bibliothek und den Vergleich. Das echte Board (`docs/index.html`) ist unverändert.
- **Noch nicht gebaut, bewusst:** der Papier-Bot für neue Tests mit eigenen Konten, Lauf-Nummern und Sperre gegen
  Doppelläufe. Er wird erst gebraucht, wenn ein Kandidat Schritt 1 besteht und du einen Test freigibst.
- **Sicherheit:** Das Register enthält nur Forschungsergebnisse, keine Kontodaten. Für die Integration ins echte
  Board gilt der Audit-Befund weiter: Solange der Klartext-Stand der Papier-Tests im öffentlichen Repo liegt,
  schützt das Passwort nichts.

## Ressourcen

| Größe | Wert |
|---|---|
| Hypothesen | 6 (5 geplant, 1 Mutation), dazu 7 Folge-Experimente zum Orderbuch |
| Experimente | 13 von höchstens 15 |
| Angesehene Einstellungen | 52 |
| Rechenzeit | rund 1 Minute Rechnung, rund 12 Minuten Downloads (2,2 GB) |
| Agenten | ein Hauptagent, keine Subagenten |
| Tokenverbrauch | in der Sitzung nicht messbar; kein zusätzlicher Verbrauch durch Agenten |
| Verworfener Aufwand | 5 Hypothesen (E02 bis E06) und 7 von 8 Ausstiegsvarianten |
| Neue Erkenntnisse | Orderbuch-Tiefe sagt vorher; Funding lässt sich nicht kurz abgreifen; BTC-Nachlauf ist nach 5 Minuten vorbei; Trailing-Ausstiege schaden |

## Was gemessen ist, was Annahme, was Erwartung

- **Gemessen:** Kursbewegungen nach dem Signal auf Binance-Daten; Spannen bei Yubit aus einer Stichprobe.
- **Annahme:** Rebate 85 %; Yubit-Kurse verhalten sich wie Binance-Kurse; Erhaltungsmargin 1 %; jede Order wird
  sofort zum Eröffnungskurs plus Spanne gefüllt.
- **Erwartung, nicht belegt:** dass der Effekt nach 03/2025 fortbesteht und bei Yubit handelbar ist.

## Ablage

| Pfad unter `swing-hybrid/forschung/` | Inhalt |
|---|---|
| `protokoll.md` | Lückenanalyse, alle Festlegungen vor der Rechnung, alle Ergebnisse |
| `bericht_runde1.md` | dieser Bericht |
| `alpha/` | Rechenwerkzeug, Kontomodell, Strategie Version 1.0 |
| `experimente/` | je Experiment ein Skript, dazu der Lader für die neuen Daten |
| `ergebnisse/` | Zahlen je Experiment (JSON) und Trade-Listen (CSV) |
| `register/` | zentrales Register und sein Erzeuger |
| `dashboard_dev/` | Vorschau der erweiterten Oberfläche |
| `tests/` | Regressionstests für das Rechenwerkzeug |
