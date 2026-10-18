# Kanalbetriebsdatenbank

Web-Anwendung für den Betrieb von Entwässerungsnetzen. Läuft im Browser am PC und auf dem Handy.

- **Kanalnetz:** Haltungen, Schächte, Bauwerke, Auslaufbauwerke und Druckleitungen mit Stammdaten, Höhen, Material und Baujahr
- **Anlagen:** Pumpwerke, Regenrückhaltebecken, Kläranlage, Auslaufbauwerke und weitere Sonderbauwerke, jeweils mit **Anlagenobjekten** (Pumpen, Schieber, Schaltanlage, Fernwirktechnik, Notstrom …)
- **Wartung und Inspektion:** Wartungspläne mit Intervall und Fälligkeitsübersicht. Wird eine Maßnahme erledigt, setzt die Anwendung den nächsten Termin automatisch.
- **Schäden:** Einzelschäden nach **DWA-M 149-2** (Hauptkode, Charakterisierung, Quantifizierung, Station, Uhrlage, Streckenschäden) mit Klassen D/S/B. Die **Zustandsklasse 0–5 nach DWA-M 149-3** wird je Haltung und Schacht ermittelt.
  - Das **Haltungsband** zeigt jeden Einzelschaden an seiner Station.
  - Auf der Karte erscheint jeder Einzelschaden als Punkt an der richtigen Stelle der Leitung, auch bei einer Inspektion gegen die Fließrichtung.
- **Störmeldungen:** Priorität, Status (offen → in Bearbeitung → behoben), Ursache, Maßnahme und Ausfallzeit
  - Fotos lassen sich direkt mit der Handykamera aufnehmen.
  - Der GPS-Standort kann per Knopfdruck übernommen werden.
- **Karte** (OpenStreetMap, Luftbild):
  - Haltungen wahlweise nach Kanalart oder Zustandsklasse eingefärbt
  - Schächte, Anlagen, Einzelschäden und offene Störungen
  - Suche, Filter nach Ortsteil und eigener Standort
- **Import:**
  - **ISYBAU-XML** (Stamm- und Zustandsdaten) und **DWA-M 150-XML**
  - CSV- und Excel-Tabellen
  - **automatischer Import** aus einem Ordner, z. B. einem SharePoint-Ordner, den OneDrive synchronisiert
- **Team:** mehrere Benutzer mit den Rollen *Lesen*, *Bearbeiten* und *Administration*
- **Sonstiges:** CSV-Export, tägliche Datensicherung

## Schnellstart

```bash
python -m venv .venv
.venv/bin/pip install -r requirements.txt        # Windows: .venv\Scripts\pip ...
.venv/bin/flask --app app demo-laden             # Beispielnetz Osterholz-Scharmbeck laden
.venv/bin/flask --app app run --host 0.0.0.0     # http://localhost:5000
```

Unter Windows genügt ein Doppelklick auf `start_windows.bat`.

Demo-Zugänge (Passwort `kanal2026`, bitte sofort ändern): `admin` (Administration), `betrieb` (Bearbeiten), `gast` (Lesen).

Ohne Demodaten legen Sie zuerst einen Administrator an: `flask --app app benutzer-anlegen admin --name "Vorname Name"`.

## Beispieldaten Osterholz-Scharmbeck

Der Befehl `flask --app app demo-laden` erzeugt ein **frei erfundenes** Trennsystem für die Kernstadt und acht Ortsteile:

| | Inhalt |
|---|---|
| Ortsteile | Pennigbüttel, Buschhausen, Scharmbeckstotel, Sandhausen, Teufelsmoor, Heilshorn, Garlstedt, Ohlenstedt |
| Schmutzwasser | Jeder Ortsteil hat ein Pumpwerk und eine Druckleitung ins Netz der Kernstadt. Der Hauptsammler führt zur **Kläranlage Lintel**. |
| Regenwasser | Dezentral: je Quartier bzw. Ortsteil ein Auslaufbauwerk in ein Oberflächengewässer (Scharmbecker Bach, Hamme, Gräben), teils mit Regenrückhaltebecken |
| Umfang | ca. 75 km Kanal, 1.100 Schächte, 29 Anlagen mit 108 Objekten, rund 700 TV-Inspektionen mit über 1.000 Einzelschäden, Wartungspläne und 45 Störmeldungen |

Die Daten durchlaufen den **regulären Import**: Kanalnetz und Inspektionen als ISYBAU-XML, die Anlagen als CSV. Dieselben Dateien liegen im Ordner `demo/` und eignen sich zum Ausprobieren des Imports.

> Lage der Ortsteile und Anlagen ist nur angenähert, die Straßennamen dienen der Orientierung. Leitungsführung, Bauwerke, Schäden und Ereignisse sind fiktiv und geben keine realen Anlagen der Osterholzer Stadtwerke wieder.

## Datenimport

| Format | Inhalt |
|---|---|
| ISYBAU-XML (2006/2013/2017) | Stammdaten (`AbwassertechnischeAnlage`: Knoten/Kante, Geometrie, Höhen, Profil, Material) und Zustandsdaten (`OptischeInspektion`, `RZustand`/`KZustand` mit Kodierung DWA-M 149-2, Streckenschäden A/B, Klassifizierung) |
| DWA-M 150-XML | wie ISYBAU; der Parser arbeitet unabhängig von Namensraum und Version |
| CSV / XLSX | Schächte, Haltungen, Schäden oder Anlagen; der Inhalt wird an den Spaltennamen erkannt (siehe Seite *Import*) |

Koordinaten werden automatisch erkannt:
- ETRS89/UTM Zone 32 mit oder ohne Zonenpräfix (`32490000` bzw. `490000`)
- Gauß-Krüger (DHDN), mit Datumsübergang nach WGS84

So verhält sich ein wiederholter Import:
- Schächte, Haltungen und Anlagen werden über ihre **Bezeichnung** abgeglichen und aktualisiert.
- Eine Inspektion desselben Objekts am selben Tag wird ersetzt.
- Für die Zustandsklasse zählt die jeweils jüngste Inspektion.

### Automatischer Import

Ist `KANALDB_AUTO_IMPORT=1` gesetzt (Standard), prüft die Anwendung den Import-Ordner alle 5 Minuten.
- Erfolgreich importierte Dateien landen in `verarbeitet/`, fehlerhafte in `fehler/`.
- Jeder Import wird protokolliert.

Alternativ lässt sich ein Import per Windows-Aufgabenplanung oder Cron anstoßen: `flask --app app import-ordner`.

## Betrieb mit OneDrive / SharePoint

SharePoint und OneDrive können **keine Programme ausführen**, nur Dateien speichern. Die Anwendung selbst muss deshalb auf einem Rechner laufen, den das Team erreicht. SharePoint bzw. OneDrive übernehmen den Datenaustausch und die Sicherung.

1. **Server:** ein Büro-PC, eine kleine VM oder ein Azure App Service.
   - Starten mit `start_windows.bat` bzw. `waitress-serve --port 8000 app:app`.
   - Das Team öffnet `http://SERVERNAME:8000` im Browser.
   - Unterwegs am Handy geht das per VPN oder über eine HTTPS-Veröffentlichung, z. B. Azure App Service oder Reverse-Proxy.
2. **Import-Ordner = SharePoint-Bibliothek:** Bibliothek „Kanalbetrieb – Import“ auf dem Server mit dem OneDrive-Client synchronisieren und `KANALDB_IMPORT_DIR` auf diesen Ordner setzen. Wer im Team eine ISYBAU-Datei von TV-Firma oder Ingenieurbüro dort ablegt, findet sie wenige Minuten später in der Datenbank.
3. **Sicherungen in OneDrive:** `KANALDB_BACKUP_DIR` auf einen synchronisierten Ordner setzen. Die täglichen Sicherungen landen dann automatisch in der Cloud.
4. **Datenbank selbst lokal halten** (`KANALDB_DATA_DIR`, Standard `./daten`). Eine SQLite-Datei, die gleichzeitig von OneDrive synchronisiert wird, kann beschädigt werden.

| Umgebungsvariable | Bedeutung | Standard |
|---|---|---|
| `KANALDB_DATA_DIR` | Datenbank, Dokumente, Schlüssel | `./daten` |
| `KANALDB_IMPORT_DIR` | überwachter Import-Ordner | `daten/import` |
| `KANALDB_BACKUP_DIR` | Ordner für Sicherungen | `daten/sicherung` |
| `KANALDB_AUTO_IMPORT` | `1` = automatischer Import und tägliche Sicherung | `1` |
| `KANALDB_AUTO_IMPORT_INTERVALL` | Prüfintervall in Sekunden | `300` |
| `KANALDB_DATABASE_URL` | z. B. PostgreSQL statt SQLite | SQLite |
| `KANALDB_SECRET_KEY` | Sitzungsschlüssel (wird sonst erzeugt) | – |
| `KANALDB_UTM_ZONE` | UTM-Zone für 6-stellige Rechtswerte | `32` |

## Handy

- Alle Seiten passen sich an kleine Bildschirme an.
- Über „Zum Startbildschirm hinzufügen“ startet die Anwendung wie eine App.
- Bei Störmeldungen und Schäden lassen sich Fotos direkt aufnehmen und der GPS-Standort übernehmen.
- Auf der Karte zeigt 📍 den eigenen Standort. „Navigation“ öffnet die Route zu Schacht oder Anlage.

## Hinweise und Grenzen

- **Schadensklassen:** Werden mit einem Schaden keine Klassen geliefert (Import oder Eingabe), schlägt die Anwendung eine **vereinfachte** Klassifizierung nach DWA-M 149-3 vor. Das ersetzt keine fachliche Bewertung. Klassen aus der Importdatei haben immer Vorrang.
- **Kodekatalog:** Der Katalog (`kanaldb/daten/dwa_m149_kodes.json`) enthält die Hauptkodes mit den gängigen Charakterisierungen und lässt sich erweitern. Unbekannte Kodes werden trotzdem übernommen.
- **ISYBAU-Import:** Getestet ist der Import mit eigenen ISYBAU-konformen Beispieldateien. Echte Dateien einzelner Programme können Elemente enthalten, die noch nicht ausgewertet werden. Das Importprotokoll zeigt dazu Hinweise.
- **Kartenhintergründe:** Sie werden aus dem Internet geladen (OpenStreetMap, CARTO, Esri). Die Kartenbibliothek Leaflet liegt lokal bei.

## Tests

```bash
pip install pytest && python -m pytest
```
