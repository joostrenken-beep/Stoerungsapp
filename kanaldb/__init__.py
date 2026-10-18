"""Kanalbetriebsdatenbank – Kanalnetz, Sonderbauwerke, Wartung, Schäden und Störmeldungen."""
import os
import secrets

from flask import Flask, abort, request, session

from .extensions import db, login_manager


def _secret_key(data_dir):
    if os.environ.get("KANALDB_SECRET_KEY"):
        return os.environ["KANALDB_SECRET_KEY"]
    pfad = os.path.join(data_dir, ".secret_key")
    if not os.path.exists(pfad):
        with open(pfad, "w") as f:
            f.write(secrets.token_hex(32))
    with open(pfad) as f:
        return f.read().strip()


def create_app(test_config=None):
    app = Flask(__name__)
    data_dir = os.path.abspath(os.environ.get("KANALDB_DATA_DIR", os.path.join(os.getcwd(), "daten")))
    app.config.update(
        DATA_DIR=data_dir,
        SQLALCHEMY_DATABASE_URI=os.environ.get("KANALDB_DATABASE_URL")
        or "sqlite:///" + os.path.join(data_dir, "kanaldb.sqlite"),
        UPLOAD_DIR=os.path.join(data_dir, "dokumente"),
        IMPORT_DIR=os.path.abspath(os.environ.get("KANALDB_IMPORT_DIR", os.path.join(data_dir, "import"))),
        BACKUP_DIR=os.path.abspath(os.environ.get("KANALDB_BACKUP_DIR", os.path.join(data_dir, "sicherung"))),
        AUTO_IMPORT=os.environ.get("KANALDB_AUTO_IMPORT", "1") == "1",
        AUTO_IMPORT_INTERVALL=int(os.environ.get("KANALDB_AUTO_IMPORT_INTERVALL", "300")),
        UTM_ZONE=int(os.environ.get("KANALDB_UTM_ZONE", "32")),
        KARTE_ZENTRUM=(53.2265, 8.7950),
        MAX_CONTENT_LENGTH=200 * 1024 * 1024,
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
    )
    if test_config:
        app.config.update(test_config)
    for ordner in ("DATA_DIR", "UPLOAD_DIR", "IMPORT_DIR", "BACKUP_DIR"):
        os.makedirs(app.config[ordner], exist_ok=True)
    app.config.setdefault("SECRET_KEY", None)
    if not app.config["SECRET_KEY"]:
        app.config["SECRET_KEY"] = _secret_key(data_dir)

    db.init_app(app)
    login_manager.init_app(app)

    from . import models  # noqa: F401  (Tabellen registrieren)

    @login_manager.user_loader
    def benutzer_laden(benutzer_id):
        return db.session.get(models.Benutzer, int(benutzer_id))

    @app.before_request
    def csrf_pruefen():
        if request.method == "POST" and not app.config.get("TESTING_OHNE_CSRF"):
            token = session.get("csrf_token")
            if not token or token != (request.form.get("csrf_token") or request.headers.get("X-CSRF-Token")):
                abort(400, "Sicherheitstoken ungültig – bitte Seite neu laden.")

    def csrf_token():
        if "csrf_token" not in session:
            session["csrf_token"] = secrets.token_hex(16)
        return session["csrf_token"]

    from .dwa149 import ZUSTANDSKLASSEN, kode_text
    from .formulare import FELDER
    from .models import KANALARTEN, ROLLEN, ZIEL_NAMEN

    app.jinja_env.globals.update(csrf_token=csrf_token, ZUSTANDSKLASSEN=ZUSTANDSKLASSEN, kode_text=kode_text,
                                 KANALARTEN=KANALARTEN, ROLLEN=ROLLEN, ZIEL_NAMEN=ZIEL_NAMEN, FELDER=FELDER)

    @app.template_filter("de")
    def format_de(wert, stellen=2):
        if wert is None or wert == "":
            return "–"
        if hasattr(wert, "strftime"):
            return wert.strftime("%d.%m.%Y %H:%M" if hasattr(wert, "hour") else "%d.%m.%Y")
        if isinstance(wert, float):
            return f"{wert:,.{stellen}f}".replace(",", "X").replace(".", ",").replace("X", ".")
        return wert

    from .views import registrieren
    registrieren(app)

    from .cli import registrieren as cli_registrieren
    cli_registrieren(app)

    with app.app_context():
        db.create_all()

    if app.config["AUTO_IMPORT"] and not app.config.get("TESTING"):
        from .automatik import starten
        starten(app)
    return app
