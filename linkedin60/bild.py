"""Baut das Beitragsbild: Hintergrund + Reihentitel + Kernaussage + Logo + KI-Hinweis.

Aufruf: python3 linkedin60/bild.py <datum> "<kernaussage>" [hintergrundbild]
(wird auch automatisch von speichern.py aufgerufen)
Ohne Hintergrundbild entsteht eine Grafik in den Markenfarben, deren Motiv
von Beitrag zu Beitrag wechselt. Ergebnis: linkedin60/bilder/<datum>.png (1200 x 675).
"""

import random
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

from stil import TITEL

HIER = Path(__file__).parent
W, H = 1200, 675
DUNKEL = (52, 66, 82)
BLAU = (58, 120, 194)
HELLBLAU = (110, 176, 224)
FONT_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FONT_REGULAR = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"


def font(path, size):
    try:
        return ImageFont.truetype(path, size)
    except OSError:
        return ImageFont.load_default(size)


def logo_transparent():
    """Schneidet Symbol und Schriftzug aus dem Original und macht Weiß transparent."""
    cached = HIER / "assets" / "logo.png"
    if cached.exists():
        return Image.open(cached).convert("RGBA")
    im = Image.open(HIER / "assets" / "logo_original.png").convert("RGB").crop((148, 264, 1116, 866))
    px = []
    for r, g, b in im.get_flattened_data() if hasattr(im, "get_flattened_data") else im.getdata():
        a = 255 - min(r, g, b)
        if a < 12:
            px.append((0, 0, 0, 0))
            continue
        # Farbe von Weiß "entmischen", damit die Kanten sauber bleiben
        f = 255 / a
        px.append(tuple(max(0, min(255, int(255 - (255 - c) * f))) for c in (r, g, b)) + (a,))
    out = Image.new("RGBA", im.size)
    out.putdata(px)
    out.save(cached)
    return out


def cover(img):
    scale = max(W / img.width, H / img.height)
    img = img.resize((round(img.width * scale), round(img.height * scale)), Image.LANCZOS)
    left, top = (img.width - W) // 2, (img.height - H) // 2
    return img.crop((left, top, left + W, top + H))


def brand_background(seed):
    rnd = random.Random(seed)
    bg = Image.new("RGB", (W, H))
    d = ImageDraw.Draw(bg)
    oben, unten = rnd.choice([(DUNKEL, BLAU), (BLAU, DUNKEL), ((30, 42, 56), (52, 66, 82))])
    for y in range(H):
        t = y / H
        d.line([(0, y), (W, y)], fill=tuple(round(oben[i] * (1 - t) + unten[i] * t) for i in range(3)))
    lines = Image.new("RGBA", (W, H))
    ld = ImageDraw.Draw(lines)
    farbe = HELLBLAU + (110,)
    motiv = rnd.choice(["wellen", "regen", "ringe", "pegel"])
    if motiv == "wellen":  # Wellenlinien wie im Logo
        y0 = rnd.randint(220, 320)
        for i in range(3):
            ld.arc((-300 + i * 40, y0 + i * 26, 1500, y0 + 840 + i * 26), 190, 350, fill=farbe, width=6)
    elif motiv == "regen":  # schräge Regenstriche
        for _ in range(140):
            x, y, l = rnd.randint(-100, W), rnd.randint(-50, H), rnd.randint(30, 90)
            ld.line((x, y, x + l * 0.35, y + l), fill=HELLBLAU + (rnd.randint(40, 120),), width=3)
    elif motiv == "ringe":  # Tropfen, die auf Wasser treffen
        for _ in range(4):
            cx, cy = rnd.randint(500, 1150), rnd.randint(150, 450)
            for r in range(30, 360, 45):
                ld.ellipse((cx - r, cy - r * 0.35, cx + r, cy + r * 0.35), outline=HELLBLAU + (max(20, 140 - r // 3),), width=3)
    else:  # Pegellatte am rechten Rand
        x = rnd.randint(900, 1050)
        for i, y in enumerate(range(120, H, 22)):
            ld.line((x, y, x + (60 if i % 5 == 0 else 30), y), fill=farbe, width=4)
        ld.line((0, 430, W, 430), fill=HELLBLAU + (160,), width=4)
    return Image.alpha_composite(bg.convert("RGBA"), lines).convert("RGB")


def wrap(draw, text, fnt, max_width):
    lines, line = [], ""
    for word in text.split():
        test = f"{line} {word}".strip()
        if draw.textlength(test, font=fnt) <= max_width:
            line = test
        else:
            lines.append(line)
            line = word
    lines.append(line)
    return lines


def erstellen(datum, aussage, hintergrund=None):
    try:
        bg = cover(Image.open(hintergrund).convert("RGB")) if hintergrund else brand_background(datum)
    except OSError:
        bg = brand_background(datum)

    canvas = bg.convert("RGBA")
    # Abdunkeln nach unten, damit die Schrift lesbar ist
    shade = Image.new("L", (W, H))
    ImageDraw.Draw(shade).rectangle((0, 0, W, H), fill=0)
    for y in range(H):
        shade.putpixel((0, y), int(max(0, (y / H - 0.25)) * 300))
    shade = shade.resize((1, H)).resize((W, H))
    canvas = Image.composite(Image.new("RGBA", (W, H), DUNKEL + (255,)), canvas, shade.point(lambda p: min(p, 215)))
    d = ImageDraw.Draw(canvas)

    # Reihentitel oben links
    f_titel = font(FONT_BOLD, 30)
    tw = d.textlength(TITEL.upper(), font=f_titel)
    d.rounded_rectangle((48, 44, 48 + tw + 44, 44 + 58), radius=29, fill=(255, 255, 255, 240))
    d.text((70, 73), TITEL.upper(), font=f_titel, fill=DUNKEL, anchor="lm")

    # Kernaussage unten links, Größe passt sich der Länge an
    # nie abschneiden: so lange verkleinern, bis der Text in höchstens 4 Zeilen passt
    for size in (120, 96, 78, 66, 58, 50, 44, 38, 34):
        f_aussage = font(FONT_BOLD, size)
        lines = wrap(d, aussage, f_aussage, 770)
        if len(lines) <= (3 if size >= 58 else 4):
            break
    line_h = int(size * 1.15)
    y = H - 60 - line_h * len(lines)
    for line in lines:
        d.text((52, y), line, font=f_aussage, fill="white")
        y += line_h

    # Logo unten rechts auf weißer Karte
    logo = logo_transparent()
    logo.thumbnail((250, 160), Image.LANCZOS)
    card = (W - logo.width - 48 - 36, H - logo.height - 48 - 28, W - 48, H - 48)
    shadow = Image.new("RGBA", (W, H))
    ImageDraw.Draw(shadow).rounded_rectangle(card, radius=18, fill=(0, 0, 0, 90))
    canvas = Image.alpha_composite(canvas, shadow.filter(ImageFilter.GaussianBlur(10)))
    d = ImageDraw.Draw(canvas)
    d.rounded_rectangle(card, radius=18, fill="white")
    canvas.alpha_composite(logo, (card[0] + 18, card[1] + 14))

    # KI-Hinweis klein oben rechts
    hinweis = "KI-generiert"
    f_hinweis = font(FONT_REGULAR, 15)
    hw = d.textlength(hinweis, font=f_hinweis)
    d.rounded_rectangle((W - hw - 48 - 20, 50, W - 48, 50 + 28), radius=14, fill=(0, 0, 0, 140))
    d.text((W - 48 - 10, 64), hinweis, font=f_hinweis, fill=(235, 235, 235), anchor="rm")

    out = HIER / "bilder" / f"{datum}.png"
    out.parent.mkdir(exist_ok=True)
    canvas.convert("RGB").save(out, optimize=True)
    print(f"Bild gespeichert: {out.relative_to(HIER.parent)}")
    return out


ROT = (214, 64, 52)
GRAU = (196, 201, 206)
LAND = (236, 239, 233)


def mit_rahmen(motiv, datum, aussage, unterzeile=""):
    """Legt den einheitlichen Rahmen über eine individuell gezeichnete Illustration.

    motiv: Bild in 1200 x 675. Die linken ~420 px werden vom Textfeld überdeckt,
    die eigentliche Szene gehört also nach rechts. Speichert bilder/<datum>.png.
    """
    img = motiv.convert("RGBA").resize((W, H))
    panel = Image.new("RGBA", (W, H))
    pd = ImageDraw.Draw(panel)
    for x in range(560):
        a = 245 if x < 380 else int(245 * (560 - x) / 180)
        pd.line((x, 0, x, H), fill=DUNKEL + (a,))
    img = Image.alpha_composite(img, panel)
    d = ImageDraw.Draw(img)

    ft = font(FONT_BOLD, 22)
    tw = d.textlength(TITEL.upper(), font=ft)
    d.rounded_rectangle((44, 40, 44 + tw + 36, 84), radius=22, fill="white")
    d.text((62, 62), TITEL.upper(), font=ft, fill=DUNKEL, anchor="lm")

    for size in (58, 54, 48, 42, 38, 34):
        fb = font(FONT_BOLD, size)
        lines = wrap(d, aussage, fb, 450)
        if len(lines) <= 4:
            break
    y = 128
    for line in lines:
        d.text((46, y), line, font=fb, fill="white")
        y += int(size * 1.2)
    fu = font(FONT_REGULAR, 21)
    for line in wrap(d, unterzeile, fu, 440) if unterzeile else []:
        y += 6
        d.text((48, y + 8), line, font=fu, fill=(215, 225, 235))
        y += 22

    logo = logo_transparent()
    logo.thumbnail((170, 96), Image.LANCZOS)
    card = (44, H - logo.height - 44 - 24, 44 + logo.width + 32, H - 44)
    d.rounded_rectangle(card, radius=14, fill="white")
    img.alpha_composite(logo, (card[0] + 16, card[1] + 12))

    fh = font(FONT_REGULAR, 15)
    hw = d.textlength("KI-generiert", font=fh)
    d.rounded_rectangle((W - hw - 64, 42, W - 44, 70), radius=14, fill=(0, 0, 0, 150))
    d.text((W - 54, 56), "KI-generiert", font=fh, fill=(235, 235, 235), anchor="rm")

    out = HIER / "bilder" / f"{datum}.png"
    out.parent.mkdir(exist_ok=True)
    img.convert("RGB").save(out, optimize=True)
    print(f"Bild gespeichert: {out.relative_to(HIER.parent)}")
    return out


if __name__ == "__main__":
    erstellen(sys.argv[1], sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else None)
