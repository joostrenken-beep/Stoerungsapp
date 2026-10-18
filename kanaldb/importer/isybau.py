"""Import von ISYBAU-XML (Austauschformate 2006/2013/2017) und DWA-M 150-XML.

Der Parser arbeitet unabhängig von XML-Namensräumen und Versionsnummern und
wertet die Elemente über ihre lokalen Namen aus. Unterstützt werden:

Stammdaten  (AbwassertechnischeAnlage):
  Objektbezeichnung, Objektart (1 = Kante/Haltung, 2 = Knoten), Entwaesserungsart
  (KS/KR/KM), Lage (Strassenname, Ortsteilname), Baujahr, Status, Geometrie
  (Punkte mit Rechtswert/Hochwert/Punkthoehe/PunktattributAbwasser DMP/SMP),
  Kante (KnotenZulauf, KnotenAblauf, SohlhoeheZulauf/-Ablauf, Laenge, Material,
  Profil), Knoten (KnotenTyp 0 Schacht / 1 Anschlusspunkt / 2 Bauwerk).

Zustandsdaten (InspizierteAbwassertechnischeAnlage):
  OptischeInspektion mit Inspektionsdatum, Untersucher, Rohrleitung
  (Inspektionsrichtung, Inspektionslaenge, RZustand) bzw. Knoten (KZustand) mit
  InspektionsKode, Charakterisierung1/2, Quantifizierung1/2, Station bzw.
  VertikaleLage, PositionVon/PositionBis, Streckenschaden (A1/B1),
  Verbindung, Fotobezeichnung, Kommentar, Klassifizierung (D/S/B).
"""
import json
import xml.etree.ElementTree as ET
from datetime import date, datetime

from ..dwa149 import gesamtklasse, ist_info_kode, klassen_vorschlag
from ..geo import nach_wgs84

ENTWAESSERUNGSART = {"KS": "SW", "KR": "RW", "KM": "MW", "S": "SW", "R": "RW", "M": "MW",
                     "SW": "SW", "RW": "RW", "MW": "MW"}
KNOTENTYP = {"0": "Schacht", "1": "Anschlusspunkt", "2": "Bauwerk"}
PROFILART = {"0": "Kreis", "1": "Ei", "2": "Maul", "3": "Rechteck", "4": "Rechteck", "5": "Rechteck"}


def lokal(tag):
    return tag.rsplit("}", 1)[-1] if isinstance(tag, str) else ""


def kind(el, *namen):
    if el is None:
        return None
    for c in el:
        if lokal(c.tag) in namen:
            return c
    return None


def kinder(el, *namen):
    return [c for c in el if lokal(c.tag) in namen] if el is not None else []


def nachfahren(el, *namen):
    return [c for c in el.iter() if lokal(c.tag) in namen] if el is not None else []


def pfad(el, weg):
    """Folgt einem Pfad lokaler Namen, z. B. 'Lage/Strassenname'.
    Ein Pfadteil kann Alternativen enthalten: 'Station|VertikaleLage'."""
    for teil in weg.split("/"):
        el = kind(el, *teil.split("|"))
        if el is None:
            return None
    return el


def txt(el, weg=None):
    if weg:
        el = pfad(el, weg)
    if el is None or el.text is None:
        return None
    wert = el.text.strip()
    return wert or None


def zahl(wert):
    if wert is None:
        return None
    try:
        return float(str(wert).replace(",", "."))
    except ValueError:
        return None


def ganzzahl(wert):
    z = zahl(wert)
    return int(z) if z is not None else None


def datum(wert):
    if not wert:
        return None
    for fmt in ("%Y-%m-%d", "%d.%m.%Y", "%Y%m%d", "%Y-%m-%dT%H:%M:%S"):
        try:
            return datetime.strptime(wert[:19] if "T" in wert else wert[:10], fmt).date()
        except ValueError:
            continue
    return None


def _punkte(geometrie_el):
    """Liefert Punkte als Dicts mit rw, hw, hoehe, attribut."""
    punkte = []
    for p in nachfahren(geometrie_el, "Punkt", "Start", "Ende"):
        rw, hw = zahl(txt(p, "Rechtswert")), zahl(txt(p, "Hochwert"))
        if rw is None or hw is None:
            continue
        punkte.append({"rw": rw, "hw": hw, "hoehe": zahl(txt(p, "Punkthoehe")),
                       "attribut": (txt(p, "PunktattributAbwasser") or "").upper()})
    return punkte


def stammdaten_lesen(root, zone=32):
    knoten, haltungen = [], []
    for anl in nachfahren(root, "AbwassertechnischeAnlage"):
        bez = txt(anl, "Objektbezeichnung")
        if not bez:
            continue
        kante_el = kind(anl, "Kante")
        knoten_el = kind(anl, "Knoten")
        objektart = txt(anl, "Objektart")
        ist_kante = objektart == "1" or (objektart is None and kante_el is not None)
        art = ENTWAESSERUNGSART.get((txt(anl, "Entwaesserungsart") or txt(anl, "Kanalart") or "").upper())
        basis = {
            "bezeichnung": bez,
            "kanalart": art,
            "strasse": txt(anl, "Lage/Strassenname"),
            "ortsteil": txt(anl, "Lage/Ortsteilname") or txt(anl, "Lage/Ortsteil"),
            "baujahr": ganzzahl(txt(anl, "Baujahr")),
            "bemerkung": txt(anl, "Kommentar"),
        }
        geometrie = pfad(anl, "Geometrie/Geometriedaten")
        punkte = _punkte(geometrie if geometrie is not None else kind(anl, "Geometrie"))
        if ist_kante:
            k = kante_el
            profil = kind(k, "Profil")
            kommentar = (basis["bemerkung"] or "") + " " + (txt(k, "Funktion") or "")
            dn = ganzzahl(txt(profil, "Profilhoehe")) or ganzzahl(txt(profil, "Profilbreite"))
            geo = []
            for p in punkte:
                ll = nach_wgs84(p["rw"], p["hw"], zone)
                if ll and (not geo or geo[-1] != [round(ll[0], 7), round(ll[1], 7)]):
                    geo.append([round(ll[0], 7), round(ll[1], 7)])
            haltungen.append({
                **basis,
                "von": txt(k, "KnotenZulauf"),
                "bis": txt(k, "KnotenAblauf"),
                "sohle_zulauf": zahl(txt(k, "SohlhoeheZulauf")),
                "sohle_ablauf": zahl(txt(k, "SohlhoeheAblauf")),
                "laenge": zahl(txt(k, "Laenge")) or zahl(txt(k, "Haltung/DMPLaenge")),
                "material": txt(k, "Material"),
                "dn": dn,
                "profilbreite": ganzzahl(txt(profil, "Profilbreite")),
                "profilart": PROFILART.get(txt(profil, "Profilart") or "", txt(profil, "Profilart")),
                "funktion": "Druckleitung" if "druck" in kommentar.lower() else "Freispiegel",
                "geometrie": json.dumps(geo) if len(geo) >= 2 else None,
            })
        else:
            k = knoten_el
            art_knoten = KNOTENTYP.get(txt(k, "KnotenTyp") or "", "Schacht")
            bauwerkstyp = txt(k, "Bauwerk/Bauwerkstyp")
            if bauwerkstyp and "auslauf" in bauwerkstyp.lower():
                art_knoten = "Auslaufbauwerk"
            dmp = next((p for p in punkte if p["attribut"] == "DMP"), None)
            smp = next((p for p in punkte if p["attribut"] in ("SMP", "SBW", "GOK")), None)
            lage = dmp or smp or (punkte[0] if punkte else None)
            ll = nach_wgs84(lage["rw"], lage["hw"], zone) if lage else None
            knoten.append({
                **basis,
                "knotenart": art_knoten,
                "rechtswert": lage["rw"] if lage else None,
                "hochwert": lage["hw"] if lage else None,
                "lat": round(ll[0], 7) if ll else None,
                "lon": round(ll[1], 7) if ll else None,
                "deckelhoehe": dmp["hoehe"] if dmp else None,
                "sohlhoehe": smp["hoehe"] if smp else zahl(txt(k, "Schacht/Sohlhoehe")),
                "material": txt(k, "Schacht/Material") or txt(k, "Material"),
            })
    return knoten, haltungen


def _klassen(zustand):
    kl = kind(zustand, "Klassifizierung", "Zustandsklassifizierung")
    if kl is None:
        return None, None, None
    return (ganzzahl(txt(kl, "Dichtheit|KlasseDichtheit|KlasseD")),
            ganzzahl(txt(kl, "Standsicherheit|KlasseStandsicherheit|KlasseS")),
            ganzzahl(txt(kl, "Betriebssicherheit|KlasseBetriebssicherheit|KlasseB")))


def _zustaende(container, station_namen):
    schaeden, offen = [], {}
    for z in nachfahren(container, "RZustand", "KZustand", "Zustand"):
        kode = (txt(z, "InspektionsKode") or txt(z, "Hauptkode") or "").upper()
        if not kode:
            continue
        station = zahl(txt(z, station_namen))
        strecke = (txt(z, "Streckenschaden") or "").upper()
        if strecke.startswith("B") and strecke[1:] in offen:
            offen.pop(strecke[1:])["station_bis"] = station
            continue
        if ist_info_kode(kode):
            continue
        c1, c2 = txt(z, "Charakterisierung1"), txt(z, "Charakterisierung2")
        q1 = txt(z, "Quantifizierung1Numerisch|Quantifizierung1|Quantifizierung1Text")
        q2 = txt(z, "Quantifizierung2Numerisch|Quantifizierung2|Quantifizierung2Text")
        kd, ks, kb = _klassen(z)
        if kd is None and ks is None and kb is None:
            kd, ks, kb = klassen_vorschlag(kode, c1, c2, q1)
        verbindung = (txt(z, "Verbindung") or "").lower() in ("ja", "j", "1", "true")
        eintrag = {
            "kode": kode, "char1": c1, "char2": c2, "quant1": q1, "quant2": q2,
            "station": station, "station_bis": None,
            "uhr_von": ganzzahl(txt(z, "PositionVon")), "uhr_bis": ganzzahl(txt(z, "PositionBis")),
            "verbindung": verbindung, "foto": txt(z, "Fotobezeichnung|Fotodatei"),
            "bemerkung": txt(z, "Kommentar"),
            "klasse_d": kd, "klasse_s": ks, "klasse_b": kb,
            "schadensklasse": gesamtklasse(kd, ks, kb),
        }
        if strecke.startswith("A"):
            offen[strecke[1:]] = eintrag
        schaeden.append(eintrag)
    return schaeden


def zustandsdaten_lesen(root):
    inspektionen = []
    for anl in nachfahren(root, "InspizierteAbwassertechnischeAnlage"):
        bez = txt(anl, "Objektbezeichnung")
        if not bez:
            continue
        anlagentyp = txt(anl, "Anlagentyp")
        for insp in kinder(anl, "OptischeInspektion"):
            rohr = kind(insp, "Rohrleitung")
            knoten = kind(insp, "Knoten")
            ist_knoten = anlagentyp == "2" or (rohr is None and knoten is not None)
            container = knoten if ist_knoten else rohr
            richtung_kz = (txt(rohr, "Inspektionsrichtung") or "O").upper() if rohr is not None else "O"
            inspektionen.append({
                "objekt": bez,
                "ziel_typ": "knoten" if ist_knoten else "haltung",
                "datum": datum(txt(insp, "Inspektionsdatum")) or date.today(),
                "untersucher": txt(insp, "NameUntersucher|Untersucher"),
                "firma": txt(insp, "Auftragnehmer|Firma|Inspektionsfirma"),
                "richtung": "gegen Fließrichtung" if richtung_kz in ("U", "G", "GEGEN") else "in Fließrichtung",
                "inspektionslaenge": zahl(txt(rohr, "Inspektionslaenge")) if rohr is not None else None,
                "zustandsklasse": ganzzahl(txt(anl, "Bewertung/Objektklasse") or txt(insp, "Zustandsklasse")),
                "schaeden": _zustaende(container, "VertikaleLage|Vertikale_Lage|Station" if ist_knoten
                                       else "Station"),
            })
    return inspektionen


def lesen(datei_oder_pfad, zone=32):
    """Liest eine ISYBAU- bzw. DWA-M 150-XML-Datei.
    Rückgabe: dict(knoten=[...], haltungen=[...], inspektionen=[...], format=str)."""
    root = ET.parse(datei_oder_pfad).getroot()
    knoten, haltungen = stammdaten_lesen(root, zone)
    inspektionen = zustandsdaten_lesen(root)
    format_name = "DWA-M 150" if "150" in lokal(root.tag) or "dwa" in (root.tag or "").lower() else "ISYBAU"
    version = txt(root, "Version")
    if version:
        format_name += f" ({version})"
    return {"knoten": knoten, "haltungen": haltungen, "inspektionen": inspektionen, "format": format_name}
