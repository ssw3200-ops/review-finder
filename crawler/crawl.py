"""모든 사이트를 수집해 docs/data/campaigns.json 으로 저장.

실행: python -m crawler.crawl
사이트 추가: crawler/sites/ 에 crawl()을 가진 모듈을 만들고 SITES에 등록.
"""
import json
import traceback
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

from crawler.sites import dinnerqueen, mrblog

SITES = [dinnerqueen, mrblog]
OUT = Path(__file__).resolve().parent.parent / "docs" / "data" / "campaigns.json"
KST = timezone(timedelta(hours=9))


def main():
    old = {}
    if OUT.exists():
        try:
            old_data = json.loads(OUT.read_text(encoding="utf-8"))
            old = {i["id"]: i for i in old_data.get("items", [])}
        except (ValueError, KeyError):
            pass

    items, status = [], {}
    for mod in SITES:
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
        a, r = i.get("applied"), i.get("recruit")
        i["ratio"] = round(a / r, 1) if a is not None and r else None

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps({
        "updated": datetime.now(KST).strftime("%Y-%m-%d %H:%M"),
        "sites": status,
        "items": items,
    }, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"총 {len(items)}건 저장 → {OUT}")


if __name__ == "__main__":
    main()
