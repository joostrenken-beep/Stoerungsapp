"""Motiv 22.10.2026: Hausschnitt bei Starkregen, Keller läuft voll, Police schwimmt.

Aufruf: python3 linkedin60/motive/2026-10-22.py
"""
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from PIL import Image, ImageDraw, ImageFilter

from bild import BLAU, DUNKEL, FONT_BOLD, FONT_REGULAR, GRAU, HELLBLAU, ROT, H, W, font, mit_rahmen

rnd = random.Random(22)
img = Image.new("RGBA", (W, H), (70, 86, 104, 255))
d = ImageDraw.Draw(img)

# Himmel mit Regen
for y in range(330):
    t = y / 330
    d.line((0, y, W, y), fill=(int(70 + 40 * t), int(86 + 40 * t), int(104 + 40 * t)))
for _ in range(260):
    x, y = rnd.randint(400, W), rnd.randint(0, 330)
    d.line((x, y, x - 6, y + 22), fill=HELLBLAU + (150,), width=2)

# Erdreich mit Schnittkante
boden_y = 330
d.rectangle((0, boden_y, W, H), fill=(120, 98, 78))
for _ in range(400):
    x, y = rnd.randint(0, W), rnd.randint(boden_y + 5, H)
    d.ellipse((x, y, x + 4, y + 3), fill=(104, 84, 66))
# Wasser auf der Straße
d.rectangle((420, boden_y - 18, W, boden_y + 4), fill=BLAU + (230,))

# Haus
hx0, hx1 = 640, 1020
d.rectangle((hx0, 150, hx1, boden_y), fill=(232, 228, 220))
d.polygon([(hx0 - 30, 152), ((hx0 + hx1) / 2, 50), (hx1 + 30, 152)], fill=(150, 70, 60))
for wx in (690, 860):
    d.rectangle((wx, 200, wx + 90, 270), fill=(170, 200, 225), outline=DUNKEL, width=3)
d.rectangle((800, 245, 850, boden_y), fill=(120, 90, 70))

# Keller im Schnitt, halb voll Wasser
kx0, kx1, ky0, ky1 = hx0 + 20, hx1 - 20, boden_y + 10, 590
d.rectangle((hx0, boden_y, hx1, ky1 + 20), fill=(150, 150, 150))
d.rectangle((kx0, ky0, kx1, ky1), fill=(214, 210, 200))
wasser = Image.new("RGBA", (W, H))
wd = ImageDraw.Draw(wasser)
wd.rectangle((kx0, 470, kx1, ky1), fill=BLAU + (200,))
for i in range(4):
    wd.arc((kx0 + i * 90, 460, kx0 + i * 90 + 90, 480), 0, 180, fill=HELLBLAU + (220,), width=3)
img = Image.alpha_composite(img, wasser)
d = ImageDraw.Draw(img)
# Regale/Kartons, halb unter Wasser
for bx in (kx0 + 30, kx0 + 120, kx0 + 210):
    d.rectangle((bx, 430, bx + 70, 520), outline=(150, 120, 80), width=3)

# Kanal mit Rückstau und Klappe
d.rectangle((420, 560, kx0, 590), fill=GRAU, outline=DUNKEL, width=2)
d.rectangle((420, 562, kx0, 588), fill=BLAU + (255,))
d.line((kx0 - 6, 556, kx0 - 6, 594), fill=ROT, width=6)
fl = font(FONT_BOLD, 18)
d.rounded_rectangle((440, 600, 640, 634), radius=8, fill="white", outline=ROT, width=2)
d.text((452, 617), "Rückstauklappe?", font=fl, fill=DUNKEL, anchor="lm")

# Schwimmende Versicherungspolice
pol = Image.new("RGBA", (150, 110))
pd = ImageDraw.Draw(pol)
pd.rectangle((0, 0, 149, 109), fill="white", outline=DUNKEL, width=3)
pd.text((12, 10), "POLICE", font=font(FONT_BOLD, 22), fill=DUNKEL)
pd.text((12, 42), "Elementar-", font=font(FONT_REGULAR, 16), fill=DUNKEL)
pd.text((12, 62), "schutz", font=font(FONT_REGULAR, 16), fill=DUNKEL)
pd.line((100, 85, 112, 97, 136, 70), fill=(40, 140, 80), width=5)
pol = pol.rotate(-12, expand=True, resample=Image.BICUBIC)
img.alpha_composite(pol, (kx1 - 190, 405))
d = ImageDraw.Draw(img)

fh = font(FONT_REGULAR, 13)
d.text((W - 30, H - 16), "Illustration", font=fh, fill=(235, 225, 210), anchor="rs")

mit_rahmen(img, "2026-10-22", "Versichert ist nicht trocken.",
           "Eckpunkte vom 21.10.: Elementarschutz soll Standard werden")
