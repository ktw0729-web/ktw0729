#!/usr/bin/env python3
"""Google News RSS를 서버(GitHub Actions)에서 받아 news/news.json으로 저장.
브라우저는 같은 사이트의 JSON만 읽으므로 외부 중계(프록시) 없이 동작한다."""
import json, html, os, sys, urllib.request, urllib.parse
import xml.etree.ElementTree as ET
from datetime import datetime, timezone, timedelta
from email.utils import parsedate_to_datetime

CATS = {
    "속보": "https://news.google.com/rss/search?q=" + urllib.parse.quote("속보 when:6h") + "&hl=ko&gl=KR&ceid=KR:ko",
    "종합": "https://news.google.com/rss?hl=ko&gl=KR&ceid=KR:ko",
    "경제": "https://news.google.com/rss/search?q=" + urllib.parse.quote("경제") + "&hl=ko&gl=KR&ceid=KR:ko",
    "IT": "https://news.google.com/rss/search?q=" + urllib.parse.quote("IT 기술") + "&hl=ko&gl=KR&ceid=KR:ko",
    "스포츠": "https://news.google.com/rss/search?q=" + urllib.parse.quote("스포츠") + "&hl=ko&gl=KR&ceid=KR:ko",
}

def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read()

def parse(xml_bytes, limit=10):
    root = ET.fromstring(xml_bytes)
    out = []
    for it in root.iter("item"):
        raw = (it.findtext("title") or "").strip()
        parts = raw.split(" - ")
        src = parts.pop() if len(parts) > 1 else (it.findtext("source") or "Google 뉴스")
        head = " - ".join(parts) if parts else raw
        pub = it.findtext("pubDate") or ""
        try:
            pub = parsedate_to_datetime(pub).astimezone(timezone.utc).isoformat()
        except Exception:
            pub = ""
        out.append({"h": html.escape(head), "src": html.escape(src),
                    "link": (it.findtext("link") or "").strip(), "pub": pub})
        if len(out) >= limit:
            break
    return out

def main():
    cats, failed = {}, []
    for name, url in CATS.items():
        try:
            items = parse(fetch(url))
            if not items:
                raise ValueError("empty")
            cats[name] = items
            print(f"[ok] {name}: {len(items)}건")
        except Exception as e:
            failed.append(name)
            print(f"[실패] {name}: {e}", file=sys.stderr)
    if not cats:
        sys.exit("모든 카테고리 수집 실패")
    kst = datetime.now(timezone(timedelta(hours=9))).strftime("%Y-%m-%d %H:%M KST")
    os.makedirs("news", exist_ok=True)
    with open("news/news.json", "w", encoding="utf-8") as f:
        json.dump({"updated": kst, "cats": cats}, f, ensure_ascii=False, indent=1)
    if failed:
        print("일부 실패:", ", ".join(failed), file=sys.stderr)

if __name__ == "__main__":
    main()
