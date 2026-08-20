"""Generate 1000x1500 branded pin images for each blog post.

Run from frontend/:  python scripts/generate_pins.py
Output: frontend/public/pins/{slug}.png
"""
import json
import os

from PIL import Image, ImageDraw, ImageFont

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
POSTS = json.load(open(os.path.join(BASE, "src", "data", "blog-posts.json"), encoding="utf-8"))
OUT = os.path.join(BASE, "public", "pins")
os.makedirs(OUT, exist_ok=True)

W, H = 1000, 1500
FONT_DIR = "C:/Windows/Fonts"
GEORGIA = os.path.join(FONT_DIR, "georgia.ttf")
GEORGIA_B = os.path.join(FONT_DIR, "georgiab.ttf")
ARIAL = os.path.join(FONT_DIR, "arial.ttf")

PAPER = (243, 244, 246)
GRAY = (156, 163, 175)
AMBER = (245, 158, 11)
GREEN = (52, 211, 153)
NEUTRAL = (203, 213, 225)

ACCENTS = {"Guide": GREEN, "Comparison": AMBER}


def gradient(size, top, bottom):
    img = Image.new("RGB", size)
    d = ImageDraw.Draw(img)
    for y in range(size[1]):
        t = y / (size[1] - 1)
        c = tuple(int(top[i] + (bottom[i] - top[i]) * t) for i in range(3))
        d.line([(0, y), (size[0], y)], fill=c)
    return img


def wrap(draw, text, font, max_width):
    words = text.split()
    lines, cur = [], ""
    for wd in words:
        test = (cur + " " + wd).strip()
        if draw.textlength(test, font=font) <= max_width:
            cur = test
        else:
            if cur:
                lines.append(cur)
            cur = wd
    if cur:
        lines.append(cur)
    return lines


def letter_spaced(draw, pos, text, font, tracking, fill):
    x, y = pos
    for ch in text:
        draw.text((x, y), ch, font=font, fill=fill)
        x += draw.textlength(ch, font=font) + tracking
    return x


def draw_pin(post, accent):
    img = gradient((W, H), (17, 24, 39), (31, 41, 55))
    d = ImageDraw.Draw(img)

    accent_dim = tuple(int(accent[i] * 0.35 + 17 * 0.65) for i in range(3))

    ring = ImageDraw.Draw(img)
    ring.ellipse([700, 1050, 1120, 1470], outline=accent_dim, width=3)

    word_font = ImageFont.truetype(GEORGIA_B, 44)
    d.rectangle([100, 112, 118, 130], fill=accent)
    letter_spaced(d, (140, 100), "NAXELY", word_font, 8, PAPER)

    label = (post.get("label") or "Article").upper()
    chip_font = ImageFont.truetype(ARIAL, 26)
    chip_w = d.textlength(label, font=chip_font)
    chip_x0, chip_y0, chip_h = W - 100 - chip_w - 56, 108, 44
    chip_x1 = W - 100
    d.rounded_rectangle([chip_x0, chip_y0, chip_x1, chip_y0 + chip_h], radius=chip_h // 2,
                        outline=accent, width=2)
    d.text(((chip_x0 + chip_x1) / 2, chip_y0 + chip_h / 2), label, font=chip_font,
           fill=accent, anchor="mm")

    title = post["title"]
    max_w = W - 200
    for size in (84, 76, 68, 60, 54, 48, 44):
        title_font = ImageFont.truetype(GEORGIA_B, size)
        lines = wrap(d, title, title_font, max_w)
        if len(lines) <= 6:
            break

    line_h = int(title_font.size * 1.18)
    block_h = line_h * len(lines)
    ty = 400
    for ln in lines:
        d.text((100, ty), ln, font=title_font, fill=PAPER)
        ty += line_h

    rule_y = ty + 56
    d.rectangle([100, rule_y, 180, rule_y + 6], fill=accent)

    site_font = ImageFont.truetype(GEORGIA_B, 40)
    d.text((100, rule_y + 34), "naxely.com", font=site_font, fill=PAPER)

    tag_font = ImageFont.truetype(ARIAL, 24)
    d.text((100, rule_y + 96), "AI client report generator — CSV & Sheets to branded PDF",
           font=tag_font, fill=GRAY)

    out = os.path.join(OUT, f"{post['slug']}.png")
    img.save(out, optimize=True)
    print(f"  {out.split(os.sep)[-1]}  ({os.path.getsize(out) // 1024} KB)")


for post in POSTS:
    accent = ACCENTS.get(post.get("label"), NEUTRAL)
    draw_pin(post, accent)

print(f"done: {len(POSTS)} pins")