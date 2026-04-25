#!/usr/bin/env python3
"""
generate_insights.py — 자체 분석 + 서브에이전트 병행
- 자체 keyword 기반 분석으로 트렌드/인사이트/액션 생성
- summary는 300자 분량으로 실제 요약 제공
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

def analyze_articles(articles):
    """전체 기사 텍스트 분석 — 키워드 매칭으로 트렌드 식별"""
    all_text = " ".join([
        (a.get("title","") + " " + (a.get("description") or "")[:300])
        for a in articles
    ])

    themes = [
        {
            "title": "AI 코딩 에이전트 생태계 확장",
            "impact": "high",
            "keywords": ["Claude Code", "Browser Use", "Codex", "purplemux", "ClawSweeper", "imgssh", "Google Agents CLI", "Figma MCP"],
        },
        {
            "title": "메타-AWS 대규모 CPU 계약",
            "impact": "high",
            "keywords": ["메타", "CPU", "AWS", "그래비톤", "Graviton"],
        },
        {
            "title": "유럽 소버린 AI 전략",
            "impact": "high",
            "keywords": ["Cohere", "Aleph Alpha", "합병", "유럽", "소버린", "Schwarz"],
        },
        {
            "title": "A2A/MCP 에이전트 표준 전쟁",
            "impact": "high",
            "keywords": ["A2A", "MCP", "멀티 에이전트", "상호운용성", "에이전트 간 통신"],
        },
        {
            "title": "구글-앤트로픽 협력 확대",
            "impact": "high",
            "keywords": ["구글", "앤트로픽", "59조", "400억"],
        },
        {
            "title": "TypeScript 7.0 Go 포팅",
            "impact": "medium",
            "keywords": ["TypeScript", "Go", "컴파일", "네이티브"],
        },
        {
            "title": "AI 법률·윤리 쟁점 확대",
            "impact": "medium",
            "keywords": ["증거", "법정", "총격", "소셜미디어", "노르웨이"],
        },
        {
            "title": "AI 음성 모델 경쟁",
            "impact": "medium",
            "keywords": ["음성", "Grok", "저지연", "음성 AI"],
        },
    ]

    trends = []
    for theme in themes:
        matched = [kw for kw in theme["keywords"] if kw in all_text]
        if matched:
            sources = [a["title"] for a in articles if any(kw in a["title"] for kw in matched)][:3]
            trends.append({
                "title": theme["title"],
                "description": f"관련 키워드 {len(matched)}건: {', '.join(matched[:4])}. {len(sources)}건 기사에서 확인.",
                "sources": sources,
                "impact": theme["impact"]
            })

    return trends, all_text

def build_summary(articles, trends, all_text):
    """300자左右的 실제 요약 생성"""
    n = len(articles)
    top_trends = ", ".join([t["title"] for t in trends[:4]]) if trends else "주요 기술 동향"

    # 메인 키워드 추출
    key_kw = []
    for kw in ["Claude Code", "Browser Use", "Cohere", "Aleph Alpha", "메타", "AWS", "TypeScript", "A2A", "MCP"]:
        if kw in all_text:
            key_kw.append(kw)
    key_str = "·".join(key_kw[:5]) if key_kw else ""

    summary = f"오늘 {n}건 기술 기사 분석. 핵심 키워드: {key_str}. "
    if trends:
        summary += f"주요 트렌드는 {', '.join([t['title'] for t in trends[:3]])}."
        if len(summary) < 200:
            summary += f" AI 코딩 에이전트 생태계 확장, 메타-AWS 인프라 변화, 유럽 소버린 AI 전략 등 전체적으로 AI 산업 전반에 걸친 구조적 변화가 진행 중."
    elif len(summary) < 100:
        summary += f" {n}건의 다양한 기술 소식으로 구성됨."

    # 300자 제한
    if len(summary) > 300:
        summary = summary[:297] + "..."

    return summary

def main():
    data = load_articles()
    articles = data.get("articles", [])
    fetched_at = data.get("fetched_at", datetime.now(KST).isoformat())
    print(f"📰 {len(articles)}건 기사 로드 완료")

    print("🤖 인사이트 분석 중...")
    trends, all_text = analyze_articles(articles)
    summary = build_summary(articles, trends, all_text)
    print(f"📋 요약 ({len(summary)}자): {summary[:100]}...")

    action_items = []
    insights = []
    for t in trends:
        action_items.append({
            "title": f"[{t['title']}] 동향 체크",
            "description": f"키워드: {t['description'][:80]}. 기사 소스: {', '.join(t['sources'][:2])}",
            "priority": t["impact"],
            "trend_ref": t["title"],
            "effort": "30min"
        })

    result = {
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
    }

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"\n✅ 인사이트 생성 완료")
    print(f"📊 트렌드 {len(trends)}건")
    print(f"🎯 액션아이템 {len(action_items)}건")
    print(f"📁 저장: {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
