#!/bin/sh
# 맥/리눅스용: crontab -e 에  0 10,16 * * * /경로/review-finder/tools/run_local.sh
cd "$(dirname "$0")/.." || exit 1
git pull --rebase -q origin main
python3 -m crawler.crawl --local >> tools/local.log 2>&1
git add docs/data/local.json docs/data/debug_local.json
git diff --cached --quiet || git commit -q -m "data: 국내 수집(강남맛집) 갱신"
git push -q origin main >> tools/local.log 2>&1
