#!/usr/bin/env bash
# Entfernt den OdinGate-Live-Dienst vollständig von diesem Server (Dienst, Container, Abbild, Ordner /opt/odingate).
set -u
[ "$(id -u)" = 0 ] || { echo "Bitte als root ausführen."; exit 1; }
if grep -q '"betreiber": "server"' /opt/odingate/bot/swing-hybrid/vorwaertstest/betrieb.json 2>/dev/null && [ "${1:-}" != "--trotzdem" ]; then
  echo "Halt: Der Bot für Test 1 und 2 läuft gerade auf diesem Server. Bitte zuerst Claude Bescheid geben, damit der Bot zurück übergeben wird."
  echo "(Nur wenn du sicher bist: denselben Befehl mit --trotzdem am Ende.)"; exit 1
fi
systemctl disable -q --now odingate-bot.timer 2>/dev/null; systemctl stop odingate-bot.service 2>/dev/null
rm -f /etc/systemd/system/odingate-bot.service /etc/systemd/system/odingate-bot.timer
systemctl disable -q --now odingate-live 2>/dev/null
docker rm -f odingate-live >/dev/null 2>&1
docker rmi odingate-live >/dev/null 2>&1
rm -f /etc/systemd/system/odingate-live.service; systemctl daemon-reload
rm -rf /opt/odingate
echo "OdinGate-Live-Dienst entfernt. Den Schlüssel 'odingate-live' bei GitHub (Settings, Deploy keys) bitte ebenfalls löschen."
