import io
import os
from datetime import date

import pytest

from kanaldb import create_app
from kanaldb.dwa149 import klassen_vorschlag, kode_text
from kanaldb.extensions import db
from kanaldb.geo import gk_nach_wgs84, nach_wgs84, utm_nach_wgs84, wgs84_nach_utm
from kanaldb.importer import isybau
from kanaldb.views.betrieb import monate_addieren
from kanaldb.models import Anlage, Haltung, Inspektion, Knoten, Schaden, Stoermeldung, Wartungsplan


@pytest.fixture(scope="module")
def app(tmp_path_factory):
    tmp = tmp_path_factory.mktemp("daten")
    os.environ["KANALDB_DATA_DIR"] = str(tmp)
    app = create_app({"TESTING": True, "TESTING_OHNE_CSRF": True, "AUTO_IMPORT": False,
                      "SECRET_KEY": "test"})
    with app.app_context():
        from kanaldb.demo import laden
        meldungen = laden("testpasswort")
        assert not any(m.startswith("FEHLER") for m in meldungen), meldungen
    yield app


def anmelden(client, name="admin"):
    r = client.post("/login", data={"benutzername": name, "passwort": "testpasswort"})
    assert r.status_code == 302


@pytest.fixture
def client(app):
    c = app.test_client()
    anmelden(c)
    return c


def test_koordinaten_hin_und_zurueck():
    e, n = wgs84_nach_utm(53.2265, 8.795)
    lat, lon = utm_nach_wgs84(e, n)
    assert abs(lat - 53.2265) < 1e-7 and abs(lon - 8.795) < 1e-7
    assert nach_wgs84(32_000_000 + e, n) == pytest.approx((53.2265, 8.795), abs=1e-7)
    # Gauß-Krüger Streifen 3: Abweichung zu UTM nach Datumsübergang nur wenige Meter
    lat_gk, lon_gk = gk_nach_wgs84(3489000.0, 5900000.0)
    assert 53.2 < lat_gk < 53.25 and 8.8 < lon_gk < 8.86


def test_dwa_katalog_und_klassen():
    assert kode_text("BAB", "B", "A") == "Rissbildung, Riss, längs"
    assert "(Schacht)" in kode_text("DAB")
    assert klassen_vorschlag("BBF", "C") == (1, None, None)
    assert klassen_vorschlag("BBA", "B", None, "60")[2] == 1


def test_demo_daten_vollstaendig(app):
    with app.app_context():
        assert Haltung.query.count() > 900
        assert Knoten.query.filter_by(knotenart="Auslaufbauwerk").count() >= 10
        assert Anlage.query.filter_by(anlagentyp="Pumpwerk").count() == 8
        ka = Anlage.query.filter_by(anlagentyp="Kläranlage").one()
        assert ka.name == "Kläranlage Lintel"
        # Alle Schmutzwasser-Freispiegelhaltungen haben Anfangs- und Endschacht
        assert Haltung.query.filter(Haltung.von_knoten_id.is_(None)).count() == 0
        assert Haltung.query.filter_by(funktion="Druckleitung").count() == 8
        # Streckenschäden (A1/B1) wurden zusammengeführt, Info-Kodes nicht als Schaden übernommen
        assert Schaden.query.filter(Schaden.station_bis.isnot(None)).count() > 0
        assert Schaden.query.filter(Schaden.kode.in_(["BCD", "BCE", "BCA"])).count() == 0
        assert Haltung.query.filter(Haltung.zustandsklasse.isnot(None)).count() > 300
        assert Stoermeldung.query.filter(Stoermeldung.status != "behoben").count() == 6
        assert Wartungsplan.query.count() > 50


def test_regenwasser_endet_in_gewaesser(app):
    """Jede RW-Haltung führt über Ablaufhaltungen zu einem Auslaufbauwerk."""
    with app.app_context():
        ablauf = {h.von_knoten_id: h.bis_knoten_id for h in Haltung.query.filter_by(kanalart="RW")}
        art = {k.id: k.knotenart for k in Knoten.query.filter_by(kanalart="RW")}
        for start in ablauf:
            k, schritte = start, 0
            while k in ablauf and schritte < 500:
                k, schritte = ablauf[k], schritte + 1
            assert art[k] == "Auslaufbauwerk"


def test_schmutzwasser_endet_in_klaeranlage(app):
    with app.app_context():
        ablauf = {h.von_knoten_id: h.bis_knoten_id for h in Haltung.query.filter_by(kanalart="SW")}
        ka = Knoten.query.filter_by(bezeichnung="KA-LINTEL-ZUL").one().id
        for start in ablauf:
            k, schritte = start, 0
            while k in ablauf and schritte < 1000:
                k, schritte = ablauf[k], schritte + 1
            assert k == ka


def test_seiten_erreichbar(app, client):
    with app.app_context():
        h = Haltung.query.join(Inspektion, (Inspektion.ziel_id == Haltung.id) & (Inspektion.ziel_typ == "haltung")).first()
        k = Knoten.query.first()
        a = Anlage.query.filter_by(anlagentyp="Pumpwerk").first()
        o = a.objekte[0]
        s = Schaden.query.first()
        st = Stoermeldung.query.first()
        i = Inspektion.query.first()
        p = Wartungsplan.query.first()
    urls = ["/", "/karte", "/kanal/haltungen", "/kanal/haltungen?ortsteil=Kernstadt&zk=2", "/kanal/schaechte",
            f"/kanal/haltung/{h.id}", f"/kanal/schacht/{k.id}", f"/kanal/inspektion/{i.id}", "/kanal/schaeden",
            f"/kanal/schaden/{s.id}", "/kanal/katalog", "/anlagen/", f"/anlagen/{a.id}", f"/anlagen/objekt/{o.id}",
            "/wartung", "/wartung/plaene", "/stoerungen", "/stoerungen?status=alle", f"/stoerung/{st.id}",
            "/verwaltung/import", "/verwaltung/benutzer", "/verwaltung/sicherung", "/suche?q=Linden",
            "/kanal/haltung/neu", f"/kanal/haltung/{h.id}/bearbeiten", "/kanal/schacht/neu", "/anlagen/neu",
            f"/anlagen/{a.id}/objekt/neu", "/stoerung/neu", f"/kanal/schaden/neu/haltung/{h.id}",
            f"/wartung/plan/neu/anlage/{a.id}", f"/wartung/plan/{p.id}/bearbeiten",
            f"/wartung/erfassen/objekt/{o.id}?plan={p.id}", "/passwort"]
    for url in urls:
        r = client.get(url)
        assert r.status_code == 200, (url, r.status_code)
    for ebene in ("haltungen", "knoten", "anlagen", "schaeden", "stoerungen"):
        r = client.get(f"/api/geo/{ebene}")
        assert r.status_code == 200 and r.json["features"], ebene
    assert client.get("/api/suche?q=PW").json
    assert client.get("/kanal/haltungen?export=csv").data.startswith("﻿".encode())


def test_anmeldung_noetig(app):
    c = app.test_client()
    assert c.get("/").status_code == 302
    assert c.get("/api/geo/haltungen").status_code == 302


def test_leser_darf_nicht_bearbeiten(app):
    c = app.test_client()
    anmelden(c, "gast")
    assert c.get("/stoerungen").status_code == 200
    assert c.get("/stoerung/neu").status_code == 302


def test_stoermeldung_ablauf(app, client):
    with app.app_context():
        a = Anlage.query.filter_by(anlagentyp="Pumpwerk").first()
        objekt = a.objekte[0]
    r = client.post("/stoerung/neu", data={
        "titel": "Pumpe läuft nicht", "prioritaet": "hoch", "meldeweg": "Telefon", "status": "offen",
        "ziel": f"objekt:{objekt.id}", "kanalobjekt": "", "lat": "53,23", "lon": "8,79",
        "foto": (io.BytesIO(b"\xff\xd8\xff"), "foto.jpg")}, content_type="multipart/form-data")
    assert r.status_code == 302
    with app.app_context():
        s = Stoermeldung.query.filter_by(titel="Pumpe läuft nicht").one()
        assert (s.ziel_typ, s.ziel_id, s.lat) == ("objekt", objekt.id, 53.23)
        sid = s.id
    client.post(f"/stoerung/{sid}/status", data={"status": "behoben"})
    with app.app_context():
        s = db.session.get(Stoermeldung, sid)
        assert s.status == "behoben" and s.behoben_am is not None and s.ausfallzeit_h is not None


def test_wartung_erledigen_setzt_naechsten_termin(app, client):
    with app.app_context():
        p = Wartungsplan.query.filter_by(intervall_monate=6).first()
        ziel_typ, ziel_id, pid = p.ziel_typ, p.ziel_id, p.id
    r = client.post(f"/wartung/erfassen/{ziel_typ}/{ziel_id}?plan={pid}",
                    data={"art": "Wartung", "datum": date.today().isoformat(), "ergebnis": "in Ordnung"})
    assert r.status_code == 302
    with app.app_context():
        p = db.session.get(Wartungsplan, pid)
        assert p.letzte_durchfuehrung == date.today()
        assert p.naechste_faelligkeit == monate_addieren(date.today(), 6)
    assert monate_addieren(date(2026, 8, 31), 6) == date(2027, 2, 28)


def test_schaden_manuell_aktualisiert_zustandsklasse(app, client):
    with app.app_context():
        h = Haltung.query.filter(Haltung.zustandsklasse.is_(None), Haltung.funktion == "Freispiegel").first()
        hid = h.id
    r = client.post(f"/kanal/schaden/neu/haltung/{hid}", data={"kode": "bac", "char1": "B", "station": "12,5",
                                                                "status": "offen"})
    assert r.status_code == 302
    with app.app_context():
        h = db.session.get(Haltung, hid)
        assert h.zustandsklasse == 0


def test_isybau_import_namensraum_und_streckenschaden(app, client, tmp_path):
    xml = """<?xml version="1.0" encoding="UTF-8"?>
<Identifikation xmlns="http://www.ofd-hannover.la/Identifikation"><Version>2013-02</Version><Datenkollektive>
<Stammdatenkollektiv>
 <AbwassertechnischeAnlage><Objektbezeichnung>T1</Objektbezeichnung><Objektart>2</Objektart><Entwaesserungsart>KM</Entwaesserungsart>
  <Knoten><KnotenTyp>0</KnotenTyp></Knoten><Geometrie><Geometriedaten><Knoten>
  <Punkt><PunktattributAbwasser>DMP</PunktattributAbwasser><Rechtswert>3489000</Rechtswert><Hochwert>5900000</Hochwert><Punkthoehe>10.5</Punkthoehe></Punkt>
  </Knoten></Geometriedaten></Geometrie></AbwassertechnischeAnlage>
 <AbwassertechnischeAnlage><Objektbezeichnung>T2</Objektbezeichnung><Objektart>2</Objektart>
  <Geometrie><Geometriedaten><Knoten><Punkt><Rechtswert>489010</Rechtswert><Hochwert>5900040</Hochwert></Punkt></Knoten></Geometriedaten></Geometrie></AbwassertechnischeAnlage>
 <AbwassertechnischeAnlage><Objektbezeichnung>T1-T2</Objektbezeichnung><Objektart>1</Objektart>
  <Kante><KnotenZulauf>T1</KnotenZulauf><KnotenAblauf>T2</KnotenAblauf><Laenge>41,2</Laenge><Material>STZ</Material>
  <Profil><Profilart>0</Profilart><Profilhoehe>300</Profilhoehe></Profil></Kante></AbwassertechnischeAnlage>
</Stammdatenkollektiv>
<Zustandsdatenkollektiv><InspizierteAbwassertechnischeAnlage><Objektbezeichnung>T1-T2</Objektbezeichnung>
 <OptischeInspektion><Inspektionsdatum>2025-03-04</Inspektionsdatum><Rohrleitung><Inspektionsrichtung>U</Inspektionsrichtung><Inspektionsdaten>
  <RZustand><Station>0</Station><InspektionsKode>BCD</InspektionsKode></RZustand>
  <RZustand><Station>3.2</Station><InspektionsKode>BBC</InspektionsKode><Charakterisierung1>A</Charakterisierung1><Quantifizierung1Numerisch>30</Quantifizierung1Numerisch><Streckenschaden>A1</Streckenschaden></RZustand>
  <RZustand><Station>9.0</Station><InspektionsKode>BAB</InspektionsKode><Charakterisierung1>C</Charakterisierung1><Charakterisierung2>A</Charakterisierung2></RZustand>
  <RZustand><Station>11.8</Station><InspektionsKode>BBC</InspektionsKode><Streckenschaden>B1</Streckenschaden></RZustand>
 </Inspektionsdaten></Rohrleitung></OptischeInspektion></InspizierteAbwassertechnischeAnlage></Zustandsdatenkollektiv>
</Datenkollektive></Identifikation>"""
    daten = isybau.lesen(io.BytesIO(xml.encode()))
    assert [k["bezeichnung"] for k in daten["knoten"]] == ["T1", "T2"]
    assert daten["knoten"][0]["kanalart"] == "MW" and daten["knoten"][0]["deckelhoehe"] == 10.5
    assert daten["haltungen"][0]["laenge"] == 41.2 and daten["haltungen"][0]["dn"] == 300
    schaeden = daten["inspektionen"][0]["schaeden"]
    assert [s["kode"] for s in schaeden] == ["BBC", "BAB"]
    assert schaeden[0]["station_bis"] == 11.8
    assert daten["inspektionen"][0]["richtung"] == "gegen Fließrichtung"

    datei = tmp_path / "test.xml"
    datei.write_text(xml, encoding="utf-8")
    r = client.post("/verwaltung/import", data={"datei": (open(datei, "rb"), "test.xml")},
                    content_type="multipart/form-data")
    assert r.status_code == 302
    with app.app_context():
        h = Haltung.query.filter_by(bezeichnung="T1-T2").one()
        assert h.von_knoten.bezeichnung == "T1" and h.zustandsklasse == 1
        assert Knoten.query.filter_by(bezeichnung="T1").one().lat == pytest.approx(53.2319, abs=1e-3)


def test_tabellenimport_schaeden_csv(app, tmp_path):
    with app.app_context():
        h = Haltung.query.filter(Haltung.funktion == "Freispiegel").order_by(Haltung.id.desc()).first()
        datei = tmp_path / "schaeden.csv"
        datei.write_text(f"objekt;objektart;datum;kode;char1;quant1;station\n{h.bezeichnung};Haltung;01.02.2026;BBA;C;60;4,5\n",
                         encoding="utf-8")
        from kanaldb.importer import datei_importieren
        p = datei_importieren(str(datei))
        assert p.erfolgreich and p.schaeden == 1
        s = Schaden.query.filter_by(ziel_typ="haltung", ziel_id=h.id, kode="BBA", station=4.5).one()
        assert s.klasse_b == 1


def test_ordnerimport_verschiebt_dateien(app, tmp_path):
    ordner = tmp_path / "import"
    ordner.mkdir()
    (ordner / "kaputt.xml").write_text("<kein xml", encoding="utf-8")
    (ordner / "anlagen.csv").write_text("bezeichnung;name;anlagentyp;lat;lon\nTEST-PW;PW Test;Pumpwerk;53,2;8,8\n",
                                        encoding="utf-8")
    with app.app_context():
        from kanaldb.importer import ordner_importieren
        ergebnis = ordner_importieren(str(ordner))
        assert sorted(p.erfolgreich for p in ergebnis) == [False, True]
        assert Anlage.query.filter_by(bezeichnung="TEST-PW").one().lat == 53.2
    assert len(os.listdir(ordner / "verarbeitet")) == 1 and len(os.listdir(ordner / "fehler")) == 1
