"""Motiv 13.11.2026, Stil Isometrische 3D-Ansicht, Layout links.

Kleine Modellsiedlung in Isometrie. Ein Haus steht unter einer großen Lupe, an drei Stellen
markieren rote Ausrufezeichen die typischen Schwachstellen: Lichtschacht, Einfahrt zum Haus hin,
Kanalanschluss ohne Rückstauklappe. Daneben eine generische Figur mit Klemmbrett.
Szene rechts von x ~ 440.
Aufruf: python3 linkedin60/motive/2026-11-13.py
"""
import math
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from PIL import Image, ImageDraw, ImageFilter

from bild import FONT_BOLD, H, W, font, mit_rahmen

S = 2
rnd = random.Random(1113)
U = 26                      # Einheit in px
OX, OY = 800, 300           # Ursprung auf dem Bild
C30, S30 = math.cos(math.radians(30)), math.sin(math.radians(30))
HIMMEL = (232, 238, 244)


def iso(x, y, z=0.0):
    return ((OX + (x - y) * C30 * U) * S, (OY + (x + y) * S30 * U - z * U) * S)


def shade(c, f):
    return tuple(max(0, min(255, int(v * f))) for v in c)


img = Image.new("RGB", (W * S, H * S), HIMMEL)
d = ImageDraw.Draw(img)


def poly(pts, farbe, rand=None):
    d.polygon([iso(*p) for p in pts], fill=farbe, outline=rand)


def box(x, y, z, dx, dy, dz, farbe):
    """Quader mit drei Helligkeitsstufen (oben hell, links mittel, rechts dunkel)."""
    poly([(x, y + dy, z), (x + dx, y + dy, z), (x + dx, y + dy, z + dz), (x, y + dy, z + dz)], shade(farbe, 0.82))
    poly([(x + dx, y, z), (x + dx, y + dy, z), (x + dx, y + dy, z + dz), (x + dx, y, z + dz)], shade(farbe, 0.64))
    poly([(x, y, z + dz), (x + dx, y, z + dz), (x + dx, y + dy, z + dz), (x, y + dy, z + dz)], farbe)


def satteldach(x, y, z, dx, dy, h, farbe):
    """Satteldach, First entlang der x-Achse."""
    m = y + dy / 2
    poly([(x, y + dy, z), (x + dx, y + dy, z), (x + dx, m, z + h), (x, m, z + h)], shade(farbe, 0.85))
    poly([(x + dx, y, z), (x + dx, y + dy, z), (x + dx, m, z + h)], shade(farbe, 0.62))
    poly([(x, y, z), (x + dx, y, z), (x + dx, m, z + h), (x, m, z + h)], shade(farbe, 1.0))


def haus(x, y, wand, dach, fenster=True):
    box(x, y, 0, 4, 3, 2.6, wand)
    if fenster:
        for fx in (0.7, 2.4):  # Fenster auf der linken (vorderen) Seite
            poly([(x + fx, y + 3, 1.0), (x + fx + 0.8, y + 3, 1.0), (x + fx + 0.8, y + 3, 1.8), (x + fx, y + 3, 1.8)], (150, 186, 214))
    satteldach(x, y, 2.6, 4, 3, 1.6, dach)


# Grundplatte als Modell-Sockel
box(-6, -6, -0.8, 14, 14, 0.8, (150, 190, 120))
# Straße und Gehweg
poly([(-6, 4.2, 0.01), (8, 4.2, 0.01), (8, 6.8, 0.01), (-6, 6.8, 0.01)], (120, 124, 132))
for k in range(-5, 8, 2):
    poly([(k, 5.4, 0.02), (k + 1, 5.4, 0.02), (k + 1, 5.6, 0.02), (k, 5.6, 0.02)], (236, 236, 228))
poly([(-6, 3.6, 0.02), (8, 3.6, 0.02), (8, 4.2, 0.02), (-6, 4.2, 0.02)], (196, 196, 190))

# Nachbarhäuser (hinten) und Bäume
haus(-5, -5, (226, 214, 196), (170, 90, 70))
haus(3.5, -5.2, (214, 222, 230), (110, 120, 136))
for tx, ty in ((-1.5, -4.5), (7, 1.5), (-5.2, 1.6)):
    box(tx, ty, 0, 0.3, 0.3, 1.0, (120, 90, 60))
    box(tx - 0.6, ty - 0.6, 1.0, 1.5, 1.5, 1.4, (96, 150, 86))

# Das untersuchte Haus vorne in der Mitte
hx, hy = -1, -0.6
haus(hx, hy, (240, 232, 214), (186, 78, 60))
# Einfahrt fällt zum Haus hin (Fläche mit Pfeil und Pfütze)
poly([(hx + 4.2, hy + 0.2, 0.03), (hx + 6.4, hy + 0.2, 0.03), (hx + 6.4, hy + 3.6, 0.03), (hx + 4.2, hy + 3.6, 0.03)], (170, 172, 178))
poly([(hx + 4.3, hy + 0.4, 0.05), (hx + 5.6, hy + 0.4, 0.05), (hx + 5.6, hy + 1.6, 0.05), (hx + 4.3, hy + 1.6, 0.05)], (110, 170, 226))
d.line([iso(hx + 5.3, hy + 3.2, 0.06), iso(hx + 5.3, hy + 1.8, 0.06)], fill=(40, 100, 180), width=4 * S)
a, b = iso(hx + 5.3, hy + 1.8, 0.06), iso(hx + 5.3, hy + 2.2, 0.06)
d.polygon([a, (b[0] - 10 * S, b[1] + 2 * S), (b[0] + 10 * S, b[1] - 2 * S)], fill=(40, 100, 180))
# Lichtschacht vor dem Haus (vertieft)
poly([(hx + 1.0, hy + 3.0, 0.04), (hx + 2.0, hy + 3.0, 0.04), (hx + 2.0, hy + 3.6, 0.04), (hx + 1.0, hy + 3.6, 0.04)], (60, 64, 72))
poly([(hx + 1.1, hy + 3.1, 0.05), (hx + 1.9, hy + 3.1, 0.05), (hx + 1.9, hy + 3.5, 0.05), (hx + 1.1, hy + 3.5, 0.05)], (90, 150, 210))
# Kanalanschluss: Rohrstutzen zum Straßenkanal
box(hx + 0.2, hy + 3.0, -0.6, 0.4, 2.6, 0.4, (150, 150, 146))
# Regen
for _ in range(130):
    px, py = rnd.randint(470, W - 20), rnd.randint(20, 300)
    d.line((px * S, py * S, (px - 4) * S, (py + 14) * S), fill=(120, 150, 190), width=S)

# Figur mit Klemmbrett (generisch)
fx, fy = hx + 7.2, hy + 3.6
box(fx, fy, 0, 0.5, 0.5, 1.4, (60, 90, 140))
cx, cy = iso(fx + 0.25, fy + 0.25, 1.75)
d.ellipse((cx - 9 * S, cy - 9 * S, cx + 9 * S, cy + 9 * S), fill=(236, 200, 170))
box(fx - 0.35, fy + 0.1, 0.8, 0.12, 0.45, 0.6, (230, 230, 220))


# Rote Ausrufezeichen als Markierungen
def marker(p, nr):
    mx, my = iso(*p)
    d.line((mx, my, mx, my - 46 * S), fill=(200, 40, 40), width=3 * S)
    d.ellipse((mx - 17 * S, my - 80 * S, mx + 17 * S, my - 46 * S), fill=(214, 52, 44))
    d.text((mx, my - 63 * S), "!", font=font(FONT_BOLD, 24 * S), fill="white", anchor="mm")


marker((hx + 1.5, hy + 3.3, 0.05), 1)   # Lichtschacht
marker((hx + 5.0, hy + 1.0, 0.05), 2)   # Einfahrt
marker((hx + 0.4, hy + 5.4, -0.2), 3)   # Kanalanschluss

# Lupe über dem Haus (Ring, Glanz, Griff)
lx, ly = iso(hx + 2.6, hy + 1.6, 2.2)
r = 150 * S
glas = Image.new("RGBA", img.size)
gd = ImageDraw.Draw(glas)
gd.ellipse((lx - r, ly - r, lx + r, ly + r), fill=(255, 255, 255, 36))
gd.arc((lx - r * 0.8, ly - r * 0.8, lx + r * 0.8, ly + r * 0.8), 200, 250, fill=(255, 255, 255, 170), width=8 * S)
img = Image.alpha_composite(img.convert("RGBA"), glas)
d = ImageDraw.Draw(img)
d.ellipse((lx - r, ly - r, lx + r, ly + r), outline=(52, 66, 82), width=12 * S)
gx, gy = lx + r * 0.72, ly + r * 0.72
d.line((gx, gy, gx + 90 * S, gy + 90 * S), fill=(52, 66, 82), width=22 * S)

img = img.resize((W, H), Image.LANCZOS)
mit_rahmen(img, "2026-11-13", "Erst der Blick von außen. Dann der Regen.",
           "Karlsruhe fördert unabhängige Starkregenberatung mit bis zu 500 Euro", layout="links")
