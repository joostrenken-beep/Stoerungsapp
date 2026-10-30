"""Motiv 30.10.2026: zwei Grundstücke im Regen. Links alles gepflastert, viel Wasser in den Kanal,
dicke Gebührenrechnung. Rechts grüner Garten, das Wasser versickert, dünne Rechnung.

Aufruf: python3 linkedin60/motive/2026-10-30.py
"""
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from PIL import Image, ImageDraw, ImageFilter

from bild import BLAU, DUNKEL, FONT_BOLD, FONT_REGULAR, GRAU, HELLBLAU, ROT, H, W, font, mit_rahmen

rnd = random.Random(30)
img = Image.new("RGBA", (W, H), (200, 210, 220, 255))
d = ImageDraw.Draw(img)

# Wolke und Regen über beiden Grundstücken
wolke = Image.new("RGBA", (W, H))
wd = ImageDraw.Draw(wolke)
for cx, cy, r in ((620, 40, 70), (720, 20, 80), (830, 40, 75), (940, 30, 80), (1050, 45, 70), (1140, 30, 60)):
    wd.ellipse((cx - r, cy - r, cx + r, cy + r), fill=(130, 142, 156, 255))
img = Image.alpha_composite(img, wolke.filter(ImageFilter.GaussianBlur(2)))
d = ImageDraw.Draw(img)
for _ in range(150):
    x, y = rnd.randint(480, W), rnd.randint(90, 250)
    d.line((x, y, x - 4, y + 16), fill=BLAU, width=2)

boden = 470
# Linkes Grundstück: grau, gepflastert, großes Flachdach
d.rectangle((440, boden, 820, H), fill=(150, 154, 160))
for x in range(440, 820, 38):
    d.line((x, boden, x, H), fill=(132, 136, 142), width=2)
for y in range(boden, H, 30):
    d.line((440, y, 820, y), fill=(132, 136, 142), width=2)
d.rectangle((480, 300, 760, boden), fill=GRAU)
d.rectangle((470, 288, 770, 304), fill=(110, 116, 124))
d.rectangle((560, 380, 620, boden), fill=(120, 126, 134))
# Wasser schießt in den Kanal
d.rectangle((440, 600, 820, 640), fill=(90, 96, 104))
for i, x in enumerate(range(470, 800, 45)):
    d.line((x, boden + 10, x + 10, 598), fill=BLAU, width=6)
    d.polygon([(x + 2, 590), (x + 18, 590), (x + 10, 604)], fill=BLAU)
d.rectangle((444, 604, 816, 636), fill=BLAU)

# Rechtes Grundstück: grün, kleines Haus, Baum, Wasser versickert
d.rectangle((820, boden, W, H), fill=(118, 160, 92))
d.rectangle((900, 360, 1060, boden), fill=(232, 226, 214))
d.polygon([(886, 362), (980, 300), (1074, 362)], fill=(150, 70, 60))
d.rectangle((960, 410, 1000, boden), fill=(120, 90, 70))
d.rectangle((1100, 380, 1114, boden), fill=(110, 80, 54))
d.ellipse((1060, 300, 1160, 400), fill=(84, 130, 70))
for x in range(850, W, 40):  # Tropfen versickern
    for y in (boden + 40, boden + 90):
        d.line((x, y, x, y + 14), fill=HELLBLAU, width=3)
d.line((820, boden, 820, H), fill=DUNKEL, width=2)

# Gebührenbescheide
def bescheid(x, y, dick, betrag):
    for k in range(dick):
        d.rectangle((x + k * 4, y - k * 4, x + 110 + k * 4, y + 70 - k * 4), fill="white", outline=DUNKEL, width=2)
    tx, ty = x + (dick - 1) * 4, y - (dick - 1) * 4
    d.text((tx + 10, ty + 8), "Gebühr", font=font(FONT_BOLD, 16), fill=DUNKEL)
    d.text((tx + 10, ty + 32), betrag, font=font(FONT_BOLD, 24), fill=ROT if len(betrag) > 2 else (40, 140, 80))

bescheid(640, 180, 6, "€€€")
bescheid(1040, 210, 1, "€")

d.text((W - 30, H - 14), "Illustration", font=font(FONT_REGULAR, 13), fill=(240, 240, 240), anchor="rs")

mit_rahmen(img, "2026-10-30", "Seit 2004 Pflicht. Ab 2027 Realität.",
           "Gesplittete Regenwassergebühr im Vogtland")
