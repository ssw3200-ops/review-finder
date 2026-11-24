from datetime import date
from pathlib import Path

from crawler.common import detect_region
from crawler.sites import dinnerqueen, mrblog

FX = Path(__file__).parent / "fixtures"
TODAY = date(2026, 11, 24)


def test_dinnerqueen():
    items = {i["id"]: i for i in dinnerqueen.parse((FX / "dinnerqueen.html").read_text(), TODAY)}
    assert set(items) == {"dq-1663398", "dq-1664298", "dq-1660479"}  # 배너 제외
    a = items["dq-1663398"]
    assert (a["media"], a["sido"], a["area"], a["applied"], a["recruit"]) == ("reels", "서울", "송파", 28, 2)
    assert a["title"] == "쿠우쿠우 송파점" and a["deadline"] == "2026-11-30" and a["offer"] == "2인 식사권"
    b = items["dq-1664298"]
    assert (b["media"], b["sido"], b["recruit"]) == ("blog", "대전", 5)
    assert items["dq-1660479"]["type"] == "배송" and items["dq-1660479"]["sido"] == "배송·전국"


def test_mrblog():
    items = {i["id"]: i for i in mrblog.parse((FX / "mrblog.html").read_text(), TODAY)}
    assert len(items) == 4
    r = items["mb-1153938"]
    assert (r["media"], r["sido"], r["applied"], r["recruit"], r["extra_mission"]) == ("reels", "서울", 0, 5, True)
    assert r["deadline"] == "2026-11-24" and r["title"] == "오태호킹크랩"
    c = items["mb-1153513"]
    assert (c["media"], c["sido"], c["extra_mission"]) == ("clip", "대전", False)
    d = items["mb-1154740"]
    assert d["type"] == "배송" and d["extra_mission"] is True
    p = items["mb-1153527"]
    assert (p["sido"], p["deadline"]) == ("경기", "2026-11-27")


def test_region():
    assert detect_region("강남구 삼성동")[0] == "서울"
    assert detect_region("충청남도 천안")[0] == "충남"
    assert detect_region("세종 고운동")[0] == "세종"
    assert detect_region("어딘가")[0] == "기타"


def test_gangnam():
    from crawler.sites import gangnam
    items = {i["id"]: i for i in gangnam.parse((FX / "gangnam.html").read_text(), TODAY)}
    assert set(items) == {"gm-2363907", "gm-2345893", "gm-2365068", "gm-2370001"}  # 리뷰 영역 링크 제외
    a = items["gm-2363907"]
    assert (a["media"], a["sido"], a["area"], a["type"], a["applied"], a["recruit"], a["deadline"]) == \
        ("blog", "충북", "음성", "방문", 8, 5, "2026-11-24")
    assert a["title"] == "유장춘닭개장 금왕점" and a["offer"] == "닭개장 OR 닭곰탕 택 2 체험권"
    b = items["gm-2345893"]
    assert (b["type"], b["sido"], b["applied"], b["deadline"]) == ("배송", "배송·전국", 6282, "2026-11-30")
    c = items["gm-2365068"]
    assert (c["type"], c["deadline"], c["title"]) == ("기자단", "2026-11-25", "종달 돌담 피자")
    d = items["gm-2370001"]
    assert (d["media"], d["sido"]) == ("reels", "세종")


def test_cometoplay():
    from crawler.sites import cometoplay
    items = {i["id"]: i for i in cometoplay.parse((FX / "cometoplay.html").read_text(), TODAY)}
    assert set(items) == {"np-1794446199", "np-1795486401", "np-1794874169", "np-1795137029"}
    a = items["np-1794446199"]
    assert (a["title"], a["sido"], a["area"], a["type"], a["applied"], a["recruit"], a["deadline"]) == \
        ("마이보쌈", "서울", "노원", "방문", 20, 10, "2026-11-24")
    assert items["np-1795486401"]["deadline"] == "2026-12-02" and items["np-1795486401"]["sido"] == "경남"
    assert items["np-1794874169"]["type"] == "배송" and items["np-1795137029"]["type"] == "기자단"


def test_assaview():
    from crawler.sites import assaview
    items = {i["id"]: i for i in assaview.parse((FX / "assaview.html").read_text(), TODAY)}
    assert set(items) == {"as-1793850681571", "as-1795138979098", "as-1794981284772", "as-1794724725328"}  # 오픈예정 제외
    a = items["as-1793850681571"]
    assert (a["title"], a["media"], a["sido"], a["area"], a["applied"], a["recruit"], a["deadline"]) == \
        ("인량훠궈", "blog", "서울", "강남구", 166, 20, "2026-12-02")
    assert a["offer"] == "강남 신사논현 고급훠궈 레스토랑 이용권"
    b = items["as-1795138979098"]
    assert (b["media"], b["type"], b["sido"], b["extra_mission"]) == ("insta", "배송", "배송·전국", False)
    c = items["as-1794981284772"]
    assert (c["media"], c["extra_mission"]) == ("blog", True)
    d = items["as-1794724725328"]
    assert (d["media"], d["sido"], d["deadline"]) == ("reels", "전남", "2026-11-24")
