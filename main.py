"""Daily News Brief Image Generator — Apify Actor entry point.

Reads Actor input (date + 3-8 headlines), renders a 1024x1024 PNG with
the pure-Python/Pillow renderer in src/render.py (no network, no LLM,
no API key), stores the PNG in the default key-value store and pushes
one dataset item per image.

Pay-per-event: each dataset item is one billable event
(apify-default-dataset-item, $0.05/image, set as the Primary event in
the Store monetization settings). No explicit Actor.charge() call is
needed — pushing to the dataset fires the default event automatically.

Local fallback: if the Apify SDK is not installed (local dev machine),
the Actor runs in stdlib mode: --input <input.json> --output <outdir>
writes news-YYYY-MM-DD.png + caption.txt + dataset.json, exactly like
the original Skill CLI. This is what test/run_local.sh uses.
"""
import argparse
import io
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))
from render import render_image  # noqa: E402

DATE_RE = re.compile(r"\d{4}-\d{2}-\d{2}")


def validate(data):
    """Validate Actor input; return a cleaned copy or raise ValueError."""
    if not isinstance(data, dict):
        raise ValueError("input must be a JSON object")
    if not DATE_RE.fullmatch(str(data.get("date", ""))):
        raise ValueError("date must be YYYY-MM-DD")
    lang = data.get("language", "zh")
    if lang not in ("zh", "en"):
        raise ValueError("language must be zh or en")
    headlines = data.get("headlines")
    if not isinstance(headlines, list) or not 3 <= len(headlines) <= 8:
        raise ValueError("headlines must be a list of 3-8 items")
    clean = {
        "date": data["date"],
        "language": lang,
        "brand": str(data.get("brand") or "")[:40] or None,
        "accent": str(data.get("accent") or "")[:7] or None,
        "headlines": [],
    }
    for h in headlines:
        if not isinstance(h, dict) or not str(h.get("title", "")).strip():
            raise ValueError("every headline needs a non-empty title")
        clean["headlines"].append({
            "title": str(h["title"])[:60],
            "source": str(h.get("source") or "")[:40],
            "summary": str(h.get("summary") or "")[:120],
        })
    return clean


def make_caption(data):
    label = "每日新闻" if data["language"] == "zh" else "Daily News"
    return "%s %s：%s" % (data["date"], label, data["headlines"][0]["title"])


def make_item(data, image_key, image_url):
    return {
        "date": data["date"],
        "language": data["language"],
        "headlineCount": len(data["headlines"]),
        "imageKey": image_key,
        "imageUrl": image_url,
        "caption": make_caption(data),
        "imageWidth": 1024,
        "imageHeight": 1024,
        "priceUsdPerImage": 0.05,
    }


def run_local(data, outdir):
    """Stdlib fallback for local testing (no Apify SDK)."""
    data = validate(data)
    img = render_image(data)
    assert img.size == (1024, 1024), "unexpected size %s" % (img.size,)
    outdir = Path(outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    image_key = "news-%s.png" % data["date"]
    png = outdir / image_key
    img.save(png)
    caption = make_caption(data)
    (outdir / "caption.txt").write_text(caption, encoding="utf-8")
    item = make_item(data, image_key, str(png))
    (outdir / "dataset.json").write_text(
        json.dumps([item], ensure_ascii=False, indent=2), encoding="utf-8")
    print("PNG: %s (%d bytes)" % (png, png.stat().st_size))
    print("caption: %s" % caption)
    print("dataset item: %s" % json.dumps(item, ensure_ascii=False))
    return item


async def run_apify():
    from apify import Actor  # Apify SDK (apify package, Python 3.12)

    async with Actor:
        data = validate(await Actor.get_input() or {})
        Actor.log.info("Rendering %s: %d headlines (%s)",
                       data["date"], len(data["headlines"]), data["language"])
        img = render_image(data)
        assert img.size == (1024, 1024), "unexpected size %s" % (img.size,)
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        image_key = "news-%s.png" % data["date"]
        await Actor.set_value(image_key, buf.getvalue(),
                              content_type="image/png")
        Actor.log.info("Stored %s (%d bytes) in key-value store",
                       image_key, buf.tell())
        # Key-value store URL pattern; the console shows the real link.
        item = make_item(data, image_key, image_key)
        await Actor.push_data(item)
        Actor.log.info("Pushed dataset item: %s", make_caption(data))
        return item


def main():
    ap = argparse.ArgumentParser(description="Daily News Brief Image Actor")
    ap.add_argument("--input", help="input JSON (local mode only)")
    ap.add_argument("--output", default="out",
                    help="output dir (local mode only)")
    args = ap.parse_args()

    try:
        from apify import Actor  # noqa: F401
        sdk_available = True
    except ImportError:
        sdk_available = False

    # On the Apify platform the SDK is installed and input comes from
    # Actor.get_input(); locally (or --input given) use stdlib mode.
    if sdk_available and not args.input:
        import asyncio
        asyncio.run(run_apify())
        return

    if not args.input:
        print("ERROR: local mode needs --input <input.json> "
              "(Apify SDK not installed)", file=sys.stderr)
        sys.exit(1)
    try:
        data = json.loads(Path(args.input).read_text(encoding="utf-8"))
    except Exception as exc:
        print("ERROR: cannot read input JSON: %s" % exc, file=sys.stderr)
        sys.exit(1)
    try:
        run_local(data, args.output)
    except ValueError as exc:
        print("ERROR: %s" % exc, file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
