"""Generate the 1200x630 link-preview card (assets/social-card.png).

LinkedIn, X/Twitter, Slack and iMessage show this image when the site URL is
shared. It is drawn with Pillow from profile.csv on every build, so the name,
title and metrics stay current, and it uses the bundled Merriweather / Open Sans
fonts so it renders identically locally and in CI.
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
NAVY = (10, 22, 40)
NAVY_MID = (21, 34, 64)
GOLD = (184, 149, 58)
GOLD_LIGHT = (212, 174, 90)
MIST = (200, 212, 224)
SILVER = (143, 163, 188)
WHITE = (248, 250, 252)


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


def _headshot(diameter: int) -> Image.Image | None:
    if not HEADSHOT.exists():
        return None
    photo = ImageOps.fit(Image.open(HEADSHOT).convert("RGB"), (diameter, diameter), centering=(0.5, 0.3))
    mask = Image.new("L", (diameter * 4, diameter * 4), 0)
    ImageDraw.Draw(mask).ellipse((0, 0, diameter * 4 - 1, diameter * 4 - 1), fill=255)
    photo.putalpha(mask.resize((diameter, diameter), Image.LANCZOS))
    return photo


def render(profile: dict) -> Image.Image:
    img = Image.new("RGB", (W, H), NAVY)
    draw = ImageDraw.Draw(img)

    # Faint grid and a warm glow behind the portrait, echoing the site hero.
    for x in range(0, W, 60):
        draw.line([(x, 0), (x, H)], fill=(16, 29, 50), width=1)
    for y in range(0, H, 60):
        draw.line([(0, y), (W, y)], fill=(16, 29, 50), width=1)
    glow = Image.new("L", (W, H), 0)
    ImageDraw.Draw(glow).ellipse((760, 70, 1180, 490), fill=60)
    glow = glow.resize((W // 8, H // 8)).resize((W, H), Image.BILINEAR)
    img.paste(Image.new("RGB", (W, H), NAVY_MID), mask=glow)
    draw = ImageDraw.Draw(img)

    left, text_w = 80, 640

    # Eyebrow
    draw.line([(left, 118), (left + 40, 118)], fill=GOLD, width=2)
    draw.text((left + 54, 108), "PHYSICIAN-SCIENTIST · MAYO CLINIC", font=_font("OpenSans-SemiBold.ttf", 19), fill=GOLD_LIGHT)

    # Name
    name = profile.get("name", "Reza Shahriarirad, M.D.").strip()
    first, _, rest = name.partition(" ")
    draw.text((left, 150), first, font=_font("Merriweather-Bold.ttf", 66), fill=WHITE)
    draw.text((left, 236), rest, font=_fit(draw, rest, "Merriweather-Italic.ttf", 64, text_w), fill=GOLD_LIGHT)

    # Title and focus
    title = f"{profile.get('title', 'Research Fellow').strip()}, Surgical Innovation"
    draw.text((left, 340), title, font=_fit(draw, title, "OpenSans-Regular.ttf", 26, text_w), fill=MIST)
    focus = "Surgical AI · Computer Vision · Digital Health"
    draw.text((left, 380), focus, font=_fit(draw, focus, "OpenSans-Regular.ttf", 22, text_w), fill=SILVER)

    # Metrics row
    metrics = [
        (f"{_int(profile.get('pub_count')):,}", "PUBLICATIONS"),
        (f"{_int(profile.get('citations_cached')):,}", "CITATIONS"),
        (f"{_int(profile.get('h_index_cached'))}", "H-INDEX"),
        (f"{_int(profile.get('peer_reviews'))}", "PEER REVIEWS"),
    ]
    num_font, label_font = _font("Merriweather-Bold.ttf", 40), _font("OpenSans-SemiBold.ttf", 14)
    x = left
    for value, label in metrics:
        draw.text((x, 452), value, font=num_font, fill=GOLD_LIGHT)
        draw.text((x, 506), label, font=label_font, fill=SILVER)
        x += max(draw.textlength(value, font=num_font), draw.textlength(label, font=label_font)) + 44

    # Site address
    url = profile.get("canonical_url", "").split("://", 1)[-1].rstrip("/")
    if url:
        draw.text((left, 566), url, font=_font("OpenSans-Regular.ttf", 18), fill=SILVER)

    # Portrait with gold ring
    photo = _headshot(300)
    if photo:
        cx, cy, r = 970, 280, 150
        draw.ellipse((cx - r - 14, cy - r - 14, cx + r + 14, cy + r + 14), outline=(60, 52, 30), width=10)
        draw.ellipse((cx - r - 5, cy - r - 5, cx + r + 5, cy + r + 5), outline=GOLD, width=4)
        img.paste(photo, (cx - r, cy - r), photo)

    # Gold baseline accent
    draw.rectangle((0, H - 8, W, H), fill=GOLD)
    return img


def main():
    profile = get_profile(load_all_data())
    OUT.parent.mkdir(parents=True, exist_ok=True)
    render(profile).save(OUT, optimize=True)
    print(f"  Generated {OUT.relative_to(ROOT)} ({OUT.stat().st_size:,} bytes, {W}x{H})")


if __name__ == "__main__":
    main()
