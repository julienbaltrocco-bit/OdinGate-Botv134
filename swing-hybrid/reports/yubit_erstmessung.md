# Erste Messung bei Yubit (14.11.2026)

Eine Momentaufnahme der öffentlichen Yubit-Kursdaten, kein Durchschnitt über die Zeit. Keine Anlageberatung.

## Die 10 Coins des Kandidaten

| Coin | Spanne Geld/Brief | Erwartete Slippage (halbe Spanne) | Mindestorder | Umsatz 24 h |
|---|---|---|---|---|
| BTC | 0,002 % | 0,001 % | 66,45 $ | 996 Mio. $ |
| ETH | 0,003 % | 0,001 % | 18,72 $ | 673 Mio. $ |
| SOL | 0,013 % | 0,007 % | 7,50 $ | 167 Mio. $ |
| XRP | 0,010 % | 0,005 % | 0,10 $ | 49 Mio. $ |
| DOT | 0,129 % | 0,065 % | 0,08 $ | 3 Mio. $ |
| DOGE | 0,016 % | 0,008 % | 0,06 $ | 30 Mio. $ |
| ADA | 0,063 % | 0,031 % | 0,16 $ | 19 Mio. $ |
| LINK | 0,011 % | 0,005 % | 0,09 $ | 12 Mio. $ |
| AVAX | 0,013 % | 0,006 % | 7,84 $ | 10 Mio. $ |
| LTC | 0,021 % | 0,011 % | 0,47 $ | 9 Mio. $ |

- **Mittel der erwarteten Slippage: 0,014 %**, Median 0,007 %. Der Backtest hat mit 0,050 % gerechnet.
- Ausreißer: DOT (0,065 %) und ADA (0,031 %).
- Der erste Papier-Durchlauf des Bots hat mit dem echten Orderbuch denselben Wert ergeben (im Mittel rund 0,015 %).

## Was das für den Kandidaten bedeuten würde

Netto mit Rebate im Prüfzeitraum (10 Coins, Hebel 0,2), je nach Slippage:

| Slippage je Order | Netto mit Rebate |
|---|---|
| 0,000 % | +9,1 % |
| 0,025 % | +5,8 % |
| 0,050 % | +2,4 % |
| 0,075 % | −0,9 % |

Bei der heute gemessenen Slippage von rund 0,014 % wären es etwa **+7,2 %** statt +2,4 %.
Das gilt nur, wenn die Spannen auch zu anderen Tageszeiten und in unruhigen Phasen so eng bleiben. Genau das misst der Vorwärtstest.

## Alle vier Coin-Gruppen

| Gruppe | Bei Yubit gelistet | Spanne Geld/Brief (Median) | Größte Spanne | Größte Mindestorder |
|---|---|---|---|---|
| A | 10 von 10 | 0,013 % | 0,129 % | 66,45 $ |
| B | 10 von 10 | 0,013 % | 0,148 % | 10,53 $ |
| C | 19 von 20 | 0,045 % | 0,179 % | 0,88 $ |
| D | 10 von 20 | 0,073 % | 0,184 % | 0,53 $ |

Nicht gelistet: SNX, IOTA, ONT, QTUM, KAVA, BAT, YFI, ANKR, RLC, KNC, CELR.

- Die Gruppen A und B (die 20 großen Coins) haben enge Spannen. In C und D sind sie drei- bis fünfmal so weit.
- BTC braucht mindestens rund 66 $ je Order. Bei 100 $ je Coin (5.000 $ Kapital, Hebel 0,2) passt genau eine Einheit.
  Unter etwa 3.300 $ Kapital fällt BTC aus dem Portfolio.

## Nachtrag: Stichprobe über eine Stunde und Tiefe des Orderbuchs

30 Messungen im Abstand von 2 Minuten (15:40–16:39 UTC). Slippage = halbe Spanne.

| Coin | Slippage im Mittel | Höchster Wert | Slippage bei 1.000 $ | bei 10.000 $ |
|---|---|---|---|---|
| BTC | 0,001 % | 0,008 % | 0,001 % | 0,001 % |
| ETH | 0,001 % | 0,004 % | 0,001 % | 0,001 % |
| SOL | 0,007 % | 0,007 % | 0,007 % | 0,007 % |
| XRP | 0,006 % | 0,021 % | 0,005 % | 0,005 % |
| DOT | 0,066 % | 0,067 % | 0,093 % | 0,127 % |
| DOGE | 0,008 % | 0,008 % | 0,008 % | 0,008 % |
| ADA | 0,032 % | 0,032 % | 0,032 % | 0,032 % |
| LINK | 0,005 % | 0,006 % | 0,005 % | 0,012 % |
| AVAX | 0,007 % | 0,013 % | 0,012 % | 0,020 % |
| LTC | 0,011 % | 0,011 % | 0,011 % | 0,021 % |

- Mittel über die 10 Coins: 0,015 %. Die Werte schwanken innerhalb der Stunde kaum.
- Das Orderbuch ist tief: Auch Orders über 10.000 $ kosten bei den meisten großen Coins nur wenig mehr.
- Für die Nachrechnung in Runde 6 habe ich den doppelten Wert je Coin angesetzt (Sicherheitsaufschlag).
- Weiterhin gilt: Es ist eine Stunde eines einzigen Tages. Den Dauerwert liefert der stündliche Vorwärtstest.
