from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user

from ..extensions import db
from ..models import Benutzer

bp = Blueprint("auth", __name__)


@bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("start.uebersicht"))
    if request.method == "POST":
        b = Benutzer.query.filter_by(benutzername=request.form.get("benutzername", "").strip().lower()).first()
        if b and b.aktiv and b.check_passwort(request.form.get("passwort", "")):
            login_user(b, remember=bool(request.form.get("merken")))
            weiter = request.args.get("next")
            if weiter and weiter.startswith("/") and not weiter.startswith("//"):
                return redirect(weiter)
            return redirect(url_for("start.uebersicht"))
        flash("Benutzername oder Passwort falsch.", "fehler")
    return render_template("login.html", erster_start=Benutzer.query.count() == 0)


@bp.route("/logout", methods=["POST"])
@login_required
def logout():
    logout_user()
    return redirect(url_for("auth.login"))


@bp.route("/passwort", methods=["GET", "POST"])
@login_required
def passwort():
    if request.method == "POST":
        if not current_user.check_passwort(request.form.get("alt", "")):
            flash("Aktuelles Passwort ist falsch.", "fehler")
        elif len(request.form.get("neu", "")) < 8:
            flash("Das neue Passwort muss mindestens 8 Zeichen haben.", "fehler")
        elif request.form.get("neu") != request.form.get("neu2"):
            flash("Die Passwörter stimmen nicht überein.", "fehler")
        else:
            current_user.set_passwort(request.form["neu"])
            db.session.commit()
            flash("Passwort geändert.", "ok")
            return redirect(url_for("start.uebersicht"))
    return render_template("passwort.html")
