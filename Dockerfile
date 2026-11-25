# Daily News Brief Image Generator — Apify Actor
# Python 3.12 slim + Pillow. No LLM, no API key, no network at runtime.
# CJK fonts are required: the renderer uses Noto Sans CJK for Chinese
# headlines (falls back to DejaVu for Latin-only input).
FROM python:3.12-slim

RUN apt-get update \
    && apt-get install -y --no-install-recommends fonts-noto-cjk \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /usr/src/app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . ./

# Apify runs the Actor as: python3 main.py (input comes from the platform).
CMD ["python3", "main.py"]
