"""
블로그 그림 만들기 (S713 · 2026-10-08)

  ★한 가지 일만 한다: 영어 그림 설명 하나로 글머리 그림 한 장을 만들어 JPG 로 저장한다.★
  제미나이 그림 모델(REST) · 키 = 환경 변수 GEMINI_API_KEY(깃허브에서는 저장소 비밀값).
  ★그림체는 여기서 고정한다★ — 글마다 그림체가 달라지면 블로그가 어수선해 보인다.

  지킬 선
    · 실제 사람처럼 보이는 얼굴을 만들지 않는다(가상 인물 표시 문제 · 2026-06-01 심사지침).
      → 수채화풍 그림책 일러스트로 고정한다.
    · 그림 속 글자는 엉터리로 그려진다 → 글자·숫자·기호를 아예 넣지 말라고 적는다.
"""
from __future__ import annotations

import base64
import io
import json
import os
import urllib.request

from PIL import Image

MODEL = os.environ.get("BLOG_IMAGE_MODEL", "gemini-3.1-flash-image")
STYLE = (
    "Soft hand-painted watercolor picture-book illustration, warm natural daylight, gentle pastel palette "
    "with teal and cream accents, calm and hopeful mood, simple uncluttered composition, Korean everyday "
    "setting. People are drawn as simple stylized illustrated figures, seen from a distance or from behind, "
    "never photorealistic and never resembling any real person. ABSOLUTELY NO writing, letters, numbers, "
    "signs, labels, logos, symbols or watermarks anywhere in the image; any sign or board must be completely blank."
)
OUT_W, OUT_H = 1200, 675


def generate(prompt: str, out_path: str) -> str:
    key = os.environ.get("GEMINI_API_KEY", "").strip()
    if not key:
        raise RuntimeError("GEMINI_API_KEY 가 없다")
    body = {
        "contents": [{"parts": [{"text": f"{prompt.strip()}\n\nStyle: {STYLE}"}]}],
        "generationConfig": {"responseModalities": ["IMAGE", "TEXT"], "imageConfig": {"aspectRatio": "16:9"}},
    }
    req = urllib.request.Request(
        f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent",
        data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json", "x-goog-api-key": key},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=300) as resp:
        data = json.loads(resp.read())
    for cand in data.get("candidates", []):
        for p in cand.get("content", {}).get("parts", []):
            inline = p.get("inlineData") or p.get("inline_data")
            if inline:
                img = Image.open(io.BytesIO(base64.b64decode(inline["data"]))).convert("RGB")
                img = _cover(img, OUT_W, OUT_H)
                os.makedirs(os.path.dirname(out_path), exist_ok=True)
                img.save(out_path, "JPEG", quality=82, optimize=True, progressive=True)
                return out_path
    raise RuntimeError("그림이 오지 않았다: " + json.dumps(data, ensure_ascii=False)[:400])


def _cover(img: Image.Image, w: int, h: int) -> Image.Image:
    """비율을 지키며 가운데를 잘라 w×h 로 맞춘다."""
    scale = max(w / img.width, h / img.height)
    img = img.resize((round(img.width * scale), round(img.height * scale)), Image.LANCZOS)
    left, top = (img.width - w) // 2, (img.height - h) // 2
    return img.crop((left, top, left + w, top + h))


if __name__ == "__main__":
    import sys
    print(generate(sys.argv[1], sys.argv[2]))
