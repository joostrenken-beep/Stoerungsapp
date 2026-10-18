from functools import wraps

from flask import abort, flash, redirect, request, url_for
from flask_login import current_user, login_required

from ..models import ZIEL_KLASSEN, ziel_laden


def bearbeiter_noetig(f):
    @wraps(f)
    @login_required
    def wrapper(*args, **kwargs):
        if not current_user.darf_bearbeiten:
            abort(403)
        return f(*args, **kwargs)
    return wrapper


def admin_noetig(f):
    @wraps(f)
    @login_required
    def wrapper(*args, **kwargs):
        if not current_user.ist_admin:
            abort(403)
        return f(*args, **kwargs)
    return wrapper


DETAIL_ENDPUNKTE = {"haltung": "kanal.haltung", "knoten": "kanal.knoten", "anlage": "anlagen.anlage",
                    "objekt": "anlagen.objekt"}


def ziel_url(ziel_typ, ziel_id):
    if ziel_typ not in DETAIL_ENDPUNKTE or not ziel_id:
        return None
    return url_for(DETAIL_ENDPUNKTE[ziel_typ], id=ziel_id)


def ziel_oder_404(ziel_typ, ziel_id):
    if ziel_typ not in ZIEL_KLASSEN:
        abort(404)
    ziel = ziel_laden(ziel_typ, ziel_id)
    if ziel is None:
        abort(404)
    return ziel


def zurueck(standard):
    ziel = request.form.get("weiter") or request.args.get("weiter")
    if ziel and ziel.startswith("/") and not ziel.startswith("//"):
        return redirect(ziel)
    return redirect(standard)


def fehler_melden(exc):
    flash(str(exc), "fehler")


def registrieren(app):
    from . import anlagen, auth, betrieb, kanal, start, verwaltung
    for modul in (auth, start, kanal, anlagen, betrieb, verwaltung):
        app.register_blueprint(modul.bp)
    app.jinja_env.globals.update(ziel_url=ziel_url)

    @app.errorhandler(403)
    def verboten(_):
        flash("Für diese Aktion fehlt Ihnen die Berechtigung.", "fehler")
        return redirect(request.referrer or url_for("start.uebersicht"))
