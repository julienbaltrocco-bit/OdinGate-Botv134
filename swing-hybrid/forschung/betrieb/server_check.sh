#!/usr/bin/env bash
# OdinGate: Vorab-Prüfung eines Servers für den Live-Papierhandel. Liest nur, ändert nichts, installiert nichts,
# gibt keine Namen, Adressen oder Dateien des Servers aus. Aufruf siehe forschung/betrieb/BETRIEB.md.
echo "=== OdinGate Server-Prüfung $(date -u '+%F %H:%M') UTC ==="
z() { printf '%-28s %s\n' "$1" "$2"; }
code() { curl -s -o /dev/null -m 12 -w '%{http_code}' "$1" 2>/dev/null || echo "kein Kontakt"; }
z "System" "$( (. /etc/os-release 2>/dev/null && echo "$PRETTY_NAME") || uname -s) / $(uname -m)"
z "Rechenkerne" "$(nproc 2>/dev/null || echo '?')"
z "Arbeitsspeicher frei (MB)" "$(free -m 2>/dev/null | awk '/^Mem/ {print $7 " von " $2}')"
z "Platte frei" "$(df -h / 2>/dev/null | awk 'NR==2 {print $4 " von " $2}')"
z "Auslastung" "$(cut -d' ' -f1-3 /proc/loadavg 2>/dev/null)"
z "Python" "$(python3 --version 2>&1 | head -1) $(python3 -c 'import venv, ssl, sqlite3; print("(venv, ssl, sqlite ok)")' 2>/dev/null || echo '(venv/ssl/sqlite fehlt)')"
z "Git" "$(git --version 2>/dev/null || echo fehlt)"
z "OpenSSL" "$(openssl version 2>/dev/null || echo fehlt)"
z "Docker" "$(docker --version 2>/dev/null || echo 'nicht vorhanden')"
z "Dienste (systemd)" "$(command -v systemctl >/dev/null && echo vorhanden || echo 'nicht vorhanden')"
z "Zeitplan (cron)" "$(command -v crontab >/dev/null && echo vorhanden || echo 'nicht vorhanden')"
z "Benutzer ist root" "$([ "$(id -u)" = 0 ] && echo ja || echo nein)"
z "sudo ohne Passwort" "$(sudo -n true 2>/dev/null && echo ja || echo nein)"
echo "--- Erreichbarkeit (200 = gut, 451 oder 403 = aus diesem Land gesperrt) ---"
z "Binance Futures (live)" "$(code https://fapi.binance.com/fapi/v1/ping)"
z "Binance Kerzen (live)" "$(code 'https://fapi.binance.com/fapi/v1/klines?symbol=BTCUSDT&interval=1m&limit=2')"
z "Binance Datenstrom" "$(code https://fstream.binance.com/)"
z "Binance Archiv" "$(code https://data.binance.vision/)"
z "Yubit" "$(code 'https://openapi.yubit.com/oapi/contract/market/public/v1/tickers?symbol=BTCUSDT')"
z "GitHub" "$(code https://raw.githubusercontent.com/julienbaltrocco-bit/OdinGate-Botv134/claude/alpha-forschung-r1/swing-hybrid/forschung/papier/OS-1.1/plan.md)"
z "Orderbuch-Reichweite BTC" "$(curl -s -m 12 'https://fapi.binance.com/fapi/v1/depth?symbol=BTCUSDT&limit=1000' 2>/dev/null | python3 -c '
import json, sys
try:
    d = json.load(sys.stdin); b, a = d["bids"], d["asks"]
    print("%d Stufen, -%.2f %% bis +%.2f %% um den Kurs" % (len(b) + len(a), (1 - float(b[-1][0]) / float(b[0][0])) * 100, (float(a[-1][0]) / float(a[0][0]) - 1) * 100))
except Exception as e:
    print("nicht lesbar")' 2>/dev/null)"
echo "=== Ende. Bitte diesen Text (oder ein Bildschirmfoto) an Claude schicken. ==="
