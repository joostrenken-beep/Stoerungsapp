import os
import tempfile

from flask import (Blueprint, current_app, flash, redirect, render_template, request, send_from_directory,
                   url_for)
from flask_login import current_user, login_required

from ..automatik import sicherung_erstellen
from ..extensions import db
from ..importer import ENDUNGEN, datei_importieren, ordner_importieren
from ..models import ROLLEN, Benutzer, ImportProtokoll
from . import admin_noetig, bearbeiter_noetig

bp = Blueprint("verwaltung", __name__, url_prefix="/verwaltung")


@bp.route("/import", methods=["GET", "POST"])
@bearbeiter_noetig
def importe():
    if request.method == "POST":
        dateien = [d for d in request.files.getlist("datei") if d and d.filename]
        if not dateien:
            flash("Bitte eine Datei auswählen.", "fehler")
        for d in dateien:
            if not d.filename.lower().endswith(ENDUNGEN):
                flash(f"{d.filename}: nur .xml, .csv oder .xlsx möglich.", "fehler")
                continue
            endung = os.path.splitext(d.filename)[1]
            fd, pfad = tempfile.mkstemp(suffix=endung)
            os.close(fd)
            try:
                d.save(pfad)
                p = datei_importieren(pfad, current_user.anzeige, anzeigename=d.filename)
            finally:
                os.remove(pfad)
            if p.erfolgreich:
                flash(f"{d.filename}: {p.knoten} Schächte, {p.haltungen} Haltungen, {p.inspektionen} Inspektionen, "
                      f"{p.schaeden} Schäden, {p.anlagen} Anlagen importiert.", "ok")
            else:
                flash(f"{d.filename}: Import fehlgeschlagen – siehe Protokoll.", "fehler")
        return redirect(url_for("verwaltung.importe"))
    protokolle = ImportProtokoll.query.order_by(ImportProtokoll.zeitpunkt.desc()).limit(50).all()
    ordner = current_app.config["IMPORT_DIR"]
    wartend = sorted(f for f in os.listdir(ordner) if f.lower().endswith(ENDUNGEN)) if os.path.isdir(ordner) else []
    return render_template("verwaltung/import.html", protokolle=protokolle, ordner=ordner, wartend=wartend,
                           auto=current_app.config["AUTO_IMPORT"],
                           intervall=current_app.config["AUTO_IMPORT_INTERVALL"])


@bp.route("/import/ordner", methods=["POST"])
@bearbeiter_noetig
def ordner_jetzt():
    ergebnisse = ordner_importieren(ausgeloest_von=current_user.anzeige)
    flash(f"{len(ergebnisse)} Datei(en) aus dem Import-Ordner verarbeitet." if ergebnisse
          else "Keine Dateien im Import-Ordner.", "ok" if ergebnisse else "info")
    return redirect(url_for("verwaltung.importe"))


@bp.route("/import/<int:id>")
@login_required
def protokoll(id):
    return render_template("verwaltung/protokoll.html", p=db.get_or_404(ImportProtokoll, id))


@bp.route("/benutzer", methods=["GET", "POST"])
@admin_noetig
def benutzer():
    if request.method == "POST":
        name = request.form.get("benutzername", "").strip().lower()
        pw = request.form.get("passwort", "")
        if not name or len(pw) < 8:
            flash("Benutzername und ein Passwort mit mindestens 8 Zeichen angeben.", "fehler")
        elif Benutzer.query.filter_by(benutzername=name).first():
            flash("Benutzername existiert bereits.", "fehler")
        else:
            b = Benutzer(benutzername=name, name=request.form.get("name") or None,
                         rolle=request.form.get("rolle") if request.form.get("rolle") in ROLLEN else "leser")
            b.set_passwort(pw)
            db.session.add(b)
            db.session.commit()
            flash(f"Benutzer {name} angelegt.", "ok")
        return redirect(url_for("verwaltung.benutzer"))
    return render_template("verwaltung/benutzer.html", benutzer=Benutzer.query.order_by(Benutzer.benutzername).all())


@bp.route("/benutzer/<int:id>", methods=["POST"])
@admin_noetig
def benutzer_aendern(id):
    b = db.get_or_404(Benutzer, id)
    if request.form.get("rolle") in ROLLEN:
        if b.id == current_user.id and request.form["rolle"] != "admin":
            flash("Die eigene Administratorrolle kann nicht entzogen werden.", "fehler")
        else:
            b.rolle = request.form["rolle"]
    if "aktiv" in request.form and b.id != current_user.id:
        b.aktiv = request.form["aktiv"] == "1"
    if request.form.get("passwort"):
        if len(request.form["passwort"]) < 8:
            flash("Passwort zu kurz (mind. 8 Zeichen).", "fehler")
            return redirect(url_for("verwaltung.benutzer"))
        b.set_passwort(request.form["passwort"])
        flash(f"Passwort für {b.benutzername} gesetzt.", "ok")
    db.session.commit()
    return redirect(url_for("verwaltung.benutzer"))


@bp.route("/sicherung", methods=["GET", "POST"])
@admin_noetig
def sicherung():
    ordner = current_app.config["BACKUP_DIR"]
    if request.method == "POST":
        pfad = sicherung_erstellen(current_app._get_current_object())
        flash(f"Sicherung erstellt: {os.path.basename(pfad)}" if pfad
              else "Sicherung nur für SQLite-Datenbanken möglich.", "ok" if pfad else "fehler")
        return redirect(url_for("verwaltung.sicherung"))
    dateien = sorted((f for f in os.listdir(ordner) if f.startswith("kanaldb_")), reverse=True)
    return render_template("verwaltung/sicherung.html", ordner=ordner, dateien=dateien)


@bp.route("/sicherung/<name>")
@admin_noetig
def sicherung_laden(name):
    return send_from_directory(current_app.config["BACKUP_DIR"], name, as_attachment=True)
