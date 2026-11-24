"""미블 (mrblog.net) — 카드: [배지] 지역 / 업체명 / 제공내역 / N일 남음 / 신청 A명 / 모집 B명"""
import re

from bs4 import BeautifulSoup

from crawler.common import detect_media, detect_region, fetch, has_extra_mission, parse_deadline, to_int

SITE = "미블"
BASE = "https://www.mrblog.net"
ID_RE = re.compile(r"^(?:https://www\.mrblog\.net)?/campaigns/(\d+)$")
BADGES = ("릴스", "클립", "배송", "인스타", "인스타그램", "유튜브", "쇼츠", "기자단")
MAX_PAGES = 5


def list_urls():
    return [f"{BASE}/campaigns/region", f"{BASE}/campaigns/delivery",
            f"{BASE}/campaigns?is_instagram=1", f"{BASE}/campaigns?sort=마감순"]


def parse(html, today=None, insta_page=False):
    soup = BeautifulSoup(html, "html.parser")
    items = []
    for a in soup.find_all("a", href=ID_RE):
        text = a.get_text(" ", strip=True)
        if "신청" not in text:
            continue
        cid = ID_RE.match(a["href"]).group(1)
        strong = a.find("strong")
        title = strong.get_text(" ", strip=True) if strong else ""
        p = a.find("p")
        offer = p.get_text(" ", strip=True) if p else ""

        # 업체명 앞부분 = 배지 + 지역
        head = text.split(title)[0].strip() if title else ""
        badge = next((b for b in BADGES if head.startswith(b)), "")
        region_src = head[len(badge):].strip() if badge else head
        if badge == "배송" or "배송" in head:
            region_src = "배송"
        sido, detail = detect_region(region_src)

        m = re.search(r"신청\s*(\d[\d,]*)\s*명?\s*/\s*모집\s*(\d[\d,]*)", text)
        applied, recruit = (to_int(m.group(1)), to_int(m.group(2))) if m else (None, None)

        items.append({
            "id": f"mb-{cid}",
            "site": SITE,
            "url": f"{BASE}/campaigns/{cid}",
            "title": title,
            "offer": offer[:120],
            "media": detect_media(badge + " " + offer, default="insta" if insta_page else "blog"),
            "sido": sido,
            "area": detail,
            "type": "배송" if "배송" in head else ("기자단" if badge == "기자단" else "방문"),
            "applied": applied,
            "recruit": recruit,
            "deadline": parse_deadline(text, today),
            "extra_mission": has_extra_mission(offer),
        })
    return items


def crawl():
    seen = {}
    for base_url in list_urls():
        insta = "is_instagram" in base_url
        sep = "&" if "?" in base_url else "?"
        for page in range(1, MAX_PAGES + 1):
            url = base_url if page == 1 else f"{base_url}{sep}page={page}"
            html = fetch(url)
            if not html:
                break
            new = [i for i in parse(html, insta_page=insta) if i["id"] not in seen]
            for i in new:
                seen[i["id"]] = i
            if not new:
                break
    return list(seen.values())
