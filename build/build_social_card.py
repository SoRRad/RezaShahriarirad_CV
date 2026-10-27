"""Generate the 1200x630 link-preview card (assets/social-card.png).

LinkedIn, X/Twitter, Slack and iMessage show this image when the site URL is
shared. It is drawn with Pillow from profile.csv on every build, so the name,
title and metrics stay current, and it uses the bundled Space Grotesk / Inter /
JetBrains Mono fonts so it renders identically locally and in CI.
"""
from __future__ import annotations

import pathlib
import sys

from PIL import Image, ImageDraw, ImageFont, ImageOps

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from utils import ROOT, get_profile, load_all_data  # noqa: E402

OUT = ROOT / "assets" / "social-card.png"
HEADSHOT = ROOT / "assets" / "headshot.jpg"
FONTS = pathlib.Path(__file__).parent / "static_assets" / "fonts"

W, H = 1200, 630
INK = (10, 15, 26)
INK_MID = (17, 26, 43)
GRID = (20, 29, 46)
CYAN = (34, 211, 238)
AMBER = (245, 184, 65)
INK_TEXT = (230, 237, 245)
DIM = (138, 155, 179)


def _font(name: str, size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(FONTS / name), size)


def _int(value, default=0) -> int:
    try:
        return int(str(value).replace(",", "").strip())
    except (TypeError, ValueError):
        return default


def _fit(draw, text, font_name, size, max_width, min_size=18):
    """Shrink the font until the text fits on one line."""
    while size > min_size:
        font = _font(font_name, size)
        if draw.textlength(text, font=font) <= max_width:
            return font
        size -= 2
    return _font(font_name, min_size)


def _headshot(width: int, height: int) -> Image.Image | None:
    if not HEADSHOT.exists():
        return None
    return ImageOps.fit(Image.open(HEADSHOT).convert("RGB"), (width, height), centering=(0.5, 0.3))


def _corners(draw, box, length, color, width=3):
    """Corner brackets, the detection-box motif used across the site."""
    x0, y0, x1, y1 = box
    for (x, y, dx, dy) in ((x0, y0, 1, 1), (x1, y0, -1, 1), (x0, y1, 1, -1), (x1, y1, -1, -1)):
        draw.line([(x, y), (x + dx * length, y)], fill=color, width=width)
        draw.line([(x, y), (x, y + dy * length)], fill=color, width=width)


def _tag(draw, xy, text, font, fg, bg):
    x, y = xy
    w = draw.textlength(text, font=font)
    draw.rectangle((x, y, x + w + 16, y + 26), fill=bg)
    draw.text((x + 8, y + 4), text, font=font, fill=fg)


def render(profile: dict) -> Image.Image:
    img = Image.new("RGB", (W, H), INK)
    draw = ImageDraw.Draw(img)

    # Faint grid and a cool glow behind the portrait, echoing the site hero.
    for x in range(0, W, 48):
        draw.line([(x, 0), (x, H)], fill=GRID, width=1)
    for y in range(0, H, 48):
        draw.line([(0, y), (W, y)], fill=GRID, width=1)
    glow = Image.new("L", (W, H), 0)
    ImageDraw.Draw(glow).ellipse((740, 40, 1200, 520), fill=70)
    glow = glow.resize((W // 8, H // 8)).resize((W, H), Image.BILINEAR)
    img.paste(Image.new("RGB", (W, H), INK_MID), mask=glow)
    draw = ImageDraw.Draw(img)

    left, text_w = 72, 660
    mono = _font("JetBrainsMono-Regular.ttf", 17)
    mono_med = _font("JetBrainsMono-Medium.ttf", 16)

    # Eyebrow
    draw.text((left, 92), "// physician-scientist / surgical innovation / mayo clinic", font=mono, fill=CYAN)

    # Name
    name = profile.get("name", "Reza Shahriarirad, M.D.").strip()
    first, _, rest = name.partition(" ")
    surname, _, suffix = rest.partition(", ")
    draw.text((left, 128), first, font=_font("SpaceGrotesk-SemiBold.ttf", 76), fill=INK_TEXT)
    line2 = f"{surname}," if suffix else surname
    f2 = _fit(draw, line2 + " " + suffix, "SpaceGrotesk-SemiBold.ttf", 76, text_w)
    draw.text((left, 214), line2, font=f2, fill=INK_TEXT)
    if suffix:
        draw.text((left + draw.textlength(line2 + " ", font=f2), 214), suffix, font=f2, fill=CYAN)

    # Title and focus
    title = f"{profile.get('title', 'Research Fellow').strip()} in Surgical Innovation"
    draw.text((left, 328), title, font=_fit(draw, title, "Inter-Regular.ttf", 26, text_w), fill=INK_TEXT)
    focus = "surgical_ai · computer_vision · digital_health"
    draw.text((left, 370), focus, font=_fit(draw, focus, "JetBrainsMono-Regular.ttf", 19, text_w), fill=DIM)

    # Metrics row
    metrics = [
        (f"{_int(profile.get('pub_count')):,}", "publications"),
        (f"{_int(profile.get('citations_cached')):,}", "citations"),
        (f"{_int(profile.get('h_index_cached'))}", "h-index"),
        (f"{_int(profile.get('last_auth'))}", "senior_author"),
    ]
    num_font = _font("SpaceGrotesk-Medium.ttf", 44)
    draw.line([(left, 438), (left + text_w, 438)], fill=(31, 42, 61), width=1)
    x = left
    for value, label in metrics:
        draw.text((x, 452), value, font=num_font, fill=INK_TEXT)
        draw.text((x, 510), label, font=mono_med, fill=DIM)
        x += max(draw.textlength(value, font=num_font), draw.textlength(label, font=mono_med)) + 44

    # Site address
    url = profile.get("canonical_url", "").split("://", 1)[-1].rstrip("/")
    if url:
        draw.text((left, 570), url, font=mono, fill=DIM)

    # Portrait inside a detection box
    pw, ph = 300, 360
    px, py = 830, 120
    photo = _headshot(pw, ph)
    if photo:
        img.paste(photo, (px, py))
    pad = 12
    box = (px - pad, py - pad, px + pw + pad, py + ph + pad)
    draw.rectangle(box, outline=(34, 211, 238), width=1)
    _corners(draw, box, 26, CYAN, width=4)
    tag_font = _font("JetBrainsMono-Medium.ttf", 15)
    _tag(draw, (box[0], box[1] - 30), "physician_scientist 0.99", tag_font, INK, CYAN)
    _tag(draw, (box[0], box[3] + 6), "mayo_clinic", tag_font, INK, AMBER)

    # Cyan baseline accent
    draw.rectangle((0, H - 6, W, H), fill=CYAN)
    return img


def main():
    profile = get_profile(load_all_data())
    OUT.parent.mkdir(parents=True, exist_ok=True)
    render(profile).save(OUT, optimize=True)
    print(f"  Generated {OUT.relative_to(ROOT)} ({OUT.stat().st_size:,} bytes, {W}x{H})")


if __name__ == "__main__":
    main()
