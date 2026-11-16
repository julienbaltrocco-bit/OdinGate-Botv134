#!/usr/bin/env bash
# Nach dem täglichen Lauf (tag.sh): Stand der Schattentests verschlüsseln und im Forschungszweig sichern.
# Das Trading Board (GitHub Pages) liest diese eine Datei. Geändert wird nur forschung/papier/board/schattentests.enc.json.
set -u
ZWEIG=claude/alpha-forschung-r1
cd "$(dirname "$0")/../.."
python3 -m forschung.papier.board || { echo "Verschlüsseln gescheitert"; exit 1; }
git add forschung/papier/board/schattentests.enc.json
git commit -q -m "Schattentests: Stand für das Board $(date -u '+%F %H:%M') UTC" -- forschung/papier/board/schattentests.enc.json || { echo "nichts zu sichern"; exit 0; }
for versuch in 1 2 3 4; do
  if git pull -q --rebase origin "$ZWEIG" && git push -q origin "HEAD:$ZWEIG"; then echo "gesichert: $(git rev-parse --short HEAD)"; exit 0; fi
  sleep $((versuch * 5))
done
echo "Sichern gescheitert (Push abgelehnt)"; exit 1
