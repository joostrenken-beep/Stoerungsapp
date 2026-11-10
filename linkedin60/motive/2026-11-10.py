"""Motiv 10.11.2026, Stil Bleistiftskizze, Layout links.

Notizbuchseite auf Karopapier mit zwei Skizzen nebeneinander:
"Bei uns": ein Rohr, daneben ein noch dickeres Rohr, Pfeil "größer?".
"Kopenhagen": Straßenschnitt mit abgesenktem Platz, der bei Starkregen Wasser hält, Bäume, Pfeile.
Dazu handschriftliche Notizen, Schraffur, ein Kaffeerand. Inhalt rechts von x ~ 440.
Aufruf: python3 linkedin60/motive/2026-11-10.py
"""
import math
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from PIL import Image, ImageDraw, ImageFilter, ImageFont

from bild import H, W, mit_rahmen

S = 2
WW, HH = W * S, H * S
rnd = random.Random(1110)
PAPIER = (248, 246, 238)
KARO = (196, 214, 230)
BLEI = (70, 70, 74)
BLAUSTIFT = (60, 100, 170)
HAND = "/usr/share/fonts/truetype/freefont/FreeSansOblique.ttf"


def s(*v):
    return tuple(int(round(x * S)) for x in v)


img = Image.new("RGBA", (WW, HH), PAPIER + (255,))
d = ImageDraw.Draw(img)

# Karopapier mit rotem Rand
for x in range(0, W, 22):
    d.line(s(x, 0, x, H), fill=KARO, width=1)
for y in range(0, H, 22):
    d.line(s(0, y, W, y), fill=KARO, width=1)
d.line(s(470, 0, 470, H), fill=(226, 150, 150), width=S)
# Lochung angedeutet
for y in range(60, H, 130):
    d.ellipse(s(450, y, 462, y + 12), fill=(232, 228, 216))

stift = Image.new("RGBA", (WW, HH))
sd = ImageDraw.Draw(stift)


def strich(pts, farbe=BLEI, breite=2.2, zittern=1.2, deckung=200, passes=2):
    """Bleistiftlinie: mehrere leicht versetzte, zittrige Durchgänge."""
    for p in range(passes):
        neu = []
        for i in range(len(pts) - 1):
            (x0, y0), (x1, y1) = pts[i], pts[i + 1]
            n = max(2, int(math.hypot(x1 - x0, y1 - y0) / 6))
            for k in range(n):
                t = k / n
                neu.append(s(x0 + (x1 - x0) * t + rnd.uniform(-zittern, zittern),
                             y0 + (y1 - y0) * t + rnd.uniform(-zittern, zittern)))
        neu.append(s(*pts[-1]))
        sd.line(neu, fill=farbe + (int(deckung * (0.75 if p else 1)),), width=int(breite * S))


def kreis(cx, cy, r, **kw):
    pts = [(cx + math.cos(a / 40 * 2 * math.pi) * r * rnd.uniform(0.98, 1.02),
            cy + math.sin(a / 40 * 2 * math.pi) * r * rnd.uniform(0.98, 1.02)) for a in range(41)]
    strich(pts, **kw)


def schraffur(box, abstand=7, farbe=BLEI, deckung=110, winkel=1.0, maske=None):
    x0, y0, x1, y1 = box
    for k in range(int(-(y1 - y0)), int(x1 - x0), abstand):
        a = (x0 + k, y1)
        b = (x0 + k + (y1 - y0) * winkel, y0)
        strich([a, b], farbe=farbe, breite=1.1, zittern=0.6, deckung=deckung, passes=1)


def hand(x, y, text, size=24, farbe=BLEI, winkel=0.0):
    f = ImageFont.truetype(HAND, size * S)
    layer = Image.new("RGBA", s(len(text) * size * 0.7 + 40, size * 1.8))
    ImageDraw.Draw(layer).text(s(10, 4), text, font=f, fill=farbe + (230,))
    layer = layer.rotate(winkel, expand=True, resample=Image.BICUBIC)
    stift.alpha_composite(layer, s(x, y))


# ---------- Skizze 1: "Bei uns" ----------
hand(540, 96, "Bei uns:", 30, winkel=2)
strich([(540, 138), (660, 136)], breite=1.6)
# kleines Rohr, Pfeil, großes Rohr (Längsansicht als Zylinder)
def rohr(x, y, laenge, r):
    strich([(x, y - r), (x + laenge, y - r)])
    strich([(x, y + r), (x + laenge, y + r)])
    pts = [(x + math.cos(a / 20 * 2 * math.pi) * r * 0.35, y + math.sin(a / 20 * 2 * math.pi) * r) for a in range(21)]
    strich(pts)
    pts = [(x + laenge + math.cos(a / 20 * 2 * math.pi) * r * 0.35, y + math.sin(a / 20 * 2 * math.pi) * r) for a in range(11)]
    strich(pts)


rohr(560, 190, 70, 18)
strich([(650, 190), (690, 190)], breite=2)
strich([(678, 180), (692, 190), (678, 200)], breite=2)
rohr(710, 190, 90, 32)
hand(560, 228, "größer? noch größer?", 20, winkel=1)
hand(580, 256, "reicht trotzdem nie", 18, farbe=(150, 60, 60), winkel=-2)

# ---------- Skizze 2: "Kopenhagen" ----------
hand(880, 96, "Kopenhagen:", 30, winkel=-1)
strich([(880, 138), (1050, 136)], breite=1.6)
strich([(960, 146), (930, 270)], breite=1.4)
strich([(920, 256), (930, 272), (942, 258)], breite=1.4)
# Straßenschnitt: Häuser links und rechts, dazwischen abgesenkter Platz
gy = 420
strich([(500, gy), (640, gy), (680, gy + 50), (900, gy + 50), (940, gy), (1160, gy)], breite=2.6)
for hx, hb, hh in ((520, 90, 120), (1030, 110, 140)):
    strich([(hx, gy), (hx, gy - hh), (hx + hb, gy - hh), (hx + hb, gy)])
    for fy in range(gy - hh + 20, gy - 20, 34):
        for fx in range(hx + 14, hx + hb - 20, 30):
            strich([(fx, fy), (fx + 14, fy), (fx + 14, fy + 18), (fx, fy + 18), (fx, fy)], breite=1.2, passes=1)
# Bäume im Platz
for tx in (730, 860):
    strich([(tx, gy + 50), (tx, gy - 10)], breite=2.2)
    kreis(tx, gy - 34, 30, breite=1.6)
# Wasser im Platz (Blaustift)
wasser = [(668, gy + 34), (912, gy + 34)]
strich(wasser, farbe=BLAUSTIFT, breite=2)
for k in range(5):
    y = gy + 38 + k * 2.5
    strich([(674 + k * 4, y), (906 - k * 4, y)], farbe=BLAUSTIFT, breite=1, deckung=120, passes=1)
# Regen und Fließpfeile
for k in range(10):
    x = 560 + k * 56
    strich([(x, 296), (x - 6, 318)], farbe=BLAUSTIFT, breite=1.2, passes=1)
for x0, x1 in ((560, 650), (1110, 950)):
    y = gy - 14
    strich([(x0, y), (x1, y + 20)], farbe=BLAUSTIFT, breite=1.8)
    dx = -1 if x1 < x0 else 1
    strich([(x1 - 12 * dx, y + 10), (x1, y + 20), (x1 - 14 * dx, y + 26)], farbe=BLAUSTIFT, breite=1.8)
hand(690, gy + 66, "Platz = Speicher bei Starkregen", 22, farbe=BLAUSTIFT)
hand(980, gy - 200, "Straße leitet ab", 20, winkel=-4)
strich([(1010, gy - 168), (1060, gy - 30)], breite=1.2)
# Einkreisung als Betonung
kreis(790, gy + 30, 160, breite=1.4, deckung=120)

# Notiz unten und Kaffeerand
hand(540, 560, "~300 Projekte an der Oberfläche statt nur Rohr", 21, winkel=0.5)
strich([(540, 596), (1010, 594)], breite=1.4)
hand(1040, 610, "Illustration", 16, farbe=(130, 130, 130))
ring = Image.new("RGBA", (WW, HH))
ImageDraw.Draw(ring).ellipse(s(1040, 470, 1160, 590), outline=(170, 130, 90, 70), width=6 * S)
img = Image.alpha_composite(img, ring.filter(ImageFilter.GaussianBlur(1.5 * S)))

# Graphitkörnung über die Striche
korn = Image.new("L", (WW, HH), 255)
kd = ImageDraw.Draw(korn)
for _ in range(60000):
    kd.point((rnd.randrange(WW), rnd.randrange(HH)), fill=rnd.randint(150, 230))
alpha = stift.split()[3]
stift.putalpha(Image.composite(alpha, alpha.point(lambda v: int(v * 0.6)), korn.point(lambda v: 255 if v > 190 else 0)))
img = Image.alpha_composite(img, stift)

img = img.resize((W, H), Image.LANCZOS)
mit_rahmen(img, "2026-11-10", "Kopenhagen plant Plätze. Wir planen Rohre.",
           "Wolkenbruchplan seit 2011: Wasser an die Oberfläche", layout="links")
