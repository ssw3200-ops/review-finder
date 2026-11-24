@echo off
chcp 65001 >nul
REM 국내 PC에서 강남맛집 수집 → docs/data/local.json 올리기 (작업 스케줄러가 10:00, 16:00에 실행)
cd /d "%~dp0.."
git pull --rebase -q origin main
python -m crawler.crawl --local >> tools\local.log 2>&1
git add docs/data/local.json docs/data/debug_local.json
git diff --cached --quiet || git commit -q -m "data: 국내 수집(강남맛집) 갱신"
git push -q origin main >> tools\local.log 2>&1
