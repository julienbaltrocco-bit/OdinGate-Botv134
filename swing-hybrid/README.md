# Swing-Hybrid (Machbarkeitsprüfung)

Historische Simulation, keine Anlageberatung, keine echten Orders.

Frage: Kann ein Swing-Signal (Richtung) plus Dip-Käufe per Limit innerhalb dieser Richtung auf Yubit-Futures
mehr Volumen erzeugen und dabei nach Gebühren mindestens so gut bleiben wie die reine Swing-Strategie?

- `config.yaml` – alle Regeln (Gebühren, Hebel, Limits, Entscheidungsregeln)
- `src/hybrid/` – Rechenkern
- `scripts/intake.py` – Upload sicher entpacken + Inventur
- `reports/hybrid_report.md` – Ergebnisbericht (kommt am Ende)

Einrichten in der Cloud-Umgebung:

```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
.venv/bin/python -m pytest -q
```

## Ablauf (nach dem Entpacken der Daten)

```bash
.venv/bin/python -I scripts/intake.py data/download/trading-labor.zip labor-daten   # ZIP sicher entpacken
.venv/bin/python -I scripts/kerzen_laden.py     # Binance-5m-Kerzen + Funding (braucht data.binance.vision)
.venv/bin/python -I scripts/signal_check.py     # Swing-Signale gegen das Labor prüfen
.venv/bin/python -I scripts/baseline.py         # reine Swing mit Yubit-Gebühren
.venv/bin/python -I scripts/raster.py           # Baseline + 18 Hybrid-Varianten, Hebel 1 und 3
.venv/bin/python -I scripts/walkforward.py      # 70/30, rollierende Fenster, Entscheidungsregeln
.venv/bin/python -I scripts/gegenpruefung.py    # Gegenprüfungen
.venv/bin/python -I scripts/bericht.py          # reports/hybrid_report.md
```

Die Rohdaten (`data/`) liegen nur in der Cloud-Umgebung und nicht im Repo.

## Suche nach einer Strategie mit hohem Umsatz (Rebate als größerer Gewinnanteil)

Regeln und Zwischenergebnisse: `reports/suche_protokoll.md`. Ergebnis: `reports/suche_bericht.md`.

```bash
.venv/bin/python -I scripts/kerzen_laden.py BNBUSDT TRXUSDT ATOMUSDT BCHUSDT ETCUSDT FILUSDT UNIUSDT NEARUSDT XLMUSDT AAVEUSDT
.venv/bin/python -I scripts/suche_stufe1.py && .venv/bin/python -I scripts/suche_stufe2bis5.py   # Runde 1
.venv/bin/python -I scripts/fuellmodell_diagnose.py
.venv/bin/python -I scripts/suche_runde2.py                                                      # Runde 2
.venv/bin/python -I scripts/suche_runde3.py                                                      # Runde 3
.venv/bin/python -I scripts/kandidat_pruefen.py && .venv/bin/python -I scripts/suche_bericht.py
```
