"""
블로그 사이트 만들기 (S713 · 2026-10-08)

  ★한 가지 일만 한다: blog/_src/*.json(원고) 전부로 블로그 페이지를 처음부터 다시 만든다.★
  같은 원고면 언제 돌려도 같은 결과다 — 손으로 고친 HTML 은 다음 빌드에 덮인다(원고를 고칠 것).

  만드는 것
    /blog/                       목록(1쪽) · /blog/page/N/  다음 쪽
    /blog/category/<분류>/        분류 모음(검색엔진이 글을 따라 들어오는 길)
    /blog/<slug>/                글
    /blog/feed.xml               RSS(네이버 서치어드바이저에 내는 것)
    /sitemap.xml                 사이트 전체 지도(구글·네이버에 내는 것)

  ★검색에 걸리게★ = 글마다 제목·요약·대표 주소(canonical)·공유 그림(og)·구조화 데이터(BlogPosting·
  BreadcrumbList)를 넣고, 목록·분류·관련 글·이전/다음 글로 모든 글을 서로 잇는다(고아 글이 없게).
"""
from __future__ import annotations

import datetime as dt
import email.utils
import glob
import html
import json
import os
import re
import shutil
import urllib.parse

import markdown

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
BLOG = os.path.join(ROOT, "blog")
SRC = os.path.join(BLOG, "_src")
SITE = "https://www.telos.it.kr"
BLOG_NAME = "걷기 건강 이야기"
BLOG_DESC = "어르신 건강과 걷기에 관한 연구와 책을 쉽게 풀어 쓴 이야기. 걷기, 뇌 건강, 마음 건강, 생활 습관까지 매일 새 글을 올립니다."
PER_PAGE = 12
PLAY_ID = "com.naoncare.guardian"
CATEGORIES = {
    "걷기 상식": "walking-basics",
    "뇌 건강": "brain",
    "마음 건강": "mind",
    "몸 건강": "body",
    "생활 습관": "habits",
    "책 이야기": "books",
}
RESERVED = {"page", "category", "images", "_src", "feed.xml"}
# ★사이트맵에 넣는 회사 페이지★ — 콘솔·인증·기관·연동 페이지는 넣지 않는다(검색에 보일 까닭이 없다).
STATIC_PAGES = ["/", "/privacy.html", "/terms.html", "/location-terms.html", "/notice.html", "/opensource.html"]
KST = dt.timezone(dt.timedelta(hours=9))

e = html.escape


def play_link(medium: str, campaign: str) -> str:
    ref = urllib.parse.quote(f"utm_source=telos_blog&utm_medium={medium}&utm_campaign={campaign}", safe="")
    return f"https://play.google.com/store/apps/details?id={PLAY_ID}&referrer={ref}"


def load() -> list[dict]:
    posts = [json.load(open(p, encoding="utf-8")) for p in glob.glob(os.path.join(SRC, "*.json"))]
    for p in posts:
        if p["slug"] in RESERVED:
            raise ValueError(f"쓸 수 없는 주소 이름: {p['slug']}")
        p["_dt"] = dt.datetime.fromisoformat(p["published"])
    posts.sort(key=lambda p: p["_dt"], reverse=True)
    return posts


def fmt_date(d: dt.datetime) -> str:
    return f"{d.year}년 {d.month}월 {d.day}일"


def reading_minutes(md: str) -> int:
    return max(2, round(len(re.sub(r"\s", "", md)) / 500))


# ── 공통 틀 ──────────────────────────────────────────────────────────────

# 방문 측정(2026-10-25 대표 결정 6 · 광고 없음): 구글 태그 관리자 컨테이너
GTM_HEAD = "<!-- Google Tag Manager -->\n<script>(function(w,d,s,l,i){w[l]=w[l]||[];w[l].push({'gtm.start':\nnew Date().getTime(),event:'gtm.js'});var f=d.getElementsByTagName(s)[0],\nj=d.createElement(s),dl=l!='dataLayer'?'&l='+l:'';j.async=true;j.src=\n'https://www.googletagmanager.com/gtm.js?id='+i+dl;f.parentNode.insertBefore(j,f);\n})(window,document,'script','dataLayer','GTM-5MKCW6RM');</script>\n<!-- End Google Tag Manager -->"

# 애널리틱스 측정 ID(2026-10-25 · 태그 관리자 안에는 GA 태그를 넣지 않는다 · 두 번 세지 않게)
GA4_HEAD = '<!-- Google tag (gtag.js) · 방문 통계만 · 광고 신호 끔(개인정보처리방침 제10조) -->\n<script async src="https://www.googletagmanager.com/gtag/js?id=G-RXELWTCRMJ"></script>\n<script>\n  window.dataLayer = window.dataLayer || [];\n  function gtag(){dataLayer.push(arguments);}\n  gtag(\'js\', new Date());\n  gtag(\'config\', \'G-RXELWTCRMJ\', {\'allow_google_signals\': false, \'allow_ad_personalization_signals\': false});\n</script>'

def head(title: str, desc: str, canonical: str, *, og_type="website", image=None, keywords=None,
         jsonld: list | None = None, prev_url=None, next_url=None, noindex=False) -> str:
    img = image or f"{SITE}/images/hero.jpg"
    out = [
        "<!DOCTYPE html>",
        '<html lang="ko">',
        "<head>",
        GTM_HEAD,
        GA4_HEAD,
        '<meta charset="UTF-8">',
        '<meta name="viewport" content="width=device-width, initial-scale=1.0">',
        f"<title>{e(title)}</title>",
        f'<meta name="description" content="{e(desc)}">',
    ]
    if keywords:
        out.append(f'<meta name="keywords" content="{e(", ".join(keywords))}">')
    out += [
        f'<link rel="canonical" href="{e(canonical)}">',
        f'<meta name="robots" content="{"noindex, follow" if noindex else "index, follow, max-image-preview:large"}">',
        f'<meta property="og:type" content="{og_type}">',
        f'<meta property="og:site_name" content="{BLOG_NAME} | 나이노트">',
        f'<meta property="og:title" content="{e(title)}">',
        f'<meta property="og:description" content="{e(desc)}">',
        f'<meta property="og:url" content="{e(canonical)}">',
        f'<meta property="og:image" content="{e(img)}">',
        '<meta property="og:locale" content="ko_KR">',
        '<meta name="twitter:card" content="summary_large_image">',
        f'<meta name="twitter:title" content="{e(title)}">',
        f'<meta name="twitter:description" content="{e(desc)}">',
        f'<meta name="twitter:image" content="{e(img)}">',
        f'<link rel="alternate" type="application/rss+xml" title="{BLOG_NAME}" href="{SITE}/blog/feed.xml">',
    ]
    if prev_url:
        out.append(f'<link rel="prev" href="{e(prev_url)}">')
    if next_url:
        out.append(f'<link rel="next" href="{e(next_url)}">')
    out += [
        '<link rel="preconnect" href="https://cdn.jsdelivr.net">',
        '<link rel="stylesheet" href="https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/variable/pretendardvariable-dynamic-subset.min.css">',
        '<link rel="stylesheet" href="/css/style.css?v=20261011">',
        '<link rel="stylesheet" href="/css/blog.css">',
        "<link rel=\"icon\" type=\"image/svg+xml\" href=\"data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><text y='.9em' font-size='90' font-weight='bold'>T</text></svg>\">",
    ]
    for block in jsonld or []:
        out.append('<script type="application/ld+json">' + json.dumps(block, ensure_ascii=False) + "</script>")
    out.append("</head>")
    return "\n".join(out)


HEADER = """<body class="blog-body">
<!-- Google Tag Manager (noscript) -->
<noscript><iframe src="https://www.googletagmanager.com/ns.html?id=GTM-5MKCW6RM"
height="0" width="0" style="display:none;visibility:hidden"></iframe></noscript>
<!-- End Google Tag Manager (noscript) -->
<header class="header scrolled" id="header">
    <div class="header-inner">
        <a href="/" class="logo" aria-label="나이노트 홈">
            <img src="/images/logo.png" alt="주식회사 텔로스 TELOS" class="logo-img" width="213" height="46">
        </a>
        <nav class="nav" id="nav" aria-label="주요 메뉴">
            <ul class="nav-list">
                <li><a href="/#solution">서비스 소개</a></li>
                <li><a href="/blog/" aria-current="page">걷기 이야기</a></li>
                <li><a href="/#audience">대상·도입 안내</a></li>
                <li><a href="/#faq">FAQ</a></li>
                <li><a href="/#company">회사 소개</a></li>
            </ul>
        </nav>
        <a class="btn btn-primary btn-sm header-cta" href="/#contact">문의하기</a>
        <button class="nav-toggle" id="navToggle" aria-label="메뉴 열기" aria-expanded="false">
            <span></span><span></span><span></span>
        </button>
    </div>
</header>"""

FOOTER = """<footer class="footer">
    <div class="container">
        <div class="footer-inner">
            <div class="footer-main">
                <div class="footer-brand">
                    <img src="/images/logo_white.png" alt="주식회사 텔로스 TELOS" class="footer-logo-img" width="170" height="37">
                    <p class="footer-company">주식회사 텔로스 / TELOS Co., Ltd.</p>
                    <p class="footer-bizinfo">
                        대표 강윤혁 · 사업자등록번호 555-81-03578<br>
                        세종특별자치시 마음안1로 139<br>
                        전화 0507-1393-5864 · 전자우편 contact@telos.it.kr
                    </p>
                </div>
                <div class="footer-links-wrap">
                    <nav class="footer-links" aria-label="법적 고지">
                        <a href="/privacy.html">개인정보처리방침</a>
                        <span class="footer-contact-divider">·</span>
                        <a href="/terms.html">이용약관</a>
                        <span class="footer-contact-divider">·</span>
                        <a href="/blog/">걷기 건강 이야기</a>
                        <span class="footer-contact-divider">·</span>
                        <a href="mailto:contact@telos.it.kr">문의하기</a>
                    </nav>
                </div>
            </div>
            <div class="footer-bottom">
                <p class="footer-copyright">&copy; 2026 TELOS Co., Ltd. All rights reserved.</p>
            </div>
        </div>
    </div>
</footer>
<script src="/js/main.js" defer></script>
</body>
</html>"""

ORG = {
    "@type": "Organization",
    "name": "주식회사 텔로스",
    "url": SITE + "/",
    "logo": {"@type": "ImageObject", "url": SITE + "/images/logo.png"},
}


def write(path_rel: str, content: str) -> None:
    path = os.path.join(ROOT, path_rel.lstrip("/"))
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(content)


def category_nav(active: str | None) -> str:
    items = [f'<a href="/blog/" class="chip{" active" if active is None else ""}">전체</a>']
    for name, slug in CATEGORIES.items():
        cls = "chip active" if active == name else "chip"
        items.append(f'<a href="/blog/category/{slug}/" class="{cls}">{e(name)}</a>')
    return '<nav class="blog-cats" aria-label="분류">' + "".join(items) + "</nav>"


def card(p: dict) -> str:
    return (
        f'<article class="post-card"><a href="/blog/{p["slug"]}/">'
        f'<img src="/blog/{p["image"]}" alt="{e(p["image_alt"])}" loading="lazy" width="1200" height="675">'
        f'<div class="post-card-body"><span class="post-cat">{e(p["category"])}</span>'
        f'<h2>{e(p["title"])}</h2><p>{e(p["description"])}</p>'
        f'<time datetime="{p["_dt"].date().isoformat()}">{fmt_date(p["_dt"])}</time></div></a></article>'
    )


# ── 목록·분류 ────────────────────────────────────────────────────────────

def build_lists(posts: list[dict], base: str, title: str, desc: str, active_cat: str | None) -> list[str]:
    """base = '/blog/' 또는 '/blog/category/x/'. 만든 주소 목록을 돌려준다."""
    pages = max(1, -(-len(posts) // PER_PAGE))
    urls = []
    for n in range(1, pages + 1):
        chunk = posts[(n - 1) * PER_PAGE: n * PER_PAGE]
        url = base if n == 1 else f"{base}page/{n}/"
        prev_url = None if n == 1 else (SITE + (base if n == 2 else f"{base}page/{n - 1}/"))
        next_url = SITE + f"{base}page/{n + 1}/" if n < pages else None
        page_title = title if n == 1 else f"{title} ({n}쪽)"
        crumbs = [{"@type": "ListItem", "position": 1, "name": "홈", "item": SITE + "/"},
                  {"@type": "ListItem", "position": 2, "name": BLOG_NAME, "item": SITE + "/blog/"}]
        if active_cat:
            crumbs.append({"@type": "ListItem", "position": 3, "name": active_cat, "item": SITE + base})
        ld = [
            {"@context": "https://schema.org", "@type": "Blog", "name": BLOG_NAME, "url": SITE + "/blog/",
             "description": BLOG_DESC, "inLanguage": "ko-KR", "publisher": ORG},
            {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": crumbs},
        ]
        pager = []
        if prev_url:
            pager.append(f'<a href="{prev_url.replace(SITE, "")}" rel="prev">← 최근 글</a>')
        pager.append(f"<span>{n} / {pages}</span>")
        if next_url:
            pager.append(f'<a href="{next_url.replace(SITE, "")}" rel="next">지난 글 →</a>')
        body = (
            head(f"{page_title} | 나이노트", desc, SITE + url, jsonld=ld, prev_url=prev_url, next_url=next_url)
            + "\n" + HEADER.replace("{play}", play_link("blog_header", "list"))
            + f'\n<main class="blog-main"><div class="container">'
            f'<header class="blog-hero"><p class="blog-kicker">나이노트 블로그</p><h1>{e(title)}</h1><p>{e(desc)}</p></header>'
            + category_nav(active_cat)
            + ('<div class="post-grid">' + "".join(card(p) for p in chunk) + "</div>" if chunk
               else '<p class="blog-empty">곧 첫 글이 올라옵니다.</p>')
            + f'<nav class="pager" aria-label="쪽 넘기기">{"".join(pager)}</nav>'
            + "</div></main>\n" + FOOTER
        )
        write(url + "index.html", body)
        urls.append(url)
    return urls


# ── 글 ──────────────────────────────────────────────────────────────────

def render_body(md: str) -> str:
    h = markdown.markdown(md, extensions=["extra", "sane_lists"])
    h = re.sub(r"\[(\d+)\]", r'<sup class="cite"><a href="#ref-\1">[\1]</a></sup>', h)
    return h


def build_post(p: dict, posts: list[dict], idx: int) -> None:
    url = f"/blog/{p['slug']}/"
    img_abs = f"{SITE}/blog/{p['image']}"
    cited = sorted({int(x) for x in re.findall(r"\[(\d+)\]", p["body_markdown"])})
    refs = []
    for n in cited:
        s = p["sources"][n - 1]
        bits = [e(s["title"])]
        if s.get("author"):
            bits.append(e(s["author"]))
        if s.get("journal"):
            bits.append(f"<i>{e(s['journal'])}</i>")
        if s.get("publisher"):
            bits.append(e(s["publisher"]))
        if s.get("year"):
            bits.append(e(str(s["year"])))
        line = ", ".join(bits)
        if s.get("url"):
            line = f'<a href="{e(s["url"])}" rel="noopener nofollow" target="_blank">{line}</a>'
        refs.append(f'<li id="ref-{n}" value="{n}">{line}</li>')

    same = [q for q in posts if q is not p and q["category"] == p["category"]][:3]
    if len(same) < 3:
        same += [q for q in posts if q is not p and q not in same][: 3 - len(same)]
    newer = posts[idx - 1] if idx > 0 else None
    older = posts[idx + 1] if idx + 1 < len(posts) else None

    ld = [
        {"@context": "https://schema.org", "@type": "BlogPosting",
         "headline": p["title"], "description": p["description"], "image": [img_abs],
         "datePublished": p["published"], "dateModified": p.get("modified", p["published"]),
         "inLanguage": "ko-KR", "keywords": ", ".join(p["keywords"]), "articleSection": p["category"],
         "author": ORG, "publisher": ORG, "mainEntityOfPage": SITE + url,
         "citation": [s["url"] for s in (p["sources"][n - 1] for n in cited) if s.get("url")]},
        {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "홈", "item": SITE + "/"},
            {"@type": "ListItem", "position": 2, "name": BLOG_NAME, "item": SITE + "/blog/"},
            {"@type": "ListItem", "position": 3, "name": p["category"],
             "item": f"{SITE}/blog/category/{CATEGORIES[p['category']]}/"},
            {"@type": "ListItem", "position": 4, "name": p["title"], "item": SITE + url}]},
    ]
    nav = []
    if newer:
        nav.append(f'<a class="next" href="/blog/{newer["slug"]}/"><span>다음 글</span>{e(newer["title"])}</a>')
    if older:
        nav.append(f'<a class="prev" href="/blog/{older["slug"]}/"><span>이전 글</span>{e(older["title"])}</a>')

    body = (
        head(f"{p['title']} | {BLOG_NAME}", p["description"], SITE + url, og_type="article",
             image=img_abs, keywords=p["keywords"], jsonld=ld)
        + "\n" + HEADER.replace("{play}", play_link("blog_header", p["slug"]))
        + '\n<main class="blog-main"><div class="container post-wrap">'
        + f'<nav class="crumbs" aria-label="현재 위치"><a href="/blog/">{BLOG_NAME}</a> › '
          f'<a href="/blog/category/{CATEGORIES[p["category"]]}/">{e(p["category"])}</a></nav>'
        + '<article class="post">'
        + f'<header class="post-head"><h1>{e(p["title"])}</h1>'
          f'<p class="post-meta"><time datetime="{p["published"]}">{fmt_date(p["_dt"])}</time>'
          f' · 읽는 데 {reading_minutes(p["body_markdown"])}분</p></header>'
        + f'<figure class="post-figure"><img src="/blog/{p["image"]}" alt="{e(p["image_alt"])}" width="1200" height="675"></figure>'
        + f'<div class="post-body">{render_body(p["body_markdown"])}</div>'
        + f'<section class="post-refs" aria-label="참고한 자료"><h2>참고한 자료</h2><ol>{"".join(refs)}</ol></section>'
        + '<aside class="post-note">이 글은 걷기와 건강에 관한 연구와 책을 쉽게 풀어 쓴 건강 정보입니다. '
          "개인의 진료나 처방을 대신하지 않습니다. 운동을 새로 시작하시거나 늘리실 때는 몸 상태에 맞게 의료진과 상의해 주세요.</aside>"
        + '<aside class="post-app"><div><p class="post-app-title">부모님의 오늘 걸음, 자녀 폰에서 함께 보세요</p>'
          '<p>나이노트는 부모님이 걸으신 기록을 자녀가 함께 보는 앱입니다. 산책을 시작하고 마치시면 알림이 옵니다.</p></div>'
          f'<a class="btn btn-primary" href="{play_link("blog_post", p["slug"])}" rel="noopener">나이노트 받기</a></aside>'
        + "</article>"
        + (f'<nav class="post-nav" aria-label="이전·다음 글">{"".join(nav)}</nav>' if nav else "")
        + ('<section class="post-related"><h2>함께 읽으면 좋은 글</h2><div class="post-grid">'
           + "".join(card(q) for q in same) + "</div></section>" if same else "")
        + "</div></main>\n" + FOOTER
    )
    write(url + "index.html", body)


# ── RSS·사이트맵 ─────────────────────────────────────────────────────────

def build_feed(posts: list[dict]) -> None:
    items = []
    for p in posts[:50]:
        link = f"{SITE}/blog/{p['slug']}/"
        items.append(
            "<item>"
            f"<title>{e(p['title'])}</title><link>{link}</link><guid isPermaLink=\"true\">{link}</guid>"
            f"<pubDate>{email.utils.format_datetime(p['_dt'])}</pubDate>"
            f"<category>{e(p['category'])}</category>"
            f"<description>{e(p['description'])}</description>"
            "</item>"
        )
    now = email.utils.format_datetime(posts[0]["_dt"] if posts else dt.datetime.now(KST))
    xml = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom"><channel>'
        f"<title>{BLOG_NAME} | 나이노트</title><link>{SITE}/blog/</link>"
        f"<description>{e(BLOG_DESC)}</description><language>ko</language>"
        f"<lastBuildDate>{now}</lastBuildDate>"
        f'<atom:link href="{SITE}/blog/feed.xml" rel="self" type="application/rss+xml"/>'
        + "".join(items) + "</channel></rss>\n"
    )
    write("/blog/feed.xml", xml)


def build_sitemap(posts: list[dict], list_urls: list[str]) -> None:
    rows = [f"<url><loc>{SITE}{u}</loc></url>" for u in STATIC_PAGES]
    latest = posts[0]["_dt"].date().isoformat() if posts else None
    for u in list_urls:
        rows.append(f"<url><loc>{SITE}{u}</loc>" + (f"<lastmod>{latest}</lastmod>" if latest else "") + "</url>")
    for p in posts:
        mod = dt.datetime.fromisoformat(p.get("modified", p["published"])).date().isoformat()
        rows.append(f"<url><loc>{SITE}/blog/{p['slug']}/</loc><lastmod>{mod}</lastmod></url>")
    xml = ('<?xml version="1.0" encoding="UTF-8"?>\n'
           '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + "\n".join(rows) + "\n</urlset>\n")
    write("/sitemap.xml", xml)


# ── 전체 ────────────────────────────────────────────────────────────────

def clean_generated() -> None:
    """지난 빌드가 만든 페이지를 지운다(원고·그림·_로 시작하는 것은 남긴다)."""
    for name in os.listdir(BLOG):
        path = os.path.join(BLOG, name)
        if name.startswith("_") or name == "images":
            continue
        if os.path.isdir(path):
            shutil.rmtree(path)
        elif name in ("index.html", "feed.xml"):
            os.remove(path)


def build_site() -> None:
    posts = load()
    os.makedirs(BLOG, exist_ok=True)
    clean_generated()
    list_urls = build_lists(posts, "/blog/", BLOG_NAME, BLOG_DESC, None)
    for name, slug in CATEGORIES.items():
        sub = [p for p in posts if p["category"] == name]
        if sub:
            list_urls += build_lists(sub, f"/blog/category/{slug}/", f"{name} | {BLOG_NAME}",
                                     f"{BLOG_NAME}의 「{name}」 글 모음. {BLOG_DESC}", name)
    for i, p in enumerate(posts):
        build_post(p, posts, i)
    build_feed(posts)
    build_sitemap(posts, list_urls)
    print(f"블로그 빌드: 글 {len(posts)}편 · 목록·분류 {len(list_urls)}쪽 · sitemap.xml · feed.xml")


if __name__ == "__main__":
    build_site()
