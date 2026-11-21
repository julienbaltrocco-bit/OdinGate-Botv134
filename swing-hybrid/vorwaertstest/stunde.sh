#!/usr/bin/env bash
# Ein stündlicher Durchlauf des Papier-Vorwärtstests: Stand holen, Schritt rechnen, Dashboard-Daten schreiben, sichern.
set -euo pipefail
ZWEIG=claude/intelligent-sagan-2cviug
cd "$(dirname "$0")/../.."
git fetch -q origin "$ZWEIG" || true
git checkout -q "$ZWEIG" 2>/dev/null || git checkout -q -b "$ZWEIG" "origin/$ZWEIG"
git pull -q --ff-only origin "$ZWEIG" || true
# --- Ab hier neu seit dem Umzug auf einen eigenen Server (16.11.2026). Die acht Zeilen darüber bleiben unverändert.
# Der Stand im Repository gilt. Ist er nicht abrufbar, wird nicht gerechnet (sonst wüsste niemand, wer an der Reihe ist).
# Ein eigener, nicht gesicherter Durchlauf (gescheiterter Push) wird verworfen und beim nächsten Mal neu gerechnet.
WURZEL="$PWD"
git fetch -q origin "+refs/heads/$ZWEIG:refs/remotes/origin/$ZWEIG" || { echo "Stand im Repository nicht abrufbar. Kein Lauf."; exit 1; }
git reset -q --hard "origin/$ZWEIG"
# Staffelstab: Genau eine Stelle führt den Bot (vorwaertstest/betrieb.json). Wer nicht an der Reihe ist, endet ohne Änderung.
ICH="${ODINGATE_BETREIBER:-claude}"
dran() {   # Wer laut Repository an der Reihe ist. Fehlt die Datei oder ist sie unlesbar, gilt "claude".
  python3 -c "import json; print(json.load(open('$WURZEL/swing-hybrid/vorwaertstest/betrieb.json', 'rb'))['betreiber'])" 2>/dev/null || echo claude
}
DRAN=$(dran)
case "$DRAN" in
  claude|server) ;;
  *) echo "betrieb.json nennt einen unbekannten Betreiber ($DRAN). Kein Lauf."; exit 1 ;;
esac
if [ "$DRAN" != "$ICH" ]; then
  echo "Der Bot läuft bei: $DRAN. Dieser Lauf ($ICH) endet ohne Änderung."
  exit 0
fi
if [ "$ICH" = claude ]; then
  ANHANG=$'\n\nCo-Authored-By: Claude Fable 5.2 <noreply@anthropic.com>\nClaude-Session: https://claude.ai/code/session_01Ti9KuBStbgAKmCzGpRA6zL'
else
  ANHANG=$'\n\nAutomatischer Lauf auf dem eigenen Server, ohne KI.'
fi
sichern() {   # Push. Hat sich der Zweig inzwischen bewegt, den eigenen Commit obenauf setzen und erneut versuchen.
  git push -q origin "$ZWEIG" && return 0
  if git pull -q --rebase origin "$ZWEIG"; then
    NEU=$(dran)   # Der Staffelstab kann während dieses Laufs gewechselt haben: dann wird der Lauf verworfen, nicht gesichert.
    if [ "$NEU" != "$ICH" ]; then
      git reset -q --hard "origin/$ZWEIG"
      echo "Der Staffelstab liegt jetzt bei: $NEU. Dieser Lauf ($ICH) wird nicht gesichert."
      exit 0
    fi
    git push -q origin "$ZWEIG" && return 0
  fi
  git rebase --abort 2>/dev/null || true
  echo "Sichern gescheitert. Der Durchlauf wird beim nächsten Mal neu gerechnet."
  return 1
}
cd swing-hybrid
python3 -m vorwaertstest.bot schritt --config vorwaertstest/config_lauf.json --daten vorwaertstest/lauf
python3 -m vorwaertstest.dashboard_daten --config vorwaertstest/config_lauf.json --daten vorwaertstest/lauf
python3 -m vorwaertstest.board_verschluesseln --quelle vorwaertstest/lauf/dashboard.json --ziel ../docs/stand.enc.json
git add vorwaertstest/lauf ../docs/stand.enc.json
git diff --cached --quiet || git commit -q -m "Vorwärtstest (Papier) $(date -u '+%F %H:%M') UTC$ANHANG"
sichern
echo "gesichert: $(git rev-parse --short HEAD)"


# Zweites, getrenntes Papier-Konto: dieselbe Regel mit Stop 5 % und Gewinnziel 15 % (Start 15.11.2026)
python3 -m vorwaertstest.bot schritt --config vorwaertstest/config_lauf_tpsl.json --daten vorwaertstest/lauf_tpsl
python3 -m vorwaertstest.dashboard_daten --config vorwaertstest/config_lauf_tpsl.json --daten vorwaertstest/lauf_tpsl
python3 -m vorwaertstest.board_verschluesseln --quelle vorwaertstest/lauf_tpsl/dashboard.json --ziel ../docs/stand_tpsl.enc.json
git add vorwaertstest/lauf_tpsl ../docs/stand_tpsl.enc.json
git diff --cached --quiet || git commit -q -m "Vorwärtstest (Papier, Stop 5 % / Ziel 15 %) $(date -u '+%F %H:%M') UTC$ANHANG"
sichern
echo "gesichert (Variante): $(git rev-parse --short HEAD)"


# Drittes, getrenntes Papier-Konto (Test 3): dieselbe Regel mit nachgezogenem Stop 5 %. Einstiege von Test 1;
# der Abschnitt bis "nachgerechnet_bis" in der Einstellung wurde aus den Aufzeichnungen von Test 1 nachgerechnet.
python3 -m vorwaertstest.bot schritt --config vorwaertstest/config_lauf_trail.json --daten vorwaertstest/lauf_trail
python3 -m vorwaertstest.dashboard_daten --config vorwaertstest/config_lauf_trail.json --daten vorwaertstest/lauf_trail
python3 -m vorwaertstest.board_verschluesseln --quelle vorwaertstest/lauf_trail/dashboard.json --ziel ../docs/stand_trail.enc.json
git add vorwaertstest/lauf_trail ../docs/stand_trail.enc.json
git diff --cached --quiet || git commit -q -m "Vorwärtstest (Papier, nachgezogener Stop 5 %) $(date -u '+%F %H:%M') UTC$ANHANG"
sichern
echo "gesichert (Test 3): $(git rev-parse --short HEAD)"


# Viertes, getrenntes Papier-Konto (Test 4): dieselbe Regel wie Test 1, aber die Richtung wird je Coin nur einmal am Tag
# übernommen (Stundenschluss 00:00 UTC). Einstiege von Test 1; der Abschnitt bis "nachgerechnet_bis" in der Einstellung
# wurde aus den Aufzeichnungen von Test 1 nachgerechnet. Läuft zuletzt: Scheitert er, sind Test 1 bis 3 schon gesichert.
# Ohne den nachgerechneten Stand wird nicht gerechnet (sonst begänne ein neues Konto mit Einstiegen von jetzt). Dauerhaft
# anhalten: die Datei vorwaertstest/lauf_tag/ANGEHALTEN ins Repository legen (eine STOPP-Datei auf dem Server übersteht das
# Erneuern des Klons dort nicht).
if [ ! -f vorwaertstest/lauf_tag/zustand.json ]; then
  echo "Test 4: kein Stand vorhanden (vorwaertstest/lauf_tag/zustand.json fehlt). Kein Durchgang."
elif [ -f vorwaertstest/lauf_tag/ANGEHALTEN ]; then
  echo "Test 4 ist angehalten (vorwaertstest/lauf_tag/ANGEHALTEN im Repository). Kein Durchgang."
else
  python3 -m vorwaertstest.bot schritt --config vorwaertstest/config_lauf_tag.json --daten vorwaertstest/lauf_tag
  python3 -m vorwaertstest.dashboard_daten --config vorwaertstest/config_lauf_tag.json --daten vorwaertstest/lauf_tag
  python3 -m vorwaertstest.board_verschluesseln --quelle vorwaertstest/lauf_tag/dashboard.json --ziel ../docs/stand_tag.enc.json
  git add vorwaertstest/lauf_tag ../docs/stand_tag.enc.json
  git diff --cached --quiet || git commit -q -m "Vorwärtstest (Papier, Tagesregel) $(date -u '+%F %H:%M') UTC$ANHANG"
  sichern
  echo "gesichert (Test 4): $(git rev-parse --short HEAD)"
fi
