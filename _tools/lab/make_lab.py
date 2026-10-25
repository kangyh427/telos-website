"""
실험 장치 · 아이디어 소개 한 장 만들기 (2026-10-25 · 텔로스 본부 신사업 실험실장)

  ★한 가지 일만 한다: _tools/lab/specs/<slug>.json(아이디어 설명) 하나로 /lab/<slug>/ 소개 한 장을 만든다.★
  「먼저 알림 받기」 단추를 누르면 방문 측정(애널리틱스)에 lab_interest 이벤트가 남고, 화면에는
  「아직 준비 중」이라고 바로 알린다. 결제를 받지 않고 개인정보를 모으지 않는다(가짜 문 실험 · 정직하게).

  쓰는 법
    python _tools/lab/make_lab.py <slug>            /lab/<slug>/index.html 을 만든다
    python _tools/lab/make_lab.py <slug> --out DIR   다른 폴더에 만든다(시험용 · 게시하지 않음)

  지키는 것(본부 스킬 lab-experiment)
    - 검색에 걸리지 않게 noindex · 사이트맵에 넣지 않는다(실험이 끝나면 접는다).
    - 가격은 「예정」으로만 · 효능 과장 · 「보장」 금지 · 크레스트류는 유사투자자문 고지.
    - 유입 경로는 utm 으로 가른다(블로그 · 카페 · 광고).
"""
from __future__ import annotations

import html
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "_tools", "blog"))
import build as blog  # noqa: E402  머리 · 위 띠 · 아래 띠(측정 코드 포함)를 블로그와 같이 쓴다

e = html.escape
REQUIRED = ["slug", "title", "desc", "headline", "problem", "offer", "cta", "thanks"]

STYLE = """<style>
.lab{max-width:760px;margin:0 auto;padding:120px 20px 64px;line-height:1.75}
.lab .eyebrow{font-size:14px;font-weight:600;color:#1b937c;margin:0 0 8px}
.lab h1{font-size:30px;line-height:1.35;margin:0 0 16px}
.lab .lead{font-size:18px;color:#3a4a55;margin:0 0 28px}
.lab h2{font-size:20px;margin:32px 0 10px}
.lab ul{padding-left:20px;margin:0}
.lab li{margin:6px 0}
.lab .price{margin:24px 0 0;padding:14px 16px;border-radius:10px;background:#f3f6f6;font-size:15px}
.lab .cta{margin:32px 0 0;display:grid;gap:10px;justify-items:start}
.lab .cta button{font:inherit;font-size:18px;font-weight:700;padding:14px 26px;border-radius:12px;border:0;background:#1b937c;color:#fff;cursor:pointer}
.lab .thanks{display:none;padding:16px 18px;border-radius:12px;background:#e1f3ee;font-size:16px}
.lab .thanks.show{display:block}
.lab .note{font-size:13px;color:#5b6c77;margin-top:28px}
</style>"""


def load(slug: str) -> dict:
    path = os.path.join(HERE, "specs", slug + ".json")
    with open(path, encoding="utf-8") as f:
        spec = json.load(f)
    missing = [k for k in REQUIRED if not spec.get(k)]
    if missing:
        raise SystemExit(f"설명 파일에 빠진 칸: {missing}")
    if spec["slug"] != slug:
        raise SystemExit("파일 이름과 slug 가 다르다")
    return spec


def render(spec: dict) -> str:
    slug = spec["slug"]
    url = f"{blog.SITE}/lab/{slug}/"
    lis = lambda xs: "\n".join(f"<li>{e(x)}</li>" for x in xs)  # noqa: E731
    price = f'<p class="price"><b>예정 가격</b> · {e(spec["price_note"])} (아직 판매하지 않습니다)</p>' if spec.get("price_note") else ""
    extra = f'<p class="note">{e(spec["legal_note"])}</p>' if spec.get("legal_note") else ""
    body = f"""
<main class="lab">
  <p class="eyebrow">{e(spec.get("eyebrow", "주식회사 텔로스 · 준비 중인 서비스"))}</p>
  <h1>{e(spec["headline"])}</h1>
  <p class="lead">{e(spec["desc"])}</p>
  <h2>{e(spec.get("problem_title", "이런 일로 힘드시죠"))}</h2>
  <ul>{lis(spec["problem"])}</ul>
  <h2>{e(spec.get("offer_title", "이렇게 도와 드리려고 합니다"))}</h2>
  <ul>{lis(spec["offer"])}</ul>
  {price}
  <div class="cta">
    <button type="button" id="lab-cta">{e(spec["cta"])}</button>
    <div class="thanks" id="lab-thanks" role="status">{e(spec["thanks"])}</div>
  </div>
  <p class="note">이 페이지는 아직 준비 중인 서비스에 대해 관심이 있는 분이 얼마나 되는지 알아보는 안내입니다. 결제를 받지 않으며, 단추를 눌러도 이름 · 연락처 같은 개인정보를 모으지 않습니다(방문 통계만 · 개인정보처리방침 제10조). 의견은 <a href="mailto:contact@telos.it.kr?subject={e(slug)}">contact@telos.it.kr</a> 로 보내 주세요.</p>
  {extra}
</main>
<script>
(function(){{
  var b=document.getElementById('lab-cta'), t=document.getElementById('lab-thanks'), sent=false;
  b.addEventListener('click',function(){{
    if(!sent && typeof gtag==='function'){{ gtag('event','lab_interest',{{lab_id:{json.dumps(slug)}}}); }}
    sent=true; t.classList.add('show'); b.disabled=true;
  }});
}})();
</script>"""
    return "\n".join([
        blog.head(spec["title"], spec["desc"], url, noindex=True),
        STYLE,
        blog.HEADER,
        body,
        blog.FOOTER,
    ])


def main(argv: list[str]) -> None:
    if not argv:
        raise SystemExit(__doc__)
    slug = argv[0]
    out_dir = argv[argv.index("--out") + 1] if "--out" in argv else os.path.join(ROOT, "lab", slug)
    page = render(load(slug))
    os.makedirs(out_dir, exist_ok=True)
    with open(os.path.join(out_dir, "index.html"), "w", encoding="utf-8", newline="\n") as f:
        f.write(page)
    print("만듦:", os.path.join(out_dir, "index.html"))


if __name__ == "__main__":
    main(sys.argv[1:])
