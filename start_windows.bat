@echo off
REM Kanalbetriebsdatenbank unter Windows starten (Python 3.10+ muss installiert sein).
REM Optional vorher setzen, z. B. auf einen per OneDrive synchronisierten SharePoint-Ordner:
REM   set KANALDB_IMPORT_DIR=C:\Users\NAME\Firma\Kanalbetrieb - Import
REM   set KANALDB_BACKUP_DIR=C:\Users\NAME\Firma\Kanalbetrieb - Sicherung
cd /d "%~dp0"
if not exist .venv (
  python -m venv .venv
  .venv\Scripts\pip install -r requirements.txt
)
if not exist daten\kanaldb.sqlite (
  echo Erster Start: Beispieldaten Osterholz-Scharmbeck werden geladen ...
  .venv\Scripts\flask --app app demo-laden
)
echo Kanalbetriebsdatenbank laeuft auf http://localhost:8000  (im Netzwerk: http://RECHNERNAME:8000)
.venv\Scripts\waitress-serve --port 8000 app:app
