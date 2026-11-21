# Vorwärtstest Yubit: Zwischenstand

Historische bzw. Papier-Messung, keine Anlageberatung. Stufe „papier“ setzt keine echten Orders.

- Zeitraum: 2026-11-15 13:21 bis 2026-11-21 14:14 UTC (6,0 Tage, 1709 Durchläufe)
- Kapital 5.000 $, Hebel 3,00, 10 Coins, Modus papier
- Tagesregel: Die Richtung wird je Coin einmal am Tag übernommen (Stundenschluss 00:00 UTC) und bis zum nächsten Tag gehalten.
- Bis 2026-11-21 13:39 UTC aus den Aufzeichnungen von Test 1 nachgerechnet (kein Vorwärtstest), danach live.

## Was eine Order zur vollen Stunde gekostet hätte

Gemessen am echten Orderbuch, Order in Standardgröße, 17074 Messungen.

- **Slippage im Mittel: 0,016 %** (unter der Annahme aus dem Backtest (0,05 %))
- Median 0,007 %, schlechteste 10 % ab 0,067 %

| Coin | Messungen | Slippage im Mittel | Schlechteste 10 % ab | Spanne Geld/Brief im Mittel |
|---|---|---|---|---|
| BTC | 1708 | 0,001 % | 0,001 % | 0,002 % |
| ETH | 1707 | 0,001 % | 0,002 % | 0,003 % |
| SOL | 1708 | 0,007 % | 0,007 % | 0,014 % |
| XRP | 1708 | 0,005 % | 0,006 % | 0,010 % |
| DOT | 1707 | 0,073 % | 0,078 % | 0,141 % |
| DOGE | 1708 | 0,009 % | 0,009 % | 0,017 % |
| ADA | 1707 | 0,033 % | 0,036 % | 0,067 % |
| LINK | 1706 | 0,007 % | 0,010 % | 0,011 % |
| AVAX | 1707 | 0,010 % | 0,014 % | 0,015 % |
| LTC | 1708 | 0,012 % | 0,013 % | 0,023 % |

## Orders des Kandidaten

- 10 Orders, Volumen 14.926 $ (2.472 $ pro Tag)
- Slippage nach Volumen gewichtet: 0,015 %
- Gebühr gezahlt: 11,94 $ (das sind 0,080 % vom Volumen)
- Hinweis: Erst 10 Orders. Unter etwa 200 ist das Mittel noch unsicher.

## Ergebnis seit Start

| | Betrag | Anteil am Kapital |
|---|---|---|
| Handel vor Gebühren | +1.211,15 $ | 24,22 % |
| Gebühr | −11,94 $ | −0,24 % |
| Funding | +0,22 $ | 0,00 % |
| Nach voller Gebühr, ohne Rebate | +1.199,43 $ | 23,99 % |
| Rebate (85 %, gerechnet) | +10,15 $ | 0,20 % |
| **Netto mit Rebate** | +1.209,58 $ | 24,19 % |

Offen: 0 Long, 10 Short, Einsatz 13.715 $.

Wenige Wochen sagen über den Gewinn fast nichts. Aussagekräftig ist hier vor allem die Slippage.
