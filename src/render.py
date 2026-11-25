"""Render a daily news brief image: 1024x1024 PNG from headlines.

Pure Pillow, no network, no API key. Fonts never shrink below 28px;
over-long titles are truncated (with ellipsis) to fit pixel width.
"""
from PIL import Image, ImageDraw, ImageFont

W, H = 1024, 1024
MARGIN = 64
ACCENT_DEFAULT = "#1A73E8"
WHITE = (255, 255, 255)
BLACK = (17, 17, 17)
GREY = (110, 110, 110)
LIGHT = (230, 230, 230)

_CANDIDATES = {
    "cjk_regular": [("/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc", i) for i in range(5)]
    + [("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 0)],
    "cjk_bold": [("/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc", i) for i in range(5)]
    + [("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 0)],
    "latin_regular": [("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 0)],
    "latin_bold": [("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 0)],
}


def _has_ink(font, text):
    try:
        return font.getmask(text).getbbox() is not None
    except Exception:
        return False


def load_font(size, bold=False, cjk=False):
    """First candidate font that can actually render the probe glyphs."""
    key = ("cjk_" if cjk else "latin_") + ("bold" if bold else "regular")
    for path, index in _CANDIDATES[key]:
        try:
            font = ImageFont.truetype(path, size, index=index)
        except Exception:
            continue
        if _has_ink(font, "中文" if cjk else "Ag"):
            return font
    return ImageFont.load_default()


def _is_cjk(text):
    return any("\u4e00" <= ch <= "\u9fff" for ch in text)


def truncate(draw, text, font, max_w):
    """Truncate to pixel width with an ellipsis; never shrink the font."""
    if draw.textlength(text, font=font) <= max_w:
        return text
    ell = "…"
    lo, hi = 0, len(text)
    while lo < hi:
        mid = (lo + hi + 1) // 2
        if draw.textlength(text[:mid] + ell, font=font) <= max_w:
            lo = mid
        else:
            hi = mid - 1
    return text[:lo] + ell if lo > 0 else ell


def render_image(data):
    date = data["date"]
    lang = data.get("language", "zh")
    brand = data.get("brand") or ("Cashonly Daily" if lang == "en" else "每日新闻")
    accent = data.get("accent") or ACCENT_DEFAULT
    headlines = data["headlines"]
    cjk = lang == "zh" or any(_is_cjk(h["title"]) for h in headlines)

    img = Image.new("RGB", (W, H), WHITE)
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, W, 8], fill=accent)

    header_font = load_font(48, bold=True, cjk=cjk)
    title_font = load_font(36, bold=True, cjk=cjk)
    source_font = load_font(28, bold=False, cjk=cjk)
    footer_font = load_font(28, bold=False, cjk=cjk)
    num_font = load_font(28, bold=True, cjk=False)

    header_text = "%s  %s" % (date, "每日新闻" if lang == "zh" else "DAILY NEWS")
    y = 8 + 40
    d.text((MARGIN, y), header_text, font=header_font, fill=BLACK)
    y += 88
    d.line([(MARGIN, y), (W - MARGIN, y)], fill=LIGHT, width=2)
    y += 24

    avail = H - y - 90  # reserve footer + bottom margin
    row_h = min(140, avail // len(headlines))
    block_h = row_h * len(headlines)
    y += max(0, (avail - block_h) // 2)  # vertically centre short lists

    for i, h in enumerate(headlines):
        row_y = y + i * row_h
        cx, cy = MARGIN + 22, row_y + 30
        d.ellipse([cx - 22, cy - 22, cx + 22, cy + 22], fill=accent)
        d.text((cx, cy), str(i + 1), font=num_font, fill=WHITE, anchor="mm")
        tx = MARGIN + 60
        max_w = W - MARGIN - tx
        title = truncate(d, h["title"], title_font, max_w)
        d.text((tx, row_y + 8), title, font=title_font, fill=BLACK)
        source = h.get("source") or ""
        if source:
            d.text((tx, row_y + 8 + 44), source, font=source_font, fill=GREY)
        if i < len(headlines) - 1:
            d.line([(tx, row_y + row_h - 8), (W - MARGIN, row_y + row_h - 8)],
                   fill=LIGHT, width=1)

    fw = d.textlength(brand, font=footer_font)
    d.text(((W - fw) / 2, H - 64), brand, font=footer_font, fill=GREY)
    return img
