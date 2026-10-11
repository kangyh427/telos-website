"""
새 글을 검색엔진에 바로 알리기 (S713 · 2026-10-08)

  ★한 가지 일만 한다: 주소 목록을 IndexNow 로 네이버(+ 빙 등 참여 검색엔진)에 알린다.★
  네이버 서치어드바이저는 2023년 7월부터 IndexNow 를 받는다. 구글은 참여하지 않는다(구글은 sitemap.xml).
  확인 키 파일 = 사이트 맨 위의 <키>.txt (키 자체는 비밀이 아니다 · 키 파일로 사이트 주인임을 보일 뿐이다).
  ★알림은 색인을 보장하지 않는다★ — 검색로봇이 빨리 오게 할 뿐이다.

  python _tools/blog/indexnow.py https://www.telos.it.kr/blog/a/ https://www.telos.it.kr/blog/
"""
from __future__ import annotations

import json
import os
import sys
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
HOST = "www.telos.it.kr"
ENDPOINTS = ["https://searchadvisor.naver.com/indexnow", "https://api.indexnow.org/indexnow"]


def notify(urls: list[str]) -> None:
    key = open(os.path.join(HERE, "indexnow_key.txt"), encoding="utf-8").read().strip()
    body = json.dumps({
        "host": HOST, "key": key, "keyLocation": f"https://{HOST}/{key}.txt", "urlList": urls,
    }).encode()
    for ep in ENDPOINTS:
        req = urllib.request.Request(ep, data=body, method="POST",
                                     headers={"Content-Type": "application/json; charset=utf-8"})
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                print(ep, r.status)
        except urllib.error.HTTPError as e:  # 알림 실패가 글 올리기를 막지 않는다
            print(ep, e.code, e.read()[:200])
        except Exception as e:
            print(ep, "실패", e)


if __name__ == "__main__":
    notify(sys.argv[1:])
