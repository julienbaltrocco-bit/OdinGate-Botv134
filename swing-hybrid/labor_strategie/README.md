# Strategie-Datei für dein Labor

`trend_14d/strategie.py` ist der Kandidat aus `reports/suche_bericht.md` im Format deines Labors
(`strategien/<name>/strategie.py`). Zum Mitbeobachten im Signalbot den Ordner `trend_14d` nach `strategien/` kopieren.

Hinweise:
- Die Suche hat auf Stundenkerzen der Binance-Futures gerechnet. Dein Labor lädt OKX-Stundenkerzen nur rund
  16 Monate zurück; für das Signal (14 Tage Rückblick) reicht das.
- Das Labor rechnet mit 0,05 % Gebühr und 0,10 % Slippage je Seite auf Stundenkerzen. Damit ist der Kandidat
  klar negativ. Er trägt nur mit deinem Rebate (effektiv 0,012 % Taker) und Slippage unter etwa 0,07 %.
