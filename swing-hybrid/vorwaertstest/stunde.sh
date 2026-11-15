#!/usr/bin/env bash
# Ein stündlicher Durchlauf des Papier-Vorwärtstests: Stand holen, Schritt rechnen, Dashboard-Daten schreiben, sichern.
set -euo pipefail
ZWEIG=claude/intelligent-sagan-2cviug
cd "$(dirname "$0")/../.."
git fetch -q origin "$ZWEIG" || true
git checkout -q "$ZWEIG" 2>/dev/null || git checkout -q -b "$ZWEIG" "origin/$ZWEIG"
git pull -q --ff-only origin "$ZWEIG" || true
cd swing-hybrid
python3 -m vorwaertstest.bot schritt --config vorwaertstest/config_lauf.json --daten vorwaertstest/lauf
python3 -m vorwaertstest.dashboard_daten --config vorwaertstest/config_lauf.json --daten vorwaertstest/lauf
git add vorwaertstest/lauf
git commit -q -m "Vorwärtstest (Papier) $(date -u '+%F %H:%M') UTC

Co-Authored-By: Claude Fable 5.2 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01Ti9KuBStbgAKmCzGpRA6zL" || true
git push -q origin "$ZWEIG"
echo "gesichert: $(git rev-parse --short HEAD)"
bash vorwaertstest/live_start.sh || true
