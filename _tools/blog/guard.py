"""
블로그 글 검사기 (S713 · 2026-10-08)

  ★한 가지 일만 한다: 글 한 편이 올라가도 되는지 판정한다.★
  에이전트가 쓴 글도, 사람이 쓴 글도 같은 문을 지난다(python guard.py <글.json>).

  왜 이 문이 필요한가
    · 건강 글이다. 지어낸 숫자 하나가 회사 신뢰를 통째로 무너뜨린다.
      → 퍼센트·배·명·걸음 수는 ★출처 본문에 그 숫자가 있어야만★ 통과한다.
    · 회사 홈페이지다. 글이 앱의 효능을 말하면 의료기기 오인·과장 광고가 된다.
      → 본문에는 앱 이름을 쓰지 않는다(앱 안내는 틀이 고정 문장으로 붙인다).
    · 「—」(대시)는 AI 문체로 읽힌다(대표 지시 2026-10-03).
"""
from __future__ import annotations

import json
import re
import sys

TITLE_LEN = (10, 40)
DESC_LEN = (50, 130)
BODY_LEN = (1500, 4000)
MIN_SECTIONS = 3
MIN_CITED = 2
SLUG_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+){1,7}$")

# ★앱·회사가 본문에 나오면 안 된다★ — 일반 건강 정보와 제품을 섞지 않는다.
BANNED_WORDS = ["나이노트", "텔로스", "이 앱", "저희 앱", "우리 앱", "본 앱"]

# ★단정·효능 표현★ — 연구는 「관련이 있다」까지만 말한다.
BANNED_PATTERNS = [
    (r"—|–", "대시(—, –)를 쓰지 않는다"),
    (r"완치", "「완치」 금지"),
    (r"진단(합니다|해 ?드|할 수)", "진단한다는 표현 금지"),
    (r"치료(합니다|됩니다|해 ?줍|효과가 있)", "치료 효과 단정 금지"),
    (r"예방(합니다|됩니다|해 ?줍|할 수 있습니다|할 수 있어요|이 됩니다)", "예방 단정 금지(「위험이 낮았다」처럼 연구 결과로 말한다)"),
    (r"막아 ?(줍|준다|드립)", "막아 준다는 단정 금지"),
    (r"(반드시|무조건|확실히) ?(좋아|낫|건강해|예방)", "단정 금지"),
    (r"보장(합니다|됩니다)", "보장 표현 금지"),
]

# ★출처에 있어야만 하는 숫자★ — 조언("10분씩 나눠 걸어도 좋습니다")은 막지 않고,
#   연구 결과처럼 읽히는 숫자만 본다.
CLAIM_NUMBER_RE = re.compile(r"(\d[\d,]*(?:\.\d+)?)\s*(%|퍼센트|배|명)")
STEP_NUMBER_RE = re.compile(r"(\d[\d,]*)\s*(?:보|걸음)")


def _norm_num(s: str) -> str:
    s = s.replace(",", "")
    if "." in s:
        s = s.rstrip("0").rstrip(".")
    return s


def _numbers_in(text: str) -> set[str]:
    # ★논문 표기를 우리 표기로 맞춘다★ — 「47 471」(얇은 띄어쓰기 천 단위) · 「0·60」(가운뎃점 소수점)
    text = re.sub(r"(?<=\d)[ -   ](?=\d{3}\b)", "", text)
    text = re.sub(r"(?<=\d)·(?=\d)", ".", text)
    return {_norm_num(m) for m in re.findall(r"\d[\d,]*(?:\.\d+)?", text)}


def _plain_len(md: str) -> int:
    t = re.sub(r"\[\d+\]", "", md)
    t = re.sub(r"[#*_>`\-\s]", "", t)
    return len(t)


def check(post: dict, sources: list[dict], existing_slugs: set[str] | None = None) -> list[str]:
    """문제 목록을 돌려준다. ★빈 목록이면 통과★."""
    errs: list[str] = []
    title = post.get("title", "")
    desc = post.get("description", "")
    body = post.get("body_markdown", "")
    slug = post.get("slug", "")

    if not (TITLE_LEN[0] <= len(title) <= TITLE_LEN[1]):
        errs.append(f"제목 길이 {len(title)}자(허용 {TITLE_LEN[0]}~{TITLE_LEN[1]})")
    if not (DESC_LEN[0] <= len(desc) <= DESC_LEN[1]):
        errs.append(f"요약 길이 {len(desc)}자(허용 {DESC_LEN[0]}~{DESC_LEN[1]})")
    n = _plain_len(body)
    if not (BODY_LEN[0] <= n <= BODY_LEN[1]):
        errs.append(f"본문 길이 {n}자(허용 {BODY_LEN[0]}~{BODY_LEN[1]})")
    if len(re.findall(r"(?m)^## ", body)) < MIN_SECTIONS:
        errs.append(f"소제목(## )이 {MIN_SECTIONS}개보다 적다")
    if not SLUG_RE.match(slug):
        errs.append(f"주소 이름(slug) 형식이 틀렸다: {slug!r}")
    if existing_slugs and slug in existing_slugs:
        errs.append(f"이미 있는 주소 이름이다: {slug}")

    whole = "\n".join([title, desc, body, post.get("image_alt", "")])
    for w in BANNED_WORDS:
        if w in whole:
            errs.append(f"본문에 앱·회사 이름 「{w}」(앱 안내는 틀이 붙인다)")
    for pat, why in BANNED_PATTERNS:
        m = re.search(pat, whole)
        if m:
            errs.append(f"{why}: 「{m.group(0)}」")

    # 출처 번호
    cited = sorted({int(x) for x in re.findall(r"\[(\d+)\]", body)})
    if len(cited) < MIN_CITED:
        errs.append(f"출처를 {MIN_CITED}개 이상 인용해야 한다(지금 {len(cited)}개)")
    bad = [c for c in cited if c < 1 or c > len(sources)]
    if bad:
        errs.append(f"없는 출처 번호: {bad}")

    # ★출처에 없는 숫자★
    source_text = " ".join((s.get("title", "") + " " + s.get("text", "")) for s in sources)
    have = _numbers_in(source_text)
    for m in CLAIM_NUMBER_RE.finditer(body):
        if _norm_num(m.group(1)) not in have:
            errs.append(f"출처에 없는 숫자: 「{m.group(0)}」")
    for m in STEP_NUMBER_RE.finditer(body):
        v = _norm_num(m.group(1))
        if int(v) >= 1000 and v not in have:
            errs.append(f"출처에 없는 걸음 수: 「{m.group(0)}」")
    return errs


def main() -> int:
    path = sys.argv[1]
    post = json.load(open(path, encoding="utf-8"))
    errs = check(post, post.get("sources", []))
    if errs:
        print("불통과:")
        for e in errs:
            print(" -", e)
        return 1
    print("통과")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
