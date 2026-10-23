# 60 Sekunden Wasserwirtschaft: automatische LinkedIn-Entwürfe

Jeden **Dienstag, Donnerstag und Freitag gegen 5:30 Uhr** (deutsche Zeit) erstellt Claude einen fertigen LinkedIn-Entwurf für die Seite *Stark! Regenberatung*. Der Entwurf erscheint im Claude-Chat, du kopierst ihn und fügst ihn auf LinkedIn ein.

Es fallen keine zusätzlichen Kosten an: Das Ganze läuft als geplante Aufgabe in Claude Code über dein Claude-Abo. Kein API-Schlüssel, kein Mailversand, kein Server.

## So funktioniert es

1. `planen.py` wählt Format, Zielgruppe und Länge, die zuletzt nicht dran waren, und gibt den Schreibauftrag aus.
2. Claude recherchiert per Websuche die wichtigste Nachricht der Woche und die laufenden Debatten und schreibt den Beitrag.
3. `speichern.py` bereinigt den Text (keine Gedankenstriche, kein Markdown), setzt die Überschrift **„60 Sekunden Wasserwirtschaft“** davor, legt den Entwurf unter `entwuerfe/<datum>.md` ab und trägt ihn in `history.json` ein.
4. Für jeden Beitrag zeichnet Claude ein **eigenes Bild** zum Thema (z. B. eine Gefahrenkarte, einen Kellerschnitt, ein überlaufendes Rohr): ein kleines Python-Skript unter `motive/<datum>.py`, das die Szene zeichnet und mit `bild.mit_rahmen()` den einheitlichen Rahmen darüberlegt. Der Rahmen enthält Reihentitel, Kernaussage, das Logo von Stark! Regenberatung und klein „KI-generiert“. Ergebnis: `bilder/<datum>.png` (1200 × 675). Klappt das einmal nicht, bleibt das einfache Markenbild aus `bild.erstellen()` als Ersatz. Das Logo liegt in `assets/logo_original.png`.
5. Claude zeigt dir Beitrag und Bild im Chat in einem Kasten zum Kopieren, mit zwei alternativen Einstiegszeilen und den Quellen.

## Abwechslung und Stil

- **13 Formate**, z. B. *Unbequeme These*, *Die Rechnung*, *Offener Brief*, *Eine Zahl*, *Kleine Szene*, *Selbstkritik*
- **4 Zielgruppen-Schwerpunkte:** Geschäftsführung Stadtentwässerung, Bürger, Politik, alle drei gegeneinander
- **3 Längen**
- Themen und Einstiegszeilen der letzten Beiträge werden nicht wiederholt.
- Geduzt, zugespitzt, mit klarer Haltung. Typische KI-Merkmale sind ausdrücklich verboten.

Alles davon steht in [`stil.py`](stil.py) und kann dort angepasst werden.

## Von Hand starten

Schreib im Claude-Chat einfach: *„Erstelle jetzt einen neuen Entwurf für 60 Sekunden Wasserwirtschaft.“*
