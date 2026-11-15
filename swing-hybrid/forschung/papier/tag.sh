#!/usr/bin/env bash
# Täglicher Lauf aller registrierten Papier-Tests. Braucht nur python3 und git, keine Zusatzpakete.
# Jeder Ordner forschung/papier/<ID>/ mit konfiguration.json ist ein Test; ein neuer Ordner wird ohne weitere Änderung mitgeführt.
# Ergebnis: forschung/papier/ausgabe/<ID>.json je Test (für das Dashboard) und register.json (Strategie-Register).
set -u
cd "$(dirname "$0")/../.."
fehler=0
for cfg in forschung/papier/*/konfiguration.json; do
  id=$(basename "$(dirname "$cfg")")
  timeout 1500 python3 -m forschung.papier.runner "$id" || fehler=1
done
timeout 300 python3 -m forschung.papier.spiegel || fehler=1
cp forschung/register/register.json forschung/papier/ausgabe/register.json
python3 -m forschung.engine.zusammenfassung || true
echo "Dateien für das Dashboard:"; ls -1 forschung/papier/ausgabe/*.json
exit $fehler
