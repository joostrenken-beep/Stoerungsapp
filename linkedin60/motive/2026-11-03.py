"""Motiv 03.11.2026 (detaillierter Stil): Straßenschnitt, darunter ein altes, gerissenes Kanalrohr
mit Wurzeleinwuchs. Auf dem Riss klebt ein Heftpflaster, am Rohr hängt ein Preisschild "+4,8 %".

Aufruf: python3 linkedin60/motive/2026-11-03.py
"""
import math
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from PIL import Image, ImageDraw, ImageFilter

from bild import BLAU, DUNKEL, FONT_BOLD, FONT_REGULAR, HELLBLAU, ROT, H, W, font, mit_rahmen

S = 2
WW, HH = W * S, H * S
rnd = random.Random(1103)


def s(*v):
    return tuple(int(x * S) for x in v)


def mix(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def verlauf(img, box, oben, unten):
    x0, y0, x1, y1 = s(*box)
    d = ImageDraw.Draw(img)
    for y in range(y0, y1):
        d.line((x0, y, x1, y), fill=mix(oben, unten, (y - y0) / max(1, y1 - y0)))


img = Image.new("RGBA", (WW, HH), (0, 0, 0, 255))

# Himmel und Straßenszene oben
verlauf(img, (0, 0, W, 170), (120, 136, 156), (190, 200, 212))
d = ImageDraw.Draw(img)
x = 420
while x < W:  # Häuserfront im Hintergrund
    w, h = rnd.randint(70, 120), rnd.randint(70, 120)
    c = rnd.choice([(214, 204, 188), (196, 188, 176), (224, 216, 204), (176, 168, 160)])
    d.rectangle(s(x, 170 - h, x + w, 172), fill=c)
    d.polygon([s(x - 4, 170 - h), s(x + w / 2, 170 - h - 26), s(x + w + 4, 170 - h)], fill=(150, 76, 62))
    for fy in range(int(170 - h + 14), 160, 26):
        for fx in range(x + 10, x + w - 16, 24):
            d.rectangle(s(fx, fy, fx + 12, fy + 14), fill=(150, 174, 196))
    x += w + 6
# Gehweg und Straße
d.rectangle(s(420, 172, W, 182), fill=(186, 184, 178))
verlauf(img, (420, 182, W, 214), (70, 72, 76), (58, 60, 64))
d = ImageDraw.Draw(img)
for xx in range(440, W, 70):  # Mittelmarkierung
    d.rectangle(s(xx, 197, xx + 36, 200), fill=(230, 230, 220))
# Schachtdeckel
d.ellipse(s(760, 186, 840, 206), fill=(46, 48, 52))
for k in range(4):
    d.arc(s(766 + k * 6, 189 + k * 1.5, 834 - k * 6, 203 - k * 1.5), 0, 360, fill=(72, 74, 78), width=S)

# Schnitt: Aufbau unter der Straße
verlauf(img, (420, 214, W, 240), (110, 110, 108), (130, 128, 122))   # Tragschicht
d = ImageDraw.Draw(img)
for _ in range(500):
    gx, gy = rnd.randint(420, W), rnd.randint(215, 239)
    d.point(s(gx, gy), fill=rnd.choice([(150, 148, 140), (96, 96, 94)]))
verlauf(img, (420, 240, W, H), (128, 98, 70), (82, 60, 44))  # Erdreich
d = ImageDraw.Draw(img)
for _ in range(1800):
    gx, gy = rnd.randint(420, W), rnd.randint(240, H)
    d.point(s(gx, gy), fill=rnd.choice([(104, 78, 56), (142, 110, 80), (92, 70, 52)]))
for _ in range(40):  # Steine
    gx, gy, r = rnd.randint(430, W), rnd.randint(250, H), rnd.uniform(3, 9)
    d.ellipse(s(gx - r, gy - r * 0.7, gx + r, gy + r * 0.7), fill=rnd.choice([(150, 140, 126), (120, 112, 100)]))

# Schacht vom Deckel nach unten
d.rectangle(s(776, 214, 824, 380), fill=(148, 146, 140))
d.rectangle(s(784, 214, 816, 380), fill=(70, 72, 76))
for k in range(8):  # Steigeisen
    d.line(s(790, 228 + k * 18, 810, 228 + k * 18), fill=(170, 170, 164), width=2 * S)

# Altes Betonrohr (Längsschnitt)
px0, py0, px1, py1 = 440, 380, W + 20, 520
layer = Image.new("RGBA", img.size)
ImageDraw.Draw(layer).rounded_rectangle(s(px0 + 8, py0 + 14, px1, py1 + 14), radius=30 * S, fill=(0, 0, 0, 110))
img.alpha_composite(layer.filter(ImageFilter.GaussianBlur(8 * S)))
d = ImageDraw.Draw(img)
verlauf(img, (px0, py0, px1, py0 + 20), (176, 172, 162), (150, 146, 138))
verlauf(img, (px0, py1 - 20, px1, py1), (140, 136, 128), (112, 108, 102))
d = ImageDraw.Draw(img)
d.rectangle(s(px0, py0 + 20, px1, py1 - 20), fill=(54, 56, 60))
# Wasserstand im Rohr
verlauf(img, (px0, py0 + 78, px1, py1 - 20), (86, 140, 200), (40, 90, 160))
d = ImageDraw.Draw(img)
for i in range(18):
    y = py0 + 86 + (i % 4) * 10
    x = px0 + 20 + i * 42
    d.line(s(x, y, x + 24, y), fill=(196, 224, 248), width=2 * S)
# Rohrstöße und Betonporen
for jx in range(px0 + 120, px1, 180):
    d.rectangle(s(jx, py0, jx + 10, py0 + 20), fill=(124, 120, 112))
    d.rectangle(s(jx, py1 - 20, jx + 10, py1), fill=(100, 96, 90))
for _ in range(260):
    gx = rnd.randint(px0, px1)
    gy = rnd.choice([rnd.randint(py0 + 2, py0 + 18), rnd.randint(py1 - 18, py1 - 2)])
    d.point(s(gx, gy), fill=(110, 106, 98))

# Riss im Rohrscheitel mit eindringendem Grundwasser
riss = [(620, py0), (632, py0 + 8), (626, py0 + 14), (640, py0 + 20)]
d.line([s(*p) for p in riss], fill=(30, 30, 32), width=3 * S)
for k in range(4):
    d.line(s(636 + k * 3, py0 + 22, 634 + k * 4, py0 + 70), fill=HELLBLAU, width=2 * S)

# Wurzel wächst durch einen Rohrstoß
wx = 1020
for k in range(6):
    pts = []
    for t in range(12):
        yy = 250 + t * 14 + k * 3
        xx = wx + math.sin(t * 0.8 + k) * (6 + k * 2) + (k - 3) * 4
        pts.append(s(xx, yy))
    d.line(pts, fill=(120, 86, 52), width=(4 - k // 2) * S)
for k in range(9):  # feine Wurzeln im Rohr
    ang = -0.9 + k * 0.22
    d.line(s(wx, py0 + 18, wx + math.cos(ang + 1.57) * 50, py0 + 18 + math.sin(ang + 1.57) * 46), fill=(150, 114, 72), width=2 * S)

# Heftpflaster auf dem Riss (der Bildwitz)
pfl = Image.new("RGBA", s(120, 40))
pd = ImageDraw.Draw(pfl)
pd.rounded_rectangle(s(0, 0, 119, 39), radius=18 * S, fill=(232, 192, 160), outline=(196, 156, 124), width=S)
pd.rectangle(s(40, 4, 80, 35), fill=(248, 236, 224))
for gx in range(8, 112, 8):
    for gy in (10, 20, 30):
        if not 40 <= gx <= 80:
            pd.point(s(gx, gy), fill=(200, 160, 128))
pfl = pfl.rotate(-14, expand=True, resample=Image.BICUBIC)
layer = Image.new("RGBA", img.size)
layer.alpha_composite(pfl, s(574, py0 - 22))
sh = Image.new("RGBA", img.size)
sh.paste((0, 0, 0, 120), s(578, py0 - 16), pfl.split()[3])
img.alpha_composite(sh.filter(ImageFilter.GaussianBlur(3 * S)))
img.alpha_composite(layer)
d = ImageDraw.Draw(img)

# Preisschild "+4,8 %" an einer Schnur am Rohr
tx, ty = 880, 560
d.line(s(860, py1 - 4, tx + 20, ty + 8), fill=(220, 214, 200), width=2 * S)
schild = Image.new("RGBA", s(190, 86))
sd = ImageDraw.Draw(schild)
sd.polygon([s(0, 43), s(30, 0), s(189, 0), s(189, 85), s(30, 85)], fill=(250, 246, 236), outline=(170, 160, 140))
sd.ellipse(s(14, 36, 28, 50), fill=(82, 60, 44))
sd.text(s(112, 43), "+4,8 %", font=font(FONT_BOLD, 34 * S), fill=ROT, anchor="mm")
schild = schild.rotate(8, expand=True, resample=Image.BICUBIC)
sh = Image.new("RGBA", img.size)
sh.paste((0, 0, 0, 110), s(tx + 6, ty + 8), schild.split()[3])
img.alpha_composite(sh.filter(ImageFilter.GaussianBlur(5 * S)))
img.alpha_composite(schild, s(tx, ty))

d = ImageDraw.Draw(img)
d.text(s(W - 30, H - 14), "Illustration", font=font(FONT_REGULAR, 13 * S), fill=(236, 226, 210), anchor="rs")

img = img.resize((W, H), Image.LANCZOS)
mit_rahmen(img, "2026-11-03", "4,8 % mehr. Und trotzdem zu wenig?",
           "Abwassergebühren 2027: Vorschlag der Verwaltung Braunschweig")
