#!/bin/bash
# Einrichtung bzw. Aktualisierung der Kanalbetriebsdatenbank auf PythonAnywhere.
#
# Voraussetzung: Im Reiter "Web" wurde bereits eine Web-App mit
# "Manual configuration" angelegt. Aufruf in einer Bash-Konsole:
#
#   git clone -b claude/kanalbetriebsdatenbank-anlagen-spyt98 https://github.com/joostrenken-beep/Stoerungsapp.git ; bash Stoerungsapp/pythonanywhere_einrichten.sh
#
# Erneutes Ausführen holt den neuesten Stand und lässt vorhandene Daten unverändert.
set -e

REPO="$HOME/Stoerungsapp"
DATEN="$HOME/kanaldb_daten"
BRANCH="claude/kanalbetriebsdatenbank-anlagen-spyt98"

echo "== Kanalbetriebsdatenbank – Einrichtung auf PythonAnywhere =="

WSGI=$(ls /var/www/*_wsgi.py 2>/dev/null | head -n 1 || true)
if [ -z "$WSGI" ]; then
  echo
  echo "FEHLER: Es gibt noch keine Web-App."
  echo "Bitte zuerst im Reiter 'Web' auf 'Add a new web app' tippen,"
  echo "'Manual configuration' und die höchste angebotene Python-Version wählen."
  echo "Danach diesen Befehl erneut ausführen."
  exit 1
fi

if [ -d "$REPO/.git" ]; then
  echo "-- Programm aktualisieren"
  git -C "$REPO" fetch -q origin "$BRANCH"
  git -C "$REPO" checkout -q "$BRANCH"
  git -C "$REPO" reset -q --hard "origin/$BRANCH"
else
  echo "-- Programm herunterladen"
  git clone -q -b "$BRANCH" https://github.com/joostrenken-beep/Stoerungsapp.git "$REPO"
fi

PYTHONS=""
for v in 3.13 3.12 3.11 3.10; do
  if command -v "python$v" >/dev/null 2>&1; then PYTHONS="$PYTHONS $v"; fi
done
if [ -z "$PYTHONS" ]; then
  echo "FEHLER: Kein Python 3.10 oder neuer gefunden."
  exit 1
fi
for v in $PYTHONS; do
  echo "-- Pakete für Python $v installieren (dauert 1–2 Minuten)"
  "python$v" -m pip install -q --user --upgrade --no-cache-dir -r "$REPO/requirements.txt"
done
PY="python$(echo $PYTHONS | cut -d' ' -f1)"

mkdir -p "$DATEN"
cd "$REPO"
export KANALDB_DATA_DIR="$DATEN"
export KANALDB_AUTO_IMPORT=0

if [ ! -f "$DATEN/kanaldb.sqlite" ]; then
  echo
  echo "-- Beispielnetz Osterholz-Scharmbeck laden"
  PW=""
  while [ ${#PW} -lt 8 ]; do
    read -r -p "Passwort für die Benutzer admin/betrieb/gast (mind. 8 Zeichen): " PW
  done
  KANALDB_DEMO_PASSWORT="$PW" "$PY" -m flask --app app demo-laden --nur-wenn-leer
else
  echo "-- Vorhandene Datenbank bleibt erhalten"
fi

echo "-- Web-App konfigurieren ($WSGI)"
cat > "$WSGI" <<EOF
# Automatisch erzeugt von pythonanywhere_einrichten.sh
import os
import sys

os.environ["KANALDB_DATA_DIR"] = "$DATEN"
os.environ["KANALDB_AUTO_IMPORT"] = "0"  # Hintergrund-Threads sind auf PythonAnywhere nicht vorgesehen
sys.path.insert(0, "$REPO")

from app import app as application  # noqa: E402
EOF

ADRESSE=$(basename "$WSGI" _wsgi.py | sed "s/^${USER}_/${USER}./; s/_/./g")
echo
echo "== Fertig =="
echo "1. Im Reiter 'Web' oben auf den grünen Knopf 'Reload' tippen."
echo "2. Danach https://$ADRESSE öffnen und mit 'admin' anmelden."
echo
echo "Optional – tägliche Datensicherung im Reiter 'Tasks' eintragen:"
echo "  cd $REPO && KANALDB_DATA_DIR=$DATEN $PY -m flask --app app sicherung"
