"""
블로그 자동 글쓰기 에이전트 (S713 · 2026-10-08 · 대표 지시 「하루 2개씩 · 수백 편 · 네이버·구글 검색」)

  ★한 번 부르면 글 한 편을 끝까지 올릴 준비를 한다★
    ① 주제 고르기   — 글이 가장 적은 주제부터(주제 목록 topics.json)
    ② 자료 찾기     — PubMed 실제 논문(같은 주제의 다음 글은 다음 논문) + WHO 지침(+ 책 분류면 확인된 책)
    ③ 글 쓰기       — Claude (writer.py)
    ④ 검사          — guard.py · 떨어지면 이유를 붙여 한 번 더 쓰게 하고, 또 떨어지면 ★싣지 않는다★
    ⑤ 그림          — 제미나이 (image_gen.py) · 실패하면 기본 그림
    ⑥ 저장·사이트   — blog/_src/<날짜>-<slug>.json → build.py 가 페이지·목록·사이트맵·RSS 를 다시 만든다
  깃 커밋·푸시는 하지 않는다(깃허브 작업 흐름 .github/workflows/blog-autopost.yml 이 한다).

  쓰는 법
    python _tools/blog/write_post.py                 # 글 한 편
    python _tools/blog/write_post.py --topic sleep   # 주제를 정해서
    python _tools/blog/write_post.py --dry-run       # 고른 주제와 자료만 보여 준다(돈 안 듦)
    python _tools/blog/write_post.py --from-json 원고.json   # 사람이 쓴 원고를 같은 문으로 올린다
"""
from __future__ import annotations

import argparse
import datetime as dt
import glob
import json
import os
import re
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
SRC_DIR = os.path.join(ROOT, "blog", "_src")
IMG_DIR = os.path.join(ROOT, "blog", "images")
DEFAULT_IMG = os.path.join(IMG_DIR, "_default.jpg")
KST = dt.timezone(dt.timedelta(hours=9))
PAPERS_PER_POST = 6

sys.path.insert(0, HERE)
import build  # noqa: E402
import guard  # noqa: E402
import pubmed  # noqa: E402


def load_posts() -> list[dict]:
    posts = []
    for p in sorted(glob.glob(os.path.join(SRC_DIR, "*.json"))):
        posts.append(json.load(open(p, encoding="utf-8")))
    return posts


def pick_topic(topics: list[dict], posts: list[dict], wanted: str | None) -> dict:
    if wanted:
        return next(t for t in topics if t["id"] == wanted)
    count = {t["id"]: 0 for t in topics}
    for p in posts:
        if p.get("topic") in count:
            count[p["topic"]] += 1
    # ★가장 적게 쓴 주제부터★ — 같으면 목록 순서(목록 앞쪽이 대표가 먼저 노리는 검색어)
    return min(topics, key=lambda t: (count[t["id"]], topics.index(t)))


def gather_sources(topic: dict, posts: list[dict]) -> list[dict]:
    done = sum(1 for p in posts if p.get("topic") == topic["id"])
    used = {s.get("pmid") for p in posts for s in p.get("sources", []) if s.get("pmid")}
    papers: list[dict] = []
    # ★같은 주제의 다음 글은 다음 논문★ — 앞 글이 쓴 논문은 빼고, 모자라면 거름을 풀어 더 찾는다.
    for strict in (True, False):
        skip = done * 3
        for _ in range(4):
            got = pubmed.search(topic["pubmed"], n=PAPERS_PER_POST, skip=skip, strict=strict)
            if not got:
                break
            for g in got:
                if g["pmid"] not in used and all(g["pmid"] != x["pmid"] for x in papers):
                    papers.append(g)
            if len(papers) >= 4:
                break
            skip += PAPERS_PER_POST
        if len(papers) >= 3:
            break
    refs = json.load(open(os.path.join(HERE, "references.json"), encoding="utf-8"))
    extra = [{"kind": "guideline", **g} for g in refs["guidelines"]]
    if topic["category"] == "책 이야기":
        extra += [{"kind": "book", "title": f"『{b['title']}』", "author": b["author"],
                   "text": b["gist"], "url": ""} for b in refs["books"]]
    return papers[:PAPERS_PER_POST] + extra


def too_similar(title: str, posts: list[dict]) -> str | None:
    """★비슷한 제목 거르기★ — 낱말이 70% 넘게 겹치면 같은 글로 본다."""
    words = set(re.findall(r"[가-힣A-Za-z0-9]{2,}", title))
    for p in posts:
        other = set(re.findall(r"[가-힣A-Za-z0-9]{2,}", p["title"]))
        if words and other and len(words & other) / min(len(words), len(other)) > 0.7:
            return p["title"]
    return None


def publish(post: dict, topic: dict, sources: list[dict], posts: list[dict], now: dt.datetime) -> str:
    import image_gen  # 그림 키가 없을 때 --dry-run 이 막히지 않게 여기서 부른다

    slug = post["slug"]
    img_rel = f"images/{slug}.jpg"
    img_abs = os.path.join(ROOT, "blog", img_rel)
    try:
        image_gen.generate(post["image_prompt"], img_abs)
    except Exception as e:  # 그림이 실패해도 글은 올린다
        print("그림 실패(기본 그림을 쓴다):", e)
        shutil.copyfile(DEFAULT_IMG, img_abs)
    record = {
        "title": post["title"],
        "slug": slug,
        "description": post["description"],
        "keywords": post["keywords"],
        "category": topic["category"],
        "topic": topic["id"],
        "published": now.isoformat(timespec="seconds"),
        "image": img_rel,
        "image_alt": post["image_alt"],
        "image_prompt": post["image_prompt"],
        "body_markdown": post["body_markdown"],
        "sources": sources,
        "usage": post.get("_usage"),
    }
    os.makedirs(SRC_DIR, exist_ok=True)
    path = os.path.join(SRC_DIR, f"{now:%Y-%m-%d-%H%M}-{slug}.json")
    json.dump(record, open(path, "w", encoding="utf-8", newline="\n"), ensure_ascii=False, indent=1)
    return path


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--topic")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--from-json")
    args = ap.parse_args()

    topics = json.load(open(os.path.join(HERE, "topics.json"), encoding="utf-8"))["topics"]
    posts = load_posts()
    slugs = {p["slug"] for p in posts}
    now = dt.datetime.now(KST)

    if args.from_json:
        draft = json.load(open(args.from_json, encoding="utf-8"))
        topic = next(t for t in topics if t["id"] == draft["topic"])
        sources = draft["sources"]
    else:
        topic = pick_topic(topics, posts, args.topic)
        sources = gather_sources(topic, posts)
        print(f"주제: {topic['id']} ({topic['keyword']}) · 자료 {len(sources)}개")
        for i, s in enumerate(sources, 1):
            print(f"  [{i}] {s.get('year', '')} {s['title'][:80]}")
        if sum(1 for s in sources if s["kind"] == "paper") < 2:
            print("논문이 모자라 이번에는 쓰지 않는다")
            return 2
        if args.dry_run:
            return 0
        import writer
        prev = [p["title"] for p in posts if p.get("topic") == topic["id"]]
        draft, feedback = None, None
        for attempt in (1, 2):
            cand = writer.write(topic, sources, prev, feedback)
            errs = guard.check(cand, sources, slugs)
            dup = too_similar(cand["title"], posts)
            if dup:
                errs.append(f"이미 비슷한 제목이 있다: {dup}")
            if not errs:
                draft = cand
                break
            print(f"{attempt}번째 원고 불통과:", *errs, sep="\n - ")
            feedback = errs
        if draft is None:
            print("두 번 다 검사를 못 넘어 이번에는 싣지 않는다")
            return 3

    errs = guard.check(draft, sources, slugs)
    if errs:
        print("불통과:", *errs, sep="\n - ")
        return 3
    path = publish(draft, topic, sources, posts, now)
    print("저장:", os.path.relpath(path, ROOT))
    build.build_site()
    # ★새 주소를 작업 흐름에 넘긴다★ — 배포가 끝나면 IndexNow 로 검색엔진에 알린다.
    cat = build.CATEGORIES[topic["category"]]
    urls = [f"{build.SITE}/blog/{draft['slug']}/", f"{build.SITE}/blog/", f"{build.SITE}/blog/category/{cat}/"]
    print("새 주소:", urls[0])
    out = os.environ.get("GITHUB_OUTPUT")
    if out:
        with open(out, "a", encoding="utf-8") as f:
            f.write(f"urls={' '.join(urls)}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
