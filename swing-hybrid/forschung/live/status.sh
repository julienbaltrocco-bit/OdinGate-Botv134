#!/usr/bin/env bash
# Zeigt, ob der OdinGate-Live-Dienst läuft, und die letzten Zeilen seines Protokolls. Ändert nichts.
echo "=== OdinGate Live-Dienst: $(systemctl is-active odingate-live 2>/dev/null) | $(date -u '+%F %H:%M') UTC ==="
docker stats --no-stream --format 'Auslastung: {{.CPUPerc}} Rechenzeit, {{.MemUsage}} Speicher' odingate-live 2>/dev/null || echo "Container läuft nicht."
echo "--- letzte Meldungen ---"
docker logs --tail 12 odingate-live 2>&1 | cut -c1-230
echo "=== Ende. Bitte diesen Text (oder ein Bildschirmfoto) an Claude schicken. ==="
