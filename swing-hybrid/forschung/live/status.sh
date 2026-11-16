#!/usr/bin/env bash
# Zeigt, ob der OdinGate-Live-Dienst läuft, und die letzten Zeilen seines Protokolls. Ändert nichts.
echo "=== OdinGate Live-Dienst: $(systemctl is-active odingate-live 2>/dev/null) | $(date -u '+%F %H:%M') UTC ==="
docker stats --no-stream --format 'Auslastung: {{.CPUPerc}} Rechenzeit, {{.MemUsage}} Speicher' odingate-live 2>/dev/null || echo "Container läuft nicht."
echo "--- letzte Meldungen ---"
docker logs --tail 12 odingate-live 2>&1 | cut -c1-230
if systemctl list-unit-files odingate-bot.timer >/dev/null 2>&1 && systemctl cat odingate-bot.timer >/dev/null 2>&1; then
  echo "--- Bot für Test 1 und 2: Zeitplan $(systemctl is-active odingate-bot.timer 2>/dev/null) ---"
  echo "wer rechnet laut Repository: $(python3 -c "import json; print(json.load(open('/opt/odingate/bot/swing-hybrid/vorwaertstest/betrieb.json', 'rb'))['betreiber'])" 2>/dev/null)   |   letzter Durchgang: $(systemctl show odingate-bot.service -p Result --value 2>/dev/null)"
  git -C /opt/odingate/bot log -1 --format='letzter gesicherter Lauf: %cd | %an | %s' --date=format:'%F %H:%M UTC' 2>/dev/null
  echo "Platz des Bot-Ordners: $(du -sh /opt/odingate/bot 2>/dev/null | cut -f1)"
  journalctl -u odingate-bot.service -n 6 --no-pager -o cat 2>/dev/null | cut -c1-200
fi
echo "=== Ende. Bitte diesen Text (oder ein Bildschirmfoto) an Claude schicken. ==="
