"""공통: HTTP 요청(robots.txt 준수·지연), 매체/지역/마감일 정규화."""
import re
import time
import urllib.robotparser
from datetime import date, timedelta
from urllib.parse import urlparse

import requests

UA = "review-finder/1.0 (+https://github.com/ssw3200-ops/review-finder)"
DELAY_SEC = 2.0
_robots = {}
_last_request = 0.0
session = requests.Session()
session.headers.update({"User-Agent": UA, "Accept-Language": "ko-KR,ko;q=0.9"})


def allowed(url):
    """robots.txt에서 허용된 URL인지 확인. robots를 못 읽으면 수집하지 않는다."""
    p = urlparse(url)
    base = f"{p.scheme}://{p.netloc}"
    if base not in _robots:
        rp = urllib.robotparser.RobotFileParser()
        try:
            r = session.get(base + "/robots.txt", timeout=15)
            if r.status_code >= 400 and r.status_code != 404:
                rp = None
            else:
                rp.parse(r.text.splitlines() if r.status_code == 200 else [])
        except requests.RequestException:
            rp = None
        _robots[base] = rp
    rp = _robots[base]
    return bool(rp) and rp.can_fetch(UA, url)


def fetch(url):
    """robots 허용 + 요청 간 지연을 지켜서 HTML을 가져온다. 실패 시 None."""
    global _last_request
    if not allowed(url):
        print(f"  [skip robots] {url}")
        return None
    wait = DELAY_SEC - (time.time() - _last_request)
    if wait > 0:
        time.sleep(wait)
    _last_request = time.time()
    try:
        r = session.get(url, timeout=20)
        r.raise_for_status()
        r.encoding = r.apparent_encoding or "utf-8"
        return r.text
    except requests.RequestException as e:
        print(f"  [error] {url}: {e}")
        return None


# ---------- 매체 ----------
MEDIA_LABELS = {"blog": "블로그", "insta": "인스타", "reels": "릴스", "clip": "클립", "youtube": "유튜브"}


def detect_media(text, default="blog"):
    t = text or ""
    low = t.lower()
    if "릴스" in t or "reels" in low or "reel" in low:
        return "reels"
    if "클립" in t or "clip" in low:
        return "clip"
    if "쇼츠" in t or "유튜브" in t or "youtube" in low or "shorts" in low:
        return "youtube"
    if "인스타" in t or "insta" in low:
        return "insta"
    return default


# 리뷰 1개 외에 추가로 요구하는 미션(영수증·스토어 리뷰 등)
EXTRA_MISSION = re.compile(r"영수증\s*리뷰|스토어\s*리뷰|예약\s*리뷰|구매\s*평|플레이스\s*리뷰|\+\s*(블로그|릴스|클립|인스타)|2개|2건")


def has_extra_mission(text):
    return bool(EXTRA_MISSION.search(text or ""))


# ---------- 지역 ----------
SIDO = ["서울", "경기", "인천", "강원", "대전", "세종", "충북", "충남", "광주", "전북", "전남",
        "대구", "경북", "경남", "부산", "울산", "제주"]
SIDO_ALIAS = {
    "충청북도": "충북", "충청남도": "충남", "전라북도": "전북", "전북특별자치도": "전북", "전라남도": "전남",
    "경상북도": "경북", "경상남도": "경남", "강원도": "강원", "강원특별자치도": "강원", "제주도": "제주",
    "세종시": "세종", "서울시": "서울",
}
# 시/군/구·주요 동네 → 시/도 (지역명이 시/도 없이 오는 경우 대비)
CITY_TO_SIDO = {
    "서울": "강남 서초 송파 강동 강서 마포 영등포 구로 관악 동작 용산 성동 광진 중랑 노원 도봉 강북 성북 "
            "종로 은평 서대문 양천 금천 동대문 홍대 홍대입구 신촌 이태원 압구정 청담 잠실 건대 성수 "
            "광화문 을지로 신림 여의도 문래 망원 합정 연남 삼성역 삼성동 강남역 역삼 선릉 논현 신사 "
            "안국 익선동 종로3가 성신여대 마곡 목동 노량진 사당 왕십리 혜화 명동 압구정로데오",
    "경기": "수원 성남 분당 판교 용인 수지 기흥 고양 일산 부천 안양 평촌 범계 안산 화성 동탄 평택 "
            "의정부 시흥 파주 김포 광명 광주시 군포 하남 오산 이천 양주 구리 안성 포천 의왕 여주 "
            "동두천 과천 가평 양평 연천 미금 정자 위례 다산 별내",
    "인천": "부평 송도 청라 계양 연수 남동 미추홀 서구청라 검단 영종 중산동",
    "강원": "춘천 원주 강릉 속초 동해 삼척 태백 홍천 평창 양양 정선",
    "대전": "유성 둔산 대덕 신성동 관평동 도안 노은 은행동 만년동",
    "세종": "조치원 나성동 보람동 고운동 도담동 어진동",
    "충북": "청주 충주 제천 오창 오송 음성 진천",
    "충남": "천안 아산 서산 당진 공주 논산 보령 홍성 계룡",
    "광주": "상무지구 수완 첨단 충장로 월계동",
    "전북": "전주 군산 익산 정읍 남원 김제 완주 수송동",
    "전남": "여수 순천 목포 광양 나주 무안 해룡",
    "대구": "수성 동성로 달서 건들바위",
    "경북": "포항 구미 경주 안동 김천 경산 영주",
    "경남": "창원 김해 진주 양산 거제 통영 마산 진해",
    "부산": "해운대 서면 광안리 기장 남포 센텀 동래 사상 연산",
    "울산": "울주 삼산",
    "제주": "서귀포 애월 이도이동 노형 연동",
}
_CITY_INDEX = sorted(((c, s) for s, cs in CITY_TO_SIDO.items() for c in cs.split()), key=lambda x: -len(x[0]))


def detect_region(text):
    """'[서울 송파]', '대전 신성동', '강남구 삼성동' 등에서 (시도, 상세) 추출."""
    t = (text or "").strip()
    if "배송" in t or "전국" in t:
        return "배송·전국", ""
    for full, short in SIDO_ALIAS.items():
        t = t.replace(full, short)
    for s in SIDO:
        if t.startswith(s):
            return s, t[len(s):].strip()
    for s in SIDO:
        if re.search(rf"(^|\s|\[){s}(\s|\]|$)", t):
            return s, t
    for city, s in _CITY_INDEX:
        if city in t:
            return s, t
    return "기타", t


# ---------- 마감 ----------
def parse_deadline(text, today=None):
    """'6일 남음', 'D-3', 'D-Day', '오늘 마감' → ISO 날짜 문자열."""
    today = today or date.today()
    t = text or ""
    m = re.search(r"(\d+)\s*일\s*남", t) or re.search(r"D\s*-\s*(\d+)", t)
    if m:
        return (today + timedelta(days=int(m.group(1)))).isoformat()
    if re.search(r"D\s*-\s*Day|오늘\s*마감", t, re.I):
        return today.isoformat()
    if re.search(r"하루\s*전|내일\s*마감", t):
        return (today + timedelta(days=1)).isoformat()
    return None


def to_int(s):
    m = re.search(r"\d[\d,]*", s or "")
    return int(m.group().replace(",", "")) if m else None
