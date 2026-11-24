"""아싸뷰 (assaview.co.kr) — 카드: [매체 아이콘] 방문형|배송형|구매형|기자단 / N일 남음 / 제목 / 제공 / 신청 A / B명"""
import re

from bs4 import BeautifulSoup

from crawler.common import detect_media, detect_region, fetch, has_extra_mission, parse_deadline, to_int

SITE = "아싸뷰"
BASE = "https://www.assaview.co.kr"
ID_RE = re.compile(r"(?:^|/)campaign\.php\?cp_id=(\d+)")
TYPES = {"방문형": "방문", "배송형": "배송", "구매형": "배송", "기자단": "기자단"}
MAX_PAGES = 10


def list_urls():
    return [f"{BASE}/campaign_list.php?type={t}" for t in ("area", "product", "reporter")]


def parse(html, today=None):
    soup = BeautifulSoup(html, "html.parser")
    items, done = [], set()
    for a in soup.find_all("a", href=ID_RE):
        text = a.get_text(" ", strip=True)
        m = re.search(r"신청\s*(\d[\d,]*)\s*/\s*(\d[\d,]*)\s*명", text)
        cid = ID_RE.search(a["href"]).group(1)
        if not m or cid in done:  # 오픈 예정(신청 수 없음)·중복 제외
            continue
        done.add(cid)
        icons = " ".join(i.get("alt", "") for i in a.find_all("img"))
        media_icons = icons.replace("shop_icon", "")
        typ_word = next((w for w in TYPES if w in text), "")
        typ = TYPES.get(typ_word, "방문")

        # 텍스트 조각: [유형, 마감, 제목, 제공, 신청…]
        parts = [s.strip() for s in a.stripped_strings]
        after = parts[parts.index(typ_word) + 1:] if typ_word in parts else parts
        after = [p for p in after if not re.search(r"일\s*남음|오늘까지|마감|회차|20\d\d[./-]\d{1,2}[./-]\d{1,2}", p)]
        title = after[0] if after else ""
        offer = after[1] if len(after) > 1 and not after[1].startswith("신청") else ""

        tag = re.match(r"^\[([^\]]+)\]", title)
        if typ == "방문" and tag:
            sido, area = detect_region(tag.group(1).replace("전남광주", "전남"))
        elif typ == "배송":
            sido, area = "배송·전국", ""
        else:
            sido, area = "기타", ""
        name = re.sub(r"^\[[^\]]+\]\s*", "", title).strip() if typ == "방문" else title

        items.append({
            "id": f"as-{cid}",
            "site": SITE,
            "url": f"{BASE}/campaign.php?cp_id={cid}",
            "title": name or title,
            "offer": offer[:120],
            "media": detect_media(media_icons),
            "sido": sido,
            "area": area,
            "type": typ,
            "applied": to_int(m.group(1)),
            "recruit": to_int(m.group(2)),
            "deadline": parse_deadline(text, today),
            # 구매형은 직접 구매 후 스토어 리뷰까지 요구
            "extra_mission": typ_word == "구매형" or has_extra_mission(offer),
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
