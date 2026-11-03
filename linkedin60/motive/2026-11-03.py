"""Motiv 03.11.2026, Stil Blaupause: technische Zeichnung eines alten Kanalrohrs im Querschnitt.

Riss im Scheitel, Wurzeleinwuchs, darauf ein Heftpflaster als "Provisorium", Bemaßung und
Schriftfeld wie auf einem Planblatt. Gezeichnet in doppelter Auflösung und verkleinert.
Aufruf: python3 linkedin60/motive/2026-11-03.py
"""
import math
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from PIL import Image, ImageDraw, ImageFilter

from bild import H, W, font, mit_rahmen

S = 2
WW, HH = W * S, H * S
rnd = random.Random(311)
MONO = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"
MONO_B = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf"
PAPIER = (22, 70, 128)
LINIE = (232, 242, 252)
FEIN = (90, 140, 196)
AKZENT = (255, 214, 102)  # Signalgelb wie Rotstift auf Blaupausen


def s(*v):
    return tuple(int(round(x * S)) for x in v)


def mono(size, bold=False):
    return font(MONO_B if bold else MONO, size * S)


img = Image.new("RGBA", (WW, HH), PAPIER + (255,))
d = ImageDraw.Draw(img)

# Papierstruktur: leichte Flecken
layer = Image.new("RGBA", img.size)
ld = ImageDraw.Draw(layer)
for _ in range(60):
    x, y, r = rnd.randint(0, W), rnd.randint(0, H), rnd.randint(40, 140)
    ld.ellipse(s(x - r, y - r, x + r, y + r), fill=(255, 255, 255, rnd.randint(4, 10)))
img.alpha_composite(layer.filter(ImageFilter.GaussianBlur(30 * S)))
d = ImageDraw.Draw(img)

# Raster
for x in range(0, W, 20):
    d.line(s(x, 0, x, H), fill=FEIN + (255,) if x % 100 == 0 else (40, 92, 152), width=S)
for y in range(0, H, 20):
    d.line(s(0, y, W, y), fill=FEIN + (255,) if y % 100 == 0 else (40, 92, 152), width=S)

# Blattrahmen
d.rectangle(s(436, 16, W - 16, H - 16), outline=LINIE, width=3 * S)
d.rectangle(s(442, 22, W - 22, H - 22), outline=LINIE, width=S)

# ---------- Rohrquerschnitt ----------
cx, cy = 760, 300
ra, ri = 170, 140  # Außen-, Innenradius
# Erdreich-Schraffur um das Rohr
for k in range(-40, 40):
    x0 = cx - 230 + k * 12
    d.line(s(x0, cy + 210, x0 + 30, cy + 180), fill=(70, 120, 180), width=S)
d.line(s(cx - 240, cy + 196, cx + 240, cy + 196), fill=LINIE, width=S)
d.text(s(cx + 170, cy + 200), "Sohle Graben", font=mono(12), fill=FEIN)

# Rohrwand mit Schraffur (Beton)
wand = Image.new("L", img.size, 0)
wd = ImageDraw.Draw(wand)
wd.ellipse(s(cx - ra, cy - ra, cx + ra, cy + ra), fill=255)
wd.ellipse(s(cx - ri, cy - ri, cx + ri, cy + ri), fill=0)
schraffur = Image.new("RGBA", img.size)
sd = ImageDraw.Draw(schraffur)
for k in range(-60, 60):
    x0 = cx - 400 + k * 9
    sd.line(s(x0, cy - 200, x0 + 400, cy + 200), fill=LINIE + (150,), width=S)
for _ in range(220):  # Zuschlagkörner
    a, r = rnd.uniform(0, 2 * math.pi), rnd.uniform(ri + 4, ra - 4)
    px, py = cx + math.cos(a) * r, cy + math.sin(a) * r
    sd.ellipse(s(px - 1.4, py - 1.4, px + 1.4, py + 1.4), outline=LINIE + (200,), width=S)
leer = Image.new("RGBA", img.size)
img.paste(Image.composite(schraffur, leer, wand), (0, 0), wand)
d = ImageDraw.Draw(img)
d.ellipse(s(cx - ra, cy - ra, cx + ra, cy + ra), outline=LINIE, width=3 * S)
d.ellipse(s(cx - ri, cy - ri, cx + ri, cy + ri), outline=LINIE, width=3 * S)

# Wasserspiegel und Wasser (waagrechte Strichelung)
ws = cy + 50
half = math.sqrt(ri ** 2 - (ws - cy) ** 2)
d.line(s(cx - half, ws, cx + half, ws), fill=LINIE, width=2 * S)
for y in range(int(ws) + 10, cy + ri, 10):
    hw = math.sqrt(max(0, ri ** 2 - (y - cy) ** 2)) - 6
    for x in range(int(cx - hw), int(cx + hw), 18):
        d.line(s(x, y, x + 10, y), fill=(150, 196, 236), width=S)
# Wasserspiegel-Symbol
d.polygon([s(cx + 60, ws - 4), s(cx + 74, ws - 4), s(cx + 67, ws - 14)], outline=LINIE, width=S)
d.line(s(cx + 54, ws - 18, cx + 80, ws - 18), fill=LINIE, width=S)

# Mittelachsen
for k in range(-12, 13):
    if k % 2 == 0:
        d.line(s(cx - 200 + k * 0, cy, cx - 200, cy), fill=LINIE)
for x in range(cx - 200, cx + 200, 22):
    d.line(s(x, cy, x + 12, cy), fill=FEIN, width=S)
for y in range(cy - 200, cy + 190, 22):
    d.line(s(cx, y, cx, y + 12), fill=FEIN, width=S)

# Riss im Scheitel (gelb hervorgehoben)
riss = [(cx - 6, cy - ra), (cx + 4, cy - ra + 10), (cx - 4, cy - ra + 18), (cx + 8, cy - ra + 30)]
d.line([s(*p) for p in riss], fill=AKZENT, width=3 * S)
for k in range(3):  # eindringendes Grundwasser
    d.line(s(cx + 6 + k * 4, cy - ri + 4, cx + 4 + k * 5, cy - ri + 40), fill=AKZENT, width=S)

# Heftpflaster als Provisorium über dem Riss
pfl = Image.new("RGBA", s(110, 36))
pd = ImageDraw.Draw(pfl)
pd.rounded_rectangle(s(1, 1, 108, 34), radius=16 * S, outline=AKZENT, width=2 * S)
pd.rectangle(s(38, 6, 72, 30), outline=AKZENT, width=S)
for gx in range(10, 104, 9):
    if not 36 <= gx <= 74:
        for gy in (12, 24):
            pd.point(s(gx, gy), fill=AKZENT)
pfl = pfl.rotate(-10, expand=True, resample=Image.BICUBIC)
img.alpha_composite(pfl, s(cx - 58, cy - ra - 22))
d = ImageDraw.Draw(img)

# Wurzeleinwuchs rechts oben durch die Wand
a0 = math.radians(-38)
wx, wy = cx + math.cos(a0) * ra, cy + math.sin(a0) * ra
for k in range(5):
    pts = []
    for t in range(9):
        r = ra + 70 - t * 16
        a = a0 + math.sin(t * 0.9 + k) * 0.05 + (k - 2) * 0.03
        pts.append(s(cx + math.cos(a) * r, cy + math.sin(a) * r))
    d.line(pts, fill=LINIE, width=S)
for k in range(7):
    a = a0 + (k - 3) * 0.12
    d.line(s(cx + math.cos(a0) * ri, cy + math.sin(a0) * ri, cx + math.cos(a) * (ri - 46), cy + math.sin(a) * (ri - 46)), fill=LINIE, width=S)

# ---------- Beschriftungen mit Hinweislinien ----------
def hinweis(px, py, tx, ty, text, farbe=LINIE):
    d.line(s(px, py, tx, ty), fill=farbe, width=S)
    d.ellipse(s(px - 3, py - 3, px + 3, py + 3), fill=farbe)
    anchor = "lm" if tx > px else "rm"
    d.line(s(tx, ty, tx + (60 if tx > px else -60), ty), fill=farbe, width=S)
    d.text(s(tx + (6 if tx > px else -6), ty - 12), text, font=mono(15, True), fill=farbe, anchor="lb" if tx > px else "rb")


hinweis(cx + 4, cy - ra + 8, cx + 150, cy - ra - 22, "Riss im Scheitel", AKZENT)
hinweis(cx + 40, cy - ra - 8, cx + 180, cy - ra + 22, "Provisorium", AKZENT)
hinweis(wx + 24, wy - 30, cx + 230, cy - 90, "Wurzeleinwuchs")
hinweis(cx + ra - 14, cy + 36, cx + 215, cy + 60, "Betonrohr")
hinweis(cx + 60, ws + 40, cx + 200, cy + 112, "Abwasser")

# Bemaßung Innendurchmesser
d.line(s(cx - ri, cy + 236, cx + ri, cy + 236), fill=LINIE, width=S)
for x in (cx - ri, cx + ri):
    d.line(s(x, cy + 226, x, cy + 246), fill=LINIE, width=S)
    d.line(s(x - 6, cy + 242, x + 6, cy + 230), fill=LINIE, width=S)
d.text(s(cx, cy + 232), "DN ?", font=mono(14, True), fill=LINIE, anchor="mb")

# ---------- Schriftfeld unten rechts ----------
bx0, by0, bx1, by1 = 880, 548, W - 30, H - 30
d.rectangle(s(bx0, by0, bx1, by1), outline=LINIE, width=2 * S)
d.line(s(bx0, by0 + 32, bx1, by0 + 32), fill=LINIE, width=S)
d.line(s(bx0, by0 + 64, bx1, by0 + 64), fill=LINIE, width=S)
d.line(s(bx0 + 110, by0 + 32, bx0 + 110, by1), fill=LINIE, width=S)
d.text(s(bx0 + 10, by0 + 8), "KANALNETZ  BESTAND", font=mono(15, True), fill=LINIE)
d.text(s(bx0 + 10, by0 + 41), "Maßnahme", font=mono(12), fill=FEIN)
d.text(s(bx0 + 120, by0 + 38), "Gebühr +4,8 %", font=mono(16, True), fill=AKZENT)
d.text(s(bx0 + 10, by0 + 73), "Sanierung", font=mono(12), fill=FEIN)
d.text(s(bx0 + 120, by0 + 70), "verschoben", font=mono(16, True), fill=LINIE)

d.text(s(600, H - 30), "Illustration, keine Bestandsdaten", font=mono(12), fill=FEIN)

img = img.resize((W, H), Image.LANCZOS)
mit_rahmen(img, "2026-11-03", "4,8 % mehr. Und trotzdem zu wenig?",
           "Abwassergebühren 2027: Vorschlag der Verwaltung Braunschweig")
