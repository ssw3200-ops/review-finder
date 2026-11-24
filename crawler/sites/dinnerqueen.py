"""디너의여왕 (dinnerqueen.net) — 목록 카드: [시도 구군][릴스] 제목 / 제공내역 / N일 남음 / 신청 A / B"""
import re
from urllib.parse import quote

from bs4 import BeautifulSoup

from crawler.common import (SIDO, detect_media, detect_region, fetch, has_extra_mission,
                            parse_deadline, to_int)

SITE = "디너의여왕"
BASE = "https://dinnerqueen.net"
ID_RE = re.compile(r"^(?:https://dinnerqueen\.net)?/taste/(\d+)$")
MAX_PAGES = 5


def list_urls():
    urls = [f"{BASE}/taste?ct={quote(ct)}" for ct in ("릴스", "클립", "배송", "기자단")]
    urls += [f"{BASE}/taste?ct={quote('지역')}&area1={quote(s)}" for s in SIDO]
    return urls


def _card(a):
    """링크에서 위로 올라가며 '신청' 수치가 들어있는 카드 요소를 찾는다."""
    node = a
    for _ in range(6):
        node = node.parent
        if node is None:
            return None
        if "신청" in node.get_text(" ", strip=True) and len(node.find_all("a", href=ID_RE)) == 1:
            return node
    return None


def parse(html, today=None):
    soup = BeautifulSoup(html, "html.parser")
    items = []
    for a in soup.find_all("a", href=ID_RE):
        card = _card(a)
        if card is None:  # 상단 배너 링크 등
            continue
        cid = ID_RE.match(a["href"]).group(1)
        img = a.find("img")
        text = card.get_text(" ", strip=True)
        title = (img.get("alt") if img else "") or text.split(" 신청")[0]
        title = title.strip()
        badges = " ".join(s.get_text(strip=True) for s in a.find_all("strong"))

        m = re.search(r"신청\s*(\d[\d,]*)\s*/\s*(?:모집\s*)?(\d[\d,]*)", text)
        applied, recruit = (to_int(m.group(1)), to_int(m.group(2))) if m else (None, None)

        tags = re.findall(r"\[([^\]]+)\]", title)
        region_src = next((t for t in tags if t not in ("릴스", "클립", "인스타", "인스타그램", "블로그", "쇼츠")), "")
        if "배송" in badges:
            region_src = "배송"
        sido, detail = detect_region(region_src)
        name = re.sub(r"^(\[[^\]]+\]\s*)+", "", title).strip()
        body = text.replace(a.get_text(" ", strip=True), "", 1).strip()  # 이미지 링크(배지) 제외
        offer = body.replace(title, "", 1)
        offer = re.split(r"\d+\s*일\s*남음|D\s*-|신청\s*\d", offer)[0].strip()

        items.append({
            "id": f"dq-{cid}",
            "site": SITE,
            "url": f"{BASE}/taste/{cid}",
            "title": name or title,
            "offer": offer[:120],
            "media": detect_media(badges + " " + title),
            "sido": sido,
            "area": detail,
            "type": "배송" if "배송" in badges else ("기자단" if "기자단" in badges else "방문"),
            "applied": applied,
            "recruit": recruit,
            "deadline": parse_deadline(text, today),
            "extra_mission": has_extra_mission(text),
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
            if not new:  # 페이지 파라미터가 없거나 끝
                break
    return list(seen.values())
