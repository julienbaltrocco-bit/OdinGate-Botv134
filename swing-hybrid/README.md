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
