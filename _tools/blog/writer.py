"""
블로그 글 쓰기 (S713 · 2026-10-08)

  ★한 가지 일만 한다: 주제와 실제 자료 묶음을 받아 Claude 에게 글 한 편(JSON)을 받는다.★
  자료를 찾는 일(pubmed.py) · 검사(guard.py) · 그림(image_gen.py) · 사이트 만들기(build.py)는 하지 않는다.

  모델 = claude-opus-5-5 (환경 변수 BLOG_MODEL 로 바꿀 수 있다)
  키   = 환경 변수 ANTHROPIC_API_KEY (깃허브에서는 저장소 비밀값)
  거절 대비 = 서버 쪽 대체 모델(fallbacks "default") — 건강 글이라 드물지만, 거절되면 같은 요청을 다른 모델이 잇는다.
"""
from __future__ import annotations

import json
import os

import anthropic

MODEL = os.environ.get("BLOG_MODEL", "claude-opus-5-5")

# ★바뀌지 않는 앞부분★ — 매번 같은 글자라 캐시가 붙는다(날짜·주제는 뒤 메시지에만 넣는다).
SYSTEM = """당신은 한국의 걷기 건강 블로그 「걷기 건강 이야기」의 필자입니다.
읽는 사람은 혼자 사시는 부모님을 걱정하는 40~60대 자녀와, 스스로 건강을 챙기시는 어르신입니다.

[말투]
- 따뜻하고 쉬운 존댓말로 씁니다("~해요", "~이에요" 위주, 가끔 "~습니다"). 옆에서 차근차근 들려주듯 씁니다.
- 어려운 의학 용어는 처음 나올 때 쉬운 말로 풀어 줍니다.
- 어르신을 공경합니다. 나이 드신 분을 약하거나 우스운 존재로 그리지 않습니다.
- 줄표(—, –)를 쓰지 않습니다. 쉼표나 문장 나누기로 대신합니다.

[사실]
- 사실과 숫자는 아래에 번호로 주어진 자료에서만 가져옵니다. 자료에 없는 숫자, 연구, 책, 전문가 말은 절대 지어내지 않습니다.
- 자료의 내용을 쓴 문장 끝에는 [1], [2]처럼 자료 번호를 붙입니다. 서로 다른 자료를 2개 이상 인용합니다.
- 퍼센트, 몇 배, 몇 명, 몇 걸음 같은 숫자는 자료에 적힌 숫자를 그대로 씁니다. 반올림하거나 바꾸지 않습니다.
- 연구 결과는 「관련이 있었다」, 「위험이 낮게 나타났다」처럼 연구가 말한 만큼만 씁니다. 「예방된다」, 「치료된다」, 「막아 준다」 같은 단정은 쓰지 않습니다.
- 한 연구의 한계(관찰 연구라서 원인이라고 단정할 수 없다 등)가 자료에 있으면 쉬운 말로 짧게 밝혀 줍니다.

[하지 말 것]
- 어떤 앱, 제품, 회사, 서비스도 이름으로 언급하거나 권하지 않습니다. 글은 순수한 건강 정보입니다.
- 진단, 처방, 약에 대한 조언을 하지 않습니다.

[짜임]
- 본문은 마크다운으로 씁니다. 첫 문단은 공감되는 일상 장면으로 엽니다(2~3문장).
- 「## 」 소제목을 3~5개 둡니다. 마지막 소제목은 「오늘 해 볼 작은 걸음」처럼 바로 해 볼 수 있는 실천 3가지를 목록으로 줍니다. 실천은 안전하고 무리 없는 것으로 씁니다.
- 본문 길이는 공백과 기호를 뺀 글자 수로 1,800~3,000자입니다.
- 제목은 15~35자로, 노리는 검색어를 자연스럽게 담되 낚시성 문구는 쓰지 않습니다.
- 요약(description)은 60~120자로, 검색 결과에 보일 한두 문장입니다.
- slug 는 글 내용을 나타내는 영어 소문자 낱말 2~6개를 하이픈으로 이은 것입니다(예: daily-steps-and-health).
- keywords 는 사람들이 실제로 검색할 만한 한국어 검색어 5~8개입니다.
- image_prompt 는 글머리 그림을 위한 영어 장면 묘사 1~2문장입니다. 글자나 간판, 화면 속 숫자가 들어가는 장면은 피합니다.
- image_alt 는 그 그림을 한국어로 설명하는 한 문장입니다."""

SCHEMA = {
    "type": "object",
    "properties": {
        "title": {"type": "string"},
        "slug": {"type": "string"},
        "description": {"type": "string"},
        "keywords": {"type": "array", "items": {"type": "string"}},
        "body_markdown": {"type": "string"},
        "image_prompt": {"type": "string"},
        "image_alt": {"type": "string"},
    },
    "required": ["title", "slug", "description", "keywords", "body_markdown", "image_prompt", "image_alt"],
    "additionalProperties": False,
}


class Refused(RuntimeError):
    """모델이 끝까지 거절했다."""


def _sources_block(sources: list[dict]) -> str:
    lines = []
    for i, s in enumerate(sources, 1):
        head = f"[{i}] {s['title']}"
        if s.get("journal") or s.get("year"):
            head += f" ({s.get('journal', '')} {s.get('year', '')})".rstrip()
        if s.get("author"):
            head += f" / 지은이 {s['author']}"
        lines.append(f"{head}\n{s['text']}")
    return "\n\n".join(lines)


def write(topic: dict, sources: list[dict], previous_titles: list[str], feedback: list[str] | None = None) -> dict:
    """글 한 편을 dict 로 돌려준다. 검사는 부르는 쪽이 한다."""
    prev = "\n".join(f"- {t}" for t in previous_titles) or "(없음)"
    ask = (
        f"노리는 검색어: {topic['keyword']}\n"
        f"분류: {topic['category']}\n\n"
        f"이 주제로 이미 쓴 글 제목(겹치지 않는 새 각도로 쓰세요):\n{prev}\n\n"
        f"쓸 수 있는 자료(이 밖의 사실은 쓰지 마세요):\n\n{_sources_block(sources)}"
    )
    if feedback:
        ask += "\n\n지난번 원고는 아래 이유로 실을 수 없었습니다. 고쳐서 새로 써 주세요:\n" + "\n".join(f"- {f}" for f in feedback)

    client = anthropic.Anthropic()
    with client.messages.stream(
        model=MODEL,
        max_tokens=32000,
        system=[{"type": "text", "text": SYSTEM, "cache_control": {"type": "ephemeral"}}],
        messages=[{"role": "user", "content": ask}],
        output_config={"effort": "high", "format": {"type": "json_schema", "schema": SCHEMA}},
        extra_headers={"anthropic-beta": "server-side-fallback-2026-07-01"},
        extra_body={"fallbacks": "default"},
    ) as stream:
        msg = stream.get_final_message()

    if msg.stop_reason == "refusal":
        raise Refused(str(getattr(msg, "stop_details", "")))
    if msg.stop_reason == "max_tokens":
        raise RuntimeError("원고가 길이 한도에서 잘렸다")
    text = next(b.text for b in msg.content if b.type == "text")
    post = json.loads(text)
    post["_usage"] = {
        "model": msg.model,
        "input_tokens": msg.usage.input_tokens,
        "output_tokens": msg.usage.output_tokens,
        "cache_read_input_tokens": getattr(msg.usage, "cache_read_input_tokens", 0) or 0,
    }
    return post
