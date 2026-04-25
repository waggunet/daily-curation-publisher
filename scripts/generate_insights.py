#!/usr/bin/env python3
"""
generate_insights.py — 자체 분석 + 서브에이전트 병행
- 먼저 자체 heuristic 인사이트 생성
- deploy.sh 실행 시 --spawn-mode이면 sessions_spawn(tool)을 직접 호출
"""
import json, sys, os, subprocess, re
from pathlib import Path
from datetime import datetime, timezone, timedelta

KST = timezone(timedelta(hours=9))

SKILL_DIR = Path(__file__).parent.parent
INPUT_FILE = SKILL_DIR / "data" / "raw_articles.json"
OUTPUT_FILE = SKILL_DIR / "data" / "insights_report.json"

def load_articles():
    with open(INPUT_FILE, encoding="utf-8") as f:
        return json.load(f)

def generate_insights(articles, fetched_at):
    """ 자체 인사이트 생성 — fallback when sub-agent unavailable """
    
    # 기사를 source별, 제목 키워드로 분석
    sources = {}
    keywords = []
    for a in articles:
        src = a.get("source", "?")
        if src not in sources:
            sources[src] = []
        sources[src].append(a)
        # 키워드 추출 (영어 제목에서)
        title = a.get("title", "")
        if not a.get("lang") == "ko":
            keywords.append(title.split()[0] if title else "")
    
    trend_templates = [
        ("AI 에이전트 및 Toolchain 확장", "high", ["Claude Code", "Browser Use", "Google Agents", "GStack", "Agent-to-Agent"]),
        ("멀티모달 음성 AI 상용화", "high", ["음성 모델", "Grok Voice", "저지연", "음성 AI"]),
        ("AI 기업간 투자/협력 구조 변화", "high", ["Google", "Anthropic", "DeepSeek", "투자", "59조"]),
        ("오픈소스 고성능화趋势", "medium", ["Go", "TypeScript 7", "GoScrapy", "네이티브 포팅"]),
        ("AI 검색 크롤러 시대의 SEO 변화", "medium", ["AI 크롤러", "검색 가시성", "SEO", "Perplexity"]),
    ]
    
    trends = []
    insights = []
    action_items = []
    
    # 키워드 매칭
    all_titles = " ".join([a.get("title","") for a in articles])
    
    for (title, impact, keywords) in trend_templates:
        matched = [kw for kw in keywords if kw.lower() in all_titles.lower()]
        if matched:
            desc = f"관련 기사 {len(matched)}건 확인: {', '.join(matched[:3])}"
            sources_list = [a["title"] for a in articles if any(kw in a["title"] for kw in matched)][:3]
            trends.append({
                "title": title,
                "description": desc,
                "sources": sources_list,
                "impact": impact
            })
            action_items.append({
                "title": f"[{title}] 관련 동향 체크",
                "description": f"매칭 키워드: {', '.join(matched[:2])}. 더 자세한 분석이 필요하면 서브에이전트 상세 조사를 고려.",
                "priority": impact,
                "trend_ref": title,
                "effort": "30min"
            })
    
    if not trends:
        # fallback: 간단한 요약
        top_source = list(sources.keys())[0] if sources else "Unknown"
        trends.append({
            "title": "기술 뉴스 동향",
            "description": f"총 {len(articles)}건의 기사가 수집됨 ({', '.join(sources.keys())})",
            "sources": [a["title"] for a in articles[:3]],
            "impact": "medium"
        })
    
    summary = f"{len(articles)}건의 기술 기사를 수집했습니다. "
    if sources:
        summary += f"({', '.join(sources.keys())} 등 소스). "
    if trends:
        summary += f"주요 트렌드로 {trends[0]['title']} 등이 확인됩니다."
    
    return {
        "summary": summary,
        "trends": trends,
        "insights": insights,
        "action_items": action_items,
        "business_impact": {
            "opportunities": [],
            "threats": [],
            "recommendations": []
        },
        "generated_at": datetime.now(KST).isoformat(),
        "article_count": len(articles),
        "note": "자체 heuristic 생성 — 서브에이전트 상세 분석 필요 시 SKILL.md 참고"
    }

def main():
    data = load_articles()
    articles = data.get("articles", [])
    fetched_at = data.get("fetched_at", datetime.now(KST).isoformat())
    print(f"📰 {len(articles)}건 기사 로드 완료")

    # 자체 인사이트 생성
    print("🤖 인사이트 생성 중...")
    result = generate_insights(articles, fetched_at)
    
    # 서브에이전트 시도 (spawn mode일 때만)
    spawn_mode = os.environ.get("SPAWN_SUBAGENT", "false").lower() == "true"
    if spawn_mode:
        print("🤖 서브에이전트 spawn 시도...")
        try:
            task = f"아래 기사를 분석해서 insights를 생성해줘.\n\n파일 경로: {OUTPUT_FILE}"
            res = subprocess.run([
                sys.executable, "-m", "openclaw", "sessions", "spawn",
                "--mode=run",
                f"--task={task}"
            ], capture_output=True, text=True, timeout=60)
            print("spawn 결과:", res.stdout[:200])
        except Exception as e:
            print(f"spawn 실패 (fallback 유지): {e}")

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ 인사이트 생성 완료")
    print(f"📊 트렌드 {len(result.get('trends', []))}건")
    print(f"🎯 액션아이템 {len(result.get('action_items', []))}건")
    print(f"📁 저장: {OUTPUT_FILE}")

if __name__ == "__main__":
    main()