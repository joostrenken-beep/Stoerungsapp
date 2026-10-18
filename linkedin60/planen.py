"""Schritt 1: Wählt Format, Zielgruppe und Länge und gibt den Schreibauftrag aus.

Aufruf: python3 linkedin60/planen.py
Die Auswahl wird in linkedin60/.auswahl.json zwischengespeichert, damit
speichern.py sie in den Verlauf übernehmen kann.
"""

import datetime as dt
import json
import random
from pathlib import Path
from zoneinfo import ZoneInfo

from stil import FORMATE, KI_VERBOTE, LAENGEN, TITEL, ZIELGRUPPEN

HIER = Path(__file__).parent
HISTORY_FILE = HIER / "history.json"
AUSWAHL_FILE = HIER / ".auswahl.json"
WOCHENTAGE = ["Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag", "Samstag", "Sonntag"]


def load_history():
    try:
        return json.loads(HISTORY_FILE.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return []


def pick_least_recent(options, history, key, avoid_last):
    recent = [h.get(key) for h in history[-avoid_last:]]
    candidates = [o for o in options if o not in recent] or list(options)
    return random.choice(candidates)


def build_brief(today, history, fmt, audience, length):
    recent_topics = "\n".join(f"- {h['datum']}: {h.get('thema', '')}" for h in history[-12:]) or "- (noch keine)"
    recent_hooks = "\n".join(f"- {h.get('erste_zeile', '')}" for h in history[-8:]) or "- (noch keine)"
    return f"""Heute ist {WOCHENTAGE[today.weekday()]}, {today:%d.%m.%Y}.

Du schreibst für Joost Renken einen LinkedIn-Beitrag für die Unternehmensseite "Starkregenberatung" in der Reihe "{TITEL}". Joost ist Starkregenberater. Der Beitrag soll in 60 Sekunden lesbar sein.

SCHRITT 1: RECHERCHE (mit der Websuche, mehrere Suchen)
a) Finde die eine Nachricht der letzten 7 Tage, die sich am besten für einen pointierten Beitrag eignet: aktuell, Deutschland oder DACH bevorzugt, Bezug zu Starkregen, Entwässerung, Klimaanpassung, Schwammstadt, Abwassergebühren, Elementarschaden, Kommunal- oder Landespolitik. Lies die Fakten dazu nach.
b) Finde heraus, worüber in der Branche und in sozialen Netzwerken (LinkedIn, Fachpresse, Kommentarspalten) gerade gestritten wird, damit der Beitrag in eine laufende Debatte passt.

Diese Themen hatten wir zuletzt, wiederhole sie nicht:
{recent_topics}

SCHRITT 2: SCHREIBEN
Format: {fmt}. {FORMATE[fmt]}
Zielgruppe: {audience}. {ZIELGRUPPEN[audience]}
Länge: {LAENGEN[length]}.

Ton: Du duzt die Leser. Etwas provokant, zugespitzt, mit klarer Haltung, sodass auch Widerspruch kommt. Fachlich sauber, nie herablassend, keine persönlichen Angriffe. Schreib wie ein erfahrener Praktiker, der morgens um halb sechs einen Kaffee trinkt und sich über etwas ärgert, nicht wie eine Marketingabteilung.

Über jedem Beitrag steht automatisch die Überschrift "{TITEL}". Schreib sie NICHT selbst, beginne direkt mit der ersten Zeile des Beitrags.

Die erste Zeile muss allein stehen und neugierig machen (unter 120 Zeichen). Sie darf keinem dieser letzten Einstiege ähneln:
{recent_hooks}

Absätze: kurze Absätze mit Leerzeilen dazwischen, wie es auf LinkedIn üblich ist. Reiner Text.

Verboten (sonst klingt es nach KI):
{KI_VERBOTE}
SCHRITT 3: AUSGABE
Schreib das Ergebnis in eine Textdatei mit genau diesem Aufbau und gib sie an speichern.py weiter:

===BEITRAG===
(der fertige Beitrag ohne Überschrift, exakt so wie er auf LinkedIn stehen soll)
===ALTERNATIVE_ERSTE_ZEILEN===
(zwei alternative erste Zeilen, je eine pro Zeile)
===THEMA===
(das Thema in maximal 10 Wörtern)
===QUELLEN===
(die wichtigsten 2 bis 4 Quellen-URLs, je eine pro Zeile)
===ENDE===
"""


def main():
    today = dt.datetime.now(ZoneInfo("Europe/Berlin")).date()
    history = load_history()
    auswahl = {
        "datum": today.isoformat(),
        "format": pick_least_recent(FORMATE, history, "format", avoid_last=8),
        "zielgruppe": pick_least_recent(ZIELGRUPPEN, history, "zielgruppe", avoid_last=2),
        "laenge": pick_least_recent(LAENGEN, history, "laenge", avoid_last=1),
    }
    AUSWAHL_FILE.write_text(json.dumps(auswahl, ensure_ascii=False), encoding="utf-8")
    print(build_brief(today, history, auswahl["format"], auswahl["zielgruppe"], auswahl["laenge"]))


if __name__ == "__main__":
    main()
