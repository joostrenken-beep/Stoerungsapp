"""Motiv 12.11.2026, Stil Holzschnitt / Linoldruck, Layout unten.

Eine Balkenwaage als Druckgrafik: Links liegt ein kleiner Münzbeutel ("Förderung") und schwebt
nach oben, rechts drückt eine schwere Regenwolke mit Haus und Wasser die Schale nach unten.
Zwei Druckfarben (Schwarz, Rot) auf Creme, Schnitzkerben, raue Kanten, leicht versetzter Rotdruck.
Szene oberhalb des Textbands (y < ~470).
Aufruf: python3 linkedin60/motive/2026-11-12.py
"""
import math
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from PIL import Image, ImageChops, ImageDraw, ImageFilter

from bild import FONT_BOLD, H, W, font, mit_rahmen

S = 2
WW, HH = W * S, H * S
rnd = random.Random(1112)
PAPIER = (240, 230, 208)
SCHWARZ = (30, 26, 24)
ROT = (186, 52, 40)


def s(*v):
    return tuple(int(round(x * S)) for x in v)


def rau(maske, staerke=2.2):
    """Raue Druckkante: Maske verrauschen und neu schwellen."""
    rausch = Image.effect_noise((WW, HH), 80).filter(ImageFilter.GaussianBlur(1.2 * S))
    m = maske.filter(ImageFilter.GaussianBlur(staerke * S))
    return ImageChops.add(m, rausch.point(lambda v: int((v - 128) * 0.6)), 1, 0).point(lambda v: 255 if v > 128 else 0)


def druck(papier, maske, farbe, versatz=(0, 0)):
    """Farbe mit Druckstruktur (Fehlstellen) auf das Papier bringen."""
    korn = Image.effect_noise((WW, HH), 60).point(lambda v: 0 if v < 40 else 255)
    m = ImageChops.multiply(maske, korn)
    m = ImageChops.offset(m, *s(*versatz))
    papier.paste(farbe, (0, 0), m)


schwarz = Image.new("L", (WW, HH), 0)
rot = Image.new("L", (WW, HH), 0)
ds = ImageDraw.Draw(schwarz)
dr = ImageDraw.Draw(rot)

# Waage: Ständer und schräger Balken
px, py = 640, 120
ds.polygon([s(600, 452), s(680, 452), s(652, 140), s(628, 140)], fill=255)   # Säule
ds.rectangle(s(560, 446, 720, 466), fill=255)                                # Fuß
neig = math.radians(14)  # rechts schwerer
dx, dy = math.cos(neig) * 300, math.sin(neig) * 300
lx, ly, rx, ry = px - dx, py - dy, px + dx, py + dy
ds.line([s(lx, ly), s(rx, ry)], fill=255, width=16 * S)
ds.ellipse(s(px - 22, py - 22, px + 22, py + 22), fill=255)
ds.polygon([s(px - 14, py - 40), s(px + 14, py - 40), s(px, py - 10)], fill=255)  # Zeiger

# Schalen an Ketten
def schale(x, y, tiefe):
    ds.line([s(x, y), s(x - 90, y + tiefe)], fill=255, width=4 * S)
    ds.line([s(x, y), s(x + 90, y + tiefe)], fill=255, width=4 * S)
    ds.chord(s(x - 110, y + tiefe - 30, x + 110, y + tiefe + 30), 0, 180, fill=255)
    return y + tiefe

lsy = schale(lx, ly, 120)
rsy = schale(rx, ry, 120)

# Linke Schale: kleiner Münzbeutel (rot) mit "€"-Aussparung
bx, by = lx, lsy - 4
dr.ellipse(s(bx - 40, by - 76, bx + 40, by + 2), fill=255)
dr.polygon([s(bx - 10, by - 72), s(bx + 10, by - 72), s(bx + 24, by - 96), s(bx - 24, by - 96)], fill=255)
dr.text(s(bx, by - 37), "€", font=font(FONT_BOLD, 48 * S), fill=0, anchor="mm")

# Rechte Schale: Haus, Wasser bis zum Fenster (rot), schwere Wolke darüber (schwarz)
hx, hy = rx, rsy - 4
ds.rectangle(s(hx - 56, hy - 92, hx + 56, hy), fill=255)
ds.polygon([s(hx - 72, hy - 90), s(hx, hy - 150), s(hx + 72, hy - 90)], fill=255)
ds.rectangle(s(hx - 36, hy - 74, hx - 8, hy - 48), fill=0)   # Fenster
ds.rectangle(s(hx + 10, hy - 74, hx + 38, hy - 48), fill=0)
dr.rectangle(s(hx - 96, hy - 40, hx + 96, hy - 2), fill=255)  # Wasser
for k in range(4):
    dr.arc(s(hx - 96 + k * 48, hy - 50, hx - 48 + k * 48, hy - 30), 180, 360, fill=0, width=4 * S)
# Wolke
wx, wy = 1090, 190  # Wolke rechts neben dem Balkenende
for cx, cy, r in ((wx - 50, wy, 38), (wx, wy - 22, 48), (wx + 50, wy - 4, 40), (wx + 6, wy + 14, 40)):
    ds.ellipse(s(cx - r, cy - r, cx + r, cy + r), fill=255)
for k in range(7):  # Regen als geschnitzte Striche, schräg aufs Haus
    x = wx - 70 + k * 22
    ds.line([s(x, wy + 50), s(x - 22, wy + 92)], fill=255, width=5 * S)

# Schnitzkerben: weiße Schraffuren in den großen schwarzen Flächen
kerben = Image.new("L", (WW, HH), 0)
kd = ImageDraw.Draw(kerben)
for k in range(40):
    y = 150 + k * 7
    kd.line([s(612, y), s(668, y + rnd.uniform(-3, 3))], fill=255, width=S)
for k in range(10):  # Wolke
    x0 = wx - 90 + k * 16
    kd.arc(s(x0, wy - 60, x0 + 60, wy), 200, 330, fill=255, width=2 * S)
for k in range(10):  # Hauswand
    y = hy - 88 + k * 9
    kd.line([s(hx - 50, y), s(hx - 40 + rnd.uniform(0, 12), y)], fill=255, width=S)
schwarz = ImageChops.subtract(schwarz, kerben)

# Hintergrund: geschnitzte Linien wie Holzmaserung, sparsam
hinter = Image.new("L", (WW, HH), 0)
hd = ImageDraw.Draw(hinter)
for k in range(12):
    y = 30 + k * 36
    pts = [s(x, y + 5 * math.sin(x / 70 + k)) for x in range(0, W + 1, 20)]
    if k % 3 == 0:
        hd.line(pts, fill=255, width=2 * S)

img = Image.new("RGB", (WW, HH), PAPIER)
# Papierstruktur
faser = Image.effect_noise((WW, HH), 18).filter(ImageFilter.GaussianBlur(0.8 * S))
img = ImageChops.multiply(img, Image.merge("RGB", [faser.point(lambda v: 225 + v // 8)] * 3))
druck(img, rau(hinter, 0.6).point(lambda v: v // 5), SCHWARZ)
druck(img, rau(rot), ROT, versatz=(3, 2))
druck(img, rau(schwarz), SCHWARZ)

img = img.resize((W, H), Image.LANCZOS)
mit_rahmen(img, "2026-11-12", "Ein Förderprogramm. Weniger als zwei Tage Schaden.",
           "Niedersachsen fördert mit 11,3 Mio. Euro. Starkregen kostet im Schnitt 6,6 Mio. Euro pro Tag.", layout="unten")
