"""Motiv 30.10.2026 (detaillierter Stil): zwei Grundstücke im Regen, mit Schnitt durch den Boden.

Links: Flachdach und Pflaster, das Wasser läuft über die Fläche in den Kanal, dicker Gebührenstapel.
Rechts: Ziegeldach, Regentonne, Rasen und Baum, das Wasser versickert in den Bodenschichten, ein Blatt.
Gezeichnet in doppelter Auflösung und verkleinert, damit Kanten weich werden.

Aufruf: python3 linkedin60/motive/2026-10-30.py
"""
import math
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from PIL import Image, ImageDraw, ImageFilter

from bild import BLAU, DUNKEL, FONT_BOLD, FONT_REGULAR, HELLBLAU, ROT, H, W, font, mit_rahmen

S = 2  # Supersampling
WW, HH = W * S, H * S
rnd = random.Random(30)


def s(*v):
    return tuple(int(x * S) for x in v)


def mix(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def verlauf(img, box, oben, unten):
    x0, y0, x1, y1 = s(*box)
    d = ImageDraw.Draw(img)
    for y in range(y0, y1):
        d.line((x0, y, x1, y), fill=mix(oben, unten, (y - y0) / max(1, y1 - y0)))


def schatten(img, poly_or_box, blur=14, alpha=90, offset=(10, 10), ellipse=False):
    layer = Image.new("RGBA", img.size)
    ld = ImageDraw.Draw(layer)
    if ellipse:
        ld.ellipse(s(*poly_or_box), fill=(0, 0, 0, alpha))
    else:
        ld.polygon([s(x + offset[0], y + offset[1]) for x, y in poly_or_box], fill=(0, 0, 0, alpha))
    img.alpha_composite(layer.filter(ImageFilter.GaussianBlur(blur * S)))


img = Image.new("RGBA", (WW, HH), (0, 0, 0, 255))

# Himmel: dämmrig, regnerisch
verlauf(img, (0, 0, W, 440), (78, 92, 112), (168, 180, 194))

# Wolkenschichten
for schicht, (farbe, n, ybase) in enumerate((((96, 108, 126), 9, 20), ((118, 130, 146), 8, 70), ((140, 152, 166), 7, 120))):
    layer = Image.new("RGBA", img.size)
    ld = ImageDraw.Draw(layer)
    for i in range(n):
        cx = 420 + i * 100 + rnd.randint(-30, 30)
        cy = ybase + rnd.randint(-15, 15)
        r = rnd.randint(55, 95)
        ld.ellipse(s(cx - r * 1.4, cy - r * 0.7, cx + r * 1.4, cy + r * 0.7), fill=farbe + (235,))
        ld.ellipse(s(cx - r, cy - r * 0.75, cx + r * 0.6, cy - r * 0.1), fill=mix(farbe, (210, 216, 224), 0.25) + (120,))
    img.alpha_composite(layer.filter(ImageFilter.GaussianBlur(6 * S)))

# Horizont: entfernte Häuserreihe im Dunst
layer = Image.new("RGBA", img.size)
ld = ImageDraw.Draw(layer)
x = 420
while x < W:
    w, h = rnd.randint(40, 90), rnd.randint(40, 110)
    ld.rectangle(s(x, 400 - h, x + w, 400), fill=(130, 142, 156, 200))
    if rnd.random() < 0.5:
        ld.polygon([s(x - 4, 400 - h), s(x + w / 2, 400 - h - 30), s(x + w + 4, 400 - h)], fill=(122, 132, 146, 200))
    x += w + rnd.randint(2, 10)
img.alpha_composite(layer.filter(ImageFilter.GaussianBlur(1.5 * S)))

d = ImageDraw.Draw(img)
BODEN = 430   # Geländeoberkante
SCHNITT = 520  # ab hier Bodenschnitt

# ---------- Bodenschnitt ----------
verlauf(img, (420, SCHNITT, W, H), (112, 86, 64), (78, 58, 44))
# Schichten rechts: Mutterboden, Kies, Sand
verlauf(img, (830, SCHNITT, W, SCHNITT + 45), (92, 70, 50), (104, 80, 58))
d.rectangle(s(830, SCHNITT + 45, W, SCHNITT + 100), fill=(150, 138, 118))
for _ in range(500):
    gx, gy = rnd.randint(830, W), rnd.randint(SCHNITT + 47, SCHNITT + 98)
    r = rnd.uniform(1.5, 4)
    c = rnd.choice([(170, 160, 140), (128, 118, 100), (186, 176, 156)])
    d.ellipse(s(gx - r, gy - r, gx + r, gy + r), fill=c)
d.rectangle(s(830, SCHNITT + 100, W, H), fill=(196, 172, 130))
for _ in range(900):
    gx, gy = rnd.randint(830, W), rnd.randint(SCHNITT + 100, H)
    d.point(s(gx, gy), fill=(176, 152, 112))
# Erdkrümel links
for _ in range(700):
    gx, gy = rnd.randint(420, 830), rnd.randint(SCHNITT, H)
    d.point(s(gx, gy), fill=rnd.choice([(96, 72, 54), (124, 96, 72)]))

# Kanalrohr im Schnitt (links), randvoll
rx0, ry0, rx1, ry1 = 430, 590, 830, 650
d.rounded_rectangle(s(rx0, ry0 - 8, rx1, ry1 + 8), radius=12 * S, fill=(150, 150, 146))
d.rounded_rectangle(s(rx0 + 6, ry0, rx1 - 6, ry1), radius=8 * S, fill=(60, 64, 70))
verlauf(img, (rx0 + 8, ry0 + 4, rx1 - 8, ry1 - 2), (92, 150, 214), (32, 86, 160))
d = ImageDraw.Draw(img)
for i in range(14):  # Strömung
    y = ry0 + 10 + (i % 5) * 9
    x = rx0 + 20 + i * 27
    d.line(s(x, y, x + 22, y), fill=(200, 226, 248), width=2 * S)
d.text(s(rx0 + 14, ry0 - 34), "Mischwasserkanal", font=font(FONT_BOLD, 14 * S), fill=(236, 226, 210))

# Versickerung rechts: Tropfenpfade durch die Schichten
for i in range(9):
    x = 860 + i * 37
    for k in range(6):
        y = SCHNITT + 10 + k * 26 + (i % 3) * 6
        a = max(60, 220 - k * 30)
        layer = Image.new("RGBA", img.size)
        ImageDraw.Draw(layer).ellipse(s(x - 3, y - 5, x + 3, y + 5), fill=HELLBLAU + (a,))
        img.alpha_composite(layer)
d = ImageDraw.Draw(img)

# ---------- Oberfläche links: Pflaster ----------
d.rectangle(s(420, BODEN, 830, SCHNITT), fill=(132, 136, 142))
for row, y in enumerate(range(BODEN, SCHNITT, 14)):
    off = 0 if row % 2 == 0 else 14
    for x in range(420 - off, 830, 28):
        c = rnd.choice([(146, 150, 156), (138, 142, 148), (152, 156, 160)])
        d.rectangle(s(x + 1, y + 1, x + 27, y + 13), fill=c)
# Wasserfilm mit Spiegelung
layer = Image.new("RGBA", img.size)
ld = ImageDraw.Draw(layer)
ld.rectangle(s(420, BODEN + 30, 830, SCHNITT), fill=BLAU + (120,))
for i in range(30):
    x = rnd.randint(430, 820)
    y = rnd.randint(BODEN + 34, SCHNITT - 4)
    ld.line(s(x, y, x + rnd.randint(14, 40), y), fill=(220, 236, 250, 160), width=S)
img.alpha_composite(layer)
d = ImageDraw.Draw(img)
# Gully mit Rost, Wasser stürzt nach unten zum Kanal
gx0 = 700
d.rectangle(s(gx0, SCHNITT - 14, gx0 + 50, SCHNITT), fill=(40, 42, 46))
for k in range(6):
    d.line(s(gx0 + 4 + k * 8, SCHNITT - 13, gx0 + 4 + k * 8, SCHNITT - 1), fill=(90, 92, 96), width=2 * S)
verlauf(img, (gx0 + 10, SCHNITT, gx0 + 40, ry0 - 8), (70, 130, 200), (40, 96, 170))
d = ImageDraw.Draw(img)
d.rectangle(s(gx0 + 6, SCHNITT, gx0 + 10, ry0 - 8), fill=(150, 150, 146))
d.rectangle(s(gx0 + 40, SCHNITT, gx0 + 44, ry0 - 8), fill=(150, 150, 146))

# Flachdachgebäude mit Seitenwand
front = [(470, 250), (700, 250), (700, BODEN), (470, BODEN)]
seite = [(700, 250), (760, 230), (760, BODEN - 12), (700, BODEN)]
schatten(img, front + [(760, BODEN)], blur=10, alpha=80, offset=(14, 4))
d = ImageDraw.Draw(img)
d.polygon([s(*p) for p in seite], fill=(150, 156, 164))
verlauf(img, (470, 250, 700, BODEN), (196, 200, 206), (170, 176, 184))
d = ImageDraw.Draw(img)
d.polygon([s(470, 250), s(700, 250), s(760, 230), s(530, 230)], fill=(110, 116, 124))  # Dachfläche
d.line(s(466, 250, 704, 250), fill=(90, 96, 104), width=4 * S)
for row in range(2):  # Fensterband
    for col in range(5):
        x, y = 486 + col * 42, 274 + row * 56
        d.rectangle(s(x, y, x + 30, y + 38), fill=(96, 110, 126))
        d.rectangle(s(x + 2, y + 2, x + 28, y + 20), fill=(150, 176, 200))
        d.line(s(x + 15, y, x + 15, y + 38), fill=(80, 86, 94), width=S)
d.rectangle(s(560, 380, 610, BODEN), fill=(84, 92, 102))  # Tor
for k in range(5):
    d.line(s(560, 384 + k * 9, 610, 384 + k * 9), fill=(70, 76, 86), width=S)
# Wasser schießt vom Flachdach über einen Speier
layer = Image.new("RGBA", img.size)
ld = ImageDraw.Draw(layer)
for k in range(6):
    ld.line(s(462 - k, 256, 452 - k * 3, BODEN + 34), fill=(150, 196, 236, 200), width=2 * S)
img.alpha_composite(layer)
d = ImageDraw.Draw(img)
d.rectangle(s(456, 252, 470, 258), fill=(90, 96, 104))
# Auto vor dem Gebäude
car = [(600, 470), (612, 452), (650, 446), (690, 446), (712, 458), (730, 470), (730, 482), (600, 482)]
schatten(img, [(596, 484), (734, 484), (734, 490), (596, 490)], blur=4, alpha=120, offset=(0, 0))
d = ImageDraw.Draw(img)
d.polygon([s(*p) for p in car], fill=(150, 46, 46))
d.polygon([s(622, 454), s(652, 450), s(652, 466), s(616, 466)], fill=(176, 206, 228))
d.polygon([s(658, 450), s(688, 450), s(704, 466), s(658, 466)], fill=(176, 206, 228))
for wx in (624, 706):
    d.ellipse(s(wx - 11, 474, wx + 11, 496), fill=(30, 30, 34))
    d.ellipse(s(wx - 5, 480, wx + 5, 490), fill=(150, 150, 156))

# ---------- Oberfläche rechts: Rasen ----------
verlauf(img, (830, BODEN, W, SCHNITT), (118, 162, 88), (92, 138, 70))
d = ImageDraw.Draw(img)
for _ in range(1400):
    gx, gy = rnd.randint(830, W), rnd.randint(BODEN + 2, SCHNITT)
    d.line(s(gx, gy, gx + rnd.uniform(-2, 2), gy - rnd.uniform(4, 9)), fill=rnd.choice([(80, 128, 60), (136, 180, 100), (104, 150, 76)]), width=S)
# Trittsteine
for i, (sx_, sy_) in enumerate(((870, 470), (905, 488), (944, 500))):
    d.ellipse(s(sx_ - 18, sy_ - 7, sx_ + 18, sy_ + 7), fill=(176, 172, 162))

# Wohnhaus mit Ziegeldach
hfront = [(880, 300), (1040, 300), (1040, BODEN), (880, BODEN)]
schatten(img, hfront, blur=10, alpha=70, offset=(12, 4))
d = ImageDraw.Draw(img)
verlauf(img, (880, 300, 1040, BODEN), (238, 230, 214), (220, 210, 192))
d = ImageDraw.Draw(img)
dach = [(864, 304), (960, 226), (1056, 304)]
d.polygon([s(*p) for p in dach], fill=(156, 70, 56))
for k in range(1, 8):  # Ziegelreihen
    y = 226 + k * 10
    half = (y - 226) / 78 * 96
    d.line(s(960 - half, y, 960 + half, y), fill=(130, 54, 44), width=S)
d.line(s(864, 304, 1056, 304), fill=(110, 44, 36), width=3 * S)
# Fenster mit warmem Licht, Sprossen, Fensterbank
for fx in (900, 990):
    d.rectangle(s(fx, 330, fx + 34, 372), fill=(250, 214, 140))
    d.rectangle(s(fx, 330, fx + 34, 372), outline=(240, 240, 236), width=3 * S)
    d.line(s(fx + 17, 330, fx + 17, 372), fill=(240, 240, 236), width=2 * S)
    d.line(s(fx, 351, fx + 34, 351), fill=(240, 240, 236), width=2 * S)
    d.rectangle(s(fx - 3, 372, fx + 37, 376), fill=(190, 186, 178))
d.rectangle(s(944, 380, 976, BODEN), fill=(120, 84, 60))
d.ellipse(s(968, 404, 972, 408), fill=(220, 190, 100))
# Dachrinne, Fallrohr, Regentonne
d.rectangle(s(862, 304, 1058, 310), fill=(150, 156, 160))
d.rectangle(s(1046, 310, 1052, 400), fill=(150, 156, 160))
d.rounded_rectangle(s(1034, 398, 1070, BODEN + 6), radius=6 * S, fill=(70, 108, 70))
for k in range(3):
    d.line(s(1034, 406 + k * 10, 1070, 406 + k * 10), fill=(56, 90, 56), width=S)
d.ellipse(s(1036, 394, 1068, 404), fill=(110, 160, 210))

# Baum mit Lichtkante
d.rectangle(s(1110, 330, 1122, BODEN + 4), fill=(96, 70, 48))
layer = Image.new("RGBA", img.size)
ld = ImageDraw.Draw(layer)
for cx, cy, r, c in ((1116, 300, 52, (66, 110, 58)), (1090, 320, 38, (74, 120, 62)), (1142, 318, 38, (70, 116, 60)),
                     (1104, 286, 30, (96, 146, 78)), (1130, 280, 24, (110, 160, 88))):
    ld.ellipse(s(cx - r, cy - r, cx + r, cy + r), fill=c + (255,))
img.alpha_composite(layer.filter(ImageFilter.GaussianBlur(1 * S)))
d = ImageDraw.Draw(img)
# Sträucher
for bx in (860, 1062, 1170):
    for k in range(3):
        r = 14 - k * 2
        d.ellipse(s(bx + k * 10 - r, BODEN - r * 1.2, bx + k * 10 + r, BODEN + 4), fill=mix((70, 118, 60), (110, 160, 86), k / 3))

# Grundstücksgrenze
d.line(s(830, BODEN - 30, 830, H), fill=(240, 240, 240), width=2 * S)
for y in range(BODEN - 30, BODEN + 4, 8):
    d.line(s(826, y, 834, y), fill=(240, 240, 240), width=S)

# ---------- Gebührenbescheide ----------
def bescheid(x, y, anzahl, zeichen, farbe, winkel):
    blatt_w, blatt_h = 150, 104
    stapel = Image.new("RGBA", s(blatt_w + 40, blatt_h + 40))
    sd = ImageDraw.Draw(stapel)
    for k in range(anzahl):
        ox, oy = 6 + k * 3, 30 - k * 3
        sd.rectangle(s(ox, oy, ox + blatt_w, oy + blatt_h), fill=(250, 250, 248), outline=(150, 154, 160), width=S)
    ox, oy = 6 + (anzahl - 1) * 3, 30 - (anzahl - 1) * 3
    sd.text(s(ox + 10, oy + 8), "Gebührenbescheid", font=font(FONT_BOLD, 13 * S), fill=DUNKEL)
    for k in range(3):
        sd.line(s(ox + 10, oy + 32 + k * 9, ox + blatt_w - 50, oy + 32 + k * 9), fill=(196, 200, 206), width=S)
    sd.text(s(ox + 10, oy + 64), zeichen, font=font(FONT_BOLD, 26 * S), fill=farbe)
    stapel = stapel.rotate(winkel, expand=True, resample=Image.BICUBIC)
    sh = Image.new("RGBA", img.size)
    alpha = stapel.split()[3].point(lambda a: int(a * 0.4))
    sh.paste((0, 0, 0, 255), s(x + 8, y + 10), alpha)
    img.alpha_composite(sh.filter(ImageFilter.GaussianBlur(6 * S)))
    img.alpha_composite(stapel, s(x, y))


bescheid(560, 120, 7, "€€€", ROT, 6)
bescheid(950, 128, 1, "€", (40, 140, 80), -4)

# ---------- Regen im Vordergrund ----------
layer = Image.new("RGBA", img.size)
ld = ImageDraw.Draw(layer)
for _ in range(420):
    x, y = rnd.randint(420, W + 40), rnd.randint(0, SCHNITT)
    l = rnd.uniform(12, 28)
    ld.line(s(x, y, x - l * 0.25, y + l), fill=(210, 226, 242, rnd.randint(70, 160)), width=S)
img.alpha_composite(layer)
# Spritzer auf dem Pflaster
d = ImageDraw.Draw(img)
for _ in range(60):
    x, y = rnd.randint(430, 820), rnd.randint(BODEN + 6, SCHNITT - 4)
    d.arc(s(x - 4, y - 2, x + 4, y + 2), 180, 360, fill=(220, 234, 248), width=S)

d.text(s(W - 30, H - 14), "Illustration", font=font(FONT_REGULAR, 13 * S), fill=(240, 232, 220), anchor="rs")

img = img.resize((W, H), Image.LANCZOS)
mit_rahmen(img, "2026-10-30", "Seit 2004 Pflicht. Ab 2027 Realität.",
           "Gesplittete Regenwassergebühr im Vogtland")
