#!/usr/bin/env bash
# Startet den Live-Server, falls er nicht läuft (nur lesend, Port 8765).
cd "$(dirname "$0")/.."
if curl -s -m 3 http://127.0.0.1:8765/api/gesund >/dev/null 2>&1; then echo "Live-Server läuft"; exit 0; fi
nohup setsid python3 -m vorwaertstest.live_server --config vorwaertstest/config_lauf.json --daten vorwaertstest/lauf --port 8765 \
  >/tmp/vorwaertstest_live.log 2>&1 < /dev/null &
sleep 2
curl -s -m 3 http://127.0.0.1:8765/api/gesund >/dev/null 2>&1 && echo "Live-Server gestartet" || { echo "Live-Server startet nicht"; tail -5 /tmp/vorwaertstest_live.log; }
