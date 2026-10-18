# Web-Version (bei Claude gehostet)

Einseitige Fassung der Kanalbetriebsdatenbank, veröffentlicht als Claude-Artefakt:
https://claude.ai/artifact/2PP5pHNFq3M4AcQrWv74Cp

- `netz.json` – Bestandsnetz Osterholz-Scharmbeck (aus der Flask-Demo exportiert mit `export_netz.py`)
- `app.js`, `huelle.html` – Seite; `python web/build.py web` setzt sie zu `kanalbetrieb.html` zusammen
- Veränderliche Daten (Störmeldungen, Wartungspläne, Maßnahmen, Schäden, Importe) liegen in der
  gemeinsamen Datenbank des Artefakts.
