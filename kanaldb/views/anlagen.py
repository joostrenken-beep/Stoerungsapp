from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from sqlalchemy import or_

from ..extensions import db
from ..formulare import ANLAGENTYPEN, FormFehler, formular_uebernehmen
from ..models import Anlage, Anlagenobjekt, Knoten
from . import bearbeiter_noetig, fehler_melden
from .betrieb import bezuege

bp = Blueprint("anlagen", __name__, url_prefix="/anlagen")


@bp.route("/")
@login_required
def liste():
    q = Anlage.query
    f = {k: request.args.get(k, "").strip() for k in ("q", "typ", "ortsteil")}
    if f["q"]:
        q = q.filter(or_(Anlage.bezeichnung.ilike(f"%{f['q']}%"), Anlage.name.ilike(f"%{f['q']}%"),
                         Anlage.adresse.ilike(f"%{f['q']}%")))
    if f["typ"]:
        q = q.filter(Anlage.anlagentyp == f["typ"])
    if f["ortsteil"]:
        q = q.filter(Anlage.ortsteil == f["ortsteil"])
    ortsteile = sorted(o for (o,) in db.session.query(Anlage.ortsteil).distinct() if o)
    return render_template("anlagen/liste.html", anlagen=q.order_by(Anlage.anlagentyp, Anlage.bezeichnung).all(),
                           f=f, typen=ANLAGENTYPEN, ortsteile=ortsteile)


@bp.route("/<int:id>")
@login_required
def anlage(id):
    a = db.get_or_404(Anlage, id)
    knoten = Knoten.query.filter_by(anlage_id=id).all()
    return render_template("anlagen/anlage.html", a=a, knoten=knoten, **bezuege("anlage", id))


@bp.route("/neu", methods=["GET", "POST"], defaults={"id": None})
@bp.route("/<int:id>/bearbeiten", methods=["GET", "POST"])
@bearbeiter_noetig
def anlage_bearbeiten(id):
    a = db.get_or_404(Anlage, id) if id else Anlage()
    if request.method == "POST":
        try:
            formular_uebernehmen(a, "anlage", request.form)
            if not id:
                db.session.add(a)
            db.session.commit()
            flash("Anlage gespeichert.", "ok")
            return redirect(url_for("anlagen.anlage", id=a.id))
        except FormFehler as exc:
            db.session.rollback()
            fehler_melden(exc)
    return render_template("formular.html", typ="anlage", obj=a,
                           titel=f"{a.anlagentyp} {a.name or a.bezeichnung}" if id else "Neue Anlage")


@bp.route("/<int:id>/loeschen", methods=["POST"])
@bearbeiter_noetig
def anlage_loeschen(id):
    if not current_user.ist_admin:
        abort(403)
    a = db.get_or_404(Anlage, id)
    Knoten.query.filter_by(anlage_id=id).update({"anlage_id": None})
    db.session.delete(a)
    db.session.commit()
    flash("Anlage gelöscht.", "ok")
    return redirect(url_for("anlagen.liste"))


@bp.route("/objekt/<int:id>")
@login_required
def objekt(id):
    o = db.get_or_404(Anlagenobjekt, id)
    return render_template("anlagen/objekt.html", o=o, **bezuege("objekt", id))


@bp.route("/<int:anlage_id>/objekt/neu", methods=["GET", "POST"], defaults={"id": None})
@bp.route("/objekt/<int:id>/bearbeiten", methods=["GET", "POST"], defaults={"anlage_id": None})
@bearbeiter_noetig
def objekt_bearbeiten(id, anlage_id):
    if id:
        o = db.get_or_404(Anlagenobjekt, id)
        anlage = o.anlage
    else:
        anlage = db.get_or_404(Anlage, anlage_id)
        o = Anlagenobjekt(anlage_id=anlage.id)
    if request.method == "POST":
        try:
            formular_uebernehmen(o, "objekt", request.form)
            if not id:
                db.session.add(o)
            db.session.commit()
            flash("Anlagenobjekt gespeichert.", "ok")
            return redirect(url_for("anlagen.objekt", id=o.id))
        except FormFehler as exc:
            db.session.rollback()
            fehler_melden(exc)
    return render_template("formular.html", typ="objekt", obj=o,
                           titel=f"{o.objekttyp} {o.bezeichnung}" if id else
                           f"Neues Objekt in {anlage.name or anlage.bezeichnung}")


@bp.route("/objekt/<int:id>/loeschen", methods=["POST"])
@bearbeiter_noetig
def objekt_loeschen(id):
    if not current_user.ist_admin:
        abort(403)
    o = db.get_or_404(Anlagenobjekt, id)
    anlage_id = o.anlage_id
    db.session.delete(o)
    db.session.commit()
    flash("Objekt gelöscht.", "ok")
    return redirect(url_for("anlagen.anlage", id=anlage_id))
