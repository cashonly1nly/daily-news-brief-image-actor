#!/usr/bin/env bash
# Local test: run main.py (stdlib fallback) on all 3 demo inputs,
# verify each PNG is 1024x1024 with the same checks as the original
# Skill's verify.py, and record sha256 + sizes in test/results.txt.
set -e
cd "$(dirname "$0")/.."
rm -rf out
mkdir -p out

for name in 3zh 5zh 8en; do
  echo "=== $name ==="
  python3 main.py --input "test/input-$name.json" --output "out/test-$name"
  python3 ../daily-news-brief-image/scripts/verify.py \
    --input "test/input-$name.json" \
    --image "out/test-$name/news-2026-11-25.png"
done

{
  echo "Daily News Brief Image Actor — local test results"
  echo "date: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
  echo
  sha256sum out/test-*/news-2026-11-25.png out/test-*/caption.txt out/test-*/dataset.json
  echo
  ls -l out/test-*/news-2026-11-25.png
  echo
  for f in out/test-*/caption.txt; do echo "$f: $(cat "$f")"; done
} | tee test/results.txt
echo "ALL LOCAL TESTS PASSED"
