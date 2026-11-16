#!/usr/bin/env bash
# Entfernt den OdinGate-Live-Dienst vollständig von diesem Server (Dienst, Container, Abbild, Ordner /opt/odingate).
set -u
[ "$(id -u)" = 0 ] || { echo "Bitte als root ausführen."; exit 1; }
systemctl disable -q --now odingate-live 2>/dev/null
docker rm -f odingate-live >/dev/null 2>&1
docker rmi odingate-live >/dev/null 2>&1
rm -f /etc/systemd/system/odingate-live.service; systemctl daemon-reload
rm -rf /opt/odingate
echo "OdinGate-Live-Dienst entfernt. Den Schlüssel 'odingate-live' bei GitHub (Settings, Deploy keys) bitte ebenfalls löschen."
