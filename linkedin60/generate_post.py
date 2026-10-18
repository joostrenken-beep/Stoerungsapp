"""Erstellt einen LinkedIn-Entwurf "60 Sekunden Wasserwirtschaft" und schickt ihn per E-Mail.

Ablauf:
1. Aktuelle Schlagzeilen über Google-News-RSS sammeln.
2. Format, Zielgruppe und Länge wählen, die zuletzt nicht dran waren.
3. Claude recherchiert per Websuche nach (Nachrichten + laufende Debatten)
   und schreibt den Beitrag.
4. Bis 5:30 Uhr (Europe/Berlin) warten, dann E-Mail senden und Verlauf speichern.

Umgebungsvariablen:
  ANTHROPIC_API_KEY     API-Schlüssel für Claude
  GMAIL_USER            Gmail-Adresse, von der gesendet wird
  GMAIL_APP_PASSWORD    App-Passwort dieses Gmail-Kontos
  MAIL_TO               Empfänger (Standard: joost.renken@gmail.com)
  FORCE=1               Zeitprüfung überspringen (manueller Lauf)
  DRY_RUN=1             Nichts senden, nichts speichern, nur ausgeben
"""

import datetime as dt
import html
import json
import os
import random
import re
import smtplib
import sys
import time
import urllib.parse
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
from zoneinfo import ZoneInfo

import anthropic
import feedparser

from stil import FORMATE, KI_VERBOTE, LAENGEN, ZIELGRUPPEN

TZ = ZoneInfo("Europe/Berlin")
SEND_TIME = dt.time(5, 30)
EARLIEST_START = dt.time(5, 0)
HISTORY_FILE = Path(__file__).with_name("history.json")
MODEL = "claude-opus-5-5"
TITEL = "60 Sekunden Wasserwirtschaft"
WOCHENTAGE = ["Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag", "Samstag", "Sonntag"]

NEWS_QUERIES = [
    "Starkregen",
    "Wasserwirtschaft",
    "Stadtentwässerung",
    "Hochwasserschutz Kommune",
    "Schwammstadt",
    "Abwassergebühren",
    "Klimaanpassung Wasser",
    "Elementarschaden Pflichtversicherung",
]


def load_history():
    try:
        return json.loads(HISTORY_FILE.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return []


def save_history(history):
    HISTORY_FILE.write_text(json.dumps(history[-60:], ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def fetch_headlines(per_query=6):
    seen, items = set(), []
    for q in NEWS_QUERIES:
        url = "https://news.google.com/rss/search?" + urllib.parse.urlencode(
            {"q": f"{q} when:7d", "hl": "de", "gl": "DE", "ceid": "DE:de"}
        )
        try:
            feed = feedparser.parse(url)
        except Exception as e:  # ein kaputter Feed soll den Lauf nicht stoppen
            print(f"Feed-Fehler bei '{q}': {e}", file=sys.stderr)
            continue
        for entry in feed.entries[:per_query]:
            title = entry.get("title", "").strip()
            if not title or title in seen:
                continue
            seen.add(title)
            items.append(f"- {title} ({entry.get('published', '')[:16]}) {entry.get('link', '')}")
    return items


def pick_least_recent(options, history, key, avoid_last):
    recent = [h.get(key) for h in history[-avoid_last:]]
    candidates = [o for o in options if o not in recent] or list(options)
    return random.choice(candidates)


def build_prompt(today, headlines, history, fmt, audience, length):
    recent_topics = "\n".join(f"- {h['datum']}: {h.get('thema', '')}" for h in history[-12:]) or "- (noch keine)"
    recent_hooks = "\n".join(f"- {h.get('erste_zeile', '')}" for h in history[-8:]) or "- (noch keine)"
    return f"""Heute ist {WOCHENTAGE[today.weekday()]}, {today:%d.%m.%Y}.

Du schreibst für Joost Renken einen LinkedIn-Beitrag für die Unternehmensseite "Starkregenberatung" in der Reihe "60 Sekunden Wasserwirtschaft". Joost ist Starkregenberater. Der Beitrag soll in 60 Sekunden lesbar sein.

SCHRITT 1: RECHERCHE
Hier sind Schlagzeilen der letzten 7 Tage aus Google News:
{chr(10).join(headlines) if headlines else "(keine Schlagzeilen abrufbar, recherchiere selbst)"}

Nutze die Websuche, um
a) die eine Nachricht zu finden, die sich am besten für einen pointierten Beitrag eignet (aktuell, Deutschland oder DACH bevorzugt, Bezug zu Starkregen, Entwässerung, Klimaanpassung, Gebühren, Politik), und die Fakten dazu nachzulesen,
b) herauszufinden, worüber in der Branche und in sozialen Netzwerken (LinkedIn, Fachpresse, Kommentarspalten) gerade gestritten wird, damit der Beitrag in eine laufende Debatte passt.

Diese Themen hatten wir zuletzt, wiederhole sie nicht:
{recent_topics}

SCHRITT 2: SCHREIBEN
Format: {fmt}. {FORMATE[fmt]}
Zielgruppe: {audience}. {ZIELGRUPPEN[audience]}
Länge: {LAENGEN[length]}.

Ton: Du duzt die Leser. Etwas provokant, zugespitzt, mit klarer Haltung, sodass auch Widerspruch kommt. Fachlich sauber, nie herablassend, keine persönlichen Angriffe. Schreib wie ein erfahrener Praktiker, der morgens um halb sechs einen Kaffee trinkt und sich über etwas ärgert, nicht wie eine Marketingabteilung.

Die erste Zeile muss allein stehen und neugierig machen (unter 120 Zeichen). Sie darf keinem dieser letzten Einstiege ähneln:
{recent_hooks}

Über jedem Beitrag steht automatisch die Überschrift "{TITEL}". Schreib sie NICHT selbst, beginne direkt mit der ersten Zeile des Beitrags.

Absätze: kurze Absätze mit Leerzeilen dazwischen, wie es auf LinkedIn üblich ist. Reiner Text.

Verboten (sonst klingt es nach KI):
{KI_VERBOTE}
AUSGABE
Gib am Ende genau diesen Block aus, ohne weiteren Text danach:

===BEITRAG===
(der fertige Beitrag, exakt so wie er auf LinkedIn stehen soll)
===ALTERNATIVE_ERSTE_ZEILEN===
(zwei alternative erste Zeilen nach der Überschrift, je eine pro Zeile)
===THEMA===
(das Thema in maximal 10 Wörtern)
===QUELLEN===
(die wichtigsten 2 bis 4 Quellen-URLs, je eine pro Zeile)
===ENDE===
"""


def generate(prompt):
    client = anthropic.Anthropic()
    messages = [{"role": "user", "content": prompt}]
    tools = [{"type": "web_search_20260209", "name": "web_search", "max_uses": 8,
              "user_location": {"type": "approximate", "country": "DE", "timezone": "Europe/Berlin"}}]

    for _ in range(5):  # pause_turn kann bei langen Websuchen auftreten
        with client.beta.messages.stream(
            model=MODEL,
            max_tokens=32000,
            output_config={"effort": "high"},
            tools=tools,
            messages=messages,
            betas=["server-side-fallback-2026-07-01"],
            fallbacks="default",
        ) as stream:
            response = stream.get_final_message()

        if response.stop_reason == "pause_turn":
            messages = [messages[0], {"role": "assistant", "content": response.content}]
            continue
        if response.stop_reason == "refusal":
            raise RuntimeError(f"Anfrage abgelehnt: {response.stop_details}")
        break
    else:
        raise RuntimeError("Zu viele pause_turn-Fortsetzungen")

    text = "".join(b.text for b in response.content if b.type == "text")
    return parse_output(text)


def section(text, name):
    m = re.search(rf"==={name}===\s*\n(.*?)\n\s*===", text, re.S)
    return m.group(1).strip() if m else ""


def clean_post(post):
    # Sicherheitsnetz für Dinge, die LinkedIn nicht darstellt oder nach KI aussehen.
    # Eine vom Modell selbst geschriebene Reihenüberschrift entfernen, sie wird einheitlich davorgesetzt.
    lines = post.strip().splitlines()
    if lines and TITEL.lower() in lines[0].lower() and len(lines[0]) < len(TITEL) + 12:
        post = "\n".join(lines[1:])
    post = re.sub(r"\*\*(.+?)\*\*", r"\1", post)
    post = re.sub(r"\s+[–—]\s+", ", ", post)
    post = re.sub(r"[–—]", "-", post)
    post = re.sub(r"\n{3,}", "\n\n", post)
    return post.strip()


def parse_output(text):
    post = section(text, "BEITRAG")
    if not post:
        raise RuntimeError("Antwort enthielt keinen Beitrag:\n" + text[-2000:])
    body = clean_post(post)
    return {
        "beitrag": f"{TITEL}\n\n{body}",
        "erste_zeile": body.splitlines()[0],
        "alternativen": [l.strip() for l in section(text, "ALTERNATIVE_ERSTE_ZEILEN").splitlines() if l.strip()],
        "thema": section(text, "THEMA"),
        "quellen": [l.strip() for l in section(text, "QUELLEN").splitlines() if l.strip()],
    }


def build_email(result, meta, today):
    subject = f"LinkedIn-Entwurf {WOCHENTAGE[today.weekday()][:2]} {today:%d.%m.}: {result['thema'] or TITEL}"
    extras = []
    if result["alternativen"]:
        extras.append("Alternative erste Zeilen:\n" + "\n".join(f"- {a}" for a in result["alternativen"]))
    if result["quellen"]:
        extras.append("Quellen (bitte vor dem Posten kurz prüfen):\n" + "\n".join(result["quellen"]))
    extras.append(f"Format: {meta['format']} | Zielgruppe: {meta['zielgruppe']} | Länge: {meta['laenge']}")

    plain = result["beitrag"] + "\n\n\n" + "-" * 40 + "\n\n" + "\n\n".join(extras) + "\n"

    def block(t):
        return html.escape(t).replace("\n", "<br>")

    rich = f"""<html><body style="font-family:Arial,Helvetica,sans-serif;font-size:15px;color:#111">
<p style="color:#666;font-size:12px">Beitrag markieren, kopieren und in LinkedIn einfügen:</p>
<div style="white-space:pre-wrap;border-left:3px solid #0a66c2;padding:12px 16px;background:#f7f9fb;max-width:640px">{html.escape(result['beitrag'])}</div>
<hr style="margin:28px 0;border:none;border-top:1px solid #ddd">
<div style="color:#555;font-size:13px">{"<br><br>".join(block(e) for e in extras)}</div>
</body></html>"""

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = os.environ["GMAIL_USER"]
    msg["To"] = os.environ.get("MAIL_TO", "joost.renken@gmail.com")
    msg.attach(MIMEText(plain, "plain", "utf-8"))
    msg.attach(MIMEText(rich, "html", "utf-8"))
    return msg


def send_email(msg):
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login(os.environ["GMAIL_USER"], os.environ["GMAIL_APP_PASSWORD"])
        smtp.send_message(msg)


def main():
    force = os.environ.get("FORCE") == "1"
    dry_run = os.environ.get("DRY_RUN") == "1"
    now = dt.datetime.now(TZ)
    today = now.date()
    history = load_history()

    # Zwei Cron-Zeiten decken Sommer- und Winterzeit ab; nur eine davon darf senden.
    if not force:
        if now.time() < EARLIEST_START:
            print(f"Zu früh ({now:%H:%M} Ortszeit), der nächste Lauf übernimmt.")
            return
        if any(h.get("datum") == today.isoformat() and not h.get("manuell") for h in history):
            print("Heute wurde schon ein Entwurf verschickt.")
            return

    fmt = pick_least_recent(FORMATE, history, "format", avoid_last=8)
    audience = pick_least_recent(ZIELGRUPPEN, history, "zielgruppe", avoid_last=2)
    length = pick_least_recent(LAENGEN, history, "laenge", avoid_last=1)
    meta = {"format": fmt, "zielgruppe": audience, "laenge": length}
    print(f"Gewählt: {meta}")

    headlines = fetch_headlines()
    print(f"{len(headlines)} Schlagzeilen gesammelt.")
    result = generate(build_prompt(today, headlines, history, fmt, audience, length))

    if dry_run:
        print("\n" + result["beitrag"] + "\n")
        print(json.dumps({k: v for k, v in result.items() if k != "beitrag"}, ensure_ascii=False, indent=2))
        return

    msg = build_email(result, meta, today)
    if not force:
        send_at = dt.datetime.combine(today, SEND_TIME, TZ)
        wait = (send_at - dt.datetime.now(TZ)).total_seconds()
        if wait > 0:
            print(f"Warte {wait / 60:.0f} Minuten bis {SEND_TIME:%H:%M} Uhr.")
            time.sleep(wait)
    send_email(msg)
    print(f"E-Mail an {msg['To']} gesendet.")

    entry = {"datum": today.isoformat(), **meta, "thema": result["thema"], "erste_zeile": result["erste_zeile"]}
    if force:
        entry["manuell"] = True
    history.append(entry)
    save_history(history)


if __name__ == "__main__":
    main()
