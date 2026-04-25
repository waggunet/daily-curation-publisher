#!/usr/bin/env python3
"""
fetch_rss.py — RSS/Atom 피드 수집 + 24시간 필터링 + 제목 한글화
"""
import json
import sys
import re
import feedparser
from datetime import datetime, timedelta, timezone
from pathlib import Path

KST = timezone(timedelta(hours=9))
CUTOFF_HOURS = 24

SKILL_DIR = Path(__file__).parent.parent
CONFIG_FILE = SKILL_DIR / "config" / "sources.json"
OUTPUT_FILE = SKILL_DIR / "data" / "raw_articles.json"

def load_sources():
    with open(CONFIG_FILE, encoding="utf-8") as f:
        data = json.load(f)
    return data.get("sources", []), data.get("settings", {})

def parse_age(age_str: str) -> datetime:
    """'N시간전', 'N분전', 'N일전' 등을 datetime으로 변환"""
    now = datetime.now(KST)
    m = re.search(r"(\d+)\s*시간전", age_str)
    if m:
        return now - timedelta(hours=int(m.group(1)))
    m = re.search(r"(\d+)\s*분전", age_str)
    if m:
        return now - timedelta(minutes=int(m.group(1)))
    m = re.search(r"(\d+)\s*일전", age_str)
    if m:
        return now - timedelta(days=int(m.group(1)))
    return now

def translate_title(text: str, src="en", dest="ko") -> str:
    """MyMemory API로 제목 번역 (fallback: 원문 반환)"""
    try:
        import urllib.request, urllib.parse
        url = f"https://api.mymemory.translated.net/get?q={urllib.parse.quote(text)}&langpair={src}|{dest}"
        with urllib.request.urlopen(url, timeout=10) as resp:
            result = json.loads(resp.read())
            translated = result["responseData"]["translatedText"]
            if translated and translated != text:
                return translated
    except Exception:
        pass
    return text

def parse_rss_entry(entry) -> dict:
    """RSS/Atom entry → 표준 dict"""
    title = entry.get("title", "")
    link = entry.get("link") or ""
    if isinstance(link, list):
        link = link[0] if link else ""
    
    # published 파싱
    pub_str = ""
    if hasattr(entry, "published_parsed") and entry.published_parsed:
        pub_str = entry.get("published", "")
    elif hasattr(entry, "updated_parsed") and entry.updated_parsed:
        pub_str = entry.get("updated", "")
    else:
        pub_str = entry.get("published") or entry.get("updated") or ""
    
    pub_date = None
    if pub_str:
        try:
            if hasattr(entry, "published_parsed") and entry.published_parsed:
                from time import mktime
                pub_date = datetime.fromtimestamp(mktime(entry.published_parsed), tz=KST)
            elif hasattr(entry, "updated_parsed") and entry.updated_parsed:
                from time import mktime
                pub_date = datetime.fromtimestamp(mktime(entry.updated_parsed), tz=KST)
        except Exception:
            pass
    
    if not pub_date:
        pub_date = datetime.now(KST)
    
    description = ""
    if hasattr(entry, "summary"):
        description = entry.summary
    elif hasattr(entry, "description"):
        description = entry.description
    # HTML 태그 제거
    description = re.sub(r"<[^>]+>", "", description).strip()[:300]
    
    return {
        "title": title.strip(),
        "link": link,
        "published": pub_date.isoformat(),
        "description": description,
    }

def is_within_24h(published_str: str) -> bool:
    """게시일이 24시간 이내인지 확인"""
    try:
        pub = datetime.fromisoformat(published_str.replace("Z", "+00:00"))
        now = datetime.now(KST)
        # published가 KST가 아닌 경우 KST로 가정
        if pub.tzinfo is None:
            pub = pub.replace(tzinfo=KST)
        diff = now - pub
        return diff.total_seconds() <= CUTOFF_HOURS * 3600
    except Exception:
        return True  # 파싱 실패 시 포함

def fetch_feed(source: dict) -> list:
    """단일 피드 수집 + 필터링"""
    url = source["url"]
    scrape_type = source.get("scrape_type", "rss")
    max_articles = source.get("max_articles", 10)
    
    try:
        if scrape_type in ("rss", "atom"):
            feed = feedparser.parse(url)
            entries = feed.entries[:max_articles]
        else:
            print(f"  ⚠️ unsupported type: {scrape_type}")
            return []
    except Exception as e:
        print(f"  ❌ fetch 실패: {url} → {e}")
        return []
    
    articles = []
    for entry in entries:
        article = parse_rss_entry(entry)
        if is_within_24h(article["published"]):
            article["source"] = source["name"]
            article["category"] = source.get("category", "general")
            article["lang"] = source.get("lang", "ko")
            # 번역 필요 시 제목 한글화
            if source.get("translate", False):
                article["title_original"] = article["title"]
                article["title"] = translate_title(article["title"])
                article["translated"] = True
            articles.append(article)
    
    print(f"  ✅ {source['name']}: {len(articles)}건 (24시간 내)")
    return articles

def main():
    sources, settings = load_sources()
    all_articles = []
    
    for source in sources:
        print(f"📡 {source['name']}: {source['url']}")
        articles = fetch_feed(source)
        all_articles.extend(articles)
    
    # published 기준 내림차순 정렬
    all_articles.sort(key=lambda x: x["published"], reverse=True)
    
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump({
            "fetched_at": datetime.now(KST).isoformat(),
            "cutoff_hours": CUTOFF_HOURS,
            "total_articles": len(all_articles),
            "articles": all_articles
        }, f, ensure_ascii=False, indent=2)
    
    print(f"\n📦 총 {len(all_articles)}건 수집 완료 → {OUTPUT_FILE}")

if __name__ == "__main__":
    main()