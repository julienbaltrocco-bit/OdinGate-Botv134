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
python3 -m vorwaertstest.board_verschluesseln --quelle vorwaertstest/lauf/dashboard.json --ziel ../docs/stand.enc.json
git add vorwaertstest/lauf ../docs/stand.enc.json
git commit -q -m "Vorwärtstest (Papier) $(date -u '+%F %H:%M') UTC

Co-Authored-By: Claude Fable 5.2 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01Ti9KuBStbgAKmCzGpRA6zL" || true
git push -q origin "$ZWEIG"
echo "gesichert: $(git rev-parse --short HEAD)"


# Zweites, getrenntes Papier-Konto: dieselbe Regel mit Stop 5 % und Gewinnziel 15 % (Start 15.11.2026)
python3 -m vorwaertstest.bot schritt --config vorwaertstest/config_lauf_tpsl.json --daten vorwaertstest/lauf_tpsl
python3 -m vorwaertstest.dashboard_daten --config vorwaertstest/config_lauf_tpsl.json --daten vorwaertstest/lauf_tpsl
python3 -m vorwaertstest.board_verschluesseln --quelle vorwaertstest/lauf_tpsl/dashboard.json --ziel ../docs/stand_tpsl.enc.json
git add vorwaertstest/lauf_tpsl ../docs/stand_tpsl.enc.json
git commit -q -m "Vorwärtstest (Papier, Stop 5 % / Ziel 15 %) $(date -u '+%F %H:%M') UTC

Co-Authored-By: Claude Fable 5.2 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01Ti9KuBStbgAKmCzGpRA6zL" || true
git push -q origin "$ZWEIG"
echo "gesichert (Variante): $(git rev-parse --short HEAD)"
