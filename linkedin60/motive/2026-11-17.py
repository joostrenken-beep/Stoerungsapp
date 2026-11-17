"""Motiv 17.11.2026, Stil Scherenschnitt / Papiercollage, Layout karte.

Schwarzwald aus Papierschichten: Hügel mit Tannen, Wolken mit ausgeschnittenen Regenstreifen,
ein Dorf im Tal, unten steigendes Wasser in mehreren Blautönen. Auf einem kleinen Hügel im Wasser
stehen drei Scherenschnitt-Figuren (Hausbesitzer, Betreiber mit Helm, Politiker am Pult) und zeigen
jeweils auf den nächsten. Textkarte oben links bleibt frei.
Aufruf: python3 linkedin60/motive/2026-11-17.py
"""
import math
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from PIL import Image, ImageChops, ImageDraw, ImageFilter

from bild import H, W, mit_rahmen

S = 2
WW, HH = W * S, H * S
rnd = random.Random(1117)


def s(*v):
    return tuple(int(round(x * S)) for x in v)


papier_korn = Image.effect_noise((WW, HH), 22).filter(ImageFilter.GaussianBlur(0.7 * S))


def lage(img, maske, farbe, schatten=10, versatz=(5, 7)):
    """Eine Papierlage: weicher Schlagschatten, dann eingefärbtes Papier mit Faser."""
    sh = Image.new("RGBA", img.size, (0, 0, 0, 0))
    verschoben = Image.new("L", maske.size, 0)  # ohne Umlauf am Bildrand verschieben
    verschoben.paste(maske, s(*versatz))
    sh.putalpha(verschoben.point(lambda v: int(v * 0.42)))
    img.alpha_composite(sh.filter(ImageFilter.GaussianBlur(schatten * S)))
    tex = Image.merge("RGB", [papier_korn.point(lambda v, c=c: max(0, min(255, c + (v - 128) // 6))) for c in farbe])
    teil = tex.convert("RGBA")
    teil.putalpha(maske)
    img.alpha_composite(teil)


def neue_maske():
    m = Image.new("L", (WW, HH), 0)
    return m, ImageDraw.Draw(m)


def huegel(basis, amp, freq, phase):
    return [s(x, basis - amp * (0.6 * math.sin(x / freq + phase) + 0.4 * math.sin(x / (freq * 0.43) + phase * 2))) for x in range(0, W + 21, 20)]


def tanne(dr, x, y, h):
    for k in range(3):
        w = h * (0.42 - k * 0.1)
        top = y - h * (0.35 + k * 0.28)
        dr.polygon([s(x, top - h * 0.3), s(x - w, top + h * 0.12), s(x + w, top + h * 0.12)], fill=255)
    dr.rectangle(s(x - h * 0.04, y - h * 0.1, x + h * 0.04, y), fill=255)


img = Image.new("RGBA", (WW, HH), (0, 0, 0, 255))
# Himmel: helles Papier mit leichtem Verlauf
him = Image.new("RGB", (WW, HH))
hd = ImageDraw.Draw(him)
for y in range(HH):
    t = y / HH
    hd.line((0, y, WW, y), fill=(int(214 - 26 * t), int(216 - 20 * t), int(214 - 10 * t)))
img.paste(him, (0, 0))

# Wolken (zwei Lagen) mit ausgeschnittenen Regenstreifen
for farbe, cy, n in (((150, 152, 162), 70, 7), ((118, 120, 134), 112, 6)):
    m, md = neue_maske()
    for k in range(n):
        cx = 560 + k * 100 + rnd.randint(-20, 20)
        r = rnd.randint(50, 80)
        md.ellipse(s(cx - r * 1.3, cy - r * 0.7, cx + r * 1.3, cy + r * 0.7), fill=255)
    lage(img, m, farbe, schatten=8)
m, md = neue_maske()
for k in range(22):  # Regenstreifen als schmale Papierstreifen
    x = 560 + k * 28 + rnd.randint(-6, 6)
    y0 = 150 + rnd.randint(0, 30)
    md.polygon([s(x, y0), s(x + 4, y0), s(x - 14, y0 + 120 + rnd.randint(0, 60)), s(x - 18, y0 + 120)], fill=255)
lage(img, m, (96, 130, 176), schatten=4, versatz=(2, 3))

# Hügelketten, hinten hell, vorne dunkel, mit Tannen
for basis, amp, phase, farbe, tannen in ((300, 40, 0.3, (112, 138, 124), 0), (350, 50, 1.7, (84, 112, 98), 14), (400, 34, 3.1, (58, 84, 72), 18)):
    m, md = neue_maske()
    md.polygon(huegel(basis, amp, 120, phase) + [s(W + 20, H), s(0, H)], fill=255)
    for k in range(tannen):
        x = 480 + k * (720 / max(1, tannen)) + rnd.randint(-10, 10)
        y = basis - amp * (0.6 * math.sin(x / 120 + phase) + 0.4 * math.sin(x / 51.6 + phase * 2)) + 6
        tanne(md, x, y, rnd.randint(36, 60))
    lage(img, m, farbe)

# Dorf im Tal (helle Häuser mit Dächern)
m, md = neue_maske()
for k, hx in enumerate((620, 700, 790, 900, 1000)):
    hy = 452 + (k % 2) * 6
    md.rectangle(s(hx, hy - 34, hx + 46, hy), fill=255)
    md.polygon([s(hx - 6, hy - 34), s(hx + 23, hy - 60), s(hx + 52, hy - 34)], fill=255)
lage(img, m, (232, 222, 200), schatten=6)
m, md = neue_maske()
for k, hx in enumerate((620, 700, 790, 900, 1000)):
    hy = 452 + (k % 2) * 6
    md.polygon([s(hx - 6, hy - 34), s(hx + 23, hy - 60), s(hx + 52, hy - 34)], fill=255)
    md.rectangle(s(hx + 16, hy - 24, hx + 30, hy - 10), fill=255)
lage(img, m, (168, 74, 58), schatten=2, versatz=(1, 1))

# Steigendes Wasser: drei Lagen
for basis, farbe in ((470, (120, 166, 204)), (505, (82, 128, 178)), (548, (52, 92, 146))):
    m, md = neue_maske()
    pts = [s(x, basis + 7 * math.sin(x / 36 + basis)) for x in range(0, W + 21, 12)]
    md.polygon(pts + [s(W + 20, H), s(0, H)], fill=255)
    lage(img, m, farbe, schatten=9)

# Kleiner Hügel im Wasser mit drei zeigenden Figuren
m, md = neue_maske()
md.ellipse(s(700, 560, 1100, 660), fill=255)
lage(img, m, (96, 120, 84), schatten=10)


def figur(md, x, y, richtung, hut=None):
    """Generische Scherenschnitt-Figur mit ausgestrecktem Zeigearm."""
    md.ellipse(s(x - 11, y - 96, x + 11, y - 74), fill=255)              # Kopf
    md.polygon([s(x - 14, y - 72), s(x + 14, y - 72), s(x + 18, y - 30), s(x - 18, y - 30)], fill=255)  # Rumpf
    md.rectangle(s(x - 13, y - 32, x - 3, y), fill=255)                   # Beine
    md.rectangle(s(x + 3, y - 32, x + 13, y), fill=255)
    ax = x + richtung * 48
    md.line([s(x + richtung * 10, y - 64), s(ax, y - 70)], fill=255, width=7 * S)  # Arm
    md.line([s(ax, y - 70), s(ax + richtung * 14, y - 72)], fill=255, width=3 * S)  # Zeigefinger
    if hut == "helm":
        md.chord(s(x - 15, y - 104, x + 15, y - 80), 180, 360, fill=255)
        md.rectangle(s(x - 18, y - 92, x + 18, y - 89), fill=255)
    if hut == "pult":
        md.polygon([s(x - 30, y - 50), s(x - 18, y - 50), s(x - 22, y), s(x - 34, y)], fill=255)


m, md = neue_maske()
figur(md, 790, 610, +1)                  # Hausbesitzer zeigt nach rechts
figur(md, 900, 600, +1, hut="helm")      # Betreiber zeigt nach rechts
figur(md, 1010, 610, -1, hut="pult")     # Politik zeigt zurück nach links
lage(img, m, (34, 34, 42), schatten=6, versatz=(4, 5))

img = img.convert("RGB").resize((W, H), Image.LANCZOS)
mit_rahmen(img, "2026-11-17", "Am Ende war es wieder niemand.",
           "DWD-Warnung: bis zu 150 Liter pro Quadratmeter im Schwarzwald", layout="karte")
