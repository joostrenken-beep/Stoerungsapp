import csv
import io
from datetime import date

from flask import Blueprint, Response, abort, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from sqlalchemy import or_

from ..dwa149 import gesamtklasse, katalog, klassen_vorschlag, zustand_aktualisieren
from ..extensions import db
from ..formulare import FormFehler, formular_uebernehmen
from ..models import Haltung, Inspektion, Knoten, Schaden, ziel_laden
from . import bearbeiter_noetig, fehler_melden, ziel_oder_404, ziel_url, zurueck
from .betrieb import bezuege

bp = Blueprint("kanal", __name__, url_prefix="/kanal")


def _filter(q, modell):
    f = {k: request.args.get(k, "").strip() for k in ("q", "ortsteil", "kanalart", "zk")}
    if f["q"]:
        q = q.filter(or_(modell.bezeichnung.ilike(f"%{f['q']}%"), modell.strasse.ilike(f"%{f['q']}%")))
    if f["ortsteil"]:
        q = q.filter(modell.ortsteil == f["ortsteil"])
    if f["kanalart"]:
        q = q.filter(modell.kanalart == f["kanalart"])
    if f["zk"] == "keine":
        q = q.filter(modell.zustandsklasse.is_(None))
    elif f["zk"]:
        q = q.filter(modell.zustandsklasse == int(f["zk"]))
    return q, f


def _ortsteile(modell):
    return sorted(o for (o,) in db.session.query(modell.ortsteil).distinct() if o)


@bp.route("/haltungen")
@login_required
def haltungen():
    q, f = _filter(Haltung.query, Haltung)
    if request.args.get("export") == "csv":
        return _csv("haltungen.csv",
                    ["bezeichnung", "von", "bis", "kanalart", "funktion", "ortsteil", "strasse", "laenge", "dn",
                     "material", "baujahr", "sohle_zulauf", "sohle_ablauf", "zustandsklasse", "letzte_inspektion"],
                    ([h.bezeichnung, h.von_knoten.bezeichnung if h.von_knoten else "",
                      h.bis_knoten.bezeichnung if h.bis_knoten else "", h.kanalart, h.funktion, h.ortsteil,
                      h.strasse, h.laenge, h.dn, h.material, h.baujahr, h.sohle_zulauf, h.sohle_ablauf,
                      h.zustandsklasse, h.letzte_inspektion] for h in q.order_by(Haltung.bezeichnung)))
    seite = q.order_by(Haltung.ortsteil, Haltung.strasse, Haltung.bezeichnung).paginate(per_page=50)
    return render_template("kanal/haltungen.html", seite=seite, f=f, ortsteile=_ortsteile(Haltung))


@bp.route("/schaechte")
@login_required
def knotenliste():
    q, f = _filter(Knoten.query, Knoten)
    if request.args.get("art"):
        q = q.filter(Knoten.knotenart == request.args["art"])
    if request.args.get("export") == "csv":
        return _csv("schaechte.csv",
                    ["bezeichnung", "knotenart", "kanalart", "ortsteil", "strasse", "rechtswert", "hochwert",
                     "lat", "lon", "deckelhoehe", "sohlhoehe", "material", "baujahr", "zustandsklasse"],
                    ([k.bezeichnung, k.knotenart, k.kanalart, k.ortsteil, k.strasse, k.rechtswert, k.hochwert,
                      k.lat, k.lon, k.deckelhoehe, k.sohlhoehe, k.material, k.baujahr, k.zustandsklasse]
                     for k in q.order_by(Knoten.bezeichnung)))
    seite = q.order_by(Knoten.ortsteil, Knoten.strasse, Knoten.bezeichnung).paginate(per_page=50)
    return render_template("kanal/knotenliste.html", seite=seite, f=f, ortsteile=_ortsteile(Knoten))


@bp.route("/haltung/<int:id>")
@login_required
def haltung(id):
    h = db.get_or_404(Haltung, id)
    inspektionen = (Inspektion.query.filter_by(ziel_typ="haltung", ziel_id=id)
                    .order_by(Inspektion.datum.desc()).all())
    aktuelle = inspektionen[0] if inspektionen else None
    manuell = Schaden.query.filter_by(ziel_typ="haltung", ziel_id=id, inspektion_id=None).all()
    band = (aktuelle.schaeden if aktuelle else []) + manuell
    return render_template("kanal/haltung.html", h=h, inspektionen=inspektionen, aktuelle=aktuelle,
                           band=band, **bezuege("haltung", id))


@bp.route("/schacht/<int:id>")
@login_required
def knoten(id):
    k = db.get_or_404(Knoten, id)
    zulauf = Haltung.query.filter_by(bis_knoten_id=id).all()
    ablauf = Haltung.query.filter_by(von_knoten_id=id).all()
    inspektionen = (Inspektion.query.filter_by(ziel_typ="knoten", ziel_id=id)
                    .order_by(Inspektion.datum.desc()).all())
    return render_template("kanal/knoten.html", k=k, zulauf=zulauf, ablauf=ablauf, inspektionen=inspektionen,
                           **bezuege("knoten", id))


def _knoten_nach_name(name):
    name = (name or "").strip()
    if not name:
        return None
    k = Knoten.query.filter_by(bezeichnung=name).first()
    if k is None:
        raise FormFehler(f"Schacht „{name}“ existiert nicht")
    return k


@bp.route("/haltung/neu", methods=["GET", "POST"], defaults={"id": None})
@bp.route("/haltung/<int:id>/bearbeiten", methods=["GET", "POST"])
@bearbeiter_noetig
def haltung_bearbeiten(id):
    h = db.get_or_404(Haltung, id) if id else Haltung()
    if request.method == "POST":
        try:
            formular_uebernehmen(h, "haltung", request.form)
            h.von_knoten = _knoten_nach_name(request.form.get("von_knoten"))
            h.bis_knoten = _knoten_nach_name(request.form.get("bis_knoten"))
            if not id:
                db.session.add(h)
            db.session.commit()
            flash("Haltung gespeichert.", "ok")
            return redirect(url_for("kanal.haltung", id=h.id))
        except FormFehler as exc:
            db.session.rollback()
            fehler_melden(exc)
    return render_template("formular.html", typ="haltung", obj=h,
                           titel=f"Haltung {h.bezeichnung}" if id else "Neue Haltung",
                           extra="kanal/_haltung_knoten.html",
                           knotennamen=[n for (n,) in db.session.query(Knoten.bezeichnung).order_by(Knoten.bezeichnung)])


@bp.route("/schacht/neu", methods=["GET", "POST"], defaults={"id": None})
@bp.route("/schacht/<int:id>/bearbeiten", methods=["GET", "POST"])
@bearbeiter_noetig
def knoten_bearbeiten(id):
    k = db.get_or_404(Knoten, id) if id else Knoten()
    if request.method == "POST":
        try:
            formular_uebernehmen(k, "knoten", request.form)
            if not id:
                db.session.add(k)
            db.session.commit()
            flash("Schacht gespeichert.", "ok")
            return redirect(url_for("kanal.knoten", id=k.id))
        except FormFehler as exc:
            db.session.rollback()
            fehler_melden(exc)
    return render_template("formular.html", typ="knoten", obj=k,
                           titel=f"{k.knotenart} {k.bezeichnung}" if id else "Neuer Schacht / Bauwerk")


@bp.route("/<typ>/<int:id>/loeschen", methods=["POST"])
@bearbeiter_noetig
def loeschen(typ, id):
    if not current_user.ist_admin:
        abort(403)
    if typ not in ("haltung", "knoten"):
        abort(404)
    obj = ziel_oder_404(typ, id)
    if typ == "knoten" and Haltung.query.filter(or_(Haltung.von_knoten_id == id, Haltung.bis_knoten_id == id)).count():
        flash("Schacht ist noch Haltungen zugeordnet und kann nicht gelöscht werden.", "fehler")
        return redirect(ziel_url(typ, id))
    for i in Inspektion.query.filter_by(ziel_typ=typ, ziel_id=id):
        db.session.delete(i)
    Schaden.query.filter_by(ziel_typ=typ, ziel_id=id).delete()
    db.session.delete(obj)
    db.session.commit()
    flash("Gelöscht.", "ok")
    return redirect(url_for("kanal.haltungen" if typ == "haltung" else "kanal.knotenliste"))


# ------------------------------------------------------------------ Inspektionen und Schäden

@bp.route("/inspektion/<int:id>")
@login_required
def inspektion(id):
    i = db.get_or_404(Inspektion, id)
    return render_template("kanal/inspektion.html", i=i)


@bp.route("/schaeden")
@login_required
def schaeden():
    q = Schaden.query
    f = {k: request.args.get(k, "").strip() for k in ("kode", "status", "klasse", "ziel_typ")}
    if f["kode"]:
        q = q.filter(Schaden.kode.ilike(f"{f['kode']}%"))
    if f["status"]:
        q = q.filter(Schaden.status == f["status"])
    elif request.args.get("alle") != "1":
        q = q.filter(Schaden.status != "saniert")
    if f["klasse"]:
        q = q.filter(Schaden.schadensklasse <= int(f["klasse"]))
    if f["ziel_typ"]:
        q = q.filter(Schaden.ziel_typ == f["ziel_typ"])
    q = q.order_by(Schaden.schadensklasse.is_(None), Schaden.schadensklasse, Schaden.datum.desc())
    if request.args.get("export") == "csv":
        return _csv("schaeden.csv",
                    ["objektart", "objekt", "datum", "kode", "char1", "char2", "quant1", "quant2", "station",
                     "station_bis", "uhr_von", "uhr_bis", "klasse_d", "klasse_s", "klasse_b", "schadensklasse",
                     "status", "bemerkung"],
                    ([s.ziel_typ, s.ziel.bezeichnung if s.ziel else "", s.datum, s.kode, s.char1, s.char2, s.quant1,
                      s.quant2, s.station, s.station_bis, s.uhr_von, s.uhr_bis, s.klasse_d, s.klasse_s, s.klasse_b,
                      s.schadensklasse, s.status, s.bemerkung] for s in q))
    seite = q.paginate(per_page=50)
    return render_template("kanal/schaeden.html", seite=seite, f=f)


@bp.route("/schaden/<int:id>")
@login_required
def schaden(id):
    s = db.get_or_404(Schaden, id)
    return render_template("kanal/schaden.html", s=s, position=s.position())


@bp.route("/schaden/neu/<ziel_typ>/<int:ziel_id>", methods=["GET", "POST"], defaults={"id": None})
@bp.route("/schaden/<int:id>/bearbeiten", methods=["GET", "POST"], defaults={"ziel_typ": None, "ziel_id": None})
@bearbeiter_noetig
def schaden_bearbeiten(id, ziel_typ, ziel_id):
    if id:
        s = db.get_or_404(Schaden, id)
    else:
        ziel_oder_404(ziel_typ, ziel_id)
        s = Schaden(ziel_typ=ziel_typ, ziel_id=ziel_id, datum=date.today(), erstellt_von=current_user.anzeige)
    if request.method == "POST":
        try:
            formular_uebernehmen(s, "schaden", request.form)
            if all(getattr(s, k) is None for k in ("klasse_d", "klasse_s", "klasse_b")):
                s.klasse_d, s.klasse_s, s.klasse_b = klassen_vorschlag(s.kode, s.char1, s.char2, s.quant1)
                flash("Keine Klassen angegeben – vereinfachter Vorschlag nach DWA-M 149-3 eingetragen, bitte prüfen.",
                      "info")
            s.schadensklasse = gesamtklasse(s.klasse_d, s.klasse_s, s.klasse_b)
            if not id:
                db.session.add(s)
            db.session.flush()
            ziel = ziel_laden(s.ziel_typ, s.ziel_id)
            zustand_aktualisieren(ziel)
            db.session.commit()
            flash("Schaden gespeichert.", "ok")
            return redirect(url_for("kanal.schaden", id=s.id))
        except FormFehler as exc:
            db.session.rollback()
            fehler_melden(exc)
    return render_template("formular.html", typ="schaden", obj=s,
                           titel=f"Schaden {s.kode_voll} – {s.ziel_anzeige}" if id else f"Neuer Schaden – {s.ziel_anzeige}",
                           katalog=katalog())


@bp.route("/schaden/<int:id>/loeschen", methods=["POST"])
@bearbeiter_noetig
def schaden_loeschen(id):
    s = db.get_or_404(Schaden, id)
    ziel = s.ziel
    db.session.delete(s)
    db.session.flush()
    if ziel:
        zustand_aktualisieren(ziel)
    db.session.commit()
    flash("Schaden gelöscht.", "ok")
    return zurueck(url_for("kanal.schaeden"))


@bp.route("/katalog")
@login_required
def kodekatalog():
    return render_template("kanal/katalog.html", katalog=katalog())


def _csv(dateiname, kopf, zeilen):
    puffer = io.StringIO()
    w = csv.writer(puffer, delimiter=";")
    w.writerow(kopf)
    for z in zeilen:
        w.writerow(["" if v is None else (str(v).replace(".", ",") if isinstance(v, float) else v) for v in z])
    return Response("﻿" + puffer.getvalue(), mimetype="text/csv",
                    headers={"Content-Disposition": f"attachment; filename={dateiname}"})
