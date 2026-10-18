import os
import uuid
from calendar import monthrange
from datetime import date, datetime, timedelta

from flask import (Blueprint, abort, current_app, flash, redirect, render_template, request, send_from_directory,
                   url_for)
from flask_login import current_user, login_required
from werkzeug.utils import secure_filename

from ..extensions import db
from ..formulare import FormFehler, formular_uebernehmen
from ..models import (Anlage, Dokument, Haltung, Knoten, Massnahme, Schaden, Stoermeldung,
                      Wartungsplan, jetzt)
from . import bearbeiter_noetig, fehler_melden, ziel_oder_404, ziel_url, zurueck

bp = Blueprint("betrieb", __name__)


def bezuege(ziel_typ, ziel_id):
    """Alle betrieblichen Datensätze zu einem Objekt (für die Detailseiten)."""
    filt = {"ziel_typ": ziel_typ, "ziel_id": ziel_id}
    return {
        "ziel_typ": ziel_typ,
        "ziel_id": ziel_id,
        "wartungsplaene": Wartungsplan.query.filter_by(**filt).order_by(Wartungsplan.naechste_faelligkeit).all(),
        "massnahmen": Massnahme.query.filter_by(**filt).order_by(Massnahme.datum.desc()).limit(50).all(),
        "stoerungen": Stoermeldung.query.filter_by(**filt).order_by(Stoermeldung.gemeldet_am.desc()).limit(50).all(),
        "dokumente": Dokument.query.filter_by(**filt).order_by(Dokument.hochgeladen_am.desc()).all(),
        "schaeden_alle": Schaden.query.filter_by(**filt).order_by(Schaden.datum.desc(), Schaden.station).all(),
    }


def monate_addieren(d, monate):
    m = d.month - 1 + monate
    jahr, monat = d.year + m // 12, m % 12 + 1
    return date(jahr, monat, min(d.day, monthrange(jahr, monat)[1]))


# ------------------------------------------------------------------ Wartung

@bp.route("/wartung")
@login_required
def wartung():
    heute = date.today()
    tage = int(request.args.get("tage", 60))
    plaene = (Wartungsplan.query.filter(Wartungsplan.aktiv.is_(True))
              .filter(Wartungsplan.naechste_faelligkeit <= heute + timedelta(days=tage))
              .order_by(Wartungsplan.naechste_faelligkeit).all())
    ohne_termin = Wartungsplan.query.filter(Wartungsplan.aktiv.is_(True),
                                            Wartungsplan.naechste_faelligkeit.is_(None)).all()
    letzte = Massnahme.query.order_by(Massnahme.datum.desc(), Massnahme.id.desc()).limit(25).all()
    return render_template("betrieb/wartung.html", plaene=plaene, ohne_termin=ohne_termin, letzte=letzte,
                           tage=tage, heute=heute)


@bp.route("/wartung/plaene")
@login_required
def wartungsplaene():
    plaene = Wartungsplan.query.order_by(Wartungsplan.naechste_faelligkeit.is_(None),
                                         Wartungsplan.naechste_faelligkeit).all()
    return render_template("betrieb/wartungsplaene.html", plaene=plaene, heute=date.today())


@bp.route("/wartung/plan/neu/<ziel_typ>/<int:ziel_id>", methods=["GET", "POST"], defaults={"id": None})
@bp.route("/wartung/plan/<int:id>/bearbeiten", methods=["GET", "POST"], defaults={"ziel_typ": None, "ziel_id": None})
@bearbeiter_noetig
def plan_bearbeiten(id, ziel_typ, ziel_id):
    if id:
        p = db.get_or_404(Wartungsplan, id)
    else:
        ziel_oder_404(ziel_typ, ziel_id)
        p = Wartungsplan(ziel_typ=ziel_typ, ziel_id=ziel_id, aktiv=True)
    if request.method == "POST":
        try:
            formular_uebernehmen(p, "wartungsplan", request.form)
            if p.naechste_faelligkeit is None and p.letzte_durchfuehrung and p.intervall_monate:
                p.naechste_faelligkeit = monate_addieren(p.letzte_durchfuehrung, p.intervall_monate)
            if not id:
                db.session.add(p)
            db.session.commit()
            flash("Wartungsplan gespeichert.", "ok")
            return redirect(ziel_url(p.ziel_typ, p.ziel_id))
        except FormFehler as exc:
            db.session.rollback()
            fehler_melden(exc)
    return render_template("formular.html", typ="wartungsplan", obj=p,
                           titel=("Wartungsplan bearbeiten – " if id else "Neuer Wartungsplan – ") + p.ziel_anzeige)


@bp.route("/wartung/plan/<int:id>/loeschen", methods=["POST"])
@bearbeiter_noetig
def plan_loeschen(id):
    p = db.get_or_404(Wartungsplan, id)
    ziel = ziel_url(p.ziel_typ, p.ziel_id)
    Massnahme.query.filter_by(wartungsplan_id=id).update({"wartungsplan_id": None})
    db.session.delete(p)
    db.session.commit()
    flash("Wartungsplan gelöscht.", "ok")
    return redirect(ziel or url_for("betrieb.wartung"))


@bp.route("/wartung/erfassen/<ziel_typ>/<int:ziel_id>", methods=["GET", "POST"], defaults={"id": None})
@bp.route("/wartung/massnahme/<int:id>/bearbeiten", methods=["GET", "POST"], defaults={"ziel_typ": None, "ziel_id": None})
@bearbeiter_noetig
def massnahme_bearbeiten(id, ziel_typ, ziel_id):
    if id:
        m = db.get_or_404(Massnahme, id)
    else:
        ziel_oder_404(ziel_typ, ziel_id)
        m = Massnahme(ziel_typ=ziel_typ, ziel_id=ziel_id, datum=date.today(),
                      durchgefuehrt_von=current_user.anzeige, erstellt_von=current_user.anzeige)
        plan_id = request.args.get("plan", type=int)
        if plan_id:
            plan = db.get_or_404(Wartungsplan, plan_id)
            m.wartungsplan, m.art, m.beschreibung = plan, plan.art, plan.beschreibung
    if request.method == "POST":
        try:
            formular_uebernehmen(m, "massnahme", request.form)
            if not id:
                db.session.add(m)
            plan = m.wartungsplan
            if plan and (plan.letzte_durchfuehrung is None or m.datum >= plan.letzte_durchfuehrung):
                plan.letzte_durchfuehrung = m.datum
                plan.naechste_faelligkeit = monate_addieren(m.datum, plan.intervall_monate)
            db.session.commit()
            flash("Maßnahme dokumentiert." + (f" Nächste Fälligkeit: {plan.naechste_faelligkeit:%d.%m.%Y}"
                                              if plan else ""), "ok")
            return zurueck(ziel_url(m.ziel_typ, m.ziel_id))
        except FormFehler as exc:
            db.session.rollback()
            fehler_melden(exc)
    titel = (f"{m.wartungsplan.bezeichnung} – " if m.wartungsplan else "Maßnahme – ") + m.ziel_anzeige
    return render_template("formular.html", typ="massnahme", obj=m, titel=titel)


# ------------------------------------------------------------------ Störmeldungen

@bp.route("/stoerungen")
@login_required
def stoerungen():
    q = Stoermeldung.query
    f = {k: request.args.get(k, "").strip() for k in ("status", "prioritaet", "q")}
    if f["status"] == "alle":
        pass
    elif f["status"]:
        q = q.filter(Stoermeldung.status == f["status"])
    else:
        q = q.filter(Stoermeldung.status != "behoben")
    if f["prioritaet"]:
        q = q.filter(Stoermeldung.prioritaet == f["prioritaet"])
    if f["q"]:
        q = q.filter(Stoermeldung.titel.ilike(f"%{f['q']}%"))
    seite = q.order_by(Stoermeldung.gemeldet_am.desc()).paginate(per_page=50)
    return render_template("betrieb/stoerungen.html", seite=seite, f=f)


@bp.route("/stoerung/<int:id>")
@login_required
def stoerung(id):
    s = db.get_or_404(Stoermeldung, id)
    return render_template("betrieb/stoerung.html", s=s, position=s.position(),
                           dokumente=Dokument.query.filter_by(ziel_typ="stoerung", ziel_id=id).all())


def _ziel_aus_formular(s):
    auswahl = request.form.get("ziel", "")
    kanal = request.form.get("kanalobjekt", "").strip()
    if kanal:
        obj = Haltung.query.filter_by(bezeichnung=kanal).first() or Knoten.query.filter_by(bezeichnung=kanal).first()
        if obj is None:
            raise FormFehler(f"Haltung/Schacht „{kanal}“ nicht gefunden")
        s.ziel_typ, s.ziel_id = obj.ZIEL_TYP, obj.id
    elif ":" in auswahl:
        typ, zid = auswahl.split(":", 1)
        ziel_oder_404(typ, zid)
        s.ziel_typ, s.ziel_id = typ, int(zid)
    elif "ziel" in request.form:
        s.ziel_typ = s.ziel_id = None
    s.__dict__.pop("_ziel_cache", None)


@bp.route("/stoerung/neu", methods=["GET", "POST"], defaults={"id": None})
@bp.route("/stoerung/<int:id>/bearbeiten", methods=["GET", "POST"])
@bearbeiter_noetig
def stoerung_bearbeiten(id):
    if id:
        s = db.get_or_404(Stoermeldung, id)
    else:
        s = Stoermeldung(gemeldet_am=jetzt(), gemeldet_von=current_user.anzeige, status="offen",
                         prioritaet="mittel", erstellt_von=current_user.anzeige)
        if request.args.get("ziel_typ"):
            ziel_oder_404(request.args["ziel_typ"], request.args.get("ziel_id"))
            s.ziel_typ, s.ziel_id = request.args["ziel_typ"], request.args.get("ziel_id", type=int)
    if request.method == "POST":
        try:
            formular_uebernehmen(s, "stoermeldung", request.form)
            _ziel_aus_formular(s)
            if s.gemeldet_am is None:
                s.gemeldet_am = jetzt()
            if s.status == "behoben" and not s.behoben_am:
                s.behoben_am = jetzt()
            if not id:
                db.session.add(s)
            db.session.commit()
            _foto_speichern("stoerung", s.id)
            flash("Störmeldung gespeichert.", "ok")
            return redirect(url_for("betrieb.stoerung", id=s.id))
        except FormFehler as exc:
            db.session.rollback()
            fehler_melden(exc)
    anlagen = Anlage.query.order_by(Anlage.anlagentyp, Anlage.bezeichnung).all()
    return render_template("formular.html", typ="stoermeldung", obj=s,
                           titel=f"Störmeldung #{s.id}" if id else "Neue Störmeldung",
                           extra="betrieb/_stoer_ziel.html", anlagen=anlagen, foto_upload=True)


@bp.route("/stoerung/<int:id>/status", methods=["POST"])
@bearbeiter_noetig
def stoerung_status(id):
    s = db.get_or_404(Stoermeldung, id)
    neu = request.form.get("status")
    if neu not in ("offen", "in Bearbeitung", "behoben"):
        abort(400)
    s.status = neu
    if neu == "in Bearbeitung" and not s.bearbeiter:
        s.bearbeiter = current_user.anzeige
    if neu == "behoben":
        s.behoben_am = s.behoben_am or jetzt()
        if s.ausfallzeit_h is None and s.gemeldet_am:
            s.ausfallzeit_h = round((s.behoben_am - s.gemeldet_am).total_seconds() / 3600, 1)
    db.session.commit()
    flash(f"Status: {neu}", "ok")
    return zurueck(url_for("betrieb.stoerung", id=id))


# ------------------------------------------------------------------ Dokumente / Fotos

ERLAUBT = {"pdf", "jpg", "jpeg", "png", "gif", "webp", "heic", "doc", "docx", "xls", "xlsx", "csv", "txt",
           "dwg", "dxf", "xml", "zip", "mp4", "mov"}


def _foto_speichern(ziel_typ, ziel_id, feld="foto"):
    gespeichert = 0
    for datei in request.files.getlist(feld):
        if not datei or not datei.filename:
            continue
        endung = datei.filename.rsplit(".", 1)[-1].lower() if "." in datei.filename else ""
        if endung not in ERLAUBT:
            flash(f"Dateityp .{endung} nicht erlaubt: {datei.filename}", "fehler")
            continue
        speichername = f"{uuid.uuid4().hex}.{endung}"
        datei.save(os.path.join(current_app.config["UPLOAD_DIR"], speichername))
        db.session.add(Dokument(ziel_typ=ziel_typ, ziel_id=ziel_id, dateiname=secure_filename(datei.filename) or
                                speichername, speichername=speichername,
                                beschreibung=request.form.get("dok_beschreibung") or None,
                                hochgeladen_von=current_user.anzeige))
        gespeichert += 1
    if gespeichert:
        db.session.commit()
    return gespeichert


@bp.route("/dokumente/<ziel_typ>/<int:ziel_id>", methods=["POST"])
@bearbeiter_noetig
def dokument_hochladen(ziel_typ, ziel_id):
    if ziel_typ == "stoerung":
        db.get_or_404(Stoermeldung, ziel_id)
    else:
        ziel_oder_404(ziel_typ, ziel_id)
    anzahl = _foto_speichern(ziel_typ, ziel_id, "datei")
    if anzahl:
        flash(f"{anzahl} Datei(en) hochgeladen.", "ok")
    return zurueck(ziel_url(ziel_typ, ziel_id) or url_for("betrieb.stoerung", id=ziel_id))


@bp.route("/dokument/<int:id>")
@login_required
def dokument(id):
    d = db.get_or_404(Dokument, id)
    return send_from_directory(current_app.config["UPLOAD_DIR"], d.speichername, download_name=d.dateiname,
                               as_attachment=not d.ist_bild and not d.dateiname.lower().endswith(".pdf"))


@bp.route("/dokument/<int:id>/loeschen", methods=["POST"])
@bearbeiter_noetig
def dokument_loeschen(id):
    d = db.get_or_404(Dokument, id)
    try:
        os.remove(os.path.join(current_app.config["UPLOAD_DIR"], d.speichername))
    except OSError:
        pass
    db.session.delete(d)
    db.session.commit()
    flash("Datei gelöscht.", "ok")
    return zurueck(url_for("start.uebersicht"))


@bp.app_template_global()
def objekt_auswahl():
    """Anlagen und Anlagenobjekte für Auswahllisten."""
    return [(a, a.objekte) for a in Anlage.query.order_by(Anlage.anlagentyp, Anlage.bezeichnung)]


@bp.app_template_filter("seit")
def seit(wert):
    if not wert:
        return "–"
    delta = datetime.now() - wert
    if delta.days >= 1:
        return f"seit {delta.days} Tag{'en' if delta.days > 1 else ''}"
    stunden = delta.seconds // 3600
    return f"seit {stunden} h" if stunden else f"seit {delta.seconds // 60} min"


@bp.app_context_processor
def _anzahl_offen():
    if not current_user.is_authenticated:
        return {}
    return {"offene_stoerungen": Stoermeldung.query.filter(Stoermeldung.status != "behoben").count()}

