# Daily News Brief Image Generator

> Give 3–8 headlines, get a clean **1024×1024** shareable news image plus a
> one-line caption — in seconds, with no design tool and no API key.

## Highlights

- **Pure Python/Pillow rendering** — no LLM, no model API, no network at
  runtime. Input headlines are rendered exactly as given; nothing is
  invented.
- **Share-ready output** — one 1024×1024 PNG (`news-YYYY-MM-DD.png`) in the
  key-value store, plus one dataset item with the image key, caption and
  headline count.
- **Bilingual** — Chinese (`zh`) or English (`en`) header and footer.
- **Predictable price** — $0.05 per image, pay-per-event.

## Input

| Field | Required | Description |
| --- | --- | --- |
| `date` | yes | Date shown on the image, `YYYY-MM-DD` |
| `headlines` | yes | 3–8 items. Each: `title` (required, max 60 chars), `source` (optional, max 40), `summary` (optional, max 120) |
| `language` | no | `zh` (default) or `en` |
| `brand` | no | Footer brand, e.g. your outlet name (max 40 chars) |
| `accent` | no | Hex accent color, e.g. `#1A73E8` (default) |

Example input:

```json
{
  "date": "2026-11-25",
  "language": "zh",
  "brand": "Cashonly Daily",
  "headlines": [
    {"title": "央行开展5000亿元逆回购和8000亿元MLF操作", "source": "央广网"},
    {"title": "6G创新发展部省协同试点启动，8省市获批", "source": "央广网"},
    {"title": "小米三季度收入1072亿元，同比下降5.2%", "source": "央广网"}
  ]
}
```

## Output

- **Key-value store:** `news-YYYY-MM-DD.png` — 1024×1024 PNG.
- **Dataset (one item per image):**

```json
{
  "date": "2026-11-25",
  "language": "zh",
  "headlineCount": 3,
  "imageKey": "news-2026-11-25.png",
  "imageUrl": "news-2026-11-25.png",
  "caption": "2026-11-25 每日新闻：央行开展5000亿元逆回购和8000亿元MLF操作",
  "imageWidth": 1024,
  "imageHeight": 1024,
  "priceUsdPerImage": 0.05
}
```

The caption is the date + label + first headline, ready to paste with the
image on social media.

## Limits

- 3–8 headlines per run. Titles longer than 60 characters are truncated
  with an ellipsis so text never overflows the image.
- One image per run (one dataset item = one billable event).
- Headlines are rendered verbatim — the Actor does not fetch, verify or
  summarise news. Supply headlines you have the right to use.
- No network access is used at runtime; fonts are Noto Sans CJK (Chinese)
  with DejaVu fallback (Latin).

## Price

**$0.05 per image**, pay-per-event: each dataset item
(`apify-default-dataset-item`) is one billable event, set as the **Primary
event** in the Store monetization settings. Rental pricing is retired and
is not used.

Cost note: creator profit = **80% of revenue − platform costs**. The
Actor is a tiny CPU-only Python job (one Pillow render, no model calls),
so platform compute cost per run is a fraction of a cent — the $0.05
price leaves a comfortable margin. Set a max cost per run in the
monetization settings so a run can never cost more than it earns.

## Local development

```bash
pip install -r requirements.txt
python3 main.py --input test/input-5zh.json --output out/test-5zh
python3 test/run_local.sh   # runs all 3 demo inputs + verification
```

Local mode (no Apify SDK installed) writes `news-YYYY-MM-DD.png`,
`caption.txt` and `dataset.json` into the output directory.

## Status

- v1.0.0 — built from the same renderer already submitted to Agensi as a
  $29 Skill (pending review). Tested locally on 3 demo inputs (3zh, 5zh,
  8en): all PNGs 1024×1024, captions correct, byte-identical re-renders.
- Published to the Apify Store 2026-11-26 (free, not monetized yet): https://apify.com/cashonly/daily-news-brief-image-actor — Build 0.0.5, test run verified (2026-11-25, zh, 5 headlines, 1024x1024 PNG, 1 dataset item). Monetization / pricing and KYC are still to be set up by the account owner when ready.
