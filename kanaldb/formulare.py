"""Feldbeschreibungen für die Erfassungsformulare und deren Auswertung."""
from datetime import date, datetime

from .models import KANALARTEN

KANALART_AUSWAHL = list(KANALARTEN.items())
STATUS_BETRIEB = ["in Betrieb", "außer Betrieb", "stillgelegt", "geplant"]
ANLAGENTYPEN = ["Pumpwerk", "Hebeanlage", "Regenrückhaltebecken", "Regenüberlaufbecken", "Stauraumkanal",
                "Regenklärbecken", "Auslaufbauwerk", "Kläranlage", "Druckerhöhungsstation", "Sonderbauwerk"]
OBJEKTTYPEN = ["Pumpe", "Rührwerk", "Schieber", "Rückschlagklappe", "Drosselorgan", "Rechen", "Schaltanlage",
               "Steuerung / SPS", "Fernwirktechnik", "Niveaumessung", "Durchflussmessung", "Notstromaggregat",
               "Lüftung / Geruchsfilter", "Hebezeug", "Sonstiges"]
KNOTENARTEN = ["Schacht", "Bauwerk", "Auslaufbauwerk", "Anschlusspunkt"]
MATERIALIEN = ["B", "SB", "STZ", "PVCU", "PEHD", "PP", "GFK", "GG", "GGG", "AZ", "MA", "ST"]
WARTUNGSARTEN = ["Wartung", "Inspektion", "Reinigung", "Sichtkontrolle", "Funktionsprüfung", "TV-Inspektion",
                 "Prüfung (DGUV/VDE)", "Reparatur"]
ERGEBNISSE = ["in Ordnung", "Mängel festgestellt", "nicht in Ordnung"]
PRIORITAETEN = ["niedrig", "mittel", "hoch", "kritisch"]
STOER_STATUS = ["offen", "in Bearbeitung", "behoben"]
MELDEWEGE = ["Fernwirktechnik / Alarm", "Telefon", "Bürgermeldung", "Kontrollgang", "Bereitschaft", "Sonstiges"]
SCHADEN_STATUS = ["offen", "Sanierung geplant", "saniert"]
KLASSEN = [(str(i), str(i)) for i in range(6)]

FELDER = {
    "anlage": [
        ("bezeichnung", "Kennung", "text", {"required": True}),
        ("name", "Name", "text", {}),
        ("anlagentyp", "Anlagentyp", "select", {"choices": ANLAGENTYPEN}),
        ("kanalart", "Kanalart", "select", {"choices": KANALART_AUSWAHL, "leer": True}),
        ("ortsteil", "Ortsteil", "text", {}),
        ("adresse", "Adresse", "text", {}),
        ("lat", "Breitengrad", "float", {"geo": True}),
        ("lon", "Längengrad", "float", {"geo": True}),
        ("baujahr", "Baujahr", "int", {}),
        ("volumen_m3", "Volumen [m³]", "float", {}),
        ("vorfluter", "Vorfluter / Einleitung", "text", {}),
        ("einleiterlaubnis", "Wasserrechtliche Erlaubnis", "text", {}),
        ("status", "Status", "select", {"choices": STATUS_BETRIEB}),
        ("bemerkung", "Bemerkung", "textarea", {}),
    ],
    "objekt": [
        ("bezeichnung", "Bezeichnung", "text", {"required": True}),
        ("objekttyp", "Objekttyp", "select", {"choices": OBJEKTTYPEN}),
        ("hersteller", "Hersteller", "text", {}),
        ("typ", "Typ / Modell", "text", {}),
        ("seriennummer", "Seriennummer", "text", {}),
        ("baujahr", "Baujahr", "int", {}),
        ("leistung_kw", "Leistung [kW]", "float", {}),
        ("foerderstrom_ls", "Förderstrom [l/s]", "float", {}),
        ("foerderhoehe_m", "Förderhöhe [m]", "float", {}),
        ("betriebsstunden", "Betriebsstunden", "float", {}),
        ("status", "Status", "select", {"choices": STATUS_BETRIEB}),
        ("bemerkung", "Bemerkung", "textarea", {}),
    ],
    "knoten": [
        ("bezeichnung", "Bezeichnung", "text", {"required": True}),
        ("knotenart", "Knotenart", "select", {"choices": KNOTENARTEN}),
        ("kanalart", "Kanalart", "select", {"choices": KANALART_AUSWAHL, "leer": True}),
        ("ortsteil", "Ortsteil", "text", {}),
        ("strasse", "Straße", "text", {}),
        ("lat", "Breitengrad", "float", {"geo": True}),
        ("lon", "Längengrad", "float", {"geo": True}),
        ("rechtswert", "Rechtswert (UTM32)", "float", {}),
        ("hochwert", "Hochwert (UTM32)", "float", {}),
        ("deckelhoehe", "Deckelhöhe [m ü. NHN]", "float", {}),
        ("sohlhoehe", "Sohlhöhe [m ü. NHN]", "float", {}),
        ("material", "Material", "select", {"choices": MATERIALIEN, "leer": True}),
        ("baujahr", "Baujahr", "int", {}),
        ("status", "Status", "select", {"choices": STATUS_BETRIEB}),
        ("bemerkung", "Bemerkung", "textarea", {}),
    ],
    "haltung": [
        ("bezeichnung", "Bezeichnung", "text", {"required": True}),
        ("kanalart", "Kanalart", "select", {"choices": KANALART_AUSWAHL, "leer": True}),
        ("funktion", "Funktion", "select", {"choices": ["Freispiegel", "Druckleitung"]}),
        ("ortsteil", "Ortsteil", "text", {}),
        ("strasse", "Straße", "text", {}),
        ("laenge", "Länge [m]", "float", {}),
        ("dn", "Nennweite / Profilhöhe [mm]", "int", {}),
        ("profilbreite", "Profilbreite [mm]", "int", {}),
        ("profilart", "Profilart", "select", {"choices": ["Kreis", "Ei", "Maul", "Rechteck"]}),
        ("material", "Material", "select", {"choices": MATERIALIEN, "leer": True}),
        ("baujahr", "Baujahr", "int", {}),
        ("sohle_zulauf", "Sohlhöhe Zulauf [m]", "float", {}),
        ("sohle_ablauf", "Sohlhöhe Ablauf [m]", "float", {}),
        ("status", "Status", "select", {"choices": STATUS_BETRIEB}),
        ("bemerkung", "Bemerkung", "textarea", {}),
    ],
    "wartungsplan": [
        ("bezeichnung", "Bezeichnung", "text", {"required": True}),
        ("art", "Art", "select", {"choices": WARTUNGSARTEN}),
        ("intervall_monate", "Intervall [Monate]", "int", {"required": True}),
        ("letzte_durchfuehrung", "Zuletzt durchgeführt", "date", {}),
        ("naechste_faelligkeit", "Nächste Fälligkeit", "date", {}),
        ("zustaendig", "Zuständig", "text", {}),
        ("aktiv", "Aktiv", "bool", {}),
        ("beschreibung", "Tätigkeiten / Checkliste", "textarea", {}),
    ],
    "massnahme": [
        ("art", "Art", "select", {"choices": WARTUNGSARTEN}),
        ("datum", "Datum", "date", {"required": True}),
        ("durchgefuehrt_von", "Durchgeführt von", "text", {}),
        ("ergebnis", "Ergebnis", "select", {"choices": ERGEBNISSE}),
        ("dauer_h", "Dauer [h]", "float", {}),
        ("beschreibung", "Tätigkeit", "textarea", {}),
        ("befund", "Befund / Mängel", "textarea", {}),
    ],
    "stoermeldung": [
        ("titel", "Kurzbeschreibung", "text", {"required": True}),
        ("prioritaet", "Priorität", "select", {"choices": PRIORITAETEN}),
        ("meldeweg", "Meldeweg", "select", {"choices": MELDEWEGE}),
        ("gemeldet_am", "Gemeldet am", "datetime", {}),
        ("gemeldet_von", "Gemeldet von", "text", {}),
        ("beschreibung", "Beschreibung", "textarea", {}),
        ("status", "Status", "select", {"choices": STOER_STATUS}),
        ("bearbeiter", "Bearbeiter", "text", {}),
        ("ursache", "Ursache", "textarea", {}),
        ("massnahme", "Maßnahme", "textarea", {}),
        ("behoben_am", "Behoben am", "datetime", {}),
        ("ausfallzeit_h", "Ausfallzeit [h]", "float", {}),
        ("lat", "Breitengrad", "float", {"geo": True}),
        ("lon", "Längengrad", "float", {"geo": True}),
    ],
    "schaden": [
        ("datum", "Feststellungsdatum", "date", {}),
        ("kode", "Hauptkode (DWA-M 149-2)", "kode", {"required": True}),
        ("char1", "Charakterisierung 1", "text", {}),
        ("char2", "Charakterisierung 2", "text", {}),
        ("quant1", "Quantifizierung 1", "text", {}),
        ("quant2", "Quantifizierung 2", "text", {}),
        ("station", "Station [m]", "float", {}),
        ("station_bis", "Station bis [m] (Streckenschaden)", "float", {}),
        ("uhr_von", "Lage von [Uhr]", "int", {}),
        ("uhr_bis", "Lage bis [Uhr]", "int", {}),
        ("verbindung", "an Rohrverbindung", "bool", {}),
        ("klasse_d", "Klasse Dichtheit (D)", "select", {"choices": KLASSEN, "leer": True}),
        ("klasse_s", "Klasse Standsicherheit (S)", "select", {"choices": KLASSEN, "leer": True}),
        ("klasse_b", "Klasse Betriebssicherheit (B)", "select", {"choices": KLASSEN, "leer": True}),
        ("status", "Status", "select", {"choices": SCHADEN_STATUS}),
        ("sanierung_datum", "Saniert am", "date", {}),
        ("sanierung_massnahme", "Sanierungsmaßnahme", "text", {}),
        ("bemerkung", "Bemerkung", "textarea", {}),
        ("lat", "Breitengrad (optional)", "float", {"geo": True}),
        ("lon", "Längengrad (optional)", "float", {"geo": True}),
    ],
}


class FormFehler(ValueError):
    pass


def _parse(wert, art, label):
    wert = (wert or "").strip()
    if art == "bool":
        return wert in ("1", "on", "ja", "true")
    if wert == "":
        return None
    try:
        if art == "int":
            return int(float(wert.replace(",", ".")))
        if art == "float":
            return float(wert.replace(",", "."))
        if art == "date":
            return date.fromisoformat(wert)
        if art == "datetime":
            return datetime.fromisoformat(wert)
    except ValueError:
        raise FormFehler(f"„{label}“: ungültiger Wert „{wert}“")
    if art == "kode":
        return wert.upper()
    return wert


def formular_uebernehmen(obj, typ, form):
    """Überträgt Formularwerte auf das Objekt. Löst FormFehler bei ungültigen Eingaben aus."""
    for name, label, art, opt in FELDER[typ]:
        if art != "bool" and name not in form:
            continue
        wert = _parse(form.get(name), art, label)
        if art == "select" and wert is not None and name.startswith("klasse"):
            wert = int(wert)
        if opt.get("required") and wert in (None, ""):
            raise FormFehler(f"„{label}“ ist ein Pflichtfeld")
        setattr(obj, name, wert)
