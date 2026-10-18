"""Fiktives Beispiel-Entwässerungsnetz für Osterholz-Scharmbeck (Landkreis Osterholz).

- Schmutzwasser: Trennsystem, alle Ortsteile entwässern über Pumpwerke und
  Druckleitungen in das Netz der Kernstadt; der Hauptsammler führt zur
  Kläranlage Lintel.
- Regenwasser: dezentral, je Quartier/Ortsteil ein Auslaufbauwerk in ein
  Oberflächengewässer, teils mit vorgeschaltetem Regenrückhaltebecken.

Alle Leitungen, Bauwerke, Schäden und Ereignisse sind frei erfunden. Ortsteil-
und Anlagenlagen sind nur angenähert, Straßennamen dienen der Orientierung und
geben keine tatsächliche Leitungsführung wieder.

Die Kanaldaten werden als ISYBAU-XML (Stamm- und Zustandsdaten) und die
Anlagen als CSV erzeugt und über den regulären Import eingelesen.
"""
import math
import os
import random
import tempfile
from datetime import date, datetime, timedelta
from xml.sax.saxutils import escape

from .dwa149 import klassen_vorschlag
from .extensions import db
from .geo import abstand_m, wgs84_nach_utm

KA_LINTEL = (53.2118, 8.7585)
STADT = "27711 Osterholz-Scharmbeck"

KERNSTADT_SAMMLER = [KA_LINTEL, (53.2150, 8.7680), (53.2195, 8.7790), (53.2235, 8.7880), (53.2265, 8.7950),
                     (53.2290, 8.8060), (53.2310, 8.8150)]
SAMMLER_NAMEN = [(0.25, "Am Klärwerk"), (0.6, "Bremer Straße"), (0.82, "Bahnhofstraße"), (1.01, "Bördestraße")]

# Quartiere der Kernstadt: Anschluss an den Hauptsammler (Anteil der Länge), Richtung, Straßen,
# Regenwasser-Auslauf (Richtung, Entfernung, Gewässer, mit RRB?)
QUARTIERE = [
    dict(name="Innenstadt Nord", anteil=0.76, richtung=345, haupt=900, seiten=6, seitlen=240,
         strassen=["Lindenstraße", "Kirchenstraße", "Klosterstraße", "Poststraße", "Rathausstraße", "Koppelstraße",
                   "Lange Straße"],
         auslauf=(250, 260, "Scharmbecker Bach", True), baujahr=(1958, 1975)),
    dict(name="Innenstadt Süd", anteil=0.70, richtung=165, haupt=800, seiten=5, seitlen=230,
         strassen=["Loger Straße", "Feldstraße", "Hafenstraße", "Georgsweg", "Blumenweg", "Gartenstraße"],
         auslauf=(200, 280, "Scharmbecker Bach", True), baujahr=(1962, 1980)),
    dict(name="Musikerviertel", anteil=0.97, richtung=20, haupt=800, seiten=6, seitlen=220,
         strassen=["Schubertring", "Mozartstraße", "Beethovenstraße", "Haydnstraße", "Bachstraße", "Händelweg",
                   "Brahmsweg"],
         auslauf=(110, 220, "Scharmbecker Bach", False), baujahr=(1972, 1988)),
    dict(name="Findorffviertel", anteil=0.50, richtung=320, haupt=900, seiten=6, seitlen=250,
         strassen=["Findorffstraße", "Berliner Straße", "Buchenweg", "Feldhorst", "Waldrand", "Ahornweg",
                   "Eichenweg"],
         auslauf=(270, 260, "Graben am Findorffviertel (fiktiv)", True), baujahr=(1975, 1995)),
    dict(name="Gewerbegebiet Ost", anteil=1.0, richtung=85, haupt=700, seiten=4, seitlen=220,
         strassen=["Teufelsmoorstraße", "Am Pumpelberg", "Gewerbestraße", "Werkstraße", "Lohweg"],
         auslauf=(160, 200, "Scharmbecker Bach", True), baujahr=(1985, 2005)),
]

SEITEN_STANDARD = ["Am Sportplatz", "Schulstraße", "Mühlenweg", "Birkenweg", "Wiesenweg", "Am Moor", "Kirchweg",
                   "Heideweg", "Kastanienweg", "Am Bach", "Tannenweg", "Lerchenweg", "Amselweg", "Rosenweg"]

ORTSTEILE = [
    dict(kurz="PEN", name="Pennigbüttel", wurzel=(53.2410, 8.8270), richtung=40, haupt=900, seiten=5, seitlen=220,
         hoehe=14, baujahr=(1975, 1998), hauptstrasse="Pennigbütteler Straße",
         auslauf=(200, 250, "Scharmbecker Bach", True)),
    dict(kurz="BUS", name="Buschhausen", wurzel=(53.2405, 8.7735), richtung=10, haupt=700, seiten=4, seitlen=200,
         hoehe=9, baujahr=(1980, 2002), hauptstrasse="Buschhauser Straße",
         auslauf=(260, 300, "Graben zur Hamme (fiktiv)", False)),
    dict(kurz="SST", name="Scharmbeckstotel", wurzel=(53.2480, 8.8030), richtung=0, haupt=700, seiten=4,
         seitlen=200, hoehe=16, baujahr=(1985, 2005), hauptstrasse="Scharmbeckstoteler Straße",
         auslauf=(180, 250, "Scharmbecker Bach (Oberlauf)", False)),
    dict(kurz="SAN", name="Sandhausen", wurzel=(53.2010, 8.8180), richtung=100, haupt=800, seiten=5, seitlen=220,
         hoehe=6, baujahr=(1976, 1994), hauptstrasse="Sandhauser Straße",
         auslauf=(190, 250, "Sandhauser Graben (fiktiv)", True)),
    dict(kurz="TEU", name="Teufelsmoor", wurzel=(53.2520, 8.8800), richtung=70, haupt=600, seiten=3, seitlen=200,
         hoehe=3, baujahr=(1985, 2000), hauptstrasse="Teufelsmoorer Straße", auslauf=(250, 200, "Hamme", False)),
    dict(kurz="HEI", name="Heilshorn", wurzel=(53.2590, 8.7200), richtung=30, haupt=800, seiten=5, seitlen=220,
         hoehe=20, baujahr=(1978, 1996), hauptstrasse="Heilshorner Straße",
         auslauf=(220, 250, "Heilshorner Graben (fiktiv)", True)),
    dict(kurz="GAR", name="Garlstedt", wurzel=(53.2745, 8.6990), richtung=60, haupt=900, seiten=5, seitlen=250,
         hoehe=25, baujahr=(1990, 2008), hauptstrasse="Garlstedter Straße",
         auslauf=(240, 250, "Graben Garlstedter Heide (fiktiv)", False)),
    dict(kurz="OHL", name="Ohlenstedt", wurzel=(53.2860, 8.7330), richtung=20, haupt=700, seiten=4, seitlen=200,
         hoehe=28, baujahr=(1982, 2000), hauptstrasse="Ohlenstedter Straße",
         auslauf=(200, 230, "Ohlenstedter Graben (fiktiv)", False)),
]

FIRMEN = ["Kanal-TV Nord GmbH (fiktiv)", "Rohrinspektion Weser-Elbe (fiktiv)", "Hamme Kanalservice (fiktiv)"]
UNTERSUCHER = ["J. Petersen", "M. Brandt", "K. Wiechmann", "S. Lührs"]
PUMPEN_HERSTELLER = ["KSB", "Xylem Flygt", "Sulzer", "Wilo"]
TEAM = ["T. Hollmann", "A. Gerdes", "B. Rugen", "N. Kück"]


# ------------------------------------------------------------------ Geometrie

def versatz(p, richtung_grad, meter):
    b = math.radians(richtung_grad)
    return (p[0] + meter * math.cos(b) / 111_320.0,
            p[1] + meter * math.sin(b) / (111_320.0 * math.cos(math.radians(p[0]))))


def richtung(a, b):
    dy = (b[0] - a[0]) * 111_320.0
    dx = (b[1] - a[1]) * 111_320.0 * math.cos(math.radians(a[0]))
    return math.degrees(math.atan2(dx, dy)) % 360


def linienzug(rng, start, winkel, laenge, abstand=50):
    punkte, gesamt = [start], 0.0
    while gesamt < laenge:
        winkel += rng.uniform(-6, 6)
        schritt = rng.uniform(0.8, 1.25) * abstand
        punkte.append(versatz(punkte[-1], winkel, schritt))
        gesamt += schritt
    return punkte


def stuetzpunkte(ecken, abstand=60):
    punkte = [ecken[0]]
    for a, b in zip(ecken, ecken[1:]):
        n = max(1, round(abstand_m(a, b) / abstand))
        for i in range(1, n + 1):
            punkte.append((a[0] + (b[0] - a[0]) * i / n, a[1] + (b[1] - a[1]) * i / n))
    return punkte


def strassenbaum(rng, wurzel, winkel, haupt, n_seiten, seitlen, hauptname, seitennamen):
    """Hauptstraße ab `wurzel` mit abzweigenden Seitenstraßen.
    Rückgabe: [(name, punkte, (strassen_index, punkt_index) des Anschlusses oder None)]"""
    hauptzug = linienzug(rng, wurzel, winkel, haupt)
    strassen = [(hauptname, hauptzug, None)]
    if len(hauptzug) > 3 and n_seiten:
        schritte = [round(2 + i * (len(hauptzug) - 3) / max(n_seiten - 1, 1)) for i in range(n_seiten)]
        for k, idx in enumerate(schritte):
            seite = 1 if k % 2 == 0 else -1
            w = winkel + seite * 90 + rng.uniform(-15, 15)
            zug = linienzug(rng, hauptzug[idx], w, seitlen * rng.uniform(0.6, 1.2))
            strassen.append((seitennamen[k % len(seitennamen)], zug, (0, idx)))
    return strassen


# ------------------------------------------------------------------ Netzaufbau

class Netz:
    def __init__(self, rng):
        self.rng = rng
        self.knoten = {}
        self.haltungen = []
        self.zaehler = {}

    def neuer_knoten(self, kurz, art, p, ortsteil, strasse, gelaende, sohle, baujahr, knotenart="Schacht",
                     bez=None, material=None):
        if bez is None:
            schluessel = (kurz, art)
            self.zaehler[schluessel] = self.zaehler.get(schluessel, 0) + 1
            bez = f"{kurz}-{'S' if art == 'SW' else 'R'}{self.zaehler[schluessel]:04d}"
        self.knoten[bez] = dict(bezeichnung=bez, kanalart=art, lat=p[0], lon=p[1], ortsteil=ortsteil,
                                strasse=strasse, deckelhoehe=round(gelaende, 2), sohlhoehe=round(sohle, 2),
                                baujahr=baujahr, knotenart=knotenart, material=material or "B")
        return bez

    def neue_haltung(self, von, bis, art, ortsteil, strasse, dn, material, baujahr, funktion="Freispiegel",
                     geometrie=None):
        a, b = self.knoten[von], self.knoten[bis]
        punkte = geometrie or [(a["lat"], a["lon"]), (b["lat"], b["lon"])]
        laenge = sum(abstand_m(p, q) for p, q in zip(punkte, punkte[1:]))
        self.haltungen.append(dict(
            bezeichnung=f"{von}-{bis.split('-')[-1]}", von=von, bis=bis, kanalart=art, ortsteil=ortsteil,
            strasse=strasse, laenge=round(laenge, 2), dn=dn, material=material, baujahr=baujahr, funktion=funktion,
            sohle_zulauf=a["sohlhoehe"] if funktion == "Freispiegel" else None,
            sohle_ablauf=b["sohlhoehe"] if funktion == "Freispiegel" else None, geometrie=punkte))

    def material(self, baujahr, art):
        if baujahr < 1975:
            return self.rng.choice(["STZ", "STZ", "B"]) if art == "SW" else "B"
        if baujahr < 1992:
            return self.rng.choice(["STZ", "B", "PVCU"]) if art == "SW" else self.rng.choice(["B", "B", "STZ"])
        return self.rng.choice(["PVCU", "PP", "STZ"]) if art == "SW" else self.rng.choice(["B", "PP"])

    def baum_verlegen(self, strassen, art, kurz, ortsteil, wurzel_bez, hoehe_wurzel, baujahre, dn_haupt, dn_seite,
                      versatz_m=0.0):
        """Legt Schächte und Haltungen entlang der Straßen an. Fließrichtung zur Wurzel."""
        wurzel = self.knoten[wurzel_bez]
        knoten_je_strasse = []
        for s_idx, (name, punkte, anschluss) in enumerate(strassen):
            w = richtung(punkte[0], punkte[-1])
            verschoben = [versatz(p, w + 90, versatz_m) if versatz_m else p for p in punkte]
            if anschluss is None:
                namen = [wurzel_bez]
            else:
                namen = [knoten_je_strasse[anschluss[0]][anschluss[1]]]
            baujahr = self.rng.randint(*baujahre)
            mat = self.material(baujahr, art)
            for p in verschoben[1:]:
                unten = self.knoten[namen[-1]]
                laenge = abstand_m((unten["lat"], unten["lon"]), p)
                gel = hoehe_wurzel + abstand_m((wurzel["lat"], wurzel["lon"]), p) * 0.004 + self.rng.uniform(-0.3, 0.3)
                gefaelle = self.rng.uniform(0.003, 0.008)
                sohle = max(unten["sohlhoehe"] + 0.002 * laenge,
                            min(unten["sohlhoehe"] + gefaelle * laenge, gel - 1.4))
                bez = self.neuer_knoten(kurz, art, p, ortsteil, name, gel, sohle, baujahr,
                                        material="B" if baujahr < 1990 else self.rng.choice(["B", "PP"]))
                self.neue_haltung(bez, namen[-1], art, ortsteil, name, dn_haupt if s_idx == 0 else dn_seite, mat,
                                  baujahr)
                namen.append(bez)
            knoten_je_strasse.append(namen)
        return knoten_je_strasse

    def naechster_knoten(self, p, art, ausser_praefix):
        beste, abst = None, None
        for bez, k in self.knoten.items():
            if k["kanalart"] != art or bez.startswith(ausser_praefix) or k["knotenart"] != "Schacht":
                continue
            d = abstand_m(p, (k["lat"], k["lon"]))
            if abst is None or d < abst:
                beste, abst = bez, d
        return beste


def netz_erzeugen(seed=2026):
    rng = random.Random(seed)
    netz = Netz(rng)
    anlagen = []

    # Kläranlage und Hauptsammler (Schmutzwasser)
    ka = netz.neuer_knoten("KA", "SW", KA_LINTEL, "Lintel", "Kläranlage Lintel", 2.5, -2.0, 1968,
                           knotenart="Bauwerk", bez="KA-LINTEL-ZUL")
    anlagen.append(dict(bezeichnung="KA-LINTEL", name="Kläranlage Lintel", anlagentyp="Kläranlage",
                        kanalart="SW", ortsteil="Lintel", adresse=f"Lintel, {STADT} (Lage angenähert)",
                        lat=KA_LINTEL[0], lon=KA_LINTEL[1], baujahr=1968, vorfluter="Hamme", knoten=ka,
                        bemerkung="Fiktive Anlagendaten. Zulauf aller Schmutzwasserkanäle der Stadt."))
    sammler = stuetzpunkte(KERNSTADT_SAMMLER, 60)
    sammler_knoten = [ka]
    for i, p in enumerate(sammler[1:], start=1):
        anteil = i / (len(sammler) - 1)
        strasse = next(n for grenze, n in SAMMLER_NAMEN if anteil <= grenze)
        unten = netz.knoten[sammler_knoten[-1]]
        laenge = abstand_m((unten["lat"], unten["lon"]), p)
        gel = 2.5 + abstand_m(KA_LINTEL, p) * 0.004
        sohle = unten["sohlhoehe"] + 0.0018 * laenge
        bez = netz.neuer_knoten("OHZ", "SW", p, "Kernstadt", strasse, gel, sohle, 1965, material="B")
        dn = 800 if anteil < 0.4 else 700 if anteil < 0.7 else 500
        netz.neue_haltung(bez, sammler_knoten[-1], "SW", "Kernstadt", strasse, dn, "B", 1965)
        sammler_knoten.append(bez)

    # Quartiere der Kernstadt
    for q in QUARTIERE:
        idx = min(int(q["anteil"] * (len(sammler_knoten) - 1)), len(sammler_knoten) - 1)
        anschluss = netz.knoten[sammler_knoten[idx]]
        start = (anschluss["lat"], anschluss["lon"])
        strassen = strassenbaum(rng, start, q["richtung"], q["haupt"], q["seiten"], q["seitlen"], q["strassen"][0],
                                q["strassen"][1:])
        netz.baum_verlegen(strassen, "SW", "OHZ", "Kernstadt", sammler_knoten[idx], anschluss["deckelhoehe"],
                           q["baujahr"], 300, 250)
        # Regenwasser: eigener Baum, Auslauf ins Gewässer
        _regenwasser(netz, anlagen, strassen, "OHZ", "Kernstadt", anschluss["deckelhoehe"], q["baujahr"],
                     q["auslauf"], q["name"])

    # Ortsteile mit Pumpwerk und Druckleitung
    for o in ORTSTEILE:
        baujahr_pw = o["baujahr"][0] + rng.randint(0, 5)
        pw = netz.neuer_knoten(o["kurz"], "SW", o["wurzel"], o["name"], o["hauptstrasse"], o["hoehe"],
                               o["hoehe"] - 4.5, baujahr_pw, knotenart="Bauwerk", bez=f"{o['kurz']}-PW01")
        seiten = rng.sample(SEITEN_STANDARD, len(SEITEN_STANDARD))
        strassen = strassenbaum(rng, o["wurzel"], o["richtung"], o["haupt"], o["seiten"], o["seitlen"],
                                o["hauptstrasse"], seiten)
        netz.baum_verlegen(strassen, "SW", o["kurz"], o["name"], pw, o["hoehe"], o["baujahr"], 250, 200)
        ziel = netz.naechster_knoten(o["wurzel"], "SW", o["kurz"])
        z = netz.knoten[ziel]
        netz.neue_haltung(pw, ziel, "SW", o["name"], f"Druckleitung {o['name']}", rng.choice([100, 125, 150]),
                          "PEHD", baujahr_pw, funktion="Druckleitung",
                          geometrie=[o["wurzel"], versatz(o["wurzel"], richtung(o["wurzel"], (z["lat"], z["lon"])) + 25,
                                                          abstand_m(o["wurzel"], (z["lat"], z["lon"])) * 0.4),
                                     (z["lat"], z["lon"])])
        pumpen = rng.choice([2, 2, 2, 3])
        anlagen.append(dict(bezeichnung=f"{o['kurz']}-PW01", name=f"PW {o['name']}", anlagentyp="Pumpwerk",
                            kanalart="SW", ortsteil=o["name"], adresse=f"{o['hauptstrasse']}, {STADT}",
                            lat=o["wurzel"][0], lon=o["wurzel"][1], baujahr=baujahr_pw,
                            volumen_m3=round(rng.uniform(8, 25), 1), knoten=pw, pumpen=pumpen,
                            bemerkung=f"Fördert über Druckleitung in Schacht {ziel}."))
        _regenwasser(netz, anlagen, strassen, o["kurz"], o["name"], o["hoehe"], o["baujahr"], o["auslauf"], o["name"])
    return netz, anlagen


def _regenwasser(netz, anlagen, strassen, kurz, ortsteil, hoehe, baujahre, auslauf, gebietsname):
    rng = netz.rng
    winkel, entfernung, gewaesser, mit_rrb = auslauf
    start = strassen[0][1][0]
    wurzel_p = versatz(start, winkel, 6)
    wurzel = netz.neuer_knoten(kurz, "RW", wurzel_p, ortsteil, strassen[0][0], hoehe, hoehe - 2.2,
                               baujahre[0])
    netz.baum_verlegen(strassen, "RW", kurz, ortsteil, wurzel, hoehe, baujahre, 500, 300, versatz_m=5.0)
    n = sum(1 for a in anlagen if a["anlagentyp"] == "Auslaufbauwerk" and a["bezeichnung"].startswith(kurz)) + 1
    aus_p = versatz(wurzel_p, winkel, entfernung)
    aus = netz.neuer_knoten(kurz, "RW", aus_p, ortsteil, f"Einleitung {gewaesser}", hoehe - 1.0, hoehe - 3.4,
                            baujahre[0], knotenart="Auslaufbauwerk", bez=f"{kurz}-A{n:02d}")
    vorher = wurzel
    if mit_rrb:
        rrb_p = versatz(wurzel_p, winkel, entfernung * 0.6)
        rrb = netz.neuer_knoten(kurz, "RW", rrb_p, ortsteil, f"RRB {gebietsname}", hoehe - 0.6, hoehe - 3.0,
                                baujahre[0] + 10, knotenart="Bauwerk", bez=f"{kurz}-RRB{n:02d}")
        netz.neue_haltung(wurzel, rrb, "RW", ortsteil, f"Zulauf RRB {gebietsname}", 600, "B", baujahre[0] + 10)
        anlagen.append(dict(bezeichnung=f"{kurz}-RRB{n:02d}", name=f"RRB {gebietsname}",
                            anlagentyp="Regenrückhaltebecken", kanalart="RW", ortsteil=ortsteil,
                            adresse=f"nahe {strassen[0][0]}, {STADT}", lat=rrb_p[0], lon=rrb_p[1],
                            baujahr=baujahre[0] + 10, volumen_m3=round(rng.uniform(600, 4500), -1),
                            vorfluter=gewaesser, knoten=rrb,
                            bemerkung="Offenes Erdbecken mit Drosselablauf (fiktiv)."))
        vorher = rrb
    netz.neue_haltung(vorher, aus, "RW", ortsteil, f"Ablauf {gewaesser}", 600, "B", baujahre[0])
    anlagen.append(dict(bezeichnung=f"{kurz}-A{n:02d}", name=f"Auslauf {gebietsname} – {gewaesser}",
                        anlagentyp="Auslaufbauwerk", kanalart="RW", ortsteil=ortsteil,
                        adresse=f"Einleitstelle {gewaesser}", lat=aus_p[0], lon=aus_p[1], baujahr=baujahre[0],
                        vorfluter=gewaesser, knoten=aus,
                        bemerkung="Dezentrale Regenwassereinleitung (fiktiv)."))


# ------------------------------------------------------------------ Zustandsdaten

SCHADEN_GEWICHTE = [("BAB", 15), ("BAJ", 15), ("BBA", 10), ("BBC", 9), ("BAH", 9), ("BAG", 6), ("BBF", 7),
                    ("BAF", 6), ("BBB", 5), ("BAI", 4), ("BAA", 3), ("BBE", 3), ("BAC", 2), ("BAO", 1)]


def _schaden_zufall(rng, kode, laenge):
    c1 = c2 = q1 = None
    if kode == "BAB":
        c1, c2, q1 = rng.choice("AAAABBBC"), rng.choice("AAB"), str(rng.choice([0.2, 0.5, 1, 2, 3]))
    elif kode == "BAJ":
        c1 = rng.choice("AAAB")
        q1 = str(rng.choice([10, 15, 20, 30, 45, 60]))
    elif kode == "BBA":
        c1, q1 = rng.choice("ABBC"), str(rng.choice([5, 5, 10, 10, 15, 25, 40, 60]))
    elif kode in ("BBC", "BBB", "BBE"):
        c1, q1 = rng.choice("AABZ") if kode != "BBE" else rng.choice("ACD"), str(rng.choice([5, 5, 10, 10, 15, 20, 30, 55]))
    elif kode == "BAH":
        c1 = rng.choice("ABCDD")
    elif kode == "BAG":
        q1 = str(rng.choice([10, 20, 30, 50]))
    elif kode == "BBF":
        c1 = rng.choice("AAABBC")
    elif kode == "BAF":
        c1, c2 = rng.choice("AAABBCCEFH"), rng.choice("AB")
    elif kode == "BAI":
        c1, c2 = "A", rng.choice("ABC")
    elif kode == "BAA":
        c1, q1 = "A", str(rng.choice([3, 5, 8, 12, 18]))
    elif kode == "BAC":
        c1 = rng.choice("AAB")
    return c1, c2, q1


def zustandsdaten_erzeugen(netz, seed=2027):
    rng = random.Random(seed)
    heute = date.today()
    inspektionen = []
    kodes, gewichte = zip(*SCHADEN_GEWICHTE)
    for h in netz.haltungen:
        if h["funktion"] != "Freispiegel" or rng.random() > 0.5:
            continue
        datum = heute - timedelta(days=rng.randint(60, 7 * 365))
        alter = datum.year - h["baujahr"]
        n = max(0, int(rng.gauss(alter / 16, 1.2)))
        if h["material"] in ("PVCU", "PP", "PEHD"):
            n = n // 2
        gegen = rng.random() < 0.2
        schaeden = [dict(kode="BCD", station=0.0)]
        for _ in range(n):
            kode = rng.choices(kodes, gewichte)[0]
            if kode == "BAA" and h["material"] not in ("PVCU", "PP", "PEHD"):
                kode = "BAB"
            c1, c2, q1 = _schaden_zufall(rng, kode, h["laenge"])
            s = dict(kode=kode, char1=c1, char2=c2, quant1=q1, station=round(rng.uniform(0.5, h["laenge"] - 0.5), 1),
                     uhr_von=rng.randint(1, 12), uhr_bis=None, verbindung=kode in ("BAJ", "BAI") or rng.random() < 0.3,
                     foto=f"{h['bezeichnung']}_{rng.randint(1, 999):03d}.jpg")
            if rng.random() < 0.7:
                s["klassen"] = klassen_vorschlag(kode, c1, c2, q1)
            if kode == "BAH":
                schaeden.append(dict(kode="BCA", station=s["station"], char1="A"))
            schaeden.append(s)
        if rng.random() < 0.06 and h["laenge"] > 20:
            von = round(rng.uniform(2, h["laenge"] / 2), 1)
            schaeden.append(dict(kode="BBC", char1="A", quant1="20", station=von, strecke="A1",
                                 klassen=klassen_vorschlag("BBC", "A", None, "20")))
            schaeden.append(dict(kode="BBC", char1="A", quant1="20", station=round(von + rng.uniform(5, 15), 1),
                                 strecke="B1"))
        schaeden.append(dict(kode="BCE", station=h["laenge"]))
        schaeden.sort(key=lambda s: s["station"])
        inspektionen.append(dict(objekt=h["bezeichnung"], typ="1", datum=datum, gegen=gegen,
                                 laenge=h["laenge"], schaeden=schaeden))
    for k in netz.knoten.values():
        if k["knotenart"] != "Schacht" or rng.random() > 0.15:
            continue
        datum = heute - timedelta(days=rng.randint(60, 6 * 365))
        schaeden = []
        for _ in range(rng.choice([0, 0, 1, 1, 2, 3])):
            kode = rng.choice(["DAB", "DAF", "DBF", "DAJ", "DAG", "DBB"])
            basis = "B" + kode[1:]
            c1, c2, q1 = _schaden_zufall(rng, basis, 3.0)
            s = dict(kode=kode, char1=c1, char2=c2, quant1=q1,
                     station=round(rng.uniform(0.3, max(k["deckelhoehe"] - k["sohlhoehe"] - 0.2, 0.5)), 2),
                     uhr_von=rng.randint(1, 12))
            s["klassen"] = klassen_vorschlag(kode, c1, c2, q1)
            schaeden.append(s)
        inspektionen.append(dict(objekt=k["bezeichnung"], typ="2", datum=datum, gegen=False, laenge=None,
                                 schaeden=sorted(schaeden, key=lambda s: s["station"])))
    return inspektionen


# ------------------------------------------------------------------ XML / CSV

def _e(name, wert):
    if wert is None:
        return ""
    if isinstance(wert, float):
        wert = f"{wert:.3f}".rstrip("0").rstrip(".")
    return f"<{name}>{escape(str(wert))}</{name}>"


def _punkt_xml(p, attribut=None, hoehe=None, tag="Punkt"):
    e, n = wgs84_nach_utm(p[0], p[1], 32)
    return (f"<{tag}>{_e('PunktattributAbwasser', attribut)}{_e('Rechtswert', round(32_000_000 + e, 3))}"
            f"{_e('Hochwert', round(n, 3))}{_e('Punkthoehe', hoehe)}</{tag}>")


ISYBAU_KOPF = ('<?xml version="1.0" encoding="UTF-8"?>\n'
               '<Identifikation xmlns="http://www.ofd-hannover.la/Identifikation">\n'
               '<Version>2017-07</Version>\n'
               '<Admindaten><Liegenschaft><Liegenschaftsnummer>OHZ-DEMO</Liegenschaftsnummer>'
               '<Liegenschaftsbezeichnung>Osterholz-Scharmbeck – fiktives Beispielnetz</Liegenschaftsbezeichnung>'
               '</Liegenschaft></Admindaten>\n<Datenkollektive>\n'
               '<Datenstatus>2</Datenstatus><Erstellungsdatum>{datum}</Erstellungsdatum>'
               '<Kommentar>Fiktive Beispieldaten – keine realen Leitungen</Kommentar>\n')
ISYBAU_FUSS = "</Datenkollektive>\n</Identifikation>\n"
ART_KZ = {"SW": "KS", "RW": "KR", "MW": "KM"}
PROFIL_ART = {"Kreis": "0"}


def stammdaten_xml(netz):
    teile = [ISYBAU_KOPF.format(datum=date.today().isoformat()), "<Stammdatenkollektiv>\n"]
    for k in netz.knoten.values():
        typ = {"Schacht": "0", "Anschlusspunkt": "1"}.get(k["knotenart"], "2")
        bauwerk = ""
        if typ == "2":
            bauwerk = f"<Bauwerk>{_e('Bauwerkstyp', 'Auslaufbauwerk' if k['knotenart'] == 'Auslaufbauwerk' else 'Sonderbauwerk')}</Bauwerk>"
        teile.append(
            "<AbwassertechnischeAnlage>"
            f"{_e('Objektbezeichnung', k['bezeichnung'])}<Objektart>2</Objektart><Status>0</Status>"
            f"{_e('Baujahr', k['baujahr'])}{_e('Entwaesserungsart', ART_KZ[k['kanalart']])}"
            f"<Lage>{_e('Strassenname', k['strasse'])}{_e('Ortsteilname', k['ortsteil'])}</Lage>"
            f"<Knoten>{_e('KnotenTyp', typ)}<Schacht>{_e('Material', k['material'])}</Schacht>{bauwerk}</Knoten>"
            "<Geometrie><Geometriedaten><Knoten>"
            f"{_punkt_xml((k['lat'], k['lon']), 'DMP', k['deckelhoehe'])}"
            f"{_punkt_xml((k['lat'], k['lon']), 'SMP', k['sohlhoehe'])}"
            "</Knoten></Geometriedaten></Geometrie></AbwassertechnischeAnlage>\n")
    for h in netz.haltungen:
        kanten = "".join(f"<Kante>{_punkt_xml(a, tag='Start')}{_punkt_xml(b, tag='Ende')}</Kante>"
                         for a, b in zip(h["geometrie"], h["geometrie"][1:]))
        teile.append(
            "<AbwassertechnischeAnlage>"
            f"{_e('Objektbezeichnung', h['bezeichnung'])}<Objektart>1</Objektart><Status>0</Status>"
            f"{_e('Baujahr', h['baujahr'])}{_e('Entwaesserungsart', ART_KZ[h['kanalart']])}"
            f"<Lage>{_e('Strassenname', h['strasse'])}{_e('Ortsteilname', h['ortsteil'])}</Lage>"
            f"{_e('Kommentar', 'Druckleitung' if h['funktion'] == 'Druckleitung' else None)}"
            f"<Kante><KantenTyp>0</KantenTyp>{_e('KnotenZulauf', h['von'])}{_e('KnotenAblauf', h['bis'])}"
            f"{_e('SohlhoeheZulauf', h['sohle_zulauf'])}{_e('SohlhoeheAblauf', h['sohle_ablauf'])}"
            f"{_e('Laenge', h['laenge'])}{_e('Material', h['material'])}"
            f"<Profil><Profilart>0</Profilart>{_e('Profilbreite', h['dn'])}{_e('Profilhoehe', h['dn'])}</Profil>"
            "</Kante>"
            f"<Geometrie><Geometriedaten><Kanten>{kanten}</Kanten></Geometriedaten></Geometrie>"
            "</AbwassertechnischeAnlage>\n")
    teile += ["</Stammdatenkollektiv>\n", ISYBAU_FUSS]
    return "".join(teile)


def zustandsdaten_xml(inspektionen, seed=2028):
    rng = random.Random(seed)
    teile = [ISYBAU_KOPF.format(datum=date.today().isoformat()), "<Zustandsdatenkollektiv>\n"]
    for i in inspektionen:
        zustaende = []
        knoten = i["typ"] == "2"
        tag = "KZustand" if knoten else "RZustand"
        for s in i["schaeden"]:
            klassen = ""
            if s.get("klassen"):
                d, st, b = s["klassen"]
                klassen = (f"<Klassifizierung>{_e('Dichtheit', d)}{_e('Standsicherheit', st)}"
                           f"{_e('Betriebssicherheit', b)}</Klassifizierung>")
            station = _e("VertikaleLage", s["station"]) if knoten else _e("Station", s["station"])
            zustaende.append(
                f"<{tag}>{station}{_e('InspektionsKode', s['kode'])}{_e('Charakterisierung1', s.get('char1'))}"
                f"{_e('Charakterisierung2', s.get('char2'))}{_e('Quantifizierung1Numerisch', s.get('quant1'))}"
                f"{_e('Streckenschaden', s.get('strecke'))}{_e('PositionVon', s.get('uhr_von'))}"
                f"{_e('PositionBis', s.get('uhr_bis'))}{_e('Verbindung', 'ja' if s.get('verbindung') else None)}"
                f"{_e('Fotobezeichnung', s.get('foto'))}{klassen}</{tag}>")
        if knoten:
            inhalt = f"<Knoten><Inspektionsdaten>{''.join(zustaende)}</Inspektionsdaten></Knoten>"
        else:
            inhalt = (f"<Rohrleitung>{_e('Inspektionsrichtung', 'U' if i['gegen'] else 'O')}"
                      f"{_e('Inspektionslaenge', i['laenge'])}"
                      f"<Inspektionsdaten>{''.join(zustaende)}</Inspektionsdaten></Rohrleitung>")
        teile.append(
            "<InspizierteAbwassertechnischeAnlage>"
            f"{_e('Objektbezeichnung', i['objekt'])}{_e('Anlagentyp', i['typ'])}"
            f"<OptischeInspektion>{_e('Inspektionsdatum', i['datum'].isoformat())}"
            f"{_e('NameUntersucher', rng.choice(UNTERSUCHER))}{_e('Auftragnehmer', rng.choice(FIRMEN))}"
            f"{inhalt}</OptischeInspektion></InspizierteAbwassertechnischeAnlage>\n")
    teile += ["</Zustandsdatenkollektiv>\n", ISYBAU_FUSS]
    return "".join(teile)


def anlagen_csv(anlagen):
    spalten = ["bezeichnung", "name", "anlagentyp", "kanalart", "ortsteil", "adresse", "lat", "lon", "baujahr",
               "volumen_m3", "vorfluter", "bemerkung"]
    zeilen = [";".join(spalten)]
    for a in anlagen:
        zeilen.append(";".join("" if a.get(s) is None else
                               (f"{a[s]:.7f}".replace(".", ",") if isinstance(a[s], float) and s in ("lat", "lon")
                                else str(a[s]).replace(".", ",") if isinstance(a[s], float) else str(a[s]))
                               for s in spalten))
    return "\n".join(zeilen) + "\n"


def dateien_schreiben(ordner):
    netz, anlagen = netz_erzeugen()
    inspektionen = zustandsdaten_erzeugen(netz)
    os.makedirs(ordner, exist_ok=True)
    dateien = {
        "OHZ_1_Stammdaten_ISYBAU.xml": stammdaten_xml(netz),
        "OHZ_2_Inspektionen_ISYBAU.xml": zustandsdaten_xml(inspektionen),
        "OHZ_3_Anlagen.csv": anlagen_csv(anlagen),
    }
    pfade = []
    for name, inhalt in dateien.items():
        pfad = os.path.join(ordner, name)
        with open(pfad, "w", encoding="utf-8") as f:
            f.write(inhalt)
        pfade.append(pfad)
    return pfade


# ------------------------------------------------------------------ Laden in die Datenbank

def laden(admin_passwort="kanal2026"):
    from .importer import datei_importieren
    from .models import (Anlage, Anlagenobjekt, Benutzer, Haltung, Knoten, Massnahme, Stoermeldung,
                         Wartungsplan)
    from .views.betrieb import monate_addieren

    meldungen = []
    for name, rolle, anzeige in (("admin", "admin", "Administrator"), ("betrieb", "bearbeiter", "Kanalbetrieb"),
                                 ("gast", "leser", "Gastzugang")):
        b = Benutzer.query.filter_by(benutzername=name).first() or Benutzer(benutzername=name)
        b.rolle, b.name = rolle, anzeige
        b.set_passwort(admin_passwort)
        db.session.add(b)
        meldungen.append(f"Benutzer {name} ({rolle}) – Passwort: {admin_passwort}")
    db.session.commit()

    with tempfile.TemporaryDirectory() as tmp:
        for pfad in dateien_schreiben(tmp):
            p = datei_importieren(pfad, "Demo")
            meldungen.append(f"{'OK' if p.erfolgreich else 'FEHLER'} {p.datei}: {p.knoten} Knoten, {p.haltungen} "
                             f"Haltungen, {p.inspektionen} Inspektionen, {p.schaeden} Schäden, {p.anlagen} Anlagen")
            if not p.erfolgreich:
                meldungen.append(p.meldungen or "")
                return meldungen

    rng = random.Random(2029)
    heute = date.today()
    _, anlagen_def = netz_erzeugen()
    for a_def in anlagen_def:
        a = Anlage.query.filter_by(bezeichnung=a_def["bezeichnung"]).first()
        k = Knoten.query.filter_by(bezeichnung=a_def["knoten"]).first()
        if k:
            k.anlage = a
        _objekte_anlegen(rng, a, a_def)
    db.session.flush()

    for a in Anlage.query:
        for plan_def in _plaene_fuer(a):
            _plan_anlegen(rng, "anlage", a.id, *plan_def, heute=heute, monate_addieren=monate_addieren)
        for o in a.objekte:
            if o.objekttyp == "Pumpe":
                _plan_anlegen(rng, "objekt", o.id, f"Pumpenwartung {o.bezeichnung}", "Wartung", 12,
                              "Laufrad, Gleitringdichtung, Ölstand, Isolationswiderstand, Stromaufnahme prüfen",
                              heute=heute, monate_addieren=monate_addieren)
            elif o.objekttyp == "Notstromaggregat":
                _plan_anlegen(rng, "objekt", o.id, "Probelauf Notstrom", "Funktionsprüfung", 3,
                              "Probelauf unter Last 30 min, Kraftstoffstand, Batterie", heute=heute,
                              monate_addieren=monate_addieren)
    sammler = Haltung.query.filter(Haltung.ortsteil == "Kernstadt", Haltung.kanalart == "SW", Haltung.dn >= 500).all()
    for h in sammler[::4]:
        _plan_anlegen(rng, "haltung", h.id, "Hochdruckreinigung Hauptsammler", "Reinigung", 12,
                      "Spülen mit HD-Spülfahrzeug, Sinkkastengut entsorgen", heute=heute,
                      monate_addieren=monate_addieren)
        _plan_anlegen(rng, "haltung", h.id, "TV-Inspektion Hauptsammler", "TV-Inspektion", 120,
                      "Optische Inspektion nach DWA-M 149-2", heute=heute, monate_addieren=monate_addieren)
    db.session.flush()

    _stoerungen_anlegen(rng, heute)
    db.session.commit()
    meldungen.append(f"Anlagen: {Anlage.query.count()}, Objekte: {Anlagenobjekt.query.count()}, "
                     f"Wartungspläne: {Wartungsplan.query.count()}, Maßnahmen: {Massnahme.query.count()}, "
                     f"Störmeldungen: {Stoermeldung.query.count()}")
    return meldungen


def _objekte_anlegen(rng, anlage, a_def):
    from .models import Anlagenobjekt

    def obj(bez, objekttyp, **werte):
        werte.setdefault("baujahr", anlage.baujahr)
        anlage.objekte.append(Anlagenobjekt(bezeichnung=bez, objekttyp=objekttyp, **werte))

    if anlage.anlagentyp == "Pumpwerk":
        hersteller = rng.choice(PUMPEN_HERSTELLER)
        baujahr = max(anlage.baujahr, rng.randint(2005, 2021))
        for i in range(1, a_def.get("pumpen", 2) + 1):
            obj(f"P{i}", "Pumpe", hersteller=hersteller, typ="Tauchmotorpumpe, Freistromrad DN 100",
                seriennummer=f"{rng.randint(10, 99)}-{rng.randint(100000, 999999)}", baujahr=baujahr,
                leistung_kw=rng.choice([3.1, 4.5, 5.5, 7.5]), foerderstrom_ls=rng.choice([8, 10, 12, 15, 18]),
                foerderhoehe_m=rng.choice([12, 15, 18, 22]), betriebsstunden=rng.randint(2000, 40000))
            obj(f"S{i}", "Schieber", typ="Keilschieber DN 100", baujahr=baujahr)
            obj(f"RK{i}", "Rückschlagklappe", typ="Kugelrückschlagventil DN 100", baujahr=baujahr)
        obj("SA", "Schaltanlage", hersteller="(fiktiv)", typ="Pumpensteuerung mit SPS", baujahr=baujahr)
        obj("FW", "Fernwirktechnik", typ="Fernwirkunterstation, Mobilfunk", baujahr=max(baujahr, 2016))
        obj("LS1", "Niveaumessung", typ="Hydrostatische Sonde + Schwimmerschalter", baujahr=baujahr)
        if rng.random() < 0.4:
            obj("NSA", "Notstromaggregat", typ="Diesel 20 kVA (mobil, Einspeisedose)", baujahr=max(baujahr, 2010))
    elif anlage.anlagentyp == "Regenrückhaltebecken":
        obj("DR1", "Drosselorgan", typ="Wirbeldrossel", baujahr=anlage.baujahr)
        obj("NOT", "Sonstiges", typ="Notüberlauf / Überlaufschwelle", baujahr=anlage.baujahr)
        obj("TS", "Sonstiges", typ="Tauchwand / Leichtstoffrückhalt", baujahr=anlage.baujahr)
    elif anlage.anlagentyp == "Kläranlage":
        obj("ZHW-P1", "Pumpe", hersteller="KSB", typ="Zulaufhebewerk Pumpe 1", baujahr=2012,
            leistung_kw=30, foerderstrom_ls=120, foerderhoehe_m=8, betriebsstunden=52000)
        obj("ZHW-P2", "Pumpe", hersteller="KSB", typ="Zulaufhebewerk Pumpe 2", baujahr=2012,
            leistung_kw=30, foerderstrom_ls=120, foerderhoehe_m=8, betriebsstunden=48500)
        obj("ZHW-P3", "Pumpe", hersteller="KSB", typ="Zulaufhebewerk Pumpe 3 (Regenwetter)", baujahr=2012,
            leistung_kw=45, foerderstrom_ls=200, foerderhoehe_m=8, betriebsstunden=6100)
        obj("RE1", "Rechen", typ="Feinrechen 6 mm", baujahr=2009)
        obj("MID", "Durchflussmessung", typ="MID Zulauf DN 600", baujahr=2015)
        obj("NSA", "Notstromaggregat", typ="Diesel 250 kVA", baujahr=2014)


def _plaene_fuer(anlage):
    if anlage.anlagentyp == "Pumpwerk":
        return [("Sichtkontrolle Pumpwerk", "Sichtkontrolle", 1,
                 "Betriebsstunden ablesen, Pumpensumpf, Geruch, Zugänglichkeit, Fernwirk-Meldungen prüfen"),
                ("Reinigung Pumpensumpf", "Reinigung", 6, "Absaugen mit Saugwagen, Schwimmschlamm entfernen"),
                ("Prüfung elektrische Anlage (DGUV V3)", "Prüfung (DGUV/VDE)", 48, "Prüfung ortsfester Anlagen")]
    if anlage.anlagentyp == "Regenrückhaltebecken":
        return [("Kontrolle Drossel und Notüberlauf", "Sichtkontrolle", 3, "Drossel freiräumen, Treibgut entfernen"),
                ("Böschungs- und Grünpflege", "Wartung", 6, "Mahd, Gehölzrückschnitt, Zaunkontrolle"),
                ("Schlammspiegelmessung", "Inspektion", 24, "Sedimenthöhe an 5 Punkten messen")]
    if anlage.anlagentyp == "Auslaufbauwerk":
        return [("Kontrolle Einleitstelle", "Sichtkontrolle", 6, "Rückstauklappe, Kolkschutz, Bewuchs prüfen")]
    if anlage.anlagentyp == "Kläranlage":
        return [("Wartung Zulaufhebewerk", "Wartung", 6, "Gemäß Wartungshandbuch"),
                ("Kalibrierung Zulaufmessung", "Prüfung (DGUV/VDE)", 12, "Vergleichsmessung MID")]
    return []


def _plan_anlegen(rng, ziel_typ, ziel_id, bezeichnung, art, intervall, beschreibung, heute, monate_addieren):
    from .models import Massnahme, Wartungsplan

    letzte = heute - timedelta(days=int(min(intervall, 24) * 30.4 * rng.uniform(0.2, 1.15)))
    plan = Wartungsplan(ziel_typ=ziel_typ, ziel_id=ziel_id, bezeichnung=bezeichnung, art=art,
                        intervall_monate=intervall, letzte_durchfuehrung=letzte,
                        naechste_faelligkeit=monate_addieren(letzte, intervall), zustaendig=rng.choice(TEAM),
                        beschreibung=beschreibung, aktiv=True)
    db.session.add(plan)
    db.session.flush()
    datum = letzte
    for i in range(rng.randint(1, 3) if intervall <= 24 else 1):
        ergebnis = rng.choices(["in Ordnung", "Mängel festgestellt", "nicht in Ordnung"], [80, 17, 3])[0]
        db.session.add(Massnahme(ziel_typ=ziel_typ, ziel_id=ziel_id, wartungsplan_id=plan.id, art=art, datum=datum,
                                 durchgefuehrt_von=rng.choice(TEAM), beschreibung=beschreibung, ergebnis=ergebnis,
                                 befund=None if ergebnis == "in Ordnung" else rng.choice(
                                     ["Leichte Ablagerungen, beim nächsten Termin reinigen",
                                      "Dichtung undicht, Ersatzteil bestellt",
                                      "Schwimmerschalter verschmutzt, gereinigt"]),
                                 dauer_h=round(rng.uniform(0.5, 4), 1), erstellt_von="Demo"))
        datum = monate_addieren(datum, -intervall)


STOERUNGSVORLAGEN = [
    ("objekt", "Pumpe", "Störung Motorschutz {bez}", "Motorschutzschalter ausgelöst, Pumpe läuft nicht an.",
     "Verzopfung Laufrad durch Feuchttücher", "Pumpe gezogen, Laufrad gereinigt, Wiederinbetriebnahme", "hoch"),
    ("objekt", "Pumpe", "Laufzeitüberschreitung {bez}", "Pumpe läuft ungewöhnlich lange, Förderleistung gering.",
     "Verschleiß Laufrad/Spaltring", "Spaltring nachgestellt, Pumpentausch eingeplant", "mittel"),
    ("anlage", "Pumpwerk", "Hochwasseralarm Pumpensumpf", "Niveau im Pumpensumpf über Alarmschwelle.",
     "Starkregen, Fremdwasser über Schachtabdeckungen", "Mobile Pumpe gestellt, Abdeckungen abgedichtet", "kritisch"),
    ("objekt", "Fernwirktechnik", "Kommunikationsausfall Fernwirkstation", "Keine Verbindung zur Leitwarte.",
     "Mobilfunkmodem hängt", "Modem neu gestartet, Antenne geprüft", "mittel"),
    ("anlage", "Pumpwerk", "Geruchsbeschwerde Anwohner", "Anwohner meldet starken Geruch am Pumpwerk.",
     "Lange Aufenthaltszeit in Druckleitung (H2S)", "Spülung, Dosierung Nitrat geprüft", "niedrig"),
    ("anlage", "Regenrückhaltebecken", "Drossel verlegt", "Wasserstand im RRB steigt nach Regen nicht ab.",
     "Treibgut vor Wirbeldrossel", "Drossel freigeräumt", "hoch"),
    ("anlage", "Auslaufbauwerk", "Rückstauklappe blockiert", "Rückstauklappe am Auslauf schließt nicht.",
     "Ast eingeklemmt", "Klappe freigelegt und gängig gemacht", "mittel"),
    ("haltung", None, "Rückstau in Hausanschluss", "Bürger meldet Rückstau im Keller.",
     "Ablagerungen in Haltung", "Haltung mit HD gespült", "hoch"),
    ("knoten", None, "Schachtdeckel klappert", "Deckel klappert bei Überfahrt.",
     "Auflagerring gebrochen", "Deckel neu gebettet", "niedrig"),
    ("knoten", None, "Schachtabdeckung fehlt", "Abdeckung fehlt – Unfallgefahr!",
     "Diebstahl / Vandalismus", "Absicherung, neue Abdeckung gesetzt", "kritisch"),
]


def _stoerungen_anlegen(rng, heute):
    from .models import Anlage, Anlagenobjekt, Haltung, Knoten, Stoermeldung

    pumpen = Anlagenobjekt.query.filter_by(objekttyp="Pumpe").all()
    fernwirk = Anlagenobjekt.query.filter_by(objekttyp="Fernwirktechnik").all()
    anlagen_nach_typ = {}
    for a in Anlage.query:
        anlagen_nach_typ.setdefault(a.anlagentyp, []).append(a)
    haltungen = Haltung.query.filter(Haltung.funktion == "Freispiegel", Haltung.kanalart == "SW").all()
    knoten = Knoten.query.filter_by(knotenart="Schacht").all()
    for i in range(45):
        typ, untertyp, titel, beschreibung, ursache, massnahme, prio = rng.choice(STOERUNGSVORLAGEN)
        if typ == "objekt":
            ziel = rng.choice(pumpen if untertyp == "Pumpe" else fernwirk)
        elif typ == "anlage":
            ziel = rng.choice(anlagen_nach_typ.get(untertyp) or anlagen_nach_typ["Pumpwerk"])
        elif typ == "haltung":
            ziel = rng.choice(haltungen)
        else:
            ziel = rng.choice(knoten)
        tage = rng.randint(0, 3) if i < 6 else rng.randint(4, 700)
        gemeldet = datetime.combine(heute - timedelta(days=tage), datetime.min.time()) + timedelta(
            hours=rng.randint(0, 23), minutes=rng.randint(0, 59))
        if i < 3:
            status = "offen"
        elif i < 6:
            status = "in Bearbeitung"
        else:
            status = "behoben"
        s = Stoermeldung(ziel_typ=typ, ziel_id=ziel.id, titel=titel.format(bez=getattr(ziel, "bezeichnung", "")),
                         beschreibung=beschreibung, gemeldet_am=gemeldet,
                         gemeldet_von=rng.choice(TEAM + ["Leitwarte", "Bürgertelefon"]),
                         meldeweg=rng.choice(["Fernwirktechnik / Alarm", "Telefon", "Bürgermeldung", "Kontrollgang"]),
                         prioritaet=prio, status=status, erstellt_von="Demo")
        if status != "offen":
            s.bearbeiter = rng.choice(TEAM)
            s.ursache = ursache
        if status == "behoben":
            s.massnahme = massnahme
            s.behoben_am = gemeldet + timedelta(hours=rng.uniform(0.5, 30))
            s.ausfallzeit_h = round((s.behoben_am - gemeldet).total_seconds() / 3600, 1)
        db.session.add(s)

