#!/usr/bin/env bash
# OdinGate Live-Papierhandel auf einem eigenen Server einrichten. Nur Simulation: keine Orders, keine Handelsschlüssel.
# Legt alles unter /opt/odingate an und startet einen einzelnen, begrenzten Docker-Container (höchstens 0,6 Kerne, 800 MB).
# Andere Programme auf dem Server werden nicht angefasst. Entfernen: bash /opt/odingate/repo/swing-hybrid/forschung/live/entfernen.sh
set -euo pipefail
ZIEL=/opt/odingate
ZWEIG=claude/alpha-forschung-r1
REPO=https://github.com/julienbaltrocco-bit/OdinGate-Botv134.git
[ "$(id -u)" = 0 ] || { echo "Bitte als root ausführen."; exit 1; }
command -v docker >/dev/null || { echo "Docker fehlt."; exit 1; }
command -v git >/dev/null || { echo "Git fehlt."; exit 1; }
echo "[1/5] Ordner und Code"
mkdir -p "$ZIEL/daten" "$ZIEL/schluessel"; chmod 700 "$ZIEL/schluessel"
if [ -d "$ZIEL/repo/.git" ]; then
  git -C "$ZIEL/repo" fetch -q --depth 1 origin "$ZWEIG" && git -C "$ZIEL/repo" reset -q --hard FETCH_HEAD
else
  git clone -q --depth 1 --branch "$ZWEIG" "$REPO" "$ZIEL/repo"
fi
echo "[2/5] Schlüssel für die Veröffentlichung (bleibt auf diesem Server)"
[ -f "$ZIEL/schluessel/deploy" ] || ssh-keygen -q -t ed25519 -N "" -C "odingate-live" -f "$ZIEL/schluessel/deploy"
echo "[3/5] Umgebung bauen (dauert beim ersten Mal zwei bis vier Minuten)"
docker build -q -t odingate-live "$ZIEL/repo/swing-hybrid/forschung/live" >/dev/null
echo "[4/5] Dienst einrichten und starten"
cat > /etc/systemd/system/odingate-live.service <<UNIT
[Unit]
Description=OdinGate Live-Papierhandel (nur Simulation, keine Orders)
After=docker.service network-online.target
Requires=docker.service

[Service]
Restart=always
RestartSec=30
ExecStartPre=-/usr/bin/docker rm -f odingate-live
ExecStart=/usr/bin/docker run --rm --name odingate-live --cpus 0.6 --memory 800m -v $ZIEL/repo:/repo -v $ZIEL/daten:/daten -v $ZIEL/schluessel:/schluessel:ro odingate-live
ExecStop=/usr/bin/docker stop odingate-live

[Install]
WantedBy=multi-user.target
UNIT
systemctl daemon-reload
systemctl enable -q odingate-live
systemctl restart odingate-live
echo "[5/5] Fertig. Der Dienst läuft: $(systemctl is-active odingate-live)"
echo
echo "=== NOCH EIN SCHRITT, damit die Ergebnisse auf dem Board erscheinen ==="
echo "Diese eine Zeile kopieren:"
echo
cat "$ZIEL/schluessel/deploy.pub"
echo
echo "und bei GitHub eintragen: https://github.com/julienbaltrocco-bit/OdinGate-Botv134/settings/keys/new"
echo "  Title: odingate-live   |   Key: die Zeile oben   |   Haken bei 'Allow write access' setzen   |   Add key"
echo
echo "Stand ansehen:  bash $ZIEL/repo/swing-hybrid/forschung/live/status.sh"
