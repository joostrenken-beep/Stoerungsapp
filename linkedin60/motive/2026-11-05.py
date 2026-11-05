"""Motiv 05.11.2026, Stil Comic: Infoabend Starkregen. Vorne ein Fachmann am Pult mit einer Sprechblase
voller Fachbegriffe, davor leere Stuhlreihen, ganz hinten eine einzelne Figur mit "???".
Dicke Konturen, Rasterpunkte, Sprechblasen. Generische Figuren, keine realen Personen.

Aufruf: python3 linkedin60/motive/2026-11-05.py
"""
import math
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from PIL import Image, ImageDraw

from bild import BLAU, DUNKEL, FONT_BOLD, HELLBLAU, ROT, H, W, font, mit_rahmen

S = 2
rnd = random.Random(1105)
INK = (24, 26, 32)
GELB = (255, 222, 110)
CREME = (250, 244, 228)
OL = 4  # Konturstärke


def s(*v):
    return tuple(int(round(x * S)) for x in v)


img = Image.new("RGBA", (W * S, H * S), GELB + (255,))
d = ImageDraw.Draw(img)

# Rasterpunkte (Comic-Druck), nach rechts unten dichter
for y in range(0, H, 12):
    for x in range(420 + (y // 12 % 2) * 6, W, 12):
        r = 1.0 + 2.4 * ((x - 420) / (W - 420)) * (y / H)
        d.ellipse(s(x - r, y - r, x + r, y + r), fill=(236, 186, 70))

# Strahlen hinter dem Redner
cx, cy = 640, 330
for k in range(18):
    a1 = k * 2 * math.pi / 18
    a2 = a1 + math.pi / 36
    d.polygon([s(cx, cy), s(cx + math.cos(a1) * 700, cy + math.sin(a1) * 700),
               s(cx + math.cos(a2) * 700, cy + math.sin(a2) * 700)], fill=(255, 232, 150))

# Boden
d.polygon([s(420, 520), s(W, 470), s(W, H), s(420, H)], fill=(196, 160, 120), outline=INK, width=OL * S)
for k in range(1, 6):
    y = 520 - (k * 10)
    d.line(s(420, 520 + k * 30, W, 470 + k * 30), fill=(176, 140, 100), width=2 * S)

# Leinwand mit Diagramm-Andeutung hinter dem Redner
d.rectangle(s(470, 110, 720, 290), fill="white", outline=INK, width=OL * S)
d.line(s(495, 260, 700, 260), fill=INK, width=3 * S)
d.line(s(495, 260, 495, 130), fill=INK, width=3 * S)
pts = [(495 + i * 20, 250 - (i * i * 1.1) - rnd.randint(0, 8)) for i in range(11)]
d.line([s(*p) for p in pts], fill=BLAU, width=4 * S)
d.text(s(600, 275), "Illustration", font=font(FONT_BOLD, 11 * S), fill=(120, 120, 120), anchor="mm")

# Redner am Pult (generische Figur)
d.ellipse(s(520, 300, 580, 360), fill=(240, 200, 170), outline=INK, width=OL * S)
d.ellipse(s(536, 322, 544, 330), fill=INK)
d.ellipse(s(556, 322, 564, 330), fill=INK)
d.arc(s(540, 334, 566, 350), 20, 160, fill=INK, width=3 * S)
d.rectangle(s(522, 360, 578, 430), fill=DUNKEL, outline=INK, width=OL * S)
d.polygon([s(500, 420), s(600, 420), s(588, 520), s(512, 520)], fill=(150, 96, 60), outline=INK, width=OL * S)
d.line(s(560, 420, 600, 398), fill=INK, width=3 * S)  # Mikrofon
d.ellipse(s(596, 390, 610, 404), fill=INK)

# Sprechblase mit Fachbegriffen
bx0, by0, bx1, by1 = 640, 40, 1010, 250
d.ellipse(s(bx0, by0, bx1, by1), fill="white", outline=INK, width=OL * S)
d.polygon([s(700, 228), s(740, 236), s(600, 320)], fill="white")
d.line(s(700, 228, 600, 320), fill=INK, width=OL * S)
d.line(s(740, 236, 600, 320), fill=INK, width=OL * S)
begriffe = [("100-jährliches", 24), ("Ereignis!", 24), ("Rückstauebene!", 22), ("Abflussbeiwert!", 20), ("Retention!", 20)]
y = 70
for text, size in begriffe:
    d.text(s((bx0 + bx1) / 2, y), text, font=font(FONT_BOLD, size * S), fill=INK, anchor="mt")
    y += size + 12

# Leere Stuhlreihen
def stuhl(x, y, sc=1.0):
    w, h = 44 * sc, 40 * sc
    d.rectangle(s(x, y - h * 1.1, x + w, y - h * 0.4), fill=ROT, outline=INK, width=3 * S)  # Lehne
    d.rectangle(s(x, y - h * 0.4, x + w, y - h * 0.2), fill=ROT, outline=INK, width=3 * S)  # Sitz
    d.line(s(x + 4, y - h * 0.2, x + 4, y), fill=INK, width=3 * S)
    d.line(s(x + w - 4, y - h * 0.2, x + w - 4, y), fill=INK, width=3 * S)


for reihe in range(3):
    sc = 1.2 - reihe * 0.18
    y = 640 - reihe * 52
    for k in range(6):
        x = 640 + k * 70 * sc + reihe * 26
        if reihe == 2 and k == 5:
            continue
        stuhl(x, y, sc)

# Einzelne Figur ganz hinten mit "???"
fx, fy = 1110, 500
d.ellipse(s(fx - 18, fy - 76, fx + 18, fy - 40), fill=(220, 180, 150), outline=INK, width=3 * S)
d.rectangle(s(fx - 20, fy - 40, fx + 20, fy), fill=HELLBLAU, outline=INK, width=3 * S)
d.ellipse(s(fx - 70, fy - 170, fx + 60, fy - 96), fill="white", outline=INK, width=3 * S)
d.polygon([s(fx - 6, fy - 102), s(fx + 12, fy - 100), s(fx + 2, fy - 80)], fill="white")
d.line(s(fx - 6, fy - 102, fx + 2, fy - 80), fill=INK, width=3 * S)
d.line(s(fx + 12, fy - 100, fx + 2, fy - 80), fill=INK, width=3 * S)
d.text(s(fx - 5, fy - 133), "???", font=font(FONT_BOLD, 30 * S), fill=ROT, anchor="mm")

img = img.resize((W, H), Image.LANCZOS)
mit_rahmen(img, "2026-11-05", "Wir reden wie ein Gutachten. Und du hörst weg.",
           "Starkregenvorsorge braucht Klartext")
