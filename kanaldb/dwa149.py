"""Schadenskodierung nach DWA-M 149-2 und Zustandsklassen nach DWA-M 149-3.

Die automatische Klassenvorschlag-Funktion ist eine VEREINFACHTE Ableitung
und ersetzt keine Klassifizierung nach DWA-M 149-3 durch Fachpersonal.
Klassen, die in einer Importdatei mitgeliefert werden, haben immer Vorrang.
"""
import json
import os
from functools import lru_cache

ZUSTANDSKLASSEN = {
    0: ("sehr starker Mangel", "Gefahr im Verzug – sofortiger Handlungsbedarf", "#7f1d1d"),
    1: ("starker Mangel", "kurzfristiger Handlungsbedarf", "#dc2626"),
    2: ("mittlerer Mangel", "mittelfristiger Handlungsbedarf", "#f97316"),
    3: ("leichter Mangel", "langfristiger Handlungsbedarf", "#eab308"),
    4: ("geringfügiger Mangel", "kein Handlungsbedarf", "#84cc16"),
    5: ("kein Mangel", "kein Handlungsbedarf", "#16a34a"),
}


@lru_cache(maxsize=1)
def katalog():
    pfad = os.path.join(os.path.dirname(__file__), "daten", "dwa_m149_kodes.json")
    with open(pfad, encoding="utf-8") as f:
        daten = json.load(f)
    daten.pop("_hinweis", None)
    return daten


def _basis_kode(kode):
    """Schachtkodes (D..) auf die entsprechende Haltungsgruppe (B..) abbilden."""
    kode = (kode or "").upper().strip()
    if len(kode) == 3 and kode[0] == "D":
        return "B" + kode[1:]
    return kode


def kode_info(kode):
    return katalog().get(_basis_kode(kode))


def kode_text(kode, char1=None, char2=None):
    info = kode_info(kode)
    if not info:
        return "nicht im Katalog"
    teile = [info["text"]]
    if char1 and info.get("char1", {}).get(char1):
        teile.append(info["char1"][char1])
    if char2 and info.get("char2", {}).get(char2):
        teile.append(info["char2"][char2])
    text = ", ".join(teile)
    if (kode or "").upper().startswith("D"):
        text += " (Schacht)"
    return text


def ist_info_kode(kode):
    info = kode_info(kode)
    return bool(info and info.get("info"))


def _zahl(wert):
    try:
        return float(str(wert).replace(",", "."))
    except (TypeError, ValueError):
        return None


def _nach_prozent(q, grenzen):
    """grenzen: [(ab_wert, klasse), ...] absteigend."""
    if q is None:
        return grenzen[-1][1]
    for ab, klasse in grenzen:
        if q >= ab:
            return klasse
    return grenzen[-1][1]


def klassen_vorschlag(kode, char1=None, char2=None, quant1=None):
    """Liefert (klasse_d, klasse_s, klasse_b) als vereinfachten Vorschlag."""
    k = _basis_kode(kode)
    c1 = (char1 or "").upper()
    q = _zahl(quant1)
    d = s = b = None
    if k == "BAA":
        s = _nach_prozent(q, [(15, 1), (7, 2), (3, 3), (0, 4)])
    elif k == "BAB":
        s, d = {"A": (4, 4), "B": (3, 3), "C": (1, 2)}.get(c1, (3, 3))
    elif k == "BAC":
        s, d = {"A": 1, "B": 0, "C": 0}.get(c1, 1), 1
    elif k == "BAD":
        s = {"A": 2, "B": 1, "C": 1, "D": 0}.get(c1, 2)
    elif k == "BAE":
        s, d = 3, 3
    elif k == "BAF":
        s = 1 if c1 in ("F", "G", "H", "I") else 2 if c1 in ("B", "C", "D", "E") else 3 if c1 in ("J", "K") else 4
    elif k == "BAG":
        b = _nach_prozent(q, [(50, 1), (25, 2), (0, 3)])
    elif k == "BAH":
        d = {"A": 2, "B": 3, "C": 2, "D": 2}.get(c1, 3)
        if c1 == "E":
            b = 1
    elif k == "BAI":
        b, d = 2, 3
    elif k == "BAJ":
        d = (2 if (q or 0) >= 40 else 3) if c1 == "A" else 2 if c1 == "B" else 3
    elif k in ("BAK", "BAL", "BAM"):
        d = 2
    elif k == "BAN":
        d = 1
    elif k == "BAO":
        s, d = 1, 1
    elif k == "BAP":
        s, d = 0, 1
    elif k == "BBA":
        b = _nach_prozent(q, [(50, 1), (10, 2), (0, 3)])
        d = 2
    elif k in ("BBB", "BBC", "BBE"):
        b = _nach_prozent(q, [(50, 1), (25, 2), (10, 3), (0, 4)])
    elif k == "BBD":
        s, d = 1, 1
    elif k == "BBF":
        d = {"A": 3, "B": 2, "C": 1, "D": 0}.get(c1, 2)
    elif k == "BBG":
        d = 1
    elif k == "BBH":
        b = 3
    return d, s, b


def gesamtklasse(*klassen):
    werte = [k for k in klassen if k is not None]
    return min(werte) if werte else None


def zustandsklasse_ermitteln(ziel_typ, ziel_id):
    """Zustandsklasse eines Objekts: schlechteste Klasse der offenen Schäden aus
    der jüngsten Inspektion sowie der manuell erfassten Schäden. Inspiziert ohne
    offene Schäden ergibt Klasse 5, nie inspiziert und ohne Schäden ergibt None."""
    from .models import Inspektion, Schaden

    letzte = (Inspektion.query.filter_by(ziel_typ=ziel_typ, ziel_id=ziel_id)
              .order_by(Inspektion.datum.desc(), Inspektion.id.desc()).first())
    q = Schaden.query.filter(Schaden.ziel_typ == ziel_typ, Schaden.ziel_id == ziel_id,
                             Schaden.status != "saniert", Schaden.schadensklasse.isnot(None))
    if letzte:
        q = q.filter((Schaden.inspektion_id == letzte.id) | (Schaden.inspektion_id.is_(None)))
    else:
        q = q.filter(Schaden.inspektion_id.is_(None))
    klassen = [s.schadensklasse for s in q]
    if klassen:
        return min(klassen), letzte
    if letzte:
        return (letzte.zustandsklasse if letzte.zustandsklasse is not None else 5), letzte
    return None, None


def zustand_aktualisieren(ziel):
    """Schreibt Zustandsklasse (und Datum der letzten Inspektion) an Haltung/Knoten."""
    if not hasattr(ziel, "zustandsklasse"):
        return
    klasse, letzte = zustandsklasse_ermitteln(ziel.ZIEL_TYP, ziel.id)
    ziel.zustandsklasse = klasse
    if hasattr(ziel, "letzte_inspektion"):
        ziel.letzte_inspektion = letzte.datum if letzte else None
