"""Motiv Testbeitrag 23.10.2026: Ratssaal spät abends, TOP 9 Starkregen, Stempel VERTAGT.

Aufruf: python3 linkedin60/motive/test-2026-10-23.py
"""
import math
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from PIL import Image, ImageDraw

from bild import BLAU, DUNKEL, FONT_BOLD, FONT_REGULAR, HELLBLAU, ROT, H, W, font, mit_rahmen

rnd = random.Random(9)
img = Image.new("RGBA", (W, H), (214, 205, 190, 255))
d = ImageDraw.Draw(img)

# Holzvertäfelung
for x in range(0, W, 60):
    d.line((x, 0, x, 400), fill=(196, 186, 170), width=2)

# Fenster mit Nacht und Regen
fx0, fy0, fx1, fy1 = 520, 60, 760, 330
d.rectangle((fx0 - 10, fy0 - 10, fx1 + 10, fy1 + 10), fill=(120, 100, 80))
d.rectangle((fx0, fy0, fx1, fy1), fill=(36, 48, 66))
for _ in range(90):
    x, y = rnd.randint(fx0 + 4, fx1 - 10), rnd.randint(fy0, fy1 - 20)
    d.line((x, y, x - 3, y + 16), fill=HELLBLAU, width=2)
d.line(((fx0 + fx1) / 2, fy0, (fx0 + fx1) / 2, fy1), fill=(120, 100, 80), width=8)
d.line((fx0, (fy0 + fy1) / 2, fx1, (fy0 + fy1) / 2), fill=(120, 100, 80), width=8)

# Wanduhr 22:10
cx, cy, r = 960, 140, 70
d.ellipse((cx - r - 8, cy - r - 8, cx + r + 8, cy + r + 8), fill=DUNKEL)
d.ellipse((cx - r, cy - r, cx + r, cy + r), fill="white")
for i in range(12):
    a = i / 12 * 2 * math.pi
    d.line((cx + math.sin(a) * (r - 6), cy - math.cos(a) * (r - 6), cx + math.sin(a) * (r - 16), cy - math.cos(a) * (r - 16)), fill=DUNKEL, width=4)
ah = (22 % 12 + 10 / 60) / 12 * 2 * math.pi
am = 10 / 60 * 2 * math.pi
d.line((cx, cy, cx + math.sin(ah) * 36, cy - math.cos(ah) * 36), fill=DUNKEL, width=7)
d.line((cx, cy, cx + math.sin(am) * 56, cy - math.cos(am) * 56), fill=DUNKEL, width=4)
d.ellipse((cx - 6, cy - 6, cx + 6, cy + 6), fill=ROT)

# Ratstisch
d.polygon([(380, 430), (W, 400), (W, 520), (380, 560)], fill=(130, 92, 62))
d.polygon([(380, 560), (W, 520), (W, H), (380, H)], fill=(104, 72, 48))
# leere Namensschilder und Mikrofone
for i, x in enumerate((560, 760, 960)):
    y = 430 - (x - 380) * 30 / 820
    d.polygon([(x, y), (x + 110, y - 4), (x + 110, y - 34), (x, y - 30)], fill="white", outline=DUNKEL)
    d.line((x + 140, y + 10, x + 165, y - 50), fill=(60, 60, 60), width=4)
    d.ellipse((x + 158, y - 62, x + 174, y - 46), fill=(60, 60, 60))

# Tagesordnung mit Stempel
blatt = Image.new("RGBA", (300, 230))
bd = ImageDraw.Draw(blatt)
bd.rectangle((0, 0, 299, 229), fill="white", outline=(170, 170, 170), width=2)
bd.text((16, 14), "Tagesordnung", font=font(FONT_BOLD, 20), fill=DUNKEL)
zeilen = ["TOP 7  Haushalt", "TOP 8  Parkplätze", "TOP 9  Starkregen-", "           vorsorgekonzept"]
for i, z in enumerate(zeilen):
    bd.text((16, 52 + i * 26), z, font=font(FONT_BOLD if i >= 2 else FONT_REGULAR, 17), fill=DUNKEL)
stempel = Image.new("RGBA", (200, 64))
sd = ImageDraw.Draw(stempel)
sd.rounded_rectangle((2, 2, 197, 61), radius=8, outline=ROT, width=5)
sd.text((100, 32), "VERTAGT", font=font(FONT_BOLD, 34), fill=ROT, anchor="mm")
blatt.alpha_composite(stempel.rotate(14, expand=True, resample=Image.BICUBIC), (70, 140))
img.alpha_composite(blatt.rotate(-6, expand=True, resample=Image.BICUBIC), (690, 385))

# kalte Kaffeetasse
d = ImageDraw.Draw(img)
d.rectangle((600, 500, 650, 550), fill="white", outline=DUNKEL, width=3)
d.arc((640, 510, 670, 540), 270, 90, fill=DUNKEL, width=4)

mit_rahmen(img, "test-2026-10-23", "Ein Konzept bestellen ist leicht. Einen Bauplatz streichen nicht.")
