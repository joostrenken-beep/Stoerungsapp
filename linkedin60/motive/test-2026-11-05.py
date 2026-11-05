"""Motiv Testbeitrag 05.11.2026, Stil Minimalistisch, Layout unten.

Ein einziges Symbol: ein Sparschwein, das zur Hälfte im Wasser steht. Zwei Farben, Figur und Grund
kehren sich an der Wasserlinie um (oben blaues Schwein auf Creme, unten cremefarbenes Schwein im Blau).
Aufruf: python3 linkedin60/motive/test-2026-11-05.py
"""
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from PIL import Image, ImageChops, ImageDraw

from bild import H, W, mit_rahmen

S = 2
CREME = (244, 239, 228)
TIEFBLAU = (28, 72, 130)


def s(*v):
    return tuple(int(round(x * S)) for x in v)


# Maske: Sparschwein
schwein = Image.new("L", (W * S, H * S), 0)
d = ImageDraw.Draw(schwein)
cx, cy = 640, 250
d.ellipse(s(cx - 170, cy - 115, cx + 150, cy + 105), fill=255)                         # Körper
d.rounded_rectangle(s(cx + 130, cy - 34, cx + 196, cy + 34), radius=18 * S, fill=255)  # Rüssel
d.polygon([s(cx + 40, cy - 92), s(cx + 70, cy - 148), s(cx + 98, cy - 80)], fill=255)  # Ohr
for lx in (cx - 120, cx - 50, cx + 30, cx + 90):                                       # Beine
    d.rounded_rectangle(s(lx, cy + 70, lx + 40, cy + 160), radius=10 * S, fill=255)
d.arc(s(cx - 214, cy - 52, cx - 160, cy + 2), 120, 420, fill=255, width=9 * S)  # Ringelschwanz
# ausgesparte Details: Münzschlitz, Auge, Nasenlöcher
d.rounded_rectangle(s(cx - 50, cy - 108, cx + 40, cy - 94), radius=6 * S, fill=0)
d.ellipse(s(cx + 76, cy - 46, cx + 94, cy - 28), fill=0)
for nx in (cx + 170, cx + 184):
    d.ellipse(s(nx - 5, cy - 10, nx + 5, cy + 10), fill=0)

# Maske: Wasser unterhalb einer ruhigen Welle
wasser = Image.new("L", (W * S, H * S), 0)
wd = ImageDraw.Draw(wasser)
wy = 300
pts = [s(x, wy + 7 * math.sin(x / 38)) for x in range(0, W + 1, 4)]
wd.polygon(pts + [s(W, H), s(0, H)], fill=255)

# Figur-Grund-Umkehr: blau, wo genau eine der beiden Masken gilt
blau = ImageChops.logical_xor(schwein.convert("1"), wasser.convert("1")).convert("L")
img = Image.new("RGB", (W * S, H * S), CREME)
img.paste(TIEFBLAU, (0, 0), blau)

img = img.resize((W, H), Image.LANCZOS)
mit_rahmen(img, "test-2026-11-05", "Kein Geld für den Plan. Aber für den Schaden?",
           "Starkregenkonzept aus Kostengründen aufgeschoben", layout="unten")
