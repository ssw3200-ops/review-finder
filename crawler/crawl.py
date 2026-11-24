"""모든 사이트를 수집해 docs/data/campaigns.json 으로 저장.

실행: python -m crawler.crawl
사이트 추가: crawler/sites/ 에 crawl()을 가진 모듈을 만들고 SITES에 등록.
"""
import json
import traceback
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

from crawler import common
from crawler.sites import assaview, cometoplay, dinnerqueen, gangnam, mrblog

SITES = [dinnerqueen, mrblog, cometoplay, assaview]  # GitHub Actions(해외)에서 수집
LOCAL_SITES = [gangnam]  # 해외 접속 차단 → 국내 PC에서 수집 (python -m crawler.crawl --local)
DATA = Path(__file__).resolve().parent.parent / "docs" / "data"
OUT = DATA / "campaigns.json"
KST = timezone(timedelta(hours=9))


def main(sites=None, out=None):
    global OUT
    sites = sites or SITES
    OUT = out or OUT
    old = {}
    if OUT.exists():
        try:
            old_data = json.loads(OUT.read_text(encoding="utf-8"))
            old = {i["id"]: i for i in old_data.get("items", [])}
        except (ValueError, KeyError):
            pass

    items, status = [], {}
    for mod in sites:
        print(f"[{mod.SITE}] 수집 시작")
        try:
            got = mod.crawl()
            status[mod.SITE] = {"ok": True, "count": len(got)}
        except Exception:  # 한 사이트가 실패해도 나머지는 계속
            traceback.print_exc()
            got = [i for i in old.values() if i["site"] == mod.SITE]  # 직전 데이터 유지
            status[mod.SITE] = {"ok": False, "count": len(got)}
        print(f"[{mod.SITE}] {len(got)}건")
        items += got

    today = date.today().isoformat()
    items = [i for i in items if not i.get("deadline") or i["deadline"] >= today]
    for i in items:
        i["cat"] = common.detect_cat(f'{i.get("title","")} {i.get("offer","")}', i.get("type"), i.pop("cat_hint", ""))
        a, r = i.get("applied"), i.get("recruit")
        i["ratio"] = round(a / r, 1) if a is not None and r else None

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps({
        "updated": datetime.now(KST).strftime("%Y-%m-%d %H:%M"),
        "sites": status,
        "items": items,
    }, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"총 {len(items)}건 저장 → {OUT}")
    # 진단: 사이트별 요청 결과 (상태코드·크기) — Actions 로그 없이 원인 확인용
    (OUT.parent / ("debug_local.json" if OUT.name == "local.json" else "debug.json")).write_text(json.dumps(
        [{"url": u, "status": st, "bytes": b} for u, st, b in common.LOG], ensure_ascii=False, indent=0), encoding="utf-8")


if __name__ == "__main__":
    import sys
    if "--local" in sys.argv:
        main(LOCAL_SITES, DATA / "local.json")
    else:
        main()
