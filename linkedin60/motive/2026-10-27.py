"""Motiv 27.10.2026: Haushaltsentwurf, die Zeile Klimaanpassung wird abgeschnitten, während es draufregnet.

Aufruf: python3 linkedin60/motive/2026-10-27.py
"""
import math
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from PIL import Image, ImageDraw, ImageFilter

from bild import BLAU, DUNKEL, FONT_BOLD, FONT_REGULAR, HELLBLAU, ROT, H, W, font, mit_rahmen

rnd = random.Random(27)
img = Image.new("RGBA", (W, H), (226, 232, 238, 255))
d = ImageDraw.Draw(img)

# Regenwolke oben
wolke = Image.new("RGBA", (W, H))
wd = ImageDraw.Draw(wolke)
for cx, cy, r in ((700, 70, 70), (790, 40, 85), (900, 60, 80), (990, 85, 60), (620, 95, 50), (840, 100, 70)):
    wd.ellipse((cx - r, cy - r, cx + r, cy + r), fill=(120, 134, 150, 255))
img = Image.alpha_composite(img, wolke.filter(ImageFilter.GaussianBlur(2)))
d = ImageDraw.Draw(img)
for _ in range(70):
    x, y = rnd.randint(600, 1040), rnd.randint(140, 230)
    d.line((x, y, x - 4, y + 18), fill=BLAU, width=3)

# Haushaltsblatt, leicht schräg
blatt = Image.new("RGBA", (470, 430))
bd = ImageDraw.Draw(blatt)
bd.rectangle((0, 0, 469, 429), fill="white", outline=(180, 186, 192), width=2)
bd.text((24, 20), "Haushaltsentwurf", font=font(FONT_BOLD, 28), fill=DUNKEL)
bd.line((24, 62, 446, 62), fill=DUNKEL, width=2)
zeilen = ["Pflichtaufgaben", "Personal", "Straßenunterhalt", "Schulen und Kitas", "Feuerwehr"]
for i, z in enumerate(zeilen):
    y = 80 + i * 40
    bd.text((24, y), z, font=font(FONT_REGULAR, 21), fill=DUNKEL)
    bd.line((300, y + 22, 446, y + 22), fill=(205, 210, 216), width=2)
# Pfützen und Tropfen auf dem Papier
for _ in range(10):
    x, y = rnd.randint(30, 430), rnd.randint(70, 290)
    r = rnd.randint(5, 12)
    bd.ellipse((x - r, y - r * 0.7, x + r, y + r * 0.7), fill=HELLBLAU + (120,))
blatt = blatt.rotate(4, expand=True, resample=Image.BICUBIC)
img.alpha_composite(blatt, (590, 205))

# Abgeschnittener Streifen "Klimaanpassung", fällt nach unten weg
streifen = Image.new("RGBA", (470, 64))
sd = ImageDraw.Draw(streifen)
sd.rectangle((0, 0, 469, 63), fill="white", outline=(180, 186, 192), width=2)
sd.text((24, 18), "Klimaanpassung (freiwillig)", font=font(FONT_BOLD, 22), fill=BLAU)
for x in range(0, 470, 16):
    sd.line((x, 0, x + 8, 0), fill=ROT, width=3)
streifen = streifen.rotate(-11, expand=True, resample=Image.BICUBIC)
img.alpha_composite(streifen, (520, 535))
d = ImageDraw.Draw(img)

# Schnittlinie und Schere
d.line((590, 545, 1080, 580), fill=ROT, width=4)
sx, sy = 1080, 580
for a in (-0.35, 0.35):
    ex, ey = sx + math.cos(math.pi + a) * 70, sy + math.sin(math.pi + a) * 70
    d.line((sx, sy, ex, ey), fill=(90, 96, 104), width=8)
for dy in (-26, 26):
    d.ellipse((sx + 6, sy + dy - 18, sx + 42, sy + dy + 18), outline=ROT, width=7)

fh = font(FONT_REGULAR, 13)
d.text((W - 30, H - 14), "Illustration", font=fh, fill=(110, 120, 130), anchor="rs")

mit_rahmen(img, "2026-10-27", "Freiwillige Aufgabe. Fliegt zuerst raus.",
           "Klimaanpassung ist für Kommunen bis heute keine Pflichtaufgabe")
