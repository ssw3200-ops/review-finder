# 체험단 모아보기 (review-finder)

여러 체험단 사이트의 **공개 목록**을 하루 3번 모아서, 매체(블로그·인스타·릴스·클립)와 지역으로 거르고
**경쟁률(신청자 ÷ 모집인원) 낮은 순**으로 보여주는 모바일용 정적 페이지입니다. 서버·API 키·비용 없음.

- 페이지: `docs/index.html` (GitHub Pages, `/docs` 폴더 배포)
- 데이터: `docs/data/campaigns.json` (GitHub Actions가 자동 갱신)
- 수집기: `crawler/` (Python, requests + BeautifulSoup)

## 수집 대상

| 사이트 | 상태 | 비고 |
|---|---|---|
| 디너의여왕 | 수집 | robots.txt 허용, 릴스·클립·지역·배송·기자단 목록 |
| 미블 | 수집 | robots.txt 허용, 지역·배송·인스타그램·마감순 목록 |
| 레뷰 | 제외 | 로그인해야 목록이 보임 |
| 리뷰노트, 체험뷰, 리뷰플레이스, 포블로그 | 제외 | robots.txt가 캠페인 경로 수집을 막음 |

원칙: robots.txt를 지키고(못 읽으면 수집 안 함), 요청 사이 2초 간격, 제목·지역·신청자 수·마감·원문 링크만 저장하고
이미지·상세 본문은 가져오지 않습니다. 신청은 원 사이트에서 합니다.

## 배포

1. GitHub에 `review-finder` 저장소를 만들고 이 폴더를 push
2. Settings → Pages → Source: `Deploy from a branch`, Branch `main` / 폴더 `/docs`
3. Settings → Actions → General → Workflow permissions: **Read and write** 선택
4. Actions 탭 → `체험단 수집` → **Run workflow** 로 첫 수집 실행 (이후 매일 06·12·18시 자동)

## 로컬 실행

```bash
pip install -r requirements.txt
python -m crawler.crawl          # docs/data/campaigns.json 생성
python -m pytest -q tests        # 파서 테스트
cd docs && python -m http.server # http://localhost:8000
```

## 사이트 추가하기

`crawler/sites/새사이트.py`에 `SITE` 이름과 `crawl()`(아래 필드를 가진 dict 목록 반환)을 만들고
`crawler/crawl.py`의 `SITES`에 등록합니다. 추가 전 robots.txt와 이용약관을 꼭 확인하세요.

`id, site, url, title, offer, media(blog|insta|reels|clip|youtube), sido, area, type(방문|배송|기자단), applied, recruit, deadline(YYYY-MM-DD), extra_mission(bool)`
