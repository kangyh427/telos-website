"""
PubMed 논문 가져오기 (S713 · 2026-10-08)

  ★한 가지 일만 한다: 검색식으로 실제 논문의 서지와 초록을 가져온다.★
  글이 인용할 수 있는 것은 ★여기서 가져온 것뿐★ 이다(지어낸 논문 방지).
  미국 국립의학도서관 공개 API(E-utilities) · 키 없이 초당 3회까지.
"""
from __future__ import annotations

import json
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

BASE = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"
TOOL = "telos-blog"
EMAIL = "contact@telos.it.kr"
# ★요약 논문(리뷰·메타분석)과 무작위 시험을 먼저 찾는다★ — 한 연구보다 근거가 단단하다.
FILTER = '(review[pt] OR meta-analysis[pt] OR randomized controlled trial[pt]) AND hasabstract AND english[la]'


def _get(endpoint: str, params: dict) -> bytes:
    params = {**params, "tool": TOOL, "email": EMAIL}
    url = BASE + endpoint + "?" + urllib.parse.urlencode(params)
    for attempt in range(3):
        try:
            with urllib.request.urlopen(url, timeout=30) as r:
                body = r.read()
            time.sleep(0.4)  # 초당 3회 제한을 지킨다
            return body
        except Exception:
            if attempt == 2:
                raise
            time.sleep(2 * (attempt + 1))
    raise RuntimeError("unreachable")


def search(query: str, n: int = 6, skip: int = 0, years: int = 15, strict: bool = True) -> list[dict]:
    """
    검색식에 맞는 논문 n편. skip 만큼 건너뛰어 같은 주제의 다음 글은 다른 논문을 쓰게 한다.
    돌려주는 칸 = pmid, title, journal, year, url, text(초록).
    strict=False 면 논문 종류 거름을 풀고 초록 있는 영어 논문 전체에서 찾는다(결과가 모자랄 때).
    """
    kinds = FILTER if strict else "hasabstract AND english[la]"
    term = f"({query}) AND {kinds} AND (\"last {years} years\"[dp])"
    ids = json.loads(_get("esearch.fcgi", {
        "db": "pubmed", "term": term, "retmax": n, "retstart": skip,
        "sort": "relevance", "retmode": "json",
    }))["esearchresult"]["idlist"]
    if not ids:
        return []
    root = ET.fromstring(_get("efetch.fcgi", {"db": "pubmed", "id": ",".join(ids), "retmode": "xml"}))
    out = []
    for art in root.iter("PubmedArticle"):
        pmid = art.findtext(".//PMID") or ""
        title = "".join(art.find(".//ArticleTitle").itertext()).strip() if art.find(".//ArticleTitle") is not None else ""
        journal = art.findtext(".//Journal/Title") or ""
        year = art.findtext(".//JournalIssue/PubDate/Year") or (art.findtext(".//JournalIssue/PubDate/MedlineDate") or "")[:4]
        parts = []
        for ab in art.iter("AbstractText"):
            label = ab.get("Label")
            txt = "".join(ab.itertext()).strip()
            if txt:
                parts.append(f"{label}: {txt}" if label else txt)
        text = " ".join(parts)
        if pmid and title and text:
            out.append({
                "kind": "paper", "pmid": pmid, "title": title, "journal": journal, "year": year,
                "url": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/", "text": text,
            })
    return out


if __name__ == "__main__":
    import sys
    for p in search(sys.argv[1], n=int(sys.argv[2]) if len(sys.argv) > 2 else 5):
        print(p["pmid"], p["year"], p["journal"], "|", p["title"][:90], "| 초록", len(p["text"]), "자")
