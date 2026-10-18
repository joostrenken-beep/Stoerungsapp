"""Hintergrundaufgaben: automatischer Import aus dem Import-Ordner und tägliche Sicherung.

Der Import-Ordner kann ein per OneDrive synchronisierter SharePoint-Ordner sein:
Wer dort eine ISYBAU-/DWA-Datei ablegt, findet sie nach wenigen Minuten in der
Datenbank. Läuft die Anwendung in mehreren Prozessen, sorgt eine Sperrdatei dafür,
dass nur einer importiert.
"""
import logging
import os
import sqlite3
import threading
import time
from datetime import date

log = logging.getLogger("kanaldb.automatik")
_gestartet = False
_sperre = threading.Lock()


def sicherung_erstellen(app, behalten=14):
    uri = app.config["SQLALCHEMY_DATABASE_URI"]
    if not uri.startswith("sqlite:///"):
        return None
    quelle = uri.replace("sqlite:///", "", 1)
    ziel = os.path.join(app.config["BACKUP_DIR"], f"kanaldb_{date.today():%Y-%m-%d}.sqlite")
    src = sqlite3.connect(quelle)
    dst = sqlite3.connect(ziel)
    with dst:
        src.backup(dst)
    src.close()
    dst.close()
    alte = sorted(f for f in os.listdir(app.config["BACKUP_DIR"]) if f.startswith("kanaldb_"))
    for f in alte[:-behalten]:
        os.remove(os.path.join(app.config["BACKUP_DIR"], f))
    return ziel


def _prozesssperre(app):
    try:
        import fcntl
    except ImportError:  # Windows: keine Sperre, ein Prozess empfohlen
        return True
    datei = open(os.path.join(app.config["DATA_DIR"], ".automatik.lock"), "w")
    try:
        fcntl.flock(datei, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        datei.close()
        return False
    app.extensions["kanaldb_lock"] = datei
    return True


def _schleife(app):
    from .importer import ordner_importieren
    letzte_sicherung = None
    while True:
        try:
            with app.app_context():
                for p in ordner_importieren():
                    log.info("Import %s: %s", p.datei, "ok" if p.erfolgreich else "Fehler")
                if letzte_sicherung != date.today():
                    sicherung_erstellen(app)
                    letzte_sicherung = date.today()
        except Exception:
            log.exception("Fehler im automatischen Import")
        time.sleep(app.config["AUTO_IMPORT_INTERVALL"])


def starten(app):
    """Startet den Hintergrund-Thread beim ersten Seitenaufruf (nicht bei CLI-Befehlen)."""

    @app.before_request
    def _automatik_starten():
        global _gestartet
        if _gestartet:
            return
        with _sperre:
            if _gestartet:
                return
            _gestartet = True
            if _prozesssperre(app):
                threading.Thread(target=_schleife, args=(app,), daemon=True, name="kanaldb-import").start()
