import json
from datetime import date, timedelta

from flask import Blueprint, current_app, jsonify, render_template, request, url_for
from flask_login import login_required
from sqlalchemy import func, or_

from ..dwa149 import kode_text
from ..extensions import db
from ..geo import punkt_auf_linie
from ..models import (Anlage, Anlagenobjekt, Haltung, ImportProtokoll, Inspektion, Knoten, Schaden,
                      Stoermeldung, Wartungsplan)
from . import ziel_url

bp = Blueprint("start", __name__)

PRIO_REIHENFOLGE = {"kritisch": 0, "hoch": 1, "mittel": 2, "niedrig": 3}


@bp.route("/")
@login_required
def uebersicht():
    heute = date.today()
    kennzahlen = {
        "haltungen": Haltung.query.count(),
        "laenge_km": (db.session.query(func.sum(Haltung.laenge)).scalar() or 0) / 1000,
        "knoten": Knoten.query.count(),
        "anlagen": Anlage.query.count(),
        "objekte": Anlagenobjekt.query.count(),
        "schaeden_offen": Schaden.query.filter(Schaden.status != "saniert").count(),
    }
    laengen = dict(db.session.query(Haltung.kanalart, func.sum(Haltung.laenge)).group_by(Haltung.kanalart).all())
    zk = dict(db.session.query(Haltung.zustandsklasse, func.count(Haltung.id)).group_by(Haltung.zustandsklasse).all())
    stoerungen = sorted(Stoermeldung.query.filter(Stoermeldung.status != "behoben").all(),
                        key=lambda s: (PRIO_REIHENFOLGE.get(s.prioritaet, 9), s.gemeldet_am))
    wartungen = (Wartungsplan.query.filter(Wartungsplan.aktiv.is_(True),
                                           Wartungsplan.naechste_faelligkeit <= heute + timedelta(days=30))
                 .order_by(Wartungsplan.naechste_faelligkeit).limit(15).all())
    importe = ImportProtokoll.query.order_by(ImportProtokoll.zeitpunkt.desc()).limit(5).all()
    return render_template("uebersicht.html", k=kennzahlen, laengen=laengen, zk=zk, stoerungen=stoerungen[:10],
                           anzahl_stoerungen=len(stoerungen), wartungen=wartungen, importe=importe, heute=heute)


@bp.route("/karte")
@login_required
def karte():
    ortsteile = sorted(o for (o,) in db.session.query(Haltung.ortsteil).distinct() if o)
    return render_template("karte.html", ortsteile=ortsteile, zentrum=current_app.config["KARTE_ZENTRUM"])


def _feature(geometrie, eigenschaften):
    return {"type": "Feature", "geometry": geometrie, "properties": eigenschaften}


def _punkt(p):
    return {"type": "Point", "coordinates": [round(p[1], 7), round(p[0], 7)]}


@bp.route("/api/geo/<ebene>")
@login_required
def geo(ebene):
    ortsteil = request.args.get("ortsteil") or None
    kanalart = request.args.get("kanalart") or None
    features = []
    knoten_pos = {k.id: (k.lat, k.lon) for k in Knoten.query.with_entities(Knoten.id, Knoten.lat, Knoten.lon)
                  if k.lat is not None}

    def haltung_koordinaten(h):
        if h.geometrie:
            try:
                return json.loads(h.geometrie)
            except ValueError:
                pass
        a, b = knoten_pos.get(h.von_knoten_id), knoten_pos.get(h.bis_knoten_id)
        return [list(a), list(b)] if a and b else []

    if ebene == "haltungen":
        q = Haltung.query
        if ortsteil:
            q = q.filter_by(ortsteil=ortsteil)
        if kanalart:
            q = q.filter_by(kanalart=kanalart)
        for h in q:
            koord = haltung_koordinaten(h)
            if len(koord) < 2:
                continue
            features.append(_feature(
                {"type": "LineString", "coordinates": [[round(p[1], 7), round(p[0], 7)] for p in koord]},
                {"id": h.id, "bez": h.bezeichnung, "kanalart": h.kanalart, "zk": h.zustandsklasse,
                 "funktion": h.funktion, "dn": h.dn, "material": h.material, "strasse": h.strasse,
                 "laenge": h.laenge, "url": url_for("kanal.haltung", id=h.id)}))
    elif ebene == "knoten":
        q = Knoten.query.filter(Knoten.lat.isnot(None))
        if ortsteil:
            q = q.filter_by(ortsteil=ortsteil)
        if kanalart:
            q = q.filter_by(kanalart=kanalart)
        for k in q:
            features.append(_feature(_punkt((k.lat, k.lon)), {
                "id": k.id, "bez": k.bezeichnung, "art": k.knotenart, "kanalart": k.kanalart,
                "zk": k.zustandsklasse, "url": url_for("kanal.knoten", id=k.id)}))
    elif ebene == "anlagen":
        q = Anlage.query.filter(Anlage.lat.isnot(None))
        if ortsteil:
            q = q.filter_by(ortsteil=ortsteil)
        offene = dict(db.session.query(Stoermeldung.ziel_id, func.count(Stoermeldung.id))
                      .filter(Stoermeldung.ziel_typ == "anlage", Stoermeldung.status != "behoben")
                      .group_by(Stoermeldung.ziel_id).all())
        for a in q:
            features.append(_feature(_punkt((a.lat, a.lon)), {
                "id": a.id, "bez": a.name or a.bezeichnung, "typ": a.anlagentyp, "kanalart": a.kanalart,
                "stoerungen": offene.get(a.id, 0), "url": url_for("anlagen.anlage", id=a.id)}))
    elif ebene == "schaeden":
        q = Schaden.query
        if request.args.get("alle") != "1":
            q = q.filter(Schaden.status != "saniert")
        if request.args.get("max_klasse"):
            q = q.filter(Schaden.schadensklasse <= int(request.args["max_klasse"]))
        haltungen = {h.id: h for h in Haltung.query}
        gegen = {i.id: i.gegen_fliessrichtung for i in Inspektion.query}
        for s in q:
            p = None
            if s.lat is not None:
                p = (s.lat, s.lon)
            elif s.ziel_typ == "haltung" and s.ziel_id in haltungen:
                h = haltungen[s.ziel_id]
                if (ortsteil and h.ortsteil != ortsteil) or (kanalart and h.kanalart != kanalart):
                    continue
                koord = haltung_koordinaten(h)
                anteil = (s.station or 0) / h.laenge if h.laenge else 0.5
                if gegen.get(s.inspektion_id):
                    anteil = 1 - anteil
                p = punkt_auf_linie(koord, anteil)
            elif s.ziel is not None:
                if ortsteil and getattr(s.ziel, "ortsteil", None) != ortsteil:
                    continue
                p = s.ziel.position()
            if not p:
                continue
            features.append(_feature(_punkt(p), {
                "id": s.id, "kode": s.kode_voll, "text": kode_text(s.kode, s.char1, s.char2),
                "klasse": s.schadensklasse, "station": s.station, "objekt": s.ziel_anzeige,
                "status": s.status, "url": url_for("kanal.schaden", id=s.id)}))
    elif ebene == "stoerungen":
        q = Stoermeldung.query
        if request.args.get("alle") != "1":
            q = q.filter(Stoermeldung.status != "behoben")
        for s in q:
            p = s.position()
            if not p:
                continue
            features.append(_feature(_punkt(p), {
                "id": s.id, "titel": s.titel, "prioritaet": s.prioritaet, "status": s.status,
                "objekt": s.ziel_anzeige, "datum": s.gemeldet_am.strftime("%d.%m.%Y %H:%M"),
                "url": url_for("betrieb.stoerung", id=s.id)}))
    else:
        return jsonify({"fehler": "unbekannte Ebene"}), 404
    return jsonify({"type": "FeatureCollection", "features": features})


def _suchen(text, grenze=25):
    muster = f"%{text}%"
    treffer = []
    for h in Haltung.query.filter(or_(Haltung.bezeichnung.ilike(muster), Haltung.strasse.ilike(muster))).limit(grenze):
        treffer.append(("Haltung", h.bezeichnung, f"{h.strasse or ''} · {h.ortsteil or ''}", "haltung", h))
    for k in Knoten.query.filter(or_(Knoten.bezeichnung.ilike(muster), Knoten.strasse.ilike(muster))).limit(grenze):
        treffer.append((k.knotenart, k.bezeichnung, f"{k.strasse or ''} · {k.ortsteil or ''}", "knoten", k))
    for a in Anlage.query.filter(or_(Anlage.bezeichnung.ilike(muster), Anlage.name.ilike(muster),
                                     Anlage.adresse.ilike(muster))).limit(grenze):
        treffer.append((a.anlagentyp, a.name or a.bezeichnung, a.adresse or "", "anlage", a))
    for o in Anlagenobjekt.query.filter(or_(Anlagenobjekt.bezeichnung.ilike(muster),
                                            Anlagenobjekt.seriennummer.ilike(muster))).limit(grenze):
        treffer.append((o.objekttyp, o.bezeichnung, o.anlage.name or o.anlage.bezeichnung, "objekt", o))
    return treffer


@bp.route("/suche")
@login_required
def suche():
    text = request.args.get("q", "").strip()
    treffer = _suchen(text) if len(text) >= 2 else []
    return render_template("suche.html", text=text, treffer=treffer)


@bp.route("/api/suche")
@login_required
def api_suche():
    text = request.args.get("q", "").strip()
    if len(text) < 2:
        return jsonify([])
    ergebnis = []
    for art, bez, info, typ, obj in _suchen(text, 10):
        p = obj.position()
        ergebnis.append({"art": art, "bez": bez, "info": info, "typ": typ, "id": obj.id,
                         "url": ziel_url(typ, obj.id), "lat": p[0] if p else None, "lon": p[1] if p else None})
    return jsonify(ergebnis)
