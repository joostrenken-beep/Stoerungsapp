import json
from datetime import date, datetime

from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

from .extensions import db
from .geo import punkt_auf_linie

KANALARTEN = {"SW": "Schmutzwasser", "RW": "Regenwasser", "MW": "Mischwasser"}
ROLLEN = {"leser": "Lesen", "bearbeiter": "Bearbeiten", "admin": "Administration"}


def jetzt():
    return datetime.now().replace(microsecond=0)


class Benutzer(UserMixin, db.Model):
    __tablename__ = "benutzer"
    id = db.Column(db.Integer, primary_key=True)
    benutzername = db.Column(db.String(60), unique=True, nullable=False)
    name = db.Column(db.String(120))
    passwort_hash = db.Column(db.String(255), nullable=False)
    rolle = db.Column(db.String(20), nullable=False, default="leser")
    aktiv = db.Column(db.Boolean, nullable=False, default=True)
    angelegt = db.Column(db.DateTime, default=jetzt)

    def set_passwort(self, passwort):
        self.passwort_hash = generate_password_hash(passwort)

    def check_passwort(self, passwort):
        return check_password_hash(self.passwort_hash, passwort)

    @property
    def is_active(self):
        return self.aktiv

    @property
    def darf_bearbeiten(self):
        return self.rolle in ("bearbeiter", "admin")

    @property
    def ist_admin(self):
        return self.rolle == "admin"

    @property
    def anzeige(self):
        return self.name or self.benutzername


class ZielMixin:
    """Gemeinsame Eigenschaften aller Objekte, an die Wartungen, Schäden,
    Störmeldungen und Dokumente gehängt werden können."""

    ZIEL_TYP = None
    TYP_NAME = None

    @property
    def anzeige(self):
        return f"{self.TYP_NAME} {self.bezeichnung}"

    def position(self):
        lat, lon = getattr(self, "lat", None), getattr(self, "lon", None)
        return (lat, lon) if lat is not None and lon is not None else None


class Anlage(ZielMixin, db.Model):
    __tablename__ = "anlage"
    ZIEL_TYP = "anlage"
    TYP_NAME = "Anlage"
    id = db.Column(db.Integer, primary_key=True)
    bezeichnung = db.Column(db.String(120), unique=True, nullable=False)
    name = db.Column(db.String(200))
    anlagentyp = db.Column(db.String(60), nullable=False, default="Pumpwerk")
    kanalart = db.Column(db.String(2))
    ortsteil = db.Column(db.String(80), index=True)
    adresse = db.Column(db.String(200))
    lat = db.Column(db.Float)
    lon = db.Column(db.Float)
    baujahr = db.Column(db.Integer)
    volumen_m3 = db.Column(db.Float)
    vorfluter = db.Column(db.String(120))
    einleiterlaubnis = db.Column(db.String(120))
    status = db.Column(db.String(30), default="in Betrieb")
    bemerkung = db.Column(db.Text)
    geaendert = db.Column(db.DateTime, default=jetzt, onupdate=jetzt)

    objekte = db.relationship("Anlagenobjekt", back_populates="anlage", cascade="all, delete-orphan",
                              order_by="Anlagenobjekt.bezeichnung")

    @property
    def anzeige(self):
        return f"{self.anlagentyp} {self.name or self.bezeichnung}"


class Anlagenobjekt(ZielMixin, db.Model):
    __tablename__ = "anlagenobjekt"
    ZIEL_TYP = "objekt"
    TYP_NAME = "Objekt"
    id = db.Column(db.Integer, primary_key=True)
    anlage_id = db.Column(db.Integer, db.ForeignKey("anlage.id"), nullable=False, index=True)
    bezeichnung = db.Column(db.String(120), nullable=False)
    objekttyp = db.Column(db.String(60), nullable=False, default="Pumpe")
    hersteller = db.Column(db.String(120))
    typ = db.Column(db.String(120))
    seriennummer = db.Column(db.String(120))
    baujahr = db.Column(db.Integer)
    leistung_kw = db.Column(db.Float)
    foerderstrom_ls = db.Column(db.Float)
    foerderhoehe_m = db.Column(db.Float)
    betriebsstunden = db.Column(db.Float)
    status = db.Column(db.String(30), default="in Betrieb")
    bemerkung = db.Column(db.Text)
    geaendert = db.Column(db.DateTime, default=jetzt, onupdate=jetzt)

    anlage = db.relationship("Anlage", back_populates="objekte")

    @property
    def anzeige(self):
        return f"{self.objekttyp} {self.bezeichnung} ({self.anlage.name or self.anlage.bezeichnung})"

    def position(self):
        return self.anlage.position() if self.anlage else None


class Knoten(ZielMixin, db.Model):
    """Schacht, Bauwerk, Auslauf oder Anschlusspunkt."""
    __tablename__ = "knoten"
    ZIEL_TYP = "knoten"
    TYP_NAME = "Schacht"
    id = db.Column(db.Integer, primary_key=True)
    bezeichnung = db.Column(db.String(60), unique=True, nullable=False, index=True)
    knotenart = db.Column(db.String(30), nullable=False, default="Schacht")
    kanalart = db.Column(db.String(2), index=True)
    ortsteil = db.Column(db.String(80), index=True)
    strasse = db.Column(db.String(120))
    rechtswert = db.Column(db.Float)
    hochwert = db.Column(db.Float)
    lat = db.Column(db.Float)
    lon = db.Column(db.Float)
    deckelhoehe = db.Column(db.Float)
    sohlhoehe = db.Column(db.Float)
    material = db.Column(db.String(40))
    baujahr = db.Column(db.Integer)
    status = db.Column(db.String(30), default="in Betrieb")
    zustandsklasse = db.Column(db.Integer)
    anlage_id = db.Column(db.Integer, db.ForeignKey("anlage.id"))
    bemerkung = db.Column(db.Text)
    quelle = db.Column(db.String(200))
    geaendert = db.Column(db.DateTime, default=jetzt, onupdate=jetzt)

    anlage = db.relationship("Anlage")

    @property
    def anzeige(self):
        return f"{self.knotenart} {self.bezeichnung}"

    @property
    def schachttiefe(self):
        if self.deckelhoehe is not None and self.sohlhoehe is not None:
            return round(self.deckelhoehe - self.sohlhoehe, 2)
        return None


class Haltung(ZielMixin, db.Model):
    __tablename__ = "haltung"
    ZIEL_TYP = "haltung"
    TYP_NAME = "Haltung"
    id = db.Column(db.Integer, primary_key=True)
    bezeichnung = db.Column(db.String(60), unique=True, nullable=False, index=True)
    von_knoten_id = db.Column(db.Integer, db.ForeignKey("knoten.id"), index=True)
    bis_knoten_id = db.Column(db.Integer, db.ForeignKey("knoten.id"), index=True)
    kanalart = db.Column(db.String(2), index=True)
    funktion = db.Column(db.String(30), default="Freispiegel")
    ortsteil = db.Column(db.String(80), index=True)
    strasse = db.Column(db.String(120))
    laenge = db.Column(db.Float)
    dn = db.Column(db.Integer)
    profilbreite = db.Column(db.Integer)
    profilart = db.Column(db.String(30), default="Kreis")
    material = db.Column(db.String(40))
    baujahr = db.Column(db.Integer)
    sohle_zulauf = db.Column(db.Float)
    sohle_ablauf = db.Column(db.Float)
    status = db.Column(db.String(30), default="in Betrieb")
    zustandsklasse = db.Column(db.Integer)
    letzte_inspektion = db.Column(db.Date)
    geometrie = db.Column(db.Text)
    bemerkung = db.Column(db.Text)
    quelle = db.Column(db.String(200))
    geaendert = db.Column(db.DateTime, default=jetzt, onupdate=jetzt)

    von_knoten = db.relationship("Knoten", foreign_keys=[von_knoten_id])
    bis_knoten = db.relationship("Knoten", foreign_keys=[bis_knoten_id])

    @property
    def gefaelle_promille(self):
        if self.sohle_zulauf is None or self.sohle_ablauf is None or not self.laenge:
            return None
        return round((self.sohle_zulauf - self.sohle_ablauf) / self.laenge * 1000, 1)

    def koordinaten(self):
        if self.geometrie:
            try:
                punkte = json.loads(self.geometrie)
                if len(punkte) >= 2:
                    return punkte
            except ValueError:
                pass
        punkte = [k.position() for k in (self.von_knoten, self.bis_knoten) if k and k.position()]
        return [list(p) for p in punkte] if len(punkte) == 2 else []

    def position(self):
        return punkt_auf_linie(self.koordinaten(), 0.5)

    def punkt_bei_station(self, station, gegen_fliessrichtung=False):
        if not self.laenge or station is None:
            return self.position()
        anteil = station / self.laenge
        if gegen_fliessrichtung:
            anteil = 1 - anteil
        return punkt_auf_linie(self.koordinaten(), anteil)


ZIEL_KLASSEN = {"haltung": Haltung, "knoten": Knoten, "anlage": Anlage, "objekt": Anlagenobjekt}
ZIEL_NAMEN = {"haltung": "Haltung", "knoten": "Schacht/Bauwerk", "anlage": "Anlage", "objekt": "Anlagenobjekt"}


def ziel_laden(ziel_typ, ziel_id):
    klasse = ZIEL_KLASSEN.get(ziel_typ)
    if not klasse or not ziel_id:
        return None
    return db.session.get(klasse, int(ziel_id))


class ZielBezug:
    """Mixin für Datensätze mit (ziel_typ, ziel_id)."""

    @property
    def ziel(self):
        if not hasattr(self, "_ziel_cache"):
            self._ziel_cache = ziel_laden(self.ziel_typ, self.ziel_id)
        return self._ziel_cache

    @property
    def ziel_anzeige(self):
        return self.ziel.anzeige if self.ziel else "–"


class Inspektion(ZielBezug, db.Model):
    """Optische Inspektion (TV-Befahrung, Schachtinspektion) einer Haltung oder eines Knotens."""
    __tablename__ = "inspektion"
    id = db.Column(db.Integer, primary_key=True)
    ziel_typ = db.Column(db.String(20), nullable=False)
    ziel_id = db.Column(db.Integer, nullable=False)
    datum = db.Column(db.Date, nullable=False)
    firma = db.Column(db.String(120))
    untersucher = db.Column(db.String(120))
    verfahren = db.Column(db.String(60), default="TV-Inspektion")
    richtung = db.Column(db.String(30), default="in Fließrichtung")
    inspektionslaenge = db.Column(db.Float)
    zustandsklasse = db.Column(db.Integer)
    quelle = db.Column(db.String(200))
    bemerkung = db.Column(db.Text)
    angelegt = db.Column(db.DateTime, default=jetzt)

    schaeden = db.relationship("Schaden", back_populates="inspektion", cascade="all, delete-orphan",
                               order_by="Schaden.station")

    __table_args__ = (db.Index("ix_inspektion_ziel", "ziel_typ", "ziel_id"),)

    @property
    def gegen_fliessrichtung(self):
        return (self.richtung or "").startswith("gegen")


class Schaden(ZielBezug, db.Model):
    """Einzelschaden nach DWA-M 149-2 / DIN EN 13508-2."""
    __tablename__ = "schaden"
    id = db.Column(db.Integer, primary_key=True)
    inspektion_id = db.Column(db.Integer, db.ForeignKey("inspektion.id"), index=True)
    ziel_typ = db.Column(db.String(20), nullable=False)
    ziel_id = db.Column(db.Integer, nullable=False)
    datum = db.Column(db.Date, default=date.today)
    kode = db.Column(db.String(10), nullable=False)
    char1 = db.Column(db.String(5))
    char2 = db.Column(db.String(5))
    quant1 = db.Column(db.String(20))
    quant2 = db.Column(db.String(20))
    station = db.Column(db.Float)
    station_bis = db.Column(db.Float)
    uhr_von = db.Column(db.Integer)
    uhr_bis = db.Column(db.Integer)
    verbindung = db.Column(db.Boolean, default=False)
    klasse_d = db.Column(db.Integer)
    klasse_s = db.Column(db.Integer)
    klasse_b = db.Column(db.Integer)
    schadensklasse = db.Column(db.Integer)
    foto = db.Column(db.String(200))
    bemerkung = db.Column(db.Text)
    status = db.Column(db.String(30), default="offen")
    sanierung_datum = db.Column(db.Date)
    sanierung_massnahme = db.Column(db.String(200))
    lat = db.Column(db.Float)
    lon = db.Column(db.Float)
    erstellt_von = db.Column(db.String(120))
    angelegt = db.Column(db.DateTime, default=jetzt)

    inspektion = db.relationship("Inspektion", back_populates="schaeden")

    __table_args__ = (db.Index("ix_schaden_ziel", "ziel_typ", "ziel_id"),)

    @property
    def kode_voll(self):
        return "".join(x for x in (self.kode, self.char1, self.char2) if x)

    def position(self):
        if self.lat is not None and self.lon is not None:
            return (self.lat, self.lon)
        ziel = self.ziel
        if ziel is None:
            return None
        if isinstance(ziel, Haltung):
            gegen = self.inspektion.gegen_fliessrichtung if self.inspektion else False
            return ziel.punkt_bei_station(self.station, gegen)
        return ziel.position()


class Wartungsplan(ZielBezug, db.Model):
    __tablename__ = "wartungsplan"
    id = db.Column(db.Integer, primary_key=True)
    ziel_typ = db.Column(db.String(20), nullable=False)
    ziel_id = db.Column(db.Integer, nullable=False)
    bezeichnung = db.Column(db.String(200), nullable=False)
    art = db.Column(db.String(40), default="Wartung")
    intervall_monate = db.Column(db.Integer, nullable=False, default=12)
    letzte_durchfuehrung = db.Column(db.Date)
    naechste_faelligkeit = db.Column(db.Date, index=True)
    zustaendig = db.Column(db.String(120))
    aktiv = db.Column(db.Boolean, default=True)
    beschreibung = db.Column(db.Text)

    __table_args__ = (db.Index("ix_wartungsplan_ziel", "ziel_typ", "ziel_id"),)

    @property
    def faellig_in_tagen(self):
        if not self.naechste_faelligkeit:
            return None
        return (self.naechste_faelligkeit - date.today()).days


class Massnahme(ZielBezug, db.Model):
    """Durchgeführte Wartung, Inspektion, Reinigung oder Reparatur."""
    __tablename__ = "massnahme"
    id = db.Column(db.Integer, primary_key=True)
    ziel_typ = db.Column(db.String(20), nullable=False)
    ziel_id = db.Column(db.Integer, nullable=False)
    wartungsplan_id = db.Column(db.Integer, db.ForeignKey("wartungsplan.id"))
    art = db.Column(db.String(40), default="Wartung")
    datum = db.Column(db.Date, nullable=False, default=date.today)
    durchgefuehrt_von = db.Column(db.String(120))
    beschreibung = db.Column(db.Text)
    befund = db.Column(db.Text)
    ergebnis = db.Column(db.String(30), default="in Ordnung")
    dauer_h = db.Column(db.Float)
    erstellt_von = db.Column(db.String(120))
    angelegt = db.Column(db.DateTime, default=jetzt)

    wartungsplan = db.relationship("Wartungsplan")

    __table_args__ = (db.Index("ix_massnahme_ziel", "ziel_typ", "ziel_id"),)


class Stoermeldung(ZielBezug, db.Model):
    __tablename__ = "stoermeldung"
    id = db.Column(db.Integer, primary_key=True)
    ziel_typ = db.Column(db.String(20))
    ziel_id = db.Column(db.Integer)
    titel = db.Column(db.String(200), nullable=False)
    beschreibung = db.Column(db.Text)
    gemeldet_am = db.Column(db.DateTime, nullable=False, default=jetzt, index=True)
    gemeldet_von = db.Column(db.String(120))
    meldeweg = db.Column(db.String(40), default="Kontrollgang")
    prioritaet = db.Column(db.String(20), default="mittel")
    status = db.Column(db.String(30), default="offen", index=True)
    bearbeiter = db.Column(db.String(120))
    ursache = db.Column(db.Text)
    massnahme = db.Column(db.Text)
    behoben_am = db.Column(db.DateTime)
    ausfallzeit_h = db.Column(db.Float)
    lat = db.Column(db.Float)
    lon = db.Column(db.Float)
    erstellt_von = db.Column(db.String(120))

    __table_args__ = (db.Index("ix_stoermeldung_ziel", "ziel_typ", "ziel_id"),)

    def position(self):
        if self.lat is not None and self.lon is not None:
            return (self.lat, self.lon)
        return self.ziel.position() if self.ziel else None


class Dokument(ZielBezug, db.Model):
    __tablename__ = "dokument"
    id = db.Column(db.Integer, primary_key=True)
    ziel_typ = db.Column(db.String(20), nullable=False)
    ziel_id = db.Column(db.Integer, nullable=False)
    dateiname = db.Column(db.String(255), nullable=False)
    speichername = db.Column(db.String(255), nullable=False)
    beschreibung = db.Column(db.String(255))
    hochgeladen_am = db.Column(db.DateTime, default=jetzt)
    hochgeladen_von = db.Column(db.String(120))

    __table_args__ = (db.Index("ix_dokument_ziel", "ziel_typ", "ziel_id"),)

    @property
    def ist_bild(self):
        return self.dateiname.lower().rsplit(".", 1)[-1] in ("jpg", "jpeg", "png", "gif", "webp")


class ImportProtokoll(db.Model):
    __tablename__ = "import_protokoll"
    id = db.Column(db.Integer, primary_key=True)
    zeitpunkt = db.Column(db.DateTime, default=jetzt, index=True)
    datei = db.Column(db.String(255))
    format = db.Column(db.String(40))
    ausgeloest_von = db.Column(db.String(120))
    erfolgreich = db.Column(db.Boolean, default=True)
    knoten = db.Column(db.Integer, default=0)
    haltungen = db.Column(db.Integer, default=0)
    inspektionen = db.Column(db.Integer, default=0)
    schaeden = db.Column(db.Integer, default=0)
    anlagen = db.Column(db.Integer, default=0)
    meldungen = db.Column(db.Text)
