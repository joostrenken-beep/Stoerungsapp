"""Motiv 29.10.2026: Herbst, Dachrinne voller Laub läuft über, Hofablauf zugedeckt, Rechen lehnt unbenutzt.

Aufruf: python3 linkedin60/motive/2026-10-29.py
"""
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from PIL import Image, ImageDraw, ImageFilter

from bild import BLAU, DUNKEL, FONT_BOLD, HELLBLAU, ROT, H, W, font, mit_rahmen

rnd = random.Random(29)
LAUB = [(204, 120, 44), (178, 84, 38), (222, 164, 60), (150, 96, 40)]

img = Image.new("RGBA", (W, H), (150, 162, 176, 255))
d = ImageDraw.Draw(img)

# Herbsthimmel mit Regen
for y in range(H):
    t = y / H
    d.line((0, y, W, y), fill=(int(120 + 40 * t), int(132 + 36 * t), int(150 + 30 * t)))
for _ in range(160):
    x, y = rnd.randint(420, W), rnd.randint(0, 420)
    d.line((x, y, x - 5, y + 20), fill=HELLBLAU + (170,), width=2)

# Hauswand mit Fenster
wx0 = 760
d.rectangle((wx0, 120, W, 560), fill=(226, 220, 208))
d.rectangle((900, 230, 1040, 360), fill=(170, 200, 225), outline=DUNKEL, width=4)
d.line((970, 230, 970, 360), fill=DUNKEL, width=3)
# Dach
d.polygon([(wx0 - 30, 120), (W, 40), (W, 120)], fill=(120, 60, 52))

# Dachrinne voller Laub
d.rounded_rectangle((wx0 - 40, 112, W, 140), radius=8, fill=(140, 146, 152), outline=DUNKEL, width=3)
for _ in range(60):
    x = rnd.randint(wx0 - 36, W - 6)
    y = rnd.randint(98, 122)
    r = rnd.randint(6, 11)
    d.ellipse((x - r, y - r * 0.6, x + r, y + r * 0.6), fill=rnd.choice(LAUB))

# Wasser schwappt vorne über die Rinne (Wasserfall)
fall = Image.new("RGBA", (W, H))
fd = ImageDraw.Draw(fall)
for i in range(10):
    x = wx0 - 30 + i * 9
    fd.line((x, 136, x - 14 + rnd.randint(-4, 4), 560), fill=BLAU + (170,), width=5)
fd.line((wx0 - 40, 136, wx0 - 60, 560), fill=HELLBLAU + (200,), width=3)
img = Image.alpha_composite(img, fall.filter(ImageFilter.GaussianBlur(1)))
d = ImageDraw.Draw(img)

# Fallrohr
d.rectangle((1100, 140, 1124, 560), fill=(140, 146, 152), outline=DUNKEL, width=2)

# Hofpflaster mit Pfütze
d.rectangle((420, 560, W, H), fill=(120, 124, 130))
for x in range(420, W, 60):
    d.line((x, 560, x - 30, H), fill=(105, 108, 114), width=2)
pf = Image.new("RGBA", (W, H))
pd = ImageDraw.Draw(pf)
pd.ellipse((560, 575, 1010, 660), fill=BLAU + (200,))
img = Image.alpha_composite(img, pf.filter(ImageFilter.GaussianBlur(3)))
d = ImageDraw.Draw(img)
# Hofablauf, zugedeckt mit Laub
d.rectangle((760, 600, 830, 630), fill=(60, 64, 70))
for _ in range(14):
    x, y = rnd.randint(752, 838), rnd.randint(592, 636)
    d.ellipse((x - 9, y - 5, x + 9, y + 5), fill=rnd.choice(LAUB))
d.ellipse((740, 582, 850, 648), outline=ROT, width=4)

# Rechen lehnt unbenutzt an der Hauswand
d.line((880, 330, 850, 600), fill=(130, 90, 55), width=7)
d.line((852, 330, 908, 330), fill=(90, 96, 104), width=6)
for i in range(7):
    x = 854 + i * 9
    d.line((x, 330, x, 354), fill=(90, 96, 104), width=3)

# Blätter im Wind
for _ in range(16):
    x, y = rnd.randint(450, 740), rnd.randint(140, 540)
    d.ellipse((x - 8, y - 4, x + 8, y + 4), fill=rnd.choice(LAUB))

mit_rahmen(img, "2026-10-29", "Der Starkregen wartet auf niemanden.",
           "Laub raus aus Dachrinne und Hofablauf")
