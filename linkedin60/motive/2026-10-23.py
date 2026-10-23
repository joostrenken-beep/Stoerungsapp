"""Motiv 23.10.2026: stilisierte Starkregengefahrenkarte mit markiertem Haus.

Vorlage für individuelle Motive: Szene in 1200 x 675 zeichnen (Inhalt rechts
von x ~ 420), dann bild.mit_rahmen() aufrufen.
Aufruf: python3 linkedin60/motive/2026-10-23.py
"""
import math
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from PIL import Image, ImageDraw, ImageFilter

from bild import DUNKEL, FONT_BOLD, FONT_REGULAR, GRAU, LAND, ROT, H, W, font, mit_rahmen

rnd = random.Random(23)
img = Image.new("RGBA", (W, H), LAND + (255,))
d = ImageDraw.Draw(img)

# Straßenraster und Häuserblöcke
for x in range(-100, W + 200, 150):
    d.line((x, -20, x + 60, H + 20), fill="white", width=14)
for y in range(-40, H + 100, 120):
    d.line((-20, y, W + 20, y + 40), fill="white", width=14)
for gx in range(-100, W + 200, 150):
    for gy in range(-40, H + 100, 120):
        for _ in range(rnd.randint(2, 4)):
            bx = gx + 20 + rnd.randint(0, 80) + (gy + 40) * 60 / H * 0.9
            by = gy + 18 + rnd.randint(0, 60) + (gx + 100) * 40 / W * 0.9
            d.rectangle((bx, by, bx + rnd.randint(26, 46), by + rnd.randint(20, 34)), fill=GRAU)


def pfad(t):
    return 380 + t * 900, 80 + t * 520 + 70 * math.sin(t * 5.2)


# Fließweg mit Wassertiefe, eine Farbe von hell nach dunkel
pts = [pfad(i / 200) for i in range(201)]
ramp = [((198, 224, 245), 120), ((140, 190, 232), 78), ((74, 140, 210), 44), ((28, 84, 160), 18)]
flut = Image.new("RGBA", (W, H))
fd = ImageDraw.Draw(flut)
for farbe, breite in ramp:
    for i, (x, y) in enumerate(pts):
        r = breite * (0.55 + 0.45 * math.sin(i / 200 * math.pi)) + rnd.uniform(-4, 4)
        fd.ellipse((x - r, y - r * 0.8, x + r, y + r * 0.8), fill=farbe + (210,))
    cx, cy = pfad(0.62)
    fd.ellipse((cx - breite * 1.6, cy - breite * 1.1, cx + breite * 1.6, cy + breite * 1.1), fill=farbe + (210,))
img = Image.alpha_composite(img, flut.filter(ImageFilter.GaussianBlur(6)))
d = ImageDraw.Draw(img)

# Fließpfeile
for t in (0.3, 0.48, 0.78, 0.92):
    x0, y0 = pfad(t)
    x1, y1 = pfad(t + 0.035)
    a = math.atan2(y1 - y0, x1 - x0)
    d.line((x0, y0, x1, y1), fill="white", width=4)
    for s in (2.6, -2.6):
        d.line((x1, y1, x1 - 14 * math.cos(a + s / 3), y1 - 14 * math.sin(a + s / 3)), fill="white", width=4)

# "Dein Haus?"
hx, hy = pfad(0.62)
hx, hy = hx - 40, hy - 20
d.rectangle((hx - 22, hy - 16, hx + 22, hy + 16), fill=GRAU, outline=DUNKEL, width=3)
d.ellipse((hx - 46, hy - 46, hx + 46, hy + 46), outline=ROT, width=5)
fl = font(FONT_BOLD, 24)
lw = d.textlength("Dein Haus?", font=fl)
d.rounded_rectangle((hx + 40, hy - 92, hx + 40 + lw + 28, hy - 52), radius=10, fill="white", outline=ROT, width=3)
d.text((hx + 54, hy - 72), "Dein Haus?", font=fl, fill=DUNKEL, anchor="lm")
d.line((hx + 40, hy - 56, hx + 30, hy - 36), fill=ROT, width=4)

# Legende mit Hinweis, dass es eine Illustration ist
lx, ly = W - 330, H - 128
d.rounded_rectangle((lx, ly, W - 30, H - 26), radius=12, fill=(255, 255, 255, 235))
d.text((lx + 16, ly + 12), "Max. Wassertiefe (Szenario)", font=font(FONT_BOLD, 16), fill=DUNKEL)
for i, (farbe, _) in enumerate(ramp):
    d.rectangle((lx + 16 + i * 66, ly + 44, lx + 78 + i * 66, ly + 62), fill=farbe)
d.text((lx + 16, ly + 70), "gering", font=font(FONT_REGULAR, 15), fill=(80, 90, 100))
d.text((lx + 276, ly + 70), "hoch", font=font(FONT_REGULAR, 15), fill=(80, 90, 100), anchor="ra")
d.text((lx + 16, ly + 88), "Illustration, keine echten Kartendaten", font=font(FONT_REGULAR, 13), fill=(110, 120, 130))

mit_rahmen(img, "2026-10-23", "Die Karte ist online. Wer traut sich nachzusehen?",
           "Hinweiskarte Starkregengefahren jetzt für ganz Hessen")
