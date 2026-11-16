#!/usr/bin/env bash
# OdinGate: Papier-Bot für Test 1 und Test 2 auf dem eigenen Server einrichten (nur Simulation, keine Orders, keine Handelsschlüssel).
# Voraussetzung: live/install.sh ist schon gelaufen (Docker-Abbild und Schlüssel vorhanden).
# Der Bot startet im Wartemodus: Er rechnet erst, wenn der Staffelstab (vorwaertstest/betrieb.json im Bot-Zweig) auf "server" steht.
# Bis dahin führt die Claude-Sitzung den Bot weiter. So rechnen nie zwei Stellen gleichzeitig.
set -euo pipefail
ZIEL=/opt/odingate
ZWEIG=claude/intelligent-sagan-2cviug
REPO=git@github.com:julienbaltrocco-bit/OdinGate-Botv134.git
[ "$(id -u)" = 0 ] || { echo "Bitte als root ausführen."; exit 1; }
[ -f "$ZIEL/schluessel/deploy" ] || { echo "Schlüssel fehlt. Bitte zuerst live/install.sh ausführen."; exit 1; }
docker image inspect odingate-live >/dev/null 2>&1 || { echo "Docker-Abbild fehlt. Bitte zuerst live/install.sh ausführen."; exit 1; }
export GIT_SSH_COMMAND="ssh -i $ZIEL/schluessel/deploy -o IdentitiesOnly=yes -o StrictHostKeyChecking=accept-new -o UserKnownHostsFile=$ZIEL/daten/known_hosts -o ConnectTimeout=15"

echo "[1/4] Stand des Bots holen"
if [ -d "$ZIEL/bot/.git" ]; then
  git -C "$ZIEL/bot" fetch -q origin "$ZWEIG" && git -C "$ZIEL/bot" reset -q --hard "origin/$ZWEIG"
else
  git clone -q --depth 50 --single-branch --branch "$ZWEIG" "$REPO" "$ZIEL/bot"
fi
grep -q ODINGATE_BETREIBER "$ZIEL/bot/swing-hybrid/vorwaertstest/stunde.sh" || { echo "Abbruch: Im Bot-Zweig fehlt der Staffelstab. Bitte Claude Bescheid geben."; exit 1; }
[ -f "$ZIEL/bot/swing-hybrid/vorwaertstest/betrieb.json" ] || { echo "Abbruch: betrieb.json fehlt. Bitte Claude Bescheid geben."; exit 1; }

echo "[2/4] Verbindung zu Yubit prüfen (liest nur öffentliche Kurse)"
docker run --rm --cpus 0.5 --memory 300m -v "$ZIEL/bot:/bot" -w /bot/swing-hybrid odingate-live \
  python -m vorwaertstest.bot selbsttest --config vorwaertstest/config_lauf.json 2>&1 | head -12

echo "[3/4] Zeitplan einrichten (alle fünf Minuten: Minute 4, 9, 14, ...)"
cat > "$ZIEL/bot.env" <<ENV
ODINGATE_BETREIBER=server
HOME=/tmp
GIT_SSH_COMMAND=ssh -i /schluessel/deploy -o IdentitiesOnly=yes -o StrictHostKeyChecking=accept-new -o UserKnownHostsFile=/daten/known_hosts -o ConnectTimeout=15
GIT_AUTHOR_NAME=OdinGate Bot (Server)
GIT_AUTHOR_EMAIL=odingate-bot@users.noreply.github.com
GIT_COMMITTER_NAME=OdinGate Bot (Server)
GIT_COMMITTER_EMAIL=odingate-bot@users.noreply.github.com
ENV
cat > /etc/systemd/system/odingate-bot.service <<UNIT
[Unit]
Description=OdinGate Papier-Bot Test 1 und 2 (ein Durchlauf, nur Simulation)
After=docker.service network-online.target
Requires=docker.service

[Service]
Type=oneshot
TimeoutStartSec=270
ExecStartPre=-/usr/bin/docker rm -f odingate-bot
ExecStart=/usr/bin/docker run --rm --name odingate-bot --cpus 0.5 --memory 300m --env-file $ZIEL/bot.env -v $ZIEL/bot:/bot -v $ZIEL/daten:/daten -v $ZIEL/schluessel:/schluessel:ro -w /bot odingate-live bash swing-hybrid/vorwaertstest/stunde.sh
UNIT
cat > /etc/systemd/system/odingate-bot.timer <<UNIT
[Unit]
Description=OdinGate Papier-Bot, alle fünf Minuten

[Timer]
OnCalendar=*:04/5
AccuracySec=5s

[Install]
WantedBy=timers.target
UNIT
systemctl daemon-reload
systemctl enable -q --now odingate-bot.timer

echo "[4/4] Probelauf"
systemctl start odingate-bot.service || true
journalctl -u odingate-bot.service -n 4 --no-pager -o cat | cut -c1-200
echo
echo "=== Fertig. Der Bot steht auf dem Server bereit und wartet. ==="
echo "Steht oben 'Der Bot läuft bei: claude', ist alles richtig: Die Übergabe startet Claude, sobald du Bescheid gibst."
echo "Stand ansehen:  bash $ZIEL/repo/swing-hybrid/forschung/live/status.sh"
