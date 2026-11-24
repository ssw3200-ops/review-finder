"""강남맛집 (강남맛집.net) — 카드: [Blog][방문형][N일 남음] [시도 구군] 업체 / 제공내역 / 신청 A / 모집 B"""
import re

from bs4 import BeautifulSoup

from crawler.common import detect_media, detect_region, fetch, has_extra_mission, parse_deadline, to_int

SITE = "강남맛집"
BASE = "https://xn--939au0g4vj8sq.net"
ID_RE = re.compile(r"^(?:https://(?:xn--939au0g4vj8sq|강남맛집)\.net)?/cp/\?id=(\d+)$")
MAX_PAGES = 10


def list_urls():
    # 지역(방문형), 제품(배송형), 클립, 기자단
    return [f"{BASE}/cp/?ca=20", f"{BASE}/cp/?ca=30", f"{BASE}/cp/?ch=clip", f"{BASE}/cp/?ca=40"]


def _card(a):
    """제목 링크에서 위로 올라가며 '신청 N / 모집 M'이 있고 캠페인이 하나뿐인 카드를 찾는다."""
    node = a
    for _ in range(6):
        node = node.parent
        if node is None:
            return None
        ids = {ID_RE.match(x["href"]).group(1) for x in node.find_all("a", href=ID_RE)}
        if len(ids) > 1:  # 여러 캠페인을 감싼 목록까지 올라감 → 카드 아님 (리뷰 영역 링크 등)
            return None
        if re.search(r"신청\s*[\d,]+\s*/\s*모집", node.get_text(" ", strip=True)):
            return node
    return None


def parse(html, today=None):
    soup = BeautifulSoup(html, "html.parser")
    items, done = [], set()
    for a in soup.find_all("a", href=ID_RE):
        cid = ID_RE.match(a["href"]).group(1)
        title = a.get_text(" ", strip=True)
        if cid in done or not title or title.startswith("캠페인"):  # 이미지 링크는 건너뛰고 제목 링크 사용
            continue
        card = _card(a)
        if card is None:
            continue
        done.add(cid)
        text = card.get_text(" ", strip=True)
        badges = " ".join(e.get_text(" ", strip=True) for e in card.find_all("em"))
        dd = card.find("dd")
        offer = dd.get_text(" ", strip=True) if dd else ""

        m = re.search(r"신청\s*(\d[\d,]*)\s*/\s*모집\s*(\d[\d,]*)", text)
        applied, recruit = (to_int(m.group(1)), to_int(m.group(2))) if m else (None, None)

        typ = "배송" if "배송형" in badges else ("기자단" if "기자단" in badges or "[기자단]" in title else "방문")
        tag = re.match(r"^\[([^\]]+)\]", title)
        region_src = "배송" if typ == "배송" else (tag.group(1) if tag and tag.group(1) != "기자단" else "")
        sido, detail = detect_region(region_src) if region_src else ("기타", "")
        name = re.sub(r"^\[[^\]]+\]\s*", "", title).strip()

        items.append({
            "id": f"gm-{cid}",
            "site": SITE,
            "url": f"{BASE}/cp/?id={cid}",
            "title": name or title,
            "offer": offer[:120],
            "media": detect_media(badges),
            "sido": sido,
            "area": detail,
            "type": typ,
            "applied": applied,
            "recruit": recruit,
            "deadline": parse_deadline(badges or text, today),
            "extra_mission": has_extra_mission(offer),
        })
    return items


def crawl():
    seen = {}
    for base_url in list_urls():
        for page in range(1, MAX_PAGES + 1):
            url = base_url if page == 1 else f"{base_url}&page={page}"
            html = fetch(url)
            if not html:
                break
            new = [i for i in parse(html) if i["id"] not in seen]
            for i in new:
                seen[i["id"]] = i
            if not new:
                break
    return list(seen.values())
