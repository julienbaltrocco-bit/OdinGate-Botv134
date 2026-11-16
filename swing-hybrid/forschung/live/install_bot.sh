#!/usr/bin/env bash
# OdinGate: Papier-Bot für Test 1 und Test 2 auf dem eigenen Server einrichten (nur Simulation, keine Orders, keine Handelsschlüssel).
# Voraussetzung: live/install.sh ist schon gelaufen (Docker-Abbild und Schlüssel vorhanden).
# Der Bot startet im Wartemodus: Er rechnet erst, wenn der Staffelstab (vorwaertstest/betrieb.json im Bot-Zweig) auf "server" steht.
# Bis dahin führt die Claude-Sitzung den Bot weiter. So rechnen nie zwei Stellen gleichzeitig.
set -euo pipefail
ZIEL=/opt/odingate
ZWEIG=claude/intelligent-sagan-2cviug
FORSCHUNG=claude/alpha-forschung-r1
REPO=git@github.com:julienbaltrocco-bit/OdinGate-Botv134.git
[ "$(id -u)" = 0 ] || { echo "Bitte als root ausführen."; exit 1; }
[ -f "$ZIEL/schluessel/deploy" ] || { echo "Schlüssel fehlt. Bitte zuerst live/install.sh ausführen."; exit 1; }
docker image inspect odingate-live >/dev/null 2>&1 || { echo "Docker-Abbild fehlt. Bitte zuerst live/install.sh ausführen."; exit 1; }
export GIT_SSH_COMMAND="ssh -i $ZIEL/schluessel/deploy -o IdentitiesOnly=yes -o StrictHostKeyChecking=accept-new -o UserKnownHostsFile=$ZIEL/daten/known_hosts -o ConnectTimeout=15"

# Läuft der Bot hier schon (erneute Installation)? Dann erst den Zeitplan anhalten und einen laufenden Durchgang abwarten.
if systemctl cat odingate-bot.timer >/dev/null 2>&1; then
  systemctl stop odingate-bot.timer
  for i in $(seq 1 60); do
    case "$(systemctl show -p ActiveState --value odingate-bot.service)" in activating|deactivating) sleep 5 ;; *) break ;; esac
  done
fi

echo "[1/5] Hilfsskripte auf den neuesten Stand bringen (der Live-Test wird nicht angefasst)"
git -C "$ZIEL/repo" fetch -q --depth 1 origin "$FORSCHUNG"
git -C "$ZIEL/repo" checkout -q FETCH_HEAD -- swing-hybrid/forschung/live/status.sh swing-hybrid/forschung/live/entfernen.sh swing-hybrid/forschung/live/install_bot.sh

echo "[2/5] Stand des Bots holen"
if [ -d "$ZIEL/bot/.git" ]; then
  rm -f "$ZIEL/bot/.git/index.lock"
  git -C "$ZIEL/bot" fetch -q origin "+refs/heads/$ZWEIG:refs/remotes/origin/$ZWEIG"
  git -C "$ZIEL/bot" reset -q --hard "origin/$ZWEIG"
else
  git clone -q --depth 50 --single-branch --branch "$ZWEIG" "$REPO" "$ZIEL/bot"
fi
grep -q ODINGATE_BETREIBER "$ZIEL/bot/swing-hybrid/vorwaertstest/stunde.sh" || { echo "Abbruch: Im Bot-Zweig fehlt der Staffelstab. Bitte Claude Bescheid geben."; exit 1; }
[ -f "$ZIEL/bot/swing-hybrid/vorwaertstest/betrieb.json" ] || { echo "Abbruch: betrieb.json fehlt. Bitte Claude Bescheid geben."; exit 1; }
DRAN=$(python3 -c "import json; print(json.load(open('$ZIEL/bot/swing-hybrid/vorwaertstest/betrieb.json', 'rb'))['betreiber'])")

cat > "$ZIEL/bot.env" <<ENV
ODINGATE_BETREIBER=server
HOME=/tmp
GIT_SSH_COMMAND=ssh -i /schluessel/deploy -o IdentitiesOnly=yes -o StrictHostKeyChecking=accept-new -o UserKnownHostsFile=/daten/known_hosts -o ConnectTimeout=15
GIT_AUTHOR_NAME=OdinGate Bot (Server)
GIT_AUTHOR_EMAIL=odingate-bot@users.noreply.github.com
GIT_COMMITTER_NAME=OdinGate Bot (Server)
GIT_COMMITTER_EMAIL=odingate-bot@users.noreply.github.com
GIT_CONFIG_COUNT=2
GIT_CONFIG_KEY_0=gc.auto
GIT_CONFIG_VALUE_0=0
GIT_CONFIG_KEY_1=maintenance.auto
GIT_CONFIG_VALUE_1=false
ENV
IMCONTAINER="docker run --rm --init --cpus 0.5 --memory 300m --env-file $ZIEL/bot.env -v $ZIEL/bot:/bot -v $ZIEL/daten:/daten -v $ZIEL/schluessel:/schluessel:ro"

echo "[3/5] Verbindungen prüfen (liest nur)"
if ! AUSGABE=$($IMCONTAINER -w /bot/swing-hybrid odingate-live python -m vorwaertstest.bot selbsttest --config vorwaertstest/config_lauf.json 2>&1); then
  echo "$AUSGABE" | tail -15; echo "Abbruch: Der Selbsttest des Bots ist gescheitert. Es wurde nichts eingerichtet."; exit 1
fi
echo "$AUSGABE" | head -12
if echo "$AUSGABE" | grep -q "FEHLER"; then echo "Abbruch: Yubit ist vom Server aus nicht für alle Coins lesbar. Es wurde nichts eingerichtet."; exit 1; fi
if ! $IMCONTAINER -w /bot odingate-live git push -q --dry-run origin "HEAD:$ZWEIG" 2>/tmp/odingate-push.txt; then
  tail -3 /tmp/odingate-push.txt; echo "Abbruch: Der Server kann nicht in das Repository schreiben. Es wurde nichts eingerichtet."; exit 1
fi
echo "  GitHub: Schreibzugriff in Ordnung (nur geprüft, nichts geschrieben)"

echo "[4/5] Zeitplan einrichten (alle fünf Minuten: Minute 4, 9, 14, ...)"
cat > "$ZIEL/bot_vorher.sh" <<VORHER
#!/usr/bin/env bash
# Vor jedem Bot-Lauf, auf dem Server selbst: Reste eines abgebrochenen Laufs entfernen; den Klon erneuern, wenn er zu groß geworden ist.
B=$ZIEL/bot
find "\$B/.git" -name '*.lock' -delete 2>/dev/null
rm -f "\$B/.git/gc.pid"; rm -rf "\$B/.git/rebase-merge" "\$B/.git/rebase-apply"
git -C "\$B" reset -q --hard 2>/dev/null
if [ "\$(du -sm "\$B/.git" 2>/dev/null | cut -f1)" -gt 300 ]; then
  export GIT_SSH_COMMAND="$GIT_SSH_COMMAND"
  rm -rf $ZIEL/bot.neu $ZIEL/bot.alt
  if git clone -q --depth 50 --single-branch --branch "$ZWEIG" "$REPO" $ZIEL/bot.neu; then
    for d in lauf lauf_tpsl; do [ -f "\$B/swing-hybrid/vorwaertstest/\$d/STOPP" ] && touch "$ZIEL/bot.neu/swing-hybrid/vorwaertstest/\$d/STOPP"; done
    mv "\$B" $ZIEL/bot.alt && mv $ZIEL/bot.neu "\$B" && rm -rf $ZIEL/bot.alt
  fi
fi
exit 0
VORHER
chmod +x "$ZIEL/bot_vorher.sh"
cat > /etc/systemd/system/odingate-bot.service <<UNIT
[Unit]
Description=OdinGate Papier-Bot Test 1 und 2 (ein Durchlauf, nur Simulation)
After=docker.service network-online.target
Requires=docker.service

[Service]
Type=oneshot
TimeoutStartSec=270
ExecStartPre=-/usr/bin/docker rm -f odingate-bot
ExecStartPre=-/bin/bash $ZIEL/bot_vorher.sh
ExecStart=/usr/bin/docker run --rm --init --name odingate-bot --cpus 0.5 --memory 300m --env-file $ZIEL/bot.env -v $ZIEL/bot:/bot -v $ZIEL/daten:/daten -v $ZIEL/schluessel:/schluessel:ro -w /bot odingate-live bash swing-hybrid/vorwaertstest/stunde.sh
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

echo "[5/5] Probelauf"
if [ "$DRAN" = server ]; then
  echo "Der Bot rechnet bereits auf diesem Server; der Zeitplan läuft weiter (kein zusätzlicher Probelauf)."
else
  if systemctl start odingate-bot.service; then
    journalctl -u odingate-bot.service -n 3 --no-pager -o cat | cut -c1-200
    echo
    echo "=== Fertig. Der Bot steht auf dem Server bereit und wartet. ==="
    echo "Steht oben 'Der Bot läuft bei: claude', ist alles richtig. Die Übergabe startet Claude, sobald du Bescheid gibst."
  else
    journalctl -u odingate-bot.service -n 8 --no-pager -o cat | cut -c1-200
    echo "=== Der Probelauf ist gescheitert. Bitte diese Ausgabe an Claude schicken; der Bot läuft unverändert in der Claude-Sitzung weiter. ==="
  fi
fi
echo "Serverzeit: $(date -u '+%F %H:%M:%S') UTC"
echo "Stand ansehen:  bash $ZIEL/repo/swing-hybrid/forschung/live/status.sh"
