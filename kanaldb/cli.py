import click

from .extensions import db
from .models import ROLLEN, Benutzer


def registrieren(app):
    @app.cli.command("benutzer-anlegen")
    @click.argument("benutzername")
    @click.option("--name", default=None, help="Anzeigename")
    @click.option("--rolle", type=click.Choice(list(ROLLEN)), default="admin")
    @click.password_option()
    def benutzer_anlegen(benutzername, name, rolle, password):
        """Legt einen Benutzer an (oder setzt dessen Passwort neu)."""
        b = Benutzer.query.filter_by(benutzername=benutzername.lower()).first()
        if b is None:
            b = Benutzer(benutzername=benutzername.lower())
            db.session.add(b)
        b.name, b.rolle = name or b.name, rolle
        b.set_passwort(password)
        db.session.commit()
        click.echo(f"Benutzer {b.benutzername} ({rolle}) gespeichert.")

    @app.cli.command("import-ordner")
    @click.argument("ordner", required=False)
    def import_ordner(ordner):
        """Importiert alle Dateien aus dem Import-Ordner (z. B. per Aufgabenplanung)."""
        from .importer import ordner_importieren
        for p in ordner_importieren(ordner, ausgeloest_von="Kommandozeile"):
            status = "OK" if p.erfolgreich else "FEHLER"
            click.echo(f"{status} {p.datei}: {p.knoten} Knoten, {p.haltungen} Haltungen, "
                       f"{p.inspektionen} Inspektionen, {p.schaeden} Schäden")

    @app.cli.command("import-datei")
    @click.argument("pfad", type=click.Path(exists=True, dir_okay=False))
    def import_datei(pfad):
        """Importiert eine einzelne XML-/CSV-/XLSX-Datei."""
        from .importer import datei_importieren
        p = datei_importieren(pfad, "Kommandozeile")
        click.echo(("OK" if p.erfolgreich else "FEHLER") + f" {p.datei} ({p.format}): {p.knoten} Knoten, "
                   f"{p.haltungen} Haltungen, {p.inspektionen} Inspektionen, {p.schaeden} Schäden")
        if p.meldungen:
            click.echo(p.meldungen)

    @app.cli.command("sicherung")
    def sicherung():
        """Erstellt eine Datenbanksicherung im Sicherungsordner."""
        from flask import current_app

        from .automatik import sicherung_erstellen
        click.echo(sicherung_erstellen(current_app) or "Nur für SQLite möglich.")

    @app.cli.command("demo-dateien")
    @click.argument("ordner", default="demo")
    def demo_dateien(ordner):
        """Schreibt die Beispiel-Importdateien (Osterholz-Scharmbeck) in einen Ordner."""
        from .demo import dateien_schreiben
        for pfad in dateien_schreiben(ordner):
            click.echo(f"geschrieben: {pfad}")

    @app.cli.command("demo-laden")
    @click.option("--admin-passwort", default="kanal2026", show_default=True)
    def demo_laden(admin_passwort):
        """Lädt das fiktive Beispielnetz Osterholz-Scharmbeck (über den regulären Import)."""
        from .demo import laden
        for zeile in laden(admin_passwort):
            click.echo(zeile)
