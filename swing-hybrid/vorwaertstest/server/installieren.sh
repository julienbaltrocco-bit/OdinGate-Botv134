#!/bin/bash
# Vorwärtstest auf einem Linux-Server (Ubuntu) einrichten: stündlicher Durchlauf per systemd, wie beim Signalbot.
# Aufruf im Ordner swing-hybrid:   bash vorwaertstest/server/installieren.sh
# Kann gefahrlos wiederholt werden. Braucht nur Python 3.10+ (keine weiteren Pakete).
set -euo pipefail
cd "$(dirname "$0")/../.."
ROOT="$PWD"
PY="$(command -v python3)"
"$PY" -c 'import sys; assert sys.version_info >= (3, 10), "Python 3.10 oder neuer nötig"'

# Schlüssel-Datei nur für Stufe „live“. Leer lassen für Stufe „papier“.
ENVF=/etc/vorwaertstest.env
if [ ! -f "$ENVF" ]; then
  sudo tee "$ENVF" >/dev/null <<EOT
# Nur für Stufe "live" ausfüllen (API-Schlüssel mit Handelsrecht, OHNE Auszahlungsrecht):
YUBIT_API_KEY=
YUBIT_API_SECRET=
# Erst auf "ja" setzen, wenn Yubit die IP freigegeben hat und config.json auf "live" steht:
YUBIT_LIVE=nein
EOT
  sudo chmod 600 "$ENVF"
fi

"$PY" -m vorwaertstest.bot selbsttest

sudo tee /etc/systemd/system/vorwaertstest.service >/dev/null <<EOT
[Unit]
Description=Vorwaertstest Yubit (ein Durchlauf)
After=network-online.target

[Service]
Type=oneshot
User=$USER
WorkingDirectory=$ROOT
EnvironmentFile=$ENVF
ExecStart=$PY -m vorwaertstest.bot schritt
EOT
sudo tee /etc/systemd/system/vorwaertstest.timer >/dev/null <<EOT
[Unit]
Description=Vorwaertstest Yubit, stuendlich um :03

[Timer]
OnCalendar=*:03
Persistent=true

[Install]
WantedBy=timers.target
EOT
sudo systemctl daemon-reload
sudo systemctl enable --now vorwaertstest.timer
echo "Eingerichtet. Status: systemctl list-timers vorwaertstest.timer | Bericht: $ROOT/vorwaertstest/daten/bericht.md"
echo "Anhalten: touch $ROOT/vorwaertstest/daten/STOPP"
