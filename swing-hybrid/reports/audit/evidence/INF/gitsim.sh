#!/usr/bin/env bash
# INF: "Git als Datenspeicher" in einer Sandbox nachgestellt.
#  - "origin" ist ein eigenes Bare-Repo im Scratch-Verzeichnis, kein Netz, kein Zugriff auf das echte Repo ausser lesend (git show).
#  - stunde.sh wird als UNVERAENDERTE Kopie aus der git-Historie des echten Repos ausgefuehrt (Vergleich per cmp).
#  - Die drei Python-Module (bot, dashboard_daten, board_verschluesseln) sind Stellvertreter, die nur Laeufe zaehlen.
#    Geprueft wird ausschliesslich die Git-Logik des Skripts.
# Aufruf: bash gitsim.sh <echtes-repo> <scratch-ordner> <stub-ordner>
set -u
REPO=$1; S=$2; STUBS=$3
Z=claude/intelligent-sagan-2cviug
export GIT_CONFIG_GLOBAL=/dev/null GIT_CONFIG_SYSTEM=/dev/null PYTHONDONTWRITEBYTECODE=1
export GIT_AUTHOR_NAME=sim GIT_AUTHOR_EMAIL=sim@example.invalid GIT_COMMITTER_NAME=sim GIT_COMMITTER_EMAIL=sim@example.invalid
unset GIT_DIR GIT_WORK_TREE
case "$S" in /tmp/*) ;; *) echo "Scratch-Ordner muss unter /tmp liegen"; exit 2;; esac

neu() {   # $1 Szenario, $2 Commit, aus dem stunde.sh stammt, $3 "mitschluessel" oder "ohneschluessel"
  SZ=$1; rm -rf "$S/$SZ"; mkdir -p "$S/$SZ"; cd "$S/$SZ" || exit 2
  git init -q --bare -b "$Z" origin.git
  git init -q -b "$Z" seed; cd seed || exit 2
  git remote add origin ../origin.git
  mkdir -p swing-hybrid/vorwaertstest docs
  git -C "$REPO" show "$2:swing-hybrid/vorwaertstest/stunde.sh" > swing-hybrid/vorwaertstest/stunde.sh
  cp "$STUBS"/bot.py "$STUBS"/dashboard_daten.py "$STUBS"/board_verschluesseln.py swing-hybrid/vorwaertstest/
  : > swing-hybrid/vorwaertstest/__init__.py
  echo '{}' > swing-hybrid/vorwaertstest/config_lauf.json; echo '{}' > swing-hybrid/vorwaertstest/config_lauf_tpsl.json
  [ "$3" = mitschluessel ] && echo PLATZHALTER > swing-hybrid/vorwaertstest/board_pub.pem
  echo "# Platzhalter" > docs/index.html
  git add -A; git commit -q -m "Ausgangsstand"; git push -q origin "$Z"
  cd ..; git clone -q origin.git runner; git clone -q origin.git dev
  echo; echo "################ Szenario $SZ (stunde.sh aus Commit $2)"
}
lauf() {  # $1 Beschriftung; weitere Argumente: Umgebungsvariablen fuer den Lauf
  local text=$1; shift
  ( cd "$S/$SZ" && env INF_WER=runner "$@" bash runner/swing-hybrid/vorwaertstest/stunde.sh ) > "$S/$SZ/aus.txt" 2>&1
  local rc=$?
  echo "--- $text: Rueckgabewert $rc"
  sed 's/^/      | /' "$S/$SZ/aus.txt" | grep -v "^      | $" | cut -c1-230 | head -12
}
zeilen() { if [ -f "$1" ]; then wc -l < "$1" | tr -d ' '; else echo 0; fi; }
status() {
  cd "$S/$SZ" || exit 2
  git -C runner fetch -q origin 2>/dev/null
  local l r ab
  l=$(git -C runner rev-parse --short HEAD); r=$(git -C origin.git rev-parse --short "$Z" 2>/dev/null)
  ab=$(git -C runner rev-list --left-right --count "HEAD...origin/$Z" 2>/dev/null | tr '\t' '/')
  echo "    Stand: Runner-HEAD $l | origin $r | Runner voraus/zurueck $ab"
  echo "    stand.csv Test 1: lokal $(zeilen runner/swing-hybrid/vorwaertstest/lauf/stand.csv) Zeilen, auf origin $(git -C origin.git show "$Z:swing-hybrid/vorwaertstest/lauf/stand.csv" 2>/dev/null | wc -l | tr -d ' ')" \
       "| Test 2: lokal $(zeilen runner/swing-hybrid/vorwaertstest/lauf_tpsl/stand.csv), auf origin $(git -C origin.git show "$Z:swing-hybrid/vorwaertstest/lauf_tpsl/stand.csv" 2>/dev/null | wc -l | tr -d ' ')"
  local dirty; dirty=$(git -C runner status --short | grep -v __pycache__ | tr '\n' ';')
  [ -n "$dirty" ] && echo "    Runner: nicht gesicherte Aenderungen: $dirty"
}

echo "Gepruefter Stand des echten Repos: $(git -C "$REPO" log -1 --format='%h %cI')"
git -C "$REPO" show HEAD:swing-hybrid/vorwaertstest/stunde.sh | cmp -s - "$REPO/swing-hybrid/vorwaertstest/stunde.sh" && echo "stunde.sh im Arbeitsverzeichnis == stunde.sh in HEAD (cmp: gleich)"

# ---------------------------------------------------------------- S1: fremder Commit im Zeitfenster zwischen pull und push
neu s1_fremder_commit HEAD mitschluessel
cmp -s "$S/$SZ/runner/swing-hybrid/vorwaertstest/stunde.sh" "$REPO/swing-hybrid/vorwaertstest/stunde.sh" && echo "Kopie von stunde.sh ist byte-gleich mit dem Original"
lauf "Lauf 1 (ungestoert)"; lauf "Lauf 2 (ungestoert)"; status
cat > "$S/$SZ/fremd.sh" <<EOF
cd "$S/$SZ/dev" && git pull -q origin "$Z" && echo "Notiz \$(date -u +%T)" >> docs/notiz.md && git add docs/notiz.md \
  && git commit -q -m "Fremder Commit auf dem Zweig (z. B. Entwickler- oder Audit-Sitzung)" && git push -q origin "$Z" && echo "[fremder Commit gepusht]"
EOF
touch "$S/$SZ/marke"
lauf "Lauf 3 (waehrend des Laufs pusht ein anderer Klon einen Commit)" INF_HAKEN="$S/$SZ/fremd.sh" INF_MARKE="$S/$SZ/marke"; status
lauf "Lauf 4 (ungestoert)"; status
lauf "Lauf 5 (ungestoert)"; status
git clone -q origin.git neuer_container
echo "    Frischer Klon (z. B. neue KI-Sitzung nach Verlust des Runners): stand.csv Test 1 hat $(zeilen neuer_container/swing-hybrid/vorwaertstest/lauf/stand.csv) Zeilen, zustand.json: $(cat neuer_container/swing-hybrid/vorwaertstest/lauf/zustand.json) ; im Runner: $(cat runner/swing-hybrid/vorwaertstest/lauf/zustand.json)"

# ---------------------------------------------------------------- S2: origin nicht erreichbar
neu s2_netzausfall HEAD mitschluessel
lauf "Lauf 1 (ungestoert)"; status
mv "$S/$SZ/origin.git" "$S/$SZ/origin.weg"
lauf "Lauf 2 (origin nicht erreichbar)"
mv "$S/$SZ/origin.weg" "$S/$SZ/origin.git"; status
lauf "Lauf 3 (origin wieder da)"; status

# ---------------------------------------------------------------- S3: Verschluesselungsschritt scheitert (wie 13:49 bis 14:55 UTC)
neu s3_schluessel_fehlt HEAD ohneschluessel
lauf "Lauf 1 (board_pub.pem fehlt im Runner)"; status
lauf "Lauf 2 (board_pub.pem fehlt im Runner)"; status

# ---------------------------------------------------------------- S4: Skript aendert sich waehrend des eigenen Laufs (wie 13:44 UTC)
neu s4_selbstaenderung 360fa1b mitschluessel
lauf "Lauf 1 (alte Fassung: kopiert Klartext nach docs/stand.json)"
echo "    docs/ auf origin: $(git -C "$S/$SZ/origin.git" ls-tree --name-only "$Z" docs/ | tr '\n' ' ')"
( cd "$S/$SZ/dev" && git pull -q origin "$Z" && git -C "$REPO" show 1695511:swing-hybrid/vorwaertstest/stunde.sh > swing-hybrid/vorwaertstest/stunde.sh \
  && git rm -q docs/stand.json && echo verschluesselt > docs/stand.enc.json && git add -A \
  && git commit -q -m "Wie 1695511: Stand nur noch verschluesselt, docs/stand.json geloescht, stunde.sh umgestellt" && git push -q origin "$Z" )
echo "    Entwickler-Klon hat die neue Fassung gepusht. docs/ auf origin: $(git -C "$S/$SZ/origin.git" ls-tree --name-only "$Z" docs/ | tr '\n' ' ')"
lauf "Lauf 2 (Runner startet die alte Datei, pull ersetzt sie waehrend des Laufs)"
echo "    docs/ auf origin nach Lauf 2: $(git -C "$S/$SZ/origin.git" ls-tree --name-only "$Z" docs/ | tr '\n' ' ')"
echo "    stunde.sh im Runner ist jetzt die neue Fassung: $(grep -c board_verschluesseln "$S/$SZ/runner/swing-hybrid/vorwaertstest/stunde.sh") Treffer fuer board_verschluesseln"
echo "    letzter Commit auf origin: $(git -C "$S/$SZ/origin.git" log -1 --format='%s' "$Z" | head -1) | geaenderte Dateien: $(git -C "$S/$SZ/origin.git" show --name-only --format= "$Z" | tr '\n' ' ')"

# ---------------------------------------------------------------- S5: git commit scheitert, Skript meldet trotzdem "gesichert"
neu s5_commit_scheitert HEAD mitschluessel
lauf "Lauf 1 (ungestoert)"; status
printf '#!/bin/sh\necho "pre-commit: simulierter Fehler (z. B. Signatur nicht moeglich)" >&2\nexit 1\n' > "$S/$SZ/runner/.git/hooks/pre-commit"; chmod +x "$S/$SZ/runner/.git/hooks/pre-commit"
lauf "Lauf 2 (git commit scheitert)"; status
