# 60 Sekunden Wasserwirtschaft: automatische LinkedIn-Entwürfe

Jeden **Dienstag, Donnerstag und Freitag um 5:30 Uhr** (deutsche Zeit) kommt ein fertiger LinkedIn-Entwurf für die Seite *Starkregenberatung* per E-Mail. Du kopierst den Text, fügst ihn auf LinkedIn ein, fertig.

## So funktioniert es

1. **Nachrichten:** Schlagzeilen der letzten 7 Tage aus Google News (Starkregen, Stadtentwässerung, Schwammstadt, Abwassergebühren, Elementarschaden …).
2. **Recherche:** Claude prüft per Websuche die Fakten und schaut, worüber in Branche, Fachpresse und sozialen Netzwerken gerade gestritten wird.
3. **Abwechslung:** Jedes Mal ein anderes Format (13 Varianten, z. B. *Unbequeme These*, *Die Rechnung*, *Offener Brief*, *Kleine Szene*, *Selbstkritik*), ein anderer Zielgruppen-Fokus (Geschäftsführung Stadtentwässerung, Bürger, Politik) und eine andere Länge. Themen und erste Zeilen der letzten Beiträge werden nicht wiederholt.
4. **Ton:** geduzt, zugespitzt, mit klarer Haltung. Typische KI-Merkmale sind ausdrücklich verboten (Gedankenstriche, Emoji-Listen, „Was denkst du? 👇“, Hashtag-Wände, Markdown …).
5. **Überschrift:** Jeder Beitrag beginnt mit der Zeile „60 Sekunden Wasserwirtschaft“. Sie wird vom Programm gesetzt, nicht von der KI, und fehlt deshalb nie.
6. **E-Mail:** oben der Beitrag zum Kopieren, darunter zwei alternative erste Zeilen und die Quellen zum Gegenprüfen.

Formate, Zielgruppen und Verbote kannst du in [`stil.py`](stil.py) anpassen.

## Einmalige Einrichtung

### 1. Anthropic-API-Schlüssel
Auf <https://platform.claude.com> einen API-Schlüssel anlegen. Die Kosten liegen bei wenigen Cent pro Beitrag (Websuche inklusive).

### 2. Gmail-App-Passwort (zum Versenden)
1. Im Google-Konto, von dem gesendet werden soll, die **Bestätigung in zwei Schritten** aktivieren.
2. Unter <https://myaccount.google.com/apppasswords> ein App-Passwort erzeugen (Name z. B. „LinkedIn60“).
3. Das 16-stellige Passwort notieren.

Du kannst dir die Mails auch von deinem eigenen Gmail-Konto an dich selbst schicken.

### 3. Secrets im GitHub-Repository hinterlegen
*Settings → Secrets and variables → Actions → New repository secret*

| Name | Inhalt |
|---|---|
| `ANTHROPIC_API_KEY` | der API-Schlüssel aus Schritt 1 |
| `GMAIL_USER` | die Gmail-Adresse, von der gesendet wird |
| `GMAIL_APP_PASSWORD` | das App-Passwort aus Schritt 2 |

Optional unter *Variables*: `MAIL_TO`, wenn die Mails an eine andere Adresse als `joost.renken@gmail.com` gehen sollen.

### 4. In den Hauptzweig übernehmen
GitHub führt Zeitpläne nur im Standardzweig (`main`) aus. Der Workflow muss also nach `main` gemergt werden.

### 5. Testen
*Actions → LinkedIn-Entwurf „60 Sekunden Wasserwirtschaft“ → Run workflow*. Ein manueller Lauf sendet sofort, ohne auf 5:30 Uhr zu warten.

## Lokal ausprobieren

```bash
cd linkedin60
pip install -r requirements.txt
export ANTHROPIC_API_KEY=...
DRY_RUN=1 FORCE=1 python generate_post.py   # zeigt den Beitrag nur an, sendet nichts
```

## Gut zu wissen

- **Uhrzeit:** GitHub-Zeitpläne laufen in UTC und starten manchmal verspätet. Deshalb startet der Workflow gegen 5:10 Uhr, erstellt den Beitrag und wartet mit dem Senden bis 5:30 Uhr. Sommer- und Winterzeit sind abgedeckt.
- **Verlauf:** `history.json` merkt sich die letzten Beiträge (Datum, Format, Thema, erste Zeile), damit nichts doppelt kommt. Der Workflow speichert die Datei automatisch.
- **Inaktivität:** GitHub pausiert Zeitpläne, wenn ein Repository 60 Tage lang keine Aktivität hat. Die automatischen Verlaufs-Commits halten es normalerweise aktiv. Falls doch einmal pausiert: unter *Actions* wieder aktivieren.
- **Direkt auf LinkedIn posten** ist bewusst nicht eingebaut. Dafür bräuchte es eine von LinkedIn freigegebene App (Community Management API), und du behältst so die Kontrolle über jeden Beitrag.
