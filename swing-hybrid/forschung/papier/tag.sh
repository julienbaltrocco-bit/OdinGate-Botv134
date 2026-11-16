#!/usr/bin/env bash
# Täglicher Lauf aller registrierten Papier-Tests.
# Jeder Ordner forschung/papier/<ID>/ mit konfiguration.json ist ein Test; ein neuer Ordner wird ohne weitere Änderung mitgeführt.
# Tests der Art "orderbuch_stuetze" brauchen nur python3. Tests aus der Strategie-Fabrik ("fabrik") brauchen numpy, pandas und numba;
# dafür wird einmal je Maschine eine kleine Python-Umgebung angelegt.
# Ergebnis: forschung/papier/ausgabe/<ID>.json je Test (für die Übersicht) und register.json (Strategie-Register).
set -u
cd "$(dirname "$0")/../.."
fehler=0
PY=python3
if grep -ql '"strategie": "fabrik"' forschung/papier/*/konfiguration.json 2>/dev/null; then
  if [ ! -x .venv-papier/bin/python ]; then
    python3 -m venv .venv-papier && .venv-papier/bin/pip -q install numpy pandas numba || { echo "Python-Umgebung für Fabrik-Tests konnte nicht angelegt werden"; fehler=1; }
  fi
  [ -x .venv-papier/bin/python ] && PY=.venv-papier/bin/python
fi
for cfg in forschung/papier/*/konfiguration.json; do
  id=$(basename "$(dirname "$cfg")")
  if grep -q '"strategie": "fabrik"' "$cfg"; then lauf="$PY"; else lauf=python3; fi
  timeout 2400 "$lauf" -m forschung.papier.runner "$id" || fehler=1
done
timeout 300 python3 -m forschung.papier.spiegel || fehler=1
cp forschung/register/register.json forschung/papier/ausgabe/register.json
python3 -m forschung.engine.zusammenfassung || true
echo "Dateien für die Übersicht:"; ls -1 forschung/papier/ausgabe/*.json
exit $fehler
