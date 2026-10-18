"""Schritt 2: Bereinigt den Entwurf, setzt die Überschrift und speichert ihn.

Aufruf: python3 linkedin60/speichern.py <datei-mit-entwurf>
Schreibt linkedin60/entwuerfe/<datum>.md, ergänzt history.json und gibt den
fertigen Beitrag aus.
"""

import json
import re
import sys
from pathlib import Path

from planen import AUSWAHL_FILE, HIER, HISTORY_FILE, load_history
from stil import TITEL


def section(text, name):
    m = re.search(rf"==={name}===\s*\n(.*?)\n\s*===", text, re.S)
    return m.group(1).strip() if m else ""


def clean_post(post):
    # Eine selbst geschriebene Reihenüberschrift entfernen, sie wird einheitlich davorgesetzt.
    lines = post.strip().splitlines()
    if lines and TITEL.lower() in lines[0].lower() and len(lines[0]) < len(TITEL) + 12:
        post = "\n".join(lines[1:])
    # Sicherheitsnetz für Dinge, die LinkedIn nicht darstellt oder nach KI aussehen.
    post = re.sub(r"\*\*(.+?)\*\*", r"\1", post)
    post = re.sub(r"\s+[–—]\s+", ", ", post)
    post = re.sub(r"[–—]", "-", post)
    post = re.sub(r"\n{3,}", "\n\n", post)
    return post.strip()


def main():
    text = Path(sys.argv[1]).read_text(encoding="utf-8")
    body = section(text, "BEITRAG")
    if not body:
        sys.exit("Kein ===BEITRAG=== Abschnitt gefunden.")
    body = clean_post(body)
    beitrag = f"{TITEL}\n\n{body}"
    alternativen = [l.strip() for l in section(text, "ALTERNATIVE_ERSTE_ZEILEN").splitlines() if l.strip()]
    thema = section(text, "THEMA")
    quellen = [l.strip() for l in section(text, "QUELLEN").splitlines() if l.strip()]

    auswahl = json.loads(AUSWAHL_FILE.read_text(encoding="utf-8"))
    datum = auswahl["datum"]

    archiv = HIER / "entwuerfe" / f"{datum}.md"
    archiv.parent.mkdir(exist_ok=True)
    archiv.write_text(
        f"{beitrag}\n\n---\n\nThema: {thema}\n"
        f"Format: {auswahl['format']} | Zielgruppe: {auswahl['zielgruppe']} | Länge: {auswahl['laenge']}\n\n"
        "Alternative erste Zeilen:\n" + "".join(f"- {a}\n" for a in alternativen) +
        "\nQuellen:\n" + "".join(f"- {q}\n" for q in quellen),
        encoding="utf-8",
    )

    history = [h for h in load_history() if h.get("datum") != datum]
    history.append({**auswahl, "thema": thema, "erste_zeile": body.splitlines()[0]})
    HISTORY_FILE.write_text(json.dumps(history[-60:], ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    AUSWAHL_FILE.unlink()

    print(beitrag)
    print("\n---")
    print("Alternative erste Zeilen:\n" + "\n".join(f"- {a}" for a in alternativen))
    print("Quellen:\n" + "\n".join(f"- {q}" for q in quellen))
    print(f"Format: {auswahl['format']} | Zielgruppe: {auswahl['zielgruppe']} | Länge: {auswahl['laenge']}")
    print(f"Gespeichert: {archiv.relative_to(HIER.parent)}")


if __name__ == "__main__":
    main()
