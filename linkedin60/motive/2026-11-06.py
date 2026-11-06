"""Motiv 06.11.2026, Stil Nacht und Neon, Layout unten.

Nächtliche Straße im Regen. An der Hauswand leuchtet ein Neonschild wie vor einem Parkhaus:
"KANAL" in Blau, darunter "VOLL" in Rot. Aus dem Gully quillt leuchtendes Wasser, alles spiegelt
sich auf dem nassen Asphalt. Szene im oberen Bereich (Textband unten ab y ~ 475).
Aufruf: python3 linkedin60/motive/2026-11-06.py
"""
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from PIL import Image, ImageChops, ImageDraw, ImageFilter

from bild import FONT_BOLD, H, W, font, mit_rahmen

S = 2
WW, HH = W * S, H * S
rnd = random.Random(1106)
NACHT = (8, 10, 22)
CYAN = (60, 230, 255)
NEONROT = (255, 50, 80)
GELBLICHT = (255, 196, 110)
STRASSE = 330  # Bordsteinkante


def s(*v):
    return tuple(int(round(x * S)) for x in v)


def glow(base, layer, radius, staerke=1):
    """Leuchtschicht additiv mit Weichzeichner auflegen."""
    for r in (radius, radius / 2.5):
        g = layer.filter(ImageFilter.GaussianBlur(r * S))
        for _ in range(staerke):
            base = ImageChops.add(base, g)
    return ImageChops.add(base, layer)


img = Image.new("RGB", (WW, HH), NACHT)
d = ImageDraw.Draw(img)

# Himmel mit leichtem Verlauf
for y in range(0, STRASSE * S):
    t = y / (STRASSE * S)
    d.line((0, y, WW, y), fill=(int(10 + 18 * t), int(12 + 16 * t), int(30 + 24 * t)))

# Häuserfront (Silhouetten) mit wenigen warmen Fenstern
x = 0
while x < W:
    w, h = rnd.randint(110, 190), rnd.randint(170, 280)
    d.rectangle(s(x, STRASSE - h, x + w, STRASSE), fill=(16, 18, 32))
    for fy in range(STRASSE - h + 24, STRASSE - 40, 42):
        for fx in range(x + 16, x + w - 26, 34):
            if rnd.random() < 0.18:
                d.rectangle(s(fx, fy, fx + 16, fy + 22), fill=(70, 52, 30))
    x += w + rnd.randint(4, 14)

# Gehweg und Straße
d.rectangle(s(0, STRASSE, W, STRASSE + 12), fill=(30, 32, 44))
for y in range((STRASSE + 12) * S, HH):
    t = (y - (STRASSE + 12) * S) / (HH - (STRASSE + 12) * S)
    d.line((0, y, WW, y), fill=(int(14 + 6 * t), int(15 + 6 * t), int(26 + 8 * t)))

# ---------- Leuchtschicht ----------
licht = Image.new("RGB", (WW, HH), (0, 0, 0))
ld = ImageDraw.Draw(licht)

# Neonschild an der Hauswand
sx0, sy0, sx1, sy1 = 760, 70, 1040, 250
ld.rounded_rectangle(s(sx0, sy0, sx1, sy1), radius=18 * S, outline=CYAN, width=4 * S)
ld.text(s((sx0 + sx1) / 2, sy0 + 52), "KANAL", font=font(FONT_BOLD, 58 * S), fill=CYAN, anchor="mm")
ld.line(s(sx0 + 30, sy0 + 98, sx1 - 30, sy0 + 98), fill=CYAN, width=2 * S)
ld.text(s((sx0 + sx1) / 2, sy0 + 140), "VOLL", font=font(FONT_BOLD, 64 * S), fill=NEONROT, anchor="mm")
ld.line(s(sx1 - 40, sy1, sx1 - 40, STRASSE - 2), fill=(60, 60, 70), width=4 * S)  # Halterung (dunkel)

# Straßenlaterne mit Lichtkegel
lx = 380
ld.ellipse(s(lx - 14, 92, lx + 14, 112), fill=GELBLICHT)
kegel = Image.new("L", (WW, HH), 0)
ImageDraw.Draw(kegel).polygon([s(lx - 10, 106), s(lx + 10, 106), s(lx + 150, STRASSE + 120), s(lx - 150, STRASSE + 120)], fill=46)
kegel = kegel.filter(ImageFilter.GaussianBlur(16 * S))
licht = ImageChops.add(licht, Image.merge("RGB", [kegel.point(lambda v: v), kegel.point(lambda v: int(v * 0.75)), kegel.point(lambda v: int(v * 0.4))]))
ld = ImageDraw.Draw(licht)

# Gully mit aufquellendem, leuchtendem Wasser
gx, gy = 640, 410
ld.ellipse(s(gx - 150, gy - 28, gx + 150, gy + 28), fill=(10, 70, 90))
for r in range(20, 150, 22):
    ld.ellipse(s(gx - r, gy - r * 0.18, gx + r, gy + r * 0.18), outline=CYAN, width=2 * S)
for k in range(9):  # Fontäne
    dx = (k - 4) * 9
    ld.line(s(gx + dx * 0.4, gy - 4, gx + dx, gy - 46 - rnd.randint(0, 22)), fill=CYAN, width=2 * S)

img = glow(img, licht, 14, 1)
d = ImageDraw.Draw(img)

# Gullydeckel als dunkle Form auf dem Licht
d.rectangle(s(gx - 34, gy - 8, gx + 34, gy + 8), fill=(20, 22, 28))
for k in range(7):
    d.line(s(gx - 30 + k * 10, gy - 6, gx - 30 + k * 10, gy + 6), fill=(70, 76, 86), width=2 * S)

# Spiegelungen auf nassem Asphalt: Schild und Laterne gestaucht und verwischt nach unten
spiegel = licht.crop(s(0, 0, W, STRASSE)).transpose(Image.FLIP_TOP_BOTTOM)
spiegel = spiegel.resize((WW, int((H - STRASSE - 12) * S)))
spiegel = spiegel.filter(ImageFilter.GaussianBlur(5 * S)).point(lambda v: int(v * 0.45))
streifen = Image.new("L", spiegel.size, 0)
sd = ImageDraw.Draw(streifen)
for y in range(0, spiegel.size[1], 6 * S):  # Wellenstreifen
    sd.rectangle((0, y, spiegel.size[0], y + 3 * S), fill=255)
spiegel = Image.composite(spiegel, Image.new("RGB", spiegel.size), streifen.filter(ImageFilter.GaussianBlur(1.5 * S)))
basis = img.crop((0, (STRASSE + 12) * S, WW, HH))
img.paste(ImageChops.add(basis, spiegel), (0, (STRASSE + 12) * S))

# Regen, im Licht heller
regen = Image.new("RGB", (WW, HH), (0, 0, 0))
rd = ImageDraw.Draw(regen)
for _ in range(700):
    x, y = rnd.randint(0, W), rnd.randint(0, STRASSE + 120)
    l = rnd.uniform(10, 24)
    hell = 70 if (lx - 170 < x < lx + 170) or (sx0 - 40 < x < sx1 + 40 and y < sy1 + 60) else 34
    rd.line(s(x, y, x - l * 0.2, y + l), fill=(hell, hell + 10, hell + 30), width=S)
img = ImageChops.add(img, regen)

d = ImageDraw.Draw(img)
img = img.resize((W, H), Image.LANCZOS)
mit_rahmen(img, "2026-11-06", "Der Kanal kann nicht alles.",
           "Bei extremem Starkregen stößt jede Kanalisation an Grenzen", layout="unten")
