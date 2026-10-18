"""Stil-Katalog für "60 Sekunden Wasserwirtschaft".

Hier kannst du Formate, Perspektiven und Verbote anpassen, ohne den
restlichen Code anzufassen. Pro Lauf wird ein Format, ein Zielgruppen-Fokus
und eine Länge gewählt, die in den letzten Beiträgen nicht vorkamen.
"""

TITEL = "60 Sekunden Wasserwirtschaft"

# Jedes Format ist ein anderer Bauplan. Name = Kurzlabel, Text = Anweisung.
FORMATE = {
    "Unbequeme These": (
        "Starte mit einer klaren, unbequemen Behauptung in einem Satz. "
        "Begründe sie knapp mit dem aktuellen Anlass. Benenne, wer widersprechen wird und warum er trotzdem falsch liegt."
    ),
    "Die Rechnung": (
        "Mach eine konkrete Rechnung auf: Was kostet Vorsorge, was kostet der Schaden? "
        "Nutze echte Zahlen aus den Quellen, grob gerundet. Kein Fließtext-Gejammer, die Zahlen sollen sprechen."
    ),
    "Offener Brief": (
        "Schreib den Beitrag als kurzen, direkten Brief an eine Gruppe (z. B. 'Liebe Bürgermeisterinnen und Bürgermeister', "
        "'Liebe Hausbesitzer', 'Liebe Stadtwerke-Chefs'). Persönlich, fordernd, nicht belehrend."
    ),
    "Mythos zerlegt": (
        "Nimm einen Satz, den man in Gemeinderäten oder am Gartenzaun ständig hört (in Anführungszeichen), "
        "und zerleg ihn mit dem aktuellen Anlass. Kein Schema 'Mythos/Fakt' mit Überschriften."
    ),
    "Kleine Szene": (
        "Beginne mit einer kurzen, konkreten Szene (Keller, Ratssitzung, Baustelle, Bürgerversammlung), "
        "erzählt in der Ich-Form oder beobachtend. Erst danach der Bezug zur Nachricht. Kein Märchenton."
    ),
    "Eine Zahl": (
        "Der Beitrag dreht sich um genau eine Zahl aus den aktuellen Nachrichten. Die Zahl steht allein in der ersten Zeile. "
        "Dann: was sie bedeutet, und was daran niemand hören will."
    ),
    "Blick über den Zaun": (
        "Vergleiche, wie ein anderes Land, eine andere Stadt oder eine andere Branche das Problem löst, "
        "und frag provokant, warum es bei uns nicht geht."
    ),
    "Pro und Contra im Kopf": (
        "Spiel einen kurzen inneren Schlagabtausch durch: Was sagt der Kämmerer, was sagt der Bürger, was sagt der Planer? "
        "Jede Stimme ein bis zwei Sätze. Am Ende deine eigene, klare Position."
    ),
    "Was keiner sagt": (
        "Formuliere, was in der Branche alle denken, aber öffentlich keiner ausspricht. "
        "Ehrlich, ein bisschen frech, ohne jemanden persönlich anzugreifen."
    ),
    "Kurz und trocken": (
        "Sehr kurzer Beitrag, maximal 6 Zeilen. Ein trockener, pointierter Kommentar zur Nachricht. Fast wie ein Tweet."
    ),
    "Szenario 2035": (
        "Spiel durch, wie es 2035 aussieht, wenn wir so weitermachen wie heute, bezogen auf den aktuellen Anlass. "
        "Konkret und nüchtern, kein Weltuntergangskitsch."
    ),
    "Frage an die Politik": (
        "Stelle drei bis vier unbequeme Fragen zum aktuellen Anlass, die du gern einem Landrat, Minister oder Gemeinderat stellen würdest. "
        "Keine Antworten liefern, die Fragen sollen hängen bleiben."
    ),
    "Selbstkritik": (
        "Kritisiere die eigene Zunft (Entwässerungsbetriebe, Planer, Berater wie dich). Wo machen wir es uns zu bequem? "
        "Das erzeugt Glaubwürdigkeit und Widerspruch aus den eigenen Reihen."
    ),
}

ZIELGRUPPEN = {
    "Geschäftsführung Stadtentwässerung": (
        "Sprich vor allem Geschäftsführer und Werkleiter von Stadtentwässerungen und Abwasserbetrieben an: "
        "Gebühren, Investitionsstau, Personal, Haftung, Prioritäten."
    ),
    "Bürgerinnen und Bürger": (
        "Sprich vor allem Bürger und Hausbesitzer an: eigener Keller, Rückstauklappe, Versicherung, "
        "versiegelte Vorgärten, Eigenverantwortung. Keine Fachbegriffe ohne Übersetzung."
    ),
    "Kommunalpolitik und Landespolitik": (
        "Sprich vor allem Bürgermeister, Gemeinderäte und Landespolitik an: Bauleitplanung, Förderprogramme, "
        "Prioritäten im Haushalt, Mut zu unpopulären Entscheidungen."
    ),
    "Alle drei gegeneinander": (
        "Stell die Interessen von Betreibern, Bürgern und Politik gegeneinander. Jeder schiebt die Verantwortung weiter, zeig das."
    ),
}

LAENGEN = {
    "kurz": "etwa 40 bis 80 Wörter",
    "mittel": "etwa 100 bis 160 Wörter",
    "lang": "etwa 180 bis 250 Wörter",
}

# Dinge, an denen man KI-Texte erkennt. Werden dem Modell ausdrücklich verboten.
KI_VERBOTE = """\
- Keine Gedankenstriche (– oder —) als Stilmittel. Nutze Punkt, Komma oder Doppelpunkt.
- Keine Einstiege wie "In der heutigen Zeit", "Stell dir vor", "Lass uns ehrlich sein", "Hand aufs Herz", "Spoiler:".
- Keine Wörter wie "Gamechanger", "spannend", "essenziell", "entscheidend", "ganzheitlich", "nachhaltig" als Füllwort, "Herausforderungen und Chancen", "in Zeiten von".
- Keine Dreier-Aufzählungen aus Gewohnheit ("schnell, effizient und nachhaltig").
- Keine Emoji-Listen, keine Pfeile (→, 👉), höchstens ein Emoji im ganzen Beitrag, gern gar keins.
- Keine Zwischenüberschriften, kein "Fazit:", keine Zusammenfassung am Ende.
- Kein Schluss mit "Was denkst du? 👇" oder "Lass es mich in den Kommentaren wissen". Wenn du am Ende fragst, dann eine konkrete, zugespitzte Frage, bei der man Position beziehen muss.
- Kein Markdown (keine **Sternchen**, keine #-Überschriften), LinkedIn zeigt das nicht an.
- Höchstens 3 Hashtags, ganz am Ende, in einer Zeile.
- Unterschiedliche Satzlängen. Auch mal ein Satz mit zwei Wörtern. Auch mal ein unvollständiger Satz.
- Konkret statt allgemein: Orte, Zahlen, Namen von Programmen oder Gesetzen, wenn sie in den Quellen stehen.
- Keine erfundenen Zahlen oder Zitate. Nur was in den Quellen steht.
"""
