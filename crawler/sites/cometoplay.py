"""놀러와체험단 (cometoplay.kr) — 카드 링크: [시도 구군] 제목 #태그 / D-day N / 신청 A 명 / 모집 B 명"""
import re

from bs4 import BeautifulSoup

from crawler.common import detect_media, detect_region, fetch, has_extra_mission, parse_deadline, to_int

SITE = "놀러와체험단"
BASE = "https://www.cometoplay.kr"
ID_RE = re.compile(r"(?:^|/)item\.php\?it_id=(\d+)")
MAX_PAGES = 10


def list_urls():
    # 001 지역, 002 제품, 004 기자단
    return [f"{BASE}/item_list.php?category_id={c}" for c in ("001", "002", "004")]


def parse(html, today=None):
    soup = BeautifulSoup(html, "html.parser")
    items, done = [], set()
    for a in soup.find_all("a", href=ID_RE):
        text = a.get_text(" ", strip=True)
        m = re.search(r"신청\s*(\d[\d,]*)\s*명?\s*/\s*모집\s*(\d[\d,]*)", text)
        cid = ID_RE.search(a["href"]).group(1)
        if not m or cid in done:  # 이미지 전용 링크 등은 건너뜀
            continue
        done.add(cid)
        head = text.split("#")[0]
        head = re.split(r"D\s*-?\s*day", head, flags=re.I)[0].strip()
        tag = re.match(r"^\[([^\]]+)\]", head)
        tag_txt = tag.group(1) if tag else ""
        if tag_txt in ("쇼핑몰", "배송", "제품"):
            typ, sido, area = "배송", "배송·전국", ""
        elif tag_txt == "기자단":
            typ, sido, area = "기자단", "기타", ""
        else:
            typ = "방문"
            sido, area = detect_region(tag_txt)
        title = re.sub(r"^(\[[^\]]+\]\s*)+", "", head).strip()
        name = re.search(r"\[([^\]]+)\]\s*$", title)  # 끝의 [업체명]
        hashtags = " ".join(re.findall(r"#\S+", text))

        card = a.parent
        icons = " ".join((i.get("alt", "") + " " + i.get("src", "")) for i in (card.find_all("img") if card else []))

        items.append({
            "id": f"np-{cid}",
            "site": SITE,
            "url": f"{BASE}/item.php?it_id={cid}",
            "title": name.group(1) if name else title,
            "offer": (title if name else "")[:120] or hashtags[:120],
            "media": detect_media(icons + " " + head),
            "sido": sido,
            "area": area,
            "type": typ,
            "applied": to_int(m.group(1)),
            "recruit": to_int(m.group(2)),
            "deadline": parse_deadline(text, today),
            "extra_mission": has_extra_mission(head) or "구매평" in head,
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
